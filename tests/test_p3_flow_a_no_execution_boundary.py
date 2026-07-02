from __future__ import annotations

import re
from dataclasses import fields
from pathlib import Path

import agentic_runtime.aurel_flow as aurel_flow
from agentic_runtime.aurel_flow import (
    FORBIDDEN_FLOW_TRUTH_LABELS,
    FlowNoExecutionProof,
    FlowTruthLabel,
    UNAVAILABLE_CAPABILITIES,
    build_flow_runtime_read_model,
    calculate_ready_queue,
    make_scheduler_decision,
)
from agentic_runtime.aurel_flow.demo import build_demo_workflow_graph, run_flow_foundation_demo
from agentic_runtime.aurel_flow.workflow_state import create_workflow_run

_FLOW_PACKAGE_DIR = Path(aurel_flow.__file__).resolve().parent

# Execution-capable machinery that must never appear in the P3-FLOW-A path.
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
)


def _flow_sources() -> dict[str, str]:
    return {
        path.name: path.read_text(encoding="utf-8")
        for path in sorted(_FLOW_PACKAGE_DIR.glob("*.py"))
    }


def test_flow_sources_contain_no_execution_machinery() -> None:
    sources = _flow_sources()

    assert sources, "aurel_flow package sources must be discoverable"
    for filename, source in sources.items():
        for pattern in _FORBIDDEN_SOURCE_PATTERNS:
            assert not re.search(pattern, source), (
                f"{filename} matches forbidden execution pattern {pattern!r}"
            )


def test_scheduler_decision_grants_no_execution_authority() -> None:
    graph = build_demo_workflow_graph()
    run = create_workflow_run(graph)
    decision = make_scheduler_decision(graph, run)
    queue = calculate_ready_queue(graph, run)

    assert decision.is_execution_capability is False
    assert decision.executes_nodes is False
    assert decision.dispatches_work is False
    assert decision.approves_approvals is False
    assert queue.executes_nothing is True
    assert all(node.is_execution_grant is False for node in queue.schedulable_nodes)


def test_scheduling_never_mutates_run_state() -> None:
    graph = build_demo_workflow_graph()
    run = create_workflow_run(graph)
    states_before = dict(run.state.node_states)
    lifecycle_before = run.state.lifecycle_status
    step_before = run.state.step

    make_scheduler_decision(graph, run)
    calculate_ready_queue(graph, run)
    build_flow_runtime_read_model(graph, run)

    assert dict(run.state.node_states) == states_before
    assert run.state.lifecycle_status is lifecycle_before
    assert run.state.step == step_before
    assert run.history == ()


def test_no_execution_proof_is_all_false() -> None:
    proof = FlowNoExecutionProof()

    for proof_field in fields(proof):
        assert getattr(proof, proof_field.name) is False, (
            f"FlowNoExecutionProof.{proof_field.name} must be False"
        )


def test_read_model_claims_no_live_and_no_trace_verified() -> None:
    read_model = run_flow_foundation_demo()

    assert read_model.live is False
    assert read_model.trace_verified is False
    forbidden = {forbidden_label.value for forbidden_label in FORBIDDEN_FLOW_TRUTH_LABELS}
    for label in read_model.truth_labels.values():
        assert label not in forbidden
    for proof_field in fields(read_model.no_execution_proof):
        assert getattr(read_model.no_execution_proof, proof_field.name) is False


def test_execution_availability_is_explicitly_unavailable() -> None:
    capabilities = {entry.capability: entry for entry in UNAVAILABLE_CAPABILITIES}

    execution = capabilities["UNAVAILABLE_EXECUTION"]
    trace = capabilities["UNAVAILABLE_TRACE_VERIFICATION"]

    assert execution.available is False
    assert execution.truth_label is FlowTruthLabel.UNAVAILABLE
    assert "P4 AurelExec" in execution.reason
    assert trace.available is False
    assert "P5 AurelTrace" in trace.reason
    assert all(entry.available is False for entry in capabilities.values())
    assert all(entry.reason for entry in capabilities.values())
