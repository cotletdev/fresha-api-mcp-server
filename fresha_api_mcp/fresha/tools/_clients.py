"""Client shapes shared by the client tools (customers-api JSON:API)."""

from __future__ import annotations

from typing import Any

EXAMPLE_CLIENT: dict[str, Any] = {
    "client_id": "304906224",
    "name": "Jane Doe",
    "email": "jane@example.com",
    "phone": "+44 7700 900456",
    "gender": "female",
    "blocked": False,
    "created_at": "2026-10-22T09:17:05Z",
    "total_sales": 0.0,
    "reviews_count": 0,
    "average_rating": 0.0,
}


def client_row(row: dict[str, Any]) -> dict[str, Any]:
    """A `customer-search-results-v2` or `customers-v2` record."""
    a = row.get("attributes") or {}
    name = a.get("name") or f"{a.get('first-name') or ''} {a.get('last-name') or ''}".strip()
    return {
        "client_id": str(row["id"]),
        "name": name or None,
        "email": a.get("email") or None,
        "phone": a.get("contact-number") or None,
        "gender": a.get("gender"),
        "blocked": bool(a.get("blocked")),
        "created_at": a.get("created-at"),
        "total_sales": a.get("total-sales-amount"),
        "reviews_count": a.get("reviews-count"),
        "average_rating": a.get("average-rating"),
    }
