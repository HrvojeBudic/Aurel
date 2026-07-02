"""P3-FLOW-F no-execution / no-persistence / no-proof / no-UI-authority tests.

The F modules must contain no replay/rollback/revert execution, no worker
fork, no external persistence (database/event store/file), no runtime.submit
bridge, no React/frontend/API implementation, and no Trace/Ledger/memory/
policy/identity binding — structurally, not just by intent.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import agentic_runtime.aurel_flow as aurel_flow
from agentic_runtime.aurel_flow import (
    FORBIDDEN_FLOW_TRUTH_LABELS,
    RuntimeCheckpointKind,
    RuntimeCheckpointReason,
    build_checkpoint_state_envelope,
    build_flow_demo_bundle,
    build_reversible_state_projection_envelope,
    build_runtime_state_diff_summary,
    create_recovery_checkpoint_requirement,
    create_runtime_checkpoint_ref,
    create_runtime_revert_candidate,
)

_FLOW_PACKAGE_DIR = Path(aurel_flow.__file__).resolve().parent
_F_MODULES = (
    "flow_checkpoint.py",
    "flow_replay.py",
    "flow_reversible_state.py",
    "flow_reversible_projection.py",
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
    # no actual replay / rollback / revert / recovery execution
    r"def\s+execute_replay",
    r"def\s+execute_rollback",
    r"def\s+execute_revert",
    r"def\s+execute_recovery",
    r"def\s+run_replay",
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


def test_f_sources_contain_no_execution_persistence_or_bridge_machinery() -> None:
    for filename in _F_MODULES:
        source = (_FLOW_PACKAGE_DIR / filename).read_text(encoding="utf-8")
        for pattern in _FORBIDDEN_SOURCE_PATTERNS:
            assert not re.search(pattern, source), (
                f"{filename} matches forbidden pattern {pattern!r}"
            )


def test_f_modules_import_only_stdlib_and_package_internals() -> None:
    allowed_absolute = {"__future__", "dataclasses", "enum", "typing"}
    for filename in _F_MODULES:
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


def test_f_source_never_claims_live_or_verified_labels() -> None:
    forbidden_assignments = (
        r"FlowTruthLabel\.LIVE",
        r"FlowTruthLabel\.TRACE_VERIFIED",
        r"CheckpointTruthLabel\.LIVE",
        r"CheckpointTruthLabel\.TRACE_VERIFIED",
        r"EXECUTION_AVAILABLE\s*=\s*True",
        r"LEDGER_WRITTEN\s*=\s*True",
        r"POLICY_ENFORCED_BY_FLOW",
    )
    for filename in _F_MODULES:
        source = (_FLOW_PACKAGE_DIR / filename).read_text(encoding="utf-8")
        for pattern in forbidden_assignments:
            assert not re.search(pattern, source), (
                f"{filename} matches forbidden pattern {pattern!r}"
            )


def _build_f_layer_outputs():
    bundle = build_flow_demo_bundle()
    ref = create_runtime_checkpoint_ref(
        bundle.run,
        checkpoint_kind=RuntimeCheckpointKind.BEFORE_RECOVERY,
        checkpoint_reason=RuntimeCheckpointReason.RECOVERY_PREPARATION,
        created_by="boundary-test",
    )
    envelope = build_checkpoint_state_envelope(bundle.run, ref)
    diff = build_runtime_state_diff_summary(
        left_envelope=envelope, right_envelope=envelope
    )
    revert = create_runtime_revert_candidate(target_checkpoint=ref)
    requirement = create_recovery_checkpoint_requirement(run_id=bundle.run.run_id)
    projection = build_reversible_state_projection_envelope(
        run_id=bundle.run.run_id,
        checkpoint_refs=(ref,),
        revert_candidates=(revert,),
        runtime_diffs=(diff,),
        recovery_checkpoint_requirements=(requirement,),
    )
    return bundle, ref, envelope, diff, revert, requirement, projection


def test_f_layer_construction_does_not_mutate_demo_run() -> None:
    outputs = _build_f_layer_outputs()
    bundle = outputs[0]
    step_before = bundle.run.state.step
    lifecycle_before = bundle.run.state.lifecycle_status
    history_before = len(bundle.run.history)

    _build_f_layer_outputs()

    assert bundle.run.state.step == step_before
    assert bundle.run.state.lifecycle_status is lifecycle_before
    assert len(bundle.run.history) == history_before


def test_no_forbidden_truth_labels_in_f_layer_outputs() -> None:
    forbidden = {label.value for label in FORBIDDEN_FLOW_TRUTH_LABELS}
    (_bundle, ref, envelope, diff, revert, requirement, projection) = (
        _build_f_layer_outputs()
    )
    for obj in (ref, envelope, diff, revert, requirement, projection):
        assert obj.truth_label.value not in forbidden


def test_f_layer_identity_diff_is_empty_and_proves_nothing() -> None:
    (_bundle, _ref, _envelope, diff, _revert, _requirement, _projection) = (
        _build_f_layer_outputs()
    )
    assert diff.added_node_ids == ()
    assert diff.removed_node_ids == ()
    assert diff.changed_node_ids == ()
    assert diff.proof_available is False
    assert diff.trace_verified is False


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
