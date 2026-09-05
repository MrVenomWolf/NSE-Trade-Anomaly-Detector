"""
anomaly_engine.py
==================
The math. Every data source module produces a plain list of
DataPoint objects; this file decides which ones count as
statistically anomalous.

Volume is log-normally distributed and right-skewed, so raw percentage
deviation is a poor anomaly signal. This engine instead:
  1. Baselines on the MEDIAN of a rolling window (outlier-resistant,
     unlike a simple moving average).
  2. Computes a log-transformed Z-score to correct for volume's
     log-normal distribution.
  3. Computes a Median Absolute Deviation (MAD) based modified Z-score
     as a secondary, outlier-resistant robustness signal.
  4. Flags an anomaly only when BOTH the Z-score AND RVOL clear their
     thresholds (dual-threshold system), reducing false positives from
     any single noisy metric.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List

import numpy as np

import config


@dataclass
class DataPoint:
    """One observation for one instrument at one point in time."""
    source: str
    symbol: str
    timestamp: datetime
    value: float              # trading volume (shares)
    value_label: str = "Volume"
    raw: dict = field(default_factory=dict)


@dataclass
class Anomaly:
    point: DataPoint
    baseline_median: float
    rvol: float               # Relative Volume ratio (e.g. 3.2 = 3.2x baseline)
    z_score: float             # Log-transformed volume Z-score
    modified_z_score: float    # MAD-based robust Z-score (informational)

    @property
    def delta_pct(self) -> str:
        return f"{(self.rvol - 1.0) * 100:+.1f}%"

    def __str__(self) -> str:
        return (
            f"[{self.point.source}] {self.point.symbol} @ {self.point.timestamp} — "
            f"{self.point.value_label}={self.point.value:,.0f} vs baseline median "
            f"{self.baseline_median:,.0f} (RVOL {self.rvol:.2f}x, "
            f"Z-score {self.z_score:+.2f}\u03c3, robust Z {self.modified_z_score:+.2f}\u03c3)"
        )


def calculate_robust_metrics(history: np.ndarray, current: float):
    """
    Computes, using NumPy:
      1. RVOL        = current / median(history)
      2. Log Z-score = (ln(1+current) - mean(ln(1+history))) / std(ln(1+history))
      3. Modified Z   = 0.6745 * (current - median(history)) / MAD(history)

    Returns (baseline_median, rvol, z_score, modified_z). Degenerate/
    insufficient inputs return 0.0 for the metrics that can't be computed.
    """
    if current <= 0 or history.size == 0:
        return 0.0, 0.0, 0.0, 0.0

    baseline_med = float(np.median(history))
    rvol = current / baseline_med if baseline_med > 0 else 1.0

    positive_history = history[history > 0]
    log_current = np.log1p(current)
    if positive_history.size >= 5:
        log_history = np.log1p(positive_history)
        log_mean = float(np.mean(log_history))
        log_std = float(np.std(log_history, ddof=1))
        z_score = (log_current - log_mean) / log_std if log_std > 0 else 0.0
    else:
        z_score = 0.0

    mad = float(np.median(np.abs(history - baseline_med)))
    modified_z = (0.6745 * (current - baseline_med)) / mad if mad > 0 else 0.0

    return baseline_med, rvol, z_score, modified_z


def find_anomalies(
    points: List[DataPoint],
    min_rvol: float = None,
    min_z_score: float = None,
    window: int = None,
) -> List[Anomaly]:
    """Check ONLY the latest data point against historical robust statistics."""
    window = window or config.BASELINE_WINDOW
    min_rvol = min_rvol if min_rvol is not None else config.MIN_RVOL
    min_z_score = min_z_score if min_z_score is not None else config.MIN_Z_SCORE

    if not points or len(points) < window + 1:
        return []

    points = sorted(points, key=lambda p: p.timestamp)
    values = np.array([p.value for p in points], dtype=float)

    history = values[-(window + 1):-1]
    latest_point = points[-1]

    baseline_med, rvol, z_score, modified_z = calculate_robust_metrics(history, latest_point.value)

    # Dual-threshold: BOTH conditions must clear for a flag
    if z_score >= min_z_score and rvol >= min_rvol:
        return [
            Anomaly(
                point=latest_point,
                baseline_median=baseline_med,
                rvol=rvol,
                z_score=z_score,
                modified_z_score=modified_z,
            )
        ]
    return []