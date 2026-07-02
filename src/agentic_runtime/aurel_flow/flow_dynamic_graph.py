"""P3-FLOW-E template / realized runtime graph layer (P3.13.0-P3.13.4).

AurelFlow can distinguish a reusable workflow template from a run-specific
realized runtime graph. Realization is deterministic bookkeeping over an
already-valid ``WorkflowGraph`` + ``WorkflowRun`` pair; it never executes a
node, never dispatches work, and never mutates the template it was derived
from. Execution belongs to P4 AurelExec. Trace verification belongs to P5
AurelTrace.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping

from .errors import AurelFlowErrorCode, AurelFlowValidationError
from .types import FlowTruthLabel, _CanonicalMixin, stable_hash
from .workflow_graph import WorkflowGraph
from .workflow_state import WorkflowRun

AUREL_FLOW_E_PACK_ID = "P3-FLOW-E"
AUREL_FLOW_E_PACK_TITLE = "Dynamic Runtime Graph / Graph Plasticity Pack"
AUREL_FLOW_E_REPORT_PATH = "agent/reports/P3_FLOW_E_DYNAMIC_RUNTIME_GRAPH_PACK.md"

WORKFLOW_TEMPLATE_VERSION = "workflow_template.v1"
REALIZED_RUNTIME_GRAPH_VERSION = "realized_runtime_graph.v1"
RUNTIME_GRAPH_INSTANCE_VERSION = "runtime_graph_instance.v1"

REALIZATION_EXECUTION_UNAVAILABLE_REASON = (
    "graph realization is deterministic bookkeeping only; it never executes "
    "a node or dispatches work — execution belongs to P4 AurelExec"
)
REALIZATION_TRACE_UNAVAILABLE_REASON = (
    "a realized runtime graph is not a trace record and is never "
    "trace-verified; the evidence spine belongs to P5 AurelTrace"
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


class GraphRealizationReason(str, Enum):
    """Why a realized runtime graph was produced. Naming is not executing."""

    RUN_CREATED = "RUN_CREATED"
    RUN_RESUMED = "RUN_RESUMED"
    RUN_REVISED = "RUN_REVISED"
    MANUAL_REALIZATION = "MANUAL_REALIZATION"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"


class GraphDeterminationTimeKind(str, Enum):
    """How realization time is anchored. No wall-clock claim is made."""

    RUN_STEP = "RUN_STEP"
    RUNTIME_EVENT = "RUNTIME_EVENT"
    UNAVAILABLE = "UNAVAILABLE"


@dataclass(frozen=True)
class GraphDeterminationTime(_CanonicalMixin):
    """Logical anchor for when a graph was realized. Not a live clock."""

    determination_kind: GraphDeterminationTimeKind
    run_step: int
    source_event_id: str = ""
    description: str = ""


@dataclass(frozen=True)
class WorkflowTemplateRef(_CanonicalMixin):
    """Stable reference to a workflow template."""

    template_id: str
    template_version: str


@dataclass(frozen=True)
class WorkflowTemplate(_CanonicalMixin):
    """Reusable workflow design. Distinct from any run-specific realized graph."""

    template_id: str
    contract_version: str
    source_workflow_graph_id: str
    source_graph_hash: str
    name: str
    version: str
    node_count: int
    edge_count: int
    truth_label: FlowTruthLabel
    template_hash: str
    metadata: Mapping[str, str] = field(default_factory=dict)
    execution_available: bool = False
    dispatch_available: bool = False

    def __post_init__(self) -> None:
        _forbid_true(self, "execution_available", "dispatch_available")


def create_workflow_template(
    graph: WorkflowGraph, *, metadata: Mapping[str, str] | None = None
) -> WorkflowTemplate:
    """Build a reusable template from a declarative graph. Nothing executes."""

    payload = {
        "contract_version": WORKFLOW_TEMPLATE_VERSION,
        "source_workflow_graph_id": graph.graph_id,
        "source_graph_hash": graph.graph_hash,
        "version": graph.version,
    }
    template_id = "fltpl-" + stable_hash(payload)[:16]
    return WorkflowTemplate(
        template_id=template_id,
        contract_version=WORKFLOW_TEMPLATE_VERSION,
        source_workflow_graph_id=graph.graph_id,
        source_graph_hash=graph.graph_hash,
        name=graph.name,
        version=graph.version,
        node_count=len(graph.nodes),
        edge_count=len(graph.edges),
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
        template_hash=stable_hash(payload),
        metadata=dict(metadata or {}),
    )


def workflow_template_ref(template: WorkflowTemplate) -> WorkflowTemplateRef:
    return WorkflowTemplateRef(
        template_id=template.template_id, template_version=template.version
    )


@dataclass(frozen=True)
class RealizedRuntimeGraphRef(_CanonicalMixin):
    """Stable reference to a realized runtime graph."""

    realized_graph_id: str
    run_id: str


@dataclass(frozen=True)
class RealizedRuntimeGraph(_CanonicalMixin):
    """Run-specific graph realization. Realizing a template does not execute it."""

    realized_graph_id: str
    contract_version: str
    template_id: str
    source_workflow_graph_id: str
    run_id: str
    graph_version: int
    determination_time: GraphDeterminationTime
    realization_reason: GraphRealizationReason
    node_count: int
    edge_count: int
    truth_label: FlowTruthLabel
    realized_graph_hash: str
    unavailable_reason: str = REALIZATION_EXECUTION_UNAVAILABLE_REASON
    metadata: Mapping[str, str] = field(default_factory=dict)
    execution_available: bool = False
    dispatch_available: bool = False
    trace_verified: bool = False

    def __post_init__(self) -> None:
        _forbid_true(
            self, "execution_available", "dispatch_available", "trace_verified"
        )


def realize_runtime_graph(
    *,
    template: WorkflowTemplate,
    run: WorkflowRun,
    realization_reason: GraphRealizationReason,
    determination_time: GraphDeterminationTime | None = None,
    graph_version: int = 1,
    metadata: Mapping[str, str] | None = None,
) -> RealizedRuntimeGraph:
    """Deterministically realize a run-specific graph from a template.

    Pure derivation: reads ``template``/``run`` and returns a new immutable
    object. Neither argument is mutated, and nothing here executes a node.
    """

    if run.graph_id != template.source_workflow_graph_id:
        raise AurelFlowValidationError(
            f"run {run.run_id!r} graph_id {run.graph_id!r} does not match "
            f"template source graph {template.source_workflow_graph_id!r}",
            code=AurelFlowErrorCode.GRAPH_RUN_MISMATCH,
            field="run",
        )
    resolved_time = determination_time or GraphDeterminationTime(
        determination_kind=GraphDeterminationTimeKind.RUN_STEP,
        run_step=run.state.step,
        description="realized from current run step",
    )
    payload = {
        "contract_version": REALIZED_RUNTIME_GRAPH_VERSION,
        "template_id": template.template_id,
        "run_id": run.run_id,
        "graph_version": graph_version,
        "realization_reason": realization_reason.value,
    }
    realized_graph_id = "flrrg-" + stable_hash(payload)[:16]
    return RealizedRuntimeGraph(
        realized_graph_id=realized_graph_id,
        contract_version=REALIZED_RUNTIME_GRAPH_VERSION,
        template_id=template.template_id,
        source_workflow_graph_id=template.source_workflow_graph_id,
        run_id=run.run_id,
        graph_version=graph_version,
        determination_time=resolved_time,
        realization_reason=realization_reason,
        node_count=template.node_count,
        edge_count=template.edge_count,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
        realized_graph_hash=stable_hash(payload),
        metadata=dict(metadata or {}),
    )


def realized_runtime_graph_ref(realized: RealizedRuntimeGraph) -> RealizedRuntimeGraphRef:
    return RealizedRuntimeGraphRef(
        realized_graph_id=realized.realized_graph_id, run_id=realized.run_id
    )


@dataclass(frozen=True)
class RuntimeGraphInstance(_CanonicalMixin):
    """Lightweight identity/status wrapper around a realized graph."""

    instance_id: str
    contract_version: str
    realized_graph_id: str
    run_id: str
    graph_version: int
    truth_label: FlowTruthLabel
    execution_available: bool = False

    def __post_init__(self) -> None:
        _forbid_true(self, "execution_available")


def build_runtime_graph_instance(realized_graph: RealizedRuntimeGraph) -> RuntimeGraphInstance:
    payload = {
        "contract_version": RUNTIME_GRAPH_INSTANCE_VERSION,
        "realized_graph_id": realized_graph.realized_graph_id,
        "run_id": realized_graph.run_id,
        "graph_version": realized_graph.graph_version,
    }
    instance_id = "flgin-" + stable_hash(payload)[:16]
    return RuntimeGraphInstance(
        instance_id=instance_id,
        contract_version=RUNTIME_GRAPH_INSTANCE_VERSION,
        realized_graph_id=realized_graph.realized_graph_id,
        run_id=realized_graph.run_id,
        graph_version=realized_graph.graph_version,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
    )
