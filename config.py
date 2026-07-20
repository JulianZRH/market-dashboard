"""Central configuration for the Market Overview Dashboard.

Everything you might want to fine-tune lives here:
refresh interval, port, and the instrument universe per asset class.

Instrument fields:
    name    display name
    ticker  Yahoo Finance symbol (None = not available on Yahoo -> placeholder row)
    ccy     currency label shown in the table
    type    "price" -> changes shown in %
            "yield" -> changes shown in basis points
    scale   optional multiplier applied to the raw Yahoo quote (default 1)
    note    small-print remark shown under the instrument name
"""

REFRESH_MINUTES = 15        # background data refresh interval
PORT = 8050                 # dashboard served at http://localhost:8050
PAGE_RELOAD_SECONDS = 60    # how often the browser re-renders the cached data

ASSET_CLASSES = {
    "Equity": [
        {"name": "S&P 500",       "ticker": "^GSPC",     "ccy": "USD", "type": "price"},
        {"name": "Nasdaq 100",    "ticker": "^NDX",      "ccy": "USD", "type": "price"},
        {"name": "Euro Stoxx 50", "ticker": "^STOXX50E", "ccy": "EUR", "type": "price"},
        {"name": "DAX",           "ticker": "^GDAXI",    "ccy": "EUR", "type": "price"},
        {"name": "SMI",           "ticker": "^SSMI",     "ccy": "CHF", "type": "price"},
        {"name": "FTSE 100",      "ticker": "^FTSE",     "ccy": "GBP", "type": "price"},
        {"name": "CAC 40",        "ticker": "^FCHI",     "ccy": "EUR", "type": "price"},
        {"name": "Nikkei 225",    "ticker": "^N225",     "ccy": "JPY", "type": "price"},
        {"name": "Hang Seng",     "ticker": "^HSI",      "ccy": "HKD", "type": "price"},
    ],
    "Rates": [
        {"name": "USD 1Y",  "ticker": None,   "ccy": "USD", "type": "yield",
         "note": "not on Yahoo - candidate source: FRED (DGS1)"},
        {"name": "USD 3Y",  "ticker": None,   "ccy": "USD", "type": "yield",
         "note": "not on Yahoo - candidate source: FRED (DGS3)"},
        {"name": "USD 5Y",  "ticker": "^FVX", "ccy": "USD", "type": "yield"},
        {"name": "USD 10Y", "ticker": "^TNX", "ccy": "USD", "type": "yield"},
        {"name": "EUR 1Y",  "ticker": None,   "ccy": "EUR", "type": "yield",
         "note": "not on Yahoo - candidate source: ECB / Bundesbank"},
        {"name": "EUR 3Y",  "ticker": None,   "ccy": "EUR", "type": "yield",
         "note": "not on Yahoo - candidate source: ECB / Bundesbank"},
        {"name": "EUR 5Y",  "ticker": None,   "ccy": "EUR", "type": "yield",
         "note": "not on Yahoo - candidate source: ECB / Bundesbank"},
        {"name": "EUR 10Y", "ticker": None,   "ccy": "EUR", "type": "yield",
         "note": "not on Yahoo - candidate source: ECB / Bundesbank"},
        {"name": "CHF 1Y",  "ticker": None,   "ccy": "CHF", "type": "yield",
         "note": "not on Yahoo - candidate source: SNB data portal"},
        {"name": "CHF 3Y",  "ticker": None,   "ccy": "CHF", "type": "yield",
         "note": "not on Yahoo - candidate source: SNB data portal"},
        {"name": "CHF 5Y",  "ticker": None,   "ccy": "CHF", "type": "yield",
         "note": "not on Yahoo - candidate source: SNB data portal"},
        {"name": "CHF 10Y", "ticker": None,   "ccy": "CHF", "type": "yield",
         "note": "not on Yahoo - candidate source: SNB data portal"},
    ],
    "Commodities": [
        {"name": "Gold",        "ticker": "GC=F",  "ccy": "USD", "type": "price"},
        {"name": "Silver",      "ticker": "SI=F",  "ccy": "USD", "type": "price"},
        {"name": "WTI Crude",   "ticker": "CL=F",  "ccy": "USD", "type": "price"},
        {"name": "Brent Crude", "ticker": "BZ=F",  "ccy": "USD", "type": "price"},
        {"name": "Copper",      "ticker": "HG=F",  "ccy": "USD", "type": "price"},
        {"name": "Nat Gas (Henry Hub)", "ticker": "NG=F", "ccy": "USD", "type": "price"},
        {"name": "Platinum",    "ticker": "PL=F",  "ccy": "USD", "type": "price"},
    ],
    "Credit": [
        # Yahoo Finance has no CDS index (iTraxx / CDX on-the-run) spreads.
        # Until a proper source is wired in, liquid ETFs serve as directional proxies.
        {"name": "iTraxx Crossover", "ticker": "IHYG.L", "ccy": "EUR", "type": "price",
         "note": "proxy: iShares EUR High Yield ETF (IHYG) - no CDS spreads on Yahoo"},
        {"name": "iTraxx Europe (Main)", "ticker": "IEAC.L", "ccy": "EUR", "type": "price",
         "note": "proxy: iShares EUR Corp Bond ETF (IEAC) - no CDS spreads on Yahoo"},
        {"name": "CDX HY", "ticker": "HYG", "ccy": "USD", "type": "price",
         "note": "proxy: iShares USD High Yield ETF (HYG) - no CDS spreads on Yahoo"},
        {"name": "CDX IG", "ticker": "LQD", "ccy": "USD", "type": "price",
         "note": "proxy: iShares USD IG Corp Bond ETF (LQD) - no CDS spreads on Yahoo"},
    ],
}
