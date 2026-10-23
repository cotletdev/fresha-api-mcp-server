"""List clients: customers-api `GET /v2/customer-search`."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from fresha_api_mcp.core.helpers import limit
from fresha_api_mcp.core.tools import tool
from fresha_api_mcp.fresha.client import CUSTOMERS, rest
from fresha_api_mcp.fresha.tools._clients import EXAMPLE_CLIENT, client_row
from fresha_api_mcp.fresha.tools._shared import CURSOR, LIMIT, offset_cursor

if TYPE_CHECKING:
    from fresha_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "search": {"type": "string", "description": "Name, email or phone."},
        "sort": {
            "type": "string",
            "enum": ["newest", "oldest", "name"],
            "description": "Order: newest (default), oldest or name.",
        },
        "limit": {**LIMIT, "maximum": 50, "description": "Page size, at most 50 (Fresha refuses more). Default: 50."},
        "cursor": CURSOR,
    },
    "additionalProperties": False,
}

_SORT = {"newest": ("created-at", "desc"), "oldest": ("created-at", "asc"), "name": ("first-name", "asc")}


@tool(
    name="list_clients",
    title="List clients",
    access="read",
    description="Clients of the business, searchable by name, email or phone.",
    details=(
        "Lists clients as the Client list shows them, newest first by default, with email, mobile, gender, "
        "total sales, review count and whether they are blocked. search matches name, email or phone. "
        "total is the number of matching clients. Page with next_cursor."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /clients",
    example_response={"clients": [EXAMPLE_CLIENT], "total": 1, "next_cursor": None},
)
async def list_clients(ctx: ToolContext, args: dict[str, Any]) -> Any:
    offset, size = offset_cursor(args.get("cursor")), limit(args, 50, 50)
    sort_by, order = _SORT[args.get("sort") or "newest"]
    params: dict[str, Any] = {
        "offset": offset,
        "limit": size,
        "sort-by": sort_by,
        "sort-order": order,
        "include-customers-count": "true",
    }
    if search := (args.get("search") or "").strip():
        params["query"] = search
    answer = await rest(ctx, "GET", f"{CUSTOMERS}/v2/customer-search", params=params)
    rows = answer.get("data") or []
    total = (answer.get("meta") or {}).get("results-count")
    more = offset + len(rows) < total if isinstance(total, int) else len(rows) >= size
    return {
        "clients": [client_row(row) for row in rows],
        "total": total,
        "next_cursor": str(offset + len(rows)) if rows and more else None,
    }
