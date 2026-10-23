"""Reply to review: gateway `reviewsV2_createReply`.

Not sent yet: the dev account has no review. The input shape is checked against Fresha's schema.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from fresha_api_mcp.core.errors import ErrorCode, ToolError
from fresha_api_mcp.core.tools import tool
from fresha_api_mcp.fresha.client import gql

if TYPE_CHECKING:
    from fresha_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "review_id": {"type": "string", "pattern": "^[0-9A-Za-z-]+$", "description": "Review id from list_reviews."},
        "text": {"type": "string", "minLength": 1, "maxLength": 2000, "description": "Reply text."},
        "reply_as": {
            "type": "string",
            "enum": ["business", "team_member"],
            "description": "Sign the reply as the business (default) or as the team member signed in.",
        },
    },
    "required": ["review_id", "text"],
    "additionalProperties": False,
}

_MUTATION = """mutation reviewsV2_createReply($input: ReviewsV2_CreateReplyInput!) {
  createReply: ReviewsV2_providerCreateReply(input: $input) {
    reply { id text createdAt displayAs publishedAt visibleFor }
  }
}"""

EXAMPLE_RESPONSE: dict[str, Any] = {
    "reply_id": "88001",
    "review_id": "7120044",
    "text": "Thank you, Emily!",
    "as": "BUSINESS",
    "created_at": "2026-10-28T17:00:00Z",
    "published_at": "2026-10-28T17:00:00Z",
}


@tool(
    name="reply_to_review",
    title="Reply to review",
    access="write",
    confirm=True,
    description="Post a public reply to a client's review.",
    details=(
        "Posts a reply under the review as Reply in Online reputation does, signed as the business or the "
        "team member. The reply is public on the business's Fresha page and the client is told, so this "
        "reaches people. It needs a review that exists: take review_id from list_reviews. By default you "
        "confirm each call; you can switch that off for this tool."
    ),
    input_schema=INPUT_SCHEMA,
    route="POST /reviews/{review_id}/replies",
    example_response=EXAMPLE_RESPONSE,
)
async def reply_to_review(ctx: ToolContext, args: dict[str, Any]) -> Any:
    text = args["text"].strip()
    if not text:
        raise ToolError("text is empty.", ErrorCode.INVALID_INPUT)
    display = "EMPLOYEE" if args.get("reply_as") == "team_member" else "BUSINESS"
    variables = {
        "input": {
            "reviewId": str(args["review_id"]),
            "text": text,
            "displayAs": display,
            "visibleFor": "MARKETPLACE",
            "shouldPublish": True,
        }
    }
    data = await gql(ctx, "reviewsV2_createReply", _MUTATION, variables, mutation=True)
    reply = (data.get("createReply") or {}).get("reply") or {}
    if not reply.get("id"):
        raise ToolError("Fresha did not return the reply.", ErrorCode.TARGET_ERROR)
    return {
        "reply_id": str(reply["id"]),
        "review_id": str(args["review_id"]),
        "text": reply.get("text"),
        "as": reply.get("displayAs"),
        "created_at": reply.get("createdAt"),
        "published_at": reply.get("publishedAt"),
    }
