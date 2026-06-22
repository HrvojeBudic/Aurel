"""Evidence projection contracts bound to canonical AurelTraceLog events."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .trace import TraceEventRef, hash_json


@dataclass(frozen=True)
class EvidenceRef:
    evidence_id: str
    source_trace_event_ref: TraceEventRef
    evidence_type: str
    content_hash: str
    summary: str
    is_canonical: bool = False

    def __post_init__(self) -> None:
        if not self.evidence_id or not self.evidence_id.strip():
            raise ValueError("evidence_id must not be empty")
        if self.source_trace_event_ref is None:
            raise ValueError("EvidenceRef requires source_trace_event_ref")
        if not self.evidence_type or not self.evidence_type.strip():
            raise ValueError("evidence_type must not be empty")
        if not self.content_hash or not self.content_hash.strip():
            raise ValueError("content_hash must not be empty")
        if self.is_canonical:
            raise ValueError("EvidenceRef is a projection and cannot claim canonical status")


def compute_evidence_content_hash(content: Any) -> str:
    return hash_json(content)


def build_evidence_ref(
    *,
    evidence_id: str,
    source_trace_event_ref: TraceEventRef,
    evidence_type: str,
    content: Any,
    summary: str,
) -> EvidenceRef:
    return EvidenceRef(
        evidence_id=evidence_id,
        source_trace_event_ref=source_trace_event_ref,
        evidence_type=evidence_type,
        content_hash=compute_evidence_content_hash(content),
        summary=summary,
        is_canonical=False,
    )


def evidence_ref_to_dict(evidence_ref: EvidenceRef) -> dict[str, object]:
    data: dict[str, object] = asdict(evidence_ref)
    data["source_trace_event_ref"] = asdict(evidence_ref.source_trace_event_ref)
    return data
