"""P3-FLOW-I ready-vs-dispatchable boundary / queue candidates / concurrency windows (P3.17).

Ready is not dispatchable: a unit can be dependency-ready while still blocked
by autonomy, checkpoint, budget, operator, resource, or execution-plane
constraints — and even a fully ready unit is only a dispatchable *candidate*
because no P4 dispatch plane exists. A queue placement candidate is not queue
insertion and no worker receives work; a concurrency window is not parallel
execution and a parallelism candidate spawns no worker.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .errors import AurelFlowErrorCode, AurelFlowValidationError
from .flow_scheduling_intent import WorkflowAtomicUnit
from .types import FlowTruthLabel, _CanonicalMixin, stable_hash

READY_STATE_FRAME_VERSION = "ready_state_frame.v1"
DISPATCHABILITY_FRAME_VERSION = "dispatchability_frame.v1"
DISPATCHABILITY_READ_MODEL_VERSION = "dispatchability_read_model.v1"
QUEUE_PLACEMENT_CANDIDATE_VERSION = "queue_placement_candidate.v1"
QUEUE_PLACEMENT_BOUNDARY_VERSION = "queue_placement_boundary.v1"
QUEUE_PLACEMENT_READ_MODEL_VERSION = "queue_placement_read_model.v1"
DEPENDENCY_WINDOW_VERSION = "dependency_window.v1"
CONCURRENCY_WINDOW_VERSION = "concurrency_window.v1"
PARALLELISM_CANDIDATE_VERSION = "parallelism_candidate.v1"
CONCURRENCY_BOUNDARY_VERSION = "concurrency_boundary.v1"
CONCURRENCY_READ_MODEL_VERSION = "concurrency_read_model.v1"

DISPATCH_PLANE_UNAVAILABLE_REASON = (
    "no dispatch plane exists in P3: ready is not dispatchable, a "
    "dispatchable candidate is not dispatched, and execution-ready is "
    "unavailable — dispatch and execution belong to P4 AurelExec"
)
QUEUE_UNAVAILABLE_REASON = (
    "no real queue exists in P3: a queue placement candidate is a scheduling "
    "visibility object only — nothing is inserted into a queue and no worker "
    "receives work before P4 AurelExec"
)
CONCURRENCY_UNAVAILABLE_REASON = (
    "no parallel execution plane exists in P3: a concurrency window "
    "describes safe/unsafe parallelism candidates only — no worker is "
    "spawned and nothing runs in parallel before P4 AurelExec"
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


class ReadinessDimension(str, Enum):
    """Closed-world readiness dimensions. Readiness is not authority."""

    DEPENDENCY_READY = "DEPENDENCY_READY"
    STATE_READY = "STATE_READY"
    CHECKPOINT_READY = "CHECKPOINT_READY"
    AUTONOMY_READY = "AUTONOMY_READY"
    BUDGET_READY = "BUDGET_READY"
    RESOURCE_PREDICTED = "RESOURCE_PREDICTED"
    OPERATOR_READY = "OPERATOR_READY"
    POLICY_READY_UNAVAILABLE = "POLICY_READY_UNAVAILABLE"
    PROOF_READY_UNAVAILABLE = "PROOF_READY_UNAVAILABLE"
    EXECUTION_READY_UNAVAILABLE = "EXECUTION_READY_UNAVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"


@dataclass(frozen=True)
class ReadyStateFrame(_CanonicalMixin):
    """Per-dimension readiness of one atomic unit. Ready is not dispatchable.

    Policy readiness (P9), proof readiness (P5), and execution readiness (P4)
    are structurally unavailable in P3 and cannot be declared ready.
    """

    ready_state_id: str
    contract_version: str
    run_id: str
    atomic_unit_id: str
    dependency_ready: bool
    state_ready: bool
    checkpoint_ready: bool
    autonomy_ready: bool
    budget_ready: bool
    resource_ready: bool
    operator_ready: bool
    truth_label: FlowTruthLabel
    unavailable_reason: str = DISPATCH_PLANE_UNAVAILABLE_REASON
    ready_is_not_dispatchable: bool = True
    policy_ready: bool = False
    proof_ready: bool = False
    execution_ready: bool = False
    dispatch_available: bool = False
    execution_available: bool = False

    def __post_init__(self) -> None:
        _forbid_false(self, "ready_is_not_dispatchable")
        _forbid_true(
            self,
            "policy_ready",
            "proof_ready",
            "execution_ready",
            "dispatch_available",
            "execution_available",
        )

    @property
    def fully_ready(self) -> bool:
        """All P3-representable readiness dimensions are ready."""

        return (
            self.dependency_ready
            and self.state_ready
            and self.checkpoint_ready
            and self.autonomy_ready
            and self.budget_ready
            and self.resource_ready
            and self.operator_ready
        )


def create_ready_state_frame(
    *,
    unit: WorkflowAtomicUnit,
    dependency_ready: bool,
    state_ready: bool,
    checkpoint_ready: bool = True,
    autonomy_ready: bool = True,
    budget_ready: bool = True,
    resource_ready: bool = True,
    operator_ready: bool = True,
) -> ReadyStateFrame:
    payload = {
        "contract_version": READY_STATE_FRAME_VERSION,
        "run_id": unit.run_id,
        "atomic_unit_id": unit.atomic_unit_id,
        "dependency_ready": dependency_ready,
        "state_ready": state_ready,
        "checkpoint_ready": checkpoint_ready,
        "autonomy_ready": autonomy_ready,
        "budget_ready": budget_ready,
        "resource_ready": resource_ready,
        "operator_ready": operator_ready,
    }
    return ReadyStateFrame(
        ready_state_id="flrsf-" + stable_hash(payload)[:16],
        contract_version=READY_STATE_FRAME_VERSION,
        run_id=unit.run_id,
        atomic_unit_id=unit.atomic_unit_id,
        dependency_ready=dependency_ready,
        state_ready=state_ready,
        checkpoint_ready=checkpoint_ready,
        autonomy_ready=autonomy_ready,
        budget_ready=budget_ready,
        resource_ready=resource_ready,
        operator_ready=operator_ready,
        truth_label=FlowTruthLabel.LOCAL_RUNTIME_SUBSTRATE,
    )


class DispatchabilityReason(str, Enum):
    """Closed-world explanations for why a unit is not dispatched."""

    READY_BUT_NO_P4 = "READY_BUT_NO_P4"
    READY_BUT_REQUIRES_OPERATOR = "READY_BUT_REQUIRES_OPERATOR"
    READY_BUT_REQUIRES_AUTHORITY = "READY_BUT_REQUIRES_AUTHORITY"
    READY_BUT_REQUIRES_PROOF = "READY_BUT_REQUIRES_PROOF"
    READY_BUT_RESOURCE_UNAVAILABLE = "READY_BUT_RESOURCE_UNAVAILABLE"
    READY_BUT_CHECKPOINT_REQUIRED = "READY_BUT_CHECKPOINT_REQUIRED"
    READY_BUT_AUTONOMY_BLOCKED = "READY_BUT_AUTONOMY_BLOCKED"
    READY_BUT_BUDGET_EXHAUSTED = "READY_BUT_BUDGET_EXHAUSTED"
    READY_BUT_RETRY_STORM = "READY_BUT_RETRY_STORM"
    READY_BUT_NO_PROGRESS = "READY_BUT_NO_PROGRESS"
    NOT_READY_DEPENDENCIES = "NOT_READY_DEPENDENCIES"
    NOT_READY_STATE = "NOT_READY_STATE"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"


@dataclass(frozen=True)
class DispatchabilityFrame(_CanonicalMixin):
    """Ready vs dispatchable, with the reason nothing is dispatched.

    A dispatchable *candidate* is still never dispatched in P3: the
    dispatch/execution booleans are structurally False.
    """

    dispatchability_id: str
    contract_version: str
    run_id: str
    atomic_unit_id: str
    ready_state_id: str
    dispatchable_candidate: bool
    dispatchability_reason: DispatchabilityReason
    explanation: str
    truth_label: FlowTruthLabel
    unavailable_reason: str = DISPATCH_PLANE_UNAVAILABLE_REASON
    dispatch_available: bool = False
    dispatched: bool = False
    execution_available: bool = False

    def __post_init__(self) -> None:
        _forbid_true(
            self, "dispatch_available", "dispatched", "execution_available"
        )


def classify_dispatchability(
    ready: ReadyStateFrame,
    *,
    retry_storm_active: bool = False,
    no_progress_active: bool = False,
) -> DispatchabilityFrame:
    """Deterministic total classifier from a ready-state frame.

    Even a fully ready unit is only a dispatchable candidate with reason
    READY_BUT_NO_P4 — ready is not dispatchable and nothing is dispatched.
    """

    dispatchable_candidate = False
    if not ready.dependency_ready:
        reason = DispatchabilityReason.NOT_READY_DEPENDENCIES
        explanation = "predecessor units have not completed"
    elif not ready.state_ready:
        reason = DispatchabilityReason.NOT_READY_STATE
        explanation = "the run/node state does not allow scheduling this unit"
    elif retry_storm_active:
        reason = DispatchabilityReason.READY_BUT_RETRY_STORM
        explanation = "a retry storm guard blocks further candidates"
    elif no_progress_active:
        reason = DispatchabilityReason.READY_BUT_NO_PROGRESS
        explanation = "a no-progress guard requires operator review first"
    elif not ready.budget_ready:
        reason = DispatchabilityReason.READY_BUT_BUDGET_EXHAUSTED
        explanation = "a scheduling-relevant budget is exhausted"
    elif not ready.autonomy_ready:
        reason = DispatchabilityReason.READY_BUT_AUTONOMY_BLOCKED
        explanation = "the governed autonomy boundary blocks this candidate"
    elif not ready.checkpoint_ready:
        reason = DispatchabilityReason.READY_BUT_CHECKPOINT_REQUIRED
        explanation = (
            "the P3-FLOW-F checkpoint discipline requires a checkpoint first"
        )
    elif not ready.resource_ready:
        reason = DispatchabilityReason.READY_BUT_RESOURCE_UNAVAILABLE
        explanation = "predicted resources are not available"
    elif not ready.operator_ready:
        reason = DispatchabilityReason.READY_BUT_REQUIRES_OPERATOR
        explanation = "an operator review is pending for this unit"
    else:
        dispatchable_candidate = True
        reason = DispatchabilityReason.READY_BUT_NO_P4
        explanation = (
            "every P3-representable readiness dimension is ready, but no P4 "
            "dispatch plane exists — the unit is a dispatchable candidate "
            "and nothing is dispatched"
        )
    payload = {
        "contract_version": DISPATCHABILITY_FRAME_VERSION,
        "ready_state_id": ready.ready_state_id,
        "reason": reason.value,
        "retry_storm_active": retry_storm_active,
        "no_progress_active": no_progress_active,
    }
    return DispatchabilityFrame(
        dispatchability_id="fldpf-" + stable_hash(payload)[:16],
        contract_version=DISPATCHABILITY_FRAME_VERSION,
        run_id=ready.run_id,
        atomic_unit_id=ready.atomic_unit_id,
        ready_state_id=ready.ready_state_id,
        dispatchable_candidate=dispatchable_candidate,
        dispatchability_reason=reason,
        explanation=explanation,
        truth_label=FlowTruthLabel.LOCAL_RUNTIME_SUBSTRATE,
    )


@dataclass(frozen=True)
class DispatchabilityReadModel(_CanonicalMixin):
    """Deterministic read model over one run's dispatchability frames."""

    read_model_id: str
    contract_version: str
    run_id: str
    frame_count: int
    reason_counts: tuple[tuple[str, int], ...]
    dispatchability_ids: tuple[str, ...]
    dispatchable_candidate_count: int
    truth_label: FlowTruthLabel
    unavailable_reason: str = DISPATCH_PLANE_UNAVAILABLE_REASON
    dispatch_available: bool = False
    dispatched: bool = False
    execution_available: bool = False

    def __post_init__(self) -> None:
        _forbid_true(
            self, "dispatch_available", "dispatched", "execution_available"
        )


def build_dispatchability_read_model(
    *, run_id: str, frames: tuple[DispatchabilityFrame, ...]
) -> DispatchabilityReadModel:
    for frame in frames:
        if frame.run_id != run_id:
            raise AurelFlowValidationError(
                f"frame {frame.dispatchability_id!r} belongs to run "
                f"{frame.run_id!r}, not {run_id!r}",
                code=AurelFlowErrorCode.RUN_MISMATCH,
                field="frames",
            )
    reason_counts: dict[str, int] = {}
    for frame in frames:
        reason_counts[frame.dispatchability_reason.value] = (
            reason_counts.get(frame.dispatchability_reason.value, 0) + 1
        )
    frame_ids = tuple(sorted(frame.dispatchability_id for frame in frames))
    payload = {
        "contract_version": DISPATCHABILITY_READ_MODEL_VERSION,
        "run_id": run_id,
        "dispatchability_ids": frame_ids,
    }
    return DispatchabilityReadModel(
        read_model_id="fldpm-" + stable_hash(payload)[:16],
        contract_version=DISPATCHABILITY_READ_MODEL_VERSION,
        run_id=run_id,
        frame_count=len(frames),
        reason_counts=tuple(sorted(reason_counts.items())),
        dispatchability_ids=frame_ids,
        dispatchable_candidate_count=sum(
            1 for frame in frames if frame.dispatchable_candidate
        ),
        truth_label=FlowTruthLabel.READ_MODEL_ONLY,
    )


class QueuePlacementKind(str, Enum):
    """Closed-world queue placement candidate vocabulary. No real queue."""

    READY_QUEUE_CANDIDATE = "READY_QUEUE_CANDIDATE"
    BLOCKED_QUEUE_CANDIDATE = "BLOCKED_QUEUE_CANDIDATE"
    WAITING_OPERATOR_QUEUE_CANDIDATE = "WAITING_OPERATOR_QUEUE_CANDIDATE"
    WAITING_PERMISSION_QUEUE_CANDIDATE = "WAITING_PERMISSION_QUEUE_CANDIDATE"
    WAITING_PROOF_QUEUE_CANDIDATE = "WAITING_PROOF_QUEUE_CANDIDATE"
    WAITING_RESOURCE_QUEUE_CANDIDATE = "WAITING_RESOURCE_QUEUE_CANDIDATE"
    WAITING_CHECKPOINT_QUEUE_CANDIDATE = "WAITING_CHECKPOINT_QUEUE_CANDIDATE"
    WAITING_VERIFIER_QUEUE_CANDIDATE = "WAITING_VERIFIER_QUEUE_CANDIDATE"
    DEGRADED_QUEUE_CANDIDATE = "DEGRADED_QUEUE_CANDIDATE"
    ESCALATED_QUEUE_CANDIDATE = "ESCALATED_QUEUE_CANDIDATE"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"


class QueuePlacementReason(str, Enum):
    """Why a queue placement candidate was chosen. Not queue insertion."""

    DEPENDENCIES_SATISFIED = "DEPENDENCIES_SATISFIED"
    DEPENDENCIES_PENDING = "DEPENDENCIES_PENDING"
    STATE_NOT_READY = "STATE_NOT_READY"
    OPERATOR_REVIEW_REQUIRED = "OPERATOR_REVIEW_REQUIRED"
    PERMISSION_REQUIRED = "PERMISSION_REQUIRED"
    PROOF_REQUIRED = "PROOF_REQUIRED"
    RESOURCE_PRESSURE = "RESOURCE_PRESSURE"
    CHECKPOINT_REQUIRED = "CHECKPOINT_REQUIRED"
    VERIFIER_EXPECTED = "VERIFIER_EXPECTED"
    BUDGET_EXHAUSTED = "BUDGET_EXHAUSTED"
    RETRY_STORM_GUARD = "RETRY_STORM_GUARD"
    NO_PROGRESS_GUARD = "NO_PROGRESS_GUARD"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"


@dataclass(frozen=True)
class QueuePlacementCandidate(_CanonicalMixin):
    """Where a unit *would* sit in a queue. Nothing is actually queued."""

    queue_candidate_id: str
    contract_version: str
    run_id: str
    atomic_unit_id: str
    placement_kind: QueuePlacementKind
    placement_reason: QueuePlacementReason
    truth_label: FlowTruthLabel
    priority_hint: int | None = None
    unavailable_reason: str = QUEUE_UNAVAILABLE_REASON
    queue_candidate_only: bool = True
    actual_queue_inserted: bool = False
    worker_assigned: bool = False
    dispatch_available: bool = False
    execution_available: bool = False

    def __post_init__(self) -> None:
        _forbid_false(self, "queue_candidate_only")
        _forbid_true(
            self,
            "actual_queue_inserted",
            "worker_assigned",
            "dispatch_available",
            "execution_available",
        )


_DISPATCHABILITY_TO_QUEUE_PLACEMENT: dict[
    DispatchabilityReason, tuple[QueuePlacementKind, QueuePlacementReason]
] = {
    DispatchabilityReason.READY_BUT_NO_P4: (
        QueuePlacementKind.READY_QUEUE_CANDIDATE,
        QueuePlacementReason.DEPENDENCIES_SATISFIED,
    ),
    DispatchabilityReason.READY_BUT_REQUIRES_OPERATOR: (
        QueuePlacementKind.WAITING_OPERATOR_QUEUE_CANDIDATE,
        QueuePlacementReason.OPERATOR_REVIEW_REQUIRED,
    ),
    DispatchabilityReason.READY_BUT_REQUIRES_AUTHORITY: (
        QueuePlacementKind.WAITING_PERMISSION_QUEUE_CANDIDATE,
        QueuePlacementReason.PERMISSION_REQUIRED,
    ),
    DispatchabilityReason.READY_BUT_REQUIRES_PROOF: (
        QueuePlacementKind.WAITING_PROOF_QUEUE_CANDIDATE,
        QueuePlacementReason.PROOF_REQUIRED,
    ),
    DispatchabilityReason.READY_BUT_RESOURCE_UNAVAILABLE: (
        QueuePlacementKind.WAITING_RESOURCE_QUEUE_CANDIDATE,
        QueuePlacementReason.RESOURCE_PRESSURE,
    ),
    DispatchabilityReason.READY_BUT_CHECKPOINT_REQUIRED: (
        QueuePlacementKind.WAITING_CHECKPOINT_QUEUE_CANDIDATE,
        QueuePlacementReason.CHECKPOINT_REQUIRED,
    ),
    DispatchabilityReason.READY_BUT_AUTONOMY_BLOCKED: (
        QueuePlacementKind.BLOCKED_QUEUE_CANDIDATE,
        QueuePlacementReason.PERMISSION_REQUIRED,
    ),
    DispatchabilityReason.READY_BUT_BUDGET_EXHAUSTED: (
        QueuePlacementKind.DEGRADED_QUEUE_CANDIDATE,
        QueuePlacementReason.BUDGET_EXHAUSTED,
    ),
    DispatchabilityReason.READY_BUT_RETRY_STORM: (
        QueuePlacementKind.ESCALATED_QUEUE_CANDIDATE,
        QueuePlacementReason.RETRY_STORM_GUARD,
    ),
    DispatchabilityReason.READY_BUT_NO_PROGRESS: (
        QueuePlacementKind.ESCALATED_QUEUE_CANDIDATE,
        QueuePlacementReason.NO_PROGRESS_GUARD,
    ),
    DispatchabilityReason.NOT_READY_DEPENDENCIES: (
        QueuePlacementKind.BLOCKED_QUEUE_CANDIDATE,
        QueuePlacementReason.DEPENDENCIES_PENDING,
    ),
    DispatchabilityReason.NOT_READY_STATE: (
        QueuePlacementKind.BLOCKED_QUEUE_CANDIDATE,
        QueuePlacementReason.STATE_NOT_READY,
    ),
    DispatchabilityReason.UNAVAILABLE: (
        QueuePlacementKind.UNAVAILABLE,
        QueuePlacementReason.UNAVAILABLE,
    ),
    DispatchabilityReason.ERROR: (
        QueuePlacementKind.ERROR,
        QueuePlacementReason.ERROR,
    ),
}


def derive_queue_placement_candidate(
    frame: DispatchabilityFrame,
    *,
    priority_hint: int | None = None,
) -> QueuePlacementCandidate:
    """Deterministic total mapping from dispatchability to queue placement."""

    placement_kind, placement_reason = _DISPATCHABILITY_TO_QUEUE_PLACEMENT[
        frame.dispatchability_reason
    ]
    payload = {
        "contract_version": QUEUE_PLACEMENT_CANDIDATE_VERSION,
        "dispatchability_id": frame.dispatchability_id,
        "placement_kind": placement_kind.value,
        "priority_hint": priority_hint,
    }
    return QueuePlacementCandidate(
        queue_candidate_id="flqpc-" + stable_hash(payload)[:16],
        contract_version=QUEUE_PLACEMENT_CANDIDATE_VERSION,
        run_id=frame.run_id,
        atomic_unit_id=frame.atomic_unit_id,
        placement_kind=placement_kind,
        placement_reason=placement_reason,
        truth_label=FlowTruthLabel.LOCAL_RUNTIME_SUBSTRATE,
        priority_hint=priority_hint,
    )


@dataclass(frozen=True)
class QueuePlacementBoundary(_CanonicalMixin):
    """The queue law as fail-closed data. Candidate is not insertion."""

    boundary_id: str
    contract_version: str
    truth_label: FlowTruthLabel
    unavailable_reason: str = QUEUE_UNAVAILABLE_REASON
    candidate_is_not_queue_insertion: bool = True
    no_worker_receives_work_in_p3: bool = True
    actual_queue_inserted: bool = False
    worker_assigned: bool = False
    dispatch_available: bool = False
    execution_available: bool = False

    def __post_init__(self) -> None:
        _forbid_false(
            self,
            "candidate_is_not_queue_insertion",
            "no_worker_receives_work_in_p3",
        )
        _forbid_true(
            self,
            "actual_queue_inserted",
            "worker_assigned",
            "dispatch_available",
            "execution_available",
        )


def build_queue_placement_boundary() -> QueuePlacementBoundary:
    payload = {"contract_version": QUEUE_PLACEMENT_BOUNDARY_VERSION}
    return QueuePlacementBoundary(
        boundary_id="flqpb-" + stable_hash(payload)[:16],
        contract_version=QUEUE_PLACEMENT_BOUNDARY_VERSION,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
    )


@dataclass(frozen=True)
class QueuePlacementReadModel(_CanonicalMixin):
    """Deterministic read model over one run's queue placement candidates."""

    read_model_id: str
    contract_version: str
    run_id: str
    candidate_count: int
    placement_kind_counts: tuple[tuple[str, int], ...]
    queue_candidate_ids: tuple[str, ...]
    boundary: QueuePlacementBoundary
    truth_label: FlowTruthLabel
    unavailable_reason: str = QUEUE_UNAVAILABLE_REASON
    actual_queue_inserted: bool = False
    worker_assigned: bool = False
    execution_available: bool = False

    def __post_init__(self) -> None:
        _forbid_true(
            self,
            "actual_queue_inserted",
            "worker_assigned",
            "execution_available",
        )


def build_queue_placement_read_model(
    *, run_id: str, candidates: tuple[QueuePlacementCandidate, ...]
) -> QueuePlacementReadModel:
    for candidate in candidates:
        if candidate.run_id != run_id:
            raise AurelFlowValidationError(
                f"candidate {candidate.queue_candidate_id!r} belongs to run "
                f"{candidate.run_id!r}, not {run_id!r}",
                code=AurelFlowErrorCode.RUN_MISMATCH,
                field="candidates",
            )
    kind_counts: dict[str, int] = {}
    for candidate in candidates:
        kind_counts[candidate.placement_kind.value] = (
            kind_counts.get(candidate.placement_kind.value, 0) + 1
        )
    candidate_ids = tuple(
        sorted(candidate.queue_candidate_id for candidate in candidates)
    )
    payload = {
        "contract_version": QUEUE_PLACEMENT_READ_MODEL_VERSION,
        "run_id": run_id,
        "queue_candidate_ids": candidate_ids,
    }
    return QueuePlacementReadModel(
        read_model_id="flqpm-" + stable_hash(payload)[:16],
        contract_version=QUEUE_PLACEMENT_READ_MODEL_VERSION,
        run_id=run_id,
        candidate_count=len(candidates),
        placement_kind_counts=tuple(sorted(kind_counts.items())),
        queue_candidate_ids=candidate_ids,
        boundary=build_queue_placement_boundary(),
        truth_label=FlowTruthLabel.READ_MODEL_ONLY,
    )


@dataclass(frozen=True)
class DependencyWindow(_CanonicalMixin):
    """Which units block which. A window orders candidates; it runs nothing."""

    dependency_window_id: str
    contract_version: str
    run_id: str
    atomic_unit_ids: tuple[str, ...]
    required_predecessor_unit_ids: tuple[str, ...]
    blocked_by_unit_ids: tuple[str, ...]
    truth_label: FlowTruthLabel
    unavailable_reason: str = CONCURRENCY_UNAVAILABLE_REASON
    window_is_not_execution_order: bool = True
    dispatch_available: bool = False
    execution_available: bool = False

    def __post_init__(self) -> None:
        _forbid_false(self, "window_is_not_execution_order")
        _forbid_true(self, "dispatch_available", "execution_available")
        if not self.atomic_unit_ids:
            raise AurelFlowValidationError(
                "a dependency window must cover at least one atomic unit",
                code=AurelFlowErrorCode.EMPTY_NODE_SET,
                field="atomic_unit_ids",
            )


def create_dependency_window(
    *,
    run_id: str,
    atomic_unit_ids: tuple[str, ...],
    required_predecessor_unit_ids: tuple[str, ...] = (),
    blocked_by_unit_ids: tuple[str, ...] = (),
) -> DependencyWindow:
    payload = {
        "contract_version": DEPENDENCY_WINDOW_VERSION,
        "run_id": run_id,
        "atomic_unit_ids": tuple(sorted(atomic_unit_ids)),
        "required_predecessor_unit_ids": tuple(
            sorted(required_predecessor_unit_ids)
        ),
        "blocked_by_unit_ids": tuple(sorted(blocked_by_unit_ids)),
    }
    return DependencyWindow(
        dependency_window_id="fldwn-" + stable_hash(payload)[:16],
        contract_version=DEPENDENCY_WINDOW_VERSION,
        run_id=run_id,
        atomic_unit_ids=tuple(sorted(atomic_unit_ids)),
        required_predecessor_unit_ids=tuple(
            sorted(required_predecessor_unit_ids)
        ),
        blocked_by_unit_ids=tuple(sorted(blocked_by_unit_ids)),
        truth_label=FlowTruthLabel.LOCAL_RUNTIME_SUBSTRATE,
    )


@dataclass(frozen=True)
class ParallelismCandidate(_CanonicalMixin):
    """Units that *could* run in parallel later. No worker is spawned."""

    parallelism_candidate_id: str
    contract_version: str
    run_id: str
    atomic_unit_ids: tuple[str, ...]
    truth_label: FlowTruthLabel
    unavailable_reason: str = CONCURRENCY_UNAVAILABLE_REASON
    parallelism_candidate_only: bool = True
    worker_spawned: bool = False
    parallel_execution_available: bool = False

    def __post_init__(self) -> None:
        _forbid_false(self, "parallelism_candidate_only")
        _forbid_true(self, "worker_spawned", "parallel_execution_available")
        if len(self.atomic_unit_ids) < 2:
            raise AurelFlowValidationError(
                "a parallelism candidate needs at least two atomic units",
                code=AurelFlowErrorCode.EMPTY_NODE_SET,
                field="atomic_unit_ids",
            )


def create_parallelism_candidate(
    *, run_id: str, atomic_unit_ids: tuple[str, ...]
) -> ParallelismCandidate:
    payload = {
        "contract_version": PARALLELISM_CANDIDATE_VERSION,
        "run_id": run_id,
        "atomic_unit_ids": tuple(sorted(atomic_unit_ids)),
    }
    return ParallelismCandidate(
        parallelism_candidate_id="flplc-" + stable_hash(payload)[:16],
        contract_version=PARALLELISM_CANDIDATE_VERSION,
        run_id=run_id,
        atomic_unit_ids=tuple(sorted(atomic_unit_ids)),
        truth_label=FlowTruthLabel.LOCAL_RUNTIME_SUBSTRATE,
    )


@dataclass(frozen=True)
class ConcurrencyWindow(_CanonicalMixin):
    """Safe/unsafe parallelism over atomic units. Not parallel execution."""

    concurrency_window_id: str
    contract_version: str
    run_id: str
    atomic_unit_ids: tuple[str, ...]
    parallel_candidate_unit_ids: tuple[str, ...]
    unsafe_parallel_unit_ids: tuple[str, ...]
    shared_resource_constraints: tuple[str, ...]
    requires_operator_ordering: bool
    truth_label: FlowTruthLabel
    unavailable_reason: str = CONCURRENCY_UNAVAILABLE_REASON
    parallelism_candidate_only: bool = True
    worker_spawned: bool = False
    parallel_execution_available: bool = False

    def __post_init__(self) -> None:
        _forbid_false(self, "parallelism_candidate_only")
        _forbid_true(self, "worker_spawned", "parallel_execution_available")
        overlap = set(self.parallel_candidate_unit_ids) & set(
            self.unsafe_parallel_unit_ids
        )
        if overlap:
            raise AurelFlowValidationError(
                "a unit cannot be both a safe and an unsafe parallel "
                f"candidate: {sorted(overlap)}",
                code=AurelFlowErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                field="unsafe_parallel_unit_ids",
            )
        known = set(self.atomic_unit_ids)
        unknown = (
            set(self.parallel_candidate_unit_ids)
            | set(self.unsafe_parallel_unit_ids)
        ) - known
        if unknown:
            raise AurelFlowValidationError(
                "parallel/unsafe unit ids must belong to the window: "
                f"{sorted(unknown)}",
                code=AurelFlowErrorCode.UNKNOWN_NODE_REF,
                field="parallel_candidate_unit_ids",
            )


def create_concurrency_window(
    *,
    run_id: str,
    atomic_unit_ids: tuple[str, ...],
    parallel_candidate_unit_ids: tuple[str, ...] = (),
    unsafe_parallel_unit_ids: tuple[str, ...] = (),
    shared_resource_constraints: tuple[str, ...] = (),
    requires_operator_ordering: bool = False,
) -> ConcurrencyWindow:
    payload = {
        "contract_version": CONCURRENCY_WINDOW_VERSION,
        "run_id": run_id,
        "atomic_unit_ids": tuple(sorted(atomic_unit_ids)),
        "parallel_candidate_unit_ids": tuple(
            sorted(parallel_candidate_unit_ids)
        ),
        "unsafe_parallel_unit_ids": tuple(sorted(unsafe_parallel_unit_ids)),
        "shared_resource_constraints": tuple(
            sorted(shared_resource_constraints)
        ),
        "requires_operator_ordering": requires_operator_ordering,
    }
    return ConcurrencyWindow(
        concurrency_window_id="flcnw-" + stable_hash(payload)[:16],
        contract_version=CONCURRENCY_WINDOW_VERSION,
        run_id=run_id,
        atomic_unit_ids=tuple(sorted(atomic_unit_ids)),
        parallel_candidate_unit_ids=tuple(sorted(parallel_candidate_unit_ids)),
        unsafe_parallel_unit_ids=tuple(sorted(unsafe_parallel_unit_ids)),
        shared_resource_constraints=tuple(sorted(shared_resource_constraints)),
        requires_operator_ordering=requires_operator_ordering,
        truth_label=FlowTruthLabel.LOCAL_RUNTIME_SUBSTRATE,
    )


@dataclass(frozen=True)
class ConcurrencyBoundary(_CanonicalMixin):
    """The concurrency law as fail-closed data. Window is not worker spawn."""

    boundary_id: str
    contract_version: str
    truth_label: FlowTruthLabel
    unavailable_reason: str = CONCURRENCY_UNAVAILABLE_REASON
    window_is_not_parallel_execution: bool = True
    parallelism_candidate_is_not_worker_spawn: bool = True
    worker_spawned: bool = False
    parallel_execution_available: bool = False
    dispatch_available: bool = False
    execution_available: bool = False

    def __post_init__(self) -> None:
        _forbid_false(
            self,
            "window_is_not_parallel_execution",
            "parallelism_candidate_is_not_worker_spawn",
        )
        _forbid_true(
            self,
            "worker_spawned",
            "parallel_execution_available",
            "dispatch_available",
            "execution_available",
        )


def build_concurrency_boundary() -> ConcurrencyBoundary:
    payload = {"contract_version": CONCURRENCY_BOUNDARY_VERSION}
    return ConcurrencyBoundary(
        boundary_id="flcnb-" + stable_hash(payload)[:16],
        contract_version=CONCURRENCY_BOUNDARY_VERSION,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
    )


@dataclass(frozen=True)
class ConcurrencyReadModel(_CanonicalMixin):
    """Deterministic read model over dependency/concurrency windows."""

    read_model_id: str
    contract_version: str
    run_id: str
    dependency_window_count: int
    concurrency_window_count: int
    parallelism_candidate_count: int
    operator_ordering_required_count: int
    boundary: ConcurrencyBoundary
    truth_label: FlowTruthLabel
    unavailable_reason: str = CONCURRENCY_UNAVAILABLE_REASON
    worker_spawned: bool = False
    parallel_execution_available: bool = False
    execution_available: bool = False

    def __post_init__(self) -> None:
        _forbid_true(
            self,
            "worker_spawned",
            "parallel_execution_available",
            "execution_available",
        )


def build_concurrency_read_model(
    *,
    run_id: str,
    dependency_windows: tuple[DependencyWindow, ...] = (),
    concurrency_windows: tuple[ConcurrencyWindow, ...] = (),
    parallelism_candidates: tuple[ParallelismCandidate, ...] = (),
) -> ConcurrencyReadModel:
    for source_name, source_run_ids in (
        ("dependency_windows", [w.run_id for w in dependency_windows]),
        ("concurrency_windows", [w.run_id for w in concurrency_windows]),
        (
            "parallelism_candidates",
            [c.run_id for c in parallelism_candidates],
        ),
    ):
        for source_run_id in source_run_ids:
            if source_run_id != run_id:
                raise AurelFlowValidationError(
                    f"{source_name} entry belongs to run "
                    f"{source_run_id!r}, not {run_id!r}",
                    code=AurelFlowErrorCode.RUN_MISMATCH,
                    field=source_name,
                )
    payload = {
        "contract_version": CONCURRENCY_READ_MODEL_VERSION,
        "run_id": run_id,
        "dependency_window_ids": tuple(
            sorted(w.dependency_window_id for w in dependency_windows)
        ),
        "concurrency_window_ids": tuple(
            sorted(w.concurrency_window_id for w in concurrency_windows)
        ),
        "parallelism_candidate_ids": tuple(
            sorted(c.parallelism_candidate_id for c in parallelism_candidates)
        ),
    }
    return ConcurrencyReadModel(
        read_model_id="flcnm-" + stable_hash(payload)[:16],
        contract_version=CONCURRENCY_READ_MODEL_VERSION,
        run_id=run_id,
        dependency_window_count=len(dependency_windows),
        concurrency_window_count=len(concurrency_windows),
        parallelism_candidate_count=len(parallelism_candidates),
        operator_ordering_required_count=sum(
            1 for w in concurrency_windows if w.requires_operator_ordering
        ),
        boundary=build_concurrency_boundary(),
        truth_label=FlowTruthLabel.READ_MODEL_ONLY,
    )
