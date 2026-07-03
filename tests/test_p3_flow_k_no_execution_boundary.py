"""P3-FLOW-K no-execution boundary tests.

The K modules contain no execution, dispatch, runtime.submit, service
runtime, network, or invocation machinery — structurally and by source scan.
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
    build_harness_no_execution_boundary_proof,
)

_FLOW_PACKAGE_DIR = Path(aurel_flow.__file__).resolve().parent
_K_MODULES = (
    "flow_harness_evaluation.py",
    "flow_boundary_probes.py",
    "flow_quality_ops.py",
    "flow_harness_projection.py",
)

_FORBIDDEN_SOURCE_PATTERNS = (
    r"\bimport\s+subprocess\b",
    r"\bimport\s+socket\b",
    r"\bimport\s+requests\b",
    r"\bimport\s+urllib\b",
    r"\bimport\s+httpx\b",
    r"\bimport\s+asyncio\b",
    r"\bimport\s+threading\b",
    r"\bimport\s+multiprocessing\b",
    r"\bimport\s+sqlite3\b",
    r"\bimport\s+pickle\b",
    r"\bos\.system\b",
    r"\bos\.exec",
    r"\bos\.spawn",
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
    r"def\s+execute_",
    r"def\s+dispatch_",
    r"def\s+run_workflow",
    r"spawn_worker",
    r"\bimport\s+fastapi\b",
    r"\bimport\s+flask\b",
    r"\bimport\s+websockets?\b",
    r"</\w+>",
    # no new lint/type suppressions in K modules
    r"#\s*type:\s*ignore",
    r"#\s*noqa",
)


def test_k_sources_contain_no_execution_machinery() -> None:
    for filename in _K_MODULES:
        source = (_FLOW_PACKAGE_DIR / filename).read_text(encoding="utf-8")
        for pattern in _FORBIDDEN_SOURCE_PATTERNS:
            assert not re.search(pattern, source), (
                f"{filename} matches forbidden pattern {pattern!r}"
            )


def test_k_modules_import_only_stdlib_contracts_and_package_internals() -> None:
    allowed_absolute = {"__future__", "dataclasses", "enum", "typing"}
    for filename in _K_MODULES:
        tree = ast.parse(
            (_FLOW_PACKAGE_DIR / filename).read_text(encoding="utf-8")
        )
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


def test_no_execution_proof_is_all_false_and_fail_closed() -> None:
    proof = build_harness_no_execution_boundary_proof()
    for boundary_field in (
        "is_p5_trace_proof",
        "workflow_executed",
        "runtime_submit_wired",
        "dispatch_available",
        "execution_available",
        "service_runtime_available",
        "network_called",
        "model_invoked",
        "tool_invoked",
        "sandbox_executed",
        "trace_written",
        "ledger_written",
        "memory_access_performed",
        "policy_mutated",
        "identity_mutated",
    ):
        assert getattr(proof, boundary_field) is False
        with pytest.raises(AurelFlowValidationError):
            dataclasses.replace(proof, **{boundary_field: True})
