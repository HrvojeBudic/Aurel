"""P4-EXEC-C ExecutionCheckpointRef / ExecutionRollbackRef — DeltaBox-lite.

Checkpoint refs record pre/post attempt execution boundaries so later packs
(P4-EXEC-E recovery, P5 verification) have named state boundaries to attach
to. A checkpoint ref is not a checkpoint persistence engine — it names a
boundary and may carry a stable hash of a real local state view, nothing
more. A rollback ref records rollback availability/status only:
``rollback_executed`` is structurally False and rollback execution remains
unavailable until a later recovery pack.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .exec_errors import AurelExecErrorCode, AurelExecValidationError
from .exec_types import (
    ExecTruthLabel,
    _ExecCanonicalMixin,
    forbid_false,
    forbid_true,
    require_allowed_truth_label,
    require_nonempty,
    stable_hash,
)

EXECUTION_CHECKPOINT_REF_VERSION = "execution_checkpoint_ref.v1"
EXECUTION_ROLLBACK_REF_VERSION = "execution_rollback_ref.v1"
NO_ROLLBACK_EXECUTION_PROOF_VERSION = "no_rollback_execution_proof.v1"
NO_RECOVERY_ENGINE_PROOF_VERSION = "no_recovery_engine_proof.v1"

CHECKPOINT_PERSISTENCE_UNAVAILABLE_REASON = (
    "a checkpoint ref names an execution boundary and may carry a stable "
    "hash of a real local state view; no checkpoint persistence engine, "
    "database, or event store exists"
)
ROLLBACK_EXECUTION_UNAVAILABLE_REASON = (
    "rollback execution is unavailable in P4-EXEC-C; a rollback ref records "
    "the boundary and availability status only — rollback execution belongs "
    "to a later bounded-recovery pack (P4-EXEC-E+) under P9 authority"
)
RECOVERY_ENGINE_UNAVAILABLE_REASON = (
    "no recovery engine, retry engine, or failure-repair loop exists in "
    "P4-EXEC-C; failure classification and bounded recovery belong to "
    "P4-EXEC-E using these checkpoint refs and local messages"
)


class ExecutionCheckpointKind(str, Enum):
    PRE_ATTEMPT = "PRE_ATTEMPT"
    POST_ATTEMPT = "POST_ATTEMPT"
    SESSION_SNAPSHOT = "SESSION_SNAPSHOT"
    OUTCOME_SNAPSHOT = "OUTCOME_SNAPSHOT"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"


@dataclass(frozen=True)
class ExecutionCheckpointRef(_ExecCanonicalMixin):
    """A named execution boundary. Not persistence, not rollback."""

    checkpoint_ref_id: str
    exec_job_id: str
    session_id: str
    checkpoint_kind: ExecutionCheckpointKind
    checkpoint_scope: str
    checkpoint_available: bool
    truth_label: ExecTruthLabel
    contract_version: str = EXECUTION_CHECKPOINT_REF_VERSION
    attempt_id: str | None = None
    checkpoint_hash: str | None = None
    created_at_tick: int | None = None
    is_persistence_engine: bool = False
    executes_rollback: bool = False

    def __post_init__(self) -> None:
        require_nonempty(self, "checkpoint_ref_id", code=AurelExecErrorCode.EMPTY_FIELD)
        require_nonempty(self, "exec_job_id", code=AurelExecErrorCode.EMPTY_JOB_ID)
        require_nonempty(self, "session_id", code=AurelExecErrorCode.EMPTY_SESSION_ID)
        require_nonempty(self, "checkpoint_scope", code=AurelExecErrorCode.EMPTY_FIELD)
        require_allowed_truth_label(self)
        forbid_true(self, "is_persistence_engine", "executes_rollback")
        if self.checkpoint_available and self.checkpoint_hash is None:
            raise AurelExecValidationError(
                "an available checkpoint ref requires a real stable hash",
                code=AurelExecErrorCode.CHECKPOINT_INVALID,
                field="checkpoint_hash",
            )


def _build_checkpoint_ref(
    kind: ExecutionCheckpointKind,
    *,
    exec_job_id: str,
    session_id: str,
    attempt_id: str | None,
    checkpoint_scope: str,
    snapshot_source: object,
    truth_label: ExecTruthLabel,
    created_at_tick: int | None,
) -> ExecutionCheckpointRef:
    checkpoint_hash = stable_hash(snapshot_source) if snapshot_source is not None else None
    checkpoint_ref_id = "exec-ckpt-" + stable_hash(
        (kind.value, exec_job_id, attempt_id, created_at_tick)
    )[:16]
    return ExecutionCheckpointRef(
        checkpoint_ref_id=checkpoint_ref_id,
        exec_job_id=exec_job_id,
        session_id=session_id,
        checkpoint_kind=kind,
        checkpoint_scope=checkpoint_scope,
        checkpoint_available=checkpoint_hash is not None,
        truth_label=truth_label,
        attempt_id=attempt_id,
        checkpoint_hash=checkpoint_hash,
        created_at_tick=created_at_tick,
    )


def create_pre_attempt_checkpoint_ref(
    *,
    exec_job_id: str,
    session_id: str,
    attempt_id: str,
    snapshot_source: object,
    truth_label: ExecTruthLabel,
    created_at_tick: int | None = None,
) -> ExecutionCheckpointRef:
    """Record the pre-attempt boundary over a real local state view."""
    return _build_checkpoint_ref(
        ExecutionCheckpointKind.PRE_ATTEMPT,
        exec_job_id=exec_job_id,
        session_id=session_id,
        attempt_id=attempt_id,
        checkpoint_scope="local pre-attempt state view (job/lease/session/attempt)",
        snapshot_source=snapshot_source,
        truth_label=truth_label,
        created_at_tick=created_at_tick,
    )


def create_post_attempt_checkpoint_ref(
    *,
    exec_job_id: str,
    session_id: str,
    attempt_id: str,
    snapshot_source: object,
    truth_label: ExecTruthLabel,
    created_at_tick: int | None = None,
) -> ExecutionCheckpointRef:
    """Record the post-attempt outcome boundary over a real local state view."""
    return _build_checkpoint_ref(
        ExecutionCheckpointKind.POST_ATTEMPT,
        exec_job_id=exec_job_id,
        session_id=session_id,
        attempt_id=attempt_id,
        checkpoint_scope="local post-attempt outcome view",
        snapshot_source=snapshot_source,
        truth_label=truth_label,
        created_at_tick=created_at_tick,
    )


@dataclass(frozen=True)
class ExecutionRollbackRef(_ExecCanonicalMixin):
    """Rollback availability/status record. Never rollback execution:
    ``rollback_available`` and ``rollback_executed`` are structurally False
    in P4-EXEC-C."""

    rollback_ref_id: str
    checkpoint_ref_id: str
    exec_job_id: str
    session_id: str
    truth_label: ExecTruthLabel
    contract_version: str = EXECUTION_ROLLBACK_REF_VERSION
    attempt_id: str | None = None
    rollback_available: bool = False
    rollback_executed: bool = False
    rollback_unavailable_reason: str = ROLLBACK_EXECUTION_UNAVAILABLE_REASON

    def __post_init__(self) -> None:
        require_nonempty(self, "rollback_ref_id", code=AurelExecErrorCode.EMPTY_FIELD)
        require_nonempty(self, "checkpoint_ref_id", code=AurelExecErrorCode.EMPTY_FIELD)
        require_nonempty(self, "exec_job_id", code=AurelExecErrorCode.EMPTY_JOB_ID)
        require_nonempty(
            self, "rollback_unavailable_reason", code=AurelExecErrorCode.EMPTY_FIELD
        )
        require_allowed_truth_label(self)
        forbid_true(self, "rollback_available", "rollback_executed")


def create_rollback_ref(
    checkpoint_ref: ExecutionCheckpointRef,
    *,
    truth_label: ExecTruthLabel,
) -> ExecutionRollbackRef:
    """Create a not-executed rollback ref bound to a checkpoint boundary."""
    rollback_ref_id = "exec-rollback-" + stable_hash(checkpoint_ref.checkpoint_ref_id)[:16]
    return ExecutionRollbackRef(
        rollback_ref_id=rollback_ref_id,
        checkpoint_ref_id=checkpoint_ref.checkpoint_ref_id,
        exec_job_id=checkpoint_ref.exec_job_id,
        session_id=checkpoint_ref.session_id,
        truth_label=truth_label,
        attempt_id=checkpoint_ref.attempt_id,
    )


@dataclass(frozen=True)
class NoRollbackExecutionProof(_ExecCanonicalMixin):
    """Evidence that nothing executed a rollback in this pack."""

    reason: str
    future_pack_owner: str
    contract_version: str = NO_ROLLBACK_EXECUTION_PROOF_VERSION
    rollback_executed: bool = False
    rollback_execution_available: bool = False
    checkpoint_persistence_engine_available: bool = False

    def __post_init__(self) -> None:
        forbid_true(
            self,
            "rollback_executed",
            "rollback_execution_available",
            "checkpoint_persistence_engine_available",
        )
        require_nonempty(self, "reason", code=AurelExecErrorCode.EMPTY_FIELD)
        require_nonempty(self, "future_pack_owner", code=AurelExecErrorCode.EMPTY_FIELD)


def build_no_rollback_execution_proof() -> NoRollbackExecutionProof:
    return NoRollbackExecutionProof(
        reason=ROLLBACK_EXECUTION_UNAVAILABLE_REASON,
        future_pack_owner="P4-EXEC-E bounded recovery under P9 authority",
    )


@dataclass(frozen=True)
class NoRecoveryEngineProof(_ExecCanonicalMixin):
    """Evidence that no recovery/retry engine exists in this pack."""

    reason: str
    future_pack_owner: str
    contract_version: str = NO_RECOVERY_ENGINE_PROOF_VERSION
    recovery_engine_available: bool = False
    retry_engine_available: bool = False

    def __post_init__(self) -> None:
        forbid_true(self, "recovery_engine_available", "retry_engine_available")
        require_nonempty(self, "reason", code=AurelExecErrorCode.EMPTY_FIELD)
        require_nonempty(self, "future_pack_owner", code=AurelExecErrorCode.EMPTY_FIELD)


def build_no_recovery_engine_proof() -> NoRecoveryEngineProof:
    return NoRecoveryEngineProof(
        reason=RECOVERY_ENGINE_UNAVAILABLE_REASON,
        future_pack_owner="P4-EXEC-E failure classification / bounded recovery",
    )
