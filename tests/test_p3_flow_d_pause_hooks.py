"""P3-FLOW-D pause hook boundary tests.

Reasoning pause is runtime state, not hidden chain-of-thought. Verifier
pause expects verification but does not verify. Operator pause requests
review but does not authorize. Evidence pause expects evidence but cannot
produce proof.
"""

from __future__ import annotations

from dataclasses import fields, replace

import pytest

from agentic_runtime.aurel_flow import (
    AurelFlowValidationError,
    PauseHookKind,
    PauseHookReason,
    create_evidence_pause_hook,
    create_operator_pause_hook,
    create_reasoning_pause_hook,
    create_runtime_pause_hook,
    create_verifier_pause_hook,
)


def test_pause_hook_reason_vocabulary():
    values = {reason.value for reason in PauseHookReason}
    assert {
        "WAITING_REASONING",
        "WAITING_VERIFIER",
        "WAITING_OPERATOR",
        "WAITING_MEDIATION",
        "WAITING_COUNTERARGUMENT",
        "WAITING_EVIDENCE",
        "WAITING_PERMISSION",
        "WAITING_EXECUTOR",
        "WAITING_PROOF",
        "UNAVAILABLE",
        "ERROR",
    } == values


def test_runtime_pause_hook_is_waiting_state_only():
    hook = create_runtime_pause_hook(
        hook_kind=PauseHookKind.RUNTIME,
        reason=PauseHookReason.WAITING_PERMISSION,
        target_run_id="run-1",
        target_node_id="plan",
        waiting_for="permission decision from future P9",
        safe_state_summary="run paused before proposed action",
    )
    assert hook.authority_granted is False
    assert hook.execution_available is False
    assert hook.verification_performed is False
    assert hook.evidence_produced is False
    assert hook.stores_hidden_chain_of_thought is False
    for boundary_field in (
        "authority_granted",
        "execution_available",
        "stores_hidden_chain_of_thought",
    ):
        with pytest.raises(AurelFlowValidationError):
            replace(hook, **{boundary_field: True})


def test_reasoning_pause_hook_stores_no_hidden_chain_of_thought():
    hook = create_reasoning_pause_hook(
        target_run_id="run-1",
        target_node_id="plan",
        safe_reasoning_category="PLAN_SELECTION",
        safe_state_summary="choosing between two candidate plans",
    )
    assert hook.stores_hidden_chain_of_thought is False
    assert hook.hook.stores_hidden_chain_of_thought is False
    assert hook.safe_reasoning_category == "PLAN_SELECTION"
    with pytest.raises(AurelFlowValidationError):
        replace(hook, stores_hidden_chain_of_thought=True)
    # structural boundary: no field can carry raw chain-of-thought
    field_names = {f.name for f in fields(hook)} | {f.name for f in fields(hook.hook)}
    for forbidden in ("chain_of_thought", "cot_content", "raw_reasoning", "thoughts"):
        assert forbidden not in field_names


def test_reasoning_pause_hook_requires_reasoning_kind():
    runtime_hook = create_runtime_pause_hook(
        hook_kind=PauseHookKind.OPERATOR,
        reason=PauseHookReason.WAITING_OPERATOR,
        target_run_id="run-1",
        target_node_id="plan",
        waiting_for="operator",
        safe_state_summary="wrong kind",
    )
    from agentic_runtime.aurel_flow import ReasoningPauseHook

    with pytest.raises(AurelFlowValidationError):
        ReasoningPauseHook(hook=runtime_hook, safe_reasoning_category="X")


def test_verifier_pause_hook_does_not_verify():
    hook = create_verifier_pause_hook(
        target_run_id="run-1",
        target_node_id="plan",
        expected_verifier="semantic-verifier",
        verification_expectation="claims must be supported by evidence",
    )
    assert hook.verification_performed is False
    assert hook.proof_available is False
    assert hook.trace_verified is False
    assert hook.future_p5_required is True
    assert hook.hook.reason is PauseHookReason.WAITING_VERIFIER
    with pytest.raises(AurelFlowValidationError):
        replace(hook, verification_performed=True)
    with pytest.raises(AurelFlowValidationError):
        replace(hook, future_p5_required=False)


def test_operator_pause_hook_does_not_authorize():
    hook = create_operator_pause_hook(
        target_run_id="run-1",
        target_node_id="plan",
        review_frame_ref="florf-x",
        requested_review="continue or stop this run",
    )
    assert hook.authority_granted is False
    assert hook.approval_granted is False
    assert hook.execution_available is False
    assert hook.hook.reason is PauseHookReason.WAITING_OPERATOR
    for boundary_field in ("authority_granted", "approval_granted"):
        with pytest.raises(AurelFlowValidationError):
            replace(hook, **{boundary_field: True})


def test_evidence_pause_hook_marks_missing_evidence_as_failure_candidate():
    hook = create_evidence_pause_hook(
        target_run_id="run-1",
        target_node_id="plan",
        evidence_requirement_ref="flevr-x",
        safe_state_summary="output blocked until evidence arrives",
    )
    assert hook.missing_evidence_is_failure_candidate is True
    assert hook.evidence_produced is False
    assert hook.proof_available is False
    assert hook.hook.reason is PauseHookReason.WAITING_EVIDENCE
    with pytest.raises(AurelFlowValidationError):
        replace(hook, evidence_produced=True)
    with pytest.raises(AurelFlowValidationError):
        replace(hook, missing_evidence_is_failure_candidate=False)


def test_pause_hooks_are_deterministic():
    def build():
        return create_reasoning_pause_hook(
            target_run_id="run-1",
            target_node_id="plan",
            safe_reasoning_category="PLAN_SELECTION",
            safe_state_summary="choosing between two candidate plans",
        )

    hook_a = build()
    hook_b = build()
    assert hook_a.hook.hook_id == hook_b.hook.hook_id
    assert hook_a == hook_b
