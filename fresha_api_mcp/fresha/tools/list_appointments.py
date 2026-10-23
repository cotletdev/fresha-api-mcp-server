"""List appointments: the Sales > Appointments report, reports.fresha.com `appointments_list`.
One row per booked service: `id` is the booking, `reference_number.record_id` the appointment.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING, Any

from fresha_api_mcp.core.errors import ErrorCode, ToolError
from fresha_api_mcp.core.helpers import limit
from fresha_api_mcp.core.tools import tool
from fresha_api_mcp.fresha.client import cell, record_id, report, workspace
from fresha_api_mcp.fresha.tools._shared import (
    CLIENT_ID,
    CURSOR,
    LIMIT,
    TEAM_MEMBER_ID,
    offset_cursor,
    parse_day,
    team_members,
)

if TYPE_CHECKING:
    from fresha_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "from": {"type": "string", "format": "date", "description": "First day."},
        "to": {"type": "string", "format": "date", "description": "Last day. Default: same as from."},
        "status": {
            "type": "string",
            "description": "Only this status, as Fresha names it: booked, confirmed, arrived, started, "
            "completed, canceled, no-show. Default: all.",
        },
        "team_member_id": {**TEAM_MEMBER_ID, "description": "Only this team member's appointments."},
        "client_id": {**CLIENT_ID, "description": "Only this client's appointments."},
        "limit": LIMIT,
        "cursor": CURSOR,
    },
    "required": ["from"],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "time_zone": "Europe/London",
    "appointments": [
        {
            "appointment_id": "1332971918",
            "booking_id": "1800615079",
            "reference": "#C7CB66CE",
            "starts_at": "2026-10-27T14:30:00",
            "duration_minutes": 45,
            "client": {"client_id": "304928171", "name": "Emily Carter"},
            "service": "Skin Fade",
            "team_member": "Daniel Hughes",
            "price": 22.0,
            "status": "Booked",
            "channel": "Offline",
            "created_at": "2026-10-22T11:56:24+01:00",
        }
    ],
    "next_cursor": None,
}


def _status(value: Any) -> str:
    """`No show`, `no_show` -> `no-show`; the report spells it `Canceled`."""
    return str(value or "").strip().lower().replace("_", "-").replace(" ", "-").replace("cancelled", "canceled")


def _start(row: dict[str, Any]) -> str | None:
    """`scheduled_date` plus `time` (`2:30 pm`): wall clock in the business's zone."""
    day, clock = cell(row, "scheduled_date"), cell(row, "time")
    if not day or not clock:
        return day
    try:
        # A clock time only, no date and no zone: the report's own wall clock.
        at = datetime.strptime(clock.upper(), "%I:%M %p").time()  # noqa: DTZ007 - a time of day, not a moment
        return datetime.combine(date.fromisoformat(day), at).isoformat()
    except ValueError:
        return day


@tool(
    name="list_appointments",
    title="List appointments",
    access="read",
    description="Appointments in a date range, with client, service, team member, price and status.",
    details=(
        "Lists appointments as Sales > Appointments shows them, latest first: one row per booked service "
        "with its appointment id, reference, start (wall clock in the business's time zone), length, client, "
        "team member, price, status and channel (online or offline). Cancelled appointments are included "
        "with their status. Page with next_cursor. The report itself has no status, team member or client "
        "filter, so those three apply to the first 100 rows of the date range: for a busy range, narrow the "
        "dates."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /appointments",
    example_response=EXAMPLE_RESPONSE,
)
async def list_appointments(ctx: ToolContext, args: dict[str, Any]) -> Any:
    first = parse_day(args["from"], "from")
    last = parse_day(args["to"], "to") if args.get("to") else first
    if last < first:
        raise ToolError("to is before from.", ErrorCode.INVALID_INPUT)
    offset, size = offset_cursor(args.get("cursor")), limit(args, 50, 100)
    member_name = None
    if args.get("team_member_id"):
        names = {m["id"]: m.get("name") for m in await team_members(ctx, with_deleted=True)}
        member_name = names.get(str(args["team_member_id"]))
        if member_name is None:
            raise ToolError("No team member with that id: see list_team_members.", ErrorCode.INVALID_INPUT)
    filtered = bool(member_name or args.get("client_id") or args.get("status"))
    params = {
        "limit": 100 if filtered else size,
        "offset": 0 if filtered else offset,
        "sort-by": "scheduled-on",
        "sort-order": "desc",
        "date-from": first,
        "date-to": last,
        "use-appt-id": 1,
    }
    rows, total = await report(ctx, "appointments_list", params)
    status = _status(args.get("status"))
    picked = [
        row
        for row in rows
        if (not member_name or cell(row, "employee_name") == member_name)
        and (not args.get("client_id") or record_id(row, "customer_name") == str(args["client_id"]))
        and (not status or _status(cell(row, "status")) == status)
    ]
    if filtered:
        # The report has no such filters: rows are filtered here on its first 100 rows, then paged.
        more, picked = len(picked) > offset + size, picked[offset : offset + size]
    else:
        more = isinstance(total, int) and offset + len(rows) < total
    return {
        "time_zone": (await workspace(ctx)).time_zone,
        "appointments": [
            {
                "appointment_id": record_id(row, "reference_number"),
                "booking_id": str(cell(row, "id")) if cell(row, "id") is not None else None,
                "reference": cell(row, "reference_number"),
                "starts_at": _start(row),
                "duration_minutes": cell(row, "duration"),
                "client": {"client_id": record_id(row, "customer_name"), "name": cell(row, "customer_name")}
                if record_id(row, "customer_name")
                else None,
                "service": cell(row, "service_name"),
                "team_member": cell(row, "employee_name"),
                "price": cell(row, "price"),
                "status": cell(row, "status"),
                "channel": cell(row, "channel_variant"),
                "created_at": cell(row, "created_on"),
            }
            for row in picked
        ],
        "next_cursor": str(offset + size) if more else None,
    }
