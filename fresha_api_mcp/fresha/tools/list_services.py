"""List services: gateway `services_getCatalogItems`."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from fresha_api_mcp.core.tools import tool
from fresha_api_mcp.fresha.client import workspace
from fresha_api_mcp.fresha.tools._shared import money, services

if TYPE_CHECKING:
    from fresha_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {"search": {"type": "string", "description": "Only services whose name contains this."}},
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "currency": "GBP",
    "services": [
        {
            "service_id": "25979401",
            "name": "Haircut",
            "category": "Hair & styling",
            "duration_minutes": 45,
            "price": 25.0,
            "price_type": "FIXED",
            "online_booking": True,
            "pricing_levels": [{"pricing_level_id": "29838166", "name": None, "duration_minutes": 45, "price": 25.0}],
        }
    ],
}


@tool(
    name="list_services",
    title="List services",
    access="read",
    description="Services of the business with category, duration and price.",
    details=(
        "Lists the active services of the business's location as the Catalogue shows them, with their "
        "category, duration in minutes, price and whether clients can book them online. A service with "
        "several prices (by length or level) lists each as a pricing level; bookings use the first one. "
        "Use service_id in find_available_slots and create_appointment."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /services",
    example_response=EXAMPLE_RESPONSE,
)
async def list_services(ctx: ToolContext, args: dict[str, Any]) -> Any:
    search = (args.get("search") or "").strip().lower()
    rows = []
    for service in await services(ctx):
        if search and search not in str(service.get("name") or "").lower():
            continue
        levels = service.get("servicePricingLevels") or []
        first = levels[0] if levels else {}
        rows.append(
            {
                "service_id": str(service["id"]),
                "name": service.get("name"),
                "category": (service.get("group") or {}).get("name"),
                "duration_minutes": first.get("duration"),
                "price": money(first.get("price")),
                "price_type": first.get("retailPriceType"),
                "online_booking": bool(service.get("onlineBookingEnabled")),
                "pricing_levels": [
                    {
                        "pricing_level_id": str(level["id"]),
                        "name": level.get("name"),
                        "duration_minutes": level.get("duration"),
                        "price": money(level.get("price")),
                    }
                    for level in levels
                ],
            }
        )
    return {"currency": (await workspace(ctx)).currency, "services": rows}
