"""P1.5.16 Capability Claim Invariant tests.

Tests structural invariants: impossible states must be impossible through
validation and contract enforcement.
"""
from __future__ import annotations

import pytest as pytest

from agentic_runtime.contracts.capability_claims import (
    CapabilityClaim,
    CapabilityClaimDecision,
    CapabilityClaimDecisionKind,
    CapabilityClaimRegistry,
    CapabilityClaimScope,
    CapabilityClaimStatus,
    ClaimEvidenceLink,
    is_positive_claim_status,
)
from agentic_runtime.contracts.trace import (
    AurelTraceLog,
    TraceEventStatus,
    TraceEventType,
    trace_event_ref,
)

_TIMESTAMP = "2026-06-22T00:00:00+00:00"


def _make_evidence_link(
    trace_log_id: str = "trace_inv_001",
    event_hash: str | None = None,
) -> ClaimEvidenceLink:
    trace_log = AurelTraceLog(trace_id=trace_log_id)
    event = trace_log.append(
        event_type=TraceEventType.STUB_EXECUTION_COMPLETED,
        actor_type="test",
        actor_id="invariants",
        payload_json={"test": True},
        timestamp=_TIMESTAMP,
        status=TraceEventStatus.COMPLETED,
    )
    ref = trace_event_ref(event)
    return ClaimEvidenceLink(
        link_id="link_001",
        capability_evidence_id="cap_ev_001",
        source_trace_event_ref=ref,
        source_event_hash=event_hash or ref.event_hash,
        evidence_refs=("ev_001",),
        verifier_result_refs=("ver_001",),
    )


def _make_scope() -> CapabilityClaimScope:
    return CapabilityClaimScope(task_type="test_task")


class TestPositiveClaimRequiresEvidence:
    """Positive claims require non-empty evidence_links."""

    def test_positive_claim_without_evidence_fails(self) -> None:
        scope = _make_scope()
        with pytest.raises(ValueError, match="positive claims require"):
            CapabilityClaim(
                claim_id="claim_001",
                capability_id="cap.test",
                claim_text="Test claim.",
                status=CapabilityClaimStatus.CONTEXT_VERIFIED,
                scope=scope,
                evidence_links=(),
                created_at=_TIMESTAMP,
                updated_at=_TIMESTAMP,
            )

    def test_verified_claim_without_evidence_fails(self) -> None:
        scope = _make_scope()
        with pytest.raises(ValueError, match="positive claims require"):
            CapabilityClaim(
                claim_id="claim_002",
                capability_id="cap.test",
                claim_text="Test.",
                status=CapabilityClaimStatus.VERIFIED,
                scope=scope,
                evidence_links=(),
                created_at=_TIMESTAMP,
                updated_at=_TIMESTAMP,
            )


class TestContextVerifiedRequiresLimits:
    """Context_verified / verified_candidate / verified claims require known_limits."""

    def test_context_verified_without_limits_fails(self) -> None:
        scope = _make_scope()
        evidence = _make_evidence_link()
        with pytest.raises(ValueError, match="requires non-empty known_limits"):
            CapabilityClaim(
                claim_id="claim_003",
                capability_id="cap.test",
                claim_text="Test.",
                status=CapabilityClaimStatus.CONTEXT_VERIFIED,
                scope=scope,
                evidence_links=(evidence,),
                known_limits=(),
                created_at=_TIMESTAMP,
                updated_at=_TIMESTAMP,
            )

    def test_verified_candidate_without_limits_fails(self) -> None:
        scope = _make_scope()
        evidence = _make_evidence_link()
        with pytest.raises(ValueError, match="requires non-empty known_limits"):
            CapabilityClaim(
                claim_id="claim_004",
                capability_id="cap.test",
                claim_text="Test.",
                status=CapabilityClaimStatus.VERIFIED_CANDIDATE,
                scope=scope,
                evidence_links=(evidence,),
                known_limits=(),
                created_at=_TIMESTAMP,
                updated_at=_TIMESTAMP,
            )


class TestClaimEvidenceLinkInvariants:
    """ClaimEvidenceLink hash must match trace ref."""

    def test_hash_mismatch_fails(self) -> None:
        with pytest.raises(ValueError, match="source_event_hash must match"):
            _make_evidence_link(event_hash="wrong_hash")


class TestClaimRegistryEnforcement:
    """Registry enforces candidate-before-decision and accept-only creation."""

    def test_rejected_does_not_create_claim(self) -> None:
        registry = CapabilityClaimRegistry()
        decision = CapabilityClaimDecision(
            decision_id="dec_reject",
            candidate_id="cand_nonexistent",
            decision=CapabilityClaimDecisionKind.REJECT,
            decided_by="test",
            reason="Rejected.",
            created_at=_TIMESTAMP,
        )
        claim = registry.apply_decision(decision, evidence_link=_make_evidence_link())
        assert claim is None
        assert registry.claim_count == 0


class TestIsPositiveClaimStatus:
    """Helper correctly identifies positive claim statuses."""

    def test_positive_statuses(self) -> None:
        positive = {
            CapabilityClaimStatus.WEAKLY_SUPPORTED,
            CapabilityClaimStatus.EXPERIMENTAL,
            CapabilityClaimStatus.CONTEXT_VERIFIED,
            CapabilityClaimStatus.VERIFIED_CANDIDATE,
            CapabilityClaimStatus.VERIFIED,
        }
        for status in CapabilityClaimStatus:
            if status in positive:
                assert is_positive_claim_status(status), f"{status} should be positive"
            else:
                assert not is_positive_claim_status(status), f"{status} should not be positive"
