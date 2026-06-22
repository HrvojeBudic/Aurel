"""P1.4.13 Authority Delta Detector.

Compares two attested canonical states and detects whether authority, scope,
risk ceiling, human oversight, tool permissions, capability status, claim
status, or doctrine status changed in a way that matters.

This module detects and reports authority deltas. It does NOT grant consent,
approve changes, or execute tools.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from typing import Any


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class AuthorityDeltaType(str, Enum):
    AUTHORITY_SCOPE_ADDED = "AUTHORITY_SCOPE_ADDED"
    AUTHORITY_SCOPE_REMOVED = "AUTHORITY_SCOPE_REMOVED"

    RISK_CEILING_INCREASED = "RISK_CEILING_INCREASED"
    RISK_CEILING_DECREASED = "RISK_CEILING_DECREASED"

    OVERSIGHT_WEAKENED = "OVERSIGHT_WEAKENED"
    OVERSIGHT_STRENGTHENED = "OVERSIGHT_STRENGTHENED"

    TOOL_PERMISSION_ADDED = "TOOL_PERMISSION_ADDED"
    TOOL_PERMISSION_REMOVED = "TOOL_PERMISSION_REMOVED"

    WRITE_SCOPE_ADDED = "WRITE_SCOPE_ADDED"
    WRITE_SCOPE_REMOVED = "WRITE_SCOPE_REMOVED"

    EXTERNAL_EFFECT_ADDED = "EXTERNAL_EFFECT_ADDED"
    EXTERNAL_EFFECT_REMOVED = "EXTERNAL_EFFECT_REMOVED"

    CAPABILITY_STATUS_ESCALATED = "CAPABILITY_STATUS_ESCALATED"
    CAPABILITY_STATUS_DEESCALATED = "CAPABILITY_STATUS_DEESCALATED"

    CLAIM_STATUS_ESCALATED = "CLAIM_STATUS_ESCALATED"
    CLAIM_STATUS_DEESCALATED = "CLAIM_STATUS_DEESCALATED"

    DOCTRINE_STATUS_ESCALATED = "DOCTRINE_STATUS_ESCALATED"
    DOCTRINE_STATUS_DEESCALATED = "DOCTRINE_STATUS_DEESCALATED"

    SOURCE_VALIDATION_DOWNGRADED = "SOURCE_VALIDATION_DOWNGRADED"
    SOURCE_VALIDATION_UPGRADED = "SOURCE_VALIDATION_UPGRADED"

    VALIDATOR_CHANGED = "VALIDATOR_CHANGED"
    SCHEMA_VERSION_CHANGED = "SCHEMA_VERSION_CHANGED"

    UNKNOWN_AUTHORITY_CHANGE = "UNKNOWN_AUTHORITY_CHANGE"


class AuthorityDeltaSeverity(str, Enum):
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


# ---------------------------------------------------------------------------
# Order tables
# ---------------------------------------------------------------------------

RISK_CEILING_ORDER: tuple[str, ...] = (
    "none",
    "low",
    "medium",
    "high",
    "critical",
)

CLAIM_STATUS_ORDER: tuple[str, ...] = (
    "FORBIDDEN",
    "ROADMAP_ONLY",
    "DRAFT_ONLY",
    "EXPERIMENTAL",
    "PARTIALLY_VERIFIED",
    "VERIFIED",
    "PRODUCTION_ELIGIBLE",
)

DOCTRINE_STATUS_ORDER: tuple[str, ...] = (
    "REJECTED",
    "REFERENCE_ONLY",
    "ROADMAP_INFLUENCING",
    "CANON_COMPATIBLE",
    "IMPLEMENTATION_PLANNED",
    "IMPLEMENTATION_ACTIVE",
    "IMPLEMENTED",
)

CAPABILITY_STATUS_ORDER: tuple[str, ...] = (
    "missing",
    "planned",
    "roadmap_only",
    "experimental",
    "implemented",
    "partially_verified",
    "verified",
    "production_eligible",
)

SEVERITY_ORDER: tuple[AuthorityDeltaSeverity, ...] = (
    AuthorityDeltaSeverity.INFO,
    AuthorityDeltaSeverity.LOW,
    AuthorityDeltaSeverity.MEDIUM,
    AuthorityDeltaSeverity.HIGH,
    AuthorityDeltaSeverity.CRITICAL,
)


# ---------------------------------------------------------------------------
# Conservative external-effect / dangerous tool heuristic
# ---------------------------------------------------------------------------

_EXTERNAL_EFFECT_TOKENS: frozenset[str] = frozenset(
    {
        "send_email",
        "email",
        "delete_file",
        "remove_file",
        "make_payment",
        "payment",
        "post_publicly",
        "social_post",
        "publish",
        "api_write",
        "external_api_write",
        "webhook",
        "deploy",
        "shell_exec",
        "subprocess",
        "network_write",
    }
)

_WRITE_TOKENS: frozenset[str] = frozenset(
    {
        "write",
        "write_file",
        "filesystem_write",
        "delete",
        "delete_file",
        "remove_file",
        "save",
        "patch",
        "replace",
    }
)

_READ_ONLY_TOKENS: frozenset[str] = frozenset(
    {
        "read",
        "read_file",
        "list",
        "search",
        "grep",
        "find",
        "get",
        "fetch",
    }
)


def _is_external_effect_tool(name: str) -> bool:
    lowered = name.lower().replace("-", "_").replace(" ", "_")
    for token in _EXTERNAL_EFFECT_TOKENS:
        if token in lowered:
            return True
    return False


def _is_write_tool(name: str) -> bool:
    lowered = name.lower().replace("-", "_").replace(" ", "_")
    for token in _WRITE_TOKENS:
        if token in lowered:
            return True
    return False


# ---------------------------------------------------------------------------
# Authority-relevant field names by source kind
# ---------------------------------------------------------------------------

_OPERATOR_CONTRACT_FIELDS: frozenset[str] = frozenset(
    {
        "authority_scope",
        "allowed_actions",
        "allowed_tools",
        "risk_ceiling",
        "requires_human_approval",
        "human_approval_required",
        "external_effect_permissions",
        "write_permissions",
        "delegation_permissions",
        "data_residency",
        "egress_allowed",
        "tool_access_implies_authority",
        "serious_actions_require_authority_check",
        "irreversible_actions_require_operator_approval",
        "external_side_effects_require_policy_allowance",
        "memory_canon_changes_require_approval_or_future_policy",
        "serious_actions_must_be_traceable",
        "operator_authorization_ref_required_for_high_risk",
        "operator_final_authority",
        "aurel_final_authority",
        "aurel_can_self_escalate",
        "aurel_can_replace_operator",
        "aurel_can_override_operator_judgment",
        "aurel_can_refuse_forbidden_action",
        "aurel_can_challenge_operator",
        "aurel_must_challenge_when_risk_detected",
        "disagreement_allowed",
        "blind_execution_forbidden",
        "risk_challenge_required",
        "passive_obedience_required",
        "cannot_override_identity_kernel",
        "cannot_override_persona_manifest_boundaries",
        "cannot_grant_tool_rights",
        "cannot_change_autonomy",
        "cannot_disable_constitutional_floor",
        "cannot_expand_delegation_scope",
    }
)

_AGENT_IDENTITY_CARD_FIELDS: frozenset[str] = frozenset(
    {
        "capabilities",
        "capability_status",
        "autonomy_class",
        "risk_ceiling",
        "tool_scope",
        "claim_status",
        "lifecycle_state",
        "authority_scope",
        "card_can_grant_authority",
        "card_can_change_identity_kernel",
        "card_can_override_policy",
        "card_can_change_autonomy",
        "card_can_create_delegation",
        "card_can_authorize_tools",
        "card_can_replace_operator",
    }
)

_SELF_MODEL_POLICY_FIELDS: frozenset[str] = frozenset(
    {
        "declared_capabilities",
        "limitations",
        "known_boundaries",
        "self_improvement_status",
        "autonomy_status",
        "memory_status",
        "tool_use_status",
        "self_model_can_change_autonomy",
        "self_model_can_change_identity",
        "self_model_can_grant_authority",
        "self_model_can_modify_policy",
        "self_model_can_verify_capability_by_itself",
        "self_model_can_write_memory",
        "capability_statuses",
        "modes_can_grant_permissions",
        "modes_can_override_identity_kernel",
        "modes_can_override_operator_contract",
        "modes_can_override_persona_manifest",
        "modes_can_change_autonomy",
        "modes_can_execute_actions",
        "modes_can_write_memory_directly",
    }
)

_EXTERNAL_DOCTRINE_FIELDS: frozenset[str] = frozenset(
    {
        "assimilation_status",
        "mapped_roadmap_modules",
        "operator_accepted",
        "claim_boundaries",
        "implementation_status",
        "capability_evidence_refs",
        "risk_notes",
        "source_type",
        "version",
    }
)

_CAPABILITY_CLAIM_FIELDS: frozenset[str] = frozenset(
    {
        "allowed_status",
        "required_evidence_level",
        "current_evidence_level",
        "safe_claim_text",
        "blockers",
    }
)

_SOURCE_ATTESTATION_FIELDS: frozenset[str] = frozenset(
    {
        "validation_status",
        "validator_name",
        "validator_version",
        "schema_version",
        "rejected_unknown_fields",
        "errors",
        "warnings",
    }
)

_AUTHORITY_FIELDS_BY_KIND: dict[str, frozenset[str]] = {
    "operator_contract": _OPERATOR_CONTRACT_FIELDS,
    "agent_identity_card_config": _AGENT_IDENTITY_CARD_FIELDS,
    "agent_identity_card": _AGENT_IDENTITY_CARD_FIELDS,
    "self_model_policy": _SELF_MODEL_POLICY_FIELDS,
    "self_model": _SELF_MODEL_POLICY_FIELDS,
    "external_doctrine": _EXTERNAL_DOCTRINE_FIELDS,
    "capability_claims": _CAPABILITY_CLAIM_FIELDS,
    "source_attestation": _SOURCE_ATTESTATION_FIELDS,
}

# Fields whose root-level presence is authority-relevant even if not in the kind-specific set
_UNIVERSAL_AUTHORITY_FIELDS: frozenset[str] = frozenset(
    {
        "risk_ceiling",
        "requires_human_approval",
        "human_approval_required",
        "allowed_tools",
        "external_effect_permissions",
        "write_permissions",
        "authority_scope",
        "autonomy_class",
        "tool_scope",
        "claim_status",
        "capability_status",
        "assimilation_status",
        "validation_status",
        "validator_name",
        "validator_version",
        "schema_version",
        "operator_accepted",
        "implementation_status",
    }
)


def _is_authority_field(field_name: str, source_kind: str) -> bool:
    lowered = field_name.lower()
    if lowered in _UNIVERSAL_AUTHORITY_FIELDS:
        return True
    kind_fields = _AUTHORITY_FIELDS_BY_KIND.get(source_kind)
    if kind_fields is not None and lowered in kind_fields:
        return True
    kwargs = {
        "authority",
        "permission",
        "oversight",
        "autonomy",
        "risk",
        "tool",
        "claim",
        "capability",
        "doctrine",
        "operator",
        "delegation",
        "escalation",
        "approval",
    }
    for kw in kwargs:
        if kw in lowered:
            return True
    return False


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AuthorityDelta:
    delta_id: str
    delta_type: AuthorityDeltaType
    severity: AuthorityDeltaSeverity

    source_kind: str
    field_path: str

    old_value: object | None
    new_value: object | None

    old_attestation_id: str | None
    new_attestation_id: str | None

    requires_operator_consent: bool
    requires_evidence: bool

    reason: str
    blockers: tuple[str, ...]
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class AuthorityDeltaInput:
    source_kind: str

    old_canonical_object: object
    new_canonical_object: object

    old_attestation: object | None = None
    new_attestation: object | None = None

    comparison_context: str | None = None


@dataclass(frozen=True)
class AuthorityDeltaReport:
    report_id: str
    source_kind: str

    deltas: tuple[AuthorityDelta, ...]

    highest_severity: AuthorityDeltaSeverity
    requires_operator_consent: bool
    requires_evidence: bool

    summary: str
    safe_to_auto_accept: bool

    old_attestation_id: str | None
    new_attestation_id: str | None


# ---------------------------------------------------------------------------
# JSON-safe value conversion
# ---------------------------------------------------------------------------


def _json_safe_value(value: object | None) -> object:
    if value is None:
        return None
    if isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, (tuple, list, set, frozenset)):
        return [_json_safe_value(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _json_safe_value(v) for k, v in value.items()}
    return str(value)


# ---------------------------------------------------------------------------
# Serialization
# ---------------------------------------------------------------------------


def authority_delta_to_dict(delta: AuthorityDelta) -> dict[str, object]:
    return {
        "delta_id": delta.delta_id,
        "delta_type": delta.delta_type.value,
        "severity": delta.severity.value,
        "source_kind": delta.source_kind,
        "field_path": delta.field_path,
        "old_value": _json_safe_value(delta.old_value),
        "new_value": _json_safe_value(delta.new_value),
        "old_attestation_id": delta.old_attestation_id,
        "new_attestation_id": delta.new_attestation_id,
        "requires_operator_consent": delta.requires_operator_consent,
        "requires_evidence": delta.requires_evidence,
        "reason": delta.reason,
        "blockers": list(delta.blockers),
        "warnings": list(delta.warnings),
    }


def authority_delta_report_to_dict(report: AuthorityDeltaReport) -> dict[str, object]:
    return {
        "report_id": report.report_id,
        "source_kind": report.source_kind,
        "deltas": [authority_delta_to_dict(d) for d in report.deltas],
        "highest_severity": report.highest_severity.value,
        "requires_operator_consent": report.requires_operator_consent,
        "requires_evidence": report.requires_evidence,
        "summary": report.summary,
        "safe_to_auto_accept": report.safe_to_auto_accept,
        "old_attestation_id": report.old_attestation_id,
        "new_attestation_id": report.new_attestation_id,
    }


# ---------------------------------------------------------------------------
# Authority surface extraction
# ---------------------------------------------------------------------------


def extract_authority_surface(
    source_kind: str,
    canonical_object: object,
) -> dict[str, object]:
    """Extract authority-relevant fields from a canonical object."""
    surface: dict[str, object] = {}

    def _extract(obj: object, prefix: str = "") -> None:
        if isinstance(obj, dict):
            for key, value in obj.items():
                key_str = str(key)
                full_path = f"{prefix}.{key_str}" if prefix else key_str
                is_auth = _is_authority_field(key_str, source_kind)
                if isinstance(value, dict):
                    _extract(value, full_path)
                elif is_auth:
                    surface[full_path] = _json_safe_value(value)
                elif isinstance(value, (list, tuple)):
                    _extract(value, full_path)
        elif isinstance(obj, (list, tuple)):
            for i, item in enumerate(obj):
                _extract(item, f"{prefix}[{i}]")
        elif hasattr(obj, "__dataclass_fields__"):
            import dataclasses
            for field in dataclasses.fields(obj):
                key_str = field.name
                full_path = f"{prefix}.{key_str}" if prefix else key_str
                value = getattr(obj, field.name)
                is_auth = _is_authority_field(key_str, source_kind)
                if isinstance(value, dict) or hasattr(value, "__dataclass_fields__"):
                    _extract(value, full_path)
                elif is_auth:
                    surface[full_path] = _json_safe_value(value)
                elif isinstance(value, (list, tuple)):
                    _extract(value, full_path)
        elif hasattr(obj, "__dict__") and not isinstance(obj, type):
            d = vars(obj)
            for key, value in d.items():
                key_str = str(key)
                full_path = f"{prefix}.{key_str}" if prefix else key_str
                is_auth = _is_authority_field(key_str, source_kind)
                if isinstance(value, dict):
                    _extract(value, full_path)
                elif is_auth:
                    surface[full_path] = _json_safe_value(value)
                elif isinstance(value, (list, tuple)):
                    _extract(value, full_path)

    _extract(canonical_object)
    return surface


# ---------------------------------------------------------------------------
# Status order helpers
# ---------------------------------------------------------------------------


def _index_in_order(order: tuple[str, ...], value: str) -> int:
    try:
        return order.index(value)
    except ValueError:
        return -1


# ---------------------------------------------------------------------------
# Delta classification
# ---------------------------------------------------------------------------


def classify_authority_delta(
    field_path: str,
    old_value: object | None,
    new_value: object | None,
    source_kind: str,
) -> AuthorityDeltaType:
    """Classify a field-level change by authority meaning."""
    field_lower = field_path.lower().replace(".", "_")

    # Risk ceiling
    if "risk_ceiling" in field_lower:
        old_idx = _index_in_order(RISK_CEILING_ORDER, str(old_value).lower() if old_value is not None else "")
        new_idx = _index_in_order(RISK_CEILING_ORDER, str(new_value).lower() if new_value is not None else "")
        if new_idx > old_idx:
            return AuthorityDeltaType.RISK_CEILING_INCREASED
        if new_idx < old_idx:
            return AuthorityDeltaType.RISK_CEILING_DECREASED

    # Human oversight
    if "human_approval" in field_lower or "requires_human" in field_lower:
        if old_value is True and new_value is False:
            return AuthorityDeltaType.OVERSIGHT_WEAKENED
        if old_value is False and new_value is True:
            return AuthorityDeltaType.OVERSIGHT_STRENGTHENED

    # Constitutional boundaries — weakening True→False is oversight/authority weakening
    boundary_prefixes = ("cannot_", "operator_final_authority", "aurel_final_authority",
                         "blind_execution_forbidden", "risk_challenge_required",
                         "passive_obedience_required", "aurel_can_", "require",
                         "_must_", "operator_authorization", "irreversible_actions_",
                         "external_side_effects_", "memory_canon_", "serious_actions_",
                         "tool_access_implies_authority")
    for prefix in boundary_prefixes:
        if prefix in field_lower:
            if isinstance(old_value, bool) and isinstance(new_value, bool):
                if old_value is True and new_value is False:
                    return AuthorityDeltaType.OVERSIGHT_WEAKENED
                if old_value is False and new_value is True:
                    return AuthorityDeltaType.OVERSIGHT_STRENGTHENED
            break

    # Allowed tools
    if "allowed_tools" in field_lower or "tool_scope" in field_lower:
        if old_value is None and new_value is not None:
            return _classify_tool_scope_added(new_value)
        if isinstance(old_value, (list, tuple, set, frozenset)) and isinstance(new_value, (list, tuple, set, frozenset)):
            old_set = frozenset(str(v) for v in old_value)
            new_set = frozenset(str(v) for v in new_value)
            added = new_set - old_set
            removed = old_set - new_set
            if added and not removed:
                return _classify_tool_scope_added(added)
            if removed and not added:
                return AuthorityDeltaType.TOOL_PERMISSION_REMOVED
            if added:
                return _classify_tool_scope_added(added)

    # Write scope
    if "write_permission" in field_lower or "write_scope" in field_lower:
        if _value_expanded(old_value, new_value):
            return AuthorityDeltaType.WRITE_SCOPE_ADDED
        if _value_shrank(old_value, new_value):
            return AuthorityDeltaType.WRITE_SCOPE_REMOVED

    # External effect
    if "external_effect" in field_lower:
        if _value_expanded(old_value, new_value):
            return AuthorityDeltaType.EXTERNAL_EFFECT_ADDED
        if _value_shrank(old_value, new_value):
            return AuthorityDeltaType.EXTERNAL_EFFECT_REMOVED

    # Claim status
    if "claim_status" in field_lower or "allowed_status" in field_lower:
        old_idx = _index_in_order(CLAIM_STATUS_ORDER, str(old_value) if old_value is not None else "")
        new_idx = _index_in_order(CLAIM_STATUS_ORDER, str(new_value) if new_value is not None else "")
        if new_idx > old_idx:
            return AuthorityDeltaType.CLAIM_STATUS_ESCALATED
        if new_idx < old_idx:
            return AuthorityDeltaType.CLAIM_STATUS_DEESCALATED

    # Doctrine status
    if "assimilation_status" in field_lower or "implementation_status" in field_lower:
        old_idx = _index_in_order(DOCTRINE_STATUS_ORDER, str(old_value) if old_value is not None else "")
        new_idx = _index_in_order(DOCTRINE_STATUS_ORDER, str(new_value) if new_value is not None else "")
        if new_idx > old_idx:
            return AuthorityDeltaType.DOCTRINE_STATUS_ESCALATED
        if new_idx < old_idx:
            return AuthorityDeltaType.DOCTRINE_STATUS_DEESCALATED

    # Capability status
    if "capability_status" in field_lower:
        old_idx = _index_in_order(CAPABILITY_STATUS_ORDER, str(old_value).lower() if old_value is not None else "")
        new_idx = _index_in_order(CAPABILITY_STATUS_ORDER, str(new_value).lower() if new_value is not None else "")
        if new_idx > old_idx:
            return AuthorityDeltaType.CAPABILITY_STATUS_ESCALATED
        if new_idx < old_idx:
            return AuthorityDeltaType.CAPABILITY_STATUS_DEESCALATED

    # Validation status
    if "validation_status" in field_lower:
        return _classify_validation_status_change(old_value, new_value)

    # Validator / schema
    if "validator_name" in field_lower:
        return AuthorityDeltaType.VALIDATOR_CHANGED
    if "schema_version" in field_lower:
        return AuthorityDeltaType.SCHEMA_VERSION_CHANGED
    if "validator_version" in field_lower:
        return AuthorityDeltaType.VALIDATOR_CHANGED

    # Authority scope
    if "authority_scope" in field_lower:
        if _value_expanded(old_value, new_value):
            return AuthorityDeltaType.AUTHORITY_SCOPE_ADDED
        if _value_shrank(old_value, new_value):
            return AuthorityDeltaType.AUTHORITY_SCOPE_REMOVED

    # Tool permission additions/removals from tool-like fields
    if _is_tool_like_field(field_lower):
        if _value_expanded(old_value, new_value):
            return AuthorityDeltaType.TOOL_PERMISSION_ADDED
        if _value_shrank(old_value, new_value):
            return AuthorityDeltaType.TOOL_PERMISSION_REMOVED

    return AuthorityDeltaType.UNKNOWN_AUTHORITY_CHANGE


def _classify_tool_scope_added(added: object) -> AuthorityDeltaType:
    items: list[str] = []
    if isinstance(added, (set, frozenset)):
        items = [str(v) for v in added]
    elif isinstance(added, (list, tuple)):
        items = [str(v) for v in added]
    elif isinstance(added, str):
        items = [added]

    has_external = any(_is_external_effect_tool(item) for item in items)
    has_write = any(_is_write_tool(item) for item in items)

    if has_external:
        return AuthorityDeltaType.EXTERNAL_EFFECT_ADDED
    if has_write:
        return AuthorityDeltaType.WRITE_SCOPE_ADDED
    return AuthorityDeltaType.TOOL_PERMISSION_ADDED


def _classify_validation_status_change(
    old_value: object | None, new_value: object | None
) -> AuthorityDeltaType:
    old_str = str(old_value) if old_value is not None else ""
    new_str = str(new_value) if new_value is not None else ""
    downgrade_targets = {"VALID_WITH_WARNINGS", "INVALID", "REJECTED_UNKNOWN_FIELDS", "SCHEMA_MISMATCH", "MISSING_SOURCE"}
    if old_str == "VALID" and new_str in downgrade_targets:
        return AuthorityDeltaType.SOURCE_VALIDATION_DOWNGRADED
    if new_str == "VALID" and old_str in downgrade_targets:
        return AuthorityDeltaType.SOURCE_VALIDATION_UPGRADED
    if old_str != new_str:
        return AuthorityDeltaType.SOURCE_VALIDATION_DOWNGRADED
    return AuthorityDeltaType.UNKNOWN_AUTHORITY_CHANGE


def _value_expanded(old_value: object | None, new_value: object | None) -> bool:
    """Check if a collection/dict/bool expanded in a way that suggests more authority."""
    if old_value is None and new_value is not None:
        return True
    if isinstance(old_value, (list, tuple, set, frozenset)) and isinstance(new_value, (list, tuple, set, frozenset)):
        old_set = frozenset(str(v) for v in old_value)
        new_set = frozenset(str(v) for v in new_value)
        return bool(new_set - old_set)
    if isinstance(old_value, bool) and isinstance(new_value, bool):
        return old_value is False and new_value is True
    if isinstance(old_value, dict) and isinstance(new_value, dict):
        return len(new_value) > len(old_value)
    if isinstance(old_value, str) and isinstance(new_value, str):
        return old_value.lower() in {"none", "low"} and new_value.lower() in {"high", "critical", "medium"}
    return False


def _value_shrank(old_value: object | None, new_value: object | None) -> bool:
    if old_value is not None and new_value is None:
        return True
    if isinstance(old_value, (list, tuple, set, frozenset)) and isinstance(new_value, (list, tuple, set, frozenset)):
        old_set = frozenset(str(v) for v in old_value)
        new_set = frozenset(str(v) for v in new_value)
        return bool(old_set - new_set)
    if isinstance(old_value, bool) and isinstance(new_value, bool):
        return old_value is True and new_value is False
    if isinstance(old_value, dict) and isinstance(new_value, dict):
        return len(new_value) < len(old_value)
    return False


def _is_tool_like_field(field_lower: str) -> bool:
    tool_keywords = {"tool", "permission", "action", "allowed", "scope", "grant"}
    return any(kw in field_lower for kw in tool_keywords)


# ---------------------------------------------------------------------------
# Severity resolver
# ---------------------------------------------------------------------------


def resolve_authority_delta_severity(
    delta_type: AuthorityDeltaType,
    old_value: object | None,
    new_value: object | None,
) -> AuthorityDeltaSeverity:
    if delta_type == AuthorityDeltaType.OVERSIGHT_WEAKENED:
        return AuthorityDeltaSeverity.CRITICAL
    if delta_type == AuthorityDeltaType.EXTERNAL_EFFECT_ADDED:
        return AuthorityDeltaSeverity.CRITICAL

    if delta_type == AuthorityDeltaType.RISK_CEILING_INCREASED:
        new_str = str(new_value).lower() if new_value is not None else ""
        if new_str == "critical":
            return AuthorityDeltaSeverity.CRITICAL
        return AuthorityDeltaSeverity.HIGH

    if delta_type == AuthorityDeltaType.TOOL_PERMISSION_ADDED:
        new_items = _to_strings(new_value) if new_value is not None else []
        if any(_is_external_effect_tool(item) for item in new_items):
            return AuthorityDeltaSeverity.CRITICAL
        if any(_is_write_tool(item) for item in new_items):
            return AuthorityDeltaSeverity.HIGH
        return AuthorityDeltaSeverity.MEDIUM

    if delta_type == AuthorityDeltaType.WRITE_SCOPE_ADDED:
        return AuthorityDeltaSeverity.HIGH

    if delta_type == AuthorityDeltaType.CLAIM_STATUS_ESCALATED:
        new_str = str(new_value) if new_value is not None else ""
        if new_str in {"VERIFIED", "PRODUCTION_ELIGIBLE"}:
            return AuthorityDeltaSeverity.CRITICAL
        return AuthorityDeltaSeverity.HIGH

    if delta_type == AuthorityDeltaType.DOCTRINE_STATUS_ESCALATED:
        new_str = str(new_value) if new_value is not None else ""
        if new_str in {"IMPLEMENTED", "IMPLEMENTATION_ACTIVE"}:
            return AuthorityDeltaSeverity.CRITICAL
        return AuthorityDeltaSeverity.HIGH

    if delta_type == AuthorityDeltaType.CAPABILITY_STATUS_ESCALATED:
        new_str = str(new_value).lower() if new_value is not None else ""
        if new_str in {"verified", "production_eligible"}:
            return AuthorityDeltaSeverity.CRITICAL
        return AuthorityDeltaSeverity.HIGH

    if delta_type == AuthorityDeltaType.SOURCE_VALIDATION_DOWNGRADED:
        return AuthorityDeltaSeverity.HIGH

    if delta_type == AuthorityDeltaType.AUTHORITY_SCOPE_ADDED:
        return AuthorityDeltaSeverity.HIGH

    if delta_type == AuthorityDeltaType.VALIDATOR_CHANGED:
        return AuthorityDeltaSeverity.MEDIUM

    if delta_type == AuthorityDeltaType.SCHEMA_VERSION_CHANGED:
        return AuthorityDeltaSeverity.MEDIUM

    if delta_type == AuthorityDeltaType.UNKNOWN_AUTHORITY_CHANGE:
        return AuthorityDeltaSeverity.MEDIUM

    # Reductions / de-escalations
    if delta_type in {
        AuthorityDeltaType.RISK_CEILING_DECREASED,
        AuthorityDeltaType.OVERSIGHT_STRENGTHENED,
        AuthorityDeltaType.TOOL_PERMISSION_REMOVED,
        AuthorityDeltaType.WRITE_SCOPE_REMOVED,
        AuthorityDeltaType.EXTERNAL_EFFECT_REMOVED,
        AuthorityDeltaType.CAPABILITY_STATUS_DEESCALATED,
        AuthorityDeltaType.CLAIM_STATUS_DEESCALATED,
        AuthorityDeltaType.DOCTRINE_STATUS_DEESCALATED,
        AuthorityDeltaType.AUTHORITY_SCOPE_REMOVED,
        AuthorityDeltaType.SOURCE_VALIDATION_UPGRADED,
    }:
        return AuthorityDeltaSeverity.INFO

    return AuthorityDeltaSeverity.LOW


def _to_strings(value: object) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, (list, tuple, set, frozenset)):
        return [str(v) for v in value]
    return [str(value)]


# ---------------------------------------------------------------------------
# Consent requirement resolver
# ---------------------------------------------------------------------------


def authority_delta_requires_consent(delta: AuthorityDelta) -> bool:
    if delta.severity in {AuthorityDeltaSeverity.HIGH, AuthorityDeltaSeverity.CRITICAL}:
        return True
    expansion_types: set[AuthorityDeltaType] = {
        AuthorityDeltaType.AUTHORITY_SCOPE_ADDED,
        AuthorityDeltaType.RISK_CEILING_INCREASED,
        AuthorityDeltaType.OVERSIGHT_WEAKENED,
        AuthorityDeltaType.TOOL_PERMISSION_ADDED,
        AuthorityDeltaType.WRITE_SCOPE_ADDED,
        AuthorityDeltaType.EXTERNAL_EFFECT_ADDED,
        AuthorityDeltaType.CAPABILITY_STATUS_ESCALATED,
        AuthorityDeltaType.CLAIM_STATUS_ESCALATED,
        AuthorityDeltaType.DOCTRINE_STATUS_ESCALATED,
        AuthorityDeltaType.SOURCE_VALIDATION_DOWNGRADED,
    }
    return delta.delta_type in expansion_types


# ---------------------------------------------------------------------------
# Evidence requirement resolver
# ---------------------------------------------------------------------------


def authority_delta_requires_evidence(delta: AuthorityDelta) -> bool:
    evidence_types: set[AuthorityDeltaType] = {
        AuthorityDeltaType.CLAIM_STATUS_ESCALATED,
        AuthorityDeltaType.CAPABILITY_STATUS_ESCALATED,
        AuthorityDeltaType.DOCTRINE_STATUS_ESCALATED,
        AuthorityDeltaType.SOURCE_VALIDATION_DOWNGRADED,
        AuthorityDeltaType.VALIDATOR_CHANGED,
        AuthorityDeltaType.SCHEMA_VERSION_CHANGED,
    }
    if delta.delta_type in evidence_types:
        return True
    new_str = str(delta.new_value).lower() if delta.new_value is not None else ""
    prod_keywords = {"production_eligible", "verified", "implemented"}
    if any(kw in new_str for kw in prod_keywords):
        return True
    return False


# ---------------------------------------------------------------------------
# Surface comparison
# ---------------------------------------------------------------------------


def compare_authority_surfaces(
    old_surface: dict[str, object],
    new_surface: dict[str, object],
    context: AuthorityDeltaInput,
) -> tuple[AuthorityDelta, ...]:
    """Compare two authority surfaces and produce classified deltas."""
    deltas: list[AuthorityDelta] = []
    old_att_id = _get_attestation_id(context.old_attestation)
    new_att_id = _get_attestation_id(context.new_attestation)
    delta_counter = 0

    all_keys = sorted(set(old_surface) | set(new_surface))
    for key in all_keys:
        old_val = old_surface.get(key)
        new_val = new_surface.get(key)
        if old_val == new_val:
            continue
        if isinstance(old_val, (list, tuple, set, frozenset)) and isinstance(new_val, (list, tuple, set, frozenset)):
            old_set = frozenset(_json_safe_value(v) for v in old_val)
            new_set = frozenset(_json_safe_value(v) for v in new_val)
            if old_set == new_set:
                continue

        delta_type = classify_authority_delta(key, old_val, new_val, context.source_kind)
        severity = resolve_authority_delta_severity(delta_type, old_val, new_val)

        delta_counter += 1
        delta_id = f"adt_{context.source_kind}_{delta_counter}"
        requires_consent = authority_delta_requires_consent(
            AuthorityDelta(
                delta_id=delta_id,
                delta_type=delta_type,
                severity=severity,
                source_kind=context.source_kind,
                field_path=key,
                old_value=old_val,
                new_value=new_val,
                old_attestation_id=old_att_id,
                new_attestation_id=new_att_id,
                requires_operator_consent=False,
                requires_evidence=False,
                reason="",
                blockers=(),
                warnings=(),
            )
        )
        requires_ev = authority_delta_requires_evidence(
            AuthorityDelta(
                delta_id=delta_id,
                delta_type=delta_type,
                severity=severity,
                source_kind=context.source_kind,
                field_path=key,
                old_value=old_val,
                new_value=new_val,
                old_attestation_id=old_att_id,
                new_attestation_id=new_att_id,
                requires_operator_consent=False,
                requires_evidence=False,
                reason="",
                blockers=(),
                warnings=(),
            )
        )

        reason = _build_delta_reason(delta_type, key, old_val, new_val)
        blockers: tuple[str, ...] = ()
        warnings: tuple[str, ...] = ()
        if requires_consent:
            blockers = (f"operator_consent_required_for_{delta_type.value}",)
        if requires_ev:
            warnings = (f"evidence_required_for_{delta_type.value}",)

        deltas.append(
            AuthorityDelta(
                delta_id=delta_id,
                delta_type=delta_type,
                severity=severity,
                source_kind=context.source_kind,
                field_path=key,
                old_value=old_val,
                new_value=new_val,
                old_attestation_id=old_att_id,
                new_attestation_id=new_att_id,
                requires_operator_consent=requires_consent,
                requires_evidence=requires_ev,
                reason=reason,
                blockers=blockers,
                warnings=warnings,
            )
        )

    return tuple(deltas)


def _build_delta_reason(
    delta_type: AuthorityDeltaType,
    field_path: str,
    old_value: object | None,
    new_value: object | None,
) -> str:
    old_repr = _json_safe_value(old_value)
    new_repr = _json_safe_value(new_value)
    return f"{delta_type.value}: {field_path} changed from {old_repr!r} to {new_repr!r}"


def _get_attestation_id(attestation: object | None) -> str | None:
    if attestation is None:
        return None
    if hasattr(attestation, "attestation_id"):
        return str(getattr(attestation, "attestation_id"))
    if isinstance(attestation, dict):
        return str(attestation.get("attestation_id", "")) or None
    return None


# ---------------------------------------------------------------------------
# Report helpers
# ---------------------------------------------------------------------------


def highest_authority_delta_severity(
    deltas: tuple[AuthorityDelta, ...],
) -> AuthorityDeltaSeverity:
    if not deltas:
        return AuthorityDeltaSeverity.INFO
    highest = AuthorityDeltaSeverity.INFO
    for delta in deltas:
        sev_idx = SEVERITY_ORDER.index(delta.severity)
        if sev_idx > SEVERITY_ORDER.index(highest):
            highest = delta.severity
    return highest


def summarize_authority_delta_report(
    deltas: tuple[AuthorityDelta, ...],
) -> str:
    if not deltas:
        return "No authority-relevant changes detected. Safe to auto-accept."
    count = len(deltas)
    high_critical = sum(
        1 for d in deltas if d.severity in {AuthorityDeltaSeverity.HIGH, AuthorityDeltaSeverity.CRITICAL}
    )
    consent = sum(1 for d in deltas if d.requires_operator_consent)
    evidence = sum(1 for d in deltas if d.requires_evidence)

    parts: list[str] = []
    parts.append(f"{count} authority-relevant change(s) detected.")
    if high_critical:
        parts.append(f"{high_critical} HIGH/CRITICAL severity delta(s).")
    if consent:
        parts.append(f"{consent} delta(s) require Operator consent.")
    if evidence:
        parts.append(f"{evidence} delta(s) require additional evidence.")
    if not high_critical and not consent:
        parts.append("All changes are INFO/LOW severity. No consent required.")
    return " ".join(parts)


# ---------------------------------------------------------------------------
# Main detector
# ---------------------------------------------------------------------------


def detect_authority_deltas(
    delta_input: AuthorityDeltaInput,
) -> AuthorityDeltaReport:
    old_surface = extract_authority_surface(delta_input.source_kind, delta_input.old_canonical_object)
    new_surface = extract_authority_surface(delta_input.source_kind, delta_input.new_canonical_object)
    deltas = compare_authority_surfaces(old_surface, new_surface, delta_input)

    old_att_id = _get_attestation_id(delta_input.old_attestation)
    new_att_id = _get_attestation_id(delta_input.new_attestation)

    import hashlib as _hashlib
    seed = json.dumps(authority_delta_report_to_dict(
        AuthorityDeltaReport(
            report_id="",
            source_kind=delta_input.source_kind,
            deltas=deltas,
            highest_severity=AuthorityDeltaSeverity.INFO,
            requires_operator_consent=False,
            requires_evidence=False,
            summary="",
            safe_to_auto_accept=True,
            old_attestation_id=old_att_id,
            new_attestation_id=new_att_id,
        )
    ), sort_keys=True)
    report_id = f"adr_{delta_input.source_kind}_{_hashlib.sha256(seed.encode('utf-8')).hexdigest()[:24]}"

    highest_sev = highest_authority_delta_severity(deltas)
    any_consent = any(d.requires_operator_consent for d in deltas)
    any_evidence = any(d.requires_evidence for d in deltas)
    safe = highest_sev not in {AuthorityDeltaSeverity.HIGH, AuthorityDeltaSeverity.CRITICAL} and not any_consent
    summary = summarize_authority_delta_report(deltas)

    return AuthorityDeltaReport(
        report_id=report_id,
        source_kind=delta_input.source_kind,
        deltas=deltas,
        highest_severity=highest_sev,
        requires_operator_consent=any_consent,
        requires_evidence=any_evidence,
        summary=summary,
        safe_to_auto_accept=safe,
        old_attestation_id=old_att_id,
        new_attestation_id=new_att_id,
    )


__all__ = [
    "AuthorityDeltaType",
    "AuthorityDeltaSeverity",
    "AuthorityDelta",
    "AuthorityDeltaInput",
    "AuthorityDeltaReport",
    "RISK_CEILING_ORDER",
    "CLAIM_STATUS_ORDER",
    "DOCTRINE_STATUS_ORDER",
    "CAPABILITY_STATUS_ORDER",
    "authority_delta_to_dict",
    "authority_delta_report_to_dict",
    "classify_authority_delta",
    "compare_authority_surfaces",
    "detect_authority_deltas",
    "extract_authority_surface",
    "highest_authority_delta_severity",
    "resolve_authority_delta_severity",
    "authority_delta_requires_consent",
    "authority_delta_requires_evidence",
    "summarize_authority_delta_report",
]
