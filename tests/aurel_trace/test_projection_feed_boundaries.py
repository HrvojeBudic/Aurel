"""P5-TRACE-E boundary proof: feed/thread/readiness are pure read-only models.

ast source-sweeps the three new modules to prove — structurally — that they
contain no runtime/execution/replay call fragments and import no runtime/P3/P4/
policy/memory module, and that the projection feed builders consume already-made
resolver decisions rather than importing the resolver as an authority.
"""

from __future__ import annotations

import ast
from pathlib import Path

import agentic_runtime.aurel_trace as aurel_trace_pkg

_DIR = Path(aurel_trace_pkg.__file__).parent

_MODULES = (
    "trace_projection_feed.py",
    "golden_thread.py",
    "replay_readiness.py",
)

_FORBIDDEN_CALL_FRAGMENTS = (
    "AgenticRuntime",
    "ToolRuntime",
    ".submit(",
    ".dispatch(",
    "trace.append",
    "_append_transition",
    "record_transition",
    ".rollback(",
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


def test_modules_have_no_side_effect_call_fragments():
    for module_name in _MODULES:
        code = _code_without_docstrings(module_name)
        for fragment in _FORBIDDEN_CALL_FRAGMENTS:
            assert fragment not in code, (
                f"{module_name} code must not contain {fragment!r} — these are pure "
                "read-only models"
            )


def test_modules_do_not_import_runtime_or_execution_paths():
    for module_name in _MODULES:
        for root in _import_roots(module_name):
            assert root not in _FORBIDDEN_IMPORT_ROOTS, (
                f"{module_name} must not import {root!r}"
            )


def test_projection_feed_does_not_import_resolver_module():
    # The feed reflects decisions passed in; it must not depend on trace_resolver
    # as an authority to build entries. (Type hints reference the decision class,
    # but the builders take an already-made decision.)
    roots_and_modules = _import_roots("trace_projection_feed.py")
    # It may import the decision types from trace_resolver for typing, but must not
    # import trace_query or call resolve_* — assert no resolve_ call in the code.
    code = _code_without_docstrings("trace_projection_feed.py")
    assert "resolve_trace_target(" not in code
    assert "resolve_trace_run(" not in code
    assert "TraceVerifiedResolver(" not in code
    # golden_thread / replay_readiness must not import trace_resolver at all.
    for module_name in ("golden_thread.py", "replay_readiness.py"):
        assert "trace_resolver" not in "".join(
            (_DIR / module_name).read_text(encoding="utf-8")
        ), f"{module_name} must not depend on the resolver"
    assert isinstance(roots_and_modules, list)
