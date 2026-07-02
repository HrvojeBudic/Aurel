"""P3-FLOW-G no-execution / no-authority / no-proof / no-UI-authority tests.

The G modules must contain no retry/repair/recovery/verifier/stop execution,
no runtime.submit bridge, no worker spawning, no external persistence, no
React/frontend/API implementation, and no Trace/Ledger/memory/policy/identity
binding — structurally, not just by intent.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import agentic_runtime.aurel_flow as aurel_flow
from agentic_runtime.aurel_flow import (
    DEFAULT_TARGETED_RECOVERY_POLICY,
    FORBIDDEN_FLOW_TRUTH_LABELS,
    RuntimeFailureKind,
    build_flow_demo_bundle,
    build_monitor_frame,
    build_recovery_budget_state,
    build_retry_storm_guard,
    build_self_healing_projection_envelope,
    classify_runtime_failure,
    create_recovery_budget,
    create_recovery_candidate_envelope,
    create_reliability_control_plane,
    create_runtime_failure_signal,
    select_recovery_candidate,
)

_FLOW_PACKAGE_DIR = Path(aurel_flow.__file__).resolve().parent
_G_MODULES = (
    "flow_reliability_control.py",
    "flow_diagnosis.py",
    "flow_recovery_policy.py",
    "flow_recovery_budget.py",
    "flow_self_healing_projection.py",
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
    # no bridge to submit / approval / trace / ledger / policy / memory /
    # tool / LLM / network / worker spawning.
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
    r"spawn_agent",
    r"spawn_worker",
    r"worker_registry",
    r"WorkerRegistry",
    # no actual retry / repair / recovery / verifier / stop execution
    r"def\s+execute_retry",
    r"def\s+execute_repair",
    r"def\s+execute_recovery",
    r"def\s+execute_rollback",
    r"def\s+execute_verifier",
    r"def\s+execute_stop",
    r"def\s+run_verifier",
    r"def\s+refresh_context",
    r"def\s+retry_now",
    # no React / frontend / API implementation (import/call level, so honest
    # docstring mentions of forbidden surfaces do not false-positive)
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
)


def test_g_sources_contain_no_execution_persistence_or_bridge_machinery() -> None:
    for filename in _G_MODULES:
        source = (_FLOW_PACKAGE_DIR / filename).read_text(encoding="utf-8")
        for pattern in _FORBIDDEN_SOURCE_PATTERNS:
            assert not re.search(pattern, source), (
                f"{filename} matches forbidden pattern {pattern!r}"
            )


def test_g_modules_import_only_stdlib_and_package_internals() -> None:
    allowed_absolute = {"__future__", "dataclasses", "enum", "typing"}
    for filename in _G_MODULES:
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


def test_g_source_never_claims_live_or_verified_labels() -> None:
    forbidden_assignments = (
        r"FlowTruthLabel\.LIVE",
        r"FlowTruthLabel\.TRACE_VERIFIED",
        r"EXECUTION_AVAILABLE\s*=\s*True",
        r"LEDGER_WRITTEN\s*=\s*True",
        r"POLICY_ENFORCED_BY_FLOW",
    )
    for filename in _G_MODULES:
        source = (_FLOW_PACKAGE_DIR / filename).read_text(encoding="utf-8")
        for pattern in forbidden_assignments:
            assert not re.search(pattern, source), (
                f"{filename} matches forbidden pattern {pattern!r}"
            )


def _build_g_layer_outputs():
    bundle = build_flow_demo_bundle()
    plane = create_reliability_control_plane(bundle.run, created_by="boundary-test")
    monitor = build_monitor_frame(bundle.run)
    signal = create_runtime_failure_signal(
        bundle.run,
        failure_kind=RuntimeFailureKind.TOOL_TIMEOUT,
        detail="boundary test",
    )
    classification = classify_runtime_failure(signal)
    selection = select_recovery_candidate(DEFAULT_TARGETED_RECOVERY_POLICY, signal)
    envelope = create_recovery_candidate_envelope(selection)
    budget_state = build_recovery_budget_state(
        create_recovery_budget(run_id=bundle.run.run_id)
    )
    guard = build_retry_storm_guard(
        run_id=bundle.run.run_id, retry_count=0, same_failure_count=0
    )
    projection = build_self_healing_projection_envelope(run_id=bundle.run.run_id)
    return (
        bundle,
        plane,
        monitor,
        signal,
        classification,
        selection,
        envelope,
        budget_state,
        guard,
        projection,
    )


def test_g_layer_construction_does_not_mutate_demo_run() -> None:
    outputs = _build_g_layer_outputs()
    bundle = outputs[0]
    step_before = bundle.run.state.step
    lifecycle_before = bundle.run.state.lifecycle_status
    history_before = len(bundle.run.history)

    _build_g_layer_outputs()

    assert bundle.run.state.step == step_before
    assert bundle.run.state.lifecycle_status is lifecycle_before
    assert len(bundle.run.history) == history_before


def test_no_forbidden_truth_labels_in_g_layer_outputs() -> None:
    forbidden = {label.value for label in FORBIDDEN_FLOW_TRUTH_LABELS}
    (
        _bundle,
        plane,
        monitor,
        signal,
        classification,
        selection,
        envelope,
        budget_state,
        guard,
        projection,
    ) = _build_g_layer_outputs()
    for obj in (
        plane,
        monitor,
        signal,
        classification,
        selection,
        envelope,
        budget_state,
        guard,
        projection,
    ):
        assert obj.truth_label.value not in forbidden


def test_g_layer_chain_never_claims_execution_proof_or_authority() -> None:
    (
        _bundle,
        plane,
        _monitor,
        signal,
        classification,
        selection,
        envelope,
        budget_state,
        guard,
        projection,
    ) = _build_g_layer_outputs()
    assert plane.recovery_executed is False
    assert signal.proof_available is False
    assert classification.proof_available is False
    assert selection.authority_granted is False
    assert envelope.execution_available is False
    assert envelope.recovery_executed is False
    assert budget_state.permission_granted is False
    assert guard.stop_executed is False
    assert projection.ui_authority_granted is False
    assert projection.frontend_implemented is False


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
