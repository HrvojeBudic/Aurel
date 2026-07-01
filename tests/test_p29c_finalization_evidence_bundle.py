"""Tests for P2.9-C finalization evidence bundle and P2.9-D handoff."""

from __future__ import annotations

import json

from agentic_runtime.aurel_shell.shell_exit_finalization import (
    P2_9_C_NEXT_RANGE,
    P2_9_C_REQUIRED_REPORTS,
    ShellExitFinalizationStatus,
    build_p2_9_c_evidence_refs,
    build_p2_9_c_shell_exit_finalization_result,
    build_shell_exit_finalization_evidence_bundle,
    render_p2_9_c_coverage_rows,
    serialize_p2_9_c_result,
)
from agentic_runtime.aurel_shell.shell_exit_readiness import (
    OLD_P2_9_B_OVERLAY_REPORT_PATH,
    P2_9_B_REPORT_PATH,
    P2_VSLICE_A_REPORT_PATH,
    ShellExitTruthLabel,
)


def test_evidence_bundle_includes_all_required_prior_reports() -> None:
    bundle = build_shell_exit_finalization_evidence_bundle()
    assert bundle.bundle_id == "p2_9_c_finalization_evidence_bundle"
    assert bundle.required_reports == P2_9_C_REQUIRED_REPORTS
    assert bundle.present_reports == P2_9_C_REQUIRED_REPORTS
    assert bundle.missing_reports == ()
    assert bundle.bundle_status is ShellExitFinalizationStatus.C_READY_FOR_D
    assert P2_9_B_REPORT_PATH in bundle.required_reports
    assert OLD_P2_9_B_OVERLAY_REPORT_PATH in bundle.required_reports
    assert P2_VSLICE_A_REPORT_PATH in bundle.required_reports
    assert "agent/STATE.md" in bundle.state_refs
    assert "tests/test_shell_exit_finalization.py" in bundle.test_refs


def test_evidence_bundle_reports_missing_reports_without_promoting_to_ready() -> None:
    present = tuple(report for report in P2_9_C_REQUIRED_REPORTS if report != P2_VSLICE_A_REPORT_PATH)
    bundle = build_shell_exit_finalization_evidence_bundle(present_reports=present)
    assert bundle.bundle_status is ShellExitFinalizationStatus.C_BLOCKED
    assert bundle.missing_reports == (P2_VSLICE_A_REPORT_PATH,)


def test_evidence_refs_preserve_true_p2_9_b_old_overlay_and_preflight_truth() -> None:
    refs = {ref.ref_id: ref for ref in build_p2_9_c_evidence_refs()}
    assert refs["true_p2_9_b_readiness_matrix"].path == P2_9_B_REPORT_PATH
    assert refs["true_p2_9_b_readiness_matrix"].commit == "161fb8b"
    assert refs["old_p2_9_b_overlay"].path == OLD_P2_9_B_OVERLAY_REPORT_PATH
    assert refs["old_p2_9_b_overlay"].truth_label is ShellExitTruthLabel.EVIDENCE_SEALED
    assert refs["p2_vslice_a_preflight"].path == P2_VSLICE_A_REPORT_PATH
    assert refs["p2_vslice_a_preflight"].truth_label is ShellExitTruthLabel.PREFLIGHT_ONLY


def test_p2_9_d_handoff_uses_evidence_bundle_and_blocks_p2_10() -> None:
    result = build_p2_9_c_shell_exit_finalization_result()
    handoff = result.p29d_handoff
    assert handoff.next_pack == "P2.9-D"
    assert handoff.next_range == P2_9_C_NEXT_RANGE == "P2.9.16-P2.9.20"
    assert handoff.p29d_handoff_ready is True
    assert handoff.p210_allowed is False
    assert "P2.9-D" in handoff.p210_block_reason
    assert handoff.inherited_evidence_bundle == result.evidence_bundle.bundle_id
    assert handoff.required_p29d_decisions
    assert handoff.remaining_blockers


def test_coverage_rows_and_serialization_are_stable() -> None:
    result = build_p2_9_c_shell_exit_finalization_result()
    rows = render_p2_9_c_coverage_rows(result)
    assert len(rows) == 5
    assert rows[0].startswith("| P2.9.11 |")
    assert "P2.9-D" in rows[-1]
    payload = json.loads(serialize_p2_9_c_result(result))
    assert payload["covered_range"] == "P2.9.11-P2.9.15"
    assert payload["p29d_next"] is True
    assert payload["p210_allowed"] is False
