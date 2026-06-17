"""P0.17.1 — Pre-P0.20 readiness regression tests."""

from __future__ import annotations

from agentic_runtime import AgentCard, AgentClass, AuthorityScope, RiskLevel, build_runtime
from agentic_runtime.approval import ApprovalRequest, ApprovalRiskClass
from agentic_runtime.core_types import CommandEnvelope
from agentic_runtime.hitl import AutoApprover
from agentic_runtime.policy import PolicyDecision, PolicyVerdict
from agentic_runtime.repo_agent import (
    RepoContextBuilder,
    RepoTaskRequest,
    RepositoryAgentLoop,
    TestRunnerAdapter,
    _approval_gate_for,
)
from agentic_runtime.sandbox import UnsafeLocalSandbox


def _card():
    return AgentCard.make(
        "t", AgentClass.EXECUTION, "m",
        AuthorityScope(write_paths=["*"], read_paths=["*"], max_risk=RiskLevel.HIGH),
        allowed_tools=["run_tests", "run_shell", "read_file", "write_file", "patch_file"],
    )


def _cmd(card, tool, args):
    return CommandEnvelope.make(
        issuer_card_id=card.id,
        tool=tool,
        args=args,
        rationale="test",
        declared_risk=RiskLevel.LOW,
        expected_effect="test",
    )


# --------------------------------------------------------------------------- #
# PATCH 1 — missing README.md
# --------------------------------------------------------------------------- #
def test_context_builder_missing_readme_does_not_crash(tmp_path):
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'\n", encoding="utf-8")
    (tmp_path / "app.txt").write_text("old\n", encoding="utf-8")
    req = RepoTaskRequest.make(
        "replace 'old' with 'new' in app.txt",
        repo_path=str(tmp_path),
        allowed_paths=["*"],
    )
    ctx = RepoContextBuilder().build(req)
    assert ctx.repo_root == str(tmp_path.resolve())
    assert not any(s.path == "README.md" and not s.skipped_reason for s in ctx.file_summaries)


def test_repository_loop_missing_readme_does_not_crash(tmp_path):
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'\n", encoding="utf-8")
    (tmp_path / "app.txt").write_text("old\n", encoding="utf-8")
    req = RepoTaskRequest.make(
        "replace 'old' with 'new' in app.txt",
        repo_path=str(tmp_path),
        allowed_paths=["*"],
    )
    report = RepositoryAgentLoop().run(req, apply=False)
    assert report.final_status in {"planned", "dry_run"}


# --------------------------------------------------------------------------- #
# PATCH 2 — TestRunnerAdapter contract
# --------------------------------------------------------------------------- #
def test_test_runner_pytest_list_uses_run_tests_contract(tmp_path):
    kernel = build_runtime(
        sandbox=UnsafeLocalSandbox(root=str(tmp_path)),
        approval_gate=AutoApprover(lambda r: True, allow_r2=True, allow_r3=True),
    )
    card = _card()
    req = RepoTaskRequest.make("x", repo_path=str(tmp_path), test_command=["python3", "-m", "pytest", "-q"])
    result = TestRunnerAdapter(kernel.runtime, card).run(req)
    assert isinstance(result.command, list)
    assert "wrong_arg_type" not in result.stderr
    assert "TOOL CONTRACT VIOLATION" not in result.stderr


def test_test_runner_python_c_list_uses_run_tests(tmp_path):
    kernel = build_runtime(
        sandbox=UnsafeLocalSandbox(root=str(tmp_path)),
        approval_gate=AutoApprover(lambda r: True, allow_r2=True, allow_r3=True),
    )
    card = _card()
    req = RepoTaskRequest.make(
        "x",
        repo_path=str(tmp_path),
        test_command=["python3", "-c", "print('ok')"],
    )
    result = TestRunnerAdapter(kernel.runtime, card).run(req)
    assert "wrong_arg_type" not in result.stderr
    assert result.exit_code == 0


def test_test_runner_simple_py_file(tmp_path):
    test_file = tmp_path / "t.py"
    test_file.write_text("assert True\n", encoding="utf-8")
    kernel = build_runtime(
        sandbox=UnsafeLocalSandbox(root=str(tmp_path)),
        approval_gate=AutoApprover(lambda r: True, allow_r2=True, allow_r3=True),
    )
    card = _card()
    req = RepoTaskRequest.make("x", repo_path=str(tmp_path), test_command=["python3", "t.py"])
    result = TestRunnerAdapter(kernel.runtime, card).run(req)
    assert result.passed


# --------------------------------------------------------------------------- #
# PATCH 3 — AutoApprover predicate narrowing
# --------------------------------------------------------------------------- #
def _approval_req(card, tool, args, risk_class):
    cmd = _cmd(card, tool, args)
    decision = PolicyDecision(PolicyVerdict.ALLOW, RiskLevel.HIGH, ["ok"])
    return ApprovalRequest.build(cmd, decision, risk_class=risk_class, preview=None)


def test_auto_approver_predicate_true_does_not_approve_r4():
    card = _card()
    approver = AutoApprover(lambda r: True, allow_r2=True, allow_r3=True)
    req = _approval_req(card, "run_shell", {"cmd": ["echo", "hi"]}, ApprovalRiskClass.R4)
    assert not approver.request(req).approved


def test_auto_approver_predicate_true_does_not_approve_r5():
    card = _card()
    approver = AutoApprover(lambda r: True, allow_r5=False)
    req = _approval_req(card, "run_shell", {"cmd": ["rm", "-rf", "/"]}, ApprovalRiskClass.R5)
    assert not approver.request(req).approved


def test_auto_approver_predicate_false_denies_r2_even_when_allowed():
    card = _card()
    approver = AutoApprover(lambda r: False, allow_r2=True)
    req = _approval_req(card, "write_file", {"path": "a.txt", "content": "x"}, ApprovalRiskClass.R2)
    assert not approver.request(req).approved


# --------------------------------------------------------------------------- #
# PATCH 4 — repo auto approval envelope
# --------------------------------------------------------------------------- #
def test_repo_auto_approval_gate_denies_r4_shell(tmp_path):
    gate = _approval_gate_for(RepoTaskRequest.make("x", approval_mode="auto"))
    card = _card()
    req = _approval_req(card, "run_shell", {"cmd": ["echo", "hi"]}, ApprovalRiskClass.R4)
    assert not gate.request(req).approved


def test_repo_auto_approval_gate_allows_r2_write(tmp_path):
    gate = _approval_gate_for(RepoTaskRequest.make("x", approval_mode="auto"))
    card = _card()
    req = _approval_req(card, "write_file", {"path": "a.txt", "content": "x"}, ApprovalRiskClass.R2)
    assert gate.request(req).approved
