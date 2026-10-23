#!/usr/bin/env python3
"""The Fresha Sales list for a date range to CSV or JSON, one row per sale.

    python export_sales.py --from 2026-10-01 --to 2026-10-31 --out october-sales.csv

Amounts are in the business's currency, with Fresha's own column names.
"""

import argparse

from fresha_api_mcp.scripting import paginate, run, write_rows


def main() -> None:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("--from", dest="start", required=True, help="First day, YYYY-MM-DD")
    parser.add_argument("--to", dest="end", help="Last day, default the first")
    parser.add_argument("--out", help="Save to .csv or .json instead of printing JSON")
    args = parser.parse_args()

    params = {"from": args.start, "to": args.end or args.start, "limit": 100}
    write_rows(list(paginate("list_sales", params, "sales")), args.out)


if __name__ == "__main__":
    run(main)
