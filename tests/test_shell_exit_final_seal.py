"""Tests for P2.9-D Shell Exit final seal contracts."""

from __future__ import annotations

import json
from dataclasses import replace

import pytest

from agentic_runtime.aurel_shell.shell_exit_final_seal import (
    P2_9_D_CHECKPOINT_IDS,
    P2_9_D_COVERED_RANGE,
    P2_9_D_PACK_ID,
    P2_9_D_WORKING_LABELS,
    ShellExitFinalSealStatus,
    ShellExitSectionSealStatus,
    assert_p2_9_aggregate_sealed,
    assert_p2_9_d_no_scope_expansion,
    assert_p2_9_d_prerequisite_gate_passed,
    assert_p2_vslice_a_remains_preflight_in_p29d,
    build_p2_9_d_shell_exit_final_seal_result,
    build_shell_exit_final_tail_intake,
    build_shell_exit_p29_seal_aggregate,
)
from agentic_runtime.aurel_shell.shell_exit_finalization import (
    ShellExitFinalizationStatus,
    build_p2_9_c_shell_exit_finalization_result,
)
from agentic_runtime.aurel_shell.shell_exit_readiness import ShellExitTruthLabel


def _roundtrip(obj) -> dict:
    return json.loads(json.dumps(obj.to_canonical_dict(), sort_keys=True))


def test_p2_9_d_constants_and_working_labels_are_scoped() -> None:
    assert P2_9_D_PACK_ID == "P2.9-D"
    assert P2_9_D_COVERED_RANGE == "P2.9.16-P2.9.20"
    assert P2_9_D_CHECKPOINT_IDS == ("P2.9.16", "P2.9.17", "P2.9.18", "P2.9.19", "P2.9.20")
    assert P2_9_D_WORKING_LABELS["P2.9.16"] == "Final Tail Intake / P2.9-C Handoff Verification"
    assert P2_9_D_WORKING_LABELS["P2.9.20"] == "P2.9 Exit Seal Report / P2.10 Handoff Pointer"


def test_final_tail_intake_consumes_p2_9_c_handoff() -> None:
    intake = build_shell_exit_final_tail_intake()
    assert intake.c_ready_for_d is True
    assert intake.p210_started is False
    assert intake.intake_status is ShellExitSectionSealStatus.P29_SEALED
    assert "P2.9.11-P2.9.15" in intake.completed_ranges
    assert "P2.9.16-P2.9.20" not in intake.not_done_ranges
    assert_p2_9_d_prerequisite_gate_passed(intake)
    assert _roundtrip(intake)


def test_final_tail_intake_refuses_incomplete_p2_9_c() -> None:
    p29c = build_p2_9_c_shell_exit_finalization_result()
    blocked_aggregate = replace(
        p29c.decision_aggregate,
        aggregate_status=ShellExitFinalizationStatus.C_BLOCKED,
        sealed_checkpoints=("P2.9.11", "P2.9.12"),
        blocked_checkpoints=("P2.9.13", "P2.9.14", "P2.9.15"),
    )
    blocked = replace(p29c, decision_aggregate=blocked_aggregate, p29d_next=False)
    intake = build_shell_exit_final_tail_intake(blocked)
    assert intake.intake_status is ShellExitSectionSealStatus.P29_REPAIR_REQUIRED
    assert "P2.9-C" in intake.failure_reason
    with pytest.raises(ValueError):
        assert_p2_9_d_prerequisite_gate_passed(intake)


def test_p2_9_seal_aggregate_requires_full_checkpoint_coverage() -> None:
    aggregate = build_shell_exit_p29_seal_aggregate()
    assert aggregate.covered_section == "P2.9 Shell Exit Foundation"
    assert aggregate.checkpoint_range == "P2.9.0-P2.9.20"
    assert aggregate.completed_ranges[-1] == "P2.9.16-P2.9.20"
    assert aggregate.all_checkpoints_done is True
    assert aggregate.section_status is ShellExitSectionSealStatus.P29_SEALED
    assert aggregate.blocked_checkpoints == ()
    assert aggregate.repair_required_checkpoints == ()
    assert ShellExitTruthLabel.PREFLIGHT_ONLY in aggregate.truth_labels
    assert_p2_9_aggregate_sealed(aggregate)


def test_p2_9_seal_aggregate_blocks_when_p2_9_d_incomplete() -> None:
    aggregate = build_shell_exit_p29_seal_aggregate(p29d_done=False)
    assert aggregate.all_checkpoints_done is False
    assert aggregate.section_status is ShellExitSectionSealStatus.P29_REPAIR_REQUIRED
    assert aggregate.blocked_checkpoints == P2_9_D_CHECKPOINT_IDS
    with pytest.raises(ValueError):
        assert_p2_9_aggregate_sealed(aggregate)


def test_final_seal_result_is_foundation_not_product_readiness() -> None:
    result = build_p2_9_d_shell_exit_final_seal_result()
    assert result.final_seal_result.final_status is ShellExitFinalSealStatus.FINAL_SEAL_READY
    assert "honest Shell exit foundation" in result.final_seal_result.sealed_as
    assert "Shell product LIVE" in result.final_seal_result.not_sealed_as
    assert "arbitrary command execution" in result.final_seal_result.not_sealed_as
    assert "safe sandbox" in result.final_seal_result.not_sealed_as
    assert result.p2_vslice_a_truth_label is ShellExitTruthLabel.PREFLIGHT_ONLY
    assert_p2_vslice_a_remains_preflight_in_p29d(result)
    assert_p2_9_d_no_scope_expansion(result)
