"""Pulls quotes from all configured sources and shapes them for the template.

Sources (Yahoo bulk download, investing.com swaps, FRED, westmetall,
central-bank scrape) are independent, so they are fetched in parallel - the
snapshot takes about as long as the slowest single source instead of the sum.
"""

import math
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timezone

import pandas as pd
import yfinance as yf

import config
import fred
import investing
import westmetall


def _yahoo_tickers():
    return [
        inst["ticker"]
        for instruments in config.ASSET_CLASSES.values()
        for inst in instruments
        if inst.get("source", "yahoo") == "yahoo" and inst.get("ticker")
    ]


def _closes_for(data: pd.DataFrame, ticker: str, multi: bool) -> pd.Series:
    if multi:
        if ticker not in data.columns.get_level_values(0):
            return pd.Series(dtype=float)
        df = data[ticker]
    else:
        df = data
    if "Close" not in df:
        return pd.Series(dtype=float)
    return df["Close"].dropna()


def _fmt_value(value: float, is_yield: bool, decimals=None) -> str:
    if is_yield:
        return f"{value:.2f}%"
    if decimals is not None:
        return f"{value:,.{decimals}f}"
    if value >= 1000:
        return f"{value:,.0f}"
    return f"{value:,.2f}"


def _fmt_change(last, base, is_yield: bool) -> dict:
    # a price change needs a non-zero base to divide by; a yield change is a
    # plain difference, so a 0.00% base is fine there
    if base is None or (not is_yield and not base):
        return {"text": "–", "cls": "flat"}
    if is_yield:
        bp = (last - base) * 100
        return {"text": f"{bp:+.1f} bp", "cls": "pos" if bp >= 0 else "neg"}
    pct = (last / base - 1) * 100
    return {"text": f"{pct:+.2f}%", "cls": "pos" if pct >= 0 else "neg"}


def _empty_row(inst) -> dict:
    return {
        "name": inst["name"],
        "ccy": inst["ccy"],
        "note": inst.get("note", ""),
        "value": "–",
        "asof": "",
        "next": "",  # next central-bank meeting date (policy-rate rows only)
        "chg_1d": {"text": "–", "cls": "flat"},
        "chg_ytd": {"text": "–", "cls": "flat"},
    }


def _age_days(asof) -> int:
    if isinstance(asof, datetime):
        return (datetime.now(timezone.utc) - asof).days
    return (date.today() - asof).days


def _number(value):
    """float(value), or None when there is no usable number - fast_info
    returns NaN for fields it has no value for, and a NaN would silently
    poison every change computed from it."""
    try:
        value = float(value)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(value) else value


def _live_quote(ticker: str):
    """Last trade and previous close straight from Yahoo's quote endpoint,
    for the sessions the bulk download does not cover (see _yahoo_row).

    regularMarketPreviousClose is the official close of the previous
    session, the same convention as the daily bars, so switching between the
    two sources does not move the number. fast_info's previousClose comes
    from intraday bars and includes post-market trading (NVDA: 208.80
    instead of the 208.48 regular close), so it only serves as the fallback
    for thin names where Yahoo publishes no regular previous close at all
    (LEON.SW)."""
    try:
        info = yf.Ticker(ticker).fast_info
        last = _number(info.get("lastPrice"))
        prev = _number(info.get("regularMarketPreviousClose"))
        if prev is None:
            prev = _number(info.get("previousClose"))
    except Exception:
        return None
    if last is None or prev is None:
        return None
    return last, prev


def _sessions(data: pd.DataFrame, multi: bool) -> pd.DatetimeIndex:
    """The dates in the downloaded panel that are real trading sessions.

    The bulk frame holds one row per date *any* ticker traded, so with
    crypto in the universe every Saturday and Sunday is a row as well, and
    every market that was closed gets a NaN in it. Counting how many tickers
    actually have a close tells the two apart: a real session is a day most
    of the universe traded, a weekend row only ever carries the crypto
    names."""
    if data.empty:
        return pd.DatetimeIndex([])
    closes = data.xs("Close", axis=1, level=1) if multi else data[["Close"]]
    traded = closes.notna().sum(axis=1)
    return traded.index[traded >= max(1, traded.max() / 2)]


def _yahoo_row(inst, data, multi, current_year, sessions) -> dict:
    row = _empty_row(inst)
    scale = inst.get("scale", 1)
    closes = _closes_for(data, inst["ticker"], multi) * scale
    if len(closes) < 2:
        if not row["note"]:
            row["note"] = f"no data returned for {inst['ticker']}"
        return row
    is_yield = inst["type"] == "yield"
    last, prev = closes.iloc[-1], closes.iloc[-2]
    last_day, prev_day = closes.index[-1], closes.index[-2]
    # A ticker's daily bars are not necessarily a gapless series: it can lag
    # the newest session (no close published yet), and thin names are missing
    # whole sessions outright - Yahoo has no 25 Aug bar for LEON.SW at all,
    # which turns the "previous" close into the one from 24 Aug and reports
    # a two-session -5.31% as the 1d change instead of -0.97%. Either way the
    # live quote is the only source for a true one-session change.
    lagging = len(sessions) > 0 and last_day < sessions[-1]
    skipped = bool(((sessions > prev_day) & (sessions < last_day)).any())
    if lagging or skipped:
        live = _live_quote(inst["ticker"])
        if live:
            last, prev = live[0] * scale, live[1] * scale
        elif lagging:
            row["asof"] = f"as of {last_day:%Y-%m-%d}"
        else:
            # no live quote to repair the hole: show what the change is
            # actually measured against rather than passing it off as 1d
            row["asof"] = f"1d vs {prev_day:%Y-%m-%d}"
    prior_year = closes[closes.index.year < current_year]
    ytd_base = prior_year.iloc[-1] if len(prior_year) else closes.iloc[0]
    row["value"] = _fmt_value(last, is_yield, inst.get("decimals"))
    row["chg_1d"] = _fmt_change(last, prev, is_yield)
    row["chg_ytd"] = _fmt_change(last, ytd_base, is_yield)
    return row


def _quote_row(inst, result, stale_days=None) -> dict:
    """Row from a {"last","prev","ytd_base","asof"} quote (fred / westmetall /
    investing). `result` may also be an Exception from the parallel fetch."""
    row = _empty_row(inst)
    if isinstance(result, Exception):
        row["note"] = f"fetch failed: {type(result).__name__}"
        return row
    if not result:
        row["note"] = "no data"
        return row
    is_yield = inst["type"] == "yield"
    scale = inst.get("scale", 1)
    last = result["last"] * scale
    prev = result["prev"] * scale if result["prev"] is not None else None
    ytd_base = result["ytd_base"] * scale if result["ytd_base"] is not None else None
    row["value"] = _fmt_value(last, is_yield, inst.get("decimals"))
    row["chg_1d"] = _fmt_change(last, prev, is_yield)
    row["chg_ytd"] = _fmt_change(last, ytd_base, is_yield)
    threshold = stale_days if stale_days is not None else config.STALE_AFTER_DAYS
    if result.get("asof") is not None and _age_days(result["asof"]) >= threshold:
        row["asof"] = f"as of {result['asof']:%Y-%m-%d}"
    return row


def _cbrate_row(inst, cb_rates) -> dict:
    row = _empty_row(inst)
    info = (cb_rates or {}).get(inst["bank"])
    if not info:
        row["note"] = f"central-bank scrape failed ({inst['bank']})"
        return row
    row["value"] = _fmt_value(info["rate"], is_yield=True)
    row["next"] = info["next"]
    parts = []
    if info["last_change"]:
        parts.append(f"last change {info['last_change']}")
    if info["next"]:
        parts.append(f"next {info['next']}")
    row["note"] = " · ".join(parts)
    return row


def _timed(label, fn, *args, **kwargs):
    """Wraps a source fetch so each one logs its duration."""
    def run():
        t0 = time.time()
        try:
            return fn(*args, **kwargs)
        finally:
            print(f"[fetch] {label}: {time.time() - t0:.1f}s", flush=True)
    return run


def _submit_all(executor) -> dict:
    """Kicks off every source fetch in parallel. Returns {key: future}."""
    futures = {
        "yahoo": executor.submit(
            _timed(
                "yahoo",
                yf.download,
                _yahoo_tickers(),
                period="1y",
                interval="1d",
                group_by="ticker",
                auto_adjust=False,
                threads=True,
                progress=False,
            )
        )
    }
    for instruments in config.ASSET_CLASSES.values():
        for inst in instruments:
            source = inst.get("source", "yahoo")
            # any row tagged with a bank (cbrate rows, EFFR) needs the
            # central-bank scrape for its rate / next-meeting date
            if inst.get("bank") and "cbrate" not in futures:
                futures["cbrate"] = executor.submit(
                    _timed("cbrate", investing.central_bank_rates)
                )
            if inst.get("bank") == "FED" and "fed_forecast" not in futures:
                futures["fed_forecast"] = executor.submit(
                    _timed("fed forecast", investing.fed_rate_forecast)
                )
            if source == "fred":
                key = ("fred", inst["series"])
                if key not in futures:
                    futures[key] = executor.submit(
                        _timed(f"fred {inst['series']}", fred.quote, inst["series"])
                    )
            elif source == "westmetall":
                key = ("westmetall", inst["field"])
                if key not in futures:
                    futures[key] = executor.submit(
                        _timed(f"lme {inst['field']}", westmetall.quote, inst["field"])
                    )
            elif source == "investing":
                key = ("investing", inst["pair_id"])
                if key not in futures:
                    futures[key] = executor.submit(
                        _timed(f"investing {inst['pair_id']}", investing.quote, inst["pair_id"])
                    )
    return futures


def fetch_snapshot() -> dict:
    """Returns {"classes": {class_name: [row, ...]}, "updated": str}."""
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = _submit_all(executor)
        results = {}
        for key, future in futures.items():
            try:
                results[key] = future.result(timeout=120)
            except Exception as exc:
                results[key] = exc

    yahoo_data = results["yahoo"]
    if isinstance(yahoo_data, Exception):
        yahoo_data = pd.DataFrame()
    multi = isinstance(yahoo_data.columns, pd.MultiIndex)
    sessions = _sessions(yahoo_data, multi)
    current_year = datetime.now().year

    cb_rates = results.get("cbrate")
    if isinstance(cb_rates, Exception):
        cb_rates = None

    fed_forecast = results.get("fed_forecast")
    if isinstance(fed_forecast, Exception):
        fed_forecast = None

    classes = {}
    for class_name, instruments in config.ASSET_CLASSES.items():
        rows = []
        for inst in instruments:
            source = inst.get("source", "yahoo")
            if source == "cbrate":
                rows.append(_cbrate_row(inst, cb_rates))
            elif source == "fred":
                # published T+2 -> only flag as stale beyond the normal lag
                row = _quote_row(inst, results[("fred", inst["series"])], stale_days=5)
                bank = (cb_rates or {}).get(inst.get("bank"))
                if bank and bank["next"]:
                    nxt = bank["next"]
                    if inst.get("bank") == "FED" and fed_forecast:
                        nxt += (f" · {fed_forecast['range']}% expected"
                                f" ({fed_forecast['prob']:.0f}%)")
                    row["next"] = nxt
                    sep = " · " if row["note"] else ""
                    row["note"] = f"{row['note']}{sep}next {nxt}"
                rows.append(row)
            elif source == "westmetall":
                # EOD settlement (T-1) -> allow for weekends before flagging
                rows.append(_quote_row(inst, results[("westmetall", inst["field"])], stale_days=5))
            elif source == "investing":
                rows.append(_quote_row(inst, results[("investing", inst["pair_id"])]))
            else:
                rows.append(_yahoo_row(inst, yahoo_data, multi, current_year, sessions))
        classes[class_name] = rows

    return {
        "classes": classes,
        "updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


if __name__ == "__main__":
    # Quick manual test: print the snapshot as plain text.
    snapshot = fetch_snapshot()
    print(f"Snapshot @ {snapshot['updated']}")
    for class_name, rows in snapshot["classes"].items():
        print(f"\n== {class_name} ==")
        for r in rows:
            asof = f"  [{r['asof']}]" if r["asof"] else ""
            print(
                f"  {r['name']:<32} {r['ccy']:<4} {r['value']:>12}"
                f"  1d {r['chg_1d']['text']:>9}  YTD {r['chg_ytd']['text']:>10}"
                f"{asof}  {r['note']}"
            )
