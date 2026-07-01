from __future__ import annotations

import json

from agentic_runtime.aurel_shell.multi_client_foundation import ShellClientKind
from agentic_runtime.aurel_shell.surface_permission_matrix import (
    DISABLED_EXECUTION_ACTIONS,
    SAFE_PRE_EXECUTION_ACTIONS,
    SurfacePermissionAction,
    SurfacePermissionLevel,
    build_surface_permission_matrix,
)
from agentic_runtime.aurel_shell.surface_permission_projection import (
    P2_11_C_NEXT_PACK,
    build_surface_permission_evidence_views,
    build_surface_permission_no_overclaim_view,
    build_surface_permission_read_model,
    serialize_surface_permission_read_model,
)
from agentic_runtime.aurel_shell.surface_registry import CANONICAL_SURFACE_ORDER


def test_p211b_read_model_consumes_p211a_matrix_hash() -> None:
    matrix = build_surface_permission_matrix()
    read_model = build_surface_permission_read_model(matrix)

    assert read_model.source_matrix_ref == matrix.matrix_hash
    assert read_model.clients == matrix.clients
    assert read_model.surfaces == matrix.surfaces
    assert read_model.safe_actions == SAFE_PRE_EXECUTION_ACTIONS
    assert read_model.disabled_actions == DISABLED_EXECUTION_ACTIONS


def test_p211b_read_model_includes_level_summaries_and_boundaries() -> None:
    matrix = build_surface_permission_matrix()
    read_model = build_surface_permission_read_model(matrix)

    assert read_model.preflight_only_summary
    assert read_model.denied_summary
    assert read_model.contract_only_summary
    assert read_model.no_overclaim_boundaries
    assert read_model.next_pack_pointer == P2_11_C_NEXT_PACK
    assert all(
        key.startswith(("WEB:", "CLI:", "TUI:", "DESKTOP_TAURI:", "MOBILE_FOUNDATION:"))
        for key in read_model.preflight_only_summary
    )


def test_p211b_evidence_views_track_supported_entries() -> None:
    matrix = build_surface_permission_matrix()
    views = build_surface_permission_evidence_views(matrix)

    assert len(views) == len(matrix.evidence_refs)
    assert all(view.entries_supported for view in views)
    assert all(view.source_report for view in views)


def test_p211b_no_overclaim_view_has_no_violations() -> None:
    matrix = build_surface_permission_matrix()
    view = build_surface_permission_no_overclaim_view(matrix)

    assert view.boundaries
    assert view.active_boundaries == view.boundaries
    assert view.violations == ()


def test_p211b_serialization_is_json_safe_and_deterministic() -> None:
    read_model = build_surface_permission_read_model()
    once = serialize_surface_permission_read_model(read_model)
    twice = serialize_surface_permission_read_model(read_model)

    assert once == twice
    parsed = json.loads(once)
    assert parsed["clients"]
    assert parsed["surfaces"] == list(CANONICAL_SURFACE_ORDER)
    assert "projection is not enforcement" in " ".join(parsed["limitations"])


def test_p211b_sensitive_surface_views_flag_system_settings_ide() -> None:
    read_model = build_surface_permission_read_model()
    surface_ids = {view.surface_id for view in read_model.sensitive_surface_views}

    assert surface_ids == {"system", "settings", "ide"}
    for view in read_model.sensitive_surface_views:
        assert view.sensitive_surface_flag is True
        assert ShellClientKind.WEB in view.clients_with_visibility


def test_p211b_action_views_cover_disabled_execution_actions() -> None:
    read_model = build_surface_permission_read_model()
    by_action = {view.permission_action: view for view in read_model.action_views}

    execute = by_action[SurfacePermissionAction.EXECUTE_COMMAND]
    assert execute.denied_clients_surfaces
    assert not execute.allowed_clients_surfaces
    assert not execute.preflight_only_clients_surfaces

    for action in DISABLED_EXECUTION_ACTIONS:
        view = by_action[action]
        assert view.permission_action is action
        assert not view.allowed_clients_surfaces
