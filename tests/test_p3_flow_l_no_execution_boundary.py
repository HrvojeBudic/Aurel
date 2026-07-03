"""P3-FLOW-L no-execution boundary tests.

No L object executes a workflow, dispatches, wires or calls
runtime.submit, enqueues work, allocates workers, invokes
models/tools/sandboxes/networks, or mutates runtime state — every
execution-shaped boolean is structurally fail-closed False.
"""

from __future__ import annotations

import dataclasses

import pytest

from agentic_runtime.aurel_flow import (
    P3_DOMAIN_SEAL_VERSION,
    AurelFlowValidationError,
    BoundaryExitCategory,
    FlowTruthLabel,
    P3AuditStatus,
    P3DomainSeal,
    P3FlowPack,
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


_EXECUTION_FIELDS = (
    "workflow_executed",
    "execution_available",
    "execution_request_created",
    "dispatch_available",
    "runtime_submit_wired",
    "runtime_submit_called",
    "worker_allocated",
)


def test_every_l_object_keeps_execution_booleans_false() -> None:
    declaring_type_names: set[str] = set()
    for subject in _l_surface():
        for field_name in _EXECUTION_FIELDS:
            if not hasattr(subject, field_name):
                continue
            declaring_type_names.add(type(subject).__name__)
            assert getattr(subject, field_name) is False
            with pytest.raises(AurelFlowValidationError):
                dataclasses.replace(subject, **{field_name: True})
    # the execution-shaped L objects all declare the boundary
    assert {
        "P3DomainSeal",
        "P4ExecutionHandoffPackage",
        "RuntimeSubmitBoundaryMap",
        "ExecutionRequestCandidateSurface",
    } <= declaring_type_names


def test_the_exit_audit_confirms_no_execution_over_the_l_surface() -> None:
    read_model = run_boundary_exit_audit(_l_surface())
    statuses = {
        finding.category: finding.status for finding in read_model.findings
    }
    for category in (
        BoundaryExitCategory.NO_RUNTIME_SUBMIT,
        BoundaryExitCategory.NO_EXECUTION,
        BoundaryExitCategory.NO_DISPATCH,
    ):
        assert statuses[category] is P3AuditStatus.PASS
    assert read_model.all_applicable_passed is True


def test_no_l_module_reaches_execution_machinery() -> None:
    from agentic_runtime.aurel_flow import (
        flow_domain_seal,
        flow_p3_audit,
        flow_p4_handoff,
        flow_seal_projection,
    )

    for module in (
        flow_domain_seal,
        flow_p3_audit,
        flow_p4_handoff,
        flow_seal_projection,
    ):
        source = open(module.__file__, encoding="utf-8").read()
        for forbidden in (
            "import subprocess",
            "import socket",
            "import httpx",
            "import urllib",
            "import requests",
            "runtime.submit(",
            ".submit(",
        ):
            assert forbidden not in source, (
                f"{module.__name__} references {forbidden!r}"
            )
