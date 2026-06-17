"""P0.19 — Demo harness tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from agentic_runtime import build_runtime
from agentic_runtime.demo_harness import (
    BUGGY_CALCULATOR,
    BUGGY_CALCULATOR_FILES,
    DemoHarness,
    DemoHarnessRequest,
    DemoRepoFactory,
    get_scenario,
    list_scenarios,
    run_tests,
)
from agentic_runtime.repo_agent import RepoTaskRequest, RepositoryAgentLoop
from agentic_runtime.sandbox import UnsafeLocalSandbox
from tests.conftest import bounded_test_approver


def _kernel_for_repo(repo_path: str):
    return build_runtime(
        sandbox=UnsafeLocalSandbox(root=repo_path),
        approval_gate=bounded_test_approver(
            lambda r: (
                r.command.tool in {"run_tests", "edit_file", "write_file", "patch_file"}
            ),
        ),
    )


def test_list_scenarios_includes_buggy_calculator():
    ids = {s.scenario_id for s in list_scenarios()}
    assert "buggy_calculator" in ids


def test_get_scenario_unknown_raises():
    with pytest.raises(ValueError, match="unknown scenario"):
        get_scenario("missing")


def test_factory_creates_scenario_repo(tmp_path):
    factory = DemoRepoFactory()
    repo = factory.create(BUGGY_CALCULATOR, tmp_path)
    assert repo.is_dir()
    for rel in BUGGY_CALCULATOR_FILES:
        assert (repo / rel).is_file()
    assert (repo / "calculator.py").read_text(encoding="utf-8").strip().endswith("return a - b")


def test_factory_initial_test_fails_for_buggy_calculator(tmp_path):
    factory = DemoRepoFactory()
    repo = factory.create(BUGGY_CALCULATOR, tmp_path)
    result = run_tests(repo, BUGGY_CALCULATOR.test_command)
    assert not result.passed
    assert result.exit_code != 0


def test_factory_does_not_write_outside_parent(tmp_path):
    factory = DemoRepoFactory()
    repo = factory.create(BUGGY_CALCULATOR, tmp_path)
    assert str(repo.resolve()).startswith(str(tmp_path.resolve()))


def test_factory_rejects_path_traversal(tmp_path):
    factory = DemoRepoFactory()
    bad = BUGGY_CALCULATOR
    # frozen dataclass — build a modified scenario copy via replace
    from dataclasses import replace
    evil = replace(bad, files={**bad.files, "../evil.py": "x"})
    with pytest.raises(ValueError, match="path traversal"):
        factory.create(evil, tmp_path)


def test_harness_fails_if_initial_test_unexpectedly_passes(tmp_path):
    factory = DemoRepoFactory()
    repo = factory.create(
        BUGGY_CALCULATOR,
        tmp_path,
    )
    # Fix the bug so initial tests pass
    (repo / "calculator.py").write_text(
        "def add(a, b):\n    return a + b\n",
        encoding="utf-8",
    )

    class FixedRepoFactory(DemoRepoFactory):
        def create(self, scenario, parent):
            return repo

    report = DemoHarness(factory=FixedRepoFactory()).run(DemoHarnessRequest(
        scenario_id="buggy_calculator",
        repo_parent=tmp_path,
        apply=False,
    ))
    assert report.final_status == "harness_failed"
    assert "initial tests passed" in report.limitations[0]


def test_harness_builds_repo_task_request(tmp_path):
    factory = DemoRepoFactory()
    repo = factory.create(BUGGY_CALCULATOR, tmp_path)
    req = RepoTaskRequest.make(
        objective=BUGGY_CALCULATOR.objective,
        repo_path=str(repo),
        allowed_paths=BUGGY_CALCULATOR.allowed_paths,
        disallowed_paths=BUGGY_CALCULATOR.disallowed_paths,
        max_files_changed=BUGGY_CALCULATOR.max_files_changed,
        test_command=BUGGY_CALCULATOR.test_command,
        require_approval_before_write=False,
    )
    assert "calculator.py" in req.objective
    assert req.max_files_changed == 1


def test_harness_plan_only_records_plan(tmp_path):
    report = DemoHarness().run(DemoHarnessRequest(
        scenario_id="buggy_calculator",
        repo_parent=tmp_path,
        apply=False,
        kernel_factory=_kernel_for_repo,
    ))
    assert report.final_status == "planned"
    assert report.agent_plan_summary
    assert report.files_inspected
    assert report.plan_verification["plan_recorded"]


def test_harness_enforces_allowed_paths_on_apply(tmp_path):
    report = DemoHarness().run(DemoHarnessRequest(
        scenario_id="buggy_calculator",
        repo_parent=tmp_path,
        apply=True,
        kernel_factory=_kernel_for_repo,
    ))
    assert report.final_status == "succeeded"
    for path in report.files_changed:
        assert path in BUGGY_CALCULATOR.allowed_paths or path.endswith(
            tuple(p for p in BUGGY_CALCULATOR.allowed_paths)
        )
    assert len(report.files_changed) <= BUGGY_CALCULATOR.max_files_changed


def test_harness_records_final_test_result(tmp_path):
    report = DemoHarness().run(DemoHarnessRequest(
        scenario_id="buggy_calculator",
        repo_parent=tmp_path,
        apply=True,
        kernel_factory=_kernel_for_repo,
    ))
    assert report.final_test_result is not None
    assert report.final_test_result.passed


def test_harness_produces_demo_run_report(tmp_path):
    report = DemoHarness().run(DemoHarnessRequest(
        scenario_id="buggy_calculator",
        repo_parent=tmp_path,
        apply=True,
        kernel_factory=_kernel_for_repo,
    ))
    data = report.to_dict()
    for key in (
        "scenario_id", "repo_path", "initial_test_result", "files_changed",
        "final_test_result", "trace_summary", "approval_summary",
        "praxis_summary", "final_status", "sandbox_profile",
    ):
        assert key in data


def test_harness_fails_honestly_when_patch_not_applied(tmp_path):
    report = DemoHarness().run(DemoHarnessRequest(
        scenario_id="buggy_calculator",
        repo_parent=tmp_path,
        apply=False,
        kernel_factory=_kernel_for_repo,
    ))
    final = run_tests(report.repo_path, BUGGY_CALCULATOR.test_command)
    assert not final.passed


def test_test_file_not_weakened(tmp_path):
    report = DemoHarness().run(DemoHarnessRequest(
        scenario_id="buggy_calculator",
        repo_parent=tmp_path,
        apply=True,
        kernel_factory=_kernel_for_repo,
    ))
    repo = Path(report.repo_path)
    assert repo.joinpath("test_calculator.py").read_text(encoding="utf-8") == (
        BUGGY_CALCULATOR_FILES["test_calculator.py"]
    )
    assert report.plan_verification.get("test_file_unchanged", True)


def test_buggy_calculator_e2e_via_repository_agent_loop(tmp_path):
    report = DemoHarness().run(DemoHarnessRequest(
        scenario_id="buggy_calculator",
        repo_parent=tmp_path,
        apply=True,
        kernel_factory=_kernel_for_repo,
    ))
    assert report.initial_test_result.passed is False
    assert report.final_status == "succeeded"
    assert report.files_changed == ["calculator.py"]
    assert "return a + b" in Path(report.repo_path, "calculator.py").read_text(encoding="utf-8")
    assert report.sandbox_profile
    assert report.approval_summary
    assert report.praxis_summary
    assert report.trace_summary.get("event_count", 0) > 0


def test_plan_verification_records_sandbox_and_praxis(tmp_path):
    report = DemoHarness().run(DemoHarnessRequest(
        scenario_id="buggy_calculator",
        repo_parent=tmp_path,
        apply=True,
        kernel_factory=_kernel_for_repo,
    ))
    pv = report.plan_verification
    assert pv["plan_recorded"]
    assert pv["sandbox_profile_recorded"]
    assert pv["tests_run_after_patch"]
    assert pv["praxis_recorded"]


def test_repository_loop_kernel_persisted_after_run(tmp_path):
    factory = DemoRepoFactory()
    repo = factory.create(BUGGY_CALCULATOR, tmp_path)
    loop = RepositoryAgentLoop(kernel=_kernel_for_repo(str(repo)))
    req = RepoTaskRequest.make(
        objective=BUGGY_CALCULATOR.objective,
        repo_path=str(repo),
        allowed_paths=BUGGY_CALCULATOR.allowed_paths,
        test_command=BUGGY_CALCULATOR.test_command,
        require_approval_before_write=False,
    )
    loop.run(req, apply=False)
    assert loop.kernel is not None
