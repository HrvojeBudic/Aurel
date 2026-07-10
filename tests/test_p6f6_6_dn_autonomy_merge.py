"""F6.6 seal — DN mechanisms (a): graduated autonomy + weighted merge verdict.

Mostly surfacing existing dual_kernel machinery: the σ autonomy index and the
merge-gate verdict, whose verifier veto is ABSOLUTE (a failed verification can
never merge, regardless of other signals).
"""
from __future__ import annotations

from agentic_runtime import build_runtime
from agentic_runtime.core_types import (
    AgentCard,
    AgentClass,
    AuthorityScope,
    CommandEnvelope,
    Intent,
    RiskLevel,
    VerifierResult,
)
from agentic_runtime.dual_kernel.merge_gate import MergeContext
from agentic_runtime.dual_kernel.sigma import SigmaGovernor
from agentic_runtime.front_server import (
    DnStatusReadModel,
    LiveReadModels,
    evaluate_merge,
    graduated_autonomy,
)


def _card(max_risk=RiskLevel.LOW, tools=("t",)):
    return AgentCard.make(
        name="op", agent_class=AgentClass.EXECUTION, mission="F6.6",
        authority=AuthorityScope(max_risk=max_risk), allowed_tools=list(tools))


def _ctx(card, *, verifier_passed: bool):
    cmd = CommandEnvelope.make(card.id, "t", {}, "r", RiskLevel.LOW, "eff")
    sigma = SigmaGovernor().register_task(card, Intent.make("do it"))
    return MergeContext(
        cmd=cmd,
        verifier_result=VerifierResult(verifier_passed, "verifier"),
        sigma=sigma, card=card,
        simulation_resolved=True,   # otherwise an unrelated blocker fires
    )


# --- graduated autonomy (σ) -----------------------------------------------------

def test_graduated_autonomy_is_bounded_index():
    idx = graduated_autonomy(_card())
    assert isinstance(idx, int) and 0 <= idx <= 10


def test_more_authority_changes_the_autonomy_index():
    # A higher risk ceiling (more freedom) changes the graduated autonomy score.
    low = graduated_autonomy(_card(max_risk=RiskLevel.LOW))
    high = graduated_autonomy(_card(max_risk=RiskLevel.CRITICAL))
    assert low != high


# --- weighted merge verdict + absolute verifier veto ----------------------------

def test_passing_verifier_can_merge():
    card = _card()
    out = evaluate_merge(_ctx(card, verifier_passed=True))
    assert out["mergeable"] is True and out["verifier_vetoed"] is False
    assert "state_verification" not in out["blockers"]


def test_failed_verifier_veto_is_absolute():
    card = _card()
    out = evaluate_merge(_ctx(card, verifier_passed=False))
    assert out["verifier_vetoed"] is True
    assert out["mergeable"] is False               # veto overrides everything
    assert "state_verification" in out["blockers"]


def test_merge_verdict_is_deterministic():
    card = _card()
    a = evaluate_merge(_ctx(card, verifier_passed=True))
    b = evaluate_merge(_ctx(card, verifier_passed=True))
    assert a == b


# --- read model (honest availability) -------------------------------------------

def test_dn_status_declares_availability(monkeypatch):
    monkeypatch.delenv("AUREL_DUAL_KERNEL", raising=False)
    off = DnStatusReadModel.status()
    assert off["dual_kernel_enabled"] is False
    assert "UNAVAILABLE" in off["graduated_autonomy"]
    assert off["verifier_veto"] == "absolute"
    monkeypatch.setenv("AUREL_DUAL_KERNEL", "1")
    on = DnStatusReadModel.status()
    assert on["dual_kernel_enabled"] is True and "live" in on["graduated_autonomy"]


def test_dn_via_live_read_registry():
    rt = build_runtime()
    status, payload = LiveReadModels(rt).read("/read/aureleu/dn")
    assert status == 200 and payload["live"] is True and payload["model"] == "aureleu/dn"
    assert payload["verifier_veto"] == "absolute"
