"""Fresha partner panel API, recorded on the dev account (22.10.2026).

The session is the `fresha_partners_session` cookie alone: no identity headers, no csrf. Every call carries the
workspace id as `__pid` (from `GET partners-api /session`), `_client_platform=web` and a `_client_version` (old
builds still answer). The areas live on different hosts:

- `partners-api-gateway` GraphQL: appointments, slots, notes, catalogue, reviews. Introspection is off, so the
  queries are short ones on the panel's root fields. Errors come back HTTP 200 with `errors[]`.
- `partners-api` and `customers-api` JSON:API: workspace, locations, team, clients.
- `reports.fresha.com` report tables (`included[].attributes.rows[].cells`), `partners-reporting-api` GraphQL
  (sales summary), `staff-working-hours-api` GraphQL (blocked time).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from fresha_api_mcp.core.errors import AuthExpiredError, ErrorCode, ToolError

if TYPE_CHECKING:
    from fresha_api_mcp.core.context import ToolContext

WEB = "https://partners.fresha.com"
API = "https://partners-api.fresha.com"
CUSTOMERS = "https://customers-api.fresha.com"
GATEWAY = "https://partners-api-gateway.fresha.com/graphql"
REPORTS = "https://reports.fresha.com/api/reports"
REPORTING = "https://partners-reporting-api.fresha.com/"
WORKING_HOURS = "https://staff-working-hours-api.fresha.com/graphql"
# Panel build seen on 22.10.2026; Fresha answers older builds as well.
CLIENT_VERSION = "2.8.12293"
JSON_API = {"accept": "application/vnd.api+json", "content-type": "application/vnd.api+json"}
_PAGE = {"origin": WEB, "referer": f"{WEB}/"}
_WORKSPACE_TTL_S = 24 * 3600


@dataclass(frozen=True)
class Workspace:
    id: str
    location_id: str
    time_zone: str
    currency: str


def _query(workspace_id: str, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    return {**(extra or {}), "__pid": workspace_id, "_client_version": CLIENT_VERSION, "_client_platform": "web"}


def _refused(what: str, body: Any, status: int) -> ToolError:
    """Fresha's own message (JSON:API `errors[].detail` or GraphQL `errors[].message`), never a stack."""
    errors = body.get("errors") if isinstance(body, dict) else None
    first = errors[0] if isinstance(errors, list) and errors and isinstance(errors[0], dict) else {}
    message = first.get("detail") or first.get("title") or first.get("message") or f"HTTP {status}"
    return ToolError(f"Fresha refused {what}: {str(message)[:200]}", ErrorCode.TARGET_ERROR)


async def workspace(ctx: ToolContext) -> Workspace:
    """The account's workspace, its first location, time zone and currency; cached a day per browser."""
    key = f"workspace:{ctx.profile.browser_id}"
    if cached := await ctx.cache_get(key):
        return Workspace(**json.loads(cached))
    session = await ctx.get_json(f"{API}/session", headers=_PAGE)
    workspaces = session.get("accessible_workspaces") if isinstance(session, dict) else None
    if not workspaces:
        raise AuthExpiredError("The app signed this account out. Sign in again in Chrome, then run connect.")
    pid = str(workspaces[0])
    provider = await rest(ctx, "GET", f"{API}/provider", pid=pid)
    locations = await rest(ctx, "GET", f"{API}/locations", pid=pid)
    attributes = (provider.get("data") or {}).get("attributes") or {}
    rows = [row for row in locations.get("data") or [] if not (row.get("attributes") or {}).get("deleted-at")]
    if not rows:
        raise ToolError("This Fresha workspace has no location.", ErrorCode.TARGET_ERROR)
    found = Workspace(
        id=pid,
        location_id=str(rows[0]["id"]),
        time_zone=str(attributes.get("time-zone") or "Europe/London"),
        currency=str(attributes.get("currency-code") or "GBP"),
    )
    await ctx.cache_set(key, json.dumps(found.__dict__), _WORKSPACE_TTL_S)
    return found


async def rest(
    ctx: ToolContext,
    method: str,
    url: str,
    *,
    params: dict[str, Any] | None = None,
    body: Any = None,
    pid: str | None = None,
) -> dict[str, Any]:
    """One JSON:API or report call; returns the parsed answer. `pid` skips the workspace lookup."""
    pid = pid or (await workspace(ctx)).id
    response = await ctx.call(
        method,
        url,
        params=_query(pid, params),
        data=None if body is None else json.dumps(body),
        headers={**_PAGE, **JSON_API},
    )
    answer = response.json() if response.text.strip() else {}
    if response.status not in (200, 201):
        raise _refused(f"{method} {url.split('?')[0].split('.com', 1)[-1]}", answer, response.status)
    return answer if isinstance(answer, dict) else {"data": answer}


async def gql(
    ctx: ToolContext,
    operation: str,
    query: str,
    variables: dict[str, Any],
    *,
    host: str = GATEWAY,
    mutation: bool = False,
) -> dict[str, Any]:
    """One GraphQL operation; returns `data`. Any `errors[]` raises with Fresha's first message."""
    pid = (await workspace(ctx)).id
    extra = {"_mutation" if mutation else "_query": operation} if host == GATEWAY else None
    response = await ctx.call(
        "POST",
        host,
        params=_query(pid, extra),
        json={"operationName": operation, "query": query, "variables": variables},
        headers={**_PAGE, "accept": "application/json"},
    )
    answer = response.json()
    if response.status != 200 or not isinstance(answer, dict) or answer.get("errors"):
        raise _refused(operation, answer, response.status)
    return answer.get("data") or {}


async def report(ctx: ToolContext, name: str, params: dict[str, Any]) -> tuple[list[dict[str, Any]], int | None]:
    """A reports.fresha.com table as rows of `{column: cell}` (cells keep `value` and `record_id`), and the total."""
    answer = await rest(ctx, "GET", f"{REPORTS}/{name}", params=params)
    tables = [t for t in answer.get("included") or [] if t.get("type") == "report-tables"]
    if not tables:
        return [], 0
    attributes = tables[0].get("attributes") or {}
    rows = [row.get("cells") or {} for row in attributes.get("rows") or []]
    return rows, attributes.get("total-rows-count")


def cell(row: dict[str, Any], column: str) -> Any:
    return (row.get(column) or {}).get("value")


def record_id(row: dict[str, Any], column: str) -> str | None:
    found = (row.get(column) or {}).get("record_id")
    return str(found) if found is not None else None


async def request_headers(ctx: ToolContext) -> dict[str, str]:
    """`docker/prod-run ... request`: Fresha needs no identity headers, only the page's origin."""
    del ctx
    return dict(_PAGE)
