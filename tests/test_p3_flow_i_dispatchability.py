"""P3-FLOW-I ready-vs-dispatchable boundary behavior tests.

Ready is not dispatchable: a fully ready unit is a dispatchable candidate
with reason READY_BUT_NO_P4 and nothing is ever dispatched.
"""

from __future__ import annotations

import dataclasses

import pytest

from agentic_runtime.aurel_flow import (
    AurelFlowValidationError,
    DispatchabilityReason,
    FlowTruthLabel,
    ReadinessDimension,
    WorkflowAtomicUnitKind,
    build_dispatchability_read_model,
    classify_dispatchability,
    create_ready_state_frame,
    create_workflow_atomic_unit,
)


def _unit():
    return create_workflow_atomic_unit(
        run_id="run-1",
        unit_kind=WorkflowAtomicUnitKind.SINGLE_NODE,
        node_ids=("n1",),
    )


def _ready(**overrides):
    kwargs = dict(dependency_ready=True, state_ready=True)
    kwargs.update(overrides)
    return create_ready_state_frame(unit=_unit(), **kwargs)


def test_ready_frame_is_deterministic() -> None:
    assert _ready().ready_state_id == _ready().ready_state_id


def test_ready_frame_cannot_claim_policy_proof_or_execution_ready() -> None:
    frame = _ready()
    assert frame.ready_is_not_dispatchable is True
    assert frame.policy_ready is False
    assert frame.proof_ready is False
    assert frame.execution_ready is False
    for forbidden_field in (
        "policy_ready",
        "proof_ready",
        "execution_ready",
        "dispatch_available",
        "execution_available",
    ):
        with pytest.raises(AurelFlowValidationError):
            dataclasses.replace(frame, **{forbidden_field: True})
    with pytest.raises(AurelFlowValidationError):
        dataclasses.replace(frame, ready_is_not_dispatchable=False)


def test_readiness_dimensions_mark_p4_p5_p9_unavailable() -> None:
    values = {dim.value for dim in ReadinessDimension}
    assert "POLICY_READY_UNAVAILABLE" in values
    assert "PROOF_READY_UNAVAILABLE" in values
    assert "EXECUTION_READY_UNAVAILABLE" in values
    assert "EXECUTION_READY" not in values


def test_fully_ready_is_candidate_only_never_dispatched() -> None:
    frame = classify_dispatchability(_ready())
    assert frame.dispatchable_candidate is True
    assert frame.dispatchability_reason is DispatchabilityReason.READY_BUT_NO_P4
    assert frame.dispatch_available is False
    assert frame.dispatched is False
    assert frame.execution_available is False


def test_dispatchability_explains_every_blocking_dimension() -> None:
    cases = (
        ({"dependency_ready": False}, DispatchabilityReason.NOT_READY_DEPENDENCIES),
        ({"state_ready": False}, DispatchabilityReason.NOT_READY_STATE),
        ({"budget_ready": False}, DispatchabilityReason.READY_BUT_BUDGET_EXHAUSTED),
        ({"autonomy_ready": False}, DispatchabilityReason.READY_BUT_AUTONOMY_BLOCKED),
        (
            {"checkpoint_ready": False},
            DispatchabilityReason.READY_BUT_CHECKPOINT_REQUIRED,
        ),
        (
            {"resource_ready": False},
            DispatchabilityReason.READY_BUT_RESOURCE_UNAVAILABLE,
        ),
        ({"operator_ready": False}, DispatchabilityReason.READY_BUT_REQUIRES_OPERATOR),
    )
    for overrides, expected_reason in cases:
        frame = classify_dispatchability(_ready(**overrides))
        assert frame.dispatchability_reason is expected_reason
        assert frame.dispatchable_candidate is False
        assert frame.explanation


def test_guard_signals_outrank_readiness() -> None:
    storm = classify_dispatchability(_ready(), retry_storm_active=True)
    assert storm.dispatchability_reason is DispatchabilityReason.READY_BUT_RETRY_STORM
    stall = classify_dispatchability(_ready(), no_progress_active=True)
    assert stall.dispatchability_reason is DispatchabilityReason.READY_BUT_NO_PROGRESS


def test_dispatchability_frame_cannot_claim_dispatch() -> None:
    frame = classify_dispatchability(_ready())
    for forbidden_field in (
        "dispatch_available",
        "dispatched",
        "execution_available",
    ):
        with pytest.raises(AurelFlowValidationError):
            dataclasses.replace(frame, **{forbidden_field: True})


def test_classifier_is_deterministic() -> None:
    first = classify_dispatchability(_ready(budget_ready=False))
    second = classify_dispatchability(_ready(budget_ready=False))
    assert first.dispatchability_id == second.dispatchability_id


def test_dispatchability_read_model_counts_and_rejects_foreign_runs() -> None:
    frames = (
        classify_dispatchability(_ready()),
        classify_dispatchability(_ready(budget_ready=False)),
    )
    read_model = build_dispatchability_read_model(run_id="run-1", frames=frames)
    assert read_model.frame_count == 2
    assert read_model.dispatchable_candidate_count == 1
    assert read_model.truth_label is FlowTruthLabel.READ_MODEL_ONLY
    assert read_model.dispatched is False
    with pytest.raises(AurelFlowValidationError):
        build_dispatchability_read_model(run_id="run-2", frames=frames)
