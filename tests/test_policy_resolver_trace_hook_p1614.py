"""P1.6.14 Policy Resolution Trace Hook — resolver integration tests."""
from __future__ import annotations

import inspect
import json

import pytest

from agentic_runtime.policy_cards import (
    EnforcementMode,
    FamilyDecision,
    PolicyFamily,
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
from agentic_runtime.policy_cards.resolution_trace import (
    PolicyResolutionTraceEvent,
    build_policy_resolution_trace_event,
)


def _ctx(risk: str = "R2", **kw) -> PolicyResolutionContext:
    return PolicyResolutionContext(context_id="c-1", risk_tier=risk, **kw)


def _pc(cid: str, kind: PolicyCardKind = PolicyCardKind.RISK_TIER) -> PolicyCard:
    return PolicyCard(
        schema_version="1.0",
        identity=PolicyCardIdentity(card_id=cid, slug=cid, name=cid, version="1.0", namespace="test"),
        kind=kind,
        status=PolicyCardStatus.ACTIVE,
        scope=PolicyCardScope(scope_type=PolicyCardScopeType.GLOBAL),
        description="test",
    )


def _risk_card(cid: str) -> RiskTierPolicyCard:
    card = create_default_risk_tier_policy_card()
    pc = _pc(cid, PolicyCardKind.RISK_TIER)
    object.__setattr__(card, "policy_card", pc)
    return card


class TestResolverTraceIntegration:
    def test_resolver_includes_trace(self):
        rps = resolve_policy_cards(_ctx("R2"), [_risk_card("r1")])
        assert rps.resolution_trace is not None
        assert isinstance(rps.resolution_trace, dict)

    def test_resolver_includes_trace_hash(self):
        rps = resolve_policy_cards(_ctx("R2"), [_risk_card("r1")])
        assert rps.resolution_trace_hash is not None
        assert len(rps.resolution_trace_hash) == 64

    def test_resolver_includes_trace_id(self):
        rps = resolve_policy_cards(_ctx("R2"), [_risk_card("r1")])
        assert rps.resolution_trace_id is not None
        assert len(rps.resolution_trace_id) == 64

    def test_trace_hash_includes_registry_source(self):
        rps = resolve_policy_cards(_ctx("R2"), [_risk_card("r1")])
        trace = rps.resolution_trace
        assert trace is not None
        assert "registry_hash" in trace

    def test_trace_hash_includes_context_hash(self):
        rps = resolve_policy_cards(_ctx("R2"), [_risk_card("r1")])
        trace = rps.resolution_trace
        assert trace is not None
        assert "context_hash" in trace

    def test_trace_hash_includes_conflict_hash(self):
        rps = resolve_policy_cards(_ctx("R2"), [_risk_card("r1")])
        trace = rps.resolution_trace
        assert trace is not None
        assert "conflict_hash" in trace

    def test_trace_hash_includes_effective_shadow_action(self):
        rps = resolve_policy_cards(_ctx("R2"), [_risk_card("r1")])
        trace = rps.resolution_trace
        assert trace is not None
        assert trace["effective_shadow_action"] == rps.effective_shadow_action.value

    def test_trace_hash_includes_strictest_rank(self):
        rps = resolve_policy_cards(_ctx("R6"), [_risk_card("r1")])
        trace = rps.resolution_trace
        assert trace is not None
        assert trace["strictest_decision_rank"] == "DENY"

    def test_trace_metadata_is_deterministic(self):
        rps1 = resolve_policy_cards(_ctx("R2"), [_risk_card("r1")])
        rps2 = resolve_policy_cards(_ctx("R2"), [_risk_card("r1")])
        assert rps1.resolution_trace_hash == rps2.resolution_trace_hash
        assert rps1.resolution_trace_id == rps2.resolution_trace_id

    def test_resolver_remains_shadow_only(self):
        rps = resolve_policy_cards(_ctx("R2"), [_risk_card("r1")])
        assert rps.enforcement_mode == EnforcementMode.SHADOW

    def test_resolver_does_not_import_agentic_runtime(self):
        import agentic_runtime.policy_cards.resolver as res
        for name in dir(res):
            obj = getattr(res, name, None)
            if obj is not None and hasattr(obj, "__module__"):
                m = getattr(obj, "__module__", "")
                assert not m.startswith("agentic_runtime.runtime")

    def test_trace_object_no_enforce_methods(self):
        for cls in (PolicyResolutionTraceEvent,):
            methods = {n for n, _ in inspect.getmembers(cls) if callable(getattr(cls, n, None))}
            assert not {"enforce", "block", "apply", "approve", "submit", "write_ledger"} & methods


class TestTraceBackwardsCompatibility:
    def test_no_trace_by_default(self):
        rps = ResolvedPolicySet(
            resolution_id="r1",
            context_hash="a" * 64,
            enforcement_mode=EnforcementMode.SHADOW,
            overall_decision=FamilyDecision.ALLOW,
            effective_shadow_action=ShadowAction.WOULD_ALLOW,
        ).with_canonical_hash()
        assert rps.resolution_trace is None
        assert rps.resolution_trace_hash is None
        assert rps.resolution_trace_id is None
        assert rps.canonical_hash is not None

    def test_existing_resolve_still_works(self):
        rps = resolve_policy_cards(_ctx("R2"), [_risk_card("r1")])
        assert rps.resolution_id.startswith("rps-")
        assert rps.canonical_hash is not None

    def test_p1613_conflict_metadata_still_present(self):
        rps = resolve_policy_cards(_ctx("R2"), [_risk_card("r1")])
        assert rps.conflict_resolution is not None
        assert rps.conflict_hash is not None
