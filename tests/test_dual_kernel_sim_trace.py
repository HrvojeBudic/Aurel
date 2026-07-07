"""Reconcile Track C ↔ dual kernel — speculative verdict as non-canonical evidence.

Every GOVERNED speculative execution (preflight OR materialize) emits a
simulation_decision event into the main trace: distinctly labeled is_speculative,
a PraxisEventRecord and never a StateTransitionRecord, advisory not authority.
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
from agentic_runtime.core_types import (
    CommandEnvelope,
    PraxisEventRecord,
    StateTransitionRecord,
)
from agentic_runtime.dual_kernel import DualKernelRuntime
from agentic_runtime.hitl import AutoApprover


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


def _write(card, path="src/f.py"):
    return CommandEnvelope.make(
        issuer_card_id=card.id, tool="write_file",
        args={"path": path, "content": "F\n"},
        rationale="dk", declared_risk=RiskLevel.LOW, expected_effect="w",
        parent_intent_id="t")


def _sim_events(kernel):
    return [e for e in kernel.trace
            if getattr(e, "event_type", "") == "simulation_decision"]


def test_preflight_emits_speculative_evidence(tmp_path):
    kernel = build_runtime(
        sandbox=UnsafeLocalSandbox(root=str(tmp_path / "ws")),
        approval_gate=_approver(), trace_backend="memory")
    card = _governed_card()
    dk = DualKernelRuntime(kernel, enabled=True)  # preflight path
    r = dk.submit(_write(card), card)
    assert r.ok

    events = _sim_events(kernel)
    assert len(events) == 1
    ev = events[0]
    assert ev.details["is_speculative"] is True
    assert ev.details["advisory"] is True
    assert ev.details["final_status"] == "pass"
    assert ev.details["executed"] is True
    # non-canonical: it is a PraxisEventRecord, NOT a state transition
    assert isinstance(ev, PraxisEventRecord)
    assert not isinstance(ev, StateTransitionRecord)


def test_materialize_emits_speculative_evidence(tmp_path):
    # entity_class gates retention on (P0-S.3), so materialize works out of the box
    kernel = build_runtime(
        sandbox=UnsafeLocalSandbox(root=str(tmp_path / "ws")),
        approval_gate=_approver(), trace_backend="memory",
        trace_dir=str(tmp_path / "tr"), entity_class=AgentClass.EXECUTION)
    card = _governed_card()
    dk = DualKernelRuntime(kernel, enabled=True, materialize=True)
    assert dk._can_materialize() is True
    r = dk.submit(_write(card), card)
    assert r.ok

    events = _sim_events(kernel)
    assert len(events) == 1
    assert events[0].details["is_speculative"] is True
    assert events[0].details["executed"] is True


def test_fast_route_emits_no_simulation_decision(tmp_path):
    kernel = build_runtime(
        sandbox=UnsafeLocalSandbox(root=str(tmp_path / "ws")),
        approval_gate=_approver(), trace_backend="memory")
    read_card = AgentCard.make(
        name="R", agent_class=AgentClass.RESEARCH, mission="dk",
        authority=AuthorityScope(write_paths=[], read_paths=["*"],
                                 max_risk=RiskLevel.LOW),
        allowed_tools=["read_file", "list_dir"])
    dk = DualKernelRuntime(kernel, enabled=True)
    dk.submit(CommandEnvelope.make(
        issuer_card_id=read_card.id, tool="list_dir", args={"path": "."},
        rationale="dk", declared_risk=RiskLevel.LOW, expected_effect="r"), read_card)
    assert _sim_events(kernel) == []
