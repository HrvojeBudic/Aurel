"""Tests for P2.10-C desktop Shell wrapper contract."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agentic_runtime.aurel_shell.desktop_shell_contract import (
    P2_10_C_FIXTURE_REL_PATH,
    P2_10_C_NEXT_PACK,
    P2_10_C_PACK_ID,
    P2_10_C_REPORT_PATH,
    P2_10_D_NOT_STARTED,
    P2_10_E_NOT_STARTED,
    DesktopShellCapability,
    DesktopShellCapabilityStatus,
    DesktopShellRunMode,
    DesktopToolingDecision,
    P210CPrerequisiteGateStatus,
    assert_desktop_shell_derives_from_p210a_b,
    assert_p2_10_c_no_shell_live_or_native_authority,
    assert_p2_10_c_prerequisite_gate_passed,
    build_desktop_shell_read_model,
    build_desktop_shell_wrapper_contract,
    build_p2_10_c_desktop_shell_result,
    build_p2_10_c_prerequisite_gate,
    export_desktop_shell_read_model_fixture,
    serialize_desktop_shell_read_model,
)
from agentic_runtime.aurel_shell.multi_client_foundation import (
    P2_10_C_NOT_STARTED,
    ShellClientKind,
    ShellClientTruthLabel,
    build_shell_client_state,
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def test_p210c_constants() -> None:
    assert P2_10_C_PACK_ID == "P2.10-C"
    assert P2_10_C_NEXT_PACK == "P2.10-D"
    assert P2_10_C_NOT_STARTED is False
    assert P2_10_D_NOT_STARTED is True
    assert P2_10_E_NOT_STARTED is True


def test_p210c_prerequisite_gate_passes_with_p210b() -> None:
    gate = build_p2_10_c_prerequisite_gate()
    assert gate.p210b_report_found is True
    assert gate.p210b_report_indexed is True
    assert gate.p210b_proves_web_shell_done is True
    assert gate.p210b_points_to_p210c is True
    assert gate.p210d_not_started is True
    assert gate.p210e_not_started is True
    assert gate.gate_status is P210CPrerequisiteGateStatus.GATE_PASSED
    assert gate.blockers == ()
    assert_p2_10_c_prerequisite_gate_passed(gate)


def test_p210c_refuses_when_p210b_report_missing() -> None:
    gate = build_p2_10_c_prerequisite_gate(p210b_report_exists=False)
    assert gate.gate_status is P210CPrerequisiteGateStatus.GATE_REPAIR_REQUIRED
    assert "P2.10-B report missing" in gate.blockers
    with pytest.raises(ValueError):
        assert_p2_10_c_prerequisite_gate_passed(gate)


def test_p210c_wrapper_contract_client_kinds() -> None:
    contract = build_desktop_shell_wrapper_contract()
    assert contract.client_kind is ShellClientKind.DESKTOP_TAURI
    assert contract.wrapped_client_kind is ShellClientKind.WEB
    assert contract.next_pack == "P2.10-D"


def test_p210c_read_model_derives_from_desktop_client_state() -> None:
    result = build_p2_10_c_desktop_shell_result()
    desktop_state = build_shell_client_state(ShellClientKind.DESKTOP_TAURI)
    rm = result.desktop_read_model
    assert rm.desktop_client_status.active_client is ShellClientKind.DESKTOP_TAURI
    assert result.source_client_state_hash == desktop_state.state_hash
    assert set(rm.available_surfaces) == set(desktop_state.available_surfaces)


def test_p210c_json_is_deterministic_and_typescript_safe() -> None:
    rm1 = build_desktop_shell_read_model()
    rm2 = build_desktop_shell_read_model()
    assert rm1.read_model_hash == rm2.read_model_hash
    parsed = json.loads(serialize_desktop_shell_read_model(rm1))
    assert parsed["pack_id"] == "P2.10-C"
    assert parsed["next_pack_pointer"] == "P2.10-D"
    assert parsed["p210d_not_started"] is True
    assert parsed["desktop_client_status"]["active_client"] == "DESKTOP_TAURI"


def test_p210c_preserves_p2_vslice_a_preflight_only() -> None:
    result = build_p2_10_c_desktop_shell_result()
    assert (
        result.desktop_read_model.p2_vslice_status
        is ShellClientTruthLabel.PREFLIGHT_ONLY
    )
    assert ShellClientTruthLabel.LIVE not in result.desktop_read_model.truth_label_summary


def test_p210c_fixture_export() -> None:
    path = export_desktop_shell_read_model_fixture()
    assert path == _repo_root() / P2_10_C_FIXTURE_REL_PATH
    fixture = json.loads(path.read_text(encoding="utf-8"))
    live = json.loads(serialize_desktop_shell_read_model(build_desktop_shell_read_model()))
    assert fixture["read_model_hash"] == live["read_model_hash"]


def test_p210c_result_integrity() -> None:
    result = build_p2_10_c_desktop_shell_result()
    assert result.covered_pack == "P2.10-C"
    assert result.next_pack == "P2.10-D"
    assert result.p210d_not_started is True
    assert result.desktop_tooling_decision is DesktopToolingDecision.PATH_B_MINIMAL_NEW
    assert result.tauri_wrapper_status in {
        ShellClientTruthLabel.DEV_FIXTURE,
        ShellClientTruthLabel.CONTRACT_ONLY,
    }
    assert_desktop_shell_derives_from_p210a_b(result)
    assert_p2_10_c_no_shell_live_or_native_authority(result)


def test_p210c_report_path_constant() -> None:
    assert P2_10_C_REPORT_PATH.endswith("P2_10_C_TAURI_DESKTOP_LOCAL_SHELL.md")
