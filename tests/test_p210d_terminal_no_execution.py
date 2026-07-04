"""Tests for P2.10-D terminal no-execution boundary."""

from __future__ import annotations

from dataclasses import fields

from agentic_runtime.aurel_shell.multi_client_foundation import ShellClientTruthLabel
from agentic_runtime.aurel_shell.terminal_shell_client import (
    P210DSideEffectProof,
    TerminalShellCapability,
    TerminalShellCapabilityStatus,
    build_p2_10_d_terminal_shell_result,
    build_terminal_shell_client_contract,
    build_terminal_shell_command_specs,
)


def test_terminal_disabled_execution_capabilities_are_machine_testable():
    contract = build_terminal_shell_client_contract()
    disabled = {
        entry.capability: entry.status for entry in contract.disabled_execution_capabilities
    }

    for capability in (
        TerminalShellCapability.EXECUTE_COMMAND,
        TerminalShellCapability.APPROVE_ACTION,
        TerminalShellCapability.RUN_TOOL,
        TerminalShellCapability.START_RUNTIME,
        TerminalShellCapability.STOP_RUNTIME,
        TerminalShellCapability.DISPATCH_AGENT,
        TerminalShellCapability.RUN_WORKFLOW,
        TerminalShellCapability.WRITE_MEMORY,
        TerminalShellCapability.MODIFY_POLICY,
        TerminalShellCapability.MUTATE_IDENTITY,
        TerminalShellCapability.TRIGGER_SANDBOX,
    ):
        assert disabled[capability] is TerminalShellCapabilityStatus.DISABLED


def test_terminal_no_overclaim_boundaries_include_required_forbidden_claims():
    contract = build_terminal_shell_client_contract()
    boundaries = {boundary.boundary_id: boundary for boundary in contract.no_overclaim_boundaries}

    for boundary_id in (
        "NO_COMMAND_EXECUTION_CLAIM",
        "NO_TOOL_EXECUTION_CLAIM",
        "NO_APPROVAL_EXECUTION_CLAIM",
        "NO_RUNTIME_CONTROL_CLAIM",
        "NO_SANDBOX_CONTROL_CLAIM",
        "NO_WORKFLOW_EXECUTION_CLAIM",
        "NO_AGENT_DISPATCH_CLAIM",
        "NO_MEMORY_WRITE_CLAIM",
        "NO_POLICY_MUTATION_CLAIM",
        "NO_IDENTITY_MUTATION_CLAIM",
        "NO_SHELL_LIVE_CLAIM",
        "NO_FULL_CLI_AUTOMATION_CLAIM",
        "NO_FULL_TUI_PRODUCT_CLAIM",
        "NO_P2_20_SEAL_CLAIM",
    ):
        assert boundaries[boundary_id].active is True


def test_terminal_command_specs_are_read_only_only():
    specs = build_terminal_shell_command_specs()

    assert {spec.command_name for spec in specs} == {
        "shell status",
        "shell clients",
        "shell surfaces",
        "shell parity",
        "shell evidence",
        "shell run-modes",
        "shell export-json",
    }
    for spec in specs:
        assert spec.read_only is True
        assert spec.allowed is True
        assert spec.disabled_reason == ""


def test_p210d_side_effect_proof_all_forbidden_flags_false():
    result = build_p2_10_d_terminal_shell_result()
    proof = result.no_scope_expansion_proof

    assert isinstance(proof, P210DSideEffectProof)
    for field in fields(proof):
        assert getattr(proof, field.name) is False


def test_terminal_result_does_not_claim_live_or_change_preflight():
    result = build_p2_10_d_terminal_shell_result()
    rm = result.terminal_read_model

    assert ShellClientTruthLabel.LIVE not in rm.truth_label_summary
    assert rm.p2_vslice_status is ShellClientTruthLabel.PREFLIGHT_ONLY
    assert rm.execution_disabled is True
    assert result.next_pack == "P2.10-E"
    assert result.p210e_not_started is True
