"""Dual-kernel speculative execution is honestly charged (P0-S.2 wiring).

Every GOVERNED speculative twin — preflight OR materialize-to-live — charges one
simulation exec against the parent run's budget, so the run's simulation spend is
truthful and capped. Over-budget denies the speculation before any compute runs.
"""
from __future__ import annotations

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
from agentic_runtime.budget import BudgetExceeded, BudgetLedger, BudgetPolicy
from agentic_runtime.core_types import CommandEnvelope
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


def _write(card):
    return CommandEnvelope.make(
        issuer_card_id=card.id, tool="write_file",
        args={"path": "src/f.py", "content": "F\n"},
        rationale="dk", declared_risk=RiskLevel.LOW, expected_effect="w",
        parent_intent_id="task-1")


def _sim_execs(kernel):
    return kernel.runtime.budget.snapshot()["usage"]["simulation_execs"]


def test_materialize_path_charges_one_simulation(tmp_path):
    kernel = build_runtime(
        sandbox=UnsafeLocalSandbox(root=str(tmp_path / "ws")),
        approval_gate=_approver(), trace_backend="memory",
        retain_states=True, state_store=StateStore(str(tmp_path / "traces")))
    card = _governed_card()
    dk = DualKernelRuntime(kernel, enabled=True, materialize=True)

    r = dk.submit(_write(card), card)
    assert r.ok
    assert _sim_execs(kernel) == 1


def test_preflight_path_charges_one_simulation(tmp_path):
    kernel = build_runtime(  # no state_store → preflight path
        sandbox=UnsafeLocalSandbox(root=str(tmp_path / "ws")),
        approval_gate=_approver(), trace_backend="memory")
    card = _governed_card()
    dk = DualKernelRuntime(kernel, enabled=True)  # materialize off

    r = dk.submit(_write(card), card)
    assert r.ok
    assert _sim_execs(kernel) == 1


def test_simulation_budget_cap_denies_speculation(tmp_path):
    kernel = build_runtime(
        sandbox=UnsafeLocalSandbox(root=str(tmp_path / "ws")),
        approval_gate=_approver(), trace_backend="memory",
        retain_states=True, state_store=StateStore(str(tmp_path / "traces")),
        budget=BudgetLedger(BudgetPolicy(max_simulation_execs=0)))
    card = _governed_card()
    dk = DualKernelRuntime(kernel, enabled=True, materialize=True)

    with pytest.raises(BudgetExceeded):
        dk.submit(_write(card), card)
    # speculation denied before running → live workspace never got the write
    try:
        kernel.runtime.tools.sandbox.read_file("src/f.py")
        raise AssertionError("write must not have reached live state")
    except OSError:
        pass


def test_fast_route_does_not_charge_simulation(tmp_path):
    # a read-only low-autonomy card routes FAST → no speculative twin, no charge
    kernel = build_runtime(
        sandbox=UnsafeLocalSandbox(root=str(tmp_path / "ws")),
        approval_gate=_approver(), trace_backend="memory")
    read_card = AgentCard.make(
        name="Reader", agent_class=AgentClass.RESEARCH, mission="dk",
        authority=AuthorityScope(write_paths=[], read_paths=["*"],
                                 max_risk=RiskLevel.LOW),
        allowed_tools=["read_file", "list_dir"])
    dk = DualKernelRuntime(kernel, enabled=True)
    dk.submit(CommandEnvelope.make(
        issuer_card_id=read_card.id, tool="list_dir", args={"path": "."},
        rationale="dk", declared_risk=RiskLevel.LOW, expected_effect="r"), read_card)
    assert _sim_execs(kernel) == 0
