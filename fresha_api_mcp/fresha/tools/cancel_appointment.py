"""Cancel appointment: gateway `initializeAppointmentProtectionEnforcement`, then `cancelAppointmentWithNoCharge`.
The first call is what the cancel dialog sends to work out a fee; an appointment
with a fee or deposit is refused here."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from fresha_api_mcp.core.errors import ErrorCode, ToolError
from fresha_api_mcp.core.tools import tool
from fresha_api_mcp.fresha.client import API, gql, rest
from fresha_api_mcp.fresha.tools._appointments import view
from fresha_api_mcp.fresha.tools._shared import APPOINTMENT_ID, money

if TYPE_CHECKING:
    from fresha_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "appointment_id": APPOINTMENT_ID,
        "reason": {
            "type": "string",
            "description": "Name of one of the business's cancellation reasons, e.g. Client not available. "
            "Default: none.",
        },
        "notify_client": {
            "type": "boolean",
            "description": "Send the client a cancellation message. Default: true.",
        },
        "scope": {
            "type": "string",
            "enum": ["this_appointment", "whole_series"],
            "description": "this_appointment (default) or whole_series, for repeating appointments: this and "
            "every later one.",
        },
    },
    "required": ["appointment_id"],
    "additionalProperties": False,
}

_ENFORCEMENT = """mutation initializeAppointmentProtectionEnforcement(
    $input: AppointmentProtection_InitializeAppointmentProtectionEnforcementInput!) {
  enforcement: AppointmentProtection_initializeAppointmentProtectionEnforcement(input: $input) {
    appointmentProtectionEnforcement { protectionAmount hasPrepayment }
  }
}"""

_CANCEL = """mutation cancelAppointmentWithNoCharge($input: AppointmentProtection_CancelAppointmentWithNoChargeInput!) {
  cancel: AppointmentProtection_cancelAppointmentWithNoCharge(input: $input) { appointmentId }
}"""

EXAMPLE_RESPONSE: dict[str, Any] = {
    "appointment_id": "1332971918",
    "status": "CANCELLED",
    "reason": "Client not available",
    "client_notified": False,
}


async def _reason_id(ctx: ToolContext, reason: str | None) -> str | None:
    if not reason:
        return None
    answer = await rest(ctx, "GET", f"{API}/cancellation-reasons")
    names = {str((r.get("attributes") or {}).get("name") or "").lower(): str(r["id"]) for r in answer.get("data") or []}
    found = names.get(reason.strip().lower())
    if found is None:
        listed = ", ".join(sorted(n for n in names if n)) or "none"
        raise ToolError(f"No cancellation reason {reason!r}. The business has: {listed}.", ErrorCode.INVALID_INPUT)
    return found


async def check_cancel(ctx: ToolContext, args: dict[str, Any]) -> None:
    """Before approval: the appointment must exist and not be closed; the reason must exist."""
    found = await view(ctx, args["appointment_id"])
    if found.get("status") in {"CANCELLED", "COMPLETED", "NO_SHOW"}:
        raise ToolError(f"This appointment is {str(found['status']).lower()}.", ErrorCode.INVALID_INPUT)
    await _reason_id(ctx, args.get("reason"))


@tool(
    name="cancel_appointment",
    title="Cancel appointment",
    access="write",
    confirm=True,
    description="Cancel an appointment without a charge, optionally telling the client.",
    details=(
        "Cancels the appointment as Cancel in its drawer does, with one of the business's cancellation "
        "reasons. With notify_client (default true) Fresha sends the client a cancellation message, so this "
        "can reach the client; false cancels quietly. whole_series also cancels the later appointments of a "
        "repeating series. An appointment with a cancellation fee or a paid deposit is refused: cancel it in "
        "Fresha. It cannot be undone here. By default you confirm each call; you can switch that off for "
        "this tool."
    ),
    input_schema=INPUT_SCHEMA,
    route="POST /appointments/{appointment_id}/cancel",
    example_response=EXAMPLE_RESPONSE,
    check=check_cancel,
)
async def cancel_appointment(ctx: ToolContext, args: dict[str, Any]) -> Any:
    await check_cancel(ctx, args)
    appointment_id = str(args["appointment_id"])
    reason = await _reason_id(ctx, args.get("reason"))
    try:
        data = await gql(
            ctx,
            "initializeAppointmentProtectionEnforcement",
            _ENFORCEMENT,
            {"input": {"action": "CANCELLATION", "appointmentId": appointment_id}},
            mutation=True,
        )
    except ToolError as exc:
        # An appointment without a cancellation policy answers the error "No fee": nothing to charge.
        if "No fee" not in str(exc):
            raise
        data = {}
    enforcement = (data.get("enforcement") or {}).get("appointmentProtectionEnforcement") or {}
    if (money(enforcement.get("protectionAmount")) or 0) > 0 or enforcement.get("hasPrepayment"):
        raise ToolError(
            "This appointment has a cancellation fee or a deposit: cancel it in Fresha.", ErrorCode.INVALID_INPUT
        )
    notify = args.get("notify_client", True)
    options: dict[str, Any] = {"cancelFutureAppointments": args.get("scope") == "whole_series"}
    if reason:
        options["cancellationReasonId"] = reason
    await gql(
        ctx,
        "cancelAppointmentWithNoCharge",
        _CANCEL,
        {"input": {"appointmentId": appointment_id, "cancellationOptions": options, "sendNotification": notify}},
        mutation=True,
    )
    after = await view(ctx, appointment_id)
    return {
        "appointment_id": appointment_id,
        "status": after.get("status"),
        "reason": args.get("reason") if reason else None,
        "client_notified": bool(notify),
    }
