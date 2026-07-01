from __future__ import annotations

from agentic_runtime.aurel_shell.multi_client_demo_seal import (
    build_p2_10_e_multi_client_demo_seal_result,
    build_p2_10_no_overclaim_matrix,
)


def test_p210e_no_overclaim_matrix_has_required_boundaries() -> None:
    matrix = build_p2_10_no_overclaim_matrix()

    assert set(matrix.active_boundaries) == {
        "NO_FULL_LOCAL_APP_CLAIM",
        "NO_FULL_WEB_PRODUCT_CLAIM",
        "NO_FULL_DESKTOP_PRODUCT_CLAIM",
        "NO_FULL_CLI_TUI_PRODUCT_CLAIM",
        "NO_MOBILE_APP_CLAIM",
        "NO_SHELL_LIVE_CLAIM",
        "NO_COMMAND_EXECUTION_CLAIM",
        "NO_TOOL_EXECUTION_CLAIM",
        "NO_APPROVAL_EXECUTION_CLAIM",
        "NO_RUNTIME_CONTROL_CLAIM",
        "NO_SANDBOX_CONTROL_CLAIM",
        "NO_NATIVE_AUTHORITY_CLAIM",
        "NO_PRODUCTION_API_CLAIM",
        "NO_FULL_API_EVENT_BRIDGE_LIVE_CLAIM",
        "NO_P2_11_CLAIM",
        "NO_P2_FINAL_SEAL_CLAIM",
        "NO_P3_HANDOFF_CLAIM",
    }
    assert matrix.violations == ()


def test_p210e_no_scope_expansion_side_effects_are_false() -> None:
    result = build_p2_10_e_multi_client_demo_seal_result()
    proof = result.side_effect_proof

    assert proof.p2_11_implemented is False
    assert proof.p2_12_plus_implemented is False
    assert proof.p2_final_seal_claimed is False
    assert proof.p3_handoff_claimed is False
    assert proof.arbitrary_command_execution_implemented is False
    assert proof.tool_execution_implemented is False
    assert proof.approval_execution_implemented is False
    assert proof.runtime_control_implemented is False
    assert proof.sandbox_control_implemented is False
    assert proof.workflow_execution_implemented is False
    assert proof.agent_dispatch_implemented is False
    assert proof.memory_write_implemented is False
    assert proof.policy_mutation_implemented is False
    assert proof.identity_mutation_implemented is False
    assert proof.command_preflight_behavior_changed is False
    assert proof.p2_vslice_a_behavior_changed is False
    assert proof.policy_identity_sandbox_behavior_changed is False
    assert proof.shell_live_claimed is False
    assert proof.full_local_app_claimed is False
    assert proof.product_readiness_claimed is False
    assert proof.runnable_clients_claimed_without_validation is False


def test_p210e_completion_seal_is_not_final_p2_or_p3() -> None:
    result = build_p2_10_e_multi_client_demo_seal_result()

    assert result.completion_seal.p210_done is True
    assert result.completion_seal.next_pack == "P2.11"
    assert "final P2 seal" in result.completion_seal.not_sealed_as
    assert "P3 handoff" in result.completion_seal.not_sealed_as
    assert "Shell LIVE" in result.completion_seal.not_claimed
    assert "product readiness" in result.completion_seal.not_claimed
