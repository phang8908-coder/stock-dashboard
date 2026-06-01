import warnings
from io import BytesIO
from datetime import datetime, timedelta
from urllib.parse import quote

import requests
import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots

warnings.filterwarnings("ignore")


# ============================================================
# Streamlit Page Setup
# ============================================================

st.set_page_config(
    page_title="Stock Scanner Dashboard",
    layout="wide"
)

# ============================================================
# Professional Finance Dashboard Theme
# ============================================================

st.markdown(
    """
    <style>
    /* Main app background */
    .stApp {
        background: linear-gradient(135deg, #020617 0%, #0B1220 42%, #111827 100%);
        color: #E5E7EB;
    }

    /* Main content spacing */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1500px;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #020617 0%, #0F172A 100%);
        border-right: 1px solid #1F2937;
    }

    section[data-testid="stSidebar"] * {
        color: #E5E7EB;
    }

    /* Typography */
    h1 {
        color: #F8FAFC;
        font-weight: 900;
        letter-spacing: -0.045em;
        font-size: 2.45rem;
        margin-bottom: 0.2rem;
    }

    h2, h3 {
        color: #E5E7EB;
        font-weight: 800;
        letter-spacing: -0.025em;
    }

    p, label, span, div {
        font-family: "Inter", "Segoe UI", "Roboto", sans-serif;
    }

    /* Metric cards */
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, rgba(17, 24, 39, 0.98) 0%, rgba(30, 41, 59, 0.92) 100%);
        border: 1px solid #334155;
        padding: 16px 18px;
        border-radius: 18px;
        box-shadow: 0 12px 32px rgba(0,0,0,0.28);
    }

    div[data-testid="stMetricLabel"] {
        color: #94A3B8;
        font-weight: 700;
    }

    div[data-testid="stMetricValue"] {
        color: #F8FAFC;
        font-weight: 900;
    }

    /* Buttons */
    .stButton > button {
        background: linear-gradient(90deg, #2563EB, #06B6D4);
        color: #FFFFFF;
        border: 0px solid transparent;
        border-radius: 14px;
        padding: 0.68rem 1.25rem;
        font-weight: 800;
        box-shadow: 0 10px 24px rgba(37, 99, 235, 0.34);
        transition: all 0.2s ease-in-out;
    }

    .stButton > button:hover {
        background: linear-gradient(90deg, #1D4ED8, #0891B2);
        color: #FFFFFF;
        border: 0px solid transparent;
        transform: translateY(-1px);
    }

    /* Dataframe shell */
    div[data-testid="stDataFrame"] {
        border-radius: 16px;
        overflow: hidden;
        border: 1px solid #334155;
        box-shadow: 0 10px 28px rgba(0,0,0,0.24);
    }

    /* Alerts */
    div[data-testid="stAlert"] {
        border-radius: 16px;
        border: 1px solid #334155;
    }

    /* Inputs */
    .stTextInput input, .stTextArea textarea {
        background-color: #0F172A;
        color: #E5E7EB;
        border: 1px solid #334155;
        border-radius: 12px;
    }

    .stNumberInput input {
        background-color: #0F172A;
        color: #E5E7EB;
        border: 1px solid #334155;
        border-radius: 12px;
    }

    .stSelectbox div[data-baseweb="select"] {
        background-color: #0F172A;
        border-radius: 12px;
        border-color: #334155;
    }

    /* Tabs/radio polish */
    div[role="radiogroup"] label {
        background-color: rgba(15, 23, 42, 0.55);
        border-radius: 10px;
        padding: 4px 8px;
    }

    /* Download buttons */
    .stDownloadButton > button {
        background: linear-gradient(90deg, #0F766E, #14B8A6);
        color: white;
        border: none;
        border-radius: 12px;
        font-weight: 800;
    }

    /* Hide Streamlit footer */
    footer {
        visibility: hidden;
    }
    </style>
    """,
    unsafe_allow_html=True
)


st.markdown(
    """
    <div style="
        background: linear-gradient(135deg, rgba(17, 24, 39, 0.95), rgba(15, 23, 42, 0.82));
        border: 1px solid #334155;
        border-radius: 22px;
        padding: 24px 28px;
        margin-bottom: 20px;
        box-shadow: 0 18px 42px rgba(0,0,0,0.30);
    ">
        <div style="color:#38BDF8; font-size:13px; font-weight:800; letter-spacing:0.18em; text-transform:uppercase;">
            Market Intelligence Dashboard
        </div>
        <div style="color:#F8FAFC; font-size:38px; font-weight:950; letter-spacing:-0.045em; margin-top:6px;">
            Market Beast Pro Scanner
        </div>
        <div style="color:#94A3B8; font-size:16px; margin-top:8px; max-width:980px;">
            Multi-market stock scanner for US, Malaysia, and Singapore markets — powered by trend, momentum,
            volume, smart money flow, capital flow, backtesting, risk/reward analysis, and US options screening.
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

st.warning(
    "Education and screening only. This is not financial advice. "
    "No indicator, score, model, or scanner can guarantee future price movement."
)

st.caption(
    "Data sources with automatic fallback. US: Yahoo Finance, then Stooq, then Alpha Vantage. "
    "Malaysia .KL: Yahoo Finance, then EODHD, then iTick, then Alpha Vantage. Singapore .SI: Yahoo Finance, then EODHD, then Alpha Vantage. "
    "Fallback providers require their own free API key in .streamlit/secrets.toml; "
    "without a key, that provider is skipped."
)


# ============================================================
# Stock Lists
# ============================================================

US_TOP_50_STOCKS = [
    "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL",
    "GOOG", "META", "BRK-B", "AVGO", "TSLA",
    "LLY", "JPM", "V", "UNH", "XOM",
    "MA", "COST", "WMT", "HD", "PG",
    "JNJ", "NFLX", "ABBV", "BAC", "KO",
    "CRM", "ORCL", "MRK", "CVX", "AMD",
    "PEP", "ADBE", "TMO", "LIN", "MCD",
    "CSCO", "ACN", "WFC", "IBM", "QCOM",
    "INTU", "TXN", "AMAT", "GE", "NOW",
    "UBER", "PM", "ISRG", "GS", "CAT"
]

ACTIVE_US_STOCKS = [
    "PLTR", "SMCI", "MSTR", "COIN", "RIVN",
    "LCID", "SOFI", "HOOD", "SNAP", "ASAN",
    "BBAI", "SOUN", "AI", "IONQ", "RGTI",
    "MARA", "RIOT", "HIMS", "RKLB", "ACHR",
    "NIO", "BABA", "PDD", "JD", "TSM",
    "ARM", "MU", "DELL", "SNOW", "CRWD",
    "PANW", "SHOP", "SE", "PYPL", "SQ",
    "DKNG", "ROKU", "U", "PATH", "WBD",
    "F", "GM", "DIS", "T", "PFE"
]

US_DEFAULT_WATCHLIST = [
    "AAPL", "MSFT", "NVDA", "TSLA", "AMZN",
    "META", "GOOGL", "AMD", "PLTR", "COIN",
    "MSTR", "ASAN", "SNAP"
]

MALAYSIA_KLCI_30 = [
    "1155.KL", "1023.KL", "1295.KL", "5347.KL", "5183.KL",
    "6033.KL", "3816.KL", "4863.KL", "6947.KL", "6888.KL",
    "6012.KL", "5819.KL", "1082.KL", "1066.KL", "1015.KL",
    "2445.KL", "1961.KL", "5285.KL", "4197.KL", "4707.KL",
    "3182.KL", "4715.KL", "5681.KL", "7277.KL", "5211.KL",
    "5398.KL", "8869.KL", "4065.KL", "1818.KL", "5168.KL",
]

ACTIVE_MALAYSIA_STOCKS = [
    "6963.KL", "5555.KL", "0193.KL", "5243.KL", "5238.KL",
    "8869.KL", "5398.KL", "1155.KL", "1066.KL", "5031.KL",
    "4863.KL", "5211.KL", "5285.KL", "2429.KL", "5286.KL",
    "5168.KL", "7113.KL", "1023.KL", "1295.KL", "5347.KL",
    "6947.KL", "5183.KL", "7277.KL", "6033.KL", "1818.KL",
]

MALAYSIA_DEFAULT_WATCHLIST = [
    "6947.KL", "1015.KL", "1066.KL", "7113.KL", "5168.KL",
    "1295.KL", "2445.KL", "5031.KL", "8869.KL", "3816.KL",
    "4863.KL", "6012.KL"
]


# Extra Malaysia broad preset. This is not the full Bursa universe,
# but it gives you a wider scan list beyond KLCI 30 and active names.
# You can still add any Bursa ticker manually using Custom.
MALAYSIA_BROAD_PRESET = list(dict.fromkeys(MALAYSIA_KLCI_30 + ACTIVE_MALAYSIA_STOCKS + [
    "5296.KL",  # Mr DIY
    "7084.KL",  # QL Resources
    "5225.KL",  # IHH Healthcare
    "5288.KL",  # Sime Darby Property
    "7202.KL",  # D&O Green Technologies
    "5292.KL",  # UWC
    "5291.KL",  # HPMT
    "5272.KL",  # Ranhill
    "5139.KL",  # AEON Credit
    "5077.KL",  # Maybulk
    "5148.KL",  # UEM Sunrise
    "5200.KL",  # UOA Development
    "5008.KL",  # Harbour-Link
    "5284.KL",  # Lotte Chemical Titan
    "5236.KL",  # Matrix Concepts
    "5258.KL",  # BIMB
    "5255.KL",  # Icon Offshore
    "5257.KL",  # Carimin
    "5199.KL",  # Hibiscus Petroleum
    "5210.KL",  # Bumi Armada
    "5141.KL",  # Dayang
    "7277.KL",  # Dialog
    "7229.KL",  # Favelle Favco
    "7090.KL",  # Apex Healthcare
    "7164.KL",  # KNM
    "0172.KL",  # Oceancash
    "0128.KL",  # Frontken
    "0122.KL",  # JHM
    "0097.KL",  # Vitrox
    "0092.KL",  # mTouche
]))

# ============================================================
# Singapore Stock Lists
# Yahoo Finance uses .SI suffix for SGX stocks.
# ============================================================

SINGAPORE_STI_30 = [
    "D05.SI",   # DBS
    "O39.SI",   # OCBC
    "U11.SI",   # UOB
    "Z74.SI",   # Singtel
    "C6L.SI",   # Singapore Airlines
    "S68.SI",   # SGX
    "C38U.SI",  # CapitaLand Integrated Commercial Trust
    "A17U.SI",  # CapitaLand Ascendas REIT
    "J36.SI",   # Jardine Matheson
    "BN4.SI",   # Keppel
    "F34.SI",   # Wilmar
    "G13.SI",   # Genting Singapore
    "H78.SI",   # Hongkong Land
    "J69U.SI",  # Frasers Centrepoint Trust
    "M44U.SI",  # Mapletree Logistics Trust
    "ME8U.SI",  # Mapletree Industrial Trust
    "N2IU.SI",  # Mapletree Pan Asia Commercial Trust
    "S58.SI",   # SATS
    "U14.SI",   # UOL
    "Y92.SI",   # Thai Beverage
    "C07.SI",   # Jardine Cycle & Carriage
    "S63.SI",   # ST Engineering
    "U96.SI",   # Sembcorp Industries
    "V03.SI",   # Venture
    "D01.SI",   # Dairy Farm / DFI Retail
    "C09.SI",   # City Developments
    "BS6.SI",   # Yangzijiang Shipbuilding
    "BUOU.SI",  # Frasers Logistics & Commercial Trust
    "AJBU.SI",  # Keppel DC REIT
    "T82U.SI",  # Suntec REIT
]

ACTIVE_SINGAPORE_STOCKS = [
    "D05.SI", "O39.SI", "U11.SI", "Z74.SI", "C6L.SI",
    "S68.SI", "C38U.SI", "A17U.SI", "M44U.SI", "ME8U.SI",
    "N2IU.SI", "S58.SI", "G13.SI", "F34.SI", "BN4.SI",
    "S63.SI", "U96.SI", "V03.SI", "C09.SI", "BS6.SI",
    "T82U.SI", "AJBU.SI", "BUOU.SI", "J69U.SI", "Y92.SI",
    "5E2.SI", "AEM.SI", "AWX.SI", "BVA.SI", "C52.SI",
]

SINGAPORE_DEFAULT_WATCHLIST = [
    "D05.SI", "O39.SI", "U11.SI", "Z74.SI", "C6L.SI",
    "S68.SI", "C38U.SI", "A17U.SI", "M44U.SI", "ME8U.SI"
]

SINGAPORE_BROAD_PRESET = list(dict.fromkeys(SINGAPORE_STI_30 + ACTIVE_SINGAPORE_STOCKS + [
    "AEM.SI", "BVA.SI", "5E2.SI", "C52.SI", "AWX.SI",
    "NO4.SI", "M01.SI", "S08.SI", "T39.SI", "E5H.SI",
    "U06.SI", "Q0X.SI", "K71U.SI", "KDCU.SI", "M44U.SI",
]))




# ============================================================
# Ticker Alias / Easy Input Helper
# ============================================================

MALAYSIA_TICKER_ALIASES = {
    "MAYBANK": "1155.KL",
    "CIMB": "1023.KL",
    "PBBANK": "1295.KL",
    "PUBLICBANK": "1295.KL",
    "RHBBANK": "1066.KL",
    "AMBANK": "1015.KL",
    "HLBANK": "5819.KL",
    "HLFG": "1082.KL",
    "BIMB": "5258.KL",

    "TENAGA": "5347.KL",
    "TNB": "5347.KL",
    "CDB": "6947.KL",
    "CDBIGI": "6947.KL",
    "CELCOMDIGI": "6947.KL",
    "MAXIS": "6012.KL",
    "AXIATA": "6888.KL",
    "TM": "4863.KL",
    "TELEKOM": "4863.KL",
    "PETGAS": "6033.KL",
    "YTL": "4677.KL",
    "YTLPOWR": "6742.KL",

    "SIMEPLT": "5285.KL",
    "KLK": "2445.KL",
    "IOICORP": "1961.KL",
    "PPB": "4065.KL",
    "QL": "7084.KL",
    "NESTLE": "4707.KL",
    "F&N": "3689.KL",
    "FNB": "3689.KL",

    "IHH": "5225.KL",
    "TOPGLOV": "7113.KL",
    "HARTA": "5168.KL",
    "KOSSAN": "7153.KL",
    "SUPERMX": "7106.KL",

    "DNEX": "4456.KL",
    "DAGANG": "4456.KL",
    "FRONTKN": "0128.KL",
    "FRONTKEN": "0128.KL",
    "VITROX": "0097.KL",
    "INARI": "0166.KL",
    "MPI": "3867.KL",
    "MI": "5286.KL",
    "GREATEC": "0208.KL",
    "UWC": "5292.KL",
    "PENTA": "7160.KL",
    "AEMULUS": "0181.KL",
    "JFTECH": "0146.KL",
    "D&O": "7202.KL",
    "DNO": "7202.KL",

    "DIALOG": "7277.KL",
    "HIBISCS": "5199.KL",
    "HIBISCUS": "5199.KL",
    "ARMADA": "5210.KL",
    "BUMIARMADA": "5210.KL",
    "DAYANG": "5141.KL",
    "YINSON": "7293.KL",
    "MISC": "3816.KL",

    "GAMUDA": "5398.KL",
    "SUNWAY": "5211.KL",
    "IJM": "3336.KL",
    "SPSETIA": "8664.KL",
    "SIMEPROP": "5288.KL",
    "MRCB": "1651.KL",
    "ECOWLD": "8206.KL",
    "MAHSING": "8583.KL",
    "MRDIY": "5296.KL",
    "GENM": "4715.KL",
    "GENTING": "3182.KL",
    "AIRPORT": "5014.KL",
    "MAHB": "5014.KL",
    "CAPITALA": "5099.KL",
    "AIRASIA": "5099.KL",
}

SINGAPORE_TICKER_ALIASES = {
    "DBS": "D05.SI",
    "OCBC": "O39.SI",
    "UOB": "U11.SI",
    "SINGTEL": "Z74.SI",
    "SIA": "C6L.SI",
    "SGX": "S68.SI",
    "CAPITALAND": "C38U.SI",
    "CICT": "C38U.SI",
    "ASCENDAS": "A17U.SI",
    "CAPLANDASCENDAS": "A17U.SI",
    "KEPPEL": "BN4.SI",
    "WILMAR": "F34.SI",
    "GENTINGSING": "G13.SI",
    "SATS": "S58.SI",
    "SEMBIND": "U96.SI",
    "SEMBCORP": "U96.SI",
    "STENGINEERING": "S63.SI",
    "STE": "S63.SI",
    "VENTURE": "V03.SI",
}



STOCK_NAME_MAP = {
    # US
    "AAPL": "Apple",
    "MSFT": "Microsoft",
    "NVDA": "Nvidia",
    "AMZN": "Amazon",
    "GOOGL": "Alphabet",
    "GOOG": "Alphabet",
    "META": "Meta Platforms",
    "TSLA": "Tesla",
    "AMD": "AMD",
    "PLTR": "Palantir",
    "COIN": "Coinbase",
    "MSTR": "MicroStrategy",
    "SMCI": "Super Micro Computer",
    "NFLX": "Netflix",
    "AVGO": "Broadcom",
    "JPM": "JPMorgan Chase",
    "V": "Visa",
    "MA": "Mastercard",
    "COST": "Costco",
    "WMT": "Walmart",
    "HD": "Home Depot",
    "BAC": "Bank of America",
    "CRM": "Salesforce",
    "ORCL": "Oracle",
    "QCOM": "Qualcomm",
    "SOFI": "SoFi",
    "HOOD": "Robinhood",
    "RIVN": "Rivian",
    "SHOP": "Shopify",
    "UBER": "Uber",
    "SNAP": "Snap",
    "ASAN": "Asana",

    # Malaysia
    "1155.KL": "Maybank",
    "1023.KL": "CIMB",
    "1295.KL": "Public Bank",
    "1066.KL": "RHB Bank",
    "1015.KL": "AmBank",
    "5819.KL": "Hong Leong Bank",
    "1082.KL": "Hong Leong Financial Group",
    "5258.KL": "BIMB",
    "5347.KL": "Tenaga Nasional",
    "6947.KL": "CelcomDigi",
    "6012.KL": "Maxis",
    "6888.KL": "Axiata",
    "4863.KL": "Telekom Malaysia",
    "6033.KL": "Petronas Gas",
    "4677.KL": "YTL Corporation",
    "6742.KL": "YTL Power",
    "5285.KL": "Sime Darby Plantation",
    "2445.KL": "KLK",
    "1961.KL": "IOI Corporation",
    "4065.KL": "PPB Group",
    "7084.KL": "QL Resources",
    "4707.KL": "Nestle Malaysia",
    "3689.KL": "Fraser & Neave",
    "5225.KL": "IHH Healthcare",
    "7113.KL": "Top Glove",
    "5168.KL": "Hartalega",
    "7153.KL": "Kossan",
    "7106.KL": "Supermax",
    "4456.KL": "DNEX",
    "0128.KL": "Frontken",
    "0097.KL": "Vitrox",
    "0166.KL": "Inari",
    "3867.KL": "MPI",
    "5286.KL": "Mi Technovation",
    "0208.KL": "Greatech",
    "5292.KL": "UWC",
    "7160.KL": "Pentamaster",
    "0181.KL": "Aemulus",
    "0146.KL": "JF Technology",
    "7202.KL": "D&O Green Technologies",
    "7277.KL": "Dialog Group",
    "5199.KL": "Hibiscus Petroleum",
    "5210.KL": "Bumi Armada",
    "5141.KL": "Dayang",
    "7293.KL": "Yinson",
    "3816.KL": "MISC",
    "5398.KL": "Gamuda",
    "5211.KL": "Sunway",
    "3336.KL": "IJM",
    "8664.KL": "SP Setia",
    "5288.KL": "Sime Darby Property",
    "1651.KL": "MRCB",
    "8206.KL": "Eco World",
    "8583.KL": "Mah Sing",
    "5296.KL": "Mr DIY",
    "4715.KL": "Genting Malaysia",
    "3182.KL": "Genting",
    "5014.KL": "Malaysia Airports",
    "5099.KL": "Capital A",
    "5031.KL": "TIME dotCom",
    "8869.KL": "Press Metal",
    "4197.KL": "Sime Darby",
    "1818.KL": "Bursa Malaysia",
    "5681.KL": "Petronas Dagangan",
    "7277.KL": "Dialog Group",

    # Singapore
    "D05.SI": "DBS",
    "O39.SI": "OCBC",
    "U11.SI": "UOB",
    "Z74.SI": "Singtel",
    "C6L.SI": "Singapore Airlines",
    "S68.SI": "SGX",
    "C38U.SI": "CapitaLand Integrated Commercial Trust",
    "A17U.SI": "CapitaLand Ascendas REIT",
    "J36.SI": "Jardine Matheson",
    "BN4.SI": "Keppel",
    "F34.SI": "Wilmar",
    "G13.SI": "Genting Singapore",
    "H78.SI": "Hongkong Land",
    "J69U.SI": "Frasers Centrepoint Trust",
    "M44U.SI": "Mapletree Logistics Trust",
    "ME8U.SI": "Mapletree Industrial Trust",
    "N2IU.SI": "Mapletree Pan Asia Commercial Trust",
    "S58.SI": "SATS",
    "U14.SI": "UOL",
    "Y92.SI": "Thai Beverage",
    "C07.SI": "Jardine Cycle & Carriage",
    "S63.SI": "ST Engineering",
    "U96.SI": "Sembcorp Industries",
    "V03.SI": "Venture",
    "C09.SI": "City Developments",
    "BS6.SI": "Yangzijiang Shipbuilding",
    "BUOU.SI": "Frasers Logistics & Commercial Trust",
    "AJBU.SI": "Keppel DC REIT",
    "T82U.SI": "Suntec REIT",
    "ES3.SI": "STI ETF",
}


def get_stock_name(ticker):
    """Return readable stock name for dashboard display."""
    ticker = str(ticker).strip().upper()

    if ticker in STOCK_NAME_MAP:
        return STOCK_NAME_MAP[ticker]

    # Fallback for unknown Bursa / SGX / US tickers
    if ticker.endswith(".KL"):
        return ticker.replace(".KL", "")
    if ticker.endswith(".SI"):
        return ticker.replace(".SI", "")

    return ticker



def normalize_user_ticker(raw_ticker, market_name):
    """
    Convert easy user input into Yahoo Finance ticker format.

    Malaysia examples:
    4456 -> 4456.KL
    4456.kl -> 4456.KL
    dnex -> 4456.KL
    DNEX -> 4456.KL
    """
    ticker = str(raw_ticker).strip().upper()

    if not ticker:
        return ""

    ticker = ticker.replace(" ", "")
    ticker = ticker.replace("_", "-")

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

    ticker = ticker.replace(".", "-")
    return ticker


def normalize_ticker_list_from_text(custom_text, market_name):
    """Convert comma/newline separated ticker input into clean Yahoo tickers."""
    raw_items = []
    for line in str(custom_text).splitlines():
        raw_items.extend(line.split(","))

    normalized = [
        normalize_user_ticker(item, market_name)
        for item in raw_items
        if str(item).strip()
    ]

    return list(dict.fromkeys([t for t in normalized if t]))


# ============================================================
# Auto-load universe functions
# ============================================================

@st.cache_data(ttl=86400)
def load_wikipedia_table_tickers(url, possible_cols):
    """Load tickers from a Wikipedia table. Falls back to an empty list if unavailable."""
    try:
        tables = pd.read_html(url)
        for table in tables:
            for col in possible_cols:
                if col in table.columns:
                    tickers = (
                        table[col]
                        .dropna()
                        .astype(str)
                        .str.replace(".", "-", regex=False)  # Yahoo uses BRK-B, not BRK.B
                        .str.strip()
                        .str.upper()
                        .tolist()
                    )
                    tickers = [t for t in tickers if t and t != "NAN"]
                    if len(tickers) >= 20:
                        return list(dict.fromkeys(tickers))
        return []
    except Exception:
        return []


@st.cache_data(ttl=86400)
def load_sp500_tickers():
    return load_wikipedia_table_tickers(
        "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies",
        ["Symbol", "Ticker"]
    )


@st.cache_data(ttl=86400)
def load_nasdaq100_tickers():
    return load_wikipedia_table_tickers(
        "https://en.wikipedia.org/wiki/Nasdaq-100",
        ["Ticker", "Symbol"]
    )


@st.cache_data(ttl=86400)
def load_dow30_tickers():
    return load_wikipedia_table_tickers(
        "https://en.wikipedia.org/wiki/Dow_Jones_Industrial_Average",
        ["Symbol", "Ticker"]
    )


def get_auto_stock_list(market_name, auto_universe):
    """Return an auto-loaded/preset stock list based on selected universe."""
    if market_name == "US":
        if auto_universe == "S&P 500":
            tickers = load_sp500_tickers()
            return tickers if tickers else US_TOP_50_STOCKS
        if auto_universe == "Nasdaq 100":
            tickers = load_nasdaq100_tickers()
            return tickers if tickers else list(dict.fromkeys(US_TOP_50_STOCKS + ACTIVE_US_STOCKS))
        if auto_universe == "Dow 30":
            tickers = load_dow30_tickers()
            return tickers if tickers else ["AAPL", "MSFT", "AMZN", "JPM", "V", "WMT", "HD", "MCD", "IBM", "CAT"]
        if auto_universe == "S&P 500 + Nasdaq 100":
            tickers = list(dict.fromkeys(load_sp500_tickers() + load_nasdaq100_tickers()))
            return tickers if tickers else list(dict.fromkeys(US_TOP_50_STOCKS + ACTIVE_US_STOCKS))
    elif market_name == "Malaysia":
        if auto_universe == "Malaysia Broad Preset":
            return MALAYSIA_BROAD_PRESET
        if auto_universe == "KLCI 30 + Active + Broad Preset":
            return MALAYSIA_BROAD_PRESET
    elif market_name == "Singapore":
        if auto_universe == "Singapore Broad Preset":
            return SINGAPORE_BROAD_PRESET
        if auto_universe == "STI 30 + Active + Broad Preset":
            return SINGAPORE_BROAD_PRESET
    return []


def limit_stock_list(stock_list, max_scan):
    stock_list = list(dict.fromkeys([str(x).strip().upper() for x in stock_list if str(x).strip()]))
    if max_scan and max_scan > 0:
        return stock_list[:max_scan]
    return stock_list


# ============================================================
# Active Stocks Ranking
# ============================================================

@st.cache_data(ttl=3600)
def calculate_auto_active_stocks(
    tickers,
    market_name,
    top_n=30,
    lookback_days=5,
    data_source="Auto"
):
    """
    Rank tickers by recent traded value.

    Traded Value = Close x Volume.
    This is better than pure volume because a RM0.10 stock with huge volume
    is not the same as a RM10 stock with similar volume.

    This updates whenever cached market data refreshes.
    Current cache ttl = 3600 seconds, so roughly every 1 hour.
    """
    rows = []

    clean_tickers = list(dict.fromkeys([
        str(t).strip().upper()
        for t in tickers
        if str(t).strip()
    ]))

    for ticker in clean_tickers:
        try:
            normalized_ticker = ticker

            if market_name == "Malaysia":
                if not normalized_ticker.endswith(".KL") and not normalized_ticker.startswith("^"):
                    normalized_ticker = f"{normalized_ticker}.KL"

            if market_name == "Singapore":
                if not normalized_ticker.endswith(".SI") and not normalized_ticker.startswith("^"):
                    normalized_ticker = f"{normalized_ticker}.SI"

            df = get_data(
                normalized_ticker,
                period="3mo",
                interval="1d",
                min_rows=20,
                source=data_source,
                market_name=market_name
            )

            if df is None or df.empty:
                continue

            df = df.copy()
            df["Traded_Value"] = df["Close"] * df["Volume"]

            latest_close = df["Close"].iloc[-1]
            latest_volume = df["Volume"].iloc[-1]
            latest_traded_value = df["Traded_Value"].iloc[-1]

            avg_traded_value = df["Traded_Value"].tail(lookback_days).mean()
            avg_volume = df["Volume"].tail(lookback_days).mean()
            volume_avg20 = df["Volume"].tail(20).mean()

            relative_volume = latest_volume / volume_avg20 if volume_avg20 and volume_avg20 > 0 else None

            price_change_5d = None
            if len(df) > lookback_days:
                old_close = df["Close"].iloc[-lookback_days - 1]
                if old_close and old_close > 0:
                    price_change_5d = ((latest_close - old_close) / old_close) * 100

            rows.append({
                "Ticker": normalized_ticker,
                "Name": get_stock_name(normalized_ticker),
                "Latest_Close": round(latest_close, 4),
                "Latest_Volume": round(latest_volume, 0),
                "Latest_Traded_Value": round(latest_traded_value, 2),
                f"Avg_{lookback_days}D_Traded_Value": round(avg_traded_value, 2),
                f"Avg_{lookback_days}D_Volume": round(avg_volume, 0),
                "Relative_Volume": round(relative_volume, 2) if relative_volume is not None else None,
                "Price_Change_5D_%": round(price_change_5d, 2) if price_change_5d is not None else None,
            })

        except Exception:
            continue

    if not rows:
        return [], pd.DataFrame()

    active_df = pd.DataFrame(rows)

    sort_col = f"Avg_{lookback_days}D_Traded_Value"

    active_df = active_df.sort_values(
        by=[sort_col, "Latest_Traded_Value", "Relative_Volume"],
        ascending=[False, False, False]
    )

    active_df = active_df.head(top_n).reset_index(drop=True)
    active_tickers = active_df["Ticker"].tolist()

    return active_tickers, active_df


# ============================================================
# Shared Helper Functions
# ============================================================

def value(x):
    return x.item() if hasattr(x, "item") else x


# ============================================================
# Multi-Source Data Layer
# ------------------------------------------------------------
# Provider chain (first that returns valid data wins):
#   US:        Yahoo -> Stooq -> Alpha Vantage
#   Malaysia:  Yahoo -> EODHD -> iTick -> Alpha Vantage
#
# API keys are read from Streamlit secrets. Add a file named
# .streamlit/secrets.toml next to this app with:
#
#   EODHD_API_KEY = "your_key_here"
#   ITICK_API_KEY = "your_key_here"
#   ALPHAVANTAGE_API_KEY = "your_key_here"
#
# Any key you leave out simply disables that provider; the chain
# skips it gracefully. None of these are tested live in this file,
# so after adding keys, verify one .KL ticker on Page 4 first.
# ============================================================


def _get_secret(name):
    """Read an API key from st.secrets without crashing if absent."""
    try:
        return st.secrets.get(name, None)
    except Exception:
        return None


def _normalize_ohlcv(df, min_rows):
    """Standardize any provider DataFrame to Open/High/Low/Close/Volume, sorted, clean."""
    if df is None or df.empty:
        return None

    required_cols = ["Open", "High", "Low", "Close", "Volume"]
    for col in required_cols:
        if col not in df.columns:
            return None

    df = df[required_cols].copy()
    df = df.apply(pd.to_numeric, errors="coerce")
    df.sort_index(inplace=True)
    df.dropna(inplace=True)

    if len(df) < min_rows:
        return None

    return df


def period_to_start_date(period):
    """Convert a yfinance-like period string into a start date for CSV/API sources."""
    today = datetime.today()

    if period.endswith("mo"):
        months = int(period.replace("mo", ""))
        return today - timedelta(days=months * 31)

    if period.endswith("wk"):
        weeks = int(period.replace("wk", ""))
        return today - timedelta(weeks=weeks)

    if period.endswith("d"):
        days = int(period.replace("d", ""))
        return today - timedelta(days=days)

    if period.endswith("y"):
        years = int(period.replace("y", ""))
        return today - timedelta(days=years * 365)

    if period == "max":
        return datetime(1990, 1, 1)

    return today - timedelta(days=365 * 2)


# ------------------------------------------------------------
# Provider 1: Yahoo Finance (yfinance) - primary for both markets
# ------------------------------------------------------------

@st.cache_data(ttl=3600)
def get_data_yahoo(ticker, period="2y", interval="1d", min_rows=120):
    """Primary data source: Yahoo Finance via yfinance."""
    try:
        df = yf.download(
            ticker,
            period=period,
            interval=interval,
            auto_adjust=True,
            progress=False,
            threads=False
        )

        if df is None or df.empty:
            return None

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        return _normalize_ohlcv(df, min_rows)

    except Exception:
        return None


# ------------------------------------------------------------
# Provider 2: Stooq (US daily only) - free, no key
# ------------------------------------------------------------

def convert_to_stooq_symbol(ticker):
    """
    Convert app ticker to Stooq format.
    Stooq works best for US tickers using ticker.us, for example AAPL -> aapl.us.
    Class shares keep their hyphen on Stooq (BRK-B -> brk-b.us).
    Malaysia .KL is not reliably available on Stooq, so return None for Bursa tickers.
    """
    ticker = ticker.strip().upper()

    if ticker.endswith(".KL") or ticker.startswith("^"):
        return None

    # Do NOT swap '-' for '.'; Stooq keeps the hyphen for class shares.
    return f"{ticker.lower()}.us"


@st.cache_data(ttl=3600)
def get_data_stooq(ticker, period="2y", interval="1d", min_rows=120):
    """Backup data source: Stooq daily CSV. US stocks only. Daily only."""
    try:
        if interval != "1d":
            return None

        stooq_symbol = convert_to_stooq_symbol(ticker)
        if stooq_symbol is None:
            return None

        url = f"https://stooq.com/q/d/l/?s={quote(stooq_symbol)}&i=d"
        df = pd.read_csv(url)

        if df is None or df.empty or "Date" not in df.columns:
            return None

        df["Date"] = pd.to_datetime(df["Date"])
        df = df.set_index("Date")

        df = _normalize_ohlcv(df, min_rows=1)  # row filter applied after date trim
        if df is None:
            return None

        start_date = period_to_start_date(period)
        df = df[df.index >= start_date]

        if len(df) < min_rows:
            return None

        return df

    except Exception:
        return None


# ------------------------------------------------------------
# Provider 3: EODHD - strong Bursa Malaysia (.KLSE) coverage
# Docs: https://eodhd.com/financial-apis
# US tickers use .US suffix; Bursa uses .KLSE
# ------------------------------------------------------------

def convert_to_eodhd_symbol(ticker, market_name):
    ticker = ticker.strip().upper()

    if ticker.startswith("^"):
        return None  # index handling left to Yahoo

    if ticker.endswith(".KL"):
        return ticker.replace(".KL", ".KLSE")

    if ticker.endswith(".SI"):
        return ticker.replace(".SI", ".SG")

    if market_name == "US":
        # EODHD expects e.g. AAPL.US ; class shares keep hyphen
        return f"{ticker}.US"

    return None


@st.cache_data(ttl=3600)
def get_data_eodhd(ticker, period="2y", interval="1d", min_rows=120, market_name="US"):
    """Fallback via EODHD. Requires EODHD_API_KEY in secrets. Daily only here."""
    try:
        if interval != "1d":
            return None

        api_key = _get_secret("EODHD_API_KEY")
        if not api_key:
            return None

        symbol = convert_to_eodhd_symbol(ticker, market_name)
        if symbol is None:
            return None

        start_date = period_to_start_date(period).strftime("%Y-%m-%d")
        url = (
            f"https://eodhd.com/api/eod/{quote(symbol)}"
            f"?from={start_date}&period=d&api_token={api_key}&fmt=json"
        )

        resp = requests.get(url, timeout=20)
        if resp.status_code != 200:
            return None

        data = resp.json()
        if not isinstance(data, list) or len(data) == 0:
            return None

        df = pd.DataFrame(data)
        if "date" not in df.columns:
            return None

        df["date"] = pd.to_datetime(df["date"])
        df = df.set_index("date")

        # EODHD uses adjusted_close; prefer it for the Close to stay consistent
        # with Yahoo auto_adjust=True.
        rename_map = {
            "open": "Open",
            "high": "High",
            "low": "Low",
            "adjusted_close": "Close",
            "volume": "Volume",
        }
        df = df.rename(columns=rename_map)

        return _normalize_ohlcv(df, min_rows)

    except Exception:
        return None


# ------------------------------------------------------------
# Provider 4: iTick - Bursa Malaysia (region=MY) daily bars
# Docs: https://itick.org / https://blog.itick.org
# Note: iTick's exact daily-bar schema varies by plan; this parser
# is defensive. Verify field names against your account's response.
# ------------------------------------------------------------

def convert_to_itick_symbol(ticker):
    """iTick MY equities are referenced by the bare Bursa code (no .KL)."""
    ticker = ticker.strip().upper()
    if ticker.endswith(".KL"):
        return ticker.replace(".KL", "")
    return None


@st.cache_data(ttl=3600)
def get_data_itick(ticker, period="2y", interval="1d", min_rows=120):
    """Fallback via iTick (Malaysia). Requires ITICK_API_KEY in secrets. Daily only."""
    try:
        if interval != "1d":
            return None

        api_key = _get_secret("ITICK_API_KEY")
        if not api_key:
            return None

        symbol = convert_to_itick_symbol(ticker)
        if symbol is None:
            return None

        # iTick daily kline endpoint. kType=8 is commonly the daily bar.
        url = "https://api.itick.org/stock/kline"
        params = {
            "region": "MY",
            "code": symbol,
            "kType": 8,
            "limit": 800,
        }
        headers = {"token": api_key}

        resp = requests.get(url, params=params, headers=headers, timeout=20)
        if resp.status_code != 200:
            return None

        payload = resp.json()
        rows = payload.get("data") if isinstance(payload, dict) else None
        if not rows:
            return None

        df = pd.DataFrame(rows)

        # iTick kline fields are typically single letters:
        # t = timestamp(ms), o/h/l/c = OHLC, v = volume.
        rename_map = {
            "t": "Date", "o": "Open", "h": "High",
            "l": "Low", "c": "Close", "v": "Volume",
        }
        df = df.rename(columns=rename_map)

        if "Date" not in df.columns:
            return None

        df["Date"] = pd.to_datetime(df["Date"], unit="ms", errors="coerce")
        df = df.dropna(subset=["Date"]).set_index("Date")

        df = _normalize_ohlcv(df, min_rows=1)
        if df is None:
            return None

        start_date = period_to_start_date(period)
        df = df[df.index >= start_date]

        if len(df) < min_rows:
            return None

        return df

    except Exception:
        return None


# ------------------------------------------------------------
# Provider 5: Alpha Vantage - global equities, last-resort fallback
# Free tier: 25 req/day, 5 req/min. Too slow for bulk scans;
# use only on single-ticker pages.
# Bursa tickers use the .KLSE suffix on Alpha Vantage.
# ------------------------------------------------------------

def convert_to_alphavantage_symbol(ticker, market_name):
    ticker = ticker.strip().upper()
    if ticker.startswith("^"):
        return None
    if ticker.endswith(".KL"):
        return ticker.replace(".KL", ".KLSE")
    if ticker.endswith(".SI"):
        return ticker
    if market_name == "US":
        return ticker
    return None


@st.cache_data(ttl=3600)
def get_data_alphavantage(ticker, period="2y", interval="1d", min_rows=120, market_name="US"):
    """Last-resort fallback via Alpha Vantage. Requires ALPHAVANTAGE_API_KEY in secrets."""
    try:
        if interval != "1d":
            return None

        api_key = _get_secret("ALPHAVANTAGE_API_KEY")
        if not api_key:
            return None

        symbol = convert_to_alphavantage_symbol(ticker, market_name)
        if symbol is None:
            return None

        url = "https://www.alphavantage.co/query"
        params = {
            "function": "TIME_SERIES_DAILY",
            "symbol": symbol,
            "outputsize": "full",
            "datatype": "json",
            "apikey": api_key,
        }

        resp = requests.get(url, params=params, timeout=25)
        if resp.status_code != 200:
            return None

        data = resp.json()
        series = data.get("Time Series (Daily)")
        if not series:
            # Likely a rate-limit note or invalid symbol.
            return None

        df = pd.DataFrame(series).T
        df.index = pd.to_datetime(df.index)
        df = df.rename(columns={
            "1. open": "Open",
            "2. high": "High",
            "3. low": "Low",
            "4. close": "Close",
            "5. volume": "Volume",
        })

        df = _normalize_ohlcv(df, min_rows=1)
        if df is None:
            return None

        start_date = period_to_start_date(period)
        df = df[df.index >= start_date]

        if len(df) < min_rows:
            return None

        return df

    except Exception:
        return None


# ------------------------------------------------------------
# Unified loader with market-aware provider chains
# ------------------------------------------------------------

@st.cache_data(ttl=3600)
def get_data(ticker, period="2y", interval="1d", min_rows=120,
             source="Auto", market_name=None):
    """
    Unified data loader with market-aware fallback chains.

    market_name: "US", "Malaysia", or None (auto-detected from .KL suffix).
    source: "Auto" runs the full chain. You may also force a single provider:
            "Yahoo Finance", "Stooq", "EODHD", "iTick", "Alpha Vantage".

    Provider chains when source == "Auto":
        US:        Yahoo -> Stooq -> Alpha Vantage
        Malaysia:  Yahoo -> EODHD -> iTick -> Alpha Vantage
        Singapore: Yahoo -> EODHD -> Alpha Vantage
        Singapore: Yahoo -> EODHD -> Alpha Vantage
    """
    source = source or "Auto"

    # Auto-detect market if not provided.
    if market_name is None:
        ticker_upper = ticker.strip().upper()
        if ticker_upper.endswith(".KL"):
            market_name = "Malaysia"
        elif ticker_upper.endswith(".SI"):
            market_name = "Singapore"
        else:
            market_name = "US"

    # --- Forced single providers (kept for backward compatibility) ---
    if source == "Yahoo Finance":
        return get_data_yahoo(ticker, period=period, interval=interval, min_rows=min_rows)
    if source == "Stooq":
        return get_data_stooq(ticker, period=period, interval=interval, min_rows=min_rows)
    if source == "EODHD":
        return get_data_eodhd(ticker, period=period, interval=interval,
                              min_rows=min_rows, market_name=market_name)
    if source == "iTick":
        return get_data_itick(ticker, period=period, interval=interval, min_rows=min_rows)
    if source == "Alpha Vantage":
        return get_data_alphavantage(ticker, period=period, interval=interval,
                                     min_rows=min_rows, market_name=market_name)

    # Legacy label still routes through Auto.
    # "Auto" and "Auto" both use the full market-aware chain.

    # --- Auto chain ---
    df = get_data_yahoo(ticker, period=period, interval=interval, min_rows=min_rows)
    if df is not None:
        return df

    if market_name == "US":
        df = get_data_stooq(ticker, period=period, interval=interval, min_rows=min_rows)
        if df is not None:
            return df
        return get_data_alphavantage(ticker, period=period, interval=interval,
                                     min_rows=min_rows, market_name=market_name)

    if market_name == "Malaysia":
        df = get_data_eodhd(ticker, period=period, interval=interval,
                            min_rows=min_rows, market_name=market_name)
        if df is not None:
            return df
        df = get_data_itick(ticker, period=period, interval=interval, min_rows=min_rows)
        if df is not None:
            return df
        return get_data_alphavantage(ticker, period=period, interval=interval,
                                     min_rows=min_rows, market_name=market_name)

    if market_name == "Singapore":
        df = get_data_eodhd(ticker, period=period, interval=interval,
                            min_rows=min_rows, market_name=market_name)
        if df is not None:
            return df
        return get_data_alphavantage(ticker, period=period, interval=interval,
                                     min_rows=min_rows, market_name=market_name)

    return None


def add_macd(df):
    df["EMA12"] = df["Close"].ewm(span=12, adjust=False).mean()
    df["EMA26"] = df["Close"].ewm(span=26, adjust=False).mean()
    df["MACD"] = df["EMA12"] - df["EMA26"]
    df["Signal"] = df["MACD"].ewm(span=9, adjust=False).mean()
    df["MACD_Hist"] = df["MACD"] - df["Signal"]
    df["MACD_Hist_Change"] = df["MACD_Hist"] - df["MACD_Hist"].shift(1)
    return df


def add_rsi(df, period=14):
    delta = df["Close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    # Wilder's smoothing (EMA with alpha = 1/period) matches TradingView/most platforms.
    avg_gain = gain.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()

    rs = avg_gain / avg_loss
    df["RSI"] = 100 - (100 / (1 + rs))
    df["RSI_Change"] = df["RSI"] - df["RSI"].shift(1)

    return df


def add_atr(df, period=14):
    high_low = df["High"] - df["Low"]
    high_close = abs(df["High"] - df["Close"].shift())
    low_close = abs(df["Low"] - df["Close"].shift())

    true_range = pd.concat(
        [high_low, high_close, low_close],
        axis=1
    ).max(axis=1)

    # Wilder's smoothing for ATR.
    df["ATR"] = true_range.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    return df


def add_adx(df, period=14):
    high = df["High"]
    low = df["Low"]
    close = df["Close"]

    plus_dm = high.diff()
    minus_dm = low.diff() * -1

    plus_dm = plus_dm.where((plus_dm > minus_dm) & (plus_dm > 0), 0)
    minus_dm = minus_dm.where((minus_dm > plus_dm) & (minus_dm > 0), 0)

    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())

    true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    # Wilder's smoothing throughout the ADX calculation.
    alpha = 1 / period
    atr = true_range.ewm(alpha=alpha, adjust=False, min_periods=period).mean()

    plus_di = 100 * (
        plus_dm.ewm(alpha=alpha, adjust=False, min_periods=period).mean() / atr
    )
    minus_di = 100 * (
        minus_dm.ewm(alpha=alpha, adjust=False, min_periods=period).mean() / atr
    )

    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
    df["ADX"] = dx.ewm(alpha=alpha, adjust=False, min_periods=period).mean()

    return df


def add_bollinger_bands(df, period=20):
    df["BB_Middle"] = df["Close"].rolling(period).mean()
    df["BB_Std"] = df["Close"].rolling(period).std()
    df["BB_Upper"] = df["BB_Middle"] + (df["BB_Std"] * 2)
    df["BB_Lower"] = df["BB_Middle"] - (df["BB_Std"] * 2)
    df["BB_Width"] = (df["BB_Upper"] - df["BB_Lower"]) / df["BB_Middle"]
    return df


def add_money_flow(df, period=20):
    """
    Estimated capital flow using daily OHLCV data.
    This is not true order-flow; it estimates accumulation/distribution from price location and volume.
    """
    price_range = df["High"] - df["Low"]
    price_range = price_range.replace(0, np.nan)

    df["Money_Flow_Multiplier"] = (
        ((df["Close"] - df["Low"]) - (df["High"] - df["Close"])) / price_range
    )

    df["Money_Flow_Volume"] = df["Money_Flow_Multiplier"] * df["Volume"]

    df["CMF"] = (
        df["Money_Flow_Volume"].rolling(period).sum() /
        df["Volume"].rolling(period).sum()
    )

    df["OBV_Daily"] = 0
    df.loc[df["Close"] > df["Close"].shift(1), "OBV_Daily"] = df["Volume"]
    df.loc[df["Close"] < df["Close"].shift(1), "OBV_Daily"] = -df["Volume"]
    df["OBV"] = df["OBV_Daily"].cumsum()
    df["OBV_Change"] = df["OBV"] - df["OBV"].shift(5)

    typical_price = (df["High"] + df["Low"] + df["Close"]) / 3
    raw_money_flow = typical_price * df["Volume"]

    positive_flow = raw_money_flow.where(typical_price > typical_price.shift(1), 0)
    negative_flow = raw_money_flow.where(typical_price < typical_price.shift(1), 0)

    positive_mf = positive_flow.rolling(14).sum()
    negative_mf = negative_flow.rolling(14).sum()

    money_flow_ratio = positive_mf / negative_mf.replace(0, np.nan)
    df["MFI"] = 100 - (100 / (1 + money_flow_ratio))

    return df



def add_smart_money_flow(df, period=20):
    """
    Custom estimated buy/sell pressure indicator using daily OHLCV data.
    This is not true order-book flow. It estimates whether buyers or sellers controlled the candle.

    Logic:
    - Close near high = buying control
    - Green candle = buying pressure
    - Close above previous close = price confirmation
    - Strong relative volume = stronger confidence
    - Larger traded value = more meaningful flow
    """
    price_range = df["High"] - df["Low"]
    price_range = price_range.replace(0, np.nan)

    # +1 means close at high, -1 means close at low
    df["Close_Position_Score"] = (
        ((df["Close"] - df["Low"]) - (df["High"] - df["Close"])) / price_range
    )

    # Positive = green candle, negative = red candle
    df["Candle_Body_Score"] = (df["Close"] - df["Open"]) / price_range

    # Daily return scaled later in Buy_Sell_Pressure
    df["Price_Change_Score"] = df["Close"].pct_change()

    df["Smart_Relative_Volume"] = df["Volume"] / df["Volume"].rolling(period).mean()
    df["Traded_Value"] = df["Close"] * df["Volume"]

    # Estimated pressure, clipped to avoid extreme candles dominating the signal
    df["Buy_Sell_Pressure"] = (
        df["Close_Position_Score"] * 0.45 +
        df["Candle_Body_Score"] * 0.35 +
        df["Price_Change_Score"] * 20 * 0.20
    )
    df["Buy_Sell_Pressure"] = df["Buy_Sell_Pressure"].clip(-1, 1)

    # Estimated smart flow value: pressure × relative volume × money traded
    df["Smart_Money_Flow"] = (
        df["Buy_Sell_Pressure"] *
        df["Smart_Relative_Volume"] *
        df["Traded_Value"]
    )

    # Short and medium accumulation/distribution windows
    df["Smart_Money_Flow_5D"] = df["Smart_Money_Flow"].rolling(5).sum()
    df["Smart_Money_Flow_20D"] = df["Smart_Money_Flow"].rolling(20).sum()

    # Normalized score: easier to compare between high-price and low-price stocks
    avg_traded_value = df["Traded_Value"].rolling(period).mean()
    df["Smart_Money_Flow_Score"] = df["Smart_Money_Flow_5D"] / avg_traded_value
    df["Smart_Money_Flow_Score"] = df["Smart_Money_Flow_Score"].clip(-5, 5)

    return df


def add_indicators(df):
    if df is None or df.empty:
        return None

    df = df.copy()

    df = add_macd(df)
    df = add_rsi(df)
    df = add_atr(df)
    df = add_adx(df)

    df["Volume_Avg20"] = df["Volume"].rolling(20).mean()
    df["Relative_Volume"] = df["Volume"] / df["Volume_Avg20"]

    df["MA20"] = df["Close"].rolling(20).mean()
    df["MA50"] = df["Close"].rolling(50).mean()
    df["MA200"] = df["Close"].rolling(200).mean()

    df["Support"] = df["Low"].rolling(20).min()
    df["Resistance"] = df["High"].rolling(20).max()

    df = add_bollinger_bands(df)
    df = add_money_flow(df)
    df = add_smart_money_flow(df)

    df.dropna(inplace=True)

    if len(df) < 5:
        return None

    return df


def calculate_relative_strength(stock_df, benchmark_df, days=20):
    try:
        if stock_df is None or benchmark_df is None:
            return None

        if len(stock_df) <= days or len(benchmark_df) <= days:
            return None

        benchmark_close = benchmark_df["Close"].reindex(stock_df.index).ffill()

        stock_return = stock_df["Close"].pct_change(days).iloc[-1]
        benchmark_return = benchmark_close.pct_change(days).iloc[-1]

        if pd.isna(stock_return) or pd.isna(benchmark_return):
            return None

        return stock_return - benchmark_return

    except Exception:
        return None


@st.cache_data(ttl=3600)
def get_analyst_target(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        target_mean = info.get("targetMeanPrice", None)
        target_high = info.get("targetHighPrice", None)
        target_low = info.get("targetLowPrice", None)

        return target_mean, target_high, target_low

    except Exception:
        return None, None, None


def get_benchmark_data(market_name, period="2y", min_rows=120):
    """
    Get benchmark indicator data with fallback.
    Malaysia primary benchmark is ^KLSE. Singapore primary benchmark is ^STI.
    If index data fails, fallback to large liquid bank/ETF proxies.
    """
    if market_name == "US":
        candidates = ["SPY", "VOO", "QQQ"]
    elif market_name == "Malaysia":
        candidates = ["^KLSE", "1155.KL", "1023.KL", "1295.KL"]
    elif market_name == "Singapore":
        candidates = ["^STI", "ES3.SI", "D05.SI", "O39.SI", "U11.SI"]
    else:
        candidates = ["SPY"]

    for ticker in candidates:
        raw = get_data(ticker, period=period, min_rows=min_rows, market_name=market_name)
        ind = add_indicators(raw)
        if ind is not None and not ind.empty:
            return ticker, ind

    return None, None


def get_market_trend(market_name):
    if market_name == "US":
        benchmark_used, ind_1 = get_benchmark_data("US", period="2y", min_rows=120)
        raw_2 = get_data("QQQ", period="2y", min_rows=120, market_name="US")
        ind_2 = add_indicators(raw_2)

        if ind_1 is None or ind_2 is None:
            return "Unknown"

        latest_1 = ind_1.iloc[-1]
        latest_2 = ind_2.iloc[-1]

        close_1 = value(latest_1["Close"])
        ma50_1 = value(latest_1["MA50"])
        ma200_1 = value(latest_1["MA200"])

        close_2 = value(latest_2["Close"])
        ma50_2 = value(latest_2["MA50"])
        ma200_2 = value(latest_2["MA200"])

        first_bullish = close_1 > ma50_1 and close_1 > ma200_1
        first_bearish = close_1 < ma50_1 and close_1 < ma200_1
        second_bullish = close_2 > ma50_2 and close_2 > ma200_2
        second_bearish = close_2 < ma50_2 and close_2 < ma200_2

        if first_bullish and second_bullish:
            return "Bullish"
        elif first_bearish and second_bearish:
            return "Bearish"
        else:
            return "Mixed"

    benchmark_used, benchmark_df = get_benchmark_data(market_name, period="2y", min_rows=120)

    if benchmark_df is None:
        return "Unknown"

    latest = benchmark_df.iloc[-1]
    close = value(latest["Close"])
    ma50 = value(latest["MA50"])
    ma200 = value(latest["MA200"])

    if close > ma50 and close > ma200:
        return "Bullish"
    elif close < ma50 and close < ma200:
        return "Bearish"
    else:
        return "Mixed"

def get_final_view(score, market_trend):
    if market_trend == "Bearish":
        if score >= 9:
            return "Careful Watchlist"
        return "Avoid"

    if score >= 9:
        return "Strong Watchlist"
    elif score >= 6:
        return "Watchlist"
    elif score >= 4:
        return "Neutral"
    else:
        return "Avoid"


def build_early_signal(
    close,
    ma20,
    rsi,
    rsi_change,
    macd_hist_change,
    relative_volume,
    bb_upper,
    bb_lower,
    relative_strength
):
    early_signal = []

    if macd_hist_change > 0 and rsi < 50 and rsi_change > 0:
        early_signal.append("Early rebound attempt")

    if macd_hist_change < 0 and rsi > 60:
        early_signal.append("Momentum slowing")

    if relative_volume >= 2 and close > ma20:
        early_signal.append("Unusual buying volume")

    if relative_volume >= 2 and close < ma20:
        early_signal.append("Unusual selling pressure")

    if close > bb_upper:
        early_signal.append("Breakout above Bollinger Band")

    if close < bb_lower:
        early_signal.append("Breakdown below Bollinger Band")

    if relative_strength > 0 and macd_hist_change > 0 and close > ma20:
        early_signal.append("Early bullish confirmation")

    if relative_strength < 0 and macd_hist_change < 0 and close < ma20:
        early_signal.append("Early bearish warning")

    if not early_signal:
        early_signal.append("No clear early signal")

    return ", ".join(early_signal)



def calculate_capital_flow_score(cmf, obv_change, mfi):
    """Return capital-flow score and readable signal."""
    capital_flow_score = 0
    capital_flow_signal = []

    if cmf > 0.20 and obv_change > 0:
        capital_flow_score += 3
        capital_flow_signal.append("Strong inflow / accumulation")
    elif cmf > 0.10 and obv_change > 0:
        capital_flow_score += 2
        capital_flow_signal.append("Positive inflow")
    elif cmf > 0:
        capital_flow_score += 1
        capital_flow_signal.append("Mild inflow")
    elif cmf < -0.20 and obv_change < 0:
        capital_flow_score -= 3
        capital_flow_signal.append("Strong outflow / distribution")
    elif cmf < -0.10 and obv_change < 0:
        capital_flow_score -= 2
        capital_flow_signal.append("Negative outflow")
    elif cmf < 0:
        capital_flow_score -= 1
        capital_flow_signal.append("Mild outflow")
    else:
        capital_flow_signal.append("Neutral capital flow")

    if 40 <= mfi <= 80:
        capital_flow_score += 1
        capital_flow_signal.append("MFI healthy")
    elif mfi > 85:
        capital_flow_score -= 1
        capital_flow_signal.append("MFI overbought")
    elif mfi < 20:
        capital_flow_score -= 1
        capital_flow_signal.append("MFI very weak")

    return capital_flow_score, ", ".join(capital_flow_signal)


def get_smart_money_signal(smart_money_flow_score):
    if smart_money_flow_score >= 2:
        return "Strong Buying Pressure"
    elif smart_money_flow_score >= 1:
        return "Buying Pressure"
    elif smart_money_flow_score > 0:
        return "Mild Buying"
    elif smart_money_flow_score <= -2:
        return "Strong Selling Pressure"
    elif smart_money_flow_score <= -1:
        return "Selling Pressure"
    elif smart_money_flow_score < 0:
        return "Mild Selling"
    return "Neutral"


def calculate_smart_money_score(smart_money_flow_score):
    """Convert custom smart money flow score into scanner score impact."""
    if smart_money_flow_score >= 2:
        return 3, "Strong smart money buying pressure"
    elif smart_money_flow_score >= 1:
        return 2, "Smart money inflow"
    elif smart_money_flow_score > 0:
        return 1, "Mild smart money inflow"
    elif smart_money_flow_score <= -2:
        return -3, "Strong smart money selling pressure"
    elif smart_money_flow_score <= -1:
        return -2, "Smart money outflow"
    elif smart_money_flow_score < 0:
        return -1, "Mild smart money outflow"
    return 0, "Neutral smart money flow"


def get_buy_sell_safety(score, cmf, obv_change, mfi, smart_money_flow_score, rsi, close, ma20, ma50):
    if (
        score >= 9 and
        cmf > 0.10 and
        obv_change > 0 and
        smart_money_flow_score > 1 and
        40 <= mfi <= 80 and
        close > ma20 and
        close > ma50 and
        rsi < 75
    ):
        return "Safer Buy Setup"

    if (
        score >= 6 and
        cmf > 0 and
        obv_change > 0 and
        smart_money_flow_score > 0 and
        close > ma20
    ):
        return "Watch Buy Setup"

    if (
        cmf < -0.10 and
        obv_change < 0 and
        smart_money_flow_score < -1 and
        close < ma20
    ):
        return "Sell / Avoid Warning"

    if rsi > 80 or mfi > 85:
        return "Too Hot / Avoid Chasing"

    return "Neutral / Wait"

def analyse_stock(ticker, benchmark_df, market_name):
    raw_df = get_data(ticker, period="2y", min_rows=250, market_name=market_name)

    if raw_df is None:
        return None

    df = add_indicators(raw_df)

    if df is None or len(df) < 2:
        return None

    relative_strength = calculate_relative_strength(df, benchmark_df)

    if relative_strength is None:
        return None

    latest = df.iloc[-1]

    close = value(latest["Close"])
    rsi = value(latest["RSI"])
    rsi_change = value(latest["RSI_Change"])
    macd = value(latest["MACD"])
    signal = value(latest["Signal"])
    macd_hist = value(latest["MACD_Hist"])
    macd_hist_change = value(latest["MACD_Hist_Change"])
    volume = value(latest["Volume"])
    volume_avg20 = value(latest["Volume_Avg20"])
    relative_volume = value(latest["Relative_Volume"])
    ma20 = value(latest["MA20"])
    ma50 = value(latest["MA50"])
    ma200 = value(latest["MA200"])
    support = value(latest["Support"])
    resistance = value(latest["Resistance"])
    adx = value(latest["ADX"])
    atr = value(latest["ATR"])
    bb_upper = value(latest["BB_Upper"])
    bb_lower = value(latest["BB_Lower"])
    bb_width = value(latest["BB_Width"])
    cmf = value(latest["CMF"])
    mfi = value(latest["MFI"])
    obv_change = value(latest["OBV_Change"])
    money_flow_volume = value(latest["Money_Flow_Volume"])
    buy_sell_pressure = value(latest["Buy_Sell_Pressure"])
    smart_money_flow_score = value(latest["Smart_Money_Flow_Score"])
    smart_money_flow_5d = value(latest["Smart_Money_Flow_5D"])
    smart_money_flow_20d = value(latest["Smart_Money_Flow_20D"])

    values_to_check = [
        close, rsi, rsi_change, macd, signal, macd_hist,
        macd_hist_change, volume, volume_avg20, relative_volume,
        ma20, ma50, ma200, support, resistance, adx, atr,
        bb_upper, bb_lower, bb_width, cmf, mfi, obv_change,
        money_flow_volume, buy_sell_pressure, smart_money_flow_score,
        smart_money_flow_5d, smart_money_flow_20d, relative_strength
    ]

    if any(pd.isna(x) for x in values_to_check):
        return None

    if close <= 0 or atr <= 0:
        return None

    score = 0
    reasons = []

    if market_name == "US":
        volume_multiplier = 1.5
        rsi_low = 45
        rsi_high = 70
        adx_min = 25
        benchmark_name = "SPY"
    elif market_name == "Malaysia":
        volume_multiplier = 1.2
        rsi_low = 40
        rsi_high = 65
        adx_min = 20
        benchmark_name = "KLCI"
    else:
        volume_multiplier = 1.2
        rsi_low = 40
        rsi_high = 65
        adx_min = 20
        benchmark_name = "STI"

    if close > ma200:
        score += 2
        reasons.append("Price above 200MA")
    else:
        score -= 2
        reasons.append("Below 200MA")

    if close > ma50:
        score += 2
        reasons.append("Price above 50MA")

    if close > ma20:
        score += 1
        reasons.append("Price above 20MA")

    if relative_strength > 0:
        score += 2
        reasons.append(f"Outperforming {benchmark_name}")
    else:
        score -= 1
        reasons.append(f"Underperforming {benchmark_name}")

    if volume > volume_avg20 * volume_multiplier:
        score += 2
        reasons.append(f"Volume > {int(volume_multiplier * 100)}% average")

    if macd > signal:
        score += 1
        reasons.append("MACD bullish")

    if rsi_low <= rsi <= rsi_high:
        score += 1
        reasons.append("RSI healthy")

    if adx > adx_min:
        score += 1
        reasons.append("Strong trend strength")

    if macd_hist_change > 0:
        score += 1
        reasons.append("MACD histogram improving")

    if macd_hist > 0 and macd_hist_change > 0:
        score += 1
        reasons.append("Positive momentum increasing")

    if relative_volume >= 2:
        score += 2
        reasons.append("Very strong relative volume")
    elif relative_volume >= 1.5:
        score += 1
        reasons.append("Strong relative volume")

    if close > bb_upper:
        score += 1
        reasons.append("Bollinger upper breakout")

    if close < bb_lower:
        score -= 1
        reasons.append("Below Bollinger lower band")

    capital_flow_score, capital_flow_signal = calculate_capital_flow_score(
        cmf=cmf,
        obv_change=obv_change,
        mfi=mfi
    )
    score += capital_flow_score
    reasons.append(capital_flow_signal)

    smart_money_score, smart_money_reason = calculate_smart_money_score(smart_money_flow_score)
    smart_money_signal = get_smart_money_signal(smart_money_flow_score)
    score += smart_money_score
    reasons.append(smart_money_reason)

    if rsi > 80:
        score -= 3
        reasons.append("Extremely overbought")
    elif rsi > 75:
        score -= 2
        reasons.append("Overbought")

    if rsi < 30:
        score -= 1
        reasons.append("Very weak RSI")

    if close >= resistance * 0.98:
        score -= 2
        reasons.append("Very close to resistance")

    early_signal = build_early_signal(
        close=close,
        ma20=ma20,
        rsi=rsi,
        rsi_change=rsi_change,
        macd_hist_change=macd_hist_change,
        relative_volume=relative_volume,
        bb_upper=bb_upper,
        bb_lower=bb_lower,
        relative_strength=relative_strength
    )

    buy_sell_safety = get_buy_sell_safety(
        score=score,
        cmf=cmf,
        obv_change=obv_change,
        mfi=mfi,
        smart_money_flow_score=smart_money_flow_score,
        rsi=rsi,
        close=close,
        ma20=ma20,
        ma50=ma50
    )

    target_1 = resistance
    target_2 = close + atr
    target_3 = close + (atr * 2)

    if close < resistance:
        technical_target = resistance
    else:
        technical_target = close + atr

    stop_loss = close - atr

    upside_percent = ((technical_target - close) / close) * 100
    risk_percent = ((close - stop_loss) / close) * 100
    reward_percent = upside_percent

    risk_reward = reward_percent / risk_percent if risk_percent > 0 else None

    target_mean, target_high, target_low = get_analyst_target(ticker)

    price_decimal = 3 if market_name in ["Malaysia", "Singapore"] else 2

    return {
        "Ticker": ticker,
        "Name": get_stock_name(ticker),
        "Stock": f"{ticker} | {get_stock_name(ticker)}",
        "Close": round(close, price_decimal),
        "Score": score,
        "Buy_Sell_Safety": buy_sell_safety,
        "Capital_Flow_Score": capital_flow_score,
        "Capital_Flow_Signal": capital_flow_signal,
        "CMF": round(cmf, 4),
        "MFI": round(mfi, 2),
        "OBV_Change": round(obv_change, 2),
        "Money_Flow_Volume": round(money_flow_volume, 2),
        "Smart_Money_Signal": smart_money_signal,
        "Smart_Money_Flow_Score": round(smart_money_flow_score, 2),
        "Buy_Sell_Pressure": round(buy_sell_pressure, 4),
        "Smart_Money_Flow_5D": round(smart_money_flow_5d, 2),
        "Smart_Money_Flow_20D": round(smart_money_flow_20d, 2),
        "RSI": round(rsi, 2),
        "RSI_Change": round(rsi_change, 2),
        "MACD": round(macd, 4),
        "Signal": round(signal, 4),
        "MACD_Hist": round(macd_hist, 4),
        "MACD_Hist_Change": round(macd_hist_change, 4),
        "Relative_Volume": round(relative_volume, 2),
        "BB_Width": round(bb_width, 4),
        "Early_Signal": early_signal,
        "MA20": round(ma20, price_decimal),
        "MA50": round(ma50, price_decimal),
        "MA200": round(ma200, price_decimal),
        "Support": round(support, price_decimal),
        "Resistance": round(resistance, price_decimal),
        "ADX": round(adx, 2),
        "ATR": round(atr, price_decimal),
        "Relative_Strength": round(relative_strength, 4),
        "Technical_Target": round(technical_target, price_decimal),
        "Target_1_Resistance": round(target_1, price_decimal),
        "Target_2_Close_1ATR": round(target_2, price_decimal),
        "Target_3_Close_2ATR": round(target_3, price_decimal),
        "Stop_Loss": round(stop_loss, price_decimal),
        "Upside_%": round(upside_percent, 2),
        "Risk_%": round(risk_percent, 2),
        "Risk_Reward": round(risk_reward, 2) if risk_reward is not None else None,
        "Analyst_Target_Mean": round(target_mean, price_decimal) if target_mean else None,
        "Analyst_Target_High": round(target_high, price_decimal) if target_high else None,
        "Analyst_Target_Low": round(target_low, price_decimal) if target_low else None,
        "Reasons": ", ".join(reasons)
    }


def calculate_practical_rank(row, market_name):
    practical_score = 0
    notes = []

    score = row["Score"]
    risk_reward = row["Risk_Reward"]
    upside = row["Upside_%"]
    rsi = row["RSI"]
    adx = row["ADX"]
    close = row["Close"]
    resistance = row["Resistance"]
    relative_strength = row["Relative_Strength"]
    macd_hist_change = row["MACD_Hist_Change"]
    relative_volume = row["Relative_Volume"]
    capital_flow_score = row.get("Capital_Flow_Score", 0)
    cmf = row.get("CMF", 0)
    obv_change = row.get("OBV_Change", 0)
    smart_money_flow_score = row.get("Smart_Money_Flow_Score", 0)

    if market_name == "US":
        rsi_low = 45
        rsi_high = 70
        adx_min = 25
        benchmark_name = "SPY"
    elif market_name == "Malaysia":
        rsi_low = 40
        rsi_high = 65
        adx_min = 20
        benchmark_name = "KLCI"
    else:
        rsi_low = 40
        rsi_high = 65
        adx_min = 20
        benchmark_name = "STI"

    practical_score += score

    if risk_reward is not None and risk_reward >= 2:
        practical_score += 3
        notes.append("Good risk/reward")
    elif risk_reward is not None and risk_reward < 1:
        practical_score -= 3
        notes.append("Poor risk/reward")

    if upside >= 5:
        practical_score += 3
        notes.append("Upside above 5%")
    elif upside < 2:
        practical_score -= 2
        notes.append("Limited upside")

    if rsi_low <= rsi <= rsi_high:
        practical_score += 2
        notes.append("Healthy RSI")
    elif rsi > 80:
        practical_score -= 4
        notes.append("Too overbought")
    elif rsi < 30:
        practical_score -= 2
        notes.append("Very weak RSI")

    if adx >= adx_min:
        practical_score += 2
        notes.append("Strong trend")
    elif adx < 20:
        practical_score -= 1
        notes.append("Weak trend")

    if relative_strength > 0:
        practical_score += 2
        notes.append(f"Outperforming {benchmark_name}")
    else:
        practical_score -= 1
        notes.append(f"Underperforming {benchmark_name}")

    if macd_hist_change > 0:
        practical_score += 1
        notes.append("Momentum improving")

    if relative_volume >= 1.5:
        practical_score += 1
        notes.append("Volume activity rising")

    practical_score += capital_flow_score
    if cmf > 0.10 and obv_change > 0:
        notes.append("Capital flow supports buy")
    elif cmf < -0.10 and obv_change < 0:
        notes.append("Capital flow warning")

    smart_money_score, smart_money_reason = calculate_smart_money_score(smart_money_flow_score)
    practical_score += smart_money_score
    notes.append(smart_money_reason)

    if close >= resistance * 0.98:
        practical_score -= 3
        notes.append("Too close to resistance")

    return practical_score, ", ".join(notes)


def dataframe_to_excel(df, sheet_name):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
    return output.getvalue()


# ============================================================
# Display Styling Helpers
# ============================================================

DISPLAY_COLUMN_RENAME = {
    "Name": "Stock Name",
    "Stock": "Stock",
    "Buy_Sell_Safety": "Buy/Sell Safety",
    "Practical_Rank_Score": "Practical Score",
    "Smart_Money_Signal": "Smart Money Signal",
    "Smart_Money_Flow_Score": "Smart Money Score",
    "Buy_Sell_Pressure": "Buy/Sell Pressure",
    "Capital_Flow_Score": "Capital Flow Score",
    "Capital_Flow_Signal": "Capital Flow",
    "Relative_Volume": "Rel Volume",
    "Relative_Strength": "Rel Strength",
    "Risk_Reward": "Risk/Reward",
    "Upside_%": "Upside %",
    "Risk_%": "Risk %",
    "MACD_Hist": "MACD Hist",
    "MACD_Hist_Change": "MACD Hist Change",
    "Money_Flow_Volume": "Money Flow Volume",
    "Early_Signal": "Early Signal",
    "Final View": "Final View",
}


def make_display_df(df):
    """
    Rename technical column names into cleaner dashboard labels.

    Streamlit freezes the dataframe index on the far-left side.
    Therefore, we set the combined Stock column as the index so you can still
    see the stock identity when scrolling horizontally.
    """
    if df is None or df.empty:
        return df

    display_df = df.rename(columns=DISPLAY_COLUMN_RENAME).copy()

    if "Stock" not in display_df.columns:
        if "Ticker" in display_df.columns and "Stock Name" in display_df.columns:
            display_df["Stock"] = (
                display_df["Ticker"].astype(str) + " | " + display_df["Stock Name"].astype(str)
            )
        elif "Ticker" in display_df.columns:
            display_df["Stock"] = display_df["Ticker"].astype(str)

    if "Stock" in display_df.columns:
        display_df = display_df.set_index("Stock")
        drop_cols = [col for col in ["Ticker", "Stock Name"] if col in display_df.columns]
        if drop_cols:
            display_df = display_df.drop(columns=drop_cols)

    return display_df


def style_scanner_table(df):
    """Professional color styling for scanner result table."""
    if df is None or df.empty:
        return df

    def color_safety(val):
        val = str(val)
        if val == "Safer Buy Setup":
            return "background-color: #14532D; color: #DCFCE7; font-weight: 900;"
        if val == "Watch Buy Setup":
            return "background-color: #1E3A8A; color: #DBEAFE; font-weight: 900;"
        if val == "Too Hot / Avoid Chasing":
            return "background-color: #78350F; color: #FEF3C7; font-weight: 900;"
        if val == "Sell / Avoid Warning":
            return "background-color: #7F1D1D; color: #FEE2E2; font-weight: 900;"
        return "background-color: #374151; color: #E5E7EB;"

    def color_score(val):
        try:
            val = float(val)
        except Exception:
            return ""

        if val >= 30:
            return "color: #22C55E; font-weight: 900;"
        if val >= 20:
            return "color: #4ADE80; font-weight: 900;"
        if val >= 12:
            return "color: #38BDF8; font-weight: 900;"
        if val >= 6:
            return "color: #F59E0B; font-weight: 900;"
        return "color: #EF4444; font-weight: 900;"

    def color_risk_reward(val):
        try:
            val = float(val)
        except Exception:
            return ""

        if val >= 3:
            return "color: #22C55E; font-weight: 900;"
        if val >= 2:
            return "color: #4ADE80; font-weight: 800;"
        if val >= 1:
            return "color: #F59E0B; font-weight: 800;"
        return "color: #EF4444; font-weight: 800;"

    def color_money_signal(val):
        val = str(val)
        if "Strong Buying" in val or val == "Buying Pressure":
            return "background-color: #064E3B; color: #D1FAE5; font-weight: 900;"
        if "Mild Buying" in val:
            return "background-color: #065F46; color: #ECFDF5; font-weight: 800;"
        if "Strong Selling" in val or val == "Selling Pressure":
            return "background-color: #7F1D1D; color: #FEE2E2; font-weight: 900;"
        if "Mild Selling" in val:
            return "background-color: #991B1B; color: #FEE2E2; font-weight: 800;"
        return "background-color: #334155; color: #E5E7EB;"

    styled = df.style

    if "Buy/Sell Safety" in df.columns:
        styled = styled.map(color_safety, subset=["Buy/Sell Safety"])

    score_cols = [c for c in ["Score", "Practical Score"] if c in df.columns]
    if score_cols:
        styled = styled.map(color_score, subset=score_cols)

    if "Risk/Reward" in df.columns:
        styled = styled.map(color_risk_reward, subset=["Risk/Reward"])

    if "Smart Money Signal" in df.columns:
        styled = styled.map(color_money_signal, subset=["Smart Money Signal"])

    numeric_cols = [
        c for c in df.columns
        if c not in [
            "Ticker", "Stock Name", "Buy/Sell Safety", "Final View", "Smart Money Signal",
            "Capital Flow", "Early Signal", "Practical_Notes", "Reasons"
        ]
    ]

    format_dict = {}
    for col in numeric_cols:
        format_dict[col] = "{:,.2f}"

    styled = styled.format(format_dict, na_rep="-")
    return styled


def render_section_header(title, subtitle=None):
    """Reusable premium section header."""
    subtitle_html = ""
    if subtitle:
        subtitle_html = f'<div style="color:#94A3B8; font-size:14px; margin-top:4px;">{subtitle}</div>'

    st.markdown(
        f"""
        <div style="
            background: rgba(15, 23, 42, 0.76);
            border: 1px solid #334155;
            border-radius: 18px;
            padding: 16px 20px;
            margin: 14px 0 18px 0;
        ">
            <div style="color:#F8FAFC; font-size:22px; font-weight:900; letter-spacing:-0.02em;">{title}</div>
            {subtitle_html}
        </div>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# Page 2 Backtest Functions
# ============================================================

def backtest_strategy(
    ticker,
    market_name,
    benchmark_ticker,
    initial_capital=10000,
    holding_days=5,
    take_profit_pct=6,
    stop_loss_pct=3
):
    raw_df = get_data(ticker, period="5y", min_rows=250)

    if raw_df is None:
        return None, None, f"No price data for {ticker}. Check ticker format, for example TSLA or 6947.KL."

    df = add_indicators(raw_df)

    if df is None or len(df) < 80:
        return None, None, f"Not enough indicator data for {ticker}."

    if market_name in ["Malaysia", "Singapore"]:
        benchmark_used, benchmark_df = get_benchmark_data(market_name, period="5y", min_rows=120)

        if benchmark_df is None or len(benchmark_df) < 80:
            return None, None, f"No {market_name} benchmark data available. Try again later or use US first."
    else:
        benchmark_used = benchmark_ticker
        benchmark_raw = get_data(benchmark_ticker, period="5y", min_rows=250)

        if benchmark_raw is None:
            return None, None, f"No benchmark data for {benchmark_ticker}."

        benchmark_df = add_indicators(benchmark_raw)

        if benchmark_df is None or len(benchmark_df) < 80:
            return None, None, f"Not enough benchmark indicator data for {benchmark_ticker}."

    df = df.copy()

    benchmark_close = benchmark_df["Close"].reindex(df.index).ffill()

    df["Relative_Strength"] = (
        df["Close"].pct_change(20) -
        benchmark_close.pct_change(20)
    )

    trades = []
    capital = float(initial_capital)

    start_index = 60

    for i in range(start_index, len(df) - holding_days):
        row = df.iloc[i]

        close = row["Close"]
        rsi = row["RSI"]
        macd_hist_change = row["MACD_Hist_Change"]
        relative_volume = row["Relative_Volume"]
        ma20 = row["MA20"]
        ma50 = row["MA50"]
        ma200 = row["MA200"]
        relative_strength = row["Relative_Strength"]
        cmf = row["CMF"]
        mfi = row["MFI"]
        obv_change = row["OBV_Change"]
        smart_money_flow_score = row["Smart_Money_Flow_Score"]

        if any(pd.isna(x) for x in [
            close, rsi, macd_hist_change, relative_volume,
            ma20, ma50, ma200, relative_strength, cmf, mfi, obv_change,
            smart_money_flow_score
        ]):
            continue

        if market_name == "US":
            rsi_low, rsi_high = 45, 70
            volume_trigger = 1.5
        else:
            rsi_low, rsi_high = 40, 65
            volume_trigger = 1.2

        buy_signal = (
            close > ma20 and
            close > ma50 and
            close > ma200 and
            rsi_low <= rsi <= rsi_high and
            macd_hist_change > 0 and
            relative_volume >= volume_trigger and
            relative_strength > 0 and
            cmf > 0 and
            obv_change > 0 and
            smart_money_flow_score > 0 and
            40 <= mfi <= 85
        )

        if buy_signal:
            entry_date = df.index[i]
            entry_price = close

            stop_price = entry_price * (1 - stop_loss_pct / 100)
            target_price = entry_price * (1 + take_profit_pct / 100)

            exit_price = None
            exit_date = None
            exit_reason = None

            future_df = df.iloc[i + 1:i + 1 + holding_days]

            for future_date, future_row in future_df.iterrows():
                low = future_row["Low"]
                high = future_row["High"]
                future_close = future_row["Close"]

                if low <= stop_price:
                    exit_price = stop_price
                    exit_date = future_date
                    exit_reason = "Stop Loss"
                    break

                if high >= target_price:
                    exit_price = target_price
                    exit_date = future_date
                    exit_reason = "Take Profit"
                    break

                exit_price = future_close
                exit_date = future_date
                exit_reason = "Time Exit"

            if exit_price is None:
                continue

            trade_return = ((exit_price - entry_price) / entry_price) * 100
            capital = capital * (1 + trade_return / 100)

            trades.append({
                "Entry Date": entry_date,
                "Exit Date": exit_date,
                "Entry Price": round(entry_price, 2),
                "Exit Price": round(exit_price, 2),
                "Return %": round(trade_return, 2),
                "Exit Reason": exit_reason,
                "Capital": round(capital, 2)
            })

    if not trades:
        return pd.DataFrame(), {
            "Total Trades": 0,
            "Win Rate %": 0,
            "Average Return %": 0,
            "Total Return %": 0,
            "Final Capital": initial_capital,
            "Profit Factor": None,
            "Best Trade %": 0,
            "Worst Trade %": 0
        }, "No trades found. The strategy rule may be too strict. Try another ticker or relax the rule."

    trades_df = pd.DataFrame(trades)

    total_trades = len(trades_df)
    wins = len(trades_df[trades_df["Return %"] > 0])
    win_rate = (wins / total_trades) * 100
    avg_return = trades_df["Return %"].mean()
    total_return = ((capital - initial_capital) / initial_capital) * 100

    gross_profit = trades_df[trades_df["Return %"] > 0]["Return %"].sum()
    gross_loss = abs(trades_df[trades_df["Return %"] < 0]["Return %"].sum())

    profit_factor = gross_profit / gross_loss if gross_loss > 0 else None

    summary = {
        "Total Trades": total_trades,
        "Win Rate %": round(win_rate, 2),
        "Average Return %": round(avg_return, 2),
        "Total Return %": round(total_return, 2),
        "Final Capital": round(capital, 2),
        "Profit Factor": round(profit_factor, 2) if profit_factor else None,
        "Best Trade %": round(trades_df["Return %"].max(), 2),
        "Worst Trade %": round(trades_df["Return %"].min(), 2)
    }

    return trades_df, summary, "Backtest completed."


# ============================================================
# Page 3 Options Functions
# ============================================================

def get_options_chain(ticker, expiry):
    try:
        stock = yf.Ticker(ticker)
        chain = stock.option_chain(expiry)

        calls = chain.calls.copy()
        puts = chain.puts.copy()

        return calls, puts

    except Exception:
        return None, None


def analyse_options_table(options_df, current_price, option_type):
    if options_df is None or options_df.empty:
        return pd.DataFrame()

    df = options_df.copy()

    needed_cols = [
        "contractSymbol", "strike", "lastPrice", "bid", "ask",
        "volume", "openInterest", "impliedVolatility"
    ]

    for col in needed_cols:
        if col not in df.columns:
            df[col] = None

    df["Mid"] = (df["bid"] + df["ask"]) / 2
    df["Spread_%"] = ((df["ask"] - df["bid"]) / df["Mid"]) * 100
    df["Spread_%"] = df["Spread_%"].replace([float("inf"), -float("inf")], None)

    if option_type == "Call":
        df["Moneyness_%"] = ((current_price - df["strike"]) / current_price) * 100
        df["Breakeven"] = df["strike"] + df["lastPrice"]
        df["Breakeven_Move_%"] = ((df["Breakeven"] - current_price) / current_price) * 100
    else:
        df["Moneyness_%"] = ((df["strike"] - current_price) / current_price) * 100
        df["Breakeven"] = df["strike"] - df["lastPrice"]
        df["Breakeven_Move_%"] = ((current_price - df["Breakeven"]) / current_price) * 100

    df["Liquidity_Score"] = 0

    df.loc[df["volume"].fillna(0) > 100, "Liquidity_Score"] += 1
    df.loc[df["openInterest"].fillna(0) > 500, "Liquidity_Score"] += 1
    df.loc[df["Spread_%"].fillna(999) < 15, "Liquidity_Score"] += 1

    df["Option_View"] = "Avoid / Illiquid"

    df.loc[
        (df["Liquidity_Score"] >= 2) &
        (df["Breakeven_Move_%"] <= 5),
        "Option_View"
    ] = "Watchlist"

    df.loc[
        (df["Liquidity_Score"] == 3) &
        (df["Breakeven_Move_%"] <= 3),
        "Option_View"
    ] = "Better Liquidity"

    columns = [
        "contractSymbol",
        "strike",
        "lastPrice",
        "bid",
        "ask",
        "Mid",
        "Spread_%",
        "volume",
        "openInterest",
        "impliedVolatility",
        "Moneyness_%",
        "Breakeven",
        "Breakeven_Move_%",
        "Liquidity_Score",
        "Option_View"
    ]

    df = df[columns]

    numeric_cols = [
        "strike", "lastPrice", "bid", "ask", "Mid", "Spread_%",
        "impliedVolatility", "Moneyness_%", "Breakeven", "Breakeven_Move_%"
    ]

    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").round(2)

    df = df.sort_values(
        by=["Liquidity_Score", "openInterest", "volume"],
        ascending=[False, False, False]
    )

    return df


# ============================================================
# Page 4 Chart Function
# ============================================================

def get_chart_download_config(display_period):
    """
    Map user-friendly chart period to yfinance-compatible download period and interval.
    We download extra history when needed so MA200/Bollinger/MACD can be calculated properly,
    then filter the chart to the selected display period.
    """
    mapping = {
        "1d": {"download_period": "5d", "interval": "5m", "lookback_days": 1},
        "1wk": {"download_period": "1mo", "interval": "15m", "lookback_days": 7},
        "2wk": {"download_period": "1mo", "interval": "30m", "lookback_days": 14},
        "1mo": {"download_period": "2y", "interval": "1d", "lookback_days": 31},
        "3mo": {"download_period": "2y", "interval": "1d", "lookback_days": 93},
        "6mo": {"download_period": "2y", "interval": "1d", "lookback_days": 186},
        "1y": {"download_period": "2y", "interval": "1d", "lookback_days": 370},
        "2y": {"download_period": "2y", "interval": "1d", "lookback_days": None},
        "5y": {"download_period": "5y", "interval": "1d", "lookback_days": None},
        "10y": {"download_period": "10y", "interval": "1d", "lookback_days": None},
        "max": {"download_period": "max", "interval": "1d", "lookback_days": None},
    }
    return mapping.get(display_period, mapping["1y"])

def filter_display_period(df, lookback_days):
    if df is None or df.empty or lookback_days is None:
        return df

    end_date = df.index.max()
    start_date = end_date - pd.Timedelta(days=lookback_days)
    return df[df.index >= start_date].copy()

def normalize_ticker_for_market(ticker, market_name):
    """Make ticker input easier for Page 4."""
    ticker = str(ticker).strip().upper()

    if ticker.startswith("^"):
        return ticker

    return normalize_user_ticker(ticker, market_name)


def adjust_chart_config_for_market(ticker, market_name, period, data_source):
    """Adjust period/interval/source so Malaysia charts do not fail.

    Yahoo Finance often has daily Bursa data, but intraday 5m/15m/30m for .KL
    is often unavailable. For Malaysia, short periods are therefore shown using
    daily candles with extra downloaded history so indicators can calculate.
    """
    config = get_chart_download_config(period).copy()
    note = None

    if market_name in ["Malaysia", "Singapore"]:
        if data_source in (None, "Auto"):
            data_source = "Auto"

        # Bursa/SGX intraday data is often unavailable from yfinance.
        # Use daily candles instead, then filter to the selected display period.
        if period in ["1d", "1wk", "2wk"]:
            config["download_period"] = "2y"
            config["interval"] = "1d"
            config["lookback_days"] = {"1d": 7, "1wk": 14, "2wk": 21}[period]
            note = (
                f"{market_name} intraday data is often unavailable from Yahoo/yfinance. "
                f"Showing recent daily candles for {period} instead."
            )

    return ticker, config, data_source, note


def plot_stock_chart(ticker, period="1y", data_source="Auto", market_name="US"):
    ticker = normalize_ticker_for_market(ticker, market_name)
    ticker, config, data_source, chart_note = adjust_chart_config_for_market(
        ticker=ticker,
        market_name=market_name,
        period=period,
        data_source=data_source
    )

    download_period = config["download_period"]
    interval = config["interval"]
    lookback_days = config["lookback_days"]

    raw_df = get_data(
        ticker,
        period=download_period,
        interval=interval,
        min_rows=30,
        source=data_source,
        market_name=market_name
    )

    if raw_df is None:
        st.error(
            f"No data available for {ticker}. For Malaysia stocks, use ticker format like 6947.KL "
            "and select Yahoo Finance. Intraday Bursa charts may not be available."
        )
        return

    df_full = add_indicators(raw_df)

    if df_full is None or df_full.empty:
        st.error(f"Not enough indicator data for {ticker}.")
        return

    df = filter_display_period(df_full, lookback_days)

    if df is None or df.empty:
        st.error(f"No chart data after filtering for {period}.")
        return

    st.caption(f"Chart uses period {period}, downloaded {download_period} data at {interval} interval. Data source: {data_source}. Data refresh cache: 1 hour.")
    if chart_note:
        st.info(chart_note)

    fig = make_subplots(
        rows=5,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.035,
        row_heights=[0.45, 0.17, 0.13, 0.12, 0.13],
        subplot_titles=(
            f"{ticker} Price + Bollinger Bands",
            "MACD",
            "RSI",
            "Relative Volume",
            "Capital Flow"
        )
    )

    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df["Open"],
            high=df["High"],
            low=df["Low"],
            close=df["Close"],
            name="Price"
        ),
        row=1,
        col=1
    )

    fig.add_trace(go.Scatter(x=df.index, y=df["MA20"], name="MA20", mode="lines"), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df["MA50"], name="MA50", mode="lines"), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df["MA200"], name="MA200", mode="lines"), row=1, col=1)

    fig.add_trace(go.Scatter(x=df.index, y=df["BB_Upper"], name="BB Upper", mode="lines"), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df["BB_Lower"], name="BB Lower", mode="lines"), row=1, col=1)

    fig.add_trace(go.Scatter(x=df.index, y=df["MACD"], name="MACD", mode="lines"), row=2, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df["Signal"], name="Signal", mode="lines"), row=2, col=1)
    fig.add_trace(go.Bar(x=df.index, y=df["MACD_Hist"], name="MACD Histogram"), row=2, col=1)

    fig.add_trace(go.Scatter(x=df.index, y=df["RSI"], name="RSI", mode="lines"), row=3, col=1)
    fig.add_hline(y=70, line_dash="dash", row=3, col=1)
    fig.add_hline(y=30, line_dash="dash", row=3, col=1)

    fig.add_trace(go.Bar(x=df.index, y=df["Relative_Volume"], name="Relative Volume"), row=4, col=1)
    fig.add_hline(y=1.5, line_dash="dash", row=4, col=1)
    fig.add_hline(y=2.0, line_dash="dash", row=4, col=1)

    fig.add_trace(go.Bar(x=df.index, y=df["Money_Flow_Volume"], name="Money Flow Volume"), row=5, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df["CMF"], name="CMF", mode="lines"), row=5, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df["Smart_Money_Flow_Score"], name="Smart Money Flow Score", mode="lines"), row=5, col=1)
    fig.add_hline(y=0, line_dash="dash", row=5, col=1)
    fig.add_hline(y=1, line_dash="dot", row=5, col=1)
    fig.add_hline(y=-1, line_dash="dot", row=5, col=1)

    fig.update_layout(
        height=1120,
        xaxis_rangeslider_visible=False,
        title=f"{ticker} Technical Chart",
        showlegend=True
    )

    st.plotly_chart(fig, use_container_width=True)

    latest = df.iloc[-1]

    col1, col2, col3, col4, col5, col6, col7, col8 = st.columns(8)
    col1.metric("Close", round(latest["Close"], 2))
    col2.metric("RSI", round(latest["RSI"], 2))
    col3.metric("MACD Hist", round(latest["MACD_Hist"], 4))
    col4.metric("Relative Volume", round(latest["Relative_Volume"], 2))
    col5.metric("CMF", round(latest["CMF"], 4))
    col6.metric("MFI", round(latest["MFI"], 2))
    col7.metric("Smart Flow", round(latest["Smart_Money_Flow_Score"], 2))
    col8.metric("BB Width", round(latest["BB_Width"], 4))

    st.subheader("Latest Indicator Values")
    latest_table = pd.DataFrame([{
        "Ticker": ticker,
        "Close": round(latest["Close"], 2),
        "MA20": round(latest["MA20"], 2),
        "MA50": round(latest["MA50"], 2),
        "MA200": round(latest["MA200"], 2),
        "RSI": round(latest["RSI"], 2),
        "MACD": round(latest["MACD"], 4),
        "Signal": round(latest["Signal"], 4),
        "MACD_Hist": round(latest["MACD_Hist"], 4),
        "MACD_Hist_Change": round(latest["MACD_Hist_Change"], 4),
        "Relative_Volume": round(latest["Relative_Volume"], 2),
        "CMF": round(latest["CMF"], 4),
        "MFI": round(latest["MFI"], 2),
        "OBV_Change": round(latest["OBV_Change"], 2),
        "Money_Flow_Volume": round(latest["Money_Flow_Volume"], 2),
        "Smart_Money_Flow_Score": round(latest["Smart_Money_Flow_Score"], 2),
        "Buy_Sell_Pressure": round(latest["Buy_Sell_Pressure"], 4),
        "Smart_Money_Flow_5D": round(latest["Smart_Money_Flow_5D"], 2),
        "Smart_Money_Flow_20D": round(latest["Smart_Money_Flow_20D"], 2),
        "BB_Upper": round(latest["BB_Upper"], 2),
        "BB_Lower": round(latest["BB_Lower"], 2),
        "BB_Width": round(latest["BB_Width"], 4),
    }])

    st.dataframe(latest_table, use_container_width=True)


# ============================================================
# Sidebar Main Navigation
# ============================================================

st.sidebar.markdown(
    """
    <div style="padding: 8px 0 12px 0;">
        <div style="color:#38BDF8; font-size:12px; font-weight:900; letter-spacing:0.16em; text-transform:uppercase;">
            Navigation
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

page = st.sidebar.radio(
    "Choose Module",
    [
        "Page 1 - Stock Scanner",
        "Page 2 - Backtest Strategy",
        "Page 3 - Options Watchlist",
        "Page 4 - Technical Chart"
    ]
)


# ============================================================
# Page 1 - Stock Scanner
# ============================================================

if page == "Page 1 - Stock Scanner":
    render_section_header("Page 1 — Stock Scanner", "Screen US, Malaysia, and Singapore stocks using trend, volume, money flow, risk/reward, and practical ranking.")

    st.sidebar.header("Scanner Settings")

    market_name = st.sidebar.radio(
        "Choose Market",
        ["US", "Malaysia", "Singapore"],
        index=0
    )

    data_source = st.sidebar.selectbox(
        "Data source",
        [
            "Auto",
            "Yahoo Finance",
            "Stooq",
            "EODHD",
            "iTick",
            "Alpha Vantage"
        ],
        index=0
    )


    if market_name == "US":
        stock_group_options = [
            "Default Watchlist",
            "Top 50 Large Cap",
            "Active Stocks",
            "Top 50 + Active Stocks",
            "Auto Load",
            "Custom"
        ]
    elif market_name == "Malaysia":
        stock_group_options = [
            "Default Watchlist",
            "KLCI 30",
            "Active Malaysia Stocks",
            "KLCI 30 + Active Malaysia Stocks",
            "Auto Load",
            "Custom"
        ]
    else:
        stock_group_options = [
            "Default Watchlist",
            "STI 30",
            "Active Singapore Stocks",
            "STI 30 + Active Singapore Stocks",
            "Auto Load",
            "Custom"
        ]

    stock_group = st.sidebar.radio(
        "Choose stock universe",
        stock_group_options
    )

    auto_active_top_n = 30
    auto_active_lookback_days = 5
    auto_active_df = pd.DataFrame()

    if stock_group in ["Active Stocks", "Active Malaysia Stocks", "Active Singapore Stocks", "Top 50 + Active Stocks", "KLCI 30 + Active Malaysia Stocks", "STI 30 + Active Singapore Stocks"]:
        st.sidebar.subheader("Auto Active Settings")

        auto_active_top_n = st.sidebar.slider(
            "Top active stocks to select",
            min_value=10,
            max_value=100,
            value=30,
            step=5
        )

        auto_active_lookback_days = st.sidebar.slider(
            "Active ranking lookback days",
            min_value=3,
            max_value=20,
            value=5,
            step=1
        )

        st.sidebar.caption(
            "Auto Active ranks stocks by recent average traded value: Close x Volume."
        )

    if market_name == "US":
        benchmark_ticker = "SPY"
        benchmark_label = "SPY"

        if stock_group == "Default Watchlist":
            stock_list = US_DEFAULT_WATCHLIST
        elif stock_group == "Top 50 Large Cap":
            stock_list = US_TOP_50_STOCKS
        elif stock_group == "Active Stocks":
            auto_base_list = list(dict.fromkeys(
                load_sp500_tickers() + load_nasdaq100_tickers() + ACTIVE_US_STOCKS + US_TOP_50_STOCKS
            ))

            if not auto_base_list:
                auto_base_list = list(dict.fromkeys(US_TOP_50_STOCKS + ACTIVE_US_STOCKS))

            with st.spinner("Finding active US stocks by recent traded value..."):
                stock_list, auto_active_df = calculate_auto_active_stocks(
                    tickers=auto_base_list,
                    market_name="US",
                    top_n=auto_active_top_n,
                    lookback_days=auto_active_lookback_days,
                    data_source=data_source
                )

            if not stock_list:
                st.warning("Auto active ranking could not load. Falling back to fixed Active Stocks.")
                stock_list = ACTIVE_US_STOCKS
        elif stock_group == "Top 50 + Active Stocks":
            top50_set = set([str(x).upper() for x in US_TOP_50_STOCKS])

            auto_base_list = list(dict.fromkeys(
                load_sp500_tickers() + load_nasdaq100_tickers() + ACTIVE_US_STOCKS
            ))

            # For combined universe, active stocks should be additional names outside Top 50.
            auto_base_list = [
                t for t in auto_base_list
                if str(t).upper() not in top50_set
            ]

            if not auto_base_list:
                auto_base_list = [
                    t for t in ACTIVE_US_STOCKS
                    if str(t).upper() not in top50_set
                ]

            with st.spinner("Finding additional active US stocks by recent traded value..."):
                auto_active_list, auto_active_df = calculate_auto_active_stocks(
                    tickers=auto_base_list,
                    market_name="US",
                    top_n=auto_active_top_n,
                    lookback_days=auto_active_lookback_days,
                    data_source=data_source
                )

            if not auto_active_list:
                st.warning("Auto active ranking could not load. Falling back to fixed Active Stocks.")
                auto_active_list = [
                    t for t in ACTIVE_US_STOCKS
                    if str(t).upper() not in top50_set
                ]

            stock_list = list(dict.fromkeys(US_TOP_50_STOCKS + auto_active_list))
        elif stock_group == "Auto Load":
            auto_universe = st.sidebar.selectbox(
                "Auto-load US universe",
                ["S&P 500", "Nasdaq 100", "Dow 30", "S&P 500 + Nasdaq 100"],
                index=0
            )
            max_scan = st.sidebar.number_input(
                "Max stocks to scan",
                min_value=10,
                max_value=800,
                value=100,
                step=10
            )
            stock_list = limit_stock_list(get_auto_stock_list("US", auto_universe), int(max_scan))
            st.sidebar.info(f"Loaded {len(stock_list)} US tickers from {auto_universe}.")
        else:
            custom_text = st.sidebar.text_area(
                "Enter tickers separated by comma",
                "TSLA,NVDA,AAPL,MSFT,AMZN"
            )
            stock_list = normalize_ticker_list_from_text(custom_text, market_name)

    elif market_name == "Malaysia":
        benchmark_ticker = "^KLSE"
        benchmark_label = "KLCI"

        if stock_group == "Default Watchlist":
            stock_list = MALAYSIA_DEFAULT_WATCHLIST
        elif stock_group == "KLCI 30":
            stock_list = MALAYSIA_KLCI_30
        elif stock_group == "Active Malaysia Stocks":
            auto_base_list = MALAYSIA_BROAD_PRESET

            with st.spinner("Finding active Malaysia stocks by recent traded value..."):
                stock_list, auto_active_df = calculate_auto_active_stocks(
                    tickers=auto_base_list,
                    market_name="Malaysia",
                    top_n=auto_active_top_n,
                    lookback_days=auto_active_lookback_days,
                    data_source=data_source
                )

            if not stock_list:
                st.warning("Auto active ranking could not load. Falling back to fixed Active Malaysia Stocks.")
                stock_list = ACTIVE_MALAYSIA_STOCKS
        elif stock_group == "KLCI 30 + Active Malaysia Stocks":
            klci_set = set([str(x).upper() for x in MALAYSIA_KLCI_30])

            # For combined universe, active stocks should be additional names outside KLCI 30.
            auto_base_list = [
                t for t in MALAYSIA_BROAD_PRESET
                if str(t).upper() not in klci_set
            ]

            with st.spinner("Finding additional active Malaysia stocks by recent traded value..."):
                auto_active_list, auto_active_df = calculate_auto_active_stocks(
                    tickers=auto_base_list,
                    market_name="Malaysia",
                    top_n=auto_active_top_n,
                    lookback_days=auto_active_lookback_days,
                    data_source=data_source
                )

            if not auto_active_list:
                st.warning("Auto active ranking could not load. Falling back to fixed Active Malaysia Stocks.")
                auto_active_list = [
                    t for t in ACTIVE_MALAYSIA_STOCKS
                    if str(t).upper() not in klci_set
                ]

            stock_list = list(dict.fromkeys(MALAYSIA_KLCI_30 + auto_active_list))
        elif stock_group == "Auto Load":
            auto_universe = st.sidebar.selectbox(
                "Auto-load Malaysia universe",
                ["Malaysia Broad Preset", "KLCI 30 + Active + Broad Preset"],
                index=0
            )
            max_scan = st.sidebar.number_input(
                "Max stocks to scan",
                min_value=10,
                max_value=300,
                value=80,
                step=10
            )
            stock_list = limit_stock_list(get_auto_stock_list("Malaysia", auto_universe), int(max_scan))
            st.sidebar.info(f"Loaded {len(stock_list)} Malaysia tickers from {auto_universe}.")
        else:
            custom_text = st.sidebar.text_area(
                "Enter Bursa tickers or stock names separated by comma",
                "DNEX,4456,1155,MAYBANK,CIMB,TOPGLOV,FRONTKEN,VITROX"
            )
            stock_list = normalize_ticker_list_from_text(custom_text, market_name)

    else:
        benchmark_ticker = "^STI"
        benchmark_label = "STI"

        if stock_group == "Default Watchlist":
            stock_list = SINGAPORE_DEFAULT_WATCHLIST
        elif stock_group == "STI 30":
            stock_list = SINGAPORE_STI_30
        elif stock_group == "Active Singapore Stocks":
            auto_base_list = SINGAPORE_BROAD_PRESET

            with st.spinner("Finding active Singapore stocks by recent traded value..."):
                stock_list, auto_active_df = calculate_auto_active_stocks(
                    tickers=auto_base_list,
                    market_name="Singapore",
                    top_n=auto_active_top_n,
                    lookback_days=auto_active_lookback_days,
                    data_source=data_source
                )

            if not stock_list:
                st.warning("Auto active ranking could not load. Falling back to fixed Active Singapore Stocks.")
                stock_list = ACTIVE_SINGAPORE_STOCKS
        elif stock_group == "STI 30 + Active Singapore Stocks":
            sti_set = set([str(x).upper() for x in SINGAPORE_STI_30])

            auto_base_list = [
                t for t in SINGAPORE_BROAD_PRESET
                if str(t).upper() not in sti_set
            ]

            with st.spinner("Finding additional active Singapore stocks by recent traded value..."):
                auto_active_list, auto_active_df = calculate_auto_active_stocks(
                    tickers=auto_base_list,
                    market_name="Singapore",
                    top_n=auto_active_top_n,
                    lookback_days=auto_active_lookback_days,
                    data_source=data_source
                )

            if not auto_active_list:
                st.warning("Auto active ranking could not load. Falling back to fixed Active Singapore Stocks.")
                auto_active_list = [
                    t for t in ACTIVE_SINGAPORE_STOCKS
                    if str(t).upper() not in sti_set
                ]

            stock_list = list(dict.fromkeys(SINGAPORE_STI_30 + auto_active_list))
        elif stock_group == "Auto Load":
            auto_universe = st.sidebar.selectbox(
                "Auto-load Singapore universe",
                ["Singapore Broad Preset", "STI 30 + Active + Broad Preset"],
                index=0
            )
            max_scan = st.sidebar.number_input(
                "Max stocks to scan",
                min_value=10,
                max_value=300,
                value=80,
                step=10
            )
            stock_list = limit_stock_list(get_auto_stock_list("Singapore", auto_universe), int(max_scan))
            st.sidebar.info(f"Loaded {len(stock_list)} Singapore tickers from {auto_universe}.")
        else:
            custom_text = st.sidebar.text_area(
                "Enter SGX tickers or stock names separated by comma",
                "DBS,D05,OCBC,O39,UOB,SINGTEL,SIA"
            )
            stock_list = normalize_ticker_list_from_text(custom_text, market_name)

    if stock_group in ["Active Stocks", "Active Malaysia Stocks", "Active Singapore Stocks", "Top 50 + Active Stocks", "KLCI 30 + Active Malaysia Stocks", "STI 30 + Active Singapore Stocks"] and auto_active_df is not None and not auto_active_df.empty:
        st.subheader("Active Stocks Selected")
        st.caption(
            "This dynamic active list is ranked by recent average traded value. "
            "The scanner/scoring logic is the same as KLCI 30 or Top 50; only the stock universe changes. "
            "It refreshes with market data cache, usually every 1 hour."
        )
        active_display_df = auto_active_df.rename(columns={
            "Name": "Stock Name",
            "Latest_Close": "Latest Close",
            "Latest_Volume": "Latest Volume",
            "Latest_Traded_Value": "Latest Traded Value",
            "Relative_Volume": "Rel Volume",
            "Price_Change_5D_%": "5D Change %"
        })

        if "Stock" not in active_display_df.columns:
            if "Ticker" in active_display_df.columns and "Stock Name" in active_display_df.columns:
                active_display_df["Stock"] = (
                    active_display_df["Ticker"].astype(str) + " | " + active_display_df["Stock Name"].astype(str)
                )
            elif "Ticker" in active_display_df.columns:
                active_display_df["Stock"] = active_display_df["Ticker"].astype(str)

        if "Stock" in active_display_df.columns:
            active_display_df = active_display_df.set_index("Stock")
            drop_cols = [col for col in ["Ticker", "Stock Name"] if col in active_display_df.columns]
            if drop_cols:
                active_display_df = active_display_df.drop(columns=drop_cols)

        st.dataframe(
            active_display_df,
            use_container_width=True,
            height=260,
            hide_index=False
        )

        if stock_group == "KLCI 30 + Active Malaysia Stocks":
            active_count = len(auto_active_df)
            expected_unique = len(stock_list)
            st.info(
                f"KLCI 30 + Active tally: 30 KLCI stocks + {active_count} additional active non-KLCI stocks "
                f"= {expected_unique} unique stocks. All stocks use the same scanner and scoring logic."
            )

        if stock_group == "Top 50 + Active Stocks":
            active_count = len(auto_active_df)
            expected_unique = len(stock_list)
            st.info(
                f"Top 50 + Active tally: 50 large-cap stocks + {active_count} additional active non-Top-50 stocks "
                f"= {expected_unique} unique stocks. All stocks use the same scanner and scoring logic."
            )

        if stock_group == "STI 30 + Active Singapore Stocks":
            active_count = len(auto_active_df)
            expected_unique = len(stock_list)
            st.info(
                f"STI 30 + Active tally: 30 STI stocks + {active_count} additional active non-STI stocks "
                f"= {expected_unique} unique stocks. All stocks use the same scanner and scoring logic."
            )

    default_selected_stocks = stock_list if stock_group in ["Active Stocks", "Active Malaysia Stocks", "Active Singapore Stocks", "Top 50 + Active Stocks", "KLCI 30 + Active Malaysia Stocks", "STI 30 + Active Singapore Stocks"] else stock_list[:10]

    selected_stocks = st.sidebar.multiselect(
        "Select stocks to scan",
        stock_list,
        default=default_selected_stocks
    )

    st.sidebar.caption(
        f"Universe unique tickers: {len(stock_list)} | Selected to scan: {len(selected_stocks)}"
    )

    if stock_group == "Custom":
        st.sidebar.caption(
            "Easy input supported: Malaysia DNEX or 4456 becomes 4456.KL; "
            "Singapore DBS or D05 becomes D05.SI. Results will show both ticker and stock name."
        )

    if stock_group in ["Active Stocks", "Active Malaysia Stocks", "Active Singapore Stocks", "Top 50 + Active Stocks", "KLCI 30 + Active Malaysia Stocks", "STI 30 + Active Singapore Stocks"]:
        st.sidebar.caption(
            "Active list is dynamic. Analysis and scoring method stays the same; only ticker selection changes."
        )

    min_practical_score = st.sidebar.slider("Minimum Practical Rank Score", -10, 35, 0)
    min_risk_reward = st.sidebar.slider("Minimum Risk/Reward", 0.0, 5.0, 0.0, 0.1)
    min_upside = st.sidebar.slider("Minimum Upside %", 0.0, 30.0, 0.0, 0.5)

    show_only_watchlist = st.sidebar.checkbox("Show only Watchlist / Strong Watchlist", value=False)
    show_only_early_bullish = st.sidebar.checkbox("Show only early bullish signals", value=False)
    show_only_early_bearish = st.sidebar.checkbox("Show only early bearish warnings", value=False)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        market_trend = get_market_trend(market_name)
        st.metric(f"{market_name} Market Trend", market_trend)

    with col2:
        st.metric("Benchmark", benchmark_label)

    with col3:
        st.metric("Total Selected Stocks", len(selected_stocks))

    with col4:
        st.metric("Market", market_name)

    run_scan = st.button(f"Run {market_name} Stock Scanner", type="primary")

    if run_scan:
        if not selected_stocks:
            st.error("Please select at least one stock.")
        else:
            if market_name in ["Malaysia", "Singapore"]:
                benchmark_used, benchmark_df = get_benchmark_data(market_name, period="2y", min_rows=120)

                if benchmark_df is None:
                    st.error(f"{market_name} benchmark data is not available. Cannot continue.")
                    st.stop()

                st.info(f"{market_name} benchmark used: {benchmark_used}")
            else:
                benchmark_used, benchmark_df = get_benchmark_data("US", period="2y", min_rows=120)

                if benchmark_df is None:
                    st.error("US benchmark data is not available. Tried SPY, VOO, and QQQ. Cannot continue.")
                    st.stop()

                st.info(f"US benchmark used: {benchmark_used}")

            results = []
            skipped = []

            progress_bar = st.progress(0)
            status_text = st.empty()

            for i, ticker in enumerate(selected_stocks):
                status_text.text(f"Scanning {ticker}...")

                try:
                    result = analyse_stock(ticker, benchmark_df, market_name)

                    if result is None:
                        skipped.append(ticker)
                    else:
                        result["Final View"] = get_final_view(result["Score"], market_trend)
                        results.append(result)

                except Exception:
                    skipped.append(ticker)

                progress_bar.progress((i + 1) / len(selected_stocks))

            status_text.text("Scan completed.")

            if not results:
                st.error("No valid stock results generated.")
            else:
                df_result = pd.DataFrame(results)

                df_result[["Practical_Rank_Score", "Practical_Notes"]] = df_result.apply(
                    lambda row: pd.Series(calculate_practical_rank(row, market_name)),
                    axis=1
                )

                df_result = df_result.sort_values(
                    by=["Practical_Rank_Score", "Score", "Risk_Reward", "Upside_%", "Relative_Strength"],
                    ascending=[False, False, False, False, False]
                )

                priority_columns = [
                    "Ticker",
                    "Name",
                    "Stock",
                    "Buy_Sell_Safety",
                    "Close",
                    "Score",
                    "Practical_Rank_Score",
                    "Final View",

                    "Smart_Money_Signal",
                    "Smart_Money_Flow_Score",
                    "Buy_Sell_Pressure",
                    "Smart_Money_Flow_5D",
                    "Smart_Money_Flow_20D",

                    "Capital_Flow_Score",
                    "Capital_Flow_Signal",
                    "CMF",
                    "MFI",
                    "OBV_Change",
                    "Money_Flow_Volume",

                    "RSI",
                    "RSI_Change",
                    "ADX",
                    "Relative_Strength",

                    "MACD",
                    "Signal",
                    "MACD_Hist",
                    "MACD_Hist_Change",

                    "Relative_Volume",
                    "BB_Width",
                    "Early_Signal",

                    "Upside_%",
                    "Risk_%",
                    "Risk_Reward",

                    "Support",
                    "Resistance",
                    "Technical_Target",
                    "Stop_Loss",

                    "Analyst_Target_Mean",
                    "Analyst_Target_High",
                    "Analyst_Target_Low",

                    "Practical_Notes",
                    "Reasons"
                ]

                # Keep only columns that exist, so the app will not crash if a data provider misses optional fields.
                priority_columns = [col for col in priority_columns if col in df_result.columns]

                df_result = df_result[priority_columns]

                filtered_df = df_result.copy()
                filtered_df = filtered_df[filtered_df["Practical_Rank_Score"] >= min_practical_score]
                filtered_df = filtered_df[filtered_df["Risk_Reward"].fillna(0) >= min_risk_reward]
                filtered_df = filtered_df[filtered_df["Upside_%"] >= min_upside]

                if show_only_watchlist:
                    filtered_df = filtered_df[
                        filtered_df["Final View"].isin(["Strong Watchlist", "Watchlist", "Careful Watchlist"])
                    ]

                if show_only_early_bullish:
                    filtered_df = filtered_df[
                        filtered_df["Early_Signal"].str.contains(
                            "bullish|buying|rebound|Breakout",
                            case=False,
                            na=False
                        )
                    ]

                if show_only_early_bearish:
                    filtered_df = filtered_df[
                        filtered_df["Early_Signal"].str.contains(
                            "bearish|selling|slowing|Breakdown",
                            case=False,
                            na=False
                        )
                    ]

                st.subheader(f"{market_name} Practical Watchlist")

                top_col1, top_col2, top_col3, top_col4 = st.columns(4)

                with top_col1:
                    st.metric("Valid Results", len(df_result))

                with top_col2:
                    st.metric("Filtered Results", len(filtered_df))

                with top_col3:
                    strong_count = len(df_result[df_result["Final View"] == "Strong Watchlist"])
                    st.metric("Strong Watchlist", strong_count)

                with top_col4:
                    early_count = len(
                        df_result[
                            df_result["Early_Signal"].str.contains(
                                "bullish|buying|rebound|Breakout",
                                case=False,
                                na=False
                            )
                        ]
                    )
                    st.metric("Early Bullish Signals", early_count)

                st.dataframe(filtered_df, use_container_width=True, height=520)

                st.subheader("Top 20")
                st.dataframe(df_result.head(20), use_container_width=True, height=420)

                excel_file_name = (
                    "us_stock_analysis_practical_rank.xlsx"
                    if market_name == "US"
                    else "malaysia_stock_analysis_practical_rank.xlsx"
                )

                csv_file_name = (
                    "us_stock_analysis_practical_rank.csv"
                    if market_name == "US"
                    else "malaysia_stock_analysis_practical_rank.csv"
                )

                excel_data = dataframe_to_excel(df_result, f"{market_name} Stock Scanner")

                st.download_button(
                    label="Download Full Result as Excel",
                    data=excel_data,
                    file_name=excel_file_name,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

                csv_data = df_result.to_csv(index=False).encode("utf-8")

                st.download_button(
                    label="Download Full Result as CSV",
                    data=csv_data,
                    file_name=csv_file_name,
                    mime="text/csv"
                )

                if skipped:
                    st.warning(f"Skipped stocks: {', '.join(skipped)}")

    with st.expander("How to interpret Page 1"):
        st.write(
            """
            **Score** = technical strength.

            **Practical_Rank_Score** = entry quality based on risk/reward, upside, RSI, ADX, and relative strength.

            **Early_Signal** helps detect improving or weakening momentum earlier.

            **Relative_Volume**:
            - 1.0 = normal
            - 1.5 = strong
            - 2.0+ = unusual

            **Risk_Reward**:
            - Below 1.0 = weak
            - 1.5 to 2.0 = acceptable
            - Above 2.0 = good
            - Above 3.0 = very good

            **Active Stocks**:
            - Ranks stocks by recent average traded value, calculated as Close × Volume.
            - This is more meaningful than pure volume because it accounts for stock price.
            - The ranking refreshes when the market data cache refreshes, usually every 1 hour.
            """
        )


# ============================================================
# Page 2 - Backtest Strategy
# ============================================================

if page == "Page 2 - Backtest Strategy":
    render_section_header("Page 2 — Backtest Strategy", "Test whether your scanner-style signals worked historically using daily candles.")

    st.write(
        "This page backtests your scanner-style signal using daily candles. "
        "It checks whether the rule worked historically."
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        market_name_bt = st.selectbox("Market", ["US", "Malaysia", "Singapore"])

    with col2:
        if market_name_bt == "US":
            default_ticker = "TSLA"
        elif market_name_bt == "Malaysia":
            default_ticker = "6947.KL"
        else:
            default_ticker = "D05.SI"
        ticker_bt = st.text_input("Ticker", default_ticker).upper()

    with col3:
        if market_name_bt == "US":
            benchmark_bt = "SPY"
        elif market_name_bt == "Malaysia":
            benchmark_bt = "^KLSE"
        else:
            benchmark_bt = "^STI"
        st.write(f"Benchmark: **{benchmark_bt}**")

    col4, col5, col6, col7 = st.columns(4)

    with col4:
        initial_capital = st.number_input("Initial Capital", min_value=1000, value=10000, step=1000)

    with col5:
        holding_days = st.number_input("Holding Days", min_value=1, max_value=30, value=5)

    with col6:
        take_profit_pct = st.number_input("Take Profit %", min_value=1.0, max_value=50.0, value=6.0)

    with col7:
        stop_loss_pct = st.number_input("Stop Loss %", min_value=1.0, max_value=30.0, value=3.0)

    st.info(
        "Backtest buy rule: Close above MA20/MA50/MA200, RSI healthy, "
        "MACD histogram improving, relative volume high, outperforming benchmark, and positive capital flow."
    )

    if st.button("Run Backtest", type="primary"):
        with st.spinner("Running backtest..."):
            trades_df, summary, message = backtest_strategy(
                ticker=ticker_bt,
                market_name=market_name_bt,
                benchmark_ticker=benchmark_bt,
                initial_capital=initial_capital,
                holding_days=int(holding_days),
                take_profit_pct=take_profit_pct,
                stop_loss_pct=stop_loss_pct
            )

        if trades_df is None:
            st.error(message)

        elif trades_df.empty:
            st.warning(message)

        else:
            st.success(message)
            st.subheader("Backtest Summary")

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total Trades", summary["Total Trades"])
            c2.metric("Win Rate %", summary["Win Rate %"])
            c3.metric("Total Return %", summary["Total Return %"])
            c4.metric("Final Capital", summary["Final Capital"])

            c5, c6, c7, c8 = st.columns(4)
            c5.metric("Average Return %", summary["Average Return %"])
            c6.metric("Profit Factor", summary["Profit Factor"])
            c7.metric("Best Trade %", summary["Best Trade %"])
            c8.metric("Worst Trade %", summary["Worst Trade %"])

            st.subheader("Equity Curve")
            st.line_chart(trades_df.set_index("Exit Date")["Capital"])

            st.subheader("Trade History")
            st.dataframe(trades_df, use_container_width=True, height=500)

            st.download_button(
                "Download Backtest CSV",
                trades_df.to_csv(index=False).encode("utf-8"),
                f"{ticker_bt}_backtest.csv",
                "text/csv"
            )

    with st.expander("How to interpret Page 2"):
        st.write(
            """
            **Win Rate**: How many trades were profitable.

            **Profit Factor**: Gross profit divided by gross loss.
            - Above 1.0 = profitable historically
            - Above 1.3 = better
            - Above 1.5 = stronger

            **Total Trades**: More trades make the result more reliable.

            If you get "No trades found", the strategy may be too strict.
            """
        )


# ============================================================
# Page 3 - US Options Checklist
# ============================================================

if page == "Page 3 - Options Watchlist":
    render_section_header("Page 3 — US Options Checklist", "Screen US-listed options contracts by liquidity, spread, breakeven move, and open interest.")

    st.write(
        "This page is for **US-listed stock options only**. "
        "Malaysia Bursa and Singapore SGX stocks do not use this Yahoo US options chain format, so .KL and .SI tickers are blocked here."
    )

    st.warning(
        "Options are high-risk. Even if the stock direction is right, the option can lose money "
        "because of time decay, IV drop, wide spreads, or poor liquidity."
    )

    option_mode = st.radio(
        "Choose option mode",
        ["Single Stock Options Chain", "Multi-Stock Options Checklist"],
        horizontal=True
    )

    popular_option_names = [
        "TSLA", "NVDA", "AAPL", "MSFT", "AMD",
        "AMZN", "META", "GOOGL", "PLTR", "COIN",
        "MSTR", "SMCI", "NFLX", "AVGO", "QCOM",
        "SOFI", "HOOD", "RIVN", "SHOP", "UBER"
    ]

    def clean_us_option_ticker(ticker):
        ticker = str(ticker).strip().upper()
        ticker = ticker.replace(".US", "")
        return ticker

    def is_valid_us_option_ticker(ticker):
        ticker = clean_us_option_ticker(ticker)
        if not ticker:
            return False
        if ticker.endswith(".KL") or ticker.endswith(".SI"):
            return False
        if ticker.startswith("^"):
            return False
        return True

    def get_current_price_for_option(ticker):
        raw_price = get_data(
            ticker,
            period="1y",
            interval="1d",
            min_rows=30,
            source="Yahoo Finance",
            market_name="US"
        )
        if raw_price is None or raw_price.empty:
            return None
        return raw_price["Close"].iloc[-1]

    def get_nearest_expiry(stock):
        expiries = stock.options
        if not expiries:
            return None
        return expiries[0]

    def get_option_checklist_summary(ticker, option_type="Call", max_breakeven_move=12, min_oi=100, max_spread=30):
        ticker = clean_us_option_ticker(ticker)

        if not is_valid_us_option_ticker(ticker):
            return None

        try:
            current_price = get_current_price_for_option(ticker)
            if current_price is None:
                return {
                    "Ticker": ticker,
                    "Status": "No price data",
                    "Current Price": None,
                    "Expiry": None,
                    "Best Contract": None,
                    "Strike": None,
                    "Last Price": None,
                    "Spread_%": None,
                    "Open Interest": None,
                    "Volume": None,
                    "Breakeven_Move_%": None,
                    "Liquidity Score": None,
                    "Option View": "No data"
                }

            stock = yf.Ticker(ticker)
            expiry = get_nearest_expiry(stock)

            if expiry is None:
                return {
                    "Ticker": ticker,
                    "Status": "No options expiry",
                    "Current Price": round(current_price, 2),
                    "Expiry": None,
                    "Best Contract": None,
                    "Strike": None,
                    "Last Price": None,
                    "Spread_%": None,
                    "Open Interest": None,
                    "Volume": None,
                    "Breakeven_Move_%": None,
                    "Liquidity Score": None,
                    "Option View": "No options"
                }

            calls, puts = get_options_chain(ticker, expiry)

            if option_type == "Call":
                option_df = analyse_options_table(calls, current_price, "Call")
            else:
                option_df = analyse_options_table(puts, current_price, "Put")

            if option_df.empty:
                return {
                    "Ticker": ticker,
                    "Status": "Options chain empty",
                    "Current Price": round(current_price, 2),
                    "Expiry": expiry,
                    "Best Contract": None,
                    "Strike": None,
                    "Last Price": None,
                    "Spread_%": None,
                    "Open Interest": None,
                    "Volume": None,
                    "Breakeven_Move_%": None,
                    "Liquidity Score": None,
                    "Option View": "No chain"
                }

            filtered = option_df[
                (option_df["openInterest"].fillna(0) >= min_oi) &
                (option_df["Spread_%"].fillna(999) <= max_spread) &
                (option_df["Breakeven_Move_%"].fillna(999) <= max_breakeven_move)
            ].copy()

            if filtered.empty:
                # still choose best liquidity contract as reference
                ref = option_df.sort_values(
                    by=["Liquidity_Score", "openInterest", "volume"],
                    ascending=[False, False, False]
                ).head(1).iloc[0]

                return {
                    "Ticker": ticker,
                    "Status": "No contract passes filters",
                    "Current Price": round(current_price, 2),
                    "Expiry": expiry,
                    "Best Contract": ref["contractSymbol"],
                    "Strike": ref["strike"],
                    "Last Price": ref["lastPrice"],
                    "Spread_%": ref["Spread_%"],
                    "Open Interest": ref["openInterest"],
                    "Volume": ref["volume"],
                    "Breakeven_Move_%": ref["Breakeven_Move_%"],
                    "Liquidity Score": ref["Liquidity_Score"],
                    "Option View": "Check manually"
                }

            filtered = filtered.sort_values(
                by=["Liquidity_Score", "openInterest", "volume", "Breakeven_Move_%"],
                ascending=[False, False, False, True]
            )

            best = filtered.head(1).iloc[0]

            return {
                "Ticker": ticker,
                "Status": "OK",
                "Current Price": round(current_price, 2),
                "Expiry": expiry,
                "Best Contract": best["contractSymbol"],
                "Strike": best["strike"],
                "Last Price": best["lastPrice"],
                "Spread_%": best["Spread_%"],
                "Open Interest": best["openInterest"],
                "Volume": best["volume"],
                "Breakeven_Move_%": best["Breakeven_Move_%"],
                "Liquidity Score": best["Liquidity_Score"],
                "Option View": best["Option_View"]
            }

        except Exception as e:
            return {
                "Ticker": ticker,
                "Status": f"Error: {str(e)[:60]}",
                "Current Price": None,
                "Expiry": None,
                "Best Contract": None,
                "Strike": None,
                "Last Price": None,
                "Spread_%": None,
                "Open Interest": None,
                "Volume": None,
                "Breakeven_Move_%": None,
                "Liquidity Score": None,
                "Option View": "Error"
            }

    if option_mode == "Single Stock Options Chain":
        col_a, col_b = st.columns(2)

        with col_a:
            ticker_opt = st.selectbox(
                "Option ticker",
                popular_option_names,
                index=0
            )

        with col_b:
            manual_ticker = st.text_input(
                "Or type custom US ticker",
                "",
                placeholder="Example: TSLA, NVDA, AAPL"
            )

        if manual_ticker.strip():
            ticker_opt = clean_us_option_ticker(manual_ticker)

        if not is_valid_us_option_ticker(ticker_opt):
            st.error("Options checklist only supports US tickers. Do not use .KL or index tickers here.")
        else:
            try:
                stock = yf.Ticker(ticker_opt)
                current_price = get_current_price_for_option(ticker_opt)

                if current_price is None:
                    st.error("Unable to load US stock price data from Yahoo Finance.")
                else:
                    expiries = stock.options

                    if not expiries:
                        st.error(
                            "No option expiry data available for this ticker from Yahoo Finance. "
                            "This can happen if Yahoo/yfinance is temporarily unavailable, or the ticker has no listed options."
                        )

                    else:
                        col1, col2, col3 = st.columns(3)

                        with col1:
                            st.metric("Current Price", round(current_price, 2))

                        with col2:
                            expiry = st.selectbox("Choose Expiry", expiries)

                        with col3:
                            option_type = st.selectbox("Option Type", ["Call", "Put"])

                        calls, puts = get_options_chain(ticker_opt, expiry)

                        if option_type == "Call":
                            option_df = analyse_options_table(calls, current_price, "Call")
                        else:
                            option_df = analyse_options_table(puts, current_price, "Put")

                        if option_df.empty:
                            st.warning("No options data found.")
                        else:
                            min_oi = st.slider("Minimum Open Interest", 0, 10000, 100)
                            max_spread = st.slider("Maximum Bid/Ask Spread %", 1, 100, 30)
                            max_breakeven = st.slider("Maximum Breakeven Move %", 1, 100, 15)

                            filtered_option_df = option_df[
                                (option_df["openInterest"].fillna(0) >= min_oi) &
                                (option_df["Spread_%"].fillna(999) <= max_spread) &
                                (option_df["Breakeven_Move_%"].fillna(999) <= max_breakeven)
                            ]

                            st.subheader(f"{ticker_opt} {option_type} Options - {expiry}")

                            st.dataframe(
                                filtered_option_df,
                                use_container_width=True,
                                height=520
                            )

                            st.download_button(
                                "Download Options CSV",
                                filtered_option_df.to_csv(index=False).encode("utf-8"),
                                f"{ticker_opt}_{option_type}_{expiry}_options.csv",
                                "text/csv"
                            )

                            st.info(
                                "For options, focus on liquidity first: high open interest, decent volume, "
                                "and tight bid/ask spread. Avoid far OTM weekly options unless you fully understand the risk."
                            )

            except Exception as e:
                st.error(f"Unable to load options data: {e}")

    else:
        st.subheader("Multi-Stock US Options Checklist")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            checklist_option_type = st.selectbox("Checklist option type", ["Call", "Put"])

        with col2:
            checklist_min_oi = st.number_input(
                "Minimum open interest",
                min_value=0,
                max_value=10000,
                value=100,
                step=50
            )

        with col3:
            checklist_max_spread = st.number_input(
                "Maximum spread %",
                min_value=1,
                max_value=100,
                value=30,
                step=1
            )

        with col4:
            checklist_max_breakeven = st.number_input(
                "Maximum breakeven move %",
                min_value=1,
                max_value=100,
                value=15,
                step=1
            )

        default_multi = ",".join(popular_option_names[:10])

        multi_text = st.text_area(
            "US tickers to check, separated by comma",
            default_multi,
            height=100
        )

        tickers_to_check = [
            clean_us_option_ticker(t)
            for t in multi_text.split(",")
            if is_valid_us_option_ticker(t)
        ]

        tickers_to_check = list(dict.fromkeys(tickers_to_check))

        max_check = st.slider("Maximum tickers to check", 1, 30, min(10, len(tickers_to_check) if tickers_to_check else 10))

        tickers_to_check = tickers_to_check[:max_check]

        if st.button("Run US Options Checklist", type="primary"):
            if not tickers_to_check:
                st.error("Please enter at least one valid US ticker.")
            else:
                rows = []
                progress = st.progress(0)
                status = st.empty()

                for i, ticker in enumerate(tickers_to_check):
                    status.text(f"Checking options for {ticker}...")
                    result = get_option_checklist_summary(
                        ticker=ticker,
                        option_type=checklist_option_type,
                        max_breakeven_move=checklist_max_breakeven,
                        min_oi=checklist_min_oi,
                        max_spread=checklist_max_spread
                    )

                    if result is not None:
                        rows.append(result)

                    progress.progress((i + 1) / len(tickers_to_check))

                status.text("Options checklist completed.")

                if not rows:
                    st.warning("No options checklist results.")
                else:
                    checklist_df = pd.DataFrame(rows)

                    checklist_df = checklist_df.sort_values(
                        by=["Status", "Liquidity Score", "Open Interest", "Volume"],
                        ascending=[True, False, False, False]
                    )

                    st.subheader("US Options Checklist Result")
                    st.dataframe(checklist_df, use_container_width=True, height=500)

                    st.download_button(
                        "Download Options Checklist CSV",
                        checklist_df.to_csv(index=False).encode("utf-8"),
                        "us_options_checklist.csv",
                        "text/csv"
                    )

                    st.info(
                        "If TSLA or another large US ticker shows no expiry, it is usually a temporary Yahoo/yfinance options-chain issue. "
                        "Try refreshing, clearing Streamlit cache, or testing another ticker such as NVDA, AAPL, AMD, META, or COIN."
                    )

    with st.expander("How to interpret Page 3"):
        st.write(
            """
            **US only**: This page checks US-listed stock options. Bursa Malaysia .KL and Singapore .SI tickers are not supported here.

            **Open Interest**: Number of outstanding contracts. Higher usually means better liquidity.

            **Volume**: Contracts traded today. Higher is better.

            **Spread %**: Bid/ask spread. Lower is better.

            **Breakeven Move %**: How much the stock must move before the option breaks even.

            **Implied Volatility**: Higher IV means option premium is more expensive.

            **Liquidity Score**:
            - 0 to 1 = weak
            - 2 = acceptable
            - 3 = better liquidity

            For beginners, avoid far OTM weekly options.
            """
        )


# ============================================================
# Page 4 - Technical Chart
# ============================================================

if page == "Page 4 - Technical Chart":
    render_section_header("Page 4 — Technical Chart", "Visualize candlesticks, moving averages, Bollinger Bands, MACD, RSI, volume, and smart money flow.")

    st.write(
        "This page shows a visual technical chart with candlestick, MA20, MA50, MA200, "
        "Bollinger Bands, MACD, RSI, Relative Volume, and Smart Money Flow. "
        "For Malaysia and Singapore, daily candles are more reliable than intraday candles."
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        chart_market = st.selectbox("Market", ["US", "Malaysia", "Singapore"], index=0)

    with col2:
        if chart_market == "US":
            default_chart_ticker = "TSLA"
        elif chart_market == "Malaysia":
            default_chart_ticker = "6947.KL"
        else:
            default_chart_ticker = "D05.SI"
        chart_ticker = st.text_input("Enter ticker", default_chart_ticker).upper()

    with col3:
        chart_period = st.selectbox(
            "Chart period",
            ["1d", "1wk", "2wk", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "max"],
            index=5
        )

    with col4:
        if chart_market == "Malaysia":
            chart_data_source = st.selectbox(
                "Data source",
                ["Auto", "Yahoo Finance", "EODHD", "iTick", "Alpha Vantage"],
                index=0,
                help="Auto = Yahoo, then EODHD, then iTick, then Alpha Vantage. "
                     "Single providers need their API key in secrets.toml."
            )
        elif chart_market == "Singapore":
            chart_data_source = st.selectbox(
                "Data source",
                ["Auto", "Yahoo Finance", "EODHD", "Alpha Vantage"],
                index=0,
                help="Auto = Yahoo, then EODHD, then Alpha Vantage. "
                     "EODHD/Alpha Vantage need their API key in secrets.toml."
            )
        else:
            chart_data_source = st.selectbox(
                "Data source",
                ["Auto", "Yahoo Finance", "Stooq", "EODHD", "Alpha Vantage"],
                index=0,
                help="Auto = Yahoo, then Stooq, then Alpha Vantage. "
                     "EODHD/Alpha Vantage need their API key in secrets.toml."
            )

    if chart_market == "Malaysia":
        st.caption("Tip: you can type 6947 or 6947.KL. The app will convert Bursa tickers to .KL automatically.")

    if chart_market == "Singapore":
        st.caption("Tip: you can type D05 or D05.SI. The app will convert SGX tickers to .SI automatically.")

    if st.button("Show Technical Chart", type="primary"):
        plot_stock_chart(chart_ticker, chart_period, chart_data_source, chart_market)

    with st.expander("How to interpret Page 4"):
        st.write(
            """
            **Candlestick**: Shows open, high, low, and close.

            **MA20 / MA50 / MA200**:
            - Price above MA20 = short-term strength
            - Price above MA50 = medium-term strength
            - Price above MA200 = long-term uptrend

            **Bollinger Bands**:
            - Price above upper band = possible breakout or overextension
            - Price below lower band = possible weakness or oversold

            **MACD Histogram**:
            - Rising histogram = momentum improving
            - Falling histogram = momentum weakening

            **RSI**:
            - Above 70 = overbought area
            - Below 30 = oversold area

            **Relative Volume**:
            - Above 1.5 = strong volume
            - Above 2.0 = unusual volume

            **Capital Flow**:
            - CMF above +0.10 = positive inflow
            - CMF above +0.20 = strong accumulation
            - CMF below -0.10 = negative outflow
            - MFI 40 to 80 = healthier money flow range
            """
        )
