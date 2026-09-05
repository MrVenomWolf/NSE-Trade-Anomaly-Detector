"""
alerts.py
==========
Dynamic threshold display in console outputs.
"""

import csv
import os
from datetime import datetime, timezone
from typing import List

from anomaly_engine import Anomaly
import config


def print_alerts(anomalies: List[Anomaly], min_rvol: float = None, min_z_score: float = None) -> None:
    if not anomalies:
        print("No trades crossed the threshold this run. Nothing to flag.")
        return

    active_rvol = min_rvol if min_rvol is not None else config.MIN_RVOL
    active_z = min_z_score if min_z_score is not None else config.MIN_Z_SCORE

    print(f"\n{'='*70}")
    print(f"  {len(anomalies)} ANOMALOUS VOLUME EVENT(S) FOUND "
          f"(RVOL >= {active_rvol:.1f}x, Z-score >= {active_z}\u03c3)")
    print(f"{'='*70}")
    for a in anomalies:
        print(f"\n  {a}")


def log_alerts_to_csv(anomalies: List[Anomaly], path: str = None) -> None:
    path = path or config.ALERT_LOG_FILE
    file_exists = os.path.exists(path)
    with open(path, "a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow([
                "detected_at", "source", "symbol", "trade_timestamp",
                "value", "value_label", "baseline_median", "rvol", "z_score", "modified_z_score",
            ])
        detected_at = datetime.now(timezone.utc).isoformat()
        for a in anomalies:
            writer.writerow([
                detected_at,
                a.point.source,
                a.point.symbol,
                a.point.timestamp.isoformat(),
                a.point.value,
                a.point.value_label,
                a.baseline_median,
                f"{a.rvol:.2f}",
                f"{a.z_score:.2f}",
                f"{a.modified_z_score:.2f}",
            ])
    print(f"\nLogged {len(anomalies)} alert(s) to {path}")