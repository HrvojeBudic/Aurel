"""P3-FLOW-I no-dispatch boundary tests.

Nothing in the I pack dispatches, enqueues real work, wires runtime.submit,
or lets an autonomy scheduling gate out-allow the H boundaries.
"""

from __future__ import annotations

import dataclasses
import re
from pathlib import Path

import pytest

import agentic_runtime.aurel_flow as aurel_flow
from agentic_runtime.aurel_flow import (
    AurelFlowValidationError,
    AutonomyDecisionClass,
    AutonomyScopeDimension,
    GovernedAutonomyLevel,
    SchedulingAutonomyDecision,
    SchedulingIntentKind,
    SchedulingIntentReason,
    WorkflowAtomicUnitKind,
    build_autonomy_scope_envelope,
    build_no_dispatch_boundary_proof,
    build_scheduling_gate_read_model,
    create_autonomy_scope_limit,
    create_scheduling_action_boundary_check,
    create_scheduling_intent,
    create_scheduling_scope_check,
    create_workflow_atomic_unit,
    evaluate_autonomy_scheduling_gate,
)

_FLOW_PACKAGE_DIR = Path(aurel_flow.__file__).resolve().parent
_I_MODULES = (
    "flow_scheduling_intent.py",
    "flow_dispatchability.py",
    "flow_resource_prediction.py",
    "flow_scheduling_projection.py",
)


def _unit():
    return create_workflow_atomic_unit(
        run_id="run-1",
        unit_kind=WorkflowAtomicUnitKind.SINGLE_NODE,
        node_ids=("n1",),
    )


def _intent(unit):
    return create_scheduling_intent(
        unit=unit,
        intent_kind=SchedulingIntentKind.SCHEDULE_READY_NODE_CANDIDATE,
        intent_reason=SchedulingIntentReason.DEPENDENCIES_SATISFIED,
    )


def _gate(
    *,
    level=GovernedAutonomyLevel.A3_INTERNAL_LOW_RISK_AUTO,
    decision_class=AutonomyDecisionClass.PREPARE_PLAN,
    with_scope: bool = True,
):
    unit = _unit()
    intent = _intent(unit)
    envelope = None
    if with_scope:
        envelope = build_autonomy_scope_envelope(
            run_id="run-1",
            level=level,
            limits=(
                create_autonomy_scope_limit(
                    dimension=AutonomyScopeDimension.RUN_SCOPE,
                    limit_description="this run only",
                ),
            ),
        )
    scope_check = create_scheduling_scope_check(
        unit=unit,
        envelope=envelope,
        required_dimensions=(AutonomyScopeDimension.RUN_SCOPE,),
    )
    boundary_check = create_scheduling_action_boundary_check(
        unit=unit, level=level, decision_class=decision_class
    )
    return evaluate_autonomy_scheduling_gate(
        intent=intent, scope_check=scope_check, boundary_check=boundary_check
    )


def test_i_sources_never_reference_runtime_submit() -> None:
    forbidden_patterns = (
        r"\.submit\(",
        r"runtime_submit\s*=\s*True",
        r"AgenticRuntime\(",
        r"ApprovalGate\(",
        r"enqueue\(",
        r"put_nowait\(",
        r"\bqueue\.Queue\b",
        r"\bmultiprocessing\b",
        r"\bthreading\b",
        r"\bconcurrent\.futures\b",
    )
    for filename in _I_MODULES:
        source = (_FLOW_PACKAGE_DIR / filename).read_text(encoding="utf-8")
        for pattern in forbidden_patterns:
            assert not re.search(pattern, source), (
                f"{filename} matches forbidden pattern {pattern!r}"
            )


def test_no_dispatch_proof_is_all_false_and_fail_closed() -> None:
    proof = build_no_dispatch_boundary_proof()
    for boundary_field in (
        "is_p5_trace_proof",
        "dispatched",
        "dispatch_available",
        "queued",
        "actual_queue_inserted",
        "worker_assigned",
        "runtime_submit_wired",
        "runtime_submit_called",
        "ui_dispatch_allowed",
    ):
        assert getattr(proof, boundary_field) is False
        with pytest.raises(AurelFlowValidationError):
            dataclasses.replace(proof, **{boundary_field: True})


def test_allowed_gate_is_still_candidate_only() -> None:
    gate = _gate()
    assert gate.decision is SchedulingAutonomyDecision.ALLOW_SCHEDULING_CANDIDATE
    assert gate.dispatch_available is False
    assert gate.execution_available is False
    assert gate.authority_granted is False
    assert gate.permission_granted is False
    assert gate.requires_p4_execution is True


def test_gate_cannot_out_allow_h_forbidden_classes() -> None:
    for decision_class in (
        AutonomyDecisionClass.TOOL_EXECUTION,
        AutonomyDecisionClass.NETWORK_CALL,
        AutonomyDecisionClass.MEMORY_WRITE,
        AutonomyDecisionClass.EXTERNAL_SIDE_EFFECT,
    ):
        gate = _gate(decision_class=decision_class)
        assert gate.decision is SchedulingAutonomyDecision.BLOCK_SCHEDULING
        assert gate.forbidden_in_p3 is True
        assert gate.requires_operator_review is True


def test_gate_holds_outside_scope_and_fails_closed_without_envelope() -> None:
    gate = _gate(with_scope=False)
    assert gate.inside_scope is False
    assert gate.decision is SchedulingAutonomyDecision.HOLD_SCHEDULING
    assert gate.requires_operator_review is True


def test_low_tier_requires_operator_review() -> None:
    gate = _gate(
        level=GovernedAutonomyLevel.A0_OBSERVE_ONLY,
        decision_class=AutonomyDecisionClass.PREPARE_PLAN,
    )
    assert gate.decision is SchedulingAutonomyDecision.REQUIRE_OPERATOR_REVIEW


def test_authority_request_routes_to_p9() -> None:
    gate = _gate(decision_class=AutonomyDecisionClass.REQUEST_AUTHORITY)
    assert gate.decision is SchedulingAutonomyDecision.REQUIRE_P9_AUTHORITY
    assert gate.requires_p9_authority is True


def test_gate_never_grants_authority_structurally() -> None:
    gate = _gate()
    for forbidden_field in (
        "authority_granted",
        "permission_granted",
        "execution_available",
        "dispatch_available",
    ):
        with pytest.raises(AurelFlowValidationError):
            dataclasses.replace(gate, **{forbidden_field: True})
    with pytest.raises(AurelFlowValidationError):
        dataclasses.replace(gate, gate_is_not_authority=False)


def test_scheduling_decision_vocabulary_has_no_dispatch_verb() -> None:
    values = {decision.value for decision in SchedulingAutonomyDecision}
    for forbidden in ("DISPATCH", "EXECUTE", "APPROVE", "AUTHORIZE", "ENQUEUE"):
        assert forbidden not in values


def test_gate_read_model_is_deterministic_and_fail_closed() -> None:
    gates = (_gate(), _gate(decision_class=AutonomyDecisionClass.TOOL_EXECUTION))
    read_model = build_scheduling_gate_read_model(run_id="run-1", gates=gates)
    assert read_model.gate_count == 2
    assert read_model.blocked_count == 1
    assert read_model.authority_granted is False
    assert read_model.dispatch_available is False
    with pytest.raises(AurelFlowValidationError):
        build_scheduling_gate_read_model(run_id="run-2", gates=gates)
