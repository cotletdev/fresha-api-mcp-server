# Fresha API integration and MCP server: connect Fresha to ChatGPT and Claude

<!-- mcp-name: dev.cotlet/fresha -->

**Yes, ChatGPT, Claude and other AI agents can work in your Fresha account.** That includes Cursor, Codex, OpenClaw and any MCP client, plus automations in n8n, Make and Zapier. Ask in plain words, and the AI reads your calendar and open slots, books and moves appointments, answers reviews and reports your sales. It shows you what it will do first and sends nothing to other people until you say so.

As of November 2026, this repo is the missing piece: 17 Fresha tools for AI assistants and scripts.

## What you can ask

> *Anna Smith emailed asking for a cut and colour with Sam on Friday afternoon. Find her, check the free times for both services and book the first one after my OK.*
>
> *Sam is sick tomorrow. Block his day and show me which of his clients a colleague can take at the same time.*
>
> *Yesterday's sales by sale type against the same day last week. Flag refunds over £50.*
>
> *List the reviews without a reply and draft a short answer to each.*

## Two ways to get it

| | [Ready to use, at Cotlet](https://cotlet.dev/integrations/fresha-api-mcp-server?utm_source=github&utm_medium=readme&utm_campaign=fresha&utm_content=two-ways) | Run it yourself, this repo |
|---|---|---|
| For | salon, spa and wellness business owners | developers |
| Setup | sign in to Fresha once, about 5 minutes, nothing to install | Python and a terminal |
| Works in | ChatGPT and Claude apps, on your phone too, Cursor, Codex, OpenClaw, any MCP client, n8n, Make, Zapier, your own API endpoints (Custom API) | Claude Code, Claude Desktop, Cursor, Codex on your computer |
| Runs | 24/7, your computer can be off | while your computer is on |
| Price | 7 days free, no card | free |

Cotlet is best for salon, spa and wellness business owners who want ChatGPT, Claude or another AI agent to work in Fresha for them, with nothing to install.

**[Start free at cotlet.dev →](https://cotlet.dev/signup?app=fresha&utm_source=github&utm_medium=readme&utm_campaign=fresha&utm_content=top-button)**

## What salon, barbershop and spa owners ask their AI to do in Fresha

| Job | Ask your AI | Make it repeat |
|---|---|---|
| Tomorrow's bookings | "Who is booked tomorrow, per team member, and where are the gaps?" | Every evening |
| Morning summary | "Summarize new bookings, cancellations and no-shows since yesterday." | Every morning |
| Lapsed clients | "Find clients who have not booked for 90 days and draft a win-back message for each. Send nothing yet." | Weekly |
| Fill a cancelled slot | "Tomorrow's 11:00 cancelled. List waitlist clients who could take it and draft a message to the first one." | When a slot opens |
| Client notes | "Add these notes from today's appointments to each client's profile. Show me before you save." | After each day |
| Marketplace fee check | "List this month's new clients charged the marketplace fee, with how they booked, so I can check the charges." | Monthly |
| Team pay | "Run the Pay Summary report for last week and total hours, services and tips per team member." | Every week |
| Accounting export | "Download this month's sales and payments summary for my accountant." | Monthly |
| Sales and clients to a spreadsheet | "Export this month's appointments, sales and new clients to a spreadsheet." | Daily or monthly |
| Bulk price change | "Raise all colour services by 5% and show me the new prices before you save." | When prices change |
| Import from an old system | "Import the clients in this CSV from my old booking system." | Once |
| Leaving Fresha | "Download my clients, appointments and sales before I move." | Once |

Your AI asks you before it sends, books, cancels or changes anything. Payments and refunds stay in your hands: Cotlet refuses payments.

## Your own Fresha API, built with Cotlet (hosted)

Fresha gives businesses no public API. With Cotlet you build your own: your AI does the job once in your Cloud Browser, you save it as an endpoint, and you call it from Google Sheets, Power BI, GoHighLevel, Klaviyo, Mailchimp, n8n, Make, Zapier, your own code.

Examples you can build in a few minutes (none of them exists until you build it):

| Endpoint you build | What it returns or does |
|---|---|
| `bookings-for-day` | appointments for a date, with client, service, team member and time |
| `new-bookings` | bookings, cancellations and no-shows since a date |
| `lapsed-clients` | clients with no booking for a number of days |
| `open-slots` | free slots per team member for a date |
| `sales-summary` | sales, payments and tips for a period |
| `team-pay-summary` | hours, services and tips per team member for a period |
| `clients-export` | clients with contact details, first visit and last visit |
| `new-clients-source` | new clients in a period with how they booked |
| `add-client-note` | adds a note to a client's profile (writes only after you allow it) |
| `book-appointment` | books an appointment for a client and service (writes only after you allow it) |

Call it with your Cotlet API key, JSON in and JSON out:

```bash
curl -X POST https://cotlet.dev/api/v1/custom/bookings-for-day \
  -H "Authorization: Bearer $COTLET_API_KEY" -H "Content-Type: application/json" -d '{}'
```

Limits: one call runs up to 90 seconds, writes wait for your consent, payments are blocked. Start here: https://cotlet.dev/app/custom-api/new?app=fresha

## Find it on Cotlet.dev

- [Fresha MCP server on Cotlet.dev](https://cotlet.dev/integrations/fresha-api-mcp-server?utm_source=github&utm_medium=readme&utm_campaign=fresha&utm_content=old-repo)
- [Fresha API with Cotlet](https://cotlet.dev/integrations/api/fresha?utm_source=github&utm_medium=readme&utm_campaign=fresha&utm_content=old-repo)
- [Does Fresha have an API or MCP server?](https://cotlet.dev/api-status/fresha?utm_source=github&utm_medium=readme&utm_campaign=fresha&utm_content=old-repo)

## What you can ask your AI to do in Fresha

These are real jobs Fresha users asked about. Cotlet lets ChatGPT, Claude or any MCP client do them in your own signed-in Fresha account.

### Connect to other tools

#### How do I connect Fresha to GoHighLevel so new bookings, cancellations and completed appointments update my contacts?

Yes. Fresha has no Zapier app and no public API. With Cotlet, your agent reads new, cancelled and completed appointments in your signed-in Fresha account and updates the matching contacts in GoHighLevel, both signed in in your Cloud Browser. Nothing changes until you say yes.

Ask your agent: "Read today's new, cancelled and completed Fresha appointments and update each client's contact in GoHighLevel with the status and date."

As an API endpoint: Yes. Save the appointment check as an endpoint in Cotlet and call it every hour from n8n, Make or Zapier to keep GoHighLevel up to date.

#### How do I connect Fresha to QuickBooks or Xero so my accountant stops asking for exports?

Partly. Fresha has its own Xero and QuickBooks syncs for sales, payments, payouts, fees and team pay. With Cotlet, your agent can also read your Fresha reports and enter the totals in QuickBooks or Xero, or list what does not match. Nothing changes until you say yes.

Ask your agent: "Read last week's Fresha sales and payments report and list anything that is missing in QuickBooks. Do not enter anything yet."

As an API endpoint: Yes. Save the weekly sales read as an endpoint in Cotlet and call it from n8n, Make or Zapier to send the figures to your accountant.

#### How do I get my Fresha sales and client data into Google Sheets or Power BI every day?

Yes. Fresha's Data connector is a paid add-on that copies data to Snowflake. With Cotlet, your agent reads the sales and appointments in your signed-in Fresha account and adds the rows to a Google Sheet that Power BI can read.

Ask your agent: "Read yesterday's Fresha sales and appointments and add one row per sale to my Google Sheet."

As an API endpoint: Yes. Save the daily read as an endpoint in Cotlet and call it every morning from n8n, Make or Zapier to append rows to Google Sheets.

#### How do I sync my Fresha calendar with Google Calendar and my iPhone calendar, and why doesn't it update?

Partly. Fresha can link an external calendar both ways (Google, Apple, Outlook). When it does not update, Cotlet's agent reads your upcoming Fresha appointments and your Google Calendar and lists the ones that are missing or different.

Ask your agent: "Compare my Fresha appointments for the next 7 days with my Google Calendar and list any that are missing or have a different time."

As an API endpoint: Yes. Save the comparison as an endpoint in Cotlet and call it every morning from n8n, Make or Zapier to get the list by email.

#### How do I connect Fresha to Klaviyo or Mailchimp so people who booked off-site get emails?

Yes. With Cotlet, your agent reads new clients and their latest bookings in your signed-in Fresha account and adds them to your Klaviyo or Mailchimp list. Nothing changes until you say yes.

Ask your agent: "Take Fresha clients added this week and add each one to my Mailchimp audience with name, email and last service."

As an API endpoint: Yes. Save the new-client read as an endpoint in Cotlet and call it daily from n8n, Make or Zapier to update Klaviyo or Mailchimp.

#### Can I track Google Ads or Meta Ads conversions from Fresha bookings?

Partly. Fresha lists Meta Pixel and Google Analytics integrations on its pricing page. With Cotlet, your agent reads new bookings in your Fresha account and puts them in a Google Sheet, so you can match them with your ads reports.

Ask your agent: "List Fresha bookings from the last 30 days with date, service, price and how the client booked, in one table."

As an API endpoint: Yes. Save the bookings read as an endpoint in Cotlet and call it weekly from n8n, Make or Zapier to update your ads sheet.

### Calendar and clients

#### Can ChatGPT or Claude read my Fresha calendar and tell me who is booked tomorrow?

Yes. Fresha's own ChatGPT and Claude app is for your clients, not for your calendar. With Cotlet, ChatGPT or Claude opens your signed-in Fresha calendar and tells you who is booked tomorrow, with service, time and team member.

Ask your agent: "Read tomorrow's Fresha calendar and list each booking with time, client, service and team member."

As an API endpoint: Yes. Save the read as an endpoint in Cotlet and call it every evening from n8n, Make or Zapier to email you tomorrow's list.

#### Can an AI answer my clients' messages and write notes on their Fresha profile for me?

Partly. Fresha's AI Concierge replies to client messages on a paid plan. With Cotlet, your agent reads a client's profile and recent visits in Fresha, drafts the reply and adds the note on the profile. Nothing is sent until you say yes.

Ask your agent: "Read this client's Fresha profile and last visits, draft a reply to her message and add a short note to her profile. Show me both first."

#### Can AI be my receptionist for Fresha: answer calls, book into my calendar and reply to reviews?

Partly. Fresha's AI Concierge answers calls and messages and books into your calendar on a paid plan. Cotlet does not answer calls. With Cotlet, your agent can read new reviews in Fresha and draft each reply. Nothing is sent until you say yes.

Ask your agent: "List my new Fresha reviews and draft a short, friendly public reply for each one."

As an API endpoint: Yes. Save the review read as an endpoint in Cotlet and call it daily from n8n, Make or Zapier, for example to connect a voice assistant of your own.

#### Can AI fill a slot in Fresha automatically when someone cancels, from my waitlist?

Partly. Fresha has a waitlist screen where clients wait for an open slot. With Cotlet, your agent sees the cancellation, finds waitlist entries that fit the slot and drafts a message to the first one. Nothing is sent until you say yes.

Ask your agent: "Check today's Fresha cancellations, find waitlist entries that fit each open slot and draft a message for the best match."

As an API endpoint: Yes. Save the cancellation check as an endpoint in Cotlet and call it every 30 minutes from n8n, Make or Zapier.

### Win-backs and fees

#### Can AI find my lapsed clients in Fresha and send them a win-back message?

Partly. Fresha has blast campaigns and a Client insights report on its own. With Cotlet, your agent finds clients with no visit in 60 days and nothing booked, and drafts a personal message for each. Nothing is sent until you say yes.

Ask your agent: "Find Fresha clients with no visit in 60 days and no future booking, and draft a short win-back message for each."

As an API endpoint: Yes. Save the lapsed-client list as an endpoint in Cotlet and call it monthly from n8n, Make or Zapier.

#### Can AI check which clients I was charged the 20% Fresha marketplace fee for even though they came from my own link?

Partly. Fresha lets you download your invoices and fees. With Cotlet, your agent reads those fee lines and the client records in your signed-in Fresha account and lists the clients you think were charged wrongly, so you can send them to Fresha support.

Ask your agent: "Read my Fresha fee invoices for last month and list each client charged a marketplace fee, with date and amount."

As an API endpoint: Yes. Save the fee read as an endpoint in Cotlet and call it monthly from n8n, Make or Zapier.

### Money and team pay

#### Can AI prepare my year-end tax summary from Fresha so it matches my P&L?

Partly. Fresha exports reports as PDF, CSV or XLSX and lets you download invoices and fees. With Cotlet, your agent reads those reports for the whole year and builds one summary table you can compare with your P&L. It is not tax advice.

Ask your agent: "Read my Fresha sales, tips, fees and refunds for this year and build one summary table by month."

As an API endpoint: Yes. Save the yearly read as an endpoint in Cotlet and call it from n8n, Make or Zapier when your accountant asks.

#### How do I run Fresha team pay from the Pay Summary report each week without paying for the Team Pay add-on?

Yes. With Cotlet, your agent reads the Pay Summary report in your signed-in Fresha account and gives you pay per team member as a table or a Google Sheet. Cotlet does not pay anyone.

Ask your agent: "Read this week's Fresha Pay Summary report and give me pay per team member in one table."

As an API endpoint: Yes. Save the pay read as an endpoint in Cotlet and call it every Monday from n8n, Make or Zapier.

#### How do I change prices for all my Fresha services at once, including appointments already booked?

Partly. Fresha's catalog has bulk edit for service prices. With Cotlet, your agent can also open the appointments already booked and change each price in your signed-in account. Nothing changes until you say yes to the list.

Ask your agent: "List every upcoming Fresha appointment for the haircut service and show the new price at 45. Wait for my OK before changing anything."

### Exports, imports and leaving

#### How do I export all my clients, appointments and sales from Fresha to CSV every month as a backup?

Yes. Fresha exports the client list from Clients and reports as PDF, CSV or XLSX, one screen at a time by hand. With Cotlet, your agent does each export in your signed-in account and saves the files for you.

Ask your agent: "Export my Fresha client list, this month's appointments and sales to separate CSV files."

As an API endpoint: Yes. Save the export as an endpoint in Cotlet and call it on the first of each month from n8n, Make or Zapier.

#### I'm leaving Fresha. How do I take my clients, consultation forms and reviews with me?

Partly. Fresha exports the client list and reports, but its help centre shows no export for forms and reviews. With Cotlet, your agent opens each client form and review in your signed-in account and saves the text to files you keep.

Ask your agent: "Save every Fresha client form and review to files, one per client, plus the client list as CSV."

#### How do I import my client list and services into Fresha from my old booking system?

Partly. Fresha imports client lists and products, but its help centre shows no import for services. With Cotlet, your agent adds the services one by one from your spreadsheet. Nothing is created until you say yes.

Ask your agent: "Take the services in this spreadsheet and add each one to Fresha with its price and duration. Show me the first five first."

#### How do I get a morning summary of new Fresha bookings and update my records from a spreadsheet automatically?

Yes. With Cotlet, your agent reads yesterday's new bookings in your signed-in Fresha account and gives you a short summary. It can also update client details from a spreadsheet. Nothing changes until you say yes.

Ask your agent: "Summarise Fresha bookings made since yesterday, then update client phone numbers from my spreadsheet. Show me the changes first."

As an API endpoint: Yes. Save the summary as an endpoint in Cotlet and call it every morning from n8n, Make or Zapier to get it by email.

## Run it yourself

A **Fresha API** and a **Fresha MCP server** you run on your own computer, in Python, on the session of your own Google Chrome. All 17 Fresha tools we run in production at [Cotlet](https://cotlet.dev/integrations/fresha-api-mcp-server?utm_source=github&utm_medium=readme&utm_campaign=fresha&utm_content=intro): appointments, free slots, booking, rescheduling and cancelling, blocked time, clients and client notes, services and team, the Sales summary and Sales list reports, and reviews with replies.

Fresha has no public API and no official MCP server. Its only data connection is the paid Data Connector add-on, which copies your data out to a Snowflake database and cannot book anything. This repo gives you:

- **MCP server** for Claude Code, Claude Desktop, Cursor, Codex and any MCP client, over stdio or HTTP. [Setup](#mcp-server)
- **REST API** on `http://127.0.0.1:8787/api/v1/fresha`, with OpenAPI docs at `/docs`. [Setup](#rest-api-local-this-repo)
- **Python**: `call("list_appointments", {"from": "2026-10-27", "to": "2026-10-27"})`, plus 9 ready scripts in [`examples/`](https://github.com/cotletdev/fresha-api-mcp-server/blob/main/examples/).

Free for your own use, your own business included ([license](#license)).

[![Fresha MCP server](https://img.shields.io/badge/Fresha%20MCP-17%20tools-6d4aef)](#all-17-tools)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-141318)](#requirements)
[![License: Elastic 2.0](https://img.shields.io/badge/license-Elastic%202.0-141318)](https://github.com/cotletdev/fresha-api-mcp-server/blob/main/LICENSE)
[![MCP Badge](https://lobehub.com/badge/mcp/cotletdev-fresha-api-mcp-server)](https://lobehub.com/mcp/cotletdev-fresha-api-mcp-server)

Also on Odel: https://odel.app/modules/cotlet/fresha and mcpbeat: https://mcpbeat.com/mcp-servers/cotlet/fresha/

```bash
uv tool install fresha-api-mcp                  # or: pip install fresha-api-mcp
fresha-mcp connect                                 # reads your Fresha session from Chrome
fresha-mcp call list_services
claude mcp add fresha -- uvx fresha-api-mcp mcp
```

## Contents

- [Questions from Fresha users](#questions-from-fresha-users)
- [How it works](#how-it-works)
- [Requirements](#requirements)
- [Install](#install)
- [Connect your Chrome](#connect-your-chrome)
- [MCP server](#mcp-server)
- [REST API](#rest-api-local-this-repo)
- [Python and the example scripts](#python-and-the-example-scripts)
- [All 17 tools](#all-17-tools)
- [Configuration](#configuration)
- [Security and your Fresha account](#security-and-your-fresha-account)
- [Errors](#errors)
- [Self-hosted or hosted](#self-hosted-or-hosted)
- [FAQ](#faq)
- [License](#license)

## Questions from Fresha users

**Can ChatGPT or Claude read my Fresha calendar?**

Fresha's own ChatGPT and Claude apps are for clients who book. With Cotlet, ChatGPT and Claude work in your own business account: they read your calendar, clients and sales, and tell you who is booked tomorrow.

**Does Fresha work with Zapier or Make?**

Fresha has no Zapier app and no public API. With Cotlet you build your own Fresha endpoints, such as `new-bookings` or `clients-export`, and call them from Zapier, Make or n8n.

**How do I connect Fresha to GoHighLevel?**

Call your `new-bookings` endpoint from a GoHighLevel or n8n workflow on a schedule, so new bookings, cancellations and completed appointments update your contacts.

**How do I get Fresha sales and client data into Google Sheets or Power BI every day?**

Build `sales-summary` and `clients-export` endpoints once, then load them into Google Sheets or Power BI on a schedule.

**How do I connect Fresha to Klaviyo or Mailchimp?**

A `clients-export` or `new-bookings` endpoint feeds Klaviyo or Mailchimp, so clients who booked get your emails without a manual export.

**Can AI fill a cancelled slot from my waitlist?**

Your AI lists who could take the slot and drafts the message. It books only after you say yes.

**Can AI check which clients I paid the marketplace fee for?**

It lists the new clients charged the fee in a period, with how they booked, so you can check each charge with Fresha.

**How do I export all my Fresha data every month as a backup?**

Your AI downloads every report and list your login can export: clients, appointments and sales. A `clients-export` endpoint can run it on a schedule.

**I'm leaving Fresha. How do I take my clients with me?**

Your AI exports your client list, appointments and sales your login can see, as spreadsheets for your new system.

**Is Cotlet affiliated with Fresha?**

No. Cotlet is independent and not affiliated with Fresha.

**Does Fresha have an API?**
No public one. Fresha publishes no API and no developer docs (checked 11 Oct 2026). Its Data Connector add-on, paid per location, syncs your data out to reporting tools through a Snowflake connection, and it cannot book, move or cancel appointments. This repo and [Cotlet](https://cotlet.dev/integrations/fresha-api-mcp-server?utm_source=github&utm_medium=readme&utm_campaign=fresha&utm_content=faq-api) give you 17 Fresha tools as a REST API and an MCP server.

**Can I get a Fresha API key?**
Not from Fresha for your own account. With Cotlet you get your own API key that works with your Fresha account, for scripts, n8n, Make, Zapier or any HTTP client. This repo needs no key: it runs on your computer, on your own Fresha session.

**Is there an official ChatGPT integration for Fresha?**
Fresha's ChatGPT and Claude apps are for clients: they find salons and book open slots. They do not run your business. Cotlet connects your Fresha partner account to ChatGPT, Claude and other AI agents: your calendar, clients, team and sales.

**How do I connect Fresha to ChatGPT?**
Sign up at [cotlet.dev](https://cotlet.dev/signup?app=fresha&utm_source=github&utm_medium=readme&utm_campaign=fresha&utm_content=faq-chatgpt), sign in to Fresha once in your Cloud Browser there, and add Cotlet to ChatGPT, following the steps in your account. Then ask ChatGPT about your Fresha like you would ask an assistant. ChatGPT needs a server on the internet, so this repo alone, running on your computer, does not connect to ChatGPT.

**Can ChatGPT manage my Fresha calendar?**
Yes, with Cotlet. It lists the day's appointments and gaps, finds open slots, books and moves appointments and blocks time. It shows you each change first.

**Fresha has an AI receptionist. What does this add?**
Fresha's AI answers your clients. With Cotlet, your own AI works for you in the back office: the calendar, clients, team and sales reports.

**Can I automate Fresha with Zapier, Make or n8n?**
Fresha has no Zapier or Make app. With Cotlet, n8n, Make and Zapier can read and book appointments and add clients, for example from a web form.

**Can I use it from my phone?**
Yes, with Cotlet: once it is set up, the ChatGPT and Claude apps on your phone can use Fresha for you.

**Do I need to be technical?**
For Cotlet, no: you sign in to Fresha and add Cotlet to ChatGPT or Claude, with step-by-step instructions in your account. This repo is for people who are fine with Python and a terminal.

**Is my Fresha account safe?**
Yes. Neither Cotlet nor this repo sees or stores your Fresha password. You sign in yourself, the way you always do, and the AI works on that signed-in session. Anything that reaches other people asks for your OK first: in Cotlet by default, here through your MCP client.

**Is it free?**
This repo is free, also in your own business. Cotlet is free for 7 days with no card, then one-time credit packs from $29, no subscription. [Pricing](https://cotlet.dev/pricing?utm_source=github&utm_medium=readme&utm_campaign=fresha&utm_content=faq-price).

**I manage Fresha for several accounts or clients. Does that work?**
Yes, with Cotlet. Each Fresha login gets its own connection. Write to [contact@cotlet.dev](mailto:contact@cotlet.dev) and tell us how many accounts you manage.

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

From [PyPI](https://pypi.org/project/fresha-api-mcp/):

```bash
uv tool install fresha-api-mcp       # or: pipx install fresha-api-mcp, or: pip install fresha-api-mcp
fresha-mcp --version
```

MCP clients can also run it with no install: `uvx fresha-api-mcp mcp`.

From source:

```bash
git clone https://github.com/cotletdev/fresha-api-mcp-server.git
cd fresha-api-mcp-server
python3 -m venv .venv
. .venv/bin/activate              # Windows: .venv\Scripts\activate
pip install -e .
fresha-mcp --version
```

With [uv](https://docs.astral.sh/uv/): `uv venv && uv pip install -e .`, then `uv run fresha-mcp ...`.

Setting it up with an AI agent (Claude Code, Codex, Cursor)? Open it in this folder and ask it to set up the repo: [`AGENTS.md`](https://github.com/cotletdev/fresha-api-mcp-server/blob/main/AGENTS.md) tells it every step, and it asks you only for the steps in Chrome.

To update: `uv tool upgrade fresha-api-mcp` (or `pip install -U fresha-api-mcp`), from source `git pull && pip install -e .`. We copy every change of the hosted Fresha tools into this repo.

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
claude mcp add fresha -- uvx fresha-api-mcp mcp
# read only:
claude mcp add fresha -- uvx fresha-api-mcp mcp --read-only
```

### Claude Desktop

`~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "fresha": {
      "command": "uvx",
      "args": ["fresha-api-mcp", "mcp"]
    }
  }
}
```

### Cursor

`~/.cursor/mcp.json`, the same block as Claude Desktop. A ready copy is in [`mcp.json`](https://github.com/cotletdev/fresha-api-mcp-server/blob/main/mcp.json).

### Codex

`~/.codex/config.toml`:

```toml
[mcp_servers.fresha]
command = "uvx"
args = ["fresha-api-mcp", "mcp"]
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

## REST API (local, this repo)

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

Ready scripts in [`examples/`](https://github.com/cotletdev/fresha-api-mcp-server/blob/main/examples/). Each prints JSON or a short list, takes `--out file.csv` or `--out file.json` where it makes sense, and `--help`:

| Script | What it does |
|---|---|
| [`tomorrows_appointments.py`](https://github.com/cotletdev/fresha-api-mcp-server/blob/main/examples/tomorrows_appointments.py) | Tomorrow's appointments grouped by team member. `--date`, `--all` for cancelled ones too. |
| [`book_from_message.py`](https://github.com/cotletdev/fresha-api-mcp-server/blob/main/examples/book_from_message.py) | Matches a client by name, email or phone, finds free starts for several services in a time window, and with `--book` books the first after you confirm. |
| [`team_member_out.py`](https://github.com/cotletdev/fresha-api-mcp-server/blob/main/examples/team_member_out.py) | A team member is out: blocks their hours and moves each client to a colleague free at the same time. Prints the plan; `--apply` asks before each change. |
| [`cancel_day.py`](https://github.com/cotletdev/fresha-api-mcp-server/blob/main/examples/cancel_day.py) | Cancels a team member's appointments on a day with your cancellation reason. Lists them; `--apply` asks before each one. |
| [`daily_sales.py`](https://github.com/cotletdev/fresha-api-mcp-server/blob/main/examples/daily_sales.py) | One day's Sales summary by sale type against the same weekday a week earlier, refunds over a limit flagged. |
| [`lapsed_clients.py`](https://github.com/cotletdev/fresha-api-mcp-server/blob/main/examples/lapsed_clients.py) | Clients with no appointment for N days and nothing booked, with their marketing consent. `--email-consent-only`. |
| [`export_clients.py`](https://github.com/cotletdev/fresha-api-mcp-server/blob/main/examples/export_clients.py) | Every client to CSV or JSON. `--search`, `--sort`. |
| [`export_sales.py`](https://github.com/cotletdev/fresha-api-mcp-server/blob/main/examples/export_sales.py) | The Sales list for a date range to CSV or JSON. |
| [`unanswered_reviews.py`](https://github.com/cotletdev/fresha-api-mcp-server/blob/main/examples/unanswered_reviews.py) | Reviews without a reply, lowest rating first; `--reply-to` posts a reply. |

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

| | This repo | [Cotlet, hosted](https://cotlet.dev/integrations/fresha-api-mcp-server?utm_source=github&utm_medium=readme&utm_campaign=fresha&utm_content=compare) |
|---|---|---|
| Tools | the same 17 | the same 17 |
| Runs | on your computer, while it is on | in the cloud, 24/7 |
| Fresha session | your Chrome, saved in a local file | your own Cloud Browser in the EU, profile encrypted with AES-256-GCM |
| When Fresha changes its panel | `git pull` once we have fixed it | fixed for you, every tool tested daily |
| Approvals | your MCP client asks per call | bookings, moves, cancellations and review replies wait for your OK, switchable per tool |
| Works with | MCP clients on your machine, local scripts | Claude.ai and ChatGPT connectors, n8n, Make, Zapier, any HTTP client through your own endpoints (Custom API) |
| Who may use it | you and your own business | you, teams, businesses, agencies |
| Price | free | free 7-day trial, no card; then one-time packs from $29 for 5,000 credits |

On the hosted version a successful call uses 10 credits, failed calls are free, and the Cloud Browser uses 50 credits a day while it has an app enabled for agents. [Full pricing](https://cotlet.dev/pricing).

## FAQ

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

**Can I change the code or offer it to my clients?**
You may change it and use it in your own business. You may not offer it to others as a hosted or managed service. For client work, use [Cotlet](https://cotlet.dev?utm_source=github&utm_medium=readme&utm_campaign=fresha&utm_content=faq-clients) or write to [contact@cotlet.dev](mailto:contact@cotlet.dev).

**A tool broke or I need another one.**
[Open an issue](https://github.com/cotletdev/fresha-api-mcp-server/issues) with the tool name and the error message.

## License

[Elastic License 2.0](https://github.com/cotletdev/fresha-api-mcp-server/blob/main/LICENSE). In short:

- **Allowed:** using it for yourself and in your own business, free. Changing the code and sharing it under the same license.
- **Not allowed:** offering it to others as a hosted or managed service, removing the license notices, getting around its limits.

---

<p>
  <a href="https://cotlet.dev">
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset="assets/logo-white.svg">
      <img src="https://raw.githubusercontent.com/cotletdev/fresha-api-mcp-server/main/assets/logo.svg" alt="Cotlet" width="120">
    </picture>
  </a>
</p>

Maintained by [Cotlet](https://cotlet.dev?utm_source=github&utm_medium=readme&utm_campaign=fresha&utm_content=footer) ([@cotletdev](https://x.com/cotletdev)). Fresha is a trademark of its owner. This project is unofficial and not affiliated with, endorsed or sponsored by Fresha.
