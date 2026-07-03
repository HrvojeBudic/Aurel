"""P3-FLOW-I workflow-atomic unit / scheduling intent behavior tests.

An atomic unit is a scheduling object, never a worker job; a scheduling
intent proposes scheduling and never enqueues, dispatches, or executes.
"""

from __future__ import annotations

import dataclasses

import pytest

from agentic_runtime.aurel_flow import (
    AurelFlowValidationError,
    FlowTruthLabel,
    SchedulingIntentKind,
    SchedulingIntentReason,
    WorkflowAtomicUnitKind,
    build_scheduling_intent_boundary,
    build_scheduling_intent_read_model,
    build_workflow_atomic_boundary,
    build_workflow_atomic_read_model,
    create_scheduling_intent,
    create_workflow_atomic_unit,
    create_workflow_atomic_unit_ref,
)


def _unit(run_id: str = "run-1", node_ids: tuple[str, ...] = ("n1",)):
    return create_workflow_atomic_unit(
        run_id=run_id,
        unit_kind=WorkflowAtomicUnitKind.SINGLE_NODE,
        node_ids=node_ids,
    )


def test_atomic_unit_is_deterministic() -> None:
    assert _unit().atomic_unit_id == _unit().atomic_unit_id
    assert _unit() == _unit()


def test_atomic_unit_is_not_worker_job_and_does_not_execute() -> None:
    unit = _unit()
    assert unit.candidate_only is True
    assert unit.worker_job is False
    assert unit.execution_available is False
    assert unit.dispatch_available is False
    for forbidden_field in (
        "worker_job",
        "execution_available",
        "dispatch_available",
    ):
        with pytest.raises(AurelFlowValidationError):
            dataclasses.replace(unit, **{forbidden_field: True})
    with pytest.raises(AurelFlowValidationError):
        dataclasses.replace(unit, candidate_only=False)


def test_atomic_unit_requires_run_and_nodes() -> None:
    with pytest.raises(AurelFlowValidationError):
        create_workflow_atomic_unit(
            run_id="",
            unit_kind=WorkflowAtomicUnitKind.SINGLE_NODE,
            node_ids=("n1",),
        )
    with pytest.raises(AurelFlowValidationError):
        create_workflow_atomic_unit(
            run_id="run-1",
            unit_kind=WorkflowAtomicUnitKind.NODE_GROUP,
            node_ids=(),
        )


def test_atomic_unit_cannot_depend_on_itself() -> None:
    unit = _unit()
    with pytest.raises(AurelFlowValidationError):
        dataclasses.replace(unit, dependency_ids=(unit.atomic_unit_id,))


def test_atomic_unit_kind_vocabulary_is_closed_world() -> None:
    values = {kind.value for kind in WorkflowAtomicUnitKind}
    assert "UNAVAILABLE" in values
    assert "ERROR" in values
    for forbidden in ("WORKER_JOB", "EXECUTABLE_UNIT", "DISPATCHED_UNIT"):
        assert forbidden not in values


def test_atomic_unit_ref_dereferences_to_nothing_live() -> None:
    unit = _unit()
    ref = create_workflow_atomic_unit_ref(unit)
    assert ref.atomic_unit_id == unit.atomic_unit_id
    assert ref.dispatch_available is False
    assert ref.execution_available is False
    assert (
        create_workflow_atomic_unit_ref(unit).ref_id == ref.ref_id
    )


def test_atomic_boundary_is_fail_closed() -> None:
    boundary = build_workflow_atomic_boundary()
    assert boundary.unit_is_not_worker_job is True
    assert boundary.unit_is_not_execution_unit is True
    assert boundary.worker_spawned is False
    with pytest.raises(AurelFlowValidationError):
        dataclasses.replace(boundary, unit_is_not_worker_job=False)
    with pytest.raises(AurelFlowValidationError):
        dataclasses.replace(boundary, worker_spawned=True)


def test_atomic_read_model_counts_and_rejects_foreign_runs() -> None:
    units = (_unit(), _unit(node_ids=("n2",)))
    read_model = build_workflow_atomic_read_model(run_id="run-1", units=units)
    assert read_model.unit_count == 2
    assert read_model.unit_kind_counts == (("SINGLE_NODE", 2),)
    assert read_model.truth_label is FlowTruthLabel.READ_MODEL_ONLY
    with pytest.raises(AurelFlowValidationError):
        build_workflow_atomic_read_model(
            run_id="run-2", units=units
        )


def test_scheduling_intent_is_deterministic_and_candidate_only() -> None:
    unit = _unit()
    first = create_scheduling_intent(
        unit=unit,
        intent_kind=SchedulingIntentKind.SCHEDULE_READY_NODE_CANDIDATE,
        intent_reason=SchedulingIntentReason.DEPENDENCIES_SATISFIED,
    )
    second = create_scheduling_intent(
        unit=unit,
        intent_kind=SchedulingIntentKind.SCHEDULE_READY_NODE_CANDIDATE,
        intent_reason=SchedulingIntentReason.DEPENDENCIES_SATISFIED,
    )
    assert first.scheduling_intent_id == second.scheduling_intent_id
    assert first.candidate_only is True
    assert first.requires_p4_dispatch is True


def test_scheduling_intent_does_not_enqueue_or_dispatch() -> None:
    intent = create_scheduling_intent(
        unit=_unit(),
        intent_kind=SchedulingIntentKind.SCHEDULE_READY_NODE_CANDIDATE,
        intent_reason=SchedulingIntentReason.DEPENDENCIES_SATISFIED,
    )
    assert intent.queued is False
    assert intent.dispatched is False
    assert intent.execution_available is False
    for forbidden_field in ("queued", "dispatched", "execution_available"):
        with pytest.raises(AurelFlowValidationError):
            dataclasses.replace(intent, **{forbidden_field: True})
    with pytest.raises(AurelFlowValidationError):
        dataclasses.replace(intent, requires_p4_dispatch=False)


def test_hold_and_block_intents_require_operator_review() -> None:
    unit = _unit()
    for kind, reason in (
        (SchedulingIntentKind.HOLD_SCHEDULING, SchedulingIntentReason.BUDGET_HOLD),
        (
            SchedulingIntentKind.BLOCK_SCHEDULING,
            SchedulingIntentReason.AUTONOMY_BLOCKED,
        ),
    ):
        intent = create_scheduling_intent(
            unit=unit, intent_kind=kind, intent_reason=reason
        )
        assert intent.requires_operator_review is True


def test_scheduling_intent_kind_has_no_dispatch_verb() -> None:
    values = {kind.value for kind in SchedulingIntentKind}
    for forbidden in ("DISPATCH", "EXECUTE", "ENQUEUE", "RUN_NOW", "SUBMIT"):
        assert forbidden not in values


def test_intent_boundary_and_read_model_are_fail_closed() -> None:
    boundary = build_scheduling_intent_boundary()
    assert boundary.intent_is_not_dispatch is True
    assert boundary.runtime_submit_wired is False
    unit = _unit()
    intents = (
        create_scheduling_intent(
            unit=unit,
            intent_kind=SchedulingIntentKind.HOLD_SCHEDULING,
            intent_reason=SchedulingIntentReason.BUDGET_HOLD,
        ),
    )
    read_model = build_scheduling_intent_read_model(
        run_id="run-1", intents=intents
    )
    assert read_model.intent_count == 1
    assert read_model.hold_or_block_count == 1
    assert read_model.queued is False
    assert read_model.dispatched is False
    with pytest.raises(AurelFlowValidationError):
        build_scheduling_intent_read_model(run_id="run-2", intents=intents)
