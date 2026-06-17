"""P0.14 — Repository Agent Loop tests."""

from __future__ import annotations

from agentic_runtime import (
    AgentCard,
    AgentClass,
    AuthorityScope,
    RiskLevel,
    build_runtime,
)
from agentic_runtime.core_types import CommandEnvelope
from agentic_runtime.hitl import AutoApprover
from agentic_runtime.repo_agent import (
    CodeTaskPlanner,
    PatchExecutor,
    PatchPlan,
    RepairAttempt,
    RepairLoop,
    RepoContextBuilder,
    RepoTaskPlan,
    RepoTaskRequest,
    RepositoryAgentLoop,
    TestFailureAnalyzer as FailureAnalyzer,
    TestRunnerAdapter as RunnerAdapter,
)
from agentic_runtime.sandbox import UnsafeLocalSandbox


def _write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _fixture_repo(tmp_path):
    _write(tmp_path / "pyproject.toml", "[project]\nname = \"fixture\"\nversion = \"0.1\"\n")
    _write(tmp_path / "src" / "calc.py", "def add(a, b):\n    return a - b\n")
    _write(tmp_path / "test_calc.py", "from src.calc import add\nassert add(2, 3) == 5\n")
    _write(tmp_path / "agent" / "AGENT.md", "# Agent\n")
    return tmp_path


def _request(tmp_path, **kw):
    defaults = dict(
        objective="replace 'return a - b' with 'return a + b' in src/calc.py",
        repo_path=str(tmp_path),
        allowed_paths=["src", "test_calc.py", "pyproject.toml", "agent"],
        disallowed_paths=[],
        test_command=["python3", "test_calc.py"],
        require_approval_before_write=False,
    )
    defaults.update(kw)
    return RepoTaskRequest.make(**defaults)


def _kernel(tmp_path):
    return build_runtime(
        sandbox=UnsafeLocalSandbox(root=str(tmp_path)),
        approval_gate=AutoApprover(lambda r: True, allow_r2=True, allow_r3=True),
    )


def _card(paths=None):
    return AgentCard.make(
        name="Repo Agent Test",
        agent_class=AgentClass.EXECUTION,
        mission="test",
        authority=AuthorityScope(write_paths=paths or ["*"], read_paths=["*"],
                                 max_risk=RiskLevel.HIGH),
        allowed_tools=["patch_file", "write_file", "run_tests", "run_shell",
                       "read_file", "list_dir", "search_text"],
    )


def test_context_builder_detects_repo_root(tmp_path):
    repo = _fixture_repo(tmp_path)
    nested = repo / "src"
    ctx = RepoContextBuilder().build(_request(nested, repo_path=str(nested)))
    assert ctx.repo_root == str(repo.resolve())
    assert ctx.metadata["name"] == "fixture"


def test_context_builder_respects_allowed_paths(tmp_path):
    _fixture_repo(tmp_path)
    _write(tmp_path / "other" / "secret.py", "x = 1\n")
    ctx = RepoContextBuilder().build(_request(tmp_path, allowed_paths=["src"]))
    paths = [f.path for f in ctx.file_summaries]
    assert "src/calc.py" in paths
    assert "other/secret.py" not in paths


def test_context_builder_rejects_outside_root(tmp_path):
    _fixture_repo(tmp_path)
    try:
        RepoContextBuilder().build(_request(tmp_path, repo_path=str(tmp_path / "missing")))
    except ValueError as e:
        assert "does not exist" in str(e)
    else:  # pragma: no cover
        raise AssertionError("expected ValueError")


def test_context_builder_avoids_huge_file_read(tmp_path):
    _fixture_repo(tmp_path)
    _write(tmp_path / "src" / "huge.py", "x" * 50_000)
    ctx = RepoContextBuilder(max_file_bytes=100).build(_request(tmp_path))
    huge = next(f for f in ctx.file_summaries if f.path == "src/huge.py")
    assert huge.truncated
    assert huge.content_preview == ""


def test_context_builder_reads_agent_docs(tmp_path):
    _fixture_repo(tmp_path)
    ctx = RepoContextBuilder().build(_request(tmp_path))
    assert "agent/AGENT.md" in ctx.agent_docs


def test_planner_produces_valid_plan(tmp_path):
    _fixture_repo(tmp_path)
    req = _request(tmp_path)
    ctx = RepoContextBuilder().build(req)
    plan = CodeTaskPlanner().create_plan(req, ctx)
    ok, reason = CodeTaskPlanner().validate_plan(plan)
    assert ok, reason
    assert plan.files_to_modify == ["src/calc.py"]
    assert plan.expected_tests
    assert plan.risk_level == "medium"
    assert plan.patch_plans


def test_planner_rejects_invalid_plan():
    plan = RepoTaskPlan("", [], [], [], "low", [], False, valid=False,
                        refusal_reason="no context")
    ok, reason = CodeTaskPlanner().validate_plan(plan)
    assert not ok
    assert reason == "no context"


def test_mock_offline_planning_works(tmp_path):
    _fixture_repo(tmp_path)
    req = _request(tmp_path)
    plan = CodeTaskPlanner().create_plan(req, RepoContextBuilder().build(req))
    assert plan.valid
    assert plan.requires_approval is False


def test_patch_executor_applies_small_patch_inside_repo(tmp_path):
    _fixture_repo(tmp_path)
    kernel = _kernel(tmp_path)
    req = _request(tmp_path)
    plan = CodeTaskPlanner().create_plan(req, RepoContextBuilder().build(req))
    result = PatchExecutor(kernel.runtime, _card(), str(tmp_path)).apply(req, plan.patch_plans)
    assert result.applied
    assert "src/calc.py" in result.files_changed
    assert "return a + b" in (tmp_path / "src" / "calc.py").read_text()


def test_patch_executor_rejects_path_traversal(tmp_path):
    _fixture_repo(tmp_path)
    kernel = _kernel(tmp_path)
    req = _request(tmp_path)
    bad = PatchPlan("../evil.py", content="x")
    result = PatchExecutor(kernel.runtime, _card(), str(tmp_path)).apply(req, [bad])
    assert not result.applied
    assert result.errors


def test_patch_executor_enforces_max_files_changed(tmp_path):
    _fixture_repo(tmp_path)
    kernel = _kernel(tmp_path)
    req = _request(tmp_path, max_files_changed=1)
    patches = [PatchPlan("src/a.py", content="x"), PatchPlan("src/b.py", content="y")]
    result = PatchExecutor(kernel.runtime, _card(), str(tmp_path)).apply(req, patches)
    assert not result.applied
    assert result.errors == ["max_files_changed exceeded"]


def test_patch_executor_uses_runtime_submit(tmp_path):
    _fixture_repo(tmp_path)
    calls = []

    class FakeRuntime:
        def submit(self, cmd: CommandEnvelope, card):
            calls.append(cmd.tool)
            class R:
                ok = True
                approval_receipt = None
                observation = type("O", (), {"artifacts": {"summary": "ok"}, "stderr": ""})()
                verifier = type("V", (), {"reason": ""})()
            return R()

    req = _request(tmp_path)
    result = PatchExecutor(FakeRuntime(), _card(), str(tmp_path)).apply(
        req, [PatchPlan("src/calc.py", content="x")])
    assert result.applied
    assert calls == ["write_file"]


def test_test_runner_adapter_captures_success(tmp_path):
    _fixture_repo(tmp_path)
    _write(tmp_path / "src" / "calc.py", "def add(a, b):\n    return a + b\n")
    kernel = _kernel(tmp_path)
    result = RunnerAdapter(kernel.runtime, _card()).run(_request(tmp_path))
    assert result.exit_code == 0
    assert result.passed


def test_test_runner_adapter_timeout_handled(tmp_path):
    _fixture_repo(tmp_path)
    kernel = _kernel(tmp_path)
    req = _request(tmp_path, test_command=["python3", "-c", "import time; time.sleep(2)"])
    runner = RunnerAdapter(kernel.runtime, _card(), default_timeout=1)
    result = runner.run(req)
    assert result.timed_out or result.exit_code != 0


def test_failure_analyzer_basic_parse():
    result = type("R", (), {
        "stdout": "FAILED tests/test_x.py::test_bad - AssertionError",
        "stderr": "",
        "passed": False,
        "timed_out": False,
    })()
    analysis = FailureAnalyzer().analyze(result)
    assert "assertion" in analysis["summary"]
    assert analysis["failing_tests"]


def test_repair_loop_stops_after_max_iterations(tmp_path):
    _fixture_repo(tmp_path)
    kernel = _kernel(tmp_path)
    req = _request(tmp_path, test_command=["python3", "-c", "import sys; sys.exit(1)"],
                   max_repair_iterations=2)
    executor = PatchExecutor(kernel.runtime, _card(), str(tmp_path))
    runner = RunnerAdapter(kernel.runtime, _card())
    patch_result, test_result, attempts = RepairLoop(executor, runner).run(req, [])
    assert not test_result.passed
    assert len(attempts) == 1


def test_repair_loop_records_attempt_and_succeeds(tmp_path):
    _fixture_repo(tmp_path)
    kernel = _kernel(tmp_path)
    req = _request(tmp_path)
    plan = CodeTaskPlanner().create_plan(req, RepoContextBuilder().build(req))
    executor = PatchExecutor(kernel.runtime, _card(), str(tmp_path))
    runner = RunnerAdapter(kernel.runtime, _card())
    patch_result, test_result, attempts = RepairLoop(executor, runner).run(req, plan.patch_plans)
    assert patch_result.applied
    assert test_result.passed
    assert attempts[0].files_touched == ["src/calc.py"]


def test_repository_loop_plan_only_report(tmp_path):
    _fixture_repo(tmp_path)
    report = RepositoryAgentLoop().run(_request(tmp_path), apply=False)
    assert report.final_status == "planned"
    assert report.files_inspected
    assert not report.files_changed


def test_repository_loop_end_to_end_tiny_fixture(tmp_path):
    _fixture_repo(tmp_path)
    report = RepositoryAgentLoop().run(_request(tmp_path), apply=True)
    assert report.final_status == "succeeded"
    assert report.test_result.passed
    assert report.files_changed == ["src/calc.py"]
    assert "return a + b" in (tmp_path / "src" / "calc.py").read_text()


def test_repository_loop_failure_report_clean(tmp_path):
    _fixture_repo(tmp_path)
    req = _request(tmp_path, objective="inspect only", test_command=["python3", "-c", "import sys; sys.exit(1)"])
    report = RepositoryAgentLoop().run(req, apply=True)
    assert report.final_status == "failed"
    assert report.test_result.exit_code != 0
