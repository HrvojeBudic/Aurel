"""P1.5.18 Memory Candidate Derivation tests.

Verifies specific derivation rules for different input types:
feedback->candidate, correction->candidate, safety/policy->candidate, capability->candidate.
"""
from __future__ import annotations

from agentic_runtime.contracts.capability_claims import (
    CapabilityClaim,
    CapabilityClaimScope,
    CapabilityClaimStatus,
    ClaimEvidenceLink,
    KnownLimit,
)
from agentic_runtime.contracts.memory_candidates import (
    MemoryCandidate,
    MemoryCandidateBridgeReport,
    MemoryCandidateRiskClass,
    MemoryCandidateScope,
    MemoryCandidateScopeType,
    MemoryCandidateSourceType,
    MemoryCandidateStatus,
    MemoryCandidateType,
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
from agentic_runtime.evaluation.memory_candidate_bridge import (
    derive_memory_candidates,
)

_TIMESTAMP = "2026-06-22T00:00:00+00:00"


def _make_trace_ref(trace_id: str = "trace_mem_der_001") -> "trace_event_ref":
    log = AurelTraceLog(trace_id=trace_id)
    event = log.append(
        event_type=TraceEventType.STUB_EXECUTION_COMPLETED,
        actor_type="test",
        actor_id="mem_der",
        payload_json={"test": True},
        timestamp=_TIMESTAMP,
        status=TraceEventStatus.COMPLETED,
    )
    return trace_event_ref(event)


def _make_target(
    target_id: str = "target_001",
    trace_ref: "trace_event_ref | None" = None,
) -> OperatorFeedbackTargetRef:
    return OperatorFeedbackTargetRef(
        target_id=target_id,
        target_type=OperatorFeedbackTargetType.CAPABILITY_CLAIM,
        source_trace_event_ref=trace_ref,
        source_event_hash=trace_ref.event_hash if trace_ref else "",
    )


# ---------------------------------------------------------------------------
# Feedback -> operator_preference
# ---------------------------------------------------------------------------


def test_create_memory_candidate_action_produces_operator_preference() -> None:
    trace_ref = _make_trace_ref()
    fb = OperatorFeedbackRecord(
        feedback_id="fb_pref_001",
        feedback_type=OperatorFeedbackType.APPROVAL,
        sentiment=OperatorFeedbackSentiment.POSITIVE,
        target_ref=_make_target(trace_ref=trace_ref),
        actor_id="op",
        raw_text="Remember this.",
        source_trace_event_ref=trace_ref,
        limitations=("Test.",),
        created_at=_TIMESTAMP,
    )
    fb_report = FeedbackProcessingReport(
        report_id="fpr_pref_001",
        feedback_id=fb.feedback_id,
        target_ref=fb.target_ref,
        signal_strength=FeedbackSignalStrength.MODERATE,
        candidate_actions=(FeedbackCandidateAction.CREATE_MEMORY_CANDIDATE,),
        created_candidates=(),
        blocked_actions=(),
        reason="Operator wants to remember.",
        warnings=(),
        errors=(),
        created_at=_TIMESTAMP,
    )
    result = derive_memory_candidates(
        operator_feedback=fb,
        feedback_report=fb_report,
        trace_event_ref=trace_ref,
    )
    assert result.created_memory_candidate_ids
    assert not result.errors


# ---------------------------------------------------------------------------
# Correction -> operator_correction
# ---------------------------------------------------------------------------


def test_correction_produces_operator_correction() -> None:
    trace_ref = _make_trace_ref()
    fb = OperatorFeedbackRecord(
        feedback_id="fb_corr_001",
        feedback_type=OperatorFeedbackType.CORRECTION,
        sentiment=OperatorFeedbackSentiment.NEUTRAL,
        target_ref=_make_target(trace_ref=trace_ref),
        actor_id="op",
        correction_text="This is wrong, it should be X.",
        source_trace_event_ref=trace_ref,
        limitations=("Test.",),
        created_at=_TIMESTAMP,
    )
    fb_report = FeedbackProcessingReport(
        report_id="fpr_corr_001",
        feedback_id=fb.feedback_id,
        target_ref=fb.target_ref,
        signal_strength=FeedbackSignalStrength.MODERATE,
        candidate_actions=(),
        created_candidates=(),
        blocked_actions=(),
        reason="Correction noted.",
        warnings=(),
        errors=(),
        created_at=_TIMESTAMP,
    )
    result = derive_memory_candidates(
        operator_feedback=fb,
        feedback_report=fb_report,
        trace_event_ref=trace_ref,
    )
    assert result.created_memory_candidate_ids
    assert not result.errors


def test_correction_without_correction_text_uses_raw_text() -> None:
    trace_ref = _make_trace_ref()
    fb = OperatorFeedbackRecord(
        feedback_id="fb_corr_notext_001",
        feedback_type=OperatorFeedbackType.CORRECTION,
        sentiment=OperatorFeedbackSentiment.NEUTRAL,
        target_ref=_make_target(trace_ref=trace_ref),
        actor_id="op",
        raw_text="Fix this approach.",
        source_trace_event_ref=trace_ref,
        limitations=("Test.",),
        created_at=_TIMESTAMP,
    )
    fb_report = FeedbackProcessingReport(
        report_id="fpr_corr_notext_001",
        feedback_id=fb.feedback_id,
        target_ref=fb.target_ref,
        signal_strength=FeedbackSignalStrength.MODERATE,
        candidate_actions=(),
        created_candidates=(),
        blocked_actions=(),
        reason="Correction noted.",
        warnings=(),
        errors=(),
        created_at=_TIMESTAMP,
    )
    result = derive_memory_candidates(
        operator_feedback=fb,
        feedback_report=fb_report,
        trace_event_ref=trace_ref,
    )
    assert result.created_memory_candidate_ids


# ---------------------------------------------------------------------------
# Safety -> safety_note
# ---------------------------------------------------------------------------


def test_safety_concern_produces_safety_note() -> None:
    trace_ref = _make_trace_ref()
    fb = OperatorFeedbackRecord(
        feedback_id="fb_safety_001",
        feedback_type=OperatorFeedbackType.SAFETY_CONCERN,
        sentiment=OperatorFeedbackSentiment.NEGATIVE,
        target_ref=_make_target(trace_ref=trace_ref),
        actor_id="op",
        raw_text="This could cause harm.",
        source_trace_event_ref=trace_ref,
        limitations=("Test.",),
        created_at=_TIMESTAMP,
    )
    fb_report = FeedbackProcessingReport(
        report_id="fpr_safety_001",
        feedback_id=fb.feedback_id,
        target_ref=fb.target_ref,
        signal_strength=FeedbackSignalStrength.STRONG,
        candidate_actions=(),
        created_candidates=(),
        blocked_actions=(),
        reason="Safety concern noted.",
        warnings=(),
        errors=(),
        created_at=_TIMESTAMP,
    )
    result = derive_memory_candidates(
        operator_feedback=fb,
        feedback_report=fb_report,
        trace_event_ref=trace_ref,
    )
    assert result.created_memory_candidate_ids
    assert any("authority_sensitive" in w for w in result.warnings)


# ---------------------------------------------------------------------------
# Policy -> policy_note
# ---------------------------------------------------------------------------


def test_policy_concern_produces_policy_note() -> None:
    trace_ref = _make_trace_ref()
    fb = OperatorFeedbackRecord(
        feedback_id="fb_policy_001",
        feedback_type=OperatorFeedbackType.POLICY_CONCERN,
        sentiment=OperatorFeedbackSentiment.NEGATIVE,
        target_ref=_make_target(trace_ref=trace_ref),
        actor_id="op",
        raw_text="This violates our policy.",
        source_trace_event_ref=trace_ref,
        limitations=("Test.",),
        created_at=_TIMESTAMP,
    )
    fb_report = FeedbackProcessingReport(
        report_id="fpr_policy_001",
        feedback_id=fb.feedback_id,
        target_ref=fb.target_ref,
        signal_strength=FeedbackSignalStrength.STRONG,
        candidate_actions=(),
        created_candidates=(),
        blocked_actions=(),
        reason="Policy concern noted.",
        warnings=(),
        errors=(),
        created_at=_TIMESTAMP,
    )
    result = derive_memory_candidates(
        operator_feedback=fb,
        feedback_report=fb_report,
        trace_event_ref=trace_ref,
    )
    assert result.created_memory_candidate_ids
    assert any("authority_sensitive" in w for w in result.warnings)


# ---------------------------------------------------------------------------
# Capability claim -> capability_lesson + limitation_note
# ---------------------------------------------------------------------------


def _make_claim(claim_id: str, trace_ref: "trace_event_ref | None" = None) -> CapabilityClaim:
    return CapabilityClaim(
        claim_id=claim_id,
        capability_id="cap.test",
        status=CapabilityClaimStatus.CONTEXT_VERIFIED,
        claim_text="Test capability.",
        scope=CapabilityClaimScope(task_type="test"),
        evidence_links=(
            ClaimEvidenceLink(
                link_id="link_001",
                capability_evidence_id="ce_001",
                source_trace_event_ref=trace_ref,
                source_event_hash=trace_ref.event_hash if trace_ref else "hash",
            ),
        ),
        known_limits=(
            KnownLimit(limit_id="limit_001", description="Test limit.", severity="info", created_at=_TIMESTAMP),
        ),
        verified_contexts=(),
        confidence_label="medium",
        created_at=_TIMESTAMP,
        updated_at=_TIMESTAMP,
    )


def test_capability_claim_with_limitations_produces_candidates() -> None:
    trace_ref = _make_trace_ref()
    claim = _make_claim("claim_cap_001", trace_ref)
    result = derive_memory_candidates(
        capability_claim=claim,
        trace_event_ref=trace_ref,
    )
    assert result.created_memory_candidate_ids
    assert not result.errors


def test_capability_claim_without_trace_ref() -> None:
    """Capability claim with trace_ref is required for ClaimEvidenceLink."""
    trace_ref = _make_trace_ref()
    claim = _make_claim("claim_cap_notrace_001", trace_ref)
    result = derive_memory_candidates(
        capability_claim=claim,
        trace_event_ref=trace_ref,
    )
    assert result.created_memory_candidate_ids


# ---------------------------------------------------------------------------
# Combined input
# ---------------------------------------------------------------------------


def test_combined_feedback_and_claim() -> None:
    trace_ref = _make_trace_ref("trace_combined_001")
    fb = OperatorFeedbackRecord(
        feedback_id="fb_comb_001",
        feedback_type=OperatorFeedbackType.APPROVAL,
        sentiment=OperatorFeedbackSentiment.POSITIVE,
        target_ref=_make_target(trace_ref=trace_ref),
        actor_id="op",
        raw_text="Remember this.",
        source_trace_event_ref=trace_ref,
        limitations=("Test.",),
        created_at=_TIMESTAMP,
    )
    fb_report = FeedbackProcessingReport(
        report_id="fpr_comb_001",
        feedback_id=fb.feedback_id,
        target_ref=fb.target_ref,
        signal_strength=FeedbackSignalStrength.MODERATE,
        candidate_actions=(FeedbackCandidateAction.CREATE_MEMORY_CANDIDATE,),
        created_candidates=(),
        blocked_actions=(),
        reason="Operator wants to remember.",
        warnings=(),
        errors=(),
        created_at=_TIMESTAMP,
    )
    claim = _make_claim("claim_comb_001", trace_ref)
    result = derive_memory_candidates(
        operator_feedback=fb,
        feedback_report=fb_report,
        capability_claim=claim,
        trace_event_ref=trace_ref,
    )
    assert result.created_memory_candidate_ids
    # Should have at least 2: operator_preference + capability_lesson
    assert len(result.created_memory_candidate_ids) >= 2
    assert not result.errors
