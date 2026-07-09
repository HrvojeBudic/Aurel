"""
client.py — the MCP protocol client (B3).

Drives the real MCP lifecycle over an injectable ``Transport``:

  initialize (protocolVersion + capabilities + clientInfo) → server reply →
  ``notifications/initialized`` → operate (tools / resources / prompts) → close.

Everything the server returns is external: tool *descriptions* are tainted
(``MCP_TOOL``) just like tool *output*, and every ``call_tool`` result is parsed
by B2 (text tainted + instruction-ineligible, binary bytes-free). Calls are
**capability-gated** (no call to a surface the server did not advertise) and
**fail-closed** (a JSON-RPC error or an off-spec reply raises ``McpCallError``,
never a fabricated result). Outbound arguments are scrubbed of registered
secrets before they leave (``redact_known``, exact-match — legit args untouched).
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Optional

from ..external_ingress import SourceKind, TaintedContent, make_tainted
from .content import ToolCallResult, parse_content_block, parse_tool_result
from .jsonrpc_client import JsonRpcClientCodec, JsonRpcClientError
from .transport import McpTransportError, Transport

PROTOCOL_VERSION = "2025-06-18"
DEFAULT_CLIENT_INFO = {"name": "aurel", "version": "f4b.v1"}
_MAX_PAGES = 100
_MAX_INTERLEAVED = 200


class McpCallError(RuntimeError):
    """A failed MCP call: JSON-RPC error, off-spec reply, or capability gate."""


@dataclass(frozen=True)
class InitializeResult:
    protocol_version: str
    server_name: str
    capabilities: dict


@dataclass(frozen=True)
class McpToolDescriptor:
    """A discovered tool. name/schema are control values; description is tainted."""

    name: str
    description: TaintedContent
    input_schema: dict
    descriptor_hash: str
    raw: dict

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description_ref": self.description.content_hash,
            "input_schema": self.input_schema,
            "descriptor_hash": self.descriptor_hash,
        }


def _descriptor_hash(name: str, description: str, input_schema: Any) -> str:
    payload = json.dumps(
        {"name": name, "description": description, "inputSchema": input_schema},
        sort_keys=True, default=str,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class McpClient:
    """One initialized session against one external MCP server."""

    def __init__(
        self,
        transport: Transport,
        server_name: str,
        *,
        redactor: Any = None,
        client_info: Optional[dict] = None,
    ) -> None:
        self._transport = transport
        self.server_name = server_name
        self._redactor = redactor
        self._client_info = client_info or DEFAULT_CLIENT_INFO
        self._codec = JsonRpcClientCodec()
        self._initialized = False
        self._capabilities: dict = {}
        self._negotiated_version = ""

    # ----------------------------------------------------------------- #
    def _request(self, method: str, params: Optional[dict] = None) -> Any:
        rid, msg = self._codec.build_request(method, params)
        try:
            self._transport.send(msg)
        except McpTransportError as e:
            raise McpCallError(f"{method}: transport send failed: {e}")
        for _ in range(_MAX_INTERLEAVED):
            try:
                raw = self._transport.receive()
            except McpTransportError as e:
                raise McpCallError(f"{method}: transport receive failed: {e}")
            if "id" not in raw:          # a server-originated notification — skip
                continue
            try:
                resp = self._codec.correlate(raw)
            except JsonRpcClientError as e:
                raise McpCallError(f"{method}: {e}")
            if resp.id != rid:           # a stray/mismatched response — skip
                continue
            if resp.is_error:
                assert resp.error is not None
                raise McpCallError(f"{method} failed: {resp.error.message}")
            return resp.result
        raise McpCallError(f"{method}: no matching response")

    def _notify(self, method: str, params: Optional[dict] = None) -> None:
        self._transport.send(self._codec.build_notification(method, params))

    def _require_capability(self, cap: str) -> None:
        if not self._initialized:
            raise McpCallError("client not initialized")
        if cap not in self._capabilities:
            raise McpCallError(f"server does not advertise capability '{cap}'")

    def _redact_args(self, args: dict) -> dict:
        if self._redactor is None:
            return dict(args)
        return {
            k: (self._redactor.redact_known(v) if isinstance(v, str) else v)
            for k, v in args.items()
        }

    # ----------------------------------------------------------------- #
    def initialize(self) -> InitializeResult:
        result = self._request("initialize", {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {},
            "clientInfo": self._client_info,
        })
        if not isinstance(result, dict) or "protocolVersion" not in result:
            raise McpCallError("initialize: server returned no protocolVersion")
        caps = result.get("capabilities")
        self._capabilities = caps if isinstance(caps, dict) else {}
        self._negotiated_version = str(result["protocolVersion"])
        server_info = result.get("serverInfo") or {}
        self._initialized = True
        self._notify("notifications/initialized")
        return InitializeResult(
            protocol_version=self._negotiated_version,
            server_name=str(server_info.get("name", self.server_name)),
            capabilities=dict(self._capabilities),
        )

    def list_tools(self) -> list[McpToolDescriptor]:
        self._require_capability("tools")
        out: list[McpToolDescriptor] = []
        cursor: Optional[str] = None
        for _ in range(_MAX_PAGES):
            params = {"cursor": cursor} if cursor else {}
            result = self._request("tools/list", params)
            if not isinstance(result, dict):
                raise McpCallError("tools/list: off-spec result")
            for t in result.get("tools", []) or []:
                if not isinstance(t, dict):
                    continue
                name = str(t.get("name", ""))
                desc = str(t.get("description", ""))
                schema = t.get("inputSchema") or {}
                out.append(McpToolDescriptor(
                    name=name,
                    description=make_tainted(desc, SourceKind.MCP_TOOL, self.server_name),
                    input_schema=schema if isinstance(schema, dict) else {},
                    descriptor_hash=_descriptor_hash(name, desc, schema),
                    raw=t,
                ))
            cursor = result.get("nextCursor")
            if not cursor:
                break
        return out

    def call_tool(self, name: str, arguments: Optional[dict] = None) -> ToolCallResult:
        self._require_capability("tools")
        result = self._request("tools/call", {
            "name": name,
            "arguments": self._redact_args(arguments or {}),
        })
        return parse_tool_result(result, origin_ref=self.server_name)

    def list_resources(self) -> list[dict]:
        self._require_capability("resources")
        result = self._request("resources/list", {})
        if not isinstance(result, dict):
            raise McpCallError("resources/list: off-spec result")
        return [r for r in (result.get("resources", []) or []) if isinstance(r, dict)]

    def read_resource(self, uri: str) -> ToolCallResult:
        self._require_capability("resources")
        result = self._request("resources/read", {"uri": uri})
        contents = result.get("contents", []) if isinstance(result, dict) else []
        blocks = tuple(
            parse_content_block({"type": "resource", "resource": c}, self.server_name)
            for c in contents if isinstance(c, dict)
        )
        return ToolCallResult(content=blocks, is_error=False)

    def list_prompts(self) -> list[dict]:
        self._require_capability("prompts")
        result = self._request("prompts/list", {})
        if not isinstance(result, dict):
            raise McpCallError("prompts/list: off-spec result")
        return [p for p in (result.get("prompts", []) or []) if isinstance(p, dict)]

    def ping(self) -> bool:
        self._request("ping", {})
        return True

    def close(self) -> None:
        self._transport.close()

    @property
    def capabilities(self) -> dict:
        return dict(self._capabilities)

    @property
    def initialized(self) -> bool:
        return self._initialized
