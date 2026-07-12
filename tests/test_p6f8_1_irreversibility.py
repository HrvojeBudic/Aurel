"""F8.1 — Irreversibility gate: fork-before-irreversible as HITL evidence."""
from __future__ import annotations

from dataclasses import dataclass

import pytest

from agentic_runtime import (
    AgentCard,
    AgentClass,
    ApprovalPolicy,
    AuthorityScope,
    RiskLevel,
    UnsafeLocalSandbox,
    build_runtime,
)
from agentic_runtime.chronos.fork_gate import (
    ForkGateEvidence,
    evaluate_fork_gate,
    flag_enabled as fork_gate_flag_enabled,
)
from agentic_runtime.chronos.irreversibility import (
    IrreversibilityClass,
    classify_irreversibility,
    influence_is_escalation_only,
)
from agentic_runtime.core_types import CommandEnvelope
from agentic_runtime.hitl import AutoApprover


def _card(**tools: object) -> AgentCard:
    allowed = tools.get("allowed_tools") or [
        "read_file", "write_file", "delete_file", "run_shell", "list_dir",
    ]
    return AgentCard.make(
        name="F8.1 Agent",
        agent_class=AgentClass.EXECUTION,
        mission="irreversibility gate test",
        authority=AuthorityScope(
            write_paths=["*"], read_paths=["*"], max_risk=RiskLevel.HIGH,
        ),
        allowed_tools=list(allowed),  # type: ignore[arg-type]
    )


def _cmd(card: AgentCard, tool: str, args: dict, *, risk: RiskLevel = RiskLevel.HIGH) -> CommandEnvelope:
    return CommandEnvelope.make(
        issuer_card_id=card.id,
        tool=tool,
        args=args,
        rationale="f8.1",
        declared_risk=risk,
        expected_effect="f8.1",
    )


@dataclass
class RecordingApprover:
    inner: AutoApprover
    last_request: object = None

    def request(self, request):
        self.last_request = request
        return self.inner.request(request)


def _kernel(tmp_path, gate=None, *, deny_r5_by_default: bool = True):
    return build_runtime(
        sandbox=UnsafeLocalSandbox(root=str(tmp_path / "ws")),
        approval_gate=gate or AutoApprover(lambda r: True, allow_r5=True),
        approval_policy=ApprovalPolicy(deny_r5_by_default=deny_r5_by_default),
    )


@pytest.fixture(autouse=True)
def _fork_gate_off(monkeypatch):
    monkeypatch.delenv("AUREL_CHRONOS_FORK_GATE", raising=False)


def test_irreversible_action_classified():
    card = _card()
    cmd = _cmd(card, "delete_file", {"path": "src/x.py"})
    result = classify_irreversibility(cmd, None, None)
    assert result.klass is IrreversibilityClass.IRREVERSIBLE
    assert result.reason


def test_reversible_write_not_forked(tmp_path, monkeypatch):
    monkeypatch.setenv("AUREL_CHRONOS_FORK_GATE", "1")
    recorder = RecordingApprover(AutoApprover(lambda r: True, allow_r2=True, allow_r5=True))
    kernel = _kernel(tmp_path, recorder)
    card = _card()
    (tmp_path / "ws" / "src").mkdir(parents=True)
    result = kernel.runtime.submit(
        _cmd(card, "write_file", {"path": "src/a.py", "content": "x\n"}, risk=RiskLevel.LOW),
        card,
    )
    assert result.ok
    ctx = getattr(recorder.last_request, "context", "") if recorder.last_request else ""
    assert "fork_gate|" not in ctx


def test_fork_gate_attaches_evidence_to_approval(tmp_path, monkeypatch):
    monkeypatch.setenv("AUREL_CHRONOS_FORK_GATE", "1")
    recorder = RecordingApprover(
        AutoApprover(lambda r: True, allow_r2=True, allow_r3=True, allow_r4=True, allow_r5=True)
    )
    kernel = _kernel(tmp_path, recorder, deny_r5_by_default=False)
    card = _card()
    (tmp_path / "ws" / "src").mkdir(parents=True)
    (tmp_path / "ws" / "src" / "x.py").write_text("keep\n", encoding="utf-8")
    result = kernel.runtime.submit(
        _cmd(card, "delete_file", {"path": "src/x.py"}),
        card,
    )
    assert result.ok
    assert recorder.last_request is not None
    assert "fork_gate|" in recorder.last_request.context


def test_evidence_is_escalation_only(tmp_path, monkeypatch):
    monkeypatch.setenv("AUREL_CHRONOS_FORK_GATE", "1")
    kernel = _kernel(tmp_path, deny_r5_by_default=False)
    card = _card()
    (tmp_path / "ws" / "src").mkdir(parents=True)
    (tmp_path / "ws" / "src" / "x.py").write_text("keep\n", encoding="utf-8")
    cmd = _cmd(card, "delete_file", {"path": "src/x.py"})
    evidence = evaluate_fork_gate(cmd, card, kernel.runtime, None)
    assert evidence.available
    assert influence_is_escalation_only(evidence)
    assert evidence.is_escalation_only is True


def test_evidence_cannot_auto_permit_r5(tmp_path, monkeypatch):
    monkeypatch.setenv("AUREL_CHRONOS_FORK_GATE", "1")
    deny_r5 = AutoApprover(lambda r: False, allow_r5=False)
    recorder = RecordingApprover(deny_r5)
    kernel = _kernel(tmp_path, recorder, deny_r5_by_default=False)
    card = _card()
    (tmp_path / "ws" / "src").mkdir(parents=True)
    (tmp_path / "ws" / "src" / "x.py").write_text("keep\n", encoding="utf-8")
    result = kernel.runtime.submit(
        _cmd(card, "delete_file", {"path": "src/x.py"}),
        card,
    )
    assert not result.ok
    assert "fork_gate|" in recorder.last_request.context


def test_unavailable_twin_fail_closed(tmp_path, monkeypatch):
    monkeypatch.setenv("AUREL_CHRONOS_FORK_GATE", "1")
    monkeypatch.setattr(
        "agentic_runtime.chronos.fork_gate.twin_available",
        lambda _runtime: False,
    )
    kernel = _kernel(tmp_path, deny_r5_by_default=False)
    card = _card()
    result = kernel.runtime.submit(
        _cmd(card, "delete_file", {"path": "src/x.py"}),
        card,
    )
    assert not result.ok
    assert "fork gate UNAVAILABLE" in (result.observation.stderr or "")


def test_flag_off_byte_identical_path(tmp_path, monkeypatch):
    monkeypatch.delenv("AUREL_CHRONOS_FORK_GATE", raising=False)
    assert fork_gate_flag_enabled() is False
    recorder = RecordingApprover(AutoApprover(lambda r: True, allow_r5=True))
    kernel = _kernel(tmp_path, recorder, deny_r5_by_default=False)
    card = _card()
    (tmp_path / "ws" / "src").mkdir(parents=True)
    (tmp_path / "ws" / "src" / "x.py").write_text("keep\n", encoding="utf-8")
    result = kernel.runtime.submit(
        _cmd(card, "delete_file", {"path": "src/x.py"}),
        card,
    )
    assert result.ok
    ctx = getattr(recorder.last_request, "context", "") if recorder.last_request else ""
    assert "fork_gate|" not in ctx
