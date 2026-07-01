from __future__ import annotations

import json

from agentic_runtime.aurel_shell.multi_client_demo_seal import (
    P2_10_E_NEXT_PACK,
    P210ClientDemoStatus,
    P210EPrerequisiteGateStatus,
    build_multi_client_shell_evidence_bundle,
    build_p2_10_e_multi_client_demo_seal_result,
    build_p2_10_e_prerequisite_gate,
    build_p2_10_operator_demo_seal,
    serialize_p2_10_e_result,
)
from agentic_runtime.aurel_shell.multi_client_foundation import (
    ShellClientKind,
    ShellClientTruthLabel,
)


def test_p210e_prerequisite_gate_consumes_p210d_and_points_to_p211() -> None:
    gate = build_p2_10_e_prerequisite_gate()

    assert gate.gate_status == P210EPrerequisiteGateStatus.GATE_PASSED
    assert gate.p210d_report_found is True
    assert gate.p210d_report_indexed is True
    assert gate.p210d_proves_terminal_client_done is True
    assert gate.p210d_points_to_p210e is True
    assert gate.p211_not_started is True
    assert gate.blockers == ()


def test_p210e_evidence_bundle_consumes_p210a_b_c_d_reports() -> None:
    bundle = build_multi_client_shell_evidence_bundle()

    assert set(bundle.source_reports) == {
        "agent/reports/P2_10_A_MULTI_CLIENT_SHELL_FOUNDATION.md",
        "agent/reports/P2_10_B_LOCAL_WEB_SHELL_SKELETON.md",
        "agent/reports/P2_10_C_TAURI_DESKTOP_LOCAL_SHELL.md",
        "agent/reports/P2_10_D_CLI_TUI_PARITY_BINDING.md",
    }
    assert bundle.next_pack_pointer == P2_10_E_NEXT_PACK == "P2.11"
    assert ShellClientTruthLabel.PREFLIGHT_ONLY in bundle.truth_labels
    assert "python -m agentic_runtime.cli shell export-json" in bundle.operator_testable_paths


def test_p210e_operator_demo_seal_keeps_client_claims_honest() -> None:
    seal = build_p2_10_operator_demo_seal()

    assert seal.demo_status.value == "DEMO_SEALED"
    assert seal.runnable_clients == (
        ShellClientKind.WEB,
        ShellClientKind.DESKTOP_TAURI,
    )
    assert seal.read_only_clients == (ShellClientKind.CLI,)
    assert seal.contract_only_clients == (ShellClientKind.TUI,)
    assert seal.unavailable_clients == (ShellClientKind.MOBILE_FOUNDATION,)
    assert "tests/test_p210d_cli_commands.py" in seal.validation_refs


def test_p210e_result_seals_p210_only_and_serializes_deterministically() -> None:
    result = build_p2_10_e_multi_client_demo_seal_result()
    encoded_once = serialize_p2_10_e_result(result)
    encoded_twice = serialize_p2_10_e_result(result)
    payload = json.loads(encoded_once)

    assert encoded_once == encoded_twice
    assert result.covered_pack == "P2.10-E"
    assert result.completion_seal.p210_done is True
    assert result.next_pack == "P2.11"
    assert result.p211_not_started is True
    assert payload["covered_pack"] == "P2.10-E"
    assert "P3 handoff" in result.completion_seal.not_sealed_as
    assert result.side_effect_proof.p2_final_seal_claimed is False


def test_p210e_run_modes_do_not_claim_mobile_or_tui_runnable() -> None:
    bundle = build_multi_client_shell_evidence_bundle()
    statuses = {entry.client_kind: entry for entry in bundle.client_run_modes}

    assert statuses[ShellClientKind.CLI].claim_level == P210ClientDemoStatus.READ_ONLY_TESTED
    assert statuses[ShellClientKind.TUI].claim_level == P210ClientDemoStatus.CONTRACT_ONLY
    assert (
        statuses[ShellClientKind.MOBILE_FOUNDATION].claim_level
        == P210ClientDemoStatus.NOT_STARTED
    )
