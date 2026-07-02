"""P3-FLOW-C runtime behavior timeline and event relation graph.

Ordered, deterministic projections over the P3-FLOW-B runtime event stream.
The timeline is not AurelTrace: it is not hash-chain proof and can never be
TRACE_VERIFIED. The relation graph is a local runtime relation projection,
not P5 Trace and not Ledger.
"""

from __future__ import annotations

from dataclasses import dataclass

from .errors import AurelFlowErrorCode, AurelFlowValidationError
from .runtime_events import RuntimeEventStream
from .types import (
    TRACE_VERIFICATION_UNAVAILABLE_REASON,
    FlowTruthLabel,
    _CanonicalMixin,
    stable_hash,
)

RUNTIME_BEHAVIOR_TIMELINE_VERSION = "runtime_behavior_timeline.v1"
RUNTIME_EVENT_RELATION_GRAPH_VERSION = "runtime_event_relation_graph.v1"


@dataclass(frozen=True)
class RuntimeBehaviorTimelineEntry(_CanonicalMixin):
    """One ordered local behavior entry. Not a trace record."""

    entry_id: str
    sequence: int
    run_id: str
    node_id: str
    event_id: str
    event_kind: str
    severity: str
    source_actor: str
    summary: str
    state_before_ref: str
    state_after_ref: str
    truth_label: FlowTruthLabel
    execution_available: bool = False
    trace_verified: bool = False
    ledger_written: bool = False

    def __post_init__(self) -> None:
        for boundary_field in ("execution_available", "trace_verified", "ledger_written"):
            if getattr(self, boundary_field):
                raise AurelFlowValidationError(
                    f"RuntimeBehaviorTimelineEntry.{boundary_field} must remain False",
                    code=AurelFlowErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                    field=boundary_field,
                )


@dataclass(frozen=True)
class RuntimeBehaviorTimeline(_CanonicalMixin):
    """Ordered local behavior timeline for one run. Not AurelTrace."""

    timeline_version: str
    run_id: str
    stream_id: str
    entries: tuple[RuntimeBehaviorTimelineEntry, ...]
    entry_count: int
    truth_label: FlowTruthLabel
    trace_unavailable_reason: str
    timeline_hash: str
    is_hash_chain_proof: bool = False
    is_trace: bool = False
    trace_verified: bool = False

    def __post_init__(self) -> None:
        for boundary_field in ("is_hash_chain_proof", "is_trace", "trace_verified"):
            if getattr(self, boundary_field):
                raise AurelFlowValidationError(
                    f"RuntimeBehaviorTimeline.{boundary_field} must remain False",
                    code=AurelFlowErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                    field=boundary_field,
                )


def build_runtime_behavior_timeline(
    event_stream: RuntimeEventStream,
) -> RuntimeBehaviorTimeline:
    """Project the event stream into an ordered timeline. Pure: the stream is
    read as-is and never mutated; order is the stream's append order."""

    entries = []
    for event in event_stream.events:
        entry_payload = {
            "timeline_version": RUNTIME_BEHAVIOR_TIMELINE_VERSION,
            "event_id": event.event_id,
            "sequence": event.sequence,
        }
        entries.append(
            RuntimeBehaviorTimelineEntry(
                entry_id=stable_hash(entry_payload),
                sequence=event.sequence,
                run_id=event.target_run_id,
                node_id=event.target_node_id,
                event_id=event.event_id,
                event_kind=event.event_kind.value,
                severity=event.severity.value,
                source_actor=event.source.source_id,
                summary=f"{event.event_kind.value} @ seq {event.sequence}",
                state_before_ref=event.local_state_before_ref,
                state_after_ref=event.local_state_after_ref,
                truth_label=event.truth_label,
            )
        )
    ordered = tuple(sorted(entries, key=lambda entry: entry.sequence))
    timeline_payload = {
        "timeline_version": RUNTIME_BEHAVIOR_TIMELINE_VERSION,
        "stream_id": event_stream.stream_id,
        "entry_ids": tuple(entry.entry_id for entry in ordered),
    }
    return RuntimeBehaviorTimeline(
        timeline_version=RUNTIME_BEHAVIOR_TIMELINE_VERSION,
        run_id=event_stream.run_id,
        stream_id=event_stream.stream_id,
        entries=ordered,
        entry_count=len(ordered),
        truth_label=FlowTruthLabel.READ_MODEL_ONLY,
        trace_unavailable_reason=TRACE_VERIFICATION_UNAVAILABLE_REASON,
        timeline_hash=stable_hash(timeline_payload),
    )


@dataclass(frozen=True)
class RuntimeEventRelationGraphNode(_CanonicalMixin):
    """One event as a relation-graph node. Not a trace entry."""

    event_id: str
    sequence: int
    event_kind: str
    target_node_id: str
    correlation_id: str
    affected_node_ids: tuple[str, ...]
    affected_run_ids: tuple[str, ...]
    truth_label: FlowTruthLabel
    trace_verified: bool = False
    ledger_written: bool = False

    def __post_init__(self) -> None:
        for boundary_field in ("trace_verified", "ledger_written"):
            if getattr(self, boundary_field):
                raise AurelFlowValidationError(
                    f"RuntimeEventRelationGraphNode.{boundary_field} must remain False",
                    code=AurelFlowErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                    field=boundary_field,
                )


@dataclass(frozen=True)
class RuntimeEventRelationGraphEdge(_CanonicalMixin):
    """A directed relation between two local events."""

    edge_id: str
    from_event_id: str
    to_event_id: str
    relation_kind: str
    influence_strength_label: str
    truth_label: FlowTruthLabel


@dataclass(frozen=True)
class RuntimeEventRelationGraph(_CanonicalMixin):
    """Local runtime event relation graph. Not P5 Trace, not Ledger."""

    graph_version: str
    run_id: str
    stream_id: str
    nodes: tuple[RuntimeEventRelationGraphNode, ...]
    edges: tuple[RuntimeEventRelationGraphEdge, ...]
    node_count: int
    edge_count: int
    correlation_ids: tuple[str, ...]
    truth_label: FlowTruthLabel
    trace_unavailable_reason: str
    graph_hash: str
    is_trace: bool = False
    is_ledger: bool = False
    trace_verified: bool = False

    def __post_init__(self) -> None:
        for boundary_field in ("is_trace", "is_ledger", "trace_verified"):
            if getattr(self, boundary_field):
                raise AurelFlowValidationError(
                    f"RuntimeEventRelationGraph.{boundary_field} must remain False",
                    code=AurelFlowErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                    field=boundary_field,
                )


def build_runtime_event_relation_graph(
    event_stream: RuntimeEventStream,
) -> RuntimeEventRelationGraph:
    """Project parent / caused-by relations into a deterministic graph.
    Relations are preserved exactly as recorded; nothing is inferred."""

    nodes = tuple(
        RuntimeEventRelationGraphNode(
            event_id=event.event_id,
            sequence=event.sequence,
            event_kind=event.event_kind.value,
            target_node_id=event.target_node_id,
            correlation_id=event.relation.correlation_id,
            affected_node_ids=event.relation.affected_node_ids,
            affected_run_ids=event.relation.affected_run_ids,
            truth_label=event.truth_label,
        )
        for event in event_stream.events
    )
    edges = []
    for event in event_stream.events:
        relation = event.relation
        for relation_kind, from_event_id in (
            ("PARENT", relation.parent_event_id),
            ("CAUSED_BY", relation.caused_by_event_id),
        ):
            if not from_event_id:
                continue
            edge_payload = {
                "graph_version": RUNTIME_EVENT_RELATION_GRAPH_VERSION,
                "relation_kind": relation_kind,
                "from": from_event_id,
                "to": event.event_id,
            }
            edges.append(
                RuntimeEventRelationGraphEdge(
                    edge_id=stable_hash(edge_payload),
                    from_event_id=from_event_id,
                    to_event_id=event.event_id,
                    relation_kind=relation_kind,
                    influence_strength_label=relation.influence_strength_label,
                    truth_label=FlowTruthLabel.READ_MODEL_ONLY,
                )
            )
    correlation_ids = tuple(
        sorted(
            {
                event.relation.correlation_id
                for event in event_stream.events
                if event.relation.correlation_id
            }
        )
    )
    graph_payload = {
        "graph_version": RUNTIME_EVENT_RELATION_GRAPH_VERSION,
        "stream_id": event_stream.stream_id,
        "node_ids": tuple(node.event_id for node in nodes),
        "edge_ids": tuple(edge.edge_id for edge in edges),
    }
    return RuntimeEventRelationGraph(
        graph_version=RUNTIME_EVENT_RELATION_GRAPH_VERSION,
        run_id=event_stream.run_id,
        stream_id=event_stream.stream_id,
        nodes=nodes,
        edges=tuple(edges),
        node_count=len(nodes),
        edge_count=len(edges),
        correlation_ids=correlation_ids,
        truth_label=FlowTruthLabel.READ_MODEL_ONLY,
        trace_unavailable_reason=TRACE_VERIFICATION_UNAVAILABLE_REASON,
        graph_hash=stable_hash(graph_payload),
    )
