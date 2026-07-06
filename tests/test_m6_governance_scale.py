"""M6 — governance scale G0–G5: presets, precedence, floor, drift audit."""

from __future__ import annotations

import pytest

from agentic_runtime import (
    AgentCard,
    AgentClass,
    AuthorityScope,
    RiskLevel,
    UnsafeLocalSandbox,
    build_runtime,
)
from agentic_runtime.approval import ApprovalRiskClass
from agentic_runtime.core_types import CommandEnvelope
from agentic_runtime.governance import (
    GovernanceLevel as G,
    audit_governance,
    governed_approver,
    issue_override,
    profile_for,
    resolve_effective,
)


# ---- precedence + floor (pure) ------------------------------------------- #

def test_most_restrictive_wins():
    r = resolve_effective(system_ceiling=G.G1, agent_ceiling=G.G3, task_request=G.G5)
    assert r.level is G.G1


def test_task_can_only_lower():
    r = resolve_effective(system_ceiling=G.G4, agent_ceiling=G.G4, task_request=G.G2)
    assert r.level is G.G2


def test_g5_refused_without_anchor_and_attestation():
    capped = resolve_effective(
        system_ceiling=G.G5, agent_ceiling=G.G5, task_request=G.G5,
        anchor_available=False, attestation_ok=False)
    assert capped.level is G.G4
    allowed = resolve_effective(
        system_ceiling=G.G5, agent_ceiling=G.G5, task_request=G.G5,
        anchor_available=True, attestation_ok=True)
    assert allowed.level is G.G5


def test_override_lifts_above_agent_but_not_system():
    ov = issue_override(operator="op", from_level=G.G1, to_level=G.G3,
                        run_id="r", reason="hotfix")
    lifted = resolve_effective(system_ceiling=G.G4, agent_ceiling=G.G1,
                               task_request=G.G1, override=ov)
    assert lifted.level is G.G3 and lifted.override_applied

    ov2 = issue_override(operator="op", from_level=G.G1, to_level=G.G5,
                         run_id="r", reason="x")
    capped = resolve_effective(system_ceiling=G.G2, agent_ceiling=G.G1,
                               task_request=G.G1, override=ov2)
    assert capped.level is G.G2  # never above the system ceiling


def test_trace_is_floor_at_every_level():
    for lvl in G:
        assert profile_for(lvl).trace_required is True
    # HERETIC still requires the anchor floor
    assert profile_for(G.G5).anchor_required is True


# ---- profile materialization drives real approvals ----------------------- #

def _card():
    return AgentCard.make(
        name="Gov", agent_class=AgentClass.EXECUTION, mission="gov",
        authority=AuthorityScope(write_paths=["src/"], read_paths=["*"],
                                 max_risk=RiskLevel.HIGH),
        allowed_tools=["read_file", "write_file", "network_fetch"],
    )


def test_g2_profile_auto_approves_reversible_write_blocks_external(tmp_path):
    # G2 auto-approves up to R2 (reversible write); R3 (external) needs a human.
    approver = governed_approver(profile_for(G.G2))
    kernel = build_runtime(sandbox=UnsafeLocalSandbox(root=str(tmp_path)),
                           approval_gate=approver)
    card = _card()
    write = CommandEnvelope.make(
        issuer_card_id=card.id, tool="write_file",
        args={"path": "src/a.txt", "content": "x"}, rationale="g",
        declared_risk=RiskLevel.LOW, expected_effect="write")
    res = kernel.runtime.submit(write, card)
    assert res.ok  # R2 write auto-approved under G2

    # an external-effect tool (network_fetch, R3-class) is NOT auto-approved
    fetch = CommandEnvelope.make(
        issuer_card_id=card.id, tool="network_fetch",
        args={"url": "http://example.com"}, rationale="g",
        declared_risk=RiskLevel.LOW, expected_effect="fetch")
    res2 = kernel.runtime.submit(fetch, card)
    assert not res2.ok  # held for human / denied under the G2 envelope


# ---- drift audit over a real trace --------------------------------------- #

def test_drift_audit_detects_understated_level(tmp_path):
    # Run auto-approves an R2 write, then audit as if declared G0.
    approver = governed_approver(profile_for(G.G2))
    kernel = build_runtime(sandbox=UnsafeLocalSandbox(root=str(tmp_path)),
                           approval_gate=approver)
    card = _card()
    kernel.runtime.submit(CommandEnvelope.make(
        issuer_card_id=card.id, tool="write_file",
        args={"path": "src/a.txt", "content": "x"}, rationale="g",
        declared_risk=RiskLevel.LOW, expected_effect="write"), card)

    events = list(kernel.trace.replay())
    # declared G0 but auto-approved an R2 → drift
    report = audit_governance(G.G0, events)
    assert report["drift_detected"] is True
    assert report["effective_level"] in ("G2",)
    # declared G2 → no drift
    assert audit_governance(G.G2, events)["drift_detected"] is False
