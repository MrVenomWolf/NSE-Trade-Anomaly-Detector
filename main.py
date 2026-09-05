"""
main.py
========
Run this to scan all NSE equities in config.py and print/log any
statistically anomalous volume activity.

    python main.py                     -> scan everything, default thresholds
    python main.py --rvol 2.5          -> require 2.5x relative volume
    python main.py --z-score 3.0       -> require 3.0 sigma
"""

import argparse
from concurrent.futures import ThreadPoolExecutor

import config
from anomaly_engine import find_anomalies
from alerts import print_alerts, log_alerts_to_csv
from data_sources import equities


def fetch_single_equity(ticker):
    try:
        return equities.fetch_equity_volume(ticker)
    except Exception:
        return []


def scan_equities():
    print(f"Fetching {len(config.EQUITY_TICKERS)} NSE equities in parallel...")
    all_points = []
    with ThreadPoolExecutor(max_workers=30) as executor:
        results = executor.map(fetch_single_equity, config.EQUITY_TICKERS)
    for pts in results:
        all_points.extend(pts)
    return all_points


def run(min_rvol=None, min_z_score=None):
    all_points = scan_equities()

    if not all_points:
        print("No data fetched — check network connection.")
        return []

    by_symbol = {}
    for p in all_points:
        by_symbol.setdefault(p.symbol, []).append(p)

    all_anomalies = []
    for symbol, points in by_symbol.items():
        all_anomalies += find_anomalies(points, min_rvol=min_rvol, min_z_score=min_z_score)

    print_alerts(all_anomalies, min_rvol=min_rvol, min_z_score=min_z_score)
    if all_anomalies:
        log_alerts_to_csv(all_anomalies)

    return all_anomalies


def main():
    parser = argparse.ArgumentParser(description="NSE trade anomaly detector")
    parser.add_argument("--rvol", type=float, default=None, help="Minimum relative volume multiplier")
    parser.add_argument("--z-score", type=float, default=None, help="Minimum log Z-score")
    args = parser.parse_args()

    run(min_rvol=args.rvol, min_z_score=args.z_score)


if __name__ == "__main__":
    main()