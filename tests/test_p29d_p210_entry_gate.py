"""Tests for the P2.9-D P2.10 entry gate."""

from __future__ import annotations

from agentic_runtime.aurel_shell.shell_exit_final_seal import (
    P2_9_D_NEXT_PACK_IF_GATE_PASSES,
    P2_9_D_REPAIR_PACK,
    ShellExitP210GateStatus,
    assert_p210_gate_decision_consistent,
    assert_p210_gate_handoff_only,
    build_p2_9_d_shell_exit_final_seal_result,
    build_shell_exit_p210_entry_gate,
    build_shell_exit_p29_seal_aggregate,
)


def _conditions(gate) -> dict[str, bool]:
    return dict(gate.condition_results)


def test_p210_gate_allows_only_handoff_pointer_when_conditions_pass() -> None:
    result = build_p2_9_d_shell_exit_final_seal_result()
    gate = result.p210_entry_gate
    assert gate.allowed is True
    assert gate.gate_status is ShellExitP210GateStatus.P210_HANDOFF_ALLOWED
    assert gate.p210_handoff_only is True
    assert gate.p210_implementation_started is False
    assert result.p210_gate_decision.allowed_next_pointer == P2_9_D_NEXT_PACK_IF_GATE_PASSES
    assert result.p210_gate_decision.not_implementation is True
    assert result.handoff_pointer.next_pack == P2_9_D_NEXT_PACK_IF_GATE_PASSES
    assert result.handoff_pointer.p210_allowed is True
    assert result.handoff_pointer.p210_started is False
    assert_p210_gate_handoff_only(result)
    assert_p210_gate_decision_consistent(result)


def test_p210_gate_blocks_when_p2_9_d_is_incomplete() -> None:
    aggregate = build_shell_exit_p29_seal_aggregate(p29d_done=False)
    gate = build_shell_exit_p210_entry_gate(aggregate)
    conditions = _conditions(gate)
    assert conditions["P2.9 complete"] is False
    assert conditions["P2.9-D done"] is False
    assert gate.allowed is False
    assert gate.gate_status is ShellExitP210GateStatus.P210_REPAIR_REQUIRED
    assert "P2.9 complete" in gate.blockers
    assert "P2.9-D done" in gate.blockers


def test_p210_gate_blocks_if_p2_10_already_started() -> None:
    result = build_p2_9_d_shell_exit_final_seal_result(p210_started=True)
    gate = result.p210_entry_gate
    assert gate.allowed is False
    assert gate.p210_implementation_started is True
    assert "P2.10 not started" in gate.blockers
    assert result.p210_gate_decision.allowed_next_pointer == ""
    assert result.p210_gate_decision.repair_pointer == P2_9_D_REPAIR_PACK
    assert result.handoff_pointer.next_pack == P2_9_D_REPAIR_PACK
    assert result.handoff_pointer.p210_allowed is False
    assert result.handoff_pointer.p210_started is False
    assert_p210_gate_decision_consistent(result)


def test_p210_gate_blocks_overclaim_dimensions() -> None:
    aggregate = build_shell_exit_p29_seal_aggregate()
    gate = build_shell_exit_p210_entry_gate(
        aggregate,
        no_shell_live_overclaim=False,
        no_command_execution_overclaim=False,
        no_product_ui_overclaim=False,
        safe_sandbox_not_claimed_if_unavailable=False,
        p2_vslice_a_remains_preflight_only=False,
        full_suite_coverage_not_claimed_unless_run=False,
        state_report_index_clean=False,
        final_git_clean=False,
    )
    assert gate.allowed is False
    assert "no Shell LIVE overclaim" in gate.blockers
    assert "no command execution overclaim" in gate.blockers
    assert "no product UI overclaim" in gate.blockers
    assert "safe sandbox not claimed if unavailable" in gate.blockers
    assert "P2.VSLICE-A remains PREFLIGHT_ONLY" in gate.blockers
    assert "full suite/coverage not claimed unless run" in gate.blockers
    assert "state/report index clean" in gate.blockers
    assert "final git clean" in gate.blockers
