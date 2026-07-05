"""P5-TRACE-D boundary proof: resolver/query are pure; CLI is read-only.

Source-sweeps (ast) the resolver and query modules to prove they contain no
runtime/execution call fragments and import no runtime/P3/P4/policy/memory
module, and sweeps the CLI command module to prove it exposes no mutating
operation. The DEV_FIXTURE demo module builds an isolated in-memory ledger, so it
is excluded from the pure sweep but asserted to never call runtime.submit or
write files.
"""

from __future__ import annotations

import ast
from pathlib import Path

import agentic_runtime.aurel_trace as aurel_trace_pkg
from agentic_runtime import cli_modules

_TRACE_DIR = Path(aurel_trace_pkg.__file__).parent
_CLI_DIR = Path(cli_modules.__file__).parent

# Modules that must be provably pure (no ledger construction, no execution).
_PURE_MODULES = (_TRACE_DIR / "trace_resolver.py", _TRACE_DIR / "trace_query.py")
_CLI_MODULE = _CLI_DIR / "trace_commands.py"
_DEMO_MODULE = _TRACE_DIR / "trace_demo.py"

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

# Mutating CLI verbs that must not appear as trace subcommands.
_FORBIDDEN_CLI_FRAGMENTS = (
    "runtime.submit",
    ".dispatch(",
    "trace.append",
    "repair",
    "replay",
    "approve",
    "memory_write",
    "os.remove",
    "shutil.rmtree",
    "open(",
    ".write(",
)


def _code_without_docstrings(path: Path) -> str:
    source = path.read_text(encoding="utf-8")
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


def _imports(path: Path):
    roots: list[str] = []
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.ImportFrom) and not (node.level and node.level > 0):
            roots.append((node.module or "").split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.level:
            roots.append((node.module or "").split(".")[0])
        elif isinstance(node, ast.Import):
            roots.extend(alias.name.split(".")[0] for alias in node.names)
    return roots


def test_resolver_and_query_are_pure():
    for path in _PURE_MODULES:
        code = _code_without_docstrings(path)
        for fragment in _FORBIDDEN_CALL_FRAGMENTS:
            assert fragment not in code, f"{path.name} must not contain {fragment!r}"
        for root in _imports(path):
            assert root not in _FORBIDDEN_IMPORT_ROOTS, (
                f"{path.name} must not import {root!r}"
            )


def test_cli_module_has_no_mutating_operations():
    code = _code_without_docstrings(_CLI_MODULE)
    for fragment in _FORBIDDEN_CLI_FRAGMENTS:
        assert fragment not in code, (
            f"trace_commands.py must not contain {fragment!r} — the CLI is read-only"
        )


def test_demo_module_never_calls_runtime_submit_or_writes_files():
    code = _code_without_docstrings(_DEMO_MODULE)
    for fragment in (
        "AgenticRuntime",
        ".submit(",
        ".dispatch(",
        "open(",
        ".write(",
        "os.remove",
    ):
        assert fragment not in code, (
            f"trace_demo.py (DEV_FIXTURE) must not contain {fragment!r}"
        )
    # The demo may not import the runtime execution modules.
    for root in _imports(_DEMO_MODULE):
        assert root not in ("runtime", "tool_runtime", "aurel_exec", "aurel_flow")
