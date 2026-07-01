from __future__ import annotations

from agentic_runtime.aurel_shell.multi_client_foundation import ShellClientKind
from agentic_runtime.aurel_shell.surface_permission_matrix import (
    DISABLED_EXECUTION_ACTIONS,
    SurfacePermissionAction,
    SurfacePermissionLevel,
    build_p2_11_a_surface_permission_matrix_result,
    build_surface_permission_matrix,
    surface_permission_entry_lookup,
)


def test_p211a_disabled_execution_actions_are_never_allowed() -> None:
    matrix = build_surface_permission_matrix()

    for entry in matrix.entries:
        if entry.permission_action in DISABLED_EXECUTION_ACTIONS:
            assert entry.permission_level in {
                SurfacePermissionLevel.DENIED,
                SurfacePermissionLevel.UNAVAILABLE,
                SurfacePermissionLevel.FUTURE_GATED,
            }
            assert entry.permission_level is not SurfacePermissionLevel.ALLOWED
            assert entry.permission_level is not SurfacePermissionLevel.PREFLIGHT_ONLY


def test_p211a_preflight_only_never_becomes_execute_command() -> None:
    matrix = build_surface_permission_matrix()
    execute = surface_permission_entry_lookup(
        matrix,
        client_kind=ShellClientKind.WEB,
        surface_id="hq",
        permission_action=SurfacePermissionAction.EXECUTE_COMMAND,
    )
    preflight = surface_permission_entry_lookup(
        matrix,
        client_kind=ShellClientKind.WEB,
        surface_id="hq",
        permission_action=SurfacePermissionAction.REQUEST_COMMAND_PREFLIGHT,
    )

    assert preflight.permission_level is SurfacePermissionLevel.PREFLIGHT_ONLY
    assert execute.permission_level is SurfacePermissionLevel.DENIED
    assert "not command execution" in " ".join(preflight.limitations)
    assert "not implemented" in " ".join(execute.limitations)


def test_p211a_sensitive_surfaces_keep_execution_and_mutation_denied() -> None:
    matrix = build_surface_permission_matrix()
    sensitive_actions = {
        SurfacePermissionAction.EXECUTE_COMMAND,
        SurfacePermissionAction.START_RUNTIME,
        SurfacePermissionAction.STOP_RUNTIME,
        SurfacePermissionAction.TRIGGER_SANDBOX,
        SurfacePermissionAction.WRITE_MEMORY,
        SurfacePermissionAction.MODIFY_POLICY,
        SurfacePermissionAction.MUTATE_IDENTITY,
        SurfacePermissionAction.RUN_TOOL,
        SurfacePermissionAction.APPROVE_ACTION,
    }

    for surface_id in ("system", "settings", "ide"):
        for action in sensitive_actions:
            entry = surface_permission_entry_lookup(
                matrix,
                client_kind=ShellClientKind.WEB,
                surface_id=surface_id,
                permission_action=action,
            )
            assert entry.permission_level is SurfacePermissionLevel.DENIED
            assert any("sensitive surface" in item for item in entry.limitations)


def test_p211a_side_effect_proof_keeps_runtime_and_product_claims_false() -> None:
    result = build_p2_11_a_surface_permission_matrix_result()
    proof = result.side_effect_proof

    assert proof.command_execution_implemented is False
    assert proof.tool_execution_implemented is False
    assert proof.approval_execution_implemented is False
    assert proof.runtime_control_implemented is False
    assert proof.sandbox_control_implemented is False
    assert proof.memory_write_implemented is False
    assert proof.policy_mutation_implemented is False
    assert proof.identity_mutation_implemented is False
    assert proof.full_policy_runtime_implemented is False
    assert proof.custos_enforcement_implemented is False
    assert proof.shell_live_claimed is False
    assert proof.product_readiness_claimed is False

