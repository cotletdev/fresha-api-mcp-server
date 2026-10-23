"""<cli>: connect your Chrome, then run the REST API and MCP server, or call one tool.

<cli> connect          # read your session of the app from Chrome (remote debugging on)
<cli> status           # which account the saved session is
<cli> tools            # every tool, read or write
<cli> call <tool> k=v  # one tool, arguments as JSON or key=value
<cli> mcp              # MCP server over stdio, for Claude Code, Claude Desktop, Cursor
<cli> serve            # REST API + MCP over HTTP on http://127.0.0.1:8787
"""

from __future__ import annotations

import argparse
import asyncio
import getpass
import ipaddress
import json
import os
import sys
from typing import Any
from urllib.parse import urlsplit

from fresha_api_mcp import __version__, app
from fresha_api_mcp import session as sessions
from fresha_api_mcp.core.errors import ToolError
from fresha_api_mcp.runner import Runner, all_tools, tools


def _connect(args: argparse.Namespace) -> None:
    if args.token:
        token = getpass.getpass(f"{sessions.SESSION_COOKIE} cookie value (input hidden): ")
        session = sessions.from_token(token)
    else:
        if not args.cdp:
            print("Connecting to Chrome. Click Allow if Chrome asks about remote debugging.", file=sys.stderr)
        session = sessions.from_chrome(args.cdp, args.profile_dir)
    path = sessions.save(session)
    who = asyncio.run(_whoami())
    print(f"Saved {len(session.cookies)} {app.NAME} cookies to {path}")
    print(f"Signed in to {app.NAME} as {who}" if who else f"Saved, but {app.NAME} did not confirm the session.")


async def _whoami() -> str | None:
    from fresha_api_mcp.core.context import ToolContext
    from fresha_api_mcp.fresha.auth import whoami

    ctx = ToolContext(session=sessions.load())
    try:
        return await whoami(ctx)
    except ToolError:
        return None
    finally:
        await ctx.close()


def _status(_: argparse.Namespace) -> None:
    session = sessions.load()
    if not session.signed_in:
        sys.exit(f"No {app.NAME} session. Run: {app.CLI} connect")
    who = asyncio.run(_whoami())
    if not who:
        sys.exit(f"{app.NAME} signed this session out. Sign in to {app.NAME} in Chrome, then run: {app.CLI} connect")
    source = {"auto": "your Chrome", "token": "a pasted token", None: f"{app.ENV}_AUTH_TOKEN"}.get(
        session.source, f"Chrome at {urlsplit(session.source or '').netloc}"
    )
    print(f"Signed in to {app.NAME} as {who} (session from {source}, {sessions.session_path()})")


def _tools(args: argparse.Namespace) -> None:
    specs = tools(args.read_only)
    if args.json:
        rows = [{"name": s.name, "access": s.access, "route": s.route, "input_schema": s.input_schema} for s in specs]
        print(json.dumps(rows, indent=2))
        return
    for spec in specs:
        print(f"{spec.name:<30} {spec.access:<5} {spec.route:<62} {spec.description}")


def _parse_args(tool: str, pairs: list[str]) -> dict[str, Any]:
    """key=value pairs; a value is JSON unless the tool's schema wants a string (IDs like 81234567)."""
    if len(pairs) == 1 and pairs[0].lstrip().startswith("{"):
        return json.loads(pairs[0])
    spec = all_tools().get(tool)
    properties = spec.input_schema.get("properties", {}) if spec else {}
    out: dict[str, Any] = {}
    for pair in pairs:
        key, sep, value = pair.partition("=")
        if not sep:
            sys.exit(f"Arguments are key=value or one JSON object, got {pair!r}")
        if properties.get(key, {}).get("type") == "string":
            out[key] = value
            continue
        try:
            out[key] = json.loads(value)
        except ValueError:
            out[key] = value
    return out


def _call(args: argparse.Namespace) -> None:
    runner = Runner(read_only=args.read_only)

    async def go() -> Any:
        try:
            return await runner.run(args.tool, _parse_args(args.tool, args.arguments))
        finally:
            await runner.close()

    try:
        result = asyncio.run(go())
    except ToolError as exc:
        sys.exit(f"{exc.code}: {exc}")
    print(json.dumps(result, indent=2, ensure_ascii=False))


def _mcp(args: argparse.Namespace) -> None:
    from fresha_api_mcp.mcp_server import run_stdio

    asyncio.run(run_stdio(Runner(read_only=args.read_only)))


def _serve(args: argparse.Namespace) -> None:
    import uvicorn

    from fresha_api_mcp.api import create_app

    try:
        loopback = ipaddress.ip_address(args.host).is_loopback
    except ValueError:
        loopback = args.host == "localhost"
    if not loopback and not os.environ.get(f"{app.ENV}_MCP_TOKEN"):
        sys.exit(
            f"Listening beyond this machine needs {app.ENV}_MCP_TOKEN, or anyone on the network can use your {app.NAME} account."
        )
    print(
        f"REST API  http://{args.host}:{args.port}{app.API_PREFIX}   docs http://{args.host}:{args.port}/docs",
        file=sys.stderr,
    )
    print(f"MCP       http://{args.host}:{args.port}/mcp", file=sys.stderr)
    uvicorn.run(create_app(Runner(read_only=args.read_only)), host=args.host, port=args.port, log_level="warning")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog=app.CLI,
        description=(__doc__ or "").replace("<cli>", app.CLI),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("connect", help=f"read your {app.NAME} session from Chrome and save it")
    p.add_argument(
        "--cdp", help="DevTools address of a Chrome started with --remote-debugging-port, e.g. http://127.0.0.1:9222"
    )
    p.add_argument("--profile-dir", help="Chrome profile folder holding DevToolsActivePort, when not the default")
    p.add_argument("--token", action="store_true", help=f"paste the {sessions.SESSION_COOKIE} cookie by hand instead")
    p.set_defaults(func=_connect)

    p = sub.add_parser("status", help=f"check the saved session with {app.NAME}")
    p.set_defaults(func=_status)

    for name, func, text in (
        ("tools", _tools, "list the tools"),
        ("mcp", _mcp, "MCP server over stdio"),
        ("serve", _serve, "REST API and MCP over HTTP"),
    ):
        p = sub.add_parser(name, help=text)
        p.add_argument(
            "--read-only",
            action="store_true",
            default=os.environ.get(f"{app.ENV}_MCP_READ_ONLY") == "1",
            help="only tools that read",
        )
        p.set_defaults(func=func)
        if name == "tools":
            p.add_argument("--json", action="store_true", help="names, routes and input schemas as JSON")
        if name == "serve":
            p.add_argument("--host", default=os.environ.get(f"{app.ENV}_MCP_HOST", "127.0.0.1"))
            p.add_argument("--port", type=int, default=int(os.environ.get(f"{app.ENV}_MCP_PORT", "8787")))

    p = sub.add_parser("call", help="run one tool and print its JSON answer")
    p.add_argument("tool")
    p.add_argument("arguments", nargs="*", help="key=value pairs or one JSON object, e.g. search=smith limit=10")
    p.add_argument("--read-only", action="store_true")
    p.set_defaults(func=_call)

    args = parser.parse_args()
    try:
        args.func(args)
    except ToolError as exc:
        sys.exit(f"{exc.code}: {exc}")
    except KeyboardInterrupt:
        sys.exit(130)


if __name__ == "__main__":
    main()
