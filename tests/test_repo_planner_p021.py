"""P0.21 -- LLM planning bridge for RepositoryAgentLoop."""

from __future__ import annotations

from pathlib import Path
import sys

from agentic_runtime import build_runtime
from agentic_runtime.demo_harness import (
    BUGGY_CALCULATOR,
    MISSING_VALIDATION,
    DemoHarness,
    DemoHarnessRequest,
    DemoRepoFactory,
    get_scenario,
    list_scenarios,
    run_tests,
)
from agentic_runtime.hitl import AutoApprover
from agentic_runtime.model_providers.mock_provider import MockProvider
from agentic_runtime.model_router import ProviderModelClient
from agentic_runtime.repo_agent import (
    LLMRepoPlanner,
    REPO_PLAN_SCHEMA,
    RepoContextBuilder,
    RepoPlanValidator,
    RepoTaskRequest,
    RepositoryAgentLoop,
)
from agentic_runtime.sandbox import UnsafeLocalSandbox


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _validation_repo(tmp_path: Path) -> Path:
    _write(tmp_path / "pyproject.toml", "[project]\nname = \"fixture\"\nversion = \"0.1\"\n")
    _write(tmp_path / "calculator.py", "def divide(a, b):\n    return a / b\n")
    _write(tmp_path / "test_calculator.py", (
        "import pytest\nfrom calculator import divide\n\n"
        "def test_valid():\n    assert divide(10, 2) == 5\n\n"
        "def test_zero():\n    with pytest.raises(ValueError):\n        divide(10, 0)\n"
    ))
    return tmp_path


def _request(repo: Path, **kw) -> RepoTaskRequest:
    data = dict(
        objective="Add explicit zero-division validation to divide() in calculator.py and keep valid division behavior.",
        repo_path=str(repo),
        allowed_paths=["calculator.py", "test_calculator.py", "pyproject.toml"],
        disallowed_paths=[".env", "secrets/*"],
        max_files_changed=1,
        test_command=[sys.executable, "-m", "pytest", "-q"],
        require_approval_before_write=False,
    )
    data.update(kw)
    return RepoTaskRequest.make(**data)


def _kernel(repo: Path, provider: MockProvider | None = None):
    kwargs = {}
    if provider is not None:
        kwargs["model_clients"] = {"balanced": [ProviderModelClient(provider)]}
    return build_runtime(
        sandbox=UnsafeLocalSandbox(root=str(repo)),
        approval_gate=AutoApprover(lambda r: True, allow_r2=True, allow_r3=True),
        **kwargs,
    )


def _valid_payload(**overrides):
    payload = {
        "objective_summary": "Add explicit zero-division validation.",
        "files_to_inspect": ["calculator.py", "test_calculator.py"],
        "files_to_modify": ["calculator.py"],
        "proposed_steps": [
            {
                "step_id": "inspect",
                "action_type": "inspect",
                "target_path": "calculator.py",
                "tool_name": "read_file",
                "reason": "Inspect implementation.",
                "expected_output": "Source context.",
                "risk_class": "low",
            },
            {
                "step_id": "patch",
                "action_type": "patch",
                "target_path": "calculator.py",
                "tool_name": "patch_file",
                "reason": "Patch implementation through runtime.",
                "expected_output": "Zero division raises ValueError.",
                "risk_class": "medium",
            },
            {
                "step_id": "test",
                "action_type": "test",
                "tool_name": "run_tests",
                "reason": "Run configured tests.",
                "expected_output": "Tests pass.",
                "risk_class": "medium",
            },
        ],
        "risk_level": "medium",
        "expected_tests": ["python -m pytest -q"],
        "requires_approval": True,
        "assumptions": [],
        "refusal_reason": None,
    }
    payload.update(overrides)
    return payload


def test_default_planner_mode_is_deterministic(tmp_path):
    repo = _validation_repo(tmp_path)
    report = RepositoryAgentLoop(kernel=_kernel(repo)).run(_request(repo), apply=False)
    assert report.final_status == "planned"
    assert report.planner_mode == "deterministic"
    assert report.model_provider == ""


def test_llm_mode_calls_mock_provider_and_builds_repo_plan(tmp_path):
    repo = _validation_repo(tmp_path)
    req = _request(repo, planner_mode="llm", model_provider="mock")
    plan = LLMRepoPlanner().create_plan(req, RepoContextBuilder().build(req))
    assert plan.valid
    assert plan.provider_name == "mock"
    assert plan.files_to_modify == ["calculator.py"]
    assert plan.patch_plans


def test_repo_plan_validator_rejects_invalid_json(tmp_path):
    repo = _validation_repo(tmp_path)
    req = _request(repo)
    result = RepoPlanValidator().validate_json("{not json", req)
    assert not result.ok
    assert "invalid_json" in result.errors[0]


def test_repo_plan_validator_rejects_missing_required_field(tmp_path):
    repo = _validation_repo(tmp_path)
    req = _request(repo)
    payload = _valid_payload()
    payload.pop("expected_tests")
    result = RepoPlanValidator().validate_payload(payload, req)
    assert not result.ok
    assert any("expected_tests" in e for e in result.errors)


def test_repo_plan_validator_rejects_disallowed_path(tmp_path):
    repo = _validation_repo(tmp_path)
    req = _request(repo, disallowed_paths=["secrets/*"])
    result = RepoPlanValidator().validate_payload(
        _valid_payload(files_to_modify=["secrets/key.txt"]), req)
    assert not result.ok
    assert any("not allowed" in e for e in result.errors)


def test_repo_plan_validator_rejects_too_many_files(tmp_path):
    repo = _validation_repo(tmp_path)
    req = _request(repo, max_files_changed=1)
    result = RepoPlanValidator().validate_payload(
        _valid_payload(files_to_modify=["calculator.py", "other.py"]), req)
    assert not result.ok
    assert any("max_files_changed" in e for e in result.errors)


def test_repo_plan_validator_rejects_test_weakening(tmp_path):
    repo = _validation_repo(tmp_path)
    req = _request(repo)
    payload = _valid_payload(files_to_modify=["test_calculator.py"])
    payload["proposed_steps"][1]["target_path"] = "test_calculator.py"
    result = RepoPlanValidator().validate_payload(payload, req)
    assert not result.ok
    assert any("test file" in e for e in result.errors)


def test_refusal_creates_no_executable_plan(tmp_path):
    repo = _validation_repo(tmp_path)
    req = _request(repo)
    result = RepoPlanValidator().validate_payload(
        _valid_payload(
            files_to_inspect=[],
            files_to_modify=[],
            proposed_steps=[],
            expected_tests=[],
            refusal_reason="unsafe objective",
        ),
        req,
    )
    assert result.ok
    assert result.refusal_reason == "unsafe objective"


def test_llm_invalid_plan_fails_safely_in_loop(tmp_path):
    repo = _validation_repo(tmp_path)
    report = RepositoryAgentLoop(kernel=_kernel(repo, MockProvider(failure_mode="invalid_json"))).run(
        _request(repo, planner_mode="llm"), apply=True)
    assert report.final_status == "planning_failed"
    assert report.files_changed == []
    assert report.planning_errors


def test_hybrid_falls_back_safely_and_records_reason(tmp_path):
    repo = _validation_repo(tmp_path)
    report = RepositoryAgentLoop(kernel=_kernel(repo, MockProvider(failure_mode="invalid_json"))).run(
        _request(repo, planner_mode="hybrid"), apply=True)
    assert report.final_status == "succeeded"
    assert report.planner_mode == "hybrid"
    assert report.fallback_reason
    assert report.files_changed == ["calculator.py"]


def test_dry_run_mode_produces_no_patch(tmp_path):
    repo = _validation_repo(tmp_path)
    report = RepositoryAgentLoop(kernel=_kernel(repo)).run(
        _request(repo, planner_mode="dry_run"), apply=True)
    assert report.final_status == "dry_run"
    assert report.files_changed == []
    assert "raise ValueError" not in (repo / "calculator.py").read_text(encoding="utf-8")


def test_llm_loop_preserves_approval_and_sandbox_path(tmp_path):
    repo = _validation_repo(tmp_path)
    report = RepositoryAgentLoop(kernel=_kernel(repo)).run(
        _request(repo, planner_mode="llm", model_provider="mock"), apply=True)
    assert report.final_status == "succeeded"
    assert report.approval_summaries
    assert report.sandbox_profile
    assert report.files_changed == ["calculator.py"]


def test_prompt_redacts_secret_and_summarizes_huge_file(tmp_path):
    repo = _validation_repo(tmp_path)
    _write(repo / "huge.py", "password = super-secret-token\n" + "x" * 50000)
    req = _request(repo, allowed_paths=["*"], planner_mode="llm")
    ctx = RepoContextBuilder(max_file_bytes=128).build(req)
    _system, user = LLMRepoPlanner()._build_prompt(req, ctx)
    assert "super-secret-token" not in user
    assert "truncated" in user


def test_demo_harness_lists_missing_validation():
    ids = {s.scenario_id for s in list_scenarios()}
    assert "buggy_calculator" in ids
    assert "missing_validation" in ids
    assert get_scenario("missing_validation") is MISSING_VALIDATION


def test_missing_validation_initial_test_fails(tmp_path):
    repo = DemoRepoFactory().create(MISSING_VALIDATION, tmp_path)
    result = run_tests(repo, MISSING_VALIDATION.test_command)
    assert not result.passed


def test_missing_validation_mock_llm_plan_and_final_success(tmp_path):
    report = DemoHarness().run(DemoHarnessRequest(
        scenario_id="missing_validation",
        repo_parent=tmp_path,
        apply=True,
        planner_mode="llm",
        model_provider="mock",
    ))
    assert report.final_status == "succeeded"
    assert report.planner_mode == "llm"
    assert report.files_changed == ["calculator.py"]
    assert report.final_test_result and report.final_test_result.passed
    assert "raise ValueError" in Path(report.repo_path, "calculator.py").read_text(encoding="utf-8")


def test_buggy_calculator_still_succeeds_deterministically(tmp_path):
    report = DemoHarness().run(DemoHarnessRequest(
        scenario_id=BUGGY_CALCULATOR.scenario_id,
        repo_parent=tmp_path,
        apply=True,
    ))
    assert report.final_status == "succeeded"
    assert report.planner_mode == "deterministic"
    assert report.files_changed == ["calculator.py"]


def test_repo_plan_schema_exposes_required_fields():
    required = set(REPO_PLAN_SCHEMA["required"])
    assert "objective_summary" in required
    assert "files_to_modify" in required
    assert "refusal_reason" in required


def test_deterministic_planner_refuses_objective_without_patch_strategy(tmp_path):
    repo = _validation_repo(tmp_path)
    req = _request(repo, objective="fix the add function bug in calculator.py so tests pass")
    report = RepositoryAgentLoop(kernel=_kernel(repo)).run(req, apply=False)
    assert report.final_status == "planning_failed"
    assert any("no patch strategy" in e for e in report.planning_errors)


def test_demo_heuristic_alias_maps_to_deterministic(tmp_path):
    repo = _validation_repo(tmp_path)
    req = _request(repo, planner_mode="demo-heuristic")
    report = RepositoryAgentLoop(kernel=_kernel(repo)).run(req, apply=False)
    assert report.planner_mode == "deterministic"
    assert report.final_status == "planned"
