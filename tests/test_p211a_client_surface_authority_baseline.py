from __future__ import annotations

from agentic_runtime.aurel_shell.multi_client_foundation import ShellClientKind
from agentic_runtime.aurel_shell.surface_permission_matrix import (
    SurfacePermissionAction,
    SurfacePermissionLevel,
    build_client_surface_authority_baseline,
    build_surface_permission_matrix,
    surface_permission_display_name,
    surface_permission_entry_lookup,
)
from agentic_runtime.aurel_shell.surface_registry import CANONICAL_SURFACE_ORDER


def test_p211a_authority_baseline_includes_p210_clients_and_seven_surfaces() -> None:
    baseline = build_client_surface_authority_baseline()

    assert baseline.clients == (
        ShellClientKind.WEB,
        ShellClientKind.DESKTOP_TAURI,
        ShellClientKind.CLI,
        ShellClientKind.TUI,
        ShellClientKind.MOBILE_FOUNDATION,
    )
    assert baseline.surfaces == CANONICAL_SURFACE_ORDER
    assert tuple(surface_permission_display_name(surface) for surface in baseline.surfaces) == (
        "Aurel CRO",
        "HQ",
        "CORP",
        "HUB",
        "IDE",
        "SYSTEM",
        "Settings",
    )
    assert baseline.permission_actions == tuple(SurfacePermissionAction)
    assert baseline.sensitive_surfaces == ("system", "settings", "ide")


def test_p211a_authority_baseline_records_rules_and_evidence_refs() -> None:
    baseline = build_client_surface_authority_baseline()

    assert any("PREFLIGHT_ONLY" in rule for rule in baseline.default_rules)
    assert any("CLI uses P2.10-D" in rule for rule in baseline.client_specific_rules)
    assert any("sensitive surfaces" in rule for rule in baseline.surface_specific_rules)
    assert {ref.source_pack for ref in baseline.evidence_refs} >= {
        "P2.10-A",
        "P2.10-B",
        "P2.10-C",
        "P2.10-D",
        "P2.10-E",
        "P2.VSLICE-A",
    }


def test_p211a_mobile_foundation_remains_contract_or_future_gated() -> None:
    matrix = build_surface_permission_matrix()
    mobile_levels = {
        entry.permission_level
        for entry in matrix.entries
        if entry.client_kind is ShellClientKind.MOBILE_FOUNDATION
    }

    assert mobile_levels <= {
        SurfacePermissionLevel.CONTRACT_ONLY,
        SurfacePermissionLevel.FUTURE_GATED,
        SurfacePermissionLevel.DENIED,
    }
    mobile_preflight = surface_permission_entry_lookup(
        matrix,
        client_kind=ShellClientKind.MOBILE_FOUNDATION,
        surface_id="hq",
        permission_action=SurfacePermissionAction.REQUEST_COMMAND_PREFLIGHT,
    )
    assert mobile_preflight.permission_level is SurfacePermissionLevel.FUTURE_GATED


def test_p211a_cli_open_focus_unavailable_but_read_export_allowed_read_only() -> None:
    matrix = build_surface_permission_matrix()
    cli_open = surface_permission_entry_lookup(
        matrix,
        client_kind=ShellClientKind.CLI,
        surface_id="hq",
        permission_action=SurfacePermissionAction.OPEN_SURFACE,
    )
    cli_read = surface_permission_entry_lookup(
        matrix,
        client_kind=ShellClientKind.CLI,
        surface_id="hq",
        permission_action=SurfacePermissionAction.READ_SURFACE_STATE,
    )
    cli_export = surface_permission_entry_lookup(
        matrix,
        client_kind=ShellClientKind.CLI,
        surface_id="hq",
        permission_action=SurfacePermissionAction.EXPORT_SURFACE_READ_MODEL,
    )

    assert cli_open.permission_level is SurfacePermissionLevel.UNAVAILABLE
    assert cli_read.permission_level is SurfacePermissionLevel.READ_ONLY
    assert cli_export.permission_level is SurfacePermissionLevel.READ_ONLY

