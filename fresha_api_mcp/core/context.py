"""What a tool function gets besides its input: a ready HTTP client with your session of the app.

Requests go out with curl_cffi, which copies Chrome's TLS and HTTP/2 fingerprint, so the app sees the same
kind of client as your browser. Only the app's hosts (`app.DOMAINS`) are reachable, redirects included.
"""

from __future__ import annotations

import json as jsonlib
import time
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urljoin, urlsplit

from curl_cffi.requests import AsyncSession, BrowserType

from fresha_api_mcp import app
from fresha_api_mcp.core.account_guard import check_account_write
from fresha_api_mcp.core.errors import AuthExpiredError, CaptchaRequiredError, ErrorCode, ToolError
from fresha_api_mcp.session import Session

DOMAINS = app.DOMAINS
_REDIRECTS = {301, 302, 303, 307, 308}
_MAX_REDIRECTS = 10
_TARGETS = {member.value for member in BrowserType}
_CHALLENGE_MARKERS = ("cf-chl", "challenge-platform", "Just a moment...", "cf_chl_opt")
_CAPTCHA_MARKERS = ("g-recaptcha", "h-captcha", "cf-turnstile")
_LOGGED_OUT_MARKERS = app.LOGGED_OUT_MARKERS


@dataclass(frozen=True)
class HttpResponse:
    status: int
    url: str
    headers: dict[str, str]
    text: str

    def json(self) -> Any:
        try:
            return jsonlib.loads(self.text)
        except ValueError as exc:
            raise ToolError(f"{app.NAME} answered with something that is not JSON.", ErrorCode.TARGET_ERROR) from exc


def allowed_host(url: str) -> bool:
    host = (urlsplit(url).hostname or "").lower()
    return any(host == domain or host.endswith(f".{domain}") for domain in DOMAINS)


def impersonate_target(chrome_major: int | None) -> str:
    """The exact Chrome version when curl_cffi has it, otherwise its newest Chrome profile."""
    target = f"chrome{chrome_major}"
    return target if chrome_major and target in _TARGETS else "chrome"


def _raise_for(response: HttpResponse) -> None:
    final_url = response.url.lower()
    if response.status == 401 or any(marker in final_url for marker in _LOGGED_OUT_MARKERS):
        raise AuthExpiredError(
            f"{app.NAME} signed this session out. Sign in to {app.NAME} in Chrome, then run: {app.CLI} connect"
        )
    if response.status == 429:
        raise ToolError(f"{app.NAME} is rate limiting this account. Try again later.", ErrorCode.RATE_LIMITED)
    head = response.text[:20000]
    if response.status in (401, 403) and any(marker in head for marker in app.RELOGIN_MARKERS):
        raise AuthExpiredError(
            f"{app.NAME} asks you to sign in again before this action. Sign out and in again at "
            f"{app.LOGIN_URL} in Chrome, then run: {app.CLI} connect"
        )
    if response.status in (200, 403) and any(marker in head for marker in _CAPTCHA_MARKERS):
        raise CaptchaRequiredError(
            f"{app.NAME} asks for a CAPTCHA. Open {app.DOMAINS[0]} in Chrome, finish it, then try again."
        )
    if response.status in (403, 503) and (
        response.headers.get("cf-mitigated") == "challenge" or any(marker in head for marker in _CHALLENGE_MARKERS)
    ):
        raise ToolError(
            f"{app.NAME} showed a bot check. Open {app.DOMAINS[0]} in Chrome once, then try again.",
            ErrorCode.TARGET_BLOCKED,
        )
    if response.status == 403:
        raise ToolError(f"{app.NAME} refused the request (403).", ErrorCode.TARGET_BLOCKED)


@dataclass(frozen=True)
class Profile:
    """What tools may know about the browser the session came from."""

    # One local session per server, so one id: it keys per-account cache entries.
    browser_id: str = "local"


@dataclass
class ToolContext:
    session: Session
    timeout_s: float = 30.0
    _cache: dict[str, tuple[float, str]] = field(default_factory=dict, repr=False)
    _http: AsyncSession | None = field(default=None, repr=False)

    @property
    def profile(self) -> Profile:
        """`ctx.profile` of the hosted tools: here only the cache key of the one local session."""
        return Profile()

    def _client(self) -> AsyncSession:
        if self._http is None:
            headers = {"accept-language": self.session.locale or "en-US,en;q=0.9"}
            target = impersonate_target(self.session.chrome_major)
            # The browser's own user agent only when the TLS fingerprint matches its version.
            if self.session.user_agent and target != "chrome":
                headers["user-agent"] = self.session.user_agent
            self._http = AsyncSession(impersonate=target, proxy=self.session.proxy or None, headers=headers)  # pyright: ignore[reportArgumentType] - target is a BrowserType value
            for cookie in self.session.cookies:
                self._http.cookies.set(
                    cookie["name"], cookie["value"], domain=cookie["domain"], path=cookie.get("path", "/")
                )
        return self._http

    async def call(self, method: str, url: str, **kwargs: Any) -> HttpResponse:
        """One request to the app with your cookies. A signed-out answer raises auth_expired.

        Writes to your account settings in the app are refused before they leave (account_guard).
        """
        if not allowed_host(url):
            raise ToolError(f"Request outside {app.DOMAINS[0]}.", ErrorCode.INTERNAL_ERROR)
        check_account_write(method, url)
        client = self._client()
        method = method.upper()
        params, json, data, headers = (
            kwargs.get("params"),
            kwargs.get("json"),
            kwargs.get("data"),
            kwargs.get("headers"),
        )
        for _ in range(_MAX_REDIRECTS + 1):
            try:
                raw = await client.request(
                    method,  # pyright: ignore[reportArgumentType] - an HTTP method name
                    url,
                    params=params,
                    json=json,
                    data=data,
                    headers=headers,
                    timeout=self.timeout_s,
                    allow_redirects=False,
                )
            except Exception as exc:
                raise ToolError(f"{app.NAME} did not answer: {type(exc).__name__}.", ErrorCode.TARGET_ERROR) from exc
            location = raw.headers.get("location")
            if raw.status_code not in _REDIRECTS or not location:
                break
            url = urljoin(str(raw.url), location)
            if not allowed_host(url):
                raise ToolError(f"{app.NAME} redirected outside {app.DOMAINS[0]}.", ErrorCode.TARGET_ERROR)
            params = None
            if raw.status_code == 303 or (raw.status_code in (301, 302) and method == "POST"):
                method, json, data = "GET", None, None
        else:
            raise ToolError("Too many redirects.", ErrorCode.TARGET_ERROR)
        response = HttpResponse(
            status=raw.status_code,
            url=str(raw.url),
            headers={k.lower(): v or "" for k, v in raw.headers.items()},
            text=raw.text,
        )
        _raise_for(response)
        return response

    async def get_json(self, url: str, **kwargs: Any) -> Any:
        return (await self.call("GET", url, **kwargs)).json()

    async def post_json(self, url: str, payload: Any, **kwargs: Any) -> Any:
        return (await self.call("POST", url, json=payload, **kwargs)).json()

    async def cache_get(self, key: str) -> str | None:
        """Short-lived app data (a build id, a page token), kept in this process."""
        entry = self._cache.get(key)
        if entry is None or entry[0] < time.monotonic():
            return None
        return entry[1]

    async def cache_set(self, key: str, value: str, ttl_s: int) -> None:
        self._cache[key] = (time.monotonic() + ttl_s, value)

    async def close(self) -> None:
        if self._http is not None:
            await self._http.close()
            self._http = None
