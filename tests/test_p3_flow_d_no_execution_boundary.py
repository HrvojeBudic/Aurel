"""P3-FLOW-D no-execution / no-authority / no-proof boundary tests.

The D modules must contain no runtime.submit bridge, no ApprovalGate/HITL
bridge, no tool/LLM/subprocess/network/sandbox execution, and no Trace/
Ledger/memory/policy/identity binding — structurally, not just by intent.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import agentic_runtime.aurel_flow as aurel_flow
from agentic_runtime.aurel_flow import (
    FORBIDDEN_FLOW_TRUTH_LABELS,
    build_boundary_truth_read_model,
    build_flow_demo_bundle,
    build_reliability_control_plane_boundary,
    build_submit_compatibility_read_model,
)

_FLOW_PACKAGE_DIR = Path(aurel_flow.__file__).resolve().parent
_D_MODULES = (
    "flow_boundary.py",
    "flow_operator_review.py",
    "flow_pause_hooks.py",
    "flow_proof_expectation.py",
)

_FORBIDDEN_SOURCE_PATTERNS = (
    r"\bimport\s+subprocess\b",
    r"\bfrom\s+subprocess\b",
    r"\bimport\s+socket\b",
    r"\bimport\s+requests\b",
    r"\bimport\s+urllib\b",
    r"\bimport\s+httpx\b",
    r"\bimport\s+asyncio\b",
    r"\bos\.system\b",
    r"\bos\.exec",
    r"\bos\.spawn",
    r"\bpopen\b",
    r"\beval\(",
    r"\bexec\(",
    # no bridge to submit / approval / trace / ledger / policy / memory.
    # descriptive mentions (e.g. submit_target strings) are legal; calls and
    # imports are not — call forms here, import forms in the AST test below
    r"\.submit\(",
    r"AgenticRuntime\(",
    r"ApprovalGate\(",
    r"TraceLedger\(",
    r"import\s+.*AgenticRuntime",
    r"import\s+.*ApprovalGate",
    r"import\s+.*TraceLedger",
    r"from\s+agentic_runtime\.trace\b",
    r"from\s+agentic_runtime\.memory\b",
    r"from\s+agentic_runtime\.policy\b",
    r"from\s+agentic_runtime\.sandbox\b",
    r"from\s+agentic_runtime\.tools\b",
    r"from\s+agentic_runtime\.runtime\b",
    r"from\s+\.\.runtime\b",
)


def test_d_sources_contain_no_execution_or_bridge_machinery() -> None:
    for filename in _D_MODULES:
        source = (_FLOW_PACKAGE_DIR / filename).read_text(encoding="utf-8")
        for pattern in _FORBIDDEN_SOURCE_PATTERNS:
            assert not re.search(pattern, source), (
                f"{filename} matches forbidden pattern {pattern!r}"
            )


def test_d_modules_import_only_stdlib_and_package_internals() -> None:
    allowed_absolute = {"__future__", "dataclasses", "enum", "typing"}
    for filename in _D_MODULES:
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


def test_boundary_builders_do_not_mutate_demo_run() -> None:
    bundle = build_flow_demo_bundle()
    step_before = bundle.run.state.step
    lifecycle_before = bundle.run.state.lifecycle_status
    history_before = len(bundle.run.history)

    build_submit_compatibility_read_model()
    build_reliability_control_plane_boundary()
    build_boundary_truth_read_model(
        proposals=(), permission_requests=(), execution_requests=(),
        proof_expectations=(),
    )

    assert bundle.run.state.step == step_before
    assert bundle.run.state.lifecycle_status is lifecycle_before
    assert len(bundle.run.history) == history_before


def test_no_forbidden_truth_labels_in_boundary_outputs() -> None:
    forbidden = {label.value for label in FORBIDDEN_FLOW_TRUTH_LABELS}
    outputs = (
        build_submit_compatibility_read_model(),
        build_reliability_control_plane_boundary(),
        build_boundary_truth_read_model(
            proposals=(), permission_requests=(), execution_requests=(),
            proof_expectations=(),
        ),
    )
    for obj in outputs:
        assert obj.truth_label.value not in forbidden


def test_d_source_never_claims_live_or_verified_labels() -> None:
    # the D modules never assign LIVE / TRACE_VERIFIED / EXECUTION_AVAILABLE
    forbidden_assignments = (
        r"FlowTruthLabel\.LIVE",
        r"FlowTruthLabel\.TRACE_VERIFIED",
        r"EXECUTION_AVAILABLE",
        r"LEDGER_WRITTEN",
        r"POLICY_ENFORCED_BY_FLOW",
    )
    for filename in _D_MODULES:
        source = (_FLOW_PACKAGE_DIR / filename).read_text(encoding="utf-8")
        for pattern in forbidden_assignments:
            assert not re.search(pattern, source), (
                f"{filename} matches forbidden pattern {pattern!r}"
            )


def test_package_wide_execution_scan_still_holds() -> None:
    execution_patterns = (
        r"\bimport\s+subprocess\b",
        r"\bimport\s+socket\b",
        r"\bos\.system\b",
        r"\bpopen\b",
    )
    for path in sorted(_FLOW_PACKAGE_DIR.glob("*.py")):
        source = path.read_text(encoding="utf-8")
        for pattern in execution_patterns:
            assert not re.search(pattern, source), (
                f"{path.name} matches forbidden pattern {pattern!r}"
            )
