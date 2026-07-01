"""Tests for P2.10-D terminal Shell client contract/read model."""

from __future__ import annotations

import json

from agentic_runtime.aurel_shell.multi_client_foundation import (
    ShellClientKind,
    ShellClientTruthLabel,
    build_shell_client_state,
)
from agentic_runtime.aurel_shell.terminal_shell_client import (
    P2_10_D_NEXT_PACK,
    P2_10_D_REPORT_PATH,
    P210DPrerequisiteGateStatus,
    TerminalShellCapability,
    TerminalShellCapabilityStatus,
    TerminalShellClientKind,
    TerminalShellRunMode,
    build_p2_10_d_prerequisite_gate,
    build_p2_10_d_terminal_shell_result,
    build_terminal_shell_client_contract,
    build_terminal_shell_read_model,
    serialize_terminal_shell_read_model,
)


def test_p210d_prerequisite_gate_passes_from_p210c_report():
    gate = build_p2_10_d_prerequisite_gate()

    assert gate.gate_status is P210DPrerequisiteGateStatus.GATE_PASSED
    assert gate.p210c_report_found is True
    assert gate.p210c_report_path.endswith("P2_10_C_TAURI_DESKTOP_LOCAL_SHELL.md")
    assert gate.p210c_report_indexed is True
    assert gate.p210c_proves_desktop_wrapper_done is True
    assert gate.p210c_points_to_p210d is True
    assert gate.p210e_not_started is True
    assert gate.blockers == ()


def test_p210d_prerequisite_gate_blocks_missing_report():
    gate = build_p2_10_d_prerequisite_gate(p210c_report_exists=False)

    assert gate.gate_status is P210DPrerequisiteGateStatus.GATE_REPAIR_REQUIRED
    assert "P2.10-C report missing" in gate.blockers


def test_terminal_client_contract_is_read_only_and_source_bound():
    contract = build_terminal_shell_client_contract()

    assert contract.client_kind is TerminalShellClientKind.CLI
    assert "multi_client_foundation.py:ShellClientState" in contract.source_shell_state_ref
    assert contract.source_web_read_model_ref.endswith("web-shell-read-model.json")
    assert contract.source_desktop_contract_ref.endswith("desktop-shell-read-model.json")
    assert "shell status" in contract.available_terminal_views
    assert "shell export-json" in contract.available_terminal_views
    assert contract.next_pack == P2_10_D_NEXT_PACK
    assert ShellClientTruthLabel.LIVE not in contract.truth_labels

    read_only = {entry.capability: entry.status for entry in contract.read_only_capabilities}
    assert read_only[TerminalShellCapability.VIEW_SHELL_STATUS] is (
        TerminalShellCapabilityStatus.READ_ONLY_ALLOWED
    )
    assert read_only[TerminalShellCapability.EXPORT_JSON] is (
        TerminalShellCapabilityStatus.READ_ONLY_ALLOWED
    )

    disabled = {
        entry.capability: entry.status for entry in contract.disabled_execution_capabilities
    }
    assert disabled[TerminalShellCapability.EXECUTE_COMMAND] is (
        TerminalShellCapabilityStatus.DISABLED
    )
    assert disabled[TerminalShellCapability.RUN_TOOL] is TerminalShellCapabilityStatus.DISABLED
    assert disabled[TerminalShellCapability.START_RUNTIME] is (
        TerminalShellCapabilityStatus.DISABLED
    )
    assert disabled[TerminalShellCapability.TRIGGER_SANDBOX] is (
        TerminalShellCapabilityStatus.DISABLED
    )


def test_terminal_read_model_derives_from_p210a_cli_state():
    read_model = build_terminal_shell_read_model()
    cli_state = build_shell_client_state(ShellClientKind.CLI)

    assert read_model.source_shell_state_hash == cli_state.state_hash
    assert set(read_model.available_surfaces) == set(cli_state.available_surfaces)
    assert len(read_model.surface_availability) == 7
    assert read_model.terminal_client_status == "READ_ONLY"
    assert read_model.p2_vslice_status is ShellClientTruthLabel.PREFLIGHT_ONLY
    assert read_model.execution_disabled is True
    assert read_model.json_export_available is True
    assert read_model.next_pack_pointer == "P2.10-E"
    assert TerminalShellRunMode.CLI_READ_ONLY in read_model.local_run_modes
    assert TerminalShellRunMode.TERMINAL_JSON_EXPORT in read_model.local_run_modes


def test_terminal_read_model_preserves_truth_labels_and_evidence_refs():
    read_model = build_terminal_shell_read_model()

    assert ShellClientTruthLabel.READ_ONLY in read_model.truth_label_summary
    assert ShellClientTruthLabel.CONTRACT_ONLY in read_model.truth_label_summary
    assert ShellClientTruthLabel.PREFLIGHT_ONLY in read_model.truth_label_summary
    assert ShellClientTruthLabel.LIVE not in read_model.truth_label_summary
    assert P2_10_D_REPORT_PATH not in read_model.evidence_refs
    assert "agent/reports/P2_10_C_TAURI_DESKTOP_LOCAL_SHELL.md" in read_model.evidence_refs
    assert "agent/reports/P2_VSLICE_A_GOVERNED_COMMAND_PALETTE_PREFLIGHT.md" in (
        read_model.evidence_refs
    )


def test_terminal_json_export_is_deterministic_and_json_safe():
    first = serialize_terminal_shell_read_model(build_terminal_shell_read_model())
    second = serialize_terminal_shell_read_model(build_terminal_shell_read_model())

    assert first == second
    payload = json.loads(first)
    assert payload["execution_disabled"] is True
    assert payload["p2_vslice_status"] == "PREFLIGHT_ONLY"


def test_p210d_result_points_to_e_without_starting_e():
    result = build_p2_10_d_terminal_shell_result()

    assert result.covered_pack == "P2.10-D"
    assert result.next_pack == "P2.10-E"
    assert result.p210e_not_started is True
    assert result.operator_testable_terminal_path is True
