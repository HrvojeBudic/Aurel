"""P4-EXEC-B first governed read_file demo against the REAL runtime kernel.

The operator-testable path: DEV_FIXTURE candidate -> ADMIT -> lease -> job
-> session -> attempt -> ExecRuntimeBridge -> CommandEnvelope ->
AgenticRuntime.submit() -> ExecutionOutcome -> ExecTraceBinding ->
ExecProjection. The only execution is the kernel's own read_file path.
"""

from __future__ import annotations

from unittest import mock

import pytest

from agentic_runtime import (
    AgentCard,
    AgentClass,
    AuthorityScope,
    RiskLevel,
    build_runtime,
)
from agentic_runtime.aurel_exec import (
    ExecLifecycleState,
    ExecRuntimeBridge,
    ExecTruthLabel,
    ExecutionMode,
    ExecutionOutcomeStatus,
    bind_lease_to_job,
    bind_session_to_job,
    build_dev_fixture_admission_request,
    build_exec_projection,
    build_runtime_bridge_submit_request,
    build_runtime_submit_proof,
    close_execution_session,
    create_exec_job,
    create_execution_attempt,
    decide_admission,
    issue_execution_lease,
    open_execution_session,
)
from agentic_runtime.aurel_flow.types import stable_hash
from agentic_runtime.sandbox import UnsafeLocalSandbox
from tests.conftest import bounded_test_approver

DEMO_PATH = "notes/hello.txt"
DEMO_CONTENT = "hello from the first governed AurelExec submit"


@pytest.fixture
def demo_kernel(tmp_path):
    kernel = build_runtime(
        sandbox=UnsafeLocalSandbox(root=str(tmp_path)),
        approval_gate=bounded_test_approver(),
    )
    kernel.sandbox.write_file(DEMO_PATH, DEMO_CONTENT)
    return kernel


@pytest.fixture
def demo_card():
    return AgentCard.make(
        name="AurelExec Bridge Demo",
        agent_class=AgentClass.EXECUTION,
        mission="first governed read-only submit",
        authority=AuthorityScope(read_paths=["*"], max_risk=RiskLevel.LOW),
        allowed_tools=["read_file"],
    )


def _bound_slice(kernel, path=DEMO_PATH):
    args = {"path": path}
    request = build_dev_fixture_admission_request(
        requested_tool_name="read_file",
        requested_args_hash=stable_hash(args),
    )
    decision = decide_admission(request)
    job = create_exec_job(
        decision,
        source_p3_candidate_ref=request.source_p3_candidate_ref,
        requested_execution_mode=ExecutionMode.TOOL,
        requested_tool_name="read_file",
    )
    lease = issue_execution_lease(
        decision, request, exec_job_id=job.exec_job_id,
        issued_at_tick=1, expires_at_tick=100,
    )
    job = bind_lease_to_job(job, lease)
    session = open_execution_session(
        job, opened_at_tick=2, trace_run_ref=kernel.trace.run_id
    )
    job = bind_session_to_job(job, session)
    attempt, _ = create_execution_attempt(
        job, lease, current_tick=3, session_id=session.session_id
    )
    return decision, job, lease, session, attempt, args


def test_first_read_file_demo_produces_execution_outcome(demo_kernel, demo_card):
    decision, job, lease, session, attempt, args = _bound_slice(demo_kernel)
    request = build_runtime_bridge_submit_request(
        job=job, lease=lease, session=session, attempt=attempt,
        issuer_card_id=demo_card.id,
        requested_tool_name="read_file",
        requested_execution_mode=ExecutionMode.TOOL,
        command_args=tuple(args.items()),
    )
    bridge = ExecRuntimeBridge(demo_kernel.runtime)
    with mock.patch.object(
        demo_kernel.runtime, "submit", wraps=demo_kernel.runtime.submit
    ) as spy:
        execution = bridge.submit_once(
            request, job=job, lease=lease, session=session, attempt=attempt,
            card=demo_card, current_tick=4,
        )
    # AgenticRuntime.submit() was actually called, exactly once
    assert spy.call_count == 1
    assert execution.result.runtime_submit_called is True
    assert execution.result.success is True
    # the runtime really read the file through its own tool path
    assert execution.outcome.result_summary == DEMO_CONTENT
    assert execution.outcome.runtime_status is ExecutionOutcomeStatus.RUNTIME_SUCCESS
    assert execution.outcome.truth_label is ExecTruthLabel.LIVE
    # real trace refs from the kernel's own ledger; bound, never verified
    assert execution.trace_binding.trace_bound is True
    assert execution.trace_binding.runtime_trace_ref.startswith("txn_")
    assert execution.trace_binding.trace_verified is False
    # lifecycle landed honestly
    assert execution.job.lifecycle_state is ExecLifecycleState.SUCCEEDED
    assert execution.attempt.lifecycle_state is ExecLifecycleState.SUCCEEDED
    # submit proof from the real result
    proof = build_runtime_submit_proof(execution.result, request)
    assert proof.agentic_runtime_submit_called is True
    assert proof.submitted_tool == "read_file"
    # session can be closed after the pass
    closed = close_execution_session(execution.session, closed_at_tick=5)
    assert closed.closed_at_tick == 5


def test_demo_projection_shows_the_full_submit_state(demo_kernel, demo_card):
    decision, job, lease, session, attempt, args = _bound_slice(demo_kernel)
    request = build_runtime_bridge_submit_request(
        job=job, lease=lease, session=session, attempt=attempt,
        issuer_card_id=demo_card.id,
        requested_tool_name="read_file",
        requested_execution_mode=ExecutionMode.TOOL,
        command_args=tuple(args.items()),
    )
    execution = ExecRuntimeBridge(demo_kernel.runtime).submit_once(
        request, job=job, lease=lease, session=session, attempt=attempt,
        card=demo_card, current_tick=4,
    )
    projection = build_exec_projection(
        decision, lease=lease, job=execution.job, attempt=execution.attempt,
        session=execution.session, outcome=execution.outcome,
        trace_binding=execution.trace_binding,
    )
    assert projection.runtime_submit_called is True
    assert projection.runtime_submit_available is True
    assert projection.outcome_status is ExecutionOutcomeStatus.RUNTIME_SUCCESS
    assert projection.outcome_summary == DEMO_CONTENT
    assert projection.trace_bound is True
    assert projection.trace_verified_available is False
    assert projection.worker_queue_available is False
    assert ExecTruthLabel.LIVE in projection.truth_labels
    assert ExecTruthLabel.TRACE_BOUND in projection.truth_labels


def test_demo_preserves_real_runtime_failure(demo_kernel, demo_card):
    decision, job, lease, session, attempt, args = _bound_slice(
        demo_kernel, path="notes/missing.txt"
    )
    request = build_runtime_bridge_submit_request(
        job=job, lease=lease, session=session, attempt=attempt,
        issuer_card_id=demo_card.id,
        requested_tool_name="read_file",
        requested_execution_mode=ExecutionMode.TOOL,
        command_args=(("path", "notes/missing.txt"),),
    )
    execution = ExecRuntimeBridge(demo_kernel.runtime).submit_once(
        request, job=job, lease=lease, session=session, attempt=attempt,
        card=demo_card, current_tick=4,
    )
    assert execution.result.runtime_submit_called is True
    assert execution.result.success is False
    assert execution.outcome.runtime_status is ExecutionOutcomeStatus.RUNTIME_FAILURE
    assert "FileNotFoundError" in (execution.outcome.error_message or "")
    assert execution.job.lifecycle_state is ExecLifecycleState.FAILED
