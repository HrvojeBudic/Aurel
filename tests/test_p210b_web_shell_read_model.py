"""Tests for P2.10-B web Shell read model."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agentic_runtime.aurel_shell.multi_client_foundation import (
    ShellClientKind,
    ShellClientTruthLabel,
    build_shell_client_state,
)
from agentic_runtime.aurel_shell.web_shell_read_model import (
    P2_10_B_FIXTURE_REL_PATH,
    P2_10_B_NEXT_PACK,
    P2_10_B_PACK_ID,
    P2_10_C_NOT_STARTED,
    P2_10_D_NOT_STARTED,
    P2_10_E_NOT_STARTED,
    P210BPrerequisiteGateStatus,
    assert_p2_10_b_no_shell_live_or_execution_claim,
    assert_p2_10_b_prerequisite_gate_passed,
    build_p2_10_b_prerequisite_gate,
    build_p2_10_b_web_shell_result,
    build_web_shell_read_model,
    export_web_shell_read_model_fixture,
    serialize_p2_10_b_result,
    serialize_web_shell_read_model,
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _roundtrip(obj) -> dict:
    return json.loads(json.dumps(obj.to_canonical_dict(), sort_keys=True))


def test_p210b_constants() -> None:
    assert P2_10_B_PACK_ID == "P2.10-B"
    assert P2_10_B_NEXT_PACK == "P2.10-C"
    assert P2_10_C_NOT_STARTED is True
    assert P2_10_D_NOT_STARTED is True
    assert P2_10_E_NOT_STARTED is True


def test_p210b_prerequisite_gate_passes_with_p210a() -> None:
    gate = build_p2_10_b_prerequisite_gate()
    assert gate.p210a_report_found is True
    assert gate.p210a_report_indexed is True
    assert gate.p210a_proves_multi_client_done is True
    assert gate.p210a_points_to_p210b is True
    assert gate.p210c_not_started is True
    assert gate.p210d_not_started is True
    assert gate.gate_status is P210BPrerequisiteGateStatus.GATE_PASSED
    assert gate.blockers == ()
    assert_p2_10_b_prerequisite_gate_passed(gate)


def test_p210b_refuses_when_p210a_report_missing() -> None:
    gate = build_p2_10_b_prerequisite_gate(p210a_report_exists=False)
    assert gate.gate_status is P210BPrerequisiteGateStatus.GATE_REPAIR_REQUIRED
    assert "P2.10-A report missing" in gate.blockers
    with pytest.raises(ValueError):
        assert_p2_10_b_prerequisite_gate_passed(gate)


def test_p210b_read_model_derives_from_web_client_state() -> None:
    result = build_p2_10_b_web_shell_result()
    web_state = build_shell_client_state(ShellClientKind.WEB)
    rm = result.read_model
    assert rm.client_status.active_client is ShellClientKind.WEB
    assert result.source_client_state_hash == web_state.state_hash
    assert {s.surface_id for s in rm.surfaces} == set(web_state.available_surfaces)


def test_p210b_json_is_deterministic_and_typescript_safe() -> None:
    result = build_p2_10_b_web_shell_result()
    roundtrip = _roundtrip(result)
    assert roundtrip["covered_pack"] == "P2.10-B"
    assert roundtrip["result_hash"] == result.result_hash
    serialized = serialize_p2_10_b_result(result)
    parsed = json.loads(serialized)
    assert parsed["next_pack"] == "P2.10-C"
    assert isinstance(parsed["read_model"]["surfaces"], list)


def test_p210b_p2_vslice_a_remains_preflight_only() -> None:
    result = build_p2_10_b_web_shell_result()
    rm = result.read_model
    assert rm.p2_vslice_a_status is ShellClientTruthLabel.PREFLIGHT_ONLY
    assert rm.command_palette_availability is ShellClientTruthLabel.PREFLIGHT_ONLY


def test_p210b_no_shell_live_or_execution_claim() -> None:
    result = build_p2_10_b_web_shell_result()
    assert_p2_10_b_no_shell_live_or_execution_claim(result)
    assert result.side_effect_proof.shell_live_claimed is False
    assert result.side_effect_proof.arbitrary_command_execution_implemented is False
    assert ShellClientTruthLabel.LIVE not in result.read_model.truth_labels


def test_p210b_p210c_next_not_implemented() -> None:
    result = build_p2_10_b_web_shell_result()
    assert result.next_pack == "P2.10-C"
    rm = result.read_model
    assert rm.p210c_not_started is True
    assert rm.p210d_not_started is True
    assert rm.p210e_not_started is True
    proof = result.side_effect_proof
    assert proof.p2_10_c_implemented is False
    assert proof.p2_10_d_implemented is False
    assert proof.tauri_desktop_implemented is False
    assert proof.mobile_app_implemented is False


def test_p210b_surface_views_cover_seven_surfaces() -> None:
    rm = build_web_shell_read_model()
    surface_ids = {s.surface_id for s in rm.surfaces}
    assert surface_ids == {
        "aurel_cro",
        "hq",
        "corp",
        "hub",
        "ide",
        "system",
        "settings",
    }
    selector = {s.surface_id for s in rm.surfaces if s.in_surface_selector}
    right = {s.surface_id for s in rm.surfaces if s.in_topbar_right}
    assert selector == {"aurel_cro", "hq", "corp", "hub", "ide"}
    assert right == {"system", "settings"}


def test_p210b_web_skeleton_locally_runnable_after_validation() -> None:
    rm = build_web_shell_read_model()
    assert rm.client_status.locally_runnable is True
    assert rm.client_status.launch_command == "npm run dev"
    assert rm.client_status.skeleton_truth_label is ShellClientTruthLabel.DEV_FIXTURE


def test_p210b_export_fixture_writes_json() -> None:
    path = export_web_shell_read_model_fixture()
    assert path == _repo_root() / P2_10_B_FIXTURE_REL_PATH
    assert path.is_file()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["pack_id"] == "P2.10-B"
    assert data["read_model_hash"] == build_web_shell_read_model().read_model_hash
    roundtrip = json.loads(serialize_web_shell_read_model(build_web_shell_read_model()))
    assert roundtrip["read_model_hash"] == data["read_model_hash"]
