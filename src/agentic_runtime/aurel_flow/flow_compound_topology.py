"""P3-FLOW-J compound runtime topology / service nodes / logical service refs (P3.18).

A compound topology is a topology map, not a service mesh: it names logical
model/agent/tool/memory/verifier/environment/sandbox/data services without
running, discovering, routing, or invoking anything. A service node is not a
live process, a service ref is not an endpoint or transport, and nothing here
opens a network. P4 dispatches and executes, P5 proves route/execution
alignment, P9 authorizes service invocation.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .errors import AurelFlowErrorCode, AurelFlowValidationError
from .types import FlowTruthLabel, _CanonicalMixin, stable_hash

AUREL_FLOW_J_PACK_ID = "P3-FLOW-J"
AUREL_FLOW_J_PACK_TITLE = (
    "Compound Runtime Topology / Model-Agent-Environment Services Pack"
)
AUREL_FLOW_J_REPORT_PATH = (
    "agent/reports/P3_FLOW_J_COMPOUND_RUNTIME_TOPOLOGY_PACK.md"
)

RUNTIME_SERVICE_NODE_VERSION = "runtime_service_node.v1"
LOGICAL_SERVICE_REF_VERSION = "logical_service_ref.v1"
COMPOUND_RUNTIME_TOPOLOGY_VERSION = "compound_runtime_topology.v1"

SERVICE_RUNTIME_UNAVAILABLE_REASON = (
    "no service runtime exists in P3: a compound topology is a map, a "
    "service node is not a live process, and a service ref is not an "
    "endpoint, handle, or transport — invocation belongs to P4 AurelExec "
    "under P9 Custos authority, proof to P5 AurelTrace"
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


class RuntimeServiceKind(str, Enum):
    """Closed-world service kinds. A kind is not execution permission."""

    MODEL_SERVICE = "MODEL_SERVICE"
    AGENT_SERVICE = "AGENT_SERVICE"
    TOOL_SERVICE = "TOOL_SERVICE"
    MEMORY_SERVICE = "MEMORY_SERVICE"
    VERIFIER_SERVICE = "VERIFIER_SERVICE"
    ENVIRONMENT_SERVICE = "ENVIRONMENT_SERVICE"
    SANDBOX_SERVICE = "SANDBOX_SERVICE"
    DATA_SERVICE = "DATA_SERVICE"
    POLICY_SERVICE_REF = "POLICY_SERVICE_REF"
    TRACE_SERVICE_REF = "TRACE_SERVICE_REF"
    OPERATOR_REVIEW_SERVICE = "OPERATOR_REVIEW_SERVICE"
    SCHEDULER_SERVICE_REF = "SCHEDULER_SERVICE_REF"
    PROJECTION_SERVICE = "PROJECTION_SERVICE"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"


# Kinds whose future use would be an invocation/side effect (P4 + P9 later).
INVOCATION_BOUND_SERVICE_KINDS: frozenset[RuntimeServiceKind] = frozenset(
    {
        RuntimeServiceKind.MODEL_SERVICE,
        RuntimeServiceKind.AGENT_SERVICE,
        RuntimeServiceKind.TOOL_SERVICE,
        RuntimeServiceKind.MEMORY_SERVICE,
        RuntimeServiceKind.VERIFIER_SERVICE,
        RuntimeServiceKind.ENVIRONMENT_SERVICE,
        RuntimeServiceKind.SANDBOX_SERVICE,
        RuntimeServiceKind.DATA_SERVICE,
    }
)


@dataclass(frozen=True)
class LogicalServiceRef(_CanonicalMixin):
    """A logical name for a future service. Never a live handle.

    One ref contract covers every service kind (model/agent/tool/memory/
    verifier/environment/sandbox/data/...): the closed-world kind carries the
    distinction, so the package does not grow eight near-identical classes.
    """

    service_ref_id: str
    contract_version: str
    service_kind: RuntimeServiceKind
    logical_name: str
    truth_label: FlowTruthLabel
    future_p4_required: bool
    future_p5_required: bool
    future_p9_required: bool
    unavailable_reason: str = SERVICE_RUNTIME_UNAVAILABLE_REASON
    live_handle: bool = False
    endpoint_available: bool = False
    transport_available: bool = False
    invocation_available: bool = False
    service_invoked: bool = False
    network_called: bool = False

    def __post_init__(self) -> None:
        _forbid_true(
            self,
            "live_handle",
            "endpoint_available",
            "transport_available",
            "invocation_available",
            "service_invoked",
            "network_called",
        )
        if not self.logical_name:
            raise AurelFlowValidationError(
                "a logical service ref must carry a logical name",
                code=AurelFlowErrorCode.EMPTY_NODE_ID,
                field="logical_name",
            )
        if (
            self.service_kind in INVOCATION_BOUND_SERVICE_KINDS
            and not (self.future_p4_required and self.future_p9_required)
        ):
            raise AurelFlowValidationError(
                "an invocation-bound service ref must stay future-bound to "
                "P4 execution and P9 authority",
                code=AurelFlowErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                field="future_p4_required",
            )


def create_logical_service_ref(
    *,
    service_kind: RuntimeServiceKind,
    logical_name: str,
) -> LogicalServiceRef:
    invocation_bound = service_kind in INVOCATION_BOUND_SERVICE_KINDS
    payload = {
        "contract_version": LOGICAL_SERVICE_REF_VERSION,
        "service_kind": service_kind.value,
        "logical_name": logical_name,
    }
    return LogicalServiceRef(
        service_ref_id="flsvr-" + stable_hash(payload)[:16],
        contract_version=LOGICAL_SERVICE_REF_VERSION,
        service_kind=service_kind,
        logical_name=logical_name,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
        future_p4_required=invocation_bound,
        future_p5_required=service_kind
        in (
            RuntimeServiceKind.VERIFIER_SERVICE,
            RuntimeServiceKind.TRACE_SERVICE_REF,
        ),
        future_p9_required=invocation_bound
        or service_kind is RuntimeServiceKind.POLICY_SERVICE_REF,
    )


@dataclass(frozen=True)
class RuntimeServiceNode(_CanonicalMixin):
    """One service-like node in the topology map. Not a live process."""

    service_node_id: str
    contract_version: str
    service_ref: LogicalServiceRef
    display_name: str
    truth_label: FlowTruthLabel
    unavailable_reason: str = SERVICE_RUNTIME_UNAVAILABLE_REASON
    live_process: bool = False
    live_endpoint: bool = False
    endpoint_available: bool = False
    transport_bound: bool = False
    service_invoked: bool = False
    execution_available: bool = False
    authority_granted: bool = False

    def __post_init__(self) -> None:
        _forbid_true(
            self,
            "live_process",
            "live_endpoint",
            "endpoint_available",
            "transport_bound",
            "service_invoked",
            "execution_available",
            "authority_granted",
        )


def create_runtime_service_node(
    *, service_ref: LogicalServiceRef, display_name: str = ""
) -> RuntimeServiceNode:
    payload = {
        "contract_version": RUNTIME_SERVICE_NODE_VERSION,
        "service_ref_id": service_ref.service_ref_id,
        "display_name": display_name,
    }
    return RuntimeServiceNode(
        service_node_id="flsvn-" + stable_hash(payload)[:16],
        contract_version=RUNTIME_SERVICE_NODE_VERSION,
        service_ref=service_ref,
        display_name=display_name or service_ref.logical_name,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
    )


@dataclass(frozen=True)
class CompoundRuntimeTopology(_CanonicalMixin):
    """The topology map: nodes only, no runtime, no mesh, no network."""

    topology_id: str
    contract_version: str
    run_id: str
    service_nodes: tuple[RuntimeServiceNode, ...]
    service_kind_counts: tuple[tuple[str, int], ...]
    truth_label: FlowTruthLabel
    unavailable_reason: str = SERVICE_RUNTIME_UNAVAILABLE_REASON
    service_runtime_available: bool = False
    service_discovery_performed: bool = False
    network_transport_available: bool = False
    dispatch_available: bool = False
    execution_available: bool = False

    def __post_init__(self) -> None:
        _forbid_true(
            self,
            "service_runtime_available",
            "service_discovery_performed",
            "network_transport_available",
            "dispatch_available",
            "execution_available",
        )
        ref_ids = [node.service_ref.service_ref_id for node in self.service_nodes]
        if len(ref_ids) != len(set(ref_ids)):
            raise AurelFlowValidationError(
                "a topology must not map the same service ref twice",
                code=AurelFlowErrorCode.DUPLICATE_NODE_ID,
                field="service_nodes",
            )

    def contains_ref(self, service_ref_id: str) -> bool:
        return any(
            node.service_ref.service_ref_id == service_ref_id
            for node in self.service_nodes
        )


def build_compound_runtime_topology(
    *, run_id: str, service_nodes: tuple[RuntimeServiceNode, ...]
) -> CompoundRuntimeTopology:
    kind_counts: dict[str, int] = {}
    for node in service_nodes:
        kind = node.service_ref.service_kind.value
        kind_counts[kind] = kind_counts.get(kind, 0) + 1
    payload = {
        "contract_version": COMPOUND_RUNTIME_TOPOLOGY_VERSION,
        "run_id": run_id,
        "service_node_ids": tuple(
            sorted(node.service_node_id for node in service_nodes)
        ),
    }
    return CompoundRuntimeTopology(
        topology_id="flcrt-" + stable_hash(payload)[:16],
        contract_version=COMPOUND_RUNTIME_TOPOLOGY_VERSION,
        run_id=run_id,
        service_nodes=service_nodes,
        service_kind_counts=tuple(sorted(kind_counts.items())),
        truth_label=FlowTruthLabel.READ_MODEL_ONLY,
    )
