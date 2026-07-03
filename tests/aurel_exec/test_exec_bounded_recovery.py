"""P4-EXEC-E bounded recovery tests — a plan is not recovery execution."""

from __future__ import annotations

import dataclasses

import pytest

from agentic_runtime.aurel_exec import (
    AurelExecValidationError,
    BoundedRecoveryActionKind,
    FailureClass,
    FailureSeverity,
    RECOVERY_RECOMMENDATIONS,
    build_no_automatic_retry_proof,
    build_no_rollback_execution_proof,
    build_no_self_healing_proof,
    classify_execution_failure,
    classify_pre_submit_block,
    create_bounded_recovery_plan,
    normalize_runtime_result,
)
from tests.aurel_exec._bridge_helpers import RecordingFakeRuntime, _FakeCard


class _Cmd:
    id = "cmd_x"


def _tool_error_classification():
    outcome = normalize_runtime_result(
        RecordingFakeRuntime(succeed=False).submit(_Cmd(), _FakeCard()),
        attempt_id="exec-attempt-a",
        exec_job_id="exec-job-a",
        session_id="exec-session-a",
        tool_name="read_file",
        command_id="cmd_x",
    )
    return classify_execution_failure(outcome, None)


def test_bounded_recovery_plan_does_not_execute_recovery():
    plan = create_bounded_recovery_plan(_tool_error_classification(), max_attempts=2)
    assert plan.recommended_action is BoundedRecoveryActionKind.RETRY_SAME_INPUT
    assert plan.recovery_executed is False
    assert plan.self_healing_available is False
    for boundary_field in (
        "recovery_executed",
        "automatic_retry_available",
        "rollback_execution_available",
        "self_healing_available",
    ):
        with pytest.raises(AurelExecValidationError):
            dataclasses.replace(plan, **{boundary_field: True})
    for verb in ("execute", "run", "retry", "recover", "rollback", "submit"):
        assert not hasattr(plan, verb)


def test_automatic_retry_remains_unavailable():
    plan = create_bounded_recovery_plan(_tool_error_classification(), max_attempts=2)
    # every retry-shaped recommendation requires operator approval
    assert plan.requires_operator_approval is True
    with pytest.raises(AurelExecValidationError):
        dataclasses.replace(plan, requires_operator_approval=False)
    proof = build_no_automatic_retry_proof()
    assert proof.automatic_retry_available is False
    assert proof.bridge_resubmit_performed is False
    with pytest.raises(AurelExecValidationError):
        dataclasses.replace(proof, automatic_retry_available=True)


def test_rollback_execution_remains_unavailable():
    # OUTPUT_CONTRACT_FAILED recommends ROLLBACK_REF_ONLY, never execution
    action, _, requires_p9, _ = RECOVERY_RECOMMENDATIONS[
        FailureClass.OUTPUT_CONTRACT_FAILED
    ]
    assert action is BoundedRecoveryActionKind.ROLLBACK_REF_ONLY
    assert requires_p9 is True
    proof = build_no_rollback_execution_proof()  # C-era proof still holds
    assert proof.rollback_executed is False
    assert proof.rollback_execution_available is False
    healing = build_no_self_healing_proof()
    assert healing.recovery_execution_available is False
    assert healing.self_healing_available is False
    with pytest.raises(AurelExecValidationError):
        dataclasses.replace(healing, self_healing_available=True)


def test_retry_budget_exhaustion_downgrades_deterministically():
    classification = _tool_error_classification()
    with_budget = create_bounded_recovery_plan(
        classification, max_attempts=2, attempts_used=1
    )
    assert with_budget.recommended_action is BoundedRecoveryActionKind.RETRY_SAME_INPUT
    assert with_budget.remaining_attempts == 1
    exhausted = create_bounded_recovery_plan(
        classification, max_attempts=1, attempts_used=1
    )
    assert (
        exhausted.recommended_action
        is BoundedRecoveryActionKind.REQUEST_OPERATOR_REVIEW
    )
    assert exhausted.remaining_attempts == 0
    assert "no retry storm" in exhausted.reason
    # a retry-shaped plan with zero attempts is unconstructible
    with pytest.raises(AurelExecValidationError):
        dataclasses.replace(
            with_budget, remaining_attempts=0
        )


def test_recommendation_table_is_total_and_deterministic():
    assert set(RECOVERY_RECOMMENDATIONS) == set(FailureClass)
    classification = _tool_error_classification()
    first = create_bounded_recovery_plan(classification, max_attempts=2)
    second = create_bounded_recovery_plan(classification, max_attempts=2)
    assert first == second
    assert first.plan_hash == second.plan_hash
    # NONE failure -> no recovery
    ok_classification = classify_pre_submit_block("LEASE_EXPIRED", exec_job_id="j")
    none_classification = dataclasses.replace(
        ok_classification,
        failure_class=FailureClass.NONE,
        severity=FailureSeverity.INFO,
        retryable=False,
        recoverable=False,
        operator_action_required=False,
        reason="no failure",
    )
    none_plan = create_bounded_recovery_plan(none_classification)
    assert none_plan.recommended_action is BoundedRecoveryActionKind.NONE
    assert none_plan.allowed is False


def test_high_risk_recovery_requires_p9_authority():
    for failure_class in (
        FailureClass.POLICY_BLOCKED,
        FailureClass.OUTPUT_CONTRACT_FAILED,
        FailureClass.RESOURCE_EXHAUSTED,
        FailureClass.UNKNOWN_ERROR,
    ):
        _, _, requires_p9, _ = RECOVERY_RECOMMENDATIONS[failure_class]
        assert requires_p9 is True, failure_class
