"""P1.5.17 Feedback Processing tests.

Verifies that process_operator_feedback produces correct candidate actions
for each feedback type, and that auto-promotion is blocked.
"""
from __future__ import annotations

from agentic_runtime.contracts.capability_claims import (
    CapabilityClaim,
    CapabilityClaimScope,
    CapabilityClaimStatus,
    ClaimEvidenceLink,
    KnownLimit,
)
from agentic_runtime.contracts.operator_feedback import (
    FeedbackCandidateAction,
    FeedbackSignalStrength,
    OperatorFeedbackRecord,
    OperatorFeedbackSentiment,
    OperatorFeedbackTargetRef,
    OperatorFeedbackTargetType,
    OperatorFeedbackType,
)
from agentic_runtime.contracts.trace import (
    AurelTraceLog,
    TraceEventStatus,
    TraceEventType,
    trace_event_ref,
)
from agentic_runtime.evaluation.feedback_processing import process_operator_feedback

_TIMESTAMP = "2026-06-22T00:00:00+00:00"


def _make_trace_ref() -> "trace_event_ref":
    log = AurelTraceLog(trace_id="trace_fb_proc_001")
    event = log.append(
        event_type=TraceEventType.STUB_EXECUTION_COMPLETED,
        actor_type="test",
        actor_id="fb_proc",
        payload_json={"test": True},
        timestamp=_TIMESTAMP,
        status=TraceEventStatus.COMPLETED,
    )
    return trace_event_ref(event)


def _make_target(
    target_type=OperatorFeedbackTargetType.CAPABILITY_CLAIM,
) -> OperatorFeedbackTargetRef:
    return OperatorFeedbackTargetRef(
        target_id="claim_001",
        target_type=target_type,
    )


def _make_feedback(
    fb_type=OperatorFeedbackType.APPROVAL,
    sentiment=OperatorFeedbackSentiment.POSITIVE,
    target=None,
    raw_text="Looks good.",
) -> OperatorFeedbackRecord:
    return OperatorFeedbackRecord(
        feedback_id="fb_001",
        feedback_type=fb_type,
        sentiment=sentiment,
        target_ref=target or _make_target(),
        actor_id="op",
        raw_text=raw_text,
        limitations=("Test limitation.",),
        created_at=_TIMESTAMP,
    )


def _make_claim(status=CapabilityClaimStatus.CONTEXT_VERIFIED) -> CapabilityClaim:
    trace_ref = _make_trace_ref()
    link = ClaimEvidenceLink(
        link_id="link_001",
        capability_evidence_id="cap_ev_001",
        source_trace_event_ref=trace_ref,
        source_event_hash=trace_ref.event_hash,
    )
    limit = KnownLimit(
        limit_id="limit_001",
        description="Test limit.",
        created_at=_TIMESTAMP,
    )
    return CapabilityClaim(
        claim_id="claim_001",
        capability_id="cap.test",
        claim_text="Test capability claim.",
        status=status,
        scope=CapabilityClaimScope(task_type="test"),
        evidence_links=(link,),
        known_limits=(limit,),
        created_at=_TIMESTAMP,
        updated_at=_TIMESTAMP,
    )


class TestApprovalProcessing:
    """Approval creates support signals only."""

    def test_approval_creates_support_signal_only(self) -> None:
        fb = _make_feedback(fb_type=OperatorFeedbackType.APPROVAL)
        claim = _make_claim()
        report = process_operator_feedback(fb, capability_claim=claim)
        assert report.signal_strength == FeedbackSignalStrength.MODERATE
        assert FeedbackCandidateAction.CREATE_EVAL_CANDIDATE in report.candidate_actions
        assert FeedbackCandidateAction.RAISE_REVIEW_PRIORITY in report.candidate_actions
        assert len(report.blocked_actions) > 0
        assert any("verify_capability" in b for b in report.blocked_actions)

    def test_approval_does_not_verify_capability(self) -> None:
        fb = _make_feedback(fb_type=OperatorFeedbackType.APPROVAL)
        claim = _make_claim()
        report = process_operator_feedback(fb, capability_claim=claim)
        blocked_set = set(report.blocked_actions)
        assert "verify_capability" in blocked_set
        assert claim.status == CapabilityClaimStatus.CONTEXT_VERIFIED

    def test_approval_with_limitation_text_adds_attach_limitation(self) -> None:
        fb = _make_feedback(
            fb_type=OperatorFeedbackType.APPROVAL,
            raw_text="Looks good, but the scope is limited.",
        )
        claim = _make_claim()
        report = process_operator_feedback(fb, capability_claim=claim)
        assert FeedbackCandidateAction.ATTACH_LIMITATION in report.candidate_actions


class TestRejectionProcessing:
    """Rejection marks claims for review."""

    def test_rejection_marks_claim_needs_review_action(self) -> None:
        fb = _make_feedback(
            fb_type=OperatorFeedbackType.REJECTION,
            sentiment=OperatorFeedbackSentiment.NEGATIVE,
            raw_text="This claim is wrong.",
        )
        claim = _make_claim()
        report = process_operator_feedback(fb, capability_claim=claim)
        assert FeedbackCandidateAction.MARK_CLAIM_NEEDS_REVIEW in report.candidate_actions
        assert FeedbackCandidateAction.CREATE_REGRESSION_CANDIDATE in report.candidate_actions
        assert FeedbackCandidateAction.LOWER_CLAIM_CONFIDENCE in report.candidate_actions


class TestCorrectionProcessing:
    """Correction creates regression candidates."""

    def test_correction_creates_regression_candidate_action(self) -> None:
        fb = _make_feedback(
            fb_type=OperatorFeedbackType.CORRECTION,
            sentiment=OperatorFeedbackSentiment.MIXED,
            raw_text="The claim should say 'partial' not 'full' capability.",
        )
        claim = _make_claim()
        report = process_operator_feedback(fb, capability_claim=claim)
        assert FeedbackCandidateAction.CREATE_REGRESSION_CANDIDATE in report.candidate_actions
        assert FeedbackCandidateAction.CREATE_MEMORY_CANDIDATE in report.candidate_actions
        assert FeedbackCandidateAction.MARK_CLAIM_NEEDS_REVIEW in report.candidate_actions


class TestMemoryCandidateProcessing:
    """Memory candidate feedback creates memory candidate action only."""

    def test_memory_candidate_feedback_creates_memory_candidate_action(self) -> None:
        fb = _make_feedback(
            fb_type=OperatorFeedbackType.MEMORY_CANDIDATE,
            sentiment=OperatorFeedbackSentiment.NEUTRAL,
            raw_text="Remember this pattern.",
        )
        report = process_operator_feedback(fb)
        assert FeedbackCandidateAction.CREATE_MEMORY_CANDIDATE in report.candidate_actions
        assert FeedbackCandidateAction.CREATE_EVAL_CANDIDATE not in report.candidate_actions


class TestCapabilityFeedbackProcessing:
    """Capability feedback governed by origin, not just content."""

    def test_capability_negative_feedback_marks_claim_needs_review_action(self) -> None:
        fb = _make_feedback(
            fb_type=OperatorFeedbackType.CAPABILITY_FEEDBACK,
            sentiment=OperatorFeedbackSentiment.NEGATIVE,
            raw_text="This capability is overstated.",
        )
        claim = _make_claim()
        report = process_operator_feedback(fb, capability_claim=claim)
        assert FeedbackCandidateAction.MARK_CLAIM_NEEDS_REVIEW in report.candidate_actions

    def test_capability_positive_feedback_raises_priority(self) -> None:
        fb = _make_feedback(
            fb_type=OperatorFeedbackType.CAPABILITY_FEEDBACK,
            sentiment=OperatorFeedbackSentiment.POSITIVE,
            raw_text="This capability is accurate.",
        )
        claim = _make_claim()
        report = process_operator_feedback(fb, capability_claim=claim)
        assert FeedbackCandidateAction.RAISE_REVIEW_PRIORITY in report.candidate_actions


class TestSafetyAndPolicyProcessing:
    """Safety and policy concerns create blocking signals."""

    def test_safety_concern_creates_blocking_signal(self) -> None:
        fb = _make_feedback(
            fb_type=OperatorFeedbackType.SAFETY_CONCERN,
            sentiment=OperatorFeedbackSentiment.NEGATIVE,
            raw_text="This could be dangerous.",
        )
        report = process_operator_feedback(fb)
        assert report.signal_strength == FeedbackSignalStrength.BLOCKING
        assert FeedbackCandidateAction.MARK_CLAIM_NEEDS_REVIEW in report.candidate_actions

    def test_policy_concern_creates_blocking_signal(self) -> None:
        fb = _make_feedback(
            fb_type=OperatorFeedbackType.POLICY_CONCERN,
            sentiment=OperatorFeedbackSentiment.NEGATIVE,
            raw_text="This violates policy.",
        )
        report = process_operator_feedback(fb)
        assert report.signal_strength == FeedbackSignalStrength.BLOCKING


class TestCandidateOnly:
    """Processing produces candidates, not committed mutations."""

    def test_feedback_processing_report_records_candidate_actions(self) -> None:
        fb = _make_feedback()
        report = process_operator_feedback(fb)
        assert len(report.candidate_actions) > 0

    def test_feedback_processing_report_records_blocked_auto_promotion(self) -> None:
        fb = _make_feedback()
        report = process_operator_feedback(fb)
        assert len(report.blocked_actions) > 0
        blocked_set = set(report.blocked_actions)
        assert "verify_capability" in blocked_set

    def test_feedback_processing_does_not_create_skill(self) -> None:
        fb = _make_feedback()
        report = process_operator_feedback(fb)
        blocked_set = set(report.blocked_actions)
        assert "create_skill" in blocked_set
        assert "promote_skill" in blocked_set

    def test_feedback_processing_does_not_create_reflex(self) -> None:
        fb = _make_feedback()
        report = process_operator_feedback(fb)
        assert "create_reflex" in set(report.blocked_actions)

    def test_feedback_processing_does_not_commit_memory(self) -> None:
        fb = _make_feedback()
        report = process_operator_feedback(fb)
        blocked_set = set(report.blocked_actions)
        assert "commit_memory" in blocked_set
        assert "canon_memory" in blocked_set
        assert "skill_memory" in blocked_set

    def test_feedback_processing_does_not_change_policy(self) -> None:
        fb = _make_feedback()
        report = process_operator_feedback(fb)
        blocked_set = set(report.blocked_actions)
        assert "mutate_policy" in blocked_set
        assert "change_policy" in blocked_set


class TestNeedsReviewProcessing:
    """Needs_review feedback type."""

    def test_needs_review_marks_claim_needs_review(self) -> None:
        fb = _make_feedback(
            fb_type=OperatorFeedbackType.NEEDS_REVIEW,
            sentiment=OperatorFeedbackSentiment.NEUTRAL,
            raw_text="This needs another look.",
        )
        claim = _make_claim()
        report = process_operator_feedback(fb, capability_claim=claim)
        assert FeedbackCandidateAction.MARK_CLAIM_NEEDS_REVIEW in report.candidate_actions
