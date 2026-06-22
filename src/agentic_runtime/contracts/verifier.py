"""Verifier result contracts with normalization support.

P1.5.13 normalizes verifier outputs so that every VerifierResult is
trace-bound, evidence-bound, reasoned, confidence-scored, and limitation-bound.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum

from .evidence import EvidenceRef, evidence_ref_to_dict
from .trace import TraceEventRef


class VerifierKind(str, Enum):
    """What kind of verification produced this result."""
    DETERMINISTIC = "deterministic"
    OPERATOR_REVIEW = "operator_review"
    POLICY_CHECK = "policy_check"
    LLM_JUDGE_STUB = "llm_judge_stub"
    CONTEXT_ADEQUACY = "context_adequacy"
    EVIDENCE_INTEGRITY = "evidence_integrity"


class VerifierResultStatus(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    NEEDS_REVIEW = "needs_review"
    INCONCLUSIVE = "inconclusive"


class NormalizationStatus(str, Enum):
    NORMALIZED = "normalized"
    FAILED = "failed"
    NEEDS_REVIEW = "needs_review"


@dataclass(frozen=True)
class VerifierResult:
    verifier_id: str
    verifier_kind: VerifierKind
    target_ref: str
    status: VerifierResultStatus
    confidence: float
    reason: str
    limitations: tuple[str, ...]
    evidence_refs: tuple[EvidenceRef, ...]
    source_trace_event_ref: TraceEventRef
    normalized_from: str | None = None
    created_at: str = ""

    def __post_init__(self) -> None:
        if not self.verifier_id or not self.verifier_id.strip():
            raise ValueError("verifier_id must not be empty")
        if not self.target_ref or not self.target_ref.strip():
            raise ValueError("target_ref must not be empty")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")
        if not self.reason or not self.reason.strip():
            raise ValueError("reason must not be empty")
        if not self.limitations:
            raise ValueError("VerifierResult limitations must be non-empty")
        if self.status == VerifierResultStatus.PASS and not self.evidence_refs:
            raise ValueError("status=pass requires evidence_refs")
        if self.source_trace_event_ref is None:
            raise ValueError("VerifierResult requires source_trace_event_ref")


@dataclass(frozen=True)
class VerifierNormalizationReport:
    normalization_id: str
    verifier_kind: VerifierKind
    raw_input_ref: str | None
    normalized_verifier_result_ref: str | None
    normalization_status: NormalizationStatus
    reason: str
    warnings: tuple[str, ...]
    errors: tuple[str, ...]
    created_at: str

    def __post_init__(self) -> None:
        if not self.normalization_id or not self.normalization_id.strip():
            raise ValueError("normalization_id must not be empty")
        if not self.reason or not self.reason.strip():
            raise ValueError("reason must not be empty")
        if not self.created_at or not self.created_at.strip():
            raise ValueError("created_at must not be empty")


def verifier_result_to_dict(result: VerifierResult) -> dict[str, object]:
    data: dict[str, object] = asdict(result)
    data["verifier_kind"] = result.verifier_kind.value
    data["status"] = result.status.value
    data["limitations"] = list(result.limitations)
    data["evidence_refs"] = [evidence_ref_to_dict(ref) for ref in result.evidence_refs]
    data["source_trace_event_ref"] = asdict(result.source_trace_event_ref)
    return data


def normalization_report_to_dict(report: VerifierNormalizationReport) -> dict[str, object]:
    return {
        "normalization_id": report.normalization_id,
        "verifier_kind": report.verifier_kind.value,
        "raw_input_ref": report.raw_input_ref,
        "normalized_verifier_result_ref": report.normalized_verifier_result_ref,
        "normalization_status": report.normalization_status.value,
        "reason": report.reason,
        "warnings": list(report.warnings),
        "errors": list(report.errors),
        "created_at": report.created_at,
    }
