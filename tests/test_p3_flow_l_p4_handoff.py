"""P3-FLOW-L P4 execution handoff behavior tests.

The handoff package names every surface P4-EXEC-A may consume and is not
P4: nothing is dispatched, wired, queued, or executable, and an execution
request candidate is not an execution request.
"""

from __future__ import annotations

import dataclasses

import pytest

from agentic_runtime.aurel_flow import (
    AurelFlowValidationError,
    FlowTruthLabel,
    P4HandoffSurface,
    build_p4_execution_handoff_package,
    create_p4_handoff_item,
    describe_execution_request_candidate,
)

_PACKAGE_FALSE_FIELDS = (
    "p4_implemented",
    "execution_request_created",
    "runtime_submit_wired",
    "runtime_submit_called",
    "dispatch_available",
    "execution_available",
    "worker_allocated",
)


def test_default_package_covers_every_handoff_surface() -> None:
    package = build_p4_execution_handoff_package()
    assert {item.surface for item in package.items} == set(P4HandoffSurface)
    for item in package.items:
        assert item.summary.strip()
        assert item.source_ref.strip()
        assert item.p4_implemented is False
        assert item.execution_request_created is False
    submit_item = next(
        item
        for item in package.items
        if item.surface is P4HandoffSurface.RUNTIME_SUBMIT_BOUNDARY
    )
    assert "never called" in submit_item.summary


def test_package_rejects_a_truncated_surface_set() -> None:
    package = build_p4_execution_handoff_package()
    with pytest.raises(AurelFlowValidationError) as excinfo:
        dataclasses.replace(package, items=package.items[:-1])
    assert P4HandoffSurface.FUTURE_BRIDGE_RECOMMENDATION.value in str(
        excinfo.value
    )
    with pytest.raises(AurelFlowValidationError):
        dataclasses.replace(
            package, items=package.items + (package.items[0],)
        )


def test_package_boundary_booleans_fail_closed() -> None:
    package = build_p4_execution_handoff_package()
    for forbidden_field in _PACKAGE_FALSE_FIELDS:
        assert getattr(package, forbidden_field) is False
        with pytest.raises(AurelFlowValidationError):
            dataclasses.replace(package, **{forbidden_field: True})


def test_handoff_item_must_carry_summary_and_source() -> None:
    with pytest.raises(AurelFlowValidationError):
        create_p4_handoff_item(
            surface=P4HandoffSurface.READY_NODE_SURFACE,
            summary="  ",
            source_ref="aurel_flow.scheduler",
        )
    with pytest.raises(AurelFlowValidationError):
        create_p4_handoff_item(
            surface=P4HandoffSurface.READY_NODE_SURFACE,
            summary="ready nodes named without execution",
            source_ref="",
        )


def test_execution_request_candidate_is_not_a_request() -> None:
    candidate = describe_execution_request_candidate(
        candidate_label="future submit of ready unit",
        source_intent_ref="scheduling-intent-1",
    )
    assert candidate.truth_label is FlowTruthLabel.CONTRACT_ONLY
    for required_field in (
        "candidate_only",
        "future_runtime_submit_required",
        "requires_operator_review",
        "requires_p5_proof",
        "requires_p9_authority",
    ):
        assert getattr(candidate, required_field) is True
        with pytest.raises(AurelFlowValidationError):
            dataclasses.replace(candidate, **{required_field: False})
    for forbidden_field in (
        "execution_request_created",
        "runtime_submit_wired",
        "runtime_submit_called",
        "dispatch_available",
        "execution_available",
        "p4_implemented",
        "worker_allocated",
    ):
        assert getattr(candidate, forbidden_field) is False
        with pytest.raises(AurelFlowValidationError):
            dataclasses.replace(candidate, **{forbidden_field: True})


def test_execution_request_candidate_requires_a_label() -> None:
    with pytest.raises(AurelFlowValidationError):
        describe_execution_request_candidate(
            candidate_label="   ", source_intent_ref="intent-1"
        )


def test_package_and_candidate_are_deterministic() -> None:
    assert (
        build_p4_execution_handoff_package().package_id
        == build_p4_execution_handoff_package().package_id
    )
    first = describe_execution_request_candidate(
        candidate_label="x", source_intent_ref="i"
    )
    second = describe_execution_request_candidate(
        candidate_label="x", source_intent_ref="i"
    )
    assert first.candidate_id == second.candidate_id
