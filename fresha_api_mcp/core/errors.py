"""Error codes a tool call can end with, and the exceptions tools raise to produce them.

The REST API answers with the code in `error` and the HTTP status from `HTTP_STATUS`; the MCP server
returns the same code and message as a tool error.
"""

from __future__ import annotations

from enum import StrEnum


class ErrorCode(StrEnum):
    # No session for this server yet, or the app signed it out: run `<cli> connect` again.
    AUTH_REQUIRED = "auth_required"
    AUTH_EXPIRED = "auth_expired"
    CAPTCHA_REQUIRED = "captcha_required"
    MFA_REQUIRED = "mfa_required"
    # The tool changes something and the server runs with --read-only.
    SCOPE_DENIED = "scope_denied"
    # The account in the app lacks the role (not a group admin, not the author).
    APP_PERMISSION_DENIED = "app_permission_denied"
    TARGET_BLOCKED = "target_blocked"
    UNKNOWN_TOOL = "unknown_tool"
    INVALID_INPUT = "invalid_input"
    NOT_BUILT = "not_built"
    TARGET_ERROR = "target_error"
    RATE_LIMITED = "rate_limited"
    TIMEOUT = "timeout"
    INTERNAL_ERROR = "internal_error"


HTTP_STATUS: dict[ErrorCode, int] = {
    ErrorCode.AUTH_REQUIRED: 401,
    ErrorCode.AUTH_EXPIRED: 401,
    ErrorCode.CAPTCHA_REQUIRED: 409,
    ErrorCode.MFA_REQUIRED: 409,
    ErrorCode.SCOPE_DENIED: 403,
    ErrorCode.APP_PERMISSION_DENIED: 403,
    ErrorCode.TARGET_BLOCKED: 403,
    ErrorCode.UNKNOWN_TOOL: 404,
    ErrorCode.INVALID_INPUT: 422,
    ErrorCode.NOT_BUILT: 501,
    ErrorCode.TARGET_ERROR: 502,
    ErrorCode.RATE_LIMITED: 429,
    ErrorCode.TIMEOUT: 504,
    ErrorCode.INTERNAL_ERROR: 500,
}


class ToolError(Exception):
    """Raised by a tool or the core; the REST API and the MCP server turn it into an error answer."""

    code: ErrorCode = ErrorCode.TARGET_ERROR

    def __init__(self, message: str, code: ErrorCode | None = None) -> None:
        super().__init__(message)
        if code is not None:
            self.code = code


class AuthExpiredError(ToolError):
    code = ErrorCode.AUTH_EXPIRED


class CaptchaRequiredError(ToolError):
    code = ErrorCode.CAPTCHA_REQUIRED


class MfaRequiredError(ToolError):
    code = ErrorCode.MFA_REQUIRED


class TargetBlockedError(ToolError):
    code = ErrorCode.TARGET_BLOCKED


class NotBuiltError(ToolError):
    code = ErrorCode.NOT_BUILT
