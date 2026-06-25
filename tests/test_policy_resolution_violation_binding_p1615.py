"""P1.6.15 Policy Violation Trace Hook — resolution binding tests."""
from __future__ import annotations

import inspect

import pytest

from agentic_runtime.policy_cards import (
    EnforcementMode,
    FamilyDecision,
    ResolvedPolicySet,
    ShadowAction,
    resolve_policy_cards,
)
from agentic_runtime.policy_cards.models import (
    PolicyCard,
    PolicyCardIdentity,
    PolicyCardKind,
    PolicyCardScope,
    PolicyCardScopeType,
    PolicyCardStatus,
)
from agentic_runtime.policy_cards.risk_tiers import create_default_risk_tier_policy_card
from agentic_runtime.policy_cards.resolution_context import PolicyResolutionContext
from agentic_runtime.policy_cards.violation_trace import (
    PolicyViolationType,
    bind_policy_violation_from_resolution,
    classify_policy_violation,
    policy_violation_hash,
)


def _ctx(risk: str = "R2") -> PolicyResolutionContext:
    return PolicyResolutionContext(context_id="c-1", risk_tier=risk)


def _pc(cid: str) -> PolicyCard:
    return PolicyCard(
        schema_version="1.0",
        identity=PolicyCardIdentity(
            card_id=cid, slug=cid, name=cid, version="1.0", namespace="test",
        ),
        kind=PolicyCardKind.RISK_TIER,
        status=PolicyCardStatus.ACTIVE,
        scope=PolicyCardScope(scope_type=PolicyCardScopeType.GLOBAL),
        description="test",
    )


def _risk_card(cid: str):
    card = create_default_risk_tier_policy_card()
    pc = _pc(cid)
    object.__setattr__(card, "policy_card", pc)
    return card


class TestResolutionViolationBinding:
    def test_includes_resolution_trace_id(self):
        rps = resolve_policy_cards(_ctx("R2"), [_risk_card("r1")])
        env = bind_policy_violation_from_resolution(rps)
        assert env.trace_event.policy_resolution_trace_id == rps.resolution_trace_id

    def test_includes_resolution_hash(self):
        rps = resolve_policy_cards(_ctx("R2"), [_risk_card("r1")])
        env = bind_policy_violation_from_resolution(rps)
        assert env.trace_event.policy_resolution_hash == rps.resolution_trace_hash

    def test_includes_conflict_hash_when_present(self):
        rps = resolve_policy_cards(_ctx("R2"), [_risk_card("r1")])
        env = bind_policy_violation_from_resolution(rps)
        assert env.trace_event.conflict_hash == (rps.conflict_hash or "")

    def test_includes_context_hash(self):
        rps = resolve_policy_cards(_ctx("R2"), [_risk_card("r1")])
        env = bind_policy_violation_from_resolution(rps)
        assert env.trace_event.context_hash == rps.context_hash

    def test_includes_strictest_decision_rank(self):
        rps = resolve_policy_cards(_ctx("R2"), [_risk_card("r1")])
        env = bind_policy_violation_from_resolution(rps)
        assert isinstance(env.trace_event.strictest_decision_rank, str)

    def test_includes_custos_shadow_action(self):
        rps = resolve_policy_cards(_ctx("R2"), [_risk_card("r1")])
        env = bind_policy_violation_from_resolution(rps)
        assert env.trace_event.custos_shadow_action == rps.effective_shadow_action.value

    def test_missing_resolution_trace_classifies_incomplete(self):
        rps = ResolvedPolicySet(
            resolution_id="rps-nt",
            context_hash="a" * 64,
            enforcement_mode=EnforcementMode.SHADOW,
            overall_decision=FamilyDecision.ALLOW,
            effective_shadow_action=ShadowAction.WOULD_ALLOW,
        )
        env = bind_policy_violation_from_resolution(rps)
        assert env.trace_event.violation_type == (
            PolicyViolationType.POLICY_TRACE_INCOMPLETE.value
        )

    def test_binding_deterministic(self):
        rps = resolve_policy_cards(_ctx("R2"), [_risk_card("r1")])
        e1 = bind_policy_violation_from_resolution(rps)
        e2 = bind_policy_violation_from_resolution(rps)
        assert policy_violation_hash(e1.trace_event) == policy_violation_hash(e2.trace_event)

    def test_shuffled_lists_same_hash(self):
        rps = resolve_policy_cards(_ctx("R2"), [_risk_card("r1")])
        env = classify_policy_violation(
            p0_verdict="allow",
            custos_shadow_action=rps.effective_shadow_action.value,
            context_hash=rps.context_hash,
            policy_resolution_trace_id=rps.resolution_trace_id or "",
            policy_resolution_hash=rps.resolution_trace_hash or "",
            reason_codes=("Z", "A"),
            conflict_codes=("b", "a"),
            source_family_ids=("sandbox", "risk_tier"),
            source_card_ids=("card-b", "card-a"),
        )
        env2 = classify_policy_violation(
            p0_verdict="allow",
            custos_shadow_action=rps.effective_shadow_action.value,
            context_hash=rps.context_hash,
            policy_resolution_trace_id=rps.resolution_trace_id or "",
            policy_resolution_hash=rps.resolution_trace_hash or "",
            reason_codes=("A", "Z"),
            conflict_codes=("a", "b"),
            source_family_ids=("risk_tier", "sandbox"),
            source_card_ids=("card-a", "card-b"),
        )
        assert policy_violation_hash(env.trace_event) == policy_violation_hash(env2.trace_event)

    def test_binding_shadow_only(self):
        rps = resolve_policy_cards(_ctx("R2"), [_risk_card("r1")])
        env = bind_policy_violation_from_resolution(rps)
        assert env.trace_event.shadow_only is True
        assert env.trace_event.enforced is False

    def test_resolver_attaches_violation_metadata(self):
        rps = resolve_policy_cards(_ctx("R2"), [_risk_card("r1")])
        assert rps.violation_trace is not None
        assert rps.violation_trace_hash is not None
        assert rps.violation_trace_id is not None

    def test_no_ledger_write_methods(self):
        import agentic_runtime.policy_cards.violation_trace as vt

        assert "write_ledger" not in dir(vt)
        for cls in (vt.PolicyViolationTraceEvent, vt.PolicyViolationTraceEnvelope):
            methods = {n for n, _ in inspect.getmembers(cls) if callable(getattr(cls, n, None))}
            assert "write_ledger" not in methods
