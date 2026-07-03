"""P4-EXEC-F execution topology profile — control-plane model, not runtime.

An ``ExecutionTopologyProfile`` describes the active local execution shape.
Repo truth: P4-EXEC-C proved exactly one local in-process worker slot, so
the default profile is LOCAL_SINGLE_SLOT. A topology profile is a
control-plane read model: it spawns nothing, distributes nothing, and
support claims for remote workers, distributed workers, worker pools,
async dispatch, or a Rust/WASM substrate are structurally unconstructible.

The profile vocabulary is F-local (``TopologyProfileKind``) because the
A-pack already exports `ExecutionTopologyKind` as structural future
vocabulary with different members (per the established naming precedent).
Contracts stay primitive/serializable for future substrate extraction.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .exec_errors import AurelExecErrorCode, AurelExecValidationError
from .exec_types import (
    ExecTruthLabel,
    _ExecCanonicalMixin,
    forbid_true,
    require_nonempty,
    stable_hash,
)

EXECUTION_TOPOLOGY_PROFILE_VERSION = "execution_topology_profile.v1"
NO_ASYNC_DISPATCHER_PROOF_VERSION = "no_async_dispatcher_proof.v1"

LOCAL_WORKER_MODEL = "single-local-in-process-worker-slot (P4-EXEC-C canon)"

REMOTE_TOPOLOGY_UNAVAILABLE_REASON = (
    "remote workers are unavailable: no network transport, no remote "
    "runtime, no distributed queue exists"
)
DISTRIBUTED_TOPOLOGY_UNAVAILABLE_REASON = (
    "distributed workers are unavailable: no distributed scheduler, no "
    "queue partitioning, no load balancer, no P8 router exists"
)
WORKER_POOL_TOPOLOGY_UNAVAILABLE_REASON = (
    "a worker pool is unavailable: exactly one local in-process worker "
    "slot exists (P4-EXEC-C); a real pool belongs to the future substrate"
)
ASYNC_DISPATCHER_UNAVAILABLE_REASON = (
    "no async dispatcher, thread pool, or task scheduler exists; every "
    "managed run is a synchronous deterministic pass through the existing "
    "ExecRuntimeBridge"
)
RUST_WASM_TOPOLOGY_UNAVAILABLE_REASON = (
    "the Rust/WASM substrate is a future extraction boundary: deterministic "
    "event log, replay, durable worker leases, real worker pools, and WASM "
    "isolation are not implemented in Python v1"
)


class TopologyProfileKind(str, Enum):
    """Closed-world F-pack topology profile vocabulary. Only the LOCAL_*
    kinds are constructible as active profiles."""

    LOCAL_SINGLE_SLOT = "LOCAL_SINGLE_SLOT"
    LOCAL_BOUNDED_WINDOW = "LOCAL_BOUNDED_WINDOW"
    REMOTE_UNAVAILABLE = "REMOTE_UNAVAILABLE"
    DISTRIBUTED_UNAVAILABLE = "DISTRIBUTED_UNAVAILABLE"
    FUTURE_RUST_WASM_SUBSTRATE = "FUTURE_RUST_WASM_SUBSTRATE"
    ERROR = "ERROR"


_ACTIVE_TOPOLOGY_KINDS = (
    TopologyProfileKind.LOCAL_SINGLE_SLOT,
    TopologyProfileKind.LOCAL_BOUNDED_WINDOW,
)


@dataclass(frozen=True)
class ExecutionTopologyProfile(_ExecCanonicalMixin):
    """The active local execution shape. Describes; never spawns."""

    topology_profile_id: str
    topology_kind: TopologyProfileKind
    local_node_id: str
    worker_model: str
    truth_label: ExecTruthLabel
    contract_version: str = EXECUTION_TOPOLOGY_PROFILE_VERSION
    max_local_slots: int = 1
    unavailable_reasons: tuple[str, ...] = (
        REMOTE_TOPOLOGY_UNAVAILABLE_REASON,
        DISTRIBUTED_TOPOLOGY_UNAVAILABLE_REASON,
        WORKER_POOL_TOPOLOGY_UNAVAILABLE_REASON,
        ASYNC_DISPATCHER_UNAVAILABLE_REASON,
        RUST_WASM_TOPOLOGY_UNAVAILABLE_REASON,
    )
    created_at_tick: int | None = None
    supports_remote_workers: bool = False
    supports_distributed_workers: bool = False
    supports_worker_pool: bool = False
    supports_async_dispatch: bool = False
    supports_rust_wasm_substrate: bool = False
    spawns_workers: bool = False
    distributes_work: bool = False

    def __post_init__(self) -> None:
        require_nonempty(self, "topology_profile_id", code=AurelExecErrorCode.EMPTY_FIELD)
        require_nonempty(self, "local_node_id", code=AurelExecErrorCode.EMPTY_FIELD)
        require_nonempty(self, "worker_model", code=AurelExecErrorCode.EMPTY_FIELD)
        forbid_true(
            self,
            "supports_remote_workers",
            "supports_distributed_workers",
            "supports_worker_pool",
            "supports_async_dispatch",
            "supports_rust_wasm_substrate",
            "spawns_workers",
            "distributes_work",
        )
        if self.topology_kind not in _ACTIVE_TOPOLOGY_KINDS:
            raise AurelExecValidationError(
                f"{self.topology_kind.value} is not constructible as an "
                "active topology profile; only local kinds exist in v1",
                code=AurelExecErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                field="topology_kind",
            )
        if self.max_local_slots < 1:
            raise AurelExecValidationError(
                "an active local topology needs at least one slot",
                code=AurelExecErrorCode.ERROR,
                field="max_local_slots",
            )
        if (
            self.topology_kind is TopologyProfileKind.LOCAL_SINGLE_SLOT
            and self.max_local_slots != 1
        ):
            raise AurelExecValidationError(
                "LOCAL_SINGLE_SLOT means exactly one slot",
                code=AurelExecErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                field="max_local_slots",
            )
        if not self.unavailable_reasons:
            raise AurelExecValidationError(
                "a topology profile must name its unavailable capabilities",
                code=AurelExecErrorCode.EMPTY_FIELD,
                field="unavailable_reasons",
            )

    @property
    def topology_hash(self) -> str:
        return stable_hash(self)


def build_local_topology_profile(
    *,
    max_local_slots: int = 1,
    local_node_id: str = "local-node-0",
    created_at_tick: int | None = None,
    truth_label: ExecTruthLabel = ExecTruthLabel.LIVE,
) -> ExecutionTopologyProfile:
    """The active local topology. Repo truth default: one slot (C canon)."""
    kind = (
        TopologyProfileKind.LOCAL_SINGLE_SLOT
        if max_local_slots == 1
        else TopologyProfileKind.LOCAL_BOUNDED_WINDOW
    )
    return ExecutionTopologyProfile(
        topology_profile_id="exec-topology-"
        + stable_hash((kind.value, local_node_id, max_local_slots))[:16],
        topology_kind=kind,
        local_node_id=local_node_id,
        worker_model=LOCAL_WORKER_MODEL,
        truth_label=truth_label,
        max_local_slots=max_local_slots,
        created_at_tick=created_at_tick,
    )


@dataclass(frozen=True)
class NoAsyncDispatcherProof(_ExecCanonicalMixin):
    """Evidence that no async dispatcher / thread pool / scheduler exists."""

    reason: str
    future_pack_owner: str
    contract_version: str = NO_ASYNC_DISPATCHER_PROOF_VERSION
    async_dispatcher_available: bool = False
    thread_pool_available: bool = False
    task_scheduler_available: bool = False

    def __post_init__(self) -> None:
        forbid_true(
            self,
            "async_dispatcher_available",
            "thread_pool_available",
            "task_scheduler_available",
        )
        require_nonempty(self, "reason", code=AurelExecErrorCode.EMPTY_FIELD)
        require_nonempty(self, "future_pack_owner", code=AurelExecErrorCode.EMPTY_FIELD)


def build_no_async_dispatcher_proof() -> NoAsyncDispatcherProof:
    return NoAsyncDispatcherProof(
        reason=ASYNC_DISPATCHER_UNAVAILABLE_REASON,
        future_pack_owner="future runtime substrate (operator-decided)",
    )
