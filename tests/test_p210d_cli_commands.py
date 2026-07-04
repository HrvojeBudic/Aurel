"""Subprocess tests for P2.10-D read-only Shell terminal CLI commands."""

from __future__ import annotations

import json

from tests.cli_helpers import run_cli


def test_shell_status_json_is_read_only():
    proc = run_cli("shell", "status", "--json")

    assert proc.returncode == 0
    payload = json.loads(proc.stdout)
    assert payload["covered_pack"] == "P2.10-D"
    assert payload["status"] == "READ_ONLY"
    assert payload["execution_disabled"] is True
    assert payload["p2_vslice_status"] == "PREFLIGHT_ONLY"
    assert payload["last_completed_pack"] == "P2.11-C"
    assert payload["next_pack"] == "P2.11-D"
    assert payload["next_pack_not_started"] is True


def test_shell_clients_command_lists_expected_clients():
    proc = run_cli("shell", "clients", "--json")

    assert proc.returncode == 0
    assert json.loads(proc.stdout) == [
        "WEB",
        "DESKTOP_TAURI",
        "CLI",
        "TUI",
        "MOBILE_FOUNDATION",
    ]


def test_shell_surfaces_command_lists_canonical_surfaces():
    proc = run_cli("shell", "surfaces", "--json")

    assert proc.returncode == 0
    payload = json.loads(proc.stdout)
    assert [surface["surface_id"] for surface in payload] == [
        "aurel_cro",
        "hq",
        "corp",
        "hub",
        "ide",
        "system",
        "settings",
    ]
    assert all(surface["truth_label"] == "CONTRACT_ONLY" for surface in payload)


def test_shell_parity_command_exposes_execution_disabled():
    proc = run_cli("shell", "parity", "--json")

    assert proc.returncode == 0
    payload = json.loads(proc.stdout)
    assert "EXECUTE_COMMAND" in payload["execution_disabled_proof"]
    assert "RUN_TOOL" in payload["execution_disabled_proof"]
    assert "TRIGGER_SANDBOX" in payload["execution_disabled_proof"]
    assert "does not enable command execution" in payload["terminal_parity_summary"]


def test_shell_run_modes_command_does_not_claim_execution_or_live():
    proc = run_cli("shell", "run-modes", "--json")

    assert proc.returncode == 0
    payload = json.loads(proc.stdout)
    assert "CLI_READ_ONLY" in payload["local_run_modes"]
    assert "TERMINAL_JSON_EXPORT" in payload["local_run_modes"]
    assert payload["command_execution_exposed"] is False
    assert payload["shell_live_claimed"] is False
    assert payload["full_terminal_automation_claimed"] is False


def test_shell_export_json_is_deterministic_and_contains_source_refs():
    proc1 = run_cli("shell", "export-json")
    proc2 = run_cli("shell", "export-json")

    assert proc1.returncode == 0
    assert proc2.returncode == 0
    assert proc1.stdout == proc2.stdout
    payload = json.loads(proc1.stdout)
    assert payload["execution_disabled"] is True
    assert payload["source_shell_state_hash"]
    assert payload["source_web_read_model_hash"]
    assert payload["source_desktop_read_model_hash"]
