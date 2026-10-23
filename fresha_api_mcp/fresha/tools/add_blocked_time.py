"""Add blocked time: staff-working-hours-api GraphQL `createBlockedTime`."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from fresha_api_mcp.core.errors import ErrorCode, ToolError
from fresha_api_mcp.core.tools import tool
from fresha_api_mcp.fresha.client import WORKING_HOURS, gql, workspace
from fresha_api_mcp.fresha.tools._shared import START_AT, TEAM_MEMBER_ID, default_team_member, parse_start

if TYPE_CHECKING:
    from fresha_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "team_member_id": TEAM_MEMBER_ID,
        "start_at": START_AT,
        "end_at": {**START_AT, "description": "End on the same day. ISO 8601 like start_at."},
        "title": {"type": "string", "maxLength": 100, "description": "Reason shown on the calendar, e.g. Lunch."},
        "description": {"type": "string", "maxLength": 1000, "description": "Note your team sees on the block."},
        "allow_online_booking": {
            "type": "boolean",
            "description": "Clients may still book this time online. Default: false.",
        },
    },
    "required": ["team_member_id", "start_at", "end_at"],
    "additionalProperties": False,
}

_MUTATION = """mutation createBlockedTime($input: BlockedTimeInput!) {
  createBlockedTime(input: $input) { id }
}"""

EXAMPLE_RESPONSE: dict[str, Any] = {
    "blocked_time_id": "215697532",
    "team_member_id": "5652945",
    "date": "2026-10-28",
    "start_time": "13:00",
    "end_time": "14:00",
    "time_zone": "Europe/London",
    "title": "Lunch",
}


@tool(
    name="add_blocked_time",
    title="Add blocked time",
    access="write",
    description="Block a time slot in a team member's calendar so nobody books it.",
    details=(
        "Adds blocked time as Add > Blocked time in the calendar does: one block on one day for one team "
        "member, with a title and a note for the team. It does not repeat. Clients cannot book it online "
        "unless allow_online_booking is true. Nobody is told."
    ),
    input_schema=INPUT_SCHEMA,
    route="POST /blocked-times",
    example_response=EXAMPLE_RESPONSE,
)
async def add_blocked_time(ctx: ToolContext, args: dict[str, Any]) -> Any:
    ws = await workspace(ctx)
    start = parse_start(args["start_at"], "start_at", ws.time_zone)
    end = parse_start(args["end_at"], "end_at", ws.time_zone)
    if end.date() != start.date() or end <= start:
        raise ToolError("end_at must be later on the same day as start_at.", ErrorCode.INVALID_INPUT)
    member = await default_team_member(ctx, args["team_member_id"])
    day = start.date().isoformat()
    title = (args.get("title") or "").strip() or "Blocked time"
    variables = {
        "input": {
            "employeeId": member,
            "blockedTimeGroup": {"employeeIds": [member]},
            "locationId": ws.location_id,
            "startDate": day,
            "endDate": day,
            "startTime": start.strftime("%H:%M:%S"),
            "endTime": end.strftime("%H:%M:%S"),
            "title": title,
            "note": (args.get("description") or "").strip(),
            "allowOnlineBooking": bool(args.get("allow_online_booking")),
            "repeat": {"type": "NONE"},
        }
    }
    data = await gql(ctx, "createBlockedTime", _MUTATION, variables, host=WORKING_HOURS, mutation=True)
    created = data.get("createBlockedTime") or {}
    if not created.get("id"):
        raise ToolError("Fresha did not return the blocked time.", ErrorCode.TARGET_ERROR)
    return {
        "blocked_time_id": str(created["id"]),
        "team_member_id": member,
        "date": day,
        "start_time": start.strftime("%H:%M"),
        "end_time": end.strftime("%H:%M"),
        "time_zone": ws.time_zone,
        "title": title,
    }
