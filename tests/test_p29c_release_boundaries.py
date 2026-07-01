"""Tests for P2.9-C release blockers and no-release boundaries."""

from __future__ import annotations

from agentic_runtime.aurel_shell.shell_exit_finalization import (
    ShellExitBlockerSeverity,
    ShellExitBoundaryType,
    assert_p2_9_c_blocks_p2_10,
    assert_p2_9_c_handoff_points_to_p2_9_d,
    assert_p2_9_c_no_scope_expansion,
    assert_p2_vslice_a_remains_preflight_in_p29c,
    build_p2_9_c_shell_exit_finalization_result,
    build_shell_exit_no_release_boundaries,
    build_shell_exit_release_blockers,
)
from agentic_runtime.aurel_shell.shell_exit_readiness import ShellExitTruthLabel


def test_release_blocker_matrix_blocks_p2_10_while_p2_9_d_not_done() -> None:
    blockers = build_shell_exit_release_blockers()
    by_id = {blocker.blocker_id: blocker for blocker in blockers}
    assert by_id["p2_9_d_not_done"].severity is ShellExitBlockerSeverity.BLOCKS_P2_10
    assert by_id["p2_9_d_not_done"].cleared is False
    assert "P2.9-D" in by_id["p2_9_d_not_done"].clearance_requirement
    assert by_id["p2_10_not_started"].cleared is False
    assert any(block == "P2.10 start" for block in by_id["p2_9_d_not_done"].blocks)


def test_release_blockers_preserve_unavailable_runtime_and_sandbox_truth() -> None:
    blockers = build_shell_exit_release_blockers()
    by_id = {blocker.blocker_id: blocker for blocker in blockers}
    assert by_id["command_execution_unavailable"].severity is ShellExitBlockerSeverity.BLOCKS_COMMAND_EXECUTION
    assert by_id["shell_ui_unavailable"].severity is ShellExitBlockerSeverity.BLOCKS_PRODUCT_RELEASE
    assert by_id["safe_sandbox_unavailable"].severity is ShellExitBlockerSeverity.BLOCKS_LIVE
    assert by_id["safe_sandbox_unavailable"].evidence_refs[0].truth_label is ShellExitTruthLabel.UNAVAILABLE
    assert by_id["api_event_bridge_not_live"].cleared is False
    assert by_id["full_suite_not_run"].cleared is False
    assert by_id["coverage_not_run"].cleared is False


def test_no_release_boundaries_prevent_live_product_execution_and_p2_10_claims() -> None:
    boundaries = build_shell_exit_no_release_boundaries()
    by_type = {boundary.boundary_type: boundary for boundary in boundaries}
    assert by_type[ShellExitBoundaryType.NO_P2_10_START].active is True
    assert by_type[ShellExitBoundaryType.NO_SHELL_LIVE].forbidden_claim == "Shell LIVE"
    assert by_type[ShellExitBoundaryType.NO_COMMAND_EXECUTION].forbidden_claim == "arbitrary command execution"
    assert by_type[ShellExitBoundaryType.NO_PRODUCT_UI_RELEASE].forbidden_claim == "full Shell product UI"
    assert by_type[ShellExitBoundaryType.NO_SAFE_SANDBOX_CLAIM].forbidden_claim == "safe sandbox"
    assert by_type[ShellExitBoundaryType.NO_FULL_SUITE_CLAIM].active is True
    assert by_type[ShellExitBoundaryType.NO_COVERAGE_CLAIM].active is True


def test_result_assertions_keep_p2_10_blocked_and_scope_closed() -> None:
    result = build_p2_9_c_shell_exit_finalization_result()
    assert_p2_9_c_blocks_p2_10(result)
    assert_p2_9_c_handoff_points_to_p2_9_d(result)
    assert_p2_vslice_a_remains_preflight_in_p29c(result)
    assert_p2_9_c_no_scope_expansion(result)
    assert result.p29d_handoff.p210_allowed is False
    assert result.p29d_handoff.next_pack == "P2.9-D"
