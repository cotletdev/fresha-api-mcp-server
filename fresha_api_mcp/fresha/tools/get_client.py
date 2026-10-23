"""Get client: customers-api `/v2/customers/{id}`, partners-api `/customers/{id}/statistics` and the gateway's
`Appointments_appointments` and `Notes_notes`."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from fresha_api_mcp.core.tools import tool
from fresha_api_mcp.fresha.client import API, CUSTOMERS, gql, rest
from fresha_api_mcp.fresha.tools._clients import EXAMPLE_CLIENT, client_row
from fresha_api_mcp.fresha.tools._shared import CLIENT_ID, plain, wall_clock

if TYPE_CHECKING:
    from fresha_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {"client_id": CLIENT_ID},
    "required": ["client_id"],
    "additionalProperties": False,
}

_DETAILS_QUERY = """query CustomerUpcomingAppointmentQuery($customerId: ID!) {
  appointments: Appointments_appointments(first: 10, customerId: $customerId, onlyFuture: true,
      order: {field: START_DATETIME, direction: ASC}) {
    edges { node { id status startWallClock bookings { id service { name } employee { firstName lastName } } } }
  }
  notes: Notes_notes(customerId: $customerId, first: 10, sort: ACTIVITY_DATE, includeClientNote: true) {
    edges { node { id body type createdAt author { fullName } } }
  }
}"""

_STATS = {
    "bookings": "bookings-count",
    "completed": "completed-bookings-count",
    "cancelled": "cancelled-bookings-count",
    "no_shows": "no-show-bookings-count",
}

EXAMPLE_RESPONSE: dict[str, Any] = {
    **EXAMPLE_CLIENT,
    "first_name": "Jane",
    "last_name": "Doe",
    "birthday": None,
    "notifications": {"email": False, "sms": False, "whatsapp": False},
    "marketing": {"email": False, "sms": False, "whatsapp": False},
    "stats": {"bookings": 1, "completed": 0, "cancelled": 0, "no_shows": 0, "total_sales": 0.0, "outstanding": 0.0},
    "upcoming_appointments": [
        {
            "appointment_id": "1332896497",
            "status": "UNCONFIRMED",
            "starts_at": "2026-10-22T12:00:00",
            "services": ["Blow Dry"],
            "team_members": ["Daniel Hughes"],
        }
    ],
    "notes": [
        {
            "note_id": "01a1633f-4e7a-7be8-a7d3-4fd1eccd012d",
            "text": "Prefers mornings.",
            "created_at": "2026-10-22T10:01:00Z",
            "author": "Daniel Hughes",
        }
    ],
}


def _name(person: dict[str, Any]) -> str:
    return f"{person.get('firstName') or ''} {person.get('lastName') or ''}".strip()


def _birthday(a: dict[str, Any]) -> str | None:
    day, month, year = a.get("birthday-day"), a.get("birthday-month"), a.get("birthday-year")
    if not (day and month):
        return None
    return f"{year:04d}-{month:02d}-{day:02d}" if year else f"--{month:02d}-{day:02d}"


@tool(
    name="get_client",
    title="Get client",
    access="read",
    description="One client: contact, notification settings, booking stats, upcoming appointments, notes.",
    details=(
        "Reads the client profile as the client's page shows it: name, email, mobile, gender, birthday, "
        "whether Fresha sends them appointment messages and marketing by email, SMS and WhatsApp, booking "
        "and sales totals, the next 10 appointments and the latest 10 notes."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /clients/{client_id}",
    example_response=EXAMPLE_RESPONSE,
)
async def get_client(ctx: ToolContext, args: dict[str, Any]) -> Any:
    client_id = str(args["client_id"])
    record = (await rest(ctx, "GET", f"{CUSTOMERS}/v2/customers/{client_id}")).get("data") or {}
    stats = ((await rest(ctx, "GET", f"{API}/customers/{client_id}/statistics")).get("data") or {}).get(
        "attributes"
    ) or {}
    data = await gql(ctx, "CustomerUpcomingAppointmentQuery", _DETAILS_QUERY, {"customerId": client_id})
    a = record.get("attributes") or {}
    upcoming = [edge.get("node") or {} for edge in (data.get("appointments") or {}).get("edges") or []]
    notes = [edge.get("node") or {} for edge in (data.get("notes") or {}).get("edges") or []]
    return {
        **client_row(record),
        "first_name": a.get("first-name"),
        "last_name": a.get("last-name") or None,
        "birthday": _birthday(a),
        "notifications": {
            "email": bool(a.get("enable-email-notifications")),
            "sms": bool(a.get("enable-sms-notifications")),
            "whatsapp": bool(a.get("enable-whatsapp-notifications")),
        },
        "marketing": {
            "email": bool(a.get("accepts-marketing-notifications")),
            "sms": bool(a.get("accepts-sms-marketing-notifications")),
            "whatsapp": bool(a.get("accepts-whatsapp-marketing-notifications")),
        },
        "stats": {
            **{key: stats.get(field) for key, field in _STATS.items()},
            "total_sales": stats.get("total-sales"),
            "outstanding": stats.get("outstanding-sales"),
        },
        "upcoming_appointments": [
            {
                "appointment_id": str(node["id"]),
                "status": node.get("status"),
                "starts_at": wall_clock(node.get("startWallClock")),
                "services": [(b.get("service") or {}).get("name") for b in node.get("bookings") or []],
                "team_members": [_name(b["employee"]) for b in node.get("bookings") or [] if b.get("employee")],
            }
            for node in upcoming
        ],
        "notes": [
            {
                "note_id": str(node["id"]),
                "text": plain(node.get("body")),
                "created_at": node.get("createdAt"),
                "author": (node.get("author") or {}).get("fullName"),
            }
            for node in notes
        ],
    }
