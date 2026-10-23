#!/usr/bin/env python3
"""A team member is out for a day: block their calendar and hand each client to a colleague at the same time.

    python team_member_out.py --team-member-id 5652945 --date 2026-10-30
    python team_member_out.py --team-member-id 5652945 --date 2026-10-30 --block 09:00-18:00 --apply

Without --apply it only prints the plan. With --apply it asks before the block and before each move.
Clients no colleague can take at the same time are listed, so you can offer them another day or cancel
with cancel_day.py.
"""

import argparse

from fresha_api_mcp.scripting import call, run

SKIP = ("cancel", "no-show", "no show", "completed")


def visits(team_member_id: str, day: str) -> list[dict]:
    """The team member's open appointments on the day, one entry per appointment."""
    rows = call("list_appointments", {"from": day, "to": day, "team_member_id": team_member_id, "limit": 100})
    seen: dict[str, dict] = {}
    for r in rows["appointments"]:
        if not any(word in (r.get("status") or "").lower() for word in SKIP):
            seen.setdefault(r["appointment_id"], r)
    return sorted(seen.values(), key=lambda r: r["starts_at"])


def colleague_free(appointment: dict, members: list[dict], absent: str) -> dict | None:
    """The first colleague who offers every service and is free at the original start."""
    detail = call("get_appointment", {"appointment_id": appointment["appointment_id"]})
    service_ids = [b["service_id"] for b in detail["bookings"]]
    start = appointment["starts_at"]
    for member in members:
        if member["team_member_id"] == absent or not member["takes_bookings"]:
            continue
        if not set(service_ids) <= set(member["service_ids"]):
            continue
        slots = call(
            "find_available_slots",
            {"service_ids": service_ids, "date": start[:10], "team_member_id": member["team_member_id"]},
        )
        if any(start[11:16] in day["start_times"] for day in slots["days"]):
            return member
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("--team-member-id", required=True, help="Who is out, from list_team_members")
    parser.add_argument("--date", required=True, help="YYYY-MM-DD")
    parser.add_argument("--block", metavar="HH:MM-HH:MM", help="Also block these hours in their calendar")
    parser.add_argument("--title", default="Time off", help="Title of the block on the calendar")
    parser.add_argument("--apply", action="store_true", help="Make the block and the moves")
    parser.add_argument("--quiet", action="store_true", help="Move without Fresha telling the clients")
    args = parser.parse_args()

    members = call("list_team_members")["team_members"]
    if args.block:
        start, end = args.block.split("-")
        print(f"Block {args.date} {start} to {end} ({args.title})")
        if args.apply and input("  Add the block? [y/N] ").strip().lower() == "y":
            call(
                "add_blocked_time",
                {
                    "team_member_id": args.team_member_id,
                    "start_at": f"{args.date}T{start}",
                    "end_at": f"{args.date}T{end}",
                    "title": args.title,
                },
            )
            print("  blocked")
    stuck = []
    for a in visits(args.team_member_id, args.date):
        client = (a.get("client") or {}).get("name") or "Walk-in"
        member = colleague_free(a, members, args.team_member_id)
        if member is None:
            stuck.append(a)
            continue
        print(f"{a['starts_at'][11:16]} {client} ({a['service']}) -> {member['name']}, same time")
        if args.apply and input("  Move? [y/N] ").strip().lower() == "y":
            call(
                "reschedule_appointment",
                {
                    "appointment_id": a["appointment_id"],
                    "start_at": a["starts_at"],
                    "team_member_id": member["team_member_id"],
                    "notify_client": not args.quiet,
                },
            )
            print("  moved")
    for a in stuck:
        client = (a.get("client") or {}).get("name") or "Walk-in"
        print(
            f"No colleague free: {a['starts_at'][11:16]} {client} ({a['service']}), appointment {a['appointment_id']}"
        )


if __name__ == "__main__":
    run(main)
