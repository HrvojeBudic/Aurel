"""P1.6.13 Policy Conflict Algebra - resolver integration tests."""
from __future__ import annotations

import inspect

import pytest

from agentic_runtime.policy_cards import (
    EnforcementMode,
    FamilyDecision,
    PolicyFamily,
    PolicyFamilyDecision,
    PolicyResolutionContext,
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
from agentic_runtime.policy_cards.risk_tiers import (
    RiskTierPolicyCard,
    create_default_risk_tier_policy_card,
)


def _ctx(risk: str = "R2", **kw) -> PolicyResolutionContext:
    return PolicyResolutionContext(context_id="c-1", risk_tier=risk, **kw)


def _pc(cid: str, kind: PolicyCardKind = PolicyCardKind.RISK_TIER) -> PolicyCard:
    return PolicyCard(
        schema_version="1.0",
        identity=PolicyCardIdentity(
            card_id=cid, slug=cid, name=cid, version="1.0", namespace="test",
        ),
        kind=kind,
        status=PolicyCardStatus.ACTIVE,
        scope=PolicyCardScope(scope_type=PolicyCardScopeType.GLOBAL),
        description="test",
    )


def _risk_card(cid: str, tier_value: str = "R2") -> RiskTierPolicyCard:
    card = create_default_risk_tier_policy_card()
    pc = _pc(cid, PolicyCardKind.RISK_TIER)
    object.__setattr__(card, "policy_card", pc)
    return card


class TestResolverConflictIntegration:

    def test_resolver_includes_conflict_resolution(self):
        ctx = _ctx("R5")
        rps = resolve_policy_cards(ctx, [_risk_card("r1")])
        assert rps.conflict_resolution is not None
        assert isinstance(rps.conflict_resolution, dict)

    def test_resolver_includes_conflict_hash(self):
        ctx = _ctx("R2")
        rps = resolve_policy_cards(ctx, [_risk_card("r1")])
        assert rps.conflict_hash is not None
        assert len(rps.conflict_hash) == 64

    def test_conflict_resolution_has_conflict_codes(self):
        ctx = _ctx("R6")
        rps = resolve_policy_cards(ctx, [_risk_card("r1")])
        cr = rps.conflict_resolution
        assert cr is not None
        assert "conflict_codes" in cr

    def test_effective_action_follows_strictest_wins(self):
        ctx = _ctx("R6")
        rps = resolve_policy_cards(ctx, [_risk_card("r1")])
        assert rps.overall_decision == FamilyDecision.DENY

    def test_conflict_hash_deterministic(self):
        ctx = _ctx("R2")
        rps1 = resolve_policy_cards(ctx, [_risk_card("r1")])
        rps2 = resolve_policy_cards(ctx, [_risk_card("r1")])
        assert rps1.conflict_hash == rps2.conflict_hash

    def test_conflict_resolution_winning_rank(self):
        ctx = _ctx("R6")
        rps = resolve_policy_cards(ctx, [_risk_card("r1")])
        cr = rps.conflict_resolution
        assert cr is not None
        assert cr["winning_rank"] in ("DENY",)

    def test_conflict_resolution_summary(self):
        ctx = _ctx("R2")
        rps = resolve_policy_cards(ctx, [_risk_card("r1")])
        assert rps.conflict_resolution is not None
        assert len(rps.conflict_resolution.get("summary", "")) > 0

    def test_conflict_resolution_has_strategy(self):
        ctx = _ctx("R2")
        rps = resolve_policy_cards(ctx, [_risk_card("r1")])
        assert rps.conflict_resolution is not None
        assert "strategy" in rps.conflict_resolution

    def test_conflict_resolution_has_winning_family(self):
        ctx = _ctx("R2")
        rps = resolve_policy_cards(ctx, [_risk_card("r1")])
        cr = rps.conflict_resolution
        assert cr is not None
        assert cr["winning_family"] is not None

    def test_conflict_resolution_has_family_decision_count(self):
        ctx = _ctx("R2")
        rps = resolve_policy_cards(ctx, [_risk_card("r1")])
        cr = rps.conflict_resolution
        assert cr is not None
        assert cr["family_decision_count"] > 0

    def test_conflict_resolution_has_distinct_ranks(self):
        ctx = _ctx("R2")
        rps = resolve_policy_cards(ctx, [_risk_card("r1")])
        cr = rps.conflict_resolution
        assert cr is not None
        assert "distinct_ranks" in cr

    def test_conflict_resolution_has_winning_card_ids(self):
        ctx = _ctx("R2")
        rps = resolve_policy_cards(ctx, [_risk_card("r1")])
        cr = rps.conflict_resolution
        assert cr is not None
        assert "winning_card_ids" in cr


class TestBackwardsCompatibility:

    def test_resolved_policy_set_default_no_conflict(self):
        rps = ResolvedPolicySet(
            resolution_id="r1",
            context_hash="a" * 64,
            enforcement_mode=EnforcementMode.SHADOW,
            overall_decision=FamilyDecision.ALLOW,
            effective_shadow_action=ShadowAction.WOULD_ALLOW,
        ).with_canonical_hash()
        assert rps.conflict_resolution is None
        assert rps.conflict_hash is None
        assert rps.canonical_hash is not None

    def test_existing_resolve_still_works(self):
        ctx = _ctx("R2")
        rps = resolve_policy_cards(ctx, [_risk_card("r1")])
        assert rps.resolution_id.startswith("rps-")
        assert rps.canonical_hash is not None
        assert rps.enforcement_mode == EnforcementMode.SHADOW


class TestShadowOnlyInvariants:

    def test_resolved_policy_set_no_enforce_methods(self):
        methods = {n for n, _ in inspect.getmembers(ResolvedPolicySet)
                   if callable(getattr(ResolvedPolicySet, n, None))}
        assert not {"enforce", "block", "apply", "approve", "submit", "execute"} & methods

    def test_resolver_no_runtime_import(self):
        import agentic_runtime.policy_cards.resolver as res
        for name in dir(res):
            obj = getattr(res, name, None)
            if obj is not None and hasattr(obj, "__module__"):
                m = getattr(obj, "__module__", "")
                assert not m.startswith("agentic_runtime.runtime")

    def test_conflict_algebra_no_runtime_import(self):
        import agentic_runtime.policy_cards.conflict_algebra as ca
        for name in dir(ca):
            obj = getattr(ca, name, None)
            if obj is not None and hasattr(obj, "__module__"):
                m = getattr(obj, "__module__", "")
                assert "agentic_runtime.runtime" not in m
