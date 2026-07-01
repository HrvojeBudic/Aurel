from __future__ import annotations

from agentic_runtime.aurel_shell.surface_permission_inspection import (
    SurfacePermissionInspectionQuery,
    build_p2_11_c_surface_permission_inspection_result,
    build_surface_permission_inspection_no_execution_proof,
    inspect_surface_permissions,
)
from agentic_runtime.aurel_shell.surface_permission_matrix import (
    DISABLED_EXECUTION_ACTIONS,
    SurfacePermissionAction,
    SurfacePermissionLevel,
)
from agentic_runtime.aurel_shell.surface_permission_projection import (
    build_surface_permission_read_model,
)


def test_p211c_no_execution_proof_keeps_all_claims_false() -> None:
    proof = build_surface_permission_inspection_no_execution_proof()

    assert proof.command_execution is False
    assert proof.tool_execution is False
    assert proof.approval_execution is False
    assert proof.runtime_control is False
    assert proof.sandbox_control is False
    assert proof.memory_write is False
    assert proof.policy_mutation is False
    assert proof.identity_mutation is False
    assert proof.permission_enforcement is False
    assert proof.full_policy_runtime is False
    assert proof.custos_enforcement is False
    assert proof.shell_live_claim is False
    assert proof.product_readiness_claim is False
    assert proof.violations == ()


def test_p211c_inspection_does_not_upgrade_disabled_execution_actions() -> None:
    read_model = build_surface_permission_read_model()
    result = inspect_surface_permissions(read_model=read_model)

    for entry in result.matched_entries:
        if entry.permission_action in DISABLED_EXECUTION_ACTIONS:
            assert entry.permission_level not in {
                SurfacePermissionLevel.ALLOWED,
                SurfacePermissionLevel.PREFLIGHT_ONLY,
                SurfacePermissionLevel.READ_ONLY,
            }


def test_p211c_sensitive_surface_inspection_denies_execution() -> None:
    result = inspect_surface_permissions(
        SurfacePermissionInspectionQuery(sensitive_only=True)
    )
    execute_entries = [
        entry
        for entry in result.matched_entries
        if entry.permission_action is SurfacePermissionAction.EXECUTE_COMMAND
    ]

    assert execute_entries
    assert all(
        entry.permission_level is SurfacePermissionLevel.DENIED
        for entry in execute_entries
    )


def test_p211c_side_effect_proof_keeps_scope_boundaries_false() -> None:
    result = build_p2_11_c_surface_permission_inspection_result()

    assert result.p211d_not_done is True
    assert result.p212_not_started is True
    assert result.no_execution_proof.permission_enforcement is False
    assert result.no_execution_proof.shell_live_claim is False
    assert result.no_execution_proof.product_readiness_claim is False
    assert any(
        "not complete" in item for item in result.handoff.inspection_summary
    )


def test_p211c_no_evidence_entries_remain_visible_without_upgrade() -> None:
    from agentic_runtime.aurel_shell.surface_permission_matrix import (
        SurfacePermissionReason,
    )

    result = inspect_surface_permissions(
        SurfacePermissionInspectionQuery(no_evidence_only=True)
    )

    if result.matched_entries:
        for entry in result.matched_entries:
            assert (
                entry.reason is SurfacePermissionReason.NO_EVIDENCE
                or not entry.evidence_refs
            )
            assert entry.permission_level not in {
                SurfacePermissionLevel.ALLOWED,
            }
