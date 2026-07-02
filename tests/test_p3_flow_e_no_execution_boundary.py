"""P3-FLOW-E no-execution / no-authority / no-proof boundary tests.

The E modules must contain no runtime.submit bridge, no agent-spawning, no
verifier/aggregator execution, no live worker/network/tool/LLM machinery,
and no Trace/Ledger/memory/policy/identity binding — structurally, not just
by intent.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import agentic_runtime.aurel_flow as aurel_flow
from agentic_runtime.aurel_flow import (
    FORBIDDEN_FLOW_TRUTH_LABELS,
    GraphPlasticityMode,
    GraphRealizationReason,
    build_diversity_risk_read_model,
    build_flow_demo_bundle,
    build_graph_plasticity_boundary,
    build_runtime_graph_revision_read_model,
    build_runtime_topology_snapshot,
    build_topology_risk_read_model,
    build_topology_snapshot_read_model,
    create_graph_plasticity_policy,
    create_workflow_template,
    realize_runtime_graph,
)

_FLOW_PACKAGE_DIR = Path(aurel_flow.__file__).resolve().parent
_E_MODULES = (
    "flow_dynamic_graph.py",
    "flow_topology.py",
    "flow_graph_revision.py",
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
    # no bridge to submit / approval / trace / ledger / policy / memory /
    # tool / LLM / network / agent spawning.
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
    r"worker_registry",
    r"WorkerRegistry",
    r"run_verifier",
    r"execute_verifier",
    r"run_aggregator",
    r"execute_aggregator",
)


def test_e_sources_contain_no_execution_or_bridge_machinery() -> None:
    for filename in _E_MODULES:
        source = (_FLOW_PACKAGE_DIR / filename).read_text(encoding="utf-8")
        for pattern in _FORBIDDEN_SOURCE_PATTERNS:
            assert not re.search(pattern, source), (
                f"{filename} matches forbidden pattern {pattern!r}"
            )


def test_e_modules_import_only_stdlib_and_package_internals() -> None:
    allowed_absolute = {"__future__", "dataclasses", "enum", "typing"}
    for filename in _E_MODULES:
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


def test_e_source_never_claims_live_or_verified_labels() -> None:
    forbidden_assignments = (
        r"FlowTruthLabel\.LIVE",
        r"FlowTruthLabel\.TRACE_VERIFIED",
        r"EXECUTION_AVAILABLE\s*=\s*True",
        r"LEDGER_WRITTEN",
        r"POLICY_ENFORCED_BY_FLOW",
    )
    for filename in _E_MODULES:
        source = (_FLOW_PACKAGE_DIR / filename).read_text(encoding="utf-8")
        for pattern in forbidden_assignments:
            assert not re.search(pattern, source), (
                f"{filename} matches forbidden pattern {pattern!r}"
            )


def _build_e_layer_outputs():
    bundle = build_flow_demo_bundle()
    template = create_workflow_template(bundle.graph)
    realized = realize_runtime_graph(
        template=template, run=bundle.run, realization_reason=GraphRealizationReason.RUN_CREATED
    )
    snapshot = build_runtime_topology_snapshot(
        realized_graph=realized, graph=bundle.graph, run=bundle.run
    )
    snapshot_read_model = build_topology_snapshot_read_model(snapshot)
    risk_read_model = build_topology_risk_read_model(snapshot=snapshot)
    diversity_read_model = build_diversity_risk_read_model()
    policy = create_graph_plasticity_policy(
        run_id=bundle.run.run_id, mode=GraphPlasticityMode.STATIC_LOCKED
    )
    boundary = build_graph_plasticity_boundary(policy)
    revision_read_model = build_runtime_graph_revision_read_model()
    return (
        bundle,
        template,
        realized,
        snapshot,
        snapshot_read_model,
        risk_read_model,
        diversity_read_model,
        boundary,
        revision_read_model,
    )


def test_e_layer_construction_does_not_mutate_demo_run() -> None:
    outputs = _build_e_layer_outputs()
    bundle = outputs[0]
    step_before = bundle.run.state.step
    lifecycle_before = bundle.run.state.lifecycle_status
    history_before = len(bundle.run.history)

    _build_e_layer_outputs()

    assert bundle.run.state.step == step_before
    assert bundle.run.state.lifecycle_status is lifecycle_before
    assert len(bundle.run.history) == history_before


def test_no_forbidden_truth_labels_in_e_layer_outputs() -> None:
    forbidden = {label.value for label in FORBIDDEN_FLOW_TRUTH_LABELS}
    (
        _bundle,
        template,
        realized,
        snapshot,
        snapshot_read_model,
        risk_read_model,
        diversity_read_model,
        boundary,
        revision_read_model,
    ) = _build_e_layer_outputs()
    for obj in (
        template,
        realized,
        snapshot,
        snapshot_read_model,
        risk_read_model,
        diversity_read_model,
        revision_read_model,
    ):
        assert obj.truth_label.value not in forbidden


def test_static_locked_plasticity_boundary_blocks_revision() -> None:
    (*_rest, boundary, _revision_read_model) = _build_e_layer_outputs()
    assert boundary.revision_blocked is True
    assert boundary.grants_execution_authority is False


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
