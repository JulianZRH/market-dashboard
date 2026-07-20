"""Swap rates from the ZKB finance portal (zkb-finance.mdgms.com).

The bonds page serves the whole Swap-Saetze table (CHF/EUR/USD/GBP,
2-20 years) as plain server-rendered HTML - one request covers every
instrument, which keeps the refresh fast.

The page only shows current values, and the portal's chart endpoints
return PNG images (no machine-readable history). Therefore this module
keeps its own daily history in data/swap_history.json: every refresh
records today's values, and 1d / YTD changes are computed against that
accumulated history (1d appears from the second day on, YTD once the
history reaches back to the previous year-end).
"""

import json
import re
from datetime import date
from pathlib import Path

import requests

_URL = "https://zkb-finance.mdgms.com/home/bonds/index.html"
_HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
_HISTORY_FILE = Path(__file__).resolve().parent / "data" / "swap_history.json"

# matches e.g. ...FI_TITLE__CHART_FACTSHEET_2=Swap+CHF+%2F+2+Jahre">0.2263</a>
# (USD/GBP titles contain a double "+": "Swap++USD+...")
_ROW_RE = re.compile(
    r"FI_TITLE__CHART_FACTSHEET_2=Swap\++([A-Z]{3})\+%2F\+(\d+)\+Jahre[^>]*>([\d.]+)</a>"
)


def swap_rates() -> dict:
    """Parses the Swap-Saetze table. Returns {"CHF2": 0.2263, "EUR10": ..., ...}."""
    r = requests.get(_URL, headers=_HEADERS, timeout=30)
    r.raise_for_status()
    out = {}
    for ccy, years, rate in _ROW_RE.findall(r.text):
        out[f"{ccy}{int(years)}"] = float(rate)
    if not out:
        raise ValueError("no swap rates found - ZKB page layout may have changed")
    return out


def _load_history() -> dict:
    if _HISTORY_FILE.exists():
        return json.loads(_HISTORY_FILE.read_text())
    return {}


def update_history(rates: dict) -> dict:
    """Records today's values (overwriting today's entry) and returns the history."""
    history = _load_history()
    history[date.today().isoformat()] = rates
    _HISTORY_FILE.parent.mkdir(exist_ok=True)
    _HISTORY_FILE.write_text(json.dumps(history, indent=1, sort_keys=True))
    return history


def change_bases(history: dict, key: str) -> dict:
    """Returns {"prev": value or None, "ytd_base": value or None} for one swap key.

    prev      = value on the most recent day before today with data
    ytd_base  = value on the last recorded day of the previous year
    """
    today = date.today().isoformat()
    year_start = f"{date.today().year}-01-01"
    prev = None
    ytd_base = None
    for day in sorted(history):
        value = history[day].get(key)
        if value is None:
            continue
        if day < today:
            prev = value
        if day < year_start:
            ytd_base = value
    return {"prev": prev, "ytd_base": ytd_base}
