"""P3-FLOW-G recovery budget / loop guard / escalation tests.

Budgets bound self-healing without granting permission, guards block
auto-recovery without executing stops, exhaustion is visible without
auto-authorizing degradation, and escalation is never approval.
"""

from __future__ import annotations

import pytest

from agentic_runtime.aurel_flow import (
    AurelFlowValidationError,
    DegradationMode,
    EscalationReason,
    FlowTruthLabel,
    LoopHealth,
    build_control_loop_collapse_signal,
    build_escalation_read_model,
    build_flow_demo_bundle,
    build_graceful_degradation_frame,
    build_human_escalation_frame,
    build_loop_health_signal,
    build_loop_safety_read_model,
    build_no_progress_guard,
    build_recovery_budget_exhausted_signal,
    build_recovery_budget_read_model,
    build_recovery_budget_state,
    build_retry_storm_guard,
    create_recovery_budget,
)


def _run_id() -> str:
    return build_flow_demo_bundle().run.run_id


def test_recovery_budget_is_deterministic_and_not_permission() -> None:
    run_id = _run_id()
    budget = create_recovery_budget(run_id=run_id)
    again = create_recovery_budget(run_id=run_id)
    assert again.budget_id == budget.budget_id
    assert budget.budget_enforced is False
    assert budget.permission_granted is False
    assert budget.requires_operator_review_above_limit is True


def test_budget_under_limits_is_available_but_still_not_permission() -> None:
    state = build_recovery_budget_state(
        create_recovery_budget(run_id=_run_id(), attempt_limit=3, attempts_used=1)
    )
    assert state.budget_available is True
    assert state.budget_exhausted is False
    assert state.budget_availability_is_not_permission is True
    assert state.permission_granted is False
    assert state.execution_available is False


def test_budget_exhaustion_is_visible_per_dimension() -> None:
    budget = create_recovery_budget(
        run_id=_run_id(),
        attempt_limit=2,
        attempts_used=2,
        depth_limit=1,
        depth_used=1,
    )
    state = build_recovery_budget_state(budget)
    assert state.budget_exhausted is True
    assert state.budget_available is False
    assert state.exhausted_dimensions == ("ATTEMPTS", "DEPTH")
    signal = build_recovery_budget_exhausted_signal(state)
    assert signal.requires_operator_review is True
    assert signal.requires_human_escalation is True
    assert signal.degradation_auto_authorized is False
    assert signal.permission_granted is False
    assert signal.stop_executed is False


def test_exhausted_signal_from_available_budget_fail_closes() -> None:
    state = build_recovery_budget_state(create_recovery_budget(run_id=_run_id()))
    with pytest.raises(AurelFlowValidationError):
        build_recovery_budget_exhausted_signal(state)


def test_negative_budget_counters_fail_close() -> None:
    with pytest.raises(AurelFlowValidationError):
        create_recovery_budget(run_id=_run_id(), attempts_used=-1)


def test_budget_read_model_rejects_foreign_state() -> None:
    budget = create_recovery_budget(run_id=_run_id())
    other_state = build_recovery_budget_state(
        create_recovery_budget(run_id=_run_id(), attempt_limit=9)
    )
    with pytest.raises(AurelFlowValidationError):
        build_recovery_budget_read_model(budget, other_state)
    state = build_recovery_budget_state(budget)
    read_model = build_recovery_budget_read_model(budget, state)
    assert read_model.budget_availability_is_not_permission is True
    assert read_model.permission_granted is False
    assert read_model.truth_label is FlowTruthLabel.READ_MODEL_ONLY


def test_retry_storm_guard_blocks_at_limit_without_executing_stop() -> None:
    guard = build_retry_storm_guard(
        run_id=_run_id(), retry_count=5, same_failure_count=3, retry_storm_limit=3
    )
    assert guard.auto_recovery_blocked is True
    assert guard.requires_human_escalation is True
    assert guard.stop_executed is False
    assert guard.execution_available is False


def test_retry_storm_guard_below_limit_does_not_block() -> None:
    guard = build_retry_storm_guard(
        run_id=_run_id(), retry_count=1, same_failure_count=1, retry_storm_limit=3
    )
    assert guard.auto_recovery_blocked is False
    assert guard.requires_human_escalation is False


def test_storm_guard_at_limit_cannot_be_constructed_unblocked() -> None:
    guard = build_retry_storm_guard(
        run_id=_run_id(), retry_count=4, same_failure_count=4, retry_storm_limit=3
    )
    with pytest.raises(AurelFlowValidationError):
        type(guard)(
            **{
                **{
                    field.name: getattr(guard, field.name)
                    for field in guard.__dataclass_fields__.values()
                },
                "auto_recovery_blocked": False,
            }
        )


def test_no_progress_guard_requires_human_escalation_without_execution() -> None:
    guard = build_no_progress_guard(
        run_id=_run_id(), no_progress_count=2, no_progress_limit=2
    )
    assert guard.auto_recovery_blocked is True
    assert guard.requires_human_escalation is True
    assert guard.stop_executed is False
    assert guard.execution_available is False


def test_loop_health_precedence_collapse_over_storm_over_stall() -> None:
    run_id = _run_id()
    storm = build_retry_storm_guard(
        run_id=run_id, retry_count=4, same_failure_count=4
    )
    stall = build_no_progress_guard(run_id=run_id, no_progress_count=3)
    collapse = build_control_loop_collapse_signal(
        run_id=run_id, detail="loop collapsed"
    )
    assert build_loop_health_signal(
        run_id=run_id,
        retry_storm_guard=storm,
        no_progress_guard=stall,
        collapse_signal=collapse,
    ).loop_health is LoopHealth.COLLAPSED
    assert build_loop_health_signal(
        run_id=run_id, retry_storm_guard=storm, no_progress_guard=stall
    ).loop_health is LoopHealth.STORMING
    assert build_loop_health_signal(
        run_id=run_id, no_progress_guard=stall
    ).loop_health is LoopHealth.STALLED
    healthy = build_retry_storm_guard(
        run_id=run_id, retry_count=0, same_failure_count=0
    )
    assert build_loop_health_signal(
        run_id=run_id, retry_storm_guard=healthy
    ).loop_health is LoopHealth.HEALTHY


def test_loop_safety_read_model_aggregates_guards() -> None:
    run_id = _run_id()
    storm = build_retry_storm_guard(
        run_id=run_id, retry_count=4, same_failure_count=4
    )
    health = build_loop_health_signal(run_id=run_id, retry_storm_guard=storm)
    read_model = build_loop_safety_read_model(
        run_id=run_id, loop_health_signal=health, retry_storm_guard=storm
    )
    assert read_model.any_auto_recovery_blocked is True
    assert read_model.any_requires_human_escalation is True
    assert read_model.guard_executes_stop is False
    assert read_model.loop_health is LoopHealth.STORMING


def test_graceful_degradation_is_visible_and_not_hidden_failure() -> None:
    run_id = _run_id()
    frame = build_graceful_degradation_frame(
        run_id=run_id,
        failure_signal_id="flfsg-test0000000000",
        degradation_mode=DegradationMode.SAFE_HOLD,
        degradation_reason="budget exhausted; holding safely",
    )
    assert frame.degradation_is_visible is True
    assert frame.failure_hidden is False
    assert frame.requires_operator_review is True
    assert frame.approval_granted is False
    with pytest.raises(AurelFlowValidationError):
        type(frame)(
            **{
                **{
                    field.name: getattr(frame, field.name)
                    for field in frame.__dataclass_fields__.values()
                },
                "failure_hidden": True,
            }
        )


def test_human_escalation_is_not_approval() -> None:
    run_id = _run_id()
    frame = build_human_escalation_frame(
        run_id=run_id,
        failure_signal_id="flfsg-test0000000000",
        escalation_reason=EscalationReason.NO_PROGRESS,
        detail="loop stalled; operator must decide",
    )
    assert frame.escalation_is_not_approval is True
    assert frame.approval_granted is False
    assert frame.authority_granted is False
    assert frame.execution_available is False
    read_model = build_escalation_read_model(
        run_id, escalation_frames=(frame,)
    )
    assert read_model.escalation_count == 1
    assert read_model.any_approval_granted is False
    assert read_model.any_failure_hidden is False
    assert read_model.escalation_reasons == ("NO_PROGRESS",)
