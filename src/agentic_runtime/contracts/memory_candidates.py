"""P1.5.18 Evaluation <-> Memory Candidate Bridge contracts.

Experience may become a MemoryCandidate.
Only governed future review may become committed memory.

MemoryCandidate is NOT committed memory.
MemoryCandidate is NOT active recall memory.
MemoryCandidate does NOT create skills, reflexes, policies, or canon.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum

from .trace import TraceEventRef


# ---------------------------------------------------------------------------
# MemoryCandidateType
# ---------------------------------------------------------------------------


class MemoryCandidateType(str, Enum):
    """Classifies what kind of memory might be created later.

    Candidate classification only — does not decide memory commitment.
    """
    OPERATOR_PREFERENCE = "operator_preference"
    OPERATOR_CORRECTION = "operator_correction"
    EVALUATION_LESSON = "evaluation_lesson"
    CAPABILITY_LESSON = "capability_lesson"
    FAILURE_PATTERN = "failure_pattern"
    CONTEXT_REQUIREMENT = "context_requirement"
    LIMITATION_NOTE = "limitation_note"
    SAFETY_NOTE = "safety_note"
    POLICY_NOTE = "policy_note"
    PROJECT_NOTE = "project_note"
    UNKNOWN = "unknown"


# ---------------------------------------------------------------------------
# MemoryCandidateStatus
# ---------------------------------------------------------------------------


class MemoryCandidateStatus(str, Enum):
    """Candidate status — NO committed state exists in P1.5.18."""
    CANDIDATE = "candidate"
    NEEDS_REVIEW = "needs_review"
    BLOCKED = "blocked"
    REJECTED = "rejected"


# ---------------------------------------------------------------------------
# MemoryCandidateSourceType
# ---------------------------------------------------------------------------


class MemoryCandidateSourceType(str, Enum):
    """Where the candidate came from."""
    EVALUATION_RUN_RESULT = "evaluation_run_result"
    BRAIN_AWARE_CONTEXT = "brain_aware_context"
    OPERATOR_FEEDBACK = "operator_feedback"
    FEEDBACK_PROCESSING_REPORT = "feedback_processing_report"
    CAPABILITY_CLAIM = "capability_claim"
    CAPABILITY_EVIDENCE = "capability_evidence"
    TRACE_EVENT = "trace_event"


# ---------------------------------------------------------------------------
# MemoryCandidateRiskClass
# ---------------------------------------------------------------------------


class MemoryCandidateRiskClass(str, Enum):
    """Risk classification for memory candidates."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    SENSITIVE = "sensitive"
    AUTHORITY_SENSITIVE = "authority_sensitive"


# Risk classes that require review.
_REQUIRES_REVIEW = frozenset({
    MemoryCandidateRiskClass.SENSITIVE,
    MemoryCandidateRiskClass.AUTHORITY_SENSITIVE,
})

# Risk classes that can block.
_CAN_BLOCK = frozenset({
    MemoryCandidateRiskClass.AUTHORITY_SENSITIVE,
})


# ---------------------------------------------------------------------------
# MemoryCandidateScope
# ---------------------------------------------------------------------------


class MemoryCandidateScopeType(str, Enum):
    """What domain the memory candidate applies to."""
    OPERATOR = "operator"
    PROJECT = "project"
    CAPABILITY = "capability"
    EVALUATION = "evaluation"
    POLICY = "policy"
    SYSTEM = "system"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class MemoryCandidateScope:
    """Prevents a local observation from becoming global memory."""

    scope_type: MemoryCandidateScopeType
    allowed_use_contexts: tuple[str, ...] = ()
    project_ref: str | None = None
    capability_id: str | None = None
    evaluation_run_id: str | None = None
    claim_id: str | None = None

    def __post_init__(self) -> None:
        if self.scope_type is None:
            raise ValueError("scope_type must not be None")


# ---------------------------------------------------------------------------
# MemoryCandidateEvidenceLink
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class MemoryCandidateEvidenceLink:
    """Binds memory candidate to trace/evidence/source chain."""

    link_id: str
    source_trace_event_ref: TraceEventRef
    source_event_hash: str
    evidence_refs: tuple[str, ...] = ()
    verifier_result_refs: tuple[str, ...] = ()
    evaluation_run_result_ref: str | None = None
    operator_feedback_ref: str | None = None
    capability_claim_ref: str | None = None
    brain_aware_context_ref: str | None = None

    def __post_init__(self) -> None:
        if not self.link_id or not self.link_id.strip():
            raise ValueError("link_id must not be empty")
        if self.source_trace_event_ref is None:
            raise ValueError("source_trace_event_ref is required")
        if not self.source_event_hash or not self.source_event_hash.strip():
            raise ValueError("source_event_hash must not be empty")
        if self.source_event_hash != self.source_trace_event_ref.event_hash:
            raise ValueError(
                "source_event_hash must match source_trace_event_ref.event_hash"
            )


# ---------------------------------------------------------------------------
# MemoryCandidate
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class MemoryCandidate:
    """A candidate memory record. NOT committed memory. NOT active recall.

    Status MUST NOT be 'committed' — that state does not exist in P1.5.18.
    """

    memory_candidate_id: str
    candidate_type: MemoryCandidateType
    status: MemoryCandidateStatus
    source_type: MemoryCandidateSourceType
    scope: MemoryCandidateScope
    proposed_memory_text: str
    risk_class: MemoryCandidateRiskClass
    limitations: tuple[str, ...]
    evidence_links: tuple[MemoryCandidateEvidenceLink, ...] = ()
    review_reason: str | None = None
    created_at: str = ""

    def __post_init__(self) -> None:
        if not self.memory_candidate_id or not self.memory_candidate_id.strip():
            raise ValueError("memory_candidate_id must not be empty")
        if self.candidate_type is None:
            raise ValueError("candidate_type must not be None")
        if self.status is None:
            raise ValueError("status must not be None")
        if self.source_type is None:
            raise ValueError("source_type must not be None")
        if self.scope is None:
            raise ValueError("scope must not be None")
        if not self.proposed_memory_text or not self.proposed_memory_text.strip():
            raise ValueError("proposed_memory_text must not be empty")
        if self.risk_class is None:
            raise ValueError("risk_class must not be None")
        if not self.limitations:
            raise ValueError("limitations must be non-empty")
        if not self.created_at or not self.created_at.strip():
            raise ValueError("created_at must not be empty")

        # Safety / policy note cannot be low risk
        if self.candidate_type in (
            MemoryCandidateType.SAFETY_NOTE,
            MemoryCandidateType.POLICY_NOTE,
        ):
            if self.risk_class == MemoryCandidateRiskClass.LOW:
                raise ValueError(
                    f"{self.candidate_type.value} candidate cannot be low risk"
                )

        # Sensitive / authority_sensitive requires review or block
        if self.risk_class in _REQUIRES_REVIEW:
            if self.status not in (
                MemoryCandidateStatus.NEEDS_REVIEW,
                MemoryCandidateStatus.BLOCKED,
            ):
                raise ValueError(
                    f"{self.risk_class.value} risk class requires "
                    f"needs_review or blocked status, got {self.status.value}"
                )

        # Positive/usable candidates require evidence links
        if self.status in (
            MemoryCandidateStatus.CANDIDATE,
            MemoryCandidateStatus.NEEDS_REVIEW,
        ):
            if not self.evidence_links:
                raise ValueError(
                    "candidate/needs_review status requires non-empty evidence_links"
                )


# ---------------------------------------------------------------------------
# MemoryCandidateValidationReport
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class MemoryCandidateValidationReport:
    """Explains whether a memory candidate is safe to queue for future review."""

    validation_id: str
    memory_candidate_id: str
    is_valid: bool
    risk_class: MemoryCandidateRiskClass
    required_review: bool = False
    blocked_reasons: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    created_at: str = ""

    def __post_init__(self) -> None:
        if not self.validation_id or not self.validation_id.strip():
            raise ValueError("validation_id must not be empty")
        if not self.memory_candidate_id or not self.memory_candidate_id.strip():
            raise ValueError("memory_candidate_id must not be empty")
        if self.risk_class is None:
            raise ValueError("risk_class must not be None")
        if not self.created_at or not self.created_at.strip():
            raise ValueError("created_at must not be empty")
        if not self.is_valid and not self.blocked_reasons:
            raise ValueError(
                "is_valid=False requires non-empty blocked_reasons"
            )


# ---------------------------------------------------------------------------
# MemoryCandidateBridgeReport
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class MemoryCandidateBridgeReport:
    """Audits the bridge from evaluation/feedback/capability output to memory candidates."""

    report_id: str
    source_ref: str
    reason: str
    created_memory_candidate_ids: tuple[str, ...] = ()
    blocked_candidate_ids: tuple[str, ...] = ()
    validation_report_ids: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()
    created_at: str = ""

    def __post_init__(self) -> None:
        if not self.report_id or not self.report_id.strip():
            raise ValueError("report_id must not be empty")
        if not self.source_ref or not self.source_ref.strip():
            raise ValueError("source_ref must not be empty")
        if not self.reason or not self.reason.strip():
            raise ValueError("reason must not be empty")
        if not self.created_at or not self.created_at.strip():
            raise ValueError("created_at must not be empty")


# ---------------------------------------------------------------------------
# Serialization helpers
# ---------------------------------------------------------------------------


def memory_candidate_scope_to_dict(scope: MemoryCandidateScope) -> dict[str, object]:
    return {
        "scope_type": scope.scope_type.value,
        "allowed_use_contexts": list(scope.allowed_use_contexts),
        "project_ref": scope.project_ref,
        "capability_id": scope.capability_id,
        "evaluation_run_id": scope.evaluation_run_id,
        "claim_id": scope.claim_id,
    }


def memory_candidate_evidence_link_to_dict(
    link: MemoryCandidateEvidenceLink,
) -> dict[str, object]:
    return {
        "link_id": link.link_id,
        "source_trace_event_ref": asdict(link.source_trace_event_ref),
        "source_event_hash": link.source_event_hash,
        "evidence_refs": list(link.evidence_refs),
        "verifier_result_refs": list(link.verifier_result_refs),
        "evaluation_run_result_ref": link.evaluation_run_result_ref,
        "operator_feedback_ref": link.operator_feedback_ref,
        "capability_claim_ref": link.capability_claim_ref,
        "brain_aware_context_ref": link.brain_aware_context_ref,
    }


def memory_candidate_to_dict(candidate: MemoryCandidate) -> dict[str, object]:
    return {
        "memory_candidate_id": candidate.memory_candidate_id,
        "candidate_type": candidate.candidate_type.value,
        "status": candidate.status.value,
        "source_type": candidate.source_type.value,
        "scope": memory_candidate_scope_to_dict(candidate.scope),
        "proposed_memory_text": candidate.proposed_memory_text,
        "risk_class": candidate.risk_class.value,
        "limitations": list(candidate.limitations),
        "evidence_links": [
            memory_candidate_evidence_link_to_dict(e) for e in candidate.evidence_links
        ],
        "review_reason": candidate.review_reason,
        "created_at": candidate.created_at,
    }


def memory_candidate_validation_report_to_dict(
    report: MemoryCandidateValidationReport,
) -> dict[str, object]:
    return {
        "validation_id": report.validation_id,
        "memory_candidate_id": report.memory_candidate_id,
        "is_valid": report.is_valid,
        "risk_class": report.risk_class.value,
        "required_review": report.required_review,
        "blocked_reasons": list(report.blocked_reasons),
        "warnings": list(report.warnings),
        "created_at": report.created_at,
    }


def memory_candidate_bridge_report_to_dict(
    report: MemoryCandidateBridgeReport,
) -> dict[str, object]:
    return {
        "report_id": report.report_id,
        "source_ref": report.source_ref,
        "reason": report.reason,
        "created_memory_candidate_ids": list(report.created_memory_candidate_ids),
        "blocked_candidate_ids": list(report.blocked_candidate_ids),
        "validation_report_ids": list(report.validation_report_ids),
        "warnings": list(report.warnings),
        "errors": list(report.errors),
        "created_at": report.created_at,
    }
