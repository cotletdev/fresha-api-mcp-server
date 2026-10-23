#!/usr/bin/env python3
"""Clients with no appointment in the last N days and nothing booked, with their marketing consent.

    python lapsed_clients.py --days 90 --out lapsed.csv
    python lapsed_clients.py --days 60 --email-consent-only

Reads the Appointments report for the window, then every client profile it needs (one call per client),
so a long client list takes a while. Clients added within the window are left out.
"""

import argparse
from datetime import UTC, date, datetime, timedelta

from fresha_api_mcp.scripting import call, paginate, run, write_rows


def main() -> None:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("--days", type=int, default=90, help="No visit for this many days")
    parser.add_argument("--email-consent-only", action="store_true", help="Only clients who accept marketing email")
    parser.add_argument("--out", help="Save to .csv or .json")
    args = parser.parse_args()

    since = date.today() - timedelta(days=args.days)
    window = {"from": str(since), "to": str(date.today()), "limit": 100}
    seen = {
        (r.get("client") or {}).get("client_id")
        for r in paginate("list_appointments", window, "appointments")
        if "cancel" not in (r.get("status") or "").lower()
    }
    cutoff = datetime.combine(since, datetime.min.time(), UTC)
    lapsed = []
    for c in paginate("list_clients", {"sort": "oldest"}, "clients"):
        created = datetime.fromisoformat(c["created_at"])
        if c["client_id"] in seen or c["blocked"] or created >= cutoff:
            continue
        profile = call("get_client", {"client_id": c["client_id"]})
        if profile.get("upcoming_appointments"):
            continue
        marketing = profile.get("marketing") or {}
        if args.email_consent_only and not (marketing.get("email") and c.get("email")):
            continue
        lapsed.append(
            {
                "client_id": c["client_id"],
                "name": c["name"],
                "email": c.get("email"),
                "phone": c.get("phone"),
                "bookings": (profile.get("stats") or {}).get("bookings"),
                "total_sales": (profile.get("stats") or {}).get("total_sales"),
                "marketing_email": marketing.get("email"),
                "marketing_sms": marketing.get("sms"),
            }
        )
    write_rows(lapsed, args.out)


if __name__ == "__main__":
    run(main)
