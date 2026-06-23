"""Deterministic policy-card registry (P1.6.11).

The registry is explicit and in-memory. It accepts resolver-ready policy-card
objects provided by the caller; it does not discover files, query databases, or
import runtime execution surfaces.
"""
from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping as MappingABC, Sequence
from dataclasses import dataclass
from typing import Any, Callable

from .data_residency import (
    DataResidencyPolicyCard,
    compute_data_residency_policy_card_hash,
)
from .errors import PolicyCardRegistryValidationError
from .human_oversight import (
    HumanOversightPolicyCard,
    compute_human_oversight_policy_card_hash,
)
from .memory_write import (
    MemoryWritePolicyCard,
    compute_memory_write_policy_card_hash,
)
from .models import PolicyCard, PolicyCardKind, PolicyCardScope, PolicyCardScopeType
from .prompt_policy import PromptPolicyCard, compute_prompt_policy_card_hash
from .resolution_context import PolicyResolutionContext
from .resolution_result import PolicyFamily
from .risk_tiers import RiskTierPolicyCard, compute_risk_tier_policy_card_hash
from .sandbox import SandboxPolicyCard, compute_sandbox_policy_card_hash
from .tool_permissions import (
    ToolMatchMode,
    ToolPermissionPolicyCard,
    compute_tool_permission_policy_card_hash,
)

CardHashFn = Callable[[Any], str]


@dataclass(frozen=True)
class PolicyCardApplicability:
    """Transparent applicability explanation for one card/context pair."""

    card_id: str
    family: PolicyFamily
    applicable: bool
    reason_codes: tuple[str, ...]

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "applicable": self.applicable,
            "card_id": self.card_id,
            "family": self.family.value,
            "reason_codes": sorted(self.reason_codes),
        }


_FAMILY_BY_CARD_TYPE: tuple[tuple[type[object], PolicyFamily, CardHashFn], ...] = (
    (RiskTierPolicyCard, PolicyFamily.RISK_TIER, compute_risk_tier_policy_card_hash),
    (HumanOversightPolicyCard, PolicyFamily.HUMAN_OVERSIGHT, compute_human_oversight_policy_card_hash),
    (DataResidencyPolicyCard, PolicyFamily.DATA_RESIDENCY, compute_data_residency_policy_card_hash),
    (ToolPermissionPolicyCard, PolicyFamily.TOOL_PERMISSION, compute_tool_permission_policy_card_hash),
    (MemoryWritePolicyCard, PolicyFamily.MEMORY_WRITE, compute_memory_write_policy_card_hash),
    (PromptPolicyCard, PolicyFamily.PROMPT, compute_prompt_policy_card_hash),
    (SandboxPolicyCard, PolicyFamily.SANDBOX, compute_sandbox_policy_card_hash),
)

_FAMILY_BY_KIND: dict[str, PolicyFamily] = {
    PolicyCardKind.RISK_TIER.value: PolicyFamily.RISK_TIER,
    PolicyCardKind.HUMAN_OVERSIGHT.value: PolicyFamily.HUMAN_OVERSIGHT,
    PolicyCardKind.DATA_RESIDENCY.value: PolicyFamily.DATA_RESIDENCY,
    PolicyCardKind.TOOL_PERMISSION.value: PolicyFamily.TOOL_PERMISSION,
    PolicyCardKind.MEMORY_WRITE.value: PolicyFamily.MEMORY_WRITE,
    PolicyCardKind.PROMPT.value: PolicyFamily.PROMPT,
    PolicyCardKind.SANDBOX.value: PolicyFamily.SANDBOX,
}

_FAMILY_ORDER: tuple[PolicyFamily, ...] = (
    PolicyFamily.RISK_TIER,
    PolicyFamily.HUMAN_OVERSIGHT,
    PolicyFamily.DATA_RESIDENCY,
    PolicyFamily.TOOL_PERMISSION,
    PolicyFamily.MEMORY_WRITE,
    PolicyFamily.PROMPT,
    PolicyFamily.SANDBOX,
)
_FAMILY_RANK: dict[PolicyFamily, int] = {family: idx for idx, family in enumerate(_FAMILY_ORDER)}


class PolicyCardRegistry:
    """Closed-world, deterministic in-memory registry for explicit card lists."""

    def __init__(self) -> None:
        self._cards_by_id: dict[str, object] = {}
        self._hash_by_id: dict[str, str] = {}

    @classmethod
    def from_cards(cls, cards: Iterable[object]) -> "PolicyCardRegistry":
        registry = cls()
        registry.register_cards(cards)
        return registry

    def register_card(self, card: object) -> "PolicyCardRegistry":
        if isinstance(card, MappingABC):
            raise PolicyCardRegistryValidationError(
                "registry accepts explicit typed card instances, not dict loading"
            )
        policy_card = _inner_policy_card(card)
        card_id = policy_card.identity.card_id
        card_hash = _card_hash(card)
        existing_hash = self._hash_by_id.get(card_id)
        if existing_hash is not None:
            if existing_hash != card_hash:
                raise PolicyCardRegistryValidationError(
                    f"duplicate policy card id '{card_id}' has different canonical hash"
                )
            return self
        self._cards_by_id[card_id] = card
        self._hash_by_id[card_id] = card_hash
        return self

    def register_cards(self, cards: Iterable[object]) -> "PolicyCardRegistry":
        if cards is None:
            raise PolicyCardRegistryValidationError("cards must be an iterable, not None")
        for card in cards:
            self.register_card(card)
        return self

    def list_cards(self) -> tuple[object, ...]:
        return tuple(sorted(self._cards_by_id.values(), key=_card_sort_key))

    def list_card_ids(self) -> tuple[str, ...]:
        return tuple(_card_id(card) for card in self.list_cards())

    def get_by_family(self, family: PolicyFamily | PolicyCardKind | str) -> tuple[object, ...]:
        normalized = _normalize_family(family)
        if normalized is None:
            return ()
        return tuple(card for card in self.list_cards() if _card_family(card) == normalized)

    def get_by_scope(self, scope: PolicyCardScopeType | str) -> tuple[object, ...]:
        scope_value = _scope_value(scope)
        if scope_value is None:
            return ()
        return tuple(
            card for card in self.list_cards()
            if _scope_matches_lookup(_card_scope(card), scope_value)
        )

    def explain_applicability(
        self,
        context: PolicyResolutionContext,
    ) -> tuple[PolicyCardApplicability, ...]:
        if not isinstance(context, PolicyResolutionContext):
            raise PolicyCardRegistryValidationError(
                "context must be a PolicyResolutionContext"
            )
        return tuple(_explain_card_applicability(card, context) for card in self.list_cards())

    def get_applicable(self, context: PolicyResolutionContext) -> tuple[object, ...]:
        explanations = self.explain_applicability(context)
        applicable_ids = {e.card_id for e in explanations if e.applicable}
        return tuple(card for card in self.list_cards() if _card_id(card) in applicable_ids)

    def source_hashes(self) -> tuple[str, ...]:
        return tuple(sorted(self._hash_by_id.values()))

    def canonical_dict(self) -> dict[str, Any]:
        cards = []
        for card in self.list_cards():
            pc = _inner_policy_card(card)
            scope = pc.scope
            cards.append({
                "canonical_hash": _card_hash(card),
                "card_id": pc.identity.card_id,
                "family": _card_family(card).value,
                "scope": _scope_to_canonical_dict(scope),
                "version": pc.identity.version,
            })
        return {
            "cards": cards,
            "source_hashes": list(self.source_hashes()),
        }

    def canonical_hash(self) -> str:
        payload = json.dumps(self.canonical_dict(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Card accessors
# ---------------------------------------------------------------------------


def _inner_policy_card(card: object) -> PolicyCard:
    policy_card = getattr(card, "policy_card", None)
    if not isinstance(policy_card, PolicyCard):
        raise PolicyCardRegistryValidationError(
            f"unsupported policy card object: {type(card).__name__}"
        )
    family = _card_family(card)
    if policy_card.kind.value != family.value:
        raise PolicyCardRegistryValidationError(
            f"card '{policy_card.identity.card_id}' family {family.value} does not match "
            f"inner policy kind {policy_card.kind.value}"
        )
    return policy_card


def _card_family(card: object) -> PolicyFamily:
    for card_type, family, _hash_fn in _FAMILY_BY_CARD_TYPE:
        if isinstance(card, card_type):
            return family
    raise PolicyCardRegistryValidationError(
        f"unsupported policy card object: {type(card).__name__}"
    )


def _card_hash(card: object) -> str:
    for card_type, _family, hash_fn in _FAMILY_BY_CARD_TYPE:
        if isinstance(card, card_type):
            return hash_fn(card)
    raise PolicyCardRegistryValidationError(
        f"unsupported policy card object: {type(card).__name__}"
    )


def _card_id(card: object) -> str:
    return _inner_policy_card(card).identity.card_id


def _card_scope(card: object) -> PolicyCardScope:
    return _inner_policy_card(card).scope


def _card_sort_key(card: object) -> tuple[str, ...]:
    pc = _inner_policy_card(card)
    scope = pc.scope
    family = _card_family(card)
    return (
        str(_FAMILY_RANK[family]),
        family.value,
        pc.identity.card_id,
        pc.identity.version,
        scope.scope_type.value,
        scope.scope_id or "",
        _card_hash(card),
    )


def _scope_to_canonical_dict(scope: PolicyCardScope) -> dict[str, Any]:
    result: dict[str, Any] = {"scope_type": scope.scope_type.value}
    if scope.scope_id is not None:
        result["scope_id"] = scope.scope_id
    if scope.applies_to:
        result["applies_to"] = sorted(scope.applies_to)
    return result


def _normalize_family(family: PolicyFamily | PolicyCardKind | str) -> PolicyFamily | None:
    if isinstance(family, PolicyFamily):
        return family
    if isinstance(family, PolicyCardKind):
        return _FAMILY_BY_KIND.get(family.value)
    if isinstance(family, str):
        return _FAMILY_BY_KIND.get(family)
    return None


def _scope_value(scope: PolicyCardScopeType | str) -> str | None:
    if isinstance(scope, PolicyCardScopeType):
        return scope.value
    if isinstance(scope, str):
        return scope
    return None


def _scope_matches_lookup(scope: PolicyCardScope, value: str) -> bool:
    return (
        scope.scope_type.value == value
        or scope.scope_id == value
        or value in scope.applies_to
    )


# ---------------------------------------------------------------------------
# Applicability
# ---------------------------------------------------------------------------


def _family_has_context_signal(family: PolicyFamily, ctx: PolicyResolutionContext) -> bool:
    if family == PolicyFamily.RISK_TIER:
        return ctx.risk_tier is not None
    if family == PolicyFamily.HUMAN_OVERSIGHT:
        return ctx.risk_tier is not None or ctx.requested_action is not None
    if family == PolicyFamily.DATA_RESIDENCY:
        return bool(ctx.data_classes)
    if family == PolicyFamily.TOOL_PERMISSION:
        return ctx.tool_name is not None or ctx.tool_category is not None
    if family == PolicyFamily.MEMORY_WRITE:
        return ctx.memory_write_intent
    if family == PolicyFamily.PROMPT:
        return bool(ctx.prompt_source_types)
    if family == PolicyFamily.SANDBOX:
        return _sandbox_context_signal(ctx)
    return False


def _sandbox_context_signal(ctx: PolicyResolutionContext) -> bool:
    return any((
        ctx.command_class is not None,
        ctx.requested_sandbox_backend is not None,
        ctx.requested_filesystem_scope is not None,
        ctx.requested_egress is not None,
        ctx.runs_shell,
        ctx.writes_files,
        ctx.installs_packages,
        ctx.requires_network,
        ctx.touches_secrets,
        bool(ctx.requested_paths),
        bool(ctx.requested_network_targets),
    ))


def _scope_applicable(card: object, ctx: PolicyResolutionContext) -> tuple[bool, str]:
    scope = _card_scope(card)
    scope_type = scope.scope_type
    if scope_type in (PolicyCardScopeType.GLOBAL, PolicyCardScopeType.RUNTIME):
        return True, "APPLICABLE_BY_SCOPE"
    if scope_type == PolicyCardScopeType.TOOL:
        return _match_named_scope(scope, (ctx.tool_name, ctx.tool_category), has_context=bool(ctx.tool_name or ctx.tool_category))
    if scope_type == PolicyCardScopeType.MODEL:
        return _match_named_scope(scope, (ctx.requested_model,), has_context=ctx.requested_model is not None)
    if scope_type == PolicyCardScopeType.MEMORY:
        if not ctx.memory_write_intent:
            return False, "SKIPPED_CONTEXT_MISSING"
        return True, "APPLICABLE_BY_SCOPE"
    if scope_type == PolicyCardScopeType.PROMPT:
        return _match_named_scope(scope, ctx.prompt_source_types, has_context=bool(ctx.prompt_source_types))
    if scope_type == PolicyCardScopeType.SANDBOX:
        if not _sandbox_context_signal(ctx):
            return False, "SKIPPED_CONTEXT_MISSING"
        return True, "APPLICABLE_BY_SCOPE"
    if scope_type == PolicyCardScopeType.AGENT:
        return _match_named_scope(scope, (ctx.agent_id,), has_context=ctx.agent_id is not None)
    metadata = dict(ctx.metadata)
    if scope_type == PolicyCardScopeType.WORKFLOW:
        workflow_id = metadata.get("workflow_id")
        return _match_named_scope(scope, (workflow_id if isinstance(workflow_id, str) else None,), has_context=isinstance(workflow_id, str))
    if scope_type == PolicyCardScopeType.BUSINESS:
        business_id = metadata.get("business_id")
        return _match_named_scope(scope, (business_id if isinstance(business_id, str) else None,), has_context=isinstance(business_id, str))
    return False, "SKIPPED_SCOPE_MISMATCH"


def _match_named_scope(
    scope: PolicyCardScope,
    candidates: Sequence[str | None],
    *,
    has_context: bool,
) -> tuple[bool, str]:
    if not has_context:
        return False, "SKIPPED_CONTEXT_MISSING"
    targets = {candidate for candidate in candidates if candidate}
    if not scope.scope_id and not scope.applies_to:
        return True, "APPLICABLE_BY_SCOPE"
    if scope.scope_id and scope.scope_id in targets:
        return True, "APPLICABLE_BY_SCOPE"
    if set(scope.applies_to) & targets:
        return True, "APPLICABLE_BY_SCOPE"
    return False, "SKIPPED_SCOPE_MISMATCH"


def _tool_rule_matches_context(card: object, ctx: PolicyResolutionContext) -> bool:
    if not isinstance(card, ToolPermissionPolicyCard):
        return True
    if not (ctx.tool_name or ctx.tool_category):
        return False
    for rule in card.permission_rules:
        matcher = rule.matcher
        if matcher.match_mode == ToolMatchMode.EXACT and matcher.tool_name and ctx.tool_name:
            if matcher.tool_name == ctx.tool_name:
                return True
        elif matcher.match_mode == ToolMatchMode.CATEGORY and matcher.tool_category and ctx.tool_category:
            if matcher.tool_category.value == ctx.tool_category:
                return True
        elif matcher.match_mode == ToolMatchMode.PREFIX and matcher.tool_name and ctx.tool_name:
            if ctx.tool_name.startswith(matcher.tool_name):
                return True
        else:
            return True
    return False


def _explain_card_applicability(
    card: object,
    ctx: PolicyResolutionContext,
) -> PolicyCardApplicability:
    family = _card_family(card)
    card_id = _card_id(card)
    if not _family_has_context_signal(family, ctx):
        return PolicyCardApplicability(
            card_id=card_id,
            family=family,
            applicable=False,
            reason_codes=("SKIPPED_CONTEXT_MISSING",),
        )
    scope_ok, scope_reason = _scope_applicable(card, ctx)
    if not scope_ok:
        return PolicyCardApplicability(
            card_id=card_id,
            family=family,
            applicable=False,
            reason_codes=(scope_reason,),
        )
    if family == PolicyFamily.TOOL_PERMISSION and not _tool_rule_matches_context(card, ctx):
        return PolicyCardApplicability(
            card_id=card_id,
            family=family,
            applicable=False,
            reason_codes=("SKIPPED_CONTEXT_MISSING",),
        )
    return PolicyCardApplicability(
        card_id=card_id,
        family=family,
        applicable=True,
        reason_codes=("APPLICABLE_BY_FAMILY", scope_reason),
    )
