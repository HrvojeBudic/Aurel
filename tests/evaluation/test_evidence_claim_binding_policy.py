"""Evidence-to-claim binding policy tests — P1.5.7."""
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
    EvidenceClaimBindingPolicy,
    bind_evidence_to_claim,
)


def _make_evidence(status: CapabilityEvidenceStatus, strength: CapabilityEvidenceStrength) -> CapabilityEvidenceRecord:
    return CapabilityEvidenceRecord(
        evidence_id=f"ev_{status.value}_{strength.value}",
        kind=CapabilityEvidenceKind.EVALUATION_RESULT,
        status=status,
        strength=strength,
        claim_id="claim_001",
    )


def test_policy_allow_stale_support():
    policy = EvidenceClaimBindingPolicy(
        policy_id="test",
        allow_stale_evidence_to_support=True,
    )
    evidence = _make_evidence(CapabilityEvidenceStatus.STALE, CapabilityEvidenceStrength.WEAK)
    binding = bind_evidence_to_claim(
        binding_id="b1", claim_id="claim_001", evidence=evidence, policy=policy,
    )
    assert binding.relationship == ClaimBindingRelationship.PARTIALLY_SUPPORTS
    assert binding.support_level == ClaimSupportLevel.WEAK


def test_policy_deny_stale_by_default():
    evidence = _make_evidence(CapabilityEvidenceStatus.STALE, CapabilityEvidenceStrength.WEAK)
    binding = bind_evidence_to_claim(binding_id="b1", claim_id="claim_001", evidence=evidence)
    # Default policy does not allow stale to support
    assert binding.relationship == ClaimBindingRelationship.WEAKENS
    assert binding.support_level == ClaimSupportLevel.NONE


def test_policy_block_conflicted_adds_blocker():
    evidence = _make_evidence(CapabilityEvidenceStatus.CONFLICTED, CapabilityEvidenceStrength.CONFLICTED)
    binding = bind_evidence_to_claim(binding_id="b1", claim_id="claim_001", evidence=evidence)
    assert any("CONFLICTED" in b for b in binding.blockers)


def test_policy_block_revoked_adds_blocker():
    evidence = _make_evidence(CapabilityEvidenceStatus.REVOKED, CapabilityEvidenceStrength.NONE)
    binding = bind_evidence_to_claim(binding_id="b1", claim_id="claim_001", evidence=evidence)
    assert any("REVOKED" in b for b in binding.blockers)


def test_policy_block_invalid_adds_blocker():
    evidence = _make_evidence(CapabilityEvidenceStatus.INVALID, CapabilityEvidenceStrength.NONE)
    binding = bind_evidence_to_claim(binding_id="b1", claim_id="claim_001", evidence=evidence)
    assert any("INVALID" in b for b in binding.blockers)


def test_policy_no_block_conflicted_when_disabled():
    policy = EvidenceClaimBindingPolicy(
        policy_id="test",
        block_conflicted_evidence=False,
    )
    evidence = _make_evidence(CapabilityEvidenceStatus.CONFLICTED, CapabilityEvidenceStrength.CONFLICTED)
    binding = bind_evidence_to_claim(
        binding_id="b1", claim_id="claim_001", evidence=evidence, policy=policy,
    )
    assert not any("blocked by policy" in b.lower() for b in binding.blockers)


def test_allow_single_evidence_to_verify_claim_is_default_false():
    from agentic_runtime.evaluation.evidence_claim_binding import build_default_evidence_claim_binding_policy
    policy = build_default_evidence_claim_binding_policy()
    assert policy.allow_single_evidence_to_verify_claim is False
