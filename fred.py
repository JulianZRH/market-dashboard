"""FRED (St. Louis Fed) data series via the keyless fredgraph.csv download.

Used for the Effective Federal Funds Rate (series EFFR, published by the
NY Fed with ~2 business days lag). The CSV contains daily history, so 1d
and YTD changes come for free. Cached for 4 hours - the series only gains
one value per business day.
"""

import time
from datetime import date, datetime

from curl_cffi import requests

_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv"
_TTL_SECONDS = 4 * 3600
_cache = {}  # series -> (fetch_time, quote dict)


def quote(series: str) -> dict:
    """{"last", "prev", "ytd_base", "asof"} for a FRED series."""
    cached = _cache.get(series)
    if cached and time.time() - cached[0] < _TTL_SECONDS:
        return cached[1]
    # start in December of last year so the YTD base (last value of the
    # previous year) is always included
    cosd = date(date.today().year - 1, 12, 1).isoformat()
    r = requests.get(
        _URL,
        params={"id": series, "cosd": cosd},
        impersonate="chrome",
        timeout=30,
    )
    r.raise_for_status()
    rows = []
    for line in r.text.strip().splitlines()[1:]:
        day, _, value = line.partition(",")
        if value.strip() in ("", "."):
            continue
        rows.append((datetime.strptime(day, "%Y-%m-%d").date(), float(value)))
    if not rows:
        raise ValueError(f"no data in FRED csv for {series}")
    current_year = date.today().year
    prior_year = [v for d, v in rows if d.year < current_year]
    q = {
        "last": rows[-1][1],
        "prev": rows[-2][1] if len(rows) >= 2 else None,
        "ytd_base": prior_year[-1] if prior_year else rows[0][1],
        "asof": rows[-1][0],
    }
    _cache[series] = (time.time(), q)
    return q
