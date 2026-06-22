"""Context binding and adequacy contracts for capability evidence."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum


class ContextAdequacyStatus(str, Enum):
    ADEQUATE = "adequate"
    PARTIAL = "partial"
    INSUFFICIENT = "insufficient"
    UNSAFE = "unsafe"


@dataclass(frozen=True)
class ContextBindingRef:
    context_id: str
    context_type: str
    source_refs: tuple[str, ...] = ()
    assumptions: tuple[str, ...] = ()
    created_at: str = ""

    def __post_init__(self) -> None:
        if not self.context_id or not self.context_id.strip():
            raise ValueError("context_id must not be empty")
        if not self.context_type or not self.context_type.strip():
            raise ValueError("context_type must not be empty")
        if not self.created_at or not self.created_at.strip():
            raise ValueError("created_at must not be empty")


@dataclass(frozen=True)
class ContextAdequacyReport:
    context_adequacy_id: str
    context_binding_ref: ContextBindingRef
    status: ContextAdequacyStatus
    missing_context_flags: tuple[str, ...] = ()
    stale_context_flags: tuple[str, ...] = ()
    contradicted_context_flags: tuple[str, ...] = ()
    uncertainty_notes: tuple[str, ...] = ()
    safe_to_act: bool = True
    requires_operator_clarification: bool = False
    created_at: str = ""
    adequacy_score: float | None = None

    def __post_init__(self) -> None:
        if not self.context_adequacy_id or not self.context_adequacy_id.strip():
            raise ValueError("context_adequacy_id must not be empty")
        if self.context_binding_ref is None:
            raise ValueError("context_binding_ref is required")
        if not self.created_at or not self.created_at.strip():
            raise ValueError("created_at must not be empty")
        if self.status == ContextAdequacyStatus.UNSAFE and self.safe_to_act:
            raise ValueError("unsafe context requires safe_to_act=false")
        if (
            self.status == ContextAdequacyStatus.INSUFFICIENT
            and not self.requires_operator_clarification
        ):
            raise ValueError(
                "insufficient context requires operator clarification or explicit justification"
            )
        if self.adequacy_score is not None and not 0.0 <= self.adequacy_score <= 1.0:
            raise ValueError("adequacy_score must be between 0.0 and 1.0")


def context_binding_ref_to_dict(ref: ContextBindingRef) -> dict[str, object]:
    data: dict[str, object] = asdict(ref)
    data["source_refs"] = list(ref.source_refs)
    data["assumptions"] = list(ref.assumptions)
    return data


def context_adequacy_report_to_dict(report: ContextAdequacyReport) -> dict[str, object]:
    return {
        "context_adequacy_id": report.context_adequacy_id,
        "context_binding_ref": context_binding_ref_to_dict(report.context_binding_ref),
        "status": report.status.value,
        "missing_context_flags": list(report.missing_context_flags),
        "stale_context_flags": list(report.stale_context_flags),
        "contradicted_context_flags": list(report.contradicted_context_flags),
        "uncertainty_notes": list(report.uncertainty_notes),
        "safe_to_act": report.safe_to_act,
        "requires_operator_clarification": report.requires_operator_clarification,
        "created_at": report.created_at,
        "adequacy_score": report.adequacy_score,
    }
