"""P3-FLOW-I scheduling projection / React readiness / boundary proofs (P3.17).

React is projection only: every scheduling view model is read-only, a UI
schedule button is not dispatch, a UI queue action is not execution, and no
React component, frontend route, frontend state, API server, REST, or
WebSocket exists. The no-dispatch / no-execution / no-resource-allocation
proofs carry the pack's side-effect boundaries as fail-closed data — report
evidence, not runtime proof (proof belongs to P5 AurelTrace).
"""

from __future__ import annotations

from dataclasses import dataclass

from .errors import AurelFlowErrorCode, AurelFlowValidationError
from .flow_dispatchability import (
    ConcurrencyWindow,
    DispatchabilityFrame,
    QueuePlacementCandidate,
)
from .flow_resource_prediction import ResourcePredictionFrame
from .flow_scheduling_intent import SchedulingIntent
from .types import FlowTruthLabel, _CanonicalMixin, stable_hash

SCHEDULING_TIMELINE_VIEW_MODEL_VERSION = "scheduling_timeline_view_model.v1"
SCHEDULING_INTENT_VIEW_MODEL_VERSION = "scheduling_intent_view_model.v1"
RESOURCE_PREDICTION_VIEW_MODEL_VERSION = "resource_prediction_view_model.v1"
DISPATCHABILITY_VIEW_MODEL_VERSION = "dispatchability_view_model.v1"
QUEUE_CANDIDATE_VIEW_MODEL_VERSION = "queue_candidate_view_model.v1"
CONCURRENCY_WINDOW_VIEW_MODEL_VERSION = "concurrency_window_view_model.v1"
SCHEDULING_PROJECTION_ENVELOPE_VERSION = "scheduling_projection_envelope.v1"
SCHEDULING_REACT_PROJECTION_BOUNDARY_VERSION = (
    "scheduling_react_projection_boundary.v1"
)
NO_DISPATCH_BOUNDARY_PROOF_VERSION = "no_dispatch_boundary_proof.v1"
NO_EXECUTION_BOUNDARY_PROOF_VERSION = "no_execution_boundary_proof.v1"
NO_RESOURCE_ALLOCATION_PROOF_VERSION = "no_resource_allocation_proof.v1"

SCHEDULING_PROJECTION_UNAVAILABLE_REASON = (
    "no React component, frontend route, frontend state, API server, REST, "
    "or WebSocket exists in P3-FLOW-I; these view models are read-only "
    "contracts for a future AurelShell — a UI schedule button is not "
    "dispatch and a UI queue action is not execution"
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


_UI_POWERLESSNESS_FALSE_FIELDS: tuple[str, ...] = (
    "frontend_mutation_allowed",
    "ui_schedule_action_allowed",
    "ui_queue_action_allowed",
    "ui_dispatch_allowed",
    "api_server_implemented",
    "frontend_implemented",
)


@dataclass(frozen=True)
class _ReactViewModelBase(_CanonicalMixin):
    """Shared UI-powerlessness boundary for every scheduling view model."""

    view_model_id: str
    contract_version: str
    run_id: str
    truth_label: FlowTruthLabel
    unavailable_reason: str = SCHEDULING_PROJECTION_UNAVAILABLE_REASON
    react_projection_only: bool = True
    read_only: bool = True
    frontend_mutation_allowed: bool = False
    ui_schedule_action_allowed: bool = False
    ui_queue_action_allowed: bool = False
    ui_dispatch_allowed: bool = False
    api_server_implemented: bool = False
    frontend_implemented: bool = False

    def __post_init__(self) -> None:
        _forbid_false(self, "react_projection_only", "read_only")
        _forbid_true(self, *_UI_POWERLESSNESS_FALSE_FIELDS)


@dataclass(frozen=True)
class SchedulingTimelineViewModel(_ReactViewModelBase):
    """Ordered scheduling intent values for a future timeline surface."""

    intent_kind_values: tuple[str, ...] = ()
    atomic_unit_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class SchedulingIntentViewModel(_ReactViewModelBase):
    """One scheduling intent, rendered read-only."""

    scheduling_intent_id: str = ""
    atomic_unit_id: str = ""
    intent_kind_value: str = ""
    intent_reason_value: str = ""
    requires_operator_review: bool = False


@dataclass(frozen=True)
class ResourcePredictionViewModel(_ReactViewModelBase):
    """One resource prediction frame, rendered read-only."""

    resource_prediction_id: str = ""
    atomic_unit_id: str = ""
    dimension_values: tuple[str, ...] = ()
    resource_available: bool = False
    resource_pressure_detected: bool = False


@dataclass(frozen=True)
class DispatchabilityViewModel(_ReactViewModelBase):
    """Why a unit is or is not dispatchable, rendered read-only."""

    dispatchability_id: str = ""
    atomic_unit_id: str = ""
    dispatchable_candidate: bool = False
    dispatchability_reason_value: str = ""
    explanation: str = ""


@dataclass(frozen=True)
class QueueCandidateViewModel(_ReactViewModelBase):
    """One queue placement candidate, rendered read-only."""

    queue_candidate_id: str = ""
    atomic_unit_id: str = ""
    placement_kind_value: str = ""
    placement_reason_value: str = ""
    priority_hint: int | None = None


@dataclass(frozen=True)
class ConcurrencyWindowViewModel(_ReactViewModelBase):
    """One concurrency window, rendered read-only."""

    concurrency_window_id: str = ""
    atomic_unit_ids: tuple[str, ...] = ()
    parallel_candidate_unit_ids: tuple[str, ...] = ()
    unsafe_parallel_unit_ids: tuple[str, ...] = ()
    requires_operator_ordering: bool = False


def build_scheduling_timeline_view_model(
    *, run_id: str, intents: tuple[SchedulingIntent, ...]
) -> SchedulingTimelineViewModel:
    for intent in intents:
        if intent.run_id != run_id:
            raise AurelFlowValidationError(
                f"intent {intent.scheduling_intent_id!r} belongs to run "
                f"{intent.run_id!r}, not {run_id!r}",
                code=AurelFlowErrorCode.RUN_MISMATCH,
                field="intents",
            )
    payload = {
        "contract_version": SCHEDULING_TIMELINE_VIEW_MODEL_VERSION,
        "run_id": run_id,
        "intent_ids": tuple(i.scheduling_intent_id for i in intents),
    }
    return SchedulingTimelineViewModel(
        view_model_id="flstv-" + stable_hash(payload)[:16],
        contract_version=SCHEDULING_TIMELINE_VIEW_MODEL_VERSION,
        run_id=run_id,
        truth_label=FlowTruthLabel.READ_MODEL_ONLY,
        intent_kind_values=tuple(i.intent_kind.value for i in intents),
        atomic_unit_ids=tuple(i.atomic_unit_id for i in intents),
    )


def build_scheduling_intent_view_model(
    intent: SchedulingIntent,
) -> SchedulingIntentViewModel:
    payload = {
        "contract_version": SCHEDULING_INTENT_VIEW_MODEL_VERSION,
        "scheduling_intent_id": intent.scheduling_intent_id,
    }
    return SchedulingIntentViewModel(
        view_model_id="flsiv-" + stable_hash(payload)[:16],
        contract_version=SCHEDULING_INTENT_VIEW_MODEL_VERSION,
        run_id=intent.run_id,
        truth_label=FlowTruthLabel.READ_MODEL_ONLY,
        scheduling_intent_id=intent.scheduling_intent_id,
        atomic_unit_id=intent.atomic_unit_id,
        intent_kind_value=intent.intent_kind.value,
        intent_reason_value=intent.intent_reason.value,
        requires_operator_review=intent.requires_operator_review,
    )


def build_resource_prediction_view_model(
    frame: ResourcePredictionFrame,
) -> ResourcePredictionViewModel:
    payload = {
        "contract_version": RESOURCE_PREDICTION_VIEW_MODEL_VERSION,
        "resource_prediction_id": frame.resource_prediction_id,
    }
    return ResourcePredictionViewModel(
        view_model_id="flrpv-" + stable_hash(payload)[:16],
        contract_version=RESOURCE_PREDICTION_VIEW_MODEL_VERSION,
        run_id=frame.run_id,
        truth_label=FlowTruthLabel.READ_MODEL_ONLY,
        resource_prediction_id=frame.resource_prediction_id,
        atomic_unit_id=frame.atomic_unit_id,
        dimension_values=tuple(
            dimension.value for dimension in frame.resource_dimensions
        ),
        resource_available=frame.resource_available,
        resource_pressure_detected=frame.resource_pressure_detected,
    )


def build_dispatchability_view_model(
    frame: DispatchabilityFrame,
) -> DispatchabilityViewModel:
    payload = {
        "contract_version": DISPATCHABILITY_VIEW_MODEL_VERSION,
        "dispatchability_id": frame.dispatchability_id,
    }
    return DispatchabilityViewModel(
        view_model_id="fldpv-" + stable_hash(payload)[:16],
        contract_version=DISPATCHABILITY_VIEW_MODEL_VERSION,
        run_id=frame.run_id,
        truth_label=FlowTruthLabel.READ_MODEL_ONLY,
        dispatchability_id=frame.dispatchability_id,
        atomic_unit_id=frame.atomic_unit_id,
        dispatchable_candidate=frame.dispatchable_candidate,
        dispatchability_reason_value=frame.dispatchability_reason.value,
        explanation=frame.explanation,
    )


def build_queue_candidate_view_model(
    candidate: QueuePlacementCandidate,
) -> QueueCandidateViewModel:
    payload = {
        "contract_version": QUEUE_CANDIDATE_VIEW_MODEL_VERSION,
        "queue_candidate_id": candidate.queue_candidate_id,
    }
    return QueueCandidateViewModel(
        view_model_id="flqcv-" + stable_hash(payload)[:16],
        contract_version=QUEUE_CANDIDATE_VIEW_MODEL_VERSION,
        run_id=candidate.run_id,
        truth_label=FlowTruthLabel.READ_MODEL_ONLY,
        queue_candidate_id=candidate.queue_candidate_id,
        atomic_unit_id=candidate.atomic_unit_id,
        placement_kind_value=candidate.placement_kind.value,
        placement_reason_value=candidate.placement_reason.value,
        priority_hint=candidate.priority_hint,
    )


def build_concurrency_window_view_model(
    window: ConcurrencyWindow,
) -> ConcurrencyWindowViewModel:
    payload = {
        "contract_version": CONCURRENCY_WINDOW_VIEW_MODEL_VERSION,
        "concurrency_window_id": window.concurrency_window_id,
    }
    return ConcurrencyWindowViewModel(
        view_model_id="flcwv-" + stable_hash(payload)[:16],
        contract_version=CONCURRENCY_WINDOW_VIEW_MODEL_VERSION,
        run_id=window.run_id,
        truth_label=FlowTruthLabel.READ_MODEL_ONLY,
        concurrency_window_id=window.concurrency_window_id,
        atomic_unit_ids=window.atomic_unit_ids,
        parallel_candidate_unit_ids=window.parallel_candidate_unit_ids,
        unsafe_parallel_unit_ids=window.unsafe_parallel_unit_ids,
        requires_operator_ordering=window.requires_operator_ordering,
    )


@dataclass(frozen=True)
class SchedulingReactProjectionBoundary(_CanonicalMixin):
    """The React scheduling law as fail-closed data.

    Python runtime is the source of truth; React is projection only; a UI
    schedule button is not dispatch; a UI queue action is not execution.
    """

    boundary_id: str
    contract_version: str
    truth_label: FlowTruthLabel
    runtime_source_of_truth: str = "python"
    unavailable_reason: str = SCHEDULING_PROJECTION_UNAVAILABLE_REASON
    react_projection_only: bool = True
    ui_schedule_button_is_not_dispatch: bool = True
    ui_queue_action_is_not_execution: bool = True
    frontend_mutation_allowed: bool = False
    ui_schedule_action_allowed: bool = False
    ui_queue_action_allowed: bool = False
    ui_dispatch_allowed: bool = False
    api_server_implemented: bool = False
    frontend_implemented: bool = False

    def __post_init__(self) -> None:
        _forbid_false(
            self,
            "react_projection_only",
            "ui_schedule_button_is_not_dispatch",
            "ui_queue_action_is_not_execution",
        )
        _forbid_true(self, *_UI_POWERLESSNESS_FALSE_FIELDS)
        if self.runtime_source_of_truth != "python":
            raise AurelFlowValidationError(
                "the Python runtime is the P3 source of truth",
                code=AurelFlowErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                field="runtime_source_of_truth",
            )


def build_scheduling_react_projection_boundary() -> (
    SchedulingReactProjectionBoundary
):
    payload = {
        "contract_version": SCHEDULING_REACT_PROJECTION_BOUNDARY_VERSION
    }
    return SchedulingReactProjectionBoundary(
        boundary_id="flsrb-" + stable_hash(payload)[:16],
        contract_version=SCHEDULING_REACT_PROJECTION_BOUNDARY_VERSION,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
    )


@dataclass(frozen=True)
class SchedulingProjectionEnvelope(_CanonicalMixin):
    """Everything a future React/AurelShell may render about scheduling."""

    envelope_id: str
    contract_version: str
    run_id: str
    timeline: SchedulingTimelineViewModel
    intent_views: tuple[SchedulingIntentViewModel, ...]
    resource_prediction_views: tuple[ResourcePredictionViewModel, ...]
    dispatchability_views: tuple[DispatchabilityViewModel, ...]
    queue_candidate_views: tuple[QueueCandidateViewModel, ...]
    concurrency_window_views: tuple[ConcurrencyWindowViewModel, ...]
    boundary: SchedulingReactProjectionBoundary
    truth_label: FlowTruthLabel
    unavailable_reason: str = SCHEDULING_PROJECTION_UNAVAILABLE_REASON
    react_projection_only: bool = True
    read_only: bool = True
    frontend_mutation_allowed: bool = False
    ui_schedule_action_allowed: bool = False
    ui_queue_action_allowed: bool = False
    ui_dispatch_allowed: bool = False
    api_server_implemented: bool = False
    frontend_implemented: bool = False

    def __post_init__(self) -> None:
        _forbid_false(self, "react_projection_only", "read_only")
        _forbid_true(self, *_UI_POWERLESSNESS_FALSE_FIELDS)


def build_scheduling_projection_envelope(
    *,
    run_id: str,
    timeline: SchedulingTimelineViewModel,
    intent_views: tuple[SchedulingIntentViewModel, ...] = (),
    resource_prediction_views: tuple[ResourcePredictionViewModel, ...] = (),
    dispatchability_views: tuple[DispatchabilityViewModel, ...] = (),
    queue_candidate_views: tuple[QueueCandidateViewModel, ...] = (),
    concurrency_window_views: tuple[ConcurrencyWindowViewModel, ...] = (),
) -> SchedulingProjectionEnvelope:
    view_run_ids: tuple[tuple[str, str], ...] = (
        ("timeline", timeline.run_id),
        *(("intent_views", view.run_id) for view in intent_views),
        *(
            ("resource_prediction_views", view.run_id)
            for view in resource_prediction_views
        ),
        *(
            ("dispatchability_views", view.run_id)
            for view in dispatchability_views
        ),
        *(
            ("queue_candidate_views", view.run_id)
            for view in queue_candidate_views
        ),
        *(
            ("concurrency_window_views", view.run_id)
            for view in concurrency_window_views
        ),
    )
    for source_name, source_run_id in view_run_ids:
        if source_run_id != run_id:
            raise AurelFlowValidationError(
                f"{source_name} entry belongs to run {source_run_id!r}, "
                f"not {run_id!r}",
                code=AurelFlowErrorCode.RUN_MISMATCH,
                field=source_name,
            )
    payload = {
        "contract_version": SCHEDULING_PROJECTION_ENVELOPE_VERSION,
        "run_id": run_id,
        "view_model_ids": tuple(
            sorted(
                [timeline.view_model_id]
                + [view.view_model_id for view in intent_views]
                + [view.view_model_id for view in resource_prediction_views]
                + [view.view_model_id for view in dispatchability_views]
                + [view.view_model_id for view in queue_candidate_views]
                + [view.view_model_id for view in concurrency_window_views]
            )
        ),
    }
    return SchedulingProjectionEnvelope(
        envelope_id="flspe-" + stable_hash(payload)[:16],
        contract_version=SCHEDULING_PROJECTION_ENVELOPE_VERSION,
        run_id=run_id,
        timeline=timeline,
        intent_views=intent_views,
        resource_prediction_views=resource_prediction_views,
        dispatchability_views=dispatchability_views,
        queue_candidate_views=queue_candidate_views,
        concurrency_window_views=concurrency_window_views,
        boundary=build_scheduling_react_projection_boundary(),
        truth_label=FlowTruthLabel.READ_MODEL_ONLY,
    )


@dataclass(frozen=True)
class NoDispatchBoundaryProof(_CanonicalMixin):
    """All-false dispatch booleans as data. Report evidence, not P5 proof."""

    proof_id: str
    contract_version: str
    truth_label: FlowTruthLabel
    unavailable_reason: str = SCHEDULING_PROJECTION_UNAVAILABLE_REASON
    is_p5_trace_proof: bool = False
    dispatched: bool = False
    dispatch_available: bool = False
    queued: bool = False
    actual_queue_inserted: bool = False
    worker_assigned: bool = False
    runtime_submit_wired: bool = False
    runtime_submit_called: bool = False
    ui_dispatch_allowed: bool = False

    def __post_init__(self) -> None:
        _forbid_true(
            self,
            "is_p5_trace_proof",
            "dispatched",
            "dispatch_available",
            "queued",
            "actual_queue_inserted",
            "worker_assigned",
            "runtime_submit_wired",
            "runtime_submit_called",
            "ui_dispatch_allowed",
        )


@dataclass(frozen=True)
class NoExecutionBoundaryProof(_CanonicalMixin):
    """All-false execution booleans as data. Report evidence, not P5 proof."""

    proof_id: str
    contract_version: str
    truth_label: FlowTruthLabel
    unavailable_reason: str = SCHEDULING_PROJECTION_UNAVAILABLE_REASON
    is_p5_trace_proof: bool = False
    execution_available: bool = False
    worker_spawned: bool = False
    parallel_execution_available: bool = False
    model_invoked: bool = False
    tool_invoked: bool = False
    sandbox_executed: bool = False
    subprocess_spawned: bool = False
    network_called: bool = False
    data_access_performed: bool = False
    memory_access_performed: bool = False
    trace_written: bool = False
    ledger_written: bool = False
    policy_mutated: bool = False
    identity_mutated: bool = False

    def __post_init__(self) -> None:
        _forbid_true(
            self,
            "is_p5_trace_proof",
            "execution_available",
            "worker_spawned",
            "parallel_execution_available",
            "model_invoked",
            "tool_invoked",
            "sandbox_executed",
            "subprocess_spawned",
            "network_called",
            "data_access_performed",
            "memory_access_performed",
            "trace_written",
            "ledger_written",
            "policy_mutated",
            "identity_mutated",
        )


@dataclass(frozen=True)
class NoResourceAllocationProof(_CanonicalMixin):
    """All-false allocation booleans as data. Report evidence, not P5 proof."""

    proof_id: str
    contract_version: str
    truth_label: FlowTruthLabel
    unavailable_reason: str = SCHEDULING_PROJECTION_UNAVAILABLE_REASON
    is_p5_trace_proof: bool = False
    resource_allocated: bool = False
    resource_reserved: bool = False
    measured_usage: bool = False
    billing_performed: bool = False
    tokens_consumed: bool = False
    permission_granted: bool = False
    authority_granted: bool = False

    def __post_init__(self) -> None:
        _forbid_true(
            self,
            "is_p5_trace_proof",
            "resource_allocated",
            "resource_reserved",
            "measured_usage",
            "billing_performed",
            "tokens_consumed",
            "permission_granted",
            "authority_granted",
        )


def build_no_dispatch_boundary_proof() -> NoDispatchBoundaryProof:
    payload = {"contract_version": NO_DISPATCH_BOUNDARY_PROOF_VERSION}
    return NoDispatchBoundaryProof(
        proof_id="flndp-" + stable_hash(payload)[:16],
        contract_version=NO_DISPATCH_BOUNDARY_PROOF_VERSION,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
    )


def build_no_execution_boundary_proof() -> NoExecutionBoundaryProof:
    payload = {"contract_version": NO_EXECUTION_BOUNDARY_PROOF_VERSION}
    return NoExecutionBoundaryProof(
        proof_id="flnep-" + stable_hash(payload)[:16],
        contract_version=NO_EXECUTION_BOUNDARY_PROOF_VERSION,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
    )


def build_no_resource_allocation_proof() -> NoResourceAllocationProof:
    payload = {"contract_version": NO_RESOURCE_ALLOCATION_PROOF_VERSION}
    return NoResourceAllocationProof(
        proof_id="flnra-" + stable_hash(payload)[:16],
        contract_version=NO_RESOURCE_ALLOCATION_PROOF_VERSION,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
    )
