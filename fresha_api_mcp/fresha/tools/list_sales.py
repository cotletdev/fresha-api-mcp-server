"""List sales: the Sales > Sales list report, reports.fresha.com `sales_list`.

The account has had no sale yet (22.10.2026), so the row columns are not known: each row comes back as
Fresha's cells, `{column: value}`, with the record ids Fresha links (`<column>_id`).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from fresha_api_mcp.core.errors import ErrorCode, ToolError
from fresha_api_mcp.core.helpers import limit
from fresha_api_mcp.core.tools import tool
from fresha_api_mcp.fresha.client import report, workspace
from fresha_api_mcp.fresha.tools._shared import CURSOR, LIMIT, offset_cursor, parse_day

if TYPE_CHECKING:
    from fresha_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "from": {"type": "string", "format": "date", "description": "First day."},
        "to": {"type": "string", "format": "date", "description": "Last day. Default: same as from."},
        "limit": LIMIT,
        "cursor": CURSOR,
    },
    "required": ["from"],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "currency": "GBP",
    "sales": [
        {
            "sale_no": "1",
            "sale_no_id": "880001",
            "sale_date": "2026-10-22",
            "client": "Emily Carter",
            "client_id": "304928171",
            "status": "Completed",
            "gross_total": 22.0,
        }
    ],
    "total": 1,
    "next_cursor": None,
}


def _flat(row: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for column, value in row.items():
        if not isinstance(value, dict):
            continue
        out[column] = value.get("value")
        if value.get("record_id") is not None:
            out[f"{column}_id"] = str(value["record_id"])
    return out


@tool(
    name="list_sales",
    title="List sales",
    access="read",
    description="Sales (invoices) in a date range: number, date, client, status and totals.",
    details=(
        "Lists sales as Sales > Sales list shows them for the days given, one row per sale with Fresha's "
        "columns (sale number, date, client, status, gross total and so on; linked records come with an "
        "`_id`). Amounts are in the business's currency. Page with next_cursor."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /sales",
    example_response=EXAMPLE_RESPONSE,
)
async def list_sales(ctx: ToolContext, args: dict[str, Any]) -> Any:
    first = parse_day(args["from"], "from")
    last = parse_day(args["to"], "to") if args.get("to") else first
    if last < first:
        raise ToolError("to is before from.", ErrorCode.INVALID_INPUT)
    offset, size = offset_cursor(args.get("cursor")), limit(args, 50, 100)
    params = {"date-from": first, "date-to": last, "limit": size, "offset": offset}
    rows, total = await report(ctx, "sales_list", params)
    more = offset + len(rows) < total if isinstance(total, int) else len(rows) >= size
    return {
        "currency": (await workspace(ctx)).currency,
        "sales": [_flat(row) for row in rows],
        "total": total,
        "next_cursor": str(offset + len(rows)) if rows and more else None,
    }
