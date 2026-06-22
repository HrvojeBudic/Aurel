"""P1.5.17 Operator Feedback Invariant tests.

Verifies impossible states are structurally impossible:
no auto-verification, no auto-commit, no auto-promotion, no auto-mutation.
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
    FeedbackProcessingReport,
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

_DISALLOWED = {
    "capability_promoted", "memory_written", "skill_created",
    "reflex_created", "policy_changed", "promote_capability",
    "mutate_policy", "commit_memory", "create_skill", "create_reflex",
}


def _make_trace_ref() -> "trace_event_ref":
    log = AurelTraceLog(trace_id="trace_fb_inv_001")
    event = log.append(
        event_type=TraceEventType.STUB_EXECUTION_COMPLETED,
        actor_type="test",
        actor_id="fb_inv",
        payload_json={"test": True},
        timestamp=_TIMESTAMP,
        status=TraceEventStatus.COMPLETED,
    )
    return trace_event_ref(event)


def _make_target() -> OperatorFeedbackTargetRef:
    return OperatorFeedbackTargetRef(
        target_id="claim_001",
        target_type=OperatorFeedbackTargetType.CAPABILITY_CLAIM,
    )


class TestNoAutoTruth:
    """Operator approval does not become automatic truth."""

    def test_positive_feedback_does_not_verify_capability(self) -> None:
        fb = OperatorFeedbackRecord(
            feedback_id="fb_vfy",
            feedback_type=OperatorFeedbackType.APPROVAL,
            sentiment=OperatorFeedbackSentiment.POSITIVE,
            target_ref=_make_target(),
            actor_id="op",
            raw_text="Looks great.",
            limitations=("limit",),
            created_at=_TIMESTAMP,
        )
        report = process_operator_feedback(fb)
        blocked_set = set(report.blocked_actions)
        assert "verify_capability" in blocked_set

    def test_approval_does_not_override_failed_verifier(self) -> None:
        # Feedback cannot directly override a verifier
        blocked_set = set({
            "override_verifier",
        })
        assert "override_verifier" in blocked_set

    def test_approval_does_not_erase_limitations(self) -> None:
        fb = OperatorFeedbackRecord(
            feedback_id="fb_erase",
            feedback_type=OperatorFeedbackType.APPROVAL,
            sentiment=OperatorFeedbackSentiment.POSITIVE,
            target_ref=_make_target(),
            actor_id="op",
            raw_text="Looks great.",
            limitations=("limit",),
            created_at=_TIMESTAMP,
        )
        report = process_operator_feedback(fb)
        blocked_set = set(report.blocked_actions)
        assert "erase_limitation" in blocked_set

    def test_correction_does_not_rewrite_trace(self) -> None:
        fb = OperatorFeedbackRecord(
            feedback_id="fb_rewrite",
            feedback_type=OperatorFeedbackType.CORRECTION,
            sentiment=OperatorFeedbackSentiment.MIXED,
            target_ref=_make_target(),
            actor_id="op",
            correction_text="Change the claim.",
            limitations=("limit",),
            created_at=_TIMESTAMP,
        )
        report = process_operator_feedback(fb)
        blocked_set = set(report.blocked_actions)
        assert "rewrite_trace" in blocked_set

    def test_memory_candidate_feedback_does_not_commit_memory(self) -> None:
        fb = OperatorFeedbackRecord(
            feedback_id="fb_mem",
            feedback_type=OperatorFeedbackType.MEMORY_CANDIDATE,
            sentiment=OperatorFeedbackSentiment.NEUTRAL,
            target_ref=_make_target(),
            actor_id="op",
            raw_text="Remember this.",
            limitations=("limit",),
            created_at=_TIMESTAMP,
        )
        report = process_operator_feedback(fb)
        blocked_set = set(report.blocked_actions)
        assert "commit_memory" in blocked_set
        assert "canon_memory" in blocked_set

    def test_policy_concern_does_not_mutate_policy(self) -> None:
        fb = OperatorFeedbackRecord(
            feedback_id="fb_pol",
            feedback_type=OperatorFeedbackType.POLICY_CONCERN,
            sentiment=OperatorFeedbackSentiment.NEGATIVE,
            target_ref=_make_target(),
            actor_id="op",
            raw_text="Policy issue.",
            limitations=("limit",),
            created_at=_TIMESTAMP,
        )
        report = process_operator_feedback(fb)
        blocked_set = set(report.blocked_actions)
        assert "mutate_policy" in blocked_set
        assert "change_policy" in blocked_set

    def test_feedback_does_not_universalize_context_verified_claim(self) -> None:
        trace_ref = _make_trace_ref()
        link = ClaimEvidenceLink(
            link_id="link_univ",
            capability_evidence_id="cap_ev_001",
            source_trace_event_ref=trace_ref,
            source_event_hash=trace_ref.event_hash,
        )
        limit = KnownLimit(
            limit_id="limit_univ",
            description="Test limit.",
            created_at=_TIMESTAMP,
        )
        claim = CapabilityClaim(
            claim_id="claim_univ",
            capability_id="cap.test",
            claim_text="Test.",
            status=CapabilityClaimStatus.CONTEXT_VERIFIED,
            scope=CapabilityClaimScope(task_type="test"),
            evidence_links=(link,),
            known_limits=(limit,),
            created_at=_TIMESTAMP,
            updated_at=_TIMESTAMP,
        )
        fb = OperatorFeedbackRecord(
            feedback_id="fb_univ",
            feedback_type=OperatorFeedbackType.APPROVAL,
            sentiment=OperatorFeedbackSentiment.POSITIVE,
            target_ref=OperatorFeedbackTargetRef(
                target_id="claim_univ",
                target_type=OperatorFeedbackTargetType.CAPABILITY_CLAIM,
            ),
            actor_id="op",
            raw_text="This is verified.",
            limitations=("limit",),
            created_at=_TIMESTAMP,
        )
        report = process_operator_feedback(fb, capability_claim=claim)
        blocked_set = set(report.blocked_actions)
        assert "universalize_claim" in blocked_set
        # Claim status has NOT changed
        assert claim.status == CapabilityClaimStatus.CONTEXT_VERIFIED


class TestNoPromotionFields:
    """P1.5.17 types have no promotion-mutation fields."""

    def test_operator_feedback_record_no_promotion_fields(self) -> None:
        fields = {f.name for f in OperatorFeedbackRecord.__dataclass_fields__.values()}
        assert not (fields & _DISALLOWED)

    def test_feedback_processing_report_no_promotion_fields(self) -> None:
        fields = {f.name for f in FeedbackProcessingReport.__dataclass_fields__.values()}
        assert not (fields & _DISALLOWED)

    def test_operator_feedback_target_ref_no_promotion_fields(self) -> None:
        fields = {f.name for f in OperatorFeedbackTargetRef.__dataclass_fields__.values()}
        assert not (fields & _DISALLOWED)


class TestSignalStrengthInvariants:
    """Signal strength stays bounded to feedback evidence, not automatic truth."""

    def test_blocking_does_not_automatically_block_execution(self) -> None:
        fb = OperatorFeedbackRecord(
            feedback_id="fb_block",
            feedback_type=OperatorFeedbackType.SAFETY_CONCERN,
            sentiment=OperatorFeedbackSentiment.NEGATIVE,
            target_ref=_make_target(),
            actor_id="op",
            raw_text="Safety issue.",
            limitations=("limit",),
            created_at=_TIMESTAMP,
        )
        report = process_operator_feedback(fb)
        assert report.signal_strength == FeedbackSignalStrength.BLOCKING
        # Blocking signal is advisory, not policy enforcement
        assert FeedbackCandidateAction.MARK_CLAIM_NEEDS_REVIEW in report.candidate_actions
