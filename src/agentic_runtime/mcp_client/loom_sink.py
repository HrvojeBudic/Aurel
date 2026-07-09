"""
loom_sink.py — the one path external MCP output enters context (B6).

An external tool result is tainted DATA; it reaches an entity's context only as a
ContextLoom ``ContextItem`` (``SourceKind.MCP_TOOL``) — instruction-ineligible and
rendered fenced as untrusted data (F4). Binary content is already reduced to
bytes-free descriptors by B2, so nothing raw leaks here either.
"""
from __future__ import annotations

from typing import Any

from ..context_loom import ContextItem, make_context_item
from ..external_ingress import SourceKind


def sink_tool_result(result: Any, server_name: str) -> ContextItem:
    """Turn a ToolCallResult into a DATA-only ContextLoom item."""
    return make_context_item(result.text(), SourceKind.MCP_TOOL, origin_ref=server_name)
