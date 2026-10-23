#!/usr/bin/env python3
"""List Fresha reviews you have not replied to yet, lowest rating first, and optionally reply to one.

    python unanswered_reviews.py
    python unanswered_reviews.py --reply-to 7120044 --text "Thank you, see you next month!"

A reply is public on your Fresha page and the client is told.
"""

import argparse
import json

from fresha_api_mcp.scripting import call, paginate, run


def main() -> None:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("--reply-to", metavar="REVIEW_ID")
    parser.add_argument("--text", help="The reply")
    parser.add_argument("--as-team-member", action="store_true", help="Sign as you, not as the business")
    args = parser.parse_args()

    if args.reply_to:
        if not args.text:
            parser.error("--text is required with --reply-to")
        reply = {"review_id": args.reply_to, "text": args.text}
        if args.as_team_member:
            reply["reply_as"] = "team_member"
        print(json.dumps(call("reply_to_review", reply), indent=2))
        return
    pending = sorted(
        paginate("list_reviews", {"unreplied_only": True, "limit": 100}, "reviews"), key=lambda r: r["rating"]
    )
    print(f"{len(pending)} reviews without a reply")
    for r in pending:
        print(f"  [{r['review_id']}] {r['rating']}/5 {r.get('author') or ''}: {(r.get('text') or '')[:80]}")


if __name__ == "__main__":
    run(main)
