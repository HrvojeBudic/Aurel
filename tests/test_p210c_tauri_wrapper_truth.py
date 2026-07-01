"""Truth and Tauri wrapper boundary tests for P2.10-C."""

from __future__ import annotations

from pathlib import Path

from agentic_runtime.aurel_shell.desktop_shell_contract import (
    P2_10_C_TAURI_CONF,
    P2_10_C_TAURI_DIR,
    DesktopShellRunMode,
    build_p2_10_c_desktop_shell_result,
)
from agentic_runtime.aurel_shell.multi_client_foundation import (
    ShellClientKind,
    ShellClientTruthLabel,
    build_shell_client_local_run_modes,
)
from agentic_runtime.aurel_shell.web_shell_read_model import build_web_shell_read_model


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def test_p210c_tauri_scaffold_present() -> None:
    root = _repo_root()
    assert (root / P2_10_C_TAURI_CONF).is_file()
    assert (root / P2_10_C_TAURI_DIR / "Cargo.toml").is_file()
    assert (root / P2_10_C_TAURI_DIR / "src" / "main.rs").is_file()


def test_p210c_desktop_run_mode_dev_runnable_when_tauri_present() -> None:
    result = build_p2_10_c_desktop_shell_result()
    assert (
        result.desktop_read_model.desktop_run_mode
        is DesktopShellRunMode.DESKTOP_TAURI_DEV_RUNNABLE
    )
    assert result.operator_testable_desktop_path is True
    assert result.desktop_read_model.desktop_client_status.launch_command == (
        "npm run tauri:dev"
    )


def test_p210c_does_not_claim_shell_live_or_command_execution() -> None:
    result = build_p2_10_c_desktop_shell_result()
    proof = result.side_effect_proof
    assert proof.shell_live_claimed is False
    assert proof.arbitrary_command_execution_implemented is False
    assert proof.full_desktop_app_claimed is False
    assert proof.native_authority_bridge_claimed is False
    forbidden = {
        b.forbidden_claim.lower() for b in result.desktop_wrapper_contract.no_overclaim_boundaries
    }
    assert any("shell live" in claim for claim in forbidden)
    assert any("command execution" in claim for claim in forbidden)


def test_p210c_wraps_web_read_model_without_inventing_truth() -> None:
    result = build_p2_10_c_desktop_shell_result()
    web_rm = build_web_shell_read_model()
    wrapped = result.desktop_read_model.wrapped_web_shell_status
    assert wrapped.source_read_model_hash == web_rm.read_model_hash
    assert wrapped.web_client_truth_label is ShellClientTruthLabel.CONTRACT_ONLY


def test_p210c_cli_tui_mobile_not_implemented() -> None:
    result = build_p2_10_c_desktop_shell_result()
    proof = result.side_effect_proof
    assert proof.cli_tui_parity_implemented is False
    assert proof.mobile_app_implemented is False
    assert proof.p2_10_d_implemented is False
    assert proof.p2_10_e_implemented is False
    assert result.p210d_not_started is True


def test_p210c_local_run_modes_mark_desktop_runnable() -> None:
    modes = {m.client_kind: m for m in build_shell_client_local_run_modes()}
    desktop = modes[ShellClientKind.DESKTOP_TAURI]
    assert desktop.locally_runnable is True
    assert desktop.launch_command == "npm run tauri:dev"
