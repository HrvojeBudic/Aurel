"""Tool capability registry seed (P1.3.3).

The registry catalogs validated ToolCapability metadata only.
Registry visibility does not grant authority and never executes tools.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from . import _serde as s
from .capability import ToolCapability, ToolRegistryEntry
from .enums import (
    CapabilityStatus,
    CapabilityType,
    PluginOrigin,
    PluginStatus,
    RegistryEntryStatus,
    Reversibility,
    RiskClass,
    ToolCategory,
    ToolRole,
    TrustLevel,
    is_high_risk_class,
)
from .loader import ManifestBundle, ManifestLoadResult, ManifestLoadStatus, validate_manifest_bundle
from .manifest import PluginManifest, PredictedEffect, ToolManifest, ValidationIssue
from .research_metadata import (
    apply_research_metadata_to_capability,
    derive_tool_roles,
    is_simulation_ready_capability,
    is_state_changing_capability,
)
from .quarantine import (
    QuarantineDecision,
    QuarantineStore,
    QuarantineSubjectType,
    create_quarantine_record,
    decide_quarantine_for_manifest_result,
    decide_quarantine_for_plugin,
    decide_quarantine_for_tool,
    merge_quarantine_decisions,
    registry_should_activate_entry,
)
from .validation import (
    ValidationSeverity,
    has_blocking_validation_issues,
    validate_plugin_manifest,
    validate_tool_manifest,
)

_PLUGIN_STATUS_BLOCK_CODE = "PLUGIN_STATUS_BLOCKS_ENABLED_TOOL"

_BLOCKED_PLUGIN_STATUSES = frozenset({
    PluginStatus.QUARANTINED,
    PluginStatus.INVALID,
    PluginStatus.DEPRECATED,
})

_INACTIVE_ENTRY_STATUSES = frozenset({
    RegistryEntryStatus.DISABLED,
    RegistryEntryStatus.INVALID,
    RegistryEntryStatus.QUARANTINED,
    RegistryEntryStatus.DEPRECATED,
    RegistryEntryStatus.EXPERIMENTAL,
})

_INACTIVE_CAPABILITY_STATUSES = frozenset({
    CapabilityStatus.DISABLED,
    CapabilityStatus.INVALID,
    CapabilityStatus.QUARANTINED,
    CapabilityStatus.DEPRECATED,
    CapabilityStatus.EXPERIMENTAL,
})

_LOADABLE_STATUSES = frozenset({
    ManifestLoadStatus.LOADED,
    ManifestLoadStatus.LOADED_WITH_WARNINGS,
})


class ToolRegistryOperationStatus(str, Enum):
    REGISTERED = "registered"
    ALREADY_EXISTS = "already_exists"
    REJECTED = "rejected"
    DISABLED = "disabled"
    ENABLED = "enabled"
    NOT_FOUND = "not_found"
    INVALID = "invalid"
    QUARANTINED = "quarantined"
    DEPRECATED = "deprecated"
    EXPERIMENTAL = "experimental"


@dataclass
class ToolRegistryResult:
    status: ToolRegistryOperationStatus
    tool_id: str | None = None
    plugin_id: str | None = None
    entry: ToolRegistryEntry | None = None
    issues: list[ValidationIssue] = field(default_factory=list)
    message: str | None = None
    quarantine_record_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "tool_id": self.tool_id,
            "plugin_id": self.plugin_id,
            "entry": self.entry.to_dict() if self.entry else None,
            "issues": [issue.to_dict() for issue in self.issues],
            "message": self.message,
            "quarantine_record_id": self.quarantine_record_id,
        }


@dataclass
class _RegisteredToolMeta:
    category: ToolCategory
    requires_approval: bool
    plugin_origin: PluginOrigin | None = None
    reversibility: Reversibility = Reversibility.UNKNOWN
    predicted_effect: PredictedEffect | None = None


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _authority_required(risk_class: RiskClass) -> str | None:
    if risk_class in {RiskClass.R0, RiskClass.R1}:
        return None
    if risk_class in {RiskClass.R2, RiskClass.R3}:
        return "operator_policy_check"
    return "approval_required"


def _capability_status(
    tool: ToolManifest,
    plugin: PluginManifest | None,
    issues: list[ValidationIssue],
    *,
    load_warnings: bool = False,
) -> CapabilityStatus:
    if has_blocking_validation_issues(issues):
        return CapabilityStatus.INVALID
    if tool.risk_class is RiskClass.R6 and tool.enabled:
        return CapabilityStatus.INVALID
    if not tool.enabled:
        return CapabilityStatus.DISABLED
    if plugin is not None:
        if plugin.status is PluginStatus.QUARANTINED:
            return CapabilityStatus.QUARANTINED
        if plugin.status is PluginStatus.DEPRECATED:
            return CapabilityStatus.DEPRECATED
        if plugin.status is PluginStatus.INVALID:
            return CapabilityStatus.INVALID
        if plugin.status is PluginStatus.DISABLED:
            return CapabilityStatus.DISABLED
        if plugin.status is PluginStatus.EXPERIMENTAL:
            return CapabilityStatus.EXPERIMENTAL
    if load_warnings:
        return CapabilityStatus.EXPERIMENTAL
    return CapabilityStatus.ACTIVE


def _entry_status(capability_status: CapabilityStatus) -> RegistryEntryStatus:
    mapping = {
        CapabilityStatus.ACTIVE: RegistryEntryStatus.REGISTERED,
        CapabilityStatus.DISABLED: RegistryEntryStatus.DISABLED,
        CapabilityStatus.INVALID: RegistryEntryStatus.INVALID,
        CapabilityStatus.QUARANTINED: RegistryEntryStatus.QUARANTINED,
        CapabilityStatus.DEPRECATED: RegistryEntryStatus.DEPRECATED,
        CapabilityStatus.EXPERIMENTAL: RegistryEntryStatus.EXPERIMENTAL,
    }
    return mapping.get(capability_status, RegistryEntryStatus.INVALID)


def create_tool_capability_from_manifest(
    tool: ToolManifest,
    plugin: PluginManifest | None = None,
    registry_source: str | None = None,
    *,
    issues: list[ValidationIssue] | None = None,
    load_warnings: bool = False,
) -> ToolCapability:
    validation_issues = list(issues or [])
    status = _capability_status(tool, plugin, validation_issues, load_warnings=load_warnings)
    base = ToolCapability(
        tool_id=tool.tool_id,
        plugin_id=tool.plugin_id,
        canonical_name=tool.name,
        version=plugin.version if plugin is not None else "unknown",
        capability_types=list(tool.capability_types),
        risk_class=tool.risk_class,
        authority_required=_authority_required(tool.risk_class),
        input_contract=dict(tool.input_schema),
        output_contract=dict(tool.output_schema),
        side_effect_profile=list(tool.side_effects),
        data_access_profile=list(tool.data_access),
        dry_run_capable=tool.dry_run_supported,
        simulation_capable=tool.simulation_supported,
        current_status=status,
        trust_score_seed=plugin.trust_level if plugin is not None else TrustLevel.UNKNOWN,
        registry_source=registry_source,
    )
    return apply_research_metadata_to_capability(base, tool)


def _operation_status_for_entry(entry: ToolRegistryEntry) -> ToolRegistryOperationStatus:
    if entry.status is RegistryEntryStatus.REGISTERED:
        return ToolRegistryOperationStatus.REGISTERED
    if entry.status is RegistryEntryStatus.DISABLED:
        return ToolRegistryOperationStatus.DISABLED
    if entry.status is RegistryEntryStatus.QUARANTINED:
        return ToolRegistryOperationStatus.QUARANTINED
    if entry.status is RegistryEntryStatus.DEPRECATED:
        return ToolRegistryOperationStatus.DEPRECATED
    if entry.status is RegistryEntryStatus.EXPERIMENTAL:
        return ToolRegistryOperationStatus.EXPERIMENTAL
    return ToolRegistryOperationStatus.INVALID


def _registration_blocking_issues(
    issues: list[ValidationIssue],
    plugin: PluginManifest | None,
) -> list[ValidationIssue]:
    blocking = [
        issue for issue in issues
        if issue.severity in {ValidationSeverity.ERROR, ValidationSeverity.CRITICAL}
    ]
    if plugin is not None and plugin.status in _BLOCKED_PLUGIN_STATUSES:
        return [
            issue for issue in blocking
            if issue.code != _PLUGIN_STATUS_BLOCK_CODE
        ]
    return blocking


def _registration_is_blocked(
    issues: list[ValidationIssue],
    plugin: PluginManifest | None,
) -> bool:
    return bool(_registration_blocking_issues(issues, plugin))


def _derive_capability_roles(
    category: ToolCategory,
    capability_types: list[CapabilityType],
) -> list[str]:
    roles: set[str] = set()
    caps = set(capability_types)

    if category in {ToolCategory.FILESYSTEM, ToolCategory.CODE, ToolCategory.GIT}:
        roles.add("perception")
    if category is ToolCategory.MEMORY:
        roles.add("memory")
    if category in {ToolCategory.TEST, ToolCategory.EVALUATION}:
        roles.add("verification")
    if category in {ToolCategory.ENVIRONMENT, ToolCategory.BROWSER, ToolCategory.WEB}:
        roles.add("environment")
    if category is ToolCategory.MODEL:
        roles.add("cognition")

    if caps & {CapabilityType.READ, CapabilityType.ANALYZE, CapabilityType.SEARCH, CapabilityType.OBSERVE}:
        roles.add("perception")
    if caps & {CapabilityType.TRANSFORM, CapabilityType.ANALYZE, CapabilityType.COMPILE}:
        roles.add("cognition")
    if caps & {CapabilityType.WRITE, CapabilityType.EXECUTE, CapabilityType.SEND, CapabilityType.SCHEDULE}:
        roles.add("action")
    if caps & {CapabilityType.VERIFY, CapabilityType.EVALUATE}:
        roles.add("verification")
    if caps & {CapabilityType.RETRIEVE, CapabilityType.PROPOSE}:
        roles.add("memory")
    if caps & {CapabilityType.SIMULATE}:
        roles.add("environment")

    return sorted(roles)


class ToolRegistry:
    """Catalog of validated tool capabilities — metadata only, no execution."""

    def __init__(self) -> None:
        self.entries: dict[str, ToolRegistryEntry] = {}
        self.created_at = _utc_now()
        self.updated_at = self.created_at
        self.source_results: list[ManifestLoadResult] = []
        self._tool_meta: dict[str, _RegisteredToolMeta] = {}
        self._plugins: dict[str, PluginManifest] = {}
        self.quarantine_store = QuarantineStore()

    def _record_quarantine(
        self,
        *,
        subject_type: QuarantineSubjectType,
        subject_id: str,
        issues: list[ValidationIssue],
        decision: QuarantineDecision,
        plugin_id: str | None = None,
        tool_id: str | None = None,
        source_path: str | None = None,
        manifest_hash: str | None = None,
    ) -> str:
        record = create_quarantine_record(
            subject_type,
            subject_id,
            issues,
            decision,
            plugin_id=plugin_id,
            tool_id=tool_id,
            source_path=source_path,
            manifest_hash=manifest_hash,
        )
        self.quarantine_store.add_record(record)
        return record.record_id

    def register_manifest_result(self, result: ManifestLoadResult) -> list[ToolRegistryResult]:
        load_decision = decide_quarantine_for_manifest_result(result)
        if result.status not in _LOADABLE_STATUSES or load_decision.should_reject:
            record_id = None
            if load_decision.should_quarantine or load_decision.should_reject:
                record_id = self._record_quarantine(
                    subject_type=QuarantineSubjectType.MANIFEST_FILE,
                    subject_id=result.source_path,
                    issues=list(result.validation_issues),
                    decision=load_decision,
                    plugin_id=(
                        result.plugin_manifest.plugin_id
                        if result.plugin_manifest is not None
                        else None
                    ),
                    source_path=result.source_path,
                    manifest_hash=result.manifest_hash,
                )
            return [
                ToolRegistryResult(
                    status=(
                        ToolRegistryOperationStatus.QUARANTINED
                        if load_decision.should_quarantine
                        else ToolRegistryOperationStatus.REJECTED
                    ),
                    message=(
                        load_decision.message
                        or f"manifest load status {result.status.value} cannot be registered"
                    ),
                    issues=list(result.validation_issues),
                    quarantine_record_id=record_id,
                ),
            ]
        if has_blocking_validation_issues(result.validation_issues):
            record_id = self._record_quarantine(
                subject_type=QuarantineSubjectType.MANIFEST_FILE,
                subject_id=result.source_path,
                issues=list(result.validation_issues),
                decision=load_decision,
                plugin_id=result.plugin_manifest.plugin_id if result.plugin_manifest else None,
                source_path=result.source_path,
                manifest_hash=result.manifest_hash,
            )
            return [
                ToolRegistryResult(
                    status=ToolRegistryOperationStatus.REJECTED,
                    message="manifest load result has blocking validation issues",
                    issues=list(result.validation_issues),
                    quarantine_record_id=record_id,
                ),
            ]
        if result.plugin_manifest is None:
            return [
                ToolRegistryResult(
                    status=ToolRegistryOperationStatus.REJECTED,
                    message="manifest load result has no plugin manifest",
                    issues=list(result.validation_issues),
                ),
            ]

        self.source_results.append(result)
        load_warnings = result.status is ManifestLoadStatus.LOADED_WITH_WARNINGS
        outcomes: list[ToolRegistryResult] = []
        for tool in result.tool_manifests:
            outcomes.append(self.register_tool_manifest(
                tool,
                result.plugin_manifest,
                manifest_hash=result.manifest_hash,
                source_path=result.source_path,
                load_warnings=load_warnings,
                extra_issues=list(result.validation_issues),
            ))
        return outcomes

    def register_bundle(self, bundle: ManifestBundle) -> list[ToolRegistryResult]:
        issues = validate_manifest_bundle(bundle)
        if has_blocking_validation_issues(issues):
            return [
                ToolRegistryResult(
                    status=ToolRegistryOperationStatus.REJECTED,
                    message="manifest bundle has blocking validation issues",
                    issues=issues,
                ),
            ]
        load_warnings = any(
            issue.severity.value in {"warning", "info"} for issue in issues
        )
        outcomes: list[ToolRegistryResult] = []
        for tool in bundle.tools:
            outcomes.append(self.register_tool_manifest(
                tool,
                bundle.plugin,
                manifest_hash=bundle.bundle_hash,
                source_path=bundle.source_path,
                load_warnings=load_warnings,
                extra_issues=issues,
            ))
        return outcomes

    def register_tool_manifest(
        self,
        tool: ToolManifest,
        plugin: PluginManifest | None = None,
        manifest_hash: str | None = None,
        source_path: str | None = None,
        *,
        load_warnings: bool = False,
        extra_issues: list[ValidationIssue] | None = None,
    ) -> ToolRegistryResult:
        issues: list[ValidationIssue] = list(extra_issues or [])
        if plugin is not None:
            issues.extend(validate_plugin_manifest(plugin))
            self._plugins[plugin.plugin_id] = plugin
        issues.extend(validate_tool_manifest(tool, plugin))

        if plugin is not None and tool.plugin_id != plugin.plugin_id:
            return ToolRegistryResult(
                status=ToolRegistryOperationStatus.REJECTED,
                tool_id=tool.tool_id,
                plugin_id=tool.plugin_id,
                issues=issues,
                message="tool plugin_id does not match plugin manifest",
            )

        plugin_decision = (
            decide_quarantine_for_plugin(plugin, issues) if plugin is not None else QuarantineDecision()
        )
        tool_decision = decide_quarantine_for_tool(tool, plugin, issues)
        decision = merge_quarantine_decisions(plugin_decision, tool_decision)

        if tool.tool_id in self.entries:
            return ToolRegistryResult(
                status=ToolRegistryOperationStatus.ALREADY_EXISTS,
                tool_id=tool.tool_id,
                plugin_id=tool.plugin_id,
                entry=self.entries[tool.tool_id],
                issues=issues,
                message=f"tool_id '{tool.tool_id}' is already registered",
            )

        reject_registration = (
            (decision.should_reject and tool.risk_class is RiskClass.R6 and tool.enabled)
            or (
                _registration_is_blocked(issues, plugin)
                and not (
                    plugin is not None
                    and plugin.status in _BLOCKED_PLUGIN_STATUSES
                    and not decision.should_reject
                )
            )
            or (plugin is not None and plugin.status is PluginStatus.INVALID)
        )
        if reject_registration:
            record_id = self._record_quarantine(
                subject_type=QuarantineSubjectType.TOOL,
                subject_id=tool.tool_id,
                issues=issues,
                decision=decision,
                plugin_id=tool.plugin_id,
                tool_id=tool.tool_id,
                source_path=source_path,
                manifest_hash=manifest_hash,
            )
            return ToolRegistryResult(
                status=(
                    ToolRegistryOperationStatus.QUARANTINED
                    if decision.should_quarantine
                    else ToolRegistryOperationStatus.REJECTED
                ),
                tool_id=tool.tool_id,
                plugin_id=tool.plugin_id,
                issues=issues,
                message=decision.message or "tool manifest rejected by quarantine policy",
                quarantine_record_id=record_id,
            )

        if plugin is not None and plugin.status in _BLOCKED_PLUGIN_STATUSES:
            cap_status = (
                CapabilityStatus.QUARANTINED
                if plugin.status is PluginStatus.QUARANTINED
                else CapabilityStatus.DEPRECATED
                if plugin.status is PluginStatus.DEPRECATED
                else CapabilityStatus.INVALID
            )
        else:
            cap_status = _capability_status(
                tool, plugin, issues, load_warnings=load_warnings
            )

        if decision.should_quarantine:
            cap_status = CapabilityStatus.QUARANTINED
        elif decision.should_disable and cap_status is CapabilityStatus.ACTIVE:
            cap_status = CapabilityStatus.DISABLED

        quarantine_record_id = None
        if decision.should_quarantine or decision.should_disable:
            quarantine_record_id = self._record_quarantine(
                subject_type=QuarantineSubjectType.TOOL,
                subject_id=tool.tool_id,
                issues=issues,
                decision=decision,
                plugin_id=tool.plugin_id,
                tool_id=tool.tool_id,
                source_path=source_path,
                manifest_hash=manifest_hash,
            )

        capability = create_tool_capability_from_manifest(
            tool,
            plugin,
            registry_source=source_path,
            issues=issues,
            load_warnings=load_warnings,
        )
        capability = replace(capability, current_status=cap_status)

        now = _utc_now()
        entry = ToolRegistryEntry(
            tool_id=tool.tool_id,
            plugin_id=tool.plugin_id,
            manifest_hash=manifest_hash,
            loaded_at=now,
            validated_at=now,
            status=_entry_status(cap_status),
            validation_errors=list(issues),
            capability=capability,
        )

        self.entries[tool.tool_id] = entry
        self._tool_meta[tool.tool_id] = _RegisteredToolMeta(
            category=tool.category,
            requires_approval=tool.requires_approval,
            plugin_origin=plugin.origin if plugin is not None else None,
            reversibility=tool.reversibility,
            predicted_effect=tool.predicted_effect,
        )
        self.updated_at = now

        return ToolRegistryResult(
            status=_operation_status_for_entry(entry),
            tool_id=tool.tool_id,
            plugin_id=tool.plugin_id,
            entry=entry,
            issues=list(issues),
            message=f"registered tool '{tool.tool_id}'",
            quarantine_record_id=quarantine_record_id,
        )

    def get_invocation_meta(self, tool_id: str) -> _RegisteredToolMeta | None:
        return self._tool_meta.get(tool_id)

    def get_tool(self, tool_id: str) -> ToolRegistryEntry | None:
        return self.entries.get(tool_id)

    def has_tool(self, tool_id: str) -> bool:
        return tool_id in self.entries

    def is_registered(self, tool_id: str) -> bool:
        return tool_id in self.entries

    def is_active(self, tool_id: str) -> bool:
        entry = self.entries.get(tool_id)
        return entry is not None and self._is_active_entry(entry)

    def is_high_risk(self, tool_id: str) -> bool:
        entry = self.entries.get(tool_id)
        if entry is None or entry.capability is None:
            return False
        return is_high_risk_class(entry.capability.risk_class)

    def requires_approval(self, tool_id: str) -> bool:
        entry = self.entries.get(tool_id)
        if entry is None or entry.capability is None:
            return False
        meta = self._tool_meta.get(tool_id)
        if meta is not None and meta.requires_approval:
            return True
        return is_high_risk_class(entry.capability.risk_class)

    def get_capability_roles(self, tool_id: str) -> list[str]:
        entry = self.entries.get(tool_id)
        if entry is None or entry.capability is None:
            return []
        return [role.value for role in entry.capability.tool_roles]

    def list_by_tool_role(self, role: ToolRole) -> list[ToolRegistryEntry]:
        return [
            entry
            for entry in self.entries.values()
            if entry.capability is not None and role in entry.capability.tool_roles
        ]

    def list_state_changing_tools(self) -> list[ToolRegistryEntry]:
        return [
            entry
            for entry in self.entries.values()
            if entry.capability is not None and is_state_changing_capability(entry.capability)
        ]

    def list_simulation_ready_tools(self) -> list[ToolRegistryEntry]:
        return [
            entry
            for entry in self.entries.values()
            if entry.capability is not None and is_simulation_ready_capability(entry.capability)
        ]

    def list_tools_requiring_operator_attention(self) -> list[ToolRegistryEntry]:
        return [
            entry
            for entry in self.entries.values()
            if entry.capability is not None
            and entry.capability.safety_surface is not None
            and entry.capability.safety_surface.operator_attention_required
        ]

    def list_tools(self) -> list[ToolRegistryEntry]:
        return list(self.entries.values())

    def list_active_tools(self) -> list[ToolRegistryEntry]:
        return [entry for entry in self.entries.values() if self._is_active_entry(entry)]

    def list_by_plugin(self, plugin_id: str) -> list[ToolRegistryEntry]:
        return [entry for entry in self.entries.values() if entry.plugin_id == plugin_id]

    def list_by_category(self, category: ToolCategory) -> list[ToolRegistryEntry]:
        return [
            entry
            for tool_id, entry in self.entries.items()
            if self._tool_meta.get(tool_id) is not None
            and self._tool_meta[tool_id].category is category
        ]

    def list_by_capability_type(
        self, capability_type: CapabilityType
    ) -> list[ToolRegistryEntry]:
        return [
            entry
            for entry in self.entries.values()
            if entry.capability is not None
            and capability_type in entry.capability.capability_types
        ]

    def list_by_risk_class(self, risk_class: RiskClass) -> list[ToolRegistryEntry]:
        return [
            entry
            for entry in self.entries.values()
            if entry.capability is not None and entry.capability.risk_class is risk_class
        ]

    def list_external_tools(self) -> list[ToolRegistryEntry]:
        return [
            entry
            for tool_id, entry in self.entries.items()
            if self._tool_meta.get(tool_id) is not None
            and self._tool_meta[tool_id].plugin_origin not in {None, PluginOrigin.BUILTIN}
        ]

    def list_high_risk_tools(self) -> list[ToolRegistryEntry]:
        return [
            entry
            for entry in self.entries.values()
            if entry.capability is not None and is_high_risk_class(entry.capability.risk_class)
        ]

    def disable_tool(self, tool_id: str, reason: str | None = None) -> ToolRegistryResult:
        entry = self.entries.get(tool_id)
        if entry is None:
            return ToolRegistryResult(
                status=ToolRegistryOperationStatus.NOT_FOUND,
                tool_id=tool_id,
                message=f"tool_id '{tool_id}' not found",
            )

        updated_capability = entry.capability
        if updated_capability is not None:
            updated_capability = replace(updated_capability, current_status=CapabilityStatus.DISABLED)

        updated_entry = replace(
            entry,
            status=RegistryEntryStatus.DISABLED,
            capability=updated_capability,
            validation_errors=list(entry.validation_errors),
        )
        if reason:
            updated_entry.validation_errors.append(ValidationIssue(
                code="TOOL_DISABLED",
                message=reason,
                field="status",
                severity=ValidationSeverity.INFO,
            ))
        self.entries[tool_id] = updated_entry
        self.updated_at = _utc_now()
        return ToolRegistryResult(
            status=ToolRegistryOperationStatus.DISABLED,
            tool_id=tool_id,
            plugin_id=entry.plugin_id,
            entry=updated_entry,
            issues=list(updated_entry.validation_errors),
            message=reason or f"disabled tool '{tool_id}'",
        )

    def enable_tool(self, tool_id: str) -> ToolRegistryResult:
        entry = self.entries.get(tool_id)
        if entry is None:
            return ToolRegistryResult(
                status=ToolRegistryOperationStatus.NOT_FOUND,
                tool_id=tool_id,
                message=f"tool_id '{tool_id}' not found",
            )

        if has_blocking_validation_issues(entry.validation_errors):
            return ToolRegistryResult(
                status=ToolRegistryOperationStatus.REJECTED,
                tool_id=tool_id,
                plugin_id=entry.plugin_id,
                entry=entry,
                issues=list(entry.validation_errors),
                message="cannot enable tool with blocking validation issues",
            )

        if entry.capability is not None and entry.capability.risk_class is RiskClass.R6:
            return ToolRegistryResult(
                status=ToolRegistryOperationStatus.REJECTED,
                tool_id=tool_id,
                plugin_id=entry.plugin_id,
                entry=entry,
                message="cannot enable R6 tool",
            )

        if entry.status in {
            RegistryEntryStatus.QUARANTINED,
            RegistryEntryStatus.INVALID,
            RegistryEntryStatus.DEPRECATED,
        }:
            return ToolRegistryResult(
                status=ToolRegistryOperationStatus.REJECTED,
                tool_id=tool_id,
                plugin_id=entry.plugin_id,
                entry=entry,
                message=f"cannot enable tool with status {entry.status.value}",
            )

        updated_capability = entry.capability
        if updated_capability is not None:
            updated_capability = replace(updated_capability, current_status=CapabilityStatus.ACTIVE)

        updated_entry = replace(
            entry,
            status=RegistryEntryStatus.REGISTERED,
            capability=updated_capability,
        )
        self.entries[tool_id] = updated_entry
        self.updated_at = _utc_now()
        return ToolRegistryResult(
            status=ToolRegistryOperationStatus.ENABLED,
            tool_id=tool_id,
            plugin_id=entry.plugin_id,
            entry=updated_entry,
            message=f"enabled tool '{tool_id}'",
        )

    def _is_active_entry(self, entry: ToolRegistryEntry) -> bool:
        return registry_should_activate_entry(entry, quarantine_store=self.quarantine_store)
