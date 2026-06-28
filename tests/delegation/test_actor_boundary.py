"""Focused tests for P1.8-A actor boundary contracts."""

import json
import sys
from dataclasses import fields

import pytest

sys.path.insert(0, "src")

from agentic_runtime.delegation import (
    DELEGATION_ACTOR_BOUNDARY_PACK_CHECKPOINT_IDS,
    DELEGATION_ACTOR_BOUNDARY_PACK_TASK_ID,
    AgentWorkerBoundary,
    AurelStateActorBoundary,
    BusinessEnvironmentActorBoundary,
    CROAuthorityStateBridge,
    DelegationActorBoundaryActorKind,
    DelegationActorBoundaryKind,
    DelegationActorBoundaryPackResult,
    DelegationActorBoundaryReadModel,
    DelegationActorBoundarySideEffects,
    DelegationActorBoundaryStatus,
    DelegationActorStateRole,
    DelegationAuthorityScope,
    DelegationBoundaryTruthLabel,
    DelegationBoundaryUnavailableReason,
    DelegationProposalOriginKind,
    SystemRootBoundaryReference,
    TriggerProposalBoundary,
    build_agent_worker_boundary,
    build_aurel_state_actor_boundary,
    build_business_environment_actor_boundary,
    build_cro_authority_state_bridge,
    build_default_delegation_actor_boundary_read_model,
    build_p1_8_a_actor_boundary_pack_result,
    build_system_root_boundary_reference,
    build_trigger_proposal_boundary,
    hash_delegation_actor_boundary_pack_result,
    hash_delegation_actor_boundary_read_model,
    serialize_delegation_actor_boundary_pack_result,
    serialize_delegation_actor_boundary_read_model,
)
from agentic_runtime.delegation.foundation import (
    DelegationSourceLabel,
    DelegationValidationError,
)


def assert_all_side_effects_false(side_effects: DelegationActorBoundarySideEffects) -> None:
    for field in fields(side_effects):
        assert getattr(side_effects, field.name) is False


def test_module_and_package_exports_available():
    assert DELEGATION_ACTOR_BOUNDARY_PACK_TASK_ID == "P1.8-A"
    assert DELEGATION_ACTOR_BOUNDARY_PACK_CHECKPOINT_IDS == (
        "P1.8.17",
        "P1.8.18",
        "P1.8.19",
        "P1.8.20",
        "P1.8.21",
        "P1.8.22",
    )
    assert AurelStateActorBoundary is not None
    assert AgentWorkerBoundary is not None
    assert CROAuthorityStateBridge is not None
    assert SystemRootBoundaryReference is not None
    assert BusinessEnvironmentActorBoundary is not None
    assert TriggerProposalBoundary is not None
    assert DelegationActorBoundaryReadModel is not None
    assert DelegationActorBoundaryPackResult is not None


@pytest.mark.parametrize(
    ("builder", "kwargs"),
    [
        (build_aurel_state_actor_boundary, {"actor_kind": "ghost_actor"}),
        (build_agent_worker_boundary, {"boundary_kind": "soft_boundary"}),
        (build_trigger_proposal_boundary, {"proposal_origin_kinds": ("timer",)}),
        (build_business_environment_actor_boundary, {"state_role": "ownerish"}),
        (build_cro_authority_state_bridge, {"truth_label": "TRUST_ME"}),
        (
            build_system_root_boundary_reference,
            {"unavailable_reasons": ("maybe_later",)},
        ),
    ],
)
def test_closed_world_rejects_unknown_enum_values(builder, kwargs):
    with pytest.raises(DelegationValidationError):
        builder(**kwargs)


def test_enum_domains_include_expected_values():
    assert DelegationActorBoundaryActorKind.AUREL_STATE_ACTOR.value == (
        "aurel_state_actor"
    )
    assert DelegationActorBoundaryKind.TRIGGER_PROPOSAL_BOUNDARY.value == (
        "trigger_proposal_boundary"
    )
    assert DelegationAuthorityScope.PROPOSAL_ONLY.value == "proposal_only"
    assert DelegationActorStateRole.WORKER_ONLY.value == "worker_only"
    assert DelegationProposalOriginKind.MEMORY_TRIGGER.value == "memory_trigger"
    assert DelegationBoundaryTruthLabel.CONTRACT_ONLY.value == "CONTRACT_ONLY"
    assert DelegationBoundaryUnavailableReason.UNAVAILABLE_RUNTIME_ENFORCEMENT.value == (
        "unavailable_runtime_enforcement"
    )


def test_deterministic_hashes_and_stable_json_serialization():
    result_a = build_p1_8_a_actor_boundary_pack_result()
    result_b = build_p1_8_a_actor_boundary_pack_result()
    assert hash_delegation_actor_boundary_pack_result(result_a) == (
        hash_delegation_actor_boundary_pack_result(result_b)
    )
    assert serialize_delegation_actor_boundary_pack_result(result_a) == (
        serialize_delegation_actor_boundary_pack_result(result_b)
    )

    payload = json.loads(serialize_delegation_actor_boundary_pack_result(result_a))
    assert payload["task_id"] == "P1.8-A"
    assert payload["checkpoint_ids"] == list(DELEGATION_ACTOR_BOUNDARY_PACK_CHECKPOINT_IDS)
    assert len(payload["result_hash"]) == 64

    read_model_json = serialize_delegation_actor_boundary_read_model(
        result_a.read_model
    )
    read_model_payload = json.loads(read_model_json)
    assert read_model_payload["checkpoint_count"] == 6
    assert hash_delegation_actor_boundary_read_model(result_a.read_model) == (
        read_model_payload["read_model_hash"]
    )


def test_p1_8_17_aurel_state_actor_can_own_state_agent_worker_cannot():
    boundary = build_aurel_state_actor_boundary()
    assert boundary.checkpoint_id == "P1.8.17"
    assert boundary.actor_kind == DelegationActorBoundaryActorKind.AUREL_STATE_ACTOR
    assert boundary.boundary_kind == (
        DelegationActorBoundaryKind.AUREL_STATE_ACTOR_BOUNDARY
    )
    assert boundary.authority_scope == DelegationAuthorityScope.STATE_OWNERSHIP
    assert boundary.state_role == DelegationActorStateRole.STATE_OWNER
    assert boundary.can_own_state is True
    assert boundary.agent_worker_can_own_state is False
    assert boundary.truth_label == DelegationBoundaryTruthLabel.CONTRACT_ONLY
    assert boundary.source_label == DelegationSourceLabel.DEV_FIXTURE
    assert_all_side_effects_false(boundary.side_effects)


def test_p1_8_18_agent_worker_is_worker_only_without_system_entry():
    boundary = build_agent_worker_boundary()
    assert boundary.checkpoint_id == "P1.8.18"
    assert boundary.actor_kind == DelegationActorBoundaryActorKind.AGENT_WORKER
    assert boundary.worker_only is True
    assert boundary.can_self_authorize is False
    assert boundary.can_enter_system is False
    assert boundary.authority_scope == DelegationAuthorityScope.WORKER_ONLY
    assert boundary.state_role == DelegationActorStateRole.WORKER_ONLY
    assert_all_side_effects_false(boundary.side_effects)


def test_p1_8_19_cro_bridge_depends_on_operator_custos_runtime_system():
    bridge = build_cro_authority_state_bridge()
    assert bridge.checkpoint_id == "P1.8.19"
    assert bridge.actor_kind == DelegationActorBoundaryActorKind.CRO
    assert bridge.boundary_kind == (
        DelegationActorBoundaryKind.CRO_AUTHORITY_STATE_BRIDGE
    )
    assert bridge.requires_operator is True
    assert bridge.requires_custos is True
    assert bridge.requires_runtime is True
    assert bridge.requires_system_root is True
    assert bridge.can_self_authorize is False
    assert bridge.can_activate_evolution is False
    assert_all_side_effects_false(bridge.side_effects)


def test_p1_8_20_system_root_is_operator_only():
    boundary = build_system_root_boundary_reference()
    assert boundary.checkpoint_id == "P1.8.20"
    assert boundary.actor_kind == DelegationActorBoundaryActorKind.SYSTEM_ROOT
    assert boundary.authority_scope == (
        DelegationAuthorityScope.SYSTEM_ROOT_OPERATOR_ONLY
    )
    assert boundary.operator_only is True
    assert boundary.agent_entry_allowed is False
    assert boundary.tool_entry_allowed is False
    assert boundary.workflow_entry_allowed is False
    assert (
        DelegationBoundaryUnavailableReason.SYSTEM_ENTRY_UNAVAILABLE
        in boundary.unavailable_reasons
    )
    assert_all_side_effects_false(boundary.side_effects)


def test_p1_8_21_business_environment_bounded_state_only():
    boundary = build_business_environment_actor_boundary()
    assert boundary.checkpoint_id == "P1.8.21"
    assert boundary.actor_kind == (
        DelegationActorBoundaryActorKind.BUSINESS_ENVIRONMENT
    )
    assert boundary.can_hold_bounded_state_refs is True
    assert boundary.can_grant_permission is False
    assert boundary.can_execute_high_impact_actions is False
    assert boundary.authority_scope == (
        DelegationAuthorityScope.BUSINESS_ENVIRONMENT_BOUNDED_STATE
    )
    assert_all_side_effects_false(boundary.side_effects)


def test_p1_8_22_tool_workflow_memory_triggers_are_proposal_only():
    boundary = build_trigger_proposal_boundary()
    assert boundary.checkpoint_id == "P1.8.22"
    assert boundary.boundary_kind == (
        DelegationActorBoundaryKind.TRIGGER_PROPOSAL_BOUNDARY
    )
    assert set(boundary.proposal_origin_kinds) == {
        DelegationProposalOriginKind.TOOL,
        DelegationProposalOriginKind.WORKFLOW,
        DelegationProposalOriginKind.MEMORY_TRIGGER,
    }
    assert boundary.proposal_only is True
    assert boundary.permission_granted is False
    assert boundary.execution_started is False
    assert boundary.memory_written is False
    assert_all_side_effects_false(boundary.side_effects)


def test_read_model_includes_all_six_checkpoints_without_live_or_trace_verified():
    read_model = build_default_delegation_actor_boundary_read_model()
    assert read_model.task_id == "P1.8-A"
    assert read_model.checkpoint_count == 6
    assert tuple(row.checkpoint_id for row in read_model.checkpoint_reads) == (
        DELEGATION_ACTOR_BOUNDARY_PACK_CHECKPOINT_IDS
    )
    assert read_model.truth_label == DelegationBoundaryTruthLabel.DEV_FIXTURE
    assert read_model.source_label == DelegationSourceLabel.DEV_FIXTURE
    assert_all_side_effects_false(read_model.side_effects)

    forbidden = {
        DelegationBoundaryTruthLabel.LIVE,
        DelegationBoundaryTruthLabel.TRACE_VERIFIED,
    }
    labels = {read_model.truth_label}
    for row in read_model.checkpoint_reads:
        assert row.status == DelegationActorBoundaryStatus.CONTRACT_ONLY
        assert row.evidence_ref
        assert len(row.contract_hash) == 64
        assert row.unavailable_reasons
        labels.add(row.truth_label)
    assert not labels.intersection(forbidden)


def test_pack_result_unavailable_surfaces_have_reasons():
    result = build_p1_8_a_actor_boundary_pack_result()
    assert result.status == DelegationActorBoundaryStatus.CONTRACT_ONLY
    assert result.truth_label == DelegationBoundaryTruthLabel.DEV_FIXTURE
    assert result.source_label == DelegationSourceLabel.DEV_FIXTURE
    assert_all_side_effects_false(result.side_effects)

    details = result.unavailable_reason_details
    for reason in result.unavailable_reasons:
        assert reason.value in details
        assert details[reason.value]

    cli_reason = DelegationBoundaryUnavailableReason.CLI_SHELL_TUI_BINDING_P1_8_28
    runtime_reason = (
        DelegationBoundaryUnavailableReason.UNAVAILABLE_RUNTIME_ENFORCEMENT
    )
    assert "P1.8.28 Delegation Shell/CLI/TUI Binding" in details[cli_reason.value]
    assert "contract-only" in details[runtime_reason.value]
    assert "runtime/policy layers" in details[runtime_reason.value]

    all_contract_labels = {
        result.aurel_state_actor_boundary.truth_label,
        result.agent_worker_boundary.truth_label,
        result.cro_authority_state_bridge.truth_label,
        result.system_root_boundary_reference.truth_label,
        result.business_environment_actor_boundary.truth_label,
        result.trigger_proposal_boundary.truth_label,
        result.truth_label,
        result.read_model.truth_label,
    }
    assert DelegationBoundaryTruthLabel.LIVE not in all_contract_labels
    assert DelegationBoundaryTruthLabel.TRACE_VERIFIED not in all_contract_labels
