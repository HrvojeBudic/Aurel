"""P3-FLOW-I workflow-atomic scheduling units / scheduling intent / autonomy gate (P3.17).

Scheduling intent is grammar, not dispatch. A workflow-atomic unit is the
smallest meaningful scheduling unit and is never a worker job; a scheduling
intent proposes scheduling and never enqueues, dispatches, or executes; an
autonomy-gated scheduling decision consumes the P3-FLOW-H governed autonomy
boundaries and is never authority. P4 dispatches and executes, P5 proves
scheduled/executed alignment, P9 authorizes scheduling actions.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .errors import AurelFlowErrorCode, AurelFlowValidationError
from .flow_autonomy import (
    AutonomyDecisionClass,
    AutonomyPermissionState,
    GovernedAutonomyLevel,
    resolve_action_boundary,
)
from .flow_autonomy_scope import AutonomyScopeDimension, AutonomyScopeEnvelope
from .types import FlowTruthLabel, _CanonicalMixin, stable_hash

AUREL_FLOW_I_PACK_ID = "P3-FLOW-I"
AUREL_FLOW_I_PACK_TITLE = (
    "Workflow-Atomic Scheduling Intent / Resource Prediction Pack"
)
AUREL_FLOW_I_REPORT_PATH = (
    "agent/reports/P3_FLOW_I_SCHEDULING_INTENT_RESOURCE_PREDICTION_PACK.md"
)

WORKFLOW_ATOMIC_UNIT_VERSION = "workflow_atomic_unit.v1"
WORKFLOW_ATOMIC_UNIT_REF_VERSION = "workflow_atomic_unit_ref.v1"
WORKFLOW_ATOMIC_BOUNDARY_VERSION = "workflow_atomic_boundary.v1"
WORKFLOW_ATOMIC_READ_MODEL_VERSION = "workflow_atomic_read_model.v1"
SCHEDULING_INTENT_VERSION = "scheduling_intent.v1"
SCHEDULING_INTENT_BOUNDARY_VERSION = "scheduling_intent_boundary.v1"
SCHEDULING_INTENT_READ_MODEL_VERSION = "scheduling_intent_read_model.v1"
SCHEDULING_SCOPE_CHECK_VERSION = "scheduling_scope_check.v1"
SCHEDULING_ACTION_BOUNDARY_CHECK_VERSION = (
    "scheduling_action_boundary_check.v1"
)
AUTONOMY_SCHEDULING_GATE_VERSION = "autonomy_scheduling_gate.v1"
SCHEDULING_GATE_READ_MODEL_VERSION = "scheduling_gate_read_model.v1"

SCHEDULING_DISPATCH_UNAVAILABLE_REASON = (
    "scheduling intent is grammar, not dispatch: nothing in P3-FLOW-I "
    "enqueues real work, allocates workers, or dispatches anything — "
    "dispatch and execution belong to P4 AurelExec, proof to P5 AurelTrace, "
    "authority to P9 Custos"
)
SCHEDULING_GATE_UNAVAILABLE_REASON = (
    "an autonomy-gated scheduling decision restricts a scheduling candidate; "
    "it grants no authority and cannot bypass the P3-FLOW-H governed "
    "autonomy boundaries or future P9 Custos"
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


class WorkflowAtomicUnitKind(str, Enum):
    """Closed-world atomic scheduling unit vocabulary. A unit is not a job."""

    SINGLE_NODE = "SINGLE_NODE"
    NODE_GROUP = "NODE_GROUP"
    RECOVERY_CANDIDATE_GROUP = "RECOVERY_CANDIDATE_GROUP"
    GRAPH_REVISION_CANDIDATE_GROUP = "GRAPH_REVISION_CANDIDATE_GROUP"
    CHECKPOINT_BOUND_REPLAY_CANDIDATE = "CHECKPOINT_BOUND_REPLAY_CANDIDATE"
    OPERATOR_REVIEW_WAITING_UNIT = "OPERATOR_REVIEW_WAITING_UNIT"
    VERIFIER_CANDIDATE_UNIT = "VERIFIER_CANDIDATE_UNIT"
    FALLBACK_PATH_CANDIDATE_UNIT = "FALLBACK_PATH_CANDIDATE_UNIT"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"


@dataclass(frozen=True)
class WorkflowAtomicUnit(_CanonicalMixin):
    """The smallest meaningful workflow scheduling unit.

    A scheduling object only: it is not an execution unit, not a worker job,
    and it never executes.
    """

    atomic_unit_id: str
    contract_version: str
    run_id: str
    unit_kind: WorkflowAtomicUnitKind
    node_ids: tuple[str, ...]
    dependency_ids: tuple[str, ...]
    truth_label: FlowTruthLabel
    workflow_id: str = ""
    source_event_ids: tuple[str, ...] = ()
    source_checkpoint_id: str = ""
    source_recovery_candidate_id: str = ""
    source_replay_plan_id: str = ""
    source_graph_revision_id: str = ""
    unavailable_reason: str = SCHEDULING_DISPATCH_UNAVAILABLE_REASON
    candidate_only: bool = True
    worker_job: bool = False
    execution_available: bool = False
    dispatch_available: bool = False

    def __post_init__(self) -> None:
        _forbid_false(self, "candidate_only")
        _forbid_true(
            self, "worker_job", "execution_available", "dispatch_available"
        )
        if not self.run_id:
            raise AurelFlowValidationError(
                "an atomic unit must belong to a run",
                code=AurelFlowErrorCode.EMPTY_RUN_KEY,
                field="run_id",
            )
        if not self.node_ids and self.unit_kind not in (
            WorkflowAtomicUnitKind.UNAVAILABLE,
            WorkflowAtomicUnitKind.ERROR,
        ):
            raise AurelFlowValidationError(
                "an atomic unit must cover at least one workflow node",
                code=AurelFlowErrorCode.EMPTY_NODE_SET,
                field="node_ids",
            )
        if self.atomic_unit_id in self.dependency_ids:
            raise AurelFlowValidationError(
                "an atomic unit cannot depend on itself",
                code=AurelFlowErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                field="dependency_ids",
            )


def create_workflow_atomic_unit(
    *,
    run_id: str,
    unit_kind: WorkflowAtomicUnitKind,
    node_ids: tuple[str, ...],
    dependency_ids: tuple[str, ...] = (),
    workflow_id: str = "",
    source_event_ids: tuple[str, ...] = (),
    source_checkpoint_id: str = "",
    source_recovery_candidate_id: str = "",
    source_replay_plan_id: str = "",
    source_graph_revision_id: str = "",
) -> WorkflowAtomicUnit:
    payload = {
        "contract_version": WORKFLOW_ATOMIC_UNIT_VERSION,
        "run_id": run_id,
        "unit_kind": unit_kind.value,
        "node_ids": node_ids,
        "dependency_ids": dependency_ids,
        "workflow_id": workflow_id,
        "source_event_ids": source_event_ids,
        "source_checkpoint_id": source_checkpoint_id,
        "source_recovery_candidate_id": source_recovery_candidate_id,
        "source_replay_plan_id": source_replay_plan_id,
        "source_graph_revision_id": source_graph_revision_id,
    }
    return WorkflowAtomicUnit(
        atomic_unit_id="flwau-" + stable_hash(payload)[:16],
        contract_version=WORKFLOW_ATOMIC_UNIT_VERSION,
        run_id=run_id,
        unit_kind=unit_kind,
        node_ids=node_ids,
        dependency_ids=dependency_ids,
        truth_label=FlowTruthLabel.LOCAL_RUNTIME_SUBSTRATE,
        workflow_id=workflow_id,
        source_event_ids=source_event_ids,
        source_checkpoint_id=source_checkpoint_id,
        source_recovery_candidate_id=source_recovery_candidate_id,
        source_replay_plan_id=source_replay_plan_id,
        source_graph_revision_id=source_graph_revision_id,
    )


@dataclass(frozen=True)
class WorkflowAtomicUnitRef(_CanonicalMixin):
    """A stable pointer to an atomic unit. A ref dereferences to nothing live."""

    ref_id: str
    contract_version: str
    atomic_unit_id: str
    run_id: str
    unit_kind: WorkflowAtomicUnitKind
    truth_label: FlowTruthLabel
    unavailable_reason: str = SCHEDULING_DISPATCH_UNAVAILABLE_REASON
    dispatch_available: bool = False
    execution_available: bool = False

    def __post_init__(self) -> None:
        _forbid_true(self, "dispatch_available", "execution_available")


def create_workflow_atomic_unit_ref(
    unit: WorkflowAtomicUnit,
) -> WorkflowAtomicUnitRef:
    payload = {
        "contract_version": WORKFLOW_ATOMIC_UNIT_REF_VERSION,
        "atomic_unit_id": unit.atomic_unit_id,
    }
    return WorkflowAtomicUnitRef(
        ref_id="flwar-" + stable_hash(payload)[:16],
        contract_version=WORKFLOW_ATOMIC_UNIT_REF_VERSION,
        atomic_unit_id=unit.atomic_unit_id,
        run_id=unit.run_id,
        unit_kind=unit.unit_kind,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
    )


@dataclass(frozen=True)
class WorkflowAtomicBoundary(_CanonicalMixin):
    """The atomic-unit law as fail-closed data. A unit is not a worker job."""

    boundary_id: str
    contract_version: str
    truth_label: FlowTruthLabel
    unavailable_reason: str = SCHEDULING_DISPATCH_UNAVAILABLE_REASON
    unit_is_not_worker_job: bool = True
    unit_is_not_execution_unit: bool = True
    unit_is_scheduling_object_only: bool = True
    dispatch_available: bool = False
    execution_available: bool = False
    worker_spawned: bool = False

    def __post_init__(self) -> None:
        _forbid_false(
            self,
            "unit_is_not_worker_job",
            "unit_is_not_execution_unit",
            "unit_is_scheduling_object_only",
        )
        _forbid_true(
            self, "dispatch_available", "execution_available", "worker_spawned"
        )


def build_workflow_atomic_boundary() -> WorkflowAtomicBoundary:
    payload = {"contract_version": WORKFLOW_ATOMIC_BOUNDARY_VERSION}
    return WorkflowAtomicBoundary(
        boundary_id="flwab-" + stable_hash(payload)[:16],
        contract_version=WORKFLOW_ATOMIC_BOUNDARY_VERSION,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
    )


@dataclass(frozen=True)
class WorkflowAtomicReadModel(_CanonicalMixin):
    """Deterministic read model over one run's atomic units."""

    read_model_id: str
    contract_version: str
    run_id: str
    unit_count: int
    unit_kind_counts: tuple[tuple[str, int], ...]
    atomic_unit_ids: tuple[str, ...]
    boundary: WorkflowAtomicBoundary
    truth_label: FlowTruthLabel
    unavailable_reason: str = SCHEDULING_DISPATCH_UNAVAILABLE_REASON
    dispatch_available: bool = False
    execution_available: bool = False

    def __post_init__(self) -> None:
        _forbid_true(self, "dispatch_available", "execution_available")


def build_workflow_atomic_read_model(
    *, run_id: str, units: tuple[WorkflowAtomicUnit, ...]
) -> WorkflowAtomicReadModel:
    for unit in units:
        if unit.run_id != run_id:
            raise AurelFlowValidationError(
                f"unit {unit.atomic_unit_id!r} belongs to run "
                f"{unit.run_id!r}, not {run_id!r}",
                code=AurelFlowErrorCode.RUN_MISMATCH,
                field="units",
            )
    kind_counts: dict[str, int] = {}
    for unit in units:
        kind_counts[unit.unit_kind.value] = (
            kind_counts.get(unit.unit_kind.value, 0) + 1
        )
    unit_ids = tuple(sorted(unit.atomic_unit_id for unit in units))
    payload = {
        "contract_version": WORKFLOW_ATOMIC_READ_MODEL_VERSION,
        "run_id": run_id,
        "atomic_unit_ids": unit_ids,
    }
    return WorkflowAtomicReadModel(
        read_model_id="flwam-" + stable_hash(payload)[:16],
        contract_version=WORKFLOW_ATOMIC_READ_MODEL_VERSION,
        run_id=run_id,
        unit_count=len(units),
        unit_kind_counts=tuple(sorted(kind_counts.items())),
        atomic_unit_ids=unit_ids,
        boundary=build_workflow_atomic_boundary(),
        truth_label=FlowTruthLabel.READ_MODEL_ONLY,
    )


class SchedulingIntentKind(str, Enum):
    """Closed-world scheduling intent vocabulary. No kind dispatches."""

    SCHEDULE_READY_NODE_CANDIDATE = "SCHEDULE_READY_NODE_CANDIDATE"
    SCHEDULE_NODE_GROUP_CANDIDATE = "SCHEDULE_NODE_GROUP_CANDIDATE"
    SCHEDULE_RECOVERY_CANDIDATE = "SCHEDULE_RECOVERY_CANDIDATE"
    SCHEDULE_REPLAY_PLAN_CANDIDATE = "SCHEDULE_REPLAY_PLAN_CANDIDATE"
    SCHEDULE_GRAPH_REVISION_CANDIDATE = "SCHEDULE_GRAPH_REVISION_CANDIDATE"
    SCHEDULE_OPERATOR_REVIEW_CANDIDATE = "SCHEDULE_OPERATOR_REVIEW_CANDIDATE"
    SCHEDULE_VERIFIER_CANDIDATE = "SCHEDULE_VERIFIER_CANDIDATE"
    SCHEDULE_FALLBACK_PATH_CANDIDATE = "SCHEDULE_FALLBACK_PATH_CANDIDATE"
    HOLD_SCHEDULING = "HOLD_SCHEDULING"
    BLOCK_SCHEDULING = "BLOCK_SCHEDULING"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"


class SchedulingIntentReason(str, Enum):
    """Why a scheduling intent was raised. A reason is not permission."""

    DEPENDENCIES_SATISFIED = "DEPENDENCIES_SATISFIED"
    RECOVERY_CANDIDATE_SELECTED = "RECOVERY_CANDIDATE_SELECTED"
    REPLAY_PLAN_PREPARED = "REPLAY_PLAN_PREPARED"
    GRAPH_REVISION_PENDING = "GRAPH_REVISION_PENDING"
    OPERATOR_REVIEW_PENDING = "OPERATOR_REVIEW_PENDING"
    VERIFIER_EXPECTED = "VERIFIER_EXPECTED"
    FALLBACK_PATH_SELECTED = "FALLBACK_PATH_SELECTED"
    BUDGET_HOLD = "BUDGET_HOLD"
    AUTONOMY_BLOCKED = "AUTONOMY_BLOCKED"
    RESOURCE_UNAVAILABLE = "RESOURCE_UNAVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"


@dataclass(frozen=True)
class SchedulingIntent(_CanonicalMixin):
    """A candidate-only scheduling proposal. Intent is not dispatch."""

    scheduling_intent_id: str
    contract_version: str
    run_id: str
    atomic_unit_id: str
    intent_kind: SchedulingIntentKind
    intent_reason: SchedulingIntentReason
    truth_label: FlowTruthLabel
    source_ready_state_id: str = ""
    source_dispatchability_id: str = ""
    source_autonomy_gate_id: str = ""
    requires_operator_review: bool = False
    requires_p4_dispatch: bool = True
    requires_p5_proof: bool = False
    requires_p9_authority: bool = False
    unavailable_reason: str = SCHEDULING_DISPATCH_UNAVAILABLE_REASON
    candidate_only: bool = True
    queued: bool = False
    dispatched: bool = False
    execution_available: bool = False

    def __post_init__(self) -> None:
        _forbid_false(self, "candidate_only", "requires_p4_dispatch")
        _forbid_true(self, "queued", "dispatched", "execution_available")


_HOLD_OR_BLOCK_INTENT_KINDS: frozenset[SchedulingIntentKind] = frozenset(
    {
        SchedulingIntentKind.HOLD_SCHEDULING,
        SchedulingIntentKind.BLOCK_SCHEDULING,
        SchedulingIntentKind.SCHEDULE_OPERATOR_REVIEW_CANDIDATE,
    }
)


def create_scheduling_intent(
    *,
    unit: WorkflowAtomicUnit,
    intent_kind: SchedulingIntentKind,
    intent_reason: SchedulingIntentReason,
    source_ready_state_id: str = "",
    source_dispatchability_id: str = "",
    source_autonomy_gate_id: str = "",
    requires_p5_proof: bool = False,
    requires_p9_authority: bool = False,
) -> SchedulingIntent:
    payload = {
        "contract_version": SCHEDULING_INTENT_VERSION,
        "run_id": unit.run_id,
        "atomic_unit_id": unit.atomic_unit_id,
        "intent_kind": intent_kind.value,
        "intent_reason": intent_reason.value,
        "source_ready_state_id": source_ready_state_id,
        "source_dispatchability_id": source_dispatchability_id,
        "source_autonomy_gate_id": source_autonomy_gate_id,
    }
    return SchedulingIntent(
        scheduling_intent_id="flsin-" + stable_hash(payload)[:16],
        contract_version=SCHEDULING_INTENT_VERSION,
        run_id=unit.run_id,
        atomic_unit_id=unit.atomic_unit_id,
        intent_kind=intent_kind,
        intent_reason=intent_reason,
        truth_label=FlowTruthLabel.LOCAL_RUNTIME_SUBSTRATE,
        source_ready_state_id=source_ready_state_id,
        source_dispatchability_id=source_dispatchability_id,
        source_autonomy_gate_id=source_autonomy_gate_id,
        requires_operator_review=intent_kind in _HOLD_OR_BLOCK_INTENT_KINDS,
        requires_p5_proof=requires_p5_proof,
        requires_p9_authority=requires_p9_authority,
    )


@dataclass(frozen=True)
class SchedulingIntentBoundary(_CanonicalMixin):
    """The scheduling-intent law as fail-closed data. Intent is not dispatch."""

    boundary_id: str
    contract_version: str
    truth_label: FlowTruthLabel
    unavailable_reason: str = SCHEDULING_DISPATCH_UNAVAILABLE_REASON
    intent_is_not_dispatch: bool = True
    intent_is_not_enqueue: bool = True
    intent_is_not_execution: bool = True
    runtime_submit_wired: bool = False
    dispatch_available: bool = False
    execution_available: bool = False

    def __post_init__(self) -> None:
        _forbid_false(
            self,
            "intent_is_not_dispatch",
            "intent_is_not_enqueue",
            "intent_is_not_execution",
        )
        _forbid_true(
            self,
            "runtime_submit_wired",
            "dispatch_available",
            "execution_available",
        )


def build_scheduling_intent_boundary() -> SchedulingIntentBoundary:
    payload = {"contract_version": SCHEDULING_INTENT_BOUNDARY_VERSION}
    return SchedulingIntentBoundary(
        boundary_id="flsib-" + stable_hash(payload)[:16],
        contract_version=SCHEDULING_INTENT_BOUNDARY_VERSION,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
    )


@dataclass(frozen=True)
class SchedulingIntentReadModel(_CanonicalMixin):
    """Deterministic read model over one run's scheduling intents."""

    read_model_id: str
    contract_version: str
    run_id: str
    intent_count: int
    intent_kind_counts: tuple[tuple[str, int], ...]
    scheduling_intent_ids: tuple[str, ...]
    hold_or_block_count: int
    boundary: SchedulingIntentBoundary
    truth_label: FlowTruthLabel
    unavailable_reason: str = SCHEDULING_DISPATCH_UNAVAILABLE_REASON
    queued: bool = False
    dispatched: bool = False
    execution_available: bool = False

    def __post_init__(self) -> None:
        _forbid_true(self, "queued", "dispatched", "execution_available")


def build_scheduling_intent_read_model(
    *, run_id: str, intents: tuple[SchedulingIntent, ...]
) -> SchedulingIntentReadModel:
    for intent in intents:
        if intent.run_id != run_id:
            raise AurelFlowValidationError(
                f"intent {intent.scheduling_intent_id!r} belongs to run "
                f"{intent.run_id!r}, not {run_id!r}",
                code=AurelFlowErrorCode.RUN_MISMATCH,
                field="intents",
            )
    kind_counts: dict[str, int] = {}
    for intent in intents:
        kind_counts[intent.intent_kind.value] = (
            kind_counts.get(intent.intent_kind.value, 0) + 1
        )
    intent_ids = tuple(sorted(intent.scheduling_intent_id for intent in intents))
    payload = {
        "contract_version": SCHEDULING_INTENT_READ_MODEL_VERSION,
        "run_id": run_id,
        "scheduling_intent_ids": intent_ids,
    }
    return SchedulingIntentReadModel(
        read_model_id="flsim-" + stable_hash(payload)[:16],
        contract_version=SCHEDULING_INTENT_READ_MODEL_VERSION,
        run_id=run_id,
        intent_count=len(intents),
        intent_kind_counts=tuple(sorted(kind_counts.items())),
        scheduling_intent_ids=intent_ids,
        hold_or_block_count=sum(
            1
            for intent in intents
            if intent.intent_kind in _HOLD_OR_BLOCK_INTENT_KINDS
        ),
        boundary=build_scheduling_intent_boundary(),
        truth_label=FlowTruthLabel.READ_MODEL_ONLY,
    )


class SchedulingAutonomyDecision(str, Enum):
    """Closed-world autonomy-gated scheduling outcomes. Never dispatch."""

    ALLOW_SCHEDULING_CANDIDATE = "ALLOW_SCHEDULING_CANDIDATE"
    HOLD_SCHEDULING = "HOLD_SCHEDULING"
    REQUIRE_OPERATOR_REVIEW = "REQUIRE_OPERATOR_REVIEW"
    REQUIRE_P9_AUTHORITY = "REQUIRE_P9_AUTHORITY"
    BLOCK_SCHEDULING = "BLOCK_SCHEDULING"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"


@dataclass(frozen=True)
class SchedulingScopeCheck(_CanonicalMixin):
    """Does a scheduling intent stay inside the H scope envelope?

    A scope check restricts; it never authorizes. With no envelope the check
    fails closed to outside-scope.
    """

    scope_check_id: str
    contract_version: str
    run_id: str
    atomic_unit_id: str
    scope_envelope_id: str
    inside_scope: bool
    checked_dimension_values: tuple[str, ...]
    uncovered_dimension_values: tuple[str, ...]
    truth_label: FlowTruthLabel
    unavailable_reason: str = SCHEDULING_GATE_UNAVAILABLE_REASON
    check_is_not_permission: bool = True
    authority_granted: bool = False
    execution_available: bool = False

    def __post_init__(self) -> None:
        _forbid_false(self, "check_is_not_permission")
        _forbid_true(self, "authority_granted", "execution_available")


def create_scheduling_scope_check(
    *,
    unit: WorkflowAtomicUnit,
    envelope: AutonomyScopeEnvelope | None,
    required_dimensions: tuple[AutonomyScopeDimension, ...],
) -> SchedulingScopeCheck:
    if envelope is not None and envelope.run_id != unit.run_id:
        raise AurelFlowValidationError(
            f"scope envelope run {envelope.run_id!r} does not match unit "
            f"run {unit.run_id!r}",
            code=AurelFlowErrorCode.RUN_MISMATCH,
            field="envelope",
        )
    if envelope is None:
        uncovered = tuple(dim.value for dim in required_dimensions)
        inside_scope = False
    else:
        uncovered = tuple(
            dim.value for dim in required_dimensions if not envelope.covers(dim)
        )
        inside_scope = not uncovered
    payload = {
        "contract_version": SCHEDULING_SCOPE_CHECK_VERSION,
        "run_id": unit.run_id,
        "atomic_unit_id": unit.atomic_unit_id,
        "scope_envelope_id": envelope.envelope_id if envelope else "",
        "required_dimensions": tuple(dim.value for dim in required_dimensions),
    }
    return SchedulingScopeCheck(
        scope_check_id="flssc-" + stable_hash(payload)[:16],
        contract_version=SCHEDULING_SCOPE_CHECK_VERSION,
        run_id=unit.run_id,
        atomic_unit_id=unit.atomic_unit_id,
        scope_envelope_id=envelope.envelope_id if envelope else "",
        inside_scope=inside_scope,
        checked_dimension_values=tuple(
            dim.value for dim in required_dimensions
        ),
        uncovered_dimension_values=uncovered,
        truth_label=FlowTruthLabel.LOCAL_RUNTIME_SUBSTRATE,
    )


@dataclass(frozen=True)
class SchedulingActionBoundaryCheck(_CanonicalMixin):
    """The H action-boundary matrix applied to a scheduling decision class."""

    boundary_check_id: str
    contract_version: str
    run_id: str
    atomic_unit_id: str
    level_value: str
    decision_class_value: str
    action_boundary_category: str
    decision_class_allowed: bool
    forbidden_in_p3: bool
    requires_operator_review: bool
    future_p4_required: bool
    future_p5_required: bool
    future_p9_required: bool
    truth_label: FlowTruthLabel
    unavailable_reason: str = SCHEDULING_GATE_UNAVAILABLE_REASON
    authority_granted: bool = False
    execution_available: bool = False
    dispatch_available: bool = False

    def __post_init__(self) -> None:
        _forbid_true(
            self,
            "authority_granted",
            "execution_available",
            "dispatch_available",
        )


def create_scheduling_action_boundary_check(
    *,
    unit: WorkflowAtomicUnit,
    level: GovernedAutonomyLevel,
    decision_class: AutonomyDecisionClass,
) -> SchedulingActionBoundaryCheck:
    boundary = resolve_action_boundary(level, decision_class)
    resolution = boundary.resolution
    payload = {
        "contract_version": SCHEDULING_ACTION_BOUNDARY_CHECK_VERSION,
        "atomic_unit_id": unit.atomic_unit_id,
        "resolution_id": resolution.resolution_id,
    }
    return SchedulingActionBoundaryCheck(
        boundary_check_id="flsbc-" + stable_hash(payload)[:16],
        contract_version=SCHEDULING_ACTION_BOUNDARY_CHECK_VERSION,
        run_id=unit.run_id,
        atomic_unit_id=unit.atomic_unit_id,
        level_value=resolution.level_value,
        decision_class_value=resolution.decision_class_value,
        action_boundary_category=resolution.permission_state.value,
        decision_class_allowed=boundary.read_only_allowed
        or boundary.candidate_only_allowed,
        forbidden_in_p3=resolution.permission_state
        is AutonomyPermissionState.FORBIDDEN_IN_P3,
        requires_operator_review=boundary.requires_operator_review,
        future_p4_required=boundary.future_p4_required,
        future_p5_required=boundary.future_p5_required,
        future_p9_required=boundary.future_p9_required,
        truth_label=FlowTruthLabel.LOCAL_RUNTIME_SUBSTRATE,
    )


@dataclass(frozen=True)
class AutonomySchedulingGate(_CanonicalMixin):
    """A scheduling intent gated through H autonomy boundaries.

    The gate restricts a scheduling candidate; it is not authority, it never
    dispatches, and it cannot bypass H or future P9.
    """

    scheduling_gate_id: str
    contract_version: str
    run_id: str
    atomic_unit_id: str
    scheduling_intent_id: str
    autonomy_level: GovernedAutonomyLevel
    decision: SchedulingAutonomyDecision
    reason: str
    inside_scope: bool
    decision_class_allowed: bool
    action_boundary_category: str
    forbidden_in_p3: bool
    truth_label: FlowTruthLabel
    scope_envelope_id: str = ""
    requires_operator_review: bool = False
    requires_p4_execution: bool = True
    requires_p5_proof: bool = False
    requires_p9_authority: bool = False
    unavailable_reason: str = SCHEDULING_GATE_UNAVAILABLE_REASON
    gate_is_not_authority: bool = True
    gate_is_not_dispatch: bool = True
    authority_granted: bool = False
    permission_granted: bool = False
    execution_available: bool = False
    dispatch_available: bool = False

    def __post_init__(self) -> None:
        _forbid_false(
            self,
            "gate_is_not_authority",
            "gate_is_not_dispatch",
            "requires_p4_execution",
        )
        _forbid_true(
            self,
            "authority_granted",
            "permission_granted",
            "execution_available",
            "dispatch_available",
        )


def evaluate_autonomy_scheduling_gate(
    *,
    intent: SchedulingIntent,
    scope_check: SchedulingScopeCheck,
    boundary_check: SchedulingActionBoundaryCheck,
) -> AutonomySchedulingGate:
    """Deterministic ladder: forbidden > authority > outside-scope > review > allow.

    The gate consumes H resolver truth via the boundary check — it never
    re-derives its own permission rules and can never out-allow H.
    """

    for source_name, source_unit_id in (
        ("scope_check", scope_check.atomic_unit_id),
        ("boundary_check", boundary_check.atomic_unit_id),
    ):
        if source_unit_id != intent.atomic_unit_id:
            raise AurelFlowValidationError(
                f"{source_name} covers unit {source_unit_id!r}, not the "
                f"intent's unit {intent.atomic_unit_id!r}",
                code=AurelFlowErrorCode.RUN_MISMATCH,
                field=source_name,
            )
    if boundary_check.forbidden_in_p3:
        decision = SchedulingAutonomyDecision.BLOCK_SCHEDULING
        reason = (
            "the decision class is FORBIDDEN_IN_P3 at every autonomy level; "
            "scheduling it is blocked"
        )
        requires_review = True
    elif boundary_check.future_p9_required:
        decision = SchedulingAutonomyDecision.REQUIRE_P9_AUTHORITY
        reason = (
            "the decision class requires future P9 authority; scheduling "
            "intent cannot substitute for Custos"
        )
        requires_review = True
    elif not scope_check.inside_scope:
        decision = SchedulingAutonomyDecision.HOLD_SCHEDULING
        reason = (
            "the scheduling intent falls outside the autonomy scope "
            "envelope; hold for operator review"
        )
        requires_review = True
    elif (
        boundary_check.requires_operator_review
        or intent.requires_operator_review
        or not boundary_check.decision_class_allowed
    ):
        decision = SchedulingAutonomyDecision.REQUIRE_OPERATOR_REVIEW
        reason = (
            "the H boundary or the intent itself requires operator review "
            "before this scheduling candidate can go further"
        )
        requires_review = True
    else:
        decision = SchedulingAutonomyDecision.ALLOW_SCHEDULING_CANDIDATE
        reason = (
            "inside scope and candidate-allowed by the H resolver; still a "
            "candidate only — dispatch requires future P4"
        )
        requires_review = False
    payload = {
        "contract_version": AUTONOMY_SCHEDULING_GATE_VERSION,
        "scheduling_intent_id": intent.scheduling_intent_id,
        "scope_check_id": scope_check.scope_check_id,
        "boundary_check_id": boundary_check.boundary_check_id,
        "decision": decision.value,
    }
    return AutonomySchedulingGate(
        scheduling_gate_id="flsgt-" + stable_hash(payload)[:16],
        contract_version=AUTONOMY_SCHEDULING_GATE_VERSION,
        run_id=intent.run_id,
        atomic_unit_id=intent.atomic_unit_id,
        scheduling_intent_id=intent.scheduling_intent_id,
        autonomy_level=GovernedAutonomyLevel(boundary_check.level_value),
        decision=decision,
        reason=reason,
        inside_scope=scope_check.inside_scope,
        decision_class_allowed=boundary_check.decision_class_allowed,
        action_boundary_category=boundary_check.action_boundary_category,
        forbidden_in_p3=boundary_check.forbidden_in_p3,
        truth_label=FlowTruthLabel.LOCAL_RUNTIME_SUBSTRATE,
        scope_envelope_id=scope_check.scope_envelope_id,
        requires_operator_review=requires_review,
        requires_p5_proof=boundary_check.future_p5_required
        or intent.requires_p5_proof,
        requires_p9_authority=boundary_check.future_p9_required
        or intent.requires_p9_authority,
    )


@dataclass(frozen=True)
class SchedulingGateReadModel(_CanonicalMixin):
    """Deterministic read model over one run's autonomy scheduling gates."""

    read_model_id: str
    contract_version: str
    run_id: str
    gate_count: int
    decision_counts: tuple[tuple[str, int], ...]
    scheduling_gate_ids: tuple[str, ...]
    review_required_count: int
    blocked_count: int
    truth_label: FlowTruthLabel
    unavailable_reason: str = SCHEDULING_GATE_UNAVAILABLE_REASON
    authority_granted: bool = False
    execution_available: bool = False
    dispatch_available: bool = False

    def __post_init__(self) -> None:
        _forbid_true(
            self,
            "authority_granted",
            "execution_available",
            "dispatch_available",
        )


def build_scheduling_gate_read_model(
    *, run_id: str, gates: tuple[AutonomySchedulingGate, ...]
) -> SchedulingGateReadModel:
    for gate in gates:
        if gate.run_id != run_id:
            raise AurelFlowValidationError(
                f"gate {gate.scheduling_gate_id!r} belongs to run "
                f"{gate.run_id!r}, not {run_id!r}",
                code=AurelFlowErrorCode.RUN_MISMATCH,
                field="gates",
            )
    decision_counts: dict[str, int] = {}
    for gate in gates:
        decision_counts[gate.decision.value] = (
            decision_counts.get(gate.decision.value, 0) + 1
        )
    gate_ids = tuple(sorted(gate.scheduling_gate_id for gate in gates))
    payload = {
        "contract_version": SCHEDULING_GATE_READ_MODEL_VERSION,
        "run_id": run_id,
        "scheduling_gate_ids": gate_ids,
    }
    return SchedulingGateReadModel(
        read_model_id="flsgm-" + stable_hash(payload)[:16],
        contract_version=SCHEDULING_GATE_READ_MODEL_VERSION,
        run_id=run_id,
        gate_count=len(gates),
        decision_counts=tuple(sorted(decision_counts.items())),
        scheduling_gate_ids=gate_ids,
        review_required_count=sum(
            1 for gate in gates if gate.requires_operator_review
        ),
        blocked_count=sum(
            1
            for gate in gates
            if gate.decision is SchedulingAutonomyDecision.BLOCK_SCHEDULING
        ),
        truth_label=FlowTruthLabel.READ_MODEL_ONLY,
    )
