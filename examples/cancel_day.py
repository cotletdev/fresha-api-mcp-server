#!/usr/bin/env python3
"""Cancel a team member's Fresha appointments on one day, with your cancellation reason.

    python cancel_day.py --team-member-id 5652945 --date 2026-10-30 --reason "Team member unwell"
    python cancel_day.py --team-member-id 5652945 --date 2026-10-30 --reason "Team member unwell" --apply

Without --apply it only lists what would be cancelled. With --apply it asks before each one. Fresha tells
each client unless you pass --quiet. Appointments with a cancellation fee or a paid deposit are refused:
cancel those in Fresha.
"""

import argparse

from fresha_api_mcp.core.errors import ToolError
from fresha_api_mcp.scripting import call, run

SKIP = ("cancel", "no-show", "no show", "completed")


def main() -> None:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("--team-member-id", required=True, help="From list_team_members")
    parser.add_argument("--date", required=True, help="YYYY-MM-DD")
    parser.add_argument("--reason", help="One of your cancellation reasons in Fresha, e.g. Client not available")
    parser.add_argument("--apply", action="store_true", help="Cancel, asking before each one")
    parser.add_argument("--quiet", action="store_true", help="Do not let Fresha tell the clients")
    args = parser.parse_args()

    rows = call(
        "list_appointments",
        {"from": args.date, "to": args.date, "team_member_id": args.team_member_id, "limit": 100},
    )["appointments"]
    todo: dict[str, dict] = {}
    for r in rows:
        if not any(word in (r.get("status") or "").lower() for word in SKIP):
            todo.setdefault(r["appointment_id"], r)
    print(f"{len(todo)} appointments to cancel on {args.date}")
    for a in sorted(todo.values(), key=lambda r: r["starts_at"]):
        client = (a.get("client") or {}).get("name") or "Walk-in"
        print(f"  {a['starts_at'][11:16]} {client}: {a['service']} ({a['appointment_id']})")
        if not args.apply or input("    Cancel? [y/N] ").strip().lower() != "y":
            continue
        try:
            done = call(
                "cancel_appointment",
                {"appointment_id": a["appointment_id"], "reason": args.reason, "notify_client": not args.quiet},
            )
            print(f"    {done['status']}, client told: {done['client_notified']}")
        except ToolError as err:
            print(f"    not cancelled: {err}")


if __name__ == "__main__":
    run(main)
