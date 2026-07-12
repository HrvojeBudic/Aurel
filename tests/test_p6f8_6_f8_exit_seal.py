"""F8.6 seal — derived F8 exit seal + north-star Time Plane projection."""
from __future__ import annotations

import argparse
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
from agentic_runtime.cli_modules.chronos_commands import cmd_chronos_seal
from agentic_runtime.core_types import CommandEnvelope
from agentic_runtime.f8_projection import F8RunProjection
from agentic_runtime.f8_seal import (
    F8_SLICES,
    ItemStatus,
    SealStatus,
    build_f8_exit_seal,
)
from agentic_runtime.hitl import AutoApprover
from agentic_runtime.succession_drill import run_succession_drill


def _approver() -> AutoApprover:
    return AutoApprover(
        lambda r: True, allow_r2=True, allow_r3=True, allow_r4=True, allow_r5=True
    )


def _card() -> AgentCard:
    return AgentCard.make(
        name="F8.6 Agent",
        agent_class=AgentClass.EXECUTION,
        mission="f8 exit seal",
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
        rationale="f8.6",
        declared_risk=RiskLevel.LOW,
        expected_effect="f8.6",
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


def test_seal_is_sealed_with_all_slices():
    seal = build_f8_exit_seal()
    assert seal.status is SealStatus.SEALED and seal.sealed is True
    assert all(i.status is ItemStatus.PASSED for i in seal.items)
    assert len(seal.items) == len(F8_SLICES) == 7


def test_missing_report_blocks(tmp_path):
    seal = build_f8_exit_seal(reports_dir=str(tmp_path))
    assert seal.status is SealStatus.BLOCKED and seal.sealed is False
    assert all(i.module_present for i in seal.items)


def test_f7_seam_flipped_live_and_scifi_guards_false():
    seal = build_f8_exit_seal()
    flipped = {s for s, _ in seal.flipped_from_f7}
    assert flipped == {"library_time_travel"}
    assert seal.claims_library_time_travel_live is True
    assert seal.claims_distributed_replay is False
    assert seal.claims_hsm_key_ceremony is False
    assert seal.claims_chronos_ui_forge is False
    assert seal.claims_threat_detection_engine is False
    assert seal.claims_policy_editor is False
    assert seal.claims_automated_succession_restore is False


def test_unavailable_registry_parks_later_and_scifi():
    ids = {u.surface_id for u in build_f8_exit_seal().unavailable}
    assert {"policy_editor", "threat_detection_engine", "chronos_ui_forge"} <= ids
    assert {"distributed_replay", "hsm_key_ceremony"} <= ids


def test_blocked_seal_does_not_claim_flip(tmp_path):
    seal = build_f8_exit_seal(reports_dir=str(tmp_path))
    assert seal.claims_library_time_travel_live is False


def test_cli_chronos_seal_returns_sealed(capsys):
    rc = cmd_chronos_seal(argparse.Namespace(json=False))
    assert rc == 0
    assert "SEALED" in capsys.readouterr().out


def test_north_star_f8_run_end_to_end(tmp_path, monkeypatch):
    monkeypatch.setenv("AUREL_CHRONOS", "1")
    monkeypatch.setenv("AUREL_SYSTEM", "1")
    kernel, trace_dir = _retained_run(tmp_path, ["A\n", "B\n"])
    run_id = kernel.trace.run_id

    proj = F8RunProjection(
        kernel, run_id=run_id, trace_dir=trace_dir, sandbox_factory=_factory,
    ).to_dict()
    assert proj["chronos_replay"]["replayable"] is True
    assert proj["system"]["available"] is True
    assert proj["system"]["audit"]["available"] is True
    assert proj["library_time_travel"] is True
    assert proj["replayable"] is True

    report = run_succession_drill(
        trace_dir,
        out_dir=str(tmp_path / "succession_copy"),
        sample=1,
        sandbox_factory=_factory,
    )
    assert report.passed is True

    replay = ChronosReplay.from_run(trace_dir, run_id, sandbox_factory=_factory)
    assert replay.replayable is True

    live_events = (
        Path(trace_dir) / "runs" / run_id / "events.jsonl"
    ).read_text(encoding="utf-8")
    run_succession_drill(
        trace_dir,
        out_dir=str(tmp_path / "succession_copy2"),
        sample=1,
        sandbox_factory=_factory,
    )
    assert (
        Path(trace_dir) / "runs" / run_id / "events.jsonl"
    ).read_text(encoding="utf-8") == live_events
