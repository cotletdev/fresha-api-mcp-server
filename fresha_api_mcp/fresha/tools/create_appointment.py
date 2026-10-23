"""Create appointment: gateway `createAppointmentByEmployee`."""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING, Any

from fresha_api_mcp.core.errors import ErrorCode, ToolError
from fresha_api_mcp.core.tools import tool
from fresha_api_mcp.fresha.client import gql, workspace
from fresha_api_mcp.fresha.tools._appointments import EXAMPLE_APPOINTMENT, appointment_row, view
from fresha_api_mcp.fresha.tools._shared import (
    CLIENT_ID,
    SERVICE_IDS,
    START_AT,
    TEAM_MEMBER_ID,
    default_team_member,
    nanoid,
    parse_start,
    pricing_levels,
    start_input,
)

if TYPE_CHECKING:
    from fresha_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "client_id": {**CLIENT_ID, "description": "Client from list_clients. Without it: a walk-in."},
        "start_at": START_AT,
        "service_ids": SERVICE_IDS,
        "team_member_id": {**TEAM_MEMBER_ID, "description": "Team member. Default: the first who takes bookings."},
    },
    "required": ["start_at", "service_ids"],
    "additionalProperties": False,
}

_MUTATION = """mutation createAppointmentByEmployee($input: AppointmentsManager_CreateAppointmentByEmployeeInput!) {
  AppointmentsManager_createAppointmentByEmployee(input: $input) {
    appointment { id } primaryBookingId warnings { message }
  }
}"""


async def check_create(ctx: ToolContext, args: dict[str, Any]) -> None:
    """Before approval: the time, the services and the team member must exist."""
    ws = await workspace(ctx)
    parse_start(args["start_at"], "start_at", ws.time_zone)
    await pricing_levels(ctx, args["service_ids"])
    await default_team_member(ctx, args.get("team_member_id"))


@tool(
    name="create_appointment",
    title="Create appointment",
    access="write",
    confirm=True,
    description="Book an appointment for a client: services, team member and start time.",
    details=(
        "Books the services one after another from start_at with one team member, as New appointment in "
        "the calendar does, at each service's catalogue price. Fresha may send the client a booking "
        "confirmation by their notification settings (get_client), so this can reach the client. Find free "
        "times with find_available_slots first: Fresha books over other appointments and returns its "
        "warnings. By default you confirm each call; you can switch that off for this tool."
    ),
    input_schema=INPUT_SCHEMA,
    route="POST /appointments",
    example_response={**EXAMPLE_APPOINTMENT, "warnings": []},
    check=check_create,
)
async def create_appointment(ctx: ToolContext, args: dict[str, Any]) -> Any:
    ws = await workspace(ctx)
    start = parse_start(args["start_at"], "start_at", ws.time_zone)
    levels = await pricing_levels(ctx, args["service_ids"])
    member = await default_team_member(ctx, args.get("team_member_id"))
    bookings, at = [], start
    for level in levels:
        bookings.append(
            {
                "employees": [{"id": member, "requested": bool(args.get("team_member_id"))}],
                "employeeGenderRequested": "NO_PREFERENCE",
                "servicePricingLevel": {"id": level["id"], "catalogPrice": level["price"]},
                "startDateAndTime": start_input(at, ws.time_zone),
                "timeSegments": [
                    {
                        "durationInSeconds": level["minutes"] * 60,
                        "isMainServicingTime": True,
                        "sortingId": 0,
                        "type": "SERVICING",
                    }
                ],
                "orderItemRef": nanoid(),
                "resources": [],
                "bookedServiceAddOns": [],
            }
        )
        at += timedelta(minutes=level["minutes"])
    appointment: dict[str, Any] = {"bookings": bookings, "locationId": ws.location_id, "priceModifiers": []}
    if args.get("client_id"):
        appointment["customerId"] = str(args["client_id"])
    variables = {
        "input": {
            "appointment": appointment,
            "appointmentProtection": {"appointmentProtectionAction": "DEFAULT_SETTINGS"},
            "metadata": {"idempotencyKey": nanoid(), "source": "new"},
        }
    }
    data = await gql(ctx, "createAppointmentByEmployee", _MUTATION, variables, mutation=True)
    result = data.get("AppointmentsManager_createAppointmentByEmployee") or {}
    appointment_id = (result.get("appointment") or {}).get("id")
    if not appointment_id:
        raise ToolError("Fresha did not return the new appointment.", ErrorCode.TARGET_ERROR)
    row = appointment_row(await view(ctx, appointment_id), ws.time_zone)
    return {**row, "warnings": [w.get("message") for w in result.get("warnings") or [] if w.get("message")]}
