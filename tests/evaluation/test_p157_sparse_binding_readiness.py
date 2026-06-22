"""Sparse binding readiness tests — P1.5.7."""
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
    bind_evidence_to_claim,
    build_p157_evidence_claim_binding_report,
)


def _make_sparse_evidence(
    evidence_id: str,
    claim_id: str = "claim_sparse_context_001",
    status: CapabilityEvidenceStatus = CapabilityEvidenceStatus.USABLE,
    strength: CapabilityEvidenceStrength = CapabilityEvidenceStrength.ADEQUATE,
    summary: str = "",
) -> CapabilityEvidenceRecord:
    return CapabilityEvidenceRecord(
        evidence_id=evidence_id,
        kind=CapabilityEvidenceKind.EVALUATION_RESULT,
        status=status,
        strength=strength,
        claim_id=claim_id,
        evidence_refs=("ref_sc_001",),
        summary=summary or "Sparse context evaluation evidence. Sparse Context Compiler NOT implemented.",
    )


def test_sparse_context_evidence_can_bind_to_claim():
    evidence = _make_sparse_evidence("ev_sc_001")
    binding = bind_evidence_to_claim(
        binding_id="b_sc_001", claim_id="claim_sparse_context_001", evidence=evidence,
    )
    assert binding.relationship == ClaimBindingRelationship.SUPPORTS
    assert binding.support_level == ClaimSupportLevel.MODERATE


def test_lost_context_risk_evidence_can_weaken_claim():
    evidence = _make_sparse_evidence(
        "ev_lcr_001",
        claim_id="claim_lost_context_risk",
        status=CapabilityEvidenceStatus.STALE,
        strength=CapabilityEvidenceStrength.WEAK,
    )
    binding = bind_evidence_to_claim(
        binding_id="b_lcr_001", claim_id="claim_lost_context_risk", evidence=evidence,
    )
    assert binding.relationship in (ClaimBindingRelationship.WEAKENS, ClaimBindingRelationship.PARTIALLY_SUPPORTS)
    assert binding.support_level in (ClaimSupportLevel.NONE, ClaimSupportLevel.WEAK)


def test_contradiction_survival_conflict_blocks_support():
    evidence = _make_sparse_evidence(
        "ev_cs_conflict",
        claim_id="claim_contradiction_survival",
        status=CapabilityEvidenceStatus.CONFLICTED,
        strength=CapabilityEvidenceStrength.CONFLICTED,
    )
    binding = bind_evidence_to_claim(
        binding_id="b_cs_001", claim_id="claim_contradiction_survival", evidence=evidence,
    )
    assert binding.relationship == ClaimBindingRelationship.CONFLICTS
    assert binding.support_level == ClaimSupportLevel.NONE


def test_evidence_recall_strong_evidence_supports_sparse_claim():
    evidence = _make_sparse_evidence(
        "ev_recall_001",
        claim_id="claim_evidence_recall",
        status=CapabilityEvidenceStatus.USABLE,
        strength=CapabilityEvidenceStrength.STRONG,
    )
    binding = bind_evidence_to_claim(
        binding_id="b_recall_001", claim_id="claim_evidence_recall", evidence=evidence,
    )
    assert binding.relationship == ClaimBindingRelationship.SUPPORTS
    assert binding.support_level == ClaimSupportLevel.STRONG


def test_context_budget_quality_evidence_can_support_sparse_claim():
    evidence = _make_sparse_evidence(
        "ev_cbq_001",
        claim_id="claim_context_budget_quality",
        status=CapabilityEvidenceStatus.USABLE,
        strength=CapabilityEvidenceStrength.ADEQUATE,
    )
    binding = bind_evidence_to_claim(
        binding_id="b_cbq_001", claim_id="claim_context_budget_quality", evidence=evidence,
    )
    assert binding.relationship == ClaimBindingRelationship.SUPPORTS


def test_sparse_binding_does_not_run_sparse_compiler():
    evidence = _make_sparse_evidence("ev_sc_002")
    binding = bind_evidence_to_claim(
        binding_id="b_sc_002", claim_id="claim_sparse", evidence=evidence,
    )
    s = str(binding)
    assert "SparseContextCompiler" not in s


def test_sparse_binding_does_not_claim_ssa_implemented():
    evidence = _make_sparse_evidence("ev_sc_003")
    binding = bind_evidence_to_claim(
        binding_id="b_sc_003", claim_id="claim_sparse", evidence=evidence,
    )
    s = str(binding)
    assert "subquadratic" not in s.lower()
    assert "ssa" not in s.lower()


def test_sparse_binding_does_not_claim_subquadratic_model_implemented():
    report = build_p157_evidence_claim_binding_report(sparse_binding_ready=True)
    assert "subquadratic" not in report.summary.lower()
    assert "ssa" not in report.summary.lower()
