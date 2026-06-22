"""P1.5.18 Memory Candidate Bridge tests.

Verifies bridge report generation, candidate derivation, and validation.
"""
from __future__ import annotations

import pytest

from agentic_runtime.contracts.capability_claims import (
    CapabilityClaim,
    CapabilityClaimReport,
    CapabilityClaimScope,
    CapabilityClaimStatus,
    ClaimEvidenceLink,
    KnownLimit,
)
from agentic_runtime.contracts.memory_candidates import (
    MemoryCandidate,
    MemoryCandidateBridgeReport,
    MemoryCandidateEvidenceLink,
    MemoryCandidateRiskClass,
    MemoryCandidateScope,
    MemoryCandidateScopeType,
    MemoryCandidateSourceType,
    MemoryCandidateStatus,
    MemoryCandidateType,
    MemoryCandidateValidationReport,
    memory_candidate_bridge_report_to_dict,
    memory_candidate_to_dict,
    memory_candidate_validation_report_to_dict,
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


def _make_trace_ref(trace_id: str = "trace_mem_bridge_001") -> "trace_event_ref":
    log = AurelTraceLog(trace_id=trace_id)
    event = log.append(
        event_type=TraceEventType.STUB_EXECUTION_COMPLETED,
        actor_type="test",
        actor_id="mem_bridge",
        payload_json={"test": True},
        timestamp=_TIMESTAMP,
        status=TraceEventStatus.COMPLETED,
    )
    return trace_event_ref(event)


def _make_feedback_target(
    trace_ref: "trace_event_ref | None" = None,
) -> OperatorFeedbackTargetRef:
    return OperatorFeedbackTargetRef(
        target_id="claim_001",
        target_type=OperatorFeedbackTargetType.CAPABILITY_CLAIM,
        source_trace_event_ref=trace_ref,
        source_event_hash=trace_ref.event_hash if trace_ref else "",
    )


def _make_feedback(
    fb_type: OperatorFeedbackType = OperatorFeedbackType.APPROVAL,
    trace_ref: "trace_event_ref | None" = None,
    raw_text: str = "Looks good.",
) -> OperatorFeedbackRecord:
    return OperatorFeedbackRecord(
        feedback_id="fb_bridge_001",
        feedback_type=fb_type,
        sentiment=OperatorFeedbackSentiment.POSITIVE,
        target_ref=_make_feedback_target(trace_ref),
        actor_id="op",
        raw_text=raw_text,
        source_trace_event_ref=trace_ref,
        limitations=("Test limitation.",),
        created_at=_TIMESTAMP,
    )


def _make_claim(trace_ref: "trace_event_ref | None" = None) -> CapabilityClaim:
    return CapabilityClaim(
        claim_id="claim_bridge_001",
        capability_id="cap.test",
        status=CapabilityClaimStatus.CONTEXT_VERIFIED,
        claim_text="Test claim.",
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
            KnownLimit(limit_id="limit_001", description="Limited to test scope.", severity="warning", created_at=_TIMESTAMP),
        ),
        verified_contexts=(),
        confidence_label="medium",
        created_at=_TIMESTAMP,
        updated_at=_TIMESTAMP,
    )


def _make_claim_report(claim: CapabilityClaim) -> CapabilityClaimReport:
    return CapabilityClaimReport(
        report_id="report_bridge_001",
        claim_id=claim.claim_id,
        status=claim.status,
        claim_text=claim.claim_text,
        scope_summary="Test scope.",
        evidence_summary="Test evidence.",
        limitations=("Limited to test scope.",),
        verified_context_count=0,
        warnings=(),
        created_at=_TIMESTAMP,
    )


def _make_feedback_report(feedback_id: str = "fb_bridge_001") -> FeedbackProcessingReport:
    return FeedbackProcessingReport(
        report_id="fpr_bridge_001",
        feedback_id=feedback_id,
        target_ref=_make_feedback_target(),
        signal_strength=FeedbackSignalStrength.MODERATE,
        candidate_actions=(),
        created_candidates=(),
        blocked_actions=(),
        reason="Test report.",
        warnings=(),
        errors=(),
        created_at=_TIMESTAMP,
    )


# ---------------------------------------------------------------------------
# Memory candidate contract creation
# ---------------------------------------------------------------------------


def test_memory_candidate_contract_requires_scope() -> None:
    scope = MemoryCandidateScope(
        scope_type=MemoryCandidateScopeType.CAPABILITY,
        allowed_use_contexts=("future_review",),
    )
    assert scope.scope_type == MemoryCandidateScopeType.CAPABILITY


def test_memory_candidate_contract_requires_limitations() -> None:
    with pytest.raises(ValueError, match="limitations must be non-empty"):
        MemoryCandidate(
            memory_candidate_id="mem_001",
            candidate_type=MemoryCandidateType.CAPABILITY_LESSON,
            status=MemoryCandidateStatus.CANDIDATE,
            source_type=MemoryCandidateSourceType.CAPABILITY_CLAIM,
            scope=MemoryCandidateScope(
                scope_type=MemoryCandidateScopeType.CAPABILITY,
            ),
            proposed_memory_text="Test memory.",
            risk_class=MemoryCandidateRiskClass.LOW,
            limitations=(),
            created_at=_TIMESTAMP,
        )


def test_memory_candidate_contract_safety_note_requires_high_risk() -> None:
    with pytest.raises(ValueError, match="cannot be low risk"):
        MemoryCandidate(
            memory_candidate_id="mem_002",
            candidate_type=MemoryCandidateType.SAFETY_NOTE,
            status=MemoryCandidateStatus.NEEDS_REVIEW,
            source_type=MemoryCandidateSourceType.OPERATOR_FEEDBACK,
            scope=MemoryCandidateScope(
                scope_type=MemoryCandidateScopeType.POLICY,
            ),
            proposed_memory_text="Safety issue.",
            risk_class=MemoryCandidateRiskClass.LOW,
            limitations=("Test.",),
            created_at=_TIMESTAMP,
        )


def test_memory_candidate_contract_policy_note_requires_high_risk() -> None:
    with pytest.raises(ValueError, match="cannot be low risk"):
        MemoryCandidate(
            memory_candidate_id="mem_003",
            candidate_type=MemoryCandidateType.POLICY_NOTE,
            status=MemoryCandidateStatus.NEEDS_REVIEW,
            source_type=MemoryCandidateSourceType.OPERATOR_FEEDBACK,
            scope=MemoryCandidateScope(
                scope_type=MemoryCandidateScopeType.POLICY,
            ),
            proposed_memory_text="Policy issue.",
            risk_class=MemoryCandidateRiskClass.LOW,
            limitations=("Test.",),
            created_at=_TIMESTAMP,
        )


def test_memory_candidate_authority_sensitive_requires_review() -> None:
    with pytest.raises(ValueError, match="requires needs_review or blocked"):
        MemoryCandidate(
            memory_candidate_id="mem_004",
            candidate_type=MemoryCandidateType.PROJECT_NOTE,
            status=MemoryCandidateStatus.CANDIDATE,
            source_type=MemoryCandidateSourceType.OPERATOR_FEEDBACK,
            scope=MemoryCandidateScope(
                scope_type=MemoryCandidateScopeType.OPERATOR,
            ),
            proposed_memory_text="Authority issue.",
            risk_class=MemoryCandidateRiskClass.AUTHORITY_SENSITIVE,
            limitations=("Test.",),
            created_at=_TIMESTAMP,
        )


def test_memory_candidate_candidate_status_requires_evidence() -> None:
    with pytest.raises(ValueError, match="non-empty evidence_links"):
        MemoryCandidate(
            memory_candidate_id="mem_005",
            candidate_type=MemoryCandidateType.PROJECT_NOTE,
            status=MemoryCandidateStatus.CANDIDATE,
            source_type=MemoryCandidateSourceType.CAPABILITY_CLAIM,
            scope=MemoryCandidateScope(
                scope_type=MemoryCandidateScopeType.PROJECT,
            ),
            proposed_memory_text="Test.",
            risk_class=MemoryCandidateRiskClass.LOW,
            limitations=("Test.",),
            evidence_links=(),
            created_at=_TIMESTAMP,
        )


# ---------------------------------------------------------------------------
# Evidence link validation
# ---------------------------------------------------------------------------


def test_evidence_link_hash_mismatch_raises() -> None:
    trace_ref = _make_trace_ref()
    with pytest.raises(ValueError, match="must match"):
        MemoryCandidateEvidenceLink(
            link_id="link_001",
            source_trace_event_ref=trace_ref,
            source_event_hash="wrong_hash",
        )


def test_evidence_link_with_match() -> None:
    trace_ref = _make_trace_ref()
    link = MemoryCandidateEvidenceLink(
        link_id="link_001",
        source_trace_event_ref=trace_ref,
        source_event_hash=trace_ref.event_hash,
    )
    assert link.source_event_hash == trace_ref.event_hash


# ---------------------------------------------------------------------------
# Validation report
# ---------------------------------------------------------------------------


def test_validation_report_invalid_requires_blocked_reasons() -> None:
    with pytest.raises(ValueError, match="non-empty blocked_reasons"):
        MemoryCandidateValidationReport(
            validation_id="val_001",
            memory_candidate_id="mem_001",
            is_valid=False,
            risk_class=MemoryCandidateRiskClass.LOW,
            blocked_reasons=(),
            created_at=_TIMESTAMP,
        )


def test_validation_report_valid_no_blocked_reasons_needed() -> None:
    report = MemoryCandidateValidationReport(
        validation_id="val_002",
        memory_candidate_id="mem_001",
        is_valid=True,
        risk_class=MemoryCandidateRiskClass.LOW,
        blocked_reasons=(),
        created_at=_TIMESTAMP,
    )
    assert report.is_valid


# ---------------------------------------------------------------------------
# Bridge report contract
# ---------------------------------------------------------------------------


def test_bridge_report_contract() -> None:
    bridge = MemoryCandidateBridgeReport(
        report_id="bridge_001",
        source_ref="src_001",
        reason="Test.",
        created_at=_TIMESTAMP,
    )
    assert bridge.report_id == "bridge_001"


# ---------------------------------------------------------------------------
# derive_memory_candidates empty input
# ---------------------------------------------------------------------------


def test_derive_empty_input() -> None:
    result = derive_memory_candidates()
    assert isinstance(result, MemoryCandidateBridgeReport)
    assert not result.created_memory_candidate_ids
    assert "No memory candidates" in result.reason


# ---------------------------------------------------------------------------
# derive_memory_candidates from feedback report
# ---------------------------------------------------------------------------


def test_derive_from_approval_feedback() -> None:
    trace_ref = _make_trace_ref()
    fb = _make_feedback(trace_ref=trace_ref)
    fb_report = FeedbackProcessingReport(
        report_id="fpr_001",
        feedback_id=fb.feedback_id,
        target_ref=fb.target_ref,
        signal_strength=FeedbackSignalStrength.MODERATE,
        candidate_actions=(FeedbackCandidateAction.CREATE_MEMORY_CANDIDATE,),
        created_candidates=(),
        blocked_actions=(),
        reason="Test.",
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
    assert result.validation_report_ids
    assert not result.errors


def test_derive_from_correction_feedback() -> None:
    trace_ref = _make_trace_ref()
    fb = OperatorFeedbackRecord(
        feedback_id="fb_corr_001",
        feedback_type=OperatorFeedbackType.CORRECTION,
        sentiment=OperatorFeedbackSentiment.NEUTRAL,
        target_ref=_make_feedback_target(trace_ref),
        actor_id="op",
        correction_text="Fix this.",
        source_trace_event_ref=trace_ref,
        limitations=("Test.",),
        created_at=_TIMESTAMP,
    )
    fb_report = FeedbackProcessingReport(
        report_id="fpr_corr_001",
        feedback_id=fb.feedback_id,
        target_ref=fb.target_ref,
        signal_strength=FeedbackSignalStrength.STRONG,
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


def test_derive_from_safety_concern() -> None:
    trace_ref = _make_trace_ref()
    fb = OperatorFeedbackRecord(
        feedback_id="fb_safety_001",
        feedback_type=OperatorFeedbackType.SAFETY_CONCERN,
        sentiment=OperatorFeedbackSentiment.NEGATIVE,
        target_ref=_make_feedback_target(trace_ref),
        actor_id="op",
        raw_text="This is unsafe.",
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
        reason="Safety concern.",
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


def test_derive_from_policy_concern() -> None:
    trace_ref = _make_trace_ref()
    fb = OperatorFeedbackRecord(
        feedback_id="fb_policy_001",
        feedback_type=OperatorFeedbackType.POLICY_CONCERN,
        sentiment=OperatorFeedbackSentiment.NEGATIVE,
        target_ref=_make_feedback_target(trace_ref),
        actor_id="op",
        raw_text="This violates policy.",
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
        reason="Policy concern.",
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
# derive_memory_candidates from capability claim
# ---------------------------------------------------------------------------


def test_derive_from_capability_claim() -> None:
    trace_ref = _make_trace_ref()
    claim = _make_claim(trace_ref)
    result = derive_memory_candidates(
        capability_claim=claim,
        trace_event_ref=trace_ref,
    )
    assert result.created_memory_candidate_ids
    # Should produce both a limitation_note and a capability_lesson
    assert len(result.created_memory_candidate_ids) >= 1


def test_derive_from_capability_claim_with_report() -> None:
    trace_ref = _make_trace_ref()
    claim = _make_claim(trace_ref)
    report = _make_claim_report(claim)
    result = derive_memory_candidates(
        capability_claim=claim,
        capability_claim_report=report,
        trace_event_ref=trace_ref,
    )
    assert result.created_memory_candidate_ids
    # Has limitations in the report, so should get a limitation_note + capability_lesson
    assert len(result.created_memory_candidate_ids) >= 2


# ---------------------------------------------------------------------------
# Serialization
# ---------------------------------------------------------------------------


def test_memory_candidate_to_dict() -> None:
    trace_ref = _make_trace_ref()
    mc = MemoryCandidate(
        memory_candidate_id="mem_ser_001",
        candidate_type=MemoryCandidateType.CAPABILITY_LESSON,
        status=MemoryCandidateStatus.CANDIDATE,
        source_type=MemoryCandidateSourceType.CAPABILITY_CLAIM,
        scope=MemoryCandidateScope(
            scope_type=MemoryCandidateScopeType.CAPABILITY,
        ),
        proposed_memory_text="Test serialization.",
        risk_class=MemoryCandidateRiskClass.LOW,
        limitations=("Test.",),
        evidence_links=(
            MemoryCandidateEvidenceLink(
                link_id="link_ser_001",
                source_trace_event_ref=trace_ref,
                source_event_hash=trace_ref.event_hash,
            ),
        ),
        created_at=_TIMESTAMP,
    )
    d = memory_candidate_to_dict(mc)
    assert d["memory_candidate_id"] == "mem_ser_001"
    assert d["candidate_type"] == "capability_lesson"
    assert d["status"] == "candidate"


def test_validation_report_to_dict() -> None:
    report = MemoryCandidateValidationReport(
        validation_id="val_ser_001",
        memory_candidate_id="mem_ser_001",
        is_valid=True,
        risk_class=MemoryCandidateRiskClass.LOW,
        created_at=_TIMESTAMP,
    )
    d = memory_candidate_validation_report_to_dict(report)
    assert d["validation_id"] == "val_ser_001"
    assert d["memory_candidate_id"] == "mem_ser_001"


def test_bridge_report_to_dict() -> None:
    bridge = MemoryCandidateBridgeReport(
        report_id="bridge_ser_001",
        source_ref="src_001",
        reason="Test serialization.",
        created_memory_candidate_ids=("mem_001",),
        created_at=_TIMESTAMP,
    )
    d = memory_candidate_bridge_report_to_dict(bridge)
    assert d["report_id"] == "bridge_ser_001"
    assert d["created_memory_candidate_ids"] == ["mem_001"]
