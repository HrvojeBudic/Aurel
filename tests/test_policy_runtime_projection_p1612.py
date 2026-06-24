"""P1.6.12 Custos shadow runtime projection tests."""
from __future__ import annotations

import inspect
import json

import pytest

from agentic_runtime.policy_cards import (
    CustosEffectiveAction,
    EnforcementMode,
    FamilyDecision,
    PolicyFamily,
    PolicyFamilyDecision,
    PolicyRuntimeAlignment,
    PolicyRuntimeMismatch,
    PolicyShadowProjection,
    PolicyShadowProjectionError,
    ResolvedPolicySet,
    RuntimeEffectiveAction,
    RuntimePolicySnapshot,
    ShadowAction,
    compute_policy_shadow_projection_hash,
    compute_runtime_policy_snapshot_hash,
    policy_shadow_projection_to_canonical_dict,
    project_policy_resolution_against_runtime,
    runtime_policy_snapshot_to_canonical_dict,
)


def _resolved(
    action: ShadowAction,
    *,
    family_decisions: tuple[PolicyFamilyDecision, ...] = (),
) -> ResolvedPolicySet:
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
        family_decisions=family_decisions,
        reason_codes=("Z_REASON", "A_REASON"),
        warnings=("z warning", "a warning"),
        violations=("z violation", "a violation"),
        approval_requirements=("approval",),
        applicable_card_ids=("card",),
        source_hashes=("b" * 64,),
    ).with_canonical_hash()


def _snapshot(action: RuntimeEffectiveAction) -> RuntimePolicySnapshot:
    return RuntimePolicySnapshot(
        runtime_effective_action=action,
        policy_verdict="allow",
        policy_risk="low",
        reason_codes=("runtime-z", "runtime-a"),
        warnings=("runtime warning",),
        violations=("runtime violation",),
        metadata={"tool": "read_file"},
    )


def test_runtime_snapshot_minimal_full_and_hash_deterministic():
    minimal = RuntimePolicySnapshot(RuntimeEffectiveAction.RUNTIME_ALLOW)
    full = _snapshot(RuntimeEffectiveAction.RUNTIME_REQUIRE_APPROVAL)
    assert minimal.runtime_effective_action is RuntimeEffectiveAction.RUNTIME_ALLOW
    assert len(compute_runtime_policy_snapshot_hash(full)) == 64
    assert compute_runtime_policy_snapshot_hash(full) == compute_runtime_policy_snapshot_hash(full)
    canonical = runtime_policy_snapshot_to_canonical_dict(full)
    assert canonical["reason_codes"] == ["runtime-a", "runtime-z"]
    json.dumps(canonical)


def test_projection_minimal_full_hash_and_sorted_payload():
    projection = PolicyShadowProjection(
        runtime_effective_action=RuntimeEffectiveAction.RUNTIME_ALLOW,
        custos_effective_action=CustosEffectiveAction.WOULD_WARN,
        alignment_status=PolicyRuntimeAlignment.CUSTOS_STRICTER,
        mismatch_codes=("Z", "A"),
        reason_codes=("Z", "A"),
        warnings=("Z", "A"),
        violations=("Z", "A"),
    ).with_projection_hash()
    payload = policy_shadow_projection_to_canonical_dict(projection)
    assert payload["enabled"] is True
    assert payload["mode"] == "shadow_only"
    assert payload["enforced"] is False
    assert payload["mismatch_codes"] == ["A", "Z"]
    assert payload["reason_codes"] == ["A", "Z"]
    assert payload["warnings"] == ["A", "Z"]
    assert payload["violations"] == ["A", "Z"]
    assert payload["projection_hash"] == compute_policy_shadow_projection_hash(projection)
    json.dumps(payload)


def test_projection_hash_excludes_hash_field_itself():
    base = PolicyShadowProjection(
        runtime_effective_action=RuntimeEffectiveAction.RUNTIME_ALLOW,
        custos_effective_action=CustosEffectiveAction.WOULD_ALLOW,
        alignment_status=PolicyRuntimeAlignment.ALIGNED,
    )
    with_hash = base.with_projection_hash()
    mutated_hash_only = PolicyShadowProjection(
        runtime_effective_action=RuntimeEffectiveAction.RUNTIME_ALLOW,
        custos_effective_action=CustosEffectiveAction.WOULD_ALLOW,
        alignment_status=PolicyRuntimeAlignment.ALIGNED,
        projection_hash="f" * 64,
    )
    assert compute_policy_shadow_projection_hash(with_hash) == compute_policy_shadow_projection_hash(mutated_hash_only)


def test_projection_is_shadow_only_and_has_no_enforcement_surface():
    with pytest.raises(PolicyShadowProjectionError):
        PolicyShadowProjection(
            runtime_effective_action=RuntimeEffectiveAction.RUNTIME_ALLOW,
            custos_effective_action=CustosEffectiveAction.WOULD_ALLOW,
            alignment_status=PolicyRuntimeAlignment.ALIGNED,
            enforced=True,
        )
    methods = {name for name, value in inspect.getmembers(PolicyShadowProjection) if callable(value)}
    assert not {"enforce", "apply", "block", "execute", "approve", "submit"} & methods


@pytest.mark.parametrize(
    ("runtime_action", "shadow_action", "alignment", "mismatch"),
    [
        (RuntimeEffectiveAction.RUNTIME_ALLOW, ShadowAction.WOULD_ALLOW, PolicyRuntimeAlignment.ALIGNED, None),
        (RuntimeEffectiveAction.RUNTIME_ALLOW, ShadowAction.WOULD_DENY, PolicyRuntimeAlignment.CUSTOS_STRICTER, PolicyRuntimeMismatch.RUNTIME_ALLOWED_CUSTOS_WOULD_DENY.value),
        (RuntimeEffectiveAction.RUNTIME_ALLOW, ShadowAction.WOULD_REQUIRE_APPROVAL, PolicyRuntimeAlignment.CUSTOS_STRICTER, PolicyRuntimeMismatch.RUNTIME_ALLOWED_CUSTOS_WOULD_REQUIRE_APPROVAL.value),
        (RuntimeEffectiveAction.RUNTIME_ALLOW, ShadowAction.WOULD_WARN, PolicyRuntimeAlignment.CUSTOS_STRICTER, PolicyRuntimeMismatch.RUNTIME_ALLOWED_CUSTOS_WOULD_WARN.value),
        (RuntimeEffectiveAction.RUNTIME_DENY, ShadowAction.WOULD_ALLOW, PolicyRuntimeAlignment.RUNTIME_STRICTER, PolicyRuntimeMismatch.RUNTIME_DENIED_CUSTOS_WOULD_ALLOW.value),
        (RuntimeEffectiveAction.RUNTIME_REQUIRE_APPROVAL, ShadowAction.WOULD_ALLOW, PolicyRuntimeAlignment.RUNTIME_STRICTER, PolicyRuntimeMismatch.RUNTIME_REQUIRES_APPROVAL_CUSTOS_WOULD_ALLOW.value),
        (RuntimeEffectiveAction.RUNTIME_WARN, ShadowAction.WOULD_ALLOW, PolicyRuntimeAlignment.RUNTIME_STRICTER, PolicyRuntimeMismatch.RUNTIME_WARNED_CUSTOS_WOULD_ALLOW.value),
        (RuntimeEffectiveAction.RUNTIME_UNKNOWN, ShadowAction.WOULD_ALLOW, PolicyRuntimeAlignment.INSUFFICIENT_CONTEXT, PolicyRuntimeMismatch.RUNTIME_CONTEXT_INSUFFICIENT.value),
        (RuntimeEffectiveAction.RUNTIME_ALLOW, ShadowAction.WOULD_ERROR, PolicyRuntimeAlignment.SHADOW_ERROR, PolicyRuntimeMismatch.CUSTOS_SHADOW_RESOLUTION_ERROR.value),
        (RuntimeEffectiveAction.RUNTIME_ALLOW, ShadowAction.WOULD_NOT_APPLY, PolicyRuntimeAlignment.INSUFFICIENT_CONTEXT, PolicyRuntimeMismatch.CUSTOS_CONTEXT_INSUFFICIENT.value),
    ],
)
def test_full_projection_matrix(runtime_action, shadow_action, alignment, mismatch):
    projection = project_policy_resolution_against_runtime(
        _snapshot(runtime_action),
        _resolved(shadow_action),
        registry_hash="c" * 64,
    )
    payload = projection.to_canonical_dict()
    assert payload["alignment_status"] == alignment.value
    if mismatch is None:
        assert payload["mismatch_codes"] == []
    else:
        assert mismatch in payload["mismatch_codes"]


def test_sandbox_policy_card_stricter_than_runtime_code_added():
    sandbox_decision = PolicyFamilyDecision(
        family=PolicyFamily.SANDBOX,
        decision=FamilyDecision.DENY,
        effective_shadow_action=ShadowAction.WOULD_DENY,
        reason_codes=("SANDBOX_BACKEND_DENIED",),
    )
    projection = project_policy_resolution_against_runtime(
        _snapshot(RuntimeEffectiveAction.RUNTIME_ALLOW),
        _resolved(ShadowAction.WOULD_DENY, family_decisions=(sandbox_decision,)),
    )
    assert PolicyRuntimeMismatch.SANDBOX_POLICY_CARD_STRICTER_THAN_RUNTIME.value in projection.mismatch_codes


def test_runtime_policy_stricter_than_custos_code_added():
    projection = project_policy_resolution_against_runtime(
        _snapshot(RuntimeEffectiveAction.RUNTIME_DENY),
        _resolved(ShadowAction.WOULD_ALLOW),
    )
    assert PolicyRuntimeMismatch.RUNTIME_POLICY_STRICTER_THAN_CUSTOS.value in projection.mismatch_codes
