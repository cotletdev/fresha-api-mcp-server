"""The REST API and the MCP endpoint on one port.

- `GET|POST|PUT|PATCH|DELETE <app.API_PREFIX>/<route>`: each tool at its route, the same paths as the
  hosted API at cotlet.dev. Path parts and the query string are arguments; a JSON body adds the rest.
- `POST <app.API_PREFIX>/tools/{name}`: any tool by name, the JSON body is its arguments.
- `GET <app.API_PREFIX>/tools`: every tool with its schema. OpenAPI at `/docs` and `/openapi.json`.
- `/mcp`: the MCP server over streamable HTTP.

With <ENV>_MCP_TOKEN set, every request needs `Authorization: Bearer <token>`.
"""

from __future__ import annotations

import contextlib
import hmac
import json
import os
import re
from collections.abc import AsyncIterator, Awaitable, Callable
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager

from fresha_api_mcp import __version__, app, mcp_server
from fresha_api_mcp.core.errors import HTTP_STATUS, ErrorCode, ToolError
from fresha_api_mcp.core.tools import ToolSpec
from fresha_api_mcp.runner import Runner, description, tools

PREFIX = app.API_PREFIX
ASGI = Callable[[dict[str, Any], Callable[[], Awaitable[Any]], Callable[[Any], Awaitable[None]]], Awaitable[None]]


def _error(code: ErrorCode, message: str) -> JSONResponse:
    return JSONResponse({"error": code.value, "message": message}, status_code=HTTP_STATUS.get(code, 500))


def _typed(value: str, schema: dict[str, Any]) -> Any:
    kind = schema.get("type")
    try:
        if kind == "integer":
            return int(value)
        if kind == "number":
            return float(value)
    except ValueError:
        return value
    if kind == "boolean":
        return value.lower() in ("1", "true", "yes", "on")
    if kind == "array":
        return [_typed(v, schema.get("items") or {}) for v in value.split(",") if v]
    if kind == "object":
        with contextlib.suppress(ValueError):
            return json.loads(value)
    return value


def _route_order(spec: ToolSpec) -> list[int]:
    """Literal segments before {placeholders}, so /groups/discover wins over /groups/{group}."""
    path = (spec.route or "").split(" ", 1)[1]
    return [1 if part.startswith("{") else 0 for part in path.strip("/").split("/")]


def _tag(path: str) -> str:
    """OpenAPI group: the part after /groups/{group}/ (posts, members ...), else the first part."""
    parts = path.strip("/").split("/")
    return parts[2] if parts[:2] == ["groups", "{group}"] and len(parts) > 2 else parts[0]


def _openapi(spec: ToolSpec, method: str, path: str) -> dict[str, Any]:
    props: dict[str, Any] = spec.input_schema.get("properties") or {}
    required = set(spec.input_schema.get("required") or [])
    in_path = set(re.findall(r"\{(\w+)\}", path))
    parameters = [
        {"name": name, "in": "path", "required": True, "schema": props.get(name, {"type": "string"})}
        for name in in_path
    ]
    rest = {k: v for k, v in props.items() if k not in in_path}
    extra: dict[str, Any] = {}
    if method == "GET":
        parameters += [
            {"name": name, "in": "query", "required": name in required, "schema": schema}
            for name, schema in rest.items()
        ]
    elif rest:
        body = {"type": "object", "properties": rest, "required": sorted(required - in_path)}
        extra["requestBody"] = {"required": bool(body["required"]), "content": {"application/json": {"schema": body}}}
    if spec.example_response:
        extra["responses"] = {
            "200": {"description": "OK", "content": {"application/json": {"example": spec.example_response}}}
        }
    return {"parameters": parameters, **extra}


async def _arguments(request: Request, spec: ToolSpec) -> dict[str, Any]:
    props: dict[str, Any] = spec.input_schema.get("properties") or {}
    args: dict[str, Any] = {}
    if request.method != "GET":
        raw = await request.body()
        if raw.strip():
            try:
                body = json.loads(raw)
            except ValueError:
                raise ToolError("The body must be a JSON object.", ErrorCode.INVALID_INPUT) from None
            if not isinstance(body, dict):
                raise ToolError("The body must be a JSON object.", ErrorCode.INVALID_INPUT)
            args.update(body)
    for name in request.query_params:
        values = request.query_params.getlist(name)
        schema = props.get(name) or {}
        args[name] = (
            [_typed(v, schema.get("items") or {}) for v in values]
            if schema.get("type") == "array" and len(values) > 1
            else _typed(values[-1], schema)
        )
    for name, value in request.path_params.items():
        args[name] = _typed(value, props.get(name) or {})
    return args


def create_app(runner: Runner) -> ASGI:
    manager = StreamableHTTPSessionManager(app=mcp_server.build(runner), json_response=True, stateless=True)
    token = os.environ.get(f"{app.ENV}_MCP_TOKEN", "").strip()

    @contextlib.asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        async with manager.run():
            yield
        await runner.close()

    api = FastAPI(
        title=f"{app.NAME} API (self-hosted)",
        version=__version__,
        description=f"Your {app.NAME} account as a REST API, run on your machine with your Chrome's session.",
        lifespan=lifespan,
    )

    async def call(spec: ToolSpec, args: dict[str, Any]) -> JSONResponse:
        try:
            result = await runner.run(spec.name, args)
        except ToolError as exc:
            return _error(exc.code, str(exc))
        return JSONResponse(result)

    def endpoint(spec: ToolSpec) -> Callable[[Request], Awaitable[JSONResponse]]:
        async def handle(request: Request) -> JSONResponse:
            try:
                args = await _arguments(request, spec)
            except ToolError as exc:
                return _error(exc.code, str(exc))
            return await call(spec, args)

        return handle

    @api.get(f"{PREFIX}/tools", summary="Every tool with its route and input schema")
    async def list_tools() -> list[dict[str, Any]]:
        return [
            {
                "name": spec.name,
                "title": spec.title,
                "access": spec.access,
                "route": spec.route,
                "description": description(spec),
                "input_schema": spec.input_schema,
                "example_response": spec.example_response,
            }
            for spec in tools(runner.read_only)
        ]

    @api.post(f"{PREFIX}/tools/{{name}}", summary="Call any tool by name; the JSON body is its arguments")
    async def call_by_name(name: str, request: Request) -> JSONResponse:
        raw = await request.body()
        try:
            args = json.loads(raw) if raw.strip() else {}
        except ValueError:
            return _error(ErrorCode.INVALID_INPUT, "The body must be a JSON object.")
        if not isinstance(args, dict):
            return _error(ErrorCode.INVALID_INPUT, "The body must be a JSON object.")
        spec = next((s for s in tools() if s.name == name), None)
        if spec is None:
            return _error(ErrorCode.UNKNOWN_TOOL, f"No tool '{name}'. GET {PREFIX}/tools lists them.")
        return await call(spec, args)

    for spec in sorted(tools(runner.read_only), key=_route_order):
        method, path = (spec.route or "").split(" ", 1)
        api.add_api_route(
            PREFIX + path,
            endpoint(spec),
            methods=[method],
            name=spec.name,
            operation_id=spec.name,
            summary=spec.title,
            description=description(spec),
            tags=[_tag(path)],
            openapi_extra=_openapi(spec, method, path),
        )

    async def asgi(
        scope: dict[str, Any], receive: Callable[[], Awaitable[Any]], send: Callable[[Any], Awaitable[None]]
    ) -> None:
        if scope["type"] == "http" and token:
            sent = dict(scope.get("headers") or []).get(b"authorization", b"").decode()
            if not hmac.compare_digest(sent, f"Bearer {token}"):
                await _error(ErrorCode.AUTH_REQUIRED, f"Send Authorization: Bearer <{app.ENV}_MCP_TOKEN>.")(
                    scope, receive, send
                )
                return
        if scope["type"] == "http" and (scope["path"] == "/mcp" or scope["path"].startswith("/mcp/")):
            await manager.handle_request(scope, receive, send)
            return
        await api(scope, receive, send)

    return asgi
