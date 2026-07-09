"""
compression.py — F4.1 deterministic, provenance-preserving context compression.

When a high-priority context item is too large to fit a token budget whole, the
ContextLoom compresses it to fit rather than dropping it entirely. Compression
here is **extractive truncation** — a deterministic head+tail slice with a
middle-elision marker — NOT semantic summarization (no model call). It is
labelled honestly as ``TRUNCATE_HEAD_TAIL`` so nothing overclaims an AI summary.

Every compression is recorded (`CompressionRecord`: what was elided) — no silent
loss. Provenance is preserved: the compressed item keeps its source kind, origin
ref, priority, taint label, and instruction-eligibility; only the content shrinks
(so it gets a fresh content hash, with the original hash retained in the record).
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .context_item import ContextItem, make_context_item

# Below this budget there is no room for a meaningful head+tail+marker slice, so
# the caller drops the item instead of compressing it to garbage.
MIN_COMPRESS_TOKENS = 8

# Fixed marker (no embedded count → no circular length dependency).
_MARKER = "\n…[elided]…\n"


class CompressionMethod(str, Enum):
    NONE = "none"
    TRUNCATE_HEAD_TAIL = "truncate_head_tail"


@dataclass(frozen=True)
class CompressionRecord:
    """Evidence that one item was compressed. No silent loss."""

    original_hash: str
    original_tokens: int
    kept_tokens: int
    elided_tokens: int
    method: CompressionMethod

    def to_dict(self) -> dict:
        return {
            "original_hash": self.original_hash,
            "original_tokens": self.original_tokens,
            "kept_tokens": self.kept_tokens,
            "elided_tokens": self.elided_tokens,
            "method": self.method.value,
        }


def compress_item(
    item: ContextItem, max_tokens: int
) -> tuple[ContextItem, CompressionRecord]:
    """Truncate an item's content (head+tail) to fit ``max_tokens``. Deterministic.

    If the item already fits, it is returned unchanged with a NONE record. The
    caller guarantees ``max_tokens >= MIN_COMPRESS_TOKENS`` for the truncating
    path; provenance (kind/origin/priority/label/eligibility) is preserved.
    """
    if item.est_tokens <= max_tokens:
        return item, CompressionRecord(
            original_hash=item.content_hash,
            original_tokens=item.est_tokens,
            kept_tokens=item.est_tokens,
            elided_tokens=0,
            method=CompressionMethod.NONE,
        )

    budget_chars = max_tokens * 4
    content_budget = max(0, budget_chars - len(_MARKER))
    head_len = (content_budget + 1) // 2
    tail_len = content_budget // 2
    content = item.content
    kept = content[:head_len] + _MARKER + (content[-tail_len:] if tail_len else "")

    new_item = make_context_item(
        kept, item.source_kind, item.origin_ref, priority=item.priority
    )
    return new_item, CompressionRecord(
        original_hash=item.content_hash,
        original_tokens=item.est_tokens,
        kept_tokens=new_item.est_tokens,
        elided_tokens=max(0, item.est_tokens - new_item.est_tokens),
        method=CompressionMethod.TRUNCATE_HEAD_TAIL,
    )
