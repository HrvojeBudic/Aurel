"""P3-FLOW-I resource prediction behavior tests.

Prediction is not allocation; an estimate is not measured usage; resource
availability is not permission.
"""

from __future__ import annotations

import dataclasses

import pytest

from agentic_runtime.aurel_flow import (
    AurelFlowValidationError,
    EstimateConfidence,
    FlowTruthLabel,
    ResourceDimension,
    WorkflowAtomicUnitKind,
    build_resource_availability_boundary,
    build_resource_prediction_frame,
    build_resource_prediction_read_model,
    create_resource_pressure_signal,
    create_resource_requirement_estimate,
    create_workflow_atomic_unit,
)


def _unit(node_ids: tuple[str, ...] = ("n1",)):
    return create_workflow_atomic_unit(
        run_id="run-1",
        unit_kind=WorkflowAtomicUnitKind.SINGLE_NODE,
        node_ids=node_ids,
    )


def _frame(unit=None):
    unit = unit or _unit()
    estimate = create_resource_requirement_estimate(
        unit=unit,
        dimension=ResourceDimension.TOKEN_BUDGET,
        estimated_magnitude="~4k tokens",
        confidence=EstimateConfidence.LOW,
    )
    signal = create_resource_pressure_signal(
        unit=unit,
        dimension=ResourceDimension.CONTEXT_WINDOW,
        pressure_detected=True,
        detail="predicted context pressure near the window limit",
    )
    return build_resource_prediction_frame(
        unit=unit,
        estimated_requirements=(estimate,),
        pressure_signals=(signal,),
    )


def test_requirement_estimate_is_deterministic_and_not_allocation() -> None:
    unit = _unit()

    def make():
        return create_resource_requirement_estimate(
            unit=unit,
            dimension=ResourceDimension.COST,
            estimated_magnitude="low",
        )

    assert make().estimate_id == make().estimate_id
    estimate = make()
    for forbidden_field in (
        "resource_allocated",
        "resource_reserved",
        "measured_usage",
        "permission_granted",
    ):
        assert getattr(estimate, forbidden_field) is False
        with pytest.raises(AurelFlowValidationError):
            dataclasses.replace(estimate, **{forbidden_field: True})


def test_estimate_confidence_has_no_measured_or_proven_member() -> None:
    values = {confidence.value for confidence in EstimateConfidence}
    for forbidden in ("MEASURED", "PROVEN", "VERIFIED", "CERTAIN"):
        assert forbidden not in values


def test_pressure_signal_is_not_measurement() -> None:
    unit = _unit()
    signal = create_resource_pressure_signal(
        unit=unit,
        dimension=ResourceDimension.LATENCY,
        pressure_detected=True,
        detail="predicted",
    )
    assert signal.measured_usage is False
    assert signal.resource_allocated is False
    with pytest.raises(AurelFlowValidationError):
        dataclasses.replace(signal, measured_usage=True)


def test_availability_boundary_is_fail_closed() -> None:
    boundary = build_resource_availability_boundary()
    assert boundary.prediction_is_not_allocation is True
    assert boundary.availability_is_not_permission is True
    with pytest.raises(AurelFlowValidationError):
        dataclasses.replace(boundary, availability_is_not_permission=False)
    with pytest.raises(AurelFlowValidationError):
        dataclasses.replace(boundary, resource_allocated=True)


def test_prediction_frame_aggregates_dimensions_and_pressure() -> None:
    frame = _frame()
    assert frame.resource_dimensions == (
        ResourceDimension.CONTEXT_WINDOW,
        ResourceDimension.TOKEN_BUDGET,
    )
    assert frame.resource_pressure_detected is True
    assert frame.resource_allocated is False
    assert frame.resource_reserved is False
    assert frame.measured_usage is False
    assert frame.permission_granted is False
    assert frame.execution_available is False


def test_prediction_frame_does_not_allocate_or_reserve() -> None:
    frame = _frame()
    for forbidden_field in (
        "resource_allocated",
        "resource_reserved",
        "measured_usage",
        "permission_granted",
        "execution_available",
    ):
        with pytest.raises(AurelFlowValidationError):
            dataclasses.replace(frame, **{forbidden_field: True})


def test_prediction_frame_rejects_foreign_unit_entries() -> None:
    unit = _unit()
    other = _unit(node_ids=("n2",))
    estimate = create_resource_requirement_estimate(
        unit=other,
        dimension=ResourceDimension.COST,
        estimated_magnitude="low",
    )
    with pytest.raises(AurelFlowValidationError):
        build_resource_prediction_frame(
            unit=unit, estimated_requirements=(estimate,)
        )


def test_prediction_frame_is_deterministic() -> None:
    assert (
        _frame().resource_prediction_id == _frame().resource_prediction_id
    )


def test_prediction_read_model_counts_and_rejects_foreign_runs() -> None:
    frames = (_frame(),)
    read_model = build_resource_prediction_read_model(
        run_id="run-1", frames=frames
    )
    assert read_model.frame_count == 1
    assert read_model.pressure_detected_count == 1
    assert read_model.truth_label is FlowTruthLabel.READ_MODEL_ONLY
    assert read_model.resource_allocated is False
    with pytest.raises(AurelFlowValidationError):
        build_resource_prediction_read_model(run_id="run-2", frames=frames)
