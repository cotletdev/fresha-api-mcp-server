"""Get appointment: gateway `viewAppointment`, `purchaseOrder` and `ListAppointmentNotes`."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from fresha_api_mcp.core.tools import tool
from fresha_api_mcp.fresha.client import gql, workspace
from fresha_api_mcp.fresha.tools._appointments import EXAMPLE_APPOINTMENT, appointment_row, view
from fresha_api_mcp.fresha.tools._shared import APPOINTMENT_ID, money, plain

if TYPE_CHECKING:
    from fresha_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {"appointment_id": APPOINTMENT_ID},
    "required": ["appointment_id"],
    "additionalProperties": False,
}

_EXTRA_QUERY = """query purchaseOrder($id: ID!, $appointmentId: ID!) {
  order: Checkout_order(id: $id, options: {usePricing: true}) { id totalAmount leftToPay }
  notes: Notes_notesByAppointment(appointmentId: $appointmentId, first: 20, includeClientNote: false) {
    edges { node { id body createdAt author { fullName } } }
  }
}"""

EXAMPLE_RESPONSE: dict[str, Any] = {
    **EXAMPLE_APPOINTMENT,
    "total": 22.0,
    "left_to_pay": 22.0,
    "currency": "GBP",
    "notes": [],
}


@tool(
    name="get_appointment",
    title="Get appointment",
    access="read",
    description="One appointment: client, services, team member, times, status, price and notes.",
    details=(
        "Reads the appointment as its drawer in the calendar shows it: status, start and end (wall clock "
        "in the business's time zone), the client, each booked service with its team member and length, "
        "the total and what is left to pay, and the appointment notes."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /appointments/{appointment_id}",
    example_response=EXAMPLE_RESPONSE,
)
async def get_appointment(ctx: ToolContext, args: dict[str, Any]) -> Any:
    ws = await workspace(ctx)
    found = await view(ctx, args["appointment_id"])
    row = appointment_row(found, ws.time_zone)
    order: dict[str, Any] = {}
    notes: list[dict[str, Any]] = []
    if found.get("purchaseOrderId"):
        data = await gql(
            ctx, "purchaseOrder", _EXTRA_QUERY, {"id": found["purchaseOrderId"], "appointmentId": found["id"]}
        )
        order = data.get("order") or {}
        notes = [edge.get("node") or {} for edge in (data.get("notes") or {}).get("edges") or []]
    return {
        **row,
        "total": money(order.get("totalAmount")),
        "left_to_pay": money(order.get("leftToPay")),
        "currency": ws.currency,
        "notes": [
            {
                "note_id": str(n["id"]),
                "text": plain(n.get("body")),
                "created_at": n.get("createdAt"),
                "author": (n.get("author") or {}).get("fullName"),
            }
            for n in notes
        ],
    }
