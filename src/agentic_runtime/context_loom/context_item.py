"""
context_item.py — one provenance-bearing unit of assembled context (F4.0).

A ``ContextItem`` carries not just text but *where it came from* (F3.0
``SourceKind``) and therefore whether it may be presented to the model as an
instruction. External-origin items (an MCP tool result, a scraped page, an
external executor's payload) are **data-only** — instruction-ineligible by
provenance, exactly as in F3.0 — no matter how a scan reads. The ContextLoom
renders them clearly fenced as untrusted data; it never lets them speak as
instructions.

Deterministic and stdlib-only: content hashes are sha256, token counts are an
honest char/4 estimate (labelled as such — not a real tokenizer).
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass

from ..external_ingress import EXTERNAL_ORIGIN_KINDS, SourceKind, TaintLabel
from ..external_ingress.taint import TRUSTED_ORIGIN_KINDS

# Default assembly priority per origin: trusted/operator high, external low.
_DEFAULT_PRIORITY: dict[SourceKind, int] = {
    SourceKind.OPERATOR: 100,
    SourceKind.INTERNAL: 80,
    SourceKind.MODEL_OUTPUT: 70,
    SourceKind.MCP_TOOL: 40,
    SourceKind.MCP_CLIENT: 40,
    SourceKind.NETWORK_FETCH: 30,
    SourceKind.SCRAPE: 20,
    SourceKind.A2A_MESSAGE: 20,
    SourceKind.EXTERNAL_EXECUTOR: 20,
    SourceKind.UNKNOWN: 10,
}


def estimate_tokens(text: str) -> int:
    """Honest char/4 token estimate. Deterministic; NOT a real tokenizer."""
    return max(1, len(text) // 4)


def _hash(*parts: str) -> str:
    h = hashlib.sha256()
    for p in parts:
        h.update(p.encode("utf-8", errors="surrogatepass"))
        h.update(b"\x00")
    return h.hexdigest()


def _label_for(source_kind: SourceKind) -> TaintLabel:
    return TaintLabel.TRUSTED if source_kind in TRUSTED_ORIGIN_KINDS else TaintLabel.UNTRUSTED


@dataclass(frozen=True)
class ContextItem:
    """A provenance-labelled piece of context. Frozen and content-addressed."""

    content: str
    source_kind: SourceKind
    origin_ref: str
    priority: int
    label: TaintLabel
    content_hash: str
    est_tokens: int

    @property
    def is_external_origin(self) -> bool:
        return self.source_kind in EXTERNAL_ORIGIN_KINDS

    @property
    def instruction_eligible(self) -> bool:
        """External origin is never instruction-eligible (F3.0 doctrine)."""
        return not self.is_external_origin

    def to_dict(self) -> dict:
        return {
            "source_kind": self.source_kind.value,
            "origin_ref": self.origin_ref,
            "priority": self.priority,
            "label": self.label.value,
            "content_hash": self.content_hash,
            "est_tokens": self.est_tokens,
            "instruction_eligible": self.instruction_eligible,
        }


def make_context_item(
    content: str,
    source_kind: SourceKind,
    origin_ref: str,
    priority: int | None = None,
) -> ContextItem:
    """Build a labelled context item. Label is derived from provenance alone."""
    prio = _DEFAULT_PRIORITY.get(source_kind, 10) if priority is None else priority
    return ContextItem(
        content=content,
        source_kind=source_kind,
        origin_ref=origin_ref,
        priority=prio,
        label=_label_for(source_kind),
        content_hash=_hash(source_kind.value, content),
        est_tokens=estimate_tokens(content),
    )
