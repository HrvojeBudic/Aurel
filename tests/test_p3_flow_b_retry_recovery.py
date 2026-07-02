from __future__ import annotations

from dataclasses import replace

import pytest

from agentic_runtime.aurel_flow import (
    AurelFlowErrorCode,
    AurelFlowValidationError,
    DEFAULT_RETRY_POLICY,
    FailureClassification,
    FailurePropagationRisk,
    RollbackCandidateReason,
    build_failure_recovery_read_model,
    build_recovery_frame,
    build_recovery_proposal,
    build_rollback_candidate,
    calculate_retry_eligibility,
    classify_failure,
    make_retry_decision,
)
from agentic_runtime.aurel_flow.demo import build_demo_workflow_graph


def _assessment(**overrides):
    params = dict(
        target_run_id="wfrun-test",
        target_node_id="fetch",
        graph=build_demo_workflow_graph(),
        validation_failed=True,
    )
    params.update(overrides)
    return classify_failure(**params)


def test_failure_classification_and_propagation_risk_are_visible() -> None:
    assessment = _assessment()

    assert assessment.classification is FailureClassification.VALIDATION_FAILURE
    # In the demo graph every exit node is downstream of "fetch".
    assert assessment.propagation_risk is FailurePropagationRisk.WORKFLOW_BLOCKING
    assert "end" in assessment.downstream_node_ids


def test_classification_precedence_and_risk_variants() -> None:
    graph = build_demo_workflow_graph()
    operator = _assessment(operator_rejected=True)
    policy = _assessment(policy_blocked=True)
    local = classify_failure(
        target_run_id="wfrun-test",
        target_node_id="end",
        graph=graph,
        validation_failed=True,
    )
    no_graph = classify_failure(
        target_run_id="wfrun-test", target_node_id="fetch", validation_failed=True
    )
    systemic = _assessment(systemic_hint=True)

    assert operator.classification is FailureClassification.OPERATOR_REJECTED
    assert policy.classification is FailureClassification.POLICY_BLOCKED
    assert local.propagation_risk is FailurePropagationRisk.LOCAL
    assert no_graph.propagation_risk is FailurePropagationRisk.UNKNOWN
    assert systemic.propagation_risk is FailurePropagationRisk.SYSTEMIC


def test_retry_eligibility_can_be_eligible_without_execution() -> None:
    eligibility = calculate_retry_eligibility(
        DEFAULT_RETRY_POLICY, _assessment(), attempt_count=1
    )

    assert eligibility.eligible is True
    assert eligibility.execution_available is False
    assert eligibility.blocked_by_missing_executor is True
    assert "remains unavailable" in eligibility.reason


def test_retry_eligibility_ineligible_paths_have_explicit_reasons() -> None:
    exhausted = calculate_retry_eligibility(
        DEFAULT_RETRY_POLICY, _assessment(), attempt_count=3
    )
    operator_rejected = calculate_retry_eligibility(
        DEFAULT_RETRY_POLICY, _assessment(operator_rejected=True), attempt_count=0
    )
    uncovered = calculate_retry_eligibility(
        DEFAULT_RETRY_POLICY, _assessment(missing_executor=True), attempt_count=0
    )

    assert exhausted.eligible is False
    assert "max_attempts" in exhausted.reason
    assert operator_rejected.eligible is False
    assert operator_rejected.blocked_by_policy is True
    assert "not retried away" in operator_rejected.reason
    assert uncovered.eligible is False
    assert "not covered" in uncovered.reason


def test_retry_decision_records_eligibility_and_never_executes() -> None:
    eligibility = calculate_retry_eligibility(
        DEFAULT_RETRY_POLICY, _assessment(), attempt_count=0
    )
    decision = make_retry_decision(eligibility)

    assert decision.decided == "MARK_ELIGIBLE"
    assert decision.retry_executed is False
    with pytest.raises(AurelFlowValidationError):
        replace(decision, retry_executed=True)


def test_recovery_proposal_is_declarative_and_not_executable() -> None:
    frame = build_recovery_frame(_assessment())
    proposal = build_recovery_proposal(
        frame, step_descriptions=("revalidate inputs", "request operator review")
    )

    assert proposal.execution_available is False
    assert proposal.requires_executor is True
    assert proposal.requires_operator_review is True
    assert len(proposal.recovery_steps) == 2
    assert proposal.recovery_steps[0].order == 0
    assert all(step.executable is False for step in proposal.recovery_steps)
    assert all(step.requires_executor is True for step in proposal.recovery_steps)
    assert "no execution" in frame.constraints

    with pytest.raises(AurelFlowValidationError) as excinfo:
        replace(proposal, execution_available=True)
    assert excinfo.value.code is AurelFlowErrorCode.FORBIDDEN_BOUNDARY_CLAIM


def test_rollback_candidate_is_marked_not_executed() -> None:
    candidate = build_rollback_candidate(
        target_run_id="wfrun-test",
        target_node_id="fetch",
        target_state_ref="fetch.result.v0",
        candidate_reason=RollbackCandidateReason.FAILED_STATE_TRANSITION,
        reason="fetch failed after internal commit",
    )

    assert candidate.safe_to_prepare is True
    assert candidate.safe_to_execute is False
    assert candidate.execution_available is False
    assert candidate.candidate_reason is RollbackCandidateReason.FAILED_STATE_TRANSITION

    for boundary_field in ("safe_to_execute", "execution_available"):
        with pytest.raises(AurelFlowValidationError):
            replace(candidate, **{boundary_field: True})


def test_failure_recovery_read_model_aggregates_candidates() -> None:
    assessment = _assessment()
    eligibility = calculate_retry_eligibility(DEFAULT_RETRY_POLICY, assessment, attempt_count=1)
    frame = build_recovery_frame(assessment)
    proposal = build_recovery_proposal(frame, step_descriptions=("step one",))
    candidate = build_rollback_candidate(
        target_run_id="wfrun-test",
        target_node_id="fetch",
        target_state_ref="ref",
        candidate_reason=RollbackCandidateReason.DOWNSTREAM_FAILURE,
        reason="downstream failure",
    )
    read_model = build_failure_recovery_read_model(
        "wfrun-test",
        failure_assessments=(assessment,),
        retry_eligibilities=(eligibility,),
        recovery_proposals=(proposal,),
        rollback_candidates=(candidate,),
    )

    assert read_model.retry_executed is False
    assert read_model.recovery_executed is False
    assert read_model.rollback_executed is False
    assert read_model.execution_available is False
    assert "P4 AurelExec" in read_model.execution_unavailable_reason
    assert read_model.read_model_hash


def test_recovery_objects_are_deterministic() -> None:
    first = build_recovery_proposal(
        build_recovery_frame(_assessment()), step_descriptions=("a", "b")
    )
    second = build_recovery_proposal(
        build_recovery_frame(_assessment()), step_descriptions=("a", "b")
    )

    assert first.proposal_id == second.proposal_id
    assert first.recovery_steps == second.recovery_steps
