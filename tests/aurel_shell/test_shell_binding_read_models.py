"""Tests for P2.7-B Shell binding read models / command surface adapter contracts."""

from __future__ import annotations

import json
from dataclasses import fields

import pytest

from agentic_runtime.aurel_shell.shell_binding_foundation import (
    build_p2_7_a_shell_binding_foundation_result,
)
from agentic_runtime.aurel_shell.shell_binding_read_models import (
    P2_7_A_REPORT_PATH,
    P2_7_B_DEPENDENCY_PACK,
    P2_7_B_NEXT_PACK,
    P2_7_B_OFFICIAL_SECTION_NAME,
    P2_7_B_PACK_CHECKPOINT_IDS,
    P2_7_B_PACK_ID,
    P2_7_B_REPORT_PATH,
    P2_7_B_SECTION_ID,
    P2_7_B_VALIDATION_COMMANDS,
    P27BShellBindingReadModelResult,
    P27BSideEffectProof,
    ShellBindingAvailabilityReadModelStatus,
    ShellBindingReadModelGateStatus,
    ShellCommandDescriptorKind,
    ShellCommandSurfaceAdapterMode,
    assert_adapter_expansion_result_is_not_command_execution,
    assert_adapter_read_model_is_not_command_handler,
    assert_adapter_read_model_is_not_command_router,
    assert_availability_read_model_is_not_permission_enforcement,
    assert_command_descriptor_is_not_command_parser,
    assert_context_descriptor_does_not_mutate_runtime_context,
    assert_omni_evidence_is_ignored_by_operator_instruction,
    assert_output_preview_is_not_output_writer,
    assert_p2_7_b_does_not_start_future_work,
    assert_p2_7_b_side_effects_all_false,
    assert_read_model_gate_depends_on_p2_7_a,
    assert_read_model_inventory_does_not_duplicate_source_of_truth,
    assert_read_model_registry_is_not_source_of_truth,
    assert_render_preview_is_not_product_ui,
    assert_render_preview_is_not_tui_runtime,
    assert_selection_descriptor_is_not_operator_confirmation,
    build_p2_7_b_shell_binding_read_model_result,
    build_p2_7_b_side_effect_proof,
    build_shell_binding_adapter_expansion_result,
    build_shell_binding_availability_read_model,
    build_shell_binding_context_descriptor,
    build_shell_binding_output_preview_schema,
    build_shell_binding_read_model_gate,
    build_shell_binding_read_model_inventory,
    build_shell_binding_read_model_registry,
    build_shell_binding_render_preview_schema,
    build_shell_binding_selection_descriptor,
    build_shell_command_descriptor_read_model,
    build_shell_command_descriptor_read_models,
    build_shell_command_surface_adapter_read_model,
    render_shell_binding_read_model_summary,
    serialize_p2_7_b_result,
)
from agentic_runtime.aurel_shell.surface_projection_foundation import (
    OFFICIAL_ACTIVE_SURFACE_NAMES,
)
from agentic_runtime.aurel_shell.surface_registry import OLD_SURFACE_TAXONOMY


def _roundtrip(obj) -> dict:
    return json.loads(json.dumps(obj.to_canonical_dict(), sort_keys=True))


def test_module_imports_p2_7_b() -> None:
    import agentic_runtime.aurel_shell.shell_binding_read_models  # noqa: F401


# ---------------------------------------------------------------------------
# Gate / dependency tests
# ---------------------------------------------------------------------------


def test_gate_dependency_and_omni_policy() -> None:
    result = build_p2_7_b_shell_binding_read_model_result()
    gate = result.read_model_gate

    assert P2_7_B_PACK_ID == "P2.7-B"
    assert P2_7_B_SECTION_ID == "P2.7"
    assert P2_7_B_OFFICIAL_SECTION_NAME == "Shell / CLI / TUI Binding"
    assert P2_7_B_DEPENDENCY_PACK == "P2.7-A"
    assert gate.dependency_pack == "P2.7-A"
    assert gate.dependency_report_ref == P2_7_A_REPORT_PATH
    assert gate.dependency_binding_foundation_result_ref
    assert gate.dependency_no_command_execution_boundary_ref
    assert gate.dependency_no_runtime_dispatch_boundary_ref
    assert gate.dependency_side_effect_proof_ref == "P27ASideEffectProof:all_false"
    assert gate.repo_evidence_gate_passed is True
    assert gate.omni_evidence_required is False
    assert gate.omni_evidence_ignored_by_operator_instruction is True
    assert_read_model_gate_depends_on_p2_7_a(gate)
    assert_omni_evidence_is_ignored_by_operator_instruction(gate)


def test_p2_7_a_evidence_represented() -> None:
    foundation = build_p2_7_a_shell_binding_foundation_result()
    result = build_p2_7_b_shell_binding_read_model_result()

    # P2.7-A binding foundation result, boundaries and side-effect proof reused by ref.
    assert result.p2_7_a_evidence_ref.startswith(P2_7_A_REPORT_PATH)
    assert foundation.binding_foundation_result.binding_foundation_result_id in (
        result.read_model_gate.dependency_binding_foundation_result_ref
    )
    assert (
        foundation.no_command_execution_boundary.boundary_id
        in result.read_model_gate.dependency_no_command_execution_boundary_ref
    )
    assert (
        foundation.no_runtime_dispatch_boundary.boundary_id
        in result.read_model_gate.dependency_no_runtime_dispatch_boundary_ref
    )


def test_p2_7_b_does_not_start_future_work() -> None:
    result = build_p2_7_b_shell_binding_read_model_result()
    assert result.next_pack == P2_7_B_NEXT_PACK == "P2.7-C"
    assert result.starts_future_work is False
    assert result.side_effect_proof.p2_7_c_started is False
    assert result.side_effect_proof.p2_8_started is False
    assert result.side_effect_proof.p2_10_started is False
    assert result.side_effect_proof.p2_13_started is False
    assert_p2_7_b_does_not_start_future_work(result)


def test_closed_world_enums_reject_unknown_values() -> None:
    with pytest.raises(ValueError):
        ShellBindingReadModelGateStatus("LIVE")
    with pytest.raises(ValueError):
        ShellCommandDescriptorKind("EXECUTABLE")
    with pytest.raises(ValueError):
        ShellCommandSurfaceAdapterMode("EXECUTABLE")
    with pytest.raises(ValueError):
        ShellBindingAvailabilityReadModelStatus("LIVE")


# ---------------------------------------------------------------------------
# P2.7.6 — Binding Read Model Registry / Inventory Contract
# ---------------------------------------------------------------------------


def test_p2_7_6_gate_registry_inventory() -> None:
    gate = build_shell_binding_read_model_gate()
    registry = build_shell_binding_read_model_registry()
    inventory = build_shell_binding_read_model_inventory()

    assert gate.gate_status in set(ShellBindingReadModelGateStatus)
    assert gate.created_for_pack == "P2.7-B"
    assert gate.official_section_name == "Shell / CLI / TUI Binding"

    assert len(registry.read_model_entries) > 0
    assert registry.official_surface_set == OFFICIAL_ACTIVE_SURFACE_NAMES
    assert registry.is_source_of_truth is False
    assert registry.creates_runtime_binding is False
    assert registry.inventory_ref == inventory.inventory_id
    for entry in registry.read_model_entries:
        assert entry.available_as_read_model is True
        assert entry.available_as_runtime_binding is False

    assert inventory.covered_checkpoints == P2_7_B_PACK_CHECKPOINT_IDS
    assert inventory.is_source_of_truth is False
    assert inventory.duplicates_source_of_truth is False
    assert "P2.7-A" in inventory.source_pack_refs
    assert "P2.7-B" in inventory.source_pack_refs

    assert_read_model_registry_is_not_source_of_truth(registry)
    assert_read_model_inventory_does_not_duplicate_source_of_truth(inventory)
    assert _roundtrip(registry)
    assert _roundtrip(inventory)
    assert _roundtrip(gate)


# ---------------------------------------------------------------------------
# P2.7.7 — Command Descriptor / Command Surface Adapter Read Model
# ---------------------------------------------------------------------------


def test_p2_7_7_command_descriptor_and_adapter() -> None:
    descriptor = build_shell_command_descriptor_read_model()
    descriptors = build_shell_command_descriptor_read_models()
    adapter = build_shell_command_surface_adapter_read_model()

    kinds = {d.descriptor_kind for d in descriptors}
    assert ShellCommandDescriptorKind.READ_ONLY_COMMAND_DESCRIPTOR in kinds
    assert ShellCommandDescriptorKind.OUTPUT_PREVIEW_DESCRIPTOR in kinds
    assert ShellCommandDescriptorKind.RENDER_PREVIEW_DESCRIPTOR in kinds

    assert descriptor.descriptor_kind in set(ShellCommandDescriptorKind)
    assert descriptor.available_as_descriptor is True
    assert descriptor.available_as_parser is False
    assert descriptor.executable is False

    assert adapter.adapter_mode in set(ShellCommandSurfaceAdapterMode)
    assert adapter.is_command_router is False
    assert adapter.is_command_handler is False
    assert adapter.executes_commands is False

    assert_command_descriptor_is_not_command_parser(descriptor)
    assert_adapter_read_model_is_not_command_router(adapter)
    assert_adapter_read_model_is_not_command_handler(adapter)
    assert _roundtrip(descriptor)
    assert _roundtrip(adapter)


# ---------------------------------------------------------------------------
# P2.7.8 — Output Preview / Render Preview Schema Contract
# ---------------------------------------------------------------------------


def test_p2_7_8_output_and_render_preview() -> None:
    output_preview = build_shell_binding_output_preview_schema()
    render_preview = build_shell_binding_render_preview_schema()

    assert output_preview.writes_output is False
    assert output_preview.creates_output_writer is False
    assert len(output_preview.preview_fields) > 0

    assert render_preview.requires_tui_runtime is False
    assert render_preview.creates_render_runtime is False
    assert render_preview.is_product_ui is False
    assert render_preview.requires_frontend is False

    assert_output_preview_is_not_output_writer(output_preview)
    assert_render_preview_is_not_tui_runtime(render_preview)
    assert_render_preview_is_not_product_ui(render_preview)
    assert _roundtrip(output_preview)
    assert _roundtrip(render_preview)


# ---------------------------------------------------------------------------
# P2.7.9 — Binding Context / Availability / Selection Descriptor Contract
# ---------------------------------------------------------------------------


def test_p2_7_9_context_availability_selection() -> None:
    context = build_shell_binding_context_descriptor()
    availability = build_shell_binding_availability_read_model()
    selection = build_shell_binding_selection_descriptor()

    assert context.reads_runtime_context is False
    assert context.mutates_runtime_context is False
    assert context.mutates_runtime is False

    assert availability.availability_status in set(ShellBindingAvailabilityReadModelStatus)
    assert availability.grants_permission is False
    assert availability.denies_permission is False
    assert availability.enforces_permission is False
    assert availability.activates_approval is False

    assert selection.creates_operator_confirmation is False
    assert selection.creates_approval_runtime is False
    assert selection.executes_selection is False

    assert_context_descriptor_does_not_mutate_runtime_context(context)
    assert_availability_read_model_is_not_permission_enforcement(availability)
    assert_selection_descriptor_is_not_operator_confirmation(selection)
    assert _roundtrip(context)
    assert _roundtrip(availability)
    assert _roundtrip(selection)


# ---------------------------------------------------------------------------
# P2.7.10 — Adapter Expansion Result / No-Execution Boundary
# ---------------------------------------------------------------------------


def test_p2_7_10_adapter_expansion_result() -> None:
    expansion = build_shell_binding_adapter_expansion_result()
    result = build_p2_7_b_shell_binding_read_model_result()

    assert expansion.creates_command_parser is False
    assert expansion.creates_command_router is False
    assert expansion.creates_command_handler is False
    assert expansion.creates_command_execution is False
    assert expansion.creates_output_writer is False
    assert expansion.creates_tui_runtime is False
    assert expansion.creates_operator_confirmation is False
    assert expansion.creates_permission_enforcement is False
    assert expansion.creates_runtime_dispatch is False
    assert expansion.creates_runtime_mutation is False
    assert expansion.creates_product_behavior is False
    assert_adapter_expansion_result_is_not_command_execution(expansion)

    assert result.covered_checkpoints == P2_7_B_PACK_CHECKPOINT_IDS
    assert result.next_pack == "P2.7-C"
    assert result.claims_live is False
    assert result.claims_trace_verified is False
    assert result.claims_release_scope is False
    assert result.claims_product_behavior is False
    assert _roundtrip(expansion)


def test_surface_taxonomy_drift_does_not_activate_old_surfaces() -> None:
    result = build_p2_7_b_shell_binding_read_model_result()
    surface_set = result.read_model_registry.official_surface_set
    for old_surface in OLD_SURFACE_TAXONOMY:
        assert old_surface not in surface_set


# ---------------------------------------------------------------------------
# Side-effect proof
# ---------------------------------------------------------------------------


def test_side_effect_proof_all_false() -> None:
    proof = build_p2_7_b_side_effect_proof()
    assert_p2_7_b_side_effects_all_false(proof)
    for field in fields(P27BSideEffectProof):
        assert getattr(proof, field.name) is False


def test_serialization_and_summary() -> None:
    result = build_p2_7_b_shell_binding_read_model_result()
    serialized = serialize_p2_7_b_result(result)
    assert isinstance(serialized, str)
    assert "P2.7" in serialized
    # Determinism: serialization is stable across builds.
    assert serialize_p2_7_b_result() == serialized

    summary = render_shell_binding_read_model_summary(result)
    assert "Shell / CLI / TUI Binding" in summary
    assert "P2.7-C" in summary
    assert "command_execution=false" in summary
    assert "runtime_dispatch=false" in summary


def test_pack_result_type() -> None:
    result = build_p2_7_b_shell_binding_read_model_result()
    assert isinstance(result, P27BShellBindingReadModelResult)
    assert result.pack_id == P2_7_B_PACK_ID
    assert P2_7_B_REPORT_PATH.endswith(".md")
    assert len(P2_7_B_VALIDATION_COMMANDS) == 5
