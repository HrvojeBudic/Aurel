"""P1.6.15 Policy Violation Trace Hook — projection violation metadata tests."""
from __future__ import annotations

import pytest

from agentic_runtime.policy_cards import (
    CustosEffectiveAction,
    EnforcementMode,
    FamilyDecision,
    PolicyRuntimeAlignment,
    ResolvedPolicySet,
    RuntimeEffectiveAction,
    RuntimePolicySnapshot,
    ShadowAction,
    compute_policy_shadow_projection_hash,
    project_policy_resolution_against_runtime,
)
from agentic_runtime.policy_cards.violation_trace import PolicyViolationType


def _resolved(action: ShadowAction, **kw) -> ResolvedPolicySet:
    decision_by_action = {
        ShadowAction.WOULD_ALLOW: FamilyDecision.ALLOW,
        ShadowAction.WOULD_WARN: FamilyDecision.WARN,
        ShadowAction.WOULD_REQUIRE_APPROVAL: FamilyDecision.REQUIRE_APPROVAL,
        ShadowAction.WOULD_DENY: FamilyDecision.DENY,
        ShadowAction.WOULD_NOT_APPLY: FamilyDecision.NOT_APPLICABLE,
        ShadowAction.WOULD_ERROR: FamilyDecision.ERROR,
    }
    return ResolvedPolicySet(
        resolution_id=f"rps-{action.value}",
        context_hash="a" * 64,
        enforcement_mode=EnforcementMode.SHADOW,
        overall_decision=decision_by_action[action],
        effective_shadow_action=action,
        resolution_trace_id=kw.pop("trace_id", "t" * 64),
        resolution_trace_hash=kw.pop("trace_hash", "h" * 64),
        **kw,
    ).with_canonical_hash()


def _snapshot(
    action: RuntimeEffectiveAction,
    *,
    policy_verdict: str = "allow",
) -> RuntimePolicySnapshot:
    return RuntimePolicySnapshot(
        runtime_effective_action=action,
        policy_verdict=policy_verdict,
        policy_risk="low",
    )


class TestProjectionViolationMetadata:
    def test_projection_exposes_violation_trace_id(self):
        rps = _resolved(ShadowAction.WOULD_ALLOW)
        proj = project_policy_resolution_against_runtime(
            _snapshot(RuntimeEffectiveAction.RUNTIME_ALLOW), rps,
        )
        assert len(proj.violation_trace_id) == 64

    def test_projection_exposes_violation_hash(self):
        rps = _resolved(ShadowAction.WOULD_ALLOW)
        proj = project_policy_resolution_against_runtime(
            _snapshot(RuntimeEffectiveAction.RUNTIME_ALLOW), rps,
        )
        assert len(proj.violation_hash) == 64

    def test_custos_stricter_than_runtime(self):
        rps = _resolved(ShadowAction.WOULD_DENY)
        proj = project_policy_resolution_against_runtime(
            _snapshot(RuntimeEffectiveAction.RUNTIME_ALLOW), rps,
        )
        assert proj.violation_type == PolicyViolationType.CUSTOS_STRICTER_THAN_RUNTIME.value
        assert proj.alignment_status is PolicyRuntimeAlignment.CUSTOS_STRICTER

    def test_runtime_stricter_than_custos(self):
        rps = _resolved(ShadowAction.WOULD_ALLOW)
        proj = project_policy_resolution_against_runtime(
            _snapshot(RuntimeEffectiveAction.RUNTIME_DENY, policy_verdict="deny"), rps,
        )
        assert proj.violation_type == PolicyViolationType.RUNTIME_STRICTER_THAN_CUSTOS.value

    def test_policy_trace_incomplete_without_trace(self):
        rps = _resolved(ShadowAction.WOULD_ALLOW, trace_id="", trace_hash="")
        proj = project_policy_resolution_against_runtime(
            _snapshot(RuntimeEffectiveAction.RUNTIME_ALLOW), rps,
        )
        assert proj.violation_type == PolicyViolationType.POLICY_TRACE_INCOMPLETE.value

    def test_projection_hash_deterministic(self):
        rps = _resolved(ShadowAction.WOULD_ALLOW)
        p1 = project_policy_resolution_against_runtime(
            _snapshot(RuntimeEffectiveAction.RUNTIME_ALLOW), rps,
        )
        p2 = project_policy_resolution_against_runtime(
            _snapshot(RuntimeEffectiveAction.RUNTIME_ALLOW), rps,
        )
        assert compute_policy_shadow_projection_hash(p1) == compute_policy_shadow_projection_hash(p2)

    def test_projection_enforced_false(self):
        rps = _resolved(ShadowAction.WOULD_ALLOW)
        proj = project_policy_resolution_against_runtime(
            _snapshot(RuntimeEffectiveAction.RUNTIME_ALLOW), rps,
        )
        assert proj.enforced is False

    def test_projection_mode_shadow_only(self):
        rps = _resolved(ShadowAction.WOULD_ALLOW)
        proj = project_policy_resolution_against_runtime(
            _snapshot(RuntimeEffectiveAction.RUNTIME_ALLOW), rps,
        )
        assert proj.mode == "shadow_only"

    def test_projection_without_trace_fields_still_works(self):
        rps = _resolved(ShadowAction.WOULD_ALLOW, trace_id="", trace_hash="")
        proj = project_policy_resolution_against_runtime(
            _snapshot(RuntimeEffectiveAction.RUNTIME_ALLOW), rps,
        )
        assert proj.resolution_trace_id == ""
        assert proj.violation_trace_id

    def test_custos_effective_action_preserved(self):
        rps = _resolved(ShadowAction.WOULD_DENY)
        proj = project_policy_resolution_against_runtime(
            _snapshot(RuntimeEffectiveAction.RUNTIME_ALLOW), rps,
        )
        assert proj.custos_effective_action is CustosEffectiveAction.WOULD_DENY
