"""Quarantine and validation error handling for tool manifests (P1.3.4).

Quarantine isolates unsafe manifests — it does not delete them, execute tools,
or implement approval workflow.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from ..core_types import new_id
from . import _serde as s
from .capability import ToolRegistryEntry
from .enums import (
    CapabilityStatus,
    ExecutionEnvironment,
    PluginOrigin,
    PluginStatus,
    RegistryEntryStatus,
    Reversibility,
    RiskClass,
    SideEffectType,
    TrustLevel,
    is_high_risk_class,
)
from .loader import (
    MANIFEST_PARSE_ERROR,
    MANIFEST_UNSUPPORTED_FORMAT,
    DUPLICATE_TOOL_ID_IN_BUNDLE,
    ManifestLoadResult,
    ManifestLoadStatus,
)
from .manifest import PluginManifest, ToolManifest, ValidationIssue
from .validation import (
    DISABLED_R6_REQUIRED,
    EXTERNAL_WRITE_REQUIRES_APPROVAL,
    HIGH_RISK_REQUIRES_APPROVAL,
    LOCAL_WRITE_REQUIRES_REVERSIBILITY,
    NETWORK_REQUIRES_NETWORK_POLICY,
    PROCESS_EXECUTION_UNKNOWN_ENV,
    R5_REQUIRES_EVIDENCE,
    SECRET_ACCESS_REQUIRES_SECRET_POLICY,
    STATE_CHANGE_MISSING_PREDICTED_EFFECT,
    UNKNOWN_ORIGIN_HIGH_RISK,
    UNTRUSTED_PLUGIN_HIGH_RISK,
    ValidationSeverity,
    has_blocking_validation_issues,
)

_SEVERITY_RANK = {
    ValidationSeverity.INFO: 0,
    ValidationSeverity.WARNING: 1,
    ValidationSeverity.ERROR: 2,
    ValidationSeverity.CRITICAL: 3,
}

_UNTRUSTED_ORIGINS = frozenset({
    PluginOrigin.GENERATED,
    PluginOrigin.IMPORTED,
    PluginOrigin.UNKNOWN,
    PluginOrigin.EXPERIMENTAL,
})

_UNSAFE_WARNING_CODES = frozenset({
    UNKNOWN_ORIGIN_HIGH_RISK,
    UNTRUSTED_PLUGIN_HIGH_RISK,
    EXTERNAL_WRITE_REQUIRES_APPROVAL,
})

class QuarantineReason(str, Enum):
    INVALID_MANIFEST = "invalid_manifest"
    CRITICAL_VALIDATION_ISSUE = "critical_validation_issue"
    UNKNOWN_ORIGIN = "unknown_origin"
    UNTRUSTED_PLUGIN = "untrusted_plugin"
    HIGH_RISK_WITHOUT_APPROVAL = "high_risk_without_approval"
    R6_ENABLED = "r6_enabled"
    SECRET_POLICY_MISSING = "secret_policy_missing"  # nosec B105 - quarantine reason code, not a credential
    NETWORK_POLICY_MISSING = "network_policy_missing"
    DUPLICATE_TOOL_ID = "duplicate_tool_id"
    PLUGIN_STATUS_QUARANTINED = "plugin_status_quarantined"
    PLUGIN_STATUS_INVALID = "plugin_status_invalid"
    DEPRECATED_PLUGIN = "deprecated_plugin"
    UNSAFE_SIDE_EFFECTS = "unsafe_side_effects"
    MISSING_PREDICTED_EFFECT = "missing_predicted_effect"
    PROVENANCE_FAILURE = "provenance_failure"
    VALIDATION_BLOCKING = "validation_blocking"
    UNSUPPORTED_MANIFEST = "unsupported_manifest"
    PARSE_ERROR = "parse_error"


_ISSUE_CODE_TO_REASON: dict[str, QuarantineReason] = {
    HIGH_RISK_REQUIRES_APPROVAL: QuarantineReason.HIGH_RISK_WITHOUT_APPROVAL,
    R5_REQUIRES_EVIDENCE: QuarantineReason.HIGH_RISK_WITHOUT_APPROVAL,
    EXTERNAL_WRITE_REQUIRES_APPROVAL: QuarantineReason.HIGH_RISK_WITHOUT_APPROVAL,
    SECRET_ACCESS_REQUIRES_SECRET_POLICY: QuarantineReason.SECRET_POLICY_MISSING,
    NETWORK_REQUIRES_NETWORK_POLICY: QuarantineReason.NETWORK_POLICY_MISSING,
    STATE_CHANGE_MISSING_PREDICTED_EFFECT: QuarantineReason.MISSING_PREDICTED_EFFECT,
    UNKNOWN_ORIGIN_HIGH_RISK: QuarantineReason.UNKNOWN_ORIGIN,
    UNTRUSTED_PLUGIN_HIGH_RISK: QuarantineReason.UNTRUSTED_PLUGIN,
    DUPLICATE_TOOL_ID_IN_BUNDLE: QuarantineReason.DUPLICATE_TOOL_ID,
    DISABLED_R6_REQUIRED: QuarantineReason.R6_ENABLED,
    MANIFEST_PARSE_ERROR: QuarantineReason.PARSE_ERROR,
    MANIFEST_UNSUPPORTED_FORMAT: QuarantineReason.UNSUPPORTED_MANIFEST,
    LOCAL_WRITE_REQUIRES_REVERSIBILITY: QuarantineReason.UNSAFE_SIDE_EFFECTS,
    PROCESS_EXECUTION_UNKNOWN_ENV: QuarantineReason.UNSAFE_SIDE_EFFECTS,
}


class QuarantineRecordStatus(str, Enum):
    QUARANTINED = "quarantined"
    REVIEW_REQUIRED = "review_required"
    REJECTED = "rejected"
    RESOLVED = "resolved"
    IGNORED = "ignored"


class QuarantineSubjectType(str, Enum):
    PLUGIN = "plugin"
    TOOL = "tool"
    MANIFEST_BUNDLE = "manifest_bundle"
    REGISTRY_ENTRY = "registry_entry"
    MANIFEST_FILE = "manifest_file"


@dataclass
class ValidationReport:
    report_id: str
    subject_id: str | None
    subject_type: str | None
    issues: list[ValidationIssue]
    issue_count: int
    info_count: int
    warning_count: int
    error_count: int
    critical_count: int
    blocking_count: int
    severity_max: ValidationSeverity | None
    is_blocking: bool
    created_at: datetime

    def to_dict(self) -> dict[str, Any]:
        return {
            "report_id": self.report_id,
            "subject_id": self.subject_id,
            "subject_type": self.subject_type,
            "issues": [issue.to_dict() for issue in self.issues],
            "issue_count": self.issue_count,
            "info_count": self.info_count,
            "warning_count": self.warning_count,
            "error_count": self.error_count,
            "critical_count": self.critical_count,
            "blocking_count": self.blocking_count,
            "severity_max": s.enum_value(self.severity_max),
            "is_blocking": self.is_blocking,
            "created_at": s.datetime_to_iso(self.created_at),
        }


@dataclass
class QuarantineDecision:
    should_quarantine: bool = False
    should_reject: bool = False
    should_disable: bool = False
    reasons: list[QuarantineReason] = field(default_factory=list)
    severity_max: ValidationSeverity | None = None
    message: str | None = None


@dataclass
class QuarantineRecord:
    record_id: str
    subject_type: QuarantineSubjectType | str
    subject_id: str
    plugin_id: str | None
    tool_id: str | None
    source_path: str | None
    manifest_hash: str | None
    reasons: list[QuarantineReason]
    validation_issues: list[ValidationIssue]
    severity_max: ValidationSeverity | None
    created_at: datetime
    status: QuarantineRecordStatus
    can_be_reviewed: bool
    suggested_action: str | None
    threat_surface: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "subject_type": (
                self.subject_type.value
                if isinstance(self.subject_type, QuarantineSubjectType)
                else self.subject_type
            ),
            "subject_id": self.subject_id,
            "plugin_id": self.plugin_id,
            "tool_id": self.tool_id,
            "source_path": self.source_path,
            "manifest_hash": self.manifest_hash,
            "reasons": [reason.value for reason in self.reasons],
            "validation_issues": [issue.to_dict() for issue in self.validation_issues],
            "severity_max": s.enum_value(self.severity_max),
            "created_at": s.datetime_to_iso(self.created_at),
            "status": self.status.value,
            "can_be_reviewed": self.can_be_reviewed,
            "suggested_action": self.suggested_action,
            "threat_surface": self.threat_surface,
        }


class QuarantineStore:
    """In-memory quarantine record store — no persistence, no execution."""

    def __init__(self) -> None:
        self.records: dict[str, QuarantineRecord] = {}

    def add_record(self, record: QuarantineRecord) -> QuarantineRecord:
        self.records[record.record_id] = record
        return record

    def get_record(self, record_id: str) -> QuarantineRecord | None:
        return self.records.get(record_id)

    def list_records(self) -> list[QuarantineRecord]:
        return list(self.records.values())

    def list_by_plugin(self, plugin_id: str) -> list[QuarantineRecord]:
        return [record for record in self.records.values() if record.plugin_id == plugin_id]

    def list_by_tool(self, tool_id: str) -> list[QuarantineRecord]:
        return [record for record in self.records.values() if record.tool_id == tool_id]

    def list_review_required(self) -> list[QuarantineRecord]:
        return [
            record for record in self.records.values()
            if record.status is QuarantineRecordStatus.REVIEW_REQUIRED
        ]

    def has_quarantined_subject(self, subject_id: str) -> bool:
        return any(
            record.subject_id == subject_id
            and record.status in {
                QuarantineRecordStatus.QUARANTINED,
                QuarantineRecordStatus.REVIEW_REQUIRED,
                QuarantineRecordStatus.REJECTED,
            }
            for record in self.records.values()
        )


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _severity_max(issues: list[ValidationIssue]) -> ValidationSeverity | None:
    if not issues:
        return None
    return max(issues, key=lambda issue: _SEVERITY_RANK[issue.severity]).severity


def _count_by_severity(issues: list[ValidationIssue]) -> dict[ValidationSeverity, int]:
    counts = {level: 0 for level in ValidationSeverity}
    for issue in issues:
        counts[issue.severity] += 1
    return counts


def _stable_report_id(subject_id: str | None, subject_type: str | None, issues: list[ValidationIssue]) -> str:
    payload = "|".join([
        subject_type or "",
        subject_id or "",
        *(f"{issue.code}:{issue.severity.value}" for issue in issues),
    ])
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:12]
    return f"vrpt_{digest}"


def _add_reason(decision: QuarantineDecision, reason: QuarantineReason) -> None:
    if reason not in decision.reasons:
        decision.reasons.append(reason)


def reasons_from_issues(issues: list[ValidationIssue]) -> list[QuarantineReason]:
    reasons: list[QuarantineReason] = []
    for issue in issues:
        mapped = _ISSUE_CODE_TO_REASON.get(issue.code)
        if mapped is not None:
            _add_reason_to_list(reasons, mapped)
        elif issue.severity is ValidationSeverity.CRITICAL:
            _add_reason_to_list(reasons, QuarantineReason.CRITICAL_VALIDATION_ISSUE)
        elif issue.severity is ValidationSeverity.ERROR:
            _add_reason_to_list(reasons, QuarantineReason.VALIDATION_BLOCKING)
    return reasons


def _add_reason_to_list(reasons: list[QuarantineReason], reason: QuarantineReason) -> None:
    if reason not in reasons:
        reasons.append(reason)


def merge_quarantine_decisions(*decisions: QuarantineDecision) -> QuarantineDecision:
    merged = QuarantineDecision()
    for decision in decisions:
        merged.should_quarantine = merged.should_quarantine or decision.should_quarantine
        merged.should_reject = merged.should_reject or decision.should_reject
        merged.should_disable = merged.should_disable or decision.should_disable
        for reason in decision.reasons:
            _add_reason(merged, reason)
        if decision.severity_max is not None:
            if merged.severity_max is None or _SEVERITY_RANK[decision.severity_max] > _SEVERITY_RANK[merged.severity_max]:
                merged.severity_max = decision.severity_max
        if decision.message and not merged.message:
            merged.message = decision.message
    if merged.severity_max is None and merged.reasons:
        merged.severity_max = ValidationSeverity.ERROR
    return merged


def classify_validation_issues(
    issues: list[ValidationIssue],
    subject_id: str | None = None,
    subject_type: str | None = None,
) -> ValidationReport:
    counts = _count_by_severity(issues)
    blocking_count = counts[ValidationSeverity.ERROR] + counts[ValidationSeverity.CRITICAL]
    return ValidationReport(
        report_id=_stable_report_id(subject_id, subject_type, issues),
        subject_id=subject_id,
        subject_type=subject_type,
        issues=list(issues),
        issue_count=len(issues),
        info_count=counts[ValidationSeverity.INFO],
        warning_count=counts[ValidationSeverity.WARNING],
        error_count=counts[ValidationSeverity.ERROR],
        critical_count=counts[ValidationSeverity.CRITICAL],
        blocking_count=blocking_count,
        severity_max=_severity_max(issues),
        is_blocking=blocking_count > 0,
        created_at=_utc_now(),
    )


def decide_quarantine_for_plugin(
    plugin: PluginManifest,
    issues: list[ValidationIssue],
) -> QuarantineDecision:
    decision = QuarantineDecision(severity_max=_severity_max(issues))
    for reason in reasons_from_issues(issues):
        _add_reason(decision, reason)

    if any(issue.severity is ValidationSeverity.CRITICAL for issue in issues):
        decision.should_quarantine = True
        _add_reason(decision, QuarantineReason.CRITICAL_VALIDATION_ISSUE)

    if has_blocking_validation_issues(issues):
        decision.should_disable = True
        _add_reason(decision, QuarantineReason.VALIDATION_BLOCKING)

    if plugin.origin is PluginOrigin.UNKNOWN and plugin.status is PluginStatus.ACTIVE:
        decision.should_quarantine = True
        _add_reason(decision, QuarantineReason.UNKNOWN_ORIGIN)
        decision.message = "unknown origin plugin is active"

    if plugin.trust_level in {TrustLevel.UNTRUSTED, TrustLevel.UNKNOWN} and plugin.status is PluginStatus.ACTIVE:
        decision.should_quarantine = True
        _add_reason(decision, QuarantineReason.UNTRUSTED_PLUGIN)

    if plugin.status is PluginStatus.QUARANTINED:
        decision.should_quarantine = True
        _add_reason(decision, QuarantineReason.PLUGIN_STATUS_QUARANTINED)

    if plugin.status is PluginStatus.INVALID:
        decision.should_quarantine = True
        decision.should_reject = True
        _add_reason(decision, QuarantineReason.PLUGIN_STATUS_INVALID)

    if plugin.status is PluginStatus.DEPRECATED:
        decision.should_disable = True
        decision.should_quarantine = True
        _add_reason(decision, QuarantineReason.DEPRECATED_PLUGIN)

    secret_codes = {
        SECRET_ACCESS_REQUIRES_SECRET_POLICY,
        "DATA_ACCESS_SECRETS_NO_POLICY",
    }
    network_codes = {
        NETWORK_REQUIRES_NETWORK_POLICY,
        "DATA_ACCESS_EXTERNAL_NO_POLICY",
    }
    if any(issue.code in secret_codes for issue in issues):
        decision.should_quarantine = True
        _add_reason(decision, QuarantineReason.SECRET_POLICY_MISSING)
    if any(issue.code in network_codes for issue in issues):
        decision.should_quarantine = True
        _add_reason(decision, QuarantineReason.NETWORK_POLICY_MISSING)

    return decision


def decide_quarantine_for_tool(
    tool: ToolManifest,
    plugin: PluginManifest | None,
    issues: list[ValidationIssue],
) -> QuarantineDecision:
    decision = QuarantineDecision(severity_max=_severity_max(issues))
    for reason in reasons_from_issues(issues):
        _add_reason(decision, reason)

    if any(issue.severity is ValidationSeverity.CRITICAL for issue in issues):
        decision.should_quarantine = True
        _add_reason(decision, QuarantineReason.CRITICAL_VALIDATION_ISSUE)

    if has_blocking_validation_issues(issues):
        if any(issue.severity is ValidationSeverity.CRITICAL for issue in issues):
            decision.should_quarantine = True
        else:
            decision.should_disable = True
        _add_reason(decision, QuarantineReason.VALIDATION_BLOCKING)

    if tool.risk_class is RiskClass.R6 and tool.enabled:
        decision.should_quarantine = True
        decision.should_reject = True
        _add_reason(decision, QuarantineReason.R6_ENABLED)
        decision.message = "R6 tools must not be enabled"

    if tool.risk_class is RiskClass.R5 and not tool.evidence_required:
        decision.should_quarantine = True
        _add_reason(decision, QuarantineReason.HIGH_RISK_WITHOUT_APPROVAL)

    if tool.risk_class in {RiskClass.R4, RiskClass.R5, RiskClass.R6} and not tool.requires_approval:
        decision.should_quarantine = True
        _add_reason(decision, QuarantineReason.HIGH_RISK_WITHOUT_APPROVAL)

    effects = set(tool.side_effects)
    if SideEffectType.EXTERNAL_WRITE in effects and not tool.requires_approval:
        decision.should_quarantine = True
        _add_reason(decision, QuarantineReason.HIGH_RISK_WITHOUT_APPROVAL)

    if SideEffectType.SECRET_ACCESS in effects or any(
        issue.code in {SECRET_ACCESS_REQUIRES_SECRET_POLICY, "DATA_ACCESS_SECRETS_NO_POLICY"}
        for issue in issues
    ):
        decision.should_quarantine = True
        _add_reason(decision, QuarantineReason.SECRET_POLICY_MISSING)

    if SideEffectType.NETWORK in effects or any(
        issue.code in {NETWORK_REQUIRES_NETWORK_POLICY, "DATA_ACCESS_EXTERNAL_NO_POLICY"}
        for issue in issues
    ):
        decision.should_quarantine = True
        _add_reason(decision, QuarantineReason.NETWORK_POLICY_MISSING)

    if SideEffectType.LOCAL_WRITE in effects and tool.reversibility in {
        Reversibility.NONE,
        Reversibility.UNKNOWN,
    }:
        decision.should_disable = True
        if has_blocking_validation_issues(issues):
            decision.should_quarantine = True
        _add_reason(decision, QuarantineReason.UNSAFE_SIDE_EFFECTS)

    if SideEffectType.PROCESS_EXECUTION in effects:
        if tool.execution_environment is ExecutionEnvironment.UNKNOWN or is_high_risk_class(tool.risk_class):
            decision.should_quarantine = True
            _add_reason(decision, QuarantineReason.UNSAFE_SIDE_EFFECTS)

    if any(issue.code == STATE_CHANGE_MISSING_PREDICTED_EFFECT and issue.severity is ValidationSeverity.ERROR for issue in issues):
        decision.should_quarantine = True
        _add_reason(decision, QuarantineReason.MISSING_PREDICTED_EFFECT)

    if plugin is not None:
        if plugin.origin in _UNTRUSTED_ORIGINS and _risk_at_least(tool.risk_class, RiskClass.R3) and tool.enabled:
            decision.should_quarantine = True
            _add_reason(decision, QuarantineReason.PROVENANCE_FAILURE)
        if plugin.status is PluginStatus.QUARANTINED:
            decision.should_quarantine = True
            decision.should_disable = True
            _add_reason(decision, QuarantineReason.PLUGIN_STATUS_QUARANTINED)
        if plugin.status is PluginStatus.INVALID:
            decision.should_quarantine = True
            decision.should_reject = True
            _add_reason(decision, QuarantineReason.PLUGIN_STATUS_INVALID)
        if plugin.status is PluginStatus.DEPRECATED:
            decision.should_disable = True
            decision.should_quarantine = True
            _add_reason(decision, QuarantineReason.DEPRECATED_PLUGIN)

    return decision


def _risk_at_least(risk: RiskClass, minimum: RiskClass) -> bool:
    order = {RiskClass.R0: 0, RiskClass.R1: 1, RiskClass.R2: 2, RiskClass.R3: 3,
             RiskClass.R4: 4, RiskClass.R5: 5, RiskClass.R6: 6}
    return order[risk] >= order[minimum]


def decide_quarantine_for_manifest_result(result: ManifestLoadResult) -> QuarantineDecision:
    issues = list(result.validation_issues)
    decision = QuarantineDecision(severity_max=_severity_max(issues))
    for reason in reasons_from_issues(issues):
        _add_reason(decision, reason)

    if result.status is ManifestLoadStatus.PARSE_ERROR:
        decision.should_reject = True
        decision.should_quarantine = True
        _add_reason(decision, QuarantineReason.PARSE_ERROR)
        decision.message = result.parse_error
        return decision

    if result.status is ManifestLoadStatus.UNSUPPORTED_FORMAT:
        decision.should_reject = True
        _add_reason(decision, QuarantineReason.UNSUPPORTED_MANIFEST)
        return decision

    if result.status is ManifestLoadStatus.NOT_FOUND:
        decision.should_reject = True
        decision.message = result.parse_error
        return decision

    if result.status is ManifestLoadStatus.INVALID:
        decision.should_quarantine = True
        decision.should_reject = True
        _add_reason(decision, QuarantineReason.INVALID_MANIFEST)
        return decision

    if result.status is ManifestLoadStatus.LOADED_WITH_WARNINGS:
        if any(issue.code in _UNSAFE_WARNING_CODES for issue in issues):
            decision.should_quarantine = True
            _add_reason(decision, QuarantineReason.PROVENANCE_FAILURE)
        elif any(issue.severity is ValidationSeverity.CRITICAL for issue in issues):
            decision.should_quarantine = True
        return decision

    if result.status is ManifestLoadStatus.LOADED:
        if any(issue.severity is ValidationSeverity.CRITICAL for issue in issues):
            decision.should_quarantine = True
            decision.should_reject = True
            _add_reason(decision, QuarantineReason.CRITICAL_VALIDATION_ISSUE)

    return decision


def suggested_action_for_reasons(
    reasons: list[QuarantineReason],
    issues: list[ValidationIssue],
) -> str | None:
    if QuarantineReason.HIGH_RISK_WITHOUT_APPROVAL in reasons:
        return "Set requires_approval=true for high-risk tool."
    if QuarantineReason.SECRET_POLICY_MISSING in reasons:
        return "Add secret_policy to the plugin manifest."
    if QuarantineReason.NETWORK_POLICY_MISSING in reasons:
        return "Add network_policy to the plugin manifest."
    if QuarantineReason.R6_ENABLED in reasons:
        return "Disable the R6 tool or lower risk only after redesign."
    if QuarantineReason.MISSING_PREDICTED_EFFECT in reasons:
        return "Add predicted_effect for state-changing high-risk tool."
    if QuarantineReason.DUPLICATE_TOOL_ID in reasons:
        return "Resolve duplicate tool_id before registration."
    if QuarantineReason.UNKNOWN_ORIGIN in reasons:
        return "Set a trusted origin or keep plugin disabled."
    if QuarantineReason.UNTRUSTED_PLUGIN in reasons:
        return "Raise trust level after review or keep plugin disabled."
    if QuarantineReason.PARSE_ERROR in reasons:
        return "Fix manifest syntax and reload."
    if QuarantineReason.UNSUPPORTED_MANIFEST in reasons:
        return "Use a supported manifest format (.json, .yaml, .yml)."
    if issues:
        return f"Resolve validation issue: {issues[0].message}"
    return None


def create_quarantine_record(
    subject_type: QuarantineSubjectType | str,
    subject_id: str,
    issues: list[ValidationIssue],
    decision: QuarantineDecision,
    plugin_id: str | None = None,
    tool_id: str | None = None,
    source_path: str | None = None,
    manifest_hash: str | None = None,
) -> QuarantineRecord:
    non_reviewable = {
        QuarantineReason.PARSE_ERROR,
        QuarantineReason.UNSUPPORTED_MANIFEST,
    }
    can_be_reviewed = not any(reason in non_reviewable for reason in decision.reasons)

    if decision.should_reject:
        status = QuarantineRecordStatus.REJECTED
    elif decision.should_quarantine and can_be_reviewed:
        status = QuarantineRecordStatus.REVIEW_REQUIRED
    elif decision.should_quarantine:
        status = QuarantineRecordStatus.QUARANTINED
    else:
        status = QuarantineRecordStatus.QUARANTINED

    reasons = list(decision.reasons)
    threat_surface = None
    if QuarantineReason.SECRET_POLICY_MISSING in reasons:
        threat_surface = "secrets"
    elif QuarantineReason.NETWORK_POLICY_MISSING in reasons:
        threat_surface = "network"

    return QuarantineRecord(
        record_id=new_id("qrec"),
        subject_type=subject_type,
        subject_id=subject_id,
        plugin_id=plugin_id,
        tool_id=tool_id,
        source_path=source_path,
        manifest_hash=manifest_hash,
        reasons=reasons,
        validation_issues=list(issues),
        severity_max=decision.severity_max or _severity_max(issues),
        created_at=_utc_now(),
        status=status,
        can_be_reviewed=can_be_reviewed,
        suggested_action=suggested_action_for_reasons(reasons, issues),
        threat_surface=threat_surface,
    )


def registry_should_activate_entry(
    entry: ToolRegistryEntry,
    *,
    quarantine_store: QuarantineStore | None = None,
) -> bool:
    _inactive_entry = frozenset({
        RegistryEntryStatus.DISABLED,
        RegistryEntryStatus.INVALID,
        RegistryEntryStatus.QUARANTINED,
        RegistryEntryStatus.DEPRECATED,
        RegistryEntryStatus.EXPERIMENTAL,
    })
    _inactive_capability = frozenset({
        CapabilityStatus.DISABLED,
        CapabilityStatus.INVALID,
        CapabilityStatus.QUARANTINED,
        CapabilityStatus.DEPRECATED,
        CapabilityStatus.EXPERIMENTAL,
    })

    if entry.status in _inactive_entry:
        return False
    if has_blocking_validation_issues(entry.validation_errors):
        return False
    if entry.capability is None:
        return False
    if entry.capability.current_status in _inactive_capability:
        return False
    if entry.capability.risk_class is RiskClass.R6:
        return False
    if quarantine_store is not None and quarantine_store.has_quarantined_subject(entry.tool_id):
        return False
    return entry.status is RegistryEntryStatus.REGISTERED
