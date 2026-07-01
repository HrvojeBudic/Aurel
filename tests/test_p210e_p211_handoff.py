from __future__ import annotations

from agentic_runtime.aurel_shell.multi_client_demo_seal import (
    P2_10_E_NEXT_TITLE,
    build_p2_10_e_handoff,
    build_p2_10_e_multi_client_demo_seal_result,
)
from agentic_runtime.aurel_shell.multi_client_foundation import ShellClientKind


def test_p210e_handoff_points_only_to_p211_surface_permission_matrix() -> None:
    handoff = build_p2_10_e_handoff()

    assert handoff.next_pack == "P2.11"
    assert handoff.next_title == P2_10_E_NEXT_TITLE == "Surface Permission Matrix"
    assert "not started" in handoff.handoff_status
    assert handoff.p211_not_started is True


def test_p210e_handoff_inherits_client_baseline_for_permission_work() -> None:
    handoff = build_p2_10_e_handoff()
    baseline = {entry.client_kind: entry for entry in handoff.inherited_client_baseline}

    assert set(baseline) == set(ShellClientKind)
    assert baseline[ShellClientKind.WEB].run_mode.value == "WEB_DEV_RUNNABLE"
    assert (
        baseline[ShellClientKind.DESKTOP_TAURI].run_mode.value
        == "DESKTOP_TAURI_DEV_RUNNABLE"
    )
    assert baseline[ShellClientKind.CLI].run_mode.value == "CLI_READ_ONLY"
    assert baseline[ShellClientKind.TUI].run_mode.value == "TUI_CONTRACT_ONLY"
    assert (
        baseline[ShellClientKind.MOBILE_FOUNDATION].run_mode.value
        == "MOBILE_CONTRACT_ONLY"
    )


def test_p210e_handoff_records_permission_relevant_findings() -> None:
    handoff = build_p2_10_e_handoff()

    assert any("read-only" in item for item in handoff.permission_relevant_findings)
    assert any("PREFLIGHT_ONLY" in item for item in handoff.permission_relevant_findings)
    assert "permission matrix not implemented" in handoff.remaining_risks
    assert "command execution unavailable" in handoff.remaining_risks


def test_p210e_result_keeps_p211_unimplemented() -> None:
    result = build_p2_10_e_multi_client_demo_seal_result()

    assert result.handoff.next_pack == "P2.11"
    assert result.handoff.p211_not_started is True
    assert result.side_effect_proof.p2_11_implemented is False
    assert result.side_effect_proof.p2_12_plus_implemented is False
