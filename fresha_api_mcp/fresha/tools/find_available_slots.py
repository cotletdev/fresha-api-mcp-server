"""Find available slots: gateway `availableTimeSlots`."""

from __future__ import annotations

from datetime import date, timedelta
from typing import TYPE_CHECKING, Any

from fresha_api_mcp.core.errors import ErrorCode, ToolError
from fresha_api_mcp.core.tools import tool
from fresha_api_mcp.fresha.client import gql, workspace
from fresha_api_mcp.fresha.tools._shared import (
    SERVICE_IDS,
    TEAM_MEMBER_ID,
    default_team_member,
    parse_day,
    pricing_levels,
)

if TYPE_CHECKING:
    from fresha_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "service_ids": SERVICE_IDS,
        "date": {"type": "string", "format": "date", "description": "First day to search."},
        "days": {"type": "integer", "minimum": 1, "maximum": 14, "description": "Days to search. Default: 1."},
        "team_member_id": {
            **TEAM_MEMBER_ID,
            "description": "Team member to book. Default: the first who takes bookings.",
        },
    },
    "required": ["service_ids", "date"],
    "additionalProperties": False,
}

_QUERY = """query availableTimeSlots($input: Scheduling_AvailableTimeSlotsInput!) {
  availableTimeSlots: Scheduling_availableTimeSlots(input: $input) {
    dailyAvailableTimeSlots { date closed locationId possibleOffers { startTime } }
  }
}"""

EXAMPLE_RESPONSE: dict[str, Any] = {
    "team_member_id": "5652945",
    "time_zone": "Europe/London",
    "duration_minutes": 45,
    "days": [{"date": "2026-10-23", "closed": False, "start_times": ["10:00", "10:15", "10:30"]}],
}


def _time(value: Any) -> str | None:
    """Fresha gives seconds after midnight (or `HH:MM:SS`): -> `HH:MM`."""
    if isinstance(value, int | float):
        hours, rest = divmod(int(value), 3600)
        return f"{hours:02d}:{rest // 60:02d}"
    return str(value)[:5] if value else None


@tool(
    name="find_available_slots",
    title="Find available slots",
    access="read",
    description="Free start times for one or more services with a team member, day by day.",
    details=(
        "Asks the calendar for free start times as New appointment does, for the services done one after "
        "another, with one team member, over up to 14 days. Times are wall clock in the business's time "
        "zone; closed days have no times. Book a time with create_appointment."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /available-slots",
    example_response=EXAMPLE_RESPONSE,
)
async def find_available_slots(ctx: ToolContext, args: dict[str, Any]) -> Any:
    first = parse_day(args["date"], "date")
    last = (date.fromisoformat(first) + timedelta(days=int(args.get("days") or 1) - 1)).isoformat()
    ws = await workspace(ctx)
    member = await default_team_member(ctx, args.get("team_member_id"))
    levels = await pricing_levels(ctx, args["service_ids"])
    if any(level["minutes"] <= 0 for level in levels):
        raise ToolError("A service has no duration in Fresha.", ErrorCode.TARGET_ERROR)
    offer_items = [
        {
            "itemType": "SERVICE_PRICING_LEVEL",
            "offerItemId": str(position),
            "position": position,
            "servicePricingLevel": {
                "servicePricingLevelId": level["id"],
                "requestedEmployeeId": member,
                "forceMaxDuration": False,
                "ignoreAssignments": False,
            },
        }
        for position, level in enumerate(levels, start=1)
    ]
    variables = {
        "input": {
            "attendees": [{"attendeeId": "1", "offerItems": offer_items}],
            "dateRange": {"startDate": first, "endDate": last},
            "locationId": ws.location_id,
            "timeslotSettingsMode": "UNRESTRICTED",
        }
    }
    data = await gql(ctx, "availableTimeSlots", _QUERY, variables)
    days = (data.get("availableTimeSlots") or {}).get("dailyAvailableTimeSlots") or []
    return {
        "team_member_id": member,
        "time_zone": ws.time_zone,
        "duration_minutes": sum(level["minutes"] for level in levels),
        "days": [
            {
                "date": day.get("date"),
                "closed": bool(day.get("closed")),
                "start_times": [t for o in day.get("possibleOffers") or [] if (t := _time(o.get("startTime")))],
            }
            for day in days
        ],
    }
