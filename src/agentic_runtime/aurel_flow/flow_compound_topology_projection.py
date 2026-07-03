"""P3-FLOW-J compound topology projection (P3.18).

Read-only projection of the topology map, capabilities, dependencies, routing
candidates, health risks, scheduling-to-service mapping, and P4 handoff
clarity for a future React/AurelShell surface. A UI service map is not a live
service mesh, a UI route action is not dispatch, a UI service action is not
invocation, and the UI cannot control runtime topology.
"""

from __future__ import annotations

from dataclasses import dataclass

from .errors import AurelFlowErrorCode, AurelFlowValidationError
from .flow_compound_topology import CompoundRuntimeTopology
from .flow_interop_topology import (
    P4HandoffClarityFrame,
    SchedulingTopologyBridge,
    TopologyHealthFrame,
)
from .flow_service_topology import (
    ServiceDependencyGraph,
    ServiceRoutingCandidate,
)
from .types import FlowTruthLabel, _CanonicalMixin, stable_hash

COMPOUND_TOPOLOGY_PROJECTION_VERSION = "compound_topology_projection.v1"

TOPOLOGY_PROJECTION_UNAVAILABLE_REASON = (
    "no React component, frontend route, frontend state, API server, REST, "
    "or WebSocket exists in P3-FLOW-J; this projection is a read-only view "
    "contract — a UI service map is not a service mesh and no UI action can "
    "route, invoke, or control topology"
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


@dataclass(frozen=True)
class CompoundTopologyProjection(_CanonicalMixin):
    """Everything a future surface may render about the compound topology."""

    projection_id: str
    projection_version: str
    run_id: str
    service_kind_counts: tuple[tuple[str, int], ...]
    dependency_edge_count: int
    cycle_detected: bool
    routing_reason_values: tuple[str, ...]
    health_signal_values: tuple[str, ...]
    topology_ready_candidate: bool
    scheduling_matched_service_kind_values: tuple[str, ...]
    p4_consumable_ref_count: int
    absent_runtime_systems: tuple[str, ...]
    truth_label: FlowTruthLabel
    unavailable_reason: str = TOPOLOGY_PROJECTION_UNAVAILABLE_REASON
    react_projection_only: bool = True
    read_only: bool = True
    frontend_mutation_allowed: bool = False
    ui_route_action_allowed: bool = False
    ui_service_invocation_allowed: bool = False
    ui_service_mesh_control_allowed: bool = False
    api_server_implemented: bool = False
    frontend_implemented: bool = False

    def __post_init__(self) -> None:
        _forbid_false(self, "react_projection_only", "read_only")
        _forbid_true(
            self,
            "frontend_mutation_allowed",
            "ui_route_action_allowed",
            "ui_service_invocation_allowed",
            "ui_service_mesh_control_allowed",
            "api_server_implemented",
            "frontend_implemented",
        )


def build_compound_topology_projection(
    *,
    topology: CompoundRuntimeTopology,
    dependency_graph: ServiceDependencyGraph | None = None,
    routing_candidates: tuple[ServiceRoutingCandidate, ...] = (),
    health_frame: TopologyHealthFrame | None = None,
    bridge: SchedulingTopologyBridge | None = None,
    p4_handoff: P4HandoffClarityFrame | None = None,
) -> CompoundTopologyProjection:
    for source_name, source_run_id in (
        (
            "dependency_graph",
            dependency_graph.run_id if dependency_graph else None,
        ),
        ("health_frame", health_frame.run_id if health_frame else None),
        ("bridge", bridge.run_id if bridge else None),
        ("p4_handoff", p4_handoff.run_id if p4_handoff else None),
        *(
            ("routing_candidates", candidate.run_id)
            for candidate in routing_candidates
        ),
    ):
        if source_run_id is not None and source_run_id != topology.run_id:
            raise AurelFlowValidationError(
                f"{source_name} run {source_run_id!r} does not match "
                f"topology run {topology.run_id!r}",
                code=AurelFlowErrorCode.RUN_MISMATCH,
                field=source_name,
            )
    payload = {
        "projection_version": COMPOUND_TOPOLOGY_PROJECTION_VERSION,
        "topology_id": topology.topology_id,
        "dependency_graph_id": dependency_graph.dependency_graph_id
        if dependency_graph
        else "",
        "routing_candidate_ids": tuple(
            sorted(c.routing_candidate_id for c in routing_candidates)
        ),
        "health_frame_id": health_frame.health_frame_id if health_frame else "",
        "bridge_id": bridge.bridge_id if bridge else "",
        "handoff_frame_id": p4_handoff.handoff_frame_id if p4_handoff else "",
    }
    return CompoundTopologyProjection(
        projection_id="flctp-" + stable_hash(payload)[:16],
        projection_version=COMPOUND_TOPOLOGY_PROJECTION_VERSION,
        run_id=topology.run_id,
        service_kind_counts=topology.service_kind_counts,
        dependency_edge_count=len(dependency_graph.edges)
        if dependency_graph
        else 0,
        cycle_detected=dependency_graph.cycle_detected
        if dependency_graph
        else False,
        routing_reason_values=tuple(
            candidate.routing_reason.value for candidate in routing_candidates
        ),
        health_signal_values=tuple(
            kind.value for kind in health_frame.signal_kinds
        )
        if health_frame
        else (),
        topology_ready_candidate=health_frame.topology_ready_candidate
        if health_frame
        else False,
        scheduling_matched_service_kind_values=tuple(
            ref.service_kind.value for ref in bridge.matched_service_refs
        )
        if bridge
        else (),
        p4_consumable_ref_count=len(p4_handoff.consumable_service_ref_ids)
        if p4_handoff
        else 0,
        absent_runtime_systems=p4_handoff.absent_runtime_systems
        if p4_handoff
        else (),
        truth_label=FlowTruthLabel.READ_MODEL_ONLY,
    )
