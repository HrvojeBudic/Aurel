"""P1.5.17 Operator Feedback Capture v2 contracts.

Operator feedback is captured as governed, trace/target-bound signals.
It is high-salience evidence input, but must NOT automatically:
- verify capability
- commit memory
- promote skill
- create reflex
- change policy
- canonize roadmap
- override verifier
- rewrite canonical trace

These contracts are candidate-only, anti-auto-truth, and projection-safe.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum

from .trace import TraceEventRef


# ---------------------------------------------------------------------------
# OperatorFeedbackType
# ---------------------------------------------------------------------------


class OperatorFeedbackType(str, Enum):
    """Classifies what kind of feedback the Operator gave."""
    RATING = "rating"
    APPROVAL = "approval"
    REJECTION = "rejection"
    CORRECTION = "correction"
    PREFERENCE_SIGNAL = "preference_signal"
    MEMORY_CANDIDATE = "memory_candidate"
    CAPABILITY_FEEDBACK = "capability_feedback"
    EVALUATION_FEEDBACK = "evaluation_feedback"
    SAFETY_CONCERN = "safety_concern"
    POLICY_CONCERN = "policy_concern"
    NEEDS_REVIEW = "needs_review"


# ---------------------------------------------------------------------------
# OperatorFeedbackSentiment
# ---------------------------------------------------------------------------


class OperatorFeedbackSentiment(str, Enum):
    """Separates emotional/tone signal from action meaning."""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    MIXED = "mixed"


# ---------------------------------------------------------------------------
# OperatorFeedbackTargetType
# ---------------------------------------------------------------------------


class OperatorFeedbackTargetType(str, Enum):
    """What type of object the Operator is giving feedback on."""
    TRACE_EVENT = "trace_event"
    EVIDENCE_REF = "evidence_ref"
    VERIFIER_RESULT = "verifier_result"
    CAPABILITY_EVIDENCE = "capability_evidence"
    EVALUATION_CASE = "evaluation_case"
    EVALUATION_RUN_RESULT = "evaluation_run_result"
    BRAIN_AWARE_CONTEXT = "brain_aware_context"
    CAPABILITY_CLAIM = "capability_claim"
    OUTPUT = "output"


# ---------------------------------------------------------------------------
# FeedbackSignalStrength
# ---------------------------------------------------------------------------


class FeedbackSignalStrength(str, Enum):
    """How strong the feedback signal is as evidence input."""
    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"
    BLOCKING = "blocking"


# Strength ordering for comparison.
_STRENGTH_ORDER: dict[FeedbackSignalStrength, int] = {
    FeedbackSignalStrength.WEAK: 0,
    FeedbackSignalStrength.MODERATE: 1,
    FeedbackSignalStrength.STRONG: 2,
    FeedbackSignalStrength.BLOCKING: 3,
}


# ---------------------------------------------------------------------------
# FeedbackCandidateAction
# ---------------------------------------------------------------------------


class FeedbackCandidateAction(str, Enum):
    """Candidate actions proposed by feedback processing.

    These are recommendations only. They do NOT execute automatically.
    """
    CREATE_MEMORY_CANDIDATE = "create_memory_candidate"
    CREATE_EVAL_CANDIDATE = "create_eval_candidate"
    CREATE_REGRESSION_CANDIDATE = "create_regression_candidate"
    MARK_CLAIM_NEEDS_REVIEW = "mark_claim_needs_review"
    LOWER_CLAIM_CONFIDENCE = "lower_claim_confidence"
    RAISE_REVIEW_PRIORITY = "raise_review_priority"
    ATTACH_LIMITATION = "attach_limitation"
    REQUEST_OPERATOR_CLARIFICATION = "request_operator_clarification"
    NO_ACTION = "no_action"


# ---------------------------------------------------------------------------
# OperatorFeedbackTargetRef
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class OperatorFeedbackTargetRef:
    """Defines what the Operator is giving feedback on.

    Projection-only feedback is allowed only as weak/unresolved signal,
    not strong canonical evidence.
    """

    target_id: str
    target_type: OperatorFeedbackTargetType
    source_trace_event_ref: TraceEventRef | None = None
    source_event_hash: str | None = None

    def __post_init__(self) -> None:
        if not self.target_id or not self.target_id.strip():
            raise ValueError("target_id must not be empty")
        if self.target_type is None:
            raise ValueError("target_type must not be None")
        if (
            self.source_trace_event_ref is not None
            and self.source_event_hash is not None
        ):
            if self.source_event_hash != self.source_trace_event_ref.event_hash:
                raise ValueError(
                    "source_event_hash must match source_trace_event_ref.event_hash "
                    "when both are present"
                )


# ---------------------------------------------------------------------------
# OperatorFeedbackRecord
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class OperatorFeedbackRecord:
    """Captures Operator feedback as a governed record.

    Does not directly verify, promote, commit, canonize, or mutate policy.
    """

    feedback_id: str
    feedback_type: OperatorFeedbackType
    sentiment: OperatorFeedbackSentiment
    target_ref: OperatorFeedbackTargetRef
    actor_id: str
    limitations: tuple[str, ...]
    salience: float = 0.5
    raw_text: str | None = None
    rating: int | None = None
    correction_text: str | None = None
    proposed_action: str | None = None
    source_trace_event_ref: TraceEventRef | None = None
    created_at: str = ""

    def __post_init__(self) -> None:
        if not self.feedback_id or not self.feedback_id.strip():
            raise ValueError("feedback_id must not be empty")
        if self.feedback_type is None:
            raise ValueError("feedback_type must not be None")
        if self.sentiment is None:
            raise ValueError("sentiment must not be None")
        if self.target_ref is None:
            raise ValueError("target_ref must not be None")
        if not self.actor_id or not self.actor_id.strip():
            raise ValueError("actor_id must not be empty")
        if not self.limitations:
            raise ValueError("limitations must be non-empty")
        if not (0.0 <= self.salience <= 1.0):
            raise ValueError("salience must be in range [0.0, 1.0]")
        if self.rating is not None and not (0 <= self.rating <= 10):
            raise ValueError("rating must be in range [0, 10]")
        if not self.created_at or not self.created_at.strip():
            raise ValueError("created_at must not be empty")

        has_content = (
            self.raw_text
            or self.rating is not None
            or self.correction_text
            or self.proposed_action
        )
        if not has_content:
            raise ValueError(
                "at least one of raw_text, rating, correction_text, or proposed_action "
                "must be present"
            )


# ---------------------------------------------------------------------------
# FeedbackProcessingReport
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class FeedbackProcessingReport:
    """Explains how feedback was interpreted and what candidate actions were produced or blocked.

    Cannot silently promote, commit, skill, reflex, canonize, or mutate policy.
    If an attempted automatic action is blocked, it is recorded in blocked_actions[].
    """

    report_id: str
    feedback_id: str
    target_ref: OperatorFeedbackTargetRef
    signal_strength: FeedbackSignalStrength
    candidate_actions: tuple[FeedbackCandidateAction, ...]
    created_candidates: tuple[str, ...]
    blocked_actions: tuple[str, ...]
    reason: str
    warnings: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()
    created_at: str = ""

    def __post_init__(self) -> None:
        if not self.report_id or not self.report_id.strip():
            raise ValueError("report_id must not be empty")
        if not self.feedback_id or not self.feedback_id.strip():
            raise ValueError("feedback_id must not be empty")
        if self.target_ref is None:
            raise ValueError("target_ref must not be None")
        if self.signal_strength is None:
            raise ValueError("signal_strength must not be None")
        if not self.reason or not self.reason.strip():
            raise ValueError("reason must not be empty")
        if not self.created_at or not self.created_at.strip():
            raise ValueError("created_at must not be empty")


# ---------------------------------------------------------------------------
# derive_signal_strength
# ---------------------------------------------------------------------------


def derive_signal_strength(feedback: OperatorFeedbackRecord) -> FeedbackSignalStrength:
    """Deterministic signal strength from feedback type and content.

    Derivation rules:
    - safety_concern or policy_concern → blocking
    - correction → strong
    - approval/rejection/capability_feedback/evaluation_feedback with trace ref → strong
    - approval/rejection/etc without trace ref (projection-only) → moderate
    - memory_candidate/preference_signal → weak
    - rating only → weak
    - needs_review → moderate
    - default → weak
    """
    blocking_types = {
        OperatorFeedbackType.SAFETY_CONCERN,
        OperatorFeedbackType.POLICY_CONCERN,
    }
    if feedback.feedback_type in blocking_types:
        return FeedbackSignalStrength.BLOCKING

    if feedback.feedback_type == OperatorFeedbackType.CORRECTION:
        return FeedbackSignalStrength.STRONG

    strong_types = {
        OperatorFeedbackType.APPROVAL,
        OperatorFeedbackType.REJECTION,
        OperatorFeedbackType.CAPABILITY_FEEDBACK,
        OperatorFeedbackType.EVALUATION_FEEDBACK,
    }
    if feedback.feedback_type in strong_types:
        if (
            feedback.source_trace_event_ref is not None
            or feedback.target_ref.source_trace_event_ref is not None
        ):
            return FeedbackSignalStrength.STRONG
        return FeedbackSignalStrength.MODERATE

    if feedback.feedback_type == OperatorFeedbackType.NEEDS_REVIEW:
        return FeedbackSignalStrength.MODERATE

    if feedback.feedback_type == OperatorFeedbackType.RATING:
        if feedback.rating is not None and feedback.rating >= 7:
            return FeedbackSignalStrength.MODERATE
        return FeedbackSignalStrength.WEAK

    weak_types = {
        OperatorFeedbackType.MEMORY_CANDIDATE,
        OperatorFeedbackType.PREFERENCE_SIGNAL,
    }
    if feedback.feedback_type in weak_types:
        return FeedbackSignalStrength.WEAK

    return FeedbackSignalStrength.WEAK


# ---------------------------------------------------------------------------
# Serialization helpers
# ---------------------------------------------------------------------------


def operator_feedback_target_ref_to_dict(
    ref: OperatorFeedbackTargetRef,
) -> dict[str, object]:
    return {
        "target_id": ref.target_id,
        "target_type": ref.target_type.value,
        "source_trace_event_ref": (
            asdict(ref.source_trace_event_ref)
            if ref.source_trace_event_ref else None
        ),
        "source_event_hash": ref.source_event_hash,
    }


def operator_feedback_record_to_dict(
    record: OperatorFeedbackRecord,
) -> dict[str, object]:
    return {
        "feedback_id": record.feedback_id,
        "feedback_type": record.feedback_type.value,
        "sentiment": record.sentiment.value,
        "target_ref": operator_feedback_target_ref_to_dict(record.target_ref),
        "actor_id": record.actor_id,
        "limitations": list(record.limitations),
        "salience": record.salience,
        "raw_text": record.raw_text,
        "rating": record.rating,
        "correction_text": record.correction_text,
        "proposed_action": record.proposed_action,
        "source_trace_event_ref": (
            asdict(record.source_trace_event_ref)
            if record.source_trace_event_ref else None
        ),
        "created_at": record.created_at,
    }


def feedback_processing_report_to_dict(
    report: FeedbackProcessingReport,
) -> dict[str, object]:
    return {
        "report_id": report.report_id,
        "feedback_id": report.feedback_id,
        "target_ref": operator_feedback_target_ref_to_dict(report.target_ref),
        "signal_strength": report.signal_strength.value,
        "candidate_actions": [a.value for a in report.candidate_actions],
        "created_candidates": list(report.created_candidates),
        "blocked_actions": list(report.blocked_actions),
        "reason": report.reason,
        "warnings": list(report.warnings),
        "errors": list(report.errors),
        "created_at": report.created_at,
    }
