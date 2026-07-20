"""Central configuration for the Market Overview Dashboard.

Everything you might want to fine-tune lives here:
refresh interval, port, and the instrument universe per asset class.

Instrument fields:
    name     display name
    ccy      currency label shown in the table
    type     "price" -> changes shown in %
             "yield" -> changes shown in basis points
    source      "yahoo" (default), "zkb", "cbrate" or "investing"
    ticker      Yahoo Finance symbol            (source "yahoo")
    swap        ZKB swap key "<CCY><years>", e.g. "CHF2"   (source "zkb")
    bank        central-bank code on investing.com/central-banks/ (source "cbrate")
    pair_id     investing.com numeric pair id   (source "investing", currently unused)
    scale       optional multiplier applied to the raw quote (default 1)
    decimals    optional number of decimals for the Last column
    note        small-print remark shown under the instrument name

Swap rates come from the ZKB finance portal (zkb-finance.mdgms.com), which
serves all currencies/maturities in one fast page load. investing.com is
currently only used for the (12h-cached) central-bank policy rates; its
slow per-instrument chart API is not used any more.
"""

REFRESH_MINUTES = 15        # background data refresh interval
PORT = 8050                 # dashboard served at http://localhost:8050
PAGE_RELOAD_SECONDS = 60    # how often the browser re-renders the cached data
STALE_AFTER_DAYS = 3        # show "as of <date>" when data is older than this

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
        {"name": "World (VT)",    "ticker": "VT",        "ccy": "USD", "type": "price",
         "note": "Vanguard Total World ETF"},
    ],
    # Central-bank policy rates (investing.com/central-banks/, 12h cache)
    # plus interest rate swaps from the ZKB finance portal.
    # ZKB's table starts at 2 years, so 2Y stands in for the 1Y bucket.
    "Rates (policy + swaps)": [
        {"name": "Fed Funds", "bank": "FED", "ccy": "USD", "type": "yield", "source": "cbrate"},
        {"name": "USD 2Y",  "swap": "USD2",  "ccy": "USD", "type": "yield", "source": "zkb"},
        {"name": "USD 3Y",  "swap": "USD3",  "ccy": "USD", "type": "yield", "source": "zkb"},
        {"name": "USD 5Y",  "swap": "USD5",  "ccy": "USD", "type": "yield", "source": "zkb"},
        {"name": "USD 10Y", "swap": "USD10", "ccy": "USD", "type": "yield", "source": "zkb"},
        {"name": "ECB (main refi)", "bank": "ECB", "ccy": "EUR", "type": "yield", "source": "cbrate"},
        {"name": "EUR 2Y",  "swap": "EUR2",  "ccy": "EUR", "type": "yield", "source": "zkb"},
        {"name": "EUR 3Y",  "swap": "EUR3",  "ccy": "EUR", "type": "yield", "source": "zkb"},
        {"name": "EUR 5Y",  "swap": "EUR5",  "ccy": "EUR", "type": "yield", "source": "zkb"},
        {"name": "EUR 10Y", "swap": "EUR10", "ccy": "EUR", "type": "yield", "source": "zkb"},
        {"name": "SNB policy rate", "bank": "SNB", "ccy": "CHF", "type": "yield", "source": "cbrate"},
        {"name": "CHF 2Y",  "swap": "CHF2",  "ccy": "CHF", "type": "yield", "source": "zkb"},
        {"name": "CHF 3Y",  "swap": "CHF3",  "ccy": "CHF", "type": "yield", "source": "zkb"},
        {"name": "CHF 5Y",  "swap": "CHF5",  "ccy": "CHF", "type": "yield", "source": "zkb"},
        {"name": "CHF 10Y", "swap": "CHF10", "ccy": "CHF", "type": "yield", "source": "zkb"},
    ],
    "Precious Metals": [
        {"name": "Gold",      "ticker": "GC=F", "ccy": "USD", "type": "price"},
        {"name": "Silver",    "ticker": "SI=F", "ccy": "USD", "type": "price"},
        {"name": "Palladium", "ticker": "PA=F", "ccy": "USD", "type": "price"},
        {"name": "Platinum",  "ticker": "PL=F", "ccy": "USD", "type": "price"},
    ],
    "Energy": [
        {"name": "WTI Crude",   "ticker": "CL=F", "ccy": "USD", "type": "price"},
        {"name": "Brent Crude", "ticker": "BZ=F", "ccy": "USD", "type": "price"},
        {"name": "Nat Gas (Henry Hub)", "ticker": "NG=F", "ccy": "USD", "type": "price"},
    ],
    "Industrial Metals": [
        {"name": "Copper", "ticker": "HG=F", "ccy": "USD", "type": "price"},
    ],
    "Crypto": [
        {"name": "Bitcoin",  "ticker": "BTC-USD", "ccy": "USD", "type": "price"},
        {"name": "Ether",    "ticker": "ETH-USD", "ccy": "USD", "type": "price"},
        {"name": "Solana",   "ticker": "SOL-USD", "ccy": "USD", "type": "price"},
    ],
    "FX": [
        {"name": "USD/CHF", "ticker": "CHF=X",    "ccy": "CHF", "type": "price", "decimals": 4},
        {"name": "EUR/CHF", "ticker": "EURCHF=X", "ccy": "CHF", "type": "price", "decimals": 4},
        {"name": "EUR/USD", "ticker": "EURUSD=X", "ccy": "USD", "type": "price", "decimals": 4},
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
