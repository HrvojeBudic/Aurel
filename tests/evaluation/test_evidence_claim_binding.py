"""Core evidence-to-claim binding tests — P1.5.7."""
from __future__ import annotations

from agentic_runtime.evaluation.capability_evidence import (
    CapabilityEvidenceKind,
    CapabilityEvidenceRecord,
    CapabilityEvidenceStatus,
    CapabilityEvidenceStrength,
    example_usable_evidence_from_result,
)
from agentic_runtime.evaluation.evidence_claim_binding import (
    ClaimBindingRelationship,
    ClaimBindingStatus,
    ClaimConflictLevel,
    ClaimSupportLevel,
    EvidenceClaimBinding,
    bind_evidence_to_claim,
    build_default_evidence_claim_binding_policy,
    validate_evidence_claim_binding,
)


# ---------------------------------------------------------------------------
# Enum closed-world
# ---------------------------------------------------------------------------


def test_claim_binding_relationship_closed_world():
    assert ClaimBindingRelationship.SUPPORTS.value == "SUPPORTS"
    assert ClaimBindingRelationship.PARTIALLY_SUPPORTS.value == "PARTIALLY_SUPPORTS"
    assert ClaimBindingRelationship.WEAKENS.value == "WEAKENS"
    assert ClaimBindingRelationship.CONFLICTS.value == "CONFLICTS"
    assert ClaimBindingRelationship.BLOCKS.value == "BLOCKS"
    assert ClaimBindingRelationship.INSUFFICIENT.value == "INSUFFICIENT"
    assert ClaimBindingRelationship.IRRELEVANT.value == "IRRELEVANT"
    assert ClaimBindingRelationship.UNKNOWN.value == "UNKNOWN"


def test_claim_binding_status_closed_world():
    assert ClaimBindingStatus.DRAFT.value == "DRAFT"
    assert ClaimBindingStatus.BOUND.value == "BOUND"
    assert ClaimBindingStatus.INSUFFICIENT.value == "INSUFFICIENT"
    assert ClaimBindingStatus.CONFLICTED.value == "CONFLICTED"
    assert ClaimBindingStatus.BLOCKED.value == "BLOCKED"
    assert ClaimBindingStatus.INVALID.value == "INVALID"
    assert ClaimBindingStatus.REJECTED.value == "REJECTED"
    assert ClaimBindingStatus.STALE.value == "STALE"
    assert ClaimBindingStatus.UNKNOWN.value == "UNKNOWN"
    # No VERIFIED status
    assert not hasattr(ClaimBindingStatus, "VERIFIED")


def test_claim_support_level_closed_world():
    assert ClaimSupportLevel.NONE.value == "NONE"
    assert ClaimSupportLevel.WEAK.value == "WEAK"
    assert ClaimSupportLevel.MODERATE.value == "MODERATE"
    assert ClaimSupportLevel.STRONG.value == "STRONG"
    assert ClaimSupportLevel.UNKNOWN.value == "UNKNOWN"


def test_claim_conflict_level_closed_world():
    assert ClaimConflictLevel.NONE.value == "NONE"
    assert ClaimConflictLevel.LOW.value == "LOW"
    assert ClaimConflictLevel.MEDIUM.value == "MEDIUM"
    assert ClaimConflictLevel.HIGH.value == "HIGH"
    assert ClaimConflictLevel.CRITICAL.value == "CRITICAL"
    assert ClaimConflictLevel.UNKNOWN.value == "UNKNOWN"


# ---------------------------------------------------------------------------
# Policy
# ---------------------------------------------------------------------------


def test_default_binding_policy_safe_values():
    policy = build_default_evidence_claim_binding_policy()
    assert policy.require_usable_evidence_for_support is True
    assert policy.block_conflicted_evidence is True
    assert policy.block_revoked_or_invalid_evidence is True
    assert policy.allow_stale_evidence_to_support is False
    assert policy.allow_single_evidence_to_verify_claim is False


# ---------------------------------------------------------------------------
# Binding mapping
# ---------------------------------------------------------------------------


def _make_evidence(status: CapabilityEvidenceStatus, strength: CapabilityEvidenceStrength) -> CapabilityEvidenceRecord:
    return CapabilityEvidenceRecord(
        evidence_id=f"ev_{status.value}_{strength.value}",
        kind=CapabilityEvidenceKind.EVALUATION_RESULT,
        status=status,
        strength=strength,
        claim_id="claim_001",
    )


def test_bind_usable_strong_evidence_supports_claim():
    evidence = _make_evidence(CapabilityEvidenceStatus.USABLE, CapabilityEvidenceStrength.STRONG)
    binding = bind_evidence_to_claim(binding_id="b1", claim_id="claim_001", evidence=evidence)
    assert binding.relationship == ClaimBindingRelationship.SUPPORTS
    assert binding.status == ClaimBindingStatus.BOUND
    assert binding.support_level == ClaimSupportLevel.STRONG
    assert binding.conflict_level == ClaimConflictLevel.NONE


def test_bind_usable_adequate_evidence_moderate_support():
    evidence = _make_evidence(CapabilityEvidenceStatus.USABLE, CapabilityEvidenceStrength.ADEQUATE)
    binding = bind_evidence_to_claim(binding_id="b1", claim_id="claim_001", evidence=evidence)
    assert binding.relationship == ClaimBindingRelationship.SUPPORTS
    assert binding.status == ClaimBindingStatus.BOUND
    assert binding.support_level == ClaimSupportLevel.MODERATE


def test_bind_usable_weak_evidence_partially_supports():
    evidence = _make_evidence(CapabilityEvidenceStatus.USABLE, CapabilityEvidenceStrength.WEAK)
    binding = bind_evidence_to_claim(binding_id="b1", claim_id="claim_001", evidence=evidence)
    assert binding.relationship == ClaimBindingRelationship.PARTIALLY_SUPPORTS
    assert binding.support_level == ClaimSupportLevel.WEAK


def test_bind_candidate_evidence_partially_supports_or_insufficient():
    evidence = _make_evidence(CapabilityEvidenceStatus.CANDIDATE, CapabilityEvidenceStrength.ADEQUATE)
    binding = bind_evidence_to_claim(binding_id="b1", claim_id="claim_001", evidence=evidence)
    assert binding.relationship in (ClaimBindingRelationship.PARTIALLY_SUPPORTS, ClaimBindingRelationship.INSUFFICIENT)
    assert binding.support_level in (ClaimSupportLevel.WEAK, ClaimSupportLevel.NONE)


def test_bind_insufficient_evidence_insufficient():
    evidence = _make_evidence(CapabilityEvidenceStatus.INSUFFICIENT, CapabilityEvidenceStrength.NONE)
    binding = bind_evidence_to_claim(binding_id="b1", claim_id="claim_001", evidence=evidence)
    assert binding.relationship == ClaimBindingRelationship.INSUFFICIENT
    assert binding.support_level == ClaimSupportLevel.NONE


def test_bind_conflicted_evidence_conflicts():
    evidence = _make_evidence(CapabilityEvidenceStatus.CONFLICTED, CapabilityEvidenceStrength.CONFLICTED)
    binding = bind_evidence_to_claim(binding_id="b1", claim_id="claim_001", evidence=evidence)
    assert binding.relationship == ClaimBindingRelationship.CONFLICTS
    assert binding.status == ClaimBindingStatus.CONFLICTED
    assert binding.support_level == ClaimSupportLevel.NONE


def test_bind_stale_evidence_weakens_or_insufficient():
    evidence = _make_evidence(CapabilityEvidenceStatus.STALE, CapabilityEvidenceStrength.WEAK)
    binding = bind_evidence_to_claim(binding_id="b1", claim_id="claim_001", evidence=evidence)
    assert binding.relationship in (ClaimBindingRelationship.WEAKENS, ClaimBindingRelationship.PARTIALLY_SUPPORTS)
    assert binding.support_level in (ClaimSupportLevel.NONE, ClaimSupportLevel.WEAK)


def test_bind_expired_evidence_weakens_or_insufficient():
    evidence = _make_evidence(CapabilityEvidenceStatus.EXPIRED, CapabilityEvidenceStrength.NONE)
    binding = bind_evidence_to_claim(binding_id="b1", claim_id="claim_001", evidence=evidence)
    assert binding.relationship in (ClaimBindingRelationship.WEAKENS, ClaimBindingRelationship.INSUFFICIENT)
    assert binding.support_level == ClaimSupportLevel.NONE


def test_bind_revoked_evidence_blocks():
    evidence = _make_evidence(CapabilityEvidenceStatus.REVOKED, CapabilityEvidenceStrength.NONE)
    binding = bind_evidence_to_claim(binding_id="b1", claim_id="claim_001", evidence=evidence)
    assert binding.relationship == ClaimBindingRelationship.BLOCKS
    assert binding.support_level == ClaimSupportLevel.NONE


def test_bind_invalid_evidence_blocks():
    evidence = _make_evidence(CapabilityEvidenceStatus.INVALID, CapabilityEvidenceStrength.NONE)
    binding = bind_evidence_to_claim(binding_id="b1", claim_id="claim_001", evidence=evidence)
    assert binding.relationship == ClaimBindingRelationship.BLOCKS
    assert binding.support_level == ClaimSupportLevel.NONE


def test_bind_rejected_evidence_blocks():
    evidence = _make_evidence(CapabilityEvidenceStatus.REJECTED, CapabilityEvidenceStrength.NONE)
    binding = bind_evidence_to_claim(binding_id="b1", claim_id="claim_001", evidence=evidence)
    assert binding.relationship == ClaimBindingRelationship.BLOCKS
    assert binding.support_level == ClaimSupportLevel.NONE


def test_binding_does_not_create_verified_status():
    evidence = _make_evidence(CapabilityEvidenceStatus.USABLE, CapabilityEvidenceStrength.STRONG)
    binding = bind_evidence_to_claim(binding_id="b1", claim_id="claim_001", evidence=evidence)
    assert binding.status.value != "VERIFIED"
    assert binding.relationship.value != "VERIFIED"
    assert "VERIFIED" not in binding.summary.upper()


def test_binding_capability_id_from_evidence():
    evidence = _make_evidence(CapabilityEvidenceStatus.USABLE, CapabilityEvidenceStrength.STRONG)
    evidence = CapabilityEvidenceRecord(
        evidence_id="ev_with_cap",
        kind=CapabilityEvidenceKind.EVALUATION_RESULT,
        status=CapabilityEvidenceStatus.USABLE,
        strength=CapabilityEvidenceStrength.STRONG,
        capability_id="cap_001",
    )
    binding = bind_evidence_to_claim(binding_id="b1", claim_id="claim_001", evidence=evidence)
    assert binding.capability_id == "cap_001"


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def test_validate_binding_rejects_empty_binding_id():
    binding = EvidenceClaimBinding(
        binding_id="",
        claim_id="claim_001",
        capability_id=None,
        evidence_id="ev_001",
        source_result_ids=(),
        source_result_set_ids=(),
        relationship=ClaimBindingRelationship.SUPPORTS,
        status=ClaimBindingStatus.BOUND,
        support_level=ClaimSupportLevel.STRONG,
        conflict_level=ClaimConflictLevel.NONE,
        evidence_status="USABLE",
        evidence_strength="STRONG",
        evidence_kind="EVALUATION_RESULT",
    )
    issues = validate_evidence_claim_binding(binding)
    assert any("binding_id" in i for i in issues)


def test_validate_binding_rejects_empty_claim_id():
    binding = EvidenceClaimBinding(
        binding_id="b1",
        claim_id="",
        capability_id=None,
        evidence_id="ev_001",
        source_result_ids=(),
        source_result_set_ids=(),
        relationship=ClaimBindingRelationship.SUPPORTS,
        status=ClaimBindingStatus.BOUND,
        support_level=ClaimSupportLevel.STRONG,
        conflict_level=ClaimConflictLevel.NONE,
        evidence_status="USABLE",
        evidence_strength="STRONG",
        evidence_kind="EVALUATION_RESULT",
    )
    issues = validate_evidence_claim_binding(binding)
    assert any("claim_id" in i for i in issues)


def test_validate_binding_rejects_empty_evidence_id():
    binding = EvidenceClaimBinding(
        binding_id="b1",
        claim_id="claim_001",
        capability_id=None,
        evidence_id="",
        source_result_ids=(),
        source_result_set_ids=(),
        relationship=ClaimBindingRelationship.SUPPORTS,
        status=ClaimBindingStatus.BOUND,
        support_level=ClaimSupportLevel.STRONG,
        conflict_level=ClaimConflictLevel.NONE,
        evidence_status="USABLE",
        evidence_strength="STRONG",
        evidence_kind="EVALUATION_RESULT",
    )
    issues = validate_evidence_claim_binding(binding)
    assert any("evidence_id" in i for i in issues)


def test_validate_bound_rejects_unknown_relationship():
    binding = EvidenceClaimBinding(
        binding_id="b1",
        claim_id="claim_001",
        capability_id=None,
        evidence_id="ev_001",
        source_result_ids=(),
        source_result_set_ids=(),
        relationship=ClaimBindingRelationship.UNKNOWN,
        status=ClaimBindingStatus.BOUND,
        support_level=ClaimSupportLevel.UNKNOWN,
        conflict_level=ClaimConflictLevel.NONE,
        evidence_status="USABLE",
        evidence_strength="STRONG",
        evidence_kind="EVALUATION_RESULT",
    )
    issues = validate_evidence_claim_binding(binding)
    assert any("BOUND" in i for i in issues)


def test_validate_support_requires_moderate_or_strong():
    binding = EvidenceClaimBinding(
        binding_id="b1",
        claim_id="claim_001",
        capability_id=None,
        evidence_id="ev_001",
        source_result_ids=(),
        source_result_set_ids=(),
        relationship=ClaimBindingRelationship.SUPPORTS,
        status=ClaimBindingStatus.BOUND,
        support_level=ClaimSupportLevel.WEAK,
        conflict_level=ClaimConflictLevel.NONE,
        evidence_status="USABLE",
        evidence_strength="WEAK",
        evidence_kind="EVALUATION_RESULT",
    )
    issues = validate_evidence_claim_binding(binding)
    assert any("SUPPORTS" in i for i in issues)


def test_validate_support_rejects_high_conflict():
    binding = EvidenceClaimBinding(
        binding_id="b1",
        claim_id="claim_001",
        capability_id=None,
        evidence_id="ev_001",
        source_result_ids=(),
        source_result_set_ids=(),
        relationship=ClaimBindingRelationship.SUPPORTS,
        status=ClaimBindingStatus.BOUND,
        support_level=ClaimSupportLevel.STRONG,
        conflict_level=ClaimConflictLevel.HIGH,
        evidence_status="USABLE",
        evidence_strength="STRONG",
        evidence_kind="EVALUATION_RESULT",
    )
    issues = validate_evidence_claim_binding(binding)
    assert any("SUPPORTS" in i and "conflict" in i.lower() for i in issues)


def test_validate_support_rejects_invalid_revoked_rejected_conflicted_evidence():
    binding = EvidenceClaimBinding(
        binding_id="b1",
        claim_id="claim_001",
        capability_id=None,
        evidence_id="ev_001",
        source_result_ids=(),
        source_result_set_ids=(),
        relationship=ClaimBindingRelationship.SUPPORTS,
        status=ClaimBindingStatus.BOUND,
        support_level=ClaimSupportLevel.MODERATE,
        conflict_level=ClaimConflictLevel.NONE,
        evidence_status="INVALID",
        evidence_strength="STRONG",
        evidence_kind="EVALUATION_RESULT",
    )
    issues = validate_evidence_claim_binding(binding)
    assert any("INVALID" in i for i in issues)


def test_validate_conflicts_requires_conflict_level_or_warning_or_blocker():
    binding = EvidenceClaimBinding(
        binding_id="b1",
        claim_id="claim_001",
        capability_id=None,
        evidence_id="ev_001",
        source_result_ids=(),
        source_result_set_ids=(),
        relationship=ClaimBindingRelationship.CONFLICTS,
        status=ClaimBindingStatus.CONFLICTED,
        support_level=ClaimSupportLevel.NONE,
        conflict_level=ClaimConflictLevel.NONE,
        evidence_status="CONFLICTED",
        evidence_strength="CONFLICTED",
        evidence_kind="EVALUATION_RESULT",
    )
    issues = validate_evidence_claim_binding(binding)
    assert any("CONFLICTS" in i for i in issues)


def test_validate_blocks_requires_warning_or_blocker():
    binding = EvidenceClaimBinding(
        binding_id="b1",
        claim_id="claim_001",
        capability_id=None,
        evidence_id="ev_001",
        source_result_ids=(),
        source_result_set_ids=(),
        relationship=ClaimBindingRelationship.BLOCKS,
        status=ClaimBindingStatus.BLOCKED,
        support_level=ClaimSupportLevel.NONE,
        conflict_level=ClaimConflictLevel.HIGH,
        evidence_status="REVOKED",
        evidence_strength="NONE",
        evidence_kind="EVALUATION_RESULT",
    )
    issues = validate_evidence_claim_binding(binding)
    assert any("BLOCKS" in i for i in issues)


def test_validate_invalid_requires_blocker():
    binding = EvidenceClaimBinding(
        binding_id="b1",
        claim_id="claim_001",
        capability_id=None,
        evidence_id="ev_001",
        source_result_ids=(),
        source_result_set_ids=(),
        relationship=ClaimBindingRelationship.BLOCKS,
        status=ClaimBindingStatus.INVALID,
        support_level=ClaimSupportLevel.NONE,
        conflict_level=ClaimConflictLevel.HIGH,
        evidence_status="INVALID",
        evidence_strength="NONE",
        evidence_kind="EVALUATION_RESULT",
    )
    issues = validate_evidence_claim_binding(binding)
    assert any("INVALID" in i for i in issues)


def test_binding_does_not_verify_claim():
    evidence = _make_evidence(CapabilityEvidenceStatus.USABLE, CapabilityEvidenceStrength.STRONG)
    binding = bind_evidence_to_claim(binding_id="b1", claim_id="claim_001", evidence=evidence)
    issues = validate_evidence_claim_binding(binding)
    assert issues == ()
    # Even valid binding doesn't claim verification
    assert "verif" not in binding.summary.lower()


# ---------------------------------------------------------------------------
# Serialization
# ---------------------------------------------------------------------------


def test_evidence_claim_binding_json_serializable():
    import json
    from agentic_runtime.evaluation.evidence_claim_binding import evidence_claim_binding_to_dict

    evidence = _make_evidence(CapabilityEvidenceStatus.USABLE, CapabilityEvidenceStrength.STRONG)
    binding = bind_evidence_to_claim(binding_id="b1", claim_id="claim_001", evidence=evidence)
    d = evidence_claim_binding_to_dict(binding)
    s = json.dumps(d)
    assert "SUPPORTS" in s
    assert "STRONG" in s


def test_evidence_claim_binding_decision_json_serializable():
    import json
    from agentic_runtime.evaluation.evidence_claim_binding import (
        aggregate_evidence_claim_bindings,
        evidence_claim_binding_decision_to_dict,
    )

    evidence = _make_evidence(CapabilityEvidenceStatus.USABLE, CapabilityEvidenceStrength.STRONG)
    binding = bind_evidence_to_claim(binding_id="b1", claim_id="claim_001", evidence=evidence)
    decision = aggregate_evidence_claim_bindings(
        decision_id="d1",
        claim_id="claim_001",
        bindings=(binding,),
    )
    d = evidence_claim_binding_decision_to_dict(decision)
    s = json.dumps(d)
    assert "claim_001" in s
    assert "SUPPORTS" in s
