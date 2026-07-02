from __future__ import annotations

import pytest

from agentic_runtime.aurel_flow import (
    AurelFlowErrorCode,
    FlowTruthLabel,
    WorkflowEdge,
    WorkflowEdgeType,
    WorkflowGraphSpec,
    WorkflowNode,
    WorkflowNodeType,
    build_workflow_graph,
    build_workflow_graph_read_model,
    to_canonical_json,
    validate_workflow_graph,
)


def _nodes() -> tuple[WorkflowNode, ...]:
    return (
        WorkflowNode(node_id="start", node_type=WorkflowNodeType.START),
        WorkflowNode(node_id="work", node_type=WorkflowNodeType.TASK),
        WorkflowNode(node_id="end", node_type=WorkflowNodeType.END),
    )


def _edges() -> tuple[WorkflowEdge, ...]:
    return (
        WorkflowEdge(edge_id="e1", from_node_id="start", to_node_id="work"),
        WorkflowEdge(edge_id="e2", from_node_id="work", to_node_id="end"),
    )


def _valid_graph(**overrides):
    params = dict(
        graph_id="g-valid",
        name="valid graph",
        nodes=_nodes(),
        edges=_edges(),
        entry_node_ids=("start",),
        exit_node_ids=("end",),
    )
    params.update(overrides)
    return build_workflow_graph(**params)


def _issue_codes(result) -> set[AurelFlowErrorCode]:
    return {issue.code for issue in result.issues}


def test_p3_flow_a_module_imports_cleanly() -> None:
    import agentic_runtime.aurel_flow as aurel_flow

    assert aurel_flow.AUREL_FLOW_PACK_ID == "P3-FLOW-A"


def test_valid_graph_passes_validation() -> None:
    graph = _valid_graph()
    result = validate_workflow_graph(graph)

    assert result.valid is True
    assert result.issues == ()
    assert result.graph_hash == graph.graph_hash
    assert graph.truth_label is FlowTruthLabel.LOCAL_RUNTIME_SUBSTRATE


def test_duplicate_node_ids_fail_closed() -> None:
    graph = _valid_graph(
        nodes=_nodes() + (WorkflowNode(node_id="work", node_type=WorkflowNodeType.TASK),)
    )
    result = validate_workflow_graph(graph)

    assert result.valid is False
    assert AurelFlowErrorCode.DUPLICATE_NODE_ID in _issue_codes(result)


def test_duplicate_edge_ids_fail_closed() -> None:
    graph = _valid_graph(
        edges=_edges()
        + (WorkflowEdge(edge_id="e1", from_node_id="start", to_node_id="end"),)
    )
    result = validate_workflow_graph(graph)

    assert result.valid is False
    assert AurelFlowErrorCode.DUPLICATE_EDGE_ID in _issue_codes(result)


def test_edge_referencing_unknown_node_fails_closed() -> None:
    graph = _valid_graph(
        edges=_edges()
        + (WorkflowEdge(edge_id="e3", from_node_id="work", to_node_id="ghost"),)
    )
    result = validate_workflow_graph(graph)

    assert result.valid is False
    assert AurelFlowErrorCode.UNKNOWN_NODE_REF in _issue_codes(result)


def test_unsupported_node_and_edge_types_fail_closed_world() -> None:
    spec = WorkflowGraphSpec(
        allowed_node_types=(
            WorkflowNodeType.START,
            WorkflowNodeType.TASK,
            WorkflowNodeType.END,
        ),
        allowed_edge_types=(WorkflowEdgeType.DEFAULT,),
    )
    graph = _valid_graph(
        nodes=_nodes() + (WorkflowNode(node_id="w1", node_type=WorkflowNodeType.WAIT),),
        edges=_edges()
        + (
            WorkflowEdge(
                edge_id="e-roll",
                from_node_id="work",
                to_node_id="w1",
                edge_type=WorkflowEdgeType.ROLLBACK_CANDIDATE,
            ),
        ),
    )
    result = validate_workflow_graph(graph, spec)

    assert result.valid is False
    codes = _issue_codes(result)
    assert AurelFlowErrorCode.UNSUPPORTED_NODE_TYPE in codes
    assert AurelFlowErrorCode.UNSUPPORTED_EDGE_TYPE in codes


def test_missing_and_unknown_entry_exit_nodes_fail_closed() -> None:
    missing = validate_workflow_graph(_valid_graph(entry_node_ids=(), exit_node_ids=()))
    unknown = validate_workflow_graph(
        _valid_graph(entry_node_ids=("ghost-in",), exit_node_ids=("ghost-out",))
    )

    assert missing.valid is False
    assert AurelFlowErrorCode.MISSING_ENTRY_NODE in _issue_codes(missing)
    assert AurelFlowErrorCode.MISSING_EXIT_NODE in _issue_codes(missing)
    assert unknown.valid is False
    assert AurelFlowErrorCode.UNKNOWN_ENTRY_NODE in _issue_codes(unknown)
    assert AurelFlowErrorCode.UNKNOWN_EXIT_NODE in _issue_codes(unknown)


def test_dependency_cycle_fails_closed() -> None:
    graph = _valid_graph(
        edges=_edges()
        + (WorkflowEdge(edge_id="e-back", from_node_id="end", to_node_id="start"),)
    )
    result = validate_workflow_graph(graph)

    assert result.valid is False
    assert AurelFlowErrorCode.GRAPH_CYCLE_DETECTED in _issue_codes(result)


def test_rollback_candidate_back_edge_is_not_a_dependency_cycle() -> None:
    graph = _valid_graph(
        edges=_edges()
        + (
            WorkflowEdge(
                edge_id="e-roll",
                from_node_id="end",
                to_node_id="work",
                edge_type=WorkflowEdgeType.ROLLBACK_CANDIDATE,
            ),
        ),
    )
    result = validate_workflow_graph(graph)

    assert result.valid is True


def test_unreachable_node_fails_closed() -> None:
    graph = _valid_graph(
        nodes=_nodes() + (WorkflowNode(node_id="island", node_type=WorkflowNodeType.TASK),)
    )
    result = validate_workflow_graph(graph)

    assert result.valid is False
    assert AurelFlowErrorCode.UNREACHABLE_NODE in _issue_codes(result)


def test_approval_node_without_flag_fails_closed() -> None:
    graph = _valid_graph(
        nodes=(
            WorkflowNode(node_id="start", node_type=WorkflowNodeType.START),
            WorkflowNode(
                node_id="work", node_type=WorkflowNodeType.APPROVAL, requires_approval=False
            ),
            WorkflowNode(node_id="end", node_type=WorkflowNodeType.END),
        )
    )
    result = validate_workflow_graph(graph)

    assert result.valid is False
    assert AurelFlowErrorCode.APPROVAL_FLAG_MISMATCH in _issue_codes(result)


def test_graph_serialization_and_hash_are_deterministic() -> None:
    first = _valid_graph()
    second = _valid_graph()
    different = _valid_graph(graph_id="g-other")

    assert first.graph_hash == second.graph_hash
    assert to_canonical_json(first) == to_canonical_json(second)
    assert first.graph_hash != different.graph_hash


def test_graph_read_model_exposes_summary_and_boundary() -> None:
    read_model = build_workflow_graph_read_model(_valid_graph())

    assert read_model.node_count == 3
    assert read_model.edge_count == 2
    assert read_model.node_ids == ("start", "work", "end")
    assert read_model.entry_node_ids == ("start",)
    assert read_model.valid is True
    assert read_model.issue_codes == ()
    assert read_model.node_type_counts == {"START": 1, "TASK": 1, "END": 1}
    assert read_model.graph_is_definition_not_permission is True
    assert read_model.graph_executes_nothing is True
    assert read_model.read_model_hash


def test_invalid_graph_read_model_reports_issue_codes() -> None:
    graph = _valid_graph(entry_node_ids=())
    read_model = build_workflow_graph_read_model(graph)

    assert read_model.valid is False
    assert "MISSING_ENTRY_NODE" in read_model.issue_codes


@pytest.mark.parametrize("field_name", ["graph_id", "name"])
def test_empty_identity_fields_fail_closed(field_name: str) -> None:
    graph = _valid_graph(**{field_name: ""})
    result = validate_workflow_graph(graph)

    assert result.valid is False
