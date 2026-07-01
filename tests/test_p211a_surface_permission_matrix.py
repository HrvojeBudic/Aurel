from __future__ import annotations

import json

from agentic_runtime.aurel_shell.multi_client_foundation import ShellClientKind
from agentic_runtime.aurel_shell.surface_permission_matrix import (
    DISABLED_EXECUTION_ACTIONS,
    SAFE_PRE_EXECUTION_ACTIONS,
    P211APrerequisiteGateStatus,
    SurfacePermissionAction,
    SurfacePermissionLevel,
    build_p2_11_a_prerequisite_gate,
    build_p2_11_a_surface_permission_matrix_result,
    build_surface_permission_matrix,
    serialize_p2_11_a_result,
    surface_permission_entry_lookup,
)
from agentic_runtime.aurel_shell.surface_registry import CANONICAL_SURFACE_ORDER


def test_p211a_prerequisite_gate_consumes_p210e_and_blocks_missing_report() -> None:
    gate = build_p2_11_a_prerequisite_gate()
    missing = build_p2_11_a_prerequisite_gate(p210e_report_exists=False)

    assert gate.gate_status is P211APrerequisiteGateStatus.GATE_PASSED
    assert gate.p210e_report_found is True
    assert gate.p210e_report_indexed is True
    assert gate.p210e_proves_p210_multi_client_sealed is True
    assert gate.p210e_points_to_p211 is True
    assert gate.p212_not_started is True
    assert gate.blockers == ()

    assert missing.gate_status is P211APrerequisiteGateStatus.GATE_REPAIR_REQUIRED
    assert "P2.10-E report missing" in missing.blockers


def test_p211a_matrix_covers_all_clients_surfaces_and_actions() -> None:
    matrix = build_surface_permission_matrix()

    assert matrix.clients == (
        ShellClientKind.WEB,
        ShellClientKind.DESKTOP_TAURI,
        ShellClientKind.CLI,
        ShellClientKind.TUI,
        ShellClientKind.MOBILE_FOUNDATION,
    )
    assert matrix.surfaces == CANONICAL_SURFACE_ORDER
    assert matrix.actions == tuple(SurfacePermissionAction)
    assert matrix.summary.total_entries == 5 * 7 * 20
    assert matrix.missing_entries == ()
    assert matrix.inconsistencies == ()


def test_p211a_matrix_entries_are_deterministic_and_evidence_bound() -> None:
    matrix = build_surface_permission_matrix()
    web_preflight = surface_permission_entry_lookup(
        matrix,
        client_kind=ShellClientKind.WEB,
        surface_id="hq",
        permission_action=SurfacePermissionAction.REQUEST_COMMAND_PREFLIGHT,
    )
    cli_export = surface_permission_entry_lookup(
        matrix,
        client_kind=ShellClientKind.CLI,
        surface_id="corp",
        permission_action=SurfacePermissionAction.EXPORT_SURFACE_READ_MODEL,
    )

    assert web_preflight.permission_level is SurfacePermissionLevel.PREFLIGHT_ONLY
    assert any(ref.source_pack == "P2.VSLICE-A" for ref in web_preflight.evidence_refs)
    assert cli_export.permission_level is SurfacePermissionLevel.READ_ONLY
    assert cli_export.reason.value == "CLIENT_READ_ONLY"
    assert all(entry.entry_hash for entry in (web_preflight, cli_export))
    assert all(entry.evidence_refs for entry in matrix.entries)
    assert all(entry.limitations for entry in matrix.entries)


def test_p211a_result_serializes_deterministically_and_seals_only_p211a() -> None:
    result = build_p2_11_a_surface_permission_matrix_result()
    encoded_once = serialize_p2_11_a_result(result)
    encoded_twice = serialize_p2_11_a_result(result)
    payload = json.loads(encoded_once)

    assert encoded_once == encoded_twice
    assert payload["covered_pack"] == "P2.11-A"
    assert result.covered_pack == "P2.11-A"
    assert result.p211b_not_done is True
    assert result.p212_not_started is True
    assert set(result.permission_matrix.actions) == (
        set(SAFE_PRE_EXECUTION_ACTIONS) | set(DISABLED_EXECUTION_ACTIONS)
    )

