"""P5-TRACE-F boundary proof: privacy/export/integrity modules are pure read models.

ast source-sweeps the three new modules to prove they contain no external export /
upload / network / DB / crypto / filesystem-write fragments, import no runtime /
execution / storage path, and never mutate P5-E source material.
"""

from __future__ import annotations

import ast
from pathlib import Path

import agentic_runtime.aurel_trace as aurel_trace_pkg

_DIR = Path(aurel_trace_pkg.__file__).parent

_MODULES = ("privacy_labels.py", "trace_export.py", "persistent_integrity.py")

_FORBIDDEN_CALL_FRAGMENTS = (
    "AgenticRuntime",
    "ToolRuntime",
    ".submit(",
    ".dispatch(",
    "trace.append",
    "_append_transition",
    ".rollback(",
    "urlopen(",
    ".post(",
    ".put(",
    ".upload(",
    "socket.",
    ".connect(",
    "open(",
    ".write(",
    "os.remove",
    "shutil.",
    "subprocess",
    ".encrypt(",
    ".execute(",  # no DB cursor execution
    "cursor(",
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
    "http",
    "socket",
    "boto3",
    "botocore",
    "sqlite3",
    "cryptography",
    "ssl",
    "smtplib",
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


def test_no_export_upload_or_storage_call_fragments():
    for module_name in _MODULES:
        code = _code_without_docstrings(module_name)
        for fragment in _FORBIDDEN_CALL_FRAGMENTS:
            assert fragment not in code, (
                f"{module_name} code must not contain {fragment!r} — no external "
                "export/upload/network/DB/crypto/filesystem-write is allowed"
            )


def test_no_forbidden_imports():
    for module_name in _MODULES:
        for root in _import_roots(module_name):
            assert root not in _FORBIDDEN_IMPORT_ROOTS, (
                f"{module_name} must not import {root!r}"
            )


def test_source_material_not_mutated():
    # Building a redacted view / manifest / bundle leaves the source feed unchanged.
    from agentic_runtime.aurel_trace import (
        TraceLocalityLabel,
        TracePrivacyLabel,
        build_redacted_trace_view,
        build_trace_projection_feed,
    )
    from agentic_runtime.aurel_trace.trace_demo import build_demo_trace_substrate

    feed = build_trace_projection_feed(build_demo_trace_substrate().decisions)
    snapshot = feed.to_dict()
    build_redacted_trace_view(
        feed=feed,
        label_map={
            e.target_id: (TracePrivacyLabel.SECRET, TraceLocalityLabel.LOCAL_ONLY)
            for e in feed.entries
        },
    )
    assert feed.to_dict() == snapshot
