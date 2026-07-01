from __future__ import annotations

import json

from agentic_runtime.aurel_shell.multi_client_foundation import ShellClientKind
from agentic_runtime.aurel_shell.surface_permission_matrix import (
    P2_11_A_REPORT_PATH,
    SurfacePermissionAction,
    SurfacePermissionLevel,
    build_surface_permission_matrix,
)
from agentic_runtime.aurel_shell.surface_permission_projection import (
    P211BPrerequisiteGateStatus,
    SurfacePermissionProjectionKind,
    build_p2_11_b_prerequisite_gate,
    build_p2_11_b_surface_permission_projection_result,
    build_surface_permission_read_model,
    project_permissions_by_action,
    project_permissions_by_client,
    project_permissions_by_surface,
    serialize_surface_permission_read_model,
)
from agentic_runtime.aurel_shell.surface_registry import CANONICAL_SURFACE_ORDER


def test_p211b_prerequisite_gate_consumes_p211a_and_blocks_missing_report() -> None:
    gate = build_p2_11_b_prerequisite_gate()
    missing = build_p2_11_b_prerequisite_gate(p211a_report_exists=False)

    assert gate.gate_status is P211BPrerequisiteGateStatus.GATE_PASSED
    assert gate.p211a_report_found is True
    assert gate.p211a_report_path == P2_11_A_REPORT_PATH
    assert gate.p211a_report_indexed is True
    assert gate.p211a_proves_matrix_foundation_done is True
    assert gate.p211a_points_to_p211b is True
    assert gate.p212_not_started is True
    assert gate.blockers == ()

    assert missing.gate_status is P211BPrerequisiteGateStatus.GATE_REPAIR_REQUIRED
    assert "P2.11-A report missing" in missing.blockers


def test_p211b_projects_all_clients_surfaces_and_actions() -> None:
    matrix = build_surface_permission_matrix()
    read_model = build_surface_permission_read_model(matrix)

    assert read_model.clients == matrix.clients
    assert read_model.surfaces == CANONICAL_SURFACE_ORDER
    assert len(read_model.client_views) == 5
    assert len(read_model.surface_views) == 7
    assert len(read_model.action_views) == 20
    assert len(read_model.entries) == 700
    assert len(read_model.sensitive_surface_views) == 3


def test_p211b_client_views_preserve_run_modes_and_surface_sets() -> None:
    read_model = build_surface_permission_read_model()
    by_client = {view.client_kind: view for view in read_model.client_views}

    assert by_client[ShellClientKind.WEB].run_mode == "WEB_DEV_RUNNABLE"
    assert by_client[ShellClientKind.CLI].run_mode == "CLI_READ_ONLY"
    assert by_client[ShellClientKind.TUI].run_mode == "TUI_CONTRACT_ONLY"
    assert len(by_client[ShellClientKind.WEB].surfaces_visible) == 7
    assert by_client[ShellClientKind.CLI].unavailable_surfaces == ()
    assert by_client[ShellClientKind.CLI].surfaces_openable == ()
    assert "hq" in by_client[ShellClientKind.CLI].surfaces_readable
    assert "hq" in by_client[ShellClientKind.WEB].preflight_available_surfaces


def test_p211b_projection_entries_preserve_matrix_truth() -> None:
    matrix = build_surface_permission_matrix()
    read_model = build_surface_permission_read_model(matrix)

    assert all(
        entry.projection_kind is SurfacePermissionProjectionKind.FULL_MATRIX
        for entry in read_model.entries
    )
    assert all(entry.source_matrix_ref == matrix.matrix_hash for entry in read_model.entries)
    assert all(entry.evidence_refs for entry in read_model.entries)
    assert all(entry.limitations for entry in read_model.entries)


def test_p211b_projection_helpers_match_read_model() -> None:
    matrix = build_surface_permission_matrix()
    read_model = build_surface_permission_read_model(matrix)

    assert project_permissions_by_client(matrix) == read_model.client_views
    assert project_permissions_by_surface(matrix) == read_model.surface_views
    assert project_permissions_by_action(matrix) == read_model.action_views


def test_p211b_result_serializes_deterministically() -> None:
    result = build_p2_11_b_surface_permission_projection_result()
    encoded_once = serialize_surface_permission_read_model(result.read_model)
    encoded_twice = serialize_surface_permission_read_model(result.read_model)

    assert encoded_once == encoded_twice
    parsed = json.loads(encoded_once)
    assert parsed["next_pack_pointer"] == "P2.11-C"
    assert parsed["source_matrix_ref"] == result.source_matrix_ref
