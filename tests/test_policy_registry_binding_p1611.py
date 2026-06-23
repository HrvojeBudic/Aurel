"""P1.6.11 Policy Resolution Context & Registry Binding tests."""
from __future__ import annotations

import inspect
import pytest

from agentic_runtime.policy_cards import (
    FamilyDecision,
    PolicyCardRegistry,
    PolicyCardRegistryValidationError,
    PolicyContextBindingError,
    PolicyFamily,
    PolicyResolutionContext,
    PolicyRiskMappingError,
    PolicyRuntimeResolver,
    RiskTier,
    ShadowAction,
    build_policy_resolution_context,
    context_from_command_like,
    context_from_runtime_request_like,
    context_from_tool_invocation_like,
    create_default_data_residency_policy_card,
    create_default_human_oversight_policy_card,
    create_default_memory_write_policy_card,
    create_default_prompt_policy_card,
    create_default_risk_tier_policy_card,
    create_default_sandbox_policy_card,
    map_approval_risk_to_policy_tier,
    map_identity_risk_to_policy_tier,
    map_runtime_risk_to_policy_tier,
    normalize_resolution_context,
    normalize_risk_tier,
    resolve_policy_cards_from_registry,
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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _pc(
    kind: PolicyCardKind,
    cid: str,
    scope: PolicyCardScope | None = None,
) -> PolicyCard:
    return PolicyCard(
        schema_version="1.0",
        identity=PolicyCardIdentity(
            card_id=cid,
            slug=cid,
            name=cid,
            version="1.0",
            namespace="test",
        ),
        kind=kind,
        status=PolicyCardStatus.ACTIVE,
        scope=scope or PolicyCardScope(scope_type=PolicyCardScopeType.GLOBAL),
        description="test card",
    )


def _tool_deny_card(
    tool: str = "rm",
    cid: str = "tool-deny",
    scope: PolicyCardScope | None = None,
) -> ToolPermissionPolicyCard:
    return ToolPermissionPolicyCard(
        policy_card=_pc(PolicyCardKind.TOOL_PERMISSION, cid, scope),
        schema_version="1.0",
        permission_rules=(
            ToolPermissionRule(
                matcher=ToolIdentityMatcher(
                    match_mode=ToolMatchMode.EXACT,
                    tool_name=tool,
                ),
                permission_type=ToolPermissionType.EXECUTE,
                decision=ToolPermissionDecision.DENY,
            ),
        ),
        default_decision=ToolPermissionDecision.DENY,
    )


def _default_cards() -> list[object]:
    return [
        create_default_risk_tier_policy_card(),
        create_default_human_oversight_policy_card(),
        create_default_data_residency_policy_card(),
        _tool_deny_card("rm"),
        create_default_memory_write_policy_card(),
        create_default_prompt_policy_card(),
        create_default_sandbox_policy_card(),
    ]


# ---------------------------------------------------------------------------
# 1. Registry construction
# ---------------------------------------------------------------------------


def test_empty_registry_valid_and_hash_ready():
    registry = PolicyCardRegistry()
    assert registry.list_cards() == ()
    assert registry.list_card_ids() == ()
    assert registry.source_hashes() == ()
    assert len(registry.canonical_hash()) == 64
    assert registry.canonical_dict() == {"cards": [], "source_hashes": []}


def test_registry_from_cards_register_single_many_and_order_deterministic():
    cards = _default_cards()
    registry = PolicyCardRegistry.from_cards(reversed(cards))
    ids = registry.list_card_ids()
    assert ids == registry.list_card_ids()

    same = PolicyCardRegistry()
    same.register_card(cards[3])
    same.register_cards([cards[0], cards[1]])
    assert same.list_card_ids() == same.list_card_ids()

    shuffled = PolicyCardRegistry.from_cards([cards[1], cards[3], cards[0]])
    unshuffled = PolicyCardRegistry.from_cards([cards[0], cards[1], cards[3]])
    assert shuffled.list_card_ids() == unshuffled.list_card_ids()
    assert shuffled.canonical_hash() == unshuffled.canonical_hash()


# ---------------------------------------------------------------------------
# 2. Duplicate handling
# ---------------------------------------------------------------------------


def test_duplicate_same_card_id_same_hash_deduplicates():
    card = _tool_deny_card("rm", cid="dup-tool")
    registry = PolicyCardRegistry.from_cards([card, card])
    assert registry.list_card_ids() == ("dup-tool",)


def test_duplicate_same_card_id_different_hash_rejected_with_reason():
    first = _tool_deny_card("rm", cid="dup-tool")
    second = _tool_deny_card("curl", cid="dup-tool")
    with pytest.raises(PolicyCardRegistryValidationError) as exc:
        PolicyCardRegistry.from_cards([first, second])
    assert "duplicate policy card id 'dup-tool' has different canonical hash" in str(exc.value)


def test_registry_rejects_dict_loading_closed_world():
    with pytest.raises(PolicyCardRegistryValidationError) as exc:
        PolicyCardRegistry.from_cards([{"card_id": "x"}])
    assert "typed card instances" in str(exc.value)


# ---------------------------------------------------------------------------
# 3. Family and scope lookup
# ---------------------------------------------------------------------------


def test_get_by_family_and_unknown_family_are_deterministic():
    registry = PolicyCardRegistry.from_cards(_default_cards())
    assert [c.policy_card.identity.card_id for c in registry.get_by_family("tool_permission")] == ["tool-deny"]
    assert [c.policy_card.identity.card_id for c in registry.get_by_family(PolicyFamily.SANDBOX)] == ["aurel-core-sandbox-policy-v1"]
    assert registry.get_by_family("business_process") == ()
    assert registry.get_by_family("unknown") == ()


def test_get_by_scope_matches_scope_type_scope_id_and_applies_to():
    scoped = _tool_deny_card(
        "rm",
        cid="scoped-tool",
        scope=PolicyCardScope(
            scope_type=PolicyCardScopeType.TOOL,
            scope_id="rm",
            applies_to=("delete",),
        ),
    )
    global_card = create_default_risk_tier_policy_card()
    registry = PolicyCardRegistry.from_cards([scoped, global_card])
    assert registry.get_by_scope(PolicyCardScopeType.TOOL) == (scoped,)
    assert registry.get_by_scope("rm") == (scoped,)
    assert registry.get_by_scope("delete") == (scoped,)
    assert registry.get_by_scope("global") == (global_card,)


# ---------------------------------------------------------------------------
# 4. Applicability filtering
# ---------------------------------------------------------------------------


def test_tool_permission_card_applies_to_matching_tool_context_only():
    matching = _tool_deny_card("rm", cid="tool-rm")
    nonmatching = _tool_deny_card("curl", cid="tool-curl")
    registry = PolicyCardRegistry.from_cards([nonmatching, matching])
    ctx = PolicyResolutionContext(context_id="ctx", tool_name="rm")
    assert registry.get_applicable(ctx) == (matching,)
    explanations = registry.explain_applicability(ctx)
    assert [e.to_canonical_dict() for e in explanations] == sorted(
        [e.to_canonical_dict() for e in explanations],
        key=lambda item: item["card_id"],
    )


def test_family_applicability_for_sandbox_prompt_memory_data_and_human_oversight():
    registry = PolicyCardRegistry.from_cards(_default_cards())

    sandbox_ctx = PolicyResolutionContext(context_id="s", runs_shell=True)
    assert registry.get_applicable(sandbox_ctx)[0].policy_card.kind == PolicyCardKind.SANDBOX

    prompt_ctx = PolicyResolutionContext(context_id="p", prompt_source_types=("web_content",))
    assert [c.policy_card.kind for c in registry.get_applicable(prompt_ctx)] == [PolicyCardKind.PROMPT]

    memory_ctx = PolicyResolutionContext(context_id="m", memory_write_intent=True)
    assert [c.policy_card.kind for c in registry.get_applicable(memory_ctx)] == [PolicyCardKind.MEMORY_WRITE]

    no_memory_ctx = PolicyResolutionContext(context_id="m0")
    assert create_default_memory_write_policy_card().policy_card.identity.card_id not in {
        c.policy_card.identity.card_id for c in registry.get_applicable(no_memory_ctx)
    }

    data_ctx = PolicyResolutionContext(context_id="d", data_classes=("credentials",))
    assert [c.policy_card.kind for c in registry.get_applicable(data_ctx)] == [PolicyCardKind.DATA_RESIDENCY]

    risk_ctx = PolicyResolutionContext(context_id="r", risk_tier="R4", requested_action="write_file")
    assert [c.policy_card.kind for c in registry.get_applicable(risk_ctx)] == [
        PolicyCardKind.RISK_TIER,
        PolicyCardKind.HUMAN_OVERSIGHT,
    ]


def test_insufficient_context_is_skipped_with_stable_reasons():
    registry = PolicyCardRegistry.from_cards(_default_cards())
    ctx = PolicyResolutionContext(context_id="empty")
    assert registry.get_applicable(ctx) == ()
    explanations = registry.explain_applicability(ctx)
    assert {e.reason_codes for e in explanations} == {("SKIPPED_CONTEXT_MISSING",)}


# ---------------------------------------------------------------------------
# 5. Context binding
# ---------------------------------------------------------------------------


def test_build_minimal_context_is_deterministic():
    first = build_policy_resolution_context({})
    second = build_policy_resolution_context({})
    assert first.context_id == second.context_id
    assert first.context_hash == second.context_hash
    assert first.risk_tier is None


def test_build_full_context_sorts_fields_maps_risk_and_validates_metadata():
    ctx = build_policy_resolution_context(
        {
            "command_id": "cmd-1",
            "summary": "run command",
            "action": "execute",
            "tool": "pytest",
            "category": "shell",
            "runtime_risk": "HIGH",
            "requested_paths": {"/b", "/a"},
            "requested_network_targets": ["z.example", "a.example"],
            "prompt_source_types": ["web_content", "system_prompt"],
            "data_classes": ["public", "credentials"],
            "runs_shell": True,
            "metadata": {"owner": "test"},
        }
    )
    assert ctx.context_id == "cmd-1"
    assert ctx.command_summary == "run command"
    assert ctx.requested_action == "execute"
    assert ctx.tool_name == "pytest"
    assert ctx.tool_category == "shell"
    assert ctx.risk_tier == "R4"
    assert ctx.requested_paths == ("/a", "/b")
    assert ctx.requested_network_targets == ("a.example", "z.example")
    assert ctx.prompt_source_types == ("system_prompt", "web_content")
    assert ctx.data_classes == ("credentials", "public")
    assert ctx.metadata["risk_mapping_reason"] == "RUNTIME_RISK_MAPPED"


def test_context_binding_rejects_unknown_fields_and_bad_metadata():
    with pytest.raises(PolicyContextBindingError):
        build_policy_resolution_context({"context_id": "c", "surprise": True})
    with pytest.raises(PolicyContextBindingError):
        build_policy_resolution_context({"context_id": "c", "metadata": {"bad": {"set"}}})
    with pytest.raises(PolicyContextBindingError):
        build_policy_resolution_context({"context_id": "c", "metadata": {"force_allow": True}})


def test_context_from_like_helpers_and_normalize_context_are_runtime_free():
    class ToolLike:
        context_id = "tool-ctx"
        tool_name = "rm"
        risk = "LOW"
        requested_paths = ["/z", "/a"]

    cmd_ctx = context_from_command_like({"command_id": "cmd", "action": "write", "risk": "MEDIUM"})
    tool_ctx = context_from_tool_invocation_like(ToolLike())
    runtime_ctx = context_from_runtime_request_like({"context_id": "rt", "approval_risk_class": "R5"})
    normalized = normalize_resolution_context(
        PolicyResolutionContext(context_id="n", requested_paths=("/z", "/a"))
    )

    assert cmd_ctx.risk_tier == "R3"
    assert tool_ctx.risk_tier == "R1"
    assert tool_ctx.requested_paths == ("/a", "/z")
    assert runtime_ctx.risk_tier == "R5"
    assert normalized.requested_paths == ("/a", "/z")

    from agentic_runtime.policy_cards import context_binding as binding_mod
    source = inspect.getsource(binding_mod)
    assert "from ..runtime" not in source
    assert "agentic_runtime.runtime" not in source
    assert ".submit(" not in source


# ---------------------------------------------------------------------------
# 6. Risk mapping
# ---------------------------------------------------------------------------


def test_runtime_risk_mapping_known_values():
    assert map_runtime_risk_to_policy_tier("LOW").normalized_tier == "R1"
    assert map_runtime_risk_to_policy_tier("HIGH").normalized_tier == "R4"
    critical = map_runtime_risk_to_policy_tier("CRITICAL")
    assert critical.normalized_tier == "R6"
    assert critical.conservative is True


def test_approval_policy_identity_unknown_and_invalid_risk_mapping():
    assert map_approval_risk_to_policy_tier("R0").normalized_tier == "R0"
    r5 = map_approval_risk_to_policy_tier("R5")
    r6 = map_approval_risk_to_policy_tier("R6")
    assert (r5.normalized_tier, r5.conservative) == ("R5", True)
    assert (r6.normalized_tier, r6.conservative) == ("R6", True)

    passthrough = normalize_risk_tier(RiskTier.R3)
    assert passthrough.normalized_tier == "R3"
    assert passthrough.reason_code == "POLICY_RISK_TIER_PASSTHROUGH"

    identity = map_identity_risk_to_policy_tier("dangerous")
    assert identity.normalized_tier == "R5"
    assert identity.conservative is True

    unknown = normalize_risk_tier("vendor_custom_risk")
    assert unknown.normalized_tier == "R5"
    assert unknown.known is False
    assert unknown.conservative is True
    assert unknown.reason_code == "UNKNOWN_RISK_CONSERVATIVE"

    with pytest.raises(PolicyRiskMappingError):
        normalize_risk_tier(["LOW"])


# ---------------------------------------------------------------------------
# 7. Resolver integration
# ---------------------------------------------------------------------------


def test_registry_applicable_cards_feed_shadow_resolver():
    registry = PolicyCardRegistry.from_cards([_tool_deny_card("rm"), create_default_risk_tier_policy_card()])
    ctx = PolicyResolutionContext(context_id="ctx", tool_name="rm")
    result = resolve_policy_cards_from_registry(ctx, registry)
    assert result.overall_decision == FamilyDecision.DENY
    assert result.effective_shadow_action == ShadowAction.WOULD_DENY
    assert result.enforcement_mode.value == "shadow"
    assert result.applicable_card_ids == ("tool-deny",)


def test_same_registry_context_and_shuffled_input_give_same_result_hash():
    cards = [
        create_default_human_oversight_policy_card(),
        _tool_deny_card("rm"),
        create_default_risk_tier_policy_card(),
    ]
    ctx = PolicyResolutionContext(context_id="ctx", risk_tier="R4", tool_name="rm")
    first = resolve_policy_cards_from_registry(ctx, PolicyCardRegistry.from_cards(cards))
    second = resolve_policy_cards_from_registry(ctx, PolicyCardRegistry.from_cards(list(reversed(cards))))
    assert first.canonical_hash == second.canonical_hash
    assert first.resolution_id == second.resolution_id


def test_no_applicable_cards_from_registry_remains_conservative():
    registry = PolicyCardRegistry.from_cards([create_default_prompt_policy_card()])
    ctx = PolicyResolutionContext(context_id="ctx")
    result = resolve_policy_cards_from_registry(ctx, registry)
    assert result.overall_decision == FamilyDecision.WARN
    assert result.effective_shadow_action == ShadowAction.WOULD_WARN
    assert "NO_APPLICABLE_CARDS" in result.reason_codes


# ---------------------------------------------------------------------------
# 8. Shadow-only / non-enforcement
# ---------------------------------------------------------------------------


def test_registry_resolver_remain_shadow_only_and_do_not_expose_enforcement_methods():
    registry = PolicyCardRegistry.from_cards([_tool_deny_card("rm")])
    ctx = PolicyResolutionContext(context_id="ctx", tool_name="rm")
    result = PolicyRuntimeResolver().resolve_from_registry(ctx, registry)
    assert result.enforcement_mode.value == "shadow"
    assert result.effective_shadow_action.value.startswith("would_")
    for obj in (registry, result):
        for attr in ("enforce", "apply", "block", "execute", "approve", "submit"):
            assert not hasattr(obj, attr)


def test_no_agentic_runtime_submit_policy_card_wiring_or_sandbox_bridge():
    from agentic_runtime.runtime import AgenticRuntime
    from agentic_runtime.policy_cards import registry as registry_mod
    from agentic_runtime.policy_cards import resolver as resolver_mod

    submit_source = inspect.getsource(AgenticRuntime.submit)
    assert "PolicyCardRegistry" not in submit_source
    assert "resolve_policy_cards" not in submit_source
    assert "resolve_from_registry" not in submit_source

    registry_source = inspect.getsource(registry_mod)
    resolver_source = inspect.getsource(resolver_mod)
    for source in (registry_source, resolver_source):
        assert "from ..runtime" not in source
        assert "agentic_runtime.runtime" not in source
        assert "Approval" not in source
        assert ".submit(" not in source.replace("AgenticRuntime.submit()", "")
    assert "create_sandbox" not in registry_source
    assert "from ..sandbox_policy" not in registry_source
    assert "agentic_runtime.sandbox_policy" not in registry_source


# ---------------------------------------------------------------------------
# 9. Export tests
# ---------------------------------------------------------------------------


def test_public_exports_and_errors_import_without_circular_imports():
    from agentic_runtime.policy_cards import (  # noqa: F401
        PolicyCardApplicability,
        PolicyCardRegistry as _Registry,
        build_policy_resolution_context as _build,
        normalize_risk_tier as _normalize,
        resolve_policy_cards_from_registry as _resolve_registry,
    )
    from agentic_runtime.policy_cards.errors import (  # noqa: F401
        PolicyCardRegistryError,
        PolicyCardRegistryValidationError as _RegistryError,
        PolicyContextBindingError as _BindingError,
        PolicyRiskMappingError as _RiskError,
    )

    assert _Registry is PolicyCardRegistry
    assert _build is build_policy_resolution_context
    assert _normalize is normalize_risk_tier
    assert _resolve_registry is resolve_policy_cards_from_registry
    assert issubclass(_RegistryError, PolicyCardRegistryError)
    assert issubclass(_BindingError, Exception)
    assert issubclass(_RiskError, Exception)
