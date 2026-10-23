"""Get sales summary: Reports > Sales summary, partners-reporting-api `getInsightData` id `sales-summary`.
Rows are Fresha's own table rows, keyed by its column ids."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from fresha_api_mcp.core.errors import ErrorCode, ToolError
from fresha_api_mcp.core.tools import tool
from fresha_api_mcp.fresha.client import REPORTING, gql, workspace
from fresha_api_mcp.fresha.tools._shared import parse_day

if TYPE_CHECKING:
    from fresha_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "from": {"type": "string", "format": "date", "description": "First day."},
        "to": {"type": "string", "format": "date", "description": "Last day. Default: same as from."},
    },
    "required": ["from"],
    "additionalProperties": False,
}

_QUERY = """query getInsightData($id: String!, $filters: [FilterType]!, $limit: Int!, $offset: Int!,
    $dateRange: DateRangeFilter) {
  getInsightData(id: $id, filters: $filters, limit: $limit, offset: $offset, dateRange: $dateRange) {
    config { sections { title columns { id title type } } }
    rows summaryRow count lastUpdated
  }
}"""

EXAMPLE_RESPONSE: dict[str, Any] = {
    "from": "2026-10-01",
    "to": "2026-10-22",
    "currency": "GBP",
    "columns": [{"id": "type", "title": "Type"}, {"id": "gross_sales", "title": "Gross sales"}],
    "rows": [{"type": "Services", "gross_sales": 22.0}],
    "totals": {"type": "Total", "gross_sales": 22.0},
    "updated_at": "2026-10-22 10:20:19",
}


@tool(
    name="get_sales_summary",
    title="Get sales summary",
    access="read",
    description="Sales summary for a period: sales, refunds, discounts, taxes and payments by type.",
    details=(
        "Reads Reports > Sales summary for the days given: one row per sale type (services, products, "
        "memberships, gift cards and so on) with Fresha's own columns (gross and net sales, discounts, "
        "refunds, taxes) and a totals row. columns names each key. A period without sales has no rows. "
        "Amounts are in the business's currency."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /sales-summary",
    example_response=EXAMPLE_RESPONSE,
)
async def get_sales_summary(ctx: ToolContext, args: dict[str, Any]) -> Any:
    first = parse_day(args["from"], "from")
    last = parse_day(args["to"], "to") if args.get("to") else first
    if last < first:
        raise ToolError("to is before from.", ErrorCode.INVALID_INPUT)
    variables = {
        "id": "sales-summary",
        "filters": [],
        "limit": 100,
        "offset": 0,
        "dateRange": {"dateFrom": first, "dateTo": last},
    }
    data = (await gql(ctx, "getInsightData", _QUERY, variables, host=REPORTING)).get("getInsightData") or {}
    sections = (data.get("config") or {}).get("sections") or []
    columns = [
        {"id": c.get("id"), "title": c.get("title")} for section in sections for c in section.get("columns") or []
    ]
    rows = data.get("rows") or []
    return {
        "from": first,
        "to": last,
        "currency": (await workspace(ctx)).currency,
        "columns": columns,
        "rows": [row for row in rows if isinstance(row, dict)],
        "totals": data.get("summaryRow") or None,
        "updated_at": data.get("lastUpdated"),
    }
