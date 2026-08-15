"""
config.py
=========
Dynamically fetches ALL publicly listed stocks from the NSE master database.
"""

from io import StringIO
import pandas as pd
import requests


# ---------------------------------------------------------------------------
# CORE THRESHOLDS
# ---------------------------------------------------------------------------
DELTA_THRESHOLD = 0.30
BASELINE_WINDOW = 20


# ---------------------------------------------------------------------------
# FETCH ALL NSE LISTED STOCKS (NO HARDCODED FALLBACKS)
# ---------------------------------------------------------------------------
def get_all_nse_stocks():
    """Fetch every publicly listed stock on NSE directly from the exchange."""
    url = "https://archives.nseindia.com/content/equities/EQUITY_L.csv"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    response = requests.get(url, headers=headers)
    response.raise_for_status()

    df = pd.read_csv(StringIO(response.text))

    # Convert all listed NSE symbols to Yahoo Finance format (SYMBOL.NS)
    return (df["SYMBOL"].str.strip() + ".NS").tolist()


# Every listed ticker on the NSE (~2,000+ stocks)
EQUITY_TICKERS = get_all_nse_stocks()

# Currency pairs
FX_PAIRS = ["USDINR=X", "EURINR=X", "GBPINR=X", "JPYINR=X" , "AEDINR=X" , "CNYINR=X"]
SWAP_ASSET_CLASSES = ["interest_rate", "credit_default", "fx"]

# ---------------------------------------------------------------------------
# DYNAMIC NEWS SEARCH
# ---------------------------------------------------------------------------

"""
NEWS_CORRELATION_ENABLED = True
NEWS_SEARCH_TERMS = {
    symbol: f"{symbol.split('.')[0]} share news"
    for symbol in EQUITY_TICKERS + FX_PAIRS
}
"""
# ---------------------------------------------------------------------------
# OUTPUT
# ---------------------------------------------------------------------------
ALERT_LOG_FILE = "alerts_log.csv"

