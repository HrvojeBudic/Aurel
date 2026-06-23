"""Tests for Custos v0 Policy Runtime Resolver — SHADOW MODE (P1.6.10).

Covers: context construction/serialization, no-card behavior, single-family
adapters, strictest-wins aggregation, shadow-mode semantics, deterministic
serialization/hash, cross-family resolution, public exports, and the
non-enforcement guarantee.
"""
from __future__ import annotations

import json

import pytest

from agentic_runtime.policy_cards import (
    EnforcementMode,
    FamilyDecision,
    PolicyFamily,
    PolicyFamilyDecision,
    PolicyResolutionContext,
    PolicyRuntimeResolver,
    ResolvedPolicySet,
    ShadowAction,
    aggregate_family_decisions,
    compute_policy_resolution_context_hash,
    compute_resolved_policy_set_hash,
    create_default_data_residency_policy_card,
    create_default_human_oversight_policy_card,
    create_default_memory_write_policy_card,
    create_default_prompt_policy_card,
    create_default_risk_tier_policy_card,
    create_default_sandbox_policy_card,
    create_default_tool_permission_policy_card,
    decision_to_shadow_action,
    load_policy_resolution_context_from_dict,
    policy_resolution_context_to_canonical_dict,
    resolve_policy_cards,
    resolved_policy_set_to_canonical_dict,
)
from agentic_runtime.policy_cards.errors import (
    PolicyCardError,
    PolicyResolutionContextError,
    PolicyResolutionError,
    PolicyResolutionValidationError,
)
from agentic_runtime.policy_cards.models import (
    PolicyCard,
    PolicyCardIdentity,
    PolicyCardKind,
    PolicyCardScope,
    PolicyCardScopeType,
    PolicyCardStatus,
)
from agentic_runtime.policy_cards.tool_permissions import (
    ToolIdentityMatcher,
    ToolMatchMode,
    ToolPermissionDecision,
    ToolPermissionPolicyCard,
    ToolPermissionRule,
    ToolPermissionType,
)


# ─────────────────────────── helpers ───────────────────────────


def _pc(kind: PolicyCardKind, cid: str,
        scope: PolicyCardScopeType = PolicyCardScopeType.GLOBAL) -> PolicyCard:
    return PolicyCard(
        schema_version="1.0",
        identity=PolicyCardIdentity(
            card_id=cid, slug=cid, name=cid, version="1.0", namespace="test",
        ),
        kind=kind,
        status=PolicyCardStatus.ACTIVE,
        scope=PolicyCardScope(scope_type=scope),
        description="test card",
    )


def _tool_deny_card(tool: str = "rm", cid: str = "tool-deny") -> ToolPermissionPolicyCard:
    return ToolPermissionPolicyCard(
        policy_card=_pc(PolicyCardKind.TOOL_PERMISSION, cid),
        schema_version="1.0",
        permission_rules=(
            ToolPermissionRule(
                matcher=ToolIdentityMatcher(
                    match_mode=ToolMatchMode.EXACT, tool_name=tool,
                ),
                permission_type=ToolPermissionType.EXECUTE,
                decision=ToolPermissionDecision.DENY,
            ),
        ),
        default_decision=ToolPermissionDecision.DENY,
    )


def _fd(family: PolicyFamily, decision: FamilyDecision, **kw) -> PolicyFamilyDecision:
    return PolicyFamilyDecision(
        family=family,
        decision=decision,
        effective_shadow_action=decision_to_shadow_action(decision),
        **kw,
    )


# ═══════════════════════ 1. Context construction ═══════════════════════


def test_minimal_context_valid():
    ctx = PolicyResolutionContext(context_id="c1")
    assert ctx.context_id == "c1"
    assert ctx.memory_write_intent is False
    assert ctx.requested_paths == ()


def test_full_context_valid():
    ctx = PolicyResolutionContext(
        context_id="c2",
        agent_id="agent-1",
        operator_id="op-1",
        command_id="cmd-1",
        command_summary="run tests",
        requested_action="run_tests",
        tool_name="pytest",
        tool_category="shell",
        command_class="shell_command",
        risk_tier="R3",
        requested_sandbox_backend="restricted_local",
        requested_filesystem_scope="read_only_project",
        requested_egress="no_egress",
        requested_model="local-model",
        requested_paths=("/proj/a",),
        requested_network_targets=(),
        prompt_source_types=("system_prompt",),
        data_classes=("public",),
        memory_write_intent=True,
        touches_secrets=False,
        writes_files=True,
        runs_shell=True,
        installs_packages=False,
        requires_network=False,
        metadata={"note": "ok"},
    )
    assert ctx.risk_tier == "R3"
    assert ctx.writes_files is True


def test_context_canonical_serialization_sorts_lists():
    ctx = PolicyResolutionContext(
        context_id="c3", data_classes=("zeta", "alpha"),
        prompt_source_types=("web_content", "system_prompt"),
    )
    d = policy_resolution_context_to_canonical_dict(ctx)
    assert d["data_classes"] == ["alpha", "zeta"]
    assert d["prompt_source_types"] == ["system_prompt", "web_content"]


def test_context_hash_deterministic():
    a = PolicyResolutionContext(context_id="c4", risk_tier="R3", tool_name="x")
    b = PolicyResolutionContext(context_id="c4", risk_tier="R3", tool_name="x")
    assert compute_policy_resolution_context_hash(a) == compute_policy_resolution_context_hash(b)
    assert a.context_hash == b.context_hash


def test_context_hash_changes_with_field():
    a = PolicyResolutionContext(context_id="c5", risk_tier="R3")
    b = PolicyResolutionContext(context_id="c5", risk_tier="R4")
    assert a.context_hash != b.context_hash


def test_context_from_dict_roundtrip():
    ctx = PolicyResolutionContext(
        context_id="c6", risk_tier="R2", data_classes=("public",),
        memory_write_intent=True,
    )
    d = policy_resolution_context_to_canonical_dict(ctx)
    reloaded = load_policy_resolution_context_from_dict(d)
    assert reloaded.context_hash == ctx.context_hash


def test_context_from_dict_unknown_field_rejected():
    with pytest.raises(PolicyResolutionContextError):
        load_policy_resolution_context_from_dict({"context_id": "c", "backdoor": True})


def test_context_from_dict_missing_id_rejected():
    with pytest.raises(PolicyResolutionContextError):
        load_policy_resolution_context_from_dict({"risk_tier": "R3"})


def test_context_invalid_risk_tier_rejected():
    with pytest.raises(PolicyResolutionContextError):
        PolicyResolutionContext(context_id="c", risk_tier="R9")


def test_context_invalid_bool_rejected():
    with pytest.raises(PolicyResolutionContextError):
        load_policy_resolution_context_from_dict(
            {"context_id": "c", "runs_shell": "yes"}
        )


def test_context_dangerous_metadata_rejected():
    with pytest.raises(PolicyResolutionContextError):
        PolicyResolutionContext(context_id="c", metadata={"force_allow": True})


# ═══════════════════════ 2. Empty / no-card behavior ═══════════════════════


def test_no_cards_does_not_silently_allow():
    ctx = PolicyResolutionContext(context_id="c", risk_tier="R3")
    res = resolve_policy_cards(ctx, [])
    assert res.overall_decision != FamilyDecision.ALLOW
    assert res.effective_shadow_action != ShadowAction.WOULD_ALLOW
    assert "NO_CARDS_PROVIDED" in res.reason_codes
    assert "NO_APPLICABLE_CARDS" in res.reason_codes


def test_no_applicable_cards_conservative():
    ctx = PolicyResolutionContext(context_id="c")  # nothing actionable
    cards = [
        create_default_memory_write_policy_card(),
        create_default_data_residency_policy_card(),
        create_default_prompt_policy_card(),
        create_default_tool_permission_policy_card(),
    ]
    res = resolve_policy_cards(ctx, cards)
    assert res.overall_decision == FamilyDecision.WARN
    assert res.effective_shadow_action == ShadowAction.WOULD_WARN
    assert "NO_APPLICABLE_CARDS" in res.reason_codes
    # all families resolved NOT_APPLICABLE
    assert all(
        fd.decision == FamilyDecision.NOT_APPLICABLE for fd in res.family_decisions
    )


# ═══════════════════════ 3. Single-family adapters ═══════════════════════


def test_tool_permission_deny_would_deny():
    ctx = PolicyResolutionContext(context_id="c", tool_name="rm")
    res = resolve_policy_cards(ctx, [_tool_deny_card("rm")])
    assert res.overall_decision == FamilyDecision.DENY
    assert res.effective_shadow_action == ShadowAction.WOULD_DENY
    assert res.would_deny is True


def test_human_oversight_approval_would_require_approval():
    ctx = PolicyResolutionContext(context_id="c", risk_tier="R4")
    res = resolve_policy_cards(ctx, [create_default_human_oversight_policy_card()])
    assert res.overall_decision == FamilyDecision.REQUIRE_APPROVAL
    assert res.effective_shadow_action == ShadowAction.WOULD_REQUIRE_APPROVAL


def test_human_oversight_deny_tier_would_deny():
    ctx = PolicyResolutionContext(context_id="c", risk_tier="R6")
    res = resolve_policy_cards(ctx, [create_default_human_oversight_policy_card()])
    assert res.overall_decision == FamilyDecision.DENY


def test_prompt_untrusted_source_warn_or_approval():
    ctx = PolicyResolutionContext(context_id="c", prompt_source_types=("web_content",))
    res = resolve_policy_cards(ctx, [create_default_prompt_policy_card()])
    assert res.overall_decision in (FamilyDecision.WARN, FamilyDecision.REQUIRE_APPROVAL)
    assert res.effective_shadow_action in (
        ShadowAction.WOULD_WARN, ShadowAction.WOULD_REQUIRE_APPROVAL,
    )


def test_sandbox_unsafe_local_high_risk():
    ctx = PolicyResolutionContext(
        context_id="c", risk_tier="R5",
        requested_sandbox_backend="unsafe_local", runs_shell=True,
    )
    res = resolve_policy_cards(ctx, [create_default_sandbox_policy_card()])
    assert res.overall_decision in (FamilyDecision.REQUIRE_APPROVAL, FamilyDecision.DENY)


def test_memory_write_without_evidence():
    ctx = PolicyResolutionContext(context_id="c", memory_write_intent=True)
    res = resolve_policy_cards(ctx, [create_default_memory_write_policy_card()])
    assert res.overall_decision in (FamilyDecision.WARN, FamilyDecision.REQUIRE_APPROVAL)


def test_data_residency_mismatch_would_deny():
    ctx = PolicyResolutionContext(
        context_id="c", data_classes=("credentials",), requires_network=True,
    )
    res = resolve_policy_cards(ctx, [create_default_data_residency_policy_card()])
    assert res.overall_decision == FamilyDecision.DENY
    assert res.would_deny is True


def test_risk_tier_r6_would_deny():
    ctx = PolicyResolutionContext(context_id="c", risk_tier="R6")
    res = resolve_policy_cards(ctx, [create_default_risk_tier_policy_card()])
    assert res.overall_decision == FamilyDecision.DENY


def test_risk_tier_r5_requires_approval():
    ctx = PolicyResolutionContext(context_id="c", risk_tier="R5")
    res = resolve_policy_cards(ctx, [create_default_risk_tier_policy_card()])
    assert res.overall_decision == FamilyDecision.REQUIRE_APPROVAL


def test_memory_not_applicable_when_no_intent():
    ctx = PolicyResolutionContext(context_id="c", risk_tier="R1")
    res = resolve_policy_cards(ctx, [create_default_memory_write_policy_card()])
    fam = res.family_decisions[0]
    assert fam.family == PolicyFamily.MEMORY_WRITE
    assert fam.decision == FamilyDecision.NOT_APPLICABLE


# ═══════════════════════ 4. Aggregation (strictest-wins) ═══════════════════════


def test_deny_beats_require_approval():
    out = aggregate_family_decisions((
        _fd(PolicyFamily.RISK_TIER, FamilyDecision.REQUIRE_APPROVAL),
        _fd(PolicyFamily.TOOL_PERMISSION, FamilyDecision.DENY),
    ))
    assert out[0] == FamilyDecision.DENY
    assert out[1] == ShadowAction.WOULD_DENY


def test_require_approval_beats_warn():
    out = aggregate_family_decisions((
        _fd(PolicyFamily.RISK_TIER, FamilyDecision.WARN),
        _fd(PolicyFamily.HUMAN_OVERSIGHT, FamilyDecision.REQUIRE_APPROVAL),
    ))
    assert out[0] == FamilyDecision.REQUIRE_APPROVAL


def test_warn_beats_allow():
    out = aggregate_family_decisions((
        _fd(PolicyFamily.RISK_TIER, FamilyDecision.ALLOW),
        _fd(PolicyFamily.PROMPT, FamilyDecision.WARN),
    ))
    assert out[0] == FamilyDecision.WARN


def test_all_allow_is_allow():
    out = aggregate_family_decisions((
        _fd(PolicyFamily.RISK_TIER, FamilyDecision.ALLOW),
        _fd(PolicyFamily.TOOL_PERMISSION, FamilyDecision.ALLOW),
    ))
    assert out[0] == FamilyDecision.ALLOW
    assert out[1] == ShadowAction.WOULD_ALLOW


def test_not_applicable_does_not_override():
    out = aggregate_family_decisions((
        _fd(PolicyFamily.RISK_TIER, FamilyDecision.ALLOW),
        _fd(PolicyFamily.MEMORY_WRITE, FamilyDecision.NOT_APPLICABLE),
    ))
    assert out[0] == FamilyDecision.ALLOW


def test_error_escalates_conservatively():
    out = aggregate_family_decisions((
        _fd(PolicyFamily.RISK_TIER, FamilyDecision.ALLOW),
        _fd(PolicyFamily.SANDBOX, FamilyDecision.ERROR),
    ))
    assert out[0] == FamilyDecision.REQUIRE_APPROVAL
    assert "ADAPTER_ERROR_CONSERVATIVE" in out[2]


def test_aggregation_reason_ordering_deterministic():
    fds = (
        _fd(PolicyFamily.RISK_TIER, FamilyDecision.WARN, reason_codes=("Z", "A")),
        _fd(PolicyFamily.PROMPT, FamilyDecision.WARN, reason_codes=("M",)),
    )
    out1 = aggregate_family_decisions(fds)
    out2 = aggregate_family_decisions(fds)
    assert out1[2] == out2[2]
    assert list(out1[2]) == sorted(out1[2])


def test_same_input_same_result_hash():
    ctx = PolicyResolutionContext(context_id="c", risk_tier="R3", tool_name="rm")
    cards = [_tool_deny_card("rm"), create_default_risk_tier_policy_card()]
    r1 = resolve_policy_cards(ctx, cards)
    r2 = resolve_policy_cards(ctx, cards)
    assert r1.canonical_hash == r2.canonical_hash
    assert r1.resolution_id == r2.resolution_id


# ═══════════════════════ 5. Shadow mode ═══════════════════════


def test_enforcement_mode_is_shadow():
    ctx = PolicyResolutionContext(context_id="c", risk_tier="R3")
    res = resolve_policy_cards(ctx, [create_default_risk_tier_policy_card()])
    assert res.enforcement_mode == EnforcementMode.SHADOW


def test_effective_action_uses_would_semantics():
    ctx = PolicyResolutionContext(context_id="c", risk_tier="R3")
    res = resolve_policy_cards(ctx, [create_default_risk_tier_policy_card()])
    assert res.effective_shadow_action.value.startswith("would_")
    for fd in res.family_decisions:
        assert fd.effective_shadow_action.value.startswith("would_")


def test_enforce_mode_rejected():
    ctx = PolicyResolutionContext(context_id="c")
    with pytest.raises(PolicyResolutionValidationError):
        resolve_policy_cards(ctx, [], EnforcementMode.ENFORCE)


def test_simulate_mode_rejected():
    ctx = PolicyResolutionContext(context_id="c")
    with pytest.raises(PolicyResolutionValidationError):
        resolve_policy_cards(ctx, [], EnforcementMode.SIMULATE)


def test_resolver_class_enforce_rejected():
    with pytest.raises(PolicyResolutionValidationError):
        PolicyRuntimeResolver(EnforcementMode.ENFORCE)


def test_resolver_class_shadow_resolves():
    resolver = PolicyRuntimeResolver()
    ctx = PolicyResolutionContext(context_id="c", risk_tier="R3")
    res = resolver.resolve(ctx, [create_default_risk_tier_policy_card()])
    assert isinstance(res, ResolvedPolicySet)
    assert res.enforcement_mode == EnforcementMode.SHADOW


def test_resolver_used_independently_of_runtime():
    # The resolver must be usable without constructing AgenticRuntime.
    ctx = PolicyResolutionContext(context_id="c", risk_tier="R2")
    res = resolve_policy_cards(ctx, [create_default_risk_tier_policy_card()])
    assert isinstance(res, ResolvedPolicySet)


# ═══════════════════════ 6. Serialization / hash ═══════════════════════


def test_resolved_set_canonical_dict_deterministic():
    ctx = PolicyResolutionContext(context_id="c", risk_tier="R3", tool_name="rm")
    cards = [_tool_deny_card("rm")]
    d1 = resolved_policy_set_to_canonical_dict(resolve_policy_cards(ctx, cards))
    d2 = resolved_policy_set_to_canonical_dict(resolve_policy_cards(ctx, cards))
    assert d1 == d2
    assert json.dumps(d1, sort_keys=True) == json.dumps(d2, sort_keys=True)


def test_resolved_set_hash_deterministic_and_64():
    ctx = PolicyResolutionContext(context_id="c", risk_tier="R3")
    cards = [create_default_risk_tier_policy_card()]
    res = resolve_policy_cards(ctx, cards)
    assert res.canonical_hash is not None
    assert len(res.canonical_hash) == 64
    assert compute_resolved_policy_set_hash(res) == res.canonical_hash


def test_resolved_set_includes_source_card_ids_and_hashes():
    ctx = PolicyResolutionContext(context_id="c", tool_name="rm")
    res = resolve_policy_cards(ctx, [_tool_deny_card("rm", cid="tool-deny-x")])
    assert "tool-deny-x" in res.applicable_card_ids
    assert len(res.source_hashes) >= 1
    assert res.context_hash == ctx.context_hash


def test_canonical_hash_excludes_itself():
    ctx = PolicyResolutionContext(context_id="c", risk_tier="R3")
    res = resolve_policy_cards(ctx, [create_default_risk_tier_policy_card()])
    # serialization used for hashing must not contain canonical_hash
    canonical = resolved_policy_set_to_canonical_dict(res, include_hash=False)
    assert "canonical_hash" not in canonical


# ═══════════════════════ 7. Cross-family ═══════════════════════


def test_multiple_families_combine():
    ctx = PolicyResolutionContext(
        context_id="c", risk_tier="R3", tool_name="rm",
        prompt_source_types=("web_content",), memory_write_intent=True,
    )
    cards = [
        create_default_risk_tier_policy_card(),
        _tool_deny_card("rm"),
        create_default_prompt_policy_card(),
        create_default_memory_write_policy_card(),
    ]
    res = resolve_policy_cards(ctx, cards)
    families = {fd.family for fd in res.family_decisions}
    assert PolicyFamily.RISK_TIER in families
    assert PolicyFamily.TOOL_PERMISSION in families
    assert PolicyFamily.PROMPT in families
    assert PolicyFamily.MEMORY_WRITE in families


def test_conflicting_allow_deny_resolves_strictest():
    ctx = PolicyResolutionContext(
        context_id="c", risk_tier="R0", tool_name="rm",
    )
    # risk R0 → allow ; tool rm → deny
    cards = [create_default_risk_tier_policy_card(), _tool_deny_card("rm")]
    res = resolve_policy_cards(ctx, cards)
    assert res.overall_decision == FamilyDecision.DENY


def test_approvals_and_violations_aggregated():
    ctx = PolicyResolutionContext(
        context_id="c", risk_tier="R4", tool_name="rm",
    )
    cards = [
        create_default_human_oversight_policy_card(),  # R4 approval
        _tool_deny_card("rm"),                          # deny + violation
    ]
    res = resolve_policy_cards(ctx, cards)
    assert res.overall_decision == FamilyDecision.DENY
    assert len(res.violations) >= 1
    assert len(res.approval_requirements) >= 1
    assert len(res.applicable_card_ids) >= 2


# ═══════════════════════ 8. Exports ═══════════════════════


def test_public_imports_work():
    from agentic_runtime.policy_cards import (  # noqa: F401
        PolicyResolutionContext as _Ctx,
        ResolvedPolicySet as _Set,
        resolve_policy_cards as _resolve,
    )
    assert _Ctx is PolicyResolutionContext
    assert _Set is ResolvedPolicySet
    assert _resolve is resolve_policy_cards


def test_error_classes_importable_and_hierarchy():
    assert issubclass(PolicyResolutionValidationError, PolicyResolutionError)
    assert issubclass(PolicyResolutionError, PolicyCardError)
    assert issubclass(PolicyResolutionContextError, PolicyResolutionError)


def test_no_circular_import():
    import importlib
    mod = importlib.import_module("agentic_runtime.policy_cards.resolver")
    assert hasattr(mod, "resolve_policy_cards")


# ═══════════════════════ 9. Non-enforcement guarantees ═══════════════════════


def test_resolver_has_no_enforcement_surface():
    ctx = PolicyResolutionContext(context_id="c", tool_name="rm")
    res = resolve_policy_cards(ctx, [_tool_deny_card("rm")])
    for attr in ("enforce", "apply", "block", "execute", "dispose", "submit"):
        assert not hasattr(res, attr)


def test_resolver_module_does_not_import_or_call_runtime():
    # The resolver must not import the runtime or invoke submit(); shadow only.
    import inspect
    from agentic_runtime.policy_cards import resolver as resolver_mod
    src = inspect.getsource(resolver_mod)
    # No import of the runtime module and no instantiation/invocation of it.
    assert "import runtime" not in src
    assert "from .runtime" not in src
    assert "from ..runtime" not in src
    assert "agentic_runtime.runtime" not in src
    assert "AgenticRuntime(" not in src  # no instantiation
    assert ".submit(" not in src.replace("AgenticRuntime.submit()", "")  # no call


def test_resolution_is_side_effect_free():
    ctx = PolicyResolutionContext(context_id="c", tool_name="rm", risk_tier="R3")
    cards = [_tool_deny_card("rm"), create_default_risk_tier_policy_card()]
    before = ctx.context_hash
    r1 = resolve_policy_cards(ctx, cards)
    r2 = resolve_policy_cards(ctx, cards)
    # context unchanged, results identical
    assert ctx.context_hash == before
    assert r1.canonical_hash == r2.canonical_hash
