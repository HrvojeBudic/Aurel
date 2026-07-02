"""P3-FLOW-A flow runtime foundation read model (operator-inspectable truth).

Exposes graph / run / scheduler truth with honest labels, and exposes what is
NOT available in this pack as first-class fields: execution (P4 AurelExec),
trace verification (P5 AurelTrace), CLI binding (P3.7), runtime event stream
(P3.3 / P3-FLOW-B), approval runtime (P3.4), and persistence. Nothing here is
LIVE and nothing is TRACE_VERIFIED.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from .errors import AurelFlowErrorCode, AurelFlowValidationError
from .scheduler import SchedulerDecision, make_scheduler_decision
from .types import (
    APPROVAL_RUNTIME_UNAVAILABLE_REASON,
    AUREL_FLOW_PACK_ID,
    CLI_BINDING_UNAVAILABLE_REASON,
    EVENT_STREAM_UNAVAILABLE_REASON,
    EXECUTION_UNAVAILABLE_REASON,
    PERSISTENCE_UNAVAILABLE_REASON,
    TRACE_VERIFICATION_UNAVAILABLE_REASON,
    FlowTruthLabel,
    _CanonicalMixin,
    stable_hash,
    to_canonical_json,
)
from .workflow_graph import (
    WorkflowGraph,
    WorkflowGraphReadModel,
    build_workflow_graph_read_model,
)
from .workflow_state import (
    WorkflowRun,
    WorkflowStateSnapshot,
    snapshot_workflow_state,
)

FLOW_RUNTIME_READ_MODEL_VERSION = "flow_runtime_foundation_read_model.v1"


@dataclass(frozen=True)
class FlowNoExecutionProof(_CanonicalMixin):
    """Proof that P3-FLOW-A performs no execution or external side effects."""

    tool_executed: bool = False
    command_executed: bool = False
    subprocess_spawned: bool = False
    network_called: bool = False
    sandbox_invoked: bool = False
    worker_dispatched: bool = False
    agent_dispatched: bool = False
    approval_executed: bool = False
    retry_executed: bool = False
    rollback_executed: bool = False
    memory_written: bool = False
    policy_mutated: bool = False
    identity_mutated: bool = False
    global_trace_written: bool = False
    ledger_written: bool = False
    business_action_executed: bool = False
    live_claimed: bool = False
    trace_verified_claimed: bool = False


@dataclass(frozen=True)
class FlowCapabilityAvailability(_CanonicalMixin):
    """Honest availability of a runtime capability in this pack."""

    capability: str
    available: bool
    truth_label: FlowTruthLabel
    reason: str


UNAVAILABLE_CAPABILITIES: tuple[FlowCapabilityAvailability, ...] = (
    FlowCapabilityAvailability(
        capability="UNAVAILABLE_EXECUTION",
        available=False,
        truth_label=FlowTruthLabel.UNAVAILABLE,
        reason=EXECUTION_UNAVAILABLE_REASON,
    ),
    FlowCapabilityAvailability(
        capability="UNAVAILABLE_TRACE_VERIFICATION",
        available=False,
        truth_label=FlowTruthLabel.UNAVAILABLE,
        reason=TRACE_VERIFICATION_UNAVAILABLE_REASON,
    ),
    FlowCapabilityAvailability(
        capability="UNAVAILABLE_CLI_BINDING",
        available=False,
        truth_label=FlowTruthLabel.UNAVAILABLE,
        reason=CLI_BINDING_UNAVAILABLE_REASON,
    ),
    FlowCapabilityAvailability(
        capability="UNAVAILABLE_EVENT_STREAM",
        available=False,
        truth_label=FlowTruthLabel.UNAVAILABLE,
        reason=EVENT_STREAM_UNAVAILABLE_REASON,
    ),
    FlowCapabilityAvailability(
        capability="UNAVAILABLE_APPROVAL_RUNTIME",
        available=False,
        truth_label=FlowTruthLabel.UNAVAILABLE,
        reason=APPROVAL_RUNTIME_UNAVAILABLE_REASON,
    ),
    FlowCapabilityAvailability(
        capability="UNAVAILABLE_PERSISTENCE",
        available=False,
        truth_label=FlowTruthLabel.UNAVAILABLE,
        reason=PERSISTENCE_UNAVAILABLE_REASON,
    ),
)


@dataclass(frozen=True)
class FlowRuntimeFoundationReadModel(_CanonicalMixin):
    """Operator-facing read model: graph -> run state -> scheduler decision."""

    read_model_version: str
    pack_id: str
    graph: WorkflowGraphReadModel
    run_snapshot: WorkflowStateSnapshot
    scheduler_decision: SchedulerDecision
    ready_node_ids: tuple[str, ...]
    waiting_dependency_node_ids: tuple[str, ...]
    waiting_approval_node_ids: tuple[str, ...]
    blocked_node_ids: tuple[str, ...]
    next_ready_node_id: str
    truth_labels: Mapping[str, str]
    unavailable_capabilities: tuple[FlowCapabilityAvailability, ...]
    no_execution_proof: FlowNoExecutionProof
    live: bool
    trace_verified: bool
    read_model_hash: str


def build_flow_runtime_read_model(
    graph: WorkflowGraph,
    run: WorkflowRun,
    scheduler_decision: SchedulerDecision | None = None,
) -> FlowRuntimeFoundationReadModel:
    """Build the operator-inspectable foundation read model. Pure and
    deterministic; recomputes the scheduler decision if not supplied."""

    decision = scheduler_decision or make_scheduler_decision(graph, run)
    if decision.run_id != run.run_id or decision.step != run.state.step:
        raise AurelFlowValidationError(
            f"scheduler decision {decision.run_id!r}@{decision.step} does not match "
            f"run {run.run_id!r}@{run.state.step}",
            code=AurelFlowErrorCode.GRAPH_RUN_MISMATCH,
            field="scheduler_decision",
        )
    graph_read_model = build_workflow_graph_read_model(graph)
    run_snapshot = snapshot_workflow_state(run)
    reasons: dict[str, list[str]] = {
        "WAITING_DEPENDENCY": [],
        "WAITING_APPROVAL": [],
        "BLOCKED": [],
    }
    for node_decision in decision.node_decisions:
        bucket = reasons.get(node_decision.reason.value)
        if bucket is not None:
            bucket.append(node_decision.node_id)
    truth_labels = {
        "graph": graph.truth_label.value,
        "run": run.truth_label.value,
        "scheduler": decision.truth_label.value,
        "execution": FlowTruthLabel.UNAVAILABLE.value,
        "trace_verification": FlowTruthLabel.UNAVAILABLE.value,
        "cli_binding": FlowTruthLabel.UNAVAILABLE.value,
    }
    payload = {
        "read_model_version": FLOW_RUNTIME_READ_MODEL_VERSION,
        "graph_hash": graph.graph_hash,
        "snapshot_hash": run_snapshot.snapshot_hash,
        "decision_hash": decision.decision_hash,
    }
    return FlowRuntimeFoundationReadModel(
        read_model_version=FLOW_RUNTIME_READ_MODEL_VERSION,
        pack_id=AUREL_FLOW_PACK_ID,
        graph=graph_read_model,
        run_snapshot=run_snapshot,
        scheduler_decision=decision,
        ready_node_ids=decision.ready_node_ids,
        waiting_dependency_node_ids=tuple(reasons["WAITING_DEPENDENCY"]),
        waiting_approval_node_ids=tuple(reasons["WAITING_APPROVAL"]),
        blocked_node_ids=tuple(reasons["BLOCKED"]),
        next_ready_node_id=decision.next_ready_node_id,
        truth_labels=truth_labels,
        unavailable_capabilities=UNAVAILABLE_CAPABILITIES,
        no_execution_proof=FlowNoExecutionProof(),
        live=False,
        trace_verified=False,
        read_model_hash=stable_hash(payload),
    )


def serialize_flow_runtime_read_model(read_model: FlowRuntimeFoundationReadModel) -> str:
    """Deterministic JSON export for operator inspection and future P5 binding."""

    return to_canonical_json(read_model)
