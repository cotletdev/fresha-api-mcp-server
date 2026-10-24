"""Self-hosted API and MCP server for one app (see app.py). Personal use only, see LICENSE.

From Python, without a server:

    from fresha_api_mcp import call
    clients = call("list_clients", search="smith")["clients"]
"""

from __future__ import annotations

import asyncio
from typing import Any

__version__ = "1.0.2"


def call(tool: str, args: dict[str, Any] | None = None, **kwargs: Any) -> Any:
    """Run one tool with the saved session and return its answer. Raises ToolError on failure."""
    from fresha_api_mcp.runner import Runner

    async def go() -> Any:
        runner = Runner()
        try:
            return await runner.run(tool, {**(args or {}), **kwargs})
        finally:
            await runner.close()

    return asyncio.run(go())
