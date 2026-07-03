"""P3-FLOW-I queue placement candidate / dependency-concurrency window tests.

A queue placement candidate is not queue insertion and no worker receives
work; a concurrency window is not parallel execution and a parallelism
candidate spawns no worker.
"""

from __future__ import annotations

import dataclasses

import pytest

from agentic_runtime.aurel_flow import (
    AurelFlowValidationError,
    DispatchabilityReason,
    FlowTruthLabel,
    QueuePlacementKind,
    WorkflowAtomicUnitKind,
    build_concurrency_boundary,
    build_concurrency_read_model,
    build_queue_placement_boundary,
    build_queue_placement_read_model,
    classify_dispatchability,
    create_concurrency_window,
    create_dependency_window,
    create_parallelism_candidate,
    create_ready_state_frame,
    create_workflow_atomic_unit,
    derive_queue_placement_candidate,
)
from agentic_runtime.aurel_flow.flow_dispatchability import (
    _DISPATCHABILITY_TO_QUEUE_PLACEMENT,
)


def _dispatchability(**overrides):
    unit = create_workflow_atomic_unit(
        run_id="run-1",
        unit_kind=WorkflowAtomicUnitKind.SINGLE_NODE,
        node_ids=("n1",),
    )
    kwargs = dict(dependency_ready=True, state_ready=True)
    kwargs.update(overrides)
    return classify_dispatchability(
        create_ready_state_frame(unit=unit, **kwargs)
    )


def test_queue_placement_mapping_is_total_over_dispatchability_reasons() -> None:
    assert set(_DISPATCHABILITY_TO_QUEUE_PLACEMENT) == set(DispatchabilityReason)


def test_ready_candidate_maps_to_ready_queue_candidate() -> None:
    candidate = derive_queue_placement_candidate(_dispatchability())
    assert candidate.placement_kind is QueuePlacementKind.READY_QUEUE_CANDIDATE
    assert candidate.queue_candidate_only is True
    assert candidate.actual_queue_inserted is False
    assert candidate.worker_assigned is False


def test_queue_candidate_never_inserts_or_assigns_workers() -> None:
    candidate = derive_queue_placement_candidate(
        _dispatchability(operator_ready=False), priority_hint=3
    )
    assert candidate.priority_hint == 3
    for forbidden_field in (
        "actual_queue_inserted",
        "worker_assigned",
        "dispatch_available",
        "execution_available",
    ):
        with pytest.raises(AurelFlowValidationError):
            dataclasses.replace(candidate, **{forbidden_field: True})
    with pytest.raises(AurelFlowValidationError):
        dataclasses.replace(candidate, queue_candidate_only=False)


def test_queue_candidate_derivation_is_deterministic() -> None:
    first = derive_queue_placement_candidate(_dispatchability())
    second = derive_queue_placement_candidate(_dispatchability())
    assert first.queue_candidate_id == second.queue_candidate_id


def test_queue_boundary_and_read_model_are_fail_closed() -> None:
    boundary = build_queue_placement_boundary()
    assert boundary.candidate_is_not_queue_insertion is True
    assert boundary.no_worker_receives_work_in_p3 is True
    candidates = (derive_queue_placement_candidate(_dispatchability()),)
    read_model = build_queue_placement_read_model(
        run_id="run-1", candidates=candidates
    )
    assert read_model.candidate_count == 1
    assert read_model.actual_queue_inserted is False
    assert read_model.worker_assigned is False
    assert read_model.truth_label is FlowTruthLabel.READ_MODEL_ONLY
    with pytest.raises(AurelFlowValidationError):
        build_queue_placement_read_model(run_id="run-2", candidates=candidates)


def test_dependency_window_is_deterministic_and_orders_nothing_live() -> None:
    def make():
        return create_dependency_window(
            run_id="run-1",
            atomic_unit_ids=("u2", "u1"),
            required_predecessor_unit_ids=("u0",),
            blocked_by_unit_ids=("u0",),
        )

    assert make().dependency_window_id == make().dependency_window_id
    window = make()
    assert window.atomic_unit_ids == ("u1", "u2")
    assert window.window_is_not_execution_order is True
    assert window.dispatch_available is False
    with pytest.raises(AurelFlowValidationError):
        create_dependency_window(run_id="run-1", atomic_unit_ids=())


def test_concurrency_window_is_deterministic_and_candidate_only() -> None:
    def make():
        return create_concurrency_window(
            run_id="run-1",
            atomic_unit_ids=("u1", "u2", "u3"),
            parallel_candidate_unit_ids=("u1", "u2"),
            unsafe_parallel_unit_ids=("u3",),
            shared_resource_constraints=("sandbox-slot",),
            requires_operator_ordering=True,
        )

    assert make().concurrency_window_id == make().concurrency_window_id
    window = make()
    assert window.parallelism_candidate_only is True
    assert window.worker_spawned is False
    assert window.parallel_execution_available is False
    for forbidden_field in ("worker_spawned", "parallel_execution_available"):
        with pytest.raises(AurelFlowValidationError):
            dataclasses.replace(window, **{forbidden_field: True})


def test_concurrency_window_rejects_overlapping_or_unknown_units() -> None:
    with pytest.raises(AurelFlowValidationError):
        create_concurrency_window(
            run_id="run-1",
            atomic_unit_ids=("u1", "u2"),
            parallel_candidate_unit_ids=("u1",),
            unsafe_parallel_unit_ids=("u1",),
        )
    with pytest.raises(AurelFlowValidationError):
        create_concurrency_window(
            run_id="run-1",
            atomic_unit_ids=("u1",),
            parallel_candidate_unit_ids=("u9",),
        )


def test_parallelism_candidate_spawns_no_worker() -> None:
    candidate = create_parallelism_candidate(
        run_id="run-1", atomic_unit_ids=("u1", "u2")
    )
    assert candidate.parallelism_candidate_only is True
    assert candidate.worker_spawned is False
    with pytest.raises(AurelFlowValidationError):
        dataclasses.replace(candidate, worker_spawned=True)
    with pytest.raises(AurelFlowValidationError):
        create_parallelism_candidate(run_id="run-1", atomic_unit_ids=("u1",))


def test_concurrency_boundary_and_read_model_are_fail_closed() -> None:
    boundary = build_concurrency_boundary()
    assert boundary.window_is_not_parallel_execution is True
    assert boundary.parallelism_candidate_is_not_worker_spawn is True
    window = create_concurrency_window(
        run_id="run-1",
        atomic_unit_ids=("u1", "u2"),
        parallel_candidate_unit_ids=("u1", "u2"),
        requires_operator_ordering=True,
    )
    read_model = build_concurrency_read_model(
        run_id="run-1",
        dependency_windows=(
            create_dependency_window(run_id="run-1", atomic_unit_ids=("u1",)),
        ),
        concurrency_windows=(window,),
        parallelism_candidates=(
            create_parallelism_candidate(
                run_id="run-1", atomic_unit_ids=("u1", "u2")
            ),
        ),
    )
    assert read_model.dependency_window_count == 1
    assert read_model.concurrency_window_count == 1
    assert read_model.parallelism_candidate_count == 1
    assert read_model.operator_ordering_required_count == 1
    assert read_model.worker_spawned is False
    with pytest.raises(AurelFlowValidationError):
        build_concurrency_read_model(
            run_id="run-2", concurrency_windows=(window,)
        )
