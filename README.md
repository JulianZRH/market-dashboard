# Market Overview Dashboard

A lightweight local dashboard that pulls market data from **Yahoo Finance**
(via `yfinance`) every 15 minutes and displays it in the browser, segregated
into four asset classes:

| Asset class | Contents |
|---|---|
| **Equity** | S&P 500, Nasdaq 100, Euro Stoxx 50, DAX, SMI, FTSE 100, CAC 40, Nikkei 225, Hang Seng |
| **Rates** | Government yields 1y / 3y / 5y / 10y in USD, EUR, CHF (see caveats below) |
| **Commodities** | Gold, Silver, WTI, Brent, Copper, Nat Gas, Platinum |
| **Credit** | iTraxx Crossover, iTraxx Europe (Main), CDX HY, CDX IG (via ETF proxies, see caveats below) |

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

## Data caveats (Yahoo Finance limitations)

- **Rates:** Yahoo only carries the CBOE US yield indices (5y `^FVX`,
  10y `^TNX`). USD 1y/3y and all EUR/CHF government yields are **not
  available on Yahoo** and are shown as placeholder rows. Candidate sources
  for a later iteration: FRED (USD), ECB/Bundesbank (EUR), SNB (CHF).
- **Credit:** Yahoo has **no CDS index spreads** (iTraxx / CDX on-the-run
  series). The dashboard currently shows liquid corporate-bond ETFs as
  clearly-labelled directional proxies (IHYG, IEAC, HYG, LQD). Replacing
  these with real on-the-run spreads requires a different data source.
- Yield changes are computed from daily closes; intraday yield moves appear
  once Yahoo updates the current day's quote.

## Project structure

```
market_dashboard/
├── app.py               # Flask server + 15-min background refresh loop
├── fetcher.py           # Yahoo Finance download + row formatting
├── config.py            # refresh interval, port, instrument universe
├── templates/
│   └── index.html       # dashboard page (dark theme, auto-reload)
├── start_dashboard.bat  # one-click launcher (creates .venv on first run)
├── requirements.txt
└── README.md
```
