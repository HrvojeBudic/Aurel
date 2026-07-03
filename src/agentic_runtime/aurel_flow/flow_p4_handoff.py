"""P3-FLOW-L P4 execution handoff / runtime.submit boundary map.

The P4 handoff package names what P4-EXEC-A may consume next; it is not P4,
it dispatches nothing, and it creates no executable request. An execution
request candidate is not an execution request. The runtime.submit boundary
map explains what P4 must build later and never wires or calls
runtime.submit.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .errors import AurelFlowErrorCode, AurelFlowValidationError
from .types import FlowTruthLabel, _CanonicalMixin, stable_hash

P4_HANDOFF_ITEM_VERSION = "p4_handoff_item.v1"
P4_EXECUTION_HANDOFF_PACKAGE_VERSION = "p4_execution_handoff_package.v1"
EXECUTION_REQUEST_CANDIDATE_SURFACE_VERSION = (
    "execution_request_candidate_surface.v1"
)
RUNTIME_SUBMIT_BOUNDARY_REQUIREMENT_VERSION = (
    "runtime_submit_boundary_requirement.v1"
)
RUNTIME_SUBMIT_BOUNDARY_MAP_VERSION = "runtime_submit_boundary_map.v1"

P4_HANDOFF_PACKAGE_UNAVAILABLE_REASON = (
    "the P4 handoff package names what P4-EXEC-A may consume; it is not "
    "P4, dispatches nothing, wires nothing, and creates no executable "
    "request"
)
RUNTIME_SUBMIT_BOUNDARY_UNAVAILABLE_REASON = (
    "runtime.submit remains not wired and never called in P3; the boundary "
    "map explains what P4 AurelExec must build later under P9 Custos "
    "authority and P5 Trace proof"
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


class P4HandoffSurface(str, Enum):
    """Closed-world content the P4 handoff package must cover."""

    READY_NODE_SURFACE = "READY_NODE_SURFACE"
    SCHEDULING_INTENT_SURFACE = "SCHEDULING_INTENT_SURFACE"
    DISPATCHABILITY_FRAME_SURFACE = "DISPATCHABILITY_FRAME_SURFACE"
    RESOURCE_PREDICTION_SURFACE = "RESOURCE_PREDICTION_SURFACE"
    QUEUE_CANDIDATE_SURFACE = "QUEUE_CANDIDATE_SURFACE"
    SERVICE_REF_SURFACE = "SERVICE_REF_SURFACE"
    ROUTING_CANDIDATE_SURFACE = "ROUTING_CANDIDATE_SURFACE"
    P4_HANDOFF_CLARITY_FRAME_SURFACE = "P4_HANDOFF_CLARITY_FRAME_SURFACE"
    RUNTIME_SUBMIT_BOUNDARY = "RUNTIME_SUBMIT_BOUNDARY"
    P5_PROOF_BOUNDARY = "P5_PROOF_BOUNDARY"
    P9_AUTHORITY_BOUNDARY = "P9_AUTHORITY_BOUNDARY"
    PERSISTENCE_UNAVAILABLE_BOUNDARY = "PERSISTENCE_UNAVAILABLE_BOUNDARY"
    FUTURE_BRIDGE_RECOMMENDATION = "FUTURE_BRIDGE_RECOMMENDATION"


_DEFAULT_HANDOFF_ROWS: dict[P4HandoffSurface, tuple[str, str]] = {
    P4HandoffSurface.READY_NODE_SURFACE: (
        "ready-queue calculation and scheduler decisions name ready nodes "
        "without executing them",
        "aurel_flow.scheduler / ReadyQueue, SchedulerDecision",
    ),
    P4HandoffSurface.SCHEDULING_INTENT_SURFACE: (
        "scheduling intents propose candidate work with no dispatch verb "
        "in the vocabulary",
        "aurel_flow.flow_scheduling_intent / SchedulingIntent",
    ),
    P4HandoffSurface.DISPATCHABILITY_FRAME_SURFACE: (
        "the total dispatchability classifier resolves a fully ready unit "
        "to READY_BUT_NO_P4 candidate-only",
        "aurel_flow.flow_dispatchability / DispatchabilityFrame",
    ),
    P4HandoffSurface.RESOURCE_PREDICTION_SURFACE: (
        "resource predictions and cost/latency/token estimates are "
        "advisory; nothing is allocated, reserved, or billed",
        "aurel_flow.flow_resource_prediction / ResourcePredictionFrame",
    ),
    P4HandoffSurface.QUEUE_CANDIDATE_SURFACE: (
        "queue placement candidates insert nothing and assign no worker",
        "aurel_flow.flow_dispatchability / QueuePlacementCandidate",
    ),
    P4HandoffSurface.SERVICE_REF_SURFACE: (
        "logical service refs name model/tool/sandbox/verifier services "
        "without endpoints or invocation",
        "aurel_flow.flow_compound_topology / LogicalServiceRef",
    ),
    P4HandoffSurface.ROUTING_CANDIDATE_SURFACE: (
        "service routing candidates route nothing; the P9 future is "
        "inherited from the ref",
        "aurel_flow.flow_service_topology / ServiceRoutingCandidate",
    ),
    P4HandoffSurface.P4_HANDOFF_CLARITY_FRAME_SURFACE: (
        "the J clarity frame names consumable refs, convertible candidates, "
        "and the full deliberately-absent system list",
        "aurel_flow.flow_interop_topology / P4HandoffClarityFrame",
    ),
    P4HandoffSurface.RUNTIME_SUBMIT_BOUNDARY: (
        "runtime.submit is mapped NOT_WIRED_FUTURE_P4 and never called",
        "aurel_flow.flow_p4_handoff / RuntimeSubmitBoundaryMap",
    ),
    P4HandoffSurface.P5_PROOF_BOUNDARY: (
        "no P3 output is proof; Trace verification belongs to P5 AurelTrace",
        "aurel_flow.flow_proof_expectation / ProofExpectationEnvelope",
    ),
    P4HandoffSurface.P9_AUTHORITY_BOUNDARY: (
        "no P3 object grants authority; enforcement belongs to P9 Custos",
        "aurel_flow.flow_boundary / PermissionRequestEnvelope",
    ),
    P4HandoffSurface.PERSISTENCE_UNAVAILABLE_BOUNDARY: (
        "all P3 state is in-memory; P4 must pick a persistence strategy "
        "before durable execution history exists",
        "aurel_flow.flow_p3_audit / UnavailableSystemsLedger",
    ),
    P4HandoffSurface.FUTURE_BRIDGE_RECOMMENDATION: (
        "P4-EXEC-A should start from a minimal runtime.submit boundary: "
        "consume dispatchability + queue candidates, require operator "
        "review, P9 authority, and P5 proof expectations per request",
        "P4-EXEC-A dispatch (future)",
    ),
}


@dataclass(frozen=True)
class P4HandoffItem(_CanonicalMixin):
    """One named handoff surface with a source pointer. Not execution."""

    item_id: str
    contract_version: str
    surface: P4HandoffSurface
    summary: str
    source_ref: str
    truth_label: FlowTruthLabel
    unavailable_reason: str = P4_HANDOFF_PACKAGE_UNAVAILABLE_REASON
    p4_implemented: bool = False
    execution_request_created: bool = False

    def __post_init__(self) -> None:
        _forbid_true(self, "p4_implemented", "execution_request_created")
        for field_name in ("summary", "source_ref"):
            if not getattr(self, field_name).strip():
                raise AurelFlowValidationError(
                    f"a handoff item must carry a non-empty {field_name}",
                    code=AurelFlowErrorCode.INVALID_SEAL_CHECK,
                    field=field_name,
                )


def create_p4_handoff_item(
    *,
    surface: P4HandoffSurface,
    summary: str,
    source_ref: str,
) -> P4HandoffItem:
    payload = {
        "contract_version": P4_HANDOFF_ITEM_VERSION,
        "surface": surface.value,
        "summary": summary,
        "source_ref": source_ref,
    }
    return P4HandoffItem(
        item_id="fllhi-" + stable_hash(payload)[:16],
        contract_version=P4_HANDOFF_ITEM_VERSION,
        surface=surface,
        summary=summary,
        source_ref=source_ref,
        truth_label=FlowTruthLabel.LOCAL_RUNTIME_SUBSTRATE,
    )


@dataclass(frozen=True)
class P4ExecutionHandoffPackage(_CanonicalMixin):
    """The non-executable P4 handoff. A handoff package is not P4."""

    package_id: str
    contract_version: str
    items: tuple[P4HandoffItem, ...]
    truth_label: FlowTruthLabel
    unavailable_reason: str = P4_HANDOFF_PACKAGE_UNAVAILABLE_REASON
    p4_implemented: bool = False
    execution_request_created: bool = False
    runtime_submit_wired: bool = False
    runtime_submit_called: bool = False
    dispatch_available: bool = False
    execution_available: bool = False
    worker_allocated: bool = False

    def __post_init__(self) -> None:
        _forbid_true(
            self,
            "p4_implemented",
            "execution_request_created",
            "runtime_submit_wired",
            "runtime_submit_called",
            "dispatch_available",
            "execution_available",
            "worker_allocated",
        )
        covered = {item.surface for item in self.items}
        if len(covered) != len(self.items):
            raise AurelFlowValidationError(
                "a handoff surface may appear only once in the package",
                code=AurelFlowErrorCode.INVALID_SEAL_CHECK,
                field="items",
            )
        absent = tuple(
            surface for surface in P4HandoffSurface if surface not in covered
        )
        if absent:
            raise AurelFlowValidationError(
                "the P4 handoff package must cover every surface; absent: "
                + ", ".join(surface.value for surface in absent),
                code=AurelFlowErrorCode.INVALID_SEAL_CHECK,
                field="items",
            )


def build_p4_execution_handoff_package(
    items: tuple[P4HandoffItem, ...] | None = None,
) -> P4ExecutionHandoffPackage:
    if items is None:
        items = tuple(
            create_p4_handoff_item(
                surface=surface,
                summary=summary,
                source_ref=source_ref,
            )
            for surface, (summary, source_ref) in (
                _DEFAULT_HANDOFF_ROWS.items()
            )
        )
    payload = {
        "contract_version": P4_EXECUTION_HANDOFF_PACKAGE_VERSION,
        "item_ids": tuple(sorted(item.item_id for item in items)),
    }
    return P4ExecutionHandoffPackage(
        package_id="fllhp-" + stable_hash(payload)[:16],
        contract_version=P4_EXECUTION_HANDOFF_PACKAGE_VERSION,
        items=tuple(items),
        truth_label=FlowTruthLabel.LOCAL_RUNTIME_SUBSTRATE,
    )


@dataclass(frozen=True)
class ExecutionRequestCandidateSurface(_CanonicalMixin):
    """Candidate-only future execution request shape for P4 design clarity.

    A candidate is not a request: nothing is created, submitted, queued,
    dispatched, or executed, and no dispatch path is wired.
    """

    candidate_id: str
    contract_version: str
    candidate_label: str
    source_intent_ref: str
    truth_label: FlowTruthLabel
    unavailable_reason: str = P4_HANDOFF_PACKAGE_UNAVAILABLE_REASON
    candidate_only: bool = True
    future_runtime_submit_required: bool = True
    requires_operator_review: bool = True
    requires_p5_proof: bool = True
    requires_p9_authority: bool = True
    execution_request_created: bool = False
    runtime_submit_wired: bool = False
    runtime_submit_called: bool = False
    dispatch_available: bool = False
    execution_available: bool = False
    p4_implemented: bool = False
    worker_allocated: bool = False

    def __post_init__(self) -> None:
        _forbid_false(
            self,
            "candidate_only",
            "future_runtime_submit_required",
            "requires_operator_review",
            "requires_p5_proof",
            "requires_p9_authority",
        )
        _forbid_true(
            self,
            "execution_request_created",
            "runtime_submit_wired",
            "runtime_submit_called",
            "dispatch_available",
            "execution_available",
            "p4_implemented",
            "worker_allocated",
        )
        if not self.candidate_label.strip():
            raise AurelFlowValidationError(
                "an execution request candidate must carry a non-empty "
                "candidate_label",
                code=AurelFlowErrorCode.INVALID_SEAL_CHECK,
                field="candidate_label",
            )


def describe_execution_request_candidate(
    *,
    candidate_label: str,
    source_intent_ref: str,
) -> ExecutionRequestCandidateSurface:
    payload = {
        "contract_version": EXECUTION_REQUEST_CANDIDATE_SURFACE_VERSION,
        "candidate_label": candidate_label,
        "source_intent_ref": source_intent_ref,
    }
    return ExecutionRequestCandidateSurface(
        candidate_id="fllec-" + stable_hash(payload)[:16],
        contract_version=EXECUTION_REQUEST_CANDIDATE_SURFACE_VERSION,
        candidate_label=candidate_label,
        source_intent_ref=source_intent_ref,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
    )


class RuntimeSubmitBoundaryStatus(str, Enum):
    """Closed-world runtime.submit posture. There is no WIRED member."""

    NOT_WIRED_FUTURE_P4 = "NOT_WIRED_FUTURE_P4"
    REQUIRES_AUREL_EXEC = "REQUIRES_AUREL_EXEC"
    REQUIRES_CUSTOS_AUTHORITY = "REQUIRES_CUSTOS_AUTHORITY"
    REQUIRES_TRACE_PROOF = "REQUIRES_TRACE_PROOF"
    REQUIRES_OPERATOR_REVIEW = "REQUIRES_OPERATOR_REVIEW"
    REQUIRES_PERSISTENCE_STRATEGY = "REQUIRES_PERSISTENCE_STRATEGY"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"


_REQUIRED_SUBMIT_REQUIREMENT_STATUSES: tuple[
    RuntimeSubmitBoundaryStatus, ...
] = (
    RuntimeSubmitBoundaryStatus.REQUIRES_AUREL_EXEC,
    RuntimeSubmitBoundaryStatus.REQUIRES_CUSTOS_AUTHORITY,
    RuntimeSubmitBoundaryStatus.REQUIRES_TRACE_PROOF,
    RuntimeSubmitBoundaryStatus.REQUIRES_OPERATOR_REVIEW,
    RuntimeSubmitBoundaryStatus.REQUIRES_PERSISTENCE_STRATEGY,
)

_ALLOWED_PRIMARY_SUBMIT_STATUSES: tuple[RuntimeSubmitBoundaryStatus, ...] = (
    RuntimeSubmitBoundaryStatus.NOT_WIRED_FUTURE_P4,
    RuntimeSubmitBoundaryStatus.UNAVAILABLE,
)

_DEFAULT_SUBMIT_REQUIREMENT_ROWS: dict[
    RuntimeSubmitBoundaryStatus, tuple[str, str]
] = {
    RuntimeSubmitBoundaryStatus.REQUIRES_AUREL_EXEC: (
        "P4 AurelExec must implement the minimal execution bridge before "
        "any request can be submitted",
        "P4-EXEC-A AurelExec",
    ),
    RuntimeSubmitBoundaryStatus.REQUIRES_CUSTOS_AUTHORITY: (
        "no submission may proceed without P9 Custos authorization",
        "P9 Custos",
    ),
    RuntimeSubmitBoundaryStatus.REQUIRES_TRACE_PROOF: (
        "every executed request must be provable on the P5 evidence spine",
        "P5 AurelTrace",
    ),
    RuntimeSubmitBoundaryStatus.REQUIRES_OPERATOR_REVIEW: (
        "operator review remains required at the submit boundary; the "
        "operator decides",
        "operator",
    ),
    RuntimeSubmitBoundaryStatus.REQUIRES_PERSISTENCE_STRATEGY: (
        "durable request/run history needs a persistence strategy that P3 "
        "deliberately does not have",
        "P4/P5/P6 persistence strategy",
    ),
}


@dataclass(frozen=True)
class RuntimeSubmitBoundaryRequirement(_CanonicalMixin):
    """One thing P4 must build before runtime.submit can exist."""

    requirement_id: str
    contract_version: str
    status: RuntimeSubmitBoundaryStatus
    detail: str
    future_owner: str
    truth_label: FlowTruthLabel
    unavailable_reason: str = RUNTIME_SUBMIT_BOUNDARY_UNAVAILABLE_REASON
    runtime_submit_wired: bool = False
    runtime_submit_called: bool = False

    def __post_init__(self) -> None:
        _forbid_true(self, "runtime_submit_wired", "runtime_submit_called")


@dataclass(frozen=True)
class RuntimeSubmitBoundaryMap(_CanonicalMixin):
    """runtime.submit as a future-bound boundary. A map is not wiring."""

    boundary_map_id: str
    contract_version: str
    primary_status: RuntimeSubmitBoundaryStatus
    requirements: tuple[RuntimeSubmitBoundaryRequirement, ...]
    truth_label: FlowTruthLabel
    unavailable_reason: str = RUNTIME_SUBMIT_BOUNDARY_UNAVAILABLE_REASON
    runtime_submit_wired: bool = False
    runtime_submit_called: bool = False
    p4_implemented: bool = False
    dispatch_available: bool = False
    execution_available: bool = False

    def __post_init__(self) -> None:
        _forbid_true(
            self,
            "runtime_submit_wired",
            "runtime_submit_called",
            "p4_implemented",
            "dispatch_available",
            "execution_available",
        )
        if self.primary_status not in _ALLOWED_PRIMARY_SUBMIT_STATUSES:
            raise AurelFlowValidationError(
                "the runtime.submit primary status must stay future-bound "
                "(NOT_WIRED_FUTURE_P4 or UNAVAILABLE), got "
                f"{self.primary_status.value}",
                code=AurelFlowErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                field="primary_status",
            )
        recorded = {requirement.status for requirement in self.requirements}
        absent = tuple(
            status
            for status in _REQUIRED_SUBMIT_REQUIREMENT_STATUSES
            if status not in recorded
        )
        if absent:
            raise AurelFlowValidationError(
                "the runtime.submit boundary map must name every future "
                "requirement; absent: "
                + ", ".join(status.value for status in absent),
                code=AurelFlowErrorCode.INVALID_SEAL_CHECK,
                field="requirements",
            )


def map_runtime_submit_boundary() -> RuntimeSubmitBoundaryMap:
    requirements: list[RuntimeSubmitBoundaryRequirement] = []
    for status in _REQUIRED_SUBMIT_REQUIREMENT_STATUSES:
        detail, future_owner = _DEFAULT_SUBMIT_REQUIREMENT_ROWS[status]
        requirement_payload = {
            "contract_version": RUNTIME_SUBMIT_BOUNDARY_REQUIREMENT_VERSION,
            "status": status.value,
        }
        requirements.append(
            RuntimeSubmitBoundaryRequirement(
                requirement_id="fllsr-" + stable_hash(requirement_payload)[:16],
                contract_version=(
                    RUNTIME_SUBMIT_BOUNDARY_REQUIREMENT_VERSION
                ),
                status=status,
                detail=detail,
                future_owner=future_owner,
                truth_label=FlowTruthLabel.CONTRACT_ONLY,
            )
        )
    payload = {
        "contract_version": RUNTIME_SUBMIT_BOUNDARY_MAP_VERSION,
        "requirement_ids": tuple(
            sorted(requirement.requirement_id for requirement in requirements)
        ),
    }
    return RuntimeSubmitBoundaryMap(
        boundary_map_id="fllsm-" + stable_hash(payload)[:16],
        contract_version=RUNTIME_SUBMIT_BOUNDARY_MAP_VERSION,
        primary_status=RuntimeSubmitBoundaryStatus.NOT_WIRED_FUTURE_P4,
        requirements=tuple(requirements),
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
    )
