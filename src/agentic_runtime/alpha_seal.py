"""
alpha_seal.py — P1.0 Runtime Alpha Seal verification.

Checks that the repository meets alpha-readiness criteria: docs, compile,
tests, coverage tooling, CI workflow, and apply-sandbox resolution.
"""
from __future__ import annotations

import subprocess  # nosec B404 - alpha seal intentionally runs fixed local verification commands
import sys
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class SealCheck:
    name: str
    passed: bool
    detail: str = ""


@dataclass
class AlphaSealReport:
    version: str
    checks: list[SealCheck] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(c.passed for c in self.checks)

    def to_dict(self) -> dict:
        return {
            "version": self.version,
            "passed": self.passed,
            "checks": [
                {"name": c.name, "passed": c.passed, "detail": c.detail}
                for c in self.checks
            ],
        }


from .doc_registry import alpha_seal_required_paths

_REQUIRED_CI = ".github/workflows/ci.yml"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def run_alpha_seal(
    *,
    repo_root: Path | None = None,
    run_tests: bool = True,
    skip_coverage: bool = False,
) -> AlphaSealReport:
    from . import __version__

    root = repo_root or _repo_root()
    checks: list[SealCheck] = []

    for label, path in alpha_seal_required_paths():
        checks.append(SealCheck(
            name=f"doc:{label}",
            passed=path.is_file(),
            detail="present" if path.is_file() else "missing",
        ))

    ci_path = root / _REQUIRED_CI
    checks.append(SealCheck(
        name="ci:workflow",
        passed=ci_path.is_file(),
        detail=str(ci_path) if ci_path.is_file() else "missing",
    ))

    compile_proc = subprocess.run(  # nosec B603 - fixed compileall argv in repo root
        [sys.executable, "-m", "compileall", "-q", "src", "tests"],
        cwd=root,
        capture_output=True,
        text=True,
    )
    checks.append(SealCheck(
        name="compileall",
        passed=compile_proc.returncode == 0,
        detail=compile_proc.stderr.strip() or "ok",
    ))

    from .sandbox_policy import resolve_apply_sandbox_profile

    profile, limitations = resolve_apply_sandbox_profile()
    checks.append(SealCheck(
        name="apply_sandbox_resolver",
        passed=bool(profile),
        detail=f"profile={profile}" + (f"; {limitations[0]}" if limitations else ""),
    ))

    if run_tests:
        env = {**dict(__import__("os").environ), "PYTHONPATH": f"src{__import__('os').pathsep}."}
        test_cmd = [sys.executable, "-m", "pytest", "-q"]
        if not skip_coverage:
            test_cmd.extend([
                "--cov=agentic_runtime",
                "--cov-report=term-missing:skip-covered",
                "--cov-fail-under=75",
            ])
        test_proc = subprocess.run(  # nosec B603 - fixed pytest argv plus optional fixed coverage flags
            test_cmd,
            cwd=root,
            env=env,
            capture_output=True,
            text=True,
        )
        tail = (test_proc.stdout + test_proc.stderr).strip().splitlines()
        summary = tail[-1] if tail else "no output"
        checks.append(SealCheck(
            name="pytest",
            passed=test_proc.returncode == 0,
            detail=summary,
        ))

    return AlphaSealReport(version=__version__, checks=checks)


def format_alpha_seal(report: AlphaSealReport) -> str:
    lines = [f"Alpha Seal v{report.version}: {'PASS' if report.passed else 'FAIL'}"]
    for check in report.checks:
        status = "ok" if check.passed else "FAIL"
        detail = f" — {check.detail}" if check.detail else ""
        lines.append(f"  [{status}] {check.name}{detail}")
    return "\n".join(lines)
