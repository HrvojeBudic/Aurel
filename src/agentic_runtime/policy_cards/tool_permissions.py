"""Tool Permission Policy Card model (P1.6.6).

Defines tool permission semantics for AurelCore policy cards. Tool permission
cards define which tools may be called, by whom, under which conditions, for
which data classes, and at which risk tier. They are declarative, deterministic,
closed-world, hash-ready, and deny-by-default.

Architectural law:
  - Tool permission cards do not grant authority.
  - Tool permission cards do not execute tools.
  - Tool permission cards do not enforce runtime permissions yet.
  - Tool permission cards do not resolve actual tool registry entries yet.
  - Tool permission cards do not perform path enforcement, network blocking,
    sandbox execution, or credential access.
  - Tool permission cards remain compatible with generic PolicyCard(kind="tool_permission").
  - Default posture is deny-by-default / least privilege.
  - Credential access must deny by default.
  - Shell command must require sandbox/approval/risk constraints.
  - External egress must deny or be strongly governed by default.
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
    ToolPermissionPolicyCardError,
    ToolPermissionPolicyCardUnknownFieldError,
    ToolPermissionPolicyCardUnsafeFieldError,
    ToolPermissionPolicyCardValidationError,
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
# Enums
# ---------------------------------------------------------------------------


class ToolCategory(str, Enum):
    FILESYSTEM = "filesystem"
    SHELL = "shell"
    NETWORK = "network"
    BROWSER = "browser"
    MODEL = "model"
    MEMORY = "memory"
    DATABASE = "database"
    CALENDAR = "calendar"
    EMAIL = "email"
    GITHUB = "github"
    DOCUMENT = "document"
    ARTIFACT = "artifact"
    SANDBOX = "sandbox"
    INTERNAL_RUNTIME = "internal_runtime"
    EXTERNAL_API = "external_api"
    BUSINESS_SYSTEM = "business_system"
    UNKNOWN = "unknown"


class ToolPermissionType(str, Enum):
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    DELETE = "delete"
    NETWORK = "network"
    EXTERNAL_EGRESS = "external_egress"
    MEMORY_READ = "memory_read"
    MEMORY_WRITE = "memory_write"
    MODEL_CALL = "model_call"
    SHELL_COMMAND = "shell_command"
    FILESYSTEM_ACCESS = "filesystem_access"
    ARTIFACT_CREATE = "artifact_create"
    ARTIFACT_EXPORT = "artifact_export"
    CREDENTIAL_ACCESS = "credential_access"
    CONFIGURATION_READ = "configuration_read"
    CONFIGURATION_WRITE = "configuration_write"
    CALENDAR_READ = "calendar_read"
    CALENDAR_WRITE = "calendar_write"
    EMAIL_READ = "email_read"
    EMAIL_SEND = "email_send"
    GITHUB_READ = "github_read"
    GITHUB_WRITE = "github_write"
    DATABASE_READ = "database_read"
    DATABASE_WRITE = "database_write"
    BROWSER_READ = "browser_read"
    BROWSER_ACTION = "browser_action"


class ToolPermissionDecision(str, Enum):
    ALLOW = "allow"
    DENY = "deny"
    APPROVAL_REQUIRED = "approval_required"
    EXPLICIT_CONFIRMATION_REQUIRED = "explicit_confirmation_required"
    SANDBOX_REQUIRED = "sandbox_required"
    READ_ONLY = "read_only"
    LOCAL_ONLY = "local_only"
    CONDITIONAL = "conditional"


class ToolScopeType(str, Enum):
    GLOBAL = "global"
    RUNTIME = "runtime"
    AGENT = "agent"
    WORKFLOW = "workflow"
    TOOL = "tool"
    PROJECT = "project"
    REPOSITORY = "repository"
    BUSINESS = "business"
    MEMORY = "memory"
    ARTIFACT = "artifact"
    SANDBOX = "sandbox"
    LOCAL_DEVICE = "local_device"


class ToolMatchMode(str, Enum):
    EXACT = "exact"
    CATEGORY = "category"
    NAMESPACE = "namespace"
    PROVIDER = "provider"
    PREFIX = "prefix"


# ---------------------------------------------------------------------------
# Valid value sets
# ---------------------------------------------------------------------------

_VALID_CATEGORIES = frozenset(c.value for c in ToolCategory)
_VALID_PERMISSION_TYPES = frozenset(p.value for p in ToolPermissionType)
_VALID_DECISIONS = frozenset(d.value for d in ToolPermissionDecision)
_VALID_SCOPE_TYPES = frozenset(s.value for s in ToolScopeType)
_VALID_MATCH_MODES = frozenset(m.value for m in ToolMatchMode)


# ---------------------------------------------------------------------------
# Dataclass models
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ToolIdentityMatcher:
    match_mode: ToolMatchMode
    tool_name: str | None = None
    tool_id: str | None = None
    tool_category: ToolCategory | None = None
    provider: str | None = None
    namespace: str | None = None


@dataclass(frozen=True)
class ToolPermissionCondition:
    condition_type: str
    value: str | bool | int | None = None
    description: str = ""


@dataclass(frozen=True)
class ToolPermissionRule:
    matcher: ToolIdentityMatcher
    permission_type: ToolPermissionType
    decision: ToolPermissionDecision
    risk_ceiling: str | None = None
    required_oversight: str | None = None
    allowed_data_classes: tuple[str, ...] = ()
    forbidden_data_classes: tuple[str, ...] = ()
    allowed_scopes: tuple[ToolScopeType, ...] = ()
    conditions: tuple[ToolPermissionCondition, ...] = ()
    sandbox_required: bool = False
    trace_required: bool = True
    evidence_required: bool = False
    description: str = ""


@dataclass(frozen=True)
class ToolPermissionValidationIssue:
    code: str
    message: str
    field: str | None = None
    severity: str = "error"


@dataclass(frozen=True)
class ToolPermissionValidationResult:
    valid: bool
    errors: tuple[ToolPermissionValidationIssue, ...]
    warnings: tuple[ToolPermissionValidationIssue, ...]
    card_id: str | None = None
    canonical_hash: str | None = None


@dataclass(frozen=True)
class ToolPermissionPolicyCard:
    policy_card: PolicyCard
    schema_version: str
    permission_rules: tuple[ToolPermissionRule, ...]
    default_decision: ToolPermissionDecision = ToolPermissionDecision.DENY
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
) -> ToolPermissionValidationIssue:
    return ToolPermissionValidationIssue(
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
        raise ToolPermissionPolicyCardValidationError(
            f"{field_name} value {raw!r} must be one of: "
            f"{', '.join(sorted(valid_values))}"
        )
    return enum_type(raw)


def _require_bool(raw: object, field_name: str) -> bool:
    if not isinstance(raw, bool):
        raise ToolPermissionPolicyCardValidationError(f"{field_name} must be boolean")
    return raw


def _require_mapping(raw: object, field_name: str) -> Mapping[str, Any]:
    if not isinstance(raw, MappingABC):
        raise ToolPermissionPolicyCardValidationError(f"{field_name} must be a mapping")
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
        raise ToolPermissionPolicyCardUnsafeFieldError(
            f"{field_name}: dangerous field(s): {', '.join(sorted(dangerous))}"
        )
    unknown = present - known_fields
    if unknown:
        raise ToolPermissionPolicyCardUnknownFieldError(
            f"{field_name}: unknown field(s): {', '.join(sorted(unknown))} - closed-world"
        )


# ---------------------------------------------------------------------------
# Sub-object loaders
# ---------------------------------------------------------------------------


def _load_matcher(
    raw: Mapping[str, Any],
    field_name: str,
) -> ToolIdentityMatcher:
    from .tool_permission_schema import (
        TOOL_IDENTITY_MATCHER_OPTIONAL_FIELDS,
        TOOL_IDENTITY_MATCHER_REQUIRED_FIELDS,
        TOOL_PERMISSION_DANGEROUS_FIELD_NAMES,
    )

    known_fields = frozenset(
        TOOL_IDENTITY_MATCHER_REQUIRED_FIELDS + TOOL_IDENTITY_MATCHER_OPTIONAL_FIELDS
    )
    _check_mapping_fields(
        raw, known_fields, TOOL_PERMISSION_DANGEROUS_FIELD_NAMES, field_name,
    )

    missing = frozenset(TOOL_IDENTITY_MATCHER_REQUIRED_FIELDS) - set(raw.keys())
    if missing:
        raise ToolPermissionPolicyCardValidationError(
            f"{field_name}: missing required field(s): {', '.join(sorted(missing))}"
        )

    tc_raw = raw.get("tool_category")
    tool_category = None
    if tc_raw is not None:
        tool_category = _coerce_enum(
            tc_raw, ToolCategory, _VALID_CATEGORIES, f"{field_name}.tool_category",
        )

    has_meaningful = bool(
        raw.get("tool_name") or raw.get("tool_id") or tc_raw
        or raw.get("provider") or raw.get("namespace")
    )
    if not has_meaningful:
        raise ToolPermissionPolicyCardValidationError(
            f"{field_name}: at least one matcher field (tool_name, tool_id, "
            f"tool_category, provider, namespace) must be present"
        )

    return ToolIdentityMatcher(
        match_mode=_coerce_enum(
            raw["match_mode"], ToolMatchMode, _VALID_MATCH_MODES,
            f"{field_name}.match_mode",
        ),
        tool_name=raw.get("tool_name"),
        tool_id=raw.get("tool_id"),
        tool_category=tool_category,
        provider=raw.get("provider"),
        namespace=raw.get("namespace"),
    )


def _load_condition(
    raw: Mapping[str, Any],
    field_name: str,
) -> ToolPermissionCondition:
    from .tool_permission_schema import (
        SAFE_CONDITION_TYPES,
        TOOL_PERMISSION_CONDITION_OPTIONAL_FIELDS,
        TOOL_PERMISSION_CONDITION_REQUIRED_FIELDS,
        TOOL_PERMISSION_DANGEROUS_FIELD_NAMES,
    )

    known_fields = frozenset(
        TOOL_PERMISSION_CONDITION_REQUIRED_FIELDS + TOOL_PERMISSION_CONDITION_OPTIONAL_FIELDS
    )
    _check_mapping_fields(
        raw, known_fields, TOOL_PERMISSION_DANGEROUS_FIELD_NAMES, field_name,
    )

    condition_type = raw["condition_type"]
    if not isinstance(condition_type, str) or condition_type not in SAFE_CONDITION_TYPES:
        raise ToolPermissionPolicyCardValidationError(
            f"{field_name}.condition_type '{condition_type}' is not a recognized condition type"
        )

    return ToolPermissionCondition(
        condition_type=condition_type,
        value=raw.get("value"),
        description=str(raw.get("description", "")),
    )


def _load_permission_rule(
    raw: Mapping[str, Any],
    index: int,
) -> ToolPermissionRule:
    from .tool_permission_schema import (
        TOOL_PERMISSION_DANGEROUS_FIELD_NAMES,
        TOOL_PERMISSION_RULE_OPTIONAL_FIELDS,
        TOOL_PERMISSION_RULE_REQUIRED_FIELDS,
    )

    field_prefix = f"permission_rules[{index}]"
    known_fields = frozenset(
        TOOL_PERMISSION_RULE_REQUIRED_FIELDS + TOOL_PERMISSION_RULE_OPTIONAL_FIELDS
    )
    _check_mapping_fields(
        raw, known_fields, TOOL_PERMISSION_DANGEROUS_FIELD_NAMES, field_prefix,
    )

    missing = frozenset(TOOL_PERMISSION_RULE_REQUIRED_FIELDS) - set(raw.keys())
    if missing:
        raise ToolPermissionPolicyCardValidationError(
            f"{field_prefix}: missing required field(s): {', '.join(sorted(missing))}"
        )

    matcher_raw = _require_mapping(raw["matcher"], f"{field_prefix}.matcher")
    matcher = _load_matcher(matcher_raw, f"{field_prefix}.matcher")

    scopes_raw = raw.get("allowed_scopes", ())
    if not isinstance(scopes_raw, (list, tuple)):
        raise ToolPermissionPolicyCardValidationError(
            f"{field_prefix}.allowed_scopes must be a list/tuple"
        )
    allowed_scopes = tuple(
        _coerce_enum(s, ToolScopeType, _VALID_SCOPE_TYPES, f"{field_prefix}.allowed_scopes[{i}]")
        for i, s in enumerate(scopes_raw)
    )

    conds_raw = raw.get("conditions", ())
    if not isinstance(conds_raw, (list, tuple)):
        raise ToolPermissionPolicyCardValidationError(
            f"{field_prefix}.conditions must be a list/tuple"
        )
    conditions = tuple(
        _load_condition(
            _require_mapping(item, f"{field_prefix}.conditions[{i}]"),
            f"{field_prefix}.conditions[{i}]",
        )
        for i, item in enumerate(conds_raw)
    )

    dcs_raw = raw.get("allowed_data_classes", ())
    if not isinstance(dcs_raw, (list, tuple)):
        raise ToolPermissionPolicyCardValidationError(
            f"{field_prefix}.allowed_data_classes must be a list/tuple"
        )
    allowed_data_classes = tuple(str(dc) for dc in dcs_raw)

    fdcs_raw = raw.get("forbidden_data_classes", ())
    if not isinstance(fdcs_raw, (list, tuple)):
        raise ToolPermissionPolicyCardValidationError(
            f"{field_prefix}.forbidden_data_classes must be a list/tuple"
        )
    forbidden_data_classes = tuple(str(dc) for dc in fdcs_raw)

    return ToolPermissionRule(
        matcher=matcher,
        permission_type=_coerce_enum(
            raw["permission_type"], ToolPermissionType, _VALID_PERMISSION_TYPES,
            f"{field_prefix}.permission_type",
        ),
        decision=_coerce_enum(
            raw["decision"], ToolPermissionDecision, _VALID_DECISIONS,
            f"{field_prefix}.decision",
        ),
        risk_ceiling=raw.get("risk_ceiling"),
        required_oversight=raw.get("required_oversight"),
        allowed_data_classes=allowed_data_classes,
        forbidden_data_classes=forbidden_data_classes,
        allowed_scopes=allowed_scopes,
        conditions=conditions,
        sandbox_required=_require_bool(
            raw.get("sandbox_required", False), f"{field_prefix}.sandbox_required",
        ),
        trace_required=_require_bool(
            raw.get("trace_required", True), f"{field_prefix}.trace_required",
        ),
        evidence_required=_require_bool(
            raw.get("evidence_required", False), f"{field_prefix}.evidence_required",
        ),
        description=str(raw.get("description", "")),
    )


def _metadata_issues(
    metadata: object,
    field_name: str,
) -> list[ToolPermissionValidationIssue]:
    from .tool_permission_schema import TOOL_PERMISSION_DANGEROUS_METADATA_KEYS

    issues: list[ToolPermissionValidationIssue] = []
    if not isinstance(metadata, MappingABC):
        issues.append(
            _make_issue("INVALID_TYPE", f"{field_name} must be a mapping", field=field_name)
        )
        return issues

    dangerous = set(metadata.keys()) & TOOL_PERMISSION_DANGEROUS_METADATA_KEYS
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


def _matcher_to_canonical_dict(m: ToolIdentityMatcher) -> dict[str, Any]:
    result: dict[str, Any] = {
        "match_mode": m.match_mode.value,
    }
    if m.tool_name is not None:
        result["tool_name"] = m.tool_name
    if m.tool_id is not None:
        result["tool_id"] = m.tool_id
    if m.tool_category is not None:
        result["tool_category"] = m.tool_category.value
    if m.provider is not None:
        result["provider"] = m.provider
    if m.namespace is not None:
        result["namespace"] = m.namespace
    return dict(sorted(result.items(), key=lambda i: i[0]))


def _condition_to_canonical_dict(c: ToolPermissionCondition) -> dict[str, Any]:
    result: dict[str, Any] = {
        "condition_type": c.condition_type,
        "description": c.description,
    }
    if c.value is not None:
        result["value"] = c.value
    return result


def _rule_to_canonical_dict(rule: ToolPermissionRule) -> dict[str, Any]:
    result: dict[str, Any] = {
        "decision": rule.decision.value,
        "description": rule.description,
        "evidence_required": rule.evidence_required,
        "matcher": _matcher_to_canonical_dict(rule.matcher),
        "permission_type": rule.permission_type.value,
        "sandbox_required": rule.sandbox_required,
        "trace_required": rule.trace_required,
    }
    if rule.risk_ceiling is not None:
        result["risk_ceiling"] = rule.risk_ceiling
    if rule.required_oversight is not None:
        result["required_oversight"] = rule.required_oversight
    if rule.allowed_data_classes:
        result["allowed_data_classes"] = list(rule.allowed_data_classes)
    if rule.forbidden_data_classes:
        result["forbidden_data_classes"] = list(rule.forbidden_data_classes)
    if rule.allowed_scopes:
        result["allowed_scopes"] = [s.value for s in rule.allowed_scopes]
    if rule.conditions:
        result["conditions"] = [_condition_to_canonical_dict(c) for c in rule.conditions]
    return dict(sorted(result.items(), key=lambda i: i[0]))


# ---------------------------------------------------------------------------
# Public serialization / hash API
# ---------------------------------------------------------------------------


def tool_permission_policy_card_to_canonical_dict(
    card: ToolPermissionPolicyCard,
) -> dict[str, Any]:
    rules = [
        _rule_to_canonical_dict(r) for r in card.permission_rules
    ]

    canonical: dict[str, Any] = {
        "default_decision": card.default_decision.value,
        "metadata": dict(sorted(dict(card.metadata).items(), key=lambda i: i[0])),
        "permission_rules": rules,
        "policy_card": policy_card_to_canonical_dict(card.policy_card),
        "schema_version": card.schema_version,
    }
    return dict(sorted(canonical.items(), key=lambda i: i[0]))


def serialize_tool_permission_policy_card_canonical(
    card: ToolPermissionPolicyCard,
) -> str:
    canonical = tool_permission_policy_card_to_canonical_dict(card)
    return json.dumps(canonical, sort_keys=True, separators=(",", ":"))


def compute_tool_permission_policy_card_hash(card: ToolPermissionPolicyCard) -> str:
    canonical = serialize_tool_permission_policy_card_canonical(card)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


PROTECTED_DATA_CLASSES: frozenset[str] = frozenset({
    "credentials",
    "operator_private",
    "sensitive_personal_data",
    "memory_record",
    "trace_record",
    "source_code",
})

EXTERNAL_PERMISSION_TYPES: frozenset[str] = frozenset({
    "external_egress",
    "network",
    "external_api",
    "model_call",
    "browser_action",
    "email_send",
    "github_write",
    "artifact_export",
})


def _check_dangerous_permission_safety(
    rule: ToolPermissionRule,
    field_prefix: str,
    errors: list[ToolPermissionValidationIssue],
) -> None:
    from .tool_permission_schema import (
        DANGEROUS_TOOL_PERMISSION_TYPES,
        HIGH_RISK_TOOL_PERMISSION_TYPES,
    )

    pt = rule.permission_type.value
    decision = rule.decision.value

    # Credential access must deny
    if pt == "credential_access":
        if decision != "deny":
            errors.append(_make_issue(
                "CREDENTIAL_ACCESS_NOT_DENIED",
                f"{field_prefix}: credential_access must be deny",
                field=f"{field_prefix}.decision",
            ))

    # Shell command cannot be simple allow
    if pt == "shell_command" and decision == "allow":
        if not rule.sandbox_required and not rule.risk_ceiling:
            errors.append(_make_issue(
                "SHELL_COMMAND_SIMPLE_ALLOW",
                f"{field_prefix}: shell_command cannot be simple allow without sandbox/risk constraints",
                field=f"{field_prefix}.decision",
            ))

    # Delete requires governance
    if pt == "delete" and decision == "allow":
        errors.append(_make_issue(
            "DELETE_SIMPLE_ALLOW",
            f"{field_prefix}: delete cannot be simple allow; requires approval or explicit confirmation",
            field=f"{field_prefix}.decision",
        ))

    # Config write requires governance
    if pt == "configuration_write" and decision == "allow":
        errors.append(_make_issue(
            "CONFIG_WRITE_SIMPLE_ALLOW",
            f"{field_prefix}: configuration_write cannot be simple allow; requires approval",
            field=f"{field_prefix}.decision",
        ))

    # Network/external egress cannot be simple allow
    if pt in ("network", "external_egress") and decision == "allow":
        errors.append(_make_issue(
            "NETWORK_SIMPLE_ALLOW",
            f"{field_prefix}: {pt} cannot be simple allow; requires governance",
            field=f"{field_prefix}.decision",
        ))

    # Dangerous permission types without risk ceiling / oversight
    if pt in DANGEROUS_TOOL_PERMISSION_TYPES and decision == "allow":
        if not rule.risk_ceiling and not rule.required_oversight:
            errors.append(_make_issue(
                "DANGEROUS_PERMISSION_ALLOW_NO_GOVERNANCE",
                f"{field_prefix}: dangerous permission {pt} allowed without risk_ceiling or required_oversight",
                field=f"{field_prefix}.risk_ceiling",
            ))
        if not rule.trace_required:
            errors.append(_make_issue(
                "DANGEROUS_PERMISSION_NO_TRACE",
                f"{field_prefix}: dangerous permission {pt} must require trace",
                field=f"{field_prefix}.trace_required",
            ))


def _check_data_residency_compatibility(
    rule: ToolPermissionRule,
    field_prefix: str,
    errors: list[ToolPermissionValidationIssue],
) -> None:
    pt = rule.permission_type.value
    decision = rule.decision.value

    if decision == "deny":
        return

    # Check if this rule allows external exposure of protected data classes
    is_external_perm = pt in EXTERNAL_PERMISSION_TYPES
    if not is_external_perm:
        return

    exposed_protected = set(rule.allowed_data_classes) & PROTECTED_DATA_CLASSES
    if exposed_protected:
        errors.append(_make_issue(
            "PROTECTED_DATA_EXPOSED_EXTERNALLY",
            f"{field_prefix}: protected data class(es) {', '.join(sorted(exposed_protected))} "
            f"cannot be exposed through external permission type '{pt}'",
            field=f"{field_prefix}.allowed_data_classes",
        ))

    # Also check if forbidden_data_classes doesn't guard protected classes
    if rule.allowed_data_classes:
        missing_forbid = PROTECTED_DATA_CLASSES - set(rule.forbidden_data_classes)
        if missing_forbid:
            errors.append(_make_issue(
                "PROTECTED_DATA_NOT_FORBIDDEN",
                f"{field_prefix}: protected data class(es) {', '.join(sorted(missing_forbid))} "
                "not in forbidden_data_classes for external permission",
                field=f"{field_prefix}.forbidden_data_classes",
            ))


def validate_tool_permission_policy_card(
    card: ToolPermissionPolicyCard,
) -> ToolPermissionValidationResult:
    from .tool_permission_schema import (
        DEFAULT_DENY_TOOL_CATEGORIES,
        SUPPORTED_TOOL_PERMISSION_POLICY_CARD_SCHEMA_VERSIONS,
    )

    errors: list[ToolPermissionValidationIssue] = []
    warnings: list[ToolPermissionValidationIssue] = []

    if not isinstance(card, ToolPermissionPolicyCard):
        errors.append(
            _make_issue("INVALID_TYPE", "card must be a ToolPermissionPolicyCard", field="card")
        )
        return ToolPermissionValidationResult(False, tuple(errors), tuple(warnings))

    if (
        not isinstance(card.schema_version, str)
        or not card.schema_version.strip()
        or card.schema_version not in SUPPORTED_TOOL_PERMISSION_POLICY_CARD_SCHEMA_VERSIONS
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
        if kind_value != PolicyCardKind.TOOL_PERMISSION.value:
            errors.append(
                _make_issue(
                    "INVALID_POLICY_CARD_KIND",
                    "ToolPermissionPolicyCard requires generic PolicyCard kind 'tool_permission'",
                    field="policy_card.kind",
                )
            )

    decision_value = _enum_value(card.default_decision)
    if decision_value not in _VALID_DECISIONS:
        errors.append(
            _make_issue("INVALID_DEFAULT_DECISION", "default_decision is invalid",
                        field="default_decision")
        )
    elif decision_value in ("allow", "conditional"):
        errors.append(
            _make_issue(
                "PERMISSIVE_DEFAULT_DECISION",
                f"default_decision must be deny-by-default, not '{decision_value}'",
                field="default_decision",
            )
        )

    errors.extend(_metadata_issues(card.metadata, "metadata"))

    if not isinstance(card.permission_rules, tuple):
        errors.append(
            _make_issue("INVALID_TYPE", "permission_rules must be a tuple",
                        field="permission_rules")
        )
        rule_items: tuple[object, ...] = ()
    else:
        rule_items = card.permission_rules

    for index, rule in enumerate(rule_items):
        field_prefix = f"permission_rules[{index}]"
        if not isinstance(rule, ToolPermissionRule):
            errors.append(
                _make_issue("INVALID_TYPE", f"{field_prefix} must be a ToolPermissionRule",
                            field=field_prefix)
            )
            continue

        cat = _enum_value(rule.matcher.tool_category)
        if cat is not None and cat not in _VALID_CATEGORIES:
            errors.append(_make_issue(
                "INVALID_TOOL_CATEGORY",
                f"{field_prefix}.matcher.tool_category '{cat}' is invalid",
                field=f"{field_prefix}.matcher.tool_category",
            ))

        pt = _enum_value(rule.permission_type)
        if pt not in _VALID_PERMISSION_TYPES:
            errors.append(_make_issue(
                "INVALID_PERMISSION_TYPE",
                f"{field_prefix}.permission_type '{pt}' is invalid",
                field=f"{field_prefix}.permission_type",
            ))

        dec = _enum_value(rule.decision)
        if dec not in _VALID_DECISIONS:
            errors.append(_make_issue(
                "INVALID_DECISION",
                f"{field_prefix}.decision '{dec}' is invalid",
                field=f"{field_prefix}.decision",
            ))

        if cat is not None and dec is not None:
            if cat in DEFAULT_DENY_TOOL_CATEGORIES and dec != "deny":
                errors.append(_make_issue(
                    "UNKNOWN_CATEGORY_NOT_DENIED",
                    f"{field_prefix}: unknown tool category must be deny, not '{dec}'",
                    field=f"{field_prefix}.decision",
                ))

        # Broad allow-all detection
        if (
            rule.matcher.match_mode == ToolMatchMode.CATEGORY
            and rule.matcher.tool_category is None
            and rule.matcher.tool_name is None
            and rule.matcher.tool_id is None
            and rule.matcher.provider is None
            and dec == "allow"
        ):
            errors.append(_make_issue(
                "BROAD_ALLOW_ALL_MATCHER",
                f"{field_prefix}: broad allow-all matcher rejected — "
                "category match with allow requires explicit category",
                field=f"{field_prefix}.matcher",
            ))

        _check_dangerous_permission_safety(rule, field_prefix, errors)
        _check_data_residency_compatibility(rule, field_prefix, errors)

    canonical_hash: str | None = None
    try:
        canonical_hash = compute_tool_permission_policy_card_hash(card)
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

    return ToolPermissionValidationResult(
        valid=len(errors) == 0,
        errors=tuple(errors),
        warnings=tuple(warnings),
        card_id=card_id,
        canonical_hash=canonical_hash,
    )


# ---------------------------------------------------------------------------
# Dict loader
# ---------------------------------------------------------------------------


def load_tool_permission_policy_card_from_dict(
    data: Mapping[str, Any],
) -> ToolPermissionPolicyCard:
    from .tool_permission_schema import (
        SUPPORTED_TOOL_PERMISSION_POLICY_CARD_SCHEMA_VERSIONS,
        TOOL_PERMISSION_DANGEROUS_FIELD_NAMES,
        TOOL_PERMISSION_DANGEROUS_METADATA_KEYS,
        TOOL_PERMISSION_OPTIONAL_FIELDS,
        TOOL_PERMISSION_REQUIRED_FIELDS,
    )

    raw = _require_mapping(data, "tool permission policy card data")
    known_fields = frozenset(TOOL_PERMISSION_REQUIRED_FIELDS + TOOL_PERMISSION_OPTIONAL_FIELDS)
    _check_mapping_fields(
        raw, known_fields, TOOL_PERMISSION_DANGEROUS_FIELD_NAMES,
        "tool_permission_policy_card",
    )

    missing = frozenset(TOOL_PERMISSION_REQUIRED_FIELDS) - set(raw.keys())
    if missing:
        raise ToolPermissionPolicyCardValidationError(
            f"missing required field(s): {', '.join(sorted(missing))}"
        )

    schema_version = raw.get("schema_version")
    if (
        not isinstance(schema_version, str)
        or not schema_version.strip()
        or schema_version not in SUPPORTED_TOOL_PERMISSION_POLICY_CARD_SCHEMA_VERSIONS
    ):
        raise ToolPermissionPolicyCardValidationError(
            f"schema_version must be one of: "
            f"{', '.join(SUPPORTED_TOOL_PERMISSION_POLICY_CARD_SCHEMA_VERSIONS)}"
        )

    policy_card_raw = _require_mapping(raw.get("policy_card"), "policy_card")
    try:
        policy_card = load_policy_card_from_dict(dict(policy_card_raw))
    except PolicyCardError as exc:
        raise ToolPermissionPolicyCardValidationError(
            f"embedded policy_card invalid: {exc}"
        ) from exc

    rules_raw = raw.get("permission_rules")
    if not isinstance(rules_raw, (list, tuple)):
        raise ToolPermissionPolicyCardValidationError("permission_rules must be a list/tuple")
    permission_rules = tuple(
        _load_permission_rule(
            _require_mapping(item, f"permission_rules[{index}]"), index,
        )
        for index, item in enumerate(rules_raw)
    )

    dd_raw = raw.get("default_decision", "deny")
    if isinstance(dd_raw, str) and dd_raw in _VALID_DECISIONS:
        default_decision = ToolPermissionDecision(dd_raw)
    else:
        raise ToolPermissionPolicyCardValidationError(
            f"default_decision must be one of: {', '.join(sorted(_VALID_DECISIONS))}"
        )

    metadata_raw = raw.get("metadata")
    if metadata_raw is None:
        metadata: dict[str, Any] = {}
    elif isinstance(metadata_raw, MappingABC):
        dangerous_meta = set(metadata_raw.keys()) & TOOL_PERMISSION_DANGEROUS_METADATA_KEYS
        if dangerous_meta:
            raise ToolPermissionPolicyCardUnsafeFieldError(
                f"dangerous metadata key(s): {', '.join(sorted(dangerous_meta))}"
            )
        metadata = dict(metadata_raw)
    else:
        raise ToolPermissionPolicyCardValidationError("metadata must be a mapping")

    card = ToolPermissionPolicyCard(
        policy_card=policy_card,
        schema_version=schema_version,
        permission_rules=permission_rules,
        default_decision=default_decision,
        metadata=metadata,
    )

    result = validate_tool_permission_policy_card(card)
    if not result.valid:
        messages = "; ".join(e.message for e in result.errors)
        raise ToolPermissionPolicyCardValidationError(f"validation failed: {messages}")

    return card


def validate_tool_permission_policy_card_dict(
    data: Mapping[str, Any],
) -> ToolPermissionValidationResult:
    try:
        card = load_tool_permission_policy_card_from_dict(data)
    except ToolPermissionPolicyCardError as exc:
        card_id = None
        if isinstance(data, MappingABC):
            policy_card_raw = data.get("policy_card")
            if isinstance(policy_card_raw, MappingABC):
                identity = policy_card_raw.get("identity")
                if isinstance(identity, MappingABC):
                    raw_card_id = identity.get("card_id")
                    if isinstance(raw_card_id, str):
                        card_id = raw_card_id
        return ToolPermissionValidationResult(
            valid=False,
            errors=(
                _make_issue("INVALID_DATA_TOOL_PERMISSION_POLICY_CARD_DICT", str(exc), field=None),
            ),
            warnings=(),
            card_id=card_id,
            canonical_hash=None,
        )
    return validate_tool_permission_policy_card(card)


# ---------------------------------------------------------------------------
# Default factory
# ---------------------------------------------------------------------------


def create_default_tool_permission_policy_card() -> ToolPermissionPolicyCard:
    from .tool_permission_schema import TOOL_PERMISSION_POLICY_CARD_SCHEMA_VERSION

    policy_card = PolicyCard(
        schema_version="1.0",
        identity=PolicyCardIdentity(
            card_id="aurel-core-tool-permission-policy-v1",
            slug="aurel-core-tool-permission-policy",
            name="AurelCore Tool Permission Policy",
            version="1.0",
            namespace="aurel_core",
        ),
        kind=PolicyCardKind.TOOL_PERMISSION,
        status=PolicyCardStatus.ACTIVE,
        scope=PolicyCardScope(scope_type=PolicyCardScopeType.GLOBAL),
        description=(
            "Defines strict deny-by-default tool permission semantics for AurelCore; "
            "does not enforce permissions, execute tools, block networks, or run sandbox at runtime."
        ),
    )

    rules: tuple[ToolPermissionRule, ...] = (
        # Unknown category — must deny
        ToolPermissionRule(
            matcher=ToolIdentityMatcher(
                match_mode=ToolMatchMode.CATEGORY,
                tool_category=ToolCategory.UNKNOWN,
            ),
            permission_type=ToolPermissionType.EXECUTE,
            decision=ToolPermissionDecision.DENY,
            description="Unknown tool categories must deny by default.",
        ),
        # Credential access — must deny
        ToolPermissionRule(
            matcher=ToolIdentityMatcher(
                match_mode=ToolMatchMode.CATEGORY,
                tool_category=ToolCategory.INTERNAL_RUNTIME,
            ),
            permission_type=ToolPermissionType.CREDENTIAL_ACCESS,
            decision=ToolPermissionDecision.DENY,
            description="Credential access denied by default.",
        ),
        # Shell command — sandbox required
        ToolPermissionRule(
            matcher=ToolIdentityMatcher(
                match_mode=ToolMatchMode.CATEGORY,
                tool_category=ToolCategory.SHELL,
            ),
            permission_type=ToolPermissionType.SHELL_COMMAND,
            decision=ToolPermissionDecision.SANDBOX_REQUIRED,
            risk_ceiling="R3",
            required_oversight="approval_required",
            sandbox_required=True,
            trace_required=True,
            evidence_required=True,
            forbidden_data_classes=(
                "credentials", "sensitive_personal_data",
            ),
            description="Shell commands require sandbox and approval.",
        ),
        # External egress — deny by default
        ToolPermissionRule(
            matcher=ToolIdentityMatcher(
                match_mode=ToolMatchMode.CATEGORY,
                tool_category=ToolCategory.NETWORK,
            ),
            permission_type=ToolPermissionType.EXTERNAL_EGRESS,
            decision=ToolPermissionDecision.DENY,
            description="External egress denied by default.",
        ),
        # External API — governed
        ToolPermissionRule(
            matcher=ToolIdentityMatcher(
                match_mode=ToolMatchMode.CATEGORY,
                tool_category=ToolCategory.EXTERNAL_API,
            ),
            permission_type=ToolPermissionType.EXTERNAL_EGRESS,
            decision=ToolPermissionDecision.APPROVAL_REQUIRED,
            risk_ceiling="R3",
            required_oversight="approval_required",
            trace_required=True,
            evidence_required=True,
            forbidden_data_classes=(
                "credentials", "operator_private", "sensitive_personal_data",
                "memory_record", "trace_record", "source_code",
            ),
            description="External API access requires approval and data residency compliance.",
        ),
        # Filesystem read — read_only
        ToolPermissionRule(
            matcher=ToolIdentityMatcher(
                match_mode=ToolMatchMode.CATEGORY,
                tool_category=ToolCategory.FILESYSTEM,
            ),
            permission_type=ToolPermissionType.FILESYSTEM_ACCESS,
            decision=ToolPermissionDecision.READ_ONLY,
            trace_required=True,
            description="Filesystem access is read-only by default.",
        ),
        # Filesystem write — conditional
        ToolPermissionRule(
            matcher=ToolIdentityMatcher(
                match_mode=ToolMatchMode.CATEGORY,
                tool_category=ToolCategory.FILESYSTEM,
            ),
            permission_type=ToolPermissionType.WRITE,
            decision=ToolPermissionDecision.APPROVAL_REQUIRED,
            risk_ceiling="R3",
            trace_required=True,
            description="Filesystem write requires approval.",
        ),
        # Filesystem delete — approval required
        ToolPermissionRule(
            matcher=ToolIdentityMatcher(
                match_mode=ToolMatchMode.CATEGORY,
                tool_category=ToolCategory.FILESYSTEM,
            ),
            permission_type=ToolPermissionType.DELETE,
            decision=ToolPermissionDecision.APPROVAL_REQUIRED,
            risk_ceiling="R4",
            trace_required=True,
            evidence_required=True,
            description="Filesystem delete requires approval.",
        ),
        # Memory write — governed
        ToolPermissionRule(
            matcher=ToolIdentityMatcher(
                match_mode=ToolMatchMode.CATEGORY,
                tool_category=ToolCategory.MEMORY,
            ),
            permission_type=ToolPermissionType.MEMORY_WRITE,
            decision=ToolPermissionDecision.APPROVAL_REQUIRED,
            risk_ceiling="R3",
            trace_required=True,
            evidence_required=True,
            forbidden_data_classes=(
                "credentials", "sensitive_personal_data",
            ),
            description="Memory write requires approval.",
        ),
        # Memory read — read_only
        ToolPermissionRule(
            matcher=ToolIdentityMatcher(
                match_mode=ToolMatchMode.CATEGORY,
                tool_category=ToolCategory.MEMORY,
            ),
            permission_type=ToolPermissionType.MEMORY_READ,
            decision=ToolPermissionDecision.READ_ONLY,
            trace_required=True,
            forbidden_data_classes=(
                "credentials", "sensitive_personal_data",
            ),
            description="Memory read is read-only by default.",
        ),
        # Model call — local model allowed, external governed
        ToolPermissionRule(
            matcher=ToolIdentityMatcher(
                match_mode=ToolMatchMode.CATEGORY,
                tool_category=ToolCategory.MODEL,
            ),
            permission_type=ToolPermissionType.MODEL_CALL,
            decision=ToolPermissionDecision.LOCAL_ONLY,
            trace_required=True,
            forbidden_data_classes=(
                "credentials", "sensitive_personal_data", "memory_record",
            ),
            description="Local model calls allowed; external requires approval.",
        ),
        # Email send — explicit confirmation
        ToolPermissionRule(
            matcher=ToolIdentityMatcher(
                match_mode=ToolMatchMode.CATEGORY,
                tool_category=ToolCategory.EMAIL,
            ),
            permission_type=ToolPermissionType.EMAIL_SEND,
            decision=ToolPermissionDecision.EXPLICIT_CONFIRMATION_REQUIRED,
            risk_ceiling="R5",
            trace_required=True,
            evidence_required=True,
            forbidden_data_classes=(
                "credentials", "sensitive_personal_data",
            ),
            description="Email send requires explicit operator confirmation.",
        ),
        # Artifact export — governed
        ToolPermissionRule(
            matcher=ToolIdentityMatcher(
                match_mode=ToolMatchMode.CATEGORY,
                tool_category=ToolCategory.ARTIFACT,
            ),
            permission_type=ToolPermissionType.ARTIFACT_EXPORT,
            decision=ToolPermissionDecision.APPROVAL_REQUIRED,
            risk_ceiling="R3",
            trace_required=True,
            forbidden_data_classes=(
                "credentials", "operator_private", "sensitive_personal_data",
                "memory_record", "trace_record",
            ),
            description="Artifact export requires approval and data residency compliance.",
        ),
        # Configuration write — approval required
        ToolPermissionRule(
            matcher=ToolIdentityMatcher(
                match_mode=ToolMatchMode.CATEGORY,
                tool_category=ToolCategory.INTERNAL_RUNTIME,
            ),
            permission_type=ToolPermissionType.CONFIGURATION_WRITE,
            decision=ToolPermissionDecision.APPROVAL_REQUIRED,
            risk_ceiling="R4",
            trace_required=True,
            evidence_required=True,
            description="Configuration write requires approval.",
        ),
        # Network access — governed
        ToolPermissionRule(
            matcher=ToolIdentityMatcher(
                match_mode=ToolMatchMode.CATEGORY,
                tool_category=ToolCategory.NETWORK,
            ),
            permission_type=ToolPermissionType.NETWORK,
            decision=ToolPermissionDecision.APPROVAL_REQUIRED,
            risk_ceiling="R3",
            trace_required=True,
            forbidden_data_classes=(
                "credentials", "sensitive_personal_data",
            ),
            description="Network access requires approval.",
        ),
        # Browser action — governed
        ToolPermissionRule(
            matcher=ToolIdentityMatcher(
                match_mode=ToolMatchMode.CATEGORY,
                tool_category=ToolCategory.BROWSER,
            ),
            permission_type=ToolPermissionType.BROWSER_ACTION,
            decision=ToolPermissionDecision.APPROVAL_REQUIRED,
            risk_ceiling="R3",
            trace_required=True,
            forbidden_data_classes=(
                "credentials", "sensitive_personal_data",
            ),
            description="Browser actions require approval.",
        ),
        # GitHub write — governed
        ToolPermissionRule(
            matcher=ToolIdentityMatcher(
                match_mode=ToolMatchMode.CATEGORY,
                tool_category=ToolCategory.GITHUB,
            ),
            permission_type=ToolPermissionType.GITHUB_WRITE,
            decision=ToolPermissionDecision.APPROVAL_REQUIRED,
            risk_ceiling="R3",
            trace_required=True,
            description="GitHub write requires approval.",
        ),
        # Database write — governed
        ToolPermissionRule(
            matcher=ToolIdentityMatcher(
                match_mode=ToolMatchMode.CATEGORY,
                tool_category=ToolCategory.DATABASE,
            ),
            permission_type=ToolPermissionType.DATABASE_WRITE,
            decision=ToolPermissionDecision.APPROVAL_REQUIRED,
            risk_ceiling="R3",
            trace_required=True,
            evidence_required=True,
            description="Database write requires approval.",
        ),
    )

    return ToolPermissionPolicyCard(
        policy_card=policy_card,
        schema_version=TOOL_PERMISSION_POLICY_CARD_SCHEMA_VERSION,
        permission_rules=rules,
        default_decision=ToolPermissionDecision.DENY,
        metadata={"owner_note": "strict default deny-by-default tool permission policy"},
    )
