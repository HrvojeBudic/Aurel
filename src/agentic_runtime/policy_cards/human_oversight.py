"""Human Oversight Policy Card model (P1.6.4).

Defines human/operator oversight semantics for AurelCore policy cards.
Human oversight cards define what human involvement is required before,
during or after an action — approval, explicit confirmation, denial, etc.
They are declarative, deterministic, closed-world, and hash-ready.

Architectural law:
  - Human oversight cards do not grant authority.
  - Human oversight cards do not bypass risk tier policy.
  - Human oversight cards do not bypass behavioral contracts.
  - Human oversight cards do not approve actions by themselves.
  - Human oversight cards do not execute approval workflow.
  - Human oversight cards do not implement runtime pauses.
  - Human oversight cards remain compatible with generic PolicyCard(kind="human_oversight").
"""
from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping as MappingABC
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping, TypeVar

from .errors import (
    HumanOversightPolicyCardUnknownFieldError,
    HumanOversightPolicyCardUnsafeFieldError,
    HumanOversightPolicyCardValidationError,
    PolicyCardError,
)
from .models import (
    PolicyCard,
    PolicyCardIdentity,
    PolicyCardKind,
    PolicyCardScope,
    PolicyCardScopeType,
    PolicyCardStatus,
)
from .risk_tiers import RiskTier
from .serialization import policy_card_to_canonical_dict
from .validation import load_policy_card_from_dict, validate_policy_card


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class HumanOversightLevel(str, Enum):
    NONE = "none"
    NOTIFY_ONLY = "notify_only"
    REVIEW_RECOMMENDED = "review_recommended"
    APPROVAL_REQUIRED = "approval_required"
    EXPLICIT_CONFIRMATION_REQUIRED = "explicit_confirmation_required"
    DUAL_REVIEW_REQUIRED = "dual_review_required"
    GOVERNANCE_BOARD_REQUIRED = "governance_board_required"
    DENY = "deny"


class HumanOversightMode(str, Enum):
    NONE = "none"
    NOTIFICATION = "notification"
    REVIEW = "review"
    APPROVAL = "approval"
    EXPLICIT_CONFIRMATION = "explicit_confirmation"
    DUAL_REVIEW = "dual_review"
    GOVERNANCE_BOARD = "governance_board"
    DENY = "deny"


class HumanOversightTrigger(str, Enum):
    RISK_TIER_AT_OR_ABOVE = "risk_tier_at_or_above"
    MISSING_EVIDENCE = "missing_evidence"
    POLICY_CONFLICT = "policy_conflict"
    AUTHORITY_UNCERTAIN = "authority_uncertain"
    EXTERNAL_EGRESS = "external_egress"
    IRREVERSIBLE_ACTION = "irreversible_action"
    PROTECTED_PATH_WRITE = "protected_path_write"
    MEMORY_WRITE_HIGH_IMPACT = "memory_write_high_impact"
    MODEL_ROUTE_EXTERNAL = "model_route_external"
    BUSINESS_PROCESS_HIGH_IMPACT = "business_process_high_impact"
    SANDBOX_UNCERTAIN = "sandbox_uncertain"
    SOURCE_TRUST_LOW = "source_trust_low"
    DELEGATION_UNCERTAIN = "delegation_uncertain"


class HumanOversightAction(str, Enum):
    NOTIFY_OPERATOR = "notify_operator"
    REQUEST_REVIEW = "request_review"
    REQUEST_APPROVAL = "request_approval"
    REQUEST_EXPLICIT_CONFIRMATION = "request_explicit_confirmation"
    REQUEST_DUAL_REVIEW = "request_dual_review"
    REQUEST_GOVERNANCE_BOARD_REVIEW = "request_governance_board_review"
    DENY_ACTION = "deny_action"
    PAUSE_FOR_HUMAN = "pause_for_human"
    REQUIRE_ADDITIONAL_EVIDENCE = "require_additional_evidence"


class OversightEvidenceType(str, Enum):
    POLICY_DECISION = "policy_decision"
    RISK_TIER_DECISION = "risk_tier_decision"
    OPERATOR_APPROVAL_RECORD = "operator_approval_record"
    EXPLICIT_CONFIRMATION_RECORD = "explicit_confirmation_record"
    SHADOW_DIFF = "shadow_diff"
    STATE_DIFF = "state_diff"
    TRACE_EVENT = "trace_event"
    EVIDENCE_REF = "evidence_ref"
    OUTPUT_PASSPORT = "output_passport"
    SANDBOX_REPORT = "sandbox_report"
    SOURCE_REFERENCE = "source_reference"
    MODEL_CALL_SUMMARY = "model_call_summary"
    TOOL_RESULT = "tool_result"


# ---------------------------------------------------------------------------
# Valid value sets
# ---------------------------------------------------------------------------

_VALID_OVERSIGHT_LEVELS = frozenset(level.value for level in HumanOversightLevel)
_VALID_OVERSIGHT_MODES = frozenset(m.value for m in HumanOversightMode)
_VALID_OVERSIGHT_TRIGGERS = frozenset(t.value for t in HumanOversightTrigger)
_VALID_OVERSIGHT_ACTIONS = frozenset(a.value for a in HumanOversightAction)
_VALID_EVIDENCE_TYPES = frozenset(e.value for e in OversightEvidenceType)
_VALID_RISK_TIER_VALUES = frozenset(t.value for t in RiskTier)


# ---------------------------------------------------------------------------
# Dataclass models
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ConfirmationRequirement:
    requires_explicit_confirmation: bool
    confirmation_phrase_required: bool = False
    preview_required: bool = False
    shadow_diff_required: bool = False
    reason_required: bool = False
    evidence_required: bool = True
    operator_identity_required: bool = True
    expires_after_seconds: int | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.requires_explicit_confirmation, bool):
            raise HumanOversightPolicyCardValidationError(
                "requires_explicit_confirmation must be boolean"
            )
        if not isinstance(self.confirmation_phrase_required, bool):
            raise HumanOversightPolicyCardValidationError(
                "confirmation_phrase_required must be boolean"
            )
        if not isinstance(self.preview_required, bool):
            raise HumanOversightPolicyCardValidationError(
                "preview_required must be boolean"
            )
        if not isinstance(self.shadow_diff_required, bool):
            raise HumanOversightPolicyCardValidationError(
                "shadow_diff_required must be boolean"
            )
        if not isinstance(self.reason_required, bool):
            raise HumanOversightPolicyCardValidationError(
                "reason_required must be boolean"
            )
        if not isinstance(self.evidence_required, bool):
            raise HumanOversightPolicyCardValidationError(
                "evidence_required must be boolean"
            )
        if not isinstance(self.operator_identity_required, bool):
            raise HumanOversightPolicyCardValidationError(
                "operator_identity_required must be boolean"
            )
        if self.expires_after_seconds is not None and not isinstance(
            self.expires_after_seconds, int
        ):
            raise HumanOversightPolicyCardValidationError(
                "expires_after_seconds must be int or None"
            )
        if (
            self.expires_after_seconds is not None
            and self.expires_after_seconds <= 0
        ):
            raise HumanOversightPolicyCardValidationError(
                "expires_after_seconds must be positive"
            )


@dataclass(frozen=True)
class ReviewerRequirement:
    operator_required: bool = False
    required_reviewer_role: str | None = None
    delegated_reviewer_allowed: bool = False
    dual_review_required: bool = False
    governance_board_required: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.operator_required, bool):
            raise HumanOversightPolicyCardValidationError(
                "operator_required must be boolean"
            )
        if self.required_reviewer_role is not None and not isinstance(
            self.required_reviewer_role, str
        ):
            raise HumanOversightPolicyCardValidationError(
                "required_reviewer_role must be string or None"
            )
        if not isinstance(self.delegated_reviewer_allowed, bool):
            raise HumanOversightPolicyCardValidationError(
                "delegated_reviewer_allowed must be boolean"
            )
        if not isinstance(self.dual_review_required, bool):
            raise HumanOversightPolicyCardValidationError(
                "dual_review_required must be boolean"
            )
        if not isinstance(self.governance_board_required, bool):
            raise HumanOversightPolicyCardValidationError(
                "governance_board_required must be boolean"
            )


@dataclass(frozen=True)
class OversightEvidenceRequirement:
    evidence_type: OversightEvidenceType
    required: bool = True
    description: str = ""


@dataclass(frozen=True)
class RiskTierOversightMapping:
    risk_tier: RiskTier
    oversight_level: HumanOversightLevel
    oversight_mode: HumanOversightMode
    action: HumanOversightAction
    confirmation_requirement: ConfirmationRequirement | None = None
    reviewer_requirement: ReviewerRequirement | None = None
    evidence_requirements: tuple[OversightEvidenceRequirement, ...] = ()
    description: str = ""


@dataclass(frozen=True)
class HumanOversightEscalationRule:
    trigger: HumanOversightTrigger
    action: HumanOversightAction
    minimum_risk_tier: RiskTier | None = None
    description: str = ""


@dataclass(frozen=True)
class HumanOversightValidationIssue:
    code: str
    message: str
    field: str | None = None
    severity: str = "error"


@dataclass(frozen=True)
class HumanOversightValidationResult:
    valid: bool
    errors: tuple[HumanOversightValidationIssue, ...]
    warnings: tuple[HumanOversightValidationIssue, ...]
    card_id: str | None = None
    canonical_hash: str | None = None


@dataclass(frozen=True)
class HumanOversightPolicyCard:
    policy_card: PolicyCard
    schema_version: str
    risk_tier_mappings: tuple[RiskTierOversightMapping, ...]
    escalation_rules: tuple[HumanOversightEscalationRule, ...] = ()
    default_confirmation_requirement: ConfirmationRequirement | None = None
    default_reviewer_requirement: ReviewerRequirement | None = None
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
) -> HumanOversightValidationIssue:
    return HumanOversightValidationIssue(
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
        raise HumanOversightPolicyCardValidationError(
            f"{field_name} value {raw!r} must be one of: "
            f"{', '.join(sorted(valid_values))}"
        )
    return enum_type(raw)


def _require_bool(raw: object, field_name: str) -> bool:
    if not isinstance(raw, bool):
        raise HumanOversightPolicyCardValidationError(f"{field_name} must be boolean")
    return raw


def _require_mapping(raw: object, field_name: str) -> Mapping[str, Any]:
    if not isinstance(raw, MappingABC):
        raise HumanOversightPolicyCardValidationError(f"{field_name} must be a mapping")
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
        raise HumanOversightPolicyCardUnsafeFieldError(
            f"{field_name}: dangerous field(s): {', '.join(sorted(dangerous))}"
        )
    unknown = present - known_fields
    if unknown:
        raise HumanOversightPolicyCardUnknownFieldError(
            f"{field_name}: unknown field(s): {', '.join(sorted(unknown))} - closed-world"
        )


# ---------------------------------------------------------------------------
# Sub-object loaders
# ---------------------------------------------------------------------------


def _load_confirmation_requirement(
    raw: Mapping[str, Any],
    field_name: str,
) -> ConfirmationRequirement:
    from .human_oversight_schema import (
        HUMAN_OVERSIGHT_CONFIRMATION_REQUIRED_FIELDS,
        HUMAN_OVERSIGHT_DANGEROUS_FIELD_NAMES,
    )

    known_fields = frozenset(HUMAN_OVERSIGHT_CONFIRMATION_REQUIRED_FIELDS)
    _check_mapping_fields(
        raw, known_fields, HUMAN_OVERSIGHT_DANGEROUS_FIELD_NAMES, field_name
    )

    return ConfirmationRequirement(
        requires_explicit_confirmation=_require_bool(
            raw["requires_explicit_confirmation"],
            f"{field_name}.requires_explicit_confirmation",
        ),
        confirmation_phrase_required=_require_bool(
            raw.get("confirmation_phrase_required", False),
            f"{field_name}.confirmation_phrase_required",
        ),
        preview_required=_require_bool(
            raw.get("preview_required", False),
            f"{field_name}.preview_required",
        ),
        shadow_diff_required=_require_bool(
            raw.get("shadow_diff_required", False),
            f"{field_name}.shadow_diff_required",
        ),
        reason_required=_require_bool(
            raw.get("reason_required", False),
            f"{field_name}.reason_required",
        ),
        evidence_required=_require_bool(
            raw.get("evidence_required", True),
            f"{field_name}.evidence_required",
        ),
        operator_identity_required=_require_bool(
            raw.get("operator_identity_required", True),
            f"{field_name}.operator_identity_required",
        ),
        expires_after_seconds=raw.get("expires_after_seconds"),
    )


def _load_reviewer_requirement(
    raw: Mapping[str, Any],
    field_name: str,
) -> ReviewerRequirement:
    from .human_oversight_schema import (
        HUMAN_OVERSIGHT_DANGEROUS_FIELD_NAMES,
        HUMAN_OVERSIGHT_REVIEWER_REQUIRED_FIELDS,
    )

    known_fields = frozenset(HUMAN_OVERSIGHT_REVIEWER_REQUIRED_FIELDS)
    _check_mapping_fields(
        raw, known_fields, HUMAN_OVERSIGHT_DANGEROUS_FIELD_NAMES, field_name
    )

    return ReviewerRequirement(
        operator_required=_require_bool(
            raw.get("operator_required", False),
            f"{field_name}.operator_required",
        ),
        required_reviewer_role=raw.get("required_reviewer_role"),
        delegated_reviewer_allowed=_require_bool(
            raw.get("delegated_reviewer_allowed", False),
            f"{field_name}.delegated_reviewer_allowed",
        ),
        dual_review_required=_require_bool(
            raw.get("dual_review_required", False),
            f"{field_name}.dual_review_required",
        ),
        governance_board_required=_require_bool(
            raw.get("governance_board_required", False),
            f"{field_name}.governance_board_required",
        ),
    )


def _load_evidence_requirement(
    raw: Mapping[str, Any],
    field_name: str,
) -> OversightEvidenceRequirement:
    from .human_oversight_schema import (
        HUMAN_OVERSIGHT_DANGEROUS_FIELD_NAMES,
        HUMAN_OVERSIGHT_EVIDENCE_REQUIRED_FIELDS,
    )

    known_fields = frozenset(HUMAN_OVERSIGHT_EVIDENCE_REQUIRED_FIELDS)
    _check_mapping_fields(
        raw, known_fields, HUMAN_OVERSIGHT_DANGEROUS_FIELD_NAMES, field_name
    )

    return OversightEvidenceRequirement(
        evidence_type=_coerce_enum(
            raw["evidence_type"],
            OversightEvidenceType,
            _VALID_EVIDENCE_TYPES,
            f"{field_name}.evidence_type",
        ),
        required=_require_bool(
            raw.get("required", True),
            f"{field_name}.required",
        ),
        description=str(raw.get("description", "")),
    )


def _load_risk_tier_mapping(
    raw: Mapping[str, Any],
    index: int,
) -> RiskTierOversightMapping:
    from .human_oversight_schema import (
        HUMAN_OVERSIGHT_DANGEROUS_FIELD_NAMES,
        HUMAN_OVERSIGHT_MAPPING_OPTIONAL_FIELDS,
        HUMAN_OVERSIGHT_MAPPING_REQUIRED_FIELDS,
    )

    field_prefix = f"risk_tier_mappings[{index}]"
    known_fields = frozenset(
        HUMAN_OVERSIGHT_MAPPING_REQUIRED_FIELDS + HUMAN_OVERSIGHT_MAPPING_OPTIONAL_FIELDS
    )
    _check_mapping_fields(
        raw, known_fields, HUMAN_OVERSIGHT_DANGEROUS_FIELD_NAMES, field_prefix
    )

    missing = frozenset(HUMAN_OVERSIGHT_MAPPING_REQUIRED_FIELDS) - set(raw.keys())
    if missing:
        raise HumanOversightPolicyCardValidationError(
            f"{field_prefix}: missing required field(s): {', '.join(sorted(missing))}"
        )

    confirmation_raw = raw.get("confirmation_requirement")
    confirmation_requirement = None
    if confirmation_raw is not None:
        confirmation_requirement = _load_confirmation_requirement(
            _require_mapping(confirmation_raw, f"{field_prefix}.confirmation_requirement"),
            f"{field_prefix}.confirmation_requirement",
        )

    reviewer_raw = raw.get("reviewer_requirement")
    reviewer_requirement = None
    if reviewer_raw is not None:
        reviewer_requirement = _load_reviewer_requirement(
            _require_mapping(reviewer_raw, f"{field_prefix}.reviewer_requirement"),
            f"{field_prefix}.reviewer_requirement",
        )

    evidence_raw = raw.get("evidence_requirements", ())
    if not isinstance(evidence_raw, (list, tuple)):
        raise HumanOversightPolicyCardValidationError(
            f"{field_prefix}.evidence_requirements must be a list/tuple"
        )
    evidence_requirements = tuple(
        _load_evidence_requirement(
            _require_mapping(item, f"{field_prefix}.evidence_requirements[{i}]"),
            f"{field_prefix}.evidence_requirements[{i}]",
        )
        for i, item in enumerate(evidence_raw)
    )

    description = raw.get("description", "")
    if not isinstance(description, str):
        raise HumanOversightPolicyCardValidationError(
            f"{field_prefix}.description must be a string"
        )

    return RiskTierOversightMapping(
        risk_tier=_coerce_enum(
            raw["risk_tier"], RiskTier, _VALID_RISK_TIER_VALUES,
            f"{field_prefix}.risk_tier",
        ),
        oversight_level=_coerce_enum(
            raw["oversight_level"], HumanOversightLevel, _VALID_OVERSIGHT_LEVELS,
            f"{field_prefix}.oversight_level",
        ),
        oversight_mode=_coerce_enum(
            raw["oversight_mode"], HumanOversightMode, _VALID_OVERSIGHT_MODES,
            f"{field_prefix}.oversight_mode",
        ),
        action=_coerce_enum(
            raw["action"], HumanOversightAction, _VALID_OVERSIGHT_ACTIONS,
            f"{field_prefix}.action",
        ),
        confirmation_requirement=confirmation_requirement,
        reviewer_requirement=reviewer_requirement,
        evidence_requirements=evidence_requirements,
        description=description,
    )


def _load_escalation_rule(
    raw: Mapping[str, Any],
    index: int,
) -> HumanOversightEscalationRule:
    from .human_oversight_schema import (
        HUMAN_OVERSIGHT_DANGEROUS_FIELD_NAMES,
        HUMAN_OVERSIGHT_ESCALATION_RULE_OPTIONAL_FIELDS,
        HUMAN_OVERSIGHT_ESCALATION_RULE_REQUIRED_FIELDS,
    )

    field_prefix = f"escalation_rules[{index}]"
    known_fields = frozenset(
        HUMAN_OVERSIGHT_ESCALATION_RULE_REQUIRED_FIELDS
        + HUMAN_OVERSIGHT_ESCALATION_RULE_OPTIONAL_FIELDS
    )
    _check_mapping_fields(
        raw, known_fields, HUMAN_OVERSIGHT_DANGEROUS_FIELD_NAMES, field_prefix
    )

    missing = frozenset(HUMAN_OVERSIGHT_ESCALATION_RULE_REQUIRED_FIELDS) - set(raw.keys())
    if missing:
        raise HumanOversightPolicyCardValidationError(
            f"{field_prefix}: missing required field(s): {', '.join(sorted(missing))}"
        )

    minimum_tier_raw = raw.get("minimum_risk_tier")
    minimum_risk_tier = None
    if minimum_tier_raw is not None:
        minimum_risk_tier = _coerce_enum(
            minimum_tier_raw, RiskTier, _VALID_RISK_TIER_VALUES,
            f"{field_prefix}.minimum_risk_tier",
        )

    description = raw.get("description", "")
    if not isinstance(description, str):
        raise HumanOversightPolicyCardValidationError(
            f"{field_prefix}.description must be a string"
        )

    return HumanOversightEscalationRule(
        trigger=_coerce_enum(
            raw["trigger"], HumanOversightTrigger, _VALID_OVERSIGHT_TRIGGERS,
            f"{field_prefix}.trigger",
        ),
        action=_coerce_enum(
            raw["action"], HumanOversightAction, _VALID_OVERSIGHT_ACTIONS,
            f"{field_prefix}.action",
        ),
        minimum_risk_tier=minimum_risk_tier,
        description=description,
    )


def _metadata_issues(
    metadata: object,
    field_name: str,
) -> list[HumanOversightValidationIssue]:
    from .human_oversight_schema import HUMAN_OVERSIGHT_DANGEROUS_METADATA_KEYS

    issues: list[HumanOversightValidationIssue] = []
    if not isinstance(metadata, MappingABC):
        issues.append(
            _make_issue(
                "INVALID_TYPE",
                f"{field_name} must be a mapping",
                field=field_name,
            )
        )
        return issues

    dangerous = set(metadata.keys()) & HUMAN_OVERSIGHT_DANGEROUS_METADATA_KEYS
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


def _confirmation_to_canonical_dict(
    cr: ConfirmationRequirement,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "confirmation_phrase_required": cr.confirmation_phrase_required,
        "evidence_required": cr.evidence_required,
        "operator_identity_required": cr.operator_identity_required,
        "preview_required": cr.preview_required,
        "reason_required": cr.reason_required,
        "requires_explicit_confirmation": cr.requires_explicit_confirmation,
        "shadow_diff_required": cr.shadow_diff_required,
    }
    if cr.expires_after_seconds is not None:
        result["expires_after_seconds"] = cr.expires_after_seconds
    return result


def _reviewer_to_canonical_dict(
    rr: ReviewerRequirement,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "delegated_reviewer_allowed": rr.delegated_reviewer_allowed,
        "dual_review_required": rr.dual_review_required,
        "governance_board_required": rr.governance_board_required,
        "operator_required": rr.operator_required,
    }
    if rr.required_reviewer_role is not None:
        result["required_reviewer_role"] = rr.required_reviewer_role
    return result


def _evidence_to_canonical_dict(
    er: OversightEvidenceRequirement,
) -> dict[str, Any]:
    return {
        "description": er.description,
        "evidence_type": er.evidence_type.value,
        "required": er.required,
    }


def _mapping_to_canonical_dict(
    mapping: RiskTierOversightMapping,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "action": mapping.action.value,
        "description": mapping.description,
        "oversight_level": mapping.oversight_level.value,
        "oversight_mode": mapping.oversight_mode.value,
        "risk_tier": mapping.risk_tier.value,
    }
    if mapping.confirmation_requirement is not None:
        result["confirmation_requirement"] = _confirmation_to_canonical_dict(
            mapping.confirmation_requirement
        )
    if mapping.reviewer_requirement is not None:
        result["reviewer_requirement"] = _reviewer_to_canonical_dict(
            mapping.reviewer_requirement
        )
    if mapping.evidence_requirements:
        result["evidence_requirements"] = [
            _evidence_to_canonical_dict(e) for e in mapping.evidence_requirements
        ]
    return result


def _escalation_to_canonical_dict(
    rule: HumanOversightEscalationRule,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "action": rule.action.value,
        "description": rule.description,
        "trigger": rule.trigger.value,
    }
    if rule.minimum_risk_tier is not None:
        result["minimum_risk_tier"] = rule.minimum_risk_tier.value
    return result


# ---------------------------------------------------------------------------
# Public serialization / hash API
# ---------------------------------------------------------------------------


def human_oversight_policy_card_to_canonical_dict(
    card: HumanOversightPolicyCard,
) -> dict[str, Any]:
    mappings = sorted(
        (_mapping_to_canonical_dict(m) for m in card.risk_tier_mappings),
        key=lambda item: item["risk_tier"],
    )
    escalations = sorted(
        (_escalation_to_canonical_dict(r) for r in card.escalation_rules),
        key=lambda item: (item["trigger"], item["action"]),
    )

    canonical: dict[str, Any] = {
        "escalation_rules": escalations,
        "metadata": dict(sorted(dict(card.metadata).items(), key=lambda item: item[0])),
        "policy_card": policy_card_to_canonical_dict(card.policy_card),
        "risk_tier_mappings": mappings,
        "schema_version": card.schema_version,
    }

    if card.default_confirmation_requirement is not None:
        canonical["default_confirmation_requirement"] = _confirmation_to_canonical_dict(
            card.default_confirmation_requirement
        )
    if card.default_reviewer_requirement is not None:
        canonical["default_reviewer_requirement"] = _reviewer_to_canonical_dict(
            card.default_reviewer_requirement
        )

    return dict(sorted(canonical.items(), key=lambda item: item[0]))


def serialize_human_oversight_policy_card_canonical(
    card: HumanOversightPolicyCard,
) -> str:
    canonical = human_oversight_policy_card_to_canonical_dict(card)
    return json.dumps(canonical, sort_keys=True, separators=(",", ":"))


def compute_human_oversight_policy_card_hash(card: HumanOversightPolicyCard) -> str:
    canonical = serialize_human_oversight_policy_card_canonical(card)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def validate_human_oversight_policy_card(
    card: HumanOversightPolicyCard,
) -> HumanOversightValidationResult:
    from .human_oversight_schema import (
        REQUIRED_HUMAN_OVERSIGHT_RISK_TIERS,
        SUPPORTED_HUMAN_OVERSIGHT_POLICY_CARD_SCHEMA_VERSIONS,
    )

    errors: list[HumanOversightValidationIssue] = []
    warnings: list[HumanOversightValidationIssue] = []

    if not isinstance(card, HumanOversightPolicyCard):
        errors.append(
            _make_issue(
                "INVALID_TYPE",
                "card must be a HumanOversightPolicyCard",
                field="card",
            )
        )
        return HumanOversightValidationResult(False, tuple(errors), tuple(warnings))

    if (
        not isinstance(card.schema_version, str)
        or not card.schema_version.strip()
        or card.schema_version not in SUPPORTED_HUMAN_OVERSIGHT_POLICY_CARD_SCHEMA_VERSIONS
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
        if kind_value != PolicyCardKind.HUMAN_OVERSIGHT.value:
            errors.append(
                _make_issue(
                    "INVALID_POLICY_CARD_KIND",
                    "HumanOversightPolicyCard requires generic PolicyCard kind 'human_oversight'",
                    field="policy_card.kind",
                )
            )

    errors.extend(_metadata_issues(card.metadata, "metadata"))

    if not isinstance(card.risk_tier_mappings, tuple):
        errors.append(
            _make_issue("INVALID_TYPE", "risk_tier_mappings must be a tuple",
                         field="risk_tier_mappings")
        )
        mapping_items: tuple[object, ...] = ()
    else:
        mapping_items = card.risk_tier_mappings

    required_tier_values = frozenset(tier.value for tier in REQUIRED_HUMAN_OVERSIGHT_RISK_TIERS)
    seen: set[str] = set()
    duplicates: set[str] = set()
    by_tier: dict[str, RiskTierOversightMapping] = {}

    for index, mapping in enumerate(mapping_items):
        field_prefix = f"risk_tier_mappings[{index}]"
        if not isinstance(mapping, RiskTierOversightMapping):
            errors.append(
                _make_issue(
                    "INVALID_TYPE",
                    f"{field_prefix} must be a RiskTierOversightMapping",
                    field=field_prefix,
                )
            )
            continue

        tier_value = _enum_value(mapping.risk_tier)
        if tier_value not in _VALID_RISK_TIER_VALUES:
            errors.append(
                _make_issue(
                    "INVALID_TIER",
                    f"{field_prefix}.risk_tier '{tier_value}' is invalid",
                    field=f"{field_prefix}.risk_tier",
                )
            )
            continue
        if tier_value in seen:
            duplicates.add(tier_value)
        seen.add(tier_value)
        by_tier[tier_value] = mapping

        level_value = _enum_value(mapping.oversight_level)
        if level_value not in _VALID_OVERSIGHT_LEVELS:
            errors.append(
                _make_issue(
                    "INVALID_OVERSIGHT_LEVEL",
                    f"{field_prefix}.oversight_level '{level_value}' is invalid",
                    field=f"{field_prefix}.oversight_level",
                )
            )
        mode_value = _enum_value(mapping.oversight_mode)
        if mode_value not in _VALID_OVERSIGHT_MODES:
            errors.append(
                _make_issue(
                    "INVALID_OVERSIGHT_MODE",
                    f"{field_prefix}.oversight_mode '{mode_value}' is invalid",
                    field=f"{field_prefix}.oversight_mode",
                )
            )
        action_value = _enum_value(mapping.action)
        if action_value not in _VALID_OVERSIGHT_ACTIONS:
            errors.append(
                _make_issue(
                    "INVALID_OVERSIGHT_ACTION",
                    f"{field_prefix}.action '{action_value}' is invalid",
                    field=f"{field_prefix}.action",
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

        for ei, evidence in enumerate(mapping.evidence_requirements):
            if _enum_value(evidence.evidence_type) not in _VALID_EVIDENCE_TYPES:
                errors.append(
                    _make_issue(
                        "INVALID_EVIDENCE_TYPE",
                        f"{field_prefix}.evidence_requirements[{ei}].evidence_type is invalid",
                        field=f"{field_prefix}.evidence_requirements[{ei}].evidence_type",
                    )
                )

    missing = required_tier_values - seen
    if missing:
        errors.append(
            _make_issue(
                "MISSING_REQUIRED_TIER",
                f"missing required risk tier mapping(s): {', '.join(sorted(missing))}",
                field="risk_tier_mappings",
            )
        )
    unknown = seen - required_tier_values
    if unknown:
        errors.append(
            _make_issue(
                "UNKNOWN_TIER",
                f"unknown risk tier(s): {', '.join(sorted(unknown))}",
                field="risk_tier_mappings",
            )
        )
    if duplicates:
        errors.append(
            _make_issue(
                "DUPLICATE_TIER",
                f"duplicate risk tier mapping(s): {', '.join(sorted(duplicates))}",
                field="risk_tier_mappings",
            )
        )

    # R4 safety: must require approval or stricter
    r4 = by_tier.get(RiskTier.R4.value)
    if r4 is not None:
        r4_level = _enum_value(r4.oversight_level)
        if r4_level in (
            HumanOversightLevel.NONE.value,
            HumanOversightLevel.NOTIFY_ONLY.value,
            HumanOversightLevel.REVIEW_RECOMMENDED.value,
        ):
            errors.append(
                _make_issue(
                    "R4_REQUIRES_APPROVAL",
                    "R4 oversight_level must be approval_required or stricter",
                    "risk_tier_mappings.R4.oversight_level",
                )
            )
        r4_action = _enum_value(r4.action)
        if r4_action in (
            HumanOversightAction.NOTIFY_OPERATOR.value,
            HumanOversightAction.REQUEST_REVIEW.value,
        ):
            errors.append(
                _make_issue(
                    "R4_REQUIRES_APPROVAL_ACTION",
                    "R4 action must be request_approval or stricter",
                    "risk_tier_mappings.R4.action",
                )
            )

    # R5 safety: must require explicit operator confirmation
    r5 = by_tier.get(RiskTier.R5.value)
    if r5 is not None:
        r5_level = _enum_value(r5.oversight_level)
        if r5_level != HumanOversightLevel.EXPLICIT_CONFIRMATION_REQUIRED.value:
            errors.append(
                _make_issue(
                    "R5_REQUIRES_EXPLICIT_CONFIRMATION",
                    "R5 oversight_level must be explicit_confirmation_required",
                    "risk_tier_mappings.R5.oversight_level",
                )
            )
        r5_mode = _enum_value(r5.oversight_mode)
        if r5_mode != HumanOversightMode.EXPLICIT_CONFIRMATION.value:
            errors.append(
                _make_issue(
                    "R5_REQUIRES_EXPLICIT_CONFIRMATION_MODE",
                    "R5 oversight_mode must be explicit_confirmation",
                    "risk_tier_mappings.R5.oversight_mode",
                )
            )
        r5_action = _enum_value(r5.action)
        if r5_action != HumanOversightAction.REQUEST_EXPLICIT_CONFIRMATION.value:
            errors.append(
                _make_issue(
                    "R5_REQUIRES_EXPLICIT_CONFIRMATION_ACTION",
                    "R5 action must be request_explicit_confirmation",
                    "risk_tier_mappings.R5.action",
                )
            )

        if r5.confirmation_requirement is None:
            errors.append(
                _make_issue(
                    "R5_MISSING_CONFIRMATION_REQUIREMENT",
                    "R5 must have a confirmation_requirement",
                    "risk_tier_mappings.R5.confirmation_requirement",
                )
            )
        else:
            cr = r5.confirmation_requirement
            if not cr.requires_explicit_confirmation:
                errors.append(
                    _make_issue(
                        "R5_CONFIRMATION_MISSING",
                        "R5 confirmation_requirement.requires_explicit_confirmation must be true",
                        "risk_tier_mappings.R5.confirmation_requirement.requires_explicit_confirmation",
                    )
                )
            if not cr.preview_required:
                errors.append(
                    _make_issue(
                        "R5_PREVIEW_REQUIRED",
                        "R5 confirmation_requirement.preview_required must be true",
                        "risk_tier_mappings.R5.confirmation_requirement.preview_required",
                    )
                )
            if not cr.evidence_required:
                errors.append(
                    _make_issue(
                        "R5_EVIDENCE_REQUIRED",
                        "R5 confirmation_requirement.evidence_required must be true",
                        "risk_tier_mappings.R5.confirmation_requirement.evidence_required",
                    )
                )
            if not cr.operator_identity_required:
                errors.append(
                    _make_issue(
                        "R5_OPERATOR_IDENTITY_REQUIRED",
                        "R5 confirmation_requirement.operator_identity_required must be true",
                        "risk_tier_mappings.R5.confirmation_requirement.operator_identity_required",
                    )
                )

        if r5.reviewer_requirement is None:
            errors.append(
                _make_issue(
                    "R5_MISSING_REVIEWER_REQUIREMENT",
                    "R5 must have a reviewer_requirement",
                    "risk_tier_mappings.R5.reviewer_requirement",
                )
            )
        elif not r5.reviewer_requirement.operator_required:
            errors.append(
                _make_issue(
                    "R5_OPERATOR_REQUIRED",
                    "R5 reviewer_requirement.operator_required must be true",
                    "risk_tier_mappings.R5.reviewer_requirement.operator_required",
                )
            )

    # R6 safety: must deny
    r6 = by_tier.get(RiskTier.R6.value)
    if r6 is not None:
        r6_level = _enum_value(r6.oversight_level)
        if r6_level != HumanOversightLevel.DENY.value:
            errors.append(
                _make_issue(
                    "R6_MUST_DENY",
                    "R6 oversight_level must be deny",
                    "risk_tier_mappings.R6.oversight_level",
                )
            )
        r6_mode = _enum_value(r6.oversight_mode)
        if r6_mode != HumanOversightMode.DENY.value:
            errors.append(
                _make_issue(
                    "R6_MUST_DENY_MODE",
                    "R6 oversight_mode must be deny",
                    "risk_tier_mappings.R6.oversight_mode",
                )
            )
        r6_action = _enum_value(r6.action)
        if r6_action != HumanOversightAction.DENY_ACTION.value:
            errors.append(
                _make_issue(
                    "R6_MUST_DENY_ACTION",
                    "R6 action must be deny_action",
                    "risk_tier_mappings.R6.action",
                )
            )
        if r6_level in (
            HumanOversightLevel.APPROVAL_REQUIRED.value,
            HumanOversightLevel.EXPLICIT_CONFIRMATION_REQUIRED.value,
            HumanOversightLevel.DUAL_REVIEW_REQUIRED.value,
            HumanOversightLevel.GOVERNANCE_BOARD_REQUIRED.value,
            HumanOversightLevel.NOTIFY_ONLY.value,
            HumanOversightLevel.REVIEW_RECOMMENDED.value,
        ):
            errors.append(
                _make_issue(
                    "R6_CANNOT_BE_APPROVABLE",
                    "R6 cannot be approvable or confirmable; R6 is denied",
                    "risk_tier_mappings.R6.oversight_level",
                )
            )

    # Validate escalation rules
    if not isinstance(card.escalation_rules, tuple):
        errors.append(
            _make_issue(
                "INVALID_TYPE",
                "escalation_rules must be a tuple",
                field="escalation_rules",
            )
        )
    else:
        for index, rule in enumerate(card.escalation_rules):
            field_prefix = f"escalation_rules[{index}]"
            if not isinstance(rule, HumanOversightEscalationRule):
                errors.append(
                    _make_issue(
                        "INVALID_TYPE",
                        f"{field_prefix} must be a HumanOversightEscalationRule",
                        field=field_prefix,
                    )
                )
                continue
            if _enum_value(rule.trigger) not in _VALID_OVERSIGHT_TRIGGERS:
                errors.append(
                    _make_issue(
                        "INVALID_TRIGGER",
                        f"{field_prefix}.trigger is invalid",
                        field=f"{field_prefix}.trigger",
                    )
                )
            if _enum_value(rule.action) not in _VALID_OVERSIGHT_ACTIONS:
                errors.append(
                    _make_issue(
                        "INVALID_ESCALATION_ACTION",
                        f"{field_prefix}.action is invalid",
                        field=f"{field_prefix}.action",
                    )
                )
            if rule.minimum_risk_tier is not None:
                if _enum_value(rule.minimum_risk_tier) not in _VALID_RISK_TIER_VALUES:
                    errors.append(
                        _make_issue(
                            "INVALID_MINIMUM_RISK_TIER",
                            f"{field_prefix}.minimum_risk_tier is invalid",
                            field=f"{field_prefix}.minimum_risk_tier",
                        )
                    )

    canonical_hash: str | None = None
    try:
        canonical_hash = compute_human_oversight_policy_card_hash(card)
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

    return HumanOversightValidationResult(
        valid=len(errors) == 0,
        errors=tuple(errors),
        warnings=tuple(warnings),
        card_id=card_id,
        canonical_hash=canonical_hash,
    )


# ---------------------------------------------------------------------------
# Dict loader
# ---------------------------------------------------------------------------


def load_human_oversight_policy_card_from_dict(
    data: Mapping[str, Any],
) -> HumanOversightPolicyCard:
    from .human_oversight_schema import (
        HUMAN_OVERSIGHT_DANGEROUS_FIELD_NAMES,
        HUMAN_OVERSIGHT_DANGEROUS_METADATA_KEYS,
        HUMAN_OVERSIGHT_OPTIONAL_FIELDS,
        HUMAN_OVERSIGHT_REQUIRED_FIELDS,
        SUPPORTED_HUMAN_OVERSIGHT_POLICY_CARD_SCHEMA_VERSIONS,
    )

    raw = _require_mapping(data, "human oversight policy card data")
    known_fields = frozenset(HUMAN_OVERSIGHT_REQUIRED_FIELDS + HUMAN_OVERSIGHT_OPTIONAL_FIELDS)
    _check_mapping_fields(
        raw,
        known_fields,
        HUMAN_OVERSIGHT_DANGEROUS_FIELD_NAMES,
        "human_oversight_policy_card",
    )

    missing = frozenset(HUMAN_OVERSIGHT_REQUIRED_FIELDS) - set(raw.keys())
    if missing:
        raise HumanOversightPolicyCardValidationError(
            f"missing required field(s): {', '.join(sorted(missing))}"
        )

    schema_version = raw.get("schema_version")
    if (
        not isinstance(schema_version, str)
        or not schema_version.strip()
        or schema_version not in SUPPORTED_HUMAN_OVERSIGHT_POLICY_CARD_SCHEMA_VERSIONS
    ):
        raise HumanOversightPolicyCardValidationError(
            f"schema_version must be one of: "
            f"{', '.join(SUPPORTED_HUMAN_OVERSIGHT_POLICY_CARD_SCHEMA_VERSIONS)}"
        )

    policy_card_raw = _require_mapping(raw.get("policy_card"), "policy_card")
    try:
        policy_card = load_policy_card_from_dict(dict(policy_card_raw))
    except PolicyCardError as exc:
        raise HumanOversightPolicyCardValidationError(
            f"embedded policy_card invalid: {exc}"
        ) from exc

    mappings_raw = raw.get("risk_tier_mappings")
    if not isinstance(mappings_raw, (list, tuple)):
        raise HumanOversightPolicyCardValidationError(
            "risk_tier_mappings must be a list/tuple"
        )
    risk_tier_mappings = tuple(
        _load_risk_tier_mapping(
            _require_mapping(item, f"risk_tier_mappings[{index}]"), index
        )
        for index, item in enumerate(mappings_raw)
    )

    escalation_raw = raw.get("escalation_rules", ())
    if not isinstance(escalation_raw, (list, tuple)):
        raise HumanOversightPolicyCardValidationError(
            "escalation_rules must be a list/tuple"
        )
    escalation_rules = tuple(
        _load_escalation_rule(
            _require_mapping(item, f"escalation_rules[{index}]"), index
        )
        for index, item in enumerate(escalation_raw)
    )

    default_confirmation_requirement = None
    dc_raw = raw.get("default_confirmation_requirement")
    if dc_raw is not None:
        default_confirmation_requirement = _load_confirmation_requirement(
            _require_mapping(dc_raw, "default_confirmation_requirement"),
            "default_confirmation_requirement",
        )

    default_reviewer_requirement = None
    dr_raw = raw.get("default_reviewer_requirement")
    if dr_raw is not None:
        default_reviewer_requirement = _load_reviewer_requirement(
            _require_mapping(dr_raw, "default_reviewer_requirement"),
            "default_reviewer_requirement",
        )

    metadata_raw = raw.get("metadata")
    if metadata_raw is None:
        metadata: dict[str, Any] = {}
    elif isinstance(metadata_raw, MappingABC):
        dangerous_meta = set(metadata_raw.keys()) & HUMAN_OVERSIGHT_DANGEROUS_METADATA_KEYS
        if dangerous_meta:
            raise HumanOversightPolicyCardUnsafeFieldError(
                f"dangerous metadata key(s): {', '.join(sorted(dangerous_meta))}"
            )
        metadata = dict(metadata_raw)
    else:
        raise HumanOversightPolicyCardValidationError("metadata must be a mapping")

    card = HumanOversightPolicyCard(
        policy_card=policy_card,
        schema_version=schema_version,
        risk_tier_mappings=risk_tier_mappings,
        escalation_rules=escalation_rules,
        default_confirmation_requirement=default_confirmation_requirement,
        default_reviewer_requirement=default_reviewer_requirement,
        metadata=metadata,
    )

    result = validate_human_oversight_policy_card(card)
    if not result.valid:
        messages = "; ".join(error.message for error in result.errors)
        raise HumanOversightPolicyCardValidationError(f"validation failed: {messages}")

    return card


def validate_human_oversight_policy_card_dict(
    data: Mapping[str, Any],
) -> HumanOversightValidationResult:
    try:
        card = load_human_oversight_policy_card_from_dict(data)
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
        return HumanOversightValidationResult(
            valid=False,
            errors=(
                _make_issue(
                    "INVALID_HUMAN_OVERSIGHT_POLICY_CARD_DICT",
                    str(exc),
                    field=None,
                ),
            ),
            warnings=(),
            card_id=card_id,
            canonical_hash=None,
        )
    return validate_human_oversight_policy_card(card)


# ---------------------------------------------------------------------------
# Default factory
# ---------------------------------------------------------------------------


def create_default_human_oversight_policy_card() -> HumanOversightPolicyCard:
    from .human_oversight_schema import (
        DEFAULT_HUMAN_OVERSIGHT_ESCALATION_RULES,
        DEFAULT_RISK_TIER_OVERSIGHT_MAPPINGS,
        HUMAN_OVERSIGHT_POLICY_CARD_SCHEMA_VERSION,
    )

    policy_card = PolicyCard(
        schema_version="1.0",
        identity=PolicyCardIdentity(
            card_id="aurel-core-human-oversight-policy-v1",
            slug="aurel-core-human-oversight-policy",
            name="AurelCore Human Oversight Policy",
            version="1.0",
            namespace="aurel_core",
        ),
        kind=PolicyCardKind.HUMAN_OVERSIGHT,
        status=PolicyCardStatus.ACTIVE,
        scope=PolicyCardScope(scope_type=PolicyCardScopeType.GLOBAL),
        description=(
            "Defines human/operator oversight semantics for future oversight resolution; "
            "does not grant authority, approve actions, or execute approval workflow."
        ),
    )
    return HumanOversightPolicyCard(
        policy_card=policy_card,
        schema_version=HUMAN_OVERSIGHT_POLICY_CARD_SCHEMA_VERSION,
        risk_tier_mappings=DEFAULT_RISK_TIER_OVERSIGHT_MAPPINGS,
        escalation_rules=DEFAULT_HUMAN_OVERSIGHT_ESCALATION_RULES,
        metadata={"owner_note": "default human oversight policy"},
    )
