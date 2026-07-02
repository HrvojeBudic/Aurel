from __future__ import annotations

from dataclasses import replace

import pytest

from agentic_runtime.aurel_flow import (
    AurelFlowValidationError,
    build_flow_demo_bundle,
    build_runtime_event_relation_graph,
)


def test_relation_graph_has_one_node_per_event() -> None:
    bundle = build_flow_demo_bundle()
    graph = build_runtime_event_relation_graph(bundle.event_stream)

    assert graph.node_count == len(bundle.event_stream.events)
    assert tuple(node.event_id for node in graph.nodes) == tuple(
        event.event_id for event in bundle.event_stream.events
    )


def test_relation_graph_preserves_parent_and_caused_by_edges() -> None:
    bundle = build_flow_demo_bundle()
    events = bundle.event_stream.events
    graph = build_runtime_event_relation_graph(bundle.event_stream)

    # demo: event 2 has parent+caused_by -> event 1; event 3 has parent -> event 2
    edge_pairs = {
        (edge.relation_kind, edge.from_event_id, edge.to_event_id)
        for edge in graph.edges
    }
    assert ("PARENT", events[0].event_id, events[1].event_id) in edge_pairs
    assert ("CAUSED_BY", events[0].event_id, events[1].event_id) in edge_pairs
    assert ("PARENT", events[1].event_id, events[2].event_id) in edge_pairs
    assert graph.edge_count == 3


def test_relation_graph_preserves_correlation_and_affected_ids() -> None:
    bundle = build_flow_demo_bundle()
    graph = build_runtime_event_relation_graph(bundle.event_stream)

    assert graph.correlation_ids == ("behavior-demo",)
    affected = {
        node.event_id: node.affected_node_ids for node in graph.nodes
    }
    events = bundle.event_stream.events
    assert affected[events[1].event_id] == ("fetch", "gate")
    assert affected[events[2].event_id] == ("gate",)


def test_relation_graph_is_deterministic() -> None:
    first = build_runtime_event_relation_graph(build_flow_demo_bundle().event_stream)
    second = build_runtime_event_relation_graph(build_flow_demo_bundle().event_stream)

    assert first.graph_hash == second.graph_hash
    assert tuple(edge.edge_id for edge in first.edges) == tuple(
        edge.edge_id for edge in second.edges
    )


def test_relation_graph_is_not_trace_or_ledger() -> None:
    graph = build_runtime_event_relation_graph(build_flow_demo_bundle().event_stream)

    assert graph.is_trace is False
    assert graph.is_ledger is False
    assert graph.trace_verified is False
    for node in graph.nodes:
        assert node.trace_verified is False
        assert node.ledger_written is False


def test_relation_graph_boundary_booleans_fail_closed() -> None:
    graph = build_runtime_event_relation_graph(build_flow_demo_bundle().event_stream)

    for forbidden in ("is_trace", "is_ledger", "trace_verified"):
        with pytest.raises(AurelFlowValidationError):
            replace(graph, **{forbidden: True})
    node = graph.nodes[0]
    for forbidden in ("trace_verified", "ledger_written"):
        with pytest.raises(AurelFlowValidationError):
            replace(node, **{forbidden: True})
