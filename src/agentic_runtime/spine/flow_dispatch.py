"""SPINE-LIVE-2 — the flow dispatch loop.

P3 AurelFlow is a sealed *non-executing* control-plane grammar: its scheduler
computes a ready queue but dispatches nothing, and its run state machine records
transitions but runs no tool. We do not weaken that seal. This spine dispatcher
**consumes** the sealed read-models (``calculate_ready_queue``) and drives real
execution through the S1 ``SpineToolExecSession`` — the only executor — while
mutating run state only through the sealed ``transition_workflow_run`` API.

A node advances only with a real execution attempt ref
(``node_dispatched = bool(exec_evidence)``); checkpoints are captured before and
after each node; a pause predicate lets a run stop and later resume from its
recorded state. AurelFlow still executes nothing; the spine dispatcher does.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Mapping

from ..aurel_flow.recovery import (
    DEFAULT_RETRY_POLICY,
    RetryPolicy,
    build_recovery_frame,
    build_recovery_proposal,
    calculate_retry_eligibility,
    classify_failure,
)
from ..aurel_flow.scheduler import calculate_ready_queue
from ..aurel_flow.workflow_graph import (
    WorkflowGraph,
    WorkflowNode,
    WorkflowNodeType,
    build_workflow_graph,
)
from ..aurel_flow.workflow_state import (
    WorkflowLifecycleStatus,
    WorkflowNodeState,
    WorkflowRun,
    create_workflow_run,
    lifecycle_transition,
    node_transition,
    snapshot_workflow_state,
    transition_workflow_run,
)
from ..core_types import new_id, now
from .tool_exec import SpineToolExecSession, ToolExecEvidenceRef, ToolExecLease

FLOW_DISPATCH_CHECKPOINT_VERSION = "flow_dispatch_checkpoint.v1"
FLOW_DISPATCH_RESULT_VERSION = "flow_dispatch_result.v1"

# node_id -> (tool, args)
NodeTaskMap = Mapping[str, tuple[str, Mapping[str, Any]]]
PausePredicate = Callable[[str, WorkflowRun], bool]


def _make_step(
    node_id: str,
    node_state_after: "WorkflowNodeState",
    evidence: "ToolExecEvidenceRef",
    attempts: int,
    attempt_evidence: list["ToolExecEvidenceRef"],
) -> "FlowDispatchStepResult":
    return FlowDispatchStepResult(
        node_id=node_id,
        node_state_after=node_state_after,
        exec_evidence=evidence,
        dispatched=evidence.available,
        success=evidence.success,
        attempts=attempts,
        attempt_evidence=tuple(attempt_evidence),
    )


@dataclass(frozen=True)
class FlowDispatchCheckpoint:
    """Recorded run + sandbox state around a node dispatch. Not persistence."""

    checkpoint_id: str
    contract_version: str
    phase: str  # "before" | "after"
    node_id: str
    run_step: int
    workflow_snapshot_hash: str
    sandbox_state_hash: str
    produced_at: float

    def to_dict(self) -> dict:
        return {
            "checkpoint_id": self.checkpoint_id,
            "contract_version": self.contract_version,
            "phase": self.phase,
            "node_id": self.node_id,
            "run_step": self.run_step,
            "workflow_snapshot_hash": self.workflow_snapshot_hash,
            "sandbox_state_hash": self.sandbox_state_hash,
            "produced_at": self.produced_at,
        }


@dataclass(frozen=True)
class FlowDispatchStepResult:
    """One node's dispatch outcome."""

    node_id: str
    node_state_after: WorkflowNodeState
    exec_evidence: ToolExecEvidenceRef | None
    dispatched: bool
    success: bool
    attempts: int = 1
    attempt_evidence: tuple[ToolExecEvidenceRef, ...] = ()

    def to_dict(self) -> dict:
        return {
            "node_id": self.node_id,
            "node_state_after": self.node_state_after.value,
            "exec_evidence": self.exec_evidence.to_dict() if self.exec_evidence else None,
            "dispatched": self.dispatched,
            "success": self.success,
            "attempts": self.attempts,
            "attempt_evidence": [e.to_dict() for e in self.attempt_evidence],
        }


@dataclass(frozen=True)
class FlowDispatchResult:
    """Outcome of a dispatch pass over a run."""

    dispatch_id: str
    contract_version: str
    run: WorkflowRun
    step_results: tuple[FlowDispatchStepResult, ...]
    checkpoints: tuple[FlowDispatchCheckpoint, ...]
    lifecycle_status: WorkflowLifecycleStatus
    success: bool
    paused: bool
    recovery_proposal: dict | None = None

    @property
    def execution_available(self) -> bool:
        """True only if every node that carried a task really dispatched."""
        task_steps = [s for s in self.step_results if s.exec_evidence is not None]
        return bool(task_steps) and all(
            s.exec_evidence is not None and s.exec_evidence.available
            for s in task_steps
        )

    def to_dict(self) -> dict:
        return {
            "dispatch_id": self.dispatch_id,
            "contract_version": self.contract_version,
            "run_id": self.run.run_id,
            "step_results": [s.to_dict() for s in self.step_results],
            "checkpoints": [c.to_dict() for c in self.checkpoints],
            "lifecycle_status": self.lifecycle_status.value,
            "success": self.success,
            "paused": self.paused,
            "execution_available": self.execution_available,
            "recovery_proposal": self.recovery_proposal,
        }


def build_patch_test_graph(
    *,
    graph_id: str = "spine-patch-test",
    patch_node_id: str = "patch",
    test_node_id: str = "test",
) -> WorkflowGraph:
    """The canonical 2-node spine graph: [patch] -> [test]."""
    from ..aurel_flow.workflow_graph import WorkflowEdge, WorkflowEdgeType

    nodes = (
        WorkflowNode(node_id=patch_node_id, node_type=WorkflowNodeType.TASK, title="patch"),
        WorkflowNode(node_id=test_node_id, node_type=WorkflowNodeType.TASK, title="test"),
    )
    edges = (
        WorkflowEdge(
            edge_id="patch-to-test",
            from_node_id=patch_node_id,
            to_node_id=test_node_id,
            edge_type=WorkflowEdgeType.DEFAULT,
        ),
    )
    return build_workflow_graph(
        graph_id=graph_id,
        name="Spine patch/test",
        nodes=nodes,
        edges=edges,
        entry_node_ids=(patch_node_id,),
        exit_node_ids=(test_node_id,),
    )


class FlowDispatcher:
    """Drives a workflow run to completion via the S1 executor. Fail-closed."""

    def __init__(self, session: SpineToolExecSession) -> None:
        self.session = session

    def _sandbox_state_hash(self) -> str:
        fn = getattr(self.session.sandbox, "state_hash", None)
        try:
            return fn() if callable(fn) else ""
        except Exception:
            return ""

    def _checkpoint(self, phase: str, node_id: str, run: WorkflowRun) -> FlowDispatchCheckpoint:
        return FlowDispatchCheckpoint(
            checkpoint_id=new_id("fchk"),
            contract_version=FLOW_DISPATCH_CHECKPOINT_VERSION,
            phase=phase,
            node_id=node_id,
            run_step=run.state.step,
            workflow_snapshot_hash=snapshot_workflow_state(run).snapshot_hash,
            sandbox_state_hash=self._sandbox_state_hash(),
            produced_at=now(),
        )

    def dispatch(
        self,
        graph: WorkflowGraph,
        run: WorkflowRun,
        node_tasks: NodeTaskMap,
        lease: ToolExecLease,
        *,
        current_tick: int = 0,
        pause_before: PausePredicate | None = None,
        max_steps: int = 256,
        retry_policy: RetryPolicy | None = None,
    ) -> FlowDispatchResult:
        step_results: list[FlowDispatchStepResult] = []
        checkpoints: list[FlowDispatchCheckpoint] = []
        paused = False
        recovery_proposal: dict | None = None
        # Retry is opt-in: without a policy the dispatcher is single-shot and a
        # failing node fails the run (unchanged behavior). Pass ``retry_policy``
        # (or ``DEFAULT_RETRY_POLICY``) to enable rollback-and-retry.
        policy = retry_policy

        run = self._begin(run)
        for _ in range(max_steps):
            if run.state.lifecycle_status is not WorkflowLifecycleStatus.RUNNING:
                break
            queue = calculate_ready_queue(graph, run)
            if not queue.ready_node_ids:
                break
            node_id = queue.ready_node_ids[0]

            if pause_before is not None and pause_before(node_id, run):
                run = transition_workflow_run(
                    run,
                    lifecycle_transition(
                        WorkflowLifecycleStatus.RUNNING,
                        WorkflowLifecycleStatus.PAUSED,
                        reason=f"paused before {node_id}",
                    ),
                )
                paused = True
                break

            checkpoints.append(self._checkpoint("before", node_id, run))
            run, step, proposal = self._dispatch_node_with_retry(
                graph, run, node_id, node_tasks, lease, current_tick, policy
            )
            step_results.append(step)
            checkpoints.append(self._checkpoint("after", node_id, run))

            if not step.success:
                # A retriable failure that exhausted its budget yields an operator
                # recovery proposal → PAUSE for review. A non-retriable failure
                # (policy/operator) has no proposal → fail closed.
                if proposal is not None:
                    recovery_proposal = proposal
                    run = transition_workflow_run(
                        run,
                        lifecycle_transition(
                            WorkflowLifecycleStatus.RUNNING,
                            WorkflowLifecycleStatus.PAUSED,
                            reason=f"node {node_id} failed; awaiting operator recovery",
                        ),
                    )
                    paused = True
                else:
                    run = transition_workflow_run(
                        run,
                        lifecycle_transition(
                            WorkflowLifecycleStatus.RUNNING,
                            WorkflowLifecycleStatus.FAILED,
                            reason=f"node {node_id} failed",
                        ),
                    )
                break

        run = self._finalize(run, paused)
        return FlowDispatchResult(
            dispatch_id=new_id("fdsp"),
            contract_version=FLOW_DISPATCH_RESULT_VERSION,
            run=run,
            step_results=tuple(step_results),
            checkpoints=tuple(checkpoints),
            lifecycle_status=run.state.lifecycle_status,
            success=run.state.lifecycle_status is WorkflowLifecycleStatus.COMPLETED,
            paused=paused,
            recovery_proposal=recovery_proposal,
        )

    def _dispatch_node_with_retry(
        self,
        graph: WorkflowGraph,
        run: WorkflowRun,
        node_id: str,
        node_tasks: NodeTaskMap,
        lease: ToolExecLease,
        current_tick: int,
        policy: RetryPolicy | None,
    ) -> tuple[WorkflowRun, FlowDispatchStepResult, dict | None]:
        """Dispatch one node, retrying flaky failures within the eligibility budget.

        The retry *decision* is delegated to the sealed recovery read-models
        (``classify_failure`` + ``calculate_retry_eligibility``); the retry
        *execution* — rolling the sandbox back to the pre-node snapshot and
        re-submitting — happens here, in the executor layer. On budget
        exhaustion of a retriable failure an operator ``RecoveryProposal`` is
        returned. Without a ``policy`` the node is dispatched exactly once.
        """
        # No retry policy, or a structural (no-task) node: single-shot dispatch.
        if policy is None or node_tasks.get(node_id) is None:
            run, step = self._dispatch_node(run, node_id, node_tasks, lease, current_tick)
            return run, step, None

        # Move the node to RUNNING once; it stays RUNNING across attempts and
        # only settles to COMPLETED/FAILED at the end (FAILED is terminal, so a
        # retry must not pass through it).
        run = transition_workflow_run(
            run,
            node_transition(node_id, WorkflowNodeState.NOT_STARTED, WorkflowNodeState.READY),
        )
        run = transition_workflow_run(
            run,
            node_transition(node_id, WorkflowNodeState.READY, WorkflowNodeState.RUNNING),
        )

        pre_snapshot = self._snapshot_sandbox()
        attempts: list[ToolExecEvidenceRef] = []
        attempt_count = 0
        evidence = self._submit_task_raw(node_id, node_tasks, lease, current_tick)
        attempt_count += 1
        attempts.append(evidence)

        while not evidence.success:
            # Classify from the observed evidence: an approval/policy block is
            # never retried; a verifier/validation failure is.
            policy_blocked = bool(evidence.blocked_reason)
            assessment = classify_failure(
                target_run_id=run.run_id,
                target_node_id=node_id,
                graph=graph,
                policy_blocked=policy_blocked,
                validation_failed=not policy_blocked,
                detail=evidence.blocked_reason or "validation failure",
            )
            eligibility = calculate_retry_eligibility(
                policy, assessment, attempt_count=attempt_count
            )
            if not eligibility.eligible:
                run = transition_workflow_run(
                    run,
                    node_transition(node_id, WorkflowNodeState.RUNNING,
                                    WorkflowNodeState.FAILED,
                                    reason=f"failed after {attempt_count} attempt(s)"),
                )
                proposal = None
                if not policy_blocked:
                    frame = build_recovery_frame(assessment)
                    proposal = build_recovery_proposal(
                        frame,
                        step_descriptions=(
                            f"review node {node_id} after {attempt_count} failed attempts",
                            "operator decides: adjust inputs, skip, or abort",
                        ),
                        metadata={"attempts": str(attempt_count)},
                    ).to_canonical_dict()
                step = _make_step(node_id, WorkflowNodeState.FAILED, evidence,
                                  attempt_count, attempts)
                return run, step, proposal

            # Roll the sandbox back to the pre-node state and retry (still RUNNING).
            self._rollback_sandbox(pre_snapshot)
            evidence = self._submit_task_raw(node_id, node_tasks, lease, current_tick)
            attempt_count += 1
            attempts.append(evidence)

        run = transition_workflow_run(
            run,
            node_transition(node_id, WorkflowNodeState.RUNNING, WorkflowNodeState.COMPLETED),
        )
        self._release_snapshot(pre_snapshot)
        step = _make_step(node_id, WorkflowNodeState.COMPLETED, evidence,
                          attempt_count, attempts)
        return run, step, None

    def _submit_task_raw(
        self,
        node_id: str,
        node_tasks: NodeTaskMap,
        lease: ToolExecLease,
        current_tick: int,
    ) -> ToolExecEvidenceRef:
        """Submit a node's task and return evidence, without any state transition."""
        tool, args = node_tasks[node_id]
        return self.session.submit_step(tool, args, lease, current_tick=current_tick)

    def _snapshot_sandbox(self) -> str | None:
        fn = getattr(self.session.sandbox, "snapshot", None)
        try:
            return fn() if callable(fn) else None
        except Exception:
            return None

    def _rollback_sandbox(self, snapshot_id: str | None) -> None:
        if snapshot_id is None:
            return
        fn = getattr(self.session.sandbox, "rollback", None)
        try:
            if callable(fn):
                fn(snapshot_id)
        except Exception:
            pass

    def _release_snapshot(self, snapshot_id: str | None) -> None:
        if snapshot_id is None:
            return
        fn = getattr(self.session.sandbox, "release_snapshot", None)
        try:
            if callable(fn):
                fn(snapshot_id)
        except Exception:
            pass

    def _begin(self, run: WorkflowRun) -> WorkflowRun:
        if run.state.lifecycle_status is WorkflowLifecycleStatus.CREATED:
            run = transition_workflow_run(
                run,
                lifecycle_transition(
                    WorkflowLifecycleStatus.CREATED, WorkflowLifecycleStatus.READY
                ),
            )
        if run.state.lifecycle_status is WorkflowLifecycleStatus.READY:
            run = transition_workflow_run(
                run,
                lifecycle_transition(
                    WorkflowLifecycleStatus.READY, WorkflowLifecycleStatus.RUNNING
                ),
            )
        if run.state.lifecycle_status is WorkflowLifecycleStatus.PAUSED:
            run = transition_workflow_run(
                run,
                lifecycle_transition(
                    WorkflowLifecycleStatus.PAUSED,
                    WorkflowLifecycleStatus.RUNNING,
                    reason="resume",
                ),
            )
        return run

    def _finalize(self, run: WorkflowRun, paused: bool) -> WorkflowRun:
        if paused or run.state.lifecycle_status is not WorkflowLifecycleStatus.RUNNING:
            return run
        all_done = all(
            state in (WorkflowNodeState.COMPLETED, WorkflowNodeState.SKIPPED)
            for state in run.state.node_states.values()
        )
        if all_done:
            run = transition_workflow_run(
                run,
                lifecycle_transition(
                    WorkflowLifecycleStatus.RUNNING, WorkflowLifecycleStatus.COMPLETED
                ),
            )
        return run

    def _dispatch_node(
        self,
        run: WorkflowRun,
        node_id: str,
        node_tasks: NodeTaskMap,
        lease: ToolExecLease,
        current_tick: int,
    ) -> tuple[WorkflowRun, FlowDispatchStepResult]:
        # NOT_STARTED -> READY -> RUNNING (recorded state, not execution)
        run = transition_workflow_run(
            run,
            node_transition(node_id, WorkflowNodeState.NOT_STARTED, WorkflowNodeState.READY),
        )
        run = transition_workflow_run(
            run,
            node_transition(node_id, WorkflowNodeState.READY, WorkflowNodeState.RUNNING),
        )

        task = node_tasks.get(node_id)
        if task is None:
            # structural node with no bound task: no-op completion
            run = transition_workflow_run(
                run,
                node_transition(
                    node_id, WorkflowNodeState.RUNNING, WorkflowNodeState.COMPLETED,
                    reason="no task bound; structural passthrough",
                ),
            )
            return run, FlowDispatchStepResult(
                node_id=node_id,
                node_state_after=WorkflowNodeState.COMPLETED,
                exec_evidence=None,
                dispatched=False,
                success=True,
            )

        return self._run_task(run, node_id, node_tasks, lease, current_tick)

    def _run_task(
        self,
        run: WorkflowRun,
        node_id: str,
        node_tasks: NodeTaskMap,
        lease: ToolExecLease,
        current_tick: int,
    ) -> tuple[WorkflowRun, FlowDispatchStepResult]:
        """Submit a node's bound task once (node already in RUNNING)."""
        tool, args = node_tasks[node_id]
        evidence = self.session.submit_step(tool, args, lease, current_tick=current_tick)
        target = (
            WorkflowNodeState.COMPLETED if evidence.success else WorkflowNodeState.FAILED
        )
        run = transition_workflow_run(
            run,
            node_transition(node_id, WorkflowNodeState.RUNNING, target),
        )
        return run, FlowDispatchStepResult(
            node_id=node_id,
            node_state_after=target,
            exec_evidence=evidence,
            dispatched=evidence.available,
            success=evidence.success,
        )


__all__ = [
    "FLOW_DISPATCH_CHECKPOINT_VERSION",
    "FLOW_DISPATCH_RESULT_VERSION",
    "FlowDispatchCheckpoint",
    "FlowDispatchStepResult",
    "FlowDispatchResult",
    "FlowDispatcher",
    "build_patch_test_graph",
    "create_workflow_run",
]
