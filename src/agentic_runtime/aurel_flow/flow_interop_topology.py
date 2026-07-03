"""P3-FLOW-J interop layer refs / topology health / scheduling bridge / P4 handoff (P3.18).

Interoperability layer refs are logical names only: a discovery ref performs
no discovery, a routing ref routes nothing, an execution layer ref executes
nothing, a security layer ref is not Custos enforcement, and an observability
ref emits no telemetry. Topology health is diagnostic readiness, never proof
or live monitoring. The scheduling-topology bridge maps P3-FLOW-I requirement
frames to candidate service refs and routing candidates only, and the P4
handoff frame says what AurelExec may later consume — it is not P4.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .errors import AurelFlowErrorCode, AurelFlowValidationError
from .flow_compound_topology import (
    CompoundRuntimeTopology,
    LogicalServiceRef,
    RuntimeServiceKind,
    create_logical_service_ref,
)
from .flow_resource_prediction import ExecutionResourceRequirementReadModel
from .flow_scheduling_intent import AutonomySchedulingGate
from .flow_service_topology import (
    ServiceCapabilityEnvelope,
    ServiceDependencyGraph,
    ServiceRoutingCandidate,
    ServiceRoutingReason,
    create_service_routing_candidate,
)
from .types import FlowTruthLabel, _CanonicalMixin, stable_hash

INTEROPERABILITY_LAYER_REF_VERSION = "interoperability_layer_ref.v1"
TOPOLOGY_HEALTH_FRAME_VERSION = "topology_health_frame.v1"
FAILURE_CONTAINMENT_BOUNDARY_VERSION = "failure_containment_boundary.v1"
SCHEDULING_TOPOLOGY_BRIDGE_VERSION = "scheduling_topology_bridge.v1"
P4_HANDOFF_CLARITY_FRAME_VERSION = "p4_handoff_clarity_frame.v1"

INTEROP_UNAVAILABLE_REASON = (
    "no interoperability runtime exists in P3: layer refs are logical names "
    "only — no discovery, routing, execution, security enforcement, or "
    "telemetry happens before P4/P5/P9"
)
TOPOLOGY_HEALTH_UNAVAILABLE_REASON = (
    "topology health is diagnostic readiness over declared contracts only: "
    "no live service is probed, no telemetry is collected, nothing is "
    "recovered, and nothing is proven — proof belongs to P5 AurelTrace"
)
P4_HANDOFF_UNAVAILABLE_REASON = (
    "the P4 handoff frame names what AurelExec may later consume; P4 is not "
    "implemented, runtime.submit is not wired, and every invocation, "
    "transport, and network system remains deliberately absent"
)

# Systems deliberately absent in P3-FLOW-J, named for the P4 handoff.
ABSENT_RUNTIME_SYSTEMS: tuple[str, ...] = (
    "service_runtime",
    "service_discovery",
    "endpoint_registry",
    "network_transport",
    "message_bus",
    "service_mesh",
    "protocol_client_server",
    "worker_pool",
    "load_balancer",
    "health_probe_runner",
    "telemetry_exporter",
    "persistence",
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


class InteropLayerKind(str, Enum):
    """Closed-world interoperability layer vocabulary. Refs, not protocols."""

    DISCOVERY_LAYER_REF = "DISCOVERY_LAYER_REF"
    ROUTING_LAYER_REF = "ROUTING_LAYER_REF"
    EXECUTION_LAYER_REF = "EXECUTION_LAYER_REF"
    SECURITY_LAYER_REF = "SECURITY_LAYER_REF"
    OBSERVABILITY_LAYER_REF = "OBSERVABILITY_LAYER_REF"
    PROJECTION_LAYER_REF = "PROJECTION_LAYER_REF"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"


@dataclass(frozen=True)
class InteroperabilityLayerRef(_CanonicalMixin):
    """A logical MAS-style layer name. Not a live protocol."""

    layer_ref_id: str
    contract_version: str
    layer_kind: InteropLayerKind
    future_owner: str
    truth_label: FlowTruthLabel
    unavailable_reason: str = INTEROP_UNAVAILABLE_REASON
    discovery_performed: bool = False
    routing_performed: bool = False
    execution_performed: bool = False
    security_enforced: bool = False
    observability_active: bool = False
    transport_bound: bool = False
    network_called: bool = False

    def __post_init__(self) -> None:
        _forbid_true(
            self,
            "discovery_performed",
            "routing_performed",
            "execution_performed",
            "security_enforced",
            "observability_active",
            "transport_bound",
            "network_called",
        )


_LAYER_FUTURE_OWNERS: dict[InteropLayerKind, str] = {
    InteropLayerKind.DISCOVERY_LAYER_REF: "P4 AurelExec",
    InteropLayerKind.ROUTING_LAYER_REF: "P4 AurelExec",
    InteropLayerKind.EXECUTION_LAYER_REF: "P4 AurelExec",
    InteropLayerKind.SECURITY_LAYER_REF: "P9 Custos",
    InteropLayerKind.OBSERVABILITY_LAYER_REF: "P5 AurelTrace",
    InteropLayerKind.PROJECTION_LAYER_REF: "future AurelShell/React",
    InteropLayerKind.UNAVAILABLE: "unavailable",
    InteropLayerKind.ERROR: "error",
}


def create_interoperability_layer_ref(
    layer_kind: InteropLayerKind,
) -> InteroperabilityLayerRef:
    payload = {
        "contract_version": INTEROPERABILITY_LAYER_REF_VERSION,
        "layer_kind": layer_kind.value,
    }
    return InteroperabilityLayerRef(
        layer_ref_id="flilr-" + stable_hash(payload)[:16],
        contract_version=INTEROPERABILITY_LAYER_REF_VERSION,
        layer_kind=layer_kind,
        future_owner=_LAYER_FUTURE_OWNERS[layer_kind],
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
    )


class TopologyHealthSignalKind(str, Enum):
    """Closed-world topology readiness risks. Diagnostic, never proof."""

    SERVICE_UNAVAILABLE_CANDIDATE = "SERVICE_UNAVAILABLE_CANDIDATE"
    SERVICE_CAPABILITY_MISSING = "SERVICE_CAPABILITY_MISSING"
    SERVICE_DEPENDENCY_UNSATISFIED = "SERVICE_DEPENDENCY_UNSATISFIED"
    TOPOLOGY_CYCLE_RISK = "TOPOLOGY_CYCLE_RISK"
    TOPOLOGY_OVERCOUPLING_RISK = "TOPOLOGY_OVERCOUPLING_RISK"
    CASCADE_AMPLIFICATION_RISK = "CASCADE_AMPLIFICATION_RISK"
    CORRELATED_SERVICE_FAILURE_RISK = "CORRELATED_SERVICE_FAILURE_RISK"
    UNKNOWN_SERVICE_BOUNDARY = "UNKNOWN_SERVICE_BOUNDARY"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"


@dataclass(frozen=True)
class TopologyHealthFrame(_CanonicalMixin):
    """Declared-contract readiness diagnosis. No live probe, no proof."""

    health_frame_id: str
    contract_version: str
    run_id: str
    topology_id: str
    signal_kinds: tuple[TopologyHealthSignalKind, ...]
    signal_details: tuple[str, ...]
    topology_ready_candidate: bool
    truth_label: FlowTruthLabel
    unavailable_reason: str = TOPOLOGY_HEALTH_UNAVAILABLE_REASON
    diagnostic_only: bool = True
    proof_available: bool = False
    trace_verified: bool = False
    recovery_executed: bool = False
    service_health_checked: bool = False
    telemetry_active: bool = False

    def __post_init__(self) -> None:
        _forbid_false(self, "diagnostic_only")
        _forbid_true(
            self,
            "proof_available",
            "trace_verified",
            "recovery_executed",
            "service_health_checked",
            "telemetry_active",
        )
        if len(self.signal_kinds) != len(self.signal_details):
            raise AurelFlowValidationError(
                "every health signal needs a detail string",
                code=AurelFlowErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                field="signal_details",
            )


def assess_topology_health(
    *,
    topology: CompoundRuntimeTopology,
    dependency_graph: ServiceDependencyGraph | None = None,
    capability_envelopes: tuple[ServiceCapabilityEnvelope, ...] = (),
    routing_candidates: tuple[ServiceRoutingCandidate, ...] = (),
) -> TopologyHealthFrame:
    """Deterministic readiness diagnosis over declared contracts only.

    Derives cycle risk from the dependency graph, capability-missing from
    routing candidates whose target ref has no capability envelope, and an
    empty-topology unavailability candidate. Nothing is probed or measured.
    """

    signals: list[tuple[TopologyHealthSignalKind, str]] = []
    if not topology.service_nodes:
        signals.append(
            (
                TopologyHealthSignalKind.SERVICE_UNAVAILABLE_CANDIDATE,
                "the topology maps no service nodes",
            )
        )
    if dependency_graph is not None:
        if dependency_graph.topology_id != topology.topology_id:
            raise AurelFlowValidationError(
                "the dependency graph belongs to a different topology",
                code=AurelFlowErrorCode.RUN_MISMATCH,
                field="dependency_graph",
            )
        if dependency_graph.cycle_detected:
            signals.append(
                (
                    TopologyHealthSignalKind.TOPOLOGY_CYCLE_RISK,
                    "the declared dependency edges contain a cycle",
                )
            )
    covered_ref_ids = {
        envelope.service_ref_id for envelope in capability_envelopes
    }
    for candidate in sorted(
        routing_candidates, key=lambda c: c.routing_candidate_id
    ):
        if not topology.contains_ref(candidate.service_ref_id):
            signals.append(
                (
                    TopologyHealthSignalKind.UNKNOWN_SERVICE_BOUNDARY,
                    f"routing candidate {candidate.routing_candidate_id} "
                    "targets a service ref outside the topology",
                )
            )
        elif candidate.service_ref_id not in covered_ref_ids:
            signals.append(
                (
                    TopologyHealthSignalKind.SERVICE_CAPABILITY_MISSING,
                    f"routing candidate {candidate.routing_candidate_id} "
                    "targets a ref with no declared capability envelope",
                )
            )
    payload = {
        "contract_version": TOPOLOGY_HEALTH_FRAME_VERSION,
        "topology_id": topology.topology_id,
        "signals": tuple(kind.value for kind, _detail in signals),
        "routing_candidate_ids": tuple(
            sorted(c.routing_candidate_id for c in routing_candidates)
        ),
    }
    return TopologyHealthFrame(
        health_frame_id="flthf-" + stable_hash(payload)[:16],
        contract_version=TOPOLOGY_HEALTH_FRAME_VERSION,
        run_id=topology.run_id,
        topology_id=topology.topology_id,
        signal_kinds=tuple(kind for kind, _detail in signals),
        signal_details=tuple(detail for _kind, detail in signals),
        topology_ready_candidate=not signals,
        truth_label=FlowTruthLabel.READ_MODEL_ONLY,
    )


@dataclass(frozen=True)
class FailureContainmentBoundary(_CanonicalMixin):
    """Which refs a failure should stay inside. Containment is not executed."""

    containment_boundary_id: str
    contract_version: str
    run_id: str
    contained_service_ref_ids: tuple[str, ...]
    containment_rationale: str
    truth_label: FlowTruthLabel
    unavailable_reason: str = TOPOLOGY_HEALTH_UNAVAILABLE_REASON
    diagnostic_only: bool = True
    recovery_executed: bool = False
    service_invoked: bool = False
    execution_available: bool = False

    def __post_init__(self) -> None:
        _forbid_false(self, "diagnostic_only")
        _forbid_true(
            self,
            "recovery_executed",
            "service_invoked",
            "execution_available",
        )
        if not self.contained_service_ref_ids:
            raise AurelFlowValidationError(
                "a containment boundary must name at least one service ref",
                code=AurelFlowErrorCode.EMPTY_NODE_SET,
                field="contained_service_ref_ids",
            )


def create_failure_containment_boundary(
    *,
    run_id: str,
    contained_service_ref_ids: tuple[str, ...],
    containment_rationale: str,
) -> FailureContainmentBoundary:
    payload = {
        "contract_version": FAILURE_CONTAINMENT_BOUNDARY_VERSION,
        "run_id": run_id,
        "contained_service_ref_ids": tuple(sorted(contained_service_ref_ids)),
        "containment_rationale": containment_rationale,
    }
    return FailureContainmentBoundary(
        containment_boundary_id="flfcb-" + stable_hash(payload)[:16],
        contract_version=FAILURE_CONTAINMENT_BOUNDARY_VERSION,
        run_id=run_id,
        contained_service_ref_ids=tuple(sorted(contained_service_ref_ids)),
        containment_rationale=containment_rationale,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
    )


@dataclass(frozen=True)
class SchedulingTopologyBridge(_CanonicalMixin):
    """P3-FLOW-I requirements mapped to service refs and routing candidates.

    The bridge matches, it never dispatches: a requirement match is not an
    invocation and a service match is not routing.
    """

    bridge_id: str
    contract_version: str
    run_id: str
    atomic_unit_id: str
    matched_service_refs: tuple[LogicalServiceRef, ...]
    routing_candidates: tuple[ServiceRoutingCandidate, ...]
    requires_p4_execution: bool
    requires_p5_proof: bool
    requires_p9_authority: bool
    truth_label: FlowTruthLabel
    unavailable_reason: str = P4_HANDOFF_UNAVAILABLE_REASON
    dispatch_available: bool = False
    service_invoked: bool = False
    execution_available: bool = False

    def __post_init__(self) -> None:
        _forbid_false(self, "requires_p4_execution")
        _forbid_true(
            self,
            "dispatch_available",
            "service_invoked",
            "execution_available",
        )


def bridge_scheduling_requirements(
    *,
    requirements: ExecutionResourceRequirementReadModel,
    scheduling_gate: AutonomySchedulingGate | None = None,
) -> SchedulingTopologyBridge:
    """Deterministic map: I requirement frames -> service refs + routing candidates.

    Consumes the P3-FLOW-I ExecutionResourceRequirementReadModel as-is
    (repo-truth API, no duplicate I structures). The optional autonomy
    scheduling gate adds operator-review / authority routing candidates and
    can only tighten the outcome, never loosen it.
    """

    if (
        scheduling_gate is not None
        and scheduling_gate.atomic_unit_id != requirements.atomic_unit_id
    ):
        raise AurelFlowValidationError(
            "the scheduling gate covers a different atomic unit than the "
            "requirement read model",
            code=AurelFlowErrorCode.RUN_MISMATCH,
            field="scheduling_gate",
        )
    matches: list[tuple[RuntimeServiceKind, ServiceRoutingReason, str]] = []
    model_req = requirements.model_requirement
    if model_req is not None and model_req.model_required:
        matches.append(
            (
                RuntimeServiceKind.MODEL_SERVICE,
                ServiceRoutingReason.MODEL_REQUIREMENT_MATCH,
                model_req.model_class or "model",
            )
        )
    tool_req = requirements.tool_requirement
    if tool_req is not None and tool_req.tool_required:
        matches.append(
            (
                RuntimeServiceKind.TOOL_SERVICE,
                ServiceRoutingReason.TOOL_REQUIREMENT_MATCH,
                "/".join(tool_req.tool_names) or "tool",
            )
        )
    sandbox_req = requirements.sandbox_requirement
    if sandbox_req is not None and sandbox_req.sandbox_required:
        matches.append(
            (
                RuntimeServiceKind.SANDBOX_SERVICE,
                ServiceRoutingReason.SANDBOX_REQUIREMENT_MATCH,
                sandbox_req.sandbox_profile or "sandbox",
            )
        )
    data_req = requirements.data_access_requirement
    if data_req is not None:
        if data_req.data_access_required or data_req.network_required:
            matches.append(
                (
                    RuntimeServiceKind.DATA_SERVICE,
                    ServiceRoutingReason.DATA_REQUIREMENT_MATCH,
                    "data",
                )
            )
        if data_req.memory_required:
            matches.append(
                (
                    RuntimeServiceKind.MEMORY_SERVICE,
                    ServiceRoutingReason.MEMORY_REQUIREMENT_MATCH,
                    "memory",
                )
            )
    matched_refs: list[LogicalServiceRef] = []
    routing_candidates: list[ServiceRoutingCandidate] = []
    for service_kind, routing_reason, logical_name in matches:
        service_ref = create_logical_service_ref(
            service_kind=service_kind, logical_name=logical_name
        )
        matched_refs.append(service_ref)
        routing_candidates.append(
            create_service_routing_candidate(
                run_id=requirements.run_id,
                atomic_unit_id=requirements.atomic_unit_id,
                service_ref=service_ref,
                routing_reason=routing_reason,
            )
        )
    requires_p9 = any(ref.future_p9_required for ref in matched_refs)
    requires_p5 = any(ref.future_p5_required for ref in matched_refs)
    if scheduling_gate is not None:
        review_ref = create_logical_service_ref(
            service_kind=RuntimeServiceKind.OPERATOR_REVIEW_SERVICE,
            logical_name="operator-review",
        )
        if scheduling_gate.requires_operator_review:
            matched_refs.append(review_ref)
            routing_candidates.append(
                create_service_routing_candidate(
                    run_id=requirements.run_id,
                    atomic_unit_id=requirements.atomic_unit_id,
                    service_ref=review_ref,
                    routing_reason=ServiceRoutingReason.OPERATOR_REVIEW_REQUIRED,
                )
            )
        requires_p9 = requires_p9 or scheduling_gate.requires_p9_authority
        requires_p5 = requires_p5 or scheduling_gate.requires_p5_proof
    payload = {
        "contract_version": SCHEDULING_TOPOLOGY_BRIDGE_VERSION,
        "run_id": requirements.run_id,
        "atomic_unit_id": requirements.atomic_unit_id,
        "requirement_read_model_id": requirements.read_model_id,
        "scheduling_gate_id": scheduling_gate.scheduling_gate_id
        if scheduling_gate
        else "",
    }
    return SchedulingTopologyBridge(
        bridge_id="flstb-" + stable_hash(payload)[:16],
        contract_version=SCHEDULING_TOPOLOGY_BRIDGE_VERSION,
        run_id=requirements.run_id,
        atomic_unit_id=requirements.atomic_unit_id,
        matched_service_refs=tuple(matched_refs),
        routing_candidates=tuple(routing_candidates),
        requires_p4_execution=True,
        requires_p5_proof=requires_p5,
        requires_p9_authority=requires_p9,
        truth_label=FlowTruthLabel.LOCAL_RUNTIME_SUBSTRATE,
    )


@dataclass(frozen=True)
class P4HandoffClarityFrame(_CanonicalMixin):
    """What AurelExec may later consume, and what is deliberately absent.

    Bridge for later: SchedulingTopologyBridge -> future P4 service dispatch
    requirement -> future ExecutionRequestEnvelope / runtime.submit boundary.
    This frame is not P4 and wires nothing.
    """

    handoff_frame_id: str
    contract_version: str
    run_id: str
    consumable_service_ref_ids: tuple[str, ...]
    convertible_routing_candidate_ids: tuple[str, ...]
    candidate_only_capability_envelope_ids: tuple[str, ...]
    source_requirement_read_model_ids: tuple[str, ...]
    absent_runtime_systems: tuple[str, ...]
    future_p5_proof_required: bool
    future_p9_authority_required: bool
    truth_label: FlowTruthLabel
    unavailable_reason: str = P4_HANDOFF_UNAVAILABLE_REASON
    p4_implemented: bool = False
    runtime_submit_wired: bool = False
    dispatch_available: bool = False
    service_invoked: bool = False
    execution_available: bool = False
    invocation_available: bool = False

    def __post_init__(self) -> None:
        _forbid_true(
            self,
            "p4_implemented",
            "runtime_submit_wired",
            "dispatch_available",
            "service_invoked",
            "execution_available",
            "invocation_available",
        )
        if self.absent_runtime_systems != ABSENT_RUNTIME_SYSTEMS:
            raise AurelFlowValidationError(
                "the handoff frame must name the full deliberately-absent "
                "runtime system list",
                code=AurelFlowErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                field="absent_runtime_systems",
            )


def build_p4_handoff_clarity_frame(
    *,
    bridge: SchedulingTopologyBridge,
    capability_envelopes: tuple[ServiceCapabilityEnvelope, ...] = (),
    source_requirement_read_model_ids: tuple[str, ...] = (),
) -> P4HandoffClarityFrame:
    payload = {
        "contract_version": P4_HANDOFF_CLARITY_FRAME_VERSION,
        "bridge_id": bridge.bridge_id,
        "capability_envelope_ids": tuple(
            sorted(e.capability_envelope_id for e in capability_envelopes)
        ),
        "source_requirement_read_model_ids": tuple(
            sorted(source_requirement_read_model_ids)
        ),
    }
    return P4HandoffClarityFrame(
        handoff_frame_id="flp4h-" + stable_hash(payload)[:16],
        contract_version=P4_HANDOFF_CLARITY_FRAME_VERSION,
        run_id=bridge.run_id,
        consumable_service_ref_ids=tuple(
            sorted(ref.service_ref_id for ref in bridge.matched_service_refs)
        ),
        convertible_routing_candidate_ids=tuple(
            sorted(
                candidate.routing_candidate_id
                for candidate in bridge.routing_candidates
            )
        ),
        candidate_only_capability_envelope_ids=tuple(
            sorted(e.capability_envelope_id for e in capability_envelopes)
        ),
        source_requirement_read_model_ids=tuple(
            sorted(source_requirement_read_model_ids)
        ),
        absent_runtime_systems=ABSENT_RUNTIME_SYSTEMS,
        future_p5_proof_required=bridge.requires_p5_proof,
        future_p9_authority_required=bridge.requires_p9_authority,
        truth_label=FlowTruthLabel.READ_MODEL_ONLY,
    )
