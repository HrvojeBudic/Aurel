"""P3-FLOW-A operator demo helper (DEV_FIXTURE).

Builds a deterministic in-memory sample workflow, applies safe transitions,
and returns the foundation read model proving graph -> run state -> scheduler
decision without executing anything. The demo marks node states via explicit
safe transitions; marking a state is recorded bookkeeping, not execution.
"""

from __future__ import annotations

from .read_model import FlowRuntimeFoundationReadModel, build_flow_runtime_read_model
from .types import FlowSourceLabel, FlowTruthLabel
from .workflow_graph import (
    WorkflowEdge,
    WorkflowEdgeType,
    WorkflowGraph,
    WorkflowNode,
    WorkflowNodeType,
    build_workflow_graph,
)
from .workflow_state import (
    WorkflowLifecycleStatus,
    WorkflowNodeState,
    WorkflowRun,
    create_workflow_run,
    lifecycle_transition,
    node_transition,
    transition_workflow_run,
)

DEMO_GRAPH_ID = "flow-demo-governed-change"
DEMO_RUN_KEY = "demo-run-0001"


def build_demo_workflow_graph() -> WorkflowGraph:
    """Deterministic sample graph: start -> fetch -> approval gate -> apply -> end."""

    nodes = (
        WorkflowNode(
            node_id="start",
            node_type=WorkflowNodeType.START,
            title="Start",
            truth_label=FlowTruthLabel.DEV_FIXTURE,
        ),
        WorkflowNode(
            node_id="fetch",
            node_type=WorkflowNodeType.TASK,
            title="Fetch inputs",
            outputs=("inputs",),
            truth_label=FlowTruthLabel.DEV_FIXTURE,
        ),
        WorkflowNode(
            node_id="gate",
            node_type=WorkflowNodeType.APPROVAL,
            title="Operator approval gate",
            requires_approval=True,
            risk_tier="HIGH",
            truth_label=FlowTruthLabel.DEV_FIXTURE,
        ),
        WorkflowNode(
            node_id="apply",
            node_type=WorkflowNodeType.TASK,
            title="Apply change",
            inputs=("inputs",),
            truth_label=FlowTruthLabel.DEV_FIXTURE,
        ),
        WorkflowNode(
            node_id="end",
            node_type=WorkflowNodeType.END,
            title="End",
            truth_label=FlowTruthLabel.DEV_FIXTURE,
        ),
    )
    edges = (
        WorkflowEdge(edge_id="e-start-fetch", from_node_id="start", to_node_id="fetch"),
        WorkflowEdge(edge_id="e-fetch-gate", from_node_id="fetch", to_node_id="gate"),
        WorkflowEdge(edge_id="e-gate-apply", from_node_id="gate", to_node_id="apply"),
        WorkflowEdge(edge_id="e-apply-end", from_node_id="apply", to_node_id="end"),
        # Declarative rollback marker only — not rollback execution (P3.5/P4).
        WorkflowEdge(
            edge_id="e-apply-rollback",
            from_node_id="apply",
            to_node_id="fetch",
            edge_type=WorkflowEdgeType.ROLLBACK_CANDIDATE,
        ),
    )
    return build_workflow_graph(
        graph_id=DEMO_GRAPH_ID,
        name="Governed change demo workflow",
        description="DEV_FIXTURE sample workflow for the P3-FLOW-A foundation demo",
        nodes=nodes,
        edges=edges,
        entry_node_ids=("start",),
        exit_node_ids=("end",),
        truth_label=FlowTruthLabel.DEV_FIXTURE,
        source_label=FlowSourceLabel.DEV_FIXTURE,
    )


def _mark_node_completed(run: WorkflowRun, node_id: str) -> WorkflowRun:
    for from_state, to_state in (
        (WorkflowNodeState.NOT_STARTED, WorkflowNodeState.READY),
        (WorkflowNodeState.READY, WorkflowNodeState.RUNNING),
        (WorkflowNodeState.RUNNING, WorkflowNodeState.COMPLETED),
    ):
        run = transition_workflow_run(
            run, node_transition(node_id, from_state, to_state, reason="demo state mark")
        )
    return run


def run_flow_foundation_demo() -> FlowRuntimeFoundationReadModel:
    """Deterministic demo: valid graph -> run -> transitions -> scheduler truth.

    Leaves the run mid-flight so the read model shows READY, WAITING_APPROVAL,
    and WAITING_DEPENDENCY reasons at once: start and fetch are marked
    COMPLETED, the approval gate waits (never self-approved), and apply/end
    wait on dependencies.
    """

    graph = build_demo_workflow_graph()
    run = create_workflow_run(
        graph,
        run_key=DEMO_RUN_KEY,
        truth_label=FlowTruthLabel.DEV_FIXTURE,
        source_label=FlowSourceLabel.DEV_FIXTURE,
    )
    run = transition_workflow_run(
        run,
        lifecycle_transition(
            WorkflowLifecycleStatus.CREATED, WorkflowLifecycleStatus.READY, "demo"
        ),
    )
    run = transition_workflow_run(
        run,
        lifecycle_transition(
            WorkflowLifecycleStatus.READY, WorkflowLifecycleStatus.RUNNING, "demo"
        ),
    )
    run = _mark_node_completed(run, "start")
    run = _mark_node_completed(run, "fetch")
    return build_flow_runtime_read_model(graph, run)
