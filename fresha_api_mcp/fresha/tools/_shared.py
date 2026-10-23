"""Inputs, times and lookups the Fresha tools share (recorded 22.10.2026).

Ids are numeric strings. Appointment times are wall clock in the workspace's time zone: Fresha answers
`2026-10-22T10:00:00[Europe/London]`, the tools give `2026-10-22T10:00:00` next to `time_zone`. Durations on
services are minutes, on bookings seconds.
"""

from __future__ import annotations

import json
import secrets
import string
from datetime import date, datetime, timedelta
from typing import TYPE_CHECKING, Any
from zoneinfo import ZoneInfo

from fresha_api_mcp.core.errors import ErrorCode, ToolError
from fresha_api_mcp.fresha.client import API, gql, rest, workspace

if TYPE_CHECKING:
    from fresha_api_mcp.core.context import ToolContext

ID = {"type": "string", "pattern": "^[0-9]+$"}
APPOINTMENT_ID: dict[str, Any] = {**ID, "description": "Appointment id from list_appointments."}
CLIENT_ID: dict[str, Any] = {**ID, "description": "Client id from list_clients."}
TEAM_MEMBER_ID: dict[str, Any] = {**ID, "description": "Team member id from list_team_members."}
SERVICE_IDS: dict[str, Any] = {
    "type": "array",
    "items": {**ID},
    "minItems": 1,
    "maxItems": 5,
    "description": "Service ids from list_services, done one after another in this order.",
}
START_AT: dict[str, Any] = {
    "type": "string",
    "description": "Start, ISO 8601: 2026-11-03T14:30 is wall clock in the business's time zone; with an "
    "offset (2026-11-03T14:30:00+01:00) it is converted.",
}
LIMIT: dict[str, Any] = {"type": "integer", "minimum": 1, "maximum": 100, "description": "Page size. Default: 50."}
CURSOR: dict[str, Any] = {"type": "string", "description": "next_cursor from the previous call."}

_KEY_CHARS = string.ascii_letters + string.digits

_SERVICES_QUERY = """query services_getCatalogItems($first: Int!, $locationIds: [ID!]) {
  catalogItems: Partners_catalogItems(first: $first, withArchived: false, locationIds: $locationIds,
      filterEmployeeAssignment: true) {
    edges { node { id service { id name description onlineBookingEnabled archivedAt
      servicePricingLevels { id name duration price retailPrice retailPriceType } }
      serviceGroup { id name } } }
  }
}"""


def nanoid() -> str:
    """The panel's 21-character ids for `orderItemRef` and `idempotencyKey`."""
    return "".join(secrets.choice(_KEY_CHARS) for _ in range(21))


def parse_day(value: str, field: str) -> str:
    try:
        return date.fromisoformat(value.strip()).isoformat()
    except ValueError:
        raise ToolError(f"{field} is a date like 2026-11-03.", ErrorCode.INVALID_INPUT) from None


def parse_start(value: str, field: str, time_zone: str) -> datetime:
    """Wall clock in the business's zone (naive); an offset is converted to it."""
    try:
        moment = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        raise ToolError(f"{field} is a time like 2026-11-03T14:30.", ErrorCode.INVALID_INPUT) from None
    if moment.tzinfo is not None:
        moment = moment.astimezone(ZoneInfo(time_zone)).replace(tzinfo=None)
    if moment.minute % 5 or moment.second:
        raise ToolError(f"{field} must be on a 5-minute mark, like 14:30 or 14:35.", ErrorCode.INVALID_INPUT)
    return moment


def wall_clock(value: str | None) -> str | None:
    """`2026-10-22T10:00:00[Europe/London]` -> `2026-10-22T10:00:00`."""
    return value.split("[", 1)[0] if value else None


def start_input(moment: datetime, time_zone: str) -> dict[str, Any]:
    """`startDateAndTime` of a booking."""
    return {
        "date": moment.date().isoformat(),
        "timeOfDay": {"hours": moment.hour, "minutes": moment.minute, "seconds": 0},
        "timezone": time_zone,
        "wallClockTime": moment.strftime("%H:%M:%S"),
    }


def offset_cursor(cursor: str | None) -> int:
    if not cursor:
        return 0
    if not cursor.isdigit():
        raise ToolError("cursor must be the next_cursor value from the previous call.", ErrorCode.INVALID_INPUT)
    return int(cursor)


def money(value: Any) -> float | None:
    try:
        return float(value) if value not in (None, "") else None
    except (TypeError, ValueError):
        return None


async def services(ctx: ToolContext) -> list[dict[str, Any]]:
    """Active services of the workspace's location, each with its pricing levels."""
    ws = await workspace(ctx)
    data = await gql(ctx, "services_getCatalogItems", _SERVICES_QUERY, {"first": 500, "locationIds": [ws.location_id]})
    edges = (data.get("catalogItems") or {}).get("edges") or []
    nodes = [edge.get("node") or {} for edge in edges]
    return [
        {**node["service"], "group": node.get("serviceGroup") or {}}
        for node in nodes
        if node.get("service") and not node["service"].get("archivedAt")
    ]


async def pricing_levels(ctx: ToolContext, service_ids: list[str]) -> list[dict[str, Any]]:
    """The first pricing level of each service, in the order given: `{service_id, name, id, price, minutes}`."""
    by_id = {str(service["id"]): service for service in await services(ctx)}
    levels: list[dict[str, Any]] = []
    for service_id in service_ids:
        service = by_id.get(str(service_id))
        if service is None or not service.get("servicePricingLevels"):
            raise ToolError(f"No active service {service_id}: take ids from list_services.", ErrorCode.INVALID_INPUT)
        level = service["servicePricingLevels"][0]
        levels.append(
            {
                "service_id": str(service["id"]),
                "name": service.get("name"),
                "id": str(level["id"]),
                "price": str(level.get("price") or level.get("retailPrice") or "0"),
                "minutes": int(level.get("duration") or 0),
            }
        )
    return levels


async def team_members(ctx: ToolContext, *, with_deleted: bool = False) -> list[dict[str, Any]]:
    answer = await rest(ctx, "GET", f"{API}/v2/employees", params={"with-deleted": "true" if with_deleted else "false"})
    return [
        {"id": str(row["id"]), **(row.get("attributes") or {}), "links": row.get("relationships") or {}}
        for row in answer.get("data") or []
        if with_deleted or not (row.get("attributes") or {}).get("deleted-at")
    ]


async def default_team_member(ctx: ToolContext, team_member_id: str | None) -> str:
    """The given team member when they take bookings, else the first who does."""
    members = [m for m in await team_members(ctx) if m.get("provides-services")]
    if team_member_id:
        if not any(m["id"] == str(team_member_id) for m in members):
            raise ToolError("No bookable team member with that id: see list_team_members.", ErrorCode.INVALID_INPUT)
        return str(team_member_id)
    if not members:
        raise ToolError("Nobody on the team takes bookings.", ErrorCode.TARGET_ERROR)
    return members[0]["id"]


def lexical(text: str) -> str:
    """A plain note as the Lexical editor state Fresha stores (one paragraph per line)."""
    paragraphs = [
        {
            "children": [{"detail": 0, "format": 0, "mode": "normal", "style": "", "text": line, "type": "text"}]
            if line
            else [],
            "direction": "ltr",
            "format": "",
            "indent": 0,
            "type": "paragraph",
            "version": 1,
        }
        for line in text.split("\n")
    ]
    root = {"children": paragraphs, "direction": "ltr", "format": "", "indent": 0, "type": "root", "version": 1}
    return json.dumps({"root": root})


def plain(body: Any) -> str | None:
    """Text of a Lexical note body (a JSON string or object); the raw value when it is not Lexical."""
    state = body
    if isinstance(body, str):
        try:
            state = json.loads(body)
        except ValueError:
            return body
    if not isinstance(state, dict):
        return str(body) if body is not None else None
    return "\n".join(
        "".join(str(child.get("text") or "") for child in paragraph.get("children") or [])
        for paragraph in (state.get("root") or {}).get("children") or []
    )


def end_of(start: datetime, minutes: int) -> str:
    return (start + timedelta(minutes=minutes)).isoformat()
