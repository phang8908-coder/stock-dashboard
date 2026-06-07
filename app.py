
import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import requests
from datetime import datetime, timedelta

# ============================================================
# App Config
# ============================================================

st.set_page_config(
    page_title="Market Beast Pro Scanner",
    page_icon="📊",
    layout="wide"
)

st.markdown(
    """
    <style>
    .main {
        background-color: #0F172A;
    }
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
    }
    h1, h2, h3 {
        color: #F8FAFC;
    }
    .stMetric {
        background: #111827;
        padding: 12px;
        border-radius: 12px;
        border: 1px solid #1F2937;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ============================================================
# Helpers
# ============================================================

def get_secret_value(key_name, default=None):
    try:
        if key_name in st.secrets:
            return st.secrets[key_name]
    except Exception:
        pass
    return default


def safe_float(x, default=None):
    try:
        if x is None:
            return default
        if pd.isna(x):
            return default
        return float(x)
    except Exception:
        return default


def safe_int(x, default=None):
    try:
        if x is None:
            return default
        if pd.isna(x):
            return default
        return int(x)
    except Exception:
        return default


def fmt_price(x):
    val = safe_float(x)
    if val is None:
        return "Unavailable"
    return f"{val:.2f}"


def fmt_pct(x):
    val = safe_float(x)
    if val is None:
        return "Unavailable"
    return f"{val * 100:.2f}%"


def fmt_num(x):
    val = safe_float(x)
    if val is None:
        return "-"
    if abs(val) >= 1_000_000_000:
        return f"{val / 1_000_000_000:.2f}B"
    if abs(val) >= 1_000_000:
        return f"{val / 1_000_000:.2f}M"
    if abs(val) >= 1_000:
        return f"{val / 1_000:.2f}K"
    return f"{val:.2f}"


def render_header(title, subtitle=None):
    st.markdown(f"## {title}")
    if subtitle:
        st.caption(subtitle)


# ============================================================
# Ticker Alias
# ============================================================

US_TICKER_ALIASES = {
    "TESLA": "TSLA",
    "NVIDIA": "NVDA",
    "APPLE": "AAPL",
    "MICROSOFT": "MSFT",
    "AMAZON": "AMZN",
    "GOOGLE": "GOOGL",
    "ALPHABET": "GOOGL",
    "META": "META",
    "FACEBOOK": "META",
    "ASANA": "ASAN",
    "SNAPCHAT": "SNAP",
    "PALANTIR": "PLTR",
    "COINBASE": "COIN",
    "MICROSTRATEGY": "MSTR",
}

MALAYSIA_TICKER_ALIASES = {
    "MAYBANK": "1155.KL",
    "CIMB": "1023.KL",
    "PBBANK": "1295.KL",
    "PUBLICBANK": "1295.KL",
    "TENAGA": "5347.KL",
    "TNB": "5347.KL",
    "CDB": "6947.KL",
    "CELCOMDIGI": "6947.KL",
    "MAXIS": "6012.KL",
    "TM": "4863.KL",
    "DNEX": "4456.KL",
    "DAGANG": "4456.KL",
    "TOPGLOV": "7113.KL",
    "HARTA": "5168.KL",
    "KOSSAN": "7153.KL",
    "SUPERMX": "7106.KL",
    "FRONTKEN": "0128.KL",
    "FRONTKN": "0128.KL",
    "VITROX": "0097.KL",
    "INARI": "0166.KL",
    "MPI": "3867.KL",
    "GREATEC": "0208.KL",
    "UWC": "5292.KL",
    "PENTA": "7160.KL",
    "DIALOG": "7277.KL",
    "HIBISCUS": "5199.KL",
    "HIBISCS": "5199.KL",
    "ARMADA": "5210.KL",
    "BUMIARMADA": "5210.KL",
    "GAMUDA": "5398.KL",
    "SUNWAY": "5211.KL",
    "IJM": "3336.KL",
    "MRDIY": "5296.KL",
    "GENM": "4715.KL",
    "GENTING": "3182.KL",
    "CAPITALA": "5099.KL",
}

SINGAPORE_TICKER_ALIASES = {
    "DBS": "D05.SI",
    "OCBC": "O39.SI",
    "UOB": "U11.SI",
    "SINGTEL": "Z74.SI",
    "SIA": "C6L.SI",
    "SGX": "S68.SI",
    "KEPPEL": "BN4.SI",
    "WILMAR": "F34.SI",
    "SATS": "S58.SI",
    "SEMBCORP": "U96.SI",
    "STENGINEERING": "S63.SI",
    "STE": "S63.SI",
}

STOCK_NAME_MAP = {
    "TSLA": "Tesla",
    "NVDA": "Nvidia",
    "AAPL": "Apple",
    "MSFT": "Microsoft",
    "AMZN": "Amazon",
    "GOOGL": "Alphabet",
    "META": "Meta Platforms",
    "ASAN": "Asana",
    "SNAP": "Snap",
    "PLTR": "Palantir",
    "COIN": "Coinbase",
    "MSTR": "MicroStrategy",
    "AMD": "AMD",
    "1155.KL": "Maybank",
    "1023.KL": "CIMB",
    "1295.KL": "Public Bank",
    "5347.KL": "Tenaga Nasional",
    "6947.KL": "CelcomDigi",
    "4863.KL": "Telekom Malaysia",
    "4456.KL": "DNEX",
    "7113.KL": "Top Glove",
    "5168.KL": "Hartalega",
    "0128.KL": "Frontken",
    "0097.KL": "Vitrox",
    "0166.KL": "Inari",
    "5398.KL": "Gamuda",
    "5211.KL": "Sunway",
    "5296.KL": "Mr DIY",
    "D05.SI": "DBS",
    "O39.SI": "OCBC",
    "U11.SI": "UOB",
    "Z74.SI": "Singtel",
    "C6L.SI": "Singapore Airlines",
    "S68.SI": "SGX",
    "BN4.SI": "Keppel",
    "F34.SI": "Wilmar",
}


def normalize_user_ticker(raw_ticker, market_name):
    ticker = str(raw_ticker).strip().upper().replace(" ", "").replace("_", "-")
    if not ticker:
        return ""

    if ticker in US_TICKER_ALIASES:
        return US_TICKER_ALIASES[ticker]

    if market_name == "Malaysia":
        ticker = ticker.replace(".KLSE", ".KL")
        if ticker in MALAYSIA_TICKER_ALIASES:
            return MALAYSIA_TICKER_ALIASES[ticker]
        if ticker.isdigit():
            return f"{ticker}.KL"
        if ticker.endswith(".KL"):
            return ticker
        return ticker

    if market_name == "Singapore":
        if ticker in SINGAPORE_TICKER_ALIASES:
            return SINGAPORE_TICKER_ALIASES[ticker]
        if ticker.endswith(".SI"):
            return ticker
        return f"{ticker}.SI"

    return ticker.replace(".", "-")


def detect_market_from_ticker(raw_ticker, selected_market="US"):
    t = str(raw_ticker).strip().upper().replace(" ", "")
    if t.endswith(".KL") or t.isdigit() or t in MALAYSIA_TICKER_ALIASES:
        return "Malaysia"
    if t.endswith(".SI") or t in SINGAPORE_TICKER_ALIASES:
        return "Singapore"
    if t in US_TICKER_ALIASES:
        return "US"
    return selected_market


def get_stock_name(ticker):
    ticker = str(ticker).strip().upper()
    if ticker in STOCK_NAME_MAP:
        return STOCK_NAME_MAP[ticker]
    return ticker.replace(".KL", "").replace(".SI", "")


def parse_ticker_text(text_input, market_name):
    items = []
    for line in str(text_input).splitlines():
        for part in line.split(","):
            if part.strip():
                items.append(normalize_user_ticker(part, market_name))
    return list(dict.fromkeys(items))


# ============================================================
# Data Providers
# ============================================================

def _normalize_ohlcv(df, min_rows=30):
    if df is None or df.empty:
        return None

    data = df.copy()
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    required = ["Open", "High", "Low", "Close", "Volume"]
    for col in required:
        if col not in data.columns:
            return None

    data = data[required].dropna(subset=["Close"])
    if len(data) < min_rows:
        return None

    return data


@st.cache_data(ttl=3600)
def get_data_yahoo(ticker, period="2y", interval="1d", min_rows=30):
    try:
        df = yf.download(
            ticker,
            period=period,
            interval=interval,
            auto_adjust=True,
            progress=False,
            threads=False
        )
        return _normalize_ohlcv(df, min_rows=min_rows)
    except Exception:
        return None


def convert_to_eodhd_symbol(ticker, market_name):
    t = str(ticker).strip().upper()
    if market_name == "Malaysia" and t.endswith(".KL"):
        return t.replace(".KL", ".KLSE")
    if market_name == "Singapore" and t.endswith(".SI"):
        return t.replace(".SI", ".SG")
    return t


@st.cache_data(ttl=3600)
def get_data_eodhd(ticker, period="2y", interval="1d", min_rows=30, market_name="US"):
    api_key = get_secret_value("EODHD_API_KEY")
    if not api_key:
        return None

    if interval != "1d":
        return None

    try:
        symbol = convert_to_eodhd_symbol(ticker, market_name)
        end = datetime.utcnow().date()
        start = end - timedelta(days=800 if period == "2y" else 400)

        url = f"https://eodhd.com/api/eod/{symbol}"
        params = {
            "api_token": api_key,
            "fmt": "json",
            "from": str(start),
            "to": str(end),
            "period": "d",
        }
        r = requests.get(url, params=params, timeout=15)
        if r.status_code != 200:
            return None

        data = r.json()
        if not isinstance(data, list) or not data:
            return None

        df = pd.DataFrame(data)
        rename = {
            "open": "Open",
            "high": "High",
            "low": "Low",
            "close": "Close",
            "volume": "Volume",
            "date": "Date",
        }
        df = df.rename(columns=rename)
        if "Date" in df.columns:
            df["Date"] = pd.to_datetime(df["Date"])
            df = df.set_index("Date")
        return _normalize_ohlcv(df, min_rows=min_rows)
    except Exception:
        return None


@st.cache_data(ttl=3600)
def get_data_stooq(ticker, period="2y", interval="1d", min_rows=30):
    if interval != "1d":
        return None
    try:
        t = str(ticker).lower().replace("-", "-")
        if "." in t:
            return None
        url = f"https://stooq.com/q/d/l/?s={t}.us&i=d"
        df = pd.read_csv(url)
        if df is None or df.empty:
            return None
        df["Date"] = pd.to_datetime(df["Date"])
        df = df.set_index("Date")
        return _normalize_ohlcv(df, min_rows=min_rows)
    except Exception:
        return None


@st.cache_data(ttl=3600)
def get_data_alphavantage(ticker, period="2y", interval="1d", min_rows=30, market_name="US"):
    api_key = get_secret_value("ALPHAVANTAGE_API_KEY")
    if not api_key or market_name != "US" or interval != "1d":
        return None

    try:
        url = "https://www.alphavantage.co/query"
        params = {
            "function": "TIME_SERIES_DAILY_ADJUSTED",
            "symbol": ticker,
            "outputsize": "full",
            "apikey": api_key,
        }
        r = requests.get(url, params=params, timeout=15)
        data = r.json()
        ts = data.get("Time Series (Daily)")
        if not ts:
            return None
        df = pd.DataFrame(ts).T
        df.index = pd.to_datetime(df.index)
        df = df.rename(columns={
            "1. open": "Open",
            "2. high": "High",
            "3. low": "Low",
            "5. adjusted close": "Close",
            "6. volume": "Volume",
        })
        df = df[["Open", "High", "Low", "Close", "Volume"]].astype(float).sort_index()
        return _normalize_ohlcv(df, min_rows=min_rows)
    except Exception:
        return None


@st.cache_data(ttl=3600)
def get_data(ticker, period="2y", interval="1d", min_rows=30, market_name="US"):
    # Priority: EODHD -> Yahoo -> Stooq US -> Alpha Vantage US
    df = get_data_eodhd(ticker, period, interval, min_rows, market_name)
    if df is not None:
        return df

    df = get_data_yahoo(ticker, period, interval, min_rows)
    if df is not None:
        return df

    if market_name == "US":
        df = get_data_stooq(ticker, period, interval, min_rows)
        if df is not None:
            return df

        df = get_data_alphavantage(ticker, period, interval, min_rows, market_name)
        if df is not None:
            return df

    return None


# ============================================================
# Indicators and Scoring
# ============================================================

def add_indicators(df):
    if df is None or df.empty:
        return None

    data = df.copy()

    data["MA20"] = data["Close"].rolling(20).mean()
    data["MA50"] = data["Close"].rolling(50).mean()
    data["MA200"] = data["Close"].rolling(200).mean()

    delta = data["Close"].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    rs = gain / loss.replace(0, np.nan)
    data["RSI"] = 100 - (100 / (1 + rs))

    ema12 = data["Close"].ewm(span=12, adjust=False).mean()
    ema26 = data["Close"].ewm(span=26, adjust=False).mean()
    data["MACD"] = ema12 - ema26
    data["Signal"] = data["MACD"].ewm(span=9, adjust=False).mean()
    data["MACD_Hist"] = data["MACD"] - data["Signal"]
    data["MACD_Hist_Change"] = data["MACD_Hist"].diff()

    data["Volume_Avg20"] = data["Volume"].rolling(20).mean()
    data["Relative_Volume"] = data["Volume"] / data["Volume_Avg20"]

    data["Support"] = data["Low"].rolling(20).min()
    data["Resistance"] = data["High"].rolling(20).max()

    high_low = data["High"] - data["Low"]
    high_close = (data["High"] - data["Close"].shift()).abs()
    low_close = (data["Low"] - data["Close"].shift()).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    data["ATR"] = tr.rolling(14).mean()

    # ADX simplified
    plus_dm = data["High"].diff()
    minus_dm = -data["Low"].diff()
    plus_dm = plus_dm.where((plus_dm > minus_dm) & (plus_dm > 0), 0)
    minus_dm = minus_dm.where((minus_dm > plus_dm) & (minus_dm > 0), 0)
    plus_di = 100 * (plus_dm.rolling(14).mean() / data["ATR"])
    minus_di = 100 * (minus_dm.rolling(14).mean() / data["ATR"])
    dx = (abs(plus_di - minus_di) / (plus_di + minus_di).replace(0, np.nan)) * 100
    data["ADX"] = dx.rolling(14).mean()

    # CMF and smart-money score
    mf_multiplier = ((data["Close"] - data["Low"]) - (data["High"] - data["Close"])) / (data["High"] - data["Low"]).replace(0, np.nan)
    mf_volume = mf_multiplier * data["Volume"]
    data["CMF"] = mf_volume.rolling(20).sum() / data["Volume"].rolling(20).sum()

    typical = (data["High"] + data["Low"] + data["Close"]) / 3
    money_flow = typical * data["Volume"]
    pos_flow = money_flow.where(typical > typical.shift(), 0).rolling(14).sum()
    neg_flow = money_flow.where(typical < typical.shift(), 0).rolling(14).sum()
    mfr = pos_flow / neg_flow.replace(0, np.nan)
    data["MFI"] = 100 - (100 / (1 + mfr))

    data["Smart_Money_Score"] = (
        data["CMF"].fillna(0) * 10
        + (data["Relative_Volume"].fillna(1) - 1) * 3
        + np.sign(data["MACD_Hist_Change"].fillna(0)) * 2
    )

    return data


def calculate_relative_strength(stock_df, benchmark_df):
    try:
        if stock_df is None or benchmark_df is None:
            return None
        stock_ret = stock_df["Close"].pct_change(60).iloc[-1]
        bench_ret = benchmark_df["Close"].pct_change(60).iloc[-1]
        return stock_ret - bench_ret
    except Exception:
        return None


def get_smart_money_signal(score):
    score = safe_float(score, 0)
    if score >= 5:
        return "Strong Buying Pressure"
    if score >= 2:
        return "Buying Pressure"
    if score <= -5:
        return "Strong Selling Pressure"
    if score <= -2:
        return "Selling Pressure"
    return "Neutral"


def get_buy_sell_safety(base_score, practical_score, rsi, risk_reward):
    base_score = safe_float(base_score, 0)
    practical_score = safe_float(practical_score, 0)
    rsi = safe_float(rsi, 50)
    risk_reward = safe_float(risk_reward, 0)

    if rsi > 78:
        return "Too Hot / Avoid Chasing"
    if base_score >= 12 and practical_score >= 22 and risk_reward >= 1.5:
        return "Safer Buy Setup"
    if base_score >= 8 and practical_score >= 14:
        return "Watch Buy Setup"
    if base_score <= 3 or practical_score <= 6:
        return "Sell / Avoid Warning"
    return "Neutral / Wait"


def get_final_view(score):
    score = safe_float(score, 0)
    if score >= 15:
        return "Strong"
    if score >= 9:
        return "Positive"
    if score >= 5:
        return "Neutral"
    return "Weak"


def get_benchmark_data(market_name):
    if market_name == "Malaysia":
        candidates = ["^KLSE", "1155.KL"]
    elif market_name == "Singapore":
        candidates = ["^STI", "D05.SI"]
    else:
        candidates = ["SPY", "VOO", "QQQ"]

    for ticker in candidates:
        df = get_data(ticker, period="2y", interval="1d", min_rows=120, market_name=market_name)
        if df is not None:
            return ticker, add_indicators(df)
    return None, None


def analyse_stock(ticker, market_name, benchmark_df=None):
    raw = get_data(ticker, period="2y", interval="1d", min_rows=80, market_name=market_name)
    if raw is None:
        return None

    df = add_indicators(raw)
    if df is None or df.empty:
        return None

    latest = df.iloc[-1]
    close = safe_float(latest.get("Close"))
    rsi = safe_float(latest.get("RSI"))
    ma20 = safe_float(latest.get("MA20"))
    ma50 = safe_float(latest.get("MA50"))
    ma200 = safe_float(latest.get("MA200"))
    macd_hist = safe_float(latest.get("MACD_Hist"))
    macd_hist_change = safe_float(latest.get("MACD_Hist_Change"))
    rel_volume = safe_float(latest.get("Relative_Volume"))
    adx = safe_float(latest.get("ADX"))
    support = safe_float(latest.get("Support"))
    resistance = safe_float(latest.get("Resistance"))
    atr = safe_float(latest.get("ATR"))
    cmf = safe_float(latest.get("CMF"))
    mfi = safe_float(latest.get("MFI"))
    smart_score = safe_float(latest.get("Smart_Money_Score"), 0)

    if close is None:
        return None

    base_score = 0
    practical_score = 0

    if ma20 and close > ma20:
        base_score += 2
        practical_score += 2
    if ma50 and close > ma50:
        base_score += 3
        practical_score += 3
    if ma200 and close > ma200:
        base_score += 3
        practical_score += 2

    if rsi is not None:
        if 45 <= rsi <= 65:
            base_score += 3
            practical_score += 5
        elif 35 <= rsi < 45:
            practical_score += 2
        elif rsi > 75:
            practical_score -= 3
        elif rsi < 30:
            base_score -= 2

    if macd_hist is not None and macd_hist > 0:
        base_score += 3
        practical_score += 3
    if macd_hist_change is not None and macd_hist_change > 0:
        base_score += 2
        practical_score += 2

    if rel_volume is not None:
        if rel_volume >= 1.5:
            base_score += 3
            practical_score += 4
        elif rel_volume >= 1.1:
            base_score += 1
            practical_score += 2

    if adx is not None:
        if adx >= 25:
            base_score += 3
            practical_score += 3
        elif adx >= 18:
            practical_score += 1

    if cmf is not None:
        if cmf > 0.1:
            base_score += 2
            practical_score += 2
        elif cmf < -0.1:
            base_score -= 2
            practical_score -= 2

    if mfi is not None:
        if 45 <= mfi <= 75:
            practical_score += 2
        elif mfi > 85:
            practical_score -= 2

    relative_strength = calculate_relative_strength(df, benchmark_df)
    if relative_strength is not None:
        if relative_strength > 0.05:
            base_score += 3
        elif relative_strength > 0:
            base_score += 1
        elif relative_strength < -0.05:
            base_score -= 2

    risk_reward = None
    upside_pct = None
    risk_pct = None

    if support and resistance and close and close > support:
        upside = resistance - close
        downside = close - support
        if downside > 0:
            risk_reward = upside / downside
            upside_pct = upside / close * 100
            risk_pct = downside / close * 100
            if risk_reward >= 2:
                practical_score += 4
            elif risk_reward >= 1:
                practical_score += 2
            elif risk_reward < 0.7:
                practical_score -= 2

    base_score = int(max(0, min(30, round(base_score))))
    practical_score = int(max(0, min(40, round(practical_score))))

    buy_sell_safety = get_buy_sell_safety(base_score, practical_score, rsi, risk_reward)
    smart_signal = get_smart_money_signal(smart_score)

    price_decimal = 3 if market_name in ["Malaysia", "Singapore"] else 2

    return {
        "Ticker": ticker,
        "Stock Name": get_stock_name(ticker),
        "Close": round(close, price_decimal),
        "Base Score": base_score,
        "Practical Score": practical_score,
        "Buy/Sell Safety": buy_sell_safety,
        "Final View": get_final_view(base_score),
        "Smart Money": smart_signal,
        "Support": round(support, price_decimal) if support else None,
        "Resistance": round(resistance, price_decimal) if resistance else None,
        "Risk/Reward": round(risk_reward, 2) if risk_reward is not None else None,
        "Upside %": round(upside_pct, 2) if upside_pct is not None else None,
        "Risk %": round(risk_pct, 2) if risk_pct is not None else None,
        "RSI": round(rsi, 2) if rsi is not None else None,
        "ADX": round(adx, 2) if adx is not None else None,
        "Rel Volume": round(rel_volume, 2) if rel_volume is not None else None,
    }


def calculate_technical_score(ticker, market_name):
    result = analyse_stock(ticker, market_name, benchmark_df=None)
    if result is None:
        return None
    score = 0
    score += min(30, safe_float(result.get("Base Score"), 0))
    score += min(30, safe_float(result.get("Practical Score"), 0) * 0.75)
    score += 10 if result.get("Smart Money") in ["Buying Pressure", "Strong Buying Pressure"] else 0
    return int(max(0, min(100, round(score))))


# ============================================================
# Fundamental Data and Research Score
# ============================================================

@st.cache_data(ttl=3600)
def get_yfinance_info(ticker, market_name=None):
    info = {}
    try:
        tk = yf.Ticker(ticker)
        info = tk.info or {}
    except Exception:
        info = {}

    # FMP quote/profile enrichment
    fmp_key = get_secret_value("FMP_API_KEY")
    if not fmp_key:
        info["fundamentalDataSource"] = "Yahoo fallback"
        return info

    try:
        symbol = ticker
        quote_url = f"https://financialmodelingprep.com/api/v3/quote/{symbol}"
        quote = requests.get(quote_url, params={"apikey": fmp_key}, timeout=15).json()
        if isinstance(quote, list) and quote:
            q = quote[0]
            if q.get("price") is not None:
                info["currentPrice"] = q.get("price")
            if q.get("marketCap") is not None:
                info["marketCap"] = q.get("marketCap")
            if q.get("pe") is not None:
                info["trailingPE"] = q.get("pe")

        profile_url = f"https://financialmodelingprep.com/api/v3/profile/{symbol}"
        profile = requests.get(profile_url, params={"apikey": fmp_key}, timeout=15).json()
        if isinstance(profile, list) and profile:
            p = profile[0]
            info["longName"] = p.get("companyName") or info.get("longName")
            info["sector"] = p.get("sector") or info.get("sector")
            info["industry"] = p.get("industry") or info.get("industry")
            info["longBusinessSummary"] = p.get("description") or info.get("longBusinessSummary")
        info["fundamentalDataSource"] = "FMP + Yahoo fallback"
    except Exception:
        info["fundamentalDataSource"] = "Yahoo fallback"

    return info


@st.cache_data(ttl=3600)
def get_yfinance_financials(ticker):
    try:
        tk = yf.Ticker(ticker)
        return tk.financials, tk.balance_sheet, tk.cashflow
    except Exception:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()


def get_statement_value(df, possible_rows, col_index=0):
    if df is None or df.empty:
        return None
    for row in possible_rows:
        if row in df.index:
            try:
                return safe_float(df.loc[row].iloc[col_index])
            except Exception:
                return None
    return None


def calculate_growth(df, rows):
    if df is None or df.empty or len(df.columns) < 2:
        return None
    for row in rows:
        if row in df.index:
            latest = safe_float(df.loc[row].iloc[0])
            previous = safe_float(df.loc[row].iloc[1])
            if latest is not None and previous not in [None, 0]:
                return (latest - previous) / abs(previous)
    return None


def calculate_research_score(ticker, market_name):
    info = get_yfinance_info(ticker, market_name)
    financials, balance_sheet, cashflow = get_yfinance_financials(ticker)

    revenue_growth = calculate_growth(financials, ["Total Revenue", "Operating Revenue"])
    earnings_growth = calculate_growth(financials, ["Net Income", "Net Income Common Stockholders"])
    fcf = get_statement_value(cashflow, ["Free Cash Flow", "Operating Cash Flow"], 0)

    pe = safe_float(info.get("trailingPE"))
    forward_pe = safe_float(info.get("forwardPE"))
    price_to_book = safe_float(info.get("priceToBook"))
    total_debt = safe_float(info.get("totalDebt"), 0)
    total_cash = safe_float(info.get("totalCash"), 0)
    market_cap = safe_float(info.get("marketCap"))

    score = 0
    notes = []

    if revenue_growth is None:
        score += 8
        notes.append("Revenue data incomplete")
    elif revenue_growth >= 0.25:
        score += 20
    elif revenue_growth >= 0.10:
        score += 16
    elif revenue_growth >= 0.03:
        score += 11
    elif revenue_growth >= 0:
        score += 7
    else:
        score += 3

    if earnings_growth is None:
        score += 8
        notes.append("Earnings data incomplete")
    elif earnings_growth >= 0.30:
        score += 20
    elif earnings_growth >= 0.12:
        score += 16
    elif earnings_growth >= 0.03:
        score += 11
    elif earnings_growth >= 0:
        score += 7
    else:
        score += 3

    if fcf is None:
        score += 6
    elif fcf > 0:
        score += 15
    else:
        score += 3

    if total_cash >= total_debt and (total_cash > 0 or total_debt > 0):
        score += 10
    elif market_cap and total_debt / market_cap < 0.15:
        score += 8
    elif market_cap and total_debt / market_cap < 0.35:
        score += 6
    else:
        score += 4

    valuation = 7
    if forward_pe and forward_pe > 0:
        valuation = 14 if forward_pe <= 15 else 10 if forward_pe <= 30 else 5
    elif pe and pe > 0:
        valuation = 13 if pe <= 15 else 9 if pe <= 30 else 5
    elif price_to_book and price_to_book > 0:
        valuation = 12 if price_to_book <= 1.5 else 8 if price_to_book <= 4 else 5

    score += valuation

    normalized = int(max(0, min(100, round(score / 72 * 100))))

    metrics = {
        "longName": info.get("longName"),
        "sector": info.get("sector"),
        "industry": info.get("industry"),
        "summary": info.get("longBusinessSummary"),
        "currentPrice": safe_float(info.get("currentPrice") or info.get("regularMarketPrice")),
        "marketCap": market_cap,
        "pe": pe,
        "forwardPE": forward_pe,
        "priceToBook": price_to_book,
        "revenueGrowth": revenue_growth,
        "earningsGrowth": earnings_growth,
        "freeCashFlow": fcf,
        "totalDebt": total_debt,
        "totalCash": total_cash,
        "dataSource": info.get("fundamentalDataSource", "Yahoo fallback"),
    }

    risk = "Low"
    if earnings_growth is not None and earnings_growth < 0:
        risk = "Medium"
    if fcf is not None and fcf < 0:
        risk = "High"
    if total_debt > total_cash * 2 and total_debt > 0:
        risk = "High"

    return normalized, risk, metrics, notes


def research_rating(score, risk):
    if score >= 75 and risk != "High":
        return "Buy / Accumulate"
    if score >= 60:
        return "Hold / Watchlist"
    if score >= 45:
        return "Neutral / Selective"
    return "Avoid / High Caution"


# ============================================================
# Portfolio Dynamic Score
# ============================================================

def entry_timing_score(scanner_result):
    if scanner_result is None:
        return 0

    score = 0
    safety = scanner_result.get("Buy/Sell Safety", "")
    practical = safe_float(scanner_result.get("Practical Score"), 0)
    base = safe_float(scanner_result.get("Base Score"), 0)
    rsi = safe_float(scanner_result.get("RSI"))
    rr = safe_float(scanner_result.get("Risk/Reward"))

    if safety == "Safer Buy Setup":
        score += 30
    elif safety == "Watch Buy Setup":
        score += 22
    elif "Avoid" in safety or "Sell" in safety:
        score += 3
    else:
        score += 12

    score += min(25, practical)
    score += min(15, base)

    if rr is not None:
        if rr >= 3:
            score += 15
        elif rr >= 2:
            score += 10
        elif rr >= 1:
            score += 5
        else:
            score -= 5

    if rsi is not None:
        if 45 <= rsi <= 65:
            score += 10
        elif rsi > 75:
            score -= 10

    return int(max(0, min(100, round(score))))


def portfolio_health_score(pl_pct, research_score, timing_score, risk_rating):
    score = safe_float(research_score, 50) * 0.45 + safe_float(timing_score, 50) * 0.35

    if pl_pct is None:
        score += 10
    elif pl_pct >= 20:
        score += 15
    elif pl_pct >= 10:
        score += 12
    elif pl_pct >= 0:
        score += 8
    elif pl_pct <= -10:
        score -= 10
    else:
        score -= 3

    if risk_rating == "Low":
        score += 5
    elif risk_rating == "High":
        score -= 12

    return int(max(0, min(100, round(score))))


def portfolio_action(score):
    if score >= 80:
        return "Strong Hold / Add on Pullback"
    if score >= 65:
        return "Healthy Hold"
    if score >= 50:
        return "Monitor / Selective"
    if score >= 35:
        return "Weak / Review"
    return "High Risk / Avoid Add"


# ============================================================
# Universes
# ============================================================

US_UNIVERSE = [
    "AAPL", "MSFT", "NVDA", "TSLA", "AMZN", "GOOGL", "META", "AMD", "NFLX",
    "AVGO", "JPM", "V", "MA", "COST", "WMT", "HD", "PLTR", "COIN", "MSTR",
    "ASAN", "SNAP", "SOFI", "HOOD", "RIVN", "UBER"
]

MALAYSIA_UNIVERSE = [
    "1155.KL", "1023.KL", "1295.KL", "5347.KL", "6947.KL", "4863.KL",
    "4456.KL", "7113.KL", "5168.KL", "0128.KL", "0097.KL", "0166.KL",
    "5398.KL", "5211.KL", "5296.KL", "7277.KL", "5199.KL", "5210.KL"
]

SINGAPORE_UNIVERSE = [
    "D05.SI", "O39.SI", "U11.SI", "Z74.SI", "C6L.SI", "S68.SI",
    "BN4.SI", "F34.SI", "S58.SI", "U96.SI"
]


def get_default_universe(market_name):
    if market_name == "Malaysia":
        return MALAYSIA_UNIVERSE
    if market_name == "Singapore":
        return SINGAPORE_UNIVERSE
    return US_UNIVERSE


# ============================================================
# Table Styling
# ============================================================

def style_score_table(df):
    if df is None or df.empty:
        return df

    def color_score(val):
        val = safe_float(val)
        if val is None:
            return ""
        if val >= 80:
            return "color: #22C55E; font-weight: 900;"
        if val >= 65:
            return "color: #4ADE80; font-weight: 900;"
        if val >= 50:
            return "color: #38BDF8; font-weight: 800;"
        if val >= 35:
            return "color: #F59E0B; font-weight: 800;"
        return "color: #EF4444; font-weight: 900;"

    def color_action(val):
        val = str(val)
        if "Strong" in val or "Healthy" in val or "Buy" in val:
            return "background-color: #14532D; color: #DCFCE7; font-weight: 900;"
        if "Monitor" in val or "Neutral" in val or "Watch" in val:
            return "background-color: #1E3A8A; color: #DBEAFE; font-weight: 900;"
        if "Weak" in val or "Avoid" in val or "Sell" in val:
            return "background-color: #7F1D1D; color: #FEE2E2; font-weight: 900;"
        return ""

    styled = df.style

    for col in ["Base Score", "Practical Score", "Research Score", "Portfolio Health Score", "Entry Timing Score"]:
        if col in df.columns:
            styled = styled.map(color_score, subset=[col])

    for col in ["Buy/Sell Safety", "Action", "Final View"]:
        if col in df.columns:
            styled = styled.map(color_action, subset=[col])

    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    return styled.format({c: "{:,.2f}" for c in numeric_cols}, na_rep="-")


# ============================================================
# Sidebar
# ============================================================

st.sidebar.title("📊 Market Beast Pro")

st.sidebar.markdown("### Data Providers")
st.sidebar.caption(("✅" if get_secret_value("EODHD_API_KEY") else "⚠️") + " EODHD")
st.sidebar.caption(("✅" if get_secret_value("FMP_API_KEY") else "⚠️") + " FMP")
st.sidebar.caption(("✅" if get_secret_value("ALPHAVANTAGE_API_KEY") else "⚠️") + " Alpha Vantage")
st.sidebar.caption("✅ Yahoo fallback")
st.sidebar.caption("✅ Stooq US fallback")

page = st.sidebar.radio(
    "Choose Module",
    [
        "Page 1 - Market Scanner",
        "Page 2 - Research Analyzer",
        "Page 3 - Portfolio Review",
    ]
)

# ============================================================
# Page 1 - Market Scanner
# ============================================================

if page == "Page 1 - Market Scanner":
    render_header(
        "Page 1 — Market Scanner",
        "Find potential candidates using price trend, volume, smart money, support/resistance and risk/reward."
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        market = st.selectbox("Market", ["US", "Malaysia", "Singapore"])

    with col2:
        mode = st.selectbox("Stock Universe", ["Default Universe", "Custom"])

    with col3:
        max_scan = st.slider("Max stocks to scan", 5, 80, 25)

    if mode == "Custom":
        custom_text = st.text_area(
            "Enter tickers / names",
            "TSLA,NVDA,ASAN" if market == "US" else "DNEX,4456,MAYBANK"
        )
        tickers = parse_ticker_text(custom_text, market)
    else:
        tickers = get_default_universe(market)

    tickers = tickers[:max_scan]

    if st.button("Run Scanner", type="primary"):
        bench_name, benchmark_df = get_benchmark_data(market)
        if benchmark_df is None:
            st.warning("Benchmark unavailable. Scanner will still run without relative strength.")

        results = []
        progress = st.progress(0)

        for i, ticker in enumerate(tickers):
            progress.progress((i + 1) / len(tickers))
            result = analyse_stock(ticker, market, benchmark_df)
            if result:
                results.append(result)

        if not results:
            st.error("No scanner data returned. Check ticker format or data provider.")
        else:
            df = pd.DataFrame(results)
            df = df.sort_values(["Practical Score", "Base Score"], ascending=False)

            df["Stock"] = df["Ticker"] + " | " + df["Stock Name"]
            df = df.set_index("Stock")
            df = df.drop(columns=["Ticker", "Stock Name"], errors="ignore")

            st.subheader("Scanner Result")
            st.dataframe(style_score_table(df), use_container_width=True, height=560)

            csv = df.reset_index().to_csv(index=False).encode("utf-8")
            st.download_button("Download Scanner CSV", csv, "scanner_result.csv", "text/csv")

# ============================================================
# Page 2 - Research Analyzer
# ============================================================

if page == "Page 2 - Research Analyzer":
    render_header(
        "Page 2 — Research Analyzer",
        "Analyze one stock using business quality, fundamentals, valuation, debt strength and technical timing."
    )

    col1, col2 = st.columns(2)

    with col1:
        market = st.selectbox("Market", ["US", "Malaysia", "Singapore"], key="research_market")

    with col2:
        default_ticker = "TSLA" if market == "US" else ("DNEX" if market == "Malaysia" else "DBS")
        raw_ticker = st.text_input("Ticker / stock name", default_ticker)

    ticker = normalize_user_ticker(raw_ticker, market)

    if st.button("Run Research Analyzer", type="primary"):
        research_score, risk_rating, metrics, notes = calculate_research_score(ticker, market)
        rating = research_rating(research_score, risk_rating)

        bench_name, benchmark_df = get_benchmark_data(market)
        scanner = analyse_stock(ticker, market, benchmark_df)
        tech_score = calculate_technical_score(ticker, market)

        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric("Research Score", f"{research_score}/100")
        with m2:
            st.metric("Rating", rating)
        with m3:
            st.metric("Risk Rating", risk_rating)
        with m4:
            st.metric("Technical Score", tech_score if tech_score is not None else "Unavailable")

        st.subheader(f"{ticker} | {get_stock_name(ticker)}")

        p1, p2, p3, p4 = st.columns(4)
        with p1:
            st.metric("Current Price", fmt_price(metrics.get("currentPrice")))
        with p2:
            st.metric("Market Cap", fmt_num(metrics.get("marketCap")))
        with p3:
            st.metric("PE", fmt_price(metrics.get("pe")))
        with p4:
            st.metric("Data Source", metrics.get("dataSource", "Yahoo fallback"))

        st.subheader("Fundamental Snapshot")
        snap = pd.DataFrame([
            {"Metric": "Revenue Growth", "Value": fmt_pct(metrics.get("revenueGrowth"))},
            {"Metric": "Earnings Growth", "Value": fmt_pct(metrics.get("earningsGrowth"))},
            {"Metric": "Free Cash Flow", "Value": fmt_num(metrics.get("freeCashFlow"))},
            {"Metric": "Total Cash", "Value": fmt_num(metrics.get("totalCash"))},
            {"Metric": "Total Debt", "Value": fmt_num(metrics.get("totalDebt"))},
            {"Metric": "Forward PE", "Value": fmt_price(metrics.get("forwardPE"))},
            {"Metric": "Price / Book", "Value": fmt_price(metrics.get("priceToBook"))},
            {"Metric": "Sector", "Value": metrics.get("sector") or "-"},
            {"Metric": "Industry", "Value": metrics.get("industry") or "-"},
        ])
        st.dataframe(snap, use_container_width=True, hide_index=True)

        if scanner:
            st.subheader("Technical Timing")
            tech_df = pd.DataFrame([{
                "Close": scanner.get("Close"),
                "Base Score": scanner.get("Base Score"),
                "Practical Score": scanner.get("Practical Score"),
                "Buy/Sell Safety": scanner.get("Buy/Sell Safety"),
                "Smart Money": scanner.get("Smart Money"),
                "Support": scanner.get("Support"),
                "Resistance": scanner.get("Resistance"),
                "Risk/Reward": scanner.get("Risk/Reward"),
            }])
            st.dataframe(style_score_table(tech_df), use_container_width=True, hide_index=True)

        st.subheader("Business Summary")
        summary = metrics.get("summary")
        if summary:
            st.write(summary[:1200] + ("..." if len(summary) > 1200 else ""))
        else:
            st.info("Business summary unavailable for this ticker.")

        if notes:
            with st.expander("Data Notes"):
                for note in notes:
                    st.write(f"- {note}")

        st.warning("This is rule-based analysis, not financial advice.")

# ============================================================
# Page 3 - Portfolio Review
# ============================================================

def build_portfolio_from_text(text_input, selected_market):
    rows = []
    for line in str(text_input).splitlines():
        if not line.strip():
            continue

        parts = [p.strip() for p in line.split(",")]
        raw_ticker = parts[0]
        market = detect_market_from_ticker(raw_ticker, selected_market)
        ticker = normalize_user_ticker(raw_ticker, market)
        buy_price = safe_float(parts[1]) if len(parts) >= 2 else None
        qty = safe_float(parts[2]) if len(parts) >= 3 else None

        rows.append({
            "Ticker": ticker,
            "Market": market,
            "Buy Price": buy_price,
            "Quantity": qty,
        })

    return pd.DataFrame(rows)


def review_portfolio(portfolio_df):
    rows = []

    for _, row in portfolio_df.iterrows():
        ticker = row["Ticker"]
        market = row["Market"]
        buy_price = safe_float(row.get("Buy Price"))
        qty = safe_float(row.get("Quantity"))

        bench_name, benchmark_df = get_benchmark_data(market)
        scanner = analyse_stock(ticker, market, benchmark_df)

        latest_price = scanner.get("Close") if scanner else None

        research_score, risk_rating, metrics, notes = calculate_research_score(ticker, market)

        pl_pct = None
        pl_value = None
        pos_value = None

        if latest_price is not None and buy_price is not None and buy_price > 0:
            pl_pct = (latest_price - buy_price) / buy_price * 100
            if qty:
                pl_value = (latest_price - buy_price) * qty
                pos_value = latest_price * qty

        timing = entry_timing_score(scanner)
        health = portfolio_health_score(pl_pct, research_score, timing, risk_rating)
        action = portfolio_action(health)

        rows.append({
            "Ticker": ticker,
            "Stock Name": get_stock_name(ticker),
            "Market": market,
            "Current Price": latest_price,
            "Buy Price": buy_price,
            "P/L %": round(pl_pct, 2) if pl_pct is not None else None,
            "Portfolio Health Score": health,
            "Entry Timing Score": timing,
            "Research Score": research_score,
            "Buy/Sell Safety": scanner.get("Buy/Sell Safety") if scanner else "No data",
            "Action": action,
            "Risk Rating": risk_rating,
            "Smart Money": scanner.get("Smart Money") if scanner else None,
            "Support": scanner.get("Support") if scanner else None,
            "Resistance": scanner.get("Resistance") if scanner else None,
            "Risk/Reward": scanner.get("Risk/Reward") if scanner else None,
            "Position Value": round(pos_value, 2) if pos_value is not None else None,
            "P/L Value": round(pl_value, 2) if pl_value is not None else None,
            "Quantity": qty,
        })

    result = pd.DataFrame(rows)
    if not result.empty:
        result["Stock"] = result["Ticker"] + " | " + result["Stock Name"] + " | " + result["Market"]
        result = result.set_index("Stock")
        result = result.drop(columns=["Ticker", "Stock Name", "Market"], errors="ignore")

    return result


if page == "Page 3 - Portfolio Review":
    render_header(
        "Page 3 — Portfolio Review",
        "Review holdings/watchlist using portfolio health, entry timing, research score, smart money and key support/resistance."
    )

    with st.expander("Score Reference"):
        st.write(
            """
            **Portfolio Health Score**: Main score for current holding/watchlist.  
            **Entry Timing Score**: Whether current setup is suitable to add/buy.  
            **Research Score**: Fundamental/business/valuation score.  
            **Smart Money**: Money-flow buying/selling pressure.  
            **Risk/Reward**: Upside vs downside based on nearby support/resistance.
            """
        )

    col1, col2 = st.columns(2)
    with col1:
        market = st.selectbox("Default Market", ["US", "Malaysia", "Singapore"], key="portfolio_market")
    with col2:
        st.caption("Format: Ticker, Buy Price, Quantity")

    default_text = "TSLA,430,1\nASAN,8.50,100" if market == "US" else (
        "DNEX,0.45,10000\nMAYBANK,9.80,1000" if market == "Malaysia" else "DBS,38,100\nOCBC,15,100"
    )

    txt = st.text_area("Portfolio / Watchlist", default_text, height=180)
    portfolio_df = build_portfolio_from_text(txt, market)

    if not portfolio_df.empty:
        st.subheader("Input Preview")
        preview = portfolio_df.copy()
        preview["Stock Name"] = preview["Ticker"].apply(get_stock_name)
        st.dataframe(preview, use_container_width=True, hide_index=True)

    if st.button("Run Portfolio Review", type="primary"):
        if portfolio_df.empty:
            st.error("Please enter at least one ticker.")
        else:
            with st.spinner("Reviewing portfolio..."):
                result = review_portfolio(portfolio_df)

            if result.empty:
                st.error("No portfolio review data returned.")
            else:
                st.subheader("Portfolio Review Result")
                st.dataframe(style_score_table(result), use_container_width=True, height=560)

                total_value = result["Position Value"].dropna().sum() if "Position Value" in result.columns else 0
                total_pl = result["P/L Value"].dropna().sum() if "P/L Value" in result.columns else 0

                c1, c2, c3 = st.columns(3)
                c1.metric("Total Position Value", f"{total_value:,.2f}" if total_value else "-")
                c2.metric("Total P/L", f"{total_pl:,.2f}" if total_pl else "-")
                c3.metric("Stocks Reviewed", len(result))

                csv = result.reset_index().to_csv(index=False).encode("utf-8")
                st.download_button("Download Portfolio Review CSV", csv, "portfolio_review.csv", "text/csv")
