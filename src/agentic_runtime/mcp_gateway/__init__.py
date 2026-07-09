"""
mcp_gateway — Aurel as a governed MCP server (F3.3).

External MCP clients (a Claude Code session, another agent) reach Aurel's tools
only through ``McpGateway``: every ``tools/call`` is tainted MCP_CLIENT, must be
explicitly exposed + contracted, is floor-checked against the executor's trust
ceiling, preflighted through the F3.1 gate, executed under a lease via the real
``runtime.submit`` kernel, and its outcome written to the executor's governed
track record. This is where an F3.1 preflight becomes real execution.

The umbrella flag ``AUREL_MCP_GATEWAY`` is defined here. In F3.3 the gateway is
opt-in by construction (nothing wires it into the default runtime), so the flag
is defined-not-gating; it becomes load-bearing when a transport is stood up.
"""
from __future__ import annotations

import os

from .jsonrpc import (
    GATEWAY_DENIED,
    JsonRpcError,
    JsonRpcRequest,
    error,
    parse_request,
    success,
)
from .server import GATEWAY_VERSION, MCP_PROTOCOL_VERSION, McpGateway
from .tool_registry import (
    DEFAULT_EXTERNAL_FLOOR,
    ExposedTool,
    GatewayToolRegistry,
)

_FLAG = "AUREL_MCP_GATEWAY"


def flag_enabled() -> bool:
    """True iff the MCP-gateway flag is explicitly enabled (default OFF)."""
    return os.environ.get(_FLAG, "").strip() in ("1", "true", "TRUE", "on")


__all__ = [
    "McpGateway",
    "MCP_PROTOCOL_VERSION",
    "GATEWAY_VERSION",
    "GatewayToolRegistry",
    "ExposedTool",
    "DEFAULT_EXTERNAL_FLOOR",
    "JsonRpcRequest",
    "JsonRpcError",
    "parse_request",
    "success",
    "error",
    "GATEWAY_DENIED",
    "flag_enabled",
]
