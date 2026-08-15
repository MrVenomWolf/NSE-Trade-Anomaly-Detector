"""
data_sources/equities.py
=========================
Real, live stock trade volume via Yahoo Finance (yfinance).
This is genuine consolidated exchange volume — the most solid data
source in this whole project.
"""

from datetime import datetime, timezone
from typing import List

from anomaly_engine import DataPoint


def fetch_equity_volume(ticker: str, period: str = "3mo", interval: str = "1d") -> List[DataPoint]:
    """
    Pull historical volume for one ticker.
    period/interval use yfinance's own strings, e.g. period="3mo", "5d";
    interval="1d", "1h" (intraday intervals only go back a limited window
    on Yahoo's side — that's a Yahoo limit, not ours).
    """
    import yfinance as yf  # imported lazily so the rest of the app works
                            # even if yfinance isn't installed yet

    df = yf.Ticker(ticker).history(period=period, interval=interval)
    if df.empty:
        return []

    points = []
    for ts, row in df.iterrows():
        py_ts = ts.to_pydatetime()
        if py_ts.tzinfo is None:
            py_ts = py_ts.replace(tzinfo=timezone.utc)
        points.append(
            DataPoint(
                source="equity",
                symbol=ticker,
                timestamp=py_ts,
                value=float(row["Volume"]),
                value_label="Volume (shares)",
                raw={"close": float(row["Close"])},
            )
        )
    return points
