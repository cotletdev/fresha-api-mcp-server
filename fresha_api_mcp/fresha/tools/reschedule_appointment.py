"""Reschedule appointment: gateway `updateAppointmentByEmployee`.

The panel sends the whole appointment back with its `version`, every booking moved by the same amount and the
time segments unchanged.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from fresha_api_mcp.core.errors import ErrorCode, ToolError
from fresha_api_mcp.core.tools import tool
from fresha_api_mcp.fresha.client import gql, workspace
from fresha_api_mcp.fresha.tools._appointments import EXAMPLE_APPOINTMENT, appointment_row, view
from fresha_api_mcp.fresha.tools._shared import (
    APPOINTMENT_ID,
    START_AT,
    TEAM_MEMBER_ID,
    default_team_member,
    nanoid,
    parse_start,
    services,
    start_input,
    wall_clock,
)

if TYPE_CHECKING:
    from fresha_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "appointment_id": APPOINTMENT_ID,
        "start_at": {**START_AT, "description": "New start." + START_AT["description"].removeprefix("Start,")},
        "team_member_id": {**TEAM_MEMBER_ID, "description": "New team member for every service. Default: unchanged."},
        "notify_client": {
            "type": "boolean",
            "description": "Let Fresha send the client a reschedule message, by their notification settings. "
            "Default: true.",
        },
    },
    "required": ["appointment_id", "start_at"],
    "additionalProperties": False,
}

_MUTATION = """mutation updateAppointmentByEmployee($input: AppointmentsManager_UpdateAppointmentByEmployeeInput!) {
  AppointmentsManager_updateAppointmentByEmployee(input: $input) {
    result {
      ... on AppointmentsManager_UpdateAppointmentByEmployeeSuccess { appointment { id } primaryBookingId }
      ... on AppointmentsManager_UpdateAppointmentByEmployeeAdditionalUserInputRequired {
        requiredInputs { code field message }
      }
    }
  }
}"""

_CLOSED = {"CANCELLED", "COMPLETED", "NO_SHOW"}


async def check_reschedule(ctx: ToolContext, args: dict[str, Any]) -> None:
    """Before approval: the appointment must exist and still be open, the time and team member valid."""
    ws = await workspace(ctx)
    parse_start(args["start_at"], "start_at", ws.time_zone)
    found = await view(ctx, args["appointment_id"])
    if found.get("status") in _CLOSED:
        raise ToolError(f"This appointment is {str(found['status']).lower()}.", ErrorCode.INVALID_INPUT)
    if args.get("team_member_id"):
        await default_team_member(ctx, args["team_member_id"])


@tool(
    name="reschedule_appointment",
    title="Reschedule appointment",
    access="write",
    confirm=True,
    description="Move an appointment to a new start time, optionally to another team member.",
    details=(
        "Moves every service of the appointment by the same amount so the first starts at start_at, as "
        "Reschedule in the appointment drawer does; lengths and prices stay. team_member_id moves all "
        "services to that team member. With notify_client (default true) Fresha sends the client a "
        "reschedule message by their notification settings; false moves it quietly. "
        "Cancelled, completed and no-show appointments are refused. By default you confirm each call; "
        "you can switch that off for this tool."
    ),
    input_schema=INPUT_SCHEMA,
    route="POST /appointments/{appointment_id}/reschedule",
    example_response=EXAMPLE_APPOINTMENT,
    check=check_reschedule,
)
async def reschedule_appointment(ctx: ToolContext, args: dict[str, Any]) -> Any:
    await check_reschedule(ctx, args)
    ws = await workspace(ctx)
    new_start = parse_start(args["start_at"], "start_at", ws.time_zone)
    found = await view(ctx, args["appointment_id"])
    old_start = wall_clock(found.get("startWallClock"))
    if not old_start:
        raise ToolError("Fresha did not give the appointment's start.", ErrorCode.TARGET_ERROR)
    shift = new_start - datetime.fromisoformat(old_start)
    prices = {
        str(level["id"]): str(level.get("price") or level.get("retailPrice") or "0")
        for service in await services(ctx)
        for level in service.get("servicePricingLevels") or []
    }
    bookings = []
    for booking in found.get("bookings") or []:
        start = wall_clock(booking.get("startWallClock")) or old_start
        employees = [
            {"id": str(args["team_member_id"]), "requested": True}
            if args.get("team_member_id")
            else {"id": str(e["id"]), "requested": bool(e.get("isRequested"))}
            for e in (booking.get("employees") or [])[:1]
        ]
        level = str(booking.get("servicePricingLevelId"))
        bookings.append(
            {
                "bookingId": str(booking["id"]),
                "employees": employees,
                "employeeGenderRequested": "NO_PREFERENCE",
                "servicePricingLevel": {"id": level, "catalogPrice": prices.get(level, "0")},
                "startDateAndTime": start_input(datetime.fromisoformat(start) + shift, ws.time_zone),
                "timeSegments": [
                    {
                        "durationInSeconds": int(s.get("durationInSeconds") or 0),
                        "isMainServicingTime": bool(s.get("isMainServicingTime")),
                        "sortingId": int(s.get("sortingId") or 0),
                        "type": s.get("durationType") or "SERVICING",
                    }
                    for s in booking.get("bookingTimeSegments") or []
                ],
                "orderItemRef": nanoid(),
                "resources": [],
                "bookedServiceAddOns": [],
            }
        )
    appointment: dict[str, Any] = {
        "bookings": bookings,
        "clientPurchaseOrderId": found.get("purchaseOrderId"),
        "priceModifiers": [],
        "previouslySelectedPriceModifiers": [],
        "version": found.get("version"),
    }
    if found.get("customerId"):
        appointment["customerId"] = str(found["customerId"])
    variables = {
        "input": {
            "appointmentId": str(found["id"]),
            "appointment": appointment,
            "appointmentProtection": {"appointmentProtectionAction": "NO_CHANGES"},
            "metadata": {"idempotencyKey": nanoid(), "primaryBookingId": found.get("primaryBookingId")},
            # Fresha asks for it (SHOULD_NOTIFY_CUSTOMER_REQUIRED) whenever the move would message the client.
            "additionalUserInput": {"shouldNotifyCustomer": args.get("notify_client", True)},
        }
    }
    data = await gql(ctx, "updateAppointmentByEmployee", _MUTATION, variables, mutation=True)
    result = (data.get("AppointmentsManager_updateAppointmentByEmployee") or {}).get("result") or {}
    if needed := result.get("requiredInputs"):
        messages = "; ".join(str(n.get("message") or n.get("code")) for n in needed)
        raise ToolError(f"Fresha needs more before this move: {messages}", ErrorCode.TARGET_ERROR)
    if not (result.get("appointment") or {}).get("id"):
        raise ToolError("Fresha did not confirm the move.", ErrorCode.TARGET_ERROR)
    return appointment_row(await view(ctx, found["id"]), ws.time_zone)
