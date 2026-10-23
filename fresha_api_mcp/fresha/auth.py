"""Who is signed in: Fresha's own user profile (partners-api /user-account/profile), for "Signed in as ..."."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fresha_api_mcp.core.errors import AuthExpiredError, ErrorCode, ToolError

if TYPE_CHECKING:
    from fresha_api_mcp.core.context import ToolContext

API = "https://partners-api.fresha.com"
WEB = "https://partners.fresha.com"


async def whoami(ctx: ToolContext) -> str | None:
    """None only when Fresha says signed out; any other failure raises (detection tries again later)."""
    try:
        response = await ctx.call(
            "GET",
            f"{API}/user-account/profile",
            headers={"accept": "application/vnd.api+json", "referer": f"{WEB}/", "origin": WEB},
        )
    except AuthExpiredError:
        return None
    if response.status != 200:
        raise ToolError(f"Fresha answered {response.status} to who am I.", ErrorCode.TARGET_ERROR)
    me = (response.json().get("data") or {}).get("attributes") or {}
    name = f"{me.get('first-name') or ''} {me.get('last-name') or ''}".strip()
    email = me.get("email")
    return f"{name} ({email})" if name and email else name or email or None
