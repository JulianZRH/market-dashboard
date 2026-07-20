# Market Overview Dashboard

A lightweight local dashboard that pulls market data from **Yahoo Finance**,
the **ZKB finance portal** and **investing.com** every 15 minutes and
displays it in the browser, segregated into asset classes:

| Asset class | Contents | Source |
|---|---|---|
| **Equity** | S&P 500, Nasdaq 100, Euro Stoxx 50, DAX, SMI, FTSE 100, CAC 40, Nikkei 225, Hang Seng, VT (Vanguard Total World ETF), Leonteq | Yahoo Finance |
| **Rates** | Effective Federal Funds Rate (FRED), ECB / SNB policy rates, interest rate swaps 2y / 3y / 5y / 10y in USD, EUR, CHF | FRED + investing.com + ZKB |
| **Precious Metals** | Gold, Silver, Palladium, Platinum | Yahoo Finance |
| **Energy** | WTI, Brent, Nat Gas | Yahoo Finance |
| **Industrial Metals** | Copper, Aluminium, Nickel, Zinc, Lead (LME cash, USD/t) | westmetall.com |
| **Crypto** | Bitcoin, Ether, Solana, XRP, UNUS SED LEO | Yahoo Finance |
| **FX** | USD/CHF, EUR/CHF, EUR/USD | Yahoo Finance |
| **Credit** | iTraxx Crossover, iTraxx Europe (Main), CDX HY, CDX IG (via ETF proxies, see caveats below) | Yahoo Finance |

All sources are fetched **in parallel** (full snapshot < 1 s) and the last
snapshot is persisted, so on startup the dashboard immediately shows the
previous session's data while fresh data loads in the background.

Each instrument shows **Last**, **1d change** and **YTD change**
(percent for prices, basis points for yields).

## How it runs

- `app.py` starts a small Flask server at **http://localhost:8050** and opens
  your browser automatically.
- A background thread re-fetches all data from Yahoo Finance every
  **15 minutes** (`REFRESH_MINUTES` in `config.py`).
- The browser page re-renders the cached data every 60 seconds, so it can
  simply stay open in a background tab / second monitor.
- Starting the launcher again while the server is running just re-opens the
  browser tab (no duplicate server).

## Quick start

Double-click **`start_dashboard.bat`** (or the *Market Dashboard* desktop
shortcut). On first run it creates a `.venv` and installs the requirements
automatically; afterwards it starts instantly.

Manual setup, if preferred:

```bat
py -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe app.py
```

Quick data check without the server:

```bat
.venv\Scripts\python.exe fetcher.py
```

## Configuration

Everything lives in [`config.py`](config.py): refresh interval, port, and the
instrument universe. Add or remove instruments by editing the
`ASSET_CLASSES` dict — each entry is one row on the dashboard.

## Data caveats

- **Swap rates (ZKB):** parsed from the Swap-Sätze table on
  [zkb-finance.mdgms.com](https://zkb-finance.mdgms.com/home/bonds/index.html)
  — one fast request covers all currencies and maturities. The table starts
  at 2 years (no 1y bucket) and only shows current values; the dashboard
  therefore records them daily in `data/swap_history.json` and computes
  1d / YTD changes from that accumulated history (1d appears from the
  second day of running, YTD once history reaches back to a year-end).
- **EFFR** comes from FRED's keyless `fredgraph.csv` download (series
  `EFFR`); the NY Fed publishes it with ~2 business days lag.
- **LME metals** are the official daily cash settlements (T-1) parsed from
  [westmetall.com](https://www.westmetall.com/en/markdaten.php); their
  history tables provide proper 1d / YTD changes, cached per calendar day.
- **Policy rates** are scraped from
  [investing.com/central-banks](https://www.investing.com/central-banks/)
  (cached for 12h; the row note shows the last change and next meeting).
  This is the only remaining investing.com dependency — the slow
  per-instrument chart API (`investing.py`) is no longer used, but kept
  in the repo in case single-instrument quotes are needed again.
- **Credit:** Yahoo has **no CDS index spreads** (iTraxx / CDX on-the-run
  series). The dashboard currently shows liquid corporate-bond ETFs as
  clearly-labelled directional proxies (IHYG, IEAC, HYG, LQD). Replacing
  these with real on-the-run spreads requires a different data source.

## Project structure

```
market_dashboard/
├── app.py               # Flask server + 15-min background refresh loop
├── fetcher.py           # orchestrates all sources + row formatting
├── zkb.py               # ZKB swap-rate table + local daily history
├── fred.py              # FRED series (EFFR) via keyless csv download
├── westmetall.py        # LME cash settlements incl. daily history
├── investing.py         # investing.com access (only policy rates in use)
├── config.py            # refresh interval, port, instrument universe
├── templates/
│   └── index.html       # dashboard page (dark theme, auto-reload)
├── start_dashboard.bat  # one-click launcher (creates .venv on first run)
├── requirements.txt
└── README.md
```
