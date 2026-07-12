"""F8.0 — Chronos replay / fork / diff seal tests."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from agentic_runtime import (
    AgentCard,
    AgentClass,
    AuthorityScope,
    RiskLevel,
    StateStore,
    UnsafeLocalSandbox,
    build_runtime,
)
from agentic_runtime.chronos import (
    ChronosDiff,
    ChronosFork,
    ChronosReplay,
    flag_enabled,
)
from agentic_runtime.cli_modules.chronos_commands import cmd_chronos_replay
from agentic_runtime.core_types import CommandEnvelope, StateTransitionRecord
from agentic_runtime.hitl import AutoApprover
from agentic_runtime.trace import PersistentTraceLedger


def _approver() -> AutoApprover:
    return AutoApprover(
        lambda r: True, allow_r2=True, allow_r3=True, allow_r4=True, allow_r5=True
    )


def _card() -> AgentCard:
    return AgentCard.make(
        name="F8 Agent",
        agent_class=AgentClass.EXECUTION,
        mission="chronos test",
        authority=AuthorityScope(
            write_paths=["src/"], read_paths=["*"], max_risk=RiskLevel.HIGH
        ),
        allowed_tools=["read_file", "write_file", "run_tests", "list_dir"],
    )


def _cmd(card: AgentCard, tool: str, args: dict) -> CommandEnvelope:
    return CommandEnvelope.make(
        issuer_card_id=card.id,
        tool=tool,
        args=args,
        rationale="f8",
        declared_risk=RiskLevel.LOW,
        expected_effect="f8",
    )


def _factory(root: str) -> UnsafeLocalSandbox:
    return UnsafeLocalSandbox(root=root)


def _retained_run(tmp_path, contents: list[str]):
    trace_dir = str(tmp_path / "traces")
    store = StateStore(trace_dir)
    kernel = build_runtime(
        sandbox=UnsafeLocalSandbox(root=str(tmp_path / "ws")),
        approval_gate=_approver(),
        trace_backend="persistent",
        trace_dir=trace_dir,
        retain_states=True,
        state_store=store,
    )
    card = _card()
    for i, content in enumerate(contents):
        result = kernel.runtime.submit(
            _cmd(card, "write_file", {"path": f"src/f{i}.py", "content": content}),
            card,
        )
        assert result.ok
    kernel.trace.seal_run("completed")
    return kernel, trace_dir


def _transitions(kernel) -> list[StateTransitionRecord]:
    return [e for e in kernel.trace if isinstance(e, StateTransitionRecord)]


@pytest.fixture(autouse=True)
def _chronos_on(monkeypatch):
    monkeypatch.setenv("AUREL_CHRONOS", "1")


def test_flag_off_by_default(monkeypatch):
    monkeypatch.delenv("AUREL_CHRONOS", raising=False)
    assert flag_enabled() is False


def test_replay_known_run_passes(tmp_path):
    kernel, trace_dir = _retained_run(tmp_path, ["A\n", "B\n"])
    run_id = kernel.trace.run_id
    result = ChronosReplay.from_run(trace_dir, run_id, sandbox_factory=_factory)
    assert result.replayable is True
    assert result.checked_count == len(_transitions(kernel))
    assert result.mismatch_at is None


def test_replay_tampered_state_reports_mismatch(tmp_path):
    kernel, trace_dir = _retained_run(tmp_path, ["A\n"])
    run_id = kernel.trace.run_id
    transition = _transitions(kernel)[0]
    state_hash = transition.after_state_hash
    state_tree = Path(trace_dir) / "states" / state_hash / "tree" / "src" / "f0.py"
    state_tree.write_text("TAMPERED\n", encoding="utf-8")
    result = ChronosReplay.from_run(trace_dir, run_id, sandbox_factory=_factory)
    assert result.replayable is False
    assert result.mismatch_at == 0


def test_replay_unretained_honestly_false(tmp_path):
    trace_dir = str(tmp_path / "traces")
    kernel = build_runtime(
        sandbox=UnsafeLocalSandbox(root=str(tmp_path / "ws")),
        approval_gate=_approver(),
        trace_backend="persistent",
        trace_dir=trace_dir,
        retain_states=False,
    )
    card = _card()
    assert kernel.runtime.submit(
        _cmd(card, "write_file", {"path": "src/x.py", "content": "x\n"}), card
    ).ok
    kernel.trace.seal_run("completed")
    result = ChronosReplay.from_run(trace_dir, kernel.trace.run_id, sandbox_factory=_factory)
    assert result.replayable is False
    assert result.reason


def test_fork_mints_child_parent_untouched(tmp_path):
    kernel, trace_dir = _retained_run(tmp_path, ["A\n", "B\n"])
    run_id = kernel.trace.run_id
    parent_events_before = list(
        Path(trace_dir).joinpath("runs", run_id, "events.jsonl").read_text(encoding="utf-8").splitlines()
    )
    fork = ChronosFork.fork_at(trace_dir, run_id, 0, sandbox_factory=_factory)
    parent_events_after = list(
        Path(trace_dir).joinpath("runs", run_id, "events.jsonl").read_text(encoding="utf-8").splitlines()
    )
    assert parent_events_before == parent_events_after
    assert fork.child_run_id != run_id
    child_ledger = PersistentTraceLedger(base_dir=trace_dir, run_id=fork.child_run_id)
    assert child_ledger.verify_persisted()["ok"]


def test_diff_two_runs_deterministic(tmp_path):
    k1, trace_dir = _retained_run(tmp_path, ["A\n"])
    k2, _ = _retained_run(tmp_path, ["B\n"])
    d1 = ChronosDiff.compare(trace_dir, k1.trace.run_id, k2.trace.run_id)
    d2 = ChronosDiff.compare(trace_dir, k1.trace.run_id, k2.trace.run_id)
    assert d1 == d2
    assert d1.added or d1.removed


def test_cli_unavailable_when_flag_off(tmp_path, monkeypatch, capsys):
    monkeypatch.delenv("AUREL_CHRONOS", raising=False)
    args = type("Args", (), {"run_id": "run_x", "trace_dir": "", "json": True})()
    assert cmd_chronos_replay(args) == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["available"] is False
