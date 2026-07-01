"""Tests for P2.9-B Shell Exit validation matrix contracts."""

from __future__ import annotations

import json

import pytest

from agentic_runtime.aurel_shell.shell_exit_readiness import (
    P2_9_B_CHECKPOINT_IDS,
    ShellExitCheckpointStatus,
    ShellExitTruthLabel,
    ShellExitValidationCheck,
    ShellExitValidationStatus,
    assert_validation_matrix_does_not_promote_not_run_or_unavailable,
    build_p2_9_b_evidence_refs,
    build_shell_exit_validation_matrix,
)


def _roundtrip(obj) -> dict:
    return json.loads(json.dumps(obj.to_canonical_dict(), sort_keys=True))


def test_validation_matrix_exists_for_each_checkpoint() -> None:
    for checkpoint_id in P2_9_B_CHECKPOINT_IDS:
        matrix = build_shell_exit_validation_matrix(checkpoint_id)
        assert matrix.status is ShellExitCheckpointStatus.DONE
        assert matrix.required_check_ids
        assert matrix.pass_check_ids
        assert matrix.unavailable_check_ids
        assert matrix.not_run_check_ids == ()
        assert_validation_matrix_does_not_promote_not_run_or_unavailable(matrix)
        assert _roundtrip(matrix)


def test_validation_matrix_distinguishes_pass_fail_not_run_unavailable_and_na() -> None:
    refs = build_p2_9_b_evidence_refs()
    checks = (
        ShellExitValidationCheck(
            check_id="pass",
            checkpoint_id="P2.9.7",
            description="passing check",
            required=True,
            status=ShellExitValidationStatus.PASS,
            truth_label=ShellExitTruthLabel.CONTRACT_ONLY,
            evidence_refs=(refs[0],),
            failure_reason="",
            notes=(),
            check_hash="test-pass",
        ),
        ShellExitValidationCheck(
            check_id="fail",
            checkpoint_id="P2.9.7",
            description="failing optional check",
            required=False,
            status=ShellExitValidationStatus.FAIL,
            truth_label=ShellExitTruthLabel.ERROR,
            evidence_refs=(refs[0],),
            failure_reason="expected test fixture failure",
            notes=(),
            check_hash="test-fail",
        ),
        ShellExitValidationCheck(
            check_id="not_run",
            checkpoint_id="P2.9.7",
            description="not run optional check",
            required=False,
            status=ShellExitValidationStatus.NOT_RUN,
            truth_label=ShellExitTruthLabel.READ_ONLY,
            evidence_refs=(refs[0],),
            failure_reason="",
            notes=(),
            check_hash="test-not-run",
        ),
        ShellExitValidationCheck(
            check_id="unavailable",
            checkpoint_id="P2.9.7",
            description="unavailable optional check",
            required=False,
            status=ShellExitValidationStatus.UNAVAILABLE,
            truth_label=ShellExitTruthLabel.UNAVAILABLE,
            evidence_refs=(refs[0],),
            failure_reason="",
            notes=(),
            check_hash="test-unavailable",
        ),
        ShellExitValidationCheck(
            check_id="na",
            checkpoint_id="P2.9.7",
            description="not applicable optional check",
            required=False,
            status=ShellExitValidationStatus.N_A,
            truth_label=ShellExitTruthLabel.READ_ONLY,
            evidence_refs=(refs[0],),
            failure_reason="",
            notes=(),
            check_hash="test-na",
        ),
    )
    matrix = build_shell_exit_validation_matrix("P2.9.7", checks=checks)
    assert matrix.status is ShellExitCheckpointStatus.DONE
    assert matrix.pass_check_ids == ("pass",)
    assert matrix.fail_check_ids == ("fail",)
    assert matrix.not_run_check_ids == ("not_run",)
    assert matrix.unavailable_check_ids == ("unavailable",)
    assert "not_run" not in matrix.pass_check_ids
    assert "unavailable" not in matrix.pass_check_ids
    assert_validation_matrix_does_not_promote_not_run_or_unavailable(matrix)


def test_required_not_run_keeps_matrix_partial_not_pass() -> None:
    refs = build_p2_9_b_evidence_refs()
    check = ShellExitValidationCheck(
        check_id="required_not_run",
        checkpoint_id="P2.9.7",
        description="required check not run",
        required=True,
        status=ShellExitValidationStatus.NOT_RUN,
        truth_label=ShellExitTruthLabel.READ_ONLY,
        evidence_refs=(refs[0],),
        failure_reason="validation not run",
        notes=(),
        check_hash="test-required-not-run",
    )
    matrix = build_shell_exit_validation_matrix("P2.9.7", checks=(check,))
    assert matrix.status is ShellExitCheckpointStatus.PARTIAL
    assert matrix.pass_check_ids == ()
    assert matrix.not_run_check_ids == ("required_not_run",)


def test_validation_matrix_rejects_out_of_scope_checkpoint() -> None:
    with pytest.raises(ValueError):
        build_shell_exit_validation_matrix("P2.10.0")
