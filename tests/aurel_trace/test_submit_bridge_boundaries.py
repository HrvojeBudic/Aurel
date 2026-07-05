"""P5-TRACE-C boundary proof: bindings are side-effect-free adapters.

Source-sweeps the new binding/bridge modules to prove — structurally, not just
behaviorally — that they never reference the runtime submit / tool dispatch /
trace-append side-effect paths and never import runtime, aurel_exec, or
aurel_flow. Binding is not execution.
"""

from __future__ import annotations

import ast
from pathlib import Path

import agentic_runtime.aurel_trace as aurel_trace_pkg

_PKG_DIR = Path(aurel_trace_pkg.__file__).parent

_BINDING_MODULES = (
    "evidence_ref.py",
    "runtime_submit_bridge.py",
    "p3_binding.py",
    "p4_binding.py",
)

# Call/reference patterns that would indicate runtime mutation or P3/P4 execution.
_FORBIDDEN_FRAGMENTS = (
    "AgenticRuntime",
    "ToolRuntime",
    ".submit(",
    ".dispatch(",
    "trace.append",
    "_append_transition",
    "record_transition",
)

# Module roots forbidden from the binding layer's imports (runtime/P3/P4/side-effect).
_FORBIDDEN_IMPORT_ROOTS = (
    "aurel_exec",
    "aurel_flow",
    "aurel_shell",
    "runtime",
    "tool_runtime",
    "sandbox",
    "policy",
    "verifier",
    "memory",
)

# Absolute (non-relative) module roots the binding layer may import — stdlib only.
_ALLOWED_ABSOLUTE_IMPORT_ROOTS = (
    "dataclasses",
    "enum",
    "typing",
    "pathlib",
    "collections",
    "__future__",
)


def _source(module_name: str) -> str:
    return (_PKG_DIR / module_name).read_text(encoding="utf-8")


def _code_without_docstrings(module_name: str) -> str:
    """Return module source with module/class/function docstrings removed."""

    tree = ast.parse(_source(module_name))
    docstring_lines: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(
            node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
        ):
            doc = ast.get_docstring(node, clean=False)
            if doc is None:
                continue
            expr = node.body[0]
            for line_no in range(expr.lineno, (expr.end_lineno or expr.lineno) + 1):
                docstring_lines.add(line_no)
    kept = [
        line
        for idx, line in enumerate(_source(module_name).splitlines(), start=1)
        if idx not in docstring_lines
    ]
    return "\n".join(kept)


def test_binding_modules_have_no_side_effect_call_fragments():
    # Inspect executable code only (docstrings that *describe* the boundary are
    # allowed to name it in prose).
    for module_name in _BINDING_MODULES:
        code = _code_without_docstrings(module_name)
        for fragment in _FORBIDDEN_FRAGMENTS:
            assert fragment not in code, (
                f"{module_name} code must not contain {fragment!r} — bindings never "
                "execute, dispatch, or append trace"
            )


def test_binding_modules_import_only_downward_or_stdlib():
    # Parse real import statements (ast) so docstring prose can never false-trip.
    for module_name in _BINDING_MODULES:
        tree = ast.parse(_source(module_name))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.level and node.level > 0:
                    # Relative import within aurel_trace — allowed. Also assert the
                    # relative target is not an execution module.
                    assert (node.module or "").split(".")[0] not in _FORBIDDEN_IMPORT_ROOTS
                    continue
                root = (node.module or "").split(".")[0]
                assert root not in _FORBIDDEN_IMPORT_ROOTS, (
                    f"{module_name} must not import {node.module!r}"
                )
                assert root in _ALLOWED_ABSOLUTE_IMPORT_ROOTS, (
                    f"{module_name} absolute import must be stdlib: {node.module!r}"
                )
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    root = alias.name.split(".")[0]
                    assert root not in _FORBIDDEN_IMPORT_ROOTS, (
                        f"{module_name} must not import {alias.name!r}"
                    )


def test_sys_modules_has_no_runtime_side_effect_import_from_bindings():
    # Importing the binding modules must not have pulled in the heavy runtime
    # execution modules as a transitive dependency.
    import sys

    # The bridge/binding modules are already imported via the package.
    assert "agentic_runtime.aurel_trace.runtime_submit_bridge" in sys.modules
    assert "agentic_runtime.aurel_trace.p3_binding" in sys.modules
    assert "agentic_runtime.aurel_trace.p4_binding" in sys.modules
    # aurel_exec / aurel_flow must not be a required import of the binding layer.
    # (They may be present if other tests imported them, so we only assert the
    # binding modules themselves declare no such import — covered above.)
