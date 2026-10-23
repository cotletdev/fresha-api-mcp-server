"""List team members: partners-api `/v2/employees` and `/locations`."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from fresha_api_mcp.core.tools import tool
from fresha_api_mcp.fresha.client import API, rest
from fresha_api_mcp.fresha.tools._shared import team_members

if TYPE_CHECKING:
    from fresha_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {"include_former": {"type": "boolean", "description": "Also team members who left. Default: false."}},
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "team_members": [
        {
            "team_member_id": "5652945",
            "name": "Daniel Hughes",
            "first_name": "Daniel",
            "last_name": "Hughes",
            "email": "daniel@example.com",
            "phone": "+44 7700 900123",
            "role": "owner",
            "job_title": None,
            "takes_bookings": True,
            "online_booking": True,
            "service_ids": ["25979401"],
            "location_id": "3231745",
            "left": False,
        }
    ],
    "locations": [{"location_id": "3231745", "name": "Hughes Barbers"}],
}


@tool(
    name="list_team_members",
    title="List team members",
    access="read",
    description="Team members with role, contact, services they do and whether they take bookings.",
    details=(
        "Lists the team as Team members shows it: name, email, mobile, role (owner, manager, basic), job "
        "title, whether they take bookings and online bookings, the services assigned to them and their "
        "location. Also lists the business's locations. Use team_member_id in the calendar tools."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /team-members",
    example_response=EXAMPLE_RESPONSE,
)
async def list_team_members(ctx: ToolContext, args: dict[str, Any]) -> Any:
    former = bool(args.get("include_former"))
    rows = []
    for member in await team_members(ctx, with_deleted=former):
        links = member["links"]
        location = ((links.get("primary-location") or {}).get("data") or {}).get("id")
        rows.append(
            {
                "team_member_id": member["id"],
                "name": member.get("name"),
                "first_name": member.get("first-name"),
                "last_name": member.get("last-name"),
                "email": member.get("email"),
                "phone": member.get("mobile-number"),
                "role": member.get("role"),
                "job_title": member.get("title"),
                "takes_bookings": bool(member.get("provides-services")),
                "online_booking": not member.get("excluded-from-online-bookings"),
                "service_ids": [str(s["id"]) for s in (links.get("services") or {}).get("data") or []],
                "location_id": str(location) if location else None,
                "left": bool(member.get("deleted-at")),
            }
        )
    locations = await rest(ctx, "GET", f"{API}/locations")
    return {
        "team_members": rows,
        "locations": [
            {"location_id": str(row["id"]), "name": (row.get("attributes") or {}).get("name")}
            for row in locations.get("data") or []
            if not (row.get("attributes") or {}).get("deleted-at")
        ],
    }
