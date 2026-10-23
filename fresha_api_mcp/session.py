"""Your session of the app: its cookies from your own Chrome, saved on this machine.

`<cli> connect` reads them from Chrome over the Chrome DevTools Protocol, in one of two ways:

- Chrome 144+ with remote debugging switched on at chrome://inspect/#remote-debugging. Chrome writes
  the port to `DevToolsActivePort` in its profile folder and asks you to allow each connection.
- Any Chrome started with `--remote-debugging-port=9222 --user-data-dir=<folder>`: pass `--cdp http://127.0.0.1:9222`.

The session file holds cookies only, never your password, and is readable by your user alone (0600).
Names, domains and the session cookie come from `app.py`.
"""

from __future__ import annotations

import json
import os
import platform
import re
import stat
import urllib.request
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from fresha_api_mcp import app
from fresha_api_mcp.core.errors import ErrorCode, ToolError

SESSION_COOKIE = app.SESSION_COOKIES[0]


def home() -> Path:
    """Where the session is kept: $<ENV>_MCP_HOME, or ~/.config/<slug>-api-mcp."""
    return Path(os.environ.get(f"{app.ENV}_MCP_HOME") or Path.home() / ".config" / f"{app.SLUG}-api-mcp")


def session_path() -> Path:
    return home() / "session.json"


@dataclass
class Session:
    cookies: list[dict[str, Any]] = field(default_factory=list)
    user_agent: str | None = None
    chrome_major: int | None = None
    locale: str | None = None
    # Where the cookies came from, so a signed-out session can be read again: "auto", a CDP URL, or "token".
    source: str | None = None
    proxy: str | None = None

    @property
    def signed_in(self) -> bool:
        return all(any(c["name"] == name and c.get("value") for c in self.cookies) for name in app.SESSION_COOKIES)


def load() -> Session:
    """The saved session, with <ENV>_AUTH_TOKEN and <ENV>_PROXY from the environment on top."""
    session = Session()
    path = session_path()
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
        session = Session(**{k: v for k, v in data.items() if k in Session.__dataclass_fields__})
    if token := os.environ.get(f"{app.ENV}_AUTH_TOKEN", "").strip():
        session.cookies = [c for c in session.cookies if c["name"] != SESSION_COOKIE]
        session.cookies.append({"name": SESSION_COOKIE, "value": token, "domain": app.COOKIE_DOMAIN, "path": "/"})
        session.source = session.source or "token"
    if proxy := os.environ.get(f"{app.ENV}_PROXY", "").strip():
        session.proxy = proxy
    return session


def save(session: Session) -> Path:
    path = session_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, stat.S_IRUSR | stat.S_IWUSR)
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        json.dump(asdict(session), fh, indent=2)
    os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)
    return path


def from_token(token: str) -> Session:
    """A session from the session cookie value copied by hand (Chrome DevTools > Application > Cookies)."""
    token = token.strip()
    if not token:
        raise ToolError("The token is empty.", ErrorCode.INVALID_INPUT)
    cookie = {"name": SESSION_COOKIE, "value": token, "domain": app.COOKIE_DOMAIN, "path": "/"}
    return Session(cookies=[cookie], source="token")


def chrome_profile_dirs() -> list[Path]:
    """Default Chrome profile folders of this OS, stable channel first."""
    system = platform.system()
    if system == "Darwin":
        base = Path.home() / "Library" / "Application Support" / "Google"
        return [base / "Chrome", base / "Chrome Beta", base / "Chrome Canary"]
    if system == "Windows":
        base = Path(os.environ.get("LOCALAPPDATA", "")) / "Google"
        return [base / "Chrome" / "User Data", base / "Chrome Beta" / "User Data", base / "Chrome SxS" / "User Data"]
    base = Path.home() / ".config"
    return [base / "google-chrome", base / "google-chrome-beta", base / "chromium"]


def auto_endpoint(profile_dir: str | None = None) -> str:
    """The browser WebSocket URL from DevToolsActivePort, written while remote debugging is on."""
    dirs = [Path(profile_dir).expanduser()] if profile_dir else chrome_profile_dirs()
    for folder in dirs:
        port_file = folder / "DevToolsActivePort"
        if port_file.exists():
            lines = port_file.read_text(encoding="utf-8").split()
            if len(lines) >= 2 and lines[0].isdigit():
                return f"ws://127.0.0.1:{lines[0]}{lines[1]}"
    raise ToolError(
        "Chrome remote debugging is off. Open chrome://inspect/#remote-debugging in Chrome, switch it on, "
        "and run this again. Or start Chrome with --remote-debugging-port=9222 and pass --cdp http://127.0.0.1:9222.",
        ErrorCode.AUTH_REQUIRED,
    )


def _endpoint(cdp: str) -> str:
    """A ws:// URL as given, or the browser WebSocket URL behind an http:// DevTools address."""
    if cdp.startswith(("ws://", "wss://")):
        return cdp
    with urllib.request.urlopen(cdp.rstrip("/") + "/json/version", timeout=10) as resp:
        return json.loads(resp.read())["webSocketDebuggerUrl"]


class _Cdp:
    """A tiny synchronous CDP client: one WebSocket to the browser target."""

    def __init__(self, url: str) -> None:
        from websockets.sync.client import connect

        # Chrome shows "Allow remote debugging?" for this connection; give the user time to click it.
        self._ws = connect(url, open_timeout=60, max_size=64 * 1024 * 1024)
        self._id = 0

    def send(self, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        self._id += 1
        self._ws.send(json.dumps({"id": self._id, "method": method, "params": params or {}}))
        while True:
            message = json.loads(self._ws.recv(timeout=60))
            if message.get("id") != self._id:
                continue
            if "error" in message:
                raise ToolError(f"Chrome refused {method}: {message['error'].get('message')}", ErrorCode.INTERNAL_ERROR)
            return message.get("result") or {}

    def close(self) -> None:
        self._ws.close()


def from_chrome(cdp: str | None = None, profile_dir: str | None = None) -> Session:
    """Read the app's cookies of a running Chrome. Nothing is changed in the browser."""
    url = _endpoint(cdp) if cdp else auto_endpoint(profile_dir)
    try:
        client = _Cdp(url)
    except Exception as exc:
        raise ToolError(
            f"Could not connect to Chrome at {urlsplit(url).netloc} ({type(exc).__name__}). "
            "Is Chrome open, and did you click Allow in its remote debugging prompt?",
            ErrorCode.AUTH_REQUIRED,
        ) from exc
    try:
        version = client.send("Browser.getVersion")
        cookies = client.send("Storage.getCookies").get("cookies") or []
    finally:
        client.close()
    mine = [
        {"name": c["name"], "value": c["value"], "domain": c["domain"], "path": c.get("path") or "/"}
        for c in cookies
        if any(c.get("domain", "").lstrip(".").endswith(domain) for domain in app.DOMAINS)
    ]
    user_agent = version.get("userAgent")
    match = re.search(r"Chrome/(\d+)", user_agent or "") or re.search(r"/(\d+)\.", version.get("product", ""))
    session = Session(
        cookies=mine,
        user_agent=user_agent,
        chrome_major=int(match.group(1)) if match else None,
        source=cdp or "auto",
    )
    if not session.signed_in:
        raise ToolError(
            f"This Chrome is not signed in to {app.NAME}. Sign in at {app.LOGIN_URL}, then run this again.",
            ErrorCode.AUTH_REQUIRED,
        )
    return session


def refresh(session: Session) -> Session | None:
    """Read the cookies again from where they came from; None when the source is a hand-copied token."""
    if not session.source or session.source == "token":
        return None
    fresh = from_chrome(None if session.source == "auto" else session.source)
    fresh.proxy = session.proxy
    save(fresh)
    return fresh
