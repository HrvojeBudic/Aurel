"""Tests for P2.3-D workspace window section projection and seal."""

from __future__ import annotations

import json

import pytest

from agentic_runtime.aurel_shell.contracts import AurelShellValidationError
from agentic_runtime.aurel_shell.surface_registry import CANONICAL_SURFACE_ORDER
from agentic_runtime.aurel_shell.workspace_state import (
    P2_3_A_PACK_ID,
    build_p2_3_a_workspace_state_foundation_result,
)
from agentic_runtime.aurel_shell.workspace_window_cross_surface import (
    P2_3_C_PACK_ID,
    P2_3_C_REPORT_FILENAME,
    build_p2_3_c_window_cross_surface_semantics_result,
)
from agentic_runtime.aurel_shell.workspace_window_section_projection import (
    AUDIT_REPAIR_001_PACK_ID,
    P2_2_D_PACK_ID,
    P2_3_B_PACK_ID,
    P2_3_D_DEPENDENCY_PACKS,
    P2_3_D_NEXT_PACK,
    P2_3_D_PACK_CHECKPOINT_IDS,
    P2_3_D_PACK_ID,
    P2_3_D_REPORT_PATH,
    BINDING_UNAVAILABLE_REASON,
    WorkspaceWindowBindingState,
    WorkspaceWindowBindingStatus,
    WorkspaceWindowSectionProjection,
    WorkspaceWindowSectionSealStatus,
    assert_cli_tui_binding_is_read_only_or_unavailable,
    assert_contract_demo_is_not_live,
    assert_exit_seal_is_not_release_scope,
    assert_p2_3_a_foundation_exists,
    assert_p2_3_b_projection_result_exists,
    assert_p2_3_c_projection_result_exists,
    assert_p2_3_d_depends_on_p2_3_c,
    assert_p2_3_d_does_not_start_p2_10,
    assert_p2_3_d_does_not_start_p2_13,
    assert_p2_3_d_does_not_start_p2_4,
    assert_p2_3_d_has_no_product_behavior,
    assert_p2_3_d_side_effects_all_false,
    assert_projection_result_is_not_product_behavior,
    assert_report_evidence_is_not_trace_verified,
    assert_section_projection_is_not_frontend_state,
    assert_section_seal_is_contract_scope_only,
    build_p2_3_d_side_effect_proof,
    build_p2_3_d_workspace_window_section_result,
    build_workspace_window_binding_status,
    build_workspace_window_docs_state_report_sync,
    build_workspace_window_section_capability_records,
    build_workspace_window_section_projection,
    build_workspace_window_section_readiness_audit,
    build_workspace_window_section_seal,
    render_workspace_window_section_summary,
    serialize_p2_3_d_result,
)
from agentic_runtime.aurel_shell.workspace_window_semantics import (
    P2_3_B_REPORT_FILENAME,
    build_p2_3_b_workspace_window_semantics_result,
)


def test_module_imports_p2_3_d() -> None:
    import agentic_runtime.aurel_shell.workspace_window_section_projection  # noqa: F401


def test_dependency_constants_and_p2_3_a_b_c_projection_reuse() -> None:
    foundation = build_p2_3_a_workspace_state_foundation_result()
    semantics = build_p2_3_b_workspace_window_semantics_result()
    cross_surface = build_p2_3_c_window_cross_surface_semantics_result()
    result = build_p2_3_d_workspace_window_section_result()

    assert P2_3_D_PACK_ID == "P2.3-D"
    assert P2_3_D_PACK_CHECKPOINT_IDS == (
        "P2.3.16",
        "P2.3.17",
        "P2.3.18",
        "P2.3.19",
        "P2.3.20",
    )
    assert AUDIT_REPAIR_001_PACK_ID in P2_3_D_DEPENDENCY_PACKS
    assert P2_2_D_PACK_ID in P2_3_D_DEPENDENCY_PACKS
    assert P2_3_A_PACK_ID in P2_3_D_DEPENDENCY_PACKS
    assert P2_3_B_PACK_ID in P2_3_D_DEPENDENCY_PACKS
    assert P2_3_C_PACK_ID in P2_3_D_DEPENDENCY_PACKS
    assert foundation.projection_seed.projection_hash in result.foundation_ref
    assert (
        semantics.workspace_focus_stack_projection_result.projection_hash
        in result.semantics_ref
    )
    assert (
        cross_surface.cross_surface_window_projection_result.projection_hash
        in result.cross_surface_ref
    )
    assert P2_3_B_REPORT_FILENAME in result.p2_3_b_ref
    assert P2_3_C_REPORT_FILENAME in result.p2_3_c_ref
    assert_p2_3_a_foundation_exists(foundation)
    assert_p2_3_b_projection_result_exists(semantics)
    assert_p2_3_c_projection_result_exists(cross_surface)
    assert_p2_3_d_depends_on_p2_3_c(cross_surface)


def test_closed_world_enums_reject_unknown_values() -> None:
    with pytest.raises(ValueError):
        WorkspaceWindowBindingState("COMMAND_PALETTE")
    with pytest.raises(ValueError):
        WorkspaceWindowSectionSealStatus("RELEASE_SEALED")


def test_p2_3_16_section_projection_builds_serializes_and_preserves_refs() -> None:
    projection = build_workspace_window_section_projection()

    assert projection.section_id == "P2.3"
    assert projection.created_for_pack == "P2.3-D"
    assert projection.official_section_name == "Floating Windows / Workspace State"
    assert projection.roadmap_section == "P2.3 - Floating Windows / Workspace State"
    assert len(projection.dependency_refs) == 5
    assert projection.foundation_ref.startswith("p2_3_workspace_state_projection_seed:")
    assert projection.focus_stack_ref.startswith("p2_3_b_workspace_focus_stack_projection:")
    assert projection.cross_surface_ref.startswith(
        "p2_3_c_cross_surface_window_projection:"
    )
    assert tuple(record.checkpoint_id for record in projection.capability_records) == (
        "P2.3.16",
        "P2.3.17",
        "P2.3.18",
        "P2.3.19",
        "P2.3.20",
    )
    assert projection.next_pack == P2_3_D_NEXT_PACK
    assert projection.is_frontend_state_store is False
    assert projection.is_product_behavior is False
    assert projection.claims_live is False
    assert projection.claims_trace_verified is False
    assert projection.claims_release_scope is False
    assert projection.starts_p2_4 is False
    assert projection.starts_p2_10 is False
    assert projection.starts_p2_13 is False
    assert_section_projection_is_not_frontend_state(projection)
    assert_projection_result_is_not_product_behavior(projection)
    assert_report_evidence_is_not_trace_verified(projection)
    assert_p2_3_d_does_not_start_p2_4(projection)
    assert_p2_3_d_does_not_start_p2_10(projection)
    assert_p2_3_d_does_not_start_p2_13(projection)
    assert json.loads(json.dumps(projection.to_canonical_dict()))


def test_p2_3_16_projection_assertions_reject_future_pack_start() -> None:
    projection = build_workspace_window_section_projection()
    payload = projection.to_canonical_dict()
    payload["starts_p2_4"] = True
    invalid = WorkspaceWindowSectionProjection(**payload)
    with pytest.raises(AurelShellValidationError):
        assert_p2_3_d_does_not_start_p2_4(invalid)


def test_p2_3_17_binding_read_only_or_unavailable() -> None:
    binding = build_workspace_window_binding_status()

    assert binding.binding_status == WorkspaceWindowBindingState.READ_ONLY
    assert binding.read_only is True
    assert binding.available is True
    assert binding.renders_section_projection is True
    assert binding.executes_commands is False
    assert binding.starts_command_palette is False
    assert binding.creates_shell_ui is False
    assert binding.mutates_runtime is False
    assert binding.writes_storage is False
    assert binding.writes_memory is False
    assert binding.writes_trace is False
    assert_cli_tui_binding_is_read_only_or_unavailable(binding)
    assert json.loads(json.dumps(binding.to_canonical_dict()))


def test_p2_3_17_unavailable_binding_requires_reason() -> None:
    binding = build_workspace_window_binding_status(
        binding_status=WorkspaceWindowBindingState.UNAVAILABLE
    )
    assert binding.available is False
    assert binding.unavailable_reason == BINDING_UNAVAILABLE_REASON

    payload = binding.to_canonical_dict()
    payload["unavailable_reason"] = ""
    invalid = WorkspaceWindowBindingStatus(**payload)
    with pytest.raises(AurelShellValidationError):
        assert_cli_tui_binding_is_read_only_or_unavailable(invalid)


def test_p2_3_17_rendered_summary_is_deterministic_and_read_only() -> None:
    projection = build_workspace_window_section_projection()
    summary = render_workspace_window_section_summary(projection)
    assert summary == render_workspace_window_section_summary(projection)
    assert "P2.3 Floating Windows / Workspace State" in summary
    assert "pack=P2.3-D" in summary
    assert "status=SEALED_FOR_CONTRACT_SCOPE" in summary
    assert "p2_4_started=false" in summary


def test_p2_3_18_docs_state_report_sync_representation() -> None:
    sync = build_workspace_window_docs_state_report_sync()

    assert sync.report_path == P2_3_D_REPORT_PATH
    assert sync.report_index_expected is True
    assert sync.report_created is True
    assert sync.report_index_updated is True
    assert sync.coverage_matrix_present is True
    assert sync.progress_mirror_is_roadmap_authority is False
    assert sync.duplicate_governance_surface_created is False
    assert sync.docs_updated is False
    assert json.loads(json.dumps(sync.to_canonical_dict()))


def test_capability_records_are_contract_scope_not_product_behavior() -> None:
    records = build_workspace_window_section_capability_records()
    assert len(records) == 5
    assert all(record.is_contract_scope for record in records)
    assert all(record.is_product_behavior is False for record in records)
    assert {record.checkpoint_id for record in records} == set(P2_3_D_PACK_CHECKPOINT_IDS)


def test_p2_3_19_readiness_audit_no_fake_product_gate() -> None:
    audit = build_workspace_window_section_readiness_audit()

    assert audit.dependency_gate_passed is True
    assert audit.p2_3_a_foundation_present is True
    assert audit.p2_3_b_semantics_present is True
    assert audit.p2_3_c_cross_surface_present is True
    assert audit.section_projection_present is True
    assert audit.binding_status_valid is True
    assert audit.docs_state_report_sync_present is True
    assert audit.coverage_matrix_present is True
    assert audit.exit_seal_present is True
    assert audit.no_fake_live is True
    assert audit.no_fake_trace_verified is True
    assert audit.no_release_scope is True
    assert audit.no_frontend_ui is True
    assert audit.no_browser_app is True
    assert audit.no_tauri_app is True
    assert audit.no_drag_drop is True
    assert audit.no_docking_ui is True
    assert audit.no_route_runtime is True
    assert audit.no_command_palette is True
    assert audit.no_layout_engine is True
    assert audit.no_conflict_resolver is True
    assert audit.no_permission_enforcement is True
    assert audit.no_storage_write is True
    assert audit.no_memory_write is True
    assert audit.no_trace_write is True
    assert audit.no_runtime_mutation is True
    assert audit.no_future_pack_started is True
    assert_p2_3_d_has_no_product_behavior(audit)
    assert json.loads(json.dumps(audit.to_canonical_dict()))


def test_p2_3_20_exit_seal_contract_scope_only() -> None:
    seal = build_workspace_window_section_seal()

    assert seal.section_id == "P2.3"
    assert seal.created_for_pack == "P2.3-D"
    assert seal.seal_status == WorkspaceWindowSectionSealStatus.SEALED_FOR_CONTRACT_SCOPE
    assert seal.seal_scope == "CONTRACT_SCOPE"
    assert seal.sealed_for_contract_scope is True
    assert seal.sealed_for_product_scope is False
    assert seal.sealed_for_release_scope is False
    assert seal.operator_testable_path
    assert seal.next_pack == "P2.4"
    assert seal.claims_live is False
    assert seal.claims_trace_verified is False
    assert_section_seal_is_contract_scope_only(seal)
    assert_exit_seal_is_not_release_scope(seal)
    assert_contract_demo_is_not_live(seal)
    assert json.loads(json.dumps(seal.to_canonical_dict()))


def test_p2_3_d_side_effect_proof_all_false() -> None:
    proof = build_p2_3_d_side_effect_proof()
    assert_p2_3_d_side_effects_all_false(proof)
    for field, value in proof.to_canonical_dict().items():
        assert value is False, field


def test_p2_3_d_result_serializes_and_preserves_boundaries() -> None:
    result = build_p2_3_d_workspace_window_section_result()

    assert result.pack_id == "P2.3-D"
    assert result.section_id == "P2.3"
    assert result.official_section_name == "Floating Windows / Workspace State"
    assert result.next_pack == "P2.4"
    assert result.canonical_surface_ids == CANONICAL_SURFACE_ORDER
    assert all(
        result.checkpoint_statuses[checkpoint_id] == "DONE"
        for checkpoint_id in P2_3_D_PACK_CHECKPOINT_IDS
    )
    assert result.section_projection.section_seal.sealed_for_contract_scope is True
    assert result.section_projection.starts_p2_4 is False
    assert result.section_projection.starts_p2_10 is False
    assert result.section_projection.starts_p2_13 is False
    assert result.surface_taxonomy_drift is True
    assert all(surface_id in CANONICAL_SURFACE_ORDER for surface_id in result.canonical_surface_ids)
    assert json.loads(serialize_p2_3_d_result(result))
