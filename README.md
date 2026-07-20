# Market Overview Dashboard

A lightweight local dashboard that pulls market data from **Yahoo Finance**
and **investing.com** every 15 minutes and displays it in the browser,
segregated into four asset classes:

| Asset class | Contents | Source |
|---|---|---|
| **Equity** | Front-month futures: S&P 500, Nasdaq 100, Euro Stoxx 50, DAX, SMI, FTSE 100, CAC 40, Nikkei 225, Hang Seng | investing.com |
| **Rates** | Interest rate swaps 1y / 3y / 5y / 10y in USD (`USDSB3L…=`), EUR (`EURIRS…=`), CHF (`CHFIRS…=`) | investing.com |
| **Commodities** | Gold, Silver, WTI, Brent, Copper, Nat Gas, Platinum | Yahoo Finance |
| **Credit** | iTraxx Crossover, iTraxx Europe (Main), CDX HY, CDX IG (via ETF proxies, see caveats below) | Yahoo Finance |

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

- **investing.com is unofficial:** there is no public API; the dashboard
  uses the site's internal chart endpoint
  (`api.investing.com/api/financialdata/{pair_id}/historical/chart/`) with
  Chrome impersonation via `curl_cffi`. If investing.com changes its
  endpoints or protection, `investing.py` may need adjusting.
- **Stale swap feeds:** investing.com's EUR and CHF IRS series update
  irregularly (at the time of writing they lag by ~2 weeks; USD swaps are
  live). Rows whose last data point is older than `STALE_AFTER_DAYS`
  (default 3) show an orange **"as of \<date\>"** marker instead of
  pretending to be live.
- **Futures YTD:** the equity YTD change is computed on the continuous
  front-month futures series, which crosses contract rolls — it can differ
  noticeably from the cash-index YTD (carry / roll effects).
- **Credit:** Yahoo has **no CDS index spreads** (iTraxx / CDX on-the-run
  series). The dashboard currently shows liquid corporate-bond ETFs as
  clearly-labelled directional proxies (IHYG, IEAC, HYG, LQD). Replacing
  these with real on-the-run spreads requires a different data source.

## Project structure

```
market_dashboard/
├── app.py               # Flask server + 15-min background refresh loop
├── fetcher.py           # orchestrates both sources + row formatting
├── investing.py         # investing.com chart-API access (curl_cffi/Chrome)
├── config.py            # refresh interval, port, instrument universe
├── templates/
│   └── index.html       # dashboard page (dark theme, auto-reload)
├── start_dashboard.bat  # one-click launcher (creates .venv on first run)
├── requirements.txt
└── README.md
```
