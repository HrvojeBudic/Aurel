"""P3-FLOW-F runtime checkpoint reference / snapshot layer (P3.14.0-P3.14.9).

A checkpoint names a runtime state point; it never persists that point
externally, never writes Trace or Ledger, and never executes anything.
A checkpoint snapshot is a deterministic local read-model envelope over an
already-existing ``WorkflowRun`` (optionally bound to its event stream,
commitments, realized graph, and topology snapshot). Snapshot is not
production storage and not proof. External persistence, execution, and
verified replay belong to P4 AurelExec / P5 AurelTrace.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping

from .errors import AurelFlowErrorCode, AurelFlowValidationError
from .flow_dynamic_graph import RealizedRuntimeGraph
from .flow_topology import RuntimeTopologySnapshot
from .runtime_events import RuntimeEventStream
from .state_commitment import RuntimeStateCommitment
from .types import _CanonicalMixin, stable_hash
from .workflow_state import WorkflowRun

AUREL_FLOW_F_PACK_ID = "P3-FLOW-F"
AUREL_FLOW_F_PACK_TITLE = (
    "Reversible Runtime State / Fork / Checkpoint / Replay Contracts Pack"
)
AUREL_FLOW_F_REPORT_PATH = "agent/reports/P3_FLOW_F_REVERSIBLE_RUNTIME_STATE_PACK.md"

RUNTIME_CHECKPOINT_REF_VERSION = "runtime_checkpoint_ref.v1"
RUNTIME_CHECKPOINT_BOUNDARY_VERSION = "runtime_checkpoint_boundary.v1"
RUNTIME_CHECKPOINT_SNAPSHOT_VERSION = "runtime_checkpoint_snapshot.v1"
CHECKPOINT_STATE_ENVELOPE_VERSION = "checkpoint_state_envelope.v1"
CHECKPOINT_SNAPSHOT_READ_MODEL_VERSION = "checkpoint_snapshot_read_model.v1"
CHECKPOINT_SERIALIZATION_CONTRACT_VERSION = "checkpoint_serialization_contract.v1"

CHECKPOINT_PERSISTENCE_UNAVAILABLE_REASON = (
    "a checkpoint names a runtime state point in memory only; no database, "
    "event store, file, or external persistence exists in P3-FLOW-F"
)
CHECKPOINT_PROOF_UNAVAILABLE_REASON = (
    "a checkpoint snapshot is a local deterministic read-model envelope, not "
    "a trace record and not proof; the evidence spine belongs to P5 AurelTrace"
)


def _forbid_true(obj: object, *boundary_fields: str) -> None:
    for boundary_field in boundary_fields:
        if getattr(obj, boundary_field):
            raise AurelFlowValidationError(
                f"{type(obj).__name__}.{boundary_field} must remain False",
                code=AurelFlowErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                field=boundary_field,
            )


def _forbid_false(obj: object, *boundary_fields: str) -> None:
    for boundary_field in boundary_fields:
        if not getattr(obj, boundary_field):
            raise AurelFlowValidationError(
                f"{type(obj).__name__}.{boundary_field} must remain True",
                code=AurelFlowErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                field=boundary_field,
            )


class RuntimeCheckpointKind(str, Enum):
    """Where in the runtime lifecycle a checkpoint sits. Naming executes nothing."""

    RUN_CREATED = "RUN_CREATED"
    BEFORE_NODE_READY = "BEFORE_NODE_READY"
    BEFORE_EXECUTION_PROPOSAL = "BEFORE_EXECUTION_PROPOSAL"
    BEFORE_OPERATOR_REVIEW = "BEFORE_OPERATOR_REVIEW"
    BEFORE_GRAPH_REVISION = "BEFORE_GRAPH_REVISION"
    BEFORE_RECOVERY = "BEFORE_RECOVERY"
    BEFORE_RETRY = "BEFORE_RETRY"
    BEFORE_ROLLBACK_CANDIDATE = "BEFORE_ROLLBACK_CANDIDATE"
    AFTER_PAUSE = "AFTER_PAUSE"
    AFTER_INTERNAL_COMMITMENT = "AFTER_INTERNAL_COMMITMENT"
    MANUAL_OPERATOR_MARKER = "MANUAL_OPERATOR_MARKER"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"


class RuntimeCheckpointReason(str, Enum):
    """Why a checkpoint was named. A reason is bookkeeping, not authority."""

    SCHEDULED_BOUNDARY = "SCHEDULED_BOUNDARY"
    OPERATOR_REQUESTED = "OPERATOR_REQUESTED"
    RECOVERY_PREPARATION = "RECOVERY_PREPARATION"
    RETRY_PREPARATION = "RETRY_PREPARATION"
    GRAPH_REVISION_PREPARATION = "GRAPH_REVISION_PREPARATION"
    FORK_CANDIDATE_PREPARATION = "FORK_CANDIDATE_PREPARATION"
    REPLAY_PLAN_PREPARATION = "REPLAY_PLAN_PREPARATION"
    DIAGNOSTIC_MARKER = "DIAGNOSTIC_MARKER"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"


class CheckpointTruthLabel(str, Enum):
    """Honest checkpoint truth labels.

    Deliberately closed-world: there is no LIVE and no TRACE_VERIFIED member,
    so a checkpoint structurally cannot claim live or trace-verified truth.
    """

    LOCAL_CHECKPOINT_ONLY = "LOCAL_CHECKPOINT_ONLY"
    CONTRACT_ONLY = "CONTRACT_ONLY"
    READ_MODEL_ONLY = "READ_MODEL_ONLY"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"


@dataclass(frozen=True)
class RuntimeCheckpointRef(_CanonicalMixin):
    """Stable local reference to a runtime state point. Not persistence."""

    checkpoint_id: str
    contract_version: str
    run_id: str
    checkpoint_kind: RuntimeCheckpointKind
    checkpoint_reason: RuntimeCheckpointReason
    created_by: str
    created_at_logical_sequence: int
    truth_label: CheckpointTruthLabel
    node_id: str = ""
    source_event_id: str = ""
    source_commitment_id: str = ""
    source_topology_snapshot_id: str = ""
    unavailable_reason: str = CHECKPOINT_PERSISTENCE_UNAVAILABLE_REASON
    persisted: bool = False
    external_persistence: bool = False
    trace_verified: bool = False
    ledger_written: bool = False
    execution_available: bool = False

    def __post_init__(self) -> None:
        _forbid_true(
            self,
            "persisted",
            "external_persistence",
            "trace_verified",
            "ledger_written",
            "execution_available",
        )


def create_runtime_checkpoint_ref(
    run: WorkflowRun,
    *,
    checkpoint_kind: RuntimeCheckpointKind,
    checkpoint_reason: RuntimeCheckpointReason,
    created_by: str,
    node_id: str = "",
    source_event_id: str = "",
    source_commitment_id: str = "",
    source_topology_snapshot_id: str = "",
) -> RuntimeCheckpointRef:
    """Name a runtime state point. Pure derivation over the run; no mutation,
    no persistence, no Trace/Ledger write. The logical sequence anchor is the
    run's own monotonic step counter, never a wall clock."""

    payload = {
        "contract_version": RUNTIME_CHECKPOINT_REF_VERSION,
        "run_id": run.run_id,
        "checkpoint_kind": checkpoint_kind.value,
        "checkpoint_reason": checkpoint_reason.value,
        "created_by": created_by,
        "created_at_logical_sequence": run.state.step,
        "node_id": node_id,
        "source_event_id": source_event_id,
        "source_commitment_id": source_commitment_id,
        "source_topology_snapshot_id": source_topology_snapshot_id,
    }
    checkpoint_id = "flckp-" + stable_hash(payload)[:16]
    return RuntimeCheckpointRef(
        checkpoint_id=checkpoint_id,
        contract_version=RUNTIME_CHECKPOINT_REF_VERSION,
        run_id=run.run_id,
        checkpoint_kind=checkpoint_kind,
        checkpoint_reason=checkpoint_reason,
        created_by=created_by,
        created_at_logical_sequence=run.state.step,
        truth_label=CheckpointTruthLabel.LOCAL_CHECKPOINT_ONLY,
        node_id=node_id,
        source_event_id=source_event_id,
        source_commitment_id=source_commitment_id,
        source_topology_snapshot_id=source_topology_snapshot_id,
    )


@dataclass(frozen=True)
class RuntimeCheckpointBoundary(_CanonicalMixin):
    """The checkpoint law as a fail-closed structural object."""

    boundary_version: str
    truth_label: CheckpointTruthLabel
    boundary_hash: str
    unavailable_reason: str = CHECKPOINT_PERSISTENCE_UNAVAILABLE_REASON
    checkpoint_is_not_persistence: bool = True
    checkpoint_is_not_trace: bool = True
    checkpoint_is_not_proof: bool = True
    checkpoint_writes_trace: bool = False
    checkpoint_writes_ledger: bool = False
    checkpoint_executes: bool = False

    def __post_init__(self) -> None:
        _forbid_false(
            self,
            "checkpoint_is_not_persistence",
            "checkpoint_is_not_trace",
            "checkpoint_is_not_proof",
        )
        _forbid_true(
            self,
            "checkpoint_writes_trace",
            "checkpoint_writes_ledger",
            "checkpoint_executes",
        )


def build_runtime_checkpoint_boundary() -> RuntimeCheckpointBoundary:
    payload = {"boundary_version": RUNTIME_CHECKPOINT_BOUNDARY_VERSION}
    return RuntimeCheckpointBoundary(
        boundary_version=RUNTIME_CHECKPOINT_BOUNDARY_VERSION,
        truth_label=CheckpointTruthLabel.CONTRACT_ONLY,
        boundary_hash=stable_hash(payload),
    )


@dataclass(frozen=True)
class CheckpointStateEnvelope(_CanonicalMixin):
    """Deterministic read-only capture of a run's state map at a checkpoint."""

    state_envelope_id: str
    contract_version: str
    run_id: str
    checkpoint_id: str
    lifecycle_status: str
    node_states: Mapping[str, str]
    step: int
    transition_count: int
    truth_label: CheckpointTruthLabel
    envelope_hash: str
    unavailable_reason: str = CHECKPOINT_PERSISTENCE_UNAVAILABLE_REASON
    read_only: bool = True
    mutation_available: bool = False
    external_persistence: bool = False

    def __post_init__(self) -> None:
        _forbid_false(self, "read_only")
        _forbid_true(self, "mutation_available", "external_persistence")


def build_checkpoint_state_envelope(
    run: WorkflowRun, checkpoint_ref: RuntimeCheckpointRef
) -> CheckpointStateEnvelope:
    """Capture the run's current state map into an immutable envelope."""

    if run.run_id != checkpoint_ref.run_id:
        raise AurelFlowValidationError(
            f"run {run.run_id!r} does not match checkpoint run "
            f"{checkpoint_ref.run_id!r}",
            code=AurelFlowErrorCode.RUN_MISMATCH,
            field="run",
        )
    node_states = {
        node_id: state.value for node_id, state in run.state.node_states.items()
    }
    payload = {
        "contract_version": CHECKPOINT_STATE_ENVELOPE_VERSION,
        "run_id": run.run_id,
        "checkpoint_id": checkpoint_ref.checkpoint_id,
        "lifecycle_status": run.state.lifecycle_status.value,
        "node_states": node_states,
        "step": run.state.step,
        "transition_count": len(run.history),
    }
    return CheckpointStateEnvelope(
        state_envelope_id="flcse-" + stable_hash(payload)[:16],
        contract_version=CHECKPOINT_STATE_ENVELOPE_VERSION,
        run_id=run.run_id,
        checkpoint_id=checkpoint_ref.checkpoint_id,
        lifecycle_status=run.state.lifecycle_status.value,
        node_states=node_states,
        step=run.state.step,
        transition_count=len(run.history),
        truth_label=CheckpointTruthLabel.LOCAL_CHECKPOINT_ONLY,
        envelope_hash=stable_hash(payload),
    )


@dataclass(frozen=True)
class RuntimeCheckpointSnapshot(_CanonicalMixin):
    """Local deterministic snapshot envelope. Not storage. Not Trace. Not proof."""

    snapshot_id: str
    contract_version: str
    checkpoint_ref_id: str
    state_envelope_id: str
    run_id: str
    workflow_state_step: int
    lifecycle_status: str
    event_count: int
    node_state_count: int
    commitment_count: int
    truth_label: CheckpointTruthLabel
    snapshot_hash: str
    runtime_event_stream_id: str = ""
    realized_graph_id: str = ""
    topology_snapshot_id: str = ""
    topology_version_number: int = 0
    source_event_id: str = ""
    source_commitment_id: str = ""
    unavailable_reason: str = CHECKPOINT_PROOF_UNAVAILABLE_REASON
    metadata: Mapping[str, str] = field(default_factory=dict)
    persisted: bool = False
    external_persistence: bool = False
    proof_available: bool = False
    trace_verified: bool = False

    def __post_init__(self) -> None:
        _forbid_true(
            self,
            "persisted",
            "external_persistence",
            "proof_available",
            "trace_verified",
        )


def build_runtime_checkpoint_snapshot(
    *,
    checkpoint_ref: RuntimeCheckpointRef,
    run: WorkflowRun,
    state_envelope: CheckpointStateEnvelope,
    event_stream: RuntimeEventStream | None = None,
    realized_graph: RealizedRuntimeGraph | None = None,
    topology_snapshot: RuntimeTopologySnapshot | None = None,
    commitments: tuple[RuntimeStateCommitment, ...] = (),
    metadata: Mapping[str, str] | None = None,
) -> RuntimeCheckpointSnapshot:
    """Bind a checkpoint to run/event/commitment/graph/topology state.

    Pure derivation over already-existing objects: nothing is mutated,
    nothing is persisted, nothing executes, nothing is proven.
    """

    if run.run_id != checkpoint_ref.run_id:
        raise AurelFlowValidationError(
            f"run {run.run_id!r} does not match checkpoint run "
            f"{checkpoint_ref.run_id!r}",
            code=AurelFlowErrorCode.RUN_MISMATCH,
            field="run",
        )
    if state_envelope.run_id != run.run_id:
        raise AurelFlowValidationError(
            f"state envelope run {state_envelope.run_id!r} does not match run "
            f"{run.run_id!r}",
            code=AurelFlowErrorCode.RUN_MISMATCH,
            field="state_envelope",
        )
    if realized_graph is not None and realized_graph.run_id != run.run_id:
        raise AurelFlowValidationError(
            f"realized graph run {realized_graph.run_id!r} does not match run "
            f"{run.run_id!r}",
            code=AurelFlowErrorCode.GRAPH_RUN_MISMATCH,
            field="realized_graph",
        )
    if topology_snapshot is not None and topology_snapshot.run_id != run.run_id:
        raise AurelFlowValidationError(
            f"topology snapshot run {topology_snapshot.run_id!r} does not "
            f"match run {run.run_id!r}",
            code=AurelFlowErrorCode.GRAPH_RUN_MISMATCH,
            field="topology_snapshot",
        )
    event_count = len(event_stream.events) if event_stream is not None else 0
    payload = {
        "contract_version": RUNTIME_CHECKPOINT_SNAPSHOT_VERSION,
        "checkpoint_ref_id": checkpoint_ref.checkpoint_id,
        "state_envelope_id": state_envelope.state_envelope_id,
        "run_id": run.run_id,
        "workflow_state_step": run.state.step,
        "event_count": event_count,
        "commitment_count": len(commitments),
        "envelope_hash": state_envelope.envelope_hash,
    }
    return RuntimeCheckpointSnapshot(
        snapshot_id="flcsn-" + stable_hash(payload)[:16],
        contract_version=RUNTIME_CHECKPOINT_SNAPSHOT_VERSION,
        checkpoint_ref_id=checkpoint_ref.checkpoint_id,
        state_envelope_id=state_envelope.state_envelope_id,
        run_id=run.run_id,
        workflow_state_step=run.state.step,
        lifecycle_status=run.state.lifecycle_status.value,
        event_count=event_count,
        node_state_count=len(run.state.node_states),
        commitment_count=len(commitments),
        truth_label=CheckpointTruthLabel.LOCAL_CHECKPOINT_ONLY,
        snapshot_hash=stable_hash(payload),
        runtime_event_stream_id=(
            event_stream.stream_id if event_stream is not None else ""
        ),
        realized_graph_id=(
            realized_graph.realized_graph_id if realized_graph is not None else ""
        ),
        topology_snapshot_id=(
            topology_snapshot.snapshot_id if topology_snapshot is not None else ""
        ),
        topology_version_number=(
            topology_snapshot.topology_version.version_number
            if topology_snapshot is not None
            else 0
        ),
        source_event_id=checkpoint_ref.source_event_id,
        source_commitment_id=checkpoint_ref.source_commitment_id,
        metadata=dict(metadata or {}),
    )


@dataclass(frozen=True)
class RuntimeCheckpointSnapshotRef(_CanonicalMixin):
    """Stable reference to a checkpoint snapshot."""

    snapshot_id: str
    checkpoint_ref_id: str
    run_id: str


def runtime_checkpoint_snapshot_ref(
    snapshot: RuntimeCheckpointSnapshot,
) -> RuntimeCheckpointSnapshotRef:
    return RuntimeCheckpointSnapshotRef(
        snapshot_id=snapshot.snapshot_id,
        checkpoint_ref_id=snapshot.checkpoint_ref_id,
        run_id=snapshot.run_id,
    )


@dataclass(frozen=True)
class RuntimeCheckpointSnapshotReadModel(_CanonicalMixin):
    """Deterministic snapshot projection. Not persistence. Not proof."""

    read_model_version: str
    snapshot_id: str
    run_id: str
    checkpoint_kind: str
    workflow_state_step: int
    event_count: int
    node_state_count: int
    commitment_count: int
    has_topology_binding: bool
    truth_label: CheckpointTruthLabel
    read_model_hash: str
    snapshot_is_not_persistence: bool = True
    snapshot_is_not_trace: bool = True
    snapshot_is_not_proof: bool = True
    trace_verified: bool = False

    def __post_init__(self) -> None:
        _forbid_false(
            self,
            "snapshot_is_not_persistence",
            "snapshot_is_not_trace",
            "snapshot_is_not_proof",
        )
        _forbid_true(self, "trace_verified")


def build_runtime_checkpoint_snapshot_read_model(
    snapshot: RuntimeCheckpointSnapshot, checkpoint_ref: RuntimeCheckpointRef
) -> RuntimeCheckpointSnapshotReadModel:
    if snapshot.checkpoint_ref_id != checkpoint_ref.checkpoint_id:
        raise AurelFlowValidationError(
            f"snapshot checkpoint {snapshot.checkpoint_ref_id!r} does not "
            f"match checkpoint {checkpoint_ref.checkpoint_id!r}",
            code=AurelFlowErrorCode.RUN_MISMATCH,
            field="checkpoint_ref",
        )
    payload = {
        "read_model_version": CHECKPOINT_SNAPSHOT_READ_MODEL_VERSION,
        "snapshot_hash": snapshot.snapshot_hash,
    }
    return RuntimeCheckpointSnapshotReadModel(
        read_model_version=CHECKPOINT_SNAPSHOT_READ_MODEL_VERSION,
        snapshot_id=snapshot.snapshot_id,
        run_id=snapshot.run_id,
        checkpoint_kind=checkpoint_ref.checkpoint_kind.value,
        workflow_state_step=snapshot.workflow_state_step,
        event_count=snapshot.event_count,
        node_state_count=snapshot.node_state_count,
        commitment_count=snapshot.commitment_count,
        has_topology_binding=bool(snapshot.topology_snapshot_id),
        truth_label=CheckpointTruthLabel.READ_MODEL_ONLY,
        read_model_hash=stable_hash(payload),
    )


@dataclass(frozen=True)
class CheckpointSerializationContract(_CanonicalMixin):
    """Deterministic serialization posture for checkpoint objects.

    Serialization readiness is not storage: no database, event store, or
    external persistence backend exists or is claimed.
    """

    contract_id: str
    contract_version: str
    schema_name: str
    schema_version: str
    truth_label: CheckpointTruthLabel
    contract_hash: str
    unavailable_reason: str = CHECKPOINT_PERSISTENCE_UNAVAILABLE_REASON
    deterministic_serialization: bool = True
    stable_ids_required: bool = True
    canonical_json: bool = True
    external_persistence: bool = False
    database_backend: bool = False
    event_store_backend: bool = False

    def __post_init__(self) -> None:
        _forbid_false(
            self,
            "deterministic_serialization",
            "stable_ids_required",
            "canonical_json",
        )
        _forbid_true(
            self, "external_persistence", "database_backend", "event_store_backend"
        )


def build_checkpoint_serialization_contract(
    *, schema_name: str = "aurel_flow.checkpoint", schema_version: str = "v1"
) -> CheckpointSerializationContract:
    payload = {
        "contract_version": CHECKPOINT_SERIALIZATION_CONTRACT_VERSION,
        "schema_name": schema_name,
        "schema_version": schema_version,
    }
    return CheckpointSerializationContract(
        contract_id="flcsc-" + stable_hash(payload)[:16],
        contract_version=CHECKPOINT_SERIALIZATION_CONTRACT_VERSION,
        schema_name=schema_name,
        schema_version=schema_version,
        truth_label=CheckpointTruthLabel.CONTRACT_ONLY,
        contract_hash=stable_hash(payload),
    )
