"""List reviews: gateway `reviewsV2_allReviews`, cursor paged."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from fresha_api_mcp.core.helpers import limit
from fresha_api_mcp.core.tools import tool
from fresha_api_mcp.fresha.client import gql
from fresha_api_mcp.fresha.tools._shared import CURSOR, LIMIT

if TYPE_CHECKING:
    from fresha_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "ratings": {
            "type": "array",
            "items": {"type": "integer", "minimum": 1, "maximum": 5},
            "description": "Only these star ratings.",
        },
        "unreplied_only": {"type": "boolean", "description": "Only reviews without a reply. Default: false."},
        "source": {"type": "string", "enum": ["fresha", "google"], "description": "Only Fresha or Google reviews."},
        "search": {"type": "string", "description": "Words in the review."},
        "limit": LIMIT,
        "cursor": CURSOR,
    },
    "additionalProperties": False,
}

_QUERY = """query reviewsV2_allReviews($first: Int!, $after: String, $ratings: [Int!],
    $sources: [ReviewsV2_ReviewSource!], $status: ReviewsV2_ReviewReplyStatus, $searchTerm: String) {
  provider: ReviewsV2_provider {
    reviews: reviews(first: $first, after: $after, ratings: $ratings, sources: $sources, status: $status,
        searchTerm: $searchTerm) {
      pageInfo { hasNextPage endCursor }
      totalCount { value }
      edges { node { id appointmentId source locationId customerId rating { value } text createdAt publishedAt
        author { fullName } externalReviewerName
        replies(first: 2) { edges { node { id text createdAt displayAs publishedAt } } } } }
    }
  }
}"""

EXAMPLE_RESPONSE: dict[str, Any] = {
    "reviews": [
        {
            "review_id": "7120044",
            "rating": 5,
            "text": "Great fade, very friendly.",
            "source": "FRESHA",
            "author": "Emily Carter",
            "client_id": "304928171",
            "appointment_id": "1332971918",
            "location_id": "3231745",
            "created_at": "2026-10-28T16:02:11Z",
            "published_at": "2026-10-28T16:02:11Z",
            "replies": [{"reply_id": "88001", "text": "Thank you, Emily!", "as": "BUSINESS", "published_at": None}],
        }
    ],
    "total": 1,
    "next_cursor": None,
}


@tool(
    name="list_reviews",
    title="List reviews",
    access="read",
    description="Client reviews of the business with rating, text and replies.",
    details=(
        "Lists reviews as Online reputation shows them, newest first: star rating, text, author, the "
        "client and appointment it is about, source (Fresha or Google) and the replies. Filter by rating, "
        "source, words or reviews still without a reply. Page with next_cursor."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /reviews",
    example_response=EXAMPLE_RESPONSE,
)
async def list_reviews(ctx: ToolContext, args: dict[str, Any]) -> Any:
    variables: dict[str, Any] = {"first": limit(args, 20, 100), "after": args.get("cursor") or None}
    if args.get("ratings"):
        variables["ratings"] = args["ratings"]
    if args.get("source"):
        variables["sources"] = [args["source"].upper()]
    if args.get("unreplied_only"):
        variables["status"] = "NOT_REPLIED"
    if search := (args.get("search") or "").strip():
        variables["searchTerm"] = search
    data = await gql(ctx, "reviewsV2_allReviews", _QUERY, variables)
    found = (data.get("provider") or {}).get("reviews") or {}
    page = found.get("pageInfo") or {}
    nodes = [edge.get("node") or {} for edge in found.get("edges") or []]
    return {
        "reviews": [
            {
                "review_id": str(n["id"]),
                "rating": (n.get("rating") or {}).get("value"),
                "text": n.get("text"),
                "source": n.get("source"),
                "author": (n.get("author") or {}).get("fullName") or n.get("externalReviewerName"),
                "client_id": str(n["customerId"]) if n.get("customerId") else None,
                "appointment_id": str(n["appointmentId"]) if n.get("appointmentId") else None,
                "location_id": str(n["locationId"]) if n.get("locationId") else None,
                "created_at": n.get("createdAt"),
                "published_at": n.get("publishedAt"),
                "replies": [
                    {
                        "reply_id": str(r["id"]),
                        "text": r.get("text"),
                        "as": r.get("displayAs"),
                        "published_at": r.get("publishedAt"),
                    }
                    for r in (e.get("node") or {} for e in (n.get("replies") or {}).get("edges") or [])
                ],
            }
            for n in nodes
        ],
        "total": (found.get("totalCount") or {}).get("value"),
        "next_cursor": page.get("endCursor") if page.get("hasNextPage") else None,
    }
