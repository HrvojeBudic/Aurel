"""P4-EXEC-C checkpoint/rollback ref tests — refs, never engines."""

from __future__ import annotations

import dataclasses

import pytest

from agentic_runtime.aurel_exec import (
    AurelExecErrorCode,
    AurelExecValidationError,
    ExecTruthLabel,
    ExecutionCheckpointKind,
    ExecutionCheckpointRef,
    build_no_recovery_engine_proof,
    build_no_rollback_execution_proof,
    create_post_attempt_checkpoint_ref,
    create_pre_attempt_checkpoint_ref,
    create_rollback_ref,
)

_IDS = dict(
    exec_job_id="exec-job-a",
    session_id="exec-session-a",
    attempt_id="exec-attempt-a",
    truth_label=ExecTruthLabel.DEV_FIXTURE,
    created_at_tick=5,
)


def test_pre_and_post_attempt_checkpoint_refs_are_created():
    pre = create_pre_attempt_checkpoint_ref(snapshot_source=("state", 1), **_IDS)
    post = create_post_attempt_checkpoint_ref(snapshot_source=("outcome", 1), **_IDS)
    assert pre.checkpoint_kind is ExecutionCheckpointKind.PRE_ATTEMPT
    assert post.checkpoint_kind is ExecutionCheckpointKind.POST_ATTEMPT
    for ref in (pre, post):
        assert ref.checkpoint_available is True
        assert ref.checkpoint_hash  # real stable hash of the local state view
    # deterministic: same source, same hash
    again = create_pre_attempt_checkpoint_ref(snapshot_source=("state", 1), **_IDS)
    assert again.checkpoint_hash == pre.checkpoint_hash
    assert again.checkpoint_ref_id == pre.checkpoint_ref_id


def test_checkpoint_ref_does_not_claim_persistence_engine():
    pre = create_pre_attempt_checkpoint_ref(snapshot_source=("state", 1), **_IDS)
    assert pre.is_persistence_engine is False
    assert pre.executes_rollback is False
    for boundary_field in ("is_persistence_engine", "executes_rollback"):
        with pytest.raises(AurelExecValidationError):
            dataclasses.replace(pre, **{boundary_field: True})
    for verb in ("persist", "save", "store", "restore", "rollback"):
        assert not hasattr(pre, verb)


def test_available_checkpoint_requires_a_real_hash():
    with pytest.raises(AurelExecValidationError) as excinfo:
        ExecutionCheckpointRef(
            checkpoint_ref_id="exec-ckpt-x",
            exec_job_id="exec-job-a",
            session_id="exec-session-a",
            checkpoint_kind=ExecutionCheckpointKind.PRE_ATTEMPT,
            checkpoint_scope="claims availability without a snapshot hash",
            checkpoint_available=True,
            truth_label=ExecTruthLabel.DEV_FIXTURE,
            checkpoint_hash=None,
        )
    assert excinfo.value.code is AurelExecErrorCode.CHECKPOINT_INVALID


def test_rollback_ref_does_not_execute_rollback():
    pre = create_pre_attempt_checkpoint_ref(snapshot_source=("state", 1), **_IDS)
    rollback = create_rollback_ref(pre, truth_label=ExecTruthLabel.DEV_FIXTURE)
    assert rollback.checkpoint_ref_id == pre.checkpoint_ref_id
    assert rollback.rollback_executed is False
    assert rollback.rollback_available is False
    assert rollback.rollback_unavailable_reason
    for boundary_field in ("rollback_executed", "rollback_available"):
        with pytest.raises(AurelExecValidationError):
            dataclasses.replace(rollback, **{boundary_field: True})
    for verb in ("execute", "rollback", "restore", "revert"):
        assert not hasattr(rollback, verb)


def test_no_rollback_execution_proof_is_fail_closed():
    proof = build_no_rollback_execution_proof()
    assert proof.rollback_executed is False
    assert proof.rollback_execution_available is False
    assert proof.checkpoint_persistence_engine_available is False
    assert "P4-EXEC-E" in proof.future_pack_owner
    for boundary_field in (
        "rollback_executed",
        "rollback_execution_available",
        "checkpoint_persistence_engine_available",
    ):
        with pytest.raises(AurelExecValidationError):
            dataclasses.replace(proof, **{boundary_field: True})


def test_no_recovery_engine_proof_is_fail_closed():
    proof = build_no_recovery_engine_proof()
    assert proof.recovery_engine_available is False
    assert proof.retry_engine_available is False
    assert "P4-EXEC-E" in proof.future_pack_owner
    for boundary_field in ("recovery_engine_available", "retry_engine_available"):
        with pytest.raises(AurelExecValidationError):
            dataclasses.replace(proof, **{boundary_field: True})
