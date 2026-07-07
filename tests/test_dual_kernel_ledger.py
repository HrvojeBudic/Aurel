"""DualKernelLedger — tamper-evident, hash-chained record of governance decisions.

Real objects only. Proves the ledger chains, detects tampering, persists +
reloads, projects a read-model (not source), and that routing every command
through the facade produces a verifiable decision trail.
"""
from __future__ import annotations

from agentic_runtime import (
    AgentCard,
    AgentClass,
    AuthorityScope,
    RiskLevel,
    UnsafeLocalSandbox,
    build_runtime,
)
from agentic_runtime.core_types import CommandEnvelope
from agentic_runtime.dual_kernel import DualKernelLedger, DualKernelRuntime
from agentic_runtime.dual_kernel.ledger import GENESIS
from agentic_runtime.hitl import AutoApprover


def _append(led, cid, route="governed", verdict="pass"):
    return led.append(command_id=cid, task_id="t", route=route,
                      autonomy_index=4, verdict=verdict, final_status=verdict,
                      nc_laws=["NC-01I-068"], executed=(verdict == "pass"))


def test_ledger_chains_from_genesis():
    led = DualKernelLedger()
    e0 = _append(led, "c0")
    e1 = _append(led, "c1")
    assert e0.prev_hash == GENESIS
    assert e1.prev_hash == e0.entry_hash
    assert led.verify()["ok"] is True
    assert led.verify()["count"] == 2


def test_tamper_is_detected():
    led = DualKernelLedger()
    _append(led, "c0")
    _append(led, "c1", verdict="blocking_fail")
    # tamper with a recorded decision without recomputing its hash
    led.entries()[0].verdict = "pass_with_warning"
    led._entries[0].verdict = "pass_with_warning"
    report = led.verify()
    assert report["ok"] is False
    assert report["reason"] == "payload tampered"
    assert report["seq"] == 0


def test_persist_and_reload_verifies(tmp_path):
    path = str(tmp_path / "dk_events.jsonl")
    led = DualKernelLedger(path=path)
    _append(led, "c0")
    _append(led, "c1")
    reloaded = DualKernelLedger.load(path)
    assert reloaded.verify()["ok"] is True
    assert [e.command_id for e in reloaded.entries()] == ["c0", "c1"]


def test_projection_is_marked_and_readonly():
    led = DualKernelLedger()
    _append(led, "c0")
    proj = led.projection()
    assert proj[0]["projection"] is True
    assert proj[0]["route"] == "governed"
    assert "NC-01I-068" in proj[0]["nc_laws"]
    # projection carries no way to mutate source — it is display only
    assert "sandbox" not in proj[0] and "content" not in proj[0]


# --------------------------------------------------------------------------- #
#  integration: routing through the facade records a verifiable trail
# --------------------------------------------------------------------------- #
def _approver():
    return AutoApprover(lambda r: True, allow_r2=True, allow_r3=True,
                        allow_r4=True, allow_r5=True)


def _governed_card():
    return AgentCard.make(
        name="Gov", agent_class=AgentClass.EXECUTION, mission="dk",
        authority=AuthorityScope(write_paths=["src/"], read_paths=["*"],
                                 max_risk=RiskLevel.HIGH),
        allowed_tools=["read_file", "write_file", "list_dir"],
        escalation_policy=["operator"])


def test_facade_records_verifiable_decision_trail(tmp_path):
    kernel = build_runtime(
        sandbox=UnsafeLocalSandbox(root=str(tmp_path / "ws")),
        approval_gate=_approver(), trace_backend="memory")
    card = _governed_card()
    dk = DualKernelRuntime(kernel, enabled=True)

    cmd = CommandEnvelope.make(
        issuer_card_id=card.id, tool="write_file",
        args={"path": "src/f.py", "content": "F\n"},
        rationale="dk", declared_risk=RiskLevel.LOW, expected_effect="w",
        parent_intent_id="task-1")
    r = dk.submit(cmd, card)

    assert r.ok
    events = dk.ledger.entries()
    assert len(events) == 1
    ev = events[0]
    assert ev.route == "governed"
    assert ev.final_status == "pass"
    assert ev.executed is True
    assert dk.ledger.verify()["ok"] is True


def test_facade_flag_off_writes_no_ledger(tmp_path):
    kernel = build_runtime(
        sandbox=UnsafeLocalSandbox(root=str(tmp_path / "ws")),
        approval_gate=_approver(), trace_backend="memory")
    card = _governed_card()
    dk = DualKernelRuntime(kernel, enabled=False)
    dk.submit(CommandEnvelope.make(
        issuer_card_id=card.id, tool="write_file",
        args={"path": "src/f.py", "content": "F\n"}, rationale="dk",
        declared_risk=RiskLevel.LOW, expected_effect="w"), card)
    assert dk.ledger.entries() == []  # off = no dual-kernel record at all
