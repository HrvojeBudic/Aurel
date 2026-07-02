"""P3-FLOW-A workflow graph foundation (P3.0.x).

Declarative workflow structure only. A workflow graph is a definition, not a
permission and not an execution plan. Validation is closed-world and fails
closed: any issue makes the graph invalid. Nothing in this module executes
nodes, dispatches work, or mutates external state.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping

from .errors import AurelFlowErrorCode
from .types import (
    FlowSourceLabel,
    FlowTruthLabel,
    _CanonicalMixin,
    stable_hash,
)

WORKFLOW_GRAPH_CONTRACT_VERSION = "workflow_graph.v1"
WORKFLOW_GRAPH_SPEC_VERSION = "workflow_graph_spec.v1"
WORKFLOW_GRAPH_READ_MODEL_VERSION = "workflow_graph_read_model.v1"


class WorkflowNodeType(str, Enum):
    START = "START"
    TASK = "TASK"
    DECISION = "DECISION"
    APPROVAL = "APPROVAL"
    WAIT = "WAIT"
    END = "END"
    UNAVAILABLE = "UNAVAILABLE"


class WorkflowEdgeType(str, Enum):
    DEFAULT = "DEFAULT"
    CONDITIONAL = "CONDITIONAL"
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"
    ERROR = "ERROR"
    ROLLBACK_CANDIDATE = "ROLLBACK_CANDIDATE"
    UNAVAILABLE = "UNAVAILABLE"


# Edge types that express a scheduling dependency (prerequisite -> dependent).
# ERROR / ROLLBACK_CANDIDATE / UNAVAILABLE edges are declarative markers only;
# a ROLLBACK_CANDIDATE edge is not rollback execution and an ERROR edge is not
# an error handler.
DEPENDENCY_EDGE_TYPES: tuple[WorkflowEdgeType, ...] = (
    WorkflowEdgeType.DEFAULT,
    WorkflowEdgeType.CONDITIONAL,
    WorkflowEdgeType.APPROVAL_REQUIRED,
)


@dataclass(frozen=True)
class WorkflowNode(_CanonicalMixin):
    """Declarative workflow step. A TASK node is a definition, not execution.

    An APPROVAL node is an approval marker; it does not create approval
    runtime and it never approves itself.
    """

    node_id: str
    node_type: WorkflowNodeType
    title: str = ""
    description: str = ""
    inputs: tuple[str, ...] = ()
    outputs: tuple[str, ...] = ()
    requires_approval: bool = False
    risk_tier: str = "UNSPECIFIED"
    truth_label: FlowTruthLabel = FlowTruthLabel.LOCAL_RUNTIME_SUBSTRATE
    metadata: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class WorkflowEdge(_CanonicalMixin):
    """Declarative transition between nodes.

    An APPROVAL_REQUIRED edge is not approval execution; a ROLLBACK_CANDIDATE
    edge is not rollback execution.
    """

    edge_id: str
    from_node_id: str
    to_node_id: str
    edge_type: WorkflowEdgeType = WorkflowEdgeType.DEFAULT
    condition: str = ""
    truth_label: FlowTruthLabel = FlowTruthLabel.LOCAL_RUNTIME_SUBSTRATE
    metadata: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class WorkflowGraphSpec(_CanonicalMixin):
    """Closed-world workflow graph contract."""

    spec_version: str = WORKFLOW_GRAPH_SPEC_VERSION
    allowed_node_types: tuple[WorkflowNodeType, ...] = tuple(WorkflowNodeType)
    allowed_edge_types: tuple[WorkflowEdgeType, ...] = tuple(WorkflowEdgeType)
    require_entry_node: bool = True
    require_exit_node: bool = True
    require_acyclic_dependencies: bool = True
    require_reachability_from_entry: bool = True
    closed_world: bool = True


DEFAULT_WORKFLOW_GRAPH_SPEC = WorkflowGraphSpec()


@dataclass(frozen=True)
class WorkflowGraph(_CanonicalMixin):
    """Canonical declarative workflow graph. Definition, not permission."""

    graph_id: str
    version: str
    name: str
    description: str
    nodes: tuple[WorkflowNode, ...]
    edges: tuple[WorkflowEdge, ...]
    entry_node_ids: tuple[str, ...]
    exit_node_ids: tuple[str, ...]
    truth_label: FlowTruthLabel
    source_label: FlowSourceLabel
    metadata: Mapping[str, str]
    contract_version: str
    graph_hash: str


@dataclass(frozen=True)
class WorkflowGraphValidationIssue(_CanonicalMixin):
    code: AurelFlowErrorCode
    field: str
    message: str


@dataclass(frozen=True)
class WorkflowGraphValidationResult(_CanonicalMixin):
    """Structured graph validation result. Any issue means invalid (fail closed)."""

    graph_id: str
    graph_hash: str
    spec_version: str
    valid: bool
    issues: tuple[WorkflowGraphValidationIssue, ...]


@dataclass(frozen=True)
class WorkflowGraphReadModel(_CanonicalMixin):
    """Operator-inspectable graph summary and boundary state."""

    read_model_version: str
    graph_id: str
    graph_version: str
    name: str
    node_count: int
    edge_count: int
    node_ids: tuple[str, ...]
    edge_ids: tuple[str, ...]
    entry_node_ids: tuple[str, ...]
    exit_node_ids: tuple[str, ...]
    node_type_counts: Mapping[str, int]
    valid: bool
    issue_codes: tuple[str, ...]
    truth_label: FlowTruthLabel
    source_label: FlowSourceLabel
    graph_is_definition_not_permission: bool
    graph_executes_nothing: bool
    graph_hash: str
    read_model_hash: str


def build_workflow_graph(
    *,
    graph_id: str,
    name: str,
    nodes: tuple[WorkflowNode, ...] | list[WorkflowNode],
    edges: tuple[WorkflowEdge, ...] | list[WorkflowEdge] = (),
    entry_node_ids: tuple[str, ...] | list[str] = (),
    exit_node_ids: tuple[str, ...] | list[str] = (),
    version: str = "1",
    description: str = "",
    truth_label: FlowTruthLabel = FlowTruthLabel.LOCAL_RUNTIME_SUBSTRATE,
    source_label: FlowSourceLabel = FlowSourceLabel.LOCAL_CONSTRUCTION,
    metadata: Mapping[str, str] | None = None,
) -> WorkflowGraph:
    """Construct a declarative graph object with a deterministic graph hash.

    Construction does not validate the graph shape; validation is explicit via
    ``validate_workflow_graph`` and run creation fails closed on invalid graphs.
    """

    payload = {
        "contract_version": WORKFLOW_GRAPH_CONTRACT_VERSION,
        "graph_id": graph_id,
        "version": version,
        "name": name,
        "description": description,
        "nodes": tuple(nodes),
        "edges": tuple(edges),
        "entry_node_ids": tuple(entry_node_ids),
        "exit_node_ids": tuple(exit_node_ids),
        "metadata": dict(metadata or {}),
    }
    return WorkflowGraph(
        graph_id=graph_id,
        version=version,
        name=name,
        description=description,
        nodes=tuple(nodes),
        edges=tuple(edges),
        entry_node_ids=tuple(entry_node_ids),
        exit_node_ids=tuple(exit_node_ids),
        truth_label=truth_label,
        source_label=source_label,
        metadata=dict(metadata or {}),
        contract_version=WORKFLOW_GRAPH_CONTRACT_VERSION,
        graph_hash=stable_hash(payload),
    )


def _dependency_adjacency(graph: WorkflowGraph) -> dict[str, tuple[str, ...]]:
    adjacency: dict[str, list[str]] = {node.node_id: [] for node in graph.nodes}
    for edge in graph.edges:
        if edge.edge_type in DEPENDENCY_EDGE_TYPES and edge.from_node_id in adjacency:
            adjacency[edge.from_node_id].append(edge.to_node_id)
    return {node_id: tuple(targets) for node_id, targets in adjacency.items()}


def _find_dependency_cycle(graph: WorkflowGraph) -> tuple[str, ...]:
    adjacency = _dependency_adjacency(graph)
    state: dict[str, int] = {}  # 0 unvisited implicit, 1 in-stack, 2 done

    def visit(node_id: str, stack: tuple[str, ...]) -> tuple[str, ...]:
        state[node_id] = 1
        for target in adjacency.get(node_id, ()):
            if target not in adjacency:
                continue
            if state.get(target) == 1:
                return stack + (node_id, target)
            if state.get(target) != 2:
                found = visit(target, stack + (node_id,))
                if found:
                    return found
        state[node_id] = 2
        return ()

    for node in graph.nodes:
        if state.get(node.node_id) is None:
            cycle = visit(node.node_id, ())
            if cycle:
                return cycle
    return ()


def _reachable_from_entries(graph: WorkflowGraph) -> frozenset[str]:
    known = {node.node_id for node in graph.nodes}
    adjacency: dict[str, list[str]] = {node.node_id: [] for node in graph.nodes}
    for edge in graph.edges:
        if edge.from_node_id in adjacency and edge.to_node_id in known:
            adjacency[edge.from_node_id].append(edge.to_node_id)
    seen: set[str] = set()
    frontier = [entry for entry in graph.entry_node_ids if entry in known]
    while frontier:
        current = frontier.pop()
        if current in seen:
            continue
        seen.add(current)
        frontier.extend(adjacency.get(current, []))
    return frozenset(seen)


def validate_workflow_graph(
    graph: WorkflowGraph,
    spec: WorkflowGraphSpec = DEFAULT_WORKFLOW_GRAPH_SPEC,
) -> WorkflowGraphValidationResult:
    """Closed-world graph validation. Fails closed: any issue means invalid."""

    issues: list[WorkflowGraphValidationIssue] = []

    def issue(code: AurelFlowErrorCode, field_name: str, message: str) -> None:
        issues.append(WorkflowGraphValidationIssue(code=code, field=field_name, message=message))

    if not graph.graph_id:
        issue(AurelFlowErrorCode.EMPTY_GRAPH_ID, "graph_id", "graph_id must be non-empty")
    if not graph.name:
        issue(AurelFlowErrorCode.EMPTY_GRAPH_NAME, "name", "name must be non-empty")
    if not graph.nodes:
        issue(AurelFlowErrorCode.EMPTY_NODE_SET, "nodes", "graph must declare at least one node")

    seen_node_ids: set[str] = set()
    for node in graph.nodes:
        if not node.node_id:
            issue(AurelFlowErrorCode.EMPTY_NODE_ID, "nodes", "node_id must be non-empty")
            continue
        if node.node_id in seen_node_ids:
            issue(
                AurelFlowErrorCode.DUPLICATE_NODE_ID,
                "nodes",
                f"duplicate node_id {node.node_id!r}",
            )
        seen_node_ids.add(node.node_id)
        if node.node_type not in spec.allowed_node_types:
            issue(
                AurelFlowErrorCode.UNSUPPORTED_NODE_TYPE,
                "nodes",
                f"node {node.node_id!r} has unsupported node_type {node.node_type.value!r}",
            )
        if node.node_type is WorkflowNodeType.APPROVAL and not node.requires_approval:
            issue(
                AurelFlowErrorCode.APPROVAL_FLAG_MISMATCH,
                "nodes",
                f"APPROVAL node {node.node_id!r} must set requires_approval=True",
            )

    seen_edge_ids: set[str] = set()
    for edge in graph.edges:
        if not edge.edge_id:
            issue(AurelFlowErrorCode.EMPTY_EDGE_ID, "edges", "edge_id must be non-empty")
            continue
        if edge.edge_id in seen_edge_ids:
            issue(
                AurelFlowErrorCode.DUPLICATE_EDGE_ID,
                "edges",
                f"duplicate edge_id {edge.edge_id!r}",
            )
        seen_edge_ids.add(edge.edge_id)
        if edge.edge_type not in spec.allowed_edge_types:
            issue(
                AurelFlowErrorCode.UNSUPPORTED_EDGE_TYPE,
                "edges",
                f"edge {edge.edge_id!r} has unsupported edge_type {edge.edge_type.value!r}",
            )
        for endpoint_field, endpoint in (
            ("from_node_id", edge.from_node_id),
            ("to_node_id", edge.to_node_id),
        ):
            if endpoint not in seen_node_ids:
                issue(
                    AurelFlowErrorCode.UNKNOWN_NODE_REF,
                    "edges",
                    f"edge {edge.edge_id!r} {endpoint_field} references unknown node {endpoint!r}",
                )

    if spec.require_entry_node and not graph.entry_node_ids:
        issue(
            AurelFlowErrorCode.MISSING_ENTRY_NODE,
            "entry_node_ids",
            "graph must declare at least one entry node",
        )
    if spec.require_exit_node and not graph.exit_node_ids:
        issue(
            AurelFlowErrorCode.MISSING_EXIT_NODE,
            "exit_node_ids",
            "graph must declare at least one exit node",
        )
    for entry in graph.entry_node_ids:
        if entry not in seen_node_ids:
            issue(
                AurelFlowErrorCode.UNKNOWN_ENTRY_NODE,
                "entry_node_ids",
                f"entry node {entry!r} is not declared in nodes",
            )
    for exit_id in graph.exit_node_ids:
        if exit_id not in seen_node_ids:
            issue(
                AurelFlowErrorCode.UNKNOWN_EXIT_NODE,
                "exit_node_ids",
                f"exit node {exit_id!r} is not declared in nodes",
            )

    if spec.require_acyclic_dependencies:
        cycle = _find_dependency_cycle(graph)
        if cycle:
            issue(
                AurelFlowErrorCode.GRAPH_CYCLE_DETECTED,
                "edges",
                "dependency cycle detected: " + " -> ".join(cycle),
            )

    entries_known = bool(graph.entry_node_ids) and all(
        entry in seen_node_ids for entry in graph.entry_node_ids
    )
    if spec.require_reachability_from_entry and entries_known:
        reachable = _reachable_from_entries(graph)
        for node in graph.nodes:
            if node.node_id and node.node_id not in reachable:
                issue(
                    AurelFlowErrorCode.UNREACHABLE_NODE,
                    "nodes",
                    f"node {node.node_id!r} is not reachable from any entry node",
                )

    return WorkflowGraphValidationResult(
        graph_id=graph.graph_id,
        graph_hash=graph.graph_hash,
        spec_version=spec.spec_version,
        valid=not issues,
        issues=tuple(issues),
    )


def build_workflow_graph_read_model(
    graph: WorkflowGraph,
    spec: WorkflowGraphSpec = DEFAULT_WORKFLOW_GRAPH_SPEC,
) -> WorkflowGraphReadModel:
    validation = validate_workflow_graph(graph, spec)
    node_type_counts: dict[str, int] = {}
    for node in graph.nodes:
        node_type_counts[node.node_type.value] = node_type_counts.get(node.node_type.value, 0) + 1
    payload = {
        "read_model_version": WORKFLOW_GRAPH_READ_MODEL_VERSION,
        "graph_hash": graph.graph_hash,
        "valid": validation.valid,
        "issue_codes": tuple(issue.code.value for issue in validation.issues),
    }
    return WorkflowGraphReadModel(
        read_model_version=WORKFLOW_GRAPH_READ_MODEL_VERSION,
        graph_id=graph.graph_id,
        graph_version=graph.version,
        name=graph.name,
        node_count=len(graph.nodes),
        edge_count=len(graph.edges),
        node_ids=tuple(node.node_id for node in graph.nodes),
        edge_ids=tuple(edge.edge_id for edge in graph.edges),
        entry_node_ids=graph.entry_node_ids,
        exit_node_ids=graph.exit_node_ids,
        node_type_counts=node_type_counts,
        valid=validation.valid,
        issue_codes=tuple(issue.code.value for issue in validation.issues),
        truth_label=graph.truth_label,
        source_label=graph.source_label,
        graph_is_definition_not_permission=True,
        graph_executes_nothing=True,
        graph_hash=graph.graph_hash,
        read_model_hash=stable_hash(payload),
    )
