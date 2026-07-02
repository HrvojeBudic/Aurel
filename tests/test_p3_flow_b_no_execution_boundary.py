from __future__ import annotations

import re
from dataclasses import fields
from pathlib import Path

import agentic_runtime.aurel_flow as aurel_flow
from agentic_runtime.aurel_flow import (
    BEHAVIOR_UNAVAILABLE_CAPABILITIES,
    FlowTruthLabel,
    RuntimeBehaviorNoExecutionProof,
    WorkflowLifecycleStatus,
)
from agentic_runtime.aurel_flow.demo import run_runtime_behavior_demo
from agentic_runtime.aurel_flow.read_model import FlowNoExecutionProof

_FLOW_PACKAGE_DIR = Path(aurel_flow.__file__).resolve().parent
_BEHAVIOR_MODULES = (
    "runtime_events.py",
    "state_commitment.py",
    "pause_resume.py",
    "recovery.py",
    "runtime_behavior_read_model.py",
)

_FORBIDDEN_SOURCE_PATTERNS = (
    r"\bimport\s+subprocess\b",
    r"\bfrom\s+subprocess\b",
    r"\bimport\s+socket\b",
    r"\bfrom\s+socket\b",
    r"\bimport\s+requests\b",
    r"\bimport\s+urllib\b",
    r"\bfrom\s+urllib\b",
    r"\bimport\s+httpx\b",
    r"\bimport\s+asyncio\b",
    r"\bos\.system\b",
    r"\bos\.exec",
    r"\bos\.spawn",
    r"\bpopen\b",
    r"\beval\(",
    r"\bexec\(",
    # behavior modules must not bind to trace/ledger/memory/policy runtimes
    r"from\s+agentic_runtime\.trace\b",
    r"from\s+\.\.trace\b",
    r"from\s+agentic_runtime\.memory\b",
    r"from\s+agentic_runtime\.policy\b",
    r"from\s+agentic_runtime\.sandbox\b",
    r"from\s+agentic_runtime\.tools\b",
)


def test_behavior_sources_contain_no_execution_or_trace_machinery() -> None:
    for filename in _BEHAVIOR_MODULES:
        source = (_FLOW_PACKAGE_DIR / filename).read_text(encoding="utf-8")
        for pattern in _FORBIDDEN_SOURCE_PATTERNS:
            assert not re.search(pattern, source), (
                f"{filename} matches forbidden pattern {pattern!r}"
            )


def test_behavior_no_execution_proof_is_all_false() -> None:
    proof = RuntimeBehaviorNoExecutionProof(foundation=FlowNoExecutionProof())

    for proof_field in fields(proof):
        value = getattr(proof, proof_field.name)
        if proof_field.name == "foundation":
            for inner_field in fields(value):
                assert getattr(value, inner_field.name) is False
        else:
            assert value is False, f"{proof_field.name} must be False"


def test_demo_behavior_loop_claims_no_execution_or_trace() -> None:
    read_model = run_runtime_behavior_demo()

    assert read_model.execution_available is False
    assert read_model.trace_verified is False
    assert read_model.ledger_written is False
    assert read_model.global_trace_written is False
    assert read_model.trace_boundary.is_trace_event is False
    assert read_model.trace_boundary.can_claim_trace_verified is False

    proof = read_model.no_execution_proof
    assert proof.retry_executed is False
    assert proof.recovery_executed is False
    assert proof.rollback_executed is False
    assert proof.resume_executed_node is False
    assert proof.operator_signal_granted_authority is False
    assert proof.responsibility_authority_transferred is False
    assert proof.runtime_event_wrote_trace is False
    assert proof.runtime_event_wrote_ledger is False
    assert proof.state_commitment_wrote_ledger is False


def test_no_forbidden_truth_labels_in_behavior_read_model() -> None:
    read_model = run_runtime_behavior_demo()
    forbidden = {FlowTruthLabel.LIVE.value, FlowTruthLabel.TRACE_VERIFIED.value}

    for label in read_model.truth_labels.values():
        assert label not in forbidden
    for event in read_model.event_stream_snapshot.event_ids:
        assert event  # events exist without any trace claim
    for signal in read_model.operator_decision_signals:
        assert signal.authority_granted is False
        assert signal.execution_permission_granted is False
    for frame in read_model.responsibility_transfer_frames:
        assert frame.authority_transferred is False
    for commitment in read_model.state_commitments:
        assert commitment.ledger_written is False
        assert commitment.external_side_effect is False


def test_behavior_unavailable_capabilities_cover_authority_and_ledger() -> None:
    capabilities = {entry.capability: entry for entry in BEHAVIOR_UNAVAILABLE_CAPABILITIES}

    assert "UNAVAILABLE_EXECUTION" in capabilities
    assert "UNAVAILABLE_TRACE_VERIFICATION" in capabilities
    assert "UNAVAILABLE_AUTHORITY" in capabilities
    assert "UNAVAILABLE_LEDGER" in capabilities
    assert all(entry.available is False for entry in capabilities.values())
    assert "P9 Custos" in capabilities["UNAVAILABLE_AUTHORITY"].reason
    assert "P5 AurelTrace" in capabilities["UNAVAILABLE_LEDGER"].reason


def test_behavior_helpers_do_not_mutate_input_runs() -> None:
    from agentic_runtime.aurel_flow import (
        OperatorDecisionKind,
        WorkflowPauseReason,
        create_operator_decision_signal,
        create_workflow_run,
        lifecycle_transition,
        pause_workflow_run,
        transition_workflow_run,
    )
    from agentic_runtime.aurel_flow.demo import build_demo_workflow_graph

    run = create_workflow_run(build_demo_workflow_graph(), run_key="immutable-check")
    run = transition_workflow_run(
        run,
        lifecycle_transition(WorkflowLifecycleStatus.CREATED, WorkflowLifecycleStatus.READY),
    )
    run = transition_workflow_run(
        run,
        lifecycle_transition(WorkflowLifecycleStatus.READY, WorkflowLifecycleStatus.RUNNING),
    )
    step_before = run.state.step

    pause_workflow_run(run, pause_reason=WorkflowPauseReason.WAITING_OPERATOR)
    create_operator_decision_signal(
        operator_id="op", decision_kind=OperatorDecisionKind.HOLD, target_run_id=run.run_id
    )

    assert run.state.step == step_before
    assert run.state.lifecycle_status is WorkflowLifecycleStatus.RUNNING
