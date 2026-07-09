"""
mcp_client — F4B: Aurel as an MCP *client* (direction B — Aurel calls OUT).

A real, protocol-compliant MCP client: connect to an external MCP server (stdio
or Streamable HTTP), run the initialize handshake, discover and call tools, and
feed each result — as tainted DATA (F3.0) — through the ContextLoom sink (F4) into
governed context. Security is inherited, not rebuilt: external output is
``TaintedContent`` (never instruction), every bridged tool carries a
``ToolContract`` and runs through ``runtime.submit`` (the same gate that already
protects everything), and outbound args are redacted (F2).

The umbrella flag ``AUREL_MCP_CLIENT`` is defined here (default OFF). The client
is opt-in by construction; the flag becomes load-bearing when a live server is
configured.
"""
from __future__ import annotations

import os

from .client import (
    InitializeResult,
    McpCallError,
    McpClient,
    McpToolDescriptor,
)
from .bridge import (
    McpBridge,
    bridged_name,
    json_schema_to_argspecs,
    json_schema_to_contract,
)
from .content import (
    ContentBlock,
    ContentKind,
    ToolCallResult,
    parse_content_block,
    parse_tool_result,
)
from .jsonrpc_client import (
    JsonRpcClientCodec,
    JsonRpcClientError,
    Response,
)
from .transport import (
    DEFAULT_MAX_BYTES,
    DEFAULT_TIMEOUT_S,
    HttpTransport,
    McpTransportError,
    StdioTransport,
    Transport,
    scrub_env,
)

_FLAG = "AUREL_MCP_CLIENT"


def flag_enabled() -> bool:
    """True iff the MCP-client flag is explicitly enabled (default OFF)."""
    return os.environ.get(_FLAG, "").strip() in ("1", "true", "TRUE", "on")


__all__ = [
    "JsonRpcClientCodec",
    "JsonRpcClientError",
    "Response",
    "Transport",
    "StdioTransport",
    "HttpTransport",
    "McpTransportError",
    "scrub_env",
    "DEFAULT_TIMEOUT_S",
    "DEFAULT_MAX_BYTES",
    "ContentBlock",
    "ContentKind",
    "ToolCallResult",
    "parse_content_block",
    "parse_tool_result",
    "McpClient",
    "McpCallError",
    "McpToolDescriptor",
    "InitializeResult",
    "McpBridge",
    "bridged_name",
    "json_schema_to_contract",
    "json_schema_to_argspecs",
    "flag_enabled",
]
