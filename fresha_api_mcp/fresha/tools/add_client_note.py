"""Add client note: gateway `notes_createNote` with a client scope."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from fresha_api_mcp.core.errors import ErrorCode, ToolError
from fresha_api_mcp.core.tools import tool
from fresha_api_mcp.fresha.client import gql
from fresha_api_mcp.fresha.tools._shared import CLIENT_ID, lexical, plain

if TYPE_CHECKING:
    from fresha_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "client_id": CLIENT_ID,
        "text": {"type": "string", "minLength": 1, "maxLength": 5000, "description": "Note text."},
    },
    "required": ["client_id", "text"],
    "additionalProperties": False,
}

_MUTATION = """mutation notes_createNote($input: Notes_CreateNoteInput!) {
  Notes_createNote(input: $input) { note { id body type createdAt author { fullName } } }
}"""

EXAMPLE_RESPONSE: dict[str, Any] = {
    "note_id": "01a1633f-4e7a-7be8-a7d3-4fd1eccd012d",
    "client_id": "305001122",
    "text": "Prefers mornings.",
    "created_at": "2026-10-22T10:01:00Z",
    "author": "Daniel Hughes",
}


@tool(
    name="add_client_note",
    title="Add client note",
    access="write",
    description="Add a note to a client's profile, seen by the team only.",
    details=(
        "Adds a note to the client's Notes tab for all locations, as the profile's Add note does. Only "
        "the team sees it; the client is not told. Line breaks become paragraphs."
    ),
    input_schema=INPUT_SCHEMA,
    route="POST /clients/{client_id}/notes",
    example_response=EXAMPLE_RESPONSE,
)
async def add_client_note(ctx: ToolContext, args: dict[str, Any]) -> Any:
    text = args["text"].strip()
    if not text:
        raise ToolError("text is empty.", ErrorCode.INVALID_INPUT)
    client_id = str(args["client_id"])
    variables = {
        "input": {
            "body": lexical(text),
            "scope": {"client": {"customerId": client_id, "allLocations": True}},
            "attachmentIds": [],
        }
    }
    data = await gql(ctx, "notes_createNote", _MUTATION, variables, mutation=True)
    note = (data.get("Notes_createNote") or {}).get("note") or {}
    if not note.get("id"):
        raise ToolError("Fresha did not return the new note.", ErrorCode.TARGET_ERROR)
    return {
        "note_id": str(note["id"]),
        "client_id": client_id,
        "text": plain(note.get("body")),
        "created_at": note.get("createdAt"),
        "author": (note.get("author") or {}).get("fullName"),
    }
