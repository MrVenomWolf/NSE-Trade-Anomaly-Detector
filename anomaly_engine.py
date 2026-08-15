"""
anomaly_engine.py
==================
The math. Every data source module produces a plain list of
DataPoint objects; this file decides which ones count as
"out of the box" trades.

Kept deliberately dependency-free (just stdlib) so you can unit-test
it without needing yfinance/pandas/network access at all.
"""

from dataclasses import dataclass, field
from datetime import datetime
from statistics import mean
from typing import List, Optional

import config


@dataclass
class DataPoint:
    """One observation for one instrument at one point in time."""
    source: str            # "equity" | "forex" | "swap_irs" | "swap_cds" | "swap_fx"
    symbol: str             # e.g. "AAPL", "USDJPY=X", "Interest Rate Swaps"
    timestamp: datetime
    value: float             # the thing we're comparing to baseline
                              # (share volume, price-range %, notional $, ticket count...)
    value_label: str = "value"   # human label for `value`, e.g. "Volume (shares)"
    raw: dict = field(default_factory=dict)   # anything else worth keeping


@dataclass
class Anomaly:
    point: DataPoint
    baseline: float
    delta: float              # fractional deviation from baseline, e.g. 0.42 = +42%

    @property
    def delta_pct(self) -> str:
        return f"{self.delta * 100:+.1f}%"

    def __str__(self) -> str:
        return (
            f"[{self.point.source}] {self.point.symbol} @ {self.point.timestamp} — "
            f"{self.point.value_label}={self.point.value:,.2f} vs baseline "
            f"{self.baseline:,.2f} (delta {self.delta_pct}, threshold "
            f"{config.DELTA_THRESHOLD*100:.0f}%)"
        )


def rolling_baseline(values: List[float], window: int = None) -> Optional[float]:
    """
    The 'market trend' number: simple rolling mean of the most recent
    `window` values, EXCLUDING the very last one (which is the candidate
    we're testing against it).

    Returns None if there isn't enough history yet.
    """
    window = window or config.BASELINE_WINDOW
    history = values[:-1]  # everything except the current/latest point
    if len(history) < min(3, window):  # need at least a few points to mean anything
        return None
    sample = history[-window:]
    return mean(sample)


def compute_delta(current: float, baseline: float) -> float:
    """(current - baseline) / baseline. Guards against divide-by-zero."""
    if baseline == 0:
        return float("inf") if current != 0 else 0.0
    return (current - baseline) / baseline


def find_anomalies(
    points: List[DataPoint],
    threshold: float = None,
    window: int = None,
) -> List[Anomaly]:
    """Check ONLY the latest data point (last working day) against baseline."""
    if not points:
        return []

    threshold = threshold if threshold is not None else config.DELTA_THRESHOLD
    window = window or config.BASELINE_WINDOW

    points = sorted(points, key=lambda p: p.timestamp)
    values = [p.value for p in points]

    # Calculate baseline using historical values (excluding the latest point)
    baseline = rolling_baseline(values, window=window)
    if baseline is None:
        return []

    # Check only the last working day
    latest_point = points[-1]
    delta = compute_delta(latest_point.value, baseline)

    if delta >= threshold:
        return [Anomaly(point=latest_point, baseline=baseline, delta=delta)]

    return []