from __future__ import annotations

import re
from dataclasses import fields
from pathlib import Path

import agentic_runtime.aurel_flow as aurel_flow
from agentic_runtime.aurel_flow import (
    FlowCliCommandKind,
    FlowCliRequest,
    FlowTruthLabel,
    build_flow_demo_bundle,
    build_flow_state_projection,
    evaluate_flow_base_exit_seal,
    handle_flow_cli_request,
)

_FLOW_PACKAGE_DIR = Path(aurel_flow.__file__).resolve().parent
_PROJECTION_MODULES = (
    "flow_projection.py",
    "flow_timeline.py",
    "flow_wiring.py",
    "flow_protocol.py",
    "flow_observability.py",
    "flow_seal.py",
    "flow_cli.py",
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
    # projection/CLI/seal modules must not bind to trace/ledger/memory/policy
    # runtimes, sandbox, tools, or the live runtime kernel
    r"from\s+agentic_runtime\.trace\b",
    r"from\s+\.\.trace\b",
    r"from\s+agentic_runtime\.memory\b",
    r"from\s+agentic_runtime\.policy\b",
    r"from\s+agentic_runtime\.sandbox\b",
    r"from\s+agentic_runtime\.tools\b",
    r"from\s+agentic_runtime\.runtime\b",
    r"from\s+\.\.runtime\b",
)


def test_projection_sources_contain_no_execution_or_trace_machinery() -> None:
    for filename in _PROJECTION_MODULES:
        source = (_FLOW_PACKAGE_DIR / filename).read_text(encoding="utf-8")
        for pattern in _FORBIDDEN_SOURCE_PATTERNS:
            assert not re.search(pattern, source), (
                f"{filename} matches forbidden pattern {pattern!r}"
            )


def test_projection_does_not_mutate_source_run() -> None:
    bundle = build_flow_demo_bundle()
    step_before = bundle.run.state.step
    lifecycle_before = bundle.run.state.lifecycle_status
    history_before = len(bundle.run.history)

    build_flow_state_projection(bundle.graph, bundle.run)
    for kind in FlowCliCommandKind:
        handle_flow_cli_request(FlowCliRequest(command_kind=kind))
    evaluate_flow_base_exit_seal(docs_reports_present=True)

    assert bundle.run.state.step == step_before
    assert bundle.run.state.lifecycle_status is lifecycle_before
    assert len(bundle.run.history) == history_before


def test_seal_and_cli_claim_no_execution() -> None:
    result = evaluate_flow_base_exit_seal(docs_reports_present=True)
    response = handle_flow_cli_request(
        FlowCliRequest(command_kind=FlowCliCommandKind.SEAL)
    )

    assert result.seal.boundary.execution_available is False
    assert result.seal.boundary.runtime_submit_wired is False
    for effect_field in fields(response.side_effects):
        assert getattr(response.side_effects, effect_field.name) is False


def test_no_forbidden_truth_labels_in_projection_outputs() -> None:
    bundle = build_flow_demo_bundle()
    projection = build_flow_state_projection(bundle.graph, bundle.run)
    forbidden = {FlowTruthLabel.LIVE.value, FlowTruthLabel.TRACE_VERIFIED.value}

    for label in projection.truth_labels.values():
        assert label not in forbidden
    result = evaluate_flow_base_exit_seal(docs_reports_present=True)
    assert result.seal.truth_label.value not in forbidden


def test_c_modules_do_not_import_llm_or_tool_layers() -> None:
    # closed-world import check via AST: only intra-package relative imports
    # and a small stdlib allow-list are permitted in the C modules
    import ast

    allowed_absolute = {"__future__", "dataclasses", "enum", "pathlib", "typing"}
    for filename in _PROJECTION_MODULES:
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


def test_package_wide_source_scan_still_holds() -> None:
    # every module in the package, including A/B, stays execution-free
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
