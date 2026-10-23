"""Helpers for scripts: call a tool, follow pages, save CSV or JSON. The scripts in examples/ use them.

from fresha_api_mcp.scripting import call, paginate

for client in paginate("list_clients", {"sort": "newest"}, "clients", max_items=100):
    print(client["name"], client["email"])
"""

from __future__ import annotations

import csv
import json
import sys
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any

from fresha_api_mcp import call as _call
from fresha_api_mcp.core.errors import ToolError


def call(tool: str, params: dict[str, Any] | None = None) -> Any:
    """Run one tool; arguments set to None are left out."""
    return _call(tool, {k: v for k, v in (params or {}).items() if v is not None})


def paginate(tool: str, params: dict[str, Any], key: str, max_items: int | None = None) -> Iterator[dict[str, Any]]:
    """Yield every item of a list tool, following next_cursor."""
    params = dict(params)
    seen = 0
    while True:
        page = call(tool, params)
        for item in page.get(key, []):
            yield item
            seen += 1
            if max_items and seen >= max_items:
                return
        cursor = page.get("next_cursor")
        if not cursor:
            return
        params["cursor"] = cursor


def write_rows(rows: list[dict[str, Any]], out: str | None) -> None:
    """Print JSON to stdout, or save .csv / .json when a path is given."""
    if not out:
        print(json.dumps(rows, indent=2, ensure_ascii=False))
        return
    path = Path(out)
    if path.suffix.lower() == ".csv":
        fields: list[str] = []
        for row in rows:
            fields += [k for k in row if k not in fields]
        with path.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=fields)
            writer.writeheader()
            for row in rows:
                writer.writerow(
                    {k: json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v for k, v in row.items()}
                )
    else:
        path.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Saved {len(rows)} rows to {path}", file=sys.stderr)


def run(main: Callable[[], None]) -> None:
    """Run a script's main() and turn tool errors into a readable message."""
    try:
        main()
    except ToolError as err:
        sys.exit(f"{err.code}: {err}")
    except KeyboardInterrupt:
        sys.exit(130)
