"""P3-FLOW-H no-execution / no-bridge / no-frontend boundary tests.

The H modules must contain no execution, dispatch, runtime.submit bridge,
persistence, or React/frontend/API machinery — structurally, not just by
intent — and no resolver output may claim execution is available.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import agentic_runtime.aurel_flow as aurel_flow
from agentic_runtime.aurel_flow import (
    AutonomyDecisionClass,
    FORBIDDEN_FLOW_TRUTH_LABELS,
    GovernedAutonomyLevel,
    resolve_permission_state,
)

_FLOW_PACKAGE_DIR = Path(aurel_flow.__file__).resolve().parent
_H_MODULES = (
    "flow_autonomy.py",
    "flow_autonomy_scope.py",
    "flow_autonomy_gates.py",
    "flow_autonomy_projection.py",
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
    r"def\s+upgrade_autonomy",
    r"def\s+self_upgrade",
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
    # no new lint/type suppressions in H modules
    r"#\s*type:\s*ignore",
    r"#\s*noqa",
)


def test_h_sources_contain_no_execution_bridge_or_frontend_machinery() -> None:
    for filename in _H_MODULES:
        source = (_FLOW_PACKAGE_DIR / filename).read_text(encoding="utf-8")
        for pattern in _FORBIDDEN_SOURCE_PATTERNS:
            assert not re.search(pattern, source), (
                f"{filename} matches forbidden pattern {pattern!r}"
            )


def test_h_modules_import_only_stdlib_and_package_internals() -> None:
    allowed_absolute = {"__future__", "dataclasses", "enum", "typing"}
    for filename in _H_MODULES:
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


def test_h_source_never_claims_live_or_verified_labels() -> None:
    forbidden_assignments = (
        r"FlowTruthLabel\.LIVE",
        r"FlowTruthLabel\.TRACE_VERIFIED",
        r"EXECUTION_AVAILABLE\s*=\s*True",
        r"LEDGER_WRITTEN\s*=\s*True",
    )
    for filename in _H_MODULES:
        source = (_FLOW_PACKAGE_DIR / filename).read_text(encoding="utf-8")
        for pattern in forbidden_assignments:
            assert not re.search(pattern, source), (
                f"{filename} matches forbidden pattern {pattern!r}"
            )


def test_execution_classes_never_resolve_executable() -> None:
    execution_classes = (
        AutonomyDecisionClass.REQUEST_EXECUTION,
        AutonomyDecisionClass.TOOL_EXECUTION,
        AutonomyDecisionClass.SANDBOX_EXECUTION,
        AutonomyDecisionClass.NETWORK_CALL,
        AutonomyDecisionClass.ROLLBACK_EXECUTION,
    )
    for level in GovernedAutonomyLevel:
        for decision_class in execution_classes:
            resolution = resolve_permission_state(level, decision_class)
            assert resolution.execution_available is False
            assert resolution.runtime_submit_wired is False
            if resolution.permission_state.value not in ("UNAVAILABLE", "ERROR"):
                assert resolution.future_p4_required is True


def test_no_forbidden_truth_labels_in_resolver_outputs() -> None:
    forbidden = {label.value for label in FORBIDDEN_FLOW_TRUTH_LABELS}
    for level in GovernedAutonomyLevel:
        for decision_class in AutonomyDecisionClass:
            resolution = resolve_permission_state(level, decision_class)
            assert resolution.truth_label.value not in forbidden


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
