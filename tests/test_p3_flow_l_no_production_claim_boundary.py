"""P3-FLOW-L no-production-claim boundary tests.

No L object claims production_ready=True or release_approved=True: the
seal is a control-plane statement, the coverage summary is bookkeeping,
and the truth-label audit rejects any fake production posture.
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
    run_boundary_exit_audit,
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


def test_no_l_object_claims_production_or_release() -> None:
    for subject in _l_surface():
        for field_name in (
            "production_ready",
            "release_approved",
            "live_path_available",
        ):
            if not hasattr(subject, field_name):
                continue
            assert getattr(subject, field_name) is False
            with pytest.raises(AurelFlowValidationError):
                dataclasses.replace(subject, **{field_name: True})


def test_the_seal_declares_the_full_production_boundary() -> None:
    seal = _direct_seal()
    assert seal.p3_control_plane_sealed is True
    assert seal.production_ready is False
    assert seal.release_approved is False
    assert seal.live_path_available is False


def test_truth_label_audit_finds_no_production_claim_on_l_objects() -> None:
    read_model = audit_truth_labels(_l_surface())
    statuses = {
        finding.category: finding.status for finding in read_model.findings
    }
    assert statuses[TruthLabelAuditCategory.NO_FAKE_PRODUCTION_READY].value == "PASS"
    assert read_model.production_ready_claim_allowed is False


def test_the_exit_audit_read_model_cannot_go_production() -> None:
    read_model = run_boundary_exit_audit(_l_surface())
    assert read_model.production_ready is False
    with pytest.raises(AurelFlowValidationError):
        dataclasses.replace(read_model, production_ready=True)
