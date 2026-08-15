"""
main.py
========
Run this to scan everything in config.py and print/log any
out-of-the-box trades.

    python main.py                  -> scan everything, default threshold
    python main.py --threshold 0.5  -> require 50% deviation instead of 30%
    python main.py --no-news        -> skip the news-headline lookup
    python main.py --equities-only  -> just stocks (fastest, good for testing)
"""

"""
main.py
========
Optimized with parallel multi-threading for fast scanning of 2,500+ NSE stocks.
"""

import argparse
from concurrent.futures import ThreadPoolExecutor
import config
from anomaly_engine import find_anomalies
from alerts import print_alerts, log_alerts_to_csv
from data_sources import equities


def fetch_single_equity(ticker):
    """Worker function for single equity fetch."""
    try:
        return equities.fetch_equity_volume(ticker)
    except Exception:
        return []


def scan_equities():
    print(f"Fetching {len(config.EQUITY_TICKERS)} NSE equities in parallel...")
    all_points = []
    
    # Run 30 requests in parallel
    with ThreadPoolExecutor(max_workers=30) as executor:
        results = executor.map(fetch_single_equity, config.EQUITY_TICKERS)

    for pts in results:
        all_points.extend(pts)

    return all_points


def run(threshold=None, include_equities=True, include_forex=True,
        include_swaps=True, include_news=True):
    all_points = []
    if include_equities:
        all_points += scan_equities()
    if include_forex:
        all_points += scan_forex()
    if include_swaps:
        all_points += scan_swaps()

    if not all_points:
        print("No data fetched — check network connection.")
        return []

    # Group by symbol
    by_symbol = {}
    for p in all_points:
        by_symbol.setdefault(p.symbol, []).append(p)

    all_anomalies = []
    for symbol, points in by_symbol.items():
        all_anomalies += find_anomalies(points, threshold=threshold)

    print_alerts(all_anomalies, threshold=threshold)
    if all_anomalies:
        log_alerts_to_csv(all_anomalies)

    return all_anomalies


def main():
    parser = argparse.ArgumentParser(description="Trade anomaly detector")
    parser.add_argument("--threshold", type=float, default=None)
    parser.add_argument("--equities-only", action="store_true")
    parser.add_argument("--forex-only", action="store_true")
    parser.add_argument("--swaps-only", action="store_true")
    parser.add_argument("--no-news", action="store_true")
    args = parser.parse_args()

    only_flags = [args.equities_only, args.forex_only, args.swaps_only]
    any_only = any(only_flags)

    run(
        threshold=args.threshold,
        include_equities=(not any_only or args.equities_only),
        include_forex=(not any_only or args.forex_only),
        include_swaps=(not any_only or args.swaps_only),
        include_news=(not args.no_news),
    )


if __name__ == "__main__":
    main()