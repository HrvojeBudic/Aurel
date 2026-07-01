from __future__ import annotations

import json

from agentic_runtime.aurel_shell.surface_permission_inspection import (
    SurfacePermissionInspectionViewKind,
    build_surface_permission_cli_specs,
    build_surface_permission_shell_view_bindings,
    build_p2_11_c_surface_permission_inspection_result,
)
from tests.cli_helpers import run_cli


def test_p211c_cli_command_specs_are_read_only() -> None:
    specs = build_surface_permission_cli_specs()
    names = {spec.command_name for spec in specs}

    assert "shell permissions summary" in names
    assert "shell permissions export" in names
    for spec in specs:
        assert spec.read_only is True
        assert spec.source_read_model
        assert "command_execution" in spec.forbidden_side_effects
        assert any("read model" in item for item in spec.no_execution_boundaries)


def test_p211c_shell_view_bindings_are_contract_only() -> None:
    bindings = build_surface_permission_shell_view_bindings()
    panel_ids = {binding.panel_id for binding in bindings}

    assert "PermissionSummaryPanel" in panel_ids
    assert "PermissionSensitiveSurfacePanel" in panel_ids
    assert "PermissionNoOverclaimPanel" in panel_ids
    for binding in bindings:
        assert binding.read_only is True
        assert SurfacePermissionInspectionViewKind.SUMMARY in binding.supported_views
        assert "client_kind" in binding.supported_filters
        assert any("not Shell LIVE" in item for item in binding.limitations)


def test_p211c_result_includes_cli_specs_and_shell_bindings() -> None:
    result = build_p2_11_c_surface_permission_inspection_result()

    assert len(result.cli_command_specs) == 8
    assert len(result.shell_view_binding) == 7
    assert result.inspection_export.read_only is True
    assert result.inspection_export.deterministic is True
    assert result.inspection_export.json_safe is True


def test_shell_permissions_summary_json_is_read_only() -> None:
    proc = run_cli("shell", "permissions", "summary", "--json")

    assert proc.returncode == 0
    payload = json.loads(proc.stdout)
    assert payload["covered_pack"] == "P2.11-C"
    assert payload["inspection_is_enforcement"] is False
    assert payload["shell_live_claimed"] is False
    assert payload["next_pack"] == "P2.11-D"
    assert payload["p211d_not_done"] is True


def test_shell_permissions_show_client_filter() -> None:
    proc = run_cli(
        "shell",
        "permissions",
        "show",
        "--client",
        "WEB",
        "--json",
    )

    assert proc.returncode == 0
    payload = json.loads(proc.stdout)
    assert payload["matched_entry_count"] == 140
    assert all(entry["client_kind"] == "WEB" for entry in payload["matched_entries"])


def test_shell_permissions_sensitive_command() -> None:
    proc = run_cli("shell", "permissions", "sensitive", "--json")

    assert proc.returncode == 0
    payload = json.loads(proc.stdout)
    assert payload["matched_entry_count"] > 0
    assert all(
        view["surface_id"] in {"system", "settings", "ide"}
        for view in payload["surface_views"]
    )
