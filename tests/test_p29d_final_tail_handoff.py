"""Tests for P2.9-D completion report and P2.10 handoff pointer."""

from __future__ import annotations

import json

from agentic_runtime.aurel_shell.shell_exit_final_seal import (
    P2_9_D_CHECKPOINT_IDS,
    P2_9_D_NEXT_PACK_IF_GATE_PASSES,
    P2_9_D_REPAIR_PACK,
    P2_9_D_REPORT_PATH,
    P2_9_D_REQUIRED_REPORTS,
    ShellExitHandoffStatus,
    build_p2_9_d_evidence_refs,
    build_p2_9_d_shell_exit_final_seal_result,
    render_p2_9_d_coverage_rows,
    serialize_p2_9_d_result,
)
from agentic_runtime.aurel_shell.shell_exit_finalization import P2_9_C_REPORT_PATH
from agentic_runtime.aurel_shell.shell_exit_readiness import (
    OLD_P2_9_B_OVERLAY_REPORT_PATH,
    P2_9_B_REPORT_PATH,
    P2_VSLICE_A_REPORT_PATH,
    ShellExitTruthLabel,
)


def test_evidence_refs_include_p2_9_c_old_overlay_and_preflight_truth() -> None:
    refs = {ref.ref_id: ref for ref in build_p2_9_d_evidence_refs()}
    assert refs["p2_9_c_finalization_report"].path == P2_9_C_REPORT_PATH
    assert refs["p2_9_c_finalization_report"].commit == "5f4aa0b"
    assert refs["true_p2_9_b_readiness_matrix"].path == P2_9_B_REPORT_PATH
    assert refs["old_p2_9_b_overlay"].path == OLD_P2_9_B_OVERLAY_REPORT_PATH
    assert refs["old_p2_9_b_overlay"].truth_label is ShellExitTruthLabel.EVIDENCE_SEALED
    assert refs["p2_vslice_a_preflight"].path == P2_VSLICE_A_REPORT_PATH
    assert refs["p2_vslice_a_preflight"].truth_label is ShellExitTruthLabel.PREFLIGHT_ONLY
    assert refs["p1_enf_e_sandbox_gate"].truth_label is ShellExitTruthLabel.UNAVAILABLE


def test_required_reports_include_prior_a_b_c_and_enforcement_chain() -> None:
    assert P2_9_C_REPORT_PATH in P2_9_D_REQUIRED_REPORTS
    assert P2_9_B_REPORT_PATH in P2_9_D_REQUIRED_REPORTS
    assert OLD_P2_9_B_OVERLAY_REPORT_PATH in P2_9_D_REQUIRED_REPORTS
    assert P2_VSLICE_A_REPORT_PATH in P2_9_D_REQUIRED_REPORTS


def test_completion_report_and_handoff_pointer_choose_p2_10_a_on_gate_pass() -> None:
    result = build_p2_9_d_shell_exit_final_seal_result()
    assert result.completion_report.report_path == P2_9_D_REPORT_PATH
    assert result.completion_report.next_pointer == P2_9_D_NEXT_PACK_IF_GATE_PASSES
    assert len(result.completion_report.checkpoint_statuses) == len(P2_9_D_CHECKPOINT_IDS)
    assert result.handoff_pointer.next_pack == P2_9_D_NEXT_PACK_IF_GATE_PASSES
    assert result.handoff_pointer.handoff_status is ShellExitHandoffStatus.HANDOFF_READY
    assert result.handoff_pointer.p210_allowed is True
    assert result.handoff_pointer.p210_started is False
    assert result.p29_done is True
    assert result.p210_next is True


def test_completion_report_and_handoff_pointer_choose_repair_on_gate_failure() -> None:
    result = build_p2_9_d_shell_exit_final_seal_result(p29d_done=False)
    assert result.completion_report.next_pointer == P2_9_D_REPAIR_PACK
    assert result.handoff_pointer.next_pack == P2_9_D_REPAIR_PACK
    assert result.handoff_pointer.handoff_status is ShellExitHandoffStatus.HANDOFF_REPAIR_REQUIRED
    assert result.handoff_pointer.p210_allowed is False
    assert result.handoff_pointer.p210_started is False
    assert result.p29_done is False
    assert result.p210_next is False


def test_coverage_rows_and_serialization_are_stable() -> None:
    result = build_p2_9_d_shell_exit_final_seal_result()
    rows = render_p2_9_d_coverage_rows(result)
    assert len(rows) == 5
    assert rows[0].startswith("| P2.9.16 |")
    assert P2_9_D_NEXT_PACK_IF_GATE_PASSES in rows[-1]
    payload = json.loads(serialize_p2_9_d_result(result))
    assert payload["covered_range"] == "P2.9.16-P2.9.20"
    assert payload["p29_done"] is True
    assert payload["p210_next"] is True
    assert payload["handoff_pointer"]["p210_started"] is False
