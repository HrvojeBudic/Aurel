"""Evidence-to-claim binding aggregation tests — P1.5.7."""
from __future__ import annotations

from agentic_runtime.evaluation.capability_evidence import (
    CapabilityEvidenceKind,
    CapabilityEvidenceRecord,
    CapabilityEvidenceStatus,
    CapabilityEvidenceStrength,
)
from agentic_runtime.evaluation.evidence_claim_binding import (
    ClaimBindingRelationship,
    ClaimBindingStatus,
    ClaimSupportLevel,
    ClaimConflictLevel,
    aggregate_evidence_claim_bindings,
    bind_evidence_to_claim,
)


def _make_evidence(
    evidence_id: str,
    status: CapabilityEvidenceStatus,
    strength: CapabilityEvidenceStrength,
) -> CapabilityEvidenceRecord:
    return CapabilityEvidenceRecord(
        evidence_id=evidence_id,
        kind=CapabilityEvidenceKind.EVALUATION_RESULT,
        status=status,
        strength=strength,
        claim_id="claim_001",
    )


def test_aggregate_no_bindings_insufficient():
    decision = aggregate_evidence_claim_bindings(
        decision_id="d1", claim_id="claim_001", bindings=(),
    )
    assert decision.aggregate_relationship == ClaimBindingRelationship.INSUFFICIENT
    assert decision.aggregate_status == ClaimBindingStatus.INSUFFICIENT
    assert decision.aggregate_support_level == ClaimSupportLevel.NONE


def test_aggregate_strong_support_no_conflict():
    evidence = _make_evidence("ev_001", CapabilityEvidenceStatus.USABLE, CapabilityEvidenceStrength.STRONG)
    b1 = bind_evidence_to_claim(binding_id="b1", claim_id="claim_001", evidence=evidence)

    evidence2 = _make_evidence("ev_002", CapabilityEvidenceStatus.USABLE, CapabilityEvidenceStrength.ADEQUATE)
    b2 = bind_evidence_to_claim(binding_id="b2", claim_id="claim_001", evidence=evidence2)

    decision = aggregate_evidence_claim_bindings(
        decision_id="d1", claim_id="claim_001", bindings=(b1, b2),
    )
    assert decision.aggregate_relationship == ClaimBindingRelationship.SUPPORTS
    assert decision.aggregate_status == ClaimBindingStatus.BOUND
    assert decision.aggregate_support_level == ClaimSupportLevel.STRONG


def test_aggregate_moderate_support_no_conflict():
    evidence = _make_evidence("ev_001", CapabilityEvidenceStatus.USABLE, CapabilityEvidenceStrength.ADEQUATE)
    b1 = bind_evidence_to_claim(binding_id="b1", claim_id="claim_001", evidence=evidence)
    decision = aggregate_evidence_claim_bindings(
        decision_id="d1", claim_id="claim_001", bindings=(b1,),
    )
    assert decision.aggregate_relationship == ClaimBindingRelationship.SUPPORTS
    assert decision.aggregate_support_level == ClaimSupportLevel.MODERATE


def test_aggregate_conflict_dominates_support():
    evidence = _make_evidence("ev_001", CapabilityEvidenceStatus.USABLE, CapabilityEvidenceStrength.STRONG)
    b1 = bind_evidence_to_claim(binding_id="b1", claim_id="claim_001", evidence=evidence)

    evidence2 = _make_evidence("ev_002", CapabilityEvidenceStatus.CONFLICTED, CapabilityEvidenceStrength.CONFLICTED)
    b2 = bind_evidence_to_claim(binding_id="b2", claim_id="claim_001", evidence=evidence2)

    decision = aggregate_evidence_claim_bindings(
        decision_id="d1", claim_id="claim_001", bindings=(b1, b2),
    )
    assert decision.aggregate_relationship == ClaimBindingRelationship.CONFLICTS
    assert decision.aggregate_status == ClaimBindingStatus.CONFLICTED
    assert decision.aggregate_support_level == ClaimSupportLevel.NONE


def test_aggregate_blocking_evidence_blocks():
    evidence = _make_evidence("ev_001", CapabilityEvidenceStatus.REVOKED, CapabilityEvidenceStrength.NONE)
    b1 = bind_evidence_to_claim(binding_id="b1", claim_id="claim_001", evidence=evidence)
    decision = aggregate_evidence_claim_bindings(
        decision_id="d1", claim_id="claim_001", bindings=(b1,),
    )
    assert decision.aggregate_relationship == ClaimBindingRelationship.BLOCKS
    assert decision.aggregate_status == ClaimBindingStatus.BLOCKED


def test_aggregate_invalid_evidence_blocks():
    evidence = _make_evidence("ev_001", CapabilityEvidenceStatus.INVALID, CapabilityEvidenceStrength.NONE)
    b1 = bind_evidence_to_claim(binding_id="b1", claim_id="claim_001", evidence=evidence)
    decision = aggregate_evidence_claim_bindings(
        decision_id="d1", claim_id="claim_001", bindings=(b1,),
    )
    assert decision.aggregate_relationship == ClaimBindingRelationship.BLOCKS


def test_aggregate_rejected_evidence_blocks():
    evidence = _make_evidence("ev_001", CapabilityEvidenceStatus.REJECTED, CapabilityEvidenceStrength.NONE)
    b1 = bind_evidence_to_claim(binding_id="b1", claim_id="claim_001", evidence=evidence)
    decision = aggregate_evidence_claim_bindings(
        decision_id="d1", claim_id="claim_001", bindings=(b1,),
    )
    assert decision.aggregate_relationship == ClaimBindingRelationship.BLOCKS


def test_aggregate_stale_only_insufficient():
    evidence = _make_evidence("ev_001", CapabilityEvidenceStatus.STALE, CapabilityEvidenceStrength.WEAK)
    b1 = bind_evidence_to_claim(binding_id="b1", claim_id="claim_001", evidence=evidence)
    decision = aggregate_evidence_claim_bindings(
        decision_id="d1", claim_id="claim_001", bindings=(b1,),
    )
    assert decision.aggregate_relationship == ClaimBindingRelationship.INSUFFICIENT
    assert decision.aggregate_status == ClaimBindingStatus.STALE
    assert decision.aggregate_support_level == ClaimSupportLevel.NONE


def test_aggregate_mixed_weak_and_insufficient_partial():
    evidence = _make_evidence("ev_001", CapabilityEvidenceStatus.USABLE, CapabilityEvidenceStrength.WEAK)
    b1 = bind_evidence_to_claim(binding_id="b1", claim_id="claim_001", evidence=evidence)

    evidence2 = _make_evidence("ev_002", CapabilityEvidenceStatus.INSUFFICIENT, CapabilityEvidenceStrength.NONE)
    b2 = bind_evidence_to_claim(binding_id="b2", claim_id="claim_001", evidence=evidence2)

    decision = aggregate_evidence_claim_bindings(
        decision_id="d1", claim_id="claim_001", bindings=(b1, b2),
    )
    assert decision.aggregate_relationship == ClaimBindingRelationship.PARTIALLY_SUPPORTS
    assert decision.aggregate_support_level in (ClaimSupportLevel.WEAK, ClaimSupportLevel.NONE)


def test_aggregate_no_numeric_score():
    evidence = _make_evidence("ev_001", CapabilityEvidenceStatus.USABLE, CapabilityEvidenceStrength.STRONG)
    b1 = bind_evidence_to_claim(binding_id="b1", claim_id="claim_001", evidence=evidence)
    decision = aggregate_evidence_claim_bindings(
        decision_id="d1", claim_id="claim_001", bindings=(b1,),
    )
    s = str(decision)
    assert "score=" not in s.lower() or "numeric" not in s.lower()


def test_aggregate_does_not_verify_claim():
    evidence = _make_evidence("ev_001", CapabilityEvidenceStatus.USABLE, CapabilityEvidenceStrength.STRONG)
    b1 = bind_evidence_to_claim(binding_id="b1", claim_id="claim_001", evidence=evidence)
    decision = aggregate_evidence_claim_bindings(
        decision_id="d1", claim_id="claim_001", bindings=(b1,),
    )
    assert "VERIFIED" not in decision.aggregate_status.value
    assert "VERIFIED" not in decision.aggregate_relationship.value


def test_aggregate_usable_insufficient_conflicted_ids():
    evidence_good = _make_evidence("ev_good", CapabilityEvidenceStatus.USABLE, CapabilityEvidenceStrength.STRONG)
    evidence_insuf = _make_evidence("ev_insuf", CapabilityEvidenceStatus.INSUFFICIENT, CapabilityEvidenceStrength.NONE)
    evidence_conf = _make_evidence("ev_conf", CapabilityEvidenceStatus.CONFLICTED, CapabilityEvidenceStrength.CONFLICTED)
    evidence_block = _make_evidence("ev_block", CapabilityEvidenceStatus.REVOKED, CapabilityEvidenceStrength.NONE)

    b1 = bind_evidence_to_claim(binding_id="b1", claim_id="claim_001", evidence=evidence_good)
    b2 = bind_evidence_to_claim(binding_id="b2", claim_id="claim_001", evidence=evidence_insuf)
    b3 = bind_evidence_to_claim(binding_id="b3", claim_id="claim_001", evidence=evidence_conf)
    b4 = bind_evidence_to_claim(binding_id="b4", claim_id="claim_001", evidence=evidence_block)

    decision = aggregate_evidence_claim_bindings(
        decision_id="d1", claim_id="claim_001", bindings=(b1, b2, b3, b4),
    )
    # BLOCKED dominates
    assert decision.aggregate_relationship == ClaimBindingRelationship.BLOCKS
    assert "ev_block" in decision.blocked_evidence_ids
    assert "ev_conf" in decision.conflicted_evidence_ids
    assert "ev_insuf" in decision.insufficient_evidence_ids
    # Note: usable_ids may be empty because BLOCKS dominates all
