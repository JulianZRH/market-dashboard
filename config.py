"""Central configuration for the Market Overview Dashboard.

Everything you might want to fine-tune lives here:
refresh interval, port, and the instrument universe per asset class.

Instrument fields:
    name     display name
    ccy      currency label shown in the table
    type     "price" -> changes shown in %
             "yield" -> changes shown in basis points
    source   "yahoo" (default) or "investing"
    ticker   Yahoo Finance symbol            (source "yahoo")
    pair_id  investing.com numeric pair id   (source "investing")
    scale    optional multiplier applied to the raw quote (default 1)
    note     small-print remark shown under the instrument name

investing.com pair ids were extracted from the instrument pages
(e.g. https://www.investing.com/rates-bonds/eur-5-years-irs-interest-rate-swap).
"""

REFRESH_MINUTES = 15        # background data refresh interval
PORT = 8050                 # dashboard served at http://localhost:8050
PAGE_RELOAD_SECONDS = 60    # how often the browser re-renders the cached data
STALE_AFTER_DAYS = 3        # show "as of <date>" when data is older than this

ASSET_CLASSES = {
    # Front-month continuous futures from investing.com - they trade nearly
    # around the clock, unlike the cash indices, and cover the European
    # contracts (FESX, FDAX, FSMI, Z) that Yahoo Finance does not carry.
    "Equity (front-month futures)": [
        {"name": "S&P 500",       "pair_id": 8839, "ccy": "USD", "type": "price", "source": "investing"},
        {"name": "Nasdaq 100",    "pair_id": 8874, "ccy": "USD", "type": "price", "source": "investing"},
        {"name": "Euro Stoxx 50", "pair_id": 8867, "ccy": "EUR", "type": "price", "source": "investing"},
        {"name": "DAX",           "pair_id": 8826, "ccy": "EUR", "type": "price", "source": "investing"},
        {"name": "SMI",           "pair_id": 8837, "ccy": "CHF", "type": "price", "source": "investing"},
        {"name": "FTSE 100",      "pair_id": 8838, "ccy": "GBP", "type": "price", "source": "investing"},
        {"name": "CAC 40",        "pair_id": 8853, "ccy": "EUR", "type": "price", "source": "investing"},
        {"name": "Nikkei 225",    "pair_id": 8859, "ccy": "JPY", "type": "price", "source": "investing"},
        {"name": "Hang Seng",     "pair_id": 8984, "ccy": "HKD", "type": "price", "source": "investing"},
    ],
    # Interest rate swaps from investing.com (Yahoo has no EUR/CHF yields).
    "Rates (IRS)": [
        {"name": "USD 1Y",  "pair_id": 1118148, "ccy": "USD", "type": "yield", "source": "investing", "note": "USDSB3L1Y="},
        {"name": "USD 3Y",  "pair_id": 1122447, "ccy": "USD", "type": "yield", "source": "investing", "note": "USDSB3L3Y="},
        {"name": "USD 5Y",  "pair_id": 1122449, "ccy": "USD", "type": "yield", "source": "investing", "note": "USDSB3L5Y="},
        {"name": "USD 10Y", "pair_id": 1122453, "ccy": "USD", "type": "yield", "source": "investing", "note": "USDSB3L10Y="},
        {"name": "EUR 1Y",  "pair_id": 1156452, "ccy": "EUR", "type": "yield", "source": "investing", "note": "EURIRS1Y="},
        {"name": "EUR 3Y",  "pair_id": 1156454, "ccy": "EUR", "type": "yield", "source": "investing", "note": "EURIRS3Y="},
        {"name": "EUR 5Y",  "pair_id": 1156456, "ccy": "EUR", "type": "yield", "source": "investing", "note": "EURIRS5Y="},
        {"name": "EUR 10Y", "pair_id": 1156461, "ccy": "EUR", "type": "yield", "source": "investing", "note": "EURIRS10Y="},
        {"name": "CHF 1Y",  "pair_id": 1156470, "ccy": "CHF", "type": "yield", "source": "investing", "note": "CHFIRS1Y="},
        {"name": "CHF 3Y",  "pair_id": 1156472, "ccy": "CHF", "type": "yield", "source": "investing", "note": "CHFIRS3Y="},
        {"name": "CHF 5Y",  "pair_id": 1156474, "ccy": "CHF", "type": "yield", "source": "investing", "note": "CHFIRS5Y="},
        {"name": "CHF 10Y", "pair_id": 1156479, "ccy": "CHF", "type": "yield", "source": "investing", "note": "CHFIRS10Y="},
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
