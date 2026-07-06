"""SPINE-LIVE-A — turn a model's plan into a live flow graph.

The cognition leg (DeepSeek or mock) emits a validated structured plan. This
module realizes that plan as a linear AurelFlow graph plus a node->(tool, args)
map the FlowDispatcher can drive. Only allow-listed tools may be realized; any
other tool fails the plan closed, so a hallucinated or unsafe step cannot bind a
lease. The plan proposes; the runtime still disposes on every step.
"""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from ..aurel_flow.workflow_graph import (
    WorkflowEdge,
    WorkflowEdgeType,
    WorkflowGraph,
    WorkflowNode,
    WorkflowNodeType,
    build_workflow_graph,
)

# Tools a realized plan step may bind. Read tools pass through the governed
# runtime; write_file/run_tests additionally hit the S1 hard-isolation gate.
DEFAULT_PLAN_TOOL_ALLOWLIST: tuple[str, ...] = (
    "read_file",
    "list_dir",
    "search_text",
    "write_file",
    "edit_file",
    "run_tests",
)


class PlanRealizationError(ValueError):
    """A plan step could not be safely realized. Fail closed."""


NodeTaskMap = dict[str, tuple[str, Mapping[str, Any]]]


def plan_to_flow(
    steps: Sequence[Mapping[str, Any]],
    *,
    allowed_tools: Sequence[str] = DEFAULT_PLAN_TOOL_ALLOWLIST,
    graph_id: str = "spine-plan",
) -> tuple[WorkflowGraph, NodeTaskMap]:
    """Realize plan steps as a linear graph + node tasks. Fail closed."""
    if not steps:
        raise PlanRealizationError("empty plan realizes no flow")
    allow = set(allowed_tools)

    nodes: list[WorkflowNode] = []
    edges: list[WorkflowEdge] = []
    node_tasks: NodeTaskMap = {}
    node_ids: list[str] = []

    for i, step in enumerate(steps):
        tool = str(step.get("tool", ""))
        if tool not in allow:
            raise PlanRealizationError(
                f"plan step {i} tool {tool!r} is not in the spine allowlist "
                f"{tuple(sorted(allow))}"
            )
        args = step.get("args")
        if not isinstance(args, Mapping):
            raise PlanRealizationError(f"plan step {i} args must be an object")
        raw_id = str(step.get("step_id") or f"s{i}")
        node_id = raw_id if raw_id not in node_tasks else f"{raw_id}_{i}"
        title = str(step.get("reason") or tool)[:60]
        nodes.append(
            WorkflowNode(node_id=node_id, node_type=WorkflowNodeType.TASK, title=title)
        )
        node_tasks[node_id] = (tool, dict(args))
        node_ids.append(node_id)

    for a, b in zip(node_ids, node_ids[1:]):
        edges.append(
            WorkflowEdge(
                edge_id=f"{a}->{b}",
                from_node_id=a,
                to_node_id=b,
                edge_type=WorkflowEdgeType.DEFAULT,
            )
        )

    graph = build_workflow_graph(
        graph_id=graph_id,
        name="Spine plan-driven flow",
        nodes=tuple(nodes),
        edges=tuple(edges),
        entry_node_ids=(node_ids[0],),
        exit_node_ids=(node_ids[-1],),
    )
    return graph, node_tasks


__all__ = [
    "DEFAULT_PLAN_TOOL_ALLOWLIST",
    "PlanRealizationError",
    "plan_to_flow",
]
