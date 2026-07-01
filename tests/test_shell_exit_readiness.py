"""Tests for P2.9-B Shell Exit readiness contracts."""

from __future__ import annotations

import json

import pytest

from agentic_runtime.aurel_shell.shell_exit_readiness import (
    P2_9_B_CHECKPOINT_IDS,
    P2_9_B_COVERED_RANGE,
    P2_9_B_PACK_ID,
    P2_9_B_WORKING_LABELS,
    ShellExitCheckpointStatus,
    ShellExitReadinessDimension,
    ShellExitTruthLabel,
    assert_old_p2_9_b_remains_overlay,
    assert_p2_9_b_no_scope_expansion,
    assert_readiness_contract_required_dimensions_gate_done,
    build_p2_9_b_evidence_refs,
    build_p2_9_b_shell_exit_readiness_result,
    build_shell_exit_readiness_contract,
)


def _roundtrip(obj) -> dict:
    return json.loads(json.dumps(obj.to_canonical_dict(), sort_keys=True))


def test_p2_9_b_constants_and_working_labels_are_scoped() -> None:
    assert P2_9_B_PACK_ID == "P2.9-B"
    assert P2_9_B_COVERED_RANGE == "P2.9.6-P2.9.10"
    assert P2_9_B_CHECKPOINT_IDS == ("P2.9.6", "P2.9.7", "P2.9.8", "P2.9.9", "P2.9.10")
    assert P2_9_B_WORKING_LABELS["P2.9.6"] == "Shell Exit Readiness Contract"
    assert P2_9_B_WORKING_LABELS["P2.9.10"] == "Integration Tail / P2.9-C Handoff Contract"


def test_readiness_contract_exists_for_each_p2_9_b_checkpoint() -> None:
    for checkpoint_id in P2_9_B_CHECKPOINT_IDS:
        contract = build_shell_exit_readiness_contract(checkpoint_id)
        assert contract.status is ShellExitCheckpointStatus.DONE
        assert contract.checkpoint_id == checkpoint_id
        assert contract.working_label == P2_9_B_WORKING_LABELS[checkpoint_id]
        assert "Shell LIVE" in contract.forbidden_claims
        assert "arbitrary command execution" in contract.forbidden_claims
        assert contract.required_dimensions
        assert_readiness_contract_required_dimensions_gate_done(contract)
        assert _roundtrip(contract)


def test_readiness_contract_rejects_missing_required_evidence_for_done() -> None:
    refs = build_p2_9_b_evidence_refs()
    broken_dimension = ShellExitReadinessDimension(
        dimension_id="TEST_EVIDENCE",
        checkpoint_id="P2.9.6",
        required=True,
        status=ShellExitCheckpointStatus.PARTIAL,
        truth_label=ShellExitTruthLabel.CONTRACT_ONLY,
        evidence_refs=(refs[0],),
        failure_reason="focused test evidence missing",
        notes=(),
        dimension_hash="test-hash",
    )
    contract = build_shell_exit_readiness_contract("P2.9.6", dimensions=(broken_dimension,))
    assert contract.status is ShellExitCheckpointStatus.PARTIAL
    assert contract.status is not ShellExitCheckpointStatus.DONE
    assert_readiness_contract_required_dimensions_gate_done(contract)


def test_readiness_contract_rejects_out_of_scope_checkpoint() -> None:
    with pytest.raises(ValueError):
        build_shell_exit_readiness_contract("P2.9.11")


def test_evidence_refs_keep_old_overlay_and_preflight_truth() -> None:
    refs = {ref.ref_id: ref for ref in build_p2_9_b_evidence_refs()}
    assert refs["old_p2_9_b_overlay"].truth_label is ShellExitTruthLabel.EVIDENCE_SEALED
    assert refs["p2_vslice_a_preflight"].truth_label is ShellExitTruthLabel.PREFLIGHT_ONLY
    assert refs["p2_9_b_r1_coverage_matrix"].commit == "0ce98df"


def test_p2_9_b_result_side_effects_all_false_and_overlay_retained() -> None:
    result = build_p2_9_b_shell_exit_readiness_result()
    assert_old_p2_9_b_remains_overlay(result)
    assert_p2_9_b_no_scope_expansion(result)
    assert all(value is False for value in result.side_effect_proof.to_canonical_dict().values())
    assert result.old_p2_9_b_retained_as_overlay is True
    assert result.p2_vslice_a_truth_label is ShellExitTruthLabel.PREFLIGHT_ONLY
