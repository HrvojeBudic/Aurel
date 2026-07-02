"""P3-FLOW-D operator review boundary tests.

Operator review is not approval. Candidates name possible next actions;
they never mutate runtime state, execute, authorize, or roll back.
"""

from __future__ import annotations

from dataclasses import replace

import pytest

from agentic_runtime.aurel_flow import (
    AurelFlowValidationError,
    FlowTruthLabel,
    OperatorReviewDecisionKind,
    build_flow_demo_bundle,
    build_operator_review_read_model,
    create_continue_candidate,
    create_operator_review_decision,
    create_operator_review_frame,
    create_reject_candidate,
    create_rollback_review_candidate,
    create_stop_candidate,
)


def _frame():
    return create_operator_review_frame(
        target_run_id="run-1",
        target_node_id="plan",
        proposal_id="flprop-x",
        review_reason="proposal awaits operator review",
    )


def test_decision_kind_vocabulary_is_closed_world_review_only():
    values = {kind.value for kind in OperatorReviewDecisionKind}
    assert "CONTINUE_CANDIDATE" in values
    assert "ESCALATE_TO_HUMAN" in values
    for forbidden in ("APPROVE", "EXECUTE", "DISPATCH", "GRANT", "AUTHORIZE"):
        assert not any(forbidden == value for value in values)


def test_review_frame_cannot_authorize():
    frame = _frame()
    assert frame.authority_granted is False
    assert frame.execution_permission_granted is False
    assert frame.execution_available is False
    assert frame.mutates_runtime_state is False
    assert frame.review_is_approval is False
    for boundary_field in (
        "authority_granted",
        "execution_permission_granted",
        "review_is_approval",
    ):
        with pytest.raises(AurelFlowValidationError):
            replace(frame, **{boundary_field: True})


def test_review_decision_is_intent_not_authority():
    frame = _frame()
    decision = create_operator_review_decision(
        frame=frame,
        operator_id="op-1",
        decision_kind=OperatorReviewDecisionKind.HOLD,
        reason="hold pending evidence",
    )
    assert decision.frame_id == frame.frame_id
    assert decision.authority_granted is False
    assert decision.decision_is_authority is False
    with pytest.raises(AurelFlowValidationError):
        replace(decision, decision_is_authority=True)


def test_review_decision_rejects_unavailable_kind():
    frame = create_operator_review_frame(
        target_run_id="run-1",
        target_node_id="plan",
        review_reason="limited frame",
        available_decision_kinds=(OperatorReviewDecisionKind.HOLD,),
    )
    with pytest.raises(AurelFlowValidationError):
        create_operator_review_decision(
            frame=frame,
            operator_id="op-1",
            decision_kind=OperatorReviewDecisionKind.CONTINUE_CANDIDATE,
            reason="not offered",
        )


def test_candidates_are_fail_closed_and_deterministic():
    frame = _frame()
    cont = create_continue_candidate(frame=frame, reason="ready to continue later")
    stop = create_stop_candidate(frame=frame, reason="stop is an option")
    rej = create_reject_candidate(frame=frame, reason="path may be rejected")
    for candidate in (cont, stop, rej):
        assert candidate.authority_granted is False
        assert candidate.execution_permission_granted is False
        assert candidate.execution_available is False
        assert candidate.mutates_runtime_state is False
        with pytest.raises(AurelFlowValidationError):
            replace(candidate, mutates_runtime_state=True)
    assert cont.candidate_id == create_continue_candidate(
        frame=frame, reason="ready to continue later"
    ).candidate_id
    assert cont.decision_kind is OperatorReviewDecisionKind.CONTINUE_CANDIDATE
    assert stop.decision_kind is OperatorReviewDecisionKind.STOP_CANDIDATE
    assert rej.decision_kind is OperatorReviewDecisionKind.REJECT_CANDIDATE


def test_rollback_review_candidate_does_not_rollback():
    candidate = create_rollback_review_candidate(
        frame=_frame(),
        reason="rollback is reviewable, not executable",
        rollback_candidate_ref="flrb-x",
    )
    assert candidate.rollback_executed is False
    assert candidate.safe_to_execute is False
    assert candidate.execution_available is False
    for boundary_field in ("rollback_executed", "safe_to_execute"):
        with pytest.raises(AurelFlowValidationError):
            replace(candidate, **{boundary_field: True})


def test_candidates_do_not_mutate_demo_run_state():
    bundle = build_flow_demo_bundle()
    run = bundle.run
    step_before = run.state.step
    lifecycle_before = run.state.lifecycle_status
    history_before = len(run.history)
    frame = create_operator_review_frame(
        target_run_id=run.run_id,
        target_node_id="plan",
        review_reason="review against a real demo run",
    )
    create_continue_candidate(frame=frame, reason="continue later")
    create_stop_candidate(frame=frame, reason="stop later")
    create_reject_candidate(frame=frame, reason="reject later")
    create_rollback_review_candidate(
        frame=frame, reason="review rollback", rollback_candidate_ref="flrb-x"
    )
    assert run.state.step == step_before
    assert run.state.lifecycle_status is lifecycle_before
    assert len(run.history) == history_before


def test_operator_review_read_model_deterministic_and_read_only():
    frame = _frame()
    decision = create_operator_review_decision(
        frame=frame,
        operator_id="op-1",
        decision_kind=OperatorReviewDecisionKind.REQUEST_VERIFICATION,
        reason="verification requested",
    )
    cont = create_continue_candidate(frame=frame, reason="continue later")

    def build():
        return build_operator_review_read_model(
            frames=(frame,), decisions=(decision,), continue_candidates=(cont,)
        )

    read_model_a = build()
    read_model_b = build()
    assert read_model_a.read_model_hash == read_model_b.read_model_hash
    assert read_model_a == read_model_b
    assert read_model_a.frame_count == 1
    assert read_model_a.decision_kind_counts == {"REQUEST_VERIFICATION": 1}
    assert read_model_a.truth_label is FlowTruthLabel.READ_MODEL_ONLY
    assert read_model_a.operator_review_is_not_approval is True
    with pytest.raises(AurelFlowValidationError):
        replace(read_model_a, operator_review_is_not_approval=False)
    with pytest.raises(AurelFlowValidationError):
        replace(read_model_a, authority_granted_any=True)
