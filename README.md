# Stock Scanner Dashboard

A Streamlit dashboard for stock screening, technical analysis, smart money flow, backtesting, and US options checklist.

## Features

- US and Malaysia stock scanner
- Dynamic active stock ranking by recent traded value
- KLCI 30, Top 50, active stock, and custom ticker screening
- Technical indicators:
  - MA20, MA50, MA200
  - RSI
  - MACD
  - Bollinger Bands
  - ADX
  - ATR
  - Support and resistance
  - Relative volume
  - Relative strength
- Money flow indicators:
  - CMF
  - MFI
  - OBV Change
  - Smart Money Flow Score
  - Buy/Sell Pressure
- Buy/Sell Safety label
- Practical Rank Score
- Backtest strategy page
- US options checklist page
- Technical chart page

## Important Disclaimer

This app is for education and screening only. It is not financial advice.

No indicator or scanner can guarantee future price movement.

## Files Needed

Your GitHub repository should contain:

```text
app.py
requirements.txt
README.md
```

## How to Run Locally

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Run the app:

```bash
python -m streamlit run app.py
```

## Deploy to Streamlit Community Cloud

When deploying on Streamlit Community Cloud, use:

```text
Repository: your-github-username/your-repository-name
Branch: main
Main file path: app.py
```

Example:

```text
Repository: phang8908/stock-dashboard
Branch: main
Main file path: app.py
```

## Optional API Keys

The app can work with Yahoo Finance without API keys.

If you want to use extra fallback providers, add secrets in Streamlit Cloud:

```toml
EODHD_API_KEY = "your_key_here"
ITICK_API_KEY = "your_key_here"
ALPHAVANTAGE_API_KEY = "your_key_here"
```

If you do not have these keys, the app will skip those providers.

## Data Notes

- US stocks use Yahoo Finance first, with fallback providers if configured.
- Malaysia `.KL` stocks mainly use Yahoo Finance.
- US options checklist only supports US-listed stocks.
- Malaysia stocks do not use the US options chain page.
- Active stock lists are ranked by recent average traded value: `Close × Volume`.

## Suggested First Test

Try Page 1 with:

```text
Market: US
Stock universe: Active Stocks
```

Try Page 4 with:

```text
Market: US
Ticker: TSLA
Chart period: 1y
```

Try Malaysia with:

```text
Market: Malaysia
Ticker: 1155.KL
Chart period: 1y
```
