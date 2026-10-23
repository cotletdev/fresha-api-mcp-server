"""Appointment shapes shared by the appointment tools (gateway `viewAppointment`).

An appointment holds one booking per service, each with its team member and time segments. `version` and the
bookings are what a reschedule sends back.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any

from fresha_api_mcp.core.errors import ErrorCode, ToolError
from fresha_api_mcp.fresha.client import gql
from fresha_api_mcp.fresha.tools._shared import wall_clock

if TYPE_CHECKING:
    from fresha_api_mcp.core.context import ToolContext

_VIEW_QUERY = """query viewAppointment($id: ID!) {
  appointment: Appointments_appointment(id: $id) {
    id version createdAt primaryBookingId customerId customer { id firstName lastName } locationId isOnline
    purchaseOrderId status statusLabel { id isCustom } startWallClock
    bookings { id serviceId service { id name } servicePricingLevelId startWallClock
      employees { id isRequested employee { id fullName } }
      bookingTimeSegments { durationInSeconds durationType isMainServicingTime sortingId } }
  }
}"""

EXAMPLE_APPOINTMENT: dict[str, Any] = {
    "appointment_id": "1332896493",
    "status": "UNCONFIRMED",
    "starts_at": "2026-10-23T10:00:00",
    "ends_at": "2026-10-23T10:45:00",
    "time_zone": "Europe/London",
    "client": {"client_id": "304928171", "name": "Emily Carter"},
    "location_id": "3231745",
    "online": False,
    "created_at": "2026-10-22T09:17:06Z",
    "bookings": [
        {
            "booking_id": "1800511195",
            "service_id": "25979626",
            "service": "Skin Fade",
            "pricing_level_id": "29838432",
            "starts_at": "2026-10-23T10:00:00",
            "duration_minutes": 45,
            "team_member": {"team_member_id": "5652945", "name": "Daniel Hughes"},
        }
    ],
}


async def view(ctx: ToolContext, appointment_id: str) -> dict[str, Any]:
    """The raw `Appointments_appointment`; `INVALID_INPUT` when Fresha has none with this id."""
    try:
        data = await gql(ctx, "viewAppointment", _VIEW_QUERY, {"id": str(appointment_id)})
    except ToolError:
        data = {}
    found = data.get("appointment")
    if not isinstance(found, dict) or not found.get("id"):
        raise ToolError("No appointment with that id: take one from list_appointments.", ErrorCode.INVALID_INPUT)
    return found


def booking_seconds(booking: dict[str, Any]) -> int:
    return sum(int(s.get("durationInSeconds") or 0) for s in booking.get("bookingTimeSegments") or [])


def appointment_row(found: dict[str, Any], time_zone: str) -> dict[str, Any]:
    bookings = found.get("bookings") or []
    ends: list[datetime] = []
    rows = []
    for booking in bookings:
        start = wall_clock(booking.get("startWallClock"))
        seconds = booking_seconds(booking)
        if start:
            ends.append(datetime.fromisoformat(start) + timedelta(seconds=seconds))
        employee = next(iter(booking.get("employees") or []), {}).get("employee") or {}
        rows.append(
            {
                "booking_id": str(booking["id"]),
                "service_id": str(booking.get("serviceId") or "") or None,
                "service": (booking.get("service") or {}).get("name"),
                "pricing_level_id": str(booking.get("servicePricingLevelId") or "") or None,
                "starts_at": start,
                "duration_minutes": seconds // 60,
                "team_member": {"team_member_id": str(employee["id"]), "name": employee.get("fullName")}
                if employee.get("id")
                else None,
            }
        )
    customer = found.get("customer") or {}
    name = f"{customer.get('firstName') or ''} {customer.get('lastName') or ''}".strip()
    return {
        "appointment_id": str(found["id"]),
        "status": found.get("status"),
        "starts_at": wall_clock(found.get("startWallClock")),
        "ends_at": max(ends).isoformat() if ends else None,
        "time_zone": time_zone,
        "client": {"client_id": str(customer["id"]), "name": name or None} if customer.get("id") else None,
        "location_id": str(found.get("locationId") or "") or None,
        "online": bool(found.get("isOnline")),
        "created_at": found.get("createdAt"),
        "bookings": rows,
    }
