"""P3-FLOW-D proposal / permission / execution / proof boundary tests.

Proposal is not permission. Permission request is not permission. Permission
is not execution. Execution is not proof. Proof expectation is not proof.
"""

from __future__ import annotations

from dataclasses import replace

import pytest

from agentic_runtime.aurel_flow import (
    AurelFlowValidationError,
    BudgetUnavailableReason,
    ControlPlaneSignalKind,
    FlowRequestedActionKind,
    FlowTruthLabel,
    RecoveryBudgetDimension,
    build_boundary_truth_read_model,
    build_control_plane_data_plane_boundary,
    build_flow_to_submit_boundary,
    build_recovery_budget_boundary,
    build_recovery_policy_boundary,
    build_reliability_control_plane_boundary,
    build_submit_compatibility_read_model,
    create_control_plane_signal,
    create_diagnostic_expectation,
    create_evidence_requirement,
    create_execution_proposal_envelope,
    create_execution_request_envelope,
    create_permission_request_envelope,
    create_proof_expectation_envelope,
    create_recovery_budget_requirement,
    create_validation_node_expectation,
    create_verifier_node_expectation,
)


def _proposal():
    return create_execution_proposal_envelope(
        run_id="run-1",
        node_id="plan",
        source_scheduler_decision_id="dec-1",
        source_runtime_event_id="evt-1",
        requested_action_kind=FlowRequestedActionKind.TOOL_CALL,
        requested_tool_or_executor_ref="tool://fs.read",
        proposal_reason="node ready; execution must be proposed, never taken",
    )


def _permission_request(proposal):
    return create_permission_request_envelope(
        proposal=proposal,
        required_permission_scope="fs.read",
        required_authority_scope="custos.tool.read",
        required_policy_family="TOOL_POLICY",
    )


def _execution_request(proposal, permission_request):
    return create_execution_request_envelope(
        proposal=proposal,
        permission_request=permission_request,
        requested_executor_ref="aurel_exec://future",
        required_sandbox_profile="SANDBOX_REQUIRED",
        required_budget_profile="BUDGET_REQUIRED",
    )


def test_proposal_envelope_is_not_permission_or_execution():
    proposal = _proposal()
    assert proposal.execution_available is False
    assert proposal.permission_granted is False
    assert proposal.authority_granted is False
    assert proposal.proposal_is_permission is False
    assert proposal.truth_label is FlowTruthLabel.CONTRACT_ONLY
    for boundary_field in (
        "execution_available",
        "permission_granted",
        "authority_granted",
        "proposal_is_permission",
    ):
        with pytest.raises(AurelFlowValidationError):
            replace(proposal, **{boundary_field: True})


def test_permission_request_cannot_grant_permission():
    request = _permission_request(_proposal())
    assert request.permission_granted is False
    assert request.authority_granted is False
    assert request.permission_request_is_permission is False
    assert request.future_p9_required is True
    assert "P9 Custos" in request.unavailable_reason
    with pytest.raises(AurelFlowValidationError):
        replace(request, permission_granted=True)
    with pytest.raises(AurelFlowValidationError):
        replace(request, future_p9_required=False)


def test_execution_request_cannot_dispatch():
    proposal = _proposal()
    request = _execution_request(proposal, _permission_request(proposal))
    assert request.execution_available is False
    assert request.execution_dispatched is False
    assert request.permission_granted is False
    assert request.future_p4_required is True
    with pytest.raises(AurelFlowValidationError):
        replace(request, execution_dispatched=True)
    with pytest.raises(AurelFlowValidationError):
        replace(request, future_p4_required=False)


def test_execution_request_rejects_foreign_permission_request():
    proposal_a = _proposal()
    proposal_b = create_execution_proposal_envelope(
        run_id="run-2",
        node_id="act",
        source_scheduler_decision_id="dec-2",
        source_runtime_event_id="evt-2",
        requested_action_kind=FlowRequestedActionKind.COMMAND,
        requested_tool_or_executor_ref="cmd://echo",
        proposal_reason="other proposal",
    )
    with pytest.raises(AurelFlowValidationError):
        _execution_request(proposal_a, _permission_request(proposal_b))


def test_flow_to_submit_boundary_is_never_crossed():
    boundary = build_flow_to_submit_boundary()
    assert boundary.runtime_submit_wired is False
    assert boundary.submit_called is False
    assert boundary.execution_available is False
    assert boundary.future_p4_required is True
    for boundary_field in ("runtime_submit_wired", "submit_called"):
        with pytest.raises(AurelFlowValidationError):
            replace(boundary, **{boundary_field: True})


def test_submit_compatibility_read_model_states_not_wired():
    read_model = build_submit_compatibility_read_model()
    assert read_model.runtime_submit_wired is False
    assert read_model.execution_available is False
    assert read_model.future_p4_required is True
    assert "execution_proposal_envelope.v1" in (
        read_model.compatible_envelope_contract_versions
    )
    assert read_model.truth_label is FlowTruthLabel.READ_MODEL_ONLY


def test_boundary_truth_read_model_laws_and_fail_closed():
    proposal = _proposal()
    permission_request = _permission_request(proposal)
    execution_request = _execution_request(proposal, permission_request)
    proof = create_proof_expectation_envelope(
        proposal_id=proposal.proposal_id,
        execution_request_id=execution_request.execution_request_id,
        target_run_id="run-1",
        target_node_id="plan",
        required_verifier="aurel_trace://future",
        required_trace_expectation="trace event chain with output hash",
        evidence_requirements=(
            create_evidence_requirement(
                target_run_id="run-1",
                target_node_id="plan",
                evidence_kind="TOOL_OUTPUT_HASH",
                description="output hash must be traced",
            ),
        ),
    )
    truth = build_boundary_truth_read_model(
        proposals=(proposal,),
        permission_requests=(permission_request,),
        execution_requests=(execution_request,),
        proof_expectations=(proof,),
    )
    assert truth.proposal_count == 1
    assert truth.proof_expectation_count == 1
    assert "proposal is not permission" in truth.laws
    with pytest.raises(AurelFlowValidationError):
        replace(truth, permission_granted_any=True)
    with pytest.raises(AurelFlowValidationError):
        replace(truth, proposal_is_not_permission=False)


def test_control_plane_data_plane_boundary_planes():
    boundary = build_control_plane_data_plane_boundary()
    assert "AurelFlow" in boundary.control_plane
    assert "AurelExec" in boundary.data_plane
    assert "AurelTrace" in boundary.proof_plane
    assert "Custos" in boundary.authority_plane
    assert boundary.control_plane_executes is False
    assert boundary.data_plane_active is False
    with pytest.raises(AurelFlowValidationError):
        replace(boundary, control_plane_executes=True)


def test_reliability_control_plane_boundary_seed():
    boundary = build_reliability_control_plane_boundary()
    assert boundary.control_plane_executes is False
    assert boundary.self_healing_loop_implemented is False
    assert boundary.recovery_policy.can_propose_repair is True
    assert boundary.recovery_policy.executes_repair is False
    assert boundary.recovery_execution.recovery_execution_available is False
    assert boundary.data_plane_ref.data_plane_active is False
    assert ControlPlaneSignalKind.DIAGNOSE_REQUIRED in boundary.allowed_signal_kinds
    with pytest.raises(AurelFlowValidationError):
        replace(boundary, self_healing_loop_implemented=True)


def test_recovery_policy_boundary_cannot_execute_repair():
    policy = build_recovery_policy_boundary()
    assert policy.can_require_diagnosis is True
    assert policy.can_require_verification is True
    assert policy.can_propose_repair is True
    assert policy.executes_repair is False
    assert policy.proves_success is False
    with pytest.raises(AurelFlowValidationError):
        replace(policy, executes_repair=True)
    with pytest.raises(AurelFlowValidationError):
        replace(policy, can_propose_repair=False)


def test_control_plane_signal_and_expectations_are_not_actions():
    signal = create_control_plane_signal(
        signal_kind=ControlPlaneSignalKind.DETECT,
        target_run_id="run-1",
        target_node_id="plan",
        reason="node failed twice",
    )
    assert signal.executes_repair is False
    assert signal.proves_success is False
    diag = create_diagnostic_expectation(
        target_run_id="run-1", target_node_id="plan", diagnosis_scope="node inputs"
    )
    assert diag.diagnosis_required is True
    assert diag.diagnosis_performed is False
    verify = create_verifier_node_expectation(
        target_run_id="run-1", target_node_id="plan", verifier_kind="SEMANTIC"
    )
    assert verify.verification_required is True
    assert verify.verification_performed is False
    validate = create_validation_node_expectation(
        target_run_id="run-1", target_node_id="plan", validation_kind="SCHEMA"
    )
    assert validate.validation_required is True
    assert validate.validation_performed is False
    with pytest.raises(AurelFlowValidationError):
        replace(verify, verification_performed=True)
    with pytest.raises(AurelFlowValidationError):
        replace(diag, diagnosis_required=False)


def test_recovery_budget_boundary_requires_but_never_enforces():
    boundary = build_recovery_budget_boundary(
        auto_continue_requirements=(
            create_recovery_budget_requirement(
                dimension=RecoveryBudgetDimension.ATTEMPTS,
                limit_value=3,
                applies_to="AUTO_CONTINUE",
            ),
        ),
        repair_requirements=(
            create_recovery_budget_requirement(
                dimension=RecoveryBudgetDimension.DEPTH,
                limit_value=2,
                applies_to="REPAIR",
            ),
        ),
    )
    assert boundary.budget_enforced is False
    assert boundary.budget_available is False
    assert boundary.unavailable_reason_kind is (
        BudgetUnavailableReason.NO_ENFORCEMENT_RUNTIME
    )
    assert boundary.auto_continue_gate.auto_continue_without_budget_allowed is False
    assert boundary.repair_gate.repair_without_budget_allowed is False
    requirement = boundary.auto_continue_gate.requirements[0]
    assert requirement.budget_enforced is False
    assert requirement.budget_is_permission is False
    with pytest.raises(AurelFlowValidationError):
        replace(boundary, budget_enforced=True)
    with pytest.raises(AurelFlowValidationError):
        replace(requirement, budget_is_permission=True)


def test_envelope_ids_are_deterministic():
    proposal_a = _proposal()
    proposal_b = _proposal()
    assert proposal_a.proposal_id == proposal_b.proposal_id
    assert proposal_a == proposal_b
    request_a = _permission_request(proposal_a)
    request_b = _permission_request(proposal_b)
    assert request_a.permission_request_id == request_b.permission_request_id
