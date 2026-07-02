"""P3-FLOW-A / P3-FLOW-B operator demo helpers (DEV_FIXTURE).

Builds a deterministic in-memory sample workflow, applies safe transitions,
and returns the foundation read model proving graph -> run state -> scheduler
decision without executing anything. The demo marks node states via explicit
safe transitions; marking a state is recorded bookkeeping, not execution.
The P3-FLOW-B demo extends this with the behavior loop: events -> mediated
state commitment -> pause/operator signal -> failure/retry/recovery/rollback
candidates -> runtime behavior read model. Still nothing executes.
"""

from __future__ import annotations

from .pause_resume import (
    OperatorDecisionKind,
    WorkflowPauseReason,
    create_operator_decision_signal,
    create_responsibility_transfer_frame,
    pause_workflow_run,
    resume_workflow_run,
)
from .read_model import FlowRuntimeFoundationReadModel, build_flow_runtime_read_model
from .recovery import (
    DEFAULT_RETRY_POLICY,
    RollbackCandidateReason,
    build_recovery_frame,
    build_recovery_proposal,
    build_rollback_candidate,
    calculate_retry_eligibility,
    classify_failure,
)
from .runtime_behavior_read_model import (
    RuntimeBehaviorReadModel,
    build_runtime_behavior_read_model,
)
from .runtime_events import (
    RuntimeEventKind,
    RuntimeEventRelation,
    RuntimeEventSource,
    append_runtime_event,
    create_runtime_event_stream,
)
from .state_commitment import (
    commit_internal_runtime_state,
    create_mediated_actor_output,
    create_runtime_state_commitment,
)
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


def _mark_node_failed(run, node_id: str):
    for from_state, to_state in (
        (WorkflowNodeState.NOT_STARTED, WorkflowNodeState.READY),
        (WorkflowNodeState.READY, WorkflowNodeState.RUNNING),
        (WorkflowNodeState.RUNNING, WorkflowNodeState.FAILED),
    ):
        run = transition_workflow_run(
            run, node_transition(node_id, from_state, to_state, reason="demo failure mark")
        )
    return run


def run_runtime_behavior_demo() -> RuntimeBehaviorReadModel:
    """Deterministic P3-FLOW-B demo: the full behavior loop, no execution.

    Records events with relations, mediates an internal state commitment,
    pauses on the approval gate, records an operator resume signal, marks a
    failure, and produces retry/recovery/rollback candidates — all as local
    DEV_FIXTURE behavior state.
    """

    graph = build_demo_workflow_graph()
    run = create_workflow_run(
        graph,
        run_key="behavior-demo-0001",
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

    source = RuntimeEventSource(source_id="aurel-flow-demo", source_label=FlowSourceLabel.DEV_FIXTURE)
    stream = create_runtime_event_stream(
        run.run_id, stream_key="behavior-demo", truth_label=FlowTruthLabel.DEV_FIXTURE
    )
    created = append_runtime_event(
        stream,
        event_kind=RuntimeEventKind.RUN_CREATED,
        source=source,
        truth_label=FlowTruthLabel.DEV_FIXTURE,
    )
    stream = created.stream
    decided = append_runtime_event(
        stream,
        event_kind=RuntimeEventKind.SCHEDULER_DECISION_RECORDED,
        source=source,
        relation=RuntimeEventRelation(
            parent_event_id=created.event.event_id,
            correlation_id="behavior-demo",
            caused_by_event_id=created.event.event_id,
            affected_node_ids=("fetch", "gate"),
        ),
        truth_label=FlowTruthLabel.DEV_FIXTURE,
    )
    stream = decided.stream
    paused_event = append_runtime_event(
        stream,
        event_kind=RuntimeEventKind.PAUSED,
        source=source,
        target_node_id="gate",
        relation=RuntimeEventRelation(
            parent_event_id=decided.event.event_id,
            correlation_id="behavior-demo",
            affected_node_ids=("gate",),
        ),
        truth_label=FlowTruthLabel.DEV_FIXTURE,
    )
    stream = paused_event.stream

    output = create_mediated_actor_output(
        actor_id="demo-actor",
        target_run_id=run.run_id,
        target_node_id="fetch",
        proposed_symbol_or_state_ref="fetch.result.v1",
        reason="demo mediated output",
    )
    commitment_result = commit_internal_runtime_state(
        create_runtime_state_commitment(
            output,
            previous_state_ref="fetch.result.v0",
            proposed_state_ref="fetch.result.v1",
            source_event_id=decided.event.event_id,
        )
    )

    pause = pause_workflow_run(
        run,
        pause_reason=WorkflowPauseReason.WAITING_APPROVAL,
        target_node_id="gate",
        waiting_for="operator approval decision",
        source_event_id=paused_event.event.event_id,
    )
    resume_signal = create_operator_decision_signal(
        operator_id="demo-operator",
        decision_kind=OperatorDecisionKind.RESUME,
        target_run_id=run.run_id,
        reason="demo operator resume",
        counterargument_present=True,
        decision_pressure_warning=True,
    )
    resumed = resume_workflow_run(pause.run, pause.pause_state, resume_signal)
    run = resumed.run

    run = _mark_node_failed(run, "fetch")
    assessment = classify_failure(
        target_run_id=run.run_id,
        target_node_id="fetch",
        graph=graph,
        validation_failed=True,
        detail="demo validation failure on fetch",
    )
    eligibility = calculate_retry_eligibility(
        DEFAULT_RETRY_POLICY, assessment, attempt_count=1
    )
    frame = build_recovery_frame(assessment)
    proposal = build_recovery_proposal(
        frame,
        step_descriptions=(
            "re-validate fetch inputs",
            "request operator review of fetch result",
        ),
    )
    candidate = build_rollback_candidate(
        target_run_id=run.run_id,
        target_node_id="fetch",
        target_state_ref="fetch.result.v0",
        candidate_reason=RollbackCandidateReason.FAILED_STATE_TRANSITION,
        reason="fetch failed after internal commit; rollback candidate marked only",
    )
    responsibility = create_responsibility_transfer_frame(
        from_actor="demo-actor",
        to_actor="demo-operator",
        target_run_id=run.run_id,
        target_node_id="fetch",
        reason="operator should decide how to continue after fetch failure",
    )

    return build_runtime_behavior_read_model(
        run.run_id,
        event_stream=stream,
        mediated_actor_outputs=(output,),
        state_commitments=(commitment_result.commitment,),
        pause_states=(pause.pause_state,),
        operator_decision_signals=(resume_signal,),
        responsibility_transfer_frames=(responsibility,),
        retry_eligibilities=(eligibility,),
        recovery_proposals=(proposal,),
        rollback_candidates=(candidate,),
        failure_assessments=(assessment,),
    )
