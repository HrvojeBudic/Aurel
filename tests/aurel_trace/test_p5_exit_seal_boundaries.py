"""P5-TRACE-G boundary proof: seal/handoff modules are pure read-only meta-layers.

ast source-sweeps the two new modules to prove they contain no runtime/execution/
network/filesystem-write fragments, import no runtime/execution/downstream module,
and instantiate no P6/P8/P9 object (provided artifacts are named by string).
"""

from __future__ import annotations

import ast
from pathlib import Path

import agentic_runtime.aurel_trace as aurel_trace_pkg

_DIR = Path(aurel_trace_pkg.__file__).parent

_MODULES = ("p5_seal.py", "p5_handoff.py")

_FORBIDDEN_CALL_FRAGMENTS = (
    "AgenticRuntime",
    "ToolRuntime",
    ".submit(",
    ".dispatch(",
    "trace.append",
    "_append_transition",
    ".rollback(",
    ".write(",
    ".upload(",
    ".post(",
    "subprocess",
    "socket.",
    "os.remove",
    "shutil.",
)

_FORBIDDEN_IMPORT_ROOTS = (
    "runtime",
    "tool_runtime",
    "policy",
    "sandbox",
    "verifier",
    "memory",
    "aurel_exec",
    "aurel_flow",
    "aurel_shell",
    "requests",
    "urllib",
    "socket",
    "subprocess",
)


def _code_without_docstrings(module_name: str) -> str:
    source = (_DIR / module_name).read_text(encoding="utf-8")
    tree = ast.parse(source)
    doc_lines: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(
            node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
        ):
            if ast.get_docstring(node, clean=False) is None:
                continue
            expr = node.body[0]
            for ln in range(expr.lineno, (expr.end_lineno or expr.lineno) + 1):
                doc_lines.add(ln)
    return "\n".join(
        line
        for idx, line in enumerate(source.splitlines(), start=1)
        if idx not in doc_lines
    )


def _import_roots(module_name: str):
    roots: list[str] = []
    for node in ast.walk(ast.parse((_DIR / module_name).read_text(encoding="utf-8"))):
        if isinstance(node, ast.ImportFrom):
            roots.append((node.module or "").split(".")[0])
        elif isinstance(node, ast.Import):
            roots.extend(alias.name.split(".")[0] for alias in node.names)
    return roots


def test_no_side_effect_call_fragments():
    for module_name in _MODULES:
        code = _code_without_docstrings(module_name)
        for fragment in _FORBIDDEN_CALL_FRAGMENTS:
            assert fragment not in code, (
                f"{module_name} code must not contain {fragment!r} — the seal/handoff "
                "layer is a pure read-only meta-layer"
            )


def test_no_forbidden_imports():
    for module_name in _MODULES:
        for root in _import_roots(module_name):
            assert root not in _FORBIDDEN_IMPORT_ROOTS, (
                f"{module_name} must not import {root!r}"
            )


def test_handoff_module_instantiates_no_downstream_object():
    # P6/P8/P9 provided artifacts are referenced by string, never imported/instantiated.
    handoff_src = (_DIR / "p5_handoff.py").read_text(encoding="utf-8")
    # No import of the P5 object classes (they are named as strings only).
    assert "from .evidence_ref import" not in handoff_src
    assert "from .trace_export import" not in handoff_src
    assert "from .persistent_integrity import" not in handoff_src
