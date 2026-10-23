#!/usr/bin/env python3
"""Yesterday's Fresha sales by sale type, against the same weekday a week earlier, with refunds flagged.

    python daily_sales.py
    python daily_sales.py --date 2026-10-27 --refund-alert 50

Prints one line per sale type from Reports > Sales summary. Good for a morning cron job:
    0 8 * * * cd ~/fresha-api-mcp-server && .venv/bin/python examples/daily_sales.py
"""

import argparse
from datetime import date, timedelta

from fresha_api_mcp.scripting import call, run


def summary(day: str) -> dict:
    return call("get_sales_summary", {"from": day, "to": day})


def column(report: dict, *words: str) -> str | None:
    """The id of the first column whose title has one of the words (Fresha names the columns)."""
    for col in report.get("columns") or []:
        if any(w in (col.get("title") or "").lower() for w in words):
            return col["id"]
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("--date", default=str(date.today() - timedelta(days=1)), help="YYYY-MM-DD, default yesterday")
    parser.add_argument("--refund-alert", type=float, default=50.0, help="Flag refunds above this amount")
    args = parser.parse_args()

    day = date.fromisoformat(args.date)
    now, before = summary(str(day)), summary(str(day - timedelta(days=7)))
    if not now.get("rows"):
        print(f"No sales on {day:%a %d %b %Y}.")
        return
    net = column(now, "net sales") or column(now, "total sales", "gross")
    refunds = column(now, "refund")
    earlier = {r.get("type"): r for r in before.get("rows") or []}
    print(f"Sales {day:%a %d %b %Y} vs {day - timedelta(days=7):%d %b}, {now['currency']}")
    for row in now["rows"] + ([now["totals"]] if now.get("totals") else []):
        value = float(row.get(net) or 0) if net else 0.0
        old = float((earlier.get(row.get("type")) or {}).get(net) or 0) if net else 0.0
        if row is now.get("totals"):
            old = float((before.get("totals") or {}).get(net) or 0) if net else 0.0
        change = f"{(value - old) / old:+.0%}" if old else "new"
        flag = ""
        if refunds and abs(float(row.get(refunds) or 0)) > args.refund_alert:
            flag = f"  REFUNDS {row.get(refunds)}"
        print(f"  {row.get('type')!s:<20} {value:>10.2f}  ({old:.2f}, {change}){flag}")


if __name__ == "__main__":
    run(main)
