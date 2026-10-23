"""All tools of the app in one registry, and the one way to call them: validate, run, map errors.

The REST API, the MCP server, the CLI and `fresha_api_mcp.call()` all go through `Runner.run`.
"""

from __future__ import annotations

import asyncio
import importlib
import pkgutil
from typing import Any

import jsonschema

from fresha_api_mcp import app
from fresha_api_mcp import session as sessions
from fresha_api_mcp.core.context import ToolContext
from fresha_api_mcp.core.errors import ErrorCode, ToolError
from fresha_api_mcp.core.tools import ToolSpec
from fresha_api_mcp.fresha import tools as tools_package

_TOOLS: dict[str, ToolSpec] | None = None


def all_tools() -> dict[str, ToolSpec]:
    """Every tool in the app's tools/ package, by name, in file order."""
    global _TOOLS
    if _TOOLS is None:
        found: dict[str, ToolSpec] = {}
        for module_info in sorted(pkgutil.iter_modules(tools_package.__path__), key=lambda m: m.name):
            module = importlib.import_module(f"{tools_package.__name__}.{module_info.name}")
            for value in vars(module).values():
                if isinstance(value, ToolSpec) and value.route:
                    found[value.name] = value
        _TOOLS = found
    return _TOOLS


def tools(read_only: bool = False) -> list[ToolSpec]:
    return [spec for spec in all_tools().values() if not read_only or spec.access == "read"]


def description(spec: ToolSpec) -> str:
    """What an agent reads: the one-liner, then the details."""
    return f"{spec.description}\n\n{spec.details}" if spec.details else spec.description


class Runner:
    """One session for the life of the process; reconnects to Chrome once when the app signs it out."""

    def __init__(self, read_only: bool = False) -> None:
        self.read_only = read_only
        self._ctx: ToolContext | None = None
        self._lock = asyncio.Lock()

    def _context(self) -> ToolContext:
        if self._ctx is None:
            session = sessions.load()
            if not session.signed_in:
                raise ToolError(
                    f"No {app.NAME} session yet. Sign in to {app.NAME} in Chrome, then run: {app.CLI} connect",
                    ErrorCode.AUTH_REQUIRED,
                )
            self._ctx = ToolContext(session=session)
        return self._ctx

    async def run(self, name: str, args: dict[str, Any] | None = None) -> Any:
        spec = all_tools().get(name)
        if spec is None:
            raise ToolError(f"No tool '{name}'. List them with: {app.CLI} tools", ErrorCode.UNKNOWN_TOOL)
        if self.read_only and spec.access != "read":
            raise ToolError(f"{name} changes {app.NAME} and this server runs read-only.", ErrorCode.SCOPE_DENIED)
        args = {k: v for k, v in (args or {}).items() if v is not None}
        try:
            jsonschema.validate(args, spec.input_schema)
        except jsonschema.ValidationError as exc:
            where = ".".join(str(p) for p in exc.absolute_path)
            raise ToolError(f"{where + ': ' if where else ''}{exc.message}", ErrorCode.INVALID_INPUT) from None
        ctx = self._context()
        try:
            return await asyncio.wait_for(spec.handler(ctx, args), timeout=spec.timeout_s or 120)
        except TimeoutError:
            raise ToolError(f"{app.NAME} took too long to answer.", ErrorCode.TIMEOUT) from None
        except ToolError as exc:
            if exc.code is not ErrorCode.AUTH_EXPIRED or not await self._reconnect():
                raise
            # The app signed the old cookies out: read them again from Chrome and try once more.
            return await spec.handler(self._context(), args)

    async def _reconnect(self) -> bool:
        async with self._lock:
            old = self._context()
            try:
                fresh = await asyncio.to_thread(sessions.refresh, old.session)
            except ToolError:
                return False
            if fresh is None or fresh.cookies == old.session.cookies:
                return False
            await old.close()
            self._ctx = ToolContext(session=fresh)
            return True

    async def close(self) -> None:
        if self._ctx is not None:
            await self._ctx.close()
            self._ctx = None
