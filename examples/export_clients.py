#!/usr/bin/env python3
"""Every Fresha client to CSV or JSON: name, email, mobile, gender, total sales, reviews, created date.

    python export_clients.py --out clients.csv
    python export_clients.py --search "@gmail.com" --out gmail.json

Without --out it prints JSON. Fresha pages clients 50 at a time, the script follows every page.
"""

import argparse

from fresha_api_mcp.scripting import paginate, run, write_rows


def main() -> None:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("--search", help="Only clients whose name, email or phone matches")
    parser.add_argument("--sort", choices=["newest", "oldest", "name"], default="name")
    parser.add_argument("--out", help="Save to .csv or .json instead of printing JSON")
    args = parser.parse_args()

    params = {"search": args.search, "sort": args.sort, "limit": 50}
    write_rows(list(paginate("list_clients", {k: v for k, v in params.items() if v}, "clients")), args.out)


if __name__ == "__main__":
    run(main)
