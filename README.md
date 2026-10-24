# Fresha API and MCP server, self-hosted

A **Fresha API** and a **Fresha MCP server** you run on your own computer, in Python, on the session of your own Google Chrome. All 17 Fresha tools we run in production at [Cotlet](https://cotlet.dev/integrations/fresha-api-mcp-server): appointments, free slots, booking, rescheduling and cancelling, blocked time, clients and client notes, services and team, the Sales summary and Sales list reports, and reviews with replies.

Fresha has no public API and no official MCP server. Its only data connection is the paid Data Connector add-on, which copies your data out to a Snowflake database and cannot book anything. This repo gives you:

- **MCP server** for Claude Code, Claude Desktop, Cursor, Codex and any MCP client, over stdio or HTTP. [Setup](#mcp-server)
- **REST API** on `http://127.0.0.1:8787/api/v1/fresha`, with OpenAPI docs at `/docs`. [Setup](#rest-api)
- **Python**: `call("list_appointments", {"from": "2026-10-27", "to": "2026-10-27"})`, plus 9 ready scripts in [`examples/`](examples/).

It is for technical people who want to run it themselves, **for noncommercial use only** ([license](#license)). If you want it running 24/7 on a server, kept working when Fresha changes its panel, for a team or a business, use the [hosted version at cotlet.dev](https://cotlet.dev/integrations/fresha-api-mcp-server).

[![Fresha MCP server](https://img.shields.io/badge/Fresha%20MCP-17%20tools-6d4aef)](#all-17-tools)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-141318)](#requirements)
[![License: PolyForm Noncommercial 1.0.0](https://img.shields.io/badge/license-PolyForm%20Noncommercial-141318)](LICENSE)
[![MCP Badge](https://lobehub.com/badge/mcp/cotletdev-fresha-api-mcp-server)](https://lobehub.com/mcp/cotletdev-fresha-api-mcp-server)

```bash
git clone https://github.com/cotletdev/fresha-api-mcp-server.git && cd fresha-api-mcp-server
python3 -m venv .venv && . .venv/bin/activate && pip install -e .
fresha-mcp connect                                 # reads your Fresha session from Chrome
fresha-mcp call list_services
claude mcp add fresha -- "$PWD/.venv/bin/fresha-mcp" mcp
```

## Contents

- [How it works](#how-it-works)
- [Requirements](#requirements)
- [Install](#install)
- [Connect your Chrome](#connect-your-chrome)
- [MCP server](#mcp-server)
- [REST API](#rest-api)
- [Python and the example scripts](#python-and-the-example-scripts)
- [All 17 tools](#all-17-tools)
- [Configuration](#configuration)
- [Security and your Fresha account](#security-and-your-fresha-account)
- [Errors](#errors)
- [Self-hosted or hosted](#self-hosted-or-hosted)
- [FAQ](#faq)
- [License](#license)

## How it works

```text
AI agent (MCP) / script (REST, Python) ──▶ fresha-mcp on your computer ──your cookies──▶ *.fresha.com
                                                  ▲
                         fresha-mcp connect ──────┘ reads them once from your Chrome (DevTools Protocol)
```

1. You sign in to Fresha for business in your own Chrome at [partners.fresha.com](https://partners.fresha.com/users/login), the way you always do: an email code, then a text message code. Tick **Trust this device**.
2. `fresha-mcp connect` attaches to that Chrome through the Chrome DevTools Protocol, reads the fresha.com cookies and saves them to `~/.config/fresha-api-mcp/session.json`, readable by your user only. It never sees or stores your password or the codes.
3. Every tool call is a request to the APIs the Fresha partner panel itself calls (`partners-api`, the `partners-api-gateway` GraphQL, `customers-api`, `reports.fresha.com` and a few more `*.fresha.com` hosts) with those cookies, sent with [curl_cffi](https://github.com/lexiforest/curl_cffi), which copies Chrome's TLS fingerprint. No headless browser runs.

The session lives in one cookie, `fresha_partners_session`. Fresha keeps it for 25 days and renews it while you use the panel or the tools. When Fresha signs you out, the server reads the cookies from Chrome again, if Chrome is open with remote debugging on.

## Requirements

- Python 3.11 or newer.
- Google Chrome 144 or newer, signed in to partners.fresha.com. Any Chrome or Chromium works with a [debugging port](#option-b-a-chrome-with-a-debugging-port).
- macOS, Linux or Windows.
- A Fresha for business account. We build and test with the workspace owner. A team member login sees what Fresha shows that team member, and the two sales tools need its reporting permissions.

## Install

```bash
git clone https://github.com/cotletdev/fresha-api-mcp-server.git
cd fresha-api-mcp-server
python3 -m venv .venv
. .venv/bin/activate              # Windows: .venv\Scripts\activate
pip install -e .
fresha-mcp --version
```

With [uv](https://docs.astral.sh/uv/): `uv venv && uv pip install -e .`, then `uv run fresha-mcp ...`.

Setting it up with an AI agent (Claude Code, Codex, Cursor)? Open it in this folder and ask it to set up the repo: [`AGENTS.md`](AGENTS.md) tells it every step, and it asks you only for the steps in Chrome.

To update: `git pull && pip install -e .`. We copy every change of the hosted Fresha tools into this repo.

## Connect your Chrome

### Option A: your everyday Chrome (recommended)

1. Open `chrome://inspect/#remote-debugging` in Chrome and switch **remote debugging** on. Chrome then accepts DevTools connections from programs on this computer, and asks you before each one.
2. Make sure you are signed in at [partners.fresha.com](https://partners.fresha.com/users/login).
3. Run:

   ```bash
   fresha-mcp connect
   ```

4. Chrome asks whether to allow the connection. Click **Allow**.

```text
Saved 24 Fresha cookies to /Users/you/.config/fresha-api-mcp/session.json
Signed in to Fresha as Daniel Hughes (daniel@example.com)
```

You can switch remote debugging off again afterwards. Leave it on if you want the server to pick up a new session by itself after Fresha signs you out.

`connect` looks for Chrome's `DevToolsActivePort` file in the default profile folder. For Chrome Beta, Canary or a custom profile folder, pass `--profile-dir "<folder>"`.

### Option B: a Chrome with a debugging port

Chrome does not open a debugging port on your default profile, so start a separate one, sign in to Fresha there once, and connect to it:

```bash
# macOS
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --remote-debugging-port=9222 --user-data-dir="$HOME/.chrome-fresha"
# Linux
google-chrome --remote-debugging-port=9222 --user-data-dir="$HOME/.chrome-fresha"
# Windows
"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="%USERPROFILE%\.chrome-fresha"

fresha-mcp connect --cdp http://127.0.0.1:9222
```

`--cdp` also takes a `ws://` DevTools URL, for example of a Chrome on another machine reached over an SSH tunnel.

### Option C: paste the cookie by hand

For a server with no Chrome: in Chrome open DevTools on partners.fresha.com, **Application > Cookies > https://partners.fresha.com**, copy the value of `fresha_partners_session`, then:

```bash
fresha-mcp connect --token          # paste it, input is hidden
# or, without a session file:
export FRESHA_AUTH_TOKEN=...
```

A pasted cookie is not read again from Chrome. Paste a new one when Fresha signs you out.

Check the session at any time:

```bash
fresha-mcp status
```

## MCP server

The MCP server lists every tool with its input schema, a description written for agents, and hints. Read tools are marked read-only, and the tools that can reach clients (booking, rescheduling, cancelling, review replies) are marked so your client asks before running them.

### Claude Code

```bash
claude mcp add fresha -- /path/to/fresha-api-mcp-server/.venv/bin/fresha-mcp mcp
# read only:
claude mcp add fresha -- /path/to/fresha-api-mcp-server/.venv/bin/fresha-mcp mcp --read-only
```

### Claude Desktop

`~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "fresha": {
      "command": "/path/to/fresha-api-mcp-server/.venv/bin/fresha-mcp",
      "args": ["mcp"]
    }
  }
}
```

### Cursor

`~/.cursor/mcp.json`, the same block as Claude Desktop. A ready copy is in [`mcp.json`](mcp.json).

### Codex

`~/.codex/config.toml`:

```toml
[mcp_servers.fresha]
command = "/path/to/fresha-api-mcp-server/.venv/bin/fresha-mcp"
args = ["mcp"]
```

### Over HTTP

`fresha-mcp serve` also serves MCP over streamable HTTP at `http://127.0.0.1:8787/mcp`, for clients that take a URL:

```bash
fresha-mcp serve
claude mcp add --transport http fresha http://127.0.0.1:8787/mcp
```

Then ask your agent things like:

> *Anna Smith emailed asking for a cut and colour with Sam on Friday afternoon. Find her, check the free times for both services and book the first one after my OK.*
>
> *Sam is sick tomorrow. Block his day and show me which of his clients a colleague can take at the same time.*
>
> *Yesterday's sales by sale type against the same day last week. Flag refunds over £50.*
>
> *List the reviews without a reply and draft a short answer to each.*

## REST API

```bash
fresha-mcp serve                   # http://127.0.0.1:8787, MCP at /mcp, docs at /docs
```

Each tool has its own route under `/api/v1/fresha`, the same paths as the hosted API at cotlet.dev, so code written against one works with the other. Path parts and the query string are arguments, and a JSON body adds the rest.

```bash
curl 'http://127.0.0.1:8787/api/v1/fresha/services'
curl 'http://127.0.0.1:8787/api/v1/fresha/appointments?from=2026-10-27&to=2026-10-31'
curl 'http://127.0.0.1:8787/api/v1/fresha/sales-summary?from=2026-10-01&to=2026-10-31'
curl -X POST http://127.0.0.1:8787/api/v1/fresha/blocked-times \
  -H 'Content-Type: application/json' \
  -d '{"team_member_id": "5652945", "start_at": "2026-11-03T13:00", "end_at": "2026-11-03T14:00", "title": "Lunch"}'
```

Any tool by name, body as its arguments:

```bash
curl -X POST http://127.0.0.1:8787/api/v1/fresha/tools/list_clients -d '{"search": "smith"}'
```

- `GET /api/v1/fresha/tools`: every tool with its route, input schema and an example answer.
- `GET /docs`: interactive OpenAPI docs, `GET /openapi.json` the schema, for n8n, Postman or a generated client.
- Answers are JSON. List tools return `next_cursor`; pass it back as `cursor` for the next page.

The server listens on `127.0.0.1` only. To reach it from another device of yours, set a token, and every request then needs `Authorization: Bearer <token>`:

```bash
FRESHA_MCP_TOKEN=$(openssl rand -hex 24) fresha-mcp serve --host 0.0.0.0
```

## Python and the example scripts

Straight from Python, no server needed:

```python
from fresha_api_mcp import call
from fresha_api_mcp.scripting import paginate, write_rows

services = call("list_services")["services"]
day = call("list_appointments", {"from": "2026-10-27", "to": "2026-10-27"})["appointments"]
clients = list(paginate("list_clients", {"sort": "name"}, "clients"))
write_rows(clients, "clients.csv")
call("add_blocked_time", team_member_id="5652945", start_at="2026-11-03T13:00", end_at="2026-11-03T14:00")
```

Or one tool from the shell: `fresha-mcp call find_available_slots service_ids='["25979401"]' date=2026-10-27 days=3`, or with a JSON object. An ID stays text where the tool takes text.

Times are wall clock in the business's time zone. `2026-11-03T14:30` means 14:30 at the salon. A time with an offset is converted to it, and answers carry `time_zone`.

Ready scripts in [`examples/`](examples/). Each prints JSON or a short list, takes `--out file.csv` or `--out file.json` where it makes sense, and `--help`:

| Script | What it does |
|---|---|
| [`tomorrows_appointments.py`](examples/tomorrows_appointments.py) | Tomorrow's appointments grouped by team member. `--date`, `--all` for cancelled ones too. |
| [`book_from_message.py`](examples/book_from_message.py) | Matches a client by name, email or phone, finds free starts for several services in a time window, and with `--book` books the first after you confirm. |
| [`team_member_out.py`](examples/team_member_out.py) | A team member is out: blocks their hours and moves each client to a colleague free at the same time. Prints the plan; `--apply` asks before each change. |
| [`cancel_day.py`](examples/cancel_day.py) | Cancels a team member's appointments on a day with your cancellation reason. Lists them; `--apply` asks before each one. |
| [`daily_sales.py`](examples/daily_sales.py) | One day's Sales summary by sale type against the same weekday a week earlier, refunds over a limit flagged. |
| [`lapsed_clients.py`](examples/lapsed_clients.py) | Clients with no appointment for N days and nothing booked, with their marketing consent. `--email-consent-only`. |
| [`export_clients.py`](examples/export_clients.py) | Every client to CSV or JSON. `--search`, `--sort`. |
| [`export_sales.py`](examples/export_sales.py) | The Sales list for a date range to CSV or JSON. |
| [`unanswered_reviews.py`](examples/unanswered_reviews.py) | Reviews without a reply, lowest rating first; `--reply-to` posts a reply. |

```bash
python examples/tomorrows_appointments.py
python examples/team_member_out.py --team-member-id 5652945 --date 2026-10-30 --block 09:00-18:00
python examples/lapsed_clients.py --days 90 --out lapsed.csv
```

On a schedule, cron on your own computer works while it is on: `0 8 * * * cd ~/fresha-api-mcp-server && .venv/bin/python examples/daily_sales.py`.

## All 17 tools

IDs come from the list tools: `service_id` from `list_services`, `team_member_id` from `list_team_members`, `client_id` from `list_clients`, `appointment_id` from `list_appointments`, `review_id` from `list_reviews`. `fresha-mcp tools` prints this list, `fresha-mcp tools --json` adds the input schemas.

### Appointments

| Tool | Access | REST route | What it does |
|---|---|---|---|
| `list_appointments` | read | `GET /appointments` | Appointments in a date range, with client, service, team member, price and status. |
| `get_appointment` | read | `GET /appointments/{appointment_id}` | One appointment: client, services, team member, times, status, price and notes. |
| `find_available_slots` | read | `GET /available-slots` | Free start times for one or more services with a team member, day by day. |
| `create_appointment` | write | `POST /appointments` | Book an appointment for a client: services, team member and start time. |
| `reschedule_appointment` | write | `POST /appointments/{appointment_id}/reschedule` | Move an appointment to a new start time, optionally to another team member. |
| `cancel_appointment` | write | `POST /appointments/{appointment_id}/cancel` | Cancel an appointment without a charge, optionally telling the client. |
| `add_blocked_time` | write | `POST /blocked-times` | Block a time slot in a team member's calendar so nobody books it. |

### Clients

| Tool | Access | REST route | What it does |
|---|---|---|---|
| `list_clients` | read | `GET /clients` | Clients of the business, searchable by name, email or phone. |
| `get_client` | read | `GET /clients/{client_id}` | One client: contact, notification settings, booking stats, upcoming appointments, notes. |
| `add_client` | write | `POST /clients` | Add a client to the business's client list. |
| `add_client_note` | write | `POST /clients/{client_id}/notes` | Add a note to a client's profile, seen by the team only. |

### Catalogue and team

| Tool | Access | REST route | What it does |
|---|---|---|---|
| `list_services` | read | `GET /services` | Services of the business with category, duration and price. |
| `list_team_members` | read | `GET /team-members` | Team members with role, contact, services they do and whether they take bookings. |

### Sales

| Tool | Access | REST route | What it does |
|---|---|---|---|
| `get_sales_summary` | read | `GET /sales-summary` | Sales summary for a period: sales, refunds, discounts, taxes and payments by type. |
| `list_sales` | read | `GET /sales` | Sales (invoices) in a date range: number, date, client, status and totals. |

### Reviews

| Tool | Access | REST route | What it does |
|---|---|---|---|
| `list_reviews` | read | `GET /reviews` | Client reviews of the business with rating, text and replies. |
| `reply_to_review` | write | `POST /reviews/{review_id}/replies` | Post a public reply to a client's review. |

`create_appointment` lets Fresha send its booking confirmation by the client's notification settings; the tool has no switch for it. `reschedule_appointment` and `cancel_appointment` tell the client unless you pass `notify_client: false`. A review reply is public and the reviewer is told. Adding a client, a note or blocked time sends nothing. In `list_appointments` the status, team member and client filters apply to the first 100 rows of the date range, so narrow the dates for a busy salon.

Not in this version: payouts and the wallet (Fresha Payments), checkout and refunds, products, gift cards, memberships, the waitlist, marketing campaigns and shifts. `create_appointment` takes no appointment note, `add_blocked_time` blocks one day with no repeats, and `cancel_appointment` refuses an appointment with a cancellation fee or a paid deposit.

Never built, on purpose: your Fresha sign-in, email, password and user account, and anything that moves money (subscription, billing, payouts, payment methods). Every request passes a guard that refuses any change to those Fresha paths.

## Configuration

| Variable | Default | What it does |
|---|---|---|
| `FRESHA_MCP_HOME` | `~/.config/fresha-api-mcp` | Folder of `session.json`. |
| `FRESHA_AUTH_TOKEN` | | The `fresha_partners_session` cookie value, used instead of `session.json`. |
| `FRESHA_PROXY` | | Proxy for every request to Fresha, e.g. `http://user:pass@host:port`. |
| `FRESHA_MCP_READ_ONLY` | | `1` hides and refuses every tool that changes Fresha (same as `--read-only`). |
| `FRESHA_MCP_TOKEN` | | Bearer token required by `serve`; needed to listen beyond `127.0.0.1`. |
| `FRESHA_MCP_HOST`, `FRESHA_MCP_PORT` | `127.0.0.1`, `8787` | Address of `serve`. |

## Security and your Fresha account

- **Your password never reaches this code.** Only the cookies Chrome already holds are read, and only those of fresha.com.
- **The session file is yours.** `session.json` is created with mode 0600. Anyone who has it can act as you in Fresha for business, so keep it out of git and shared folders.
- **Local by default.** `serve` binds to `127.0.0.1` and refuses another address without `FRESHA_MCP_TOKEN`.
- **fresha.com only.** Requests and redirects outside fresha.com are refused.
- **Read-only mode.** `--read-only` or `FRESHA_MCP_READ_ONLY=1` exposes the 10 read tools only.
- **Actions reach real people.** A booking, a move or a cancellation can message your client, and a review reply is public. MCP clients ask before running those tools; a script does not, so try it on a test client of your own first.

## Errors

The REST API answers `{"error": "<code>", "message": "..."}`. The MCP server returns the same code and message as a tool error.

| Status | Code | What to do |
|---|---|---|
| 401 | `auth_required`, `auth_expired` | No session, or Fresha signed you out. Sign in at partners.fresha.com in Chrome and run `fresha-mcp connect`. |
| 403 | `app_permission_denied` | Your Fresha role cannot do this, e.g. reports without the reporting permissions. |
| 403 | `scope_denied` | The server runs read-only, or the request would change your Fresha account itself. |
| 403 | `target_blocked` | Fresha refused the request or showed a bot check. Open the panel in Chrome once, then retry. |
| 409 | `captcha_required` | Fresha asks for a CAPTCHA. Solve it in Chrome. |
| 422 | `invalid_input` | An argument is missing or wrong; the message names it. |
| 429 | `rate_limited` | Fresha is limiting the account. Wait a few minutes. |
| 502 | `target_error` | Fresha answered with an error (its own message is in `message`), or changed its panel. `git pull` for the latest tools, or [open an issue](https://github.com/cotletdev/fresha-api-mcp-server/issues). |

## Self-hosted or hosted

| | This repo | [Cotlet, hosted](https://cotlet.dev/integrations/fresha-api-mcp-server) |
|---|---|---|
| Tools | the same 17 | the same 17 |
| Runs | on your computer, while it is on | in the cloud, 24/7 |
| Fresha session | your Chrome, saved in a local file | your own Cloud Browser in the EU, profile encrypted with AES-256-GCM |
| When Fresha changes its panel | `git pull` once we have fixed it | fixed for you, every tool tested daily |
| Approvals | your MCP client asks per call | bookings, moves, cancellations and review replies wait for your OK, switchable per tool |
| Works with | MCP clients on your machine, local scripts | Claude.ai and ChatGPT connectors, n8n, Make, Zapier, any HTTP client |
| Who may use it | you, for noncommercial use | teams, businesses, agencies |
| Price | free | free 7-day trial with 2,000 credits, no card; then one-time packs from $29 for 5,000 credits |

On the hosted version a successful call uses 10 credits, failed calls are free, and the Cloud Browser uses 50 credits a day while it has an app enabled for agents. [Full pricing](https://cotlet.dev/pricing).

## FAQ

**Does Fresha have an official API?**
No public one. Fresha publishes no API and no developer docs (checked 11 Oct 2026). Its Data Connector add-on, paid per location, syncs your data out to reporting tools through a Snowflake connection, and it cannot book, move or cancel appointments. Details: [cotlet.dev/integrations/fresha-api-mcp-server](https://cotlet.dev/integrations/fresha-api-mcp-server).

**Is there a Fresha MCP server for Claude, ChatGPT or Cursor?**
Yes, this one runs on your machine: `fresha-mcp mcp` for Claude Code, Claude Desktop, Cursor and Codex. ChatGPT and Claude.ai connectors need a public HTTPS URL, which the [hosted Fresha MCP server](https://cotlet.dev/integrations/fresha-api-mcp-server) gives you. A community server on GitHub reads Data Connector tables from Snowflake; it needs the add-on and does not write anything.

**Do I need the Data Connector add-on?**
No. The tools work on your own partners.fresha.com session, the same requests the panel sends.

**Can it find free slots and book for me?**
`find_available_slots` returns the free start times for one or more services done back to back, with one team member, for up to 14 days. `create_appointment` books one of them. Fresha books over other appointments if you ask it to, so check the slot first.

**Can I export my Fresha clients or sales to CSV?**
Yes: `python examples/export_clients.py --out clients.csv` and `python examples/export_sales.py --from 2026-10-01 --to 2026-10-31 --out sales.csv`.

**Does it work outside the UK?**
Yes. The tools read the time zone and currency of your workspace from Fresha. With several locations, the calendar tools use the first one.

**Why does it need my Chrome?**
To read your Fresha session without your password and the two sign-in codes. Chrome is used once per sign-in, not for each call.

**What happens when Fresha signs me out?**
Calls fail with `auth_expired`. With Chrome remote debugging on, the server reads the new session on the next call (click Allow when Chrome asks). Otherwise run `fresha-mcp connect` again.

**Can it run on a VPS or in Docker?**
Technically yes, with a pasted cookie or a `session.json` copied from your computer. Fresha then sees your session from a datacenter IP, which looks less like you. For an always-on setup the hosted version keeps your session in your own Cloud Browser on a fixed IP.

**Will my Fresha account get banned?**
Requests carry Chrome's fingerprint and go out one at a time, as you would click. Nobody can promise a platform never acts. Keep to your normal use.

**Can I use it for my salon or for my clients?**
No. The license allows noncommercial use only, and running your own business counts as business use. For a salon, a team or client work, use [Cotlet](https://cotlet.dev) or write to [contact@cotlet.dev](mailto:contact@cotlet.dev).

**Can I use the code for anything I like?**
No. The source is public, but the license allows noncommercial use only: no business use.

**A tool broke or I need another one.**
[Open an issue](https://github.com/cotletdev/fresha-api-mcp-server/issues) with the tool name and the error message.

## License

[PolyForm Noncommercial License 1.0.0](LICENSE). In short:

- **Allowed:** noncommercial use: you, for your own personal purposes with your own Fresha account, or a charity, school, public research or government body. Changing the code, and sharing it under the same license.
- **Not allowed:** any commercial use, your own business included; client work; selling or offering it, or a service built on it.

---

<p>
  <a href="https://cotlet.dev">
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset="assets/logo-white.svg">
      <img src="assets/logo.svg" alt="Cotlet" width="120">
    </picture>
  </a>
</p>

Maintained by [Cotlet](https://cotlet.dev) ([@cotletdev](https://x.com/cotletdev)). Fresha is a trademark of its owner. This project is unofficial and not affiliated with, endorsed or sponsored by Fresha.
