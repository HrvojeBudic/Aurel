"""P1.0 — Runtime Alpha Seal tests."""

from __future__ import annotations

from pathlib import Path

from agentic_runtime.alpha_seal import run_alpha_seal
from agentic_runtime.sandbox_policy import (
    SandboxProfileName,
    resolve_apply_sandbox_profile,
)


def test_resolve_apply_sandbox_without_explicit():
    profile, limitations = resolve_apply_sandbox_profile()
    assert profile in {
        SandboxProfileName.BUBBLEWRAP.value,
        SandboxProfileName.DOCKER.value,
        SandboxProfileName.RESTRICTED_LOCAL.value,
    }
    if profile == SandboxProfileName.RESTRICTED_LOCAL.value:
        assert limitations


def test_resolve_apply_sandbox_honors_explicit():
    profile, limitations = resolve_apply_sandbox_profile("no_exec_readonly")
    assert profile == "no_exec_readonly"
    assert not limitations


def test_alpha_seal_docs_and_compile():
    report = run_alpha_seal(run_tests=False)
    doc_checks = [c for c in report.checks if c.name.startswith("doc:")]
    assert doc_checks
    assert all(c.passed for c in doc_checks)
    compile_check = next(c for c in report.checks if c.name == "compileall")
    assert compile_check.passed
    resolver = next(c for c in report.checks if c.name == "apply_sandbox_resolver")
    assert resolver.passed


def test_alpha_seal_ci_workflow_present():
    root = Path(__file__).resolve().parents[1]
    assert (root / ".github/workflows/ci.yml").is_file()


def test_cli_resolve_apply_sandbox_for_repo_task():
    from agentic_runtime.cli import _resolve_cli_sandbox
    from argparse import Namespace

    profile, warnings = _resolve_cli_sandbox(Namespace(sandbox=None), apply=True)
    assert profile
    profile2, _ = _resolve_cli_sandbox(
        Namespace(sandbox="restricted_local"), apply=True)
    assert profile2 == "restricted_local"


def test_cli_plan_only_defaults_restricted_local():
    from agentic_runtime.cli import _resolve_cli_sandbox
    from argparse import Namespace

    profile, warnings = _resolve_cli_sandbox(Namespace(sandbox=None), apply=False)
    assert profile == "restricted_local"
    assert not warnings
