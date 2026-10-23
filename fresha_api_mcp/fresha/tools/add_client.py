"""Add client: customers-api `POST /v2/customers`, JSON:API `customer-create-requests`."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from fresha_api_mcp.core.errors import ErrorCode, ToolError
from fresha_api_mcp.core.tools import tool
from fresha_api_mcp.fresha.client import CUSTOMERS, rest
from fresha_api_mcp.fresha.tools._clients import client_row

if TYPE_CHECKING:
    from fresha_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "first_name": {"type": "string", "minLength": 1, "maxLength": 100, "description": "First name."},
        "last_name": {"type": "string", "maxLength": 100, "description": "Last name."},
        "email": {"type": "string", "format": "email", "description": "Email."},
        "phone": {
            "type": "string",
            "pattern": r"^\+[1-9][0-9 ]{6,18}$",
            "description": "Mobile number with country code, e.g. +44 7700 900123.",
        },
        "gender": {"type": "string", "enum": ["female", "male", "non_binary", "other"], "description": "Gender."},
        "appointment_messages": {
            "type": "boolean",
            "description": "Let Fresha send this client booking confirmations and reminders by email, SMS and "
            "WhatsApp. Default: true.",
        },
        "marketing": {
            "type": "boolean",
            "description": "The client agreed to marketing messages. Default: false.",
        },
    },
    "required": ["first_name"],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "client_id": "305001122",
    "name": "Emily Carter",
    "email": None,
    "phone": None,
    "gender": None,
    "blocked": False,
    "created_at": "2026-10-22T11:02:41Z",
    "total_sales": None,
    "reviews_count": None,
    "average_rating": None,
}


@tool(
    name="add_client",
    title="Add client",
    access="write",
    description="Add a client to the business's client list.",
    details=(
        "Adds a client as Add client in the Client list does: name, email, mobile and gender. With "
        "appointment_messages (default true) Fresha sends the client booking confirmations and reminders to "
        "the email and mobile given; marketing (default false) records consent to marketing messages. "
        "Nothing is sent when the client is added."
    ),
    input_schema=INPUT_SCHEMA,
    route="POST /clients",
    example_response=EXAMPLE_RESPONSE,
)
async def add_client(ctx: ToolContext, args: dict[str, Any]) -> Any:
    first = args["first_name"].strip()
    if not first:
        raise ToolError("first_name is empty.", ErrorCode.INVALID_INPUT)
    messages, marketing = args.get("appointment_messages", True), bool(args.get("marketing"))
    attributes: dict[str, Any] = {
        "first-name": first,
        "last-name": (args.get("last_name") or "").strip(),
        "email": (args.get("email") or "").strip() or None,
        "contact-number": (args.get("phone") or "").replace(" ", "") or None,
        "gender": args.get("gender"),
        "enable-email-notifications": messages,
        "enable-sms-notifications": messages,
        "enable-whatsapp-notifications": messages,
        "accepts-marketing-notifications": marketing,
        "accepts-sms-marketing-notifications": marketing,
        "accepts-whatsapp-marketing-notifications": marketing,
        "marketplace-appointment-confirmation-enabled": False,
        "tag-ids": [],
        "tag-names": [],
        "creation-source": "client_list",
    }
    body = {
        "data": {
            "type": "customer-create-requests",
            "attributes": attributes,
            "relationships": {"addresses": {"data": []}},
        }
    }
    answer = await rest(ctx, "POST", f"{CUSTOMERS}/v2/customers", body=body)
    record = answer.get("data") or {}
    if not record.get("id"):
        raise ToolError("Fresha did not return the new client.", ErrorCode.TARGET_ERROR)
    return client_row(record)
