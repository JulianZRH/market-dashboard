"""Pulls quotes from Yahoo Finance and shapes them for the dashboard template."""

from datetime import datetime

import pandas as pd
import yfinance as yf

import config


def _all_tickers():
    return [
        inst["ticker"]
        for instruments in config.ASSET_CLASSES.values()
        for inst in instruments
        if inst.get("ticker")
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


def _fmt_value(value: float, is_yield: bool) -> str:
    if is_yield:
        return f"{value:.2f}%"
    if value >= 1000:
        return f"{value:,.0f}"
    return f"{value:,.2f}"


def _fmt_change(last: float, base: float, is_yield: bool) -> dict:
    if is_yield:
        bp = (last - base) * 100
        return {"text": f"{bp:+.1f} bp", "cls": "pos" if bp >= 0 else "neg"}
    pct = (last / base - 1) * 100
    return {"text": f"{pct:+.2f}%", "cls": "pos" if pct >= 0 else "neg"}


def fetch_snapshot() -> dict:
    """Returns {"classes": {class_name: [row, ...]}, "updated": str}.

    Each row: name, ccy, note, value, chg_1d, chg_ytd (change dicts with text/cls).
    Placeholder instruments (ticker None) and failed downloads yield "n/a" rows.
    """
    tickers = _all_tickers()
    data = yf.download(
        tickers,
        period="1y",
        interval="1d",
        group_by="ticker",
        auto_adjust=False,
        threads=True,
        progress=False,
    )
    multi = isinstance(data.columns, pd.MultiIndex)
    current_year = datetime.now().year

    classes = {}
    for class_name, instruments in config.ASSET_CLASSES.items():
        rows = []
        for inst in instruments:
            row = {
                "name": inst["name"],
                "ccy": inst["ccy"],
                "note": inst.get("note", ""),
                "value": "–",
                "chg_1d": {"text": "–", "cls": "flat"},
                "chg_ytd": {"text": "–", "cls": "flat"},
            }
            ticker = inst.get("ticker")
            if ticker:
                closes = _closes_for(data, ticker, multi) * inst.get("scale", 1)
                if len(closes) >= 2:
                    is_yield = inst["type"] == "yield"
                    last, prev = closes.iloc[-1], closes.iloc[-2]
                    prior_year = closes[closes.index.year < current_year]
                    ytd_base = prior_year.iloc[-1] if len(prior_year) else closes.iloc[0]
                    row["value"] = _fmt_value(last, is_yield)
                    row["chg_1d"] = _fmt_change(last, prev, is_yield)
                    row["chg_ytd"] = _fmt_change(last, ytd_base, is_yield)
                elif not row["note"]:
                    row["note"] = f"no data returned for {ticker}"
            rows.append(row)
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
            print(
                f"  {r['name']:<28} {r['ccy']:<4} {r['value']:>12}"
                f"  1d {r['chg_1d']['text']:>9}  YTD {r['chg_ytd']['text']:>9}"
                f"  {r['note']}"
            )
