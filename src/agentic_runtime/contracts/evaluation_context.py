"""P1.5.15 Brain-Aware Evaluation Context contracts.

A deterministic, explicit-flag, contract-first diagnostic layer for
Evaluation Mirror. The context classifier uses only explicit status fields,
hashes, verifier statuses, and existing context adequacy statuses — never
open-domain semantic reasoning, LLMs, NLI, or Theory-of-Mind.

These contracts are diagnostic projections/snapshots bound to canonical
AurelTraceLog. They are not a second source of truth.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum

from .trace import TraceEventRef


class EvaluationFailureReason(str, Enum):
    """Why an evaluation passed, failed, or needs review.

    Deterministic — derived only from explicit trace/context/evidence/verifier signals.
    """
    NONE = "none"
    MISSING_CONTEXT = "missing_context"
    STALE_CONTEXT = "stale_context"
    CONTRADICTED_CONTEXT = "contradicted_context"
    WRONG_INTENT_HYPOTHESIS = "wrong_intent_hypothesis"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    WEAK_EVIDENCE = "weak_evidence"
    VERIFIER_FAILED = "verifier_failed"
    VERIFIER_INCONCLUSIVE = "verifier_inconclusive"
    POLICY_BLOCK = "policy_block"
    TOOL_FAILURE = "tool_failure"
    TRACE_INTEGRITY_FAILURE = "trace_integrity_failure"
    HASH_MISMATCH = "hash_mismatch"
    UNSAFE_CONTEXT = "unsafe_context"
    UNKNOWN = "unknown"


class ContextRiskLevel(str, Enum):
    """How safe/useful the evaluation context is for decision-making."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# Severity ordering for priority resolution when multiple signals exist.
_CONTEXT_RISK_ORDER: dict[ContextRiskLevel, int] = {
    ContextRiskLevel.LOW: 0,
    ContextRiskLevel.MEDIUM: 1,
    ContextRiskLevel.HIGH: 2,
    ContextRiskLevel.CRITICAL: 3,
}


# ---------------------------------------------------------------------------
# ContextSignal
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ContextSignal:
    """A single diagnostic signal detected during evaluation context analysis."""

    signal_id: str
    signal_type: str
    severity: str
    reason: str
    source_ref: str | None = None
    created_at: str = ""

    def __post_init__(self) -> None:
        if not self.signal_id or not self.signal_id.strip():
            raise ValueError("signal_id must not be empty")
        if not self.signal_type or not self.signal_type.strip():
            raise ValueError("signal_type must not be empty")
        if not self.severity or not self.severity.strip():
            raise ValueError("severity must not be empty")
        if not self.reason or not self.reason.strip():
            raise ValueError("reason must not be empty")
        if not self.created_at or not self.created_at.strip():
            raise ValueError("created_at must not be empty")


# ---------------------------------------------------------------------------
# EvaluationContextSnapshot
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class EvaluationContextSnapshot:
    """Freeze what Aurel knew at evaluation time.

    A diagnostic projection bound to canonical AurelTraceLog.
    NOT a second source of truth.
    """

    snapshot_id: str
    source_trace_event_ref: TraceEventRef
    context_binding_ref: str | None = None
    context_adequacy_ref: str | None = None
    verifier_result_refs: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    capability_evidence_ref: str | None = None
    evaluation_case_ref: str | None = None
    created_at: str = ""

    def __post_init__(self) -> None:
        if not self.snapshot_id or not self.snapshot_id.strip():
            raise ValueError("snapshot_id must not be empty")
        if self.source_trace_event_ref is None:
            raise ValueError("source_trace_event_ref is required")
        if not self.created_at or not self.created_at.strip():
            raise ValueError("created_at must not be empty")


# ---------------------------------------------------------------------------
# EvaluationFailureClassification
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class EvaluationFailureClassification:
    """Classify why an evaluation failed, needs review, or must limit confidence.

    Uses only explicit trace/context/evidence/verifier signals.
    """

    classification_id: str
    primary_reason: EvaluationFailureReason
    secondary_reasons: tuple[str, ...] = ()
    context_risk_level: ContextRiskLevel = ContextRiskLevel.LOW
    signals: tuple[ContextSignal, ...] = ()
    requires_operator_clarification: bool = False
    blocks_verified_capability: bool = False
    blocks_positive_eval_case: bool = False
    created_at: str = ""

    def __post_init__(self) -> None:
        if not self.classification_id or not self.classification_id.strip():
            raise ValueError("classification_id must not be empty")
        if not self.created_at or not self.created_at.strip():
            raise ValueError("created_at must not be empty")
        if self.primary_reason is None:
            raise ValueError("primary_reason must not be None")
        if self.primary_reason != EvaluationFailureReason.NONE and not self.signals:
            raise ValueError(
                "signals must be non-empty when primary_reason is not none"
            )


# ---------------------------------------------------------------------------
# BrainAwareEvaluationContext
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class BrainAwareEvaluationContext:
    """Attach deterministic brain/context diagnostics to an EvaluationRunResult."""

    brain_eval_context_id: str
    evaluation_context_snapshot: EvaluationContextSnapshot
    failure_classification: EvaluationFailureClassification
    context_limitations: tuple[str, ...] = ()
    recommended_next_action: str = ""
    created_at: str = ""

    def __post_init__(self) -> None:
        if not self.brain_eval_context_id or not self.brain_eval_context_id.strip():
            raise ValueError("brain_eval_context_id must not be empty")
        if self.evaluation_context_snapshot is None:
            raise ValueError("evaluation_context_snapshot is required")
        if self.failure_classification is None:
            raise ValueError("failure_classification is required")
        if not self.recommended_next_action or not self.recommended_next_action.strip():
            raise ValueError("recommended_next_action must not be empty")
        if not self.created_at or not self.created_at.strip():
            raise ValueError("created_at must not be empty")


# ---------------------------------------------------------------------------
# Serialization helpers
# ---------------------------------------------------------------------------


def context_signal_to_dict(signal: ContextSignal) -> dict[str, object]:
    return {
        "signal_id": signal.signal_id,
        "signal_type": signal.signal_type,
        "severity": signal.severity,
        "reason": signal.reason,
        "source_ref": signal.source_ref,
        "created_at": signal.created_at,
    }


def evaluation_context_snapshot_to_dict(snapshot: EvaluationContextSnapshot) -> dict[str, object]:
    return {
        "snapshot_id": snapshot.snapshot_id,
        "source_trace_event_ref": asdict(snapshot.source_trace_event_ref),
        "context_binding_ref": snapshot.context_binding_ref,
        "context_adequacy_ref": snapshot.context_adequacy_ref,
        "verifier_result_refs": list(snapshot.verifier_result_refs),
        "evidence_refs": list(snapshot.evidence_refs),
        "capability_evidence_ref": snapshot.capability_evidence_ref,
        "evaluation_case_ref": snapshot.evaluation_case_ref,
        "created_at": snapshot.created_at,
    }


def evaluation_failure_classification_to_dict(
    classification: EvaluationFailureClassification,
) -> dict[str, object]:
    return {
        "classification_id": classification.classification_id,
        "primary_reason": classification.primary_reason.value,
        "secondary_reasons": list(classification.secondary_reasons),
        "context_risk_level": classification.context_risk_level.value,
        "signals": [context_signal_to_dict(s) for s in classification.signals],
        "requires_operator_clarification": classification.requires_operator_clarification,
        "blocks_verified_capability": classification.blocks_verified_capability,
        "blocks_positive_eval_case": classification.blocks_positive_eval_case,
        "created_at": classification.created_at,
    }


def brain_aware_evaluation_context_to_dict(
    brain: BrainAwareEvaluationContext,
) -> dict[str, object]:
    return {
        "brain_eval_context_id": brain.brain_eval_context_id,
        "evaluation_context_snapshot": evaluation_context_snapshot_to_dict(
            brain.evaluation_context_snapshot
        ),
        "failure_classification": evaluation_failure_classification_to_dict(
            brain.failure_classification
        ),
        "context_limitations": list(brain.context_limitations),
        "recommended_next_action": brain.recommended_next_action,
        "created_at": brain.created_at,
    }
