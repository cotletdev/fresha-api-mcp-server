"""The MCP server: one MCP tool per tool of the app, over stdio or streamable HTTP."""

from __future__ import annotations

import json
from typing import Any

from mcp import types
from mcp.server.lowlevel import Server

from fresha_api_mcp import __version__, app
from fresha_api_mcp.core.errors import ToolError
from fresha_api_mcp.runner import Runner, description, tools

INSTRUCTIONS = (
    f"{app.NAME} tools working in the user's own {app.NAME} account, through the session of their Chrome. "
    f"{app.AGENT_START} "
    "Tools that post, comment, message, invite or change settings act under the user's name and reach real "
    "people: say what you will send and get the user's OK first. Lists page with next_cursor."
)


def _annotations(spec: Any) -> types.ToolAnnotations:
    method = (spec.route or "GET").split(" ", 1)[0]
    return types.ToolAnnotations(
        title=spec.title,
        readOnlyHint=spec.access == "read",
        destructiveHint=spec.access == "write" and (method == "DELETE" or spec.confirm),
        idempotentHint=method in ("GET", "PUT"),
        openWorldHint=True,
    )


def build(runner: Runner) -> Server:
    server: Server = Server(app.SLUG, version=__version__, instructions=INSTRUCTIONS)

    @server.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            types.Tool(
                name=spec.name,
                title=spec.title,
                description=description(spec),
                inputSchema=spec.input_schema,
                annotations=_annotations(spec),
            )
            for spec in tools(runner.read_only)
        ]

    @server.call_tool(validate_input=False)
    async def call_tool(name: str, arguments: dict[str, Any]) -> list[types.TextContent]:
        try:
            result = await runner.run(name, arguments)
        except ToolError as exc:
            raise RuntimeError(f"{exc.code}: {exc}") from None
        return [types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]

    return server


async def run_stdio(runner: Runner) -> None:
    from mcp.server.stdio import stdio_server

    server = build(runner)
    async with stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())
