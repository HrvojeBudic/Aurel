"""P1.5.17 Operator feedback processing logic.

Converts governed operator feedback into candidate actions.
Feedback may influence future evaluation, memory candidates, capability review,
or priority, but it may not directly verify, commit, promote, canonize, or mutate.
"""
from __future__ import annotations

import uuid
from typing import Any

from agentic_runtime.contracts.capability_claims import (
    CapabilityClaim,
    CapabilityClaimStatus,
)
from agentic_runtime.contracts.evaluation_cases import EvaluationCase
from agentic_runtime.contracts.evaluation_runtime import EvaluationRunResult
from agentic_runtime.contracts.operator_feedback import (
    FeedbackCandidateAction,
    FeedbackProcessingReport,
    FeedbackSignalStrength,
    OperatorFeedbackRecord,
    OperatorFeedbackType,
    derive_signal_strength,
)
from agentic_runtime.contracts.trace import TraceEventRef

_PROCESSING_TIMESTAMP = "2026-06-22T00:00:00+00:00"

# Actions that are ALWAYS blocked (they represent automatic promotion/mutation).
_ALWAYS_BLOCKED = frozenset({
    "verify_capability",
    "commit_memory",
    "promote_skill",
    "create_skill",
    "create_reflex",
    "mutate_policy",
    "change_policy",
    "rewrite_trace",
    "canonize_roadmap",
    "override_verifier",
    "universalize_claim",
    "erase_limitation",
    "demote_skill",
    "canon_memory",
    "skill_memory",
})

# Actions that may be allowed as candidates (not automatic).
_APPROVAL_ALLOWED = frozenset({
    FeedbackCandidateAction.CREATE_EVAL_CANDIDATE,
    FeedbackCandidateAction.RAISE_REVIEW_PRIORITY,
    FeedbackCandidateAction.ATTACH_LIMITATION,
})

_REJECTION_ALLOWED = frozenset({
    FeedbackCandidateAction.MARK_CLAIM_NEEDS_REVIEW,
    FeedbackCandidateAction.CREATE_REGRESSION_CANDIDATE,
    FeedbackCandidateAction.LOWER_CLAIM_CONFIDENCE,
    FeedbackCandidateAction.RAISE_REVIEW_PRIORITY,
})

_CORRECTION_ALLOWED = frozenset({
    FeedbackCandidateAction.CREATE_REGRESSION_CANDIDATE,
    FeedbackCandidateAction.CREATE_MEMORY_CANDIDATE,
    FeedbackCandidateAction.MARK_CLAIM_NEEDS_REVIEW,
    FeedbackCandidateAction.ATTACH_LIMITATION,
    FeedbackCandidateAction.LOWER_CLAIM_CONFIDENCE,
})

_MEMORY_CANDIDATE_ALLOWED = frozenset({
    FeedbackCandidateAction.CREATE_MEMORY_CANDIDATE,
})

_SAFETY_ALLOWED = frozenset({
    FeedbackCandidateAction.MARK_CLAIM_NEEDS_REVIEW,
    FeedbackCandidateAction.RAISE_REVIEW_PRIORITY,
})

_CAPABILITY_ALLOWED = frozenset({
    FeedbackCandidateAction.RAISE_REVIEW_PRIORITY,
    FeedbackCandidateAction.MARK_CLAIM_NEEDS_REVIEW,
    FeedbackCandidateAction.ATTACH_LIMITATION,
    FeedbackCandidateAction.LOWER_CLAIM_CONFIDENCE,
})


def _new_report_id() -> str:
    return f"fb_report_{uuid.uuid4().hex[:12]}"


def _new_candidate_id() -> str:
    return f"fbc_{uuid.uuid4().hex[:12]}"


def process_operator_feedback(
    feedback: OperatorFeedbackRecord,
    *,
    capability_claim: CapabilityClaim | None = None,
    evaluation_case: EvaluationCase | None = None,
    evaluation_run_result: EvaluationRunResult | None = None,
    trace_event_ref: TraceEventRef | None = None,
    **_kwargs: Any,
) -> FeedbackProcessingReport:
    """Process operator feedback and produce a governed report with candidate actions.

    The feedback type determines which candidate actions are allowed.
    All automatic promotion/mutation actions are blocked.
    """
    signal_strength = derive_signal_strength(feedback)
    fb_type = feedback.feedback_type

    candidate_actions: list[FeedbackCandidateAction] = []
    blocked_actions: list[str] = list(_ALWAYS_BLOCKED)
    created_candidates: list[str] = []
    warnings: list[str] = []
    errors: list[str] = []
    reason_parts: list[str] = []

    reason_parts.append(f"Processing feedback type={fb_type.value} sentiment={feedback.sentiment.value}")

    # ---------------------------------------------------------------
    # Approval
    # ---------------------------------------------------------------
    if fb_type == OperatorFeedbackType.APPROVAL:
        reason_parts.append("Operator approved the target.")
        _add_if_allowed(
            FeedbackCandidateAction.CREATE_EVAL_CANDIDATE,
            _APPROVAL_ALLOWED, candidate_actions, created_candidates,
        )
        _add_if_allowed(
            FeedbackCandidateAction.RAISE_REVIEW_PRIORITY,
            _APPROVAL_ALLOWED, candidate_actions, created_candidates,
        )
        if feedback.raw_text and _has_limitation_language(feedback.raw_text):
            _add_if_allowed(
                FeedbackCandidateAction.ATTACH_LIMITATION,
                _APPROVAL_ALLOWED, candidate_actions, created_candidates,
            )
        warnings.append(
            "Approval is a support signal only. It does not automatically verify, "
            "commit, promote, or canonize anything."
        )

    # ---------------------------------------------------------------
    # Rejection
    # ---------------------------------------------------------------
    elif fb_type == OperatorFeedbackType.REJECTION:
        reason_parts.append("Operator rejected the target.")
        _add_if_allowed(
            FeedbackCandidateAction.MARK_CLAIM_NEEDS_REVIEW,
            _REJECTION_ALLOWED, candidate_actions, created_candidates,
        )
        _add_if_allowed(
            FeedbackCandidateAction.CREATE_REGRESSION_CANDIDATE,
            _REJECTION_ALLOWED, candidate_actions, created_candidates,
        )
        _add_if_allowed(
            FeedbackCandidateAction.LOWER_CLAIM_CONFIDENCE,
            _REJECTION_ALLOWED, candidate_actions, created_candidates,
        )
        _add_if_allowed(
            FeedbackCandidateAction.RAISE_REVIEW_PRIORITY,
            _REJECTION_ALLOWED, candidate_actions, created_candidates,
        )
        warnings.append(
            "Rejection marks claims for review but does not auto-delete or auto-downgrade."
        )

    # ---------------------------------------------------------------
    # Correction
    # ---------------------------------------------------------------
    elif fb_type == OperatorFeedbackType.CORRECTION:
        reason_parts.append("Operator provided a correction.")
        _add_if_allowed(
            FeedbackCandidateAction.CREATE_REGRESSION_CANDIDATE,
            _CORRECTION_ALLOWED, candidate_actions, created_candidates,
        )
        _add_if_allowed(
            FeedbackCandidateAction.CREATE_MEMORY_CANDIDATE,
            _CORRECTION_ALLOWED, candidate_actions, created_candidates,
        )
        _add_if_allowed(
            FeedbackCandidateAction.MARK_CLAIM_NEEDS_REVIEW,
            _CORRECTION_ALLOWED, candidate_actions, created_candidates,
        )
        _add_if_allowed(
            FeedbackCandidateAction.ATTACH_LIMITATION,
            _CORRECTION_ALLOWED, candidate_actions, created_candidates,
        )
        _add_if_allowed(
            FeedbackCandidateAction.LOWER_CLAIM_CONFIDENCE,
            _CORRECTION_ALLOWED, candidate_actions, created_candidates,
        )
        warnings.append(
            "Correction creates candidates for review. It does not rewrite canonical "
            "trace, auto-change committed memory, auto-change policy, or auto-demote skill."
        )

    # ---------------------------------------------------------------
    # Memory candidate
    # ---------------------------------------------------------------
    elif fb_type == OperatorFeedbackType.MEMORY_CANDIDATE:
        reason_parts.append("Operator requested a memory candidate.")
        _add_if_allowed(
            FeedbackCandidateAction.CREATE_MEMORY_CANDIDATE,
            _MEMORY_CANDIDATE_ALLOWED, candidate_actions, created_candidates,
        )
        warnings.append(
            "Memory candidate created. P1.5.17 does not commit memory. "
            "Actual MemoryCandidate bridge comes in P1.5.18."
        )

    # ---------------------------------------------------------------
    # Capability feedback
    # ---------------------------------------------------------------
    elif fb_type == OperatorFeedbackType.CAPABILITY_FEEDBACK:
        if feedback.sentiment.value in ("positive",):
            reason_parts.append("Positive capability feedback — raising review priority.")
            _add_if_allowed(
                FeedbackCandidateAction.RAISE_REVIEW_PRIORITY,
                _CAPABILITY_ALLOWED, candidate_actions, created_candidates,
            )
            warnings.append(
                "Positive operator feedback on capability is a support signal. "
                "It does not create a verified claim alone. "
                "Operator feedback alone cannot universalize a context_verified claim."
            )
        else:
            reason_parts.append("Negative/mixed capability feedback — marking for review.")
            _add_if_allowed(
                FeedbackCandidateAction.MARK_CLAIM_NEEDS_REVIEW,
                _CAPABILITY_ALLOWED, candidate_actions, created_candidates,
            )
            _add_if_allowed(
                FeedbackCandidateAction.LOWER_CLAIM_CONFIDENCE,
                _CAPABILITY_ALLOWED, candidate_actions, created_candidates,
            )
            _add_if_allowed(
                FeedbackCandidateAction.ATTACH_LIMITATION,
                _CAPABILITY_ALLOWED, candidate_actions, created_candidates,
            )

    # ---------------------------------------------------------------
    # Evaluation feedback
    # ---------------------------------------------------------------
    elif fb_type == OperatorFeedbackType.EVALUATION_FEEDBACK:
        if feedback.sentiment.value in ("positive",):
            reason_parts.append("Positive evaluation feedback.")
            _add_if_allowed(
                FeedbackCandidateAction.CREATE_EVAL_CANDIDATE,
                _APPROVAL_ALLOWED, candidate_actions, created_candidates,
            )
            _add_if_allowed(
                FeedbackCandidateAction.RAISE_REVIEW_PRIORITY,
                _APPROVAL_ALLOWED, candidate_actions, created_candidates,
            )
        else:
            reason_parts.append("Negative/mixed evaluation feedback.")
            _add_if_allowed(
                FeedbackCandidateAction.CREATE_REGRESSION_CANDIDATE,
                _CORRECTION_ALLOWED, candidate_actions, created_candidates,
            )
            _add_if_allowed(
                FeedbackCandidateAction.MARK_CLAIM_NEEDS_REVIEW,
                _CORRECTION_ALLOWED, candidate_actions, created_candidates,
            )

    # ---------------------------------------------------------------
    # Safety / policy concern
    # ---------------------------------------------------------------
    elif fb_type in (OperatorFeedbackType.SAFETY_CONCERN, OperatorFeedbackType.POLICY_CONCERN):
        reason_parts.append(f"{fb_type.value} — blocking signal.")
        _add_if_allowed(
            FeedbackCandidateAction.MARK_CLAIM_NEEDS_REVIEW,
            _SAFETY_ALLOWED, candidate_actions, created_candidates,
        )
        _add_if_allowed(
            FeedbackCandidateAction.RAISE_REVIEW_PRIORITY,
            _SAFETY_ALLOWED, candidate_actions, created_candidates,
        )
        warnings.append(
            f"{fb_type.value} creates a blocking signal. "
            "It does not silently mutate policy or execute blocks without policy engine."
        )

    # ---------------------------------------------------------------
    # Rating
    # ---------------------------------------------------------------
    elif fb_type == OperatorFeedbackType.RATING:
        reason_parts.append(f"Rating feedback (rating={feedback.rating}).")
        _add_if_allowed(
            FeedbackCandidateAction.RAISE_REVIEW_PRIORITY,
            _APPROVAL_ALLOWED, candidate_actions, created_candidates,
        )

    # ---------------------------------------------------------------
    # Needs review
    # ---------------------------------------------------------------
    elif fb_type == OperatorFeedbackType.NEEDS_REVIEW:
        reason_parts.append("Operator marked target as needing review.")
        _add_if_allowed(
            FeedbackCandidateAction.MARK_CLAIM_NEEDS_REVIEW,
            _CAPABILITY_ALLOWED, candidate_actions, created_candidates,
        )

    # ---------------------------------------------------------------
    # Preference signal
    # ---------------------------------------------------------------
    elif fb_type == OperatorFeedbackType.PREFERENCE_SIGNAL:
        reason_parts.append("Preference signal — no strong candidate actions derived.")
        warnings.append(
            "Preference signals are weak evidence. No candidate actions generated."
        )

    # ---------------------------------------------------------------
    # Default fallback
    # ---------------------------------------------------------------
    else:
        reason_parts.append("Unknown or unhandled feedback type.")
        warnings.append("Feedback type not fully handled — defaulting to no action.")
        candidate_actions.append(FeedbackCandidateAction.NO_ACTION)

    # ---------------------------------------------------------------
    # Assemble report
    # ---------------------------------------------------------------
    reason = ". ".join(reason_parts) + "."

    return FeedbackProcessingReport(
        report_id=_new_report_id(),
        feedback_id=feedback.feedback_id,
        target_ref=feedback.target_ref,
        signal_strength=signal_strength,
        candidate_actions=tuple(candidate_actions),
        created_candidates=tuple(created_candidates),
        blocked_actions=tuple(sorted(blocked_actions)),
        reason=reason,
        warnings=tuple(warnings),
        errors=tuple(errors),
        created_at=_PROCESSING_TIMESTAMP,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _add_if_allowed(
    action: FeedbackCandidateAction,
    allowed_set: frozenset[FeedbackCandidateAction],
    candidate_actions: list[FeedbackCandidateAction],
    created_candidates: list[str],
) -> None:
    """Add candidate action if allowed by the current feedback type's rules."""
    if action in allowed_set:
        candidate_actions.append(action)
        created_candidates.append(f"{action.value}__{_new_candidate_id()}")


def _has_limitation_language(raw_text: str) -> bool:
    """Check if feedback text contains limitation-suggesting language."""
    markers = (
        "but", "however", "limitation", "limit", "not always",
        "only works", "does not", "should be scoped", "not universal",
        "bounded", "scope", "partial", "conditional",
    )
    text_lower = raw_text.lower()
    return any(m in text_lower for m in markers)
