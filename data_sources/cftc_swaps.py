"""
data_sources/cftc_swaps.py
============================
Real swap & CDS data, straight from the U.S. regulator.

Under Dodd-Frank, swap data repositories (DTCC, ICE, CME) must report
aggregated market data to the CFTC, which publishes it free, weekly,
every Monday, at:
    https://www.cftc.gov/MarketReports/SwapsReports/index.htm

WHAT THIS GIVES YOU: real weekly ticket-volume (# of trades) and gross
notional (total $ value) for Interest Rate Swaps, Credit Default Swaps,
and FX/Cross-Currency Swaps.

WHAT THIS DOES NOT GIVE YOU: individual trade tickets in real time.
The CFTC's own per-asset-class pages only show the CURRENT week, not a
history — so this module builds its OWN trend history by appending
each week's snapshot to a local CSV (`swap_history.csv`) every time you
run it. After a few weeks of runs, `find_anomalies()` will have enough
history to actually flag anything. This is a real, honest limitation
of free swap data — there is no public bulk download of historical
weekly snapshots, so "run it regularly" IS the intended usage pattern.

If CFTC ever changes their page layout, `_extract_total()` below is the
one function you'll need to fix — run this file directly
(`python data_sources/cftc_swaps.py`) to dump the raw tables it sees,
which makes that easy to debug.
"""

import csv
import os
from datetime import datetime, timezone
from typing import List, Optional

from anomaly_engine import DataPoint

# Ticket-volume pages, current week only, by asset class.
CFTC_TICKET_VOLUME_URLS = {
    "swap_irs": "https://www.cftc.gov/MarketReports/SwapsReports/L2IRSAct.html",
    "swap_cds": "https://www.cftc.gov/MarketReports/SwapsReports/L2CDSAct.html",
    "swap_fx": "https://www.cftc.gov/MarketReports/SwapsReports/L2FXAct.html",
}

HISTORY_FILE = os.path.join(os.path.dirname(__file__), "..", "swap_history.csv")


def _extract_total(tables) -> float:
    """
    CFTC's tables generally end with a 'Total' row. We scan every table
    on the page for a row whose first cell looks like a total, and take
    the last numeric column in that row (the most recent figure).
    If the layout doesn't match, this raises — see module docstring.
    """
    import pandas as pd  # noqa

    for table in tables:
        first_col = table.iloc[:, 0].astype(str).str.strip().str.lower()
        total_rows = table[first_col.str.contains("total", na=False)]
        if not total_rows.empty:
            row = total_rows.iloc[0]
            # walk backwards through the row looking for the last numeric cell
            for cell in reversed(row.tolist()[1:]):
                cleaned = str(cell).replace(",", "").replace("$", "").strip()
                try:
                    return float(cleaned)
                except ValueError:
                    continue
    raise ValueError(
        "Could not find a 'Total' row with a numeric value. CFTC may have "
        "changed their page layout — run this file directly to inspect "
        "the raw tables and adjust _extract_total()."
    )


def fetch_current_week_snapshot(asset_class: str) -> Optional[float]:
    """asset_class must be a key in CFTC_TICKET_VOLUME_URLS."""
    import pandas as pd

    url = CFTC_TICKET_VOLUME_URLS[asset_class]
    tables = pd.read_html(url)
    return _extract_total(tables)


def _append_to_history(asset_class: str, value: float, timestamp: datetime) -> None:
    file_exists = os.path.exists(HISTORY_FILE)
    with open(HISTORY_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["timestamp", "asset_class", "ticket_volume"])
        writer.writerow([timestamp.isoformat(), asset_class, value])


def _load_history(asset_class: str) -> List[DataPoint]:
    if not os.path.exists(HISTORY_FILE):
        return []
    points = []
    with open(HISTORY_FILE, newline="") as f:
        for row in csv.DictReader(f):
            if row["asset_class"] != asset_class:
                continue
            points.append(
                DataPoint(
                    source=asset_class,
                    symbol=asset_class.replace("swap_", "").upper(),
                    timestamp=datetime.fromisoformat(row["timestamp"]),
                    value=float(row["ticket_volume"]),
                    value_label="Weekly ticket volume (CFTC)",
                )
            )
    return points


def fetch_swap_points(asset_class: str, record_new: bool = True) -> List[DataPoint]:
    """
    Main entry point: fetches this week's real CFTC figure, records it
    into local history, and returns the FULL history (past + present)
    so the anomaly engine has something to compare against.
    """
    now = datetime.now(timezone.utc)
    if record_new:
        try:
            value = fetch_current_week_snapshot(asset_class)
            _append_to_history(asset_class, value, now)
        except Exception as e:
            print(f"[cftc_swaps] Warning: could not fetch fresh data for "
                  f"{asset_class}: {e}. Falling back to stored history only.")
    return _load_history(asset_class)


if __name__ == "__main__":
    # Debug helper: python data_sources/cftc_swaps.py
    import pandas as pd
    for name, url in CFTC_TICKET_VOLUME_URLS.items():
        print(f"\n=== {name}: {url} ===")
        try:
            tables = pd.read_html(url)
            for i, t in enumerate(tables):
                print(f"--- table {i} ---")
                print(t.head(10))
        except Exception as e:
            print(f"Failed to fetch/parse: {e}")
