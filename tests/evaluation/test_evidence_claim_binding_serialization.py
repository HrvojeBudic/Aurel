"""Evidence-to-claim binding serialization tests — P1.5.7."""
from __future__ import annotations

import json

from agentic_runtime.evaluation.capability_evidence import (
    CapabilityEvidenceKind,
    CapabilityEvidenceRecord,
    CapabilityEvidenceStatus,
    CapabilityEvidenceStrength,
)
from agentic_runtime.evaluation.evidence_claim_binding import (
    ClaimBindingRelationship,
    ClaimBindingStatus,
    ClaimConflictLevel,
    ClaimSupportLevel,
    EvidenceClaimBinding,
    EvidenceClaimBindingDecision,
    EvidenceClaimBindingPolicy,
    EvidenceClaimBindingReport,
    aggregate_evidence_claim_bindings,
    bind_evidence_to_claim,
    build_default_evidence_claim_binding_policy,
    build_p157_evidence_claim_binding_report,
    evidence_claim_binding_decision_to_dict,
    evidence_claim_binding_policy_to_dict,
    evidence_claim_binding_report_to_dict,
    evidence_claim_binding_to_dict,
)


def _make_evidence() -> CapabilityEvidenceRecord:
    return CapabilityEvidenceRecord(
        evidence_id="ev_001",
        kind=CapabilityEvidenceKind.EVALUATION_RESULT,
        status=CapabilityEvidenceStatus.USABLE,
        strength=CapabilityEvidenceStrength.STRONG,
        claim_id="claim_001",
        source_result_ids=("result_001",),
        source_result_set_ids=("rset_001",),
        evidence_refs=("ref_01", "ref_02"),
    )


def test_binding_policy_json_serializable():
    policy = build_default_evidence_claim_binding_policy()
    d = evidence_claim_binding_policy_to_dict(policy)
    assert d["require_usable_evidence_for_support"] is True
    s = json.dumps(d)
    assert "default_p157" in s


def test_binding_json_serializable():
    evidence = _make_evidence()
    binding = bind_evidence_to_claim(binding_id="b1", claim_id="claim_001", evidence=evidence)
    d = evidence_claim_binding_to_dict(binding)
    s = json.dumps(d)
    assert "b1" in s
    assert "SUPPORTS" in s
    assert "STRONG" in s


def test_binding_decision_json_serializable():
    evidence = _make_evidence()
    binding = bind_evidence_to_claim(binding_id="b1", claim_id="claim_001", evidence=evidence)
    decision = aggregate_evidence_claim_bindings(
        decision_id="d1", claim_id="claim_001", bindings=(binding,),
    )
    d = evidence_claim_binding_decision_to_dict(decision)
    s = json.dumps(d)
    assert "d1" in s


def test_binding_report_json_serializable():
    report = build_p157_evidence_claim_binding_report(sparse_binding_ready=True)
    d = evidence_claim_binding_report_to_dict(report)
    s = json.dumps(d)
    assert "P1.5.7" in s
    assert "P1.5.8" in s


def test_binding_roundtrip_preserves_relationship():
    evidence = _make_evidence()
    binding = bind_evidence_to_claim(binding_id="b1", claim_id="claim_001", evidence=evidence)
    d = evidence_claim_binding_to_dict(binding)
    assert d["relationship"] == "SUPPORTS"
    assert d["support_level"] == "STRONG"
    assert d["conflict_level"] == "NONE"


def test_binding_serialization_deterministic():
    evidence = _make_evidence()
    binding = bind_evidence_to_claim(binding_id="b1", claim_id="claim_001", evidence=evidence)
    d1 = evidence_claim_binding_to_dict(binding)
    d2 = evidence_claim_binding_to_dict(binding)
    assert d1 == d2


def test_decision_serialization_includes_lists():
    evidence = _make_evidence()
    binding = bind_evidence_to_claim(binding_id="b1", claim_id="claim_001", evidence=evidence)
    decision = aggregate_evidence_claim_bindings(
        decision_id="d1", claim_id="claim_001", bindings=(binding,),
    )
    d = evidence_claim_binding_decision_to_dict(decision)
    assert isinstance(d["bindings"], list)
    assert isinstance(d["usable_evidence_ids"], list)
    assert isinstance(d["insufficient_evidence_ids"], list)
    assert isinstance(d["conflicted_evidence_ids"], list)
    assert isinstance(d["blocked_evidence_ids"], list)
