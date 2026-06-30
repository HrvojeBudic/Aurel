"""Tests for P2.7-A Shell / CLI / TUI binding foundation contracts."""

from __future__ import annotations

import json
from dataclasses import fields

import pytest

from agentic_runtime.aurel_shell.shell_binding_foundation import (
    P2_6_D_REPORT_PATH,
    P2_7_A_DEPENDENCY_PACK,
    P2_7_A_NEXT_PACK,
    P2_7_A_OFFICIAL_SECTION_NAME,
    P2_7_A_PACK_CHECKPOINT_IDS,
    P2_7_A_PACK_ID,
    P2_7_A_REPORT_PATH,
    P2_7_A_SECTION_ID,
    P2_7_A_VALIDATION_COMMANDS,
    P27ASideEffectProof,
    P27AShellBindingFoundationResult,
    ShellBindingCapabilityKind,
    ShellBindingCapabilityMode,
    ShellBindingCommandSurfaceMode,
    ShellBindingSectionGateStatus,
    assert_adapter_contract_is_not_runtime_dispatch,
    assert_binding_contract_is_not_command_execution,
    assert_binding_section_gate_depends_on_p2_6_d,
    assert_binding_target_registry_is_not_source_of_truth,
    assert_cli_descriptor_is_not_cli_app,
    assert_command_surface_is_read_only,
    assert_no_command_execution_boundary_is_active,
    assert_no_runtime_dispatch_boundary_is_active,
    assert_omni_evidence_is_ignored_by_operator_instruction,
    assert_output_descriptor_is_not_product_ui,
    assert_p2_7_a_does_not_start_future_work,
    assert_p2_7_a_side_effects_all_false,
    assert_projection_consumption_is_not_live_bridge_consumption,
    assert_render_descriptor_is_not_tui_runtime,
    assert_shell_descriptor_is_not_shell_runtime,
    assert_surface_binding_catalog_is_not_surface_switcher,
    assert_tui_descriptor_is_not_tui_runtime,
    build_p2_7_a_shell_binding_foundation_result,
    build_p2_7_a_side_effect_proof,
    build_shell_binding_adapter_contract,
    build_shell_binding_capability_descriptor,
    build_shell_binding_capability_descriptors,
    build_shell_binding_foundation_result,
    build_shell_binding_no_command_execution_boundary,
    build_shell_binding_no_runtime_dispatch_boundary,
    build_shell_binding_output_descriptor,
    build_shell_binding_projection_consumption_contract,
    build_shell_binding_read_only_command_surface,
    build_shell_binding_render_descriptor,
    build_shell_binding_section_gate,
    build_shell_binding_surface_catalog,
    build_shell_binding_target_registry,
    render_shell_binding_contract_summary,
    serialize_p2_7_a_result,
)
from agentic_runtime.aurel_shell.surface_projection_foundation import (
    OFFICIAL_ACTIVE_SURFACE_NAMES,
)
from agentic_runtime.aurel_shell.surface_registry import CANONICAL_SURFACE_ORDER, OLD_SURFACE_TAXONOMY


def test_module_imports_p2_7_a() -> None:
    import agentic_runtime.aurel_shell.shell_binding_foundation  # noqa: F401


def test_gate_dependency_and_omni_policy() -> None:
    result = build_p2_7_a_shell_binding_foundation_result()
    gate = result.binding_section_gate

    assert P2_7_A_PACK_ID == "P2.7-A"
    assert P2_7_A_SECTION_ID == "P2.7"
    assert P2_7_A_OFFICIAL_SECTION_NAME == "Shell / CLI / TUI Binding"
    assert P2_7_A_DEPENDENCY_PACK == "P2.6-D"
    assert gate.dependency_pack == "P2.6-D"
    assert gate.dependency_report_ref == P2_6_D_REPORT_PATH
    assert gate.dependency_section_seal_result_ref
    assert gate.dependency_binding_availability_ref
    assert gate.dependency_no_live_infrastructure_proof_ref
    assert gate.dependency_side_effect_proof_ref == "P26DSideEffectProof:all_false"
    assert gate.repo_evidence_gate_passed is True
    assert gate.omni_evidence_required is False
    assert gate.omni_evidence_ignored_by_operator_instruction is True
    assert_binding_section_gate_depends_on_p2_6_d(gate)
    assert_omni_evidence_is_ignored_by_operator_instruction(gate)


def test_p2_7_a_does_not_start_future_work() -> None:
    result = build_p2_7_a_shell_binding_foundation_result()
    assert result.next_pack == P2_7_A_NEXT_PACK == "P2.7-B"
    assert result.starts_future_work is False
    assert result.side_effect_proof.p2_7_b_started is False
    assert result.side_effect_proof.p2_8_started is False
    assert result.side_effect_proof.p2_10_started is False
    assert result.side_effect_proof.p2_13_started is False
    assert_p2_7_a_does_not_start_future_work(result)


def test_closed_world_enums_reject_unknown_values() -> None:
    with pytest.raises(ValueError):
        ShellBindingSectionGateStatus("LIVE")
    with pytest.raises(ValueError):
        ShellBindingCapabilityMode("EXECUTABLE")
    with pytest.raises(ValueError):
        ShellBindingCommandSurfaceMode("EXECUTABLE")


def test_p2_7_0_binding_section_gate() -> None:
    gate = build_shell_binding_section_gate()
    assert gate.gate_status in set(ShellBindingSectionGateStatus)
    assert gate.created_for_pack == "P2.7-A"
    assert gate.official_section_name == "Shell / CLI / TUI Binding"
    assert gate.truth_label == "BINDING_GATE_ONLY"
    assert json.loads(json.dumps(gate.to_canonical_dict(), sort_keys=True))


def test_p2_7_1_target_registry_and_surface_catalog() -> None:
    registry = build_shell_binding_target_registry()
    catalog = build_shell_binding_surface_catalog(registry.registry_id)

    assert len(registry.target_entries) == len(CANONICAL_SURFACE_ORDER)
    assert registry.official_surface_set == OFFICIAL_ACTIVE_SURFACE_NAMES
    assert registry.is_source_of_truth is False
    assert registry.creates_surface_switch is False
    assert catalog.official_surface_set == OFFICIAL_ACTIVE_SURFACE_NAMES
    assert catalog.is_live_surface_switcher is False
    assert catalog.mutates_navigation is False
    assert catalog.binding_surface_kinds == ("SHELL", "CLI", "TUI")
    assert_binding_target_registry_is_not_source_of_truth(registry)
    assert_surface_binding_catalog_is_not_surface_switcher(catalog)
    for old_surface in OLD_SURFACE_TAXONOMY:
        assert old_surface not in catalog.official_surface_set
    assert json.loads(json.dumps(registry.to_canonical_dict(), sort_keys=True))
    assert json.loads(json.dumps(catalog.to_canonical_dict(), sort_keys=True))


def test_p2_7_2_capability_descriptors() -> None:
    descriptors = build_shell_binding_capability_descriptors()
    kinds = {descriptor.capability_kind for descriptor in descriptors}
    assert ShellBindingCapabilityKind.CLI_BINDING_DESCRIPTOR in kinds
    assert ShellBindingCapabilityKind.TUI_BINDING_DESCRIPTOR in kinds
    assert ShellBindingCapabilityKind.SHELL_BINDING_DESCRIPTOR in kinds
    assert ShellBindingCapabilityKind.READ_ONLY_COMMAND_SURFACE_DESCRIPTOR in kinds
    assert ShellBindingCapabilityKind.OUTPUT_DESCRIPTOR in kinds
    assert ShellBindingCapabilityKind.RENDER_DESCRIPTOR in kinds

    cli = build_shell_binding_capability_descriptor(
        ShellBindingCapabilityKind.CLI_BINDING_DESCRIPTOR
    )
    tui = build_shell_binding_capability_descriptor(
        ShellBindingCapabilityKind.TUI_BINDING_DESCRIPTOR
    )
    shell = build_shell_binding_capability_descriptor(
        ShellBindingCapabilityKind.SHELL_BINDING_DESCRIPTOR
    )
    unavailable = build_shell_binding_capability_descriptor(
        ShellBindingCapabilityKind.UNKNOWN_UNAVAILABLE
    )

    assert cli.available_as_cli_app is False
    assert tui.available_as_tui_runtime is False
    assert shell.available_as_shell_runtime is False
    assert cli.executable is False
    assert unavailable.capability_mode == ShellBindingCapabilityMode.UNAVAILABLE
    assert_cli_descriptor_is_not_cli_app(cli)
    assert_tui_descriptor_is_not_tui_runtime(tui)
    assert_shell_descriptor_is_not_shell_runtime(shell)


def test_p2_7_3_adapter_and_projection_consumption() -> None:
    consumption = build_shell_binding_projection_consumption_contract()
    adapter = build_shell_binding_adapter_contract(consumption)

    assert consumption.source_pack == "P2.6-D"
    assert consumption.source_section == "P2.6"
    assert consumption.source_section_seal_ref
    assert consumption.source_read_model_ref
    assert consumption.source_contract_inventory_ref
    assert adapter.dispatches_runtime is False
    assert adapter.creates_runtime_bridge is False
    assert adapter.mutates_runtime is False
    assert consumption.consumes_live_api is False
    assert consumption.consumes_live_event_bridge is False
    assert consumption.reads_runtime_state is False
    assert consumption.mutates_runtime is False
    assert_adapter_contract_is_not_runtime_dispatch(adapter)
    assert_projection_consumption_is_not_live_bridge_consumption(consumption)


def test_p2_7_4_read_only_command_surface_and_output_descriptors() -> None:
    command_surface = build_shell_binding_read_only_command_surface()
    output_descriptor = build_shell_binding_output_descriptor()
    render_descriptor = build_shell_binding_render_descriptor()

    assert command_surface.command_surface_mode in set(ShellBindingCommandSurfaceMode)
    assert command_surface.executable_commands == ()
    assert command_surface.creates_command_parser is False
    assert command_surface.creates_command_router is False
    assert command_surface.creates_command_handler is False
    assert command_surface.executes_commands is False
    assert output_descriptor.is_product_ui is False
    assert output_descriptor.requires_tui_runtime is False
    assert render_descriptor.is_tui_runtime is False
    assert render_descriptor.is_product_ui is False
    assert render_descriptor.requires_frontend is False
    assert_command_surface_is_read_only(command_surface)
    assert_output_descriptor_is_not_product_ui(output_descriptor)
    assert_render_descriptor_is_not_tui_runtime(render_descriptor)


def test_p2_7_5_boundaries_and_foundation_result() -> None:
    no_command = build_shell_binding_no_command_execution_boundary()
    no_runtime = build_shell_binding_no_runtime_dispatch_boundary()
    foundation = build_shell_binding_foundation_result()
    result = build_p2_7_a_shell_binding_foundation_result()

    assert no_command.boundary_active is True
    assert no_command.prevents_command_parser is True
    assert no_command.prevents_command_router is True
    assert no_command.prevents_command_handler is True
    assert no_command.prevents_command_execution is True
    assert no_command.prevents_command_invocation is True
    assert no_command.prevents_tool_invocation is True
    assert no_command.prevents_workflow_dispatch is True
    assert no_runtime.boundary_active is True
    assert no_runtime.prevents_runtime_dispatch is True
    assert no_runtime.prevents_runtime_bridge is True
    assert no_runtime.prevents_runtime_mutation is True
    assert no_runtime.prevents_surface_switch is True
    assert no_runtime.prevents_trace_write is True
    assert no_runtime.prevents_memory_write is True
    assert no_runtime.prevents_storage_write is True
    assert_no_command_execution_boundary_is_active(no_command)
    assert_no_runtime_dispatch_boundary_is_active(no_runtime)

    assert foundation.creates_cli_app is False
    assert foundation.creates_cli_runner is False
    assert foundation.creates_tui_runtime is False
    assert foundation.creates_shell_runtime is False
    assert foundation.creates_command_execution is False
    assert foundation.creates_command_router is False
    assert foundation.creates_command_handler is False
    assert foundation.creates_tool_invocation is False
    assert foundation.creates_workflow_dispatch is False
    assert foundation.creates_runtime_dispatch is False
    assert foundation.creates_runtime_bridge is False
    assert foundation.creates_runtime_mutation is False
    assert foundation.creates_product_behavior is False
    assert_binding_contract_is_not_command_execution(foundation)

    assert result.covered_checkpoints == P2_7_A_PACK_CHECKPOINT_IDS
    assert result.claims_live is False
    assert result.claims_trace_verified is False
    assert result.claims_release_scope is False
    assert result.claims_product_behavior is False


def test_side_effect_proof_all_false() -> None:
    proof = build_p2_7_a_side_effect_proof()
    assert_p2_7_a_side_effects_all_false(proof)
    for field in fields(P27ASideEffectProof):
        assert getattr(proof, field.name) is False


def test_serialization_and_summary() -> None:
    result = build_p2_7_a_shell_binding_foundation_result()
    serialized = serialize_p2_7_a_result(result)
    assert isinstance(serialized, str)
    assert "P2.7" in serialized
    summary = render_shell_binding_contract_summary(result)
    assert "Shell / CLI / TUI Binding" in summary
    assert "P2.7-B" in summary
    assert "command_execution=false" in summary


def test_pack_result_type() -> None:
    result = build_p2_7_a_shell_binding_foundation_result()
    assert isinstance(result, P27AShellBindingFoundationResult)
    assert result.pack_id == P2_7_A_PACK_ID
    assert P2_7_A_REPORT_PATH.endswith(".md")
    assert len(P2_7_A_VALIDATION_COMMANDS) == 5
