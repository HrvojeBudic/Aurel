"""P1.5.14/15 Evaluation Mirror runtime contracts.

The runtime-callable boundary for Evaluation Mirror that future AurelFlow
can call safely. Every evaluation is trace-bound, candidate-only, and
incapable of promoting capability, committing memory, creating skills,
creating reflexes, or changing policy.

P1.5.15 extends EvaluationRunResult with brain-aware diagnostic fields.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum

from .trace import TraceEventRef


class EvaluationTargetType(str, Enum):
    """What kind of target is being evaluated."""
    CAPABILITY_EVIDENCE = "capability_evidence"
    EVALUATION_CASE = "evaluation_case"
    REGRESSION_CANDIDATE = "regression_candidate"
    VERIFIER_RESULT = "verifier_result"
    TRACE_EVENT = "trace_event"


class EvaluationMode(str, Enum):
    """What mode of evaluation is requested."""
    CONTRACT = "contract"
    REGRESSION_SEED = "regression_seed"
    REVIEW_SEED = "review_seed"
    CAPABILITY_CHECK = "capability_check"


class EvaluationRunStatus(str, Enum):
    """Lifecycle status of one evaluation run."""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    NEEDS_REVIEW = "needs_review"
    INCONCLUSIVE = "inconclusive"


_TERMINAL_STATUSES = frozenset({
    EvaluationRunStatus.PASSED,
    EvaluationRunStatus.FAILED,
    EvaluationRunStatus.NEEDS_REVIEW,
    EvaluationRunStatus.INCONCLUSIVE,
})


class EvaluationEventKind(str, Enum):
    """Typed evaluation event within AurelTraceLog."""
    EVALUATION_REQUESTED = "evaluation_requested"
    EVALUATION_STARTED = "evaluation_started"
    EVALUATION_TARGET_VALIDATED = "evaluation_target_validated"
    EVALUATION_VERIFIER_USED = "evaluation_verifier_used"
    EVALUATION_CASE_EXTRACTED = "evaluation_case_extracted"
    EVALUATION_REGRESSION_CANDIDATE_EXTRACTED = "evaluation_regression_candidate_extracted"
    EVALUATION_COMPLETED = "evaluation_completed"
    EVALUATION_FAILED = "evaluation_failed"
    EVALUATION_NEEDS_REVIEW = "evaluation_needs_review"


# ---------------------------------------------------------------------------
# EvaluationTargetRef
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class EvaluationTargetRef:
    """Represents the thing being evaluated through a runtime-callable boundary."""

    target_id: str
    target_type: EvaluationTargetType
    source_trace_event_ref: TraceEventRef
    source_event_hash: str
    evidence_refs: tuple[str, ...]
    created_at: str

    def __post_init__(self) -> None:
        if not self.target_id or not self.target_id.strip():
            raise ValueError("target_id must not be empty")
        if self.source_trace_event_ref is None:
            raise ValueError("source_trace_event_ref is required")
        if not self.source_event_hash or not self.source_event_hash.strip():
            raise ValueError("source_event_hash must not be empty")
        if self.source_event_hash != self.source_trace_event_ref.event_hash:
            raise ValueError(
                "source_event_hash must match source_trace_event_ref.event_hash"
            )
        if not self.created_at or not self.created_at.strip():
            raise ValueError("created_at must not be empty")


# ---------------------------------------------------------------------------
# EvaluationRequest
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class EvaluationRequest:
    """A future runtime-callable request to evaluate a trace-bound target.

    EvaluationRequest must not execute anything by itself.
    """

    request_id: str
    target_ref: EvaluationTargetRef
    requested_by: str
    reason: str
    evaluation_mode: EvaluationMode
    required_verifier_kinds: tuple[str, ...] = ()
    created_at: str = ""

    def __post_init__(self) -> None:
        if not self.request_id or not self.request_id.strip():
            raise ValueError("request_id must not be empty")
        if self.target_ref is None:
            raise ValueError("target_ref must not be None")
        if not self.requested_by or not self.requested_by.strip():
            raise ValueError("requested_by must not be empty")
        if not self.reason or not self.reason.strip():
            raise ValueError("reason must not be empty")
        if not self.created_at or not self.created_at.strip():
            raise ValueError("created_at must not be empty")


# ---------------------------------------------------------------------------
# EvaluationRun
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class EvaluationRun:
    """Represents one evaluation execution instance."""

    run_id: str
    request_id: str
    target_ref: EvaluationTargetRef
    status: EvaluationRunStatus
    started_at: str
    completed_at: str | None = None
    emitted_event_refs: tuple[str, ...] = ()
    verifier_result_refs: tuple[str, ...] = ()
    evaluation_case_refs: tuple[str, ...] = ()
    regression_candidate_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.run_id or not self.run_id.strip():
            raise ValueError("run_id must not be empty")
        if not self.request_id or not self.request_id.strip():
            raise ValueError("request_id must not be empty")
        if self.target_ref is None:
            raise ValueError("target_ref must not be None")
        if not self.started_at or not self.started_at.strip():
            raise ValueError("started_at must not be empty")
        if self.completed_at is not None and not self.completed_at.strip():
            raise ValueError("completed_at must not be empty if set")
        if self.status in _TERMINAL_STATUSES and self.completed_at is None:
            raise ValueError(
                "completed_at is required when status is terminal"
            )
        if self.completed_at is not None and self.status not in _TERMINAL_STATUSES:
            raise ValueError(
                "completed_at may only be set when status is terminal"
            )


# ---------------------------------------------------------------------------
# EvaluationEvent
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class EvaluationEvent:
    """A typed evaluation event bound to canonical AurelTraceLog.

    EvaluationEvent is not a second source of truth.
    Every serious EvaluationEvent must bind to an emitted canonical TraceEventRef.
    """

    evaluation_event_id: str
    run_id: str
    request_id: str
    event_kind: EvaluationEventKind
    source_trace_event_ref: TraceEventRef
    emitted_trace_event_ref: TraceEventRef | None = None
    message: str = ""
    payload_hash: str = ""
    created_at: str = ""

    def __post_init__(self) -> None:
        if not self.evaluation_event_id or not self.evaluation_event_id.strip():
            raise ValueError("evaluation_event_id must not be empty")
        if not self.run_id or not self.run_id.strip():
            raise ValueError("run_id must not be empty")
        if not self.request_id or not self.request_id.strip():
            raise ValueError("request_id must not be empty")
        if self.source_trace_event_ref is None:
            raise ValueError("source_trace_event_ref is required")
        if not self.created_at or not self.created_at.strip():
            raise ValueError("created_at must not be empty")


# ---------------------------------------------------------------------------
# EvaluationRunResult
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class EvaluationRunResult:
    """Final result of an evaluation run.

    EvaluationRunResult may only produce trace-bound result/candidate records.
    It may not promote, commit, execute, or mutate authority.

    P1.5.15: brain-aware diagnostic fields provide deterministic context/evidence/
    verifier failure classification without open-domain cognition.
    """

    run_id: str
    request_id: str
    status: EvaluationRunStatus
    summary: str
    verifier_result_refs: tuple[str, ...] = ()
    evaluation_case_refs: tuple[str, ...] = ()
    regression_candidate_refs: tuple[str, ...] = ()
    emitted_event_refs: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    completed_at: str = ""
    brain_aware_context_ref: str | None = None
    failure_classification_ref: str | None = None
    context_limitations: tuple[str, ...] = ()
    recommended_next_action: str | None = None

    def __post_init__(self) -> None:
        if not self.run_id or not self.run_id.strip():
            raise ValueError("run_id must not be empty")
        if not self.request_id or not self.request_id.strip():
            raise ValueError("request_id must not be empty")
        if self.status not in _TERMINAL_STATUSES:
            raise ValueError(
                f"EvaluationRunResult status must be terminal, got {self.status.value}"
            )
        if not self.summary or not self.summary.strip():
            raise ValueError("summary must not be empty")
        if not self.limitations:
            raise ValueError("EvaluationRunResult limitations must be non-empty")
        if self.status == EvaluationRunStatus.FAILED and not self.errors:
            raise ValueError("errors must be non-empty when status is failed")
        if not self.completed_at or not self.completed_at.strip():
            raise ValueError("completed_at must not be empty")


# ---------------------------------------------------------------------------
# Serialization helpers
# ---------------------------------------------------------------------------


def evaluation_target_ref_to_dict(ref: EvaluationTargetRef) -> dict[str, object]:
    return {
        "target_id": ref.target_id,
        "target_type": ref.target_type.value,
        "source_trace_event_ref": asdict(ref.source_trace_event_ref),
        "source_event_hash": ref.source_event_hash,
        "evidence_refs": list(ref.evidence_refs),
        "created_at": ref.created_at,
    }


def evaluation_request_to_dict(req: EvaluationRequest) -> dict[str, object]:
    return {
        "request_id": req.request_id,
        "target_ref": evaluation_target_ref_to_dict(req.target_ref),
        "requested_by": req.requested_by,
        "reason": req.reason,
        "evaluation_mode": req.evaluation_mode.value,
        "required_verifier_kinds": list(req.required_verifier_kinds),
        "created_at": req.created_at,
    }


def evaluation_run_to_dict(run: EvaluationRun) -> dict[str, object]:
    return {
        "run_id": run.run_id,
        "request_id": run.request_id,
        "target_ref": evaluation_target_ref_to_dict(run.target_ref),
        "status": run.status.value,
        "started_at": run.started_at,
        "completed_at": run.completed_at,
        "emitted_event_refs": list(run.emitted_event_refs),
        "verifier_result_refs": list(run.verifier_result_refs),
        "evaluation_case_refs": list(run.evaluation_case_refs),
        "regression_candidate_refs": list(run.regression_candidate_refs),
    }


def evaluation_event_to_dict(event: EvaluationEvent) -> dict[str, object]:
    data: dict[str, object] = {
        "evaluation_event_id": event.evaluation_event_id,
        "run_id": event.run_id,
        "request_id": event.request_id,
        "event_kind": event.event_kind.value,
        "source_trace_event_ref": asdict(event.source_trace_event_ref),
        "message": event.message,
        "payload_hash": event.payload_hash,
        "created_at": event.created_at,
    }
    if event.emitted_trace_event_ref is not None:
        data["emitted_trace_event_ref"] = asdict(event.emitted_trace_event_ref)
    else:
        data["emitted_trace_event_ref"] = None
    return data


def evaluation_run_result_to_dict(result: EvaluationRunResult) -> dict[str, object]:
    return {
        "run_id": result.run_id,
        "request_id": result.request_id,
        "status": result.status.value,
        "summary": result.summary,
        "verifier_result_refs": list(result.verifier_result_refs),
        "evaluation_case_refs": list(result.evaluation_case_refs),
        "regression_candidate_refs": list(result.regression_candidate_refs),
        "emitted_event_refs": list(result.emitted_event_refs),
        "limitations": list(result.limitations),
        "errors": list(result.errors),
        "warnings": list(result.warnings),
        "completed_at": result.completed_at,
        "brain_aware_context_ref": result.brain_aware_context_ref,
        "failure_classification_ref": result.failure_classification_ref,
        "context_limitations": list(result.context_limitations),
        "recommended_next_action": result.recommended_next_action,
    }
