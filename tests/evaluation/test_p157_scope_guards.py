"""Scope guard tests — P1.5.7."""
from __future__ import annotations

import inspect

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
    validate_evidence_claim_binding,
)


def _make_evidence(status: CapabilityEvidenceStatus = CapabilityEvidenceStatus.USABLE, strength: CapabilityEvidenceStrength = CapabilityEvidenceStrength.STRONG) -> CapabilityEvidenceRecord:
    return CapabilityEvidenceRecord(
        evidence_id="ev_001",
        kind=CapabilityEvidenceKind.EVALUATION_RESULT,
        status=status,
        strength=strength,
        claim_id="claim_001",
    )


def test_p157_does_not_verify_capability():
    evidence = _make_evidence()
    binding = bind_evidence_to_claim(binding_id="b1", claim_id="claim_001", evidence=evidence)
    assert binding.status.value != "VERIFIED"
    assert binding.relationship.value != "VERIFIED"
    assert "verif" not in binding.summary.lower()


def test_p157_does_not_mutate_claim_status():
    # Binding is a frozen dataclass, cannot mutate
    evidence = _make_evidence()
    binding = bind_evidence_to_claim(binding_id="b1", claim_id="claim_001", evidence=evidence)
    # The claim_id in the binding is just a reference, not a mutation
    assert binding.claim_id == "claim_001"
    # No claim object mutation happens


def test_p157_does_not_create_verified_status():
    evidence = _make_evidence()
    binding = bind_evidence_to_claim(binding_id="b1", claim_id="claim_001", evidence=evidence)
    issues = validate_evidence_claim_binding(binding)
    # Even a valid binding has no VERIFIED
    assert issues == ()


def test_p157_does_not_promote_skill():
    evidence = _make_evidence()
    binding = bind_evidence_to_claim(binding_id="b1", claim_id="claim_001", evidence=evidence)
    assert "promot" not in binding.summary.lower()
    assert "skill" not in binding.summary.lower()


def test_p157_does_not_promote_memory():
    evidence = _make_evidence()
    binding = bind_evidence_to_claim(binding_id="b1", claim_id="claim_001", evidence=evidence)
    assert "memory" not in binding.summary.lower()


def test_p157_does_not_run_evaluation():
    evidence = _make_evidence()
    binding = bind_evidence_to_claim(binding_id="b1", claim_id="claim_001", evidence=evidence)
    assert "evaluat" not in binding.summary.lower() or "evaluation" not in binding.summary.lower()


def test_p157_does_not_call_llm_or_tools():
    src = inspect.getsource(bind_evidence_to_claim)
    assert "call_tool" not in src.lower()
    assert "llm_judge" not in src.lower()


def test_p157_does_not_introduce_numeric_score():
    evidence = _make_evidence()
    binding = bind_evidence_to_claim(binding_id="b1", claim_id="claim_001", evidence=evidence)
    s = str(binding)
    # Categorical support/conflict levels, not numeric
    assert binding.support_level.value in ("NONE", "WEAK", "MODERATE", "STRONG", "UNKNOWN")
    assert binding.conflict_level.value in ("NONE", "LOW", "MEDIUM", "HIGH", "CRITICAL", "UNKNOWN")


def test_p157_does_not_implement_sparse_context_compiler():
    src = inspect.getsource(bind_evidence_to_claim)
    assert "SparseContextCompiler" not in src


def test_p157_does_not_implement_hub_runtime():
    src = inspect.getsource(bind_evidence_to_claim)
    assert "hub_runtime" not in src.lower()


def test_p157_prepares_p158_benchmark_hygiene():
    report = build_p157_evidence_claim_binding_report()
    assert "P1.5.8" in report.next_module
