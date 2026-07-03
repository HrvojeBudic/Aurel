"""P3-FLOW-I resource prediction / advisory estimates / requirement frames (P3.17).

Prediction is not allocation: a resource prediction frame estimates what a
unit *would* need without reserving, allocating, measuring, or permitting
anything. Cost/latency/token/context estimates are advisory only — no cost is
billed, no token is consumed, nothing is measured, nothing is proven. A
model/tool/sandbox/data requirement frame names a future execution
requirement and is never an invocation, call, sandbox execution, data access,
or network use.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .errors import AurelFlowErrorCode, AurelFlowValidationError
from .flow_scheduling_intent import WorkflowAtomicUnit
from .types import FlowTruthLabel, _CanonicalMixin, stable_hash

RESOURCE_REQUIREMENT_ESTIMATE_VERSION = "resource_requirement_estimate.v1"
RESOURCE_PRESSURE_SIGNAL_VERSION = "resource_pressure_signal.v1"
RESOURCE_AVAILABILITY_BOUNDARY_VERSION = "resource_availability_boundary.v1"
RESOURCE_PREDICTION_FRAME_VERSION = "resource_prediction_frame.v1"
RESOURCE_PREDICTION_READ_MODEL_VERSION = "resource_prediction_read_model.v1"
COST_ESTIMATE_VERSION = "cost_estimate.v1"
LATENCY_ESTIMATE_VERSION = "latency_estimate.v1"
TOKEN_BUDGET_ESTIMATE_VERSION = "token_budget_estimate.v1"
CONTEXT_WINDOW_ESTIMATE_VERSION = "context_window_estimate.v1"
SCHEDULING_ESTIMATE_READ_MODEL_VERSION = "scheduling_estimate_read_model.v1"
MODEL_REQUIREMENT_FRAME_VERSION = "model_requirement_frame.v1"
TOOL_REQUIREMENT_FRAME_VERSION = "tool_requirement_frame.v1"
SANDBOX_REQUIREMENT_FRAME_VERSION = "sandbox_requirement_frame.v1"
DATA_ACCESS_REQUIREMENT_FRAME_VERSION = "data_access_requirement_frame.v1"
EXECUTION_RESOURCE_REQUIREMENT_READ_MODEL_VERSION = (
    "execution_resource_requirement_read_model.v1"
)

RESOURCE_ALLOCATION_UNAVAILABLE_REASON = (
    "prediction is not allocation: no resource is allocated, reserved, or "
    "measured in P3, no cost is billed, no token is consumed, and resource "
    "availability is not permission — allocation belongs to P4 AurelExec, "
    "proof to P5 AurelTrace, permission to P9 Custos"
)
REQUIREMENT_INVOCATION_UNAVAILABLE_REASON = (
    "a requirement is not invocation: naming a model, tool, sandbox, data, "
    "network, or memory requirement never calls a model, invokes a tool, "
    "executes a sandbox, accesses data, or touches the network — invocation "
    "belongs to P4 AurelExec under P9 Custos authority"
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


class ResourceDimension(str, Enum):
    """Closed-world resource dimensions a prediction may cover."""

    TOKEN_BUDGET = "TOKEN_BUDGET"
    CONTEXT_WINDOW = "CONTEXT_WINDOW"
    LATENCY = "LATENCY"
    COST = "COST"
    MODEL_CLASS = "MODEL_CLASS"
    TOOL_REQUIREMENT = "TOOL_REQUIREMENT"
    SANDBOX_REQUIREMENT = "SANDBOX_REQUIREMENT"
    MEMORY_REQUIREMENT = "MEMORY_REQUIREMENT"
    DATA_ACCESS_REQUIREMENT = "DATA_ACCESS_REQUIREMENT"
    NETWORK_REQUIREMENT = "NETWORK_REQUIREMENT"
    CPU_ESTIMATE = "CPU_ESTIMATE"
    GPU_ESTIMATE = "GPU_ESTIMATE"
    IO_ESTIMATE = "IO_ESTIMATE"
    OPERATOR_ATTENTION = "OPERATOR_ATTENTION"
    TRACE_REQUIREMENT = "TRACE_REQUIREMENT"
    PROOF_REQUIREMENT = "PROOF_REQUIREMENT"


class EstimateConfidence(str, Enum):
    """Closed-world estimate confidence. No MEASURED/PROVEN/VERIFIED member.

    An estimate can never claim measured or proven status: measurement
    belongs to P4 execution and proof belongs to P5 AurelTrace.
    """

    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class ResourceRequirementEstimate(_CanonicalMixin):
    """One predicted requirement on one dimension. Estimate, not allocation."""

    estimate_id: str
    contract_version: str
    run_id: str
    atomic_unit_id: str
    dimension: ResourceDimension
    estimated_magnitude: str
    confidence: EstimateConfidence
    truth_label: FlowTruthLabel
    unavailable_reason: str = RESOURCE_ALLOCATION_UNAVAILABLE_REASON
    resource_allocated: bool = False
    resource_reserved: bool = False
    measured_usage: bool = False
    permission_granted: bool = False

    def __post_init__(self) -> None:
        _forbid_true(
            self,
            "resource_allocated",
            "resource_reserved",
            "measured_usage",
            "permission_granted",
        )


def create_resource_requirement_estimate(
    *,
    unit: WorkflowAtomicUnit,
    dimension: ResourceDimension,
    estimated_magnitude: str,
    confidence: EstimateConfidence = EstimateConfidence.UNKNOWN,
) -> ResourceRequirementEstimate:
    payload = {
        "contract_version": RESOURCE_REQUIREMENT_ESTIMATE_VERSION,
        "run_id": unit.run_id,
        "atomic_unit_id": unit.atomic_unit_id,
        "dimension": dimension.value,
        "estimated_magnitude": estimated_magnitude,
        "confidence": confidence.value,
    }
    return ResourceRequirementEstimate(
        estimate_id="flrre-" + stable_hash(payload)[:16],
        contract_version=RESOURCE_REQUIREMENT_ESTIMATE_VERSION,
        run_id=unit.run_id,
        atomic_unit_id=unit.atomic_unit_id,
        dimension=dimension,
        estimated_magnitude=estimated_magnitude,
        confidence=confidence,
        truth_label=FlowTruthLabel.LOCAL_RUNTIME_SUBSTRATE,
    )


@dataclass(frozen=True)
class ResourcePressureSignal(_CanonicalMixin):
    """Predicted pressure on one dimension. A signal, not a measurement."""

    signal_id: str
    contract_version: str
    run_id: str
    atomic_unit_id: str
    dimension: ResourceDimension
    pressure_detected: bool
    detail: str
    truth_label: FlowTruthLabel
    unavailable_reason: str = RESOURCE_ALLOCATION_UNAVAILABLE_REASON
    measured_usage: bool = False
    resource_allocated: bool = False

    def __post_init__(self) -> None:
        _forbid_true(self, "measured_usage", "resource_allocated")


def create_resource_pressure_signal(
    *,
    unit: WorkflowAtomicUnit,
    dimension: ResourceDimension,
    pressure_detected: bool,
    detail: str,
) -> ResourcePressureSignal:
    payload = {
        "contract_version": RESOURCE_PRESSURE_SIGNAL_VERSION,
        "run_id": unit.run_id,
        "atomic_unit_id": unit.atomic_unit_id,
        "dimension": dimension.value,
        "pressure_detected": pressure_detected,
        "detail": detail,
    }
    return ResourcePressureSignal(
        signal_id="flrps-" + stable_hash(payload)[:16],
        contract_version=RESOURCE_PRESSURE_SIGNAL_VERSION,
        run_id=unit.run_id,
        atomic_unit_id=unit.atomic_unit_id,
        dimension=dimension,
        pressure_detected=pressure_detected,
        detail=detail,
        truth_label=FlowTruthLabel.LOCAL_RUNTIME_SUBSTRATE,
    )


@dataclass(frozen=True)
class ResourceAvailabilityBoundary(_CanonicalMixin):
    """The resource law as fail-closed data. Availability is not permission."""

    boundary_id: str
    contract_version: str
    truth_label: FlowTruthLabel
    unavailable_reason: str = RESOURCE_ALLOCATION_UNAVAILABLE_REASON
    prediction_is_not_allocation: bool = True
    estimate_is_not_measured_usage: bool = True
    availability_is_not_permission: bool = True
    resource_allocated: bool = False
    resource_reserved: bool = False
    measured_usage: bool = False
    permission_granted: bool = False
    execution_available: bool = False

    def __post_init__(self) -> None:
        _forbid_false(
            self,
            "prediction_is_not_allocation",
            "estimate_is_not_measured_usage",
            "availability_is_not_permission",
        )
        _forbid_true(
            self,
            "resource_allocated",
            "resource_reserved",
            "measured_usage",
            "permission_granted",
            "execution_available",
        )


def build_resource_availability_boundary() -> ResourceAvailabilityBoundary:
    payload = {"contract_version": RESOURCE_AVAILABILITY_BOUNDARY_VERSION}
    return ResourceAvailabilityBoundary(
        boundary_id="flrab-" + stable_hash(payload)[:16],
        contract_version=RESOURCE_AVAILABILITY_BOUNDARY_VERSION,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
    )


@dataclass(frozen=True)
class ResourcePredictionFrame(_CanonicalMixin):
    """Everything predicted about one unit's resources. Never allocation."""

    resource_prediction_id: str
    contract_version: str
    run_id: str
    atomic_unit_id: str
    resource_dimensions: tuple[ResourceDimension, ...]
    estimated_requirements: tuple[ResourceRequirementEstimate, ...]
    pressure_signals: tuple[ResourcePressureSignal, ...]
    resource_available: bool
    resource_pressure_detected: bool
    boundary: ResourceAvailabilityBoundary
    truth_label: FlowTruthLabel
    unavailable_reason: str = RESOURCE_ALLOCATION_UNAVAILABLE_REASON
    resource_allocated: bool = False
    resource_reserved: bool = False
    measured_usage: bool = False
    permission_granted: bool = False
    execution_available: bool = False

    def __post_init__(self) -> None:
        _forbid_true(
            self,
            "resource_allocated",
            "resource_reserved",
            "measured_usage",
            "permission_granted",
            "execution_available",
        )


def build_resource_prediction_frame(
    *,
    unit: WorkflowAtomicUnit,
    estimated_requirements: tuple[ResourceRequirementEstimate, ...],
    pressure_signals: tuple[ResourcePressureSignal, ...] = (),
    resource_available: bool = True,
) -> ResourcePredictionFrame:
    for source_name, entries in (
        ("estimated_requirements", estimated_requirements),
        ("pressure_signals", pressure_signals),
    ):
        for entry in entries:
            if entry.atomic_unit_id != unit.atomic_unit_id:
                raise AurelFlowValidationError(
                    f"{source_name} entry covers unit "
                    f"{entry.atomic_unit_id!r}, not {unit.atomic_unit_id!r}",
                    code=AurelFlowErrorCode.RUN_MISMATCH,
                    field=source_name,
                )
    dimensions = tuple(
        sorted(
            {estimate.dimension for estimate in estimated_requirements}
            | {signal.dimension for signal in pressure_signals},
            key=lambda dimension: dimension.value,
        )
    )
    payload = {
        "contract_version": RESOURCE_PREDICTION_FRAME_VERSION,
        "atomic_unit_id": unit.atomic_unit_id,
        "estimate_ids": tuple(
            sorted(e.estimate_id for e in estimated_requirements)
        ),
        "signal_ids": tuple(sorted(s.signal_id for s in pressure_signals)),
        "resource_available": resource_available,
    }
    return ResourcePredictionFrame(
        resource_prediction_id="flrpf-" + stable_hash(payload)[:16],
        contract_version=RESOURCE_PREDICTION_FRAME_VERSION,
        run_id=unit.run_id,
        atomic_unit_id=unit.atomic_unit_id,
        resource_dimensions=dimensions,
        estimated_requirements=estimated_requirements,
        pressure_signals=pressure_signals,
        resource_available=resource_available,
        resource_pressure_detected=any(
            signal.pressure_detected for signal in pressure_signals
        ),
        boundary=build_resource_availability_boundary(),
        truth_label=FlowTruthLabel.LOCAL_RUNTIME_SUBSTRATE,
    )


@dataclass(frozen=True)
class ResourcePredictionReadModel(_CanonicalMixin):
    """Deterministic read model over one run's resource prediction frames."""

    read_model_id: str
    contract_version: str
    run_id: str
    frame_count: int
    dimension_counts: tuple[tuple[str, int], ...]
    resource_prediction_ids: tuple[str, ...]
    pressure_detected_count: int
    truth_label: FlowTruthLabel
    unavailable_reason: str = RESOURCE_ALLOCATION_UNAVAILABLE_REASON
    resource_allocated: bool = False
    resource_reserved: bool = False
    measured_usage: bool = False
    execution_available: bool = False

    def __post_init__(self) -> None:
        _forbid_true(
            self,
            "resource_allocated",
            "resource_reserved",
            "measured_usage",
            "execution_available",
        )


def build_resource_prediction_read_model(
    *, run_id: str, frames: tuple[ResourcePredictionFrame, ...]
) -> ResourcePredictionReadModel:
    for frame in frames:
        if frame.run_id != run_id:
            raise AurelFlowValidationError(
                f"frame {frame.resource_prediction_id!r} belongs to run "
                f"{frame.run_id!r}, not {run_id!r}",
                code=AurelFlowErrorCode.RUN_MISMATCH,
                field="frames",
            )
    dimension_counts: dict[str, int] = {}
    for frame in frames:
        for dimension in frame.resource_dimensions:
            dimension_counts[dimension.value] = (
                dimension_counts.get(dimension.value, 0) + 1
            )
    frame_ids = tuple(sorted(frame.resource_prediction_id for frame in frames))
    payload = {
        "contract_version": RESOURCE_PREDICTION_READ_MODEL_VERSION,
        "run_id": run_id,
        "resource_prediction_ids": frame_ids,
    }
    return ResourcePredictionReadModel(
        read_model_id="flrpm-" + stable_hash(payload)[:16],
        contract_version=RESOURCE_PREDICTION_READ_MODEL_VERSION,
        run_id=run_id,
        frame_count=len(frames),
        dimension_counts=tuple(sorted(dimension_counts.items())),
        resource_prediction_ids=frame_ids,
        pressure_detected_count=sum(
            1 for frame in frames if frame.resource_pressure_detected
        ),
        truth_label=FlowTruthLabel.READ_MODEL_ONLY,
    )


@dataclass(frozen=True)
class _AdvisoryEstimateBase(_CanonicalMixin):
    """Shared advisory-estimate boundary. Estimate is not billing or proof."""

    estimate_id: str
    contract_version: str
    run_id: str
    atomic_unit_id: str
    estimate_confidence: EstimateConfidence
    exceeds_budget: bool
    requires_operator_review: bool
    truth_label: FlowTruthLabel
    unavailable_reason: str = RESOURCE_ALLOCATION_UNAVAILABLE_REASON
    billing_performed: bool = False
    tokens_consumed: bool = False
    measured_usage: bool = False
    proof_available: bool = False

    def __post_init__(self) -> None:
        _forbid_true(
            self,
            "billing_performed",
            "tokens_consumed",
            "measured_usage",
            "proof_available",
        )
        if self.exceeds_budget and not self.requires_operator_review:
            raise AurelFlowValidationError(
                "an estimate that exceeds budget must require operator review",
                code=AurelFlowErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                field="requires_operator_review",
            )


@dataclass(frozen=True)
class CostEstimate(_AdvisoryEstimateBase):
    """Advisory cost estimate. No cost is billed."""

    estimated_cost_micro_usd: int | None = None


@dataclass(frozen=True)
class LatencyEstimate(_AdvisoryEstimateBase):
    """Advisory latency estimate in logical steps, never wall clock."""

    estimated_latency_steps: int | None = None


@dataclass(frozen=True)
class TokenBudgetEstimate(_AdvisoryEstimateBase):
    """Advisory token estimate. No token is consumed."""

    estimated_input_tokens: int | None = None
    estimated_output_tokens: int | None = None


@dataclass(frozen=True)
class ContextWindowEstimate(_AdvisoryEstimateBase):
    """Advisory context-window pressure estimate. Nothing is measured."""

    estimated_context_window_tokens: int | None = None
    context_pressure_detected: bool = False


def _estimate_payload(
    version: str,
    unit: WorkflowAtomicUnit,
    confidence: EstimateConfidence,
    exceeds_budget: bool,
    extra: dict[str, object],
) -> dict[str, object]:
    payload: dict[str, object] = {
        "contract_version": version,
        "run_id": unit.run_id,
        "atomic_unit_id": unit.atomic_unit_id,
        "confidence": confidence.value,
        "exceeds_budget": exceeds_budget,
    }
    payload.update(extra)
    return payload


def create_cost_estimate(
    *,
    unit: WorkflowAtomicUnit,
    estimated_cost_micro_usd: int | None = None,
    estimate_confidence: EstimateConfidence = EstimateConfidence.UNKNOWN,
    exceeds_budget: bool = False,
) -> CostEstimate:
    payload = _estimate_payload(
        COST_ESTIMATE_VERSION,
        unit,
        estimate_confidence,
        exceeds_budget,
        {"estimated_cost_micro_usd": estimated_cost_micro_usd},
    )
    return CostEstimate(
        estimate_id="flcst-" + stable_hash(payload)[:16],
        contract_version=COST_ESTIMATE_VERSION,
        run_id=unit.run_id,
        atomic_unit_id=unit.atomic_unit_id,
        estimate_confidence=estimate_confidence,
        exceeds_budget=exceeds_budget,
        requires_operator_review=exceeds_budget,
        truth_label=FlowTruthLabel.LOCAL_RUNTIME_SUBSTRATE,
        estimated_cost_micro_usd=estimated_cost_micro_usd,
    )


def create_latency_estimate(
    *,
    unit: WorkflowAtomicUnit,
    estimated_latency_steps: int | None = None,
    estimate_confidence: EstimateConfidence = EstimateConfidence.UNKNOWN,
    exceeds_budget: bool = False,
) -> LatencyEstimate:
    payload = _estimate_payload(
        LATENCY_ESTIMATE_VERSION,
        unit,
        estimate_confidence,
        exceeds_budget,
        {"estimated_latency_steps": estimated_latency_steps},
    )
    return LatencyEstimate(
        estimate_id="fllat-" + stable_hash(payload)[:16],
        contract_version=LATENCY_ESTIMATE_VERSION,
        run_id=unit.run_id,
        atomic_unit_id=unit.atomic_unit_id,
        estimate_confidence=estimate_confidence,
        exceeds_budget=exceeds_budget,
        requires_operator_review=exceeds_budget,
        truth_label=FlowTruthLabel.LOCAL_RUNTIME_SUBSTRATE,
        estimated_latency_steps=estimated_latency_steps,
    )


def create_token_budget_estimate(
    *,
    unit: WorkflowAtomicUnit,
    estimated_input_tokens: int | None = None,
    estimated_output_tokens: int | None = None,
    estimate_confidence: EstimateConfidence = EstimateConfidence.UNKNOWN,
    exceeds_budget: bool = False,
) -> TokenBudgetEstimate:
    payload = _estimate_payload(
        TOKEN_BUDGET_ESTIMATE_VERSION,
        unit,
        estimate_confidence,
        exceeds_budget,
        {
            "estimated_input_tokens": estimated_input_tokens,
            "estimated_output_tokens": estimated_output_tokens,
        },
    )
    return TokenBudgetEstimate(
        estimate_id="fltok-" + stable_hash(payload)[:16],
        contract_version=TOKEN_BUDGET_ESTIMATE_VERSION,
        run_id=unit.run_id,
        atomic_unit_id=unit.atomic_unit_id,
        estimate_confidence=estimate_confidence,
        exceeds_budget=exceeds_budget,
        requires_operator_review=exceeds_budget,
        truth_label=FlowTruthLabel.LOCAL_RUNTIME_SUBSTRATE,
        estimated_input_tokens=estimated_input_tokens,
        estimated_output_tokens=estimated_output_tokens,
    )


def create_context_window_estimate(
    *,
    unit: WorkflowAtomicUnit,
    estimated_context_window_tokens: int | None = None,
    context_pressure_detected: bool = False,
    estimate_confidence: EstimateConfidence = EstimateConfidence.UNKNOWN,
    exceeds_budget: bool = False,
) -> ContextWindowEstimate:
    payload = _estimate_payload(
        CONTEXT_WINDOW_ESTIMATE_VERSION,
        unit,
        estimate_confidence,
        exceeds_budget,
        {
            "estimated_context_window_tokens": estimated_context_window_tokens,
            "context_pressure_detected": context_pressure_detected,
        },
    )
    return ContextWindowEstimate(
        estimate_id="flctx-" + stable_hash(payload)[:16],
        contract_version=CONTEXT_WINDOW_ESTIMATE_VERSION,
        run_id=unit.run_id,
        atomic_unit_id=unit.atomic_unit_id,
        estimate_confidence=estimate_confidence,
        exceeds_budget=exceeds_budget,
        requires_operator_review=exceeds_budget,
        truth_label=FlowTruthLabel.LOCAL_RUNTIME_SUBSTRATE,
        estimated_context_window_tokens=estimated_context_window_tokens,
        context_pressure_detected=context_pressure_detected,
    )


@dataclass(frozen=True)
class SchedulingEstimateReadModel(_CanonicalMixin):
    """Deterministic read model over one unit's advisory estimates."""

    read_model_id: str
    contract_version: str
    run_id: str
    atomic_unit_id: str
    cost_estimate: CostEstimate | None
    latency_estimate: LatencyEstimate | None
    token_budget_estimate: TokenBudgetEstimate | None
    context_window_estimate: ContextWindowEstimate | None
    any_exceeds_budget: bool
    requires_operator_review: bool
    truth_label: FlowTruthLabel
    unavailable_reason: str = RESOURCE_ALLOCATION_UNAVAILABLE_REASON
    billing_performed: bool = False
    tokens_consumed: bool = False
    measured_usage: bool = False
    proof_available: bool = False

    def __post_init__(self) -> None:
        _forbid_true(
            self,
            "billing_performed",
            "tokens_consumed",
            "measured_usage",
            "proof_available",
        )


def build_scheduling_estimate_read_model(
    *,
    unit: WorkflowAtomicUnit,
    cost_estimate: CostEstimate | None = None,
    latency_estimate: LatencyEstimate | None = None,
    token_budget_estimate: TokenBudgetEstimate | None = None,
    context_window_estimate: ContextWindowEstimate | None = None,
) -> SchedulingEstimateReadModel:
    estimates = tuple(
        estimate
        for estimate in (
            cost_estimate,
            latency_estimate,
            token_budget_estimate,
            context_window_estimate,
        )
        if estimate is not None
    )
    for estimate in estimates:
        if estimate.atomic_unit_id != unit.atomic_unit_id:
            raise AurelFlowValidationError(
                f"estimate {estimate.estimate_id!r} covers unit "
                f"{estimate.atomic_unit_id!r}, not {unit.atomic_unit_id!r}",
                code=AurelFlowErrorCode.RUN_MISMATCH,
                field="estimates",
            )
    any_exceeds = any(estimate.exceeds_budget for estimate in estimates)
    payload = {
        "contract_version": SCHEDULING_ESTIMATE_READ_MODEL_VERSION,
        "atomic_unit_id": unit.atomic_unit_id,
        "estimate_ids": tuple(sorted(e.estimate_id for e in estimates)),
    }
    return SchedulingEstimateReadModel(
        read_model_id="flsem-" + stable_hash(payload)[:16],
        contract_version=SCHEDULING_ESTIMATE_READ_MODEL_VERSION,
        run_id=unit.run_id,
        atomic_unit_id=unit.atomic_unit_id,
        cost_estimate=cost_estimate,
        latency_estimate=latency_estimate,
        token_budget_estimate=token_budget_estimate,
        context_window_estimate=context_window_estimate,
        any_exceeds_budget=any_exceeds,
        requires_operator_review=any_exceeds
        or any(estimate.requires_operator_review for estimate in estimates),
        truth_label=FlowTruthLabel.READ_MODEL_ONLY,
    )


@dataclass(frozen=True)
class ModelRequirementFrame(_CanonicalMixin):
    """A future model requirement. A model requirement is not an LLM call."""

    requirement_id: str
    contract_version: str
    run_id: str
    atomic_unit_id: str
    model_required: bool
    truth_label: FlowTruthLabel
    model_class: str = ""
    unavailable_reason: str = REQUIREMENT_INVOCATION_UNAVAILABLE_REASON
    requires_p4_execution: bool = True
    requires_p9_authority: bool = True
    model_invoked: bool = False
    tokens_consumed: bool = False

    def __post_init__(self) -> None:
        _forbid_false(self, "requires_p4_execution", "requires_p9_authority")
        _forbid_true(self, "model_invoked", "tokens_consumed")


@dataclass(frozen=True)
class ToolRequirementFrame(_CanonicalMixin):
    """A future tool requirement. A tool requirement is not a tool call."""

    requirement_id: str
    contract_version: str
    run_id: str
    atomic_unit_id: str
    tool_required: bool
    truth_label: FlowTruthLabel
    tool_names: tuple[str, ...] = ()
    unavailable_reason: str = REQUIREMENT_INVOCATION_UNAVAILABLE_REASON
    requires_p4_execution: bool = True
    requires_p9_authority: bool = True
    tool_invoked: bool = False

    def __post_init__(self) -> None:
        _forbid_false(self, "requires_p4_execution", "requires_p9_authority")
        _forbid_true(self, "tool_invoked")


@dataclass(frozen=True)
class SandboxRequirementFrame(_CanonicalMixin):
    """A future sandbox requirement. Not a sandbox execution."""

    requirement_id: str
    contract_version: str
    run_id: str
    atomic_unit_id: str
    sandbox_required: bool
    truth_label: FlowTruthLabel
    sandbox_profile: str = ""
    unavailable_reason: str = REQUIREMENT_INVOCATION_UNAVAILABLE_REASON
    requires_p4_execution: bool = True
    requires_p9_authority: bool = True
    sandbox_executed: bool = False
    subprocess_spawned: bool = False

    def __post_init__(self) -> None:
        _forbid_false(self, "requires_p4_execution", "requires_p9_authority")
        _forbid_true(self, "sandbox_executed", "subprocess_spawned")


@dataclass(frozen=True)
class DataAccessRequirementFrame(_CanonicalMixin):
    """A future data/network/memory access requirement. Not an access."""

    requirement_id: str
    contract_version: str
    run_id: str
    atomic_unit_id: str
    data_access_required: bool
    network_required: bool
    memory_required: bool
    truth_label: FlowTruthLabel
    unavailable_reason: str = REQUIREMENT_INVOCATION_UNAVAILABLE_REASON
    requires_p4_execution: bool = True
    requires_p9_authority: bool = True
    data_access_performed: bool = False
    network_called: bool = False
    memory_access_performed: bool = False

    def __post_init__(self) -> None:
        _forbid_false(self, "requires_p4_execution", "requires_p9_authority")
        _forbid_true(
            self,
            "data_access_performed",
            "network_called",
            "memory_access_performed",
        )


def create_model_requirement_frame(
    *, unit: WorkflowAtomicUnit, model_required: bool, model_class: str = ""
) -> ModelRequirementFrame:
    payload = {
        "contract_version": MODEL_REQUIREMENT_FRAME_VERSION,
        "atomic_unit_id": unit.atomic_unit_id,
        "model_required": model_required,
        "model_class": model_class,
    }
    return ModelRequirementFrame(
        requirement_id="flmrq-" + stable_hash(payload)[:16],
        contract_version=MODEL_REQUIREMENT_FRAME_VERSION,
        run_id=unit.run_id,
        atomic_unit_id=unit.atomic_unit_id,
        model_required=model_required,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
        model_class=model_class,
    )


def create_tool_requirement_frame(
    *,
    unit: WorkflowAtomicUnit,
    tool_required: bool,
    tool_names: tuple[str, ...] = (),
) -> ToolRequirementFrame:
    payload = {
        "contract_version": TOOL_REQUIREMENT_FRAME_VERSION,
        "atomic_unit_id": unit.atomic_unit_id,
        "tool_required": tool_required,
        "tool_names": tuple(sorted(tool_names)),
    }
    return ToolRequirementFrame(
        requirement_id="fltrq-" + stable_hash(payload)[:16],
        contract_version=TOOL_REQUIREMENT_FRAME_VERSION,
        run_id=unit.run_id,
        atomic_unit_id=unit.atomic_unit_id,
        tool_required=tool_required,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
        tool_names=tuple(sorted(tool_names)),
    )


def create_sandbox_requirement_frame(
    *,
    unit: WorkflowAtomicUnit,
    sandbox_required: bool,
    sandbox_profile: str = "",
) -> SandboxRequirementFrame:
    payload = {
        "contract_version": SANDBOX_REQUIREMENT_FRAME_VERSION,
        "atomic_unit_id": unit.atomic_unit_id,
        "sandbox_required": sandbox_required,
        "sandbox_profile": sandbox_profile,
    }
    return SandboxRequirementFrame(
        requirement_id="flsrq-" + stable_hash(payload)[:16],
        contract_version=SANDBOX_REQUIREMENT_FRAME_VERSION,
        run_id=unit.run_id,
        atomic_unit_id=unit.atomic_unit_id,
        sandbox_required=sandbox_required,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
        sandbox_profile=sandbox_profile,
    )


def create_data_access_requirement_frame(
    *,
    unit: WorkflowAtomicUnit,
    data_access_required: bool,
    network_required: bool = False,
    memory_required: bool = False,
) -> DataAccessRequirementFrame:
    payload = {
        "contract_version": DATA_ACCESS_REQUIREMENT_FRAME_VERSION,
        "atomic_unit_id": unit.atomic_unit_id,
        "data_access_required": data_access_required,
        "network_required": network_required,
        "memory_required": memory_required,
    }
    return DataAccessRequirementFrame(
        requirement_id="fldrq-" + stable_hash(payload)[:16],
        contract_version=DATA_ACCESS_REQUIREMENT_FRAME_VERSION,
        run_id=unit.run_id,
        atomic_unit_id=unit.atomic_unit_id,
        data_access_required=data_access_required,
        network_required=network_required,
        memory_required=memory_required,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
    )


@dataclass(frozen=True)
class ExecutionResourceRequirementReadModel(_CanonicalMixin):
    """Deterministic read model over one unit's requirement frames."""

    read_model_id: str
    contract_version: str
    run_id: str
    atomic_unit_id: str
    model_requirement: ModelRequirementFrame | None
    tool_requirement: ToolRequirementFrame | None
    sandbox_requirement: SandboxRequirementFrame | None
    data_access_requirement: DataAccessRequirementFrame | None
    any_requirement_present: bool
    truth_label: FlowTruthLabel
    unavailable_reason: str = REQUIREMENT_INVOCATION_UNAVAILABLE_REASON
    requires_p4_execution: bool = True
    requires_p9_authority: bool = True
    model_invoked: bool = False
    tool_invoked: bool = False
    sandbox_executed: bool = False
    network_called: bool = False
    data_access_performed: bool = False
    memory_access_performed: bool = False

    def __post_init__(self) -> None:
        _forbid_false(self, "requires_p4_execution", "requires_p9_authority")
        _forbid_true(
            self,
            "model_invoked",
            "tool_invoked",
            "sandbox_executed",
            "network_called",
            "data_access_performed",
            "memory_access_performed",
        )


def build_execution_resource_requirement_read_model(
    *,
    unit: WorkflowAtomicUnit,
    model_requirement: ModelRequirementFrame | None = None,
    tool_requirement: ToolRequirementFrame | None = None,
    sandbox_requirement: SandboxRequirementFrame | None = None,
    data_access_requirement: DataAccessRequirementFrame | None = None,
) -> ExecutionResourceRequirementReadModel:
    frames: tuple[
        ModelRequirementFrame
        | ToolRequirementFrame
        | SandboxRequirementFrame
        | DataAccessRequirementFrame,
        ...,
    ] = tuple(
        frame
        for frame in (
            model_requirement,
            tool_requirement,
            sandbox_requirement,
            data_access_requirement,
        )
        if frame is not None
    )
    for frame in frames:
        if frame.atomic_unit_id != unit.atomic_unit_id:
            raise AurelFlowValidationError(
                f"requirement {frame.requirement_id!r} covers unit "
                f"{frame.atomic_unit_id!r}, not {unit.atomic_unit_id!r}",
                code=AurelFlowErrorCode.RUN_MISMATCH,
                field="requirements",
            )
    any_present = (
        (model_requirement is not None and model_requirement.model_required)
        or (tool_requirement is not None and tool_requirement.tool_required)
        or (
            sandbox_requirement is not None
            and sandbox_requirement.sandbox_required
        )
        or (
            data_access_requirement is not None
            and (
                data_access_requirement.data_access_required
                or data_access_requirement.network_required
                or data_access_requirement.memory_required
            )
        )
    )
    payload = {
        "contract_version": EXECUTION_RESOURCE_REQUIREMENT_READ_MODEL_VERSION,
        "atomic_unit_id": unit.atomic_unit_id,
        "requirement_ids": tuple(sorted(f.requirement_id for f in frames)),
    }
    return ExecutionResourceRequirementReadModel(
        read_model_id="flerm-" + stable_hash(payload)[:16],
        contract_version=EXECUTION_RESOURCE_REQUIREMENT_READ_MODEL_VERSION,
        run_id=unit.run_id,
        atomic_unit_id=unit.atomic_unit_id,
        model_requirement=model_requirement,
        tool_requirement=tool_requirement,
        sandbox_requirement=sandbox_requirement,
        data_access_requirement=data_access_requirement,
        any_requirement_present=any_present,
        truth_label=FlowTruthLabel.READ_MODEL_ONLY,
    )
