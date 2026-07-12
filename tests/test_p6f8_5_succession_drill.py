"""F8.5 seal — succession drill + System React surface."""
from __future__ import annotations

import argparse
import json
import shutil
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
from agentic_runtime.chronos import ChronosReplay
from agentic_runtime.cli_modules.drill_commands import cmd_drill_succession
from agentic_runtime.core_types import CommandEnvelope, StateTransitionRecord
from agentic_runtime.front_server import LiveReadModels
from agentic_runtime.hitl import AutoApprover
from agentic_runtime.succession_drill import run_succession_drill


def _approver() -> AutoApprover:
    return AutoApprover(
        lambda r: True, allow_r2=True, allow_r3=True, allow_r4=True, allow_r5=True
    )


def _card() -> AgentCard:
    return AgentCard.make(
        name="F8.5 Agent",
        agent_class=AgentClass.EXECUTION,
        mission="succession drill",
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
        rationale="f8.5",
        declared_risk=RiskLevel.LOW,
        expected_effect="f8.5",
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
def _flags_on(monkeypatch):
    monkeypatch.setenv("AUREL_CHRONOS", "1")
    monkeypatch.setenv("AUREL_SYSTEM", "1")


def test_succession_drill_export_restore_verify_replay_passes(tmp_path):
    kernel, trace_dir = _retained_run(tmp_path, ["A\n", "B\n"])
    out_dir = str(tmp_path / "succession_copy")
    report = run_succession_drill(
        trace_dir, out_dir=out_dir, sample=1, sandbox_factory=_factory,
    )
    assert report.exported is True
    assert report.restored is True
    assert report.verified is True
    assert report.replayed == 1
    assert report.passed is True
    assert kernel.trace.run_id in report.sample_run_ids
    assert Path(out_dir).is_dir()


def test_succession_drill_tamper_reports_discrepancy(tmp_path):
    kernel, trace_dir = _retained_run(tmp_path, ["A\n"])
    tampered_src = str(tmp_path / "tampered_src")
    shutil.copytree(trace_dir, tampered_src)
    transition = _transitions(kernel)[0]
    state_hash = transition.after_state_hash
    state_tree = (
        Path(tampered_src) / "states" / state_hash / "tree" / "src" / "f0.py"
    )
    state_tree.write_text("TAMPERED\n", encoding="utf-8")
    report = run_succession_drill(
        tampered_src, out_dir=str(tmp_path / "out"), sample=1, sandbox_factory=_factory,
    )
    assert report.passed is False
    assert report.discrepancies
    replay_disc = [d for d in report.discrepancies if d.get("stage") == "replay"]
    assert replay_disc


def test_succession_drill_does_not_mutate_live_trace(tmp_path):
    kernel, trace_dir = _retained_run(tmp_path, ["A\n"])
    run_id = kernel.trace.run_id
    events_path = Path(trace_dir) / "runs" / run_id / "events.jsonl"
    before = events_path.read_text(encoding="utf-8")
    run_succession_drill(
        trace_dir, out_dir=str(tmp_path / "copy"), sample=1, sandbox_factory=_factory,
    )
    after = events_path.read_text(encoding="utf-8")
    assert before == after


def test_cli_succession_end_to_end(tmp_path, capsys):
    _kernel, trace_dir = _retained_run(tmp_path, ["X\n"])
    args = argparse.Namespace(
        trace_dir=trace_dir,
        out=str(tmp_path / "cli_out"),
        sample=1,
        json=True,
    )
    assert cmd_drill_succession(args) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["passed"] is True
    assert payload["exported"] is True


def test_cli_unavailable_when_chronos_off(tmp_path, monkeypatch, capsys):
    monkeypatch.delenv("AUREL_CHRONOS", raising=False)
    args = argparse.Namespace(trace_dir="", out="", sample=1, json=True)
    assert cmd_drill_succession(args) == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["available"] is False


def test_system_reads_live(monkeypatch):
    monkeypatch.setenv("AUREL_SYSTEM", "1")
    kernel = build_runtime()
    reads = LiveReadModels(kernel)
    for path in (
        "/read/system/audit",
        "/read/system/usage",
        "/read/system/model_routing",
        "/read/system/policies",
        "/read/system/archive",
    ):
        status, body = reads.read(path)
        assert status == 200
        assert body["live"] is True
        assert body["operator_only"] is True


def test_chronos_replay_confirms_tamper_on_copy(tmp_path):
    """Sanity: tampered isolated copy fails replay (same substrate as drill)."""
    kernel, trace_dir = _retained_run(tmp_path, ["A\n"])
    copy_dir = str(tmp_path / "iso")
    shutil.copytree(trace_dir, copy_dir)
    transition = _transitions(kernel)[0]
    state_hash = transition.after_state_hash
    (
        Path(copy_dir) / "states" / state_hash / "tree" / "src" / "f0.py"
    ).write_text("TAMPERED\n", encoding="utf-8")
    result = ChronosReplay.from_run(
        copy_dir, kernel.trace.run_id, sandbox_factory=_factory,
    )
    assert result.replayable is False
