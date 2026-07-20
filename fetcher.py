"""Pulls quotes from Yahoo Finance, ZKB and investing.com and shapes them for the template."""

from datetime import datetime, timezone

import pandas as pd
import yfinance as yf

import config
import investing
import zkb


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
    if base is None:
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
        "chg_1d": {"text": "–", "cls": "flat"},
        "chg_ytd": {"text": "–", "cls": "flat"},
    }


def _yahoo_row(inst, data, multi, current_year) -> dict:
    row = _empty_row(inst)
    closes = _closes_for(data, inst["ticker"], multi) * inst.get("scale", 1)
    if len(closes) >= 2:
        is_yield = inst["type"] == "yield"
        last, prev = closes.iloc[-1], closes.iloc[-2]
        prior_year = closes[closes.index.year < current_year]
        ytd_base = prior_year.iloc[-1] if len(prior_year) else closes.iloc[0]
        row["value"] = _fmt_value(last, is_yield, inst.get("decimals"))
        row["chg_1d"] = _fmt_change(last, prev, is_yield)
        row["chg_ytd"] = _fmt_change(last, ytd_base, is_yield)
    elif not row["note"]:
        row["note"] = f"no data returned for {inst['ticker']}"
    return row


def _zkb_row(inst, swap_rates, swap_history) -> dict:
    """A swap-rate row from the ZKB table + locally accumulated history."""
    row = _empty_row(inst)
    rate = (swap_rates or {}).get(inst["swap"])
    if rate is None:
        row["note"] = f"ZKB fetch failed ({inst['swap']})"
        return row
    bases = zkb.change_bases(swap_history or {}, inst["swap"])
    row["value"] = _fmt_value(rate, is_yield=True)
    row["chg_1d"] = _fmt_change(rate, bases["prev"], is_yield=True)
    row["chg_ytd"] = _fmt_change(rate, bases["ytd_base"], is_yield=True)
    return row


def _investing_row(inst) -> dict:
    row = _empty_row(inst)
    try:
        q = investing.quote(inst["pair_id"])
    except Exception as exc:
        row["note"] = f"investing.com fetch failed: {type(exc).__name__}"
        return row
    if not q:
        row["note"] = "no data from investing.com"
        return row
    is_yield = inst["type"] == "yield"
    scale = inst.get("scale", 1)
    last = q["last"] * scale
    prev = q["prev"] * scale if q["prev"] is not None else None
    ytd_base = q["ytd_base"] * scale if q["ytd_base"] is not None else None
    row["value"] = _fmt_value(last, is_yield, inst.get("decimals"))
    row["chg_1d"] = _fmt_change(last, prev, is_yield)
    row["chg_ytd"] = ytd_override or _fmt_change(last, ytd_base, is_yield)
    age = datetime.now(timezone.utc) - q["asof"]
    if age.days >= config.STALE_AFTER_DAYS:
        row["asof"] = f"as of {q['asof']:%Y-%m-%d}"
    return row


def _cbrate_row(inst, cb_rates) -> dict:
    row = _empty_row(inst)
    info = (cb_rates or {}).get(inst["bank"])
    if not info:
        row["note"] = f"central-bank scrape failed ({inst['bank']})"
        return row
    row["value"] = _fmt_value(info["rate"], is_yield=True)
    parts = []
    if info["last_change"]:
        parts.append(f"last change {info['last_change']}")
    if info["next"]:
        parts.append(f"next {info['next']}")
    row["note"] = " · ".join(parts)
    return row


def fetch_snapshot() -> dict:
    """Returns {"classes": {class_name: [row, ...]}, "updated": str}."""
    yahoo_data = yf.download(
        _yahoo_tickers(),
        period="1y",
        interval="1d",
        group_by="ticker",
        auto_adjust=False,
        threads=True,
        progress=False,
    )
    multi = isinstance(yahoo_data.columns, pd.MultiIndex)
    current_year = datetime.now().year

    sources = {
        inst.get("source", "yahoo")
        for instruments in config.ASSET_CLASSES.values()
        for inst in instruments
    }
    cb_rates = None
    if "cbrate" in sources:
        try:
            cb_rates = investing.central_bank_rates()
        except Exception:
            cb_rates = None
    swap_rates = None
    swap_history = None
    if "zkb" in sources:
        try:
            swap_rates = zkb.swap_rates()
            swap_history = zkb.update_history(swap_rates)
        except Exception:
            swap_rates = None

    classes = {}
    for class_name, instruments in config.ASSET_CLASSES.items():
        rows = []
        for inst in instruments:
            source = inst.get("source", "yahoo")
            if source == "zkb":
                rows.append(_zkb_row(inst, swap_rates, swap_history))
            elif source == "cbrate":
                rows.append(_cbrate_row(inst, cb_rates))
            elif source == "investing":
                rows.append(_investing_row(inst))
            else:
                rows.append(_yahoo_row(inst, yahoo_data, multi, current_year))
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
                f"  {r['name']:<28} {r['ccy']:<4} {r['value']:>12}"
                f"  1d {r['chg_1d']['text']:>9}  YTD {r['chg_ytd']['text']:>10}"
                f"{asof}  {r['note']}"
            )
