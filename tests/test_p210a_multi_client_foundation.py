"""Tests for P2.10-A multi-client Shell foundation."""

from __future__ import annotations

import json

import pytest

from agentic_runtime.aurel_shell.multi_client_foundation import (
    P2_10_A_NEXT_PACK,
    P2_10_A_PACK_ID,
    P2_10_B_NOT_STARTED,
    P2_10_C_NOT_STARTED,
    P2_10_D_NOT_STARTED,
    P210APrerequisiteGateStatus,
    ShellClientKind,
    ShellClientTruthLabel,
    assert_p2_10_a_no_shell_live_or_execution_claim,
    assert_p2_10_a_prerequisite_gate_passed,
    build_p2_10_a_multi_client_foundation_result,
    build_p2_10_a_prerequisite_gate,
    map_shell_client_kind_to_legacy,
    serialize_p2_10_a_result,
)
from agentic_runtime.aurel_shell.client_consistency import ClientKind


def _roundtrip(obj) -> dict:
    return json.loads(json.dumps(obj.to_canonical_dict(), sort_keys=True))


def test_p210a_constants_and_supported_clients() -> None:
    assert P2_10_A_PACK_ID == "P2.10-A"
    assert P2_10_A_NEXT_PACK == "P2.10-B"
    assert P2_10_B_NOT_STARTED is True
    assert P2_10_C_NOT_STARTED is False
    assert P2_10_D_NOT_STARTED is True
    result = build_p2_10_a_multi_client_foundation_result()
    kinds = {s.client_kind for s in result.client_states}
    assert kinds == set(ShellClientKind)


def test_p210a_prerequisite_gate_passes_with_p29d() -> None:
    gate = build_p2_10_a_prerequisite_gate()
    assert gate.p29d_report_found is True
    assert gate.p29d_report_indexed is True
    assert gate.p29d_seals_p29 is True
    assert gate.p29d_allows_p210a is True
    assert gate.gate_status is P210APrerequisiteGateStatus.GATE_PASSED
    assert gate.blockers == ()
    assert_p2_10_a_prerequisite_gate_passed(gate)


def test_p210a_refuses_when_p29d_report_missing() -> None:
    gate = build_p2_10_a_prerequisite_gate(p29d_report_exists=False)
    assert gate.gate_status is P210APrerequisiteGateStatus.GATE_REPAIR_REQUIRED
    assert "P2.9-D report missing" in gate.blockers
    with pytest.raises(ValueError):
        assert_p2_10_a_prerequisite_gate_passed(gate)


def test_p210a_result_is_json_serializable_and_deterministic() -> None:
    result = build_p2_10_a_multi_client_foundation_result()
    roundtrip = _roundtrip(result)
    assert roundtrip["covered_pack"] == "P2.10-A"
    assert roundtrip["result_hash"] == result.result_hash
    serialized = serialize_p2_10_a_result(result)
    assert json.loads(serialized)["next_pack"] == "P2.10-B"


def test_p210a_legacy_client_kind_mapping() -> None:
    assert map_shell_client_kind_to_legacy(ShellClientKind.WEB) is ClientKind.WEB
    assert map_shell_client_kind_to_legacy(ShellClientKind.DESKTOP_TAURI) is ClientKind.DESKTOP
    assert map_shell_client_kind_to_legacy(ShellClientKind.MOBILE_FOUNDATION) is ClientKind.MOBILE
    assert map_shell_client_kind_to_legacy(ShellClientKind.CLI) is ClientKind.CLI
    assert map_shell_client_kind_to_legacy(ShellClientKind.TUI) is ClientKind.TUI
    result = build_p2_10_a_multi_client_foundation_result()
    assert result.legacy_client_kind_map["DESKTOP_TAURI"] == "DESKTOP"
    assert result.legacy_client_kind_map["MOBILE_FOUNDATION"] == "MOBILE"


def test_p210a_p2_vslice_a_remains_preflight_only() -> None:
    result = build_p2_10_a_multi_client_foundation_result()
    assert result.p2_vslice_a_truth_label is ShellClientTruthLabel.PREFLIGHT_ONLY
    for state in result.client_states:
        assert state.command_palette_availability is ShellClientTruthLabel.PREFLIGHT_ONLY


def test_p210a_p210b_next_not_implemented() -> None:
    result = build_p2_10_a_multi_client_foundation_result()
    assert result.next_pack == "P2.10-B"
    assert result.p210b_ready is True
    assert result.p210b_not_started is True
    assert result.p210c_not_started is False
    assert result.p210d_not_started is True
    proof = result.side_effect_proof
    assert proof.p2_10_b_implemented is False
    assert proof.p2_10_c_implemented is False
    assert proof.p2_10_d_implemented is False


def test_p210a_no_shell_live_or_execution_claim() -> None:
    result = build_p2_10_a_multi_client_foundation_result()
    assert_p2_10_a_no_shell_live_or_execution_claim(result)
    assert result.side_effect_proof.shell_live_claimed is False
    assert result.side_effect_proof.arbitrary_command_execution_implemented is False
    assert len(result.no_overclaim_boundaries) == 9


def test_p210a_surface_availability_covers_seven_surfaces() -> None:
    result = build_p2_10_a_multi_client_foundation_result()
    surface_ids = {s.surface_id for s in result.surface_contracts}
    assert surface_ids == {
        "aurel_cro",
        "hq",
        "corp",
        "hub",
        "ide",
        "system",
        "settings",
    }
    topbar = result.client_states[0].global_topbar_contract
    assert set(topbar.surface_selector_surface_ids) == {
        "aurel_cro",
        "hq",
        "corp",
        "hub",
        "ide",
    }
    assert set(topbar.right_side_surface_ids) == {"system", "settings"}
