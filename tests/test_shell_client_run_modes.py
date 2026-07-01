"""Tests for P2.10-A Shell client local run mode boundaries."""

from __future__ import annotations

import json

from agentic_runtime.aurel_shell.multi_client_foundation import (
    ShellClientKind,
    ShellClientRunMode,
    ShellClientTruthLabel,
    build_p2_10_a_multi_client_foundation_result,
    build_shell_client_local_run_modes,
)


def _roundtrip(obj) -> dict:
    return json.loads(json.dumps(obj.to_canonical_dict(), sort_keys=True))


def test_local_run_modes_are_honest_and_not_live() -> None:
    modes = build_shell_client_local_run_modes()
    assert len(modes) == 6  # python backend + 5 clients
    for entry in modes:
        assert entry.locally_runnable is False
        assert entry.truth_label is not ShellClientTruthLabel.LIVE
        assert entry.launch_command == ""


def test_web_desktop_mobile_are_contract_only() -> None:
    modes = {
        m.client_kind: m
        for m in build_shell_client_local_run_modes()
        if m.client_kind is not None
    }
    web = modes[ShellClientKind.WEB]
    desktop = modes[ShellClientKind.DESKTOP_TAURI]
    mobile = modes[ShellClientKind.MOBILE_FOUNDATION]
    assert web.run_mode is ShellClientRunMode.WEB_DEV_SHELL_CONTRACT
    assert desktop.run_mode is ShellClientRunMode.DESKTOP_TAURI_CONTRACT
    assert mobile.run_mode is ShellClientRunMode.MOBILE_CONTRACT_ONLY
    assert web.truth_label is ShellClientTruthLabel.CONTRACT_ONLY
    assert desktop.truth_label is ShellClientTruthLabel.CONTRACT_ONLY
    assert mobile.truth_label is ShellClientTruthLabel.CONTRACT_ONLY
    assert web.contract_only is True
    assert desktop.contract_only is True
    assert mobile.contract_only is True


def test_cli_read_only_tui_unavailable() -> None:
    modes = {
        m.client_kind: m
        for m in build_shell_client_local_run_modes()
        if m.client_kind is not None
    }
    cli = modes[ShellClientKind.CLI]
    tui = modes[ShellClientKind.TUI]
    assert cli.run_mode is ShellClientRunMode.CLI_TUI_CONTRACT
    assert cli.truth_label is ShellClientTruthLabel.READ_ONLY
    assert tui.run_mode is ShellClientRunMode.UNAVAILABLE
    assert tui.truth_label is ShellClientTruthLabel.UNAVAILABLE


def test_no_runnable_web_desktop_mobile_claims_in_result() -> None:
    result = build_p2_10_a_multi_client_foundation_result()
    proof = result.side_effect_proof
    assert proof.full_web_app_implemented is False
    assert proof.tauri_desktop_implemented is False
    assert proof.mobile_app_implemented is False
    assert proof.desktop_runnable_claimed is False
    assert proof.mobile_runnable_claimed is False
    assert proof.full_local_app_claimed is False


def test_local_run_modes_json_serializable() -> None:
    modes = build_shell_client_local_run_modes()
    for entry in modes:
        data = _roundtrip(entry)
        assert data["entry_hash"] == entry.entry_hash


def test_python_backend_only_entry_exists() -> None:
    modes = build_shell_client_local_run_modes()
    backend = next(m for m in modes if m.run_mode is ShellClientRunMode.PYTHON_BACKEND_ONLY)
    assert backend.truth_label is ShellClientTruthLabel.READ_ONLY
    assert backend.contract_only is True
