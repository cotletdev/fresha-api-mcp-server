"""Everything the server knows about Fresha outside `fresha/`: names, domains and the session cookie.

The rest of the package reads these values and never names the app itself.
"""

from __future__ import annotations

NAME = "Fresha"
SLUG = "fresha"
# The command and the prefix of every environment variable (FRESHA_AUTH_TOKEN, FRESHA_MCP_TOKEN ...).
CLI = "fresha-mcp"
ENV = "FRESHA"
# Requests may reach only these hosts and their subdomains. Their cookies are read from Chrome.
# The partner panel talks to partners-api, partners-api-gateway (GraphQL), customers-api, reports and a few
# more *.fresha.com hosts, all on the same session cookie.
DOMAINS = ("fresha.com",)
# Present only while signed in. The first is the cookie a pasted token sets. It alone signs the panel in.
SESSION_COOKIES = ("fresha_partners_session",)
COOKIE_DOMAIN = ".fresha.com"
LOGIN_URL = "https://partners.fresha.com/users/login"
# A final URL with one of these means the app signed the session out.
LOGGED_OUT_MARKERS = ("/users/login",)
# An answer with one of these asks you to sign in again before a sensitive action. Fresha has none.
RELOGIN_MARKERS: tuple[str, ...] = ()
# Paths a tool may only read: your Fresha user account, sign-in and sign-up, and billing.
# Any method but GET, HEAD or OPTIONS to one of them is refused before it leaves (core/account_guard.py).
ACCOUNT_PATHS = (
    r"^/user-account",
    r"^/users/",
    r"billing|subscription|payout|bank-account|payment-method",
)
# REST routes live under this path, the same as on cotlet.dev.
API_PREFIX = "/api/v1/fresha"
# Prepended to the MCP server's instructions: where an agent starts.
AGENT_START = (
    "Start with list_services and list_team_members: their ids are what find_available_slots, "
    "create_appointment and add_blocked_time take. list_clients gives the client_id for get_client, "
    "add_client_note and create_appointment, list_appointments the appointment_id for get_appointment, "
    "reschedule_appointment and cancel_appointment. Times are wall clock in the business's time zone."
)
