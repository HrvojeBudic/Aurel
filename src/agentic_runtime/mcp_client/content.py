"""
content.py — MCP tool-result content model (B2).

An MCP ``tools/call`` returns a ``content`` array of typed blocks (text / image /
audio / resource / resource_link) plus ``isError`` and optional
``structuredContent``. This parses them into typed, provenance-labelled values:

  - **Text** (and text-bearing resources) becomes ``TaintedContent(MCP_TOOL)`` —
    instruction-ineligible (F3.0), the only thing that ever reaches context.
  - **Binary** (image / audio / blob resource) never enters context as bytes: it
    is reduced to a **descriptor** (mime, encoded length, content ref hash). The
    raw base64 is dropped at the boundary.
  - An **unknown** block type fails *open into UNKNOWN* (never raises) — a hostile
    server cannot crash the parse with a novel block.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional

from ..external_ingress import SourceKind, TaintedContent, make_tainted


class ContentKind(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    RESOURCE = "resource"
    RESOURCE_LINK = "resource_link"
    UNKNOWN = "unknown"


_BINARY_KINDS = {ContentKind.IMAGE, ContentKind.AUDIO}


def _ref(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8", errors="surrogatepass")).hexdigest()[:16]


@dataclass(frozen=True)
class ContentBlock:
    """One parsed content block. Text is tainted; binary is a descriptor only."""

    kind: ContentKind
    tainted: TaintedContent            # provenance for text, or a descriptor for binary
    mime_type: Optional[str] = None
    uri: Optional[str] = None
    data_ref: Optional[str] = None     # hash of binary payload (never the bytes)
    encoded_len: int = 0

    @property
    def instruction_eligible(self) -> bool:
        return self.tainted.instruction_eligible  # always False (MCP_TOOL)

    def render(self) -> str:
        """A context-safe string: text as-is, binary as a bytes-free descriptor."""
        if self.kind is ContentKind.TEXT:
            return self.tainted.content
        if self.kind is ContentKind.RESOURCE and self.data_ref is None:
            return self.tainted.content        # text resource
        if self.kind is ContentKind.RESOURCE_LINK:
            return f"[resource_link {self.uri or ''} {self.mime_type or ''}]".strip()
        # binary / blob resource
        return (
            f"[{self.kind.value} {self.mime_type or 'application/octet-stream'} "
            f"{self.encoded_len}b ref:{self.data_ref}]"
        )

    def to_dict(self) -> dict:
        return {
            "kind": self.kind.value,
            "mime_type": self.mime_type,
            "uri": self.uri,
            "data_ref": self.data_ref,
            "encoded_len": self.encoded_len,
            "instruction_eligible": self.instruction_eligible,
            "provenance": self.tainted.to_dict(),
        }


def parse_content_block(block: Any, origin_ref: str) -> ContentBlock:
    """Parse one MCP content block. Never raises on a hostile/unknown shape."""
    if not isinstance(block, dict):
        return ContentBlock(
            kind=ContentKind.UNKNOWN,
            tainted=make_tainted("[non-object content block]", SourceKind.MCP_TOOL, origin_ref),
        )
    btype = block.get("type")

    if btype == "text":
        text = str(block.get("text", ""))
        return ContentBlock(ContentKind.TEXT, make_tainted(text, SourceKind.MCP_TOOL, origin_ref))

    if btype in ("image", "audio"):
        data = str(block.get("data", ""))
        mime = block.get("mimeType")
        kind = ContentKind.IMAGE if btype == "image" else ContentKind.AUDIO
        desc = f"[{btype} {mime or '?'} {len(data)}b]"
        return ContentBlock(
            kind=kind,
            tainted=make_tainted(desc, SourceKind.MCP_TOOL, origin_ref),
            mime_type=mime,
            data_ref=_ref(data),
            encoded_len=len(data),
        )

    if btype == "resource":
        res = block.get("resource") or {}
        uri = res.get("uri")
        mime = res.get("mimeType")
        if "text" in res:
            return ContentBlock(
                ContentKind.RESOURCE,
                make_tainted(str(res.get("text", "")), SourceKind.MCP_TOOL, origin_ref),
                mime_type=mime,
                uri=uri,
            )
        blob = str(res.get("blob", ""))
        return ContentBlock(
            ContentKind.RESOURCE,
            make_tainted(f"[resource blob {uri or '?'} {len(blob)}b]", SourceKind.MCP_TOOL, origin_ref),
            mime_type=mime,
            uri=uri,
            data_ref=_ref(blob),
            encoded_len=len(blob),
        )

    if btype == "resource_link":
        uri = block.get("uri")
        return ContentBlock(
            ContentKind.RESOURCE_LINK,
            make_tainted(f"[resource_link {uri or '?'}]", SourceKind.MCP_TOOL, origin_ref),
            mime_type=block.get("mimeType"),
            uri=uri,
        )

    return ContentBlock(
        ContentKind.UNKNOWN,
        make_tainted(f"[unknown content type {btype!r}]", SourceKind.MCP_TOOL, origin_ref),
    )


@dataclass(frozen=True)
class ToolCallResult:
    """A parsed MCP tools/call result. All text is tainted (instruction-ineligible)."""

    content: tuple[ContentBlock, ...]
    is_error: bool
    structured: Optional[dict] = None

    def text(self) -> str:
        """Context-safe rendering: text inline, binary as bytes-free descriptors."""
        return "\n".join(b.render() for b in self.content)

    @property
    def has_binary(self) -> bool:
        return any(b.kind in _BINARY_KINDS or b.data_ref is not None for b in self.content)

    def to_dict(self) -> dict:
        return {
            "is_error": self.is_error,
            "has_binary": self.has_binary,
            "structured": self.structured,
            "content": [b.to_dict() for b in self.content],
        }


def parse_tool_result(result: Any, origin_ref: str) -> ToolCallResult:
    """Parse a tools/call ``result`` object. Fail-closed on shape, never raises."""
    if not isinstance(result, dict):
        return ToolCallResult(content=(), is_error=True)
    raw = result.get("content")
    blocks = raw if isinstance(raw, list) else []
    content = tuple(parse_content_block(b, origin_ref) for b in blocks)
    structured = result.get("structuredContent")
    return ToolCallResult(
        content=content,
        is_error=bool(result.get("isError", False)),
        structured=structured if isinstance(structured, dict) else None,
    )
