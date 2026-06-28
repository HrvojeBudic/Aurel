"""Focused tests for P1.8-B action boundary contracts."""

import json
import sys
from dataclasses import fields
from pathlib import Path

import pytest

sys.path.insert(0, "src")

from agentic_runtime.delegation import (  # noqa: E402
    DELEGATION_ACTION_BOUNDARY_PACK_CHECKPOINT_IDS,
    DELEGATION_ACTION_BOUNDARY_PACK_TASK_ID,
    DELEGATION_ACTOR_BOUNDARY_PACK_TASK_ID,
    DelegationActionBoundaryKind,
    DelegationActionBoundaryPackResult,
    DelegationActionBoundaryReadModel,
    DelegationActionBoundarySideEffects,
    DelegationActionBoundaryStatus,
    DelegationActionState,
    DelegationActionTransitionVerdict,
    DelegationActionTruthLabel,
    DelegationActionUnavailableReason,
    DelegationExecutionProofBoundary,
    DelegationOperatorDecisionState,
    DelegationPermissionBoundary,
    DelegationProposalBoundary,
    OperatorDelegationDecisionBinding,
    assert_execution_is_not_proof,
    assert_operator_decision_is_not_auto_execution,
    assert_permission_is_not_execution,
    assert_proposal_is_not_permission,
    build_default_delegation_action_boundary_read_model,
    build_delegation_action_transition_check,
    build_delegation_execution_proof_boundary,
    build_delegation_permission_boundary,
    build_delegation_proposal_boundary,
    build_operator_delegation_decision_binding,
    build_p1_8_a_actor_boundary_pack_result,
    build_p1_8_b_action_boundary_pack_result,
    hash_delegation_action_boundary_pack_result,
    hash_delegation_action_boundary_read_model,
    serialize_delegation_action_boundary_pack_result,
    serialize_delegation_action_boundary_read_model,
)
from agentic_runtime.delegation.actor_boundary import AurelStateActorBoundary  # noqa: E402
from agentic_runtime.delegation.foundation import (  # noqa: E402
    DelegationSourceLabel,
    DelegationValidationError,
)


def assert_all_side_effects_false(
    side_effects: DelegationActionBoundarySideEffects,
) -> None:
    for field in fields(side_effects):
        assert getattr(side_effects, field.name) is False


def test_module_and_package_exports_available():
    assert DELEGATION_ACTION_BOUNDARY_PACK_TASK_ID == "P1.8-B"
    assert DELEGATION_ACTION_BOUNDARY_PACK_CHECKPOINT_IDS == (
        "P1.8.23",
        "P1.8.24",
        "P1.8.25",
        "P1.8.26",
    )
    assert DelegationProposalBoundary is not None
    assert DelegationPermissionBoundary is not None
    assert DelegationExecutionProofBoundary is not None
    assert OperatorDelegationDecisionBinding is not None
    assert DelegationActionBoundaryReadModel is not None
    assert DelegationActionBoundaryPackResult is not None
    assert DELEGATION_ACTOR_BOUNDARY_PACK_TASK_ID == "P1.8-A"
    assert build_p1_8_a_actor_boundary_pack_result().task_id == "P1.8-A"


def test_p1_8_a_dependency_files_exist_and_contracts_are_not_duplicated():
    assert Path("agent/reports/P1_8_A_ACTOR_BOUNDARY_PACK.md").is_file()
    assert Path("src/agentic_runtime/delegation/actor_boundary.py").is_file()
    assert Path("tests/delegation/test_actor_boundary.py").is_file()
    assert AurelStateActorBoundary is not DelegationProposalBoundary


@pytest.mark.parametrize(
    ("builder", "kwargs"),
    [
        (build_delegation_proposal_boundary, {"action_state": "maybe_proposed"}),
        (build_delegation_permission_boundary, {"boundary_kind": "soft_boundary"}),
        (
            build_operator_delegation_decision_binding,
            {"operator_decision_state": "rubber_stamped"},
        ),
        (
            build_delegation_action_transition_check,
            {
                "source_state": DelegationActionState.PROPOSED,
                "target_state": DelegationActionState.PROPOSED,
                "boundary_kind": DelegationActionBoundaryKind.PROPOSAL_NOT_PERMISSION,
                "verdict": "looks_fine",
                "reason": "invalid verdict should fail",
            },
        ),
        (
            build_delegation_execution_proof_boundary,
            {"unavailable_reasons": ("eventually",)},
        ),
    ],
)
def test_closed_world_rejects_unknown_enum_values(builder, kwargs):
    with pytest.raises(DelegationValidationError):
        builder(**kwargs)


def test_enum_domains_include_expected_values():
    assert DelegationActionBoundaryKind.PROPOSAL_NOT_PERMISSION.value == (
        "proposal_not_permission"
    )
    assert DelegationActionState.PROPOSED.value == "proposed"
    assert DelegationOperatorDecisionState.PENDING_REVIEW.value == "pending_review"
    assert DelegationActionTransitionVerdict.REJECTED_SEMANTIC_COLLAPSE.value == (
        "rejected_semantic_collapse"
    )
    assert DelegationActionTruthLabel.PROPOSAL_ONLY.value == "PROPOSAL_ONLY"
    assert DelegationActionUnavailableReason.UNAVAILABLE_RUNTIME_ENFORCEMENT.value == (
        "unavailable_runtime_enforcement"
    )


def test_deterministic_hashes_and_stable_json_serialization():
    result_a = build_p1_8_b_action_boundary_pack_result()
    result_b = build_p1_8_b_action_boundary_pack_result()
    assert hash_delegation_action_boundary_pack_result(result_a) == (
        hash_delegation_action_boundary_pack_result(result_b)
    )
    assert serialize_delegation_action_boundary_pack_result(result_a) == (
        serialize_delegation_action_boundary_pack_result(result_b)
    )

    payload = json.loads(serialize_delegation_action_boundary_pack_result(result_a))
    assert payload["task_id"] == "P1.8-B"
    assert payload["checkpoint_ids"] == list(DELEGATION_ACTION_BOUNDARY_PACK_CHECKPOINT_IDS)
    assert len(payload["result_hash"]) == 64

    read_model_json = serialize_delegation_action_boundary_read_model(
        result_a.read_model
    )
    read_model_payload = json.loads(read_model_json)
    assert read_model_payload["checkpoint_count"] == 4
    assert hash_delegation_action_boundary_read_model(result_a.read_model) == (
        read_model_payload["read_model_hash"]
    )


def test_p1_8_23_proposal_is_not_permission():
    proposal = build_delegation_proposal_boundary()
    assert proposal.checkpoint_id == "P1.8.23"
    assert proposal.boundary_kind == (
        DelegationActionBoundaryKind.PROPOSAL_NOT_PERMISSION
    )
    assert proposal.action_state == DelegationActionState.PROPOSED
    assert proposal.truth_label == DelegationActionTruthLabel.PROPOSAL_ONLY
    assert proposal.permission_ref is None
    assert proposal.execution_ref is None
    assert proposal.proof_ref is None
    assert proposal.side_effects.permission_granted is False
    assert proposal.side_effects.execution_started is False
    assert proposal.side_effects.memory_written is False
    assert proposal.side_effects.tool_invoked is False
    assert proposal.side_effects.workflow_mutated is False
    assert proposal.side_effects.proof_verified is False
    assert_all_side_effects_false(proposal.side_effects)

    check = assert_proposal_is_not_permission(proposal)
    assert check.verdict == DelegationActionTransitionVerdict.ALLOWED_AS_CONTRACT_STATE
    with pytest.raises(DelegationValidationError):
        assert_proposal_is_not_permission(
            proposal,
            target_state=DelegationActionState.PERMITTED,
        )
    with pytest.raises(DelegationValidationError):
        build_delegation_proposal_boundary(permission_ref="permission:live")
    with pytest.raises(DelegationValidationError):
        build_delegation_proposal_boundary(execution_ref="execution:live")
    with pytest.raises(DelegationValidationError):
        build_delegation_proposal_boundary(proof_ref="proof:live")


def test_p1_8_24_permission_is_not_execution():
    permission = build_delegation_permission_boundary(proposal_ref="proposal:123")
    assert permission.checkpoint_id == "P1.8.24"
    assert permission.boundary_kind == (
        DelegationActionBoundaryKind.PERMISSION_NOT_EXECUTION
    )
    assert permission.action_state == DelegationActionState.PERMITTED
    assert permission.proposal_ref == "proposal:123"
    assert permission.truth_label == DelegationActionTruthLabel.PERMISSION_ONLY
    assert permission.execution_ref is None
    assert permission.proof_ref is None
    assert permission.side_effects.execution_started is False
    assert permission.side_effects.tool_invoked is False
    assert permission.side_effects.workflow_mutated is False
    assert permission.side_effects.runtime_mutated is False
    assert permission.side_effects.proof_verified is False
    assert_all_side_effects_false(permission.side_effects)

    check = assert_permission_is_not_execution(permission)
    assert check.verdict == DelegationActionTransitionVerdict.ALLOWED_AS_CONTRACT_STATE
    with pytest.raises(DelegationValidationError):
        assert_permission_is_not_execution(
            permission,
            target_state=DelegationActionState.EXECUTED,
        )
    with pytest.raises(DelegationValidationError):
        build_delegation_permission_boundary(execution_ref="execution:live")
    with pytest.raises(DelegationValidationError):
        build_delegation_permission_boundary(proof_ref="proof:live")


def test_p1_8_25_execution_is_not_proof():
    boundary = build_delegation_execution_proof_boundary()
    assert boundary.checkpoint_id == "P1.8.25"
    assert boundary.boundary_kind == DelegationActionBoundaryKind.EXECUTION_NOT_PROOF
    assert boundary.action_state == DelegationActionState.PROOF_PENDING
    assert boundary.truth_label == DelegationActionTruthLabel.PROOF_PENDING
    assert boundary.proof_claimed is False
    assert boundary.trace_verified is False
    assert boundary.evidence_ref is None
    assert boundary.trace_ref is None
    assert boundary.side_effects.proof_verified is False
    assert (
        DelegationActionUnavailableReason.UNAVAILABLE_TRACE_VERIFICATION
        in boundary.unavailable_reasons
    )
    assert_all_side_effects_false(boundary.side_effects)

    check = assert_execution_is_not_proof(boundary)
    assert check.verdict == DelegationActionTransitionVerdict.REQUIRES_EVIDENCE
    with pytest.raises(DelegationValidationError):
        assert_execution_is_not_proof(
            boundary,
            target_truth_label=DelegationActionTruthLabel.TRACE_VERIFIED,
        )
    with pytest.raises(DelegationValidationError):
        build_delegation_execution_proof_boundary(proof_claimed=True)
    with pytest.raises(DelegationValidationError):
        build_delegation_execution_proof_boundary(trace_verified=True)
    with pytest.raises(DelegationValidationError):
        build_delegation_execution_proof_boundary(
            truth_label=DelegationActionTruthLabel.TRACE_VERIFIED
        )


def test_p1_8_26_operator_decision_binding_is_explicit_and_non_executing():
    pending = build_operator_delegation_decision_binding()
    assert pending.checkpoint_id == "P1.8.26"
    assert pending.operator_decision_state == (
        DelegationOperatorDecisionState.PENDING_REVIEW
    )
    assert pending.action_state == DelegationActionState.OPERATOR_REVIEW_PENDING
    assert pending.final_claim_allowed is False
    assert pending.continuation_allowed is False
    assert pending.auto_execute is False
    assert pending.truth_label == (
        DelegationActionTruthLabel.OPERATOR_DECISION_REQUIRED
    )
    assert_all_side_effects_false(pending.side_effects)

    approved = build_operator_delegation_decision_binding(
        operator_decision_state=DelegationOperatorDecisionState.APPROVED
    )
    assert approved.final_claim_allowed is True
    assert approved.continuation_allowed is True
    assert approved.side_effects.execution_started is False
    assert approved.side_effects.runtime_mutated is False

    rejected = build_operator_delegation_decision_binding(
        operator_decision_state=DelegationOperatorDecisionState.REJECTED
    )
    stopped = build_operator_delegation_decision_binding(
        operator_decision_state=DelegationOperatorDecisionState.STOPPED
    )
    revision = build_operator_delegation_decision_binding(
        operator_decision_state=DelegationOperatorDecisionState.REVISION_REQUESTED
    )
    assert rejected.continuation_allowed is False
    assert stopped.continuation_allowed is False
    assert revision.final_claim_allowed is False
    assert revision.action_state == DelegationActionState.REVISION_REQUESTED

    check = assert_operator_decision_is_not_auto_execution(approved)
    assert check.verdict == DelegationActionTransitionVerdict.ALLOWED_AS_CONTRACT_STATE
    with pytest.raises(DelegationValidationError):
        assert_operator_decision_is_not_auto_execution(approved, auto_execute=True)
    with pytest.raises(DelegationValidationError):
        build_operator_delegation_decision_binding(auto_execute=True)
    with pytest.raises(DelegationValidationError):
        build_operator_delegation_decision_binding(
            operator_decision_state="manager_said_yes"
        )


def test_side_effect_proof_all_forbidden_booleans_false():
    result = build_p1_8_b_action_boundary_pack_result()
    contracts = (
        result.proposal_boundary,
        result.permission_boundary,
        result.execution_proof_boundary,
        result.operator_decision_binding,
        result.read_model,
        result,
    )
    for contract in contracts:
        assert_all_side_effects_false(contract.side_effects)


def test_read_model_includes_all_four_checkpoints_with_unavailable_reasons():
    read_model = build_default_delegation_action_boundary_read_model()
    assert read_model.task_id == "P1.8-B"
    assert read_model.checkpoint_count == 4
    assert tuple(row.checkpoint_id for row in read_model.checkpoint_reads) == (
        DELEGATION_ACTION_BOUNDARY_PACK_CHECKPOINT_IDS
    )
    assert read_model.truth_label == DelegationActionTruthLabel.DEV_FIXTURE
    assert read_model.source_label == DelegationSourceLabel.DEV_FIXTURE
    assert_all_side_effects_false(read_model.side_effects)

    forbidden = {
        DelegationActionTruthLabel.LIVE,
        DelegationActionTruthLabel.TRACE_VERIFIED,
    }
    labels = {read_model.truth_label}
    for row in read_model.checkpoint_reads:
        assert row.status == DelegationActionBoundaryStatus.CONTRACT_READY
        assert row.evidence_ref
        assert len(row.contract_hash) == 64
        assert row.unavailable_reasons
        labels.add(row.truth_label)
    assert not labels.intersection(forbidden)

    details = read_model.unavailable_reason_details
    cli_reason = DelegationActionUnavailableReason.CLI_SHELL_TUI_BINDING_P1_8_28
    runtime_reason = (
        DelegationActionUnavailableReason.UNAVAILABLE_RUNTIME_ENFORCEMENT
    )
    trace_reason = DelegationActionUnavailableReason.UNAVAILABLE_TRACE_VERIFICATION
    assert "P1.8.28 Delegation Shell/CLI/TUI Binding" in details[cli_reason.value]
    assert "contract-only" in details[runtime_reason.value]
    assert "runtime/policy layers" in details[runtime_reason.value]
    assert "does not perform Ledger/global trace verification" in details[
        trace_reason.value
    ]


def test_pack_result_truth_labels_do_not_overclaim():
    result = build_p1_8_b_action_boundary_pack_result()
    assert result.status == DelegationActionBoundaryStatus.CONTRACT_READY
    assert result.truth_label == DelegationActionTruthLabel.DEV_FIXTURE
    assert result.source_label == DelegationSourceLabel.DEV_FIXTURE
    assert_all_side_effects_false(result.side_effects)

    labels = {
        result.proposal_boundary.truth_label,
        result.permission_boundary.truth_label,
        result.execution_proof_boundary.truth_label,
        result.operator_decision_binding.truth_label,
        result.read_model.truth_label,
        result.truth_label,
    }
    assert DelegationActionTruthLabel.LIVE not in labels
    assert DelegationActionTruthLabel.TRACE_VERIFIED not in labels

    details = result.unavailable_reason_details
    for reason in result.unavailable_reasons:
        assert reason.value in details
        assert details[reason.value]

    assert json.loads(serialize_delegation_action_boundary_pack_result(result))[
        "proposal_boundary"
    ]["truth_label"] == "PROPOSAL_ONLY"
