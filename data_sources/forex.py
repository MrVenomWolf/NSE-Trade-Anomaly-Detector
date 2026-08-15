"""
data_sources/forex.py
=======================
IMPORTANT CAVEAT (read this before trusting FX output):
Forex is an over-the-counter market with no single exchange, so there is
no official, universal "trade volume" number the way there is for a
listed stock. What you see from any broker is only THAT broker's own
flow, not the market's.

What we do instead: use each day's (High - Low) / Open as a stand-in
for "how much action happened" — a day with an unusually wide price
range gets flagged the same way an unusually large trade would. It's a
legitimate and commonly-used proxy, but it is a proxy, not real volume.
If you get a broker/data vendor with real tick-volume access later,
swap this out and everything downstream (engine, alerts) keeps working
unchanged.
"""

from datetime import timezone
from typing import List

from anomaly_engine import DataPoint


def fetch_fx_range(pair: str, period: str = "3mo", interval: str = "1d") -> List[DataPoint]:
    import yfinance as yf

    df = yf.Ticker(pair).history(period=period, interval=interval)
    if df.empty:
        return []

    points = []
    for ts, row in df.iterrows():
        py_ts = ts.to_pydatetime()
        if py_ts.tzinfo is None:
            py_ts = py_ts.replace(tzinfo=timezone.utc)
        open_px = float(row["Open"])
        if open_px == 0:
            continue
        day_range_pct = (float(row["High"]) - float(row["Low"])) / open_px * 100
        points.append(
            DataPoint(
                source="forex",
                symbol=pair,
                timestamp=py_ts,
                value=day_range_pct,
                value_label="Day range (% of open, proxy for volume)",
                raw={"close": float(row["Close"])},
            )
        )
    return points
