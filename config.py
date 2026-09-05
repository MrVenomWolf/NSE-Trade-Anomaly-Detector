"""
config.py
=========
Dynamically fetches ALL publicly listed stocks from the NSE master database.
"""

from io import StringIO
import pandas as pd
import requests


# ---------------------------------------------------------------------------
# CORE THRESHOLDS (dual-threshold system: BOTH must clear to flag an anomaly)
# ---------------------------------------------------------------------------
MIN_Z_SCORE = 2.5      # log-normalized Z-score cutoff (~99th percentile)
MIN_RVOL = 2.0           # relative volume multiplier vs. median baseline
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
    return (df["SYMBOL"].str.strip() + ".NS").tolist()


# Every listed ticker on the NSE (~2,500+ stocks)
EQUITY_TICKERS = get_all_nse_stocks()

# ---------------------------------------------------------------------------
# OUTPUT
# ---------------------------------------------------------------------------
ALERT_LOG_FILE = "alerts_log.csv"