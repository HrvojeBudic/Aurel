"""Tool lifecycle trace events (P1.3.6).

Trace events record manifest/registry/quarantine/draft lifecycle transitions.
They are not execution, verified evidence, or authority grants.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from ..core_types import new_id
from . import _serde as s
from .enums import ValidationSeverity
from .invocation import ToolInvocationDraftResult, ToolInvocationDraftResultStatus
from .loader import ManifestLoadResult, ManifestLoadStatus
from .manifest import PredictedEffect, ValidationIssue
from .quarantine import QuarantineRecord
from .registry import ToolRegistryOperationStatus, ToolRegistryResult


def _merge_research_metadata(
    metadata: dict[str, Any],
    capability: Any | None,
) -> dict[str, Any]:
    if capability is None:
        return metadata
    from .research_metadata import research_metadata_from_capability

    merged = dict(metadata)
    merged.update(research_metadata_from_capability(capability))
    return merged

_SEVERITY_RANK = {
    ValidationSeverity.INFO: 0,
    ValidationSeverity.WARNING: 1,
    ValidationSeverity.ERROR: 2,
    ValidationSeverity.CRITICAL: 3,
}

_LOADED_STATUSES = frozenset({
    ManifestLoadStatus.LOADED,
    ManifestLoadStatus.LOADED_WITH_WARNINGS,
})


class ToolLifecycleEventType(str, Enum):
    MANIFEST_LOADED = "manifest_loaded"
    MANIFEST_REJECTED = "manifest_rejected"
    MANIFEST_PARSE_ERROR = "manifest_parse_error"
    PLUGIN_LOADED = "plugin_loaded"
    PLUGIN_QUARANTINED = "plugin_quarantined"
    PLUGIN_REJECTED = "plugin_rejected"
    TOOL_CAPABILITY_REGISTERED = "tool_capability_registered"
    TOOL_CAPABILITY_REJECTED = "tool_capability_rejected"
    TOOL_CAPABILITY_DISABLED = "tool_capability_disabled"
    TOOL_CAPABILITY_ENABLED = "tool_capability_enabled"
    DUPLICATE_TOOL_REJECTED = "duplicate_tool_rejected"
    QUARANTINE_RECORD_CREATED = "quarantine_record_created"
    INVOCATION_DRAFT_CREATED = "invocation_draft_created"
    INVOCATION_DRAFT_REJECTED = "invocation_draft_rejected"
    INVOCATION_DRAFT_BLOCKED = "invocation_draft_blocked"
    INVOCATION_DRAFT_REQUIRES_APPROVAL = "invocation_draft_requires_approval"
    REGISTRY_BUILT = "registry_built"


@dataclass
class ToolLifecycleEvent:
    event_id: str
    event_type: ToolLifecycleEventType
    timestamp: datetime
    source: str | None = None
    plugin_id: str | None = None
    tool_id: str | None = None
    draft_id: str | None = None
    registry_status: str | None = None
    load_status: str | None = None
    risk_class: str | None = None
    severity_max: str | None = None
    approval_required: bool | None = None
    subject_type: str | None = None
    subject_id: str | None = None
    correlation_id: str | None = None
    parent_event_id: str | None = None
    manifest_hash: str | None = None
    source_path: str | None = None
    message: str | None = None
    issues: list[ValidationIssue] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "timestamp": s.datetime_to_iso(self.timestamp),
            "source": self.source,
            "plugin_id": self.plugin_id,
            "tool_id": self.tool_id,
            "draft_id": self.draft_id,
            "registry_status": self.registry_status,
            "load_status": self.load_status,
            "risk_class": self.risk_class,
            "severity_max": self.severity_max,
            "approval_required": self.approval_required,
            "subject_type": self.subject_type,
            "subject_id": self.subject_id,
            "correlation_id": self.correlation_id,
            "parent_event_id": self.parent_event_id,
            "manifest_hash": self.manifest_hash,
            "source_path": self.source_path,
            "message": self.message,
            "issues": [issue.to_dict() for issue in self.issues],
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ToolLifecycleEvent:
        return cls(
            event_id=str(data["event_id"]),
            event_type=ToolLifecycleEventType(data["event_type"]),
            timestamp=s.datetime_from_iso(data["timestamp"]) or datetime.now(timezone.utc),
            source=data.get("source"),
            plugin_id=data.get("plugin_id"),
            tool_id=data.get("tool_id"),
            draft_id=data.get("draft_id"),
            registry_status=data.get("registry_status"),
            load_status=data.get("load_status"),
            risk_class=data.get("risk_class"),
            severity_max=data.get("severity_max"),
            approval_required=data.get("approval_required"),
            subject_type=data.get("subject_type"),
            subject_id=data.get("subject_id"),
            correlation_id=data.get("correlation_id"),
            parent_event_id=data.get("parent_event_id"),
            manifest_hash=data.get("manifest_hash"),
            source_path=data.get("source_path"),
            message=data.get("message"),
            issues=[
                ValidationIssue.from_dict(item)
                for item in (data.get("issues") or [])
            ],
            metadata=dict(data.get("metadata") or {}),
        )


class ToolLifecycleEventRecorder:
    """In-memory lifecycle event recorder — not a hash-chain ledger."""

    def __init__(self) -> None:
        self.events: list[ToolLifecycleEvent] = []
        self._by_id: dict[str, ToolLifecycleEvent] = {}

    def record(self, event: ToolLifecycleEvent) -> ToolLifecycleEvent:
        self.events.append(event)
        self._by_id[event.event_id] = event
        return event

    def list_events(self) -> list[ToolLifecycleEvent]:
        return list(self.events)

    def list_by_tool(self, tool_id: str) -> list[ToolLifecycleEvent]:
        return [event for event in self.events if event.tool_id == tool_id]

    def list_by_plugin(self, plugin_id: str) -> list[ToolLifecycleEvent]:
        return [event for event in self.events if event.plugin_id == plugin_id]

    def list_by_type(self, event_type: ToolLifecycleEventType) -> list[ToolLifecycleEvent]:
        return [event for event in self.events if event.event_type is event_type]

    def get_event(self, event_id: str) -> ToolLifecycleEvent | None:
        return self._by_id.get(event_id)

    def clear(self) -> None:
        self.events.clear()
        self._by_id.clear()


def event_to_dict(event: ToolLifecycleEvent) -> dict[str, Any]:
    return event.to_dict()


def event_from_dict(data: dict[str, Any]) -> ToolLifecycleEvent:
    return ToolLifecycleEvent.from_dict(data)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _severity_max(issues: list[ValidationIssue]) -> ValidationSeverity | None:
    if not issues:
        return None
    return max(issues, key=lambda issue: _SEVERITY_RANK[issue.severity]).severity


def _predicted_effect_metadata(predicted_effect: PredictedEffect | None) -> dict[str, Any]:
    if predicted_effect is None:
        return {}
    return predicted_effect.to_dict()


def _new_event(
    event_type: ToolLifecycleEventType,
    *,
    message: str | None = None,
    source: str = "tool_manifest",
    plugin_id: str | None = None,
    tool_id: str | None = None,
    draft_id: str | None = None,
    registry_status: str | None = None,
    load_status: str | None = None,
    risk_class: str | None = None,
    severity_max: ValidationSeverity | None = None,
    approval_required: bool | None = None,
    subject_type: str | None = None,
    subject_id: str | None = None,
    correlation_id: str | None = None,
    parent_event_id: str | None = None,
    manifest_hash: str | None = None,
    source_path: str | None = None,
    issues: list[ValidationIssue] | None = None,
    metadata: dict[str, Any] | None = None,
) -> ToolLifecycleEvent:
    issue_list = list(issues or [])
    resolved_severity = severity_max if severity_max is not None else _severity_max(issue_list)
    return ToolLifecycleEvent(
        event_id=new_id("tlc"),
        event_type=event_type,
        timestamp=_utc_now(),
        source=source,
        plugin_id=plugin_id,
        tool_id=tool_id,
        draft_id=draft_id,
        registry_status=registry_status,
        load_status=load_status,
        risk_class=risk_class,
        severity_max=s.enum_value(resolved_severity),
        approval_required=approval_required,
        subject_type=subject_type,
        subject_id=subject_id,
        correlation_id=correlation_id,
        parent_event_id=parent_event_id,
        manifest_hash=manifest_hash,
        source_path=source_path,
        message=message,
        issues=issue_list,
        metadata=dict(metadata or {}),
    )


def build_manifest_loaded_event(result: ManifestLoadResult) -> ToolLifecycleEvent:
    plugin_id = result.plugin_manifest.plugin_id if result.plugin_manifest else None
    tool_ids = [tool.tool_id for tool in result.tool_manifests]
    metadata: dict[str, Any] = {"tool_ids": tool_ids}
    if result.parse_error:
        metadata["parse_error"] = result.parse_error

    message = f"manifest loaded from {result.source_path}"
    if result.status is ManifestLoadStatus.LOADED_WITH_WARNINGS:
        message = f"manifest loaded with warnings from {result.source_path}"

    return _new_event(
        ToolLifecycleEventType.MANIFEST_LOADED,
        message=message,
        source_path=result.source_path,
        manifest_hash=result.manifest_hash,
        load_status=result.status.value,
        plugin_id=plugin_id,
        issues=list(result.validation_issues),
        metadata=metadata,
    )


def build_manifest_rejected_event(result: ManifestLoadResult) -> ToolLifecycleEvent:
    event_type = ToolLifecycleEventType.MANIFEST_REJECTED
    if result.status is ManifestLoadStatus.PARSE_ERROR:
        event_type = ToolLifecycleEventType.MANIFEST_PARSE_ERROR

    plugin_id = result.plugin_manifest.plugin_id if result.plugin_manifest else None
    metadata: dict[str, Any] = {}
    if result.parse_error:
        metadata["parse_error"] = result.parse_error

    message = result.parse_error or f"manifest rejected: {result.status.value}"
    if result.status is ManifestLoadStatus.INVALID:
        message = f"manifest invalid at {result.source_path}"

    return _new_event(
        event_type,
        message=message,
        source_path=result.source_path,
        manifest_hash=result.manifest_hash,
        load_status=result.status.value,
        plugin_id=plugin_id,
        issues=list(result.validation_issues),
        metadata=metadata,
    )


def build_tool_registered_event(result: ToolRegistryResult) -> ToolLifecycleEvent:
    risk_class: str | None = None
    metadata: dict[str, Any] = {}
    if result.entry is not None and result.entry.capability is not None:
        cap = result.entry.capability
        risk_class = s.enum_value(cap.risk_class)
        metadata["capability_status"] = s.enum_value(cap.current_status)
        metadata["dry_run_supported"] = cap.dry_run_capable
        metadata["simulation_supported"] = cap.simulation_capable
    if result.entry is not None and result.entry.manifest_hash:
        metadata["manifest_hash"] = result.entry.manifest_hash
    if result.entry is not None and result.entry.capability is not None:
        metadata = _merge_research_metadata(metadata, result.entry.capability)

    return _new_event(
        ToolLifecycleEventType.TOOL_CAPABILITY_REGISTERED,
        message=result.message or f"tool '{result.tool_id}' registered",
        tool_id=result.tool_id,
        plugin_id=result.plugin_id,
        registry_status=result.status.value,
        risk_class=risk_class,
        issues=list(result.issues),
        metadata=metadata,
    )


def build_tool_rejected_event(result: ToolRegistryResult) -> ToolLifecycleEvent:
    event_type = ToolLifecycleEventType.TOOL_CAPABILITY_REJECTED
    if result.status is ToolRegistryOperationStatus.ALREADY_EXISTS:
        event_type = ToolLifecycleEventType.DUPLICATE_TOOL_REJECTED
    elif result.message and "duplicate" in result.message.lower():
        event_type = ToolLifecycleEventType.DUPLICATE_TOOL_REJECTED

    return _new_event(
        event_type,
        message=result.message or f"tool '{result.tool_id}' rejected",
        tool_id=result.tool_id,
        plugin_id=result.plugin_id,
        registry_status=result.status.value,
        issues=list(result.issues),
        metadata={"quarantine_record_id": result.quarantine_record_id},
    )


def build_tool_disabled_event(result: ToolRegistryResult) -> ToolLifecycleEvent:
    return _new_event(
        ToolLifecycleEventType.TOOL_CAPABILITY_DISABLED,
        message=result.message or f"tool '{result.tool_id}' disabled",
        tool_id=result.tool_id,
        plugin_id=result.plugin_id,
        registry_status=result.status.value,
        issues=list(result.issues),
    )


def build_tool_enabled_event(result: ToolRegistryResult) -> ToolLifecycleEvent:
    return _new_event(
        ToolLifecycleEventType.TOOL_CAPABILITY_ENABLED,
        message=result.message or f"tool '{result.tool_id}' enabled",
        tool_id=result.tool_id,
        plugin_id=result.plugin_id,
        registry_status=result.status.value,
        issues=list(result.issues),
    )


def build_quarantine_record_created_event(record: QuarantineRecord) -> ToolLifecycleEvent:
    subject_type = (
        record.subject_type.value
        if hasattr(record.subject_type, "value")
        else str(record.subject_type)
    )
    metadata: dict[str, Any] = {
        "quarantine_reasons": [reason.value for reason in record.reasons],
        "suggested_action": record.suggested_action,
        "can_be_reviewed": record.can_be_reviewed,
        "quarantine_status": record.status.value,
    }
    if record.threat_surface:
        metadata["threat_surface"] = record.threat_surface

    return _new_event(
        ToolLifecycleEventType.QUARANTINE_RECORD_CREATED,
        message=f"quarantine record created for {subject_type}:{record.subject_id}",
        subject_type=subject_type,
        subject_id=record.subject_id,
        plugin_id=record.plugin_id,
        tool_id=record.tool_id,
        source_path=record.source_path,
        manifest_hash=record.manifest_hash,
        severity_max=record.severity_max,
        issues=list(record.validation_issues),
        metadata=metadata,
    )


def build_invocation_draft_event(result: ToolInvocationDraftResult) -> ToolLifecycleEvent:
    status_map = {
        ToolInvocationDraftResultStatus.CREATED: ToolLifecycleEventType.INVOCATION_DRAFT_CREATED,
        ToolInvocationDraftResultStatus.REQUIRES_APPROVAL: (
            ToolLifecycleEventType.INVOCATION_DRAFT_REQUIRES_APPROVAL
        ),
        ToolInvocationDraftResultStatus.TOOL_QUARANTINED: ToolLifecycleEventType.INVOCATION_DRAFT_BLOCKED,
        ToolInvocationDraftResultStatus.TOOL_NOT_ACTIVE: ToolLifecycleEventType.INVOCATION_DRAFT_BLOCKED,
        ToolInvocationDraftResultStatus.BLOCKED: ToolLifecycleEventType.INVOCATION_DRAFT_BLOCKED,
        ToolInvocationDraftResultStatus.INVALID_INPUT: ToolLifecycleEventType.INVOCATION_DRAFT_REJECTED,
        ToolInvocationDraftResultStatus.REJECTED: ToolLifecycleEventType.INVOCATION_DRAFT_REJECTED,
        ToolInvocationDraftResultStatus.TOOL_NOT_FOUND: ToolLifecycleEventType.INVOCATION_DRAFT_REJECTED,
    }
    event_type = status_map.get(
        result.status,
        ToolLifecycleEventType.INVOCATION_DRAFT_REJECTED,
    )

    draft = result.draft
    metadata: dict[str, Any] = {}
    if result.blocked_reason:
        metadata["blocked_reason"] = result.blocked_reason
    if draft is not None:
        metadata["purpose"] = draft.purpose
        metadata["requested_by"] = draft.requested_by
        if draft.evidence_plan:
            metadata["evidence_plan"] = draft.evidence_plan
        if draft.predicted_effect is not None:
            metadata["predicted_effect"] = _predicted_effect_metadata(draft.predicted_effect)
    if result.research_metadata:
        metadata.update(result.research_metadata)

    return _new_event(
        event_type,
        message=result.message or f"invocation draft {result.status.value}",
        tool_id=result.tool_id,
        draft_id=draft.draft_id if draft else None,
        risk_class=s.enum_value(draft.risk_class) if draft else None,
        approval_required=result.approval_required,
        issues=list(result.issues),
        metadata=metadata,
    )


def build_registry_built_event(results: list[ToolRegistryResult]) -> ToolLifecycleEvent:
    registered = sum(
        1 for result in results if result.status is ToolRegistryOperationStatus.REGISTERED
    )
    rejected = sum(
        1
        for result in results
        if result.status
        in {
            ToolRegistryOperationStatus.REJECTED,
            ToolRegistryOperationStatus.ALREADY_EXISTS,
            ToolRegistryOperationStatus.INVALID,
            ToolRegistryOperationStatus.QUARANTINED,
        }
    )
    metadata = {
        "registered_count": registered,
        "rejected_count": rejected,
        "total_results": len(results),
    }
    return _new_event(
        ToolLifecycleEventType.REGISTRY_BUILT,
        message=f"registry built: {registered} registered, {rejected} rejected",
        metadata=metadata,
    )
