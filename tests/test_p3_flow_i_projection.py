"""P3-FLOW-I scheduling projection / React readiness tests.

React is projection only: every view model and the envelope are read-only,
a UI schedule button is not dispatch, and a UI queue action is not execution.
"""

from __future__ import annotations

import dataclasses

import pytest

from agentic_runtime.aurel_flow import (
    AurelFlowValidationError,
    FlowTruthLabel,
    ResourceDimension,
    SchedulingIntentKind,
    SchedulingIntentReason,
    WorkflowAtomicUnitKind,
    build_concurrency_window_view_model,
    build_dispatchability_view_model,
    build_queue_candidate_view_model,
    build_resource_prediction_frame,
    build_resource_prediction_view_model,
    build_scheduling_intent_view_model,
    build_scheduling_projection_envelope,
    build_scheduling_react_projection_boundary,
    build_scheduling_timeline_view_model,
    classify_dispatchability,
    create_concurrency_window,
    create_ready_state_frame,
    create_resource_requirement_estimate,
    create_scheduling_intent,
    create_workflow_atomic_unit,
    derive_queue_placement_candidate,
)

_UI_FALSE_FIELDS = (
    "frontend_mutation_allowed",
    "ui_schedule_action_allowed",
    "ui_queue_action_allowed",
    "ui_dispatch_allowed",
    "api_server_implemented",
    "frontend_implemented",
)


def _fixture():
    unit = create_workflow_atomic_unit(
        run_id="run-1",
        unit_kind=WorkflowAtomicUnitKind.SINGLE_NODE,
        node_ids=("n1",),
    )
    intent = create_scheduling_intent(
        unit=unit,
        intent_kind=SchedulingIntentKind.SCHEDULE_READY_NODE_CANDIDATE,
        intent_reason=SchedulingIntentReason.DEPENDENCIES_SATISFIED,
    )
    dispatchability = classify_dispatchability(
        create_ready_state_frame(
            unit=unit, dependency_ready=True, state_ready=True
        )
    )
    prediction = build_resource_prediction_frame(
        unit=unit,
        estimated_requirements=(
            create_resource_requirement_estimate(
                unit=unit,
                dimension=ResourceDimension.TOKEN_BUDGET,
                estimated_magnitude="~4k tokens",
            ),
        ),
    )
    queue_candidate = derive_queue_placement_candidate(dispatchability)
    window = create_concurrency_window(
        run_id="run-1",
        atomic_unit_ids=(unit.atomic_unit_id, "u2"),
        parallel_candidate_unit_ids=(unit.atomic_unit_id, "u2"),
    )
    return unit, intent, dispatchability, prediction, queue_candidate, window


def _envelope():
    _unit, intent, dispatchability, prediction, queue_candidate, window = (
        _fixture()
    )
    return build_scheduling_projection_envelope(
        run_id="run-1",
        timeline=build_scheduling_timeline_view_model(
            run_id="run-1", intents=(intent,)
        ),
        intent_views=(build_scheduling_intent_view_model(intent),),
        resource_prediction_views=(
            build_resource_prediction_view_model(prediction),
        ),
        dispatchability_views=(
            build_dispatchability_view_model(dispatchability),
        ),
        queue_candidate_views=(
            build_queue_candidate_view_model(queue_candidate),
        ),
        concurrency_window_views=(
            build_concurrency_window_view_model(window),
        ),
    )


def test_every_view_model_preserves_ui_powerlessness() -> None:
    envelope = _envelope()
    views = (
        envelope.timeline,
        *envelope.intent_views,
        *envelope.resource_prediction_views,
        *envelope.dispatchability_views,
        *envelope.queue_candidate_views,
        *envelope.concurrency_window_views,
    )
    for view in views:
        assert view.react_projection_only is True
        assert view.read_only is True
        for forbidden_field in _UI_FALSE_FIELDS:
            assert getattr(view, forbidden_field) is False
            with pytest.raises(AurelFlowValidationError):
                dataclasses.replace(view, **{forbidden_field: True})


def test_view_models_mirror_source_truth() -> None:
    _unit, intent, dispatchability, prediction, queue_candidate, window = (
        _fixture()
    )
    intent_view = build_scheduling_intent_view_model(intent)
    assert intent_view.intent_kind_value == intent.intent_kind.value
    dispatch_view = build_dispatchability_view_model(dispatchability)
    assert dispatch_view.dispatchability_reason_value == "READY_BUT_NO_P4"
    assert dispatch_view.explanation == dispatchability.explanation
    prediction_view = build_resource_prediction_view_model(prediction)
    assert prediction_view.dimension_values == ("TOKEN_BUDGET",)
    queue_view = build_queue_candidate_view_model(queue_candidate)
    assert queue_view.placement_kind_value == "READY_QUEUE_CANDIDATE"
    window_view = build_concurrency_window_view_model(window)
    assert window_view.atomic_unit_ids == window.atomic_unit_ids


def test_envelope_is_deterministic_and_read_only() -> None:
    first = _envelope()
    second = _envelope()
    assert first.envelope_id == second.envelope_id
    assert first.truth_label is FlowTruthLabel.READ_MODEL_ONLY
    for forbidden_field in _UI_FALSE_FIELDS:
        with pytest.raises(AurelFlowValidationError):
            dataclasses.replace(first, **{forbidden_field: True})


def test_envelope_rejects_foreign_run_views() -> None:
    _unit, intent, *_rest = _fixture()
    timeline = build_scheduling_timeline_view_model(
        run_id="run-1", intents=(intent,)
    )
    with pytest.raises(AurelFlowValidationError):
        build_scheduling_projection_envelope(run_id="run-2", timeline=timeline)


def test_react_boundary_pins_python_source_of_truth() -> None:
    boundary = build_scheduling_react_projection_boundary()
    assert boundary.runtime_source_of_truth == "python"
    assert boundary.ui_schedule_button_is_not_dispatch is True
    assert boundary.ui_queue_action_is_not_execution is True
    with pytest.raises(AurelFlowValidationError):
        dataclasses.replace(boundary, runtime_source_of_truth="react")
    with pytest.raises(AurelFlowValidationError):
        dataclasses.replace(boundary, ui_schedule_button_is_not_dispatch=False)
    for forbidden_field in _UI_FALSE_FIELDS:
        with pytest.raises(AurelFlowValidationError):
            dataclasses.replace(boundary, **{forbidden_field: True})


def test_timeline_rejects_foreign_run_intents() -> None:
    _unit, intent, *_rest = _fixture()
    with pytest.raises(AurelFlowValidationError):
        build_scheduling_timeline_view_model(run_id="run-2", intents=(intent,))
