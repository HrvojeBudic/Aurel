"""P3-FLOW-L no-TRACE_VERIFIED-claim boundary tests.

No L object claims trace_verified=True or proof_available=True, and no L
object carries the LIVE or TRACE_VERIFIED truth label: proof belongs to
P5 AurelTrace and does not exist in P3.
"""

from __future__ import annotations

import dataclasses

import pytest

from agentic_runtime.aurel_flow import (
    P3_DOMAIN_SEAL_VERSION,
    AurelFlowValidationError,
    FlowTruthLabel,
    P3DomainSeal,
    P3FlowPack,
    TruthLabelAuditCategory,
    audit_truth_labels,
    build_default_p3_pack_coverage_items,
    build_p3_coverage_summary,
    build_p4_execution_handoff_package,
    build_unavailable_systems_ledger,
    describe_execution_request_candidate,
    map_runtime_submit_boundary,
)


def _direct_seal() -> P3DomainSeal:
    return P3DomainSeal(
        seal_id="fllds-test",
        contract_version=P3_DOMAIN_SEAL_VERSION,
        coverage_summary_id="fllcs-test",
        k_evaluation_summary_id="fllke-test",
        sealed_pack_values=tuple(pack.value for pack in P3FlowPack),
        truth_label=FlowTruthLabel.LOCAL_RUNTIME_SUBSTRATE,
    )


def _l_surface():
    return (
        _direct_seal(),
        build_p3_coverage_summary(build_default_p3_pack_coverage_items()),
        build_unavailable_systems_ledger(),
        build_p4_execution_handoff_package(),
        map_runtime_submit_boundary(),
        describe_execution_request_candidate(
            candidate_label="demo", source_intent_ref="intent-1"
        ),
    )


def test_no_l_object_claims_trace_verified_or_proof() -> None:
    declaring = 0
    for subject in _l_surface():
        for field_name in ("trace_verified", "proof_available"):
            if not hasattr(subject, field_name):
                continue
            declaring += 1
            assert getattr(subject, field_name) is False
            with pytest.raises(AurelFlowValidationError):
                dataclasses.replace(subject, **{field_name: True})
    assert declaring > 0


def test_no_l_object_carries_a_live_or_trace_verified_label() -> None:
    forbidden = {FlowTruthLabel.LIVE, FlowTruthLabel.TRACE_VERIFIED}
    for subject in _l_surface():
        assert subject.truth_label not in forbidden
    ledger = build_unavailable_systems_ledger()
    for entry in ledger.entries:
        assert entry.truth_label not in forbidden
    package = build_p4_execution_handoff_package()
    for item in package.items:
        assert item.truth_label not in forbidden


def test_truth_label_audit_confirms_no_fake_trace_verified() -> None:
    read_model = audit_truth_labels(_l_surface())
    statuses = {
        finding.category: finding.status.value
        for finding in read_model.findings
    }
    assert (
        statuses[TruthLabelAuditCategory.NO_FAKE_TRACE_VERIFIED] == "PASS"
    )
    assert read_model.trace_verified_claim_allowed is False
    assert read_model.live_claim_allowed is False
    with pytest.raises(AurelFlowValidationError):
        dataclasses.replace(read_model, trace_verified_claim_allowed=True)
