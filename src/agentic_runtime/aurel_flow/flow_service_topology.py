"""P3-FLOW-J service capabilities / dependency graph / routing candidates (P3.18).

A capability envelope is candidate-only and grants no permission; a
dependency edge is not a transport route and sends no message; a routing
candidate names what P4 could later convert into a dispatch request and
performs no routing, no network call, and no invocation.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .errors import AurelFlowErrorCode, AurelFlowValidationError
from .flow_compound_topology import (
    SERVICE_RUNTIME_UNAVAILABLE_REASON,
    CompoundRuntimeTopology,
    LogicalServiceRef,
)
from .types import FlowTruthLabel, _CanonicalMixin, stable_hash

SERVICE_CAPABILITY_ENVELOPE_VERSION = "service_capability_envelope.v1"
SERVICE_DEPENDENCY_EDGE_VERSION = "service_dependency_edge.v1"
SERVICE_DEPENDENCY_GRAPH_VERSION = "service_dependency_graph.v1"
SERVICE_ROUTING_CANDIDATE_VERSION = "service_routing_candidate.v1"

ROUTING_UNAVAILABLE_REASON = (
    "no routing exists in P3: a routing candidate is a scheduling-to-service "
    "match only — no message is sent, no network is called, no service is "
    "invoked, and nothing is dispatched before P4 AurelExec under P9 Custos"
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


class ServiceCapabilityKind(str, Enum):
    """Closed-world candidate-only capability vocabulary."""

    CAN_GENERATE_TEXT_CANDIDATE = "CAN_GENERATE_TEXT_CANDIDATE"
    CAN_VERIFY_CANDIDATE = "CAN_VERIFY_CANDIDATE"
    CAN_RETRIEVE_MEMORY_CANDIDATE = "CAN_RETRIEVE_MEMORY_CANDIDATE"
    CAN_CALL_TOOL_CANDIDATE = "CAN_CALL_TOOL_CANDIDATE"
    CAN_EXECUTE_SANDBOX_CANDIDATE = "CAN_EXECUTE_SANDBOX_CANDIDATE"
    CAN_ACCESS_DATA_CANDIDATE = "CAN_ACCESS_DATA_CANDIDATE"
    CAN_ROUTE_MESSAGE_CANDIDATE = "CAN_ROUTE_MESSAGE_CANDIDATE"
    CAN_ACCEPT_OPERATOR_REVIEW_CANDIDATE = (
        "CAN_ACCEPT_OPERATOR_REVIEW_CANDIDATE"
    )
    CAN_PROJECT_READ_MODEL_CANDIDATE = "CAN_PROJECT_READ_MODEL_CANDIDATE"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"


# Capabilities whose future exercise would be an invocation/side effect.
INVOCATION_BOUND_CAPABILITY_KINDS: frozenset[ServiceCapabilityKind] = frozenset(
    {
        ServiceCapabilityKind.CAN_GENERATE_TEXT_CANDIDATE,
        ServiceCapabilityKind.CAN_VERIFY_CANDIDATE,
        ServiceCapabilityKind.CAN_RETRIEVE_MEMORY_CANDIDATE,
        ServiceCapabilityKind.CAN_CALL_TOOL_CANDIDATE,
        ServiceCapabilityKind.CAN_EXECUTE_SANDBOX_CANDIDATE,
        ServiceCapabilityKind.CAN_ACCESS_DATA_CANDIDATE,
        ServiceCapabilityKind.CAN_ROUTE_MESSAGE_CANDIDATE,
    }
)


@dataclass(frozen=True)
class ServiceCapabilityEnvelope(_CanonicalMixin):
    """What a service *could* do later. Candidate-only, never permission."""

    capability_envelope_id: str
    contract_version: str
    service_ref_id: str
    capability_kinds: tuple[ServiceCapabilityKind, ...]
    requires_p4_execution: bool
    requires_p9_authority: bool
    truth_label: FlowTruthLabel
    unavailable_reason: str = SERVICE_RUNTIME_UNAVAILABLE_REASON
    candidate_only: bool = True
    permission_granted: bool = False
    authority_granted: bool = False
    service_invoked: bool = False
    execution_available: bool = False

    def __post_init__(self) -> None:
        _forbid_false(self, "candidate_only")
        _forbid_true(
            self,
            "permission_granted",
            "authority_granted",
            "service_invoked",
            "execution_available",
        )
        if not self.capability_kinds:
            raise AurelFlowValidationError(
                "a capability envelope must name at least one capability",
                code=AurelFlowErrorCode.EMPTY_NODE_SET,
                field="capability_kinds",
            )
        invocation_bound = any(
            kind in INVOCATION_BOUND_CAPABILITY_KINDS
            for kind in self.capability_kinds
        )
        if invocation_bound and not (
            self.requires_p4_execution and self.requires_p9_authority
        ):
            raise AurelFlowValidationError(
                "an invocation-bound capability must stay future-bound to "
                "P4 execution and P9 authority",
                code=AurelFlowErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                field="requires_p4_execution",
            )


def create_service_capability_envelope(
    *,
    service_ref: LogicalServiceRef,
    capability_kinds: tuple[ServiceCapabilityKind, ...],
) -> ServiceCapabilityEnvelope:
    invocation_bound = any(
        kind in INVOCATION_BOUND_CAPABILITY_KINDS for kind in capability_kinds
    )
    payload = {
        "contract_version": SERVICE_CAPABILITY_ENVELOPE_VERSION,
        "service_ref_id": service_ref.service_ref_id,
        "capability_kinds": tuple(sorted(k.value for k in capability_kinds)),
    }
    return ServiceCapabilityEnvelope(
        capability_envelope_id="flcap-" + stable_hash(payload)[:16],
        contract_version=SERVICE_CAPABILITY_ENVELOPE_VERSION,
        service_ref_id=service_ref.service_ref_id,
        capability_kinds=tuple(
            sorted(capability_kinds, key=lambda kind: kind.value)
        ),
        requires_p4_execution=invocation_bound,
        requires_p9_authority=invocation_bound,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
    )


class ServiceDependencyKind(str, Enum):
    """Closed-world dependency vocabulary. A dependency is not a call."""

    REQUIRES_MODEL = "REQUIRES_MODEL"
    REQUIRES_AGENT = "REQUIRES_AGENT"
    REQUIRES_TOOL = "REQUIRES_TOOL"
    REQUIRES_MEMORY = "REQUIRES_MEMORY"
    REQUIRES_VERIFIER = "REQUIRES_VERIFIER"
    REQUIRES_ENVIRONMENT = "REQUIRES_ENVIRONMENT"
    REQUIRES_SANDBOX = "REQUIRES_SANDBOX"
    REQUIRES_DATA = "REQUIRES_DATA"
    REQUIRES_POLICY = "REQUIRES_POLICY"
    REQUIRES_TRACE = "REQUIRES_TRACE"
    REQUIRES_OPERATOR_REVIEW = "REQUIRES_OPERATOR_REVIEW"
    REQUIRES_SCHEDULER = "REQUIRES_SCHEDULER"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"


@dataclass(frozen=True)
class ServiceDependencyEdge(_CanonicalMixin):
    """from-service needs to-service later. Not a transport route."""

    dependency_edge_id: str
    contract_version: str
    from_service_ref_id: str
    to_service_ref_id: str
    dependency_kind: ServiceDependencyKind
    truth_label: FlowTruthLabel
    unavailable_reason: str = ROUTING_UNAVAILABLE_REASON
    transport_route: bool = False
    message_sent: bool = False
    service_invoked: bool = False
    execution_available: bool = False

    def __post_init__(self) -> None:
        _forbid_true(
            self,
            "transport_route",
            "message_sent",
            "service_invoked",
            "execution_available",
        )
        if self.from_service_ref_id == self.to_service_ref_id:
            raise AurelFlowValidationError(
                "a service cannot depend on itself",
                code=AurelFlowErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                field="to_service_ref_id",
            )


def create_service_dependency_edge(
    *,
    from_service_ref: LogicalServiceRef,
    to_service_ref: LogicalServiceRef,
    dependency_kind: ServiceDependencyKind,
) -> ServiceDependencyEdge:
    payload = {
        "contract_version": SERVICE_DEPENDENCY_EDGE_VERSION,
        "from_service_ref_id": from_service_ref.service_ref_id,
        "to_service_ref_id": to_service_ref.service_ref_id,
        "dependency_kind": dependency_kind.value,
    }
    return ServiceDependencyEdge(
        dependency_edge_id="flsde-" + stable_hash(payload)[:16],
        contract_version=SERVICE_DEPENDENCY_EDGE_VERSION,
        from_service_ref_id=from_service_ref.service_ref_id,
        to_service_ref_id=to_service_ref.service_ref_id,
        dependency_kind=dependency_kind,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
    )


@dataclass(frozen=True)
class ServiceDependencyGraph(_CanonicalMixin):
    """Deterministic dependency map over topology refs. Never call-graph execution."""

    dependency_graph_id: str
    contract_version: str
    run_id: str
    topology_id: str
    edges: tuple[ServiceDependencyEdge, ...]
    cycle_detected: bool
    truth_label: FlowTruthLabel
    unavailable_reason: str = ROUTING_UNAVAILABLE_REASON
    transport_route: bool = False
    message_sent: bool = False
    service_invoked: bool = False
    execution_available: bool = False

    def __post_init__(self) -> None:
        _forbid_true(
            self,
            "transport_route",
            "message_sent",
            "service_invoked",
            "execution_available",
        )


def _detect_dependency_cycle(edges: tuple[ServiceDependencyEdge, ...]) -> bool:
    adjacency: dict[str, list[str]] = {}
    for edge in edges:
        adjacency.setdefault(edge.from_service_ref_id, []).append(
            edge.to_service_ref_id
        )
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(ref_id: str) -> bool:
        if ref_id in visiting:
            return True
        if ref_id in visited:
            return False
        visiting.add(ref_id)
        for successor in adjacency.get(ref_id, ()):
            if visit(successor):
                return True
        visiting.discard(ref_id)
        visited.add(ref_id)
        return False

    return any(visit(ref_id) for ref_id in sorted(adjacency))


def build_service_dependency_graph(
    *,
    topology: CompoundRuntimeTopology,
    edges: tuple[ServiceDependencyEdge, ...],
) -> ServiceDependencyGraph:
    for edge in edges:
        for endpoint_ref_id in (
            edge.from_service_ref_id,
            edge.to_service_ref_id,
        ):
            if not topology.contains_ref(endpoint_ref_id):
                raise AurelFlowValidationError(
                    f"dependency edge endpoint {endpoint_ref_id!r} is not in "
                    f"topology {topology.topology_id!r}",
                    code=AurelFlowErrorCode.UNKNOWN_NODE_REF,
                    field="edges",
                )
    payload = {
        "contract_version": SERVICE_DEPENDENCY_GRAPH_VERSION,
        "topology_id": topology.topology_id,
        "edge_ids": tuple(sorted(edge.dependency_edge_id for edge in edges)),
    }
    return ServiceDependencyGraph(
        dependency_graph_id="flsdg-" + stable_hash(payload)[:16],
        contract_version=SERVICE_DEPENDENCY_GRAPH_VERSION,
        run_id=topology.run_id,
        topology_id=topology.topology_id,
        edges=edges,
        cycle_detected=_detect_dependency_cycle(edges),
        truth_label=FlowTruthLabel.READ_MODEL_ONLY,
    )


class ServiceRoutingReason(str, Enum):
    """Why a routing candidate names a service. A reason is not a route."""

    MODEL_REQUIREMENT_MATCH = "MODEL_REQUIREMENT_MATCH"
    TOOL_REQUIREMENT_MATCH = "TOOL_REQUIREMENT_MATCH"
    VERIFIER_REQUIREMENT_MATCH = "VERIFIER_REQUIREMENT_MATCH"
    MEMORY_REQUIREMENT_MATCH = "MEMORY_REQUIREMENT_MATCH"
    ENVIRONMENT_REQUIREMENT_MATCH = "ENVIRONMENT_REQUIREMENT_MATCH"
    DATA_REQUIREMENT_MATCH = "DATA_REQUIREMENT_MATCH"
    SANDBOX_REQUIREMENT_MATCH = "SANDBOX_REQUIREMENT_MATCH"
    FALLBACK_SERVICE_CANDIDATE = "FALLBACK_SERVICE_CANDIDATE"
    DEGRADED_SERVICE_CANDIDATE = "DEGRADED_SERVICE_CANDIDATE"
    OPERATOR_REVIEW_REQUIRED = "OPERATOR_REVIEW_REQUIRED"
    AUTHORITY_REQUIRED = "AUTHORITY_REQUIRED"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"


@dataclass(frozen=True)
class ServiceRoutingCandidate(_CanonicalMixin):
    """What P4 could later route where. No routing happens here."""

    routing_candidate_id: str
    contract_version: str
    run_id: str
    atomic_unit_id: str
    service_ref_id: str
    routing_reason: ServiceRoutingReason
    requires_p4_execution: bool
    requires_p9_authority: bool
    truth_label: FlowTruthLabel
    unavailable_reason: str = ROUTING_UNAVAILABLE_REASON
    routing_candidate_only: bool = True
    message_sent: bool = False
    network_called: bool = False
    service_invoked: bool = False
    dispatch_available: bool = False
    execution_available: bool = False

    def __post_init__(self) -> None:
        _forbid_false(self, "routing_candidate_only", "requires_p4_execution")
        _forbid_true(
            self,
            "message_sent",
            "network_called",
            "service_invoked",
            "dispatch_available",
            "execution_available",
        )


def create_service_routing_candidate(
    *,
    run_id: str,
    atomic_unit_id: str,
    service_ref: LogicalServiceRef,
    routing_reason: ServiceRoutingReason,
) -> ServiceRoutingCandidate:
    payload = {
        "contract_version": SERVICE_ROUTING_CANDIDATE_VERSION,
        "run_id": run_id,
        "atomic_unit_id": atomic_unit_id,
        "service_ref_id": service_ref.service_ref_id,
        "routing_reason": routing_reason.value,
    }
    return ServiceRoutingCandidate(
        routing_candidate_id="flsrc-" + stable_hash(payload)[:16],
        contract_version=SERVICE_ROUTING_CANDIDATE_VERSION,
        run_id=run_id,
        atomic_unit_id=atomic_unit_id,
        service_ref_id=service_ref.service_ref_id,
        routing_reason=routing_reason,
        requires_p4_execution=True,
        requires_p9_authority=service_ref.future_p9_required
        or routing_reason is ServiceRoutingReason.AUTHORITY_REQUIRED,
        truth_label=FlowTruthLabel.LOCAL_RUNTIME_SUBSTRATE,
    )
