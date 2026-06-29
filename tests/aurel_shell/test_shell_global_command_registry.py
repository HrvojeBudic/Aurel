"""Tests for P2.4-A global command registry foundation."""

from __future__ import annotations

import json

import pytest

from agentic_runtime.aurel_shell.contracts import AurelShellValidationError
from agentic_runtime.aurel_shell.global_command_registry import (
    COMMAND_EXECUTION_UNAVAILABLE_REASON,
    P2_4_A_DEPENDENCY_PACK,
    P2_4_A_NEXT_PACK,
    P2_4_A_PACK_CHECKPOINT_IDS,
    P2_4_A_PACK_ID,
    P2_4_A_REPORT_PATH,
    P2_4_A_SECTION_ID,
    CommandPaletteSectionGateStatus,
    GlobalCommandAvailability,
    GlobalCommandAvailabilityStatus,
    GlobalCommandIdentity,
    GlobalCommandKind,
    GlobalCommandParameterKind,
    GlobalCommandRegistry,
    GlobalCommandRegistryStatus,
    GlobalCommandScopeKind,
    P24AGlobalCommandFoundationResult,
    assert_availability_is_not_permission,
    assert_command_is_not_execution,
    assert_input_contract_is_not_invocation,
    assert_omni_evidence_is_ignored_by_operator_instruction,
    assert_p2_4_a_depends_on_p2_3_d,
    assert_p2_4_a_does_not_start_future_work,
    assert_p2_4_a_side_effects_all_false,
    assert_registry_is_not_router,
    assert_surface_target_is_not_route_execution,
    build_command_palette_section_gate,
    build_global_command_availability,
    build_global_command_id,
    build_global_command_identity,
    build_global_command_input_contract,
    build_global_command_parameter,
    build_global_command_registry,
    build_global_command_scope,
    build_global_command_surface_target,
    build_p2_4_a_global_command_foundation_result,
    build_p2_4_a_side_effect_proof,
    render_global_command_registry_summary,
    serialize_p2_4_a_result,
)
from agentic_runtime.aurel_shell.surface_registry import CANONICAL_SURFACE_ORDER
from agentic_runtime.aurel_shell.workspace_window_section_projection import (
    P2_3_D_PACK_ID,
    build_p2_3_d_workspace_window_section_result,
)


def test_module_imports_p2_4_a() -> None:
    import agentic_runtime.aurel_shell.global_command_registry  # noqa: F401


def test_gate_dependency_and_omni_policy() -> None:
    p2_3_d = build_p2_3_d_workspace_window_section_result()
    gate = build_command_palette_section_gate()
    result = build_p2_4_a_global_command_foundation_result()

    assert P2_4_A_PACK_ID == "P2.4-A"
    assert P2_4_A_SECTION_ID == "P2.4"
    assert P2_4_A_PACK_CHECKPOINT_IDS == (
        "P2.4.0",
        "P2.4.1",
        "P2.4.2",
        "P2.4.3",
        "P2.4.4",
        "P2.4.5",
    )
    assert P2_4_A_DEPENDENCY_PACK == P2_3_D_PACK_ID
    assert p2_3_d.section_seal.sealed_for_contract_scope is True
    assert gate.dependency_contract_seal_ref.startswith(
        "p2_3_workspace_window_contract_scope_exit_seal:"
    )
    assert gate.repo_evidence_gate_passed is True
    assert gate.omni_evidence_required is False
    assert gate.omni_evidence_ignored_by_operator_instruction is True
    assert result.next_pack == P2_4_A_NEXT_PACK
    assert result.starts_future_work is False
    assert_p2_4_a_depends_on_p2_3_d(gate)
    assert_omni_evidence_is_ignored_by_operator_instruction(gate)


def test_closed_world_enums_reject_unknown_values() -> None:
    with pytest.raises(ValueError):
        CommandPaletteSectionGateStatus("OMNI_BLOCKED")
    with pytest.raises(ValueError):
        GlobalCommandKind("EXECUTE_TOOL")
    with pytest.raises(ValueError):
        GlobalCommandRegistryStatus("ROUTER_READY")
    with pytest.raises(ValueError):
        GlobalCommandScopeKind("KEYBOARD_SHORTCUT")
    with pytest.raises(ValueError):
        GlobalCommandAvailabilityStatus("EXECUTABLE")
    with pytest.raises(ValueError):
        GlobalCommandParameterKind("HANDLER")


def test_p2_4_0_section_gate_builds_and_serializes() -> None:
    gate = build_command_palette_section_gate()

    assert gate.section_id == "P2.4"
    assert gate.created_for_pack == "P2.4-A"
    assert gate.official_section_name == "Command Palette / Global Commands"
    assert gate.dependency_pack == "P2.3-D"
    assert gate.gate_status == CommandPaletteSectionGateStatus.READY
    assert gate.repo_evidence_gate_passed is True
    assert gate.omni_evidence_required is False
    assert gate.omni_evidence_ignored_by_operator_instruction is True
    assert json.loads(json.dumps(gate.to_canonical_dict()))


def test_p2_4_1_global_command_identity_is_declarative_only() -> None:
    command_id = build_global_command_id("open_hq_surface")
    identity = build_global_command_identity()

    assert command_id.command_id == "global_command:open_hq_surface"
    assert command_id.stable is True
    assert identity.slug == "open_hq_surface"
    assert identity.label == "Open HQ Surface"
    assert identity.description
    assert identity.kind == GlobalCommandKind.NAVIGATION_PROPOSAL
    assert identity.is_declarative is True
    assert identity.is_executable is False
    assert identity.is_command_handler is False
    assert identity.claims_live is False
    assert identity.claims_trace_verified is False
    assert identity.claims_product_behavior is False
    assert_command_is_not_execution(identity)
    assert json.loads(json.dumps(identity.to_canonical_dict()))


def test_p2_4_1_identity_assertion_rejects_execution_claim() -> None:
    identity = build_global_command_identity()
    payload = identity.to_canonical_dict()
    payload["is_executable"] = True
    invalid = GlobalCommandIdentity(**payload)
    with pytest.raises(AurelShellValidationError):
        assert_command_is_not_execution(invalid)


def test_p2_4_2_registry_builds_serializes_and_is_not_router() -> None:
    registry = build_global_command_registry()
    serialized = json.dumps(registry.to_canonical_dict(), sort_keys=True)

    assert registry.section_id == "P2.4"
    assert registry.created_for_pack == "P2.4-A"
    assert registry.registry_status == GlobalCommandRegistryStatus.READY
    assert len(registry.commands) == 3
    assert serialized == json.dumps(registry.to_canonical_dict(), sort_keys=True)
    assert registry.is_command_router is False
    assert registry.executes_commands is False
    assert registry.mutates_runtime is False
    assert registry.writes_memory is False
    assert registry.writes_trace is False
    assert registry.writes_storage is False
    assert registry.creates_ui is False
    assert_registry_is_not_router(registry)


def test_p2_4_2_registry_rejects_router_overclaim() -> None:
    registry = build_global_command_registry()
    payload = registry.to_canonical_dict()
    payload["is_command_router"] = True
    invalid = GlobalCommandRegistry(**payload)
    with pytest.raises(AurelShellValidationError):
        assert_registry_is_not_router(invalid)


def test_p2_4_3_scope_and_surface_target_use_official_registry_only() -> None:
    target = build_global_command_surface_target("hq")
    scope = build_global_command_scope(surface_id="hq")

    assert target.surface_id == "hq"
    assert target.surface_display_name == "HQ"
    assert target.uses_official_surface_registry is True
    assert target.is_authority_grant is False
    assert target.executes_route is False
    assert target.switches_surface_runtime is False
    assert scope.scope_kind == GlobalCommandScopeKind.SURFACE
    assert scope.surface_id == "hq"
    assert scope.uses_official_surface_registry is True
    assert scope.is_authority_grant is False
    assert scope.executes_route is False
    assert scope.switches_surface_runtime is False
    assert_surface_target_is_not_route_execution(target)


def test_p2_4_3_invalid_surface_target_rejected() -> None:
    with pytest.raises(AurelShellValidationError):
        build_global_command_surface_target("workspace")


def test_p2_4_4_availability_execution_unavailable_and_not_permission() -> None:
    availability = build_global_command_availability()

    assert availability.availability_status == (
        GlobalCommandAvailabilityStatus.UNAVAILABLE_FOR_EXECUTION
    )
    assert availability.available_for_declaration is True
    assert availability.available_for_execution is False
    assert availability.unavailable_reason == COMMAND_EXECUTION_UNAVAILABLE_REASON
    assert availability.is_permission_decision is False
    assert availability.grants_permission is False
    assert availability.denies_permission is False
    assert availability.blocks_runtime is False
    assert availability.requires_custos is False
    assert_availability_is_not_permission(availability)
    assert json.loads(json.dumps(availability.to_canonical_dict()))


def test_p2_4_4_unavailable_execution_requires_reason() -> None:
    with pytest.raises(AurelShellValidationError):
        build_global_command_availability(unavailable_reason="")

    availability = build_global_command_availability()
    payload = availability.to_canonical_dict()
    payload["grants_permission"] = True
    invalid = GlobalCommandAvailability(**payload)
    with pytest.raises(AurelShellValidationError):
        assert_availability_is_not_permission(invalid)


def test_p2_4_5_input_contract_parameters_are_not_invocation() -> None:
    parameter = build_global_command_parameter(
        "surface_id",
        GlobalCommandParameterKind.SURFACE_ID,
        required=True,
        description="Official surface identifier.",
        enum_values=CANONICAL_SURFACE_ORDER,
    )
    contract = build_global_command_input_contract(parameters=(parameter,))

    assert parameter.required is True
    assert parameter.parameter_kind == GlobalCommandParameterKind.SURFACE_ID
    assert contract.parameters == (parameter,)
    assert contract.required_parameters == ("surface_id",)
    assert contract.optional_parameters == ()
    assert contract.validation_mode == "DECLARATIVE_SCHEMA_ONLY"
    assert contract.is_invocation is False
    assert contract.invokes_handler is False
    assert contract.executes_command is False
    assert_input_contract_is_not_invocation(contract)
    assert json.loads(json.dumps(contract.to_canonical_dict()))


def test_result_serializes_preserves_surfaces_and_future_pack_boundaries() -> None:
    result = build_p2_4_a_global_command_foundation_result()
    summary = render_global_command_registry_summary(result)

    assert result.pack_id == "P2.4-A"
    assert result.section_id == "P2.4"
    assert result.official_section_name == "Command Palette / Global Commands"
    assert result.dependency_pack == "P2.3-D"
    assert result.covered_checkpoints == P2_4_A_PACK_CHECKPOINT_IDS
    assert result.canonical_surface_ids == CANONICAL_SURFACE_ORDER
    assert result.surface_taxonomy_drift is True
    assert result.report_path == P2_4_A_REPORT_PATH
    assert result.report_index_expected is True
    assert result.claims_live is False
    assert result.claims_trace_verified is False
    assert result.claims_release_scope is False
    assert result.claims_product_behavior is False
    assert result.starts_future_work is False
    assert result.next_pack == "P2.4-B"
    assert "commands=3" in summary
    assert "executes_commands=false" in summary
    assert "command_palette_ui=false" in summary
    assert json.loads(serialize_p2_4_a_result(result))
    assert_p2_4_a_does_not_start_future_work(result)


def test_future_work_assertion_rejects_start_flag() -> None:
    result = build_p2_4_a_global_command_foundation_result()
    payload = result.to_canonical_dict()
    payload["starts_future_work"] = True
    invalid = P24AGlobalCommandFoundationResult(**payload)
    with pytest.raises(AurelShellValidationError):
        assert_p2_4_a_does_not_start_future_work(invalid)


def test_side_effect_proof_all_false() -> None:
    proof = build_p2_4_a_side_effect_proof()
    assert_p2_4_a_side_effects_all_false(proof)
    for field, value in proof.to_canonical_dict().items():
        assert value is False, field
