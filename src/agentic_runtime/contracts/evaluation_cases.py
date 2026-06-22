"""P1.5.12 Evaluation Case Extraction contracts.

EvaluationCase and RegressionCandidate carry zero automatic capability:
- defaults are candidate/needs_review (never accepted)
- extraction requires trace-bound CapabilityEvidenceRecord
- impossible states are blocked by invariant validation
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum

from .trace import TraceEventRef


class FailureMode(str, Enum):
    """Deterministic v1 failure taxonomy for regression candidate origin."""

    VERIFIER_FAILED = "verifier_failed"
    INSUFFICIENT_CONTEXT = "insufficient_context"
    UNSAFE_CONTEXT = "unsafe_context"
    MISSING_EVIDENCE = "missing_evidence"
    WEAK_EVIDENCE = "weak_evidence"
    HASH_MISMATCH = "hash_mismatch"
    MISSING_LIMITATIONS = "missing_limitations"
    POLICY_BLOCK = "policy_block"
    UNKNOWN = "unknown"


class EvaluationCaseStatus(str, Enum):
    CANDIDATE = "candidate"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    NEEDS_REVIEW = "needs_review"


class EvaluationCaseKind(str, Enum):
    POSITIVE = "positive"
    REGRESSION = "regression"
    REVIEW = "review"
    EXPLORATORY = "exploratory"


class RegressionPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ExtractionStatus(str, Enum):
    EXTRACTED = "extracted"
    SKIPPED = "skipped"
    FAILED = "failed"
    NEEDS_REVIEW = "needs_review"


@dataclass(frozen=True)
class EvaluationCase:
    """Minimal v1 seed for a future reusable evaluation/test case.

    Derives from trace-bound capability evidence.
    Never automatically accepted — always requires explicit promotion.
    """

    case_id: str
    case_kind: EvaluationCaseKind
    source_capability_evidence_id: str
    source_trace_event_ref: TraceEventRef
    source_event_hash: str
    evidence_refs: tuple[str, ...]
    verifier_result_ref: str | None
    context_adequacy_ref: str | None
    input_snapshot_ref: str | None
    expected_behavior: str | None
    success_criteria: tuple[str, ...]
    known_limitations: tuple[str, ...]
    failure_mode: FailureMode | None
    regression_priority: RegressionPriority | None
    created_at: str
    status: EvaluationCaseStatus

    def __post_init__(self) -> None:
        if not self.case_id or not self.case_id.strip():
            raise ValueError("case_id must not be empty")
        if not self.source_capability_evidence_id or not self.source_capability_evidence_id.strip():
            raise ValueError("source_capability_evidence_id must not be empty")
        if self.source_trace_event_ref is None:
            raise ValueError("source_trace_event_ref is required")
        if not self.source_event_hash or not self.source_event_hash.strip():
            raise ValueError("source_event_hash must not be empty")
        if not self.created_at or not self.created_at.strip():
            raise ValueError("created_at must not be empty")
        if self.source_event_hash != self.source_trace_event_ref.event_hash:
            raise ValueError("source_event_hash must match source_trace_event_ref.event_hash")

        if self.case_kind == EvaluationCaseKind.POSITIVE:
            if self.status not in (EvaluationCaseStatus.CANDIDATE, EvaluationCaseStatus.NEEDS_REVIEW):
                raise ValueError("positive EvaluationCase status must be candidate or needs_review")
            if not self.evidence_refs:
                raise ValueError("positive EvaluationCase requires non-empty evidence_refs")
            if not self.known_limitations:
                raise ValueError("positive EvaluationCase requires non-empty known_limitations")
            if self.failure_mode is not None:
                raise ValueError("positive EvaluationCase must not set failure_mode")
            if self.regression_priority is not None:
                raise ValueError("positive EvaluationCase must not set regression_priority")

        elif self.case_kind == EvaluationCaseKind.REVIEW:
            if self.status != EvaluationCaseStatus.NEEDS_REVIEW:
                raise ValueError("review EvaluationCase requires status=needs_review")

        if self.status == EvaluationCaseStatus.ACCEPTED:
            raise ValueError(
                "EvaluationCase.status=accepted is forbidden during extraction; "
                "cases must be explicitly promoted by operator action"
            )

        if self.case_kind != EvaluationCaseKind.REGRESSION:
            if self.failure_mode is not None:
                raise ValueError(
                    "failure_mode must only be set on regression cases "
                    "or regression EvaluationCases"
                )


@dataclass(frozen=True)
class RegressionCandidate:
    """Captures failed, unsafe, weak, or unverifiable outcomes.

    Becomes a future regression test after operator acceptance.
    Never automatically accepted — defaults to candidate.
    """

    regression_id: str
    source_case_id: str | None
    source_capability_evidence_id: str
    source_trace_event_ref: TraceEventRef
    source_event_hash: str
    failure_mode: FailureMode
    reproduction_hint: str | None
    priority: RegressionPriority
    evidence_refs: tuple[str, ...]
    verifier_result_ref: str | None
    context_adequacy_ref: str | None
    created_at: str
    status: EvaluationCaseStatus

    def __post_init__(self) -> None:
        if not self.regression_id or not self.regression_id.strip():
            raise ValueError("regression_id must not be empty")
        if not self.source_capability_evidence_id or not self.source_capability_evidence_id.strip():
            raise ValueError("source_capability_evidence_id must not be empty")
        if self.source_trace_event_ref is None:
            raise ValueError("source_trace_event_ref is required")
        if not self.source_event_hash or not self.source_event_hash.strip():
            raise ValueError("source_event_hash must not be empty")
        if not self.created_at or not self.created_at.strip():
            raise ValueError("created_at must not be empty")
        if self.source_event_hash != self.source_trace_event_ref.event_hash:
            raise ValueError("source_event_hash must match source_trace_event_ref.event_hash")
        if self.status == EvaluationCaseStatus.ACCEPTED:
            raise ValueError(
                "RegressionCandidate.status=accepted is forbidden during extraction; "
                "regressions must be explicitly promoted by operator action"
            )
        if self.failure_mode == FailureMode.UNKNOWN:
            pass
        if self.failure_mode == FailureMode.MISSING_EVIDENCE:
            pass
        else:
            if not self.evidence_refs:
                raise ValueError(
                    "regression candidate requires evidence_refs unless failure_mode is "
                    "missing_evidence"
                )


@dataclass(frozen=True)
class EvaluationCaseExtractionReport:
    """Auditable extraction result explaining what was produced and why."""

    extraction_id: str
    source_capability_evidence_id: str
    extracted_case_id: str | None
    extracted_regression_id: str | None
    extraction_status: ExtractionStatus
    reason: str
    warnings: tuple[str, ...]
    errors: tuple[str, ...]
    created_at: str

    def __post_init__(self) -> None:
        if not self.extraction_id or not self.extraction_id.strip():
            raise ValueError("extraction_id must not be empty")
        if not self.source_capability_evidence_id or not self.source_capability_evidence_id.strip():
            raise ValueError("source_capability_evidence_id must not be empty")
        if not self.reason or not self.reason.strip():
            raise ValueError("reason must not be empty")
        if not self.created_at or not self.created_at.strip():
            raise ValueError("created_at must not be empty")


def evaluation_case_to_dict(case: EvaluationCase) -> dict[str, object]:
    return {
        "case_id": case.case_id,
        "case_kind": case.case_kind.value,
        "source_capability_evidence_id": case.source_capability_evidence_id,
        "source_trace_event_ref": asdict(case.source_trace_event_ref),
        "source_event_hash": case.source_event_hash,
        "evidence_refs": list(case.evidence_refs),
        "verifier_result_ref": case.verifier_result_ref,
        "context_adequacy_ref": case.context_adequacy_ref,
        "input_snapshot_ref": case.input_snapshot_ref,
        "expected_behavior": case.expected_behavior,
        "success_criteria": list(case.success_criteria),
        "known_limitations": list(case.known_limitations),
        "failure_mode": case.failure_mode.value if case.failure_mode else None,
        "regression_priority": case.regression_priority.value if case.regression_priority else None,
        "created_at": case.created_at,
        "status": case.status.value,
    }


def regression_candidate_to_dict(candidate: RegressionCandidate) -> dict[str, object]:
    return {
        "regression_id": candidate.regression_id,
        "source_case_id": candidate.source_case_id,
        "source_capability_evidence_id": candidate.source_capability_evidence_id,
        "source_trace_event_ref": asdict(candidate.source_trace_event_ref),
        "source_event_hash": candidate.source_event_hash,
        "failure_mode": candidate.failure_mode.value,
        "reproduction_hint": candidate.reproduction_hint,
        "priority": candidate.priority.value,
        "evidence_refs": list(candidate.evidence_refs),
        "verifier_result_ref": candidate.verifier_result_ref,
        "context_adequacy_ref": candidate.context_adequacy_ref,
        "created_at": candidate.created_at,
        "status": candidate.status.value,
    }


def extraction_report_to_dict(report: EvaluationCaseExtractionReport) -> dict[str, object]:
    return {
        "extraction_id": report.extraction_id,
        "source_capability_evidence_id": report.source_capability_evidence_id,
        "extracted_case_id": report.extracted_case_id,
        "extracted_regression_id": report.extracted_regression_id,
        "extraction_status": report.extraction_status.value,
        "reason": report.reason,
        "warnings": list(report.warnings),
        "errors": list(report.errors),
        "created_at": report.created_at,
    }
