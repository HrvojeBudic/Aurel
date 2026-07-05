"""P5.15 — Causal graph is a read-only diagnostic model, never executable."""

from __future__ import annotations

import pytest

from agentic_runtime.aurel_trace import (
    AurelTraceError,
    CausalEdgeKind,
    CausalGraphEdge,
    CausalGraphNode,
    CausalNodeKind,
    GoldenThreadGraph,
    build_causal_graph,
    build_golden_thread_ref,
    build_golden_thread_segment,
)


def _graph():
    segs = [
        build_golden_thread_segment(
            segment_kind="P3->P4", source_ref="si-1", target_ref="job-1", causal_order=0
        ),
        build_golden_thread_segment(
            segment_kind="P4->P5",
            source_ref="job-1",
            target_ref="evt-1",
            causal_order=1,
            missing_links=("no outcome ref bound",),
        ),
    ]
    ref = build_golden_thread_ref(
        root_target_id="si-1", root_target_kind="P3_INTENT", segments=segs
    )
    return build_causal_graph(golden_thread_ref=ref, segments=segs)


def test_graph_has_expected_nodes_and_edges():
    graph = _graph()
    assert len(graph.nodes) == 3  # si-1, job-1, evt-1
    caused = [e for e in graph.edges if e.edge_kind is CausalEdgeKind.CAUSED]
    assert len(caused) == 2


def test_missing_link_surfaces_as_edge_with_reason():
    graph = _graph()
    missing = [e for e in graph.edges if e.edge_kind is CausalEdgeKind.MISSING_LINK]
    assert len(missing) == 1
    assert missing[0].missing_reason == "no outcome ref bound"
    assert graph.missing_links == ("no outcome ref bound",)


def test_graph_is_deterministic():
    assert _graph().to_dict() == _graph().to_dict()


def test_graph_cannot_execute_schedule_or_replay():
    graph = _graph()
    assert graph.executes is False
    assert graph.schedules is False
    assert graph.replays is False
    assert graph.mutates is False
    assert graph.repairs is False
    for bad in ("executes", "schedules", "replays", "mutates", "repairs"):
        with pytest.raises(AurelTraceError):
            GoldenThreadGraph(
                graph_id="g",
                golden_thread_ref=graph.golden_thread_ref,
                nodes=graph.nodes,
                edges=graph.edges,
                **{bad: True},
            )


def test_unknown_node_kind_fails_closed():
    with pytest.raises(AurelTraceError):
        CausalGraphNode(
            node_id="n", node_kind="NOT_A_KIND", source_ref="x"  # type: ignore[arg-type]
        )


def test_unknown_edge_kind_fails_closed():
    with pytest.raises(AurelTraceError):
        CausalGraphEdge(
            edge_id="e",
            edge_kind="NOPE",  # type: ignore[arg-type]
            from_node_id="a",
            to_node_id="b",
        )


def test_missing_link_edge_requires_reason():
    with pytest.raises(AurelTraceError):
        CausalGraphEdge(
            edge_id="e",
            edge_kind=CausalEdgeKind.MISSING_LINK,
            from_node_id="a",
            to_node_id="b",
        )


def test_supported_node_kinds_are_closed_world():
    # Sanity: every declared node kind is constructible.
    for kind in CausalNodeKind:
        node = CausalGraphNode(node_id=f"n-{kind.value}", node_kind=kind, source_ref="r")
        assert node.node_kind is kind
