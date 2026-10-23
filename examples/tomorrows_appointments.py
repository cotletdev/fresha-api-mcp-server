#!/usr/bin/env python3
"""Tomorrow's Fresha appointments, one line each, grouped by team member.

    python tomorrows_appointments.py
    python tomorrows_appointments.py --date 2026-10-28 --out day.csv

Cancelled and no-show appointments are left out unless you pass --all.
"""

import argparse
from collections import defaultdict
from datetime import date, timedelta

from fresha_api_mcp.scripting import paginate, run, write_rows

SKIP = ("cancel", "no-show", "no show")


def main() -> None:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("--date", default=str(date.today() + timedelta(days=1)), help="YYYY-MM-DD, default tomorrow")
    parser.add_argument("--all", action="store_true", help="Also cancelled and no-show appointments")
    parser.add_argument("--out", help="Save the rows to .csv or .json instead of printing them")
    args = parser.parse_args()

    rows = list(paginate("list_appointments", {"from": args.date, "to": args.date, "limit": 100}, "appointments"))
    if not args.all:
        rows = [r for r in rows if not any(word in (r.get("status") or "").lower() for word in SKIP)]
    rows.sort(key=lambda r: r["starts_at"])
    if args.out:
        write_rows(rows, args.out)
        return
    by_member: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_member[r.get("team_member") or "Unassigned"].append(r)
    print(f"{args.date}: {len(rows)} booked services")
    for member, visits in sorted(by_member.items()):
        print(f"\n{member}")
        for r in visits:
            client = (r.get("client") or {}).get("name") or "Walk-in"
            print(f"  {r['starts_at'][11:16]} {r['duration_minutes']:>3} min  {client}: {r['service']} ({r['status']})")


if __name__ == "__main__":
    run(main)
