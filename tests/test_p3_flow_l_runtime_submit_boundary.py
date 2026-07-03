"""P3-FLOW-L runtime.submit boundary map behavior tests.

The boundary map explains what P4 must build later; it is not wiring, it
never calls runtime.submit, and its primary status is structurally
future-bound.
"""

from __future__ import annotations

import dataclasses

import pytest

from agentic_runtime.aurel_flow import (
    AurelFlowValidationError,
    FlowTruthLabel,
    RuntimeSubmitBoundaryStatus,
    map_runtime_submit_boundary,
)


def test_map_is_future_bound_with_every_requirement_named() -> None:
    boundary_map = map_runtime_submit_boundary()
    assert (
        boundary_map.primary_status
        is RuntimeSubmitBoundaryStatus.NOT_WIRED_FUTURE_P4
    )
    recorded = {req.status for req in boundary_map.requirements}
    assert recorded == {
        RuntimeSubmitBoundaryStatus.REQUIRES_AUREL_EXEC,
        RuntimeSubmitBoundaryStatus.REQUIRES_CUSTOS_AUTHORITY,
        RuntimeSubmitBoundaryStatus.REQUIRES_TRACE_PROOF,
        RuntimeSubmitBoundaryStatus.REQUIRES_OPERATOR_REVIEW,
        RuntimeSubmitBoundaryStatus.REQUIRES_PERSISTENCE_STRATEGY,
    }
    owners = {
        req.status: req.future_owner for req in boundary_map.requirements
    }
    assert (
        owners[RuntimeSubmitBoundaryStatus.REQUIRES_CUSTOS_AUTHORITY]
        == "P9 Custos"
    )
    assert (
        owners[RuntimeSubmitBoundaryStatus.REQUIRES_TRACE_PROOF]
        == "P5 AurelTrace"
    )


def test_map_never_wires_or_calls_runtime_submit() -> None:
    boundary_map = map_runtime_submit_boundary()
    for forbidden_field in (
        "runtime_submit_wired",
        "runtime_submit_called",
        "p4_implemented",
        "dispatch_available",
        "execution_available",
    ):
        assert getattr(boundary_map, forbidden_field) is False
        with pytest.raises(AurelFlowValidationError):
            dataclasses.replace(boundary_map, **{forbidden_field: True})
    for requirement in boundary_map.requirements:
        assert requirement.runtime_submit_wired is False
        assert requirement.runtime_submit_called is False
        with pytest.raises(AurelFlowValidationError):
            dataclasses.replace(requirement, runtime_submit_wired=True)


def test_primary_status_cannot_claim_a_wired_or_satisfied_posture() -> None:
    boundary_map = map_runtime_submit_boundary()
    for wrong_status in (
        RuntimeSubmitBoundaryStatus.REQUIRES_AUREL_EXEC,
        RuntimeSubmitBoundaryStatus.REQUIRES_OPERATOR_REVIEW,
        RuntimeSubmitBoundaryStatus.ERROR,
    ):
        with pytest.raises(AurelFlowValidationError):
            dataclasses.replace(boundary_map, primary_status=wrong_status)
    # UNAVAILABLE stays an honest allowed posture
    unavailable = dataclasses.replace(
        boundary_map,
        primary_status=RuntimeSubmitBoundaryStatus.UNAVAILABLE,
    )
    assert (
        unavailable.primary_status is RuntimeSubmitBoundaryStatus.UNAVAILABLE
    )


def test_map_requires_the_full_requirement_set() -> None:
    boundary_map = map_runtime_submit_boundary()
    with pytest.raises(AurelFlowValidationError) as excinfo:
        dataclasses.replace(
            boundary_map, requirements=boundary_map.requirements[1:]
        )
    assert RuntimeSubmitBoundaryStatus.REQUIRES_AUREL_EXEC.value in str(
        excinfo.value
    )


def test_map_is_deterministic_contract_only() -> None:
    first = map_runtime_submit_boundary()
    second = map_runtime_submit_boundary()
    assert first.boundary_map_id == second.boundary_map_id
    assert first.truth_label is FlowTruthLabel.CONTRACT_ONLY
