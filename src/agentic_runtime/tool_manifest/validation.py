"""Risk, permission, and safety metadata validation for tool manifests (P1.3.1).

Validation inspects manifests only — it does not grant authority, register tools,
or execute anything. Unsafe metadata must block normalization into ToolCapability.
"""
from __future__ import annotations

import re
from typing import Any

from .enums import (
    CapabilityType,
    DataAccessType,
    ExecutionEnvironment,
    PluginOrigin,
    PluginStatus,
    Reversibility,
    RiskClass,
    SideEffectType,
    TraceLevel,
    TrustLevel,
    ValidationSeverity,
    is_high_risk_class,
)
from .manifest import PluginManifest, ToolManifest, ValidationIssue

# --------------------------------------------------------------------------- #
#  Stable validation codes
# --------------------------------------------------------------------------- #
TOOL_ID_MISSING = "TOOL_ID_MISSING"
PLUGIN_ID_MISSING = "PLUGIN_ID_MISSING"
NAME_MISSING = "NAME_MISSING"
DESCRIPTION_MISSING = "DESCRIPTION_MISSING"
VERSION_MISSING = "VERSION_MISSING"
INPUT_SCHEMA_MISSING = "INPUT_SCHEMA_MISSING"
OUTPUT_SCHEMA_MISSING = "OUTPUT_SCHEMA_MISSING"
CAPABILITY_TYPES_MISSING = "CAPABILITY_TYPES_MISSING"
CATEGORY_MISSING = "CATEGORY_MISSING"
ORIGIN_MISSING = "ORIGIN_MISSING"
TRUST_LEVEL_MISSING = "TRUST_LEVEL_MISSING"
STATUS_MISSING = "STATUS_MISSING"

R0_HAS_SIDE_EFFECTS = "R0_HAS_SIDE_EFFECTS"
R1_HAS_WRITE_OR_EXECUTE = "R1_HAS_WRITE_OR_EXECUTE"
R2_REQUIRES_REVERSIBILITY = "R2_REQUIRES_REVERSIBILITY"
R3_REQUIRES_DATA_ACCESS = "R3_REQUIRES_DATA_ACCESS"
R3_REQUIRES_TRACE = "R3_REQUIRES_TRACE"
HIGH_RISK_REQUIRES_APPROVAL = "HIGH_RISK_REQUIRES_APPROVAL"
R5_REQUIRES_EVIDENCE = "R5_REQUIRES_EVIDENCE"
DISABLED_R6_REQUIRED = "DISABLED_R6_REQUIRED"
INVALID_TRACE_LEVEL_FOR_RISK = "INVALID_TRACE_LEVEL_FOR_RISK"

LOCAL_WRITE_RISK_TOO_LOW = "LOCAL_WRITE_RISK_TOO_LOW"
EXTERNAL_WRITE_RISK_TOO_LOW = "EXTERNAL_WRITE_RISK_TOO_LOW"
SECRET_ACCESS_REQUIRES_DATA_ACCESS = "SECRET_ACCESS_REQUIRES_DATA_ACCESS"
NETWORK_REQUIRES_NETWORK_POLICY = "NETWORK_REQUIRES_NETWORK_POLICY"
PROCESS_EXECUTION_UNKNOWN_ENV = "PROCESS_EXECUTION_UNKNOWN_ENV"
STATE_CHANGE_MISSING_PREDICTED_EFFECT = "STATE_CHANGE_MISSING_PREDICTED_EFFECT"

PERMISSIONS_REQUIRED_MISSING = "PERMISSIONS_REQUIRED_MISSING"
HIGH_RISK_EMPTY_PERMISSIONS = "HIGH_RISK_EMPTY_PERMISSIONS"
SECRET_ACCESS_REQUIRES_SECRET_POLICY = "SECRET_ACCESS_REQUIRES_SECRET_POLICY"

LOCAL_WRITE_REQUIRES_REVERSIBILITY = "LOCAL_WRITE_REQUIRES_REVERSIBILITY"
EXTERNAL_WRITE_REVERSIBILITY_MISMATCH = "EXTERNAL_WRITE_REVERSIBILITY_MISMATCH"
IRREVERSIBLE_TOOL_TOO_LOW_RISK = "IRREVERSIBLE_TOOL_TOO_LOW_RISK"
DELETE_LIKE_REVERSIBILITY_WARNING = "DELETE_LIKE_REVERSIBILITY_WARNING"
DRAFT_ONLY_EXTERNAL_WRITE = "DRAFT_ONLY_EXTERNAL_WRITE"

EXTERNAL_WRITE_REQUIRES_APPROVAL = "EXTERNAL_WRITE_REQUIRES_APPROVAL"
SECRET_ACCESS_REQUIRES_APPROVAL = "SECRET_ACCESS_REQUIRES_APPROVAL"
PROCESS_EXECUTION_REQUIRES_APPROVAL = "PROCESS_EXECUTION_REQUIRES_APPROVAL"
UNTRUSTED_ORIGIN_REQUIRES_APPROVAL = "UNTRUSTED_ORIGIN_REQUIRES_APPROVAL"

UNKNOWN_ORIGIN_HIGH_TRUST = "UNKNOWN_ORIGIN_HIGH_TRUST"
EXTERNAL_HIGH_TRUST_WARNING = "EXTERNAL_HIGH_TRUST_WARNING"
GENERATED_ACTIVE_STATUS = "GENERATED_ACTIVE_STATUS"
UNKNOWN_ORIGIN_HIGH_RISK = "UNKNOWN_ORIGIN_HIGH_RISK"
UNTRUSTED_PLUGIN_HIGH_RISK = "UNTRUSTED_PLUGIN_HIGH_RISK"
UNTRUSTED_PLUGIN_ENABLED = "UNTRUSTED_PLUGIN_ENABLED"
PLUGIN_STATUS_BLOCKS_ENABLED_TOOL = "PLUGIN_STATUS_BLOCKS_ENABLED_TOOL"

DATA_ACCESS_SECRETS_NO_POLICY = "DATA_ACCESS_SECRETS_NO_POLICY"
DATA_ACCESS_EXTERNAL_NO_POLICY = "DATA_ACCESS_EXTERNAL_NO_POLICY"
OPERATOR_PRIVATE_RISK_TOO_LOW = "OPERATOR_PRIVATE_RISK_TOO_LOW"
LOCAL_SENSITIVE_TRACE_TOO_LOW = "LOCAL_SENSITIVE_TRACE_TOO_LOW"
R0_UNSAFE_DATA_ACCESS = "R0_UNSAFE_DATA_ACCESS"

TRACE_LEVEL_TOO_LOW = "TRACE_LEVEL_TOO_LOW"
EVIDENCE_RECOMMENDED = "EVIDENCE_RECOMMENDED"

PREDICTED_EFFECT_AFFECTED_OBJECTS_EMPTY = "PREDICTED_EFFECT_AFFECTED_OBJECTS_EMPTY"
PREDICTED_EFFECT_REVERSIBILITY_MISMATCH = "PREDICTED_EFFECT_REVERSIBILITY_MISMATCH"

TOOL_ROLE_MISSING = "TOOL_ROLE_MISSING"
ACTION_TOOL_MISSING_STATE_DELTA_CONTRACT = "ACTION_TOOL_MISSING_STATE_DELTA_CONTRACT"
STATE_CHANGING_TOOL_MISSING_SIMULATION_PROFILE = "STATE_CHANGING_TOOL_MISSING_SIMULATION_PROFILE"
EXTERNAL_TOOL_MISSING_SAFETY_SURFACE = "EXTERNAL_TOOL_MISSING_SAFETY_SURFACE"
HIGH_RISK_ACTION_MISSING_SAFETY_SURFACE = "HIGH_RISK_ACTION_MISSING_SAFETY_SURFACE"
EXTERNAL_STATE_CHANGE_MISSING_DELTA_CONTRACT = "EXTERNAL_STATE_CHANGE_MISSING_DELTA_CONTRACT"
R5_TOOL_MISSING_STATE_DELTA_CONTRACT = "R5_TOOL_MISSING_STATE_DELTA_CONTRACT"
SECRET_TOOL_MISSING_SAFETY_SURFACE = "SECRET_TOOL_MISSING_SAFETY_SURFACE"
R5_EXTERNAL_ACTION_WITHOUT_DELTA_OR_SAFETY_SURFACE = "R5_EXTERNAL_ACTION_WITHOUT_DELTA_OR_SAFETY_SURFACE"
UNKNOWN_TOOL_ROLE_FOR_HIGH_RISK_ACTION = "UNKNOWN_TOOL_ROLE_FOR_HIGH_RISK_ACTION"

_DELETE_LIKE_RE = re.compile(r"\b(delete|remove|destroy|purge|wipe)\b", re.IGNORECASE)

_RISK_ORDER = {
    RiskClass.R0: 0,
    RiskClass.R1: 1,
    RiskClass.R2: 2,
    RiskClass.R3: 3,
    RiskClass.R4: 4,
    RiskClass.R5: 5,
    RiskClass.R6: 6,
}

_TRACE_ORDER = {
    TraceLevel.NONE: 0,
    TraceLevel.MINIMAL: 1,
    TraceLevel.STANDARD: 2,
    TraceLevel.DETAILED: 3,
    TraceLevel.FORENSIC: 4,
}

_R0_FORBIDDEN_CAPABILITIES = frozenset({
    CapabilityType.WRITE,
    CapabilityType.EXECUTE,
    CapabilityType.SEND,
})

_R0_FORBIDDEN_SIDE_EFFECTS = frozenset({
    SideEffectType.LOCAL_WRITE,
    SideEffectType.EXTERNAL_WRITE,
    SideEffectType.EXTERNAL_READ,
    SideEffectType.SECRET_ACCESS,
    SideEffectType.NETWORK,
    SideEffectType.PROCESS_EXECUTION,
    SideEffectType.STATE_CHANGE,
})

_R1_FORBIDDEN_CAPABILITIES = frozenset({
    CapabilityType.WRITE,
    CapabilityType.EXECUTE,
})

_R1_FORBIDDEN_SIDE_EFFECTS = frozenset({
    SideEffectType.LOCAL_WRITE,
    SideEffectType.EXTERNAL_WRITE,
    SideEffectType.PROCESS_EXECUTION,
    SideEffectType.STATE_CHANGE,
})

_R2_ALLOWED_REVERSIBILITY = frozenset({
    Reversibility.REVERSIBLE,
    Reversibility.PARTIALLY_REVERSIBLE,
    Reversibility.DRAFT_ONLY,
})

_STATE_CHANGING_SIDE_EFFECTS = frozenset({
    SideEffectType.LOCAL_WRITE,
    SideEffectType.EXTERNAL_WRITE,
    SideEffectType.STATE_CHANGE,
})

_PERMISSION_CAPABILITIES = frozenset({
    CapabilityType.WRITE,
    CapabilityType.EXECUTE,
    CapabilityType.SEND,
    CapabilityType.SCHEDULE,
})

_UNTRUSTED_ORIGINS = frozenset({
    PluginOrigin.GENERATED,
    PluginOrigin.IMPORTED,
    PluginOrigin.UNKNOWN,
    PluginOrigin.EXPERIMENTAL,
})

_BLOCKED_PLUGIN_STATUSES = frozenset({
    PluginStatus.DEPRECATED,
    PluginStatus.QUARANTINED,
    PluginStatus.INVALID,
})

_R0_SAFE_DATA_ACCESS = frozenset({
    DataAccessType.NONE,
    DataAccessType.LOCAL_PROJECT,
})


def _issue(
    code: str,
    message: str,
    field: str | None,
    severity: ValidationSeverity,
) -> ValidationIssue:
    return ValidationIssue(code=code, message=message, field=field, severity=severity)


def _blank(value: str | None) -> bool:
    return value is None or not str(value).strip()


def _risk_at_least(risk: RiskClass, minimum: RiskClass) -> bool:
    return _RISK_ORDER[risk] >= _RISK_ORDER[minimum]


def _trace_at_least(level: TraceLevel, minimum: TraceLevel) -> bool:
    return _TRACE_ORDER[level] >= _TRACE_ORDER[minimum]


def _side_effect_set(tool: ToolManifest) -> set[SideEffectType]:
    return set(tool.side_effects)


def _capability_set(tool: ToolManifest) -> set[CapabilityType]:
    return set(tool.capability_types)


def _data_access_set(tool: ToolManifest) -> set[DataAccessType]:
    return set(tool.data_access)


def _plugin_network_policy(plugin: PluginManifest | None) -> bool:
    if plugin is not None and plugin.network_policy is not None:
        return True
    return False


def _plugin_secret_policy(plugin: PluginManifest | None) -> bool:
    if plugin is not None and plugin.secret_policy is not None:
        return True
    return False


def _has_network_policy(tool: ToolManifest, plugin: PluginManifest | None) -> bool:
    if _plugin_network_policy(plugin):
        return True
    if plugin is not None and isinstance(plugin.compatibility, dict):
        if plugin.compatibility.get("network_policy"):
            return True
    return False


def _has_secret_policy(tool: ToolManifest, plugin: PluginManifest | None) -> bool:
    if _plugin_secret_policy(plugin):
        return True
    compat = plugin.compatibility if plugin else {}
    if isinstance(compat, dict) and compat.get("secret_policy"):
        return True
    return False


def _requires_permissions(tool: ToolManifest) -> bool:
    caps = _capability_set(tool)
    effects = _side_effect_set(tool)
    if caps & _PERMISSION_CAPABILITIES:
        return True
    if SideEffectType.EXTERNAL_WRITE in effects:
        return True
    if SideEffectType.SECRET_ACCESS in effects:
        return True
    if SideEffectType.PROCESS_EXECUTION in effects:
        return True
    return False


def _is_delete_like(tool: ToolManifest) -> bool:
    text = f"{tool.name} {tool.description}"
    return bool(_DELETE_LIKE_RE.search(text))


def _validate_tool_identity(tool: ToolManifest) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if _blank(tool.tool_id):
        issues.append(_issue(TOOL_ID_MISSING, "tool_id is required", "tool_id", ValidationSeverity.ERROR))
    if _blank(tool.plugin_id):
        issues.append(_issue(PLUGIN_ID_MISSING, "plugin_id is required", "plugin_id", ValidationSeverity.ERROR))
    if _blank(tool.name):
        issues.append(_issue(NAME_MISSING, "name is required", "name", ValidationSeverity.ERROR))
    if _blank(tool.description):
        issues.append(_issue(DESCRIPTION_MISSING, "description is required", "description", ValidationSeverity.ERROR))
    if not isinstance(tool.input_schema, dict):
        issues.append(_issue(INPUT_SCHEMA_MISSING, "input_schema must be a dict", "input_schema", ValidationSeverity.ERROR))
    if not isinstance(tool.output_schema, dict):
        issues.append(_issue(OUTPUT_SCHEMA_MISSING, "output_schema must be a dict", "output_schema", ValidationSeverity.ERROR))
    if not tool.capability_types:
        issues.append(_issue(CAPABILITY_TYPES_MISSING, "capability_types must not be empty", "capability_types", ValidationSeverity.ERROR))
    if tool.category is None:
        issues.append(_issue(CATEGORY_MISSING, "category is required", "category", ValidationSeverity.ERROR))
    return issues


def _validate_plugin_identity(plugin: PluginManifest) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if _blank(plugin.plugin_id):
        issues.append(_issue(PLUGIN_ID_MISSING, "plugin_id is required", "plugin_id", ValidationSeverity.ERROR))
    if _blank(plugin.name):
        issues.append(_issue(NAME_MISSING, "name is required", "name", ValidationSeverity.ERROR))
    if _blank(plugin.version):
        issues.append(_issue(VERSION_MISSING, "version is required", "version", ValidationSeverity.ERROR))
    if _blank(plugin.description):
        issues.append(_issue(DESCRIPTION_MISSING, "description is required", "description", ValidationSeverity.ERROR))
    if plugin.origin is None:
        issues.append(_issue(ORIGIN_MISSING, "origin is required", "origin", ValidationSeverity.ERROR))
    if plugin.trust_level is None:
        issues.append(_issue(TRUST_LEVEL_MISSING, "trust_level is required", "trust_level", ValidationSeverity.ERROR))
    if plugin.status is None:
        issues.append(_issue(STATUS_MISSING, "status is required", "status", ValidationSeverity.ERROR))
    return issues


def validate_tool_risk_metadata(tool: ToolManifest) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    caps = _capability_set(tool)
    effects = _side_effect_set(tool)
    data = _data_access_set(tool)

    if tool.risk_class is RiskClass.R0:
        bad_caps = caps & _R0_FORBIDDEN_CAPABILITIES
        bad_effects = effects & _R0_FORBIDDEN_SIDE_EFFECTS
        if bad_caps or bad_effects:
            issues.append(_issue(
                R0_HAS_SIDE_EFFECTS,
                "R0 tools must not declare write, execute, send, or unsafe side effects",
                "risk_class",
                ValidationSeverity.ERROR,
            ))
        unsafe_data = data - _R0_SAFE_DATA_ACCESS
        if unsafe_data:
            issues.append(_issue(
                R0_UNSAFE_DATA_ACCESS,
                "R0 tools may only access none or local non-sensitive data",
                "data_access",
                ValidationSeverity.ERROR,
            ))

    if tool.risk_class is RiskClass.R1:
        if caps & _R1_FORBIDDEN_CAPABILITIES or effects & _R1_FORBIDDEN_SIDE_EFFECTS:
            issues.append(_issue(
                R1_HAS_WRITE_OR_EXECUTE,
                "R1 tools must not write or execute",
                "risk_class",
                ValidationSeverity.ERROR,
            ))

    if tool.risk_class is RiskClass.R2:
        if tool.reversibility not in _R2_ALLOWED_REVERSIBILITY:
            issues.append(_issue(
                R2_REQUIRES_REVERSIBILITY,
                "R2 tools must declare reversibility as reversible, partially_reversible, or draft_only",
                "reversibility",
                ValidationSeverity.ERROR,
            ))

    if tool.risk_class is RiskClass.R3:
        if not tool.data_access:
            issues.append(_issue(
                R3_REQUIRES_DATA_ACCESS,
                "R3 tools must declare data_access",
                "data_access",
                ValidationSeverity.ERROR,
            ))
        if not _trace_at_least(tool.trace_level, TraceLevel.STANDARD):
            issues.append(_issue(
                R3_REQUIRES_TRACE,
                "R3 tools must use trace_level at least standard",
                "trace_level",
                ValidationSeverity.ERROR,
            ))

    if tool.risk_class is RiskClass.R4 and not tool.requires_approval:
        issues.append(_issue(
            HIGH_RISK_REQUIRES_APPROVAL,
            "R4 tools must require approval",
            "requires_approval",
            ValidationSeverity.ERROR,
        ))

    if tool.risk_class is RiskClass.R5:
        if not tool.requires_approval:
            issues.append(_issue(
                HIGH_RISK_REQUIRES_APPROVAL,
                "R5 tools must require approval",
                "requires_approval",
                ValidationSeverity.ERROR,
            ))
        if not tool.evidence_required:
            issues.append(_issue(
                R5_REQUIRES_EVIDENCE,
                "R5 tools must require evidence",
                "evidence_required",
                ValidationSeverity.ERROR,
            ))

    if tool.risk_class is RiskClass.R6 and tool.enabled:
        issues.append(_issue(
            DISABLED_R6_REQUIRED,
            "R6 tools must not be enabled",
            "enabled",
            ValidationSeverity.CRITICAL,
        ))

    if is_high_risk_class(tool.risk_class):
        if tool.trace_level in {TraceLevel.NONE, TraceLevel.MINIMAL}:
            issues.append(_issue(
                INVALID_TRACE_LEVEL_FOR_RISK,
                "R4/R5/R6 tools must not use trace_level none or minimal",
                "trace_level",
                ValidationSeverity.ERROR,
            ))

    if tool.risk_class in {RiskClass.R2, RiskClass.R3}:
        if not _trace_at_least(tool.trace_level, TraceLevel.STANDARD):
            issues.append(_issue(
                TRACE_LEVEL_TOO_LOW,
                "R2/R3 tools should use trace_level standard or higher",
                "trace_level",
                ValidationSeverity.ERROR,
            ))

    if is_high_risk_class(tool.risk_class):
        if not _trace_at_least(tool.trace_level, TraceLevel.DETAILED):
            issues.append(_issue(
                TRACE_LEVEL_TOO_LOW,
                "R4/R5/R6 tools must use trace_level detailed or forensic",
                "trace_level",
                ValidationSeverity.ERROR,
            ))

    return issues


def validate_tool_permission_metadata(
    tool: ToolManifest,
    plugin: PluginManifest | None = None,
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    effects = _side_effect_set(tool)
    data = _data_access_set(tool)

    if _requires_permissions(tool) and not tool.permissions_required:
        severity = ValidationSeverity.ERROR
        code = PERMISSIONS_REQUIRED_MISSING
        if tool.risk_class in {RiskClass.R4, RiskClass.R5}:
            severity = ValidationSeverity.CRITICAL
            code = HIGH_RISK_EMPTY_PERMISSIONS
        issues.append(_issue(
            code,
            "tools with write/execute/send/schedule or sensitive side effects must declare permissions_required",
            "permissions_required",
            severity,
        ))

    if tool.risk_class in {RiskClass.R4, RiskClass.R5} and not tool.permissions_required:
        issues.append(_issue(
            HIGH_RISK_EMPTY_PERMISSIONS,
            "R4/R5 tools must declare permissions_required",
            "permissions_required",
            ValidationSeverity.CRITICAL,
        ))

    touches_secrets = (
        SideEffectType.SECRET_ACCESS in effects
        or DataAccessType.SECRETS in data
    )
    if touches_secrets and not _has_secret_policy(tool, plugin):
        issues.append(_issue(
            SECRET_ACCESS_REQUIRES_SECRET_POLICY,
            "tools touching secrets require explicit secret_policy at plugin level",
            "secret_policy",
            ValidationSeverity.CRITICAL,
        ))

    touches_network = (
        SideEffectType.NETWORK in effects
        or SideEffectType.EXTERNAL_WRITE in effects
        or SideEffectType.EXTERNAL_READ in effects
        or DataAccessType.EXTERNAL in data
    )
    if touches_network and not _has_network_policy(tool, plugin):
        issues.append(_issue(
            NETWORK_REQUIRES_NETWORK_POLICY,
            "external or networked tools require explicit network_policy at plugin level",
            "network_policy",
            ValidationSeverity.CRITICAL,
        ))

    return issues


def validate_tool_side_effect_metadata(
    tool: ToolManifest,
    plugin: PluginManifest | None = None,
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    effects = _side_effect_set(tool)
    data = _data_access_set(tool)

    if SideEffectType.LOCAL_WRITE in effects:
        if tool.risk_class in {RiskClass.R0, RiskClass.R1}:
            issues.append(_issue(
                LOCAL_WRITE_RISK_TOO_LOW,
                "local_write side effects require risk_class R2 or higher",
                "side_effects",
                ValidationSeverity.ERROR,
            ))

    if SideEffectType.EXTERNAL_WRITE in effects:
        if not _risk_at_least(tool.risk_class, RiskClass.R4):
            issues.append(_issue(
                EXTERNAL_WRITE_RISK_TOO_LOW,
                "external_write side effects require risk_class R4 or higher",
                "side_effects",
                ValidationSeverity.ERROR,
            ))

    if SideEffectType.SECRET_ACCESS in effects:
        if DataAccessType.SECRETS not in data:
            issues.append(_issue(
                SECRET_ACCESS_REQUIRES_DATA_ACCESS,
                "secret_access side effects require secrets in data_access",
                "data_access",
                ValidationSeverity.ERROR,
            ))

    if SideEffectType.NETWORK in effects and not _has_network_policy(tool, plugin):
        issues.append(_issue(
            NETWORK_REQUIRES_NETWORK_POLICY,
            "network side effects require network_policy at plugin level",
            "network_policy",
            ValidationSeverity.CRITICAL,
        ))

    if SideEffectType.PROCESS_EXECUTION in effects:
        if tool.execution_environment is ExecutionEnvironment.UNKNOWN:
            issues.append(_issue(
                PROCESS_EXECUTION_UNKNOWN_ENV,
                "process_execution side effects require a known execution_environment",
                "execution_environment",
                ValidationSeverity.ERROR,
            ))

    if DataAccessType.SECRETS in data and not _has_secret_policy(tool, plugin):
        issues.append(_issue(
            DATA_ACCESS_SECRETS_NO_POLICY,
            "data_access including secrets requires secret_policy at plugin level",
            "secret_policy",
            ValidationSeverity.CRITICAL,
        ))

    if DataAccessType.EXTERNAL in data and not _has_network_policy(tool, plugin):
        issues.append(_issue(
            DATA_ACCESS_EXTERNAL_NO_POLICY,
            "data_access including external requires network_policy at plugin level",
            "network_policy",
            ValidationSeverity.CRITICAL,
        ))

    if DataAccessType.OPERATOR_PRIVATE in data and not _risk_at_least(tool.risk_class, RiskClass.R3):
        issues.append(_issue(
            OPERATOR_PRIVATE_RISK_TOO_LOW,
            "operator_private data access requires risk_class R3 or higher",
            "data_access",
            ValidationSeverity.ERROR,
        ))

    if DataAccessType.LOCAL_SENSITIVE in data:
        if not _trace_at_least(tool.trace_level, TraceLevel.STANDARD):
            issues.append(_issue(
                LOCAL_SENSITIVE_TRACE_TOO_LOW,
                "local_sensitive data access requires trace_level standard or higher",
                "trace_level",
                ValidationSeverity.ERROR,
            ))

    return issues


def _validate_reversibility_rules(tool: ToolManifest) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    effects = _side_effect_set(tool)

    if SideEffectType.EXTERNAL_WRITE in effects:
        if tool.reversibility is Reversibility.REVERSIBLE:
            issues.append(_issue(
                EXTERNAL_WRITE_REVERSIBILITY_MISMATCH,
                "external_write tools cannot declare fully reversible unless draft_only",
                "reversibility",
                ValidationSeverity.ERROR,
            ))

    if tool.reversibility is Reversibility.IRREVERSIBLE:
        if not _risk_at_least(tool.risk_class, RiskClass.R4):
            issues.append(_issue(
                IRREVERSIBLE_TOOL_TOO_LOW_RISK,
                "irreversible tools must be at least R4",
                "reversibility",
                ValidationSeverity.ERROR,
            ))

    if SideEffectType.LOCAL_WRITE in effects:
        if tool.reversibility in {Reversibility.NONE, Reversibility.UNKNOWN}:
            issues.append(_issue(
                LOCAL_WRITE_REQUIRES_REVERSIBILITY,
                "local_write tools must declare meaningful reversibility metadata",
                "reversibility",
                ValidationSeverity.ERROR,
            ))

    if _is_delete_like(tool):
        if tool.reversibility not in {
            Reversibility.IRREVERSIBLE,
            Reversibility.PARTIALLY_REVERSIBLE,
        }:
            issues.append(_issue(
                DELETE_LIKE_REVERSIBILITY_WARNING,
                "delete-like tools should declare irreversible or partially_reversible reversibility",
                "reversibility",
                ValidationSeverity.WARNING,
            ))

    if tool.reversibility is Reversibility.DRAFT_ONLY:
        if SideEffectType.EXTERNAL_WRITE in effects:
            issues.append(_issue(
                DRAFT_ONLY_EXTERNAL_WRITE,
                "draft_only tools must not declare external_write side effects",
                "side_effects",
                ValidationSeverity.ERROR,
            ))

    return issues


def _validate_approval_rules(
    tool: ToolManifest,
    plugin: PluginManifest | None = None,
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    effects = _side_effect_set(tool)

    if tool.risk_class in {RiskClass.R4, RiskClass.R5, RiskClass.R6}:
        if not tool.requires_approval:
            issues.append(_issue(
                HIGH_RISK_REQUIRES_APPROVAL,
                "high-risk tools must require approval",
                "requires_approval",
                ValidationSeverity.ERROR,
            ))

    if SideEffectType.EXTERNAL_WRITE in effects and not tool.requires_approval:
        issues.append(_issue(
            EXTERNAL_WRITE_REQUIRES_APPROVAL,
            "external_write tools must require approval",
            "requires_approval",
            ValidationSeverity.ERROR,
        ))

    if SideEffectType.SECRET_ACCESS in effects and not tool.requires_approval:
        issues.append(_issue(
            SECRET_ACCESS_REQUIRES_APPROVAL,
            "secret_access tools must require approval",
            "requires_approval",
            ValidationSeverity.ERROR,
        ))

    if SideEffectType.PROCESS_EXECUTION in effects and not tool.requires_approval:
        sandbox_ok = (
            tool.risk_class is RiskClass.R2
            and tool.execution_environment is ExecutionEnvironment.SANDBOX
        )
        if not sandbox_ok:
            issues.append(_issue(
                PROCESS_EXECUTION_REQUIRES_APPROVAL,
                "process_execution tools must require approval unless R2 sandbox execution is declared",
                "requires_approval",
                ValidationSeverity.ERROR,
            ))

    if plugin is not None and plugin.origin in _UNTRUSTED_ORIGINS:
        if _risk_at_least(tool.risk_class, RiskClass.R3) and not tool.requires_approval:
            issues.append(_issue(
                UNTRUSTED_ORIGIN_REQUIRES_APPROVAL,
                "tools from generated/imported/unknown/experimental plugins at R3+ must require approval",
                "requires_approval",
                ValidationSeverity.ERROR,
            ))

    return issues


def _validate_trace_evidence_rules(tool: ToolManifest) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    effects = _side_effect_set(tool)

    needs_evidence = (
        SideEffectType.EXTERNAL_WRITE in effects
        or SideEffectType.SECRET_ACCESS in effects
        or SideEffectType.PROCESS_EXECUTION in effects
        or tool.reversibility is Reversibility.IRREVERSIBLE
    )
    if needs_evidence and not tool.evidence_required:
        issues.append(_issue(
            EVIDENCE_RECOMMENDED,
            "tools with external_write, secret_access, process_execution, or irreversible actions should require evidence",
            "evidence_required",
            ValidationSeverity.WARNING,
        ))

    return issues


def _validate_predicted_effect_rules(tool: ToolManifest) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    effects = _side_effect_set(tool)
    state_changing = effects & _STATE_CHANGING_SIDE_EFFECTS

    if state_changing and tool.predicted_effect is None:
        if tool.risk_class in {RiskClass.R4, RiskClass.R5}:
            severity = ValidationSeverity.ERROR
        elif tool.risk_class in {RiskClass.R2, RiskClass.R3}:
            severity = ValidationSeverity.WARNING
        else:
            severity = ValidationSeverity.WARNING
        issues.append(_issue(
            STATE_CHANGE_MISSING_PREDICTED_EFFECT,
            "state-changing tools should declare predicted_effect",
            "predicted_effect",
            severity,
        ))

    if tool.predicted_effect is not None and state_changing:
        if not tool.predicted_effect.affected_objects:
            issues.append(_issue(
                PREDICTED_EFFECT_AFFECTED_OBJECTS_EMPTY,
                "predicted_effect.affected_objects must not be empty for state-changing tools",
                "predicted_effect.affected_objects",
                ValidationSeverity.ERROR,
            ))

        pe = tool.predicted_effect
        if tool.reversibility is Reversibility.IRREVERSIBLE and pe.reversible:
            issues.append(_issue(
                PREDICTED_EFFECT_REVERSIBILITY_MISMATCH,
                "predicted_effect.reversible conflicts with irreversible tool reversibility",
                "predicted_effect.reversible",
                ValidationSeverity.ERROR,
            ))
        if tool.reversibility is Reversibility.REVERSIBLE and not pe.reversible:
            issues.append(_issue(
                PREDICTED_EFFECT_REVERSIBILITY_MISMATCH,
                "predicted_effect.reversible conflicts with reversible tool reversibility",
                "predicted_effect.reversible",
                ValidationSeverity.WARNING,
            ))

    return issues


def validate_tool_provenance_metadata(
    tool: ToolManifest,
    plugin: PluginManifest | None = None,
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if plugin is None:
        return issues

    if plugin.origin is PluginOrigin.UNKNOWN:
        if plugin.trust_level is TrustLevel.HIGH and plugin.status is PluginStatus.ACTIVE:
            issues.append(_issue(
                UNKNOWN_ORIGIN_HIGH_TRUST,
                "unknown origin plugins cannot be active with high trust",
                "trust_level",
                ValidationSeverity.ERROR,
            ))
        if tool.enabled and _risk_at_least(tool.risk_class, RiskClass.R3):
            issues.append(_issue(
                UNKNOWN_ORIGIN_HIGH_RISK,
                "enabled high-risk tools from unknown-origin plugins are not allowed",
                "origin",
                ValidationSeverity.CRITICAL,
            ))

    if plugin.origin is PluginOrigin.EXTERNAL and plugin.trust_level is TrustLevel.HIGH:
        issues.append(_issue(
            EXTERNAL_HIGH_TRUST_WARNING,
            "external plugins should not default to high trust without explicit review",
            "trust_level",
            ValidationSeverity.WARNING,
        ))

    if plugin.origin is PluginOrigin.GENERATED and plugin.status is PluginStatus.ACTIVE:
        issues.append(_issue(
            GENERATED_ACTIVE_STATUS,
            "generated plugins should use experimental or quarantined status",
            "status",
            ValidationSeverity.WARNING,
        ))

    if plugin.trust_level in {TrustLevel.UNTRUSTED, TrustLevel.UNKNOWN}:
        if tool.enabled:
            severity = ValidationSeverity.WARNING
            if _risk_at_least(tool.risk_class, RiskClass.R3):
                severity = ValidationSeverity.CRITICAL
                code = UNTRUSTED_PLUGIN_HIGH_RISK
            else:
                code = UNTRUSTED_PLUGIN_ENABLED
            issues.append(_issue(
                code,
                "untrusted plugin exposes an enabled tool",
                "trust_level",
                severity,
            ))

    if plugin.status in _BLOCKED_PLUGIN_STATUSES and tool.enabled:
        issues.append(_issue(
            PLUGIN_STATUS_BLOCKS_ENABLED_TOOL,
            "deprecated, quarantined, or invalid plugins must not expose enabled tools",
            "enabled",
            ValidationSeverity.ERROR,
        ))

    return issues


def _validate_plugin_provenance(plugin: PluginManifest) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if plugin.origin is PluginOrigin.UNKNOWN:
        if plugin.trust_level is TrustLevel.HIGH and plugin.status is PluginStatus.ACTIVE:
            issues.append(_issue(
                UNKNOWN_ORIGIN_HIGH_TRUST,
                "unknown origin plugins cannot be active with high trust",
                "trust_level",
                ValidationSeverity.ERROR,
            ))
    if plugin.origin is PluginOrigin.EXTERNAL and plugin.trust_level is TrustLevel.HIGH:
        issues.append(_issue(
            EXTERNAL_HIGH_TRUST_WARNING,
            "external plugins should not default to high trust without explicit review",
            "trust_level",
            ValidationSeverity.WARNING,
        ))
    if plugin.origin is PluginOrigin.GENERATED and plugin.status is PluginStatus.ACTIVE:
        issues.append(_issue(
            GENERATED_ACTIVE_STATUS,
            "generated plugins should use experimental or quarantined status",
            "status",
            ValidationSeverity.WARNING,
        ))
    return issues


def _is_action_tool_manifest(tool: ToolManifest) -> bool:
    caps = set(tool.capability_types)
    effects = set(tool.side_effects)
    action_caps = {
        CapabilityType.WRITE,
        CapabilityType.EXECUTE,
        CapabilityType.SEND,
        CapabilityType.SCHEDULE,
    }
    action_effects = {
        SideEffectType.LOCAL_WRITE,
        SideEffectType.EXTERNAL_WRITE,
        SideEffectType.PROCESS_EXECUTION,
        SideEffectType.STATE_CHANGE,
    }
    return bool(caps & action_caps) or bool(effects & action_effects)


def _is_state_changing_tool(tool: ToolManifest) -> bool:
    read_only = {SideEffectType.NONE, SideEffectType.LOCAL_READ, SideEffectType.EXTERNAL_READ}
    effects = set(tool.side_effects)
    return bool(effects - read_only)


def validate_tool_research_metadata(tool: ToolManifest) -> list[ValidationIssue]:
    """Validate research-inspired metadata (P1.3.7). Derived seeds do not block low-risk tools."""
    from .research_metadata import derive_tool_roles

    issues: list[ValidationIssue] = []
    effects = set(tool.side_effects)
    is_action = _is_action_tool_manifest(tool)
    is_state_changing = _is_state_changing_tool(tool)
    is_external_state = SideEffectType.EXTERNAL_WRITE in effects or CapabilityType.SEND in set(
        tool.capability_types
    )
    has_secrets = SideEffectType.SECRET_ACCESS in effects or DataAccessType.SECRETS in set(
        tool.data_access
    )
    derived_roles = derive_tool_roles(tool)

    if is_action and not tool.tool_roles and not derived_roles:
        issues.append(_issue(
            UNKNOWN_TOOL_ROLE_FOR_HIGH_RISK_ACTION,
            "high-risk action tool has no explicit or derivable tool role",
            "tool_roles",
            ValidationSeverity.CRITICAL if is_high_risk_class(tool.risk_class) else ValidationSeverity.ERROR,
        ))
    elif is_action and not tool.tool_roles:
        issues.append(_issue(
            TOOL_ROLE_MISSING,
            "action tool has no explicit tool_roles; derived roles used as seed",
            "tool_roles",
            ValidationSeverity.WARNING,
        ))

    if is_state_changing and tool.state_delta_contract is None:
        severity = ValidationSeverity.WARNING
        code = ACTION_TOOL_MISSING_STATE_DELTA_CONTRACT
        if tool.risk_class is RiskClass.R5:
            severity = ValidationSeverity.ERROR
            code = R5_TOOL_MISSING_STATE_DELTA_CONTRACT
        elif is_external_state:
            severity = ValidationSeverity.ERROR
            code = EXTERNAL_STATE_CHANGE_MISSING_DELTA_CONTRACT
        issues.append(_issue(
            code,
            "state-changing tool missing explicit state_delta_contract",
            "state_delta_contract",
            severity,
        ))

    if (
        is_state_changing
        and tool.simulation_profile is None
        and _RISK_ORDER[tool.risk_class] >= _RISK_ORDER[RiskClass.R2]
    ):
        issues.append(_issue(
            STATE_CHANGING_TOOL_MISSING_SIMULATION_PROFILE,
            "state-changing tool missing explicit simulation_profile",
            "simulation_profile",
            ValidationSeverity.WARNING,
        ))

    if is_external_state and tool.safety_surface is None:
        issues.append(_issue(
            EXTERNAL_TOOL_MISSING_SAFETY_SURFACE,
            "external state-changing tool missing explicit safety_surface",
            "safety_surface",
            ValidationSeverity.ERROR,
        ))

    if is_high_risk_class(tool.risk_class) and is_action and tool.safety_surface is None:
        severity = ValidationSeverity.ERROR if tool.risk_class in {RiskClass.R5, RiskClass.R6} else ValidationSeverity.WARNING
        issues.append(_issue(
            HIGH_RISK_ACTION_MISSING_SAFETY_SURFACE,
            "high-risk action tool missing explicit safety_surface",
            "safety_surface",
            severity,
        ))

    if has_secrets and tool.safety_surface is None:
        issues.append(_issue(
            SECRET_TOOL_MISSING_SAFETY_SURFACE,
            "secret-access tool missing explicit safety_surface",
            "safety_surface",
            ValidationSeverity.ERROR,
        ))

    if (
        tool.risk_class is RiskClass.R5
        and is_external_state
        and tool.state_delta_contract is None
        and tool.safety_surface is None
    ):
        issues.append(_issue(
            R5_EXTERNAL_ACTION_WITHOUT_DELTA_OR_SAFETY_SURFACE,
            "R5 external action missing both state_delta_contract and safety_surface",
            None,
            ValidationSeverity.CRITICAL,
        ))

    return issues


def _dedupe_issues(issues: list[ValidationIssue]) -> list[ValidationIssue]:
    severity_rank = {
        ValidationSeverity.INFO: 0,
        ValidationSeverity.WARNING: 1,
        ValidationSeverity.ERROR: 2,
        ValidationSeverity.CRITICAL: 3,
    }
    best: dict[tuple[str, str | None], ValidationIssue] = {}
    for issue in issues:
        key = (issue.code, issue.field)
        existing = best.get(key)
        if existing is None or severity_rank[issue.severity] > severity_rank[existing.severity]:
            best[key] = issue
    return list(best.values())


def validate_plugin_manifest(plugin: PluginManifest) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    issues.extend(_validate_plugin_identity(plugin))
    issues.extend(_validate_plugin_provenance(plugin))
    return _dedupe_issues(issues)


def validate_tool_manifest(
    tool: ToolManifest,
    plugin: PluginManifest | None = None,
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    issues.extend(_validate_tool_identity(tool))
    issues.extend(validate_tool_risk_metadata(tool))
    issues.extend(validate_tool_permission_metadata(tool, plugin))
    issues.extend(validate_tool_side_effect_metadata(tool, plugin))
    issues.extend(_validate_reversibility_rules(tool))
    issues.extend(_validate_approval_rules(tool, plugin))
    issues.extend(_validate_trace_evidence_rules(tool))
    issues.extend(_validate_predicted_effect_rules(tool))
    issues.extend(validate_tool_provenance_metadata(tool, plugin))
    issues.extend(validate_tool_research_metadata(tool))
    return _dedupe_issues(issues)


def has_blocking_validation_issues(issues: list[ValidationIssue]) -> bool:
    return any(
        issue.severity in {ValidationSeverity.ERROR, ValidationSeverity.CRITICAL}
        for issue in issues
    )


def is_tool_manifest_valid(
    tool: ToolManifest,
    plugin: PluginManifest | None = None,
) -> bool:
    return not has_blocking_validation_issues(validate_tool_manifest(tool, plugin))


def is_plugin_manifest_valid(plugin: PluginManifest) -> bool:
    return not has_blocking_validation_issues(validate_plugin_manifest(plugin))


def validation_summary(issues: list[ValidationIssue]) -> dict[str, Any]:
    counts = {level.value: 0 for level in ValidationSeverity}
    codes: list[str] = []
    for issue in issues:
        counts[issue.severity.value] += 1
        codes.append(issue.code)
    return {
        "total": len(issues),
        "info": counts[ValidationSeverity.INFO.value],
        "warning": counts[ValidationSeverity.WARNING.value],
        "error": counts[ValidationSeverity.ERROR.value],
        "critical": counts[ValidationSeverity.CRITICAL.value],
        "blocking": has_blocking_validation_issues(issues),
        "codes": codes,
    }
