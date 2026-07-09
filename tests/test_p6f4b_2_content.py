"""F4B / B2 seal — MCP tool-result content model.

  1. Text (and text resources) → tainted MCP_TOOL, instruction-ineligible.
  2. Binary (image/audio/blob) never enters context as bytes — descriptor only.
  3. isError honored; structuredContent captured.
  4. Unknown / hostile block shapes fail open into UNKNOWN, never raise.
  5. Deterministic.
"""
from __future__ import annotations

from agentic_runtime.mcp_client import (
    ContentKind,
    parse_content_block,
    parse_tool_result,
)
from agentic_runtime.external_ingress import SourceKind, TaintLabel

SECRET_B64 = "QUJDRA=="  # some base64-looking blob


def _text(t):
    return {"type": "text", "text": t}


# --------------------------------------------------------------------------- #
# 1. Text is tainted + ineligible.
# --------------------------------------------------------------------------- #
def test_text_block_is_tainted_ineligible():
    b = parse_content_block(_text("hello from tool"), "srv")
    assert b.kind is ContentKind.TEXT
    assert b.instruction_eligible is False
    assert b.tainted.source_kind is SourceKind.MCP_TOOL
    assert b.tainted.label is TaintLabel.UNTRUSTED
    assert b.render() == "hello from tool"


def test_text_resource_is_text():
    b = parse_content_block(
        {"type": "resource", "resource": {"uri": "file://x", "text": "body"}}, "srv"
    )
    assert b.kind is ContentKind.RESOURCE
    assert b.render() == "body"
    assert b.instruction_eligible is False


# --------------------------------------------------------------------------- #
# 2. Binary never leaks bytes into context.
# --------------------------------------------------------------------------- #
def test_image_is_descriptor_not_bytes():
    b = parse_content_block(
        {"type": "image", "data": SECRET_B64, "mimeType": "image/png"}, "srv"
    )
    assert b.kind is ContentKind.IMAGE
    assert b.data_ref is not None and len(b.data_ref) == 16
    rendered = b.render()
    assert SECRET_B64 not in rendered        # raw base64 never rendered
    assert "image/png" in rendered and "ref:" in rendered
    assert SECRET_B64 not in str(b.to_dict())


def test_blob_resource_is_descriptor():
    b = parse_content_block(
        {"type": "resource", "resource": {"uri": "x", "blob": SECRET_B64,
                                          "mimeType": "application/pdf"}}, "srv"
    )
    assert b.data_ref is not None
    assert SECRET_B64 not in b.render()


# --------------------------------------------------------------------------- #
# 3. Result-level.
# --------------------------------------------------------------------------- #
def test_tool_result_error_and_structured():
    res = parse_tool_result(
        {"content": [_text("a")], "isError": True, "structuredContent": {"k": 1}}, "srv"
    )
    assert res.is_error is True
    assert res.structured == {"k": 1}
    assert res.text() == "a"


def test_tool_result_mixed_text_and_binary():
    res = parse_tool_result(
        {"content": [_text("summary:"),
                     {"type": "image", "data": SECRET_B64, "mimeType": "image/png"}]},
        "srv",
    )
    assert res.has_binary is True
    text = res.text()
    assert "summary:" in text
    assert SECRET_B64 not in text            # binary bytes-free in the sink text


# --------------------------------------------------------------------------- #
# 4. Hostile / unknown never raises.
# --------------------------------------------------------------------------- #
def test_unknown_block_fails_open():
    assert parse_content_block({"type": "quantum"}, "s").kind is ContentKind.UNKNOWN
    assert parse_content_block("not a dict", "s").kind is ContentKind.UNKNOWN
    assert parse_content_block(12345, "s").kind is ContentKind.UNKNOWN


def test_malformed_result_fails_closed_to_error():
    res = parse_tool_result("not a dict", "s")
    assert res.is_error is True
    assert res.content == ()


# --------------------------------------------------------------------------- #
# 5. Deterministic.
# --------------------------------------------------------------------------- #
def test_deterministic():
    a = parse_tool_result({"content": [_text("x")]}, "s").to_dict()
    b = parse_tool_result({"content": [_text("x")]}, "s").to_dict()
    assert a == b
