"""Input and answer helpers the tools share."""

from __future__ import annotations

import json
from typing import Any

from fresha_api_mcp.core.errors import ErrorCode, ToolError


def page_cursor(cursor: str | None) -> int:
    """A page-number cursor: None is page 1, anything else must be a positive number we handed out."""
    if not cursor:
        return 1
    if not cursor.isdigit() or int(cursor) < 1:
        raise ToolError("cursor must be the next_cursor value from the previous call.", ErrorCode.INVALID_INPUT)
    return int(cursor)


def limit(args: dict[str, Any], default: int, maximum: int) -> int:
    """`limit` from the input, clamped to 1..maximum."""
    value = int(args.get("limit") or default)
    return max(1, min(value, maximum))


def json_field(value: Any) -> Any:
    """Apps keep some metadata as JSON strings: the parsed value, None when it does not parse."""
    if isinstance(value, str) and value[:1] in "{[":
        try:
            return json.loads(value)
        except ValueError:
            return None
    return value
