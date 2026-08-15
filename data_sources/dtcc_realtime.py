"""
data_sources/dtcc_realtime.py
================================
EXPERIMENTAL / OPTIONAL — this is the module for what you actually
described: individual, real-time large swap/CDS trades, not weekly
aggregates.

Under Dodd-Frank real-time reporting rules (17 CFR 43), DTCC's swap
data repository publishes individual trade tickets publicly, with
fields like notional amount, asset class, execution timestamp, and a
"block trade" flag — usually within minutes of execution. You can
browse it live here:
    https://rtdata.dtcc.com/gtr/dashboard.do

The catch: the exact CSV/file download URL for bulk-pulling that feed
programmatically has changed over the years and isn't something I can
verify or guarantee from here (I don't have live access to browse the
current dashboard). Rather than hand you a URL that might silently be
wrong, this module is set up as a slot you fill in yourself:

  1. Open the dashboard link above.
  2. Find the "Download" / export option for a day's data (usually a
     CSV or XML link).
  3. Paste that URL pattern into DTCC_CSV_URL_TEMPLATE below, with
     "{date}" where the date goes.
  4. Run this file directly to sanity-check the columns it returns
     against COLUMN_MAP.

One important note for what you're hoping to catch (huge one-off
trades): DTCC's real-time public feed CAPS notional amounts on very
large trades before publishing them, specifically to prevent identifying
counterparties on outsized deals — so the biggest trades will show up
capped/rounded, not exact. That's a regulatory privacy feature, not a
bug in this code.
"""

from datetime import datetime, timezone
from typing import List, Optional

from anomaly_engine import DataPoint

# Fill this in once you've confirmed the real download URL, e.g.:
# "https://rtdata.dtcc.com/gtr/export?date={date}&assetClass=CREDITS"
DTCC_CSV_URL_TEMPLATE: Optional[str] = None

# Adjust these to match whatever column names the real CSV actually uses.
COLUMN_MAP = {
    "notional": "Notional Amount",
    "asset_class": "Asset Class",
    "timestamp": "Execution Timestamp",
    "block_trade_flag": "Block Trade Election Indicator",
}


def fetch_dtcc_day(date: str) -> List[DataPoint]:
    """date format: 'YYYY-MM-DD'. Returns [] and prints guidance if the
    URL template hasn't been configured yet."""
    if not DTCC_CSV_URL_TEMPLATE:
        print(
            "[dtcc_realtime] Not configured yet — see the module docstring "
            "in data_sources/dtcc_realtime.py to wire up the real feed URL. "
            "Skipping this data source for now."
        )
        return []

    import pandas as pd

    url = DTCC_CSV_URL_TEMPLATE.format(date=date)
    df = pd.read_csv(url)

    points = []
    for _, row in df.iterrows():
        try:
            notional = float(str(row[COLUMN_MAP["notional"]]).replace(",", ""))
            ts_raw = row[COLUMN_MAP["timestamp"]]
            ts = pd.to_datetime(ts_raw).to_pydatetime()
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
        except (KeyError, ValueError):
            continue
        points.append(
            DataPoint(
                source="swap_realtime",
                symbol=str(row.get(COLUMN_MAP["asset_class"], "swap")),
                timestamp=ts,
                value=notional,
                value_label="Notional ($, capped on large trades)",
                raw={"block_trade": row.get(COLUMN_MAP["block_trade_flag"])},
            )
        )
    return points


if __name__ == "__main__":
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    pts = fetch_dtcc_day(today)
    print(f"Fetched {len(pts)} points for {today}")
