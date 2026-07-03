"""P3-FLOW-L no-P4-implementation boundary tests.

No L object marks p4_implemented=True or creates a real execution
request: the handoff package is not P4, the candidate surface is not a
request, and the boundary map is not a bridge.
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
    build_p4_execution_handoff_package,
    build_unavailable_systems_ledger,
    describe_execution_request_candidate,
    map_runtime_submit_boundary,
)


def _p4_shaped_objects():
    return (
        P3DomainSeal(
            seal_id="fllds-test",
            contract_version=P3_DOMAIN_SEAL_VERSION,
            coverage_summary_id="fllcs-test",
            k_evaluation_summary_id="fllke-test",
            sealed_pack_values=tuple(pack.value for pack in P3FlowPack),
            truth_label=FlowTruthLabel.LOCAL_RUNTIME_SUBSTRATE,
        ),
        build_unavailable_systems_ledger(),
        build_p4_execution_handoff_package(),
        map_runtime_submit_boundary(),
        describe_execution_request_candidate(
            candidate_label="demo", source_intent_ref="intent-1"
        ),
    )


def test_no_l_object_claims_p4_implemented() -> None:
    for subject in _p4_shaped_objects():
        assert hasattr(subject, "p4_implemented")
        assert subject.p4_implemented is False
        with pytest.raises(AurelFlowValidationError):
            dataclasses.replace(subject, p4_implemented=True)


def test_no_real_execution_request_can_be_created() -> None:
    package = build_p4_execution_handoff_package()
    candidate = describe_execution_request_candidate(
        candidate_label="future request", source_intent_ref="intent-1"
    )
    for subject in (package, candidate):
        assert subject.execution_request_created is False
        with pytest.raises(AurelFlowValidationError):
            dataclasses.replace(subject, execution_request_created=True)
    # the candidate stays structurally candidate-only
    with pytest.raises(AurelFlowValidationError):
        dataclasses.replace(candidate, candidate_only=False)
    with pytest.raises(AurelFlowValidationError):
        dataclasses.replace(candidate, future_runtime_submit_required=False)


def test_the_ledger_records_p4_as_unavailable_not_implemented() -> None:
    ledger = build_unavailable_systems_ledger()
    p4_entry = next(
        entry
        for entry in ledger.entries
        if entry.system.value == "P4_EXECUTION"
    )
    assert p4_entry.implemented is False
    assert p4_entry.truth_label is FlowTruthLabel.UNAVAILABLE
    assert "P4" in p4_entry.future_owner
