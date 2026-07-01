"""Tests for P2.10-D CLI/TUI terminal parity matrix."""

from __future__ import annotations

from agentic_runtime.aurel_shell.multi_client_foundation import (
    ShellClientKind,
    ShellClientTruthLabel,
)
from agentic_runtime.aurel_shell.terminal_shell_client import (
    TerminalShellCapability,
    TerminalShellParityDimension,
    build_terminal_shell_parity_matrix,
)


def test_terminal_parity_matrix_covers_required_clients_and_dimensions():
    matrix = build_terminal_shell_parity_matrix()

    assert matrix.clients == (
        ShellClientKind.WEB,
        ShellClientKind.DESKTOP_TAURI,
        ShellClientKind.CLI,
        ShellClientKind.TUI,
        ShellClientKind.MOBILE_FOUNDATION,
    )
    assert set(matrix.dimensions) == set(TerminalShellParityDimension)
    assert len(matrix.entries) == len(matrix.clients) * len(matrix.dimensions)


def test_terminal_parity_means_same_truth_not_execution():
    matrix = build_terminal_shell_parity_matrix()

    assert "same Shell truth" in matrix.terminal_parity_summary
    assert "does not enable command execution" in matrix.terminal_parity_summary
    for entry in matrix.entries:
        if entry.client_kind is ShellClientKind.CLI:
            assert entry.truth_label in {
                ShellClientTruthLabel.READ_ONLY,
                ShellClientTruthLabel.PREFLIGHT_ONLY,
            }
        if entry.dimension is TerminalShellParityDimension.COMMAND_PREFLIGHT_STATUS_VISIBLE:
            assert entry.truth_label is ShellClientTruthLabel.PREFLIGHT_ONLY


def test_terminal_parity_matrix_exposes_execution_disabled_for_every_client():
    matrix = build_terminal_shell_parity_matrix()

    execution_entries = [
        entry
        for entry in matrix.entries
        if entry.dimension is TerminalShellParityDimension.EXECUTION_DISABLED
    ]
    assert len(execution_entries) == len(matrix.clients)
    assert all(entry.supported for entry in execution_entries)
    assert {
        TerminalShellCapability.EXECUTE_COMMAND.value,
        TerminalShellCapability.APPROVE_ACTION.value,
        TerminalShellCapability.RUN_TOOL.value,
        TerminalShellCapability.START_RUNTIME.value,
        TerminalShellCapability.STOP_RUNTIME.value,
        TerminalShellCapability.DISPATCH_AGENT.value,
        TerminalShellCapability.RUN_WORKFLOW.value,
        TerminalShellCapability.WRITE_MEMORY.value,
        TerminalShellCapability.MODIFY_POLICY.value,
        TerminalShellCapability.MUTATE_IDENTITY.value,
        TerminalShellCapability.TRIGGER_SANDBOX.value,
    } == set(matrix.execution_disabled_proof)


def test_tui_and_mobile_missing_json_export_are_honest_gaps():
    matrix = build_terminal_shell_parity_matrix()

    assert "TUI:JSON_EXPORT_AVAILABLE" in matrix.missing_parity
    assert "MOBILE_FOUNDATION:JSON_EXPORT_AVAILABLE" in matrix.missing_parity
    tui_json = next(
        entry
        for entry in matrix.entries
        if entry.client_kind is ShellClientKind.TUI
        and entry.dimension is TerminalShellParityDimension.JSON_EXPORT_AVAILABLE
    )
    assert tui_json.supported is False
    assert tui_json.truth_label is ShellClientTruthLabel.UNAVAILABLE


def test_parity_matrix_preserves_evidence_refs():
    matrix = build_terminal_shell_parity_matrix()

    assert "agent/reports/P2_10_A_MULTI_CLIENT_SHELL_FOUNDATION.md" in matrix.evidence_refs
    assert "agent/reports/P2_10_B_LOCAL_WEB_SHELL_SKELETON.md" in matrix.evidence_refs
    assert "agent/reports/P2_10_C_TAURI_DESKTOP_LOCAL_SHELL.md" in matrix.evidence_refs
