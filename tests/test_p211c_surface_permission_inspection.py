from __future__ import annotations

from agentic_runtime.aurel_shell.multi_client_foundation import ShellClientKind
from agentic_runtime.aurel_shell.surface_permission_inspection import (
    P211CPrerequisiteGateStatus,
    P2_11_B_REPORT_PATH,
    SurfacePermissionInspectionViewKind,
    build_p2_11_c_prerequisite_gate,
    build_p2_11_c_surface_permission_inspection_result,
    inspect_surface_permissions,
    render_surface_permission_inspection,
)
from agentic_runtime.aurel_shell.surface_permission_matrix import (
    SurfacePermissionAction,
    SurfacePermissionLevel,
)
from agentic_runtime.aurel_shell.surface_permission_projection import (
    build_surface_permission_read_model,
)
from agentic_runtime.aurel_shell.surface_registry import CANONICAL_SURFACE_ORDER


def test_p211c_prerequisite_gate_consumes_p211b_and_blocks_missing_report() -> None:
    gate = build_p2_11_c_prerequisite_gate()
    missing = build_p2_11_c_prerequisite_gate(p211b_report_exists=False)

    assert gate.gate_status is P211CPrerequisiteGateStatus.GATE_PASSED
    assert gate.p211b_report_found is True
    assert gate.p211b_report_path == P2_11_B_REPORT_PATH
    assert gate.p211b_report_indexed is True
    assert gate.p211b_proves_projection_read_model_done is True
    assert gate.p211b_points_to_p211c is True
    assert gate.p212_not_started is True
    assert gate.blockers == ()

    assert missing.gate_status is P211CPrerequisiteGateStatus.GATE_REPAIR_REQUIRED
    assert "P2.11-B report missing" in missing.blockers


def test_p211c_inspection_consumes_p211b_read_model_without_recomputing_logic() -> None:
    read_model = build_surface_permission_read_model()
    result = inspect_surface_permissions(read_model=read_model)

    assert len(result.matched_entries) == 700
    assert len(result.matched_client_views) == 5
    assert len(result.matched_surface_views) == 7
    assert len(result.matched_action_views) == 20
    assert result.matched_entries[0].source_matrix_ref == read_model.source_matrix_ref
    assert all(entry.evidence_refs for entry in result.matched_entries)


def test_p211c_inspection_supports_all_clients_and_surfaces() -> None:
    read_model = build_surface_permission_read_model()
    result = inspect_surface_permissions(read_model=read_model)

    clients = {entry.client_kind for entry in result.matched_entries}
    surfaces = {entry.surface_id for entry in result.matched_entries}

    assert clients == set(ShellClientKind)
    assert surfaces == set(CANONICAL_SURFACE_ORDER)


def test_p211c_inspection_views_cover_required_formats() -> None:
    result = inspect_surface_permissions()
    for kind in SurfacePermissionInspectionViewKind:
        view = render_surface_permission_inspection(result, view_kind=kind)
        assert view.view_kind is kind
        assert view.rows
        assert view.truth_notes
        assert "not enforcement" in " ".join(view.truth_notes)


def test_p211c_result_declares_inspection_contract_and_next_pack() -> None:
    result = build_p2_11_c_surface_permission_inspection_result()

    assert result.covered_pack == "P2.11-C"
    assert "SurfacePermissionInspectionQuery" in result.inspection_contract
    assert result.handoff.next_pack == "P2.11-D"
    assert result.p211d_not_done is True
    assert result.p212_not_started is True
    assert len(result.cli_command_specs) == 8
    assert len(result.shell_view_binding) == 7


def test_p211c_preflight_only_entries_remain_non_execution_in_inspection() -> None:
    from agentic_runtime.aurel_shell.surface_permission_inspection import (
        SurfacePermissionInspectionQuery,
    )

    result = inspect_surface_permissions(
        SurfacePermissionInspectionQuery(
            permission_action=SurfacePermissionAction.REQUEST_COMMAND_PREFLIGHT,
            preflight_only_only=True,
        )
    )

    assert result.matched_entries
    assert all(
        entry.permission_level is SurfacePermissionLevel.PREFLIGHT_ONLY
        for entry in result.matched_entries
    )
    assert any("non-execution" in item for item in result.limitations)
