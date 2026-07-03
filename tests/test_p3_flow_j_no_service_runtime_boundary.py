"""P3-FLOW-J no-service-runtime boundary tests.

No J object exposes a live service runtime, and the J modules import only
stdlib contracts plus package internals — no runtime machinery.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import agentic_runtime.aurel_flow as aurel_flow
from agentic_runtime.aurel_flow import (
    FORBIDDEN_FLOW_TRUTH_LABELS,
    RuntimeServiceKind,
    build_compound_runtime_topology,
    create_logical_service_ref,
    create_runtime_service_node,
)

_FLOW_PACKAGE_DIR = Path(aurel_flow.__file__).resolve().parent
_J_MODULES = (
    "flow_compound_topology.py",
    "flow_service_topology.py",
    "flow_interop_topology.py",
    "flow_compound_topology_projection.py",
)

_FORBIDDEN_RUNTIME_PATTERNS = (
    r"\bimport\s+threading\b",
    r"\bimport\s+multiprocessing\b",
    r"\bconcurrent\.futures\b",
    r"\bimport\s+asyncio\b",
    r"\bimport\s+subprocess\b",
    r"\bos\.system\b",
    r"\bos\.spawn",
    r"\bos\.fork\b",
    r"\bpopen\b",
    r"\beval\(",
    r"\bexec\(",
    r"\bopen\(",
    r"\.submit\(",
    r"def\s+run_service",
    r"def\s+start_service",
    r"def\s+spawn_",
    r"def\s+execute_",
    r"def\s+dispatch_",
    r"AgenticRuntime\(",
    r"ApprovalGate\(",
    r"TraceLedger\(",
    # no new lint/type suppressions in J modules
    r"#\s*type:\s*ignore",
    r"#\s*noqa",
)


def test_j_sources_contain_no_service_runtime_machinery() -> None:
    for filename in _J_MODULES:
        source = (_FLOW_PACKAGE_DIR / filename).read_text(encoding="utf-8")
        for pattern in _FORBIDDEN_RUNTIME_PATTERNS:
            assert not re.search(pattern, source), (
                f"{filename} matches forbidden pattern {pattern!r}"
            )


def test_j_modules_import_only_stdlib_contracts_and_package_internals() -> None:
    allowed_absolute = {"__future__", "dataclasses", "enum", "typing"}
    for filename in _J_MODULES:
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


def test_topology_objects_never_claim_service_runtime() -> None:
    node = create_runtime_service_node(
        service_ref=create_logical_service_ref(
            service_kind=RuntimeServiceKind.MODEL_SERVICE,
            logical_name="frontier",
        )
    )
    topology = build_compound_runtime_topology(
        run_id="run-1", service_nodes=(node,)
    )
    assert topology.service_runtime_available is False
    assert node.live_process is False
    assert node.service_ref.live_handle is False
    for obj in (topology, node, node.service_ref):
        assert obj.truth_label not in FORBIDDEN_FLOW_TRUTH_LABELS


def test_j_sources_never_claim_live_or_verified_labels() -> None:
    for filename in _J_MODULES:
        source = (_FLOW_PACKAGE_DIR / filename).read_text(encoding="utf-8")
        assert not re.search(r"FlowTruthLabel\.LIVE", source)
        assert not re.search(r"FlowTruthLabel\.TRACE_VERIFIED", source)
