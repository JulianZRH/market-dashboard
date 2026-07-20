"""Central configuration for the Market Overview Dashboard.

Everything you might want to fine-tune lives here:
refresh interval, port, and the instrument universe per asset class.

Instrument fields:
    name     display name
    ccy      currency label shown in the table
    type     "price" -> changes shown in %
             "yield" -> changes shown in basis points
    source      "yahoo" (default), "zkb", "cbrate", "fred", "westmetall"
                or "investing"
    ticker      Yahoo Finance symbol            (source "yahoo")
    swap        ZKB swap key "<CCY><years>", e.g. "CHF2"   (source "zkb")
    bank        central-bank code on investing.com/central-banks/ (source "cbrate")
    series      FRED series id, e.g. "EFFR"     (source "fred")
    field       westmetall table field, e.g. "LME_Ni_cash" (source "westmetall")
    pair_id     investing.com numeric pair id   (source "investing", currently unused)
    scale       optional multiplier applied to the raw quote (default 1)
    decimals    optional number of decimals for the Last column
    note        small-print remark shown under the instrument name

Swap rates come from the ZKB finance portal (zkb-finance.mdgms.com), which
serves all currencies/maturities in one fast page load. investing.com is
currently only used for the (12h-cached) central-bank policy rates; its
slow per-instrument chart API is not used any more.
"""

REFRESH_MINUTES = 1         # background data refresh interval
PORT = 8050                 # dashboard served at http://localhost:8050
PAGE_RELOAD_SECONDS = 60    # how often the browser re-renders the cached data
STALE_AFTER_DAYS = 3        # show "as of <date>" when data is older than this
WALLPAPER_MONITOR = "left"  # wallpaper mode: "left", "right" or "all" monitors
WALLPAPER_OTHERS = "black"  # non-target monitors: "black" or "keep" their wallpaper

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
        {"name": "Leonteq",       "ticker": "LEON.SW",   "ccy": "CHF", "type": "price",
         "note": "Leonteq Securities AG (SIX)"},
    ],
    # Central-bank policy rates (investing.com/central-banks/, 12h cache)
    # plus interest rate swaps from the ZKB finance portal.
    # ZKB's table starts at 2 years, so 2Y stands in for the 1Y bucket.
    "Rates (policy + swaps)": [
        {"name": "Effective Federal Funds Rate", "series": "EFFR", "ccy": "USD",
         "type": "yield", "source": "fred", "note": "NY Fed via FRED, published T+2"},
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
    # Official LME cash settlements (USD/t) from westmetall.com - Yahoo has
    # no LME quotes. Settled once per day (T-1), hence EOD values.
    "Industrial Metals (LME, USD/t)": [
        {"name": "Copper",    "field": "LME_Cu_cash", "ccy": "USD", "type": "price", "source": "westmetall"},
        {"name": "Aluminium", "field": "LME_Al_cash", "ccy": "USD", "type": "price", "source": "westmetall"},
        {"name": "Nickel",    "field": "LME_Ni_cash", "ccy": "USD", "type": "price", "source": "westmetall"},
        {"name": "Zinc",      "field": "LME_Zn_cash", "ccy": "USD", "type": "price", "source": "westmetall"},
        {"name": "Lead",      "field": "LME_Pb_cash", "ccy": "USD", "type": "price", "source": "westmetall"},
    ],
    "Crypto": [
        {"name": "Bitcoin",       "ticker": "BTC-USD", "ccy": "USD", "type": "price"},
        {"name": "Ether",         "ticker": "ETH-USD", "ccy": "USD", "type": "price"},
        {"name": "Solana",        "ticker": "SOL-USD", "ccy": "USD", "type": "price"},
        {"name": "XRP",           "ticker": "XRP-USD", "ccy": "USD", "type": "price", "decimals": 4},
        {"name": "LEO",           "ticker": "LEO-USD", "ccy": "USD", "type": "price"},
    ],
    "FX": [
        {"name": "USD/CHF", "ticker": "CHF=X",    "ccy": "CHF", "type": "price", "decimals": 4},
        {"name": "EUR/CHF", "ticker": "EURCHF=X", "ccy": "CHF", "type": "price", "decimals": 4},
        {"name": "EUR/USD", "ticker": "EURUSD=X", "ccy": "USD", "type": "price", "decimals": 4},
    ],
    "Credit": [
        {"name": "IHYG", "ticker": "IHYG.L", "ccy": "EUR", "type": "price",
         "note": "iShares EUR High Yield Corp Bond ETF"},
        {"name": "IEAC", "ticker": "IEAC.L", "ccy": "EUR", "type": "price",
         "note": "iShares EUR Corp Bond ETF"},
        {"name": "HYG", "ticker": "HYG", "ccy": "USD", "type": "price",
         "note": "iShares USD High Yield Corp Bond ETF"},
        {"name": "LQD", "ticker": "LQD", "ccy": "USD", "type": "price",
         "note": "iShares USD IG Corp Bond ETF"},
    ],
}
