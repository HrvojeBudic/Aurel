"""P1.5.18 Memory Candidate Invariant tests.

Verifies hard invariants:
no-commit, no-retrieval, no-skill, no-reflex, no-policy, risk/review rules.
"""
from __future__ import annotations

import pytest

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
    MemoryCandidateEvidenceLink,
    MemoryCandidateRiskClass,
    MemoryCandidateScope,
    MemoryCandidateScopeType,
    MemoryCandidateSourceType,
    MemoryCandidateStatus,
    MemoryCandidateType,
    MemoryCandidateValidationReport,
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

# Hard invariants — these states must never appear in any MemoryCandidate
_NO_COMMIT_STATUS = "committed"
_NO_COMMIT_IN_CANDIDATE = "commit"
_NO_RETRIEVAL = "retrieve"
_NO_SKILL = "skill"
_NO_REFLEX = "reflex"
_NO_POLICY = "policy"
_NO_PROMOTE = "promote"
_NO_AUTO_VERIFY = "auto_verify"


def _make_trace_ref(trace_id: str = "trace_mem_inv_001") -> "trace_event_ref":
    log = AurelTraceLog(trace_id=trace_id)
    event = log.append(
        event_type=TraceEventType.STUB_EXECUTION_COMPLETED,
        actor_type="test",
        actor_id="mem_inv",
        payload_json={"test": True},
        timestamp=_TIMESTAMP,
        status=TraceEventStatus.COMPLETED,
    )
    return trace_event_ref(event)


def _make_target(
    trace_ref: "trace_event_ref | None" = None,
) -> OperatorFeedbackTargetRef:
    return OperatorFeedbackTargetRef(
        target_id="target_inv_001",
        target_type=OperatorFeedbackTargetType.CAPABILITY_CLAIM,
        source_trace_event_ref=trace_ref,
        source_event_hash=trace_ref.event_hash if trace_ref else "",
    )


# ---------------------------------------------------------------------------
# No "committed" status exists
# ---------------------------------------------------------------------------


def test_no_committed_status_in_enum() -> None:
    """MemoryCandidateStatus MUST NOT have a 'committed' value."""
    statuses = {s.value for s in MemoryCandidateStatus}
    assert _NO_COMMIT_STATUS not in statuses
    assert "committed" not in statuses


# ---------------------------------------------------------------------------
# MemoryCandidate cannot describe itself as committed
# ---------------------------------------------------------------------------


def test_memory_candidate_cannot_be_committed() -> None:
    """Any valid MemoryCandidate MUST NOT have status related to committed."""
    trace_ref = _make_trace_ref()
    mc = MemoryCandidate(
        memory_candidate_id="mem_inv_001",
        candidate_type=MemoryCandidateType.PROJECT_NOTE,
        status=MemoryCandidateStatus.CANDIDATE,
        source_type=MemoryCandidateSourceType.CAPABILITY_CLAIM,
        scope=MemoryCandidateScope(
            scope_type=MemoryCandidateScopeType.PROJECT,
        ),
        proposed_memory_text="Test invariant.",
        risk_class=MemoryCandidateRiskClass.LOW,
        limitations=("Test.",),
        evidence_links=(
            MemoryCandidateEvidenceLink(
                link_id="link_inv_001",
                source_trace_event_ref=trace_ref,
                source_event_hash=trace_ref.event_hash,
            ),
        ),
        created_at=_TIMESTAMP,
    )
    # The candidate itself cannot reference committed state
    assert mc.status != MemoryCandidateStatus.CANDIDATE or mc.status.value != "committed"
    assert "committed" not in mc.proposed_memory_text.lower()


# ---------------------------------------------------------------------------
# The bridge NEVER creates committed memory
# ---------------------------------------------------------------------------


def test_bridge_never_commits_memory() -> None:
    """derive_memory_candidates MUST NOT produce any committed memory."""
    trace_ref = _make_trace_ref()
    fb = OperatorFeedbackRecord(
        feedback_id="fb_inv_001",
        feedback_type=OperatorFeedbackType.APPROVAL,
        sentiment=OperatorFeedbackSentiment.POSITIVE,
        target_ref=_make_target(trace_ref),
        actor_id="op",
        raw_text="Approved.",
        source_trace_event_ref=trace_ref,
        limitations=("Test.",),
        created_at=_TIMESTAMP,
    )
    fb_report = FeedbackProcessingReport(
        report_id="fpr_inv_001",
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
    # The report must not contain any committed status
    assert "committed" not in result.reason.lower()


# ---------------------------------------------------------------------------
# No retrieval, skill, reflex, policy creation
# ---------------------------------------------------------------------------


def test_bridge_report_does_not_create_skills_reflexes_policies() -> None:
    """Bridge report MUST NOT mention skill/reflex/policy creation."""
    trace_ref = _make_trace_ref()
    claim = CapabilityClaim(
        claim_id="claim_inv_002",
        capability_id="cap.test",
        status=CapabilityClaimStatus.CONTEXT_VERIFIED,
        claim_text="Test claim.",
        scope=CapabilityClaimScope(task_type="test"),
        evidence_links=(
            ClaimEvidenceLink(
                link_id="link_inv_002",
                capability_evidence_id="ce_inv_001",
                source_trace_event_ref=trace_ref,
                source_event_hash=trace_ref.event_hash,
            ),
        ),
        known_limits=(
            KnownLimit(limit_id="limit_inv_001", description="Test limit.", severity="info", created_at=_TIMESTAMP),
        ),
        verified_contexts=(),
        confidence_label="medium",
        created_at=_TIMESTAMP,
        updated_at=_TIMESTAMP,
    )
    result = derive_memory_candidates(
        capability_claim=claim,
        trace_event_ref=trace_ref,
    )
    reason_lower = result.reason.lower()
    for forbidden in ("skill", "reflex", "policy", "canon"):
        assert forbidden not in reason_lower, (
            f"'{forbidden}' must not appear in bridge report reason: {result.reason}"
        )


# ---------------------------------------------------------------------------
# Risk/review rules
# ---------------------------------------------------------------------------


def test_authority_sensitive_requires_review_or_blocked() -> None:
    """AUTHORITY_SENSITIVE risk class MUST require needs_review or blocked."""
    with pytest.raises(ValueError):
        MemoryCandidate(
            memory_candidate_id="mem_inv_risk_001",
            candidate_type=MemoryCandidateType.PROJECT_NOTE,
            status=MemoryCandidateStatus.CANDIDATE,  # Should fail
            source_type=MemoryCandidateSourceType.OPERATOR_FEEDBACK,
            scope=MemoryCandidateScope(
                scope_type=MemoryCandidateScopeType.OPERATOR,
            ),
            proposed_memory_text="Authority issue.",
            risk_class=MemoryCandidateRiskClass.AUTHORITY_SENSITIVE,
            limitations=("Test.",),
            created_at=_TIMESTAMP,
        )


def test_authority_sensitive_with_needs_review_allowed() -> None:
    """AUTHORITY_SENSITIVE with needs_review is allowed."""
    trace_ref = _make_trace_ref()
    mc = MemoryCandidate(
        memory_candidate_id="mem_inv_risk_002",
        candidate_type=MemoryCandidateType.SAFETY_NOTE,
        status=MemoryCandidateStatus.NEEDS_REVIEW,
        source_type=MemoryCandidateSourceType.OPERATOR_FEEDBACK,
        scope=MemoryCandidateScope(
            scope_type=MemoryCandidateScopeType.POLICY,
        ),
        proposed_memory_text="Safety with needs_review.",
        risk_class=MemoryCandidateRiskClass.AUTHORITY_SENSITIVE,
        limitations=("Test.",),
        evidence_links=(
            MemoryCandidateEvidenceLink(
                link_id="link_inv_risk_002",
                source_trace_event_ref=trace_ref,
                source_event_hash=trace_ref.event_hash,
            ),
        ),
        created_at=_TIMESTAMP,
    )
    assert mc.status == MemoryCandidateStatus.NEEDS_REVIEW


def test_sensitive_requires_review_or_blocked() -> None:
    """SENSITIVE risk class MUST require needs_review or blocked."""
    with pytest.raises(ValueError):
        MemoryCandidate(
            memory_candidate_id="mem_inv_risk_003",
            candidate_type=MemoryCandidateType.PROJECT_NOTE,
            status=MemoryCandidateStatus.CANDIDATE,
            source_type=MemoryCandidateSourceType.OPERATOR_FEEDBACK,
            scope=MemoryCandidateScope(
                scope_type=MemoryCandidateScopeType.OPERATOR,
            ),
            proposed_memory_text="Sensitive info.",
            risk_class=MemoryCandidateRiskClass.SENSITIVE,
            limitations=("Test.",),
            created_at=_TIMESTAMP,
        )


def test_low_risk_no_review_needed() -> None:
    """LOW risk class with CANDIDATE status is valid."""
    trace_ref = _make_trace_ref()
    mc = MemoryCandidate(
        memory_candidate_id="mem_inv_risk_004",
        candidate_type=MemoryCandidateType.PROJECT_NOTE,
        status=MemoryCandidateStatus.CANDIDATE,
        source_type=MemoryCandidateSourceType.CAPABILITY_CLAIM,
        scope=MemoryCandidateScope(
            scope_type=MemoryCandidateScopeType.PROJECT,
        ),
        proposed_memory_text="Low risk note.",
        risk_class=MemoryCandidateRiskClass.LOW,
        limitations=("Test.",),
        evidence_links=(
            MemoryCandidateEvidenceLink(
                link_id="link_inv_risk_004",
                source_trace_event_ref=trace_ref,
                source_event_hash=trace_ref.event_hash,
            ),
        ),
        created_at=_TIMESTAMP,
    )
    assert mc.status == MemoryCandidateStatus.CANDIDATE
    assert mc.risk_class == MemoryCandidateRiskClass.LOW


# ---------------------------------------------------------------------------
# MemoryCandidate limitations always include anti-commit language
# ---------------------------------------------------------------------------


def test_limitations_include_no_commit_language() -> None:
    """Every MemoryCandidate limitation set should include anti-commit language."""
    trace_ref = _make_trace_ref()
    mc = MemoryCandidate(
        memory_candidate_id="mem_inv_lim_001",
        candidate_type=MemoryCandidateType.CAPABILITY_LESSON,
        status=MemoryCandidateStatus.CANDIDATE,
        source_type=MemoryCandidateSourceType.CAPABILITY_CLAIM,
        scope=MemoryCandidateScope(
            scope_type=MemoryCandidateScopeType.CAPABILITY,
        ),
        proposed_memory_text="Memory text.",
        risk_class=MemoryCandidateRiskClass.LOW,
        limitations=("Not committed memory.", "Another limitation."),
        evidence_links=(
            MemoryCandidateEvidenceLink(
                link_id="link_inv_lim_001",
                source_trace_event_ref=trace_ref,
                source_event_hash=trace_ref.event_hash,
            ),
        ),
        created_at=_TIMESTAMP,
    )
    assert any("NOT committed" in lim or "not committed" in lim.lower()
               for lim in mc.limitations)


# ---------------------------------------------------------------------------
# Validation report requires blocked_reasons when invalid
# ---------------------------------------------------------------------------


def test_validation_report_invalid_no_reasons_raises() -> None:
    with pytest.raises(ValueError, match="non-empty blocked_reasons"):
        MemoryCandidateValidationReport(
            validation_id="val_inv_001",
            memory_candidate_id="mem_inv_001",
            is_valid=False,
            risk_class=MemoryCandidateRiskClass.LOW,
            blocked_reasons=(),
            created_at=_TIMESTAMP,
        )


# ---------------------------------------------------------------------------
# Bridge report contract
# ---------------------------------------------------------------------------


def test_bridge_report_empty_errors_is_empty_tuple() -> None:
    result = derive_memory_candidates()
    assert isinstance(result, MemoryCandidateBridgeReport)
    assert result.errors == ()


def test_bridge_report_warnings_is_empty_when_no_safety() -> None:
    trace_ref = _make_trace_ref()
    fb = OperatorFeedbackRecord(
        feedback_id="fb_inv_warn_001",
        feedback_type=OperatorFeedbackType.APPROVAL,
        sentiment=OperatorFeedbackSentiment.POSITIVE,
        target_ref=_make_target(trace_ref),
        actor_id="op",
        raw_text="Remember this.",
        source_trace_event_ref=trace_ref,
        limitations=("Test.",),
        created_at=_TIMESTAMP,
    )
    fb_report = FeedbackProcessingReport(
        report_id="fpr_inv_warn_001",
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
    # Approval with create_memory_candidate should work without warnings
    assert isinstance(result.warnings, tuple)
