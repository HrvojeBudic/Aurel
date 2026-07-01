from __future__ import annotations

from agentic_runtime.aurel_shell.multi_client_foundation import ShellClientKind
from agentic_runtime.aurel_shell.surface_permission_matrix import (
    DISABLED_EXECUTION_ACTIONS,
    SurfacePermissionAction,
    SurfacePermissionLevel,
    build_p2_11_a_surface_permission_matrix_result,
    build_surface_permission_matrix,
)
from agentic_runtime.aurel_shell.surface_permission_projection import (
    build_p2_11_b_surface_permission_projection_result,
    build_surface_permission_read_model,
    project_permissions_by_action,
)


def test_p211b_disabled_execution_actions_remain_non_executable_in_projection() -> None:
    matrix = build_surface_permission_matrix()
    action_views = project_permissions_by_action(matrix)

    for view in action_views:
        if view.permission_action in DISABLED_EXECUTION_ACTIONS:
            assert not view.allowed_clients_surfaces
            assert not view.read_only_clients_surfaces
            assert not view.preflight_only_clients_surfaces


def test_p211b_preflight_only_never_becomes_execute_command_in_read_model() -> None:
    read_model = build_surface_permission_read_model()
    by_action = {view.permission_action: view for view in read_model.action_views}

    preflight = by_action[SurfacePermissionAction.REQUEST_COMMAND_PREFLIGHT]
    execute = by_action[SurfacePermissionAction.EXECUTE_COMMAND]

    assert preflight.preflight_only_clients_surfaces
    assert not execute.preflight_only_clients_surfaces
    assert execute.denied_clients_surfaces
    assert "PREFLIGHT_ONLY means governed preflight request only" in " ".join(
        preflight.limitations
    )


def test_p211b_allowed_projection_does_not_claim_final_authorization() -> None:
    read_model = build_surface_permission_read_model()

    assert any(
        "does not mean final authorization" in limitation
        for limitation in read_model.limitations
    )
    for view in read_model.client_views:
        assert any("not permission enforcement" in item for item in view.limitations)


def test_p211b_sensitive_surfaces_remain_conservative() -> None:
    read_model = build_surface_permission_read_model()
    execute_view = next(
        view
        for view in read_model.action_views
        if view.permission_action is SurfacePermissionAction.EXECUTE_COMMAND
    )
    sensitive_keys = {
        key
        for key in execute_view.denied_clients_surfaces
        if key.endswith(":system") or key.endswith(":settings") or key.endswith(":ide")
    }

    assert len(sensitive_keys) == 5 * 3


def test_p211b_side_effect_proof_keeps_enforcement_and_product_claims_false() -> None:
    result = build_p2_11_b_surface_permission_projection_result()
    proof = result.side_effect_proof

    assert proof.command_execution_implemented is False
    assert proof.permission_enforcement_implemented is False
    assert proof.full_policy_runtime_implemented is False
    assert proof.custos_enforcement_implemented is False
    assert proof.shell_live_claimed is False
    assert proof.product_readiness_claimed is False
    assert proof.p2_11_claimed_complete is False
    assert proof.p2_12_plus_implemented is False


def test_p211b_does_not_change_p211a_matrix_truth() -> None:
    p211a = build_p2_11_a_surface_permission_matrix_result()
    p211b = build_p2_11_b_surface_permission_projection_result()

    assert p211b.source_matrix_ref == p211a.permission_matrix.matrix_hash
    assert p211a.p211b_not_done is True
    for entry, proj in zip(
        p211a.permission_matrix.entries,
        p211b.read_model.entries,
        strict=True,
    ):
        assert proj.permission_level is entry.permission_level
        assert proj.source_entry_ref == entry.entry_hash


def test_p211b_cli_can_export_system_read_model_projection() -> None:
    read_model = build_surface_permission_read_model()
    cli_view = next(
        view for view in read_model.client_views if view.client_kind is ShellClientKind.CLI
    )

    assert "system" in cli_view.surfaces_readable
    export_view = next(
        view
        for view in read_model.action_views
        if view.permission_action is SurfacePermissionAction.EXPORT_SURFACE_READ_MODEL
    )
    cli_system_export = "CLI:system"
    assert cli_system_export in export_view.read_only_clients_surfaces
