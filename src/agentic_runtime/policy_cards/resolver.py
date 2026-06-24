"""Custos v0 Policy Runtime Resolver — SHADOW MODE (P1.6.10).

The first step from policy vocabulary toward policy adjudication. The resolver
accepts a PolicyResolutionContext and an explicit list of policy cards, evaluates
each present policy family through a small adapter, aggregates the family
decisions with strictest-wins MVP logic, and produces a deterministic
ResolvedPolicySet describing what WOULD happen if enforcement were active.

Architectural law:
  - P1.6.10 interprets policy cards. It does NOT enforce them.
  - This resolver never blocks, mutates, or approves a real command.
  - It is decoupled from AgenticRuntime.submit(); shadow mode only.
  - "Entity proposes, runtime disposes" — P1.6.10 does not yet dispose; it
    teaches Custos how to judge before it is allowed to enforce.
"""
from __future__ import annotations

import hashlib
from dataclasses import replace
from typing import Callable, Sequence

from .data_residency import (
    DataResidencyPolicyCard,
    DataResidencyZone,
    compute_data_residency_policy_card_hash,
)
from .errors import (
    PolicyResolutionAdapterError,
    PolicyResolutionValidationError,
)
from .human_oversight import (
    HumanOversightLevel,
    HumanOversightPolicyCard,
    HumanOversightTrigger,
    compute_human_oversight_policy_card_hash,
)
from .memory_write import (
    MemoryWriteDecision,
    MemoryWritePolicyCard,
    compute_memory_write_policy_card_hash,
)
from .models import PolicyCard
from .prompt_policy import (
    PromptInjectionRisk,
    PromptPolicyCard,
    PromptPolicyDecision,
    compute_prompt_policy_card_hash,
)
from .resolution_context import EnforcementMode, PolicyResolutionContext
from .resolution_result import (
    FamilyDecision,
    PolicyFamily,
    PolicyFamilyDecision,
    ResolvedPolicySet,
    ShadowAction,
    decision_rank,
    decision_to_shadow_action,
)
from .conflict_algebra import resolve_policy_conflicts_strictest_wins
from .resolution_trace import (
    PolicyResolutionTraceEvent,
    build_policy_resolution_trace_event,
    build_policy_resolution_trace_envelope,
)
from .risk_tiers import (
    OversightLevel,
    ReversibilityLevel,
    RiskTier,
    RiskTierPolicyCard,
    compute_risk_tier_policy_card_hash,
)
from .sandbox import (
    CommandClass,
    EgressPolicy,
    FilesystemScope,
    SandboxBackend,
    SandboxPolicyCard,
    SandboxPolicyDecisionInput,
    compute_sandbox_policy_card_hash,
    evaluate_sandbox_policy_decision,
)
from .tool_permissions import (
    ToolMatchMode,
    ToolPermissionDecision,
    ToolPermissionPolicyCard,
)
from .tool_permissions import (
    compute_tool_permission_policy_card_hash,
)


# ---------------------------------------------------------------------------
# Static helper sets
# ---------------------------------------------------------------------------

_RISK_RANK: dict[str, int] = {f"R{i}": i for i in range(7)}

_SENSITIVE_DATA_CLASSES: frozenset[str] = frozenset({
    "credentials", "secret", "sensitive_personal_data", "personal_data",
    "operator_private", "financial", "identity_record", "memory_record",
    "trace_record", "policy_record",
})

_UNTRUSTED_PROMPT_TRUST_LEVELS: frozenset[str] = frozenset({
    "external_untrusted", "tool_output_untrusted", "unknown_untrusted",
    "retrieved_context",
})

_UNTRUSTED_PROMPT_SOURCES: frozenset[str] = frozenset({
    "web_content", "email_content", "unknown", "tool_output",
    "external_api_content", "file_content", "code_content",
    "retrieved_document", "retrieved_memory",
})

_EXTERNAL_EGRESS_VALUES: frozenset[str] = frozenset({
    "any_egress", "allowlist_only", "private_network_only",
})


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _card_id(card: object) -> str:
    pc = getattr(card, "policy_card", None)
    if isinstance(pc, PolicyCard):
        return pc.identity.card_id
    return "<unknown>"


def _safe_hash(fn: Callable[[object], str], card: object) -> str | None:
    try:
        return fn(card)
    except Exception:
        return None


def _family_decision(
    family: PolicyFamily,
    decision: FamilyDecision,
    reason_codes: Sequence[str] = (),
    warnings: Sequence[str] = (),
    violations: Sequence[str] = (),
    approval_requirements: Sequence[str] = (),
    applicable_card_ids: Sequence[str] = (),
    source_hashes: Sequence[str] = (),
) -> PolicyFamilyDecision:
    return PolicyFamilyDecision(
        family=family,
        decision=decision,
        effective_shadow_action=decision_to_shadow_action(decision),
        reason_codes=tuple(reason_codes),
        warnings=tuple(warnings),
        violations=tuple(violations),
        approval_requirements=tuple(approval_requirements),
        applicable_card_ids=tuple(applicable_card_ids),
        source_hashes=tuple(h for h in source_hashes if h is not None),
    )


def _stricter(a: FamilyDecision, b: FamilyDecision) -> FamilyDecision:
    return a if decision_rank(a) >= decision_rank(b) else b


# ---------------------------------------------------------------------------
# Family adapters
# ---------------------------------------------------------------------------


def evaluate_risk_tier_policy(
    ctx: PolicyResolutionContext,
    cards: Sequence[RiskTierPolicyCard],
) -> PolicyFamilyDecision:
    family = PolicyFamily.RISK_TIER
    card_ids = sorted(_card_id(c) for c in cards)
    hashes = [_safe_hash(compute_risk_tier_policy_card_hash, c) for c in cards]
    reasons: list[str] = []
    warnings: list[str] = []
    violations: list[str] = []
    approvals: list[str] = []

    if ctx.risk_tier is None:
        return _family_decision(
            family, FamilyDecision.WARN, ["RISK_TIER_UNKNOWN"],
            warnings=["no risk tier specified in context"],
            applicable_card_ids=card_ids, source_hashes=hashes,
        )

    try:
        tier = RiskTier(ctx.risk_tier)
    except ValueError:
        return _family_decision(
            family, FamilyDecision.REQUIRE_APPROVAL, ["RISK_TIER_UNRECOGNIZED"],
            applicable_card_ids=card_ids, source_hashes=hashes,
        )

    definition = None
    for c in sorted(cards, key=_card_id):
        for d in c.tiers:
            if d.tier == tier:
                definition = d
                break
        if definition is not None:
            break

    decision = FamilyDecision.ALLOW
    if definition is None:
        decision = FamilyDecision.REQUIRE_APPROVAL
        reasons.append("RISK_TIER_NOT_DEFINED")
    elif (
        definition.oversight == OversightLevel.DENIED
        or definition.reversibility == ReversibilityLevel.DENIED
    ):
        decision = FamilyDecision.DENY
        reasons.append("RISK_TIER_DENIED")
        violations.append(f"risk tier {tier.value} is denied by policy")
    elif definition.default_requires_explicit_confirmation:
        decision = FamilyDecision.REQUIRE_APPROVAL
        reasons.append("RISK_TIER_EXPLICIT_CONFIRMATION_REQUIRED")
        approvals.append("explicit_confirmation_required")
    elif definition.default_requires_approval:
        decision = FamilyDecision.REQUIRE_APPROVAL
        reasons.append("RISK_TIER_APPROVAL_REQUIRED")
        approvals.append("approval_required")
    elif definition.default_requires_evidence:
        decision = FamilyDecision.WARN
        reasons.append("RISK_TIER_EVIDENCE_EXPECTED")
    else:
        decision = FamilyDecision.ALLOW
        reasons.append("RISK_TIER_ALLOWED")

    # Ceiling check from inner policy card risk binding (strictest ceiling wins)
    ceiling_idx: int | None = None
    for c in cards:
        rb = c.policy_card.risk_binding
        if rb is not None and rb.risk_ceiling in _RISK_RANK:
            idx = _RISK_RANK[rb.risk_ceiling]
            ceiling_idx = idx if ceiling_idx is None else min(ceiling_idx, idx)
    if ceiling_idx is not None and _RISK_RANK[tier.value] > ceiling_idx:
        decision = _stricter(decision, FamilyDecision.DENY)
        reasons.append("RISK_ABOVE_CEILING")
        violations.append(f"risk tier {tier.value} exceeds card ceiling")

    return _family_decision(
        family, decision, reasons, warnings, violations, approvals,
        card_ids, hashes,
    )


def evaluate_human_oversight_policy(
    ctx: PolicyResolutionContext,
    cards: Sequence[HumanOversightPolicyCard],
) -> PolicyFamilyDecision:
    family = PolicyFamily.HUMAN_OVERSIGHT
    card_ids = sorted(_card_id(c) for c in cards)
    hashes = [_safe_hash(compute_human_oversight_policy_card_hash, c) for c in cards]
    reasons: list[str] = []
    approvals: list[str] = []
    violations: list[str] = []

    if ctx.risk_tier is None:
        return _family_decision(
            family, FamilyDecision.WARN, ["OVERSIGHT_RISK_UNKNOWN"],
            warnings=["cannot map oversight without a risk tier"],
            applicable_card_ids=card_ids, source_hashes=hashes,
        )
    try:
        tier = RiskTier(ctx.risk_tier)
    except ValueError:
        return _family_decision(
            family, FamilyDecision.REQUIRE_APPROVAL, ["OVERSIGHT_RISK_UNRECOGNIZED"],
            applicable_card_ids=card_ids, source_hashes=hashes,
        )

    mapping = None
    for c in sorted(cards, key=_card_id):
        for m in c.risk_tier_mappings:
            if m.risk_tier == tier:
                mapping = m
                break
        if mapping is not None:
            break

    decision = FamilyDecision.ALLOW
    if mapping is None:
        decision = FamilyDecision.REQUIRE_APPROVAL
        reasons.append("OVERSIGHT_NO_MAPPING")
        approvals.append("approval_required")
    else:
        level = mapping.oversight_level
        if level == HumanOversightLevel.DENY:
            decision = FamilyDecision.DENY
            reasons.append("OVERSIGHT_DENY")
            violations.append(f"risk tier {tier.value} denied by oversight policy")
        elif level in (
            HumanOversightLevel.APPROVAL_REQUIRED,
            HumanOversightLevel.EXPLICIT_CONFIRMATION_REQUIRED,
            HumanOversightLevel.DUAL_REVIEW_REQUIRED,
            HumanOversightLevel.GOVERNANCE_BOARD_REQUIRED,
        ):
            decision = FamilyDecision.REQUIRE_APPROVAL
            reasons.append("OVERSIGHT_APPROVAL_REQUIRED")
            approvals.append(level.value)
        elif level in (
            HumanOversightLevel.REVIEW_RECOMMENDED,
            HumanOversightLevel.NOTIFY_ONLY,
        ):
            decision = FamilyDecision.WARN
            reasons.append("OVERSIGHT_REVIEW_RECOMMENDED")
        else:
            decision = FamilyDecision.ALLOW
            reasons.append("OVERSIGHT_NONE")

    # Minimal escalation: external egress trigger
    if ctx.requires_network or bool(ctx.requested_network_targets):
        for c in cards:
            for rule in c.escalation_rules:
                if rule.trigger == HumanOversightTrigger.EXTERNAL_EGRESS:
                    decision = _stricter(decision, FamilyDecision.REQUIRE_APPROVAL)
                    reasons.append("OVERSIGHT_EXTERNAL_EGRESS_ESCALATION")
                    approvals.append("approval_required")
                    break

    return _family_decision(
        family, decision, reasons, [], violations, approvals, card_ids, hashes,
    )


def evaluate_data_residency_policy(
    ctx: PolicyResolutionContext,
    cards: Sequence[DataResidencyPolicyCard],
) -> PolicyFamilyDecision:
    family = PolicyFamily.DATA_RESIDENCY
    card_ids = sorted(_card_id(c) for c in cards)
    hashes = [_safe_hash(compute_data_residency_policy_card_hash, c) for c in cards]

    if not ctx.data_classes:
        return _family_decision(
            family, FamilyDecision.NOT_APPLICABLE, ["DATA_RESIDENCY_NO_DATA_CLASSES"],
            applicable_card_ids=card_ids, source_hashes=hashes,
        )

    external_intent = (
        ctx.requires_network
        or bool(ctx.requested_network_targets)
        or (ctx.requested_egress in _EXTERNAL_EGRESS_VALUES)
        or bool(ctx.requested_model and "external" in ctx.requested_model.lower())
    )

    reasons: list[str] = []
    violations: list[str] = []
    approvals: list[str] = []
    overall = FamilyDecision.ALLOW

    for dc in sorted(set(ctx.data_classes)):
        rule = None
        for c in sorted(cards, key=_card_id):
            for r in c.residency_rules:
                if r.data_class.value == dc:
                    rule = r
                    break
            if rule is not None:
                break

        if rule is not None:
            if rule.residency_zone == DataResidencyZone.FORBIDDEN:
                overall = _stricter(overall, FamilyDecision.DENY)
                reasons.append("DATA_RESIDENCY_FORBIDDEN")
                violations.append(f"data class {dc} is forbidden")
            elif external_intent and not rule.egress_rule.egress_allowed:
                overall = _stricter(overall, FamilyDecision.DENY)
                reasons.append("DATA_EGRESS_DENIED")
                violations.append(f"data class {dc} cannot egress externally")
            elif external_intent and rule.residency_zone in (
                DataResidencyZone.LOCAL_ONLY, DataResidencyZone.LOCAL_PRIVATE,
            ):
                overall = _stricter(overall, FamilyDecision.DENY)
                reasons.append("DATA_LOCAL_ONLY_EXTERNAL")
                violations.append(f"local-only data class {dc} requested externally")
            elif external_intent and rule.egress_rule.requires_operator_approval:
                overall = _stricter(overall, FamilyDecision.REQUIRE_APPROVAL)
                reasons.append("DATA_EGRESS_APPROVAL_REQUIRED")
                approvals.append("operator_approval")
            else:
                reasons.append("DATA_RESIDENCY_ALLOWED")
        else:
            if dc in _SENSITIVE_DATA_CLASSES:
                overall = _stricter(overall, FamilyDecision.REQUIRE_APPROVAL)
                reasons.append("DATA_RESIDENCY_UNKNOWN_SENSITIVE")
                approvals.append("operator_approval")
            else:
                overall = _stricter(overall, FamilyDecision.WARN)
                reasons.append("DATA_RESIDENCY_UNKNOWN")

    return _family_decision(
        family, overall, reasons, [], violations, approvals, card_ids, hashes,
    )


def evaluate_tool_permission_policy(
    ctx: PolicyResolutionContext,
    cards: Sequence[ToolPermissionPolicyCard],
) -> PolicyFamilyDecision:
    family = PolicyFamily.TOOL_PERMISSION
    card_ids = sorted(_card_id(c) for c in cards)
    hashes = [_safe_hash(compute_tool_permission_policy_card_hash, c) for c in cards]

    if not ctx.tool_name and not ctx.tool_category:
        return _family_decision(
            family, FamilyDecision.NOT_APPLICABLE, ["TOOL_NO_TOOL_CONTEXT"],
            applicable_card_ids=card_ids, source_hashes=hashes,
        )

    matched = []
    for c in sorted(cards, key=_card_id):
        for rule in c.permission_rules:
            m = rule.matcher
            if (
                m.match_mode == ToolMatchMode.EXACT
                and m.tool_name and ctx.tool_name and m.tool_name == ctx.tool_name
            ):
                matched.append(rule)
            elif (
                m.match_mode == ToolMatchMode.CATEGORY
                and m.tool_category and ctx.tool_category
                and m.tool_category.value == ctx.tool_category
            ):
                matched.append(rule)
            elif (
                m.match_mode == ToolMatchMode.PREFIX
                and m.tool_name and ctx.tool_name
                and ctx.tool_name.startswith(m.tool_name)
            ):
                matched.append(rule)

    reasons: list[str] = []
    violations: list[str] = []
    approvals: list[str] = []

    if not matched:
        return _family_decision(
            family, FamilyDecision.REQUIRE_APPROVAL, ["TOOL_NOT_MATCHED"],
            warnings=["no tool permission rule matched; conservative default"],
            approval_requirements=["approval_required"],
            applicable_card_ids=card_ids, source_hashes=hashes,
        )

    overall = FamilyDecision.ALLOW
    for rule in matched:
        d = rule.decision
        if d == ToolPermissionDecision.DENY:
            overall = _stricter(overall, FamilyDecision.DENY)
            reasons.append("TOOL_DENIED")
            violations.append("tool denied by policy")
        elif d in (
            ToolPermissionDecision.APPROVAL_REQUIRED,
            ToolPermissionDecision.EXPLICIT_CONFIRMATION_REQUIRED,
        ):
            overall = _stricter(overall, FamilyDecision.REQUIRE_APPROVAL)
            reasons.append("TOOL_APPROVAL_REQUIRED")
            approvals.append(d.value)
        elif d in (
            ToolPermissionDecision.SANDBOX_REQUIRED,
            ToolPermissionDecision.READ_ONLY,
            ToolPermissionDecision.LOCAL_ONLY,
            ToolPermissionDecision.CONDITIONAL,
        ):
            overall = _stricter(overall, FamilyDecision.WARN)
            reasons.append("TOOL_CONSTRAINED")
        else:
            reasons.append("TOOL_ALLOWED")

    return _family_decision(
        family, overall, reasons, [], violations, approvals, card_ids, hashes,
    )


def evaluate_memory_write_policy(
    ctx: PolicyResolutionContext,
    cards: Sequence[MemoryWritePolicyCard],
) -> PolicyFamilyDecision:
    family = PolicyFamily.MEMORY_WRITE
    card_ids = sorted(_card_id(c) for c in cards)
    hashes = [_safe_hash(compute_memory_write_policy_card_hash, c) for c in cards]

    if not ctx.memory_write_intent:
        return _family_decision(
            family, FamilyDecision.NOT_APPLICABLE, ["MEMORY_NO_WRITE_INTENT"],
            applicable_card_ids=card_ids, source_hashes=hashes,
        )

    decisions: set[MemoryWriteDecision] = set()
    default_forbidden = False
    default_deny = False
    for c in cards:
        if c.default_decision == MemoryWriteDecision.FORBIDDEN:
            default_forbidden = True
        if c.default_decision == MemoryWriteDecision.DENY:
            default_deny = True
        for r in c.memory_rules:
            decisions.add(r.decision)

    reasons: list[str] = []
    violations: list[str] = []
    approvals: list[str] = []

    if default_forbidden:
        decision = FamilyDecision.DENY
        reasons.append("MEMORY_WRITE_FORBIDDEN")
        violations.append("memory write forbidden by default")
    elif (
        MemoryWriteDecision.REQUIRES_REVIEW in decisions
        or MemoryWriteDecision.REQUIRES_CONFIRMATION in decisions
    ):
        decision = FamilyDecision.REQUIRE_APPROVAL
        reasons.append("MEMORY_WRITE_REVIEW_REQUIRED")
        approvals.append("memory_write_review")
    elif (
        MemoryWriteDecision.REQUIRES_EVIDENCE in decisions
        or MemoryWriteDecision.REQUIRES_PROVENANCE in decisions
        or MemoryWriteDecision.CANDIDATE_ONLY in decisions
    ):
        decision = FamilyDecision.WARN
        reasons.append("MEMORY_WRITE_NEEDS_EVIDENCE")
    elif default_deny and MemoryWriteDecision.ALLOW not in decisions:
        decision = FamilyDecision.REQUIRE_APPROVAL
        reasons.append("MEMORY_WRITE_DEFAULT_DENY")
        approvals.append("memory_write_review")
    else:
        decision = FamilyDecision.WARN
        reasons.append("MEMORY_WRITE_NEEDS_EVIDENCE")

    return _family_decision(
        family, decision, reasons, [], violations, approvals, card_ids, hashes,
    )


def evaluate_prompt_policy(
    ctx: PolicyResolutionContext,
    cards: Sequence[PromptPolicyCard],
) -> PolicyFamilyDecision:
    family = PolicyFamily.PROMPT
    card_ids = sorted(_card_id(c) for c in cards)
    hashes = [_safe_hash(compute_prompt_policy_card_hash, c) for c in cards]

    if not ctx.prompt_source_types:
        return _family_decision(
            family, FamilyDecision.NOT_APPLICABLE, ["PROMPT_NO_SOURCES"],
            applicable_card_ids=card_ids, source_hashes=hashes,
        )

    reasons: list[str] = []
    warnings: list[str] = []
    violations: list[str] = []
    approvals: list[str] = []
    overall = FamilyDecision.ALLOW

    for src in sorted(set(ctx.prompt_source_types)):
        rule = None
        for c in sorted(cards, key=_card_id):
            for r in c.prompt_rules:
                if r.source_type.value == src:
                    rule = r
                    break
            if rule is not None:
                break

        if rule is not None:
            d = rule.decision
            if d in (PromptPolicyDecision.DENY, PromptPolicyDecision.FORBIDDEN):
                overall = _stricter(overall, FamilyDecision.DENY)
                reasons.append("PROMPT_DENIED")
                violations.append(f"prompt source {src} denied")
            elif (
                rule.allowed_as_instruction
                and rule.trust_level.value in _UNTRUSTED_PROMPT_TRUST_LEVELS
            ):
                overall = _stricter(overall, FamilyDecision.DENY)
                reasons.append("PROMPT_UNTRUSTED_INSTRUCTION")
                violations.append(f"untrusted source {src} claims instruction authority")
            elif rule.injection_risk in (
                PromptInjectionRisk.HIGH, PromptInjectionRisk.CRITICAL,
            ):
                overall = _stricter(overall, FamilyDecision.REQUIRE_APPROVAL)
                reasons.append("PROMPT_HIGH_INJECTION_RISK")
                approvals.append("prompt_review")
            elif d == PromptPolicyDecision.REQUIRES_REVIEW:
                overall = _stricter(overall, FamilyDecision.REQUIRE_APPROVAL)
                reasons.append("PROMPT_REVIEW_REQUIRED")
                approvals.append("prompt_review")
            elif rule.injection_risk == PromptInjectionRisk.MEDIUM:
                overall = _stricter(overall, FamilyDecision.WARN)
                reasons.append("PROMPT_MEDIUM_INJECTION_RISK")
            elif d in (
                PromptPolicyDecision.CONTEXT_ONLY,
                PromptPolicyDecision.QUOTE_ONLY,
                PromptPolicyDecision.REDACTION_REQUIRED,
                PromptPolicyDecision.REQUIRES_PROVENANCE,
                PromptPolicyDecision.REQUIRES_SANDBOX,
                PromptPolicyDecision.LOCAL_ONLY,
            ):
                overall = _stricter(overall, FamilyDecision.WARN)
                reasons.append("PROMPT_CONTEXT_CONSTRAINED")
            else:
                reasons.append("PROMPT_ALLOWED")
        else:
            if src in _UNTRUSTED_PROMPT_SOURCES:
                overall = _stricter(overall, FamilyDecision.REQUIRE_APPROVAL)
                reasons.append("PROMPT_SOURCE_UNKNOWN_UNTRUSTED")
                approvals.append("prompt_review")
            else:
                overall = _stricter(overall, FamilyDecision.WARN)
                reasons.append("PROMPT_SOURCE_UNKNOWN")
                warnings.append(f"prompt source {src} not modelled")

    return _family_decision(
        family, overall, reasons, warnings, violations, approvals, card_ids, hashes,
    )


_BACKEND_BY_VALUE = {b.value: b for b in SandboxBackend}
_FS_BY_VALUE = {s.value: s for s in FilesystemScope}
_EGRESS_BY_VALUE = {e.value: e for e in EgressPolicy}
_COMMAND_BY_VALUE = {c.value: c for c in CommandClass}


def _build_sandbox_input(ctx: PolicyResolutionContext) -> SandboxPolicyDecisionInput:
    command_class = None
    if ctx.command_class is not None:
        command_class = _COMMAND_BY_VALUE.get(ctx.command_class)
    if command_class is None:
        if ctx.installs_packages:
            command_class = CommandClass.PACKAGE_INSTALL
        elif ctx.runs_shell:
            command_class = CommandClass.SHELL_COMMAND
        elif ctx.requires_network or ctx.requested_network_targets:
            command_class = CommandClass.NETWORK_COMMAND
        elif ctx.touches_secrets:
            command_class = CommandClass.SECRET_TOUCHING_COMMAND
        elif ctx.writes_files:
            command_class = CommandClass.WRITE_COMMAND

    risk_tier = None
    if ctx.risk_tier is not None:
        try:
            risk_tier = RiskTier(ctx.risk_tier)
        except ValueError:
            risk_tier = None

    return SandboxPolicyDecisionInput(
        command_class=command_class,
        risk_tier=risk_tier,
        requested_backend=_BACKEND_BY_VALUE.get(ctx.requested_sandbox_backend or ""),
        requested_filesystem_scope=_FS_BY_VALUE.get(ctx.requested_filesystem_scope or ""),
        requested_egress=_EGRESS_BY_VALUE.get(ctx.requested_egress or ""),
        touches_secrets=ctx.touches_secrets,
        writes_files=ctx.writes_files,
        runs_shell=ctx.runs_shell,
        installs_packages=ctx.installs_packages,
        requested_paths=ctx.requested_paths,
        requested_network_targets=ctx.requested_network_targets,
    )


def _sandbox_is_applicable(ctx: PolicyResolutionContext) -> bool:
    return any((
        ctx.command_class is not None,
        ctx.requested_sandbox_backend is not None,
        ctx.requested_filesystem_scope is not None,
        ctx.requested_egress is not None,
        ctx.runs_shell, ctx.writes_files, ctx.installs_packages,
        ctx.requires_network, ctx.touches_secrets,
        bool(ctx.requested_paths), bool(ctx.requested_network_targets),
    ))


def evaluate_sandbox_policy(
    ctx: PolicyResolutionContext,
    cards: Sequence[SandboxPolicyCard],
) -> PolicyFamilyDecision:
    family = PolicyFamily.SANDBOX
    card_ids = sorted(_card_id(c) for c in cards)
    hashes = [_safe_hash(compute_sandbox_policy_card_hash, c) for c in cards]

    if not _sandbox_is_applicable(ctx):
        return _family_decision(
            family, FamilyDecision.NOT_APPLICABLE, ["SANDBOX_NO_EXECUTION_INTENT"],
            applicable_card_ids=card_ids, source_hashes=hashes,
        )

    inp = _build_sandbox_input(ctx)
    reasons: list[str] = []
    warnings: list[str] = []
    violations: list[str] = []
    approvals: list[str] = []
    overall = FamilyDecision.ALLOW

    for c in sorted(cards, key=_card_id):
        try:
            decision = evaluate_sandbox_policy_decision(c, inp)
        except Exception as exc:  # pragma: no cover - defensive
            raise PolicyResolutionAdapterError(
                f"sandbox adapter failed for card {_card_id(c)}: {exc}"
            ) from exc

        if decision.allowed and not decision.approval_required:
            fd = FamilyDecision.ALLOW
        elif decision.allowed and decision.approval_required:
            fd = FamilyDecision.REQUIRE_APPROVAL
            approvals.append("sandbox_approval")
        elif not decision.allowed and decision.violations:
            fd = FamilyDecision.DENY
        else:
            fd = FamilyDecision.REQUIRE_APPROVAL
            approvals.append("sandbox_approval")
        overall = _stricter(overall, fd)

        reasons.extend(decision.reason_codes)
        for v in decision.violations:
            violations.append(v.code)
        for w in decision.warnings:
            warnings.append(w.code)

    if not reasons:
        reasons.append("SANDBOX_EVALUATED")

    return _family_decision(
        family, overall, reasons, warnings, violations, approvals, card_ids, hashes,
    )


# ---------------------------------------------------------------------------
# Adapter registry & grouping
# ---------------------------------------------------------------------------

_CARD_TYPE_BY_FAMILY = {
    PolicyFamily.RISK_TIER: RiskTierPolicyCard,
    PolicyFamily.HUMAN_OVERSIGHT: HumanOversightPolicyCard,
    PolicyFamily.DATA_RESIDENCY: DataResidencyPolicyCard,
    PolicyFamily.TOOL_PERMISSION: ToolPermissionPolicyCard,
    PolicyFamily.MEMORY_WRITE: MemoryWritePolicyCard,
    PolicyFamily.PROMPT: PromptPolicyCard,
    PolicyFamily.SANDBOX: SandboxPolicyCard,
}

_ADAPTERS: dict[PolicyFamily, Callable[..., PolicyFamilyDecision]] = {
    PolicyFamily.RISK_TIER: evaluate_risk_tier_policy,
    PolicyFamily.HUMAN_OVERSIGHT: evaluate_human_oversight_policy,
    PolicyFamily.DATA_RESIDENCY: evaluate_data_residency_policy,
    PolicyFamily.TOOL_PERMISSION: evaluate_tool_permission_policy,
    PolicyFamily.MEMORY_WRITE: evaluate_memory_write_policy,
    PolicyFamily.PROMPT: evaluate_prompt_policy,
    PolicyFamily.SANDBOX: evaluate_sandbox_policy,
}

# Deterministic family evaluation order.
_FAMILY_ORDER: tuple[PolicyFamily, ...] = (
    PolicyFamily.RISK_TIER,
    PolicyFamily.HUMAN_OVERSIGHT,
    PolicyFamily.DATA_RESIDENCY,
    PolicyFamily.TOOL_PERMISSION,
    PolicyFamily.MEMORY_WRITE,
    PolicyFamily.PROMPT,
    PolicyFamily.SANDBOX,
)


def _group_cards(
    cards: Sequence[object],
) -> dict[PolicyFamily, list[object]]:
    grouped: dict[PolicyFamily, list[object]] = {}
    seen_ids: set[str] = set()
    for card in cards:
        family = None
        for fam, card_type in _CARD_TYPE_BY_FAMILY.items():
            if isinstance(card, card_type):
                family = fam
                break
        if family is None:
            raise PolicyResolutionValidationError(
                f"unrecognized policy card object: {type(card).__name__}"
            )
        cid = _card_id(card)
        if cid in seen_ids:
            raise PolicyResolutionValidationError(
                f"duplicate policy card id '{cid}' creates ambiguous resolution"
            )
        seen_ids.add(cid)
        grouped.setdefault(family, []).append(card)
    return grouped


# ---------------------------------------------------------------------------
# Aggregation (strictest-wins MVP)
# ---------------------------------------------------------------------------


def aggregate_family_decisions(
    family_decisions: Sequence[PolicyFamilyDecision],
) -> tuple[FamilyDecision, ShadowAction, tuple[str, ...], tuple[str, ...],
           tuple[str, ...], tuple[str, ...]]:
    """Strictest-wins aggregation.

    DENY > REQUIRE_APPROVAL(=ERROR) > WARN > ALLOW > NOT_APPLICABLE.
    Returns (overall_decision, shadow_action, reason_codes, warnings,
    violations, approval_requirements).
    """
    applicable = [
        fd for fd in family_decisions
        if fd.decision != FamilyDecision.NOT_APPLICABLE
    ]

    reasons: set[str] = set()
    warnings: set[str] = set()
    violations: set[str] = set()
    approvals: set[str] = set()
    for fd in applicable:
        reasons.update(fd.reason_codes)
        warnings.update(fd.warnings)
        violations.update(fd.violations)
        approvals.update(fd.approval_requirements)

    if not applicable:
        overall = FamilyDecision.WARN
        reasons.add("NO_APPLICABLE_CARDS")
    else:
        has_deny = any(fd.decision == FamilyDecision.DENY for fd in applicable)
        has_error = any(fd.decision == FamilyDecision.ERROR for fd in applicable)
        has_approval = any(
            fd.decision == FamilyDecision.REQUIRE_APPROVAL for fd in applicable
        )
        has_warn = any(fd.decision == FamilyDecision.WARN for fd in applicable)
        if has_deny:
            overall = FamilyDecision.DENY
        elif has_error or has_approval:
            overall = FamilyDecision.REQUIRE_APPROVAL
            if has_error:
                reasons.add("ADAPTER_ERROR_CONSERVATIVE")
        elif has_warn:
            overall = FamilyDecision.WARN
        else:
            overall = FamilyDecision.ALLOW

    shadow = decision_to_shadow_action(overall)
    return (
        overall, shadow,
        tuple(sorted(reasons)), tuple(sorted(warnings)),
        tuple(sorted(violations)), tuple(sorted(approvals)),
    )


# ---------------------------------------------------------------------------
# Resolution id
# ---------------------------------------------------------------------------


def _resolution_id(context_hash: str, source_hashes: Sequence[str]) -> str:
    payload = context_hash + "|" + "|".join(sorted(source_hashes))
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return f"rps-{digest[:32]}"


# ---------------------------------------------------------------------------
# Public resolve API
# ---------------------------------------------------------------------------


def resolve_policy_cards(
    context: PolicyResolutionContext,
    cards: Sequence[object],
    mode: EnforcementMode = EnforcementMode.SHADOW,
) -> ResolvedPolicySet:
    """Resolve policy cards against a context in SHADOW mode.

    P1.6.10 only supports SHADOW. Any other mode is rejected fail-closed; no
    enforcement is ever performed.
    """
    if mode != EnforcementMode.SHADOW:
        raise PolicyResolutionValidationError(
            f"enforcement mode '{getattr(mode, 'value', mode)}' is not supported in "
            "P1.6.10 — only SHADOW mode is available"
        )
    if not isinstance(context, PolicyResolutionContext):
        raise PolicyResolutionValidationError(
            "context must be a PolicyResolutionContext"
        )
    if cards is None:
        raise PolicyResolutionValidationError("cards must be a sequence, not None")

    grouped = _group_cards(cards)

    family_decisions: list[PolicyFamilyDecision] = []
    for family in _FAMILY_ORDER:
        fcards = grouped.get(family)
        if not fcards:
            continue
        adapter = _ADAPTERS[family]
        try:
            fd = adapter(context, fcards)
        except Exception as exc:
            fd = PolicyFamilyDecision(
                family=family,
                decision=FamilyDecision.ERROR,
                effective_shadow_action=ShadowAction.WOULD_ERROR,
                reason_codes=("ADAPTER_ERROR",),
                violations=(f"{type(exc).__name__}: {exc}",),
                applicable_card_ids=tuple(sorted(_card_id(c) for c in fcards)),
            )
        family_decisions.append(fd)

    overall, shadow, reasons, warnings, violations, approvals = (
        aggregate_family_decisions(tuple(family_decisions))
    )

    reason_list = list(reasons)
    if not cards:
        reason_list.append("NO_CARDS_PROVIDED")

    applicable_ids = sorted({
        cid
        for fd in family_decisions
        if fd.decision != FamilyDecision.NOT_APPLICABLE
        for cid in fd.applicable_card_ids
    })
    source_hashes = sorted({
        h for fd in family_decisions for h in fd.source_hashes
    })

    context_hash = context.context_hash
    resolution = ResolvedPolicySet(
        resolution_id=_resolution_id(context_hash, source_hashes),
        context_hash=context_hash,
        enforcement_mode=EnforcementMode.SHADOW,
        overall_decision=overall,
        effective_shadow_action=shadow,
        family_decisions=tuple(family_decisions),
        reason_codes=tuple(sorted(reason_list)),
        warnings=warnings,
        violations=violations,
        approval_requirements=approvals,
        applicable_card_ids=tuple(applicable_ids),
        source_hashes=tuple(source_hashes),
    )

    # P1.6.13 — Attach conflict algebra metadata (shadow-only, no enforcement)
    try:
        resolution = _attach_conflict_metadata(resolution, family_decisions, context)
    except Exception:  # pragma: no cover - defensive
        pass

    # P1.6.14 — Attach trace-compatible metadata (shadow-only, no enforcement)
    try:
        resolution = _attach_trace_metadata(resolution)
    except Exception:  # pragma: no cover - defensive
        pass

    return resolution.with_canonical_hash()


def _attach_conflict_metadata(
    resolution: ResolvedPolicySet,
    family_decisions: list[PolicyFamilyDecision],
    context: PolicyResolutionContext,
) -> ResolvedPolicySet:
    """Attach P1.6.13 conflict algebra metadata to a ResolvedPolicySet."""
    if not family_decisions:
        return resolution
    cr = resolve_policy_conflicts_strictest_wins(
        family_decisions=family_decisions,
        context=context,
    )
    return replace(
        resolution,
        conflict_resolution=cr.to_canonical_dict(),
        conflict_hash=cr.compute_hash(),
    )


def _attach_trace_metadata(resolution: ResolvedPolicySet) -> ResolvedPolicySet:
    """Attach P1.6.14 trace-compatible metadata to a ResolvedPolicySet."""
    conflict_codes: tuple[str, ...] = ()
    strictest_rank: str = ""

    if resolution.conflict_resolution is not None:
        conflict_codes = tuple(
            resolution.conflict_resolution.get("conflict_codes", ()) or ()
        )
        strictest_rank = str(
            resolution.conflict_resolution.get("winning_rank", "")
        )

    source_families = tuple(sorted({
        fd.family.value for fd in resolution.family_decisions
    }))

    trace_event = build_policy_resolution_trace_event(
        registry_hash=resolution.source_hashes[0] if resolution.source_hashes else "",
        context_hash=resolution.context_hash,
        resolution_hash=resolution.canonical_hash or "",
        conflict_hash=resolution.conflict_hash or "",
        effective_shadow_action=resolution.effective_shadow_action.value,
        strictest_decision_rank=strictest_rank,
        source_family_ids=source_families,
        source_card_ids=resolution.applicable_card_ids,
        reason_codes=resolution.reason_codes,
        conflict_codes=conflict_codes,
    )

    return replace(
        resolution,
        resolution_trace=trace_event.to_canonical_dict(include_hash=True),
        resolution_trace_hash=trace_event.trace_hash,
        resolution_trace_id=trace_event.trace_id,
    )


def resolve_policy_cards_from_registry(
    context: PolicyResolutionContext,
    registry: object,
    mode: EnforcementMode = EnforcementMode.SHADOW,
) -> ResolvedPolicySet:
    """Resolve cards selected by a PolicyCardRegistry in SHADOW mode.

    P1.6.11 binds deterministic registry applicability to the existing Custos v0
    resolver. The registry supplies explicit applicable cards; the resolver still
    produces WOULD_* shadow outcomes only.
    """
    if not hasattr(registry, "get_applicable"):
        raise PolicyResolutionValidationError(
            "registry must provide get_applicable(context)"
        )
    applicable_cards = registry.get_applicable(context)
    return resolve_policy_cards(context, applicable_cards, mode)


class PolicyRuntimeResolver:
    """Custos v0 resolver facade. Shadow mode only in P1.6.10/P1.6.11."""

    def __init__(self, mode: EnforcementMode = EnforcementMode.SHADOW) -> None:
        if mode != EnforcementMode.SHADOW:
            raise PolicyResolutionValidationError(
                "PolicyRuntimeResolver only supports SHADOW mode in P1.6.10"
            )
        self.mode = mode

    def resolve(
        self,
        context: PolicyResolutionContext,
        cards: Sequence[object],
    ) -> ResolvedPolicySet:
        return resolve_policy_cards(context, cards, self.mode)

    def resolve_from_registry(
        self,
        context: PolicyResolutionContext,
        registry: object,
    ) -> ResolvedPolicySet:
        return resolve_policy_cards_from_registry(context, registry, self.mode)
