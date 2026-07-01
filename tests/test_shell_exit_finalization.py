"""Tests for P2.9-C Shell Exit finalization intake and aggregation."""

from __future__ import annotations

import json
from dataclasses import replace

import pytest

from agentic_runtime.aurel_shell.shell_exit_finalization import (
    P2_9_C_CHECKPOINT_IDS,
    P2_9_C_COVERED_RANGE,
    P2_9_C_PACK_ID,
    P2_9_C_WORKING_LABELS,
    ShellExitDecisionStatus,
    ShellExitFinalizationStatus,
    assert_p2_9_c_aggregate_does_not_claim_p2_complete,
    assert_p2_9_c_prerequisite_gate_passed,
    build_p2_9_c_shell_exit_finalization_result,
    build_shell_exit_decision_aggregate,
    build_shell_exit_finalization_intake,
    build_shell_exit_seal_decisions,
)
from agentic_runtime.aurel_shell.shell_exit_readiness import (
    P2_9_B_CHECKPOINT_IDS,
    P2_9_B_REPORT_PATH,
    ShellExitTruthLabel,
    build_p2_9_b_shell_exit_readiness_result,
)


def _roundtrip(obj) -> dict:
    return json.loads(json.dumps(obj.to_canonical_dict(), sort_keys=True))


def test_p2_9_c_constants_and_working_labels_are_scoped() -> None:
    assert P2_9_C_PACK_ID == "P2.9-C"
    assert P2_9_C_COVERED_RANGE == "P2.9.11-P2.9.15"
    assert P2_9_C_CHECKPOINT_IDS == ("P2.9.11", "P2.9.12", "P2.9.13", "P2.9.14", "P2.9.15")
    assert P2_9_C_WORKING_LABELS["P2.9.11"] == "Shell Exit Finalization Intake"
    assert P2_9_C_WORKING_LABELS["P2.9.15"] == "P2.9-D Final Tail Handoff Contract"


def test_finalization_intake_consumes_true_p2_9_b_and_prior_evidence() -> None:
    intake = build_shell_exit_finalization_intake()
    assert intake.intake_status is ShellExitFinalizationStatus.C_READY_FOR_D
    assert intake.p29b_result_ref == P2_9_B_REPORT_PATH
    assert "P2.9.0-P2.9.5" in intake.completed_ranges
    assert "P2.9.6-P2.9.10" in intake.completed_ranges
    assert "P2.9.16-P2.9.20" in intake.not_done_ranges
    assert "P2.10+" in intake.not_done_ranges
    assert intake.prior_checkpoint_seals == P2_9_B_CHECKPOINT_IDS
    assert_p2_9_c_prerequisite_gate_passed(intake)
    assert _roundtrip(intake)


def test_finalization_intake_blocks_when_true_p2_9_b_is_incomplete() -> None:
    p29b = build_p2_9_b_shell_exit_readiness_result()
    incomplete = replace(
        p29b,
        done_checkpoints=("P2.9.6", "P2.9.7"),
        partial_checkpoints=("P2.9.8", "P2.9.9", "P2.9.10"),
    )
    intake = build_shell_exit_finalization_intake(incomplete)
    assert intake.intake_status is ShellExitFinalizationStatus.C_BLOCKED
    assert "true P2.9-B" in intake.failure_reason
    with pytest.raises(ValueError):
        assert_p2_9_c_prerequisite_gate_passed(intake)


def test_seal_decisions_exist_for_each_p2_9_c_checkpoint() -> None:
    decisions = build_shell_exit_seal_decisions()
    assert tuple(decision.checkpoint_id for decision in decisions) == P2_9_C_CHECKPOINT_IDS
    for decision in decisions:
        assert decision.decision_status is ShellExitDecisionStatus.SEALED
        assert decision.working_label == P2_9_C_WORKING_LABELS[decision.checkpoint_id]
        assert decision.blockers
        assert decision.boundaries
        assert "P2.9-C can produce C_READY_FOR_D but not P2_COMPLETE." in decision.notes
        assert _roundtrip(decision)


def test_seal_aggregation_can_be_c_ready_for_d_but_not_p2_complete() -> None:
    aggregate = build_shell_exit_decision_aggregate()
    assert aggregate.aggregate_status is ShellExitFinalizationStatus.C_READY_FOR_D
    assert aggregate.sealed_checkpoints == P2_9_C_CHECKPOINT_IDS
    assert aggregate.can_claim_p2_complete is False
    assert aggregate.can_start_p210 is False
    assert_p2_9_c_aggregate_does_not_claim_p2_complete(aggregate)


def test_result_truth_labels_and_no_scope_side_effects() -> None:
    result = build_p2_9_c_shell_exit_finalization_result()
    assert result.p2_vslice_a_truth_label is ShellExitTruthLabel.PREFLIGHT_ONLY
    assert result.p29d_next is True
    assert result.p210_allowed is False
    assert all(value is False for value in result.side_effect_proof.to_canonical_dict().values())
