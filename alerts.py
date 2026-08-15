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


def print_alerts(anomalies: List[Anomaly], threshold: float = None) -> None:
    if not anomalies:
        print("No trades crossed the threshold this run. Nothing to flag.")
        return

    # Use runtime threshold if provided, else fall back to config
    active_threshold = threshold if threshold is not None else config.DELTA_THRESHOLD

    print(f"\n{'='*70}")
    print(f"  {len(anomalies)} OUT-OF-THE-BOX TRADE(S) FOUND "
          f"(>= {active_threshold * 100:.0f}% above trend)")
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
                "value", "value_label", "baseline", "delta_pct",
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
                a.baseline,
                f"{a.delta*100:.1f}",
            ])
    print(f"\nLogged {len(anomalies)} alert(s) to {path}")  