"""LME industrial-metal prices from westmetall.com.

Yahoo Finance has no LME quotes (only COMEX aluminium/copper), so nickel,
zinc, lead etc. come from westmetall's public market-data pages. Each
metal has a history table (markdaten.php?action=table&field=LME_Xx_cash)
with daily official LME cash settlements back to the start of the year -
that gives proper 1d and YTD changes in a single request per metal.
Results are cached for the calendar day (LME settles once per day).
"""

import re
from datetime import date, datetime

from curl_cffi import requests

_URL = "https://www.westmetall.com/en/markdaten.php"
# field -> (fetch_date, [(date, settlement), ...] ascending)
_cache = {}

# table rows look like: 17. July 2026|16,725.00|16,870.00|274,284
_ROW_RE = re.compile(r"(\d{1,2}\. [A-Za-z]+ \d{4})\|([\d,]+\.?\d*)\|")


def _history(field: str) -> list:
    today = date.today()
    cached = _cache.get(field)
    if cached and cached[0] == today:
        return cached[1]
    r = requests.get(
        _URL,
        params={"action": "table", "field": field},
        impersonate="chrome",
        timeout=30,
    )
    r.raise_for_status()
    text = re.sub(r"<[^>]+>", "|", r.text)
    text = re.sub(r"\s*\|\s*", "|", text)
    text = re.sub(r"\|+", "|", text)
    series = []
    for day, value in _ROW_RE.findall(text):
        try:
            series.append(
                (datetime.strptime(day, "%d. %B %Y").date(),
                 float(value.replace(",", "")))
            )
        except ValueError:
            continue
    series.sort()
    if not series:
        raise ValueError(f"no data parsed for {field} - page layout may have changed")
    _cache[field] = (today, series)
    return series


def quote(field: str) -> dict:
    """{"last", "prev", "ytd_base", "asof"} from the LME settlement history."""
    series = _history(field)
    asof, last = series[-1]
    current_year = date.today().year
    prior_year = [v for d, v in series if d.year < current_year]
    return {
        "last": last,
        "prev": series[-2][1] if len(series) >= 2 else None,
        # table usually starts at the first trading day of the current year,
        # so fall back to that as the YTD base
        "ytd_base": prior_year[-1] if prior_year else series[0][1],
        "asof": asof,
    }
