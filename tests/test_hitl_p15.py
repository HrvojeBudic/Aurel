"""P0.15 — HITL / approval upgrade tests."""

from __future__ import annotations

from agentic_runtime import (
    AgentCard,
    AgentClass,
    ApprovalMode,
    ApprovalOutcome,
    ApprovalPolicy,
    ApprovalReceipt,
    ApprovalRequest,
    ApprovalRiskClass,
    AuthorityScope,
    AutoApprover,
    ConsoleApprover,
    DenyAllApprover,
    PreviewOnlyApprover,
    RiskLevel,
    build_preview,
    build_runtime,
    classify_risk,
)
from agentic_runtime.core_types import CommandEnvelope
from agentic_runtime.hitl import make_approval_gate
from agentic_runtime.policy import PolicyDecision, PolicyVerdict
from agentic_runtime.sandbox import UnsafeLocalSandbox


def _card(**kw):
    defaults = dict(
        name="Approval Test Agent",
        agent_class=AgentClass.EXECUTION,
        mission="approval tests",
        authority=AuthorityScope(write_paths=["*"], read_paths=["*"],
                                 max_risk=RiskLevel.HIGH),
        allowed_tools=[
            "read_file", "write_file", "patch_file", "run_shell", "run_tests",
        ],
    )
    defaults.update(kw)
    return AgentCard.make(**defaults)


def _cmd(card, tool, args, risk=RiskLevel.LOW):
    return CommandEnvelope.make(
        issuer_card_id=card.id,
        tool=tool,
        args=args,
        rationale="approval test",
        declared_risk=risk,
        expected_effect="test",
    )


def _kernel(tmp_path, gate):
    return build_runtime(
        sandbox=UnsafeLocalSandbox(root=str(tmp_path)),
        approval_gate=gate,
    )


def test_approval_request_creation():
    card = _card()
    cmd = _cmd(card, "read_file", {"path": "a.txt"})
    decision = PolicyDecision(PolicyVerdict.ALLOW, RiskLevel.TRIVIAL, ["ok"])
    req = ApprovalRequest.build(
        cmd,
        decision,
        risk_class=ApprovalRiskClass.R0,
        preview=None,
    )
    assert req.request_id
    assert req.command_id == cmd.id
    assert req.command.tool == "read_file"
    assert req.risk_class is ApprovalRiskClass.R0


def test_approval_decision_and_receipt_creation():
    card = _card()
    cmd = _cmd(card, "write_file", {"path": "a.txt", "content": "x"})
    decision = PolicyDecision(PolicyVerdict.ALLOW, RiskLevel.MEDIUM, ["ok"])
    req = ApprovalRequest.build(
        cmd,
        decision,
        risk_class=ApprovalRiskClass.R2,
        preview=build_preview(cmd, UnsafeLocalSandbox(root=".")),
    )
    approval = ConsoleApprover(input_fn=lambda _: "y").request(req)
    assert approval.approved
    receipt = ApprovalReceipt.from_decision(req, approval)
    assert receipt.receipt_id
    assert receipt.tool_name == "write_file"
    assert receipt.risk_class is ApprovalRiskClass.R2


def test_policy_r0_auto_allow():
    card = _card()
    cmd = _cmd(card, "read_file", {"path": "a.txt"})
    decision = PolicyDecision(PolicyVerdict.ALLOW, RiskLevel.TRIVIAL, ["ok"])
    req = ApprovalPolicy().resolve(cmd, decision)
    assert req.auto_allow
    assert not req.required


def test_policy_r1_auto_allow():
    card = _card()
    cmd = _cmd(card, "list_dir", {"path": "."})
    decision = PolicyDecision(PolicyVerdict.ALLOW, RiskLevel.LOW, ["ok"])
    req = ApprovalPolicy().resolve(cmd, decision)
    assert req.auto_allow
    assert classify_risk(cmd, decision) is ApprovalRiskClass.R0


def test_policy_r2_preview_required():
    card = _card()
    cmd = _cmd(card, "write_file", {"path": "a.txt", "content": "x"})
    decision = PolicyDecision(PolicyVerdict.ALLOW, RiskLevel.MEDIUM, ["ok"])
    req = ApprovalPolicy().resolve(cmd, decision)
    assert req.preview_required
    assert req.required
    assert req.risk_class is ApprovalRiskClass.R2


def test_policy_r3_explicit_approval_required():
    card = _card()
    cmd = _cmd(card, "run_tests", {"test_file": "t.py"})
    decision = PolicyDecision(PolicyVerdict.ALLOW, RiskLevel.HIGH, ["exec"])
    req = ApprovalPolicy().resolve(cmd, decision)
    assert req.required
    assert req.risk_class is ApprovalRiskClass.R3


def test_policy_r4_warning_for_run_shell():
    card = _card()
    cmd = _cmd(card, "run_shell", {"cmd": ["echo", "hi"]})
    decision = PolicyDecision(PolicyVerdict.ALLOW, RiskLevel.HIGH, ["shell"])
    req = ApprovalPolicy().resolve(cmd, decision)
    assert req.strong_warning
    assert req.risk_class is ApprovalRiskClass.R4


def test_policy_r5_denied_by_default():
    card = _card()
    cmd = _cmd(card, "run_shell", {"cmd": ["rm", "-rf", "."], "irreversible": True})
    decision = PolicyDecision(PolicyVerdict.ALLOW, RiskLevel.CRITICAL, ["destructive"])
    req = ApprovalPolicy().resolve(cmd, decision)
    assert req.auto_deny
    assert req.confirmation_level == 2


def test_auto_approver_allows_safe_and_blocks_r5():
    card = _card()
    cmd = _cmd(card, "read_file", {"path": "a.txt"})
    decision = PolicyDecision(PolicyVerdict.ALLOW, RiskLevel.TRIVIAL, ["ok"])
    req = ApprovalRequest.build(cmd, decision, risk_class=ApprovalRiskClass.R0, preview=None)
    assert AutoApprover().request(req).approved

    destructive = ApprovalRequest.build(
        _cmd(card, "delete_file", {"path": "x"}),
        PolicyDecision(PolicyVerdict.ALLOW, RiskLevel.CRITICAL, ["x"]),
        risk_class=ApprovalRiskClass.R5,
        preview=None,
    )
    assert not AutoApprover().request(destructive).approved


def test_deny_all_approver_denies():
    card = _card()
    cmd = _cmd(card, "read_file", {"path": "a.txt"})
    req = ApprovalRequest.build(
        cmd,
        PolicyDecision(PolicyVerdict.ALLOW, RiskLevel.TRIVIAL, ["ok"]),
        risk_class=ApprovalRiskClass.R0,
        preview=None,
    )
    assert DenyAllApprover().request(req).outcome is ApprovalOutcome.DENIED


def test_console_approver_two_step_for_r5(tmp_path):
    card = _card()
    cmd = _cmd(card, "run_shell", {"cmd": ["rm", "-rf", "."]})
    req = ApprovalRequest.build(
        cmd,
        PolicyDecision(PolicyVerdict.ALLOW, RiskLevel.CRITICAL, ["destructive"]),
        risk_class=ApprovalRiskClass.R5,
        preview=build_preview(cmd, UnsafeLocalSandbox(root=str(tmp_path))),
        confirmation_level=2,
        strong_warning=True,
    )
    approver = ConsoleApprover(input_fn=lambda prompt: "YES" if "YES" in prompt else "y")
    assert approver.request(req).approved


def test_auto_approver_predicate_cannot_widen_r4():
    card = _card()
    cmd = _cmd(card, "run_shell", {"cmd": ["echo", "hi"]})
    req = ApprovalRequest.build(
        cmd, PolicyDecision(PolicyVerdict.ALLOW, RiskLevel.HIGH, ["shell"]),
        risk_class=ApprovalRiskClass.R4, preview=None,
    )
    assert not AutoApprover(lambda r: True, allow_r2=True, allow_r3=True).request(req).approved


def test_auto_approver_predicate_cannot_widen_r5():
    card = _card()
    cmd = _cmd(card, "run_shell", {"cmd": ["rm", "-rf", "/"]})
    req = ApprovalRequest.build(
        cmd, PolicyDecision(PolicyVerdict.ALLOW, RiskLevel.CRITICAL, ["destructive"]),
        risk_class=ApprovalRiskClass.R5, preview=None,
    )
    assert not AutoApprover(lambda r: True, allow_r5=False).request(req).approved


def test_runtime_r0_executes_without_manual_gate(tmp_path):
    kernel = _kernel(tmp_path, AutoApprover())
    card = _card()
    kernel.sandbox.write_file("a.txt", "hello")
    res = kernel.runtime.submit(_cmd(card, "read_file", {"path": "a.txt"}), card)
    assert res.ok
    assert res.approval_receipt is not None
    assert res.approval_receipt.decision is ApprovalOutcome.AUTO_APPROVED


def test_runtime_r2_write_requires_approval_and_can_deny(tmp_path):
    kernel = _kernel(tmp_path, DenyAllApprover())
    card = _card()
    res = kernel.runtime.submit(
        _cmd(card, "write_file", {"path": "a.txt", "content": "x"}),
        card,
    )
    assert not res.ok
    assert res.verifier.code == "HITL_DENIED"
    assert res.approval_receipt is not None
    try:
        kernel.sandbox.read_file("a.txt")
    except OSError:
        return
    raise AssertionError("denied write should not create file")


def test_runtime_approval_receipt_traced(tmp_path):
    kernel = _kernel(tmp_path, AutoApprover(lambda r: True, allow_r2=True))
    card = _card()
    res = kernel.runtime.submit(
        _cmd(card, "write_file", {"path": "a.txt", "content": "x"}),
        card,
    )
    assert res.ok
    kinds = [row["kind"] for row in kernel.trace.replay()]
    assert "approval_receipt" in kinds


def test_preview_redacts_secrets(tmp_path):
    card = _card()
    cmd = _cmd(card, "write_file", {
        "path": "a.txt",
        "content": "token=sk-abcdefghijklmnopqrstuvwxyz",
    })
    preview = build_preview(cmd, UnsafeLocalSandbox(root=str(tmp_path)))
    assert "sk-abc" not in preview.after_summary
    assert "[REDACTED]" in preview.after_summary or "..." in preview.after_summary


def test_repo_agent_dry_run_reports_approval_requirements(tmp_path):
    from agentic_runtime.repo_agent import RepositoryAgentLoop, RepoTaskRequest

    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "calc.py").write_text("def add(a, b):\n    return a - b\n", encoding="utf-8")
    (tmp_path / "test_calc.py").write_text(
        "from src.calc import add\nassert add(2, 3) == 5\n", encoding="utf-8")
    req = RepoTaskRequest.make(
        objective="replace 'return a - b' with 'return a + b' in src/calc.py",
        repo_path=str(tmp_path),
        allowed_paths=["src", "test_calc.py"],
        test_command=["python3", "test_calc.py"],
        approval_mode="deny",
    )
    report = RepositoryAgentLoop().run(req, apply=False, dry_run=True)
    assert report.final_status == "dry_run"
    assert report.approval_summaries
    assert report.approval_summaries[0]["risk_class"] == "R2"
    assert report.approval_summaries[0]["preview_required"] is True
