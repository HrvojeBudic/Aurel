"""P0.19 — reproducible demo harness for P0.20 First Real Coding Agent Demo.

Creates controlled scenario repos, verifies initial test failure, runs the governed
RepositoryAgentLoop, and produces an honest DemoRunReport without faking success.
"""
from __future__ import annotations

import difflib
import json
import shutil
import subprocess  # nosec B404 - demo harness intentionally executes repo-local test commands
import sys
import time
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional

from .repo_agent import (
    CodeTaskReport,
    RepoTaskRequest,
    RepositoryAgentLoop,
    TestRunResult,
    _is_allowed,
)


@dataclass(frozen=True)
class DemoScenario:
    scenario_id: str
    name: str
    description: str
    objective: str
    files: dict[str, str]
    test_command: list[str]
    expected_initial_test_failure: bool = True
    expected_final_test_success: bool = True
    allowed_paths: list[str] = field(default_factory=list)
    disallowed_paths: list[str] = field(default_factory=list)
    max_files_changed: int = 1
    max_repair_iterations: int = 2
    require_approval_before_write: bool = False
    sandbox_profile: str = "restricted_local"
    approval_mode: str = "auto"
    planner_mode: str = "deterministic"
    model_provider: Optional[str] = None


@dataclass
class DemoHarnessRequest:
    scenario_id: str
    repo_parent: Optional[str] = None
    apply: bool = True
    dry_run: bool = False
    approval_mode: Optional[str] = None
    sandbox_profile: Optional[str] = None
    planner_mode: str = "deterministic"
    model_provider: Optional[str] = None
    kernel: Any = None
    kernel_factory: Optional[Callable[[str], Any]] = None
    loop_factory: Optional[Callable[[], RepositoryAgentLoop]] = None


@dataclass
class DemoHarnessResult:
    """Structured outcome from a harness run (alias target for DemoRunReport)."""

    scenario_id: str
    repo_path: str
    initial_test_result: TestRunResult
    agent_plan_summary: str = ""
    files_inspected: list[str] = field(default_factory=list)
    files_changed: list[str] = field(default_factory=list)
    final_test_result: Optional[TestRunResult] = None
    trace_summary: dict = field(default_factory=dict)
    approval_summary: list[dict] = field(default_factory=list)
    praxis_summary: dict = field(default_factory=dict)
    sandbox_profile: str = ""
    planner_mode: str = "deterministic"
    model_provider: str = ""
    fallback_reason: str = ""
    sandbox_violations: list[str] = field(default_factory=list)
    code_task_report: Optional[CodeTaskReport] = None
    final_status: str = "not_started"
    limitations: list[str] = field(default_factory=list)
    plan_verification: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


DemoRunReport = DemoHarnessResult


def _default_test_command() -> list[str]:
    return [sys.executable, "-m", "pytest", "-q"]


def _validated_test_command(command: list[str]) -> list[str]:
    """Validate scenario-owned test argv before execution.

    The demo harness accepts only direct argv execution, never shell-wrapped
    commands, so test scenarios cannot silently expand into a broader shell.
    """
    if not isinstance(command, list):
        raise TypeError("test command must be a list[str]")
    if not command:
        raise ValueError("test command must not be empty")

    validated: list[str] = []
    for index, part in enumerate(command):
        if not isinstance(part, str):
            raise TypeError(f"test command entry {index} must be str")
        if not part:
            raise ValueError(f"test command entry {index} must not be empty")
        if "\x00" in part:
            raise ValueError(f"test command entry {index} must not contain NUL bytes")
        validated.append(part)

    executable = os.path.basename(validated[0])
    if executable in {"sh", "bash", "zsh", "dash"}:
        raise ValueError("shell-wrapped test commands are not allowed")
    return validated


BUGGY_CALCULATOR_FILES = {
    "pyproject.toml": (
        '[project]\n'
        'name = "demo-calculator"\n'
        'version = "0.1.0"\n'
    ),
    "calculator.py": (
        "def add(a, b):\n"
        "    return a - b\n"
    ),
    "test_calculator.py": (
        "from calculator import add\n\n\n"
        "def test_add():\n"
        "    assert add(2, 3) == 5\n"
    ),
}

BUGGY_CALCULATOR = DemoScenario(
    scenario_id="buggy_calculator",
    name="Buggy Calculator",
    description="Fix add() that subtracts instead of adding.",
    objective="replace 'return a - b' with 'return a + b' in calculator.py",
    files=BUGGY_CALCULATOR_FILES,
    test_command=_default_test_command(),
    expected_initial_test_failure=True,
    expected_final_test_success=True,
    allowed_paths=["calculator.py", "test_calculator.py", "pyproject.toml"],
    disallowed_paths=[".env", ".env.*", "secrets/*", "credentials.json"],
    max_files_changed=1,
    require_approval_before_write=False,
    sandbox_profile="restricted_local",
    approval_mode="auto",
)

MISSING_VALIDATION_FILES = {
    "pyproject.toml": (
        '[project]\n'
        'name = "demo-validation"\n'
        'version = "0.1.0"\n'
    ),
    "calculator.py": (
        "def divide(a, b):\n"
        "    return a / b\n"
    ),
    "test_calculator.py": (
        "import pytest\n"
        "from calculator import divide\n\n\n"
        "def test_divide_valid():\n"
        "    assert divide(10, 2) == 5\n\n\n"
        "def test_divide_zero_validation():\n"
        "    with pytest.raises(ValueError):\n"
        "        divide(10, 0)\n"
    ),
}

MISSING_VALIDATION = DemoScenario(
    scenario_id="missing_validation",
    name="Missing Validation",
    description="Add explicit zero-division validation to divide().",
    objective="Add explicit zero-division validation to divide() in calculator.py and keep valid division behavior.",
    files=MISSING_VALIDATION_FILES,
    test_command=_default_test_command(),
    expected_initial_test_failure=True,
    expected_final_test_success=True,
    allowed_paths=["calculator.py", "test_calculator.py", "pyproject.toml"],
    disallowed_paths=[".env", ".env.*", "secrets/*", "credentials.json"],
    max_files_changed=1,
    require_approval_before_write=False,
    sandbox_profile="restricted_local",
    approval_mode="auto",
)

SCENARIOS: dict[str, DemoScenario] = {
    BUGGY_CALCULATOR.scenario_id: BUGGY_CALCULATOR,
    MISSING_VALIDATION.scenario_id: MISSING_VALIDATION,
}


def get_scenario(scenario_id: str) -> DemoScenario:
    try:
        return SCENARIOS[scenario_id]
    except KeyError as exc:
        known = ", ".join(sorted(SCENARIOS))
        raise ValueError(f"unknown scenario {scenario_id!r}; known: {known}") from exc


def list_scenarios() -> list[DemoScenario]:
    return list(SCENARIOS.values())


class DemoRepoFactory:
    """Materialize a scenario repo under a parent directory (no git required)."""

    def create(self, scenario: DemoScenario, parent: str | Path) -> Path:
        parent_path = Path(parent).resolve()
        parent_path.mkdir(parents=True, exist_ok=True)
        repo = (parent_path / f"demo_{scenario.scenario_id}").resolve()
        if repo.exists():
            shutil.rmtree(repo)
        repo.mkdir(parents=True)
        for rel, content in scenario.files.items():
            self._write_under(repo, rel, content)
        return repo

    def cleanup(self, repo_path: str | Path) -> None:
        path = Path(repo_path).resolve()
        if path.exists():
            shutil.rmtree(path, ignore_errors=True)

    @staticmethod
    def _write_under(repo_root: Path, rel: str, content: str) -> Path:
        rel_path = Path(rel)
        if rel_path.is_absolute() or ".." in rel_path.parts:
            raise ValueError(f"path traversal not allowed: {rel}")
        dest = (repo_root / rel_path).resolve()
        if repo_root not in dest.parents and dest != repo_root:
            raise ValueError(f"path escapes repo root: {rel}")
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content, encoding="utf-8")
        return dest


def _clear_pycache(repo_path: Path) -> None:
    cache = repo_path / "__pycache__"
    if cache.is_dir():
        shutil.rmtree(cache, ignore_errors=True)
    pytest_cache = repo_path / ".pytest_cache"
    if pytest_cache.is_dir():
        shutil.rmtree(pytest_cache, ignore_errors=True)


def run_tests(repo_path: str | Path, command: list[str], timeout: int = 120) -> TestRunResult:
    cmd = _validated_test_command(_normalize_test_command(command))
    start = time.monotonic()
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    try:
        proc = subprocess.run(  # nosec B603 - demo scenarios supply validated direct argv, never shell=True
            cmd,
            cwd=str(repo_path),
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
        )
        duration_ms = int((time.monotonic() - start) * 1000)
        return TestRunResult(
            command=cmd,
            exit_code=proc.returncode,
            stdout=proc.stdout,
            stderr=proc.stderr,
            duration_ms=duration_ms,
            timed_out=False,
        )
    except subprocess.TimeoutExpired as exc:
        duration_ms = int((time.monotonic() - start) * 1000)
        stdout = exc.stdout.decode("utf-8", errors="replace") if exc.stdout else ""
        stderr = exc.stderr.decode("utf-8", errors="replace") if exc.stderr else ""
        return TestRunResult(
            command=cmd,
            exit_code=-1,
            stdout=stdout,
            stderr=stderr or "timed out",
            duration_ms=duration_ms,
            timed_out=True,
        )


def _trace_summary(kernel) -> dict:
    events = list(kernel.trace.replay())
    kinds = sorted({e.get("kind") for e in events if e.get("kind")})
    return {
        "run_id": kernel.trace.run_id,
        "event_count": len(events),
        "kinds": kinds,
    }


def _praxis_summary(report: Optional[CodeTaskReport]) -> dict:
    if report is None or report.praxis_report is None:
        return {}
    pr = report.praxis_report
    return {
        "experience_id": pr.experience_id,
        "memory_candidates_created": pr.memory_candidates_created,
        "procedure_candidates_created": pr.procedure_candidates_created,
        "skill_candidates_created": pr.skill_candidates_created,
        "promotion_decisions": len(pr.promotion_decisions),
        "limitations": list(pr.limitations),
    }


def _verify_plan_first(
    scenario: DemoScenario,
    report: Optional[CodeTaskReport],
    *,
    apply: bool,
) -> dict:
    checks: dict[str, bool | list[str]] = {
        "plan_recorded": False,
        "files_inspected_recorded": False,
        "files_changed_within_bounds": True,
        "tests_run_after_patch": False,
        "approval_recorded": False,
        "sandbox_profile_recorded": False,
        "praxis_recorded": False,
        "test_file_unchanged": True,
        "violations": [],
    }
    if report is None:
        checks["violations"] = ["no CodeTaskReport produced"]
        return checks

    checks["plan_recorded"] = bool(report.plan_summary)
    checks["files_inspected_recorded"] = bool(report.files_inspected)
    checks["sandbox_profile_recorded"] = bool(report.sandbox_profile)

    if report.files_changed:
        over_max = len(report.files_changed) > scenario.max_files_changed
        disallowed = [
            f for f in report.files_changed
            if not _is_allowed(f, scenario.allowed_paths, scenario.disallowed_paths)
        ]
        checks["files_changed_within_bounds"] = not over_max and not disallowed
        if over_max:
            checks["violations"].append("files_changed exceeds max_files_changed")
        if disallowed:
            checks["violations"].append(f"changed files outside allowed_paths: {disallowed}")

    if apply:
        checks["tests_run_after_patch"] = report.test_result is not None
        checks["approval_recorded"] = bool(report.approval_summaries)
        checks["praxis_recorded"] = report.praxis_report is not None

    return checks


def _test_file_unchanged(repo_path: Path, scenario: DemoScenario) -> tuple[bool, str]:
    for rel, expected in scenario.files.items():
        if not rel.startswith("test_"):
            continue
        path = repo_path / rel
        if not path.exists():
            return False, f"missing test file: {rel}"
        if path.read_text(encoding="utf-8") != expected:
            return False, f"test file modified: {rel}"
    return True, ""


def _normalize_test_command(command: list[str]) -> list[str]:
    cmd = list(command)
    if cmd and cmd[0] == "python3":
        cmd[0] = sys.executable
    return cmd


def _build_repo_request(scenario: DemoScenario, repo_path: Path, request: DemoHarnessRequest) -> RepoTaskRequest:
    return RepoTaskRequest.make(
        objective=scenario.objective,
        repo_path=str(repo_path),
        allowed_paths=list(scenario.allowed_paths),
        disallowed_paths=list(scenario.disallowed_paths),
        max_files_changed=scenario.max_files_changed,
        max_repair_iterations=scenario.max_repair_iterations,
        test_command=_normalize_test_command(scenario.test_command),
        require_approval_before_write=scenario.require_approval_before_write,
        approval_mode=request.approval_mode or scenario.approval_mode,
        sandbox_profile=request.sandbox_profile or scenario.sandbox_profile,
        planner_mode=request.planner_mode,
        model_provider=request.model_provider,
    )


class DemoHarness:
    """Run a demo scenario end-to-end through RepositoryAgentLoop."""

    def __init__(
        self,
        factory: Optional[DemoRepoFactory] = None,
        loop_factory: Optional[Callable[[], RepositoryAgentLoop]] = None,
    ) -> None:
        self.factory = factory or DemoRepoFactory()
        self.loop_factory = loop_factory

    def run(self, request: DemoHarnessRequest | str, **kwargs) -> DemoRunReport:
        if isinstance(request, str):
            request = DemoHarnessRequest(scenario_id=request, **kwargs)
        scenario = get_scenario(request.scenario_id)
        parent = request.repo_parent or "."
        repo_path = self.factory.create(scenario, parent)
        limitations: list[str] = []

        initial = run_tests(repo_path, scenario.test_command)
        if scenario.expected_initial_test_failure and initial.passed:
            return DemoRunReport(
                scenario_id=scenario.scenario_id,
                repo_path=str(repo_path),
                initial_test_result=initial,
                final_status="harness_failed",
                limitations=["initial tests passed but scenario expects failure"],
            )
        if not scenario.expected_initial_test_failure and not initial.passed:
            limitations.append("initial tests failed unexpectedly")

        _clear_pycache(repo_path)

        repo_request = _build_repo_request(scenario, repo_path, request)
        if request.kernel_factory is not None:
            loop = RepositoryAgentLoop(kernel=request.kernel_factory(str(repo_path)))
        elif request.kernel is not None:
            loop = RepositoryAgentLoop(kernel=request.kernel)
        elif request.loop_factory is not None:
            loop = request.loop_factory()
        elif self.loop_factory is not None:
            loop = self.loop_factory()
        else:
            loop = RepositoryAgentLoop()

        code_report = loop.run(
            repo_request,
            apply=request.apply,
            dry_run=request.dry_run,
        )

        trace_kernel = loop.kernel or request.kernel
        trace_summary = _trace_summary(trace_kernel) if trace_kernel is not None else {}

        final_test: Optional[TestRunResult] = None
        if request.apply and not request.dry_run:
            _clear_pycache(repo_path)
            final_test = run_tests(repo_path, scenario.test_command)
            ok, reason = _test_file_unchanged(repo_path, scenario)
            if not ok:
                limitations.append(reason)

        plan_verification = _verify_plan_first(scenario, code_report, apply=request.apply)
        if request.apply and not request.dry_run:
            ok, reason = _test_file_unchanged(repo_path, scenario)
            plan_verification["test_file_unchanged"] = ok
            if not ok:
                plan_verification["violations"].append(reason)

        final_status = _resolve_final_status(
            scenario,
            code_report,
            final_test,
            request.apply,
            request.dry_run,
            limitations,
            plan_verification,
        )

        return DemoRunReport(
            scenario_id=scenario.scenario_id,
            repo_path=str(repo_path),
            initial_test_result=initial,
            agent_plan_summary=code_report.plan_summary if code_report else "",
            files_inspected=list(code_report.files_inspected) if code_report else [],
            files_changed=list(code_report.files_changed) if code_report else [],
            final_test_result=final_test or (code_report.test_result if code_report else None),
            trace_summary=trace_summary,
            approval_summary=list(code_report.approval_summaries) if code_report else [],
            praxis_summary=_praxis_summary(code_report),
            sandbox_profile=code_report.sandbox_profile if code_report else "",
            planner_mode=code_report.planner_mode if code_report else request.planner_mode,
            model_provider=code_report.model_provider if code_report else (request.model_provider or ""),
            fallback_reason=code_report.fallback_reason if code_report else "",
            sandbox_violations=list(code_report.sandbox_violations) if code_report else [],
            code_task_report=code_report,
            final_status=final_status,
            limitations=limitations + list(plan_verification.get("violations", [])),
            plan_verification=plan_verification,
        )


def _resolve_final_status(
    scenario: DemoScenario,
    code_report: Optional[CodeTaskReport],
    final_test: Optional[TestRunResult],
    apply: bool,
    dry_run: bool,
    limitations: list[str],
    plan_verification: dict,
) -> str:
    if not apply or dry_run:
        if code_report and code_report.final_status in {"planned", "dry_run"}:
            return code_report.final_status
        return "planned"

    agent_status = code_report.final_status if code_report else "not_started"
    if final_test is not None and scenario.expected_final_test_success and not final_test.passed:
        return "failed"
    if not plan_verification.get("files_changed_within_bounds", True):
        return "failed"
    if not plan_verification.get("test_file_unchanged", True):
        return "failed"
    if agent_status in {"patch_failed", "planning_failed", "sandbox_unavailable", "failed"}:
        return agent_status
    if final_test is not None and final_test.passed and agent_status == "succeeded":
        return "succeeded"
    if final_test is not None and not final_test.passed:
        return "failed"
    return agent_status


_MAX_OUTPUT_CHARS = 20_000


def _truncate(text: str, limit: int = _MAX_OUTPUT_CHARS) -> str:
    text = text or ""
    if len(text) <= limit:
        return text
    return text[:limit] + f"\n... [truncated {len(text) - limit} chars]"


def _compute_diff(report: "DemoRunReport", scenario: DemoScenario) -> str:
    """Honest unified diff of changed files: original scenario content vs final repo content."""
    repo = Path(report.repo_path)
    chunks: list[str] = []
    for rel in report.files_changed:
        before = scenario.files.get(rel, "")
        path = repo / rel
        after = path.read_text(encoding="utf-8") if path.exists() else ""
        if before == after:
            continue
        diff = difflib.unified_diff(
            before.splitlines(keepends=True),
            after.splitlines(keepends=True),
            fromfile=f"a/{rel}",
            tofile=f"b/{rel}",
        )
        chunks.append("".join(diff))
    return "\n".join(chunks)


def build_sandbox_summary(report: "DemoRunReport", scenario: DemoScenario) -> dict:
    """Honest sandbox summary derived from the public profile template."""
    from .sandbox_policy import get_sandbox_profile

    profile_name = report.sandbox_profile or scenario.sandbox_profile
    try:
        profile = get_sandbox_profile(
            profile_name,
            report.repo_path,
            allowed_paths=scenario.allowed_paths,
            disallowed_paths=scenario.disallowed_paths,
        )
    except ValueError:
        return {
            "sandbox_profile": profile_name,
            "limitations": ["profile metadata unavailable"],
            "violations": list(report.sandbox_violations),
        }
    return {
        "sandbox_profile": profile.profile_name,
        "backend_name": profile.backend_name,
        "mode": profile.mode.value,
        "workspace_root": os.path.basename(profile.workspace_root.rstrip("/")) or profile.workspace_root,
        "network_allowed": profile.allow_network,
        "secrets_allowed": profile.allow_secrets,
        "write_allowed": profile.allow_write,
        "exec_allowed": profile.allow_exec,
        "unsafe": profile.unsafe,
        "limitations": list(profile.limitations),
        "violations": list(report.sandbox_violations),
    }


def write_evidence(evidence_dir: str | Path, report: "DemoRunReport", scenario: DemoScenario) -> list[str]:
    """Write P0.20 evidence artifacts. Returns list of files written. No fake data."""
    out_dir = Path(evidence_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[str] = []

    def _write(name: str, content: str) -> None:
        (out_dir / name).write_text(content, encoding="utf-8")
        written.append(name)

    def _write_json(name: str, obj: Any) -> None:
        _write(name, json.dumps(obj, indent=2, default=str))

    repo_id = Path(report.repo_path).name

    demo_run = {
        "scenario_id": report.scenario_id,
        "objective": scenario.objective,
        "repo_id": repo_id,
        "initial_test_result": {
            "command": report.initial_test_result.command,
            "exit_code": report.initial_test_result.exit_code,
            "passed": report.initial_test_result.passed,
            "timed_out": report.initial_test_result.timed_out,
        },
        "plan_summary": report.agent_plan_summary,
        "planner_mode": report.planner_mode,
        "model_provider": report.model_provider,
        "fallback_reason": report.fallback_reason,
        "files_inspected": report.files_inspected,
        "files_changed": report.files_changed,
        "final_test_result": None if report.final_test_result is None else {
            "command": report.final_test_result.command,
            "exit_code": report.final_test_result.exit_code,
            "passed": report.final_test_result.passed,
            "timed_out": report.final_test_result.timed_out,
        },
        "final_status": report.final_status,
        "plan_verification": report.plan_verification,
        "limitations": report.limitations,
    }
    _write_json("demo_run_report.json", demo_run)
    _write_json("trace_summary.json", report.trace_summary)

    if report.approval_summary:
        _write_json("approval_summary.json", report.approval_summary)
    else:
        _write_json("approval_summary.json", {"limitation": "no approval receipts recorded"})

    _write_json("sandbox_summary.json", build_sandbox_summary(report, scenario))

    if report.praxis_summary:
        _write_json("praxis_summary.json", report.praxis_summary)
    else:
        _write_json("praxis_summary.json", {"limitation": "no praxis report available"})

    diff_text = _compute_diff(report, scenario)
    if diff_text.strip():
        _write("final_diff.patch", diff_text)
    else:
        _write("final_diff.patch", "# no textual diff available for changed files\n")

    _write("test_output_before.txt", _truncate(
        f"$ {' '.join(report.initial_test_result.command)}\n"
        f"exit_code={report.initial_test_result.exit_code} "
        f"passed={report.initial_test_result.passed}\n\n"
        f"{report.initial_test_result.stdout}\n{report.initial_test_result.stderr}"
    ))
    if report.final_test_result is not None:
        _write("test_output_after.txt", _truncate(
            f"$ {' '.join(report.final_test_result.command)}\n"
            f"exit_code={report.final_test_result.exit_code} "
            f"passed={report.final_test_result.passed}\n\n"
            f"{report.final_test_result.stdout}\n{report.final_test_result.stderr}"
        ))
    else:
        _write("test_output_after.txt", "# final tests not run (plan-only / dry-run)\n")

    return written
