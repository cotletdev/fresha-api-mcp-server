"""A tool is one async function, declared with @tool next to its schemas.

The declaration is the only source of a tool's shape: the REST API, the MCP server and the CLI are
all built from it.
"""

from __future__ import annotations

import re
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal

if TYPE_CHECKING:
    from fresha_api_mcp.core.context import ToolContext

ToolHandler = Callable[["ToolContext", dict[str, Any]], Awaitable[Any]]

# The REST route under app.API_PREFIX, e.g. "POST /groups/{group}/posts".
ROUTE = re.compile(r"^(GET|POST|PUT|PATCH|DELETE) (/(?:[a-z0-9-]+|\{[a-z][a-z0-9_]*\}))+$")

# The hosted service asks the owner to approve each call that reaches other people. Here your MCP client
# asks before each tool call instead, so those sentences are dropped from the published details.
_HOSTED_CONFIRM = re.compile(
    r"(,? ?so)?[,;]? ?[Bb]y default you confirm each [a-z]+[;,] ?(and )?you can switch that off for this tool\."
)


def _local_details(details: str | None) -> str | None:
    if details is None:
        return None
    text = _HOSTED_CONFIRM.sub(".", details).replace("..", ".").replace(" through Cotlet", "")
    return re.sub(r"\s+", " ", text).strip()


@dataclass(frozen=True)
class ToolSpec:
    name: str
    title: str
    access: Literal["read", "write"]
    description: str
    input_schema: dict[str, Any]
    handler: ToolHandler
    route: str | None = None
    details: str | None = None
    # Reaches other people (messages, posts, emails): MCP clients should ask before each call.
    confirm: bool = False
    credits: int = 25
    output_schema: dict[str, Any] | None = None
    example_response: dict[str, Any] | None = None
    needs_browser: bool = False
    timeout_s: int | None = None
    # Read-only check of the input against the app before a call that reaches people.
    check: ToolHandler | None = None


def check_route(name: str, route: str, input_schema: dict[str, Any]) -> None:
    """A route is a method and a path whose {placeholders} are required arguments of the tool."""
    if not ROUTE.match(route):
        raise ValueError(f"{name}: route must look like 'POST /groups/{{group}}/posts', got {route!r}")
    required = set(input_schema.get("required", []))
    for param in re.findall(r"\{(\w+)\}", route):
        if param not in required:
            raise ValueError(f"{name}: route parameter {{{param}}} must be a required argument")


def tool(
    *,
    name: str,
    title: str,
    access: Literal["read", "write"],
    description: str,
    input_schema: dict[str, Any],
    route: str | None = None,
    details: str | None = None,
    confirm: bool = False,
    credits: int = 25,
    output_schema: dict[str, Any] | None = None,
    example_response: dict[str, Any] | None = None,
    needs_browser: bool = False,
    timeout_s: int | None = None,
    check: ToolHandler | None = None,
) -> Callable[[ToolHandler], ToolSpec]:
    if route is not None:
        check_route(name, route, input_schema)

    def wrap(handler: ToolHandler) -> ToolSpec:
        return ToolSpec(
            name=name,
            title=title,
            access=access,
            description=description,
            input_schema=input_schema,
            handler=handler,
            route=route,
            details=_local_details(details),
            confirm=confirm,
            credits=credits,
            output_schema=output_schema,
            example_response=example_response,
            needs_browser=needs_browser,
            timeout_s=timeout_s,
            check=check,
        )

    return wrap
