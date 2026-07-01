"""Tests for true P2.9-B Shell Exit checkpoint evidence matrix."""

from __future__ import annotations

import json

from agentic_runtime.aurel_shell.shell_exit_readiness import (
    OLD_P2_9_B_OVERLAY_REPORT_PATH,
    P2_9_B_CHECKPOINT_IDS,
    P2_9_B_NEXT_PACK,
    P2_9_B_NEXT_RANGE,
    P2_VSLICE_A_REPORT_PATH,
    ShellExitCheckpointStatus,
    ShellExitTruthLabel,
    assert_old_p2_9_b_remains_overlay,
    assert_p2_9_b_handoff_points_to_p2_9_c,
    assert_p2_9_b_no_scope_expansion,
    assert_p2_vslice_a_binding_is_preflight_only,
    build_p2_9_b_shell_exit_readiness_result,
    build_p2_vslice_a_evidence_binding,
    build_shell_exit_checkpoint_seal,
    build_shell_exit_evidence_bindings,
    render_p2_9_b_coverage_rows,
    serialize_p2_9_b_result,
)


def test_p2_vslice_a_bound_as_preflight_only_not_execution() -> None:
    binding = build_p2_vslice_a_evidence_binding()
    assert binding.checkpoint_id == "P2.9.8"
    assert binding.source_report == P2_VSLICE_A_REPORT_PATH
    assert binding.truth_label is ShellExitTruthLabel.PREFLIGHT_ONLY
    assert binding.supports_done is True
    assert binding.supports_partial is False
    notes = " ".join(binding.notes).lower()
    assert "shell live" in notes
    assert "command execution" in notes
    assert_p2_vslice_a_binding_is_preflight_only(binding)


def test_checkpoint_seals_created_for_p2_9_6_through_p2_9_10() -> None:
    result = build_p2_9_b_shell_exit_readiness_result()
    assert tuple(seal.checkpoint_id for seal in result.checkpoint_seals) == P2_9_B_CHECKPOINT_IDS
    assert result.done_checkpoints == P2_9_B_CHECKPOINT_IDS
    assert result.partial_checkpoints == ()
    assert result.not_done_checkpoints == ()
    assert result.blocked_checkpoints == ()
    assert result.unavailable_checkpoints == ()
    for seal in result.checkpoint_seals:
        assert seal.status is ShellExitCheckpointStatus.DONE
        assert seal.readiness_dimensions
        assert seal.validation_checks
        assert seal.evidence_bindings
        assert seal.remaining_gaps
        assert json.loads(json.dumps(seal.to_canonical_dict(), sort_keys=True))


def test_p2_9_8_seal_contains_preflight_vertical_slice_binding() -> None:
    seal = build_shell_exit_checkpoint_seal("P2.9.8")
    assert seal.truth_label is ShellExitTruthLabel.PREFLIGHT_ONLY
    assert any(binding.source_report == P2_VSLICE_A_REPORT_PATH for binding in seal.evidence_bindings)
    assert any(binding.truth_label is ShellExitTruthLabel.PREFLIGHT_ONLY for binding in seal.evidence_bindings)
    assert all("Shell LIVE not claimed" in seal.remaining_gaps for _ in (0,))


def test_old_p2_9_b_overlay_remains_evidence_overlay_not_true_implementation() -> None:
    bindings = build_shell_exit_evidence_bindings("P2.9.6")
    overlay = [binding for binding in bindings if binding.source_report == OLD_P2_9_B_OVERLAY_REPORT_PATH]
    assert len(overlay) == 1
    assert overlay[0].truth_label is ShellExitTruthLabel.EVIDENCE_SEALED
    assert "overlay evidence only" in " ".join(overlay[0].notes)


def test_integration_tail_hands_off_to_p2_9_c_not_p2_10() -> None:
    result = build_p2_9_b_shell_exit_readiness_result()
    assert result.integration_tail.next_pack == P2_9_B_NEXT_PACK == "P2.9-C"
    assert result.integration_tail.next_range == P2_9_B_NEXT_RANGE == "P2.9.11-P2.9.15"
    assert result.integration_tail.p29c_handoff_ready is True
    assert result.integration_tail.p29d_handoff_ready is False
    assert result.integration_tail.p210_allowed is False
    assert result.handoff.p29c_status is ShellExitCheckpointStatus.NOT_DONE
    assert result.handoff.p29d_status is ShellExitCheckpointStatus.NOT_DONE
    assert result.handoff.no_p2_10_start_claim is True
    assert_p2_9_b_handoff_points_to_p2_9_c(result)


def test_no_scope_expansion_flags_remain_false() -> None:
    result = build_p2_9_b_shell_exit_readiness_result()
    assert_p2_9_b_no_scope_expansion(result)
    assert_old_p2_9_b_remains_overlay(result)
    proof = result.side_effect_proof.to_canonical_dict()
    assert proof["shell_live_claimed"] is False
    assert proof["command_execution_implemented"] is False
    assert proof["p2_9_c_implemented"] is False
    assert proof["p2_9_d_implemented"] is False
    assert proof["p2_10_started"] is False
    assert proof["old_p2_9_b_deleted"] is False


def test_coverage_rows_and_serialization_are_stable() -> None:
    result = build_p2_9_b_shell_exit_readiness_result()
    rows = render_p2_9_b_coverage_rows(result)
    assert len(rows) == 5
    assert rows[0].startswith("| P2.9.6 |")
    assert "P2.9-C" in rows[-1]
    payload = json.loads(serialize_p2_9_b_result(result))
    assert payload["covered_range"] == "P2.9.6-P2.9.10"
    assert payload["p29c_next"] is True
    assert payload["p210_allowed"] is False
