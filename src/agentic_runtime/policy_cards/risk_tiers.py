"""Risk Tier Policy Card model (P1.6.3).

Defines the R0-R6 risk-tier semantic vocabulary for AurelCore policy cards.
Risk tier cards are declarative, deterministic, closed-world, and hash-ready.

Architectural law:
  - Risk tier cards do not grant authority.
  - Risk tier cards do not classify arbitrary actions.
  - Risk tier cards do not enforce runtime behavior.
  - Risk tier cards remain compatible with generic PolicyCard(kind="risk_tier").
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
    RiskTierPolicyCardUnknownFieldError,
    RiskTierPolicyCardUnsafeFieldError,
    RiskTierPolicyCardValidationError,
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
from .validation import load_policy_card_from_dict, validate_policy_card


class RiskTier(str, Enum):
    R0 = "R0"
    R1 = "R1"
    R2 = "R2"
    R3 = "R3"
    R4 = "R4"
    R5 = "R5"
    R6 = "R6"


class ReversibilityLevel(str, Enum):
    NONE = "none"
    READ_ONLY = "read_only"
    REVERSIBLE = "reversible"
    COMPENSATABLE = "compensatable"
    IRREVERSIBLE = "irreversible"
    DENIED = "denied"


class OversightLevel(str, Enum):
    NONE = "none"
    OPTIONAL = "optional"
    REVIEW_RECOMMENDED = "review_recommended"
    APPROVAL_REQUIRED = "approval_required"
    EXPLICIT_OPERATOR_CONFIRMATION = "explicit_operator_confirmation"
    DENIED = "denied"


class EvidenceExpectation(str, Enum):
    NONE = "none"
    LIGHTWEIGHT_TRACE = "lightweight_trace"
    TRACE_SUMMARY = "trace_summary"
    TRACE_EVIDENCE_REF = "trace_evidence_ref"
    TRACE_EVIDENCE_APPROVAL = "trace_evidence_approval"
    TRACE_SHADOW_DIFF_EXPLICIT_CONFIRMATION = (
        "trace_shadow_diff_explicit_confirmation"
    )
    DENIAL_TRACE = "denial_trace"


class RiskActionClass(str, Enum):
    INFORMATIONAL = "informational"
    READ_LOCAL = "read_local"
    WRITE_LOCAL = "write_local"
    MODIFY_CODE = "modify_code"
    RUN_TESTS = "run_tests"
    EXECUTE_COMMAND = "execute_command"
    CALL_MODEL_LOCAL = "call_model_local"
    CALL_MODEL_EXTERNAL = "call_model_external"
    WRITE_MEMORY = "write_memory"
    READ_MEMORY = "read_memory"
    SEND_EMAIL = "send_email"
    DELETE_FILE = "delete_file"
    NETWORK_EGRESS = "network_egress"
    BUSINESS_DECISION = "business_decision"
    FINANCIAL_ACTION = "financial_action"
    PROTECTED_PATH_WRITE = "protected_path_write"
    SANDBOXED_TOOL_CALL = "sandboxed_tool_call"
    EXTERNAL_API_CALL = "external_api_call"


@dataclass(frozen=True)
class RiskTierDefinition:
    tier: RiskTier
    label: str
    description: str
    reversibility: ReversibilityLevel
    oversight: OversightLevel
    evidence_expectation: EvidenceExpectation
    default_requires_trace: bool
    default_requires_evidence: bool
    default_requires_approval: bool
    default_requires_explicit_confirmation: bool
    default_requires_sandbox: bool
    default_allows_external_egress: bool
    default_allows_memory_write: bool
    default_allows_tool_write: bool
    default_allows_execution: bool


@dataclass(frozen=True)
class RiskActionClassMapping:
    action_class: RiskActionClass
    default_tier: RiskTier
    description: str = ""


@dataclass(frozen=True)
class RiskTierValidationIssue:
    code: str
    message: str
    field: str | None = None
    severity: str = "error"


@dataclass(frozen=True)
class RiskTierValidationResult:
    valid: bool
    errors: tuple[RiskTierValidationIssue, ...]
    warnings: tuple[RiskTierValidationIssue, ...]
    card_id: str | None = None
    canonical_hash: str | None = None


@dataclass(frozen=True)
class RiskTierPolicyCard:
    policy_card: PolicyCard
    schema_version: str
    tiers: tuple[RiskTierDefinition, ...]
    action_class_mappings: tuple[RiskActionClassMapping, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)


_EnumT = TypeVar("_EnumT", bound=Enum)

_VALID_RISK_TIERS = frozenset(t.value for t in RiskTier)
_VALID_REVERSIBILITY_LEVELS = frozenset(r.value for r in ReversibilityLevel)
_VALID_OVERSIGHT_LEVELS = frozenset(o.value for o in OversightLevel)
_VALID_EVIDENCE_EXPECTATIONS = frozenset(e.value for e in EvidenceExpectation)
_VALID_ACTION_CLASSES = frozenset(a.value for a in RiskActionClass)


def _make_issue(
    code: str,
    message: str,
    field: str | None = None,
    severity: str = "error",
) -> RiskTierValidationIssue:
    return RiskTierValidationIssue(
        code=code,
        message=message,
        field=field,
        severity=severity,
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
        raise RiskTierPolicyCardValidationError(
            f"{field_name} value {raw!r} must be one of: "
            f"{', '.join(sorted(valid_values))}"
        )
    return enum_type(raw)  # type: ignore[call-arg]


def _require_bool(raw: object, field_name: str) -> bool:
    if not isinstance(raw, bool):
        raise RiskTierPolicyCardValidationError(f"{field_name} must be boolean")
    return raw


def _require_mapping(raw: object, field_name: str) -> Mapping[str, Any]:
    if not isinstance(raw, MappingABC):
        raise RiskTierPolicyCardValidationError(f"{field_name} must be a mapping")
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
        raise RiskTierPolicyCardUnsafeFieldError(
            f"{field_name}: dangerous field(s): {', '.join(sorted(dangerous))}"
        )
    unknown = present - known_fields
    if unknown:
        raise RiskTierPolicyCardUnknownFieldError(
            f"{field_name}: unknown field(s): {', '.join(sorted(unknown))} - closed-world"
        )


def _load_risk_tier_definition(
    raw: Mapping[str, Any],
    index: int,
) -> RiskTierDefinition:
    from .risk_tier_schema import (
        RISK_TIER_DANGEROUS_FIELD_NAMES,
        RISK_TIER_DEFINITION_REQUIRED_FIELDS,
    )

    field_prefix = f"tiers[{index}]"
    known_fields = frozenset(RISK_TIER_DEFINITION_REQUIRED_FIELDS)
    _check_mapping_fields(
        raw,
        known_fields,
        RISK_TIER_DANGEROUS_FIELD_NAMES,
        field_prefix,
    )

    missing = known_fields - set(raw.keys())
    if missing:
        raise RiskTierPolicyCardValidationError(
            f"{field_prefix}: missing required field(s): {', '.join(sorted(missing))}"
        )

    label = raw["label"]
    description = raw["description"]
    if not isinstance(label, str) or not label.strip():
        raise RiskTierPolicyCardValidationError(f"{field_prefix}.label is required")
    if not isinstance(description, str) or not description.strip():
        raise RiskTierPolicyCardValidationError(
            f"{field_prefix}.description is required"
        )

    return RiskTierDefinition(
        tier=_coerce_enum(raw["tier"], RiskTier, _VALID_RISK_TIERS, f"{field_prefix}.tier"),
        label=label,
        description=description,
        reversibility=_coerce_enum(
            raw["reversibility"],
            ReversibilityLevel,
            _VALID_REVERSIBILITY_LEVELS,
            f"{field_prefix}.reversibility",
        ),
        oversight=_coerce_enum(
            raw["oversight"],
            OversightLevel,
            _VALID_OVERSIGHT_LEVELS,
            f"{field_prefix}.oversight",
        ),
        evidence_expectation=_coerce_enum(
            raw["evidence_expectation"],
            EvidenceExpectation,
            _VALID_EVIDENCE_EXPECTATIONS,
            f"{field_prefix}.evidence_expectation",
        ),
        default_requires_trace=_require_bool(
            raw["default_requires_trace"],
            f"{field_prefix}.default_requires_trace",
        ),
        default_requires_evidence=_require_bool(
            raw["default_requires_evidence"],
            f"{field_prefix}.default_requires_evidence",
        ),
        default_requires_approval=_require_bool(
            raw["default_requires_approval"],
            f"{field_prefix}.default_requires_approval",
        ),
        default_requires_explicit_confirmation=_require_bool(
            raw["default_requires_explicit_confirmation"],
            f"{field_prefix}.default_requires_explicit_confirmation",
        ),
        default_requires_sandbox=_require_bool(
            raw["default_requires_sandbox"],
            f"{field_prefix}.default_requires_sandbox",
        ),
        default_allows_external_egress=_require_bool(
            raw["default_allows_external_egress"],
            f"{field_prefix}.default_allows_external_egress",
        ),
        default_allows_memory_write=_require_bool(
            raw["default_allows_memory_write"],
            f"{field_prefix}.default_allows_memory_write",
        ),
        default_allows_tool_write=_require_bool(
            raw["default_allows_tool_write"],
            f"{field_prefix}.default_allows_tool_write",
        ),
        default_allows_execution=_require_bool(
            raw["default_allows_execution"],
            f"{field_prefix}.default_allows_execution",
        ),
    )


def _load_action_class_mapping(
    raw: Mapping[str, Any],
    index: int,
) -> RiskActionClassMapping:
    from .risk_tier_schema import (
        RISK_TIER_ACTION_MAPPING_OPTIONAL_FIELDS,
        RISK_TIER_ACTION_MAPPING_REQUIRED_FIELDS,
        RISK_TIER_DANGEROUS_FIELD_NAMES,
    )

    field_prefix = f"action_class_mappings[{index}]"
    known_fields = frozenset(
        RISK_TIER_ACTION_MAPPING_REQUIRED_FIELDS
        + RISK_TIER_ACTION_MAPPING_OPTIONAL_FIELDS
    )
    _check_mapping_fields(
        raw,
        known_fields,
        RISK_TIER_DANGEROUS_FIELD_NAMES,
        field_prefix,
    )

    missing = frozenset(RISK_TIER_ACTION_MAPPING_REQUIRED_FIELDS) - set(raw.keys())
    if missing:
        raise RiskTierPolicyCardValidationError(
            f"{field_prefix}: missing required field(s): {', '.join(sorted(missing))}"
        )
    description = raw.get("description", "")
    if not isinstance(description, str):
        raise RiskTierPolicyCardValidationError(
            f"{field_prefix}.description must be a string"
        )

    return RiskActionClassMapping(
        action_class=_coerce_enum(
            raw["action_class"],
            RiskActionClass,
            _VALID_ACTION_CLASSES,
            f"{field_prefix}.action_class",
        ),
        default_tier=_coerce_enum(
            raw["default_tier"],
            RiskTier,
            _VALID_RISK_TIERS,
            f"{field_prefix}.default_tier",
        ),
        description=description,
    )


def _metadata_issues(
    metadata: object,
    field_name: str,
) -> list[RiskTierValidationIssue]:
    from .risk_tier_schema import RISK_TIER_DANGEROUS_METADATA_KEYS

    issues: list[RiskTierValidationIssue] = []
    if not isinstance(metadata, MappingABC):
        issues.append(
            _make_issue(
                "INVALID_TYPE",
                f"{field_name} must be a mapping",
                field=field_name,
            )
        )
        return issues

    dangerous = set(metadata.keys()) & RISK_TIER_DANGEROUS_METADATA_KEYS
    for key in sorted(dangerous):
        issues.append(
            _make_issue(
                "UNSAFE_METADATA_KEY",
                f"{field_name}: dangerous key '{key}' rejected",
                field=f"{field_name}.{key}",
            )
        )
    return issues


def _tier_definition_to_canonical_dict(
    definition: RiskTierDefinition,
) -> dict[str, Any]:
    return {
        "default_allows_execution": definition.default_allows_execution,
        "default_allows_external_egress": definition.default_allows_external_egress,
        "default_allows_memory_write": definition.default_allows_memory_write,
        "default_allows_tool_write": definition.default_allows_tool_write,
        "default_requires_approval": definition.default_requires_approval,
        "default_requires_evidence": definition.default_requires_evidence,
        "default_requires_explicit_confirmation": (
            definition.default_requires_explicit_confirmation
        ),
        "default_requires_sandbox": definition.default_requires_sandbox,
        "default_requires_trace": definition.default_requires_trace,
        "description": definition.description,
        "evidence_expectation": definition.evidence_expectation.value,
        "label": definition.label,
        "oversight": definition.oversight.value,
        "reversibility": definition.reversibility.value,
        "tier": definition.tier.value,
    }


def _action_mapping_to_canonical_dict(
    mapping: RiskActionClassMapping,
) -> dict[str, Any]:
    return {
        "action_class": mapping.action_class.value,
        "default_tier": mapping.default_tier.value,
        "description": mapping.description,
    }


def risk_tier_policy_card_to_canonical_dict(
    card: RiskTierPolicyCard,
) -> dict[str, Any]:
    tiers = sorted(
        (_tier_definition_to_canonical_dict(definition) for definition in card.tiers),
        key=lambda item: item["tier"],
    )
    mappings = sorted(
        (
            _action_mapping_to_canonical_dict(mapping)
            for mapping in card.action_class_mappings
        ),
        key=lambda item: (item["action_class"], item["default_tier"]),
    )

    canonical: dict[str, Any] = {
        "action_class_mappings": mappings,
        "metadata": dict(sorted(dict(card.metadata).items(), key=lambda item: item[0])),
        "policy_card": policy_card_to_canonical_dict(card.policy_card),
        "schema_version": card.schema_version,
        "tiers": tiers,
    }
    return dict(sorted(canonical.items(), key=lambda item: item[0]))


def serialize_risk_tier_policy_card_canonical(
    card: RiskTierPolicyCard,
) -> str:
    canonical = risk_tier_policy_card_to_canonical_dict(card)
    return json.dumps(canonical, sort_keys=True, separators=(",", ":"))


def compute_risk_tier_policy_card_hash(card: RiskTierPolicyCard) -> str:
    canonical = serialize_risk_tier_policy_card_canonical(card)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def validate_risk_tier_policy_card(
    card: RiskTierPolicyCard,
) -> RiskTierValidationResult:
    from .risk_tier_schema import (
        REQUIRED_RISK_TIERS,
        SUPPORTED_RISK_TIER_POLICY_CARD_SCHEMA_VERSIONS,
    )

    errors: list[RiskTierValidationIssue] = []
    warnings: list[RiskTierValidationIssue] = []

    if not isinstance(card, RiskTierPolicyCard):
        errors.append(
            _make_issue(
                "INVALID_TYPE",
                "card must be a RiskTierPolicyCard",
                field="card",
            )
        )
        return RiskTierValidationResult(False, tuple(errors), tuple(warnings))

    if (
        not isinstance(card.schema_version, str)
        or not card.schema_version.strip()
        or card.schema_version not in SUPPORTED_RISK_TIER_POLICY_CARD_SCHEMA_VERSIONS
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
            _make_issue(
                "INVALID_TYPE",
                "policy_card must be a PolicyCard",
                field="policy_card",
            )
        )
    else:
        try:
            policy_result = validate_policy_card(card.policy_card)
        except Exception as exc:
            policy_result = None
            errors.append(
                _make_issue(
                    "INVALID_POLICY_CARD",
                    f"embedded policy_card validation failed: {exc}",
                    field="policy_card",
                )
            )
        if policy_result is not None:
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
        if kind_value != PolicyCardKind.RISK_TIER.value:
            errors.append(
                _make_issue(
                    "INVALID_POLICY_CARD_KIND",
                    "RiskTierPolicyCard requires generic PolicyCard kind 'risk_tier'",
                    field="policy_card.kind",
                )
            )

    errors.extend(_metadata_issues(card.metadata, "metadata"))

    if not isinstance(card.tiers, tuple):
        errors.append(
            _make_issue("INVALID_TYPE", "tiers must be a tuple", field="tiers")
        )
        tier_items: tuple[object, ...] = ()
    else:
        tier_items = card.tiers

    required_values = frozenset(tier.value for tier in REQUIRED_RISK_TIERS)
    seen: set[str] = set()
    duplicates: set[str] = set()
    by_tier: dict[str, RiskTierDefinition] = {}

    for index, definition in enumerate(tier_items):
        field_prefix = f"tiers[{index}]"
        if not isinstance(definition, RiskTierDefinition):
            errors.append(
                _make_issue(
                    "INVALID_TYPE",
                    f"{field_prefix} must be a RiskTierDefinition",
                    field=field_prefix,
                )
            )
            continue

        tier_value = _enum_value(definition.tier)
        if tier_value not in _VALID_RISK_TIERS:
            errors.append(
                _make_issue(
                    "INVALID_TIER",
                    f"{field_prefix}.tier '{tier_value}' is invalid",
                    field=f"{field_prefix}.tier",
                )
            )
            continue
        if tier_value in seen:
            duplicates.add(tier_value)
        seen.add(tier_value)
        by_tier[tier_value] = definition

        if not isinstance(definition.label, str) or not definition.label.strip():
            errors.append(
                _make_issue(
                    "MISSING_REQUIRED",
                    f"{field_prefix}.label is required",
                    field=f"{field_prefix}.label",
                )
            )
        if not isinstance(definition.description, str) or not definition.description.strip():
            errors.append(
                _make_issue(
                    "MISSING_REQUIRED",
                    f"{field_prefix}.description is required",
                    field=f"{field_prefix}.description",
                )
            )

        if _enum_value(definition.reversibility) not in _VALID_REVERSIBILITY_LEVELS:
            errors.append(
                _make_issue(
                    "INVALID_ENUM",
                    f"{field_prefix}.reversibility is invalid",
                    field=f"{field_prefix}.reversibility",
                )
            )
        if _enum_value(definition.oversight) not in _VALID_OVERSIGHT_LEVELS:
            errors.append(
                _make_issue(
                    "INVALID_ENUM",
                    f"{field_prefix}.oversight is invalid",
                    field=f"{field_prefix}.oversight",
                )
            )
        if _enum_value(definition.evidence_expectation) not in _VALID_EVIDENCE_EXPECTATIONS:
            errors.append(
                _make_issue(
                    "INVALID_ENUM",
                    f"{field_prefix}.evidence_expectation is invalid",
                    field=f"{field_prefix}.evidence_expectation",
                )
            )

        for bool_field in (
            "default_requires_trace",
            "default_requires_evidence",
            "default_requires_approval",
            "default_requires_explicit_confirmation",
            "default_requires_sandbox",
            "default_allows_external_egress",
            "default_allows_memory_write",
            "default_allows_tool_write",
            "default_allows_execution",
        ):
            if not isinstance(getattr(definition, bool_field), bool):
                errors.append(
                    _make_issue(
                        "INVALID_TYPE",
                        f"{field_prefix}.{bool_field} must be boolean",
                        field=f"{field_prefix}.{bool_field}",
                    )
                )

    missing = required_values - seen
    if missing:
        errors.append(
            _make_issue(
                "MISSING_REQUIRED_TIER",
                f"missing required risk tier(s): {', '.join(sorted(missing))}",
                field="tiers",
            )
        )
    unknown = seen - required_values
    if unknown:
        errors.append(
            _make_issue(
                "UNKNOWN_TIER",
                f"unknown risk tier(s): {', '.join(sorted(unknown))}",
                field="tiers",
            )
        )
    if duplicates:
        errors.append(
            _make_issue(
                "DUPLICATE_TIER",
                f"duplicate risk tier definition(s): {', '.join(sorted(duplicates))}",
                field="tiers",
            )
        )

    r5 = by_tier.get(RiskTier.R5.value)
    if r5 is not None:
        if not r5.default_requires_trace:
            errors.append(_make_issue("R5_REQUIRES_TRACE", "R5 must require trace", "tiers.R5.default_requires_trace"))
        if not r5.default_requires_evidence:
            errors.append(_make_issue("R5_REQUIRES_EVIDENCE", "R5 must require evidence", "tiers.R5.default_requires_evidence"))
        if not r5.default_requires_approval:
            errors.append(_make_issue("R5_REQUIRES_APPROVAL", "R5 must require approval", "tiers.R5.default_requires_approval"))
        if not r5.default_requires_explicit_confirmation:
            errors.append(_make_issue(
                "R5_REQUIRES_EXPLICIT_CONFIRMATION",
                "R5 must require explicit Operator confirmation",
                "tiers.R5.default_requires_explicit_confirmation",
            ))
        if r5.oversight != OversightLevel.EXPLICIT_OPERATOR_CONFIRMATION:
            errors.append(_make_issue(
                "R5_OVERSIGHT_REQUIRED",
                "R5 oversight must be explicit_operator_confirmation",
                "tiers.R5.oversight",
            ))
        if r5.reversibility != ReversibilityLevel.IRREVERSIBLE:
            errors.append(_make_issue(
                "R5_REVERSIBILITY_REQUIRED",
                "R5 reversibility must be irreversible",
                "tiers.R5.reversibility",
            ))
        if r5.oversight == OversightLevel.NONE:
            errors.append(_make_issue(
                "INCONSISTENT_R5_OVERSIGHT",
                "R5 cannot use oversight none",
                "tiers.R5.oversight",
            ))

    r6 = by_tier.get(RiskTier.R6.value)
    if r6 is not None:
        if r6.oversight != OversightLevel.DENIED:
            errors.append(_make_issue(
                "R6_OVERSIGHT_DENIED",
                "R6 oversight must be denied",
                "tiers.R6.oversight",
            ))
        if r6.reversibility != ReversibilityLevel.DENIED:
            errors.append(_make_issue(
                "R6_REVERSIBILITY_DENIED",
                "R6 reversibility must be denied",
                "tiers.R6.reversibility",
            ))
        if r6.default_allows_execution:
            errors.append(_make_issue(
                "R6_CANNOT_ALLOW_EXECUTION",
                "R6 cannot allow execution",
                "tiers.R6.default_allows_execution",
            ))
        if r6.default_allows_external_egress:
            errors.append(_make_issue(
                "R6_CANNOT_ALLOW_EXTERNAL_EGRESS",
                "R6 cannot allow external egress",
                "tiers.R6.default_allows_external_egress",
            ))
        if r6.default_allows_memory_write:
            errors.append(_make_issue(
                "R6_CANNOT_ALLOW_MEMORY_WRITE",
                "R6 cannot allow memory write",
                "tiers.R6.default_allows_memory_write",
            ))
        if r6.default_allows_tool_write:
            errors.append(_make_issue(
                "R6_CANNOT_ALLOW_TOOL_WRITE",
                "R6 cannot allow tool write",
                "tiers.R6.default_allows_tool_write",
            ))
        if r6.reversibility == ReversibilityLevel.REVERSIBLE:
            errors.append(_make_issue(
                "INCONSISTENT_R6_REVERSIBILITY",
                "R6 cannot be reversible",
                "tiers.R6.reversibility",
            ))

    r4 = by_tier.get(RiskTier.R4.value)
    if r4 is not None and not r4.default_requires_approval:
        errors.append(_make_issue(
            "R4_REQUIRES_APPROVAL",
            "R4 must require approval",
            "tiers.R4.default_requires_approval",
        ))

    r1 = by_tier.get(RiskTier.R1.value)
    if r1 is not None and r1.default_allows_tool_write:
        errors.append(_make_issue(
            "R1_CANNOT_ALLOW_TOOL_WRITE",
            "R1 safe local read cannot allow tool write",
            "tiers.R1.default_allows_tool_write",
        ))

    if not isinstance(card.action_class_mappings, tuple):
        errors.append(
            _make_issue(
                "INVALID_TYPE",
                "action_class_mappings must be a tuple",
                field="action_class_mappings",
            )
        )
        mapping_items: tuple[object, ...] = ()
    else:
        mapping_items = card.action_class_mappings

    seen_actions: set[str] = set()
    duplicate_actions: set[str] = set()
    for index, mapping in enumerate(mapping_items):
        field_prefix = f"action_class_mappings[{index}]"
        if not isinstance(mapping, RiskActionClassMapping):
            errors.append(
                _make_issue(
                    "INVALID_TYPE",
                    f"{field_prefix} must be a RiskActionClassMapping",
                    field=field_prefix,
                )
            )
            continue
        action_value = _enum_value(mapping.action_class)
        tier_value = _enum_value(mapping.default_tier)
        if action_value not in _VALID_ACTION_CLASSES:
            errors.append(
                _make_issue(
                    "INVALID_ACTION_CLASS",
                    f"{field_prefix}.action_class '{action_value}' is invalid",
                    field=f"{field_prefix}.action_class",
                )
            )
        elif action_value in seen_actions:
            duplicate_actions.add(action_value)
        seen_actions.add(action_value or "")
        if tier_value not in _VALID_RISK_TIERS:
            errors.append(
                _make_issue(
                    "INVALID_TIER",
                    f"{field_prefix}.default_tier '{tier_value}' is invalid",
                    field=f"{field_prefix}.default_tier",
                )
            )
        if not isinstance(mapping.description, str):
            errors.append(
                _make_issue(
                    "INVALID_TYPE",
                    f"{field_prefix}.description must be a string",
                    field=f"{field_prefix}.description",
                )
            )

    if duplicate_actions:
        errors.append(
            _make_issue(
                "DUPLICATE_ACTION_CLASS_MAPPING",
                f"duplicate action class mapping(s): {', '.join(sorted(duplicate_actions))}",
                field="action_class_mappings",
            )
        )

    canonical_hash: str | None = None
    try:
        canonical_hash = compute_risk_tier_policy_card_hash(card)
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

    return RiskTierValidationResult(
        valid=len(errors) == 0,
        errors=tuple(errors),
        warnings=tuple(warnings),
        card_id=card_id,
        canonical_hash=canonical_hash,
    )


def load_risk_tier_policy_card_from_dict(
    data: Mapping[str, Any],
) -> RiskTierPolicyCard:
    from .risk_tier_schema import (
        RISK_TIER_DANGEROUS_FIELD_NAMES,
        RISK_TIER_DANGEROUS_METADATA_KEYS,
        RISK_TIER_OPTIONAL_FIELDS,
        RISK_TIER_REQUIRED_FIELDS,
        SUPPORTED_RISK_TIER_POLICY_CARD_SCHEMA_VERSIONS,
    )

    raw = _require_mapping(data, "risk tier policy card data")
    known_fields = frozenset(RISK_TIER_REQUIRED_FIELDS + RISK_TIER_OPTIONAL_FIELDS)
    _check_mapping_fields(
        raw,
        known_fields,
        RISK_TIER_DANGEROUS_FIELD_NAMES,
        "risk_tier_policy_card",
    )

    missing = frozenset(RISK_TIER_REQUIRED_FIELDS) - set(raw.keys())
    if missing:
        raise RiskTierPolicyCardValidationError(
            f"missing required field(s): {', '.join(sorted(missing))}"
        )

    schema_version = raw.get("schema_version")
    if (
        not isinstance(schema_version, str)
        or not schema_version.strip()
        or schema_version not in SUPPORTED_RISK_TIER_POLICY_CARD_SCHEMA_VERSIONS
    ):
        raise RiskTierPolicyCardValidationError(
            f"schema_version must be one of: "
            f"{', '.join(SUPPORTED_RISK_TIER_POLICY_CARD_SCHEMA_VERSIONS)}"
        )

    policy_card_raw = _require_mapping(raw.get("policy_card"), "policy_card")
    try:
        policy_card = load_policy_card_from_dict(dict(policy_card_raw))
    except PolicyCardError as exc:
        raise RiskTierPolicyCardValidationError(
            f"embedded policy_card invalid: {exc}"
        ) from exc

    tiers_raw = raw.get("tiers")
    if not isinstance(tiers_raw, (list, tuple)):
        raise RiskTierPolicyCardValidationError("tiers must be a list/tuple")
    tiers = tuple(
        _load_risk_tier_definition(_require_mapping(item, f"tiers[{index}]"), index)
        for index, item in enumerate(tiers_raw)
    )

    mappings_raw = raw.get("action_class_mappings", ())
    if not isinstance(mappings_raw, (list, tuple)):
        raise RiskTierPolicyCardValidationError(
            "action_class_mappings must be a list/tuple"
        )
    action_class_mappings = tuple(
        _load_action_class_mapping(
            _require_mapping(item, f"action_class_mappings[{index}]"),
            index,
        )
        for index, item in enumerate(mappings_raw)
    )

    metadata_raw = raw.get("metadata")
    if metadata_raw is None:
        metadata: dict[str, Any] = {}
    elif isinstance(metadata_raw, MappingABC):
        dangerous_meta = set(metadata_raw.keys()) & RISK_TIER_DANGEROUS_METADATA_KEYS
        if dangerous_meta:
            raise RiskTierPolicyCardUnsafeFieldError(
                f"dangerous metadata key(s): {', '.join(sorted(dangerous_meta))}"
            )
        metadata = dict(metadata_raw)
    else:
        raise RiskTierPolicyCardValidationError("metadata must be a mapping")

    card = RiskTierPolicyCard(
        policy_card=policy_card,
        schema_version=schema_version,
        tiers=tiers,
        action_class_mappings=action_class_mappings,
        metadata=metadata,
    )

    result = validate_risk_tier_policy_card(card)
    if not result.valid:
        messages = "; ".join(error.message for error in result.errors)
        raise RiskTierPolicyCardValidationError(f"validation failed: {messages}")

    return card


def validate_risk_tier_policy_card_dict(
    data: Mapping[str, Any],
) -> RiskTierValidationResult:
    try:
        card = load_risk_tier_policy_card_from_dict(data)
    except Exception as exc:
        card_id = None
        if isinstance(data, MappingABC):
            policy_card_raw = data.get("policy_card")
            if isinstance(policy_card_raw, MappingABC):
                identity = policy_card_raw.get("identity")
                if isinstance(identity, MappingABC):
                    raw_card_id = identity.get("card_id")
                    if isinstance(raw_card_id, str):
                        card_id = raw_card_id
        return RiskTierValidationResult(
            valid=False,
            errors=(
                _make_issue(
                    "INVALID_RISK_TIER_POLICY_CARD_DICT",
                    str(exc),
                    field=None,
                ),
            ),
            warnings=(),
            card_id=card_id,
            canonical_hash=None,
        )
    return validate_risk_tier_policy_card(card)


def create_default_risk_tier_policy_card() -> RiskTierPolicyCard:
    from .risk_tier_schema import (
        DEFAULT_RISK_ACTION_CLASS_MAPPINGS,
        DEFAULT_RISK_TIER_DEFINITIONS,
        RISK_TIER_POLICY_CARD_SCHEMA_VERSION,
    )

    policy_card = PolicyCard(
        schema_version="1.0",
        identity=PolicyCardIdentity(
            card_id="aurel-core-risk-tier-policy-v1",
            slug="aurel-core-risk-tier-policy",
            name="AurelCore Risk Tier Policy",
            version="1.0",
            namespace="aurel_core",
        ),
        kind=PolicyCardKind.RISK_TIER,
        status=PolicyCardStatus.ACTIVE,
        scope=PolicyCardScope(scope_type=PolicyCardScopeType.GLOBAL),
        description=(
            "Defines R0-R6 risk tier semantics for future policy resolution; "
            "does not classify, grant authority, or enforce runtime behavior."
        ),
    )
    return RiskTierPolicyCard(
        policy_card=policy_card,
        schema_version=RISK_TIER_POLICY_CARD_SCHEMA_VERSION,
        tiers=DEFAULT_RISK_TIER_DEFINITIONS,
        action_class_mappings=DEFAULT_RISK_ACTION_CLASS_MAPPINGS,
        metadata={"owner_note": "default risk tier policy"},
    )
