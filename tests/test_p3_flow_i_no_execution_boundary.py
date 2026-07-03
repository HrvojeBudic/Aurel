"""P3-FLOW-I no-execution / no-bridge / no-frontend boundary tests.

The I modules must contain no execution, worker, network, persistence,
Trace/Ledger, or React/frontend/API machinery — structurally, not just by
intent.
"""

from __future__ import annotations

import ast
import dataclasses
import re
from pathlib import Path

import pytest

import agentic_runtime.aurel_flow as aurel_flow
from agentic_runtime.aurel_flow import (
    AurelFlowValidationError,
    FORBIDDEN_FLOW_TRUTH_LABELS,
    SchedulingIntentKind,
    SchedulingIntentReason,
    WorkflowAtomicUnitKind,
    build_no_execution_boundary_proof,
    classify_dispatchability,
    create_ready_state_frame,
    create_scheduling_intent,
    create_workflow_atomic_unit,
)

_FLOW_PACKAGE_DIR = Path(aurel_flow.__file__).resolve().parent
_I_MODULES = (
    "flow_scheduling_intent.py",
    "flow_dispatchability.py",
    "flow_resource_prediction.py",
    "flow_scheduling_projection.py",
)

_FORBIDDEN_SOURCE_PATTERNS = (
    r"\bimport\s+subprocess\b",
    r"\bfrom\s+subprocess\b",
    r"\bimport\s+socket\b",
    r"\bimport\s+requests\b",
    r"\bimport\s+urllib\b",
    r"\bimport\s+httpx\b",
    r"\bimport\s+asyncio\b",
    r"\bimport\s+sqlite3\b",
    r"\bimport\s+pickle\b",
    r"\bimport\s+shelve\b",
    r"\bos\.system\b",
    r"\bos\.exec",
    r"\bos\.spawn",
    r"\bos\.fork\b",
    r"\bpopen\b",
    r"\beval\(",
    r"\bexec\(",
    r"\bopen\(",
    r"\.submit\(",
    r"AgenticRuntime\(",
    r"ApprovalGate\(",
    r"TraceLedger\(",
    r"from\s+agentic_runtime\.trace\b",
    r"from\s+agentic_runtime\.memory\b",
    r"from\s+agentic_runtime\.policy\b",
    r"from\s+agentic_runtime\.sandbox\b",
    r"from\s+agentic_runtime\.tools\b",
    r"from\s+agentic_runtime\.runtime\b",
    r"from\s+\.\.runtime\b",
    r"spawn_agent",
    r"spawn_worker",
    r"def\s+execute_",
    r"def\s+dispatch_",
    r"def\s+allocate_",
    r"def\s+reserve_",
    r"def\s+bill_",
    r"def\s+consume_",
    r"\bimport\s+react\b",
    r"\bimport\s+fastapi\b",
    r"\bfrom\s+fastapi\b",
    r"\bimport\s+flask\b",
    r"\bfrom\s+flask\b",
    r"\bimport\s+django\b",
    r"\bimport\s+websockets?\b",
    r"\buseState\(",
    r"\bReactDOM\b",
    r"</\w+>",
    # no new lint/type suppressions in I modules
    r"#\s*type:\s*ignore",
    r"#\s*noqa",
)


def test_i_sources_contain_no_execution_bridge_or_frontend_machinery() -> None:
    for filename in _I_MODULES:
        source = (_FLOW_PACKAGE_DIR / filename).read_text(encoding="utf-8")
        for pattern in _FORBIDDEN_SOURCE_PATTERNS:
            assert not re.search(pattern, source), (
                f"{filename} matches forbidden pattern {pattern!r}"
            )


def test_i_modules_import_only_stdlib_and_package_internals() -> None:
    allowed_absolute = {"__future__", "dataclasses", "enum", "typing"}
    for filename in _I_MODULES:
        source = (_FLOW_PACKAGE_DIR / filename).read_text(encoding="utf-8")
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.level > 0:  # relative import inside aurel_flow
                    continue
                assert node.module in allowed_absolute, (
                    f"{filename}: unexpected import from {node.module!r}"
                )
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    assert alias.name in allowed_absolute, (
                        f"{filename}: unexpected import {alias.name!r}"
                    )


def test_i_source_never_claims_live_or_verified_labels() -> None:
    forbidden_assignments = (
        r"FlowTruthLabel\.LIVE",
        r"FlowTruthLabel\.TRACE_VERIFIED",
        r"EXECUTION_AVAILABLE\s*=\s*True",
        r"LEDGER_WRITTEN\s*=\s*True",
    )
    for filename in _I_MODULES:
        source = (_FLOW_PACKAGE_DIR / filename).read_text(encoding="utf-8")
        for pattern in forbidden_assignments:
            assert not re.search(pattern, source), (
                f"{filename} matches forbidden pattern {pattern!r}"
            )


def test_no_execution_proof_is_all_false_and_fail_closed() -> None:
    proof = build_no_execution_boundary_proof()
    for boundary_field in (
        "is_p5_trace_proof",
        "execution_available",
        "worker_spawned",
        "parallel_execution_available",
        "model_invoked",
        "tool_invoked",
        "sandbox_executed",
        "subprocess_spawned",
        "network_called",
        "data_access_performed",
        "memory_access_performed",
        "trace_written",
        "ledger_written",
        "policy_mutated",
        "identity_mutated",
    ):
        assert getattr(proof, boundary_field) is False
        with pytest.raises(AurelFlowValidationError):
            dataclasses.replace(proof, **{boundary_field: True})


def test_i_objects_never_carry_forbidden_truth_labels() -> None:
    unit = create_workflow_atomic_unit(
        run_id="run-1",
        unit_kind=WorkflowAtomicUnitKind.SINGLE_NODE,
        node_ids=("n1",),
    )
    intent = create_scheduling_intent(
        unit=unit,
        intent_kind=SchedulingIntentKind.SCHEDULE_READY_NODE_CANDIDATE,
        intent_reason=SchedulingIntentReason.DEPENDENCIES_SATISFIED,
    )
    dispatchability = classify_dispatchability(
        create_ready_state_frame(
            unit=unit, dependency_ready=True, state_ready=True
        )
    )
    for obj in (unit, intent, dispatchability):
        assert obj.truth_label not in FORBIDDEN_FLOW_TRUTH_LABELS


def test_execution_stays_unavailable_across_the_vertical_slice() -> None:
    unit = create_workflow_atomic_unit(
        run_id="run-1",
        unit_kind=WorkflowAtomicUnitKind.SINGLE_NODE,
        node_ids=("n1",),
    )
    intent = create_scheduling_intent(
        unit=unit,
        intent_kind=SchedulingIntentKind.SCHEDULE_READY_NODE_CANDIDATE,
        intent_reason=SchedulingIntentReason.DEPENDENCIES_SATISFIED,
    )
    dispatchability = classify_dispatchability(
        create_ready_state_frame(
            unit=unit, dependency_ready=True, state_ready=True
        )
    )
    for obj in (unit, intent, dispatchability):
        assert obj.execution_available is False
