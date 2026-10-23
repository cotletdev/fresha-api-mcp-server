#!/usr/bin/env python3
"""Turn a booking request into a Fresha appointment: match the client, find a slot for every service, book it.

    python book_from_message.py --client "Anna Smith" --services "Haircut,Colour" --date 2026-10-30 --after 12:00
    python book_from_message.py --client +447700900123 --services Haircut --date 2026-10-30 --book

Without --book it only prints the match and the free start times. With --book it books the first one
after you confirm. Fresha may send the client a confirmation by their notification settings.
"""

import argparse

from fresha_api_mcp.scripting import call, run


def pick_client(query: str) -> dict:
    found = call("list_clients", {"search": query, "limit": 10})["clients"]
    if not found:
        raise SystemExit(f"No client matches {query!r}. Add one with add_client first.")
    if len(found) > 1:
        print(f"{len(found)} clients match {query!r}:")
        for c in found:
            print(f"  {c['client_id']}  {c['name']}  {c.get('email') or ''} {c.get('phone') or ''}")
        raise SystemExit("Pass a phone number or email to pick one.")
    return found[0]


def pick_services(names: str) -> list[dict]:
    catalogue = call("list_services")["services"]
    picked = []
    for name in [n.strip() for n in names.split(",") if n.strip()]:
        matches = [s for s in catalogue if name.lower() in s["name"].lower()]
        if not matches:
            raise SystemExit(f"No service named like {name!r}. Run: fresha-mcp call list_services")
        picked.append(min(matches, key=lambda s: len(s["name"])))
    return picked


def main() -> None:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("--client", required=True, help="Name, email or phone of the client")
    parser.add_argument("--services", required=True, help="Service names, comma separated, in the order done")
    parser.add_argument("--date", required=True, help="First day to search, YYYY-MM-DD")
    parser.add_argument("--days", type=int, default=1, help="Days to search, at most 14")
    parser.add_argument("--after", default="00:00", help="Earliest start, HH:MM")
    parser.add_argument("--before", default="23:59", help="Latest start, HH:MM")
    parser.add_argument("--team-member-id", help="From list_team_members; default the first who takes bookings")
    parser.add_argument("--book", action="store_true", help="Book the first free time after you confirm")
    args = parser.parse_args()

    client = pick_client(args.client)
    services = pick_services(args.services)
    profile = call("get_client", {"client_id": client["client_id"]})
    print(f"Client: {client['name']} ({client['client_id']}), {profile['stats']['bookings']} bookings")
    for visit in profile.get("upcoming_appointments") or []:
        print(f"  already booked: {visit['starts_at']} {', '.join(visit.get('services') or [])}")
    print("Services: " + ", ".join(f"{s['name']} {s['duration_minutes']} min" for s in services))

    slots = call(
        "find_available_slots",
        {
            "service_ids": [s["service_id"] for s in services],
            "date": args.date,
            "days": args.days,
            "team_member_id": args.team_member_id,
        },
    )
    free = [
        f"{day['date']}T{time}"
        for day in slots["days"]
        for time in day["start_times"]
        if args.after <= time <= args.before
    ]
    if not free:
        raise SystemExit("No free start time in that window.")
    print(
        f"Free starts ({slots['duration_minutes']} min, team member {slots['team_member_id']}): " + ", ".join(free[:12])
    )
    if not args.book:
        return
    if input(f"Book {client['name']} at {free[0]}? [y/N] ").strip().lower() != "y":
        return
    booked = call(
        "create_appointment",
        {
            "client_id": client["client_id"],
            "start_at": free[0],
            "service_ids": [s["service_id"] for s in services],
            "team_member_id": slots["team_member_id"],
        },
    )
    print(f"Booked {booked['appointment_id']}: {booked['starts_at']} to {booked['ends_at']}")
    for warning in booked.get("warnings") or []:
        print(f"  Fresha warns: {warning}")


if __name__ == "__main__":
    run(main)
