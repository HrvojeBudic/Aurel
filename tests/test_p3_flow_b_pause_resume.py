from __future__ import annotations

from dataclasses import replace

import pytest

from agentic_runtime.aurel_flow import (
    AurelFlowErrorCode,
    AurelFlowValidationError,
    OperatorDecisionKind,
    WorkflowLifecycleStatus,
    WorkflowNodeState,
    WorkflowPauseReason,
    build_workflow_pause_read_model,
    create_operator_decision_signal,
    create_responsibility_transfer_frame,
    create_workflow_run,
    lifecycle_transition,
    pause_workflow_run,
    reject_workflow_path,
    resume_workflow_run,
    stop_workflow_run,
    transition_workflow_run,
)
from agentic_runtime.aurel_flow.demo import build_demo_workflow_graph


def _running_run():
    run = create_workflow_run(build_demo_workflow_graph(), run_key="pause-test")
    run = transition_workflow_run(
        run,
        lifecycle_transition(WorkflowLifecycleStatus.CREATED, WorkflowLifecycleStatus.READY),
    )
    return transition_workflow_run(
        run,
        lifecycle_transition(WorkflowLifecycleStatus.READY, WorkflowLifecycleStatus.RUNNING),
    )


def _signal(kind: OperatorDecisionKind, run, **overrides):
    params = dict(
        operator_id="operator-1",
        decision_kind=kind,
        target_run_id=run.run_id,
    )
    params.update(overrides)
    return create_operator_decision_signal(**params)


def test_workflow_pauses_with_explicit_reason() -> None:
    result = pause_workflow_run(
        _running_run(),
        pause_reason=WorkflowPauseReason.WAITING_APPROVAL,
        target_node_id="gate",
        waiting_for="operator approval",
    )

    assert result.run.state.lifecycle_status is WorkflowLifecycleStatus.PAUSED
    assert result.previous_lifecycle is WorkflowLifecycleStatus.RUNNING
    assert result.pause_state.pause_reason is WorkflowPauseReason.WAITING_APPROVAL
    assert result.pause_state.waiting_for == "operator approval"
    assert result.pause_state.resumable is True
    assert result.node_executed is False
    assert result.execution_available is False


@pytest.mark.parametrize(
    "reason",
    [
        WorkflowPauseReason.WAITING_OPERATOR,
        WorkflowPauseReason.WAITING_APPROVAL,
        WorkflowPauseReason.WAITING_REASONING,
        WorkflowPauseReason.WAITING_VERIFIER,
    ],
)
def test_pause_reasons_are_representable(reason: WorkflowPauseReason) -> None:
    result = pause_workflow_run(_running_run(), pause_reason=reason)

    assert result.pause_state.pause_reason is reason


def test_pause_fails_closed_when_lifecycle_cannot_pause() -> None:
    created_run = create_workflow_run(build_demo_workflow_graph(), run_key="pause-created")

    with pytest.raises(AurelFlowValidationError) as excinfo:
        pause_workflow_run(created_run, pause_reason=WorkflowPauseReason.WAITING_OPERATOR)

    assert excinfo.value.code is AurelFlowErrorCode.INVALID_LIFECYCLE_TRANSITION


def test_operator_signal_kinds_and_quality_flags_round_trip() -> None:
    run = _running_run()
    for kind in (
        OperatorDecisionKind.RESUME,
        OperatorDecisionKind.STOP,
        OperatorDecisionKind.REJECT,
        OperatorDecisionKind.HOLD,
    ):
        signal = _signal(
            kind,
            run,
            counterargument_present=True,
            minority_objection_present=True,
            mediation_required=True,
            decision_pressure_warning=True,
        )
        assert signal.decision_kind is kind
        assert signal.counterargument_present is True
        assert signal.minority_objection_present is True
        assert signal.mediation_required is True
        assert signal.decision_pressure_warning is True
        assert signal.authority_granted is False
        assert signal.execution_permission_granted is False


def test_operator_signal_cannot_grant_authority_or_execution_permission() -> None:
    signal = _signal(OperatorDecisionKind.RESUME, _running_run())

    for boundary_field in ("authority_granted", "execution_permission_granted"):
        with pytest.raises(AurelFlowValidationError) as excinfo:
            replace(signal, **{boundary_field: True})
        assert excinfo.value.code is AurelFlowErrorCode.FORBIDDEN_BOUNDARY_CLAIM


def test_resume_changes_internal_lifecycle_only() -> None:
    paused = pause_workflow_run(
        _running_run(), pause_reason=WorkflowPauseReason.WAITING_APPROVAL
    )
    signal = _signal(OperatorDecisionKind.RESUME, paused.run)
    nodes_before = dict(paused.run.state.node_states)

    result = resume_workflow_run(paused.run, paused.pause_state, signal)

    assert result.resumed_internal is True
    assert result.lifecycle_after is WorkflowLifecycleStatus.RUNNING
    assert result.node_executed is False
    assert result.execution_available is False
    assert dict(result.run.state.node_states) == nodes_before
    assert result.request.decision_signal_id == signal.decision_id
    assert result.request.pause_id == paused.pause_state.pause_id


def test_resume_requires_resume_signal_and_matching_run() -> None:
    paused = pause_workflow_run(
        _running_run(), pause_reason=WorkflowPauseReason.WAITING_OPERATOR
    )
    stop_signal = _signal(OperatorDecisionKind.STOP, paused.run)

    with pytest.raises(AurelFlowValidationError) as excinfo:
        resume_workflow_run(paused.run, paused.pause_state, stop_signal)

    assert excinfo.value.code is AurelFlowErrorCode.SIGNAL_KIND_MISMATCH


def test_non_resumable_pause_fails_closed() -> None:
    paused = pause_workflow_run(
        _running_run(),
        pause_reason=WorkflowPauseReason.BLOCKED,
        resumable=False,
    )
    signal = _signal(OperatorDecisionKind.RESUME, paused.run)

    with pytest.raises(AurelFlowValidationError) as excinfo:
        resume_workflow_run(paused.run, paused.pause_state, signal)

    assert excinfo.value.code is AurelFlowErrorCode.NOT_RESUMABLE


def test_stop_moves_lifecycle_to_cancelled_without_execution() -> None:
    run = _running_run()
    result = stop_workflow_run(run, _signal(OperatorDecisionKind.STOP, run))

    assert result.stopped_internal is True
    assert result.lifecycle_after is WorkflowLifecycleStatus.CANCELLED
    assert result.node_executed is False
    assert result.execution_available is False


def test_reject_marks_node_blocked_without_execution() -> None:
    run = _running_run()
    result = reject_workflow_path(run, "gate", _signal(OperatorDecisionKind.REJECT, run))

    assert result.rejected_internal is True
    assert result.node_state_after is WorkflowNodeState.BLOCKED
    assert result.node_executed is False
    assert run.state.node_states["gate"] is WorkflowNodeState.NOT_STARTED


def test_responsibility_transfer_never_transfers_authority() -> None:
    run = _running_run()
    frame = create_responsibility_transfer_frame(
        from_actor="actor-1",
        to_actor="operator-1",
        target_run_id=run.run_id,
        reason="operator should continue",
    )

    assert frame.authority_transferred is False
    assert frame.execution_permission_granted is False
    assert frame.handoff_state == "RECORDED"

    for boundary_field in ("authority_transferred", "execution_permission_granted"):
        with pytest.raises(AurelFlowValidationError) as excinfo:
            replace(frame, **{boundary_field: True})
        assert excinfo.value.code is AurelFlowErrorCode.FORBIDDEN_BOUNDARY_CLAIM


def test_pause_read_model_exposes_state_and_authority_boundaries() -> None:
    run = _running_run()
    paused = pause_workflow_run(run, pause_reason=WorkflowPauseReason.WAITING_APPROVAL)
    signal = _signal(OperatorDecisionKind.HOLD, run)
    frame = create_responsibility_transfer_frame(
        from_actor="a", to_actor="b", target_run_id=run.run_id, reason="handoff"
    )
    read_model = build_workflow_pause_read_model(
        run.run_id,
        pause_states=(paused.pause_state,),
        operator_signals=(signal,),
        responsibility_frames=(frame,),
    )

    assert read_model.paused_count == 1
    assert read_model.execution_available is False
    assert read_model.authority_available is False
    assert "P9 Custos" in read_model.authority_unavailable_reason
    assert "P4 AurelExec" in read_model.execution_unavailable_reason
    assert read_model.read_model_hash
