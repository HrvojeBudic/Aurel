"""Prompt Policy Card model (P1.6.8).

Defines prompt trust and prompt authority semantics for AurelCore policy cards.
Prompt policy cards declare which prompt source is trusted, which may act as
instruction, which may only be context/data, which may request tools, influence
memory writes, modify policy or identity, and which must be quoted, sandboxed,
provenance-bound or denied. They are declarative, deterministic, closed-world,
hash-ready, and strict deny-by-default.

Core Aurel law:
  Untrusted content may inform, but must never command.

Architectural law:
  - Prompt policy cards do not grant authority.
  - Prompt policy cards do not compile prompts.
  - Prompt policy cards do not enforce runtime instruction hierarchy yet.
  - Prompt policy cards do not implement a prompt injection / jailbreak detector.
  - Prompt policy cards do not modify identity/persona or policy.
  - Prompt policy cards do not write memory or request tools by themselves.
  - Prompt policy cards remain compatible with generic PolicyCard(kind="prompt").
  - Unknown prompt source defaults to untrusted/deny posture.
  - External content cannot become instruction authority.
  - Tool output is data/context, not command.
  - Retrieved memory is context, not automatic authority.
  - Prompt authority is never inferred from text content alone.
"""
from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping as MappingABC
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping, TypeVar

from .errors import (
    PolicyCardError,
    PromptPolicyCardError,
    PromptPolicyCardUnknownFieldError,
    PromptPolicyCardUnsafeFieldError,
    PromptPolicyCardValidationError,
)
from .models import (
    PolicyCard,
    PolicyCardIdentity,
    PolicyCardKind,
    PolicyCardScope,
    PolicyCardScopeType,
    PolicyCardStatus,
)
from .serialization import policy_card_to_canonical_dict
from .validation import load_policy_card_from_dict


# ---------------------------------------------------------------------------
# Enums (prompt policy vocabulary)
# ---------------------------------------------------------------------------


class PromptSourceType(str, Enum):
    SYSTEM_PROMPT = "system_prompt"
    DEVELOPER_PROMPT = "developer_prompt"
    OPERATOR_PROMPT = "operator_prompt"
    TASK_PROMPT = "task_prompt"
    AGENT_PROMPT = "agent_prompt"
    TOOL_OUTPUT = "tool_output"
    RETRIEVED_MEMORY = "retrieved_memory"
    RETRIEVED_DOCUMENT = "retrieved_document"
    WEB_CONTENT = "web_content"
    EMAIL_CONTENT = "email_content"
    FILE_CONTENT = "file_content"
    CODE_CONTENT = "code_content"
    EXTERNAL_API_CONTENT = "external_api_content"
    EVALUATION_PROMPT = "evaluation_prompt"
    CRITIC_PROMPT = "critic_prompt"
    PLANNER_PROMPT = "planner_prompt"
    REFLECTION_PROMPT = "reflection_prompt"
    GENERATED_PROMPT = "generated_prompt"
    UNKNOWN = "unknown"


class PromptTrustLevel(str, Enum):
    TRUSTED_SYSTEM = "trusted_system"
    TRUSTED_DEVELOPER = "trusted_developer"
    OPERATOR_AUTHORIZED = "operator_authorized"
    REPO_CANONICAL = "repo_canonical"
    VERIFIED_TEMPLATE = "verified_template"
    INTERNAL_GENERATED = "internal_generated"
    RETRIEVED_CONTEXT = "retrieved_context"
    EXTERNAL_UNTRUSTED = "external_untrusted"
    TOOL_OUTPUT_UNTRUSTED = "tool_output_untrusted"
    UNKNOWN_UNTRUSTED = "unknown_untrusted"


class PromptRole(str, Enum):
    INSTRUCTION = "instruction"
    CONTEXT = "context"
    DATA = "data"
    EXAMPLE = "example"
    CONSTRAINT = "constraint"
    OUTPUT_FORMAT = "output_format"
    TOOL_REQUEST = "tool_request"
    MEMORY_REQUEST = "memory_request"
    POLICY_REQUEST = "policy_request"
    IDENTITY_REQUEST = "identity_request"
    EVALUATION = "evaluation"
    REFLECTION = "reflection"
    PLANNING = "planning"
    CODE_GENERATION = "code_generation"
    BUSINESS_PROCESS = "business_process"
    UNKNOWN = "unknown"


class PromptPolicyDecision(str, Enum):
    ALLOW = "allow"
    DENY = "deny"
    CONTEXT_ONLY = "context_only"
    QUOTE_ONLY = "quote_only"
    REQUIRES_REVIEW = "requires_review"
    REQUIRES_PROVENANCE = "requires_provenance"
    REQUIRES_SANDBOX = "requires_sandbox"
    REDACTION_REQUIRED = "redaction_required"
    LOCAL_ONLY = "local_only"
    FORBIDDEN = "forbidden"


class PromptInjectionRisk(str, Enum):
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class PromptInjectionPattern(str, Enum):
    IGNORE_PREVIOUS_INSTRUCTIONS = "ignore_previous_instructions"
    REVEAL_SYSTEM_PROMPT = "reveal_system_prompt"
    BYPASS_POLICY = "bypass_policy"
    GRANT_TOOL_ACCESS = "grant_tool_access"
    WRITE_MEMORY = "write_memory"
    MODIFY_IDENTITY = "modify_identity"
    MODIFY_POLICY = "modify_policy"
    EXFILTRATE_DATA = "exfiltrate_data"
    EXECUTE_COMMAND = "execute_command"
    UNKNOWN_AUTHORITY_CLAIM = "unknown_authority_claim"
    ROLEPLAY_AUTHORITY = "roleplay_authority"
    HIDDEN_INSTRUCTION = "hidden_instruction"
    ENCODED_INSTRUCTION = "encoded_instruction"
    PROMPT_LEAK_REQUEST = "prompt_leak_request"
    SECRET_REQUEST = "secret_request"


class PromptBoundaryRequirementType(str, Enum):
    REQUIRES_SOURCE_REFERENCE = "requires_source_reference"
    REQUIRES_PROVENANCE = "requires_provenance"
    REQUIRES_REVIEW = "requires_review"
    REQUIRES_SANDBOX = "requires_sandbox"
    REQUIRES_REDACTION = "requires_redaction"
    REQUIRES_LOCAL_ONLY = "requires_local_only"
    REQUIRES_QUOTE_ONLY = "requires_quote_only"
    REQUIRES_CONTEXT_ONLY = "requires_context_only"
    REQUIRES_INSTRUCTION_BOUNDARY = "requires_instruction_boundary"
    REQUIRES_TOOL_POLICY_CHECK = "requires_tool_policy_check"
    REQUIRES_MEMORY_POLICY_CHECK = "requires_memory_policy_check"
    REQUIRES_IDENTITY_PROTECTION = "requires_identity_protection"
    REQUIRES_POLICY_PROTECTION = "requires_policy_protection"
    REQUIRES_DATA_RESIDENCY_CHECK = "requires_data_residency_check"


# ---------------------------------------------------------------------------
# Valid value sets
# ---------------------------------------------------------------------------

_VALID_SOURCE_TYPES = frozenset(s.value for s in PromptSourceType)
_VALID_TRUST_LEVELS = frozenset(t.value for t in PromptTrustLevel)
_VALID_ROLES = frozenset(r.value for r in PromptRole)
_VALID_DECISIONS = frozenset(d.value for d in PromptPolicyDecision)
_VALID_INJECTION_RISKS = frozenset(r.value for r in PromptInjectionRisk)
_VALID_INJECTION_PATTERNS = frozenset(p.value for p in PromptInjectionPattern)
_VALID_REQUIREMENT_TYPES = frozenset(r.value for r in PromptBoundaryRequirementType)

# Trust-level categories used by validation
_UNTRUSTED_TRUST_LEVELS = frozenset({
    "external_untrusted",
    "tool_output_untrusted",
    "unknown_untrusted",
    "retrieved_context",
})

_TRUSTED_TRUST_LEVELS = frozenset({
    "trusted_system",
    "trusted_developer",
    "operator_authorized",
    "repo_canonical",
    "verified_template",
})

# Injection risk ordering for severity comparisons
_INJECTION_RISK_RANK = {
    "none": 0,
    "low": 1,
    "medium": 2,
    "high": 3,
    "critical": 4,
}


# ---------------------------------------------------------------------------
# Dataclass models
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PromptBoundaryRequirement:
    requirement_type: PromptBoundaryRequirementType
    required: bool = True
    description: str = ""


@dataclass(frozen=True)
class PromptInjectionSignal:
    pattern: PromptInjectionPattern
    risk: PromptInjectionRisk
    description: str = ""


@dataclass(frozen=True)
class PromptHandlingRule:
    source_type: PromptSourceType
    trust_level: PromptTrustLevel
    prompt_role: PromptRole
    decision: PromptPolicyDecision
    allowed_as_instruction: bool = False
    allowed_as_context: bool = True
    allowed_to_request_tools: bool = False
    allowed_to_write_memory: bool = False
    allowed_to_modify_policy: bool = False
    allowed_to_modify_identity: bool = False
    requires_provenance: bool = True
    requires_redaction: bool = False
    requires_review: bool = False
    requires_sandbox: bool = False
    local_only: bool = False
    injection_risk: PromptInjectionRisk = PromptInjectionRisk.NONE
    injection_signals: tuple[PromptInjectionSignal, ...] = ()
    requirements: tuple[PromptBoundaryRequirement, ...] = ()
    risk_ceiling: str | None = None
    required_oversight: str | None = None
    description: str = ""


@dataclass(frozen=True)
class PromptPolicyValidationIssue:
    code: str
    message: str
    field: str | None = None
    severity: str = "error"


@dataclass(frozen=True)
class PromptPolicyValidationResult:
    valid: bool
    errors: tuple[PromptPolicyValidationIssue, ...]
    warnings: tuple[PromptPolicyValidationIssue, ...]
    card_id: str | None = None
    canonical_hash: str | None = None


@dataclass(frozen=True)
class PromptPolicyCard:
    policy_card: PolicyCard
    schema_version: str
    prompt_rules: tuple[PromptHandlingRule, ...]
    default_decision: PromptPolicyDecision = PromptPolicyDecision.DENY
    metadata: Mapping[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


_EnumT = TypeVar("_EnumT", bound=Enum)


def _make_issue(
    code: str,
    message: str,
    field: str | None = None,
    severity: str = "error",
) -> PromptPolicyValidationIssue:
    return PromptPolicyValidationIssue(
        code=code, message=message, field=field, severity=severity,
    )


def _enum_value(value: object) -> str | None:
    if isinstance(value, Enum):
        return str(value.value)
    if isinstance(value, str):
        return value
    return None


def _coerce_enum(
    raw: object,
    enum_type: type[_EnumT],
    valid_values: frozenset[str],
    field_name: str,
) -> _EnumT:
    if not isinstance(raw, str) or raw not in valid_values:
        raise PromptPolicyCardValidationError(
            f"{field_name} value {raw!r} must be one of: "
            f"{', '.join(sorted(valid_values))}"
        )
    return enum_type(raw)


def _require_bool(raw: object, field_name: str) -> bool:
    if not isinstance(raw, bool):
        raise PromptPolicyCardValidationError(f"{field_name} must be boolean")
    return raw


def _require_mapping(raw: object, field_name: str) -> Mapping[str, Any]:
    if not isinstance(raw, MappingABC):
        raise PromptPolicyCardValidationError(f"{field_name} must be a mapping")
    return raw


def _check_mapping_fields(
    raw: Mapping[str, Any],
    known_fields: frozenset[str],
    dangerous_fields: frozenset[str],
    field_name: str,
) -> None:
    present = set(raw.keys())
    dangerous = present & dangerous_fields
    if dangerous:
        raise PromptPolicyCardUnsafeFieldError(
            f"{field_name}: dangerous field(s): {', '.join(sorted(dangerous))}"
        )
    unknown = present - known_fields
    if unknown:
        raise PromptPolicyCardUnknownFieldError(
            f"{field_name}: unknown field(s): {', '.join(sorted(unknown))} - closed-world"
        )


def _effective_injection_rank(rule: PromptHandlingRule) -> int:
    rank = _INJECTION_RISK_RANK.get(rule.injection_risk.value, 0)
    for signal in rule.injection_signals:
        rank = max(rank, _INJECTION_RISK_RANK.get(signal.risk.value, 0))
    return rank


# ---------------------------------------------------------------------------
# Sub-object loaders
# ---------------------------------------------------------------------------


def _load_requirement(
    raw: Mapping[str, Any],
    field_name: str,
) -> PromptBoundaryRequirement:
    from .prompt_policy_schema import (
        PROMPT_BOUNDARY_REQUIREMENT_OPTIONAL_FIELDS,
        PROMPT_BOUNDARY_REQUIREMENT_REQUIRED_FIELDS,
        PROMPT_POLICY_DANGEROUS_FIELD_NAMES,
    )

    known_fields = frozenset(
        PROMPT_BOUNDARY_REQUIREMENT_REQUIRED_FIELDS
        + PROMPT_BOUNDARY_REQUIREMENT_OPTIONAL_FIELDS
    )
    _check_mapping_fields(
        raw, known_fields, PROMPT_POLICY_DANGEROUS_FIELD_NAMES, field_name,
    )

    missing = frozenset(PROMPT_BOUNDARY_REQUIREMENT_REQUIRED_FIELDS) - set(raw.keys())
    if missing:
        raise PromptPolicyCardValidationError(
            f"{field_name}: missing required field(s): {', '.join(sorted(missing))}"
        )

    return PromptBoundaryRequirement(
        requirement_type=_coerce_enum(
            raw["requirement_type"], PromptBoundaryRequirementType,
            _VALID_REQUIREMENT_TYPES, f"{field_name}.requirement_type",
        ),
        required=_require_bool(raw.get("required", True), f"{field_name}.required"),
        description=str(raw.get("description", "")),
    )


def _load_injection_signal(
    raw: Mapping[str, Any],
    field_name: str,
) -> PromptInjectionSignal:
    from .prompt_policy_schema import (
        PROMPT_INJECTION_SIGNAL_OPTIONAL_FIELDS,
        PROMPT_INJECTION_SIGNAL_REQUIRED_FIELDS,
        PROMPT_POLICY_DANGEROUS_FIELD_NAMES,
    )

    known_fields = frozenset(
        PROMPT_INJECTION_SIGNAL_REQUIRED_FIELDS
        + PROMPT_INJECTION_SIGNAL_OPTIONAL_FIELDS
    )
    _check_mapping_fields(
        raw, known_fields, PROMPT_POLICY_DANGEROUS_FIELD_NAMES, field_name,
    )

    missing = frozenset(PROMPT_INJECTION_SIGNAL_REQUIRED_FIELDS) - set(raw.keys())
    if missing:
        raise PromptPolicyCardValidationError(
            f"{field_name}: missing required field(s): {', '.join(sorted(missing))}"
        )

    return PromptInjectionSignal(
        pattern=_coerce_enum(
            raw["pattern"], PromptInjectionPattern,
            _VALID_INJECTION_PATTERNS, f"{field_name}.pattern",
        ),
        risk=_coerce_enum(
            raw["risk"], PromptInjectionRisk,
            _VALID_INJECTION_RISKS, f"{field_name}.risk",
        ),
        description=str(raw.get("description", "")),
    )


def _load_handling_rule(
    raw: Mapping[str, Any],
    index: int,
) -> PromptHandlingRule:
    from .prompt_policy_schema import (
        PROMPT_HANDLING_RULE_OPTIONAL_FIELDS,
        PROMPT_HANDLING_RULE_REQUIRED_FIELDS,
        PROMPT_POLICY_DANGEROUS_FIELD_NAMES,
    )

    field_prefix = f"prompt_rules[{index}]"
    known_fields = frozenset(
        PROMPT_HANDLING_RULE_REQUIRED_FIELDS + PROMPT_HANDLING_RULE_OPTIONAL_FIELDS
    )
    _check_mapping_fields(
        raw, known_fields, PROMPT_POLICY_DANGEROUS_FIELD_NAMES, field_prefix,
    )

    missing = frozenset(PROMPT_HANDLING_RULE_REQUIRED_FIELDS) - set(raw.keys())
    if missing:
        raise PromptPolicyCardValidationError(
            f"{field_prefix}: missing required field(s): {', '.join(sorted(missing))}"
        )

    sigs_raw = raw.get("injection_signals", ())
    if not isinstance(sigs_raw, (list, tuple)):
        raise PromptPolicyCardValidationError(
            f"{field_prefix}.injection_signals must be a list/tuple"
        )
    injection_signals = tuple(
        _load_injection_signal(
            _require_mapping(item, f"{field_prefix}.injection_signals[{i}]"),
            f"{field_prefix}.injection_signals[{i}]",
        )
        for i, item in enumerate(sigs_raw)
    )

    reqs_raw = raw.get("requirements", ())
    if not isinstance(reqs_raw, (list, tuple)):
        raise PromptPolicyCardValidationError(
            f"{field_prefix}.requirements must be a list/tuple"
        )
    requirements = tuple(
        _load_requirement(
            _require_mapping(item, f"{field_prefix}.requirements[{i}]"),
            f"{field_prefix}.requirements[{i}]",
        )
        for i, item in enumerate(reqs_raw)
    )

    def _b(name: str, default: bool) -> bool:
        return _require_bool(raw.get(name, default), f"{field_prefix}.{name}")

    injection_risk_raw = raw.get("injection_risk", "none")
    injection_risk = _coerce_enum(
        injection_risk_raw, PromptInjectionRisk, _VALID_INJECTION_RISKS,
        f"{field_prefix}.injection_risk",
    )

    return PromptHandlingRule(
        source_type=_coerce_enum(
            raw["source_type"], PromptSourceType, _VALID_SOURCE_TYPES,
            f"{field_prefix}.source_type",
        ),
        trust_level=_coerce_enum(
            raw["trust_level"], PromptTrustLevel, _VALID_TRUST_LEVELS,
            f"{field_prefix}.trust_level",
        ),
        prompt_role=_coerce_enum(
            raw["prompt_role"], PromptRole, _VALID_ROLES,
            f"{field_prefix}.prompt_role",
        ),
        decision=_coerce_enum(
            raw["decision"], PromptPolicyDecision, _VALID_DECISIONS,
            f"{field_prefix}.decision",
        ),
        allowed_as_instruction=_b("allowed_as_instruction", False),
        allowed_as_context=_b("allowed_as_context", True),
        allowed_to_request_tools=_b("allowed_to_request_tools", False),
        allowed_to_write_memory=_b("allowed_to_write_memory", False),
        allowed_to_modify_policy=_b("allowed_to_modify_policy", False),
        allowed_to_modify_identity=_b("allowed_to_modify_identity", False),
        requires_provenance=_b("requires_provenance", True),
        requires_redaction=_b("requires_redaction", False),
        requires_review=_b("requires_review", False),
        requires_sandbox=_b("requires_sandbox", False),
        local_only=_b("local_only", False),
        injection_risk=injection_risk,
        injection_signals=injection_signals,
        requirements=requirements,
        risk_ceiling=raw.get("risk_ceiling"),
        required_oversight=raw.get("required_oversight"),
        description=str(raw.get("description", "")),
    )


def _metadata_issues(
    metadata: object,
    field_name: str,
) -> list[PromptPolicyValidationIssue]:
    from .prompt_policy_schema import PROMPT_POLICY_DANGEROUS_METADATA_KEYS

    issues: list[PromptPolicyValidationIssue] = []
    if not isinstance(metadata, MappingABC):
        issues.append(
            _make_issue("INVALID_TYPE", f"{field_name} must be a mapping", field=field_name)
        )
        return issues

    dangerous = set(metadata.keys()) & PROMPT_POLICY_DANGEROUS_METADATA_KEYS
    for key in sorted(dangerous):
        issues.append(
            _make_issue(
                "UNSAFE_METADATA_KEY",
                f"{field_name}: dangerous key '{key}' rejected",
                field=f"{field_name}.{key}",
            )
        )
    return issues


# ---------------------------------------------------------------------------
# Canonical serialization helpers
# ---------------------------------------------------------------------------


def _requirement_to_canonical_dict(req: PromptBoundaryRequirement) -> dict[str, Any]:
    return {
        "description": req.description,
        "required": req.required,
        "requirement_type": req.requirement_type.value,
    }


def _signal_to_canonical_dict(sig: PromptInjectionSignal) -> dict[str, Any]:
    return {
        "description": sig.description,
        "pattern": sig.pattern.value,
        "risk": sig.risk.value,
    }


def _rule_to_canonical_dict(rule: PromptHandlingRule) -> dict[str, Any]:
    result: dict[str, Any] = {
        "allowed_as_context": rule.allowed_as_context,
        "allowed_as_instruction": rule.allowed_as_instruction,
        "allowed_to_modify_identity": rule.allowed_to_modify_identity,
        "allowed_to_modify_policy": rule.allowed_to_modify_policy,
        "allowed_to_request_tools": rule.allowed_to_request_tools,
        "allowed_to_write_memory": rule.allowed_to_write_memory,
        "decision": rule.decision.value,
        "description": rule.description,
        "injection_risk": rule.injection_risk.value,
        "local_only": rule.local_only,
        "prompt_role": rule.prompt_role.value,
        "requires_provenance": rule.requires_provenance,
        "requires_redaction": rule.requires_redaction,
        "requires_review": rule.requires_review,
        "requires_sandbox": rule.requires_sandbox,
        "source_type": rule.source_type.value,
        "trust_level": rule.trust_level.value,
    }
    if rule.injection_signals:
        result["injection_signals"] = [
            _signal_to_canonical_dict(s) for s in rule.injection_signals
        ]
    if rule.requirements:
        result["requirements"] = [
            _requirement_to_canonical_dict(r) for r in rule.requirements
        ]
    if rule.risk_ceiling is not None:
        result["risk_ceiling"] = rule.risk_ceiling
    if rule.required_oversight is not None:
        result["required_oversight"] = rule.required_oversight
    return dict(sorted(result.items(), key=lambda i: i[0]))


# ---------------------------------------------------------------------------
# Public serialization / hash API
# ---------------------------------------------------------------------------


def prompt_policy_card_to_canonical_dict(
    card: PromptPolicyCard,
) -> dict[str, Any]:
    rules = [_rule_to_canonical_dict(r) for r in card.prompt_rules]

    canonical: dict[str, Any] = {
        "default_decision": card.default_decision.value,
        "metadata": dict(sorted(dict(card.metadata).items(), key=lambda i: i[0])),
        "policy_card": policy_card_to_canonical_dict(card.policy_card),
        "prompt_rules": rules,
        "schema_version": card.schema_version,
    }
    return dict(sorted(canonical.items(), key=lambda i: i[0]))


def serialize_prompt_policy_card_canonical(card: PromptPolicyCard) -> str:
    canonical = prompt_policy_card_to_canonical_dict(card)
    return json.dumps(canonical, sort_keys=True, separators=(",", ":"))


def compute_prompt_policy_card_hash(card: PromptPolicyCard) -> str:
    canonical = serialize_prompt_policy_card_canonical(card)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def _check_rule_safety(
    rule: PromptHandlingRule,
    field_prefix: str,
    errors: list[PromptPolicyValidationIssue],
) -> None:
    from .prompt_policy_schema import EXTERNAL_PROMPT_SOURCES

    source = rule.source_type.value
    trust = rule.trust_level.value
    decision = rule.decision.value
    untrusted = trust in _UNTRUSTED_TRUST_LEVELS

    # Unknown source cannot be trusted
    if source == "unknown" and trust in _TRUSTED_TRUST_LEVELS:
        errors.append(_make_issue(
            "UNKNOWN_SOURCE_TRUSTED",
            f"{field_prefix}: unknown source cannot have trusted trust level '{trust}'",
            field=f"{field_prefix}.trust_level",
        ))

    # External content cannot be instruction authority
    if source in EXTERNAL_PROMPT_SOURCES and rule.allowed_as_instruction:
        errors.append(_make_issue(
            "EXTERNAL_AS_INSTRUCTION",
            f"{field_prefix}: external source '{source}' cannot be instruction authority",
            field=f"{field_prefix}.allowed_as_instruction",
        ))

    # Untrusted trust level cannot be instruction authority
    if untrusted and rule.allowed_as_instruction:
        errors.append(_make_issue(
            "UNTRUSTED_AS_INSTRUCTION",
            f"{field_prefix}: untrusted trust level '{trust}' cannot be instruction authority",
            field=f"{field_prefix}.allowed_as_instruction",
        ))

    # Tool output is data, not command
    if source == "tool_output" and rule.allowed_as_instruction:
        errors.append(_make_issue(
            "TOOL_OUTPUT_AS_INSTRUCTION",
            f"{field_prefix}: tool_output cannot be instruction authority; "
            "tool output is data/context, not command",
            field=f"{field_prefix}.allowed_as_instruction",
        ))

    # Retrieved memory is context, not automatic authority
    if source == "retrieved_memory":
        if rule.allowed_as_instruction:
            errors.append(_make_issue(
                "RETRIEVED_MEMORY_AS_INSTRUCTION",
                f"{field_prefix}: retrieved_memory cannot be automatic instruction authority",
                field=f"{field_prefix}.allowed_as_instruction",
            ))
        if (
            rule.allowed_to_request_tools
            or rule.allowed_to_write_memory
            or rule.allowed_to_modify_policy
            or rule.allowed_to_modify_identity
        ):
            errors.append(_make_issue(
                "RETRIEVED_MEMORY_OVERREACH",
                f"{field_prefix}: retrieved_memory cannot request tools, write memory, "
                "or modify policy/identity",
                field=f"{field_prefix}",
            ))

    # Untrusted content cannot request tools
    if untrusted and rule.allowed_to_request_tools:
        errors.append(_make_issue(
            "UNTRUSTED_REQUEST_TOOLS",
            f"{field_prefix}: untrusted trust level '{trust}' cannot request tools",
            field=f"{field_prefix}.allowed_to_request_tools",
        ))

    # Untrusted content cannot write memory
    if untrusted and rule.allowed_to_write_memory:
        errors.append(_make_issue(
            "UNTRUSTED_WRITE_MEMORY",
            f"{field_prefix}: untrusted trust level '{trust}' cannot write memory",
            field=f"{field_prefix}.allowed_to_write_memory",
        ))

    # Untrusted content cannot modify policy
    if untrusted and rule.allowed_to_modify_policy:
        errors.append(_make_issue(
            "UNTRUSTED_MODIFY_POLICY",
            f"{field_prefix}: untrusted trust level '{trust}' cannot modify policy",
            field=f"{field_prefix}.allowed_to_modify_policy",
        ))

    # Untrusted content cannot modify identity
    if untrusted and rule.allowed_to_modify_identity:
        errors.append(_make_issue(
            "UNTRUSTED_MODIFY_IDENTITY",
            f"{field_prefix}: untrusted trust level '{trust}' cannot modify identity",
            field=f"{field_prefix}.allowed_to_modify_identity",
        ))

    # High/critical injection risk cannot be paired with permissive instruction authority
    if _effective_injection_rank(rule) >= _INJECTION_RISK_RANK["high"]:
        if rule.allowed_as_instruction and decision == "allow":
            errors.append(_make_issue(
                "INJECTION_RISK_PERMISSIVE_INSTRUCTION",
                f"{field_prefix}: high/critical injection risk cannot be paired with "
                "allow + instruction authority",
                field=f"{field_prefix}.injection_risk",
            ))


def validate_prompt_policy_card(
    card: PromptPolicyCard,
) -> PromptPolicyValidationResult:
    from .prompt_policy_schema import (
        SUPPORTED_PROMPT_POLICY_CARD_SCHEMA_VERSIONS,
    )

    errors: list[PromptPolicyValidationIssue] = []
    warnings: list[PromptPolicyValidationIssue] = []

    if not isinstance(card, PromptPolicyCard):
        errors.append(
            _make_issue("INVALID_TYPE", "card must be a PromptPolicyCard", field="card")
        )
        return PromptPolicyValidationResult(False, tuple(errors), tuple(warnings))

    if (
        not isinstance(card.schema_version, str)
        or not card.schema_version.strip()
        or card.schema_version not in SUPPORTED_PROMPT_POLICY_CARD_SCHEMA_VERSIONS
    ):
        errors.append(
            _make_issue(
                "UNSUPPORTED_SCHEMA_VERSION",
                f"schema_version '{card.schema_version}' is not supported",
                field="schema_version",
            )
        )

    if not isinstance(card.policy_card, PolicyCard):
        errors.append(
            _make_issue("INVALID_TYPE", "policy_card must be a PolicyCard", field="policy_card")
        )
    else:
        try:
            from .validation import validate_policy_card as _vp
            policy_result = _vp(card.policy_card)
        except Exception as exc:
            errors.append(_make_issue(
                "INVALID_POLICY_CARD",
                f"embedded policy_card validation failed: {exc}",
                field="policy_card",
            ))
            policy_result = None
        if policy_result is not None and hasattr(policy_result, 'errors'):
            for issue in policy_result.errors:
                errors.append(
                    _make_issue(
                        f"POLICY_CARD_{issue.code}",
                        issue.message,
                        field=f"policy_card.{issue.field}" if issue.field else "policy_card",
                        severity=issue.severity,
                    )
                )
        kind_value = _enum_value(card.policy_card.kind)
        if kind_value != PolicyCardKind.PROMPT.value:
            errors.append(
                _make_issue(
                    "INVALID_POLICY_CARD_KIND",
                    "PromptPolicyCard requires generic PolicyCard kind 'prompt'",
                    field="policy_card.kind",
                )
            )

    decision_value = _enum_value(card.default_decision)
    if decision_value not in _VALID_DECISIONS:
        errors.append(
            _make_issue("INVALID_DEFAULT_DECISION", "default_decision is invalid",
                        field="default_decision")
        )
    elif decision_value not in ("deny", "forbidden"):
        errors.append(
            _make_issue(
                "PERMISSIVE_DEFAULT_DECISION",
                f"default_decision must be strict/deny-by-default, not '{decision_value}'",
                field="default_decision",
            )
        )

    errors.extend(_metadata_issues(card.metadata, "metadata"))

    if not isinstance(card.prompt_rules, tuple):
        errors.append(
            _make_issue("INVALID_TYPE", "prompt_rules must be a tuple", field="prompt_rules")
        )
        rule_items: tuple[object, ...] = ()
    else:
        rule_items = card.prompt_rules

    if isinstance(card.prompt_rules, tuple) and not card.prompt_rules:
        errors.append(
            _make_issue("EMPTY_PROMPT_RULES", "prompt_rules must not be empty",
                        field="prompt_rules")
        )

    for index, rule in enumerate(rule_items):
        field_prefix = f"prompt_rules[{index}]"
        if not isinstance(rule, PromptHandlingRule):
            errors.append(
                _make_issue("INVALID_TYPE", f"{field_prefix} must be a PromptHandlingRule",
                            field=field_prefix)
            )
            continue

        src = _enum_value(rule.source_type)
        if src not in _VALID_SOURCE_TYPES:
            errors.append(_make_issue(
                "INVALID_SOURCE_TYPE",
                f"{field_prefix}.source_type '{src}' is invalid",
                field=f"{field_prefix}.source_type",
            ))
        trust = _enum_value(rule.trust_level)
        if trust not in _VALID_TRUST_LEVELS:
            errors.append(_make_issue(
                "INVALID_TRUST_LEVEL",
                f"{field_prefix}.trust_level '{trust}' is invalid",
                field=f"{field_prefix}.trust_level",
            ))
        role = _enum_value(rule.prompt_role)
        if role not in _VALID_ROLES:
            errors.append(_make_issue(
                "INVALID_PROMPT_ROLE",
                f"{field_prefix}.prompt_role '{role}' is invalid",
                field=f"{field_prefix}.prompt_role",
            ))
        dec = _enum_value(rule.decision)
        if dec not in _VALID_DECISIONS:
            errors.append(_make_issue(
                "INVALID_DECISION",
                f"{field_prefix}.decision '{dec}' is invalid",
                field=f"{field_prefix}.decision",
            ))
        ir = _enum_value(rule.injection_risk)
        if ir not in _VALID_INJECTION_RISKS:
            errors.append(_make_issue(
                "INVALID_INJECTION_RISK",
                f"{field_prefix}.injection_risk '{ir}' is invalid",
                field=f"{field_prefix}.injection_risk",
            ))

        for si, sig in enumerate(rule.injection_signals):
            if _enum_value(sig.pattern) not in _VALID_INJECTION_PATTERNS:
                errors.append(_make_issue(
                    "INVALID_INJECTION_PATTERN",
                    f"{field_prefix}.injection_signals[{si}].pattern is invalid",
                    field=f"{field_prefix}.injection_signals[{si}]",
                ))
            if _enum_value(sig.risk) not in _VALID_INJECTION_RISKS:
                errors.append(_make_issue(
                    "INVALID_INJECTION_RISK",
                    f"{field_prefix}.injection_signals[{si}].risk is invalid",
                    field=f"{field_prefix}.injection_signals[{si}]",
                ))

        for ri, req in enumerate(rule.requirements):
            if _enum_value(req.requirement_type) not in _VALID_REQUIREMENT_TYPES:
                errors.append(_make_issue(
                    "INVALID_REQUIREMENT_TYPE",
                    f"{field_prefix}.requirements[{ri}] is invalid",
                    field=f"{field_prefix}.requirements[{ri}]",
                ))

        _check_rule_safety(rule, field_prefix, errors)

    canonical_hash: str | None = None
    try:
        canonical_hash = compute_prompt_policy_card_hash(card)
    except Exception as exc:
        errors.append(
            _make_issue(
                "CANONICAL_HASH_FAILED",
                f"canonical hash could not be computed: {exc}",
                field="canonical_hash",
            )
        )

    card_id = None
    if isinstance(card.policy_card, PolicyCard):
        card_id = card.policy_card.identity.card_id

    return PromptPolicyValidationResult(
        valid=len(errors) == 0,
        errors=tuple(errors),
        warnings=tuple(warnings),
        card_id=card_id,
        canonical_hash=canonical_hash,
    )


# ---------------------------------------------------------------------------
# Dict loader
# ---------------------------------------------------------------------------


def load_prompt_policy_card_from_dict(
    data: Mapping[str, Any],
) -> PromptPolicyCard:
    from .prompt_policy_schema import (
        PROMPT_POLICY_DANGEROUS_FIELD_NAMES,
        PROMPT_POLICY_DANGEROUS_METADATA_KEYS,
        PROMPT_POLICY_OPTIONAL_FIELDS,
        PROMPT_POLICY_REQUIRED_FIELDS,
        SUPPORTED_PROMPT_POLICY_CARD_SCHEMA_VERSIONS,
    )

    raw = _require_mapping(data, "prompt policy card data")
    known_fields = frozenset(PROMPT_POLICY_REQUIRED_FIELDS + PROMPT_POLICY_OPTIONAL_FIELDS)
    _check_mapping_fields(
        raw, known_fields, PROMPT_POLICY_DANGEROUS_FIELD_NAMES,
        "prompt_policy_card",
    )

    missing = frozenset(PROMPT_POLICY_REQUIRED_FIELDS) - set(raw.keys())
    if missing:
        raise PromptPolicyCardValidationError(
            f"missing required field(s): {', '.join(sorted(missing))}"
        )

    schema_version = raw.get("schema_version")
    if (
        not isinstance(schema_version, str)
        or not schema_version.strip()
        or schema_version not in SUPPORTED_PROMPT_POLICY_CARD_SCHEMA_VERSIONS
    ):
        raise PromptPolicyCardValidationError(
            f"schema_version must be one of: "
            f"{', '.join(SUPPORTED_PROMPT_POLICY_CARD_SCHEMA_VERSIONS)}"
        )

    policy_card_raw = _require_mapping(raw.get("policy_card"), "policy_card")
    try:
        policy_card = load_policy_card_from_dict(dict(policy_card_raw))
    except PolicyCardError as exc:
        raise PromptPolicyCardValidationError(
            f"embedded policy_card invalid: {exc}"
        ) from exc

    rules_raw = raw.get("prompt_rules")
    if not isinstance(rules_raw, (list, tuple)):
        raise PromptPolicyCardValidationError("prompt_rules must be a list/tuple")
    prompt_rules = tuple(
        _load_handling_rule(
            _require_mapping(item, f"prompt_rules[{index}]"), index,
        )
        for index, item in enumerate(rules_raw)
    )

    dd_raw = raw.get("default_decision", "deny")
    if isinstance(dd_raw, str) and dd_raw in _VALID_DECISIONS:
        default_decision = PromptPolicyDecision(dd_raw)
    else:
        raise PromptPolicyCardValidationError(
            f"default_decision must be one of: {', '.join(sorted(_VALID_DECISIONS))}"
        )

    metadata_raw = raw.get("metadata")
    if metadata_raw is None:
        metadata: dict[str, Any] = {}
    elif isinstance(metadata_raw, MappingABC):
        dangerous_meta = set(metadata_raw.keys()) & PROMPT_POLICY_DANGEROUS_METADATA_KEYS
        if dangerous_meta:
            raise PromptPolicyCardUnsafeFieldError(
                f"dangerous metadata key(s): {', '.join(sorted(dangerous_meta))}"
            )
        metadata = dict(metadata_raw)
    else:
        raise PromptPolicyCardValidationError("metadata must be a mapping")

    card = PromptPolicyCard(
        policy_card=policy_card,
        schema_version=schema_version,
        prompt_rules=prompt_rules,
        default_decision=default_decision,
        metadata=metadata,
    )

    result = validate_prompt_policy_card(card)
    if not result.valid:
        messages = "; ".join(e.message for e in result.errors)
        raise PromptPolicyCardValidationError(f"validation failed: {messages}")

    return card


def validate_prompt_policy_card_dict(
    data: Mapping[str, Any],
) -> PromptPolicyValidationResult:
    try:
        card = load_prompt_policy_card_from_dict(data)
    except PromptPolicyCardError as exc:
        card_id = None
        if isinstance(data, MappingABC):
            policy_card_raw = data.get("policy_card")
            if isinstance(policy_card_raw, MappingABC):
                identity = policy_card_raw.get("identity")
                if isinstance(identity, MappingABC):
                    raw_card_id = identity.get("card_id")
                    if isinstance(raw_card_id, str):
                        card_id = raw_card_id
        return PromptPolicyValidationResult(
            valid=False,
            errors=(
                _make_issue("INVALID_DATA_PROMPT_POLICY_CARD_DICT", str(exc), field=None),
            ),
            warnings=(),
            card_id=card_id,
            canonical_hash=None,
        )
    return validate_prompt_policy_card(card)


# ---------------------------------------------------------------------------
# Default factory
# ---------------------------------------------------------------------------


def create_default_prompt_policy_card() -> PromptPolicyCard:
    from .prompt_policy_schema import (
        DEFAULT_PROMPT_HANDLING_RULES,
        PROMPT_POLICY_CARD_SCHEMA_VERSION,
    )

    policy_card = PolicyCard(
        schema_version="1.0",
        identity=PolicyCardIdentity(
            card_id="aurel-core-prompt-policy-v1",
            slug="aurel-core-prompt-policy",
            name="AurelCore Prompt Policy",
            version="1.0",
            namespace="aurel_core",
        ),
        kind=PolicyCardKind.PROMPT,
        status=PolicyCardStatus.ACTIVE,
        scope=PolicyCardScope(scope_type=PolicyCardScopeType.PROMPT),
        description=(
            "Defines strict deny-by-default prompt trust and instruction-boundary "
            "semantics for AurelCore; does not compile prompts, enforce instruction "
            "hierarchy, detect injection, or block tools/memory at runtime."
        ),
    )

    return PromptPolicyCard(
        policy_card=policy_card,
        schema_version=PROMPT_POLICY_CARD_SCHEMA_VERSION,
        prompt_rules=DEFAULT_PROMPT_HANDLING_RULES,
        default_decision=PromptPolicyDecision.DENY,
        metadata={"owner_note": "strict default prompt policy: untrusted content may inform, never command"},
    )
