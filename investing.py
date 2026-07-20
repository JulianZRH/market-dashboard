"""investing.com data access (unofficial chart API, Chrome-impersonated).

investing.com has no official API. Its site loads chart data from
    https://api.investing.com/api/financialdata/{pair_id}/historical/chart/
which is protected by Cloudflare; curl_cffi's Chrome impersonation gets
through. Each instrument is identified by a numeric pair_id (stored in
config.py; found via the page HTML or the /api/search/v2/search endpoint).

quote(pair_id) returns:
    last      most recent traded/marked value
    prev      final value of the previous day with data (basis for 1d change)
    ytd_base  final value of the previous year (basis for YTD change)
    asof      UTC datetime of the last data point (swaps update irregularly)
"""

import time
from datetime import date, datetime, timezone

from curl_cffi import requests

_CHART_URL = "https://api.investing.com/api/financialdata/{pair_id}/historical/chart/"
_HEADERS = {"domain-id": "www"}
_THROTTLE_SECONDS = 0.4  # be polite: ~20 instruments per refresh cycle

# pair_id -> (fetch_date, ytd_base); the yearly series is refetched once a day
_ytd_cache = {}


def _get_chart(pair_id: int, interval: str, period: str) -> list:
    """Returns [(utc_datetime, close), ...] sorted ascending."""
    r = requests.get(
        _CHART_URL.format(pair_id=pair_id),
        params={"interval": interval, "period": period, "pointscount": "160"},
        headers=_HEADERS,
        impersonate="chrome",
        timeout=25,
    )
    r.raise_for_status()
    rows = r.json().get("data") or []
    time.sleep(_THROTTLE_SECONDS)
    return [
        (datetime.fromtimestamp(p[0] / 1000, tz=timezone.utc), p[4])
        for p in rows
        if p[4] is not None
    ]


def _ytd_base(pair_id: int):
    today = date.today()
    cached = _ytd_cache.get(pair_id)
    if cached and cached[0] == today:
        return cached[1]
    # period=P1Y comes back as ~53 weekly bars; the last bar dated before
    # Jan 1 approximates the previous year's closing level.
    points = _get_chart(pair_id, "P1D", "P1Y")
    prior = [close for ts, close in points if ts.year < today.year]
    base = prior[-1] if prior else (points[0][1] if points else None)
    _ytd_cache[pair_id] = (today, base)
    return base


def quote(pair_id: int):
    hourly = _get_chart(pair_id, "PT1H", "P1M")
    if not hourly:
        return None
    asof, last = hourly[-1]
    prev_day = [close for ts, close in hourly if ts.date() < asof.date()]
    return {
        "last": last,
        "prev": prev_day[-1] if prev_day else None,
        "ytd_base": _ytd_base(pair_id),
        "asof": asof,
    }
