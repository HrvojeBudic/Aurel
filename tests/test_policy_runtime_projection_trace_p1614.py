"""P1.6.14 Policy Resolution Trace Hook — projection trace metadata tests."""
from __future__ import annotations

import inspect
import json

import pytest

from agentic_runtime.policy_cards import (
    EnforcementMode,
    FamilyDecision,
    PolicyFamily,
    PolicyFamilyDecision,
    ResolvedPolicySet,
    ShadowAction,
)
from agentic_runtime.policy_cards.runtime_projection import (
    PolicyShadowProjection,
    RuntimeEffectiveAction,
    RuntimePolicySnapshot,
    compute_policy_shadow_projection_hash,
    policy_shadow_projection_to_canonical_dict,
    project_policy_resolution_against_runtime,
)


def _rps(action: ShadowAction, **kw) -> ResolvedPolicySet:
    return ResolvedPolicySet(
        resolution_id="rps-test",
        context_hash="a" * 64,
        enforcement_mode=EnforcementMode.SHADOW,
        overall_decision=FamilyDecision.ALLOW,
        effective_shadow_action=action,
        resolution_trace_id=kw.pop("trace_id", "t" * 64),
        resolution_trace_hash=kw.pop("trace_hash", "h" * 64),
        **kw,
    ).with_canonical_hash()


def _snapshot(action: RuntimeEffectiveAction) -> RuntimePolicySnapshot:
    return RuntimePolicySnapshot(
        runtime_effective_action=action,
        policy_verdict="allow",
        policy_risk="low",
    )


class TestProjectionTraceMetadata:
    def test_projection_exposes_trace_id(self):
        rps = _rps(ShadowAction.WOULD_ALLOW)
        proj = project_policy_resolution_against_runtime(
            _snapshot(RuntimeEffectiveAction.RUNTIME_ALLOW), rps,
        )
        assert proj.resolution_trace_id == "t" * 64

    def test_projection_exposes_trace_hash(self):
        rps = _rps(ShadowAction.WOULD_ALLOW)
        proj = project_policy_resolution_against_runtime(
            _snapshot(RuntimeEffectiveAction.RUNTIME_ALLOW), rps,
        )
        assert proj.resolution_trace_hash == "h" * 64

    def test_projection_hash_remains_deterministic(self):
        rps = _rps(ShadowAction.WOULD_ALLOW)
        p1 = project_policy_resolution_against_runtime(
            _snapshot(RuntimeEffectiveAction.RUNTIME_ALLOW), rps,
        )
        p2 = project_policy_resolution_against_runtime(
            _snapshot(RuntimeEffectiveAction.RUNTIME_ALLOW), rps,
        )
        assert compute_policy_shadow_projection_hash(p1) == compute_policy_shadow_projection_hash(p2)

    def test_projection_enforced_false(self):
        rps = _rps(ShadowAction.WOULD_ALLOW)
        proj = project_policy_resolution_against_runtime(
            _snapshot(RuntimeEffectiveAction.RUNTIME_ALLOW), rps,
        )
        assert proj.enforced is False

    def test_projection_mode_shadow_only(self):
        rps = _rps(ShadowAction.WOULD_ALLOW)
        proj = project_policy_resolution_against_runtime(
            _snapshot(RuntimeEffectiveAction.RUNTIME_ALLOW), rps,
        )
        assert proj.mode == "shadow_only"

    def test_projection_behavior_unchanged_without_trace(self):
        rps = _rps(ShadowAction.WOULD_ALLOW, trace_id="", trace_hash="")
        proj = project_policy_resolution_against_runtime(
            _snapshot(RuntimeEffectiveAction.RUNTIME_ALLOW), rps,
        )
        assert proj.resolution_trace_id == ""
        assert proj.resolution_trace_hash == ""

    def test_projection_handles_missing_trace_gracefully(self):
        rps = ResolvedPolicySet(
            resolution_id="rps-nt",
            context_hash="a" * 64,
            enforcement_mode=EnforcementMode.SHADOW,
            overall_decision=FamilyDecision.ALLOW,
            effective_shadow_action=ShadowAction.WOULD_ALLOW,
        ).with_canonical_hash()
        proj = project_policy_resolution_against_runtime(
            _snapshot(RuntimeEffectiveAction.RUNTIME_ALLOW), rps,
        )
        assert proj.resolution_trace_id == ""
        assert proj.resolution_trace_hash == ""

    def test_projection_canonical_dict_includes_trace_fields(self):
        rps = _rps(ShadowAction.WOULD_ALLOW)
        proj = project_policy_resolution_against_runtime(
            _snapshot(RuntimeEffectiveAction.RUNTIME_ALLOW), rps,
        )
        payload = policy_shadow_projection_to_canonical_dict(proj, include_hash=True)
        assert payload["resolution_trace_id"] == "t" * 64
        assert payload["resolution_trace_hash"] == "h" * 64

    def test_projection_trace_no_enforce_methods(self):
        methods = {n for n, _ in inspect.getmembers(PolicyShadowProjection) if callable(getattr(PolicyShadowProjection, n, None))}
        assert not {"enforce", "block", "apply", "approve", "execute", "submit"} & methods
