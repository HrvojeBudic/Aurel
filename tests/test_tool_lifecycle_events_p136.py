"""P1.3.6 — Tool Lifecycle Trace Events tests."""

from __future__ import annotations

import inspect
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

import pytest

from agentic_runtime.tool_manifest import (
    CapabilityType,
    ConfidenceSeed,
    DataAccessType,
    DataResidency,
    ExecutionEnvironment,
    FilesystemPolicy,
    ManifestLoadStatus,
    NetworkPolicy,
    PluginManifest,
    PluginOrigin,
    PluginStatus,
    PredictedEffect,
    QuarantineReason,
    QuarantineRecordStatus,
    QuarantineSubjectType,
    Reversibility,
    RiskClass,
    SecretPolicy,
    SideEffectType,
    ToolCategory,
    ToolInvocationContext,
    ToolLifecycleEventRecorder,
    ToolLifecycleEventType,
    ToolManifest,
    ToolRegistry,
    ToolRegistryOperationStatus,
    TraceLevel,
    TrustLevel,
    ValidationIssue,
    ValidationSeverity,
    build_invocation_draft_event,
    build_manifest_loaded_event,
    build_manifest_rejected_event,
    build_quarantine_record_created_event,
    build_tool_disabled_event,
    build_tool_enabled_event,
    build_tool_registered_event,
    build_tool_rejected_event,
    create_quarantine_record,
    create_tool_invocation_draft,
    event_from_dict,
    event_to_dict,
    load_manifest_file,
)
from agentic_runtime.tool_manifest.events import build_registry_built_event
from agentic_runtime.tool_manifest.quarantine import QuarantineDecision

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "tool_manifests"


def _now() -> datetime:
    return datetime(2026, 6, 20, 12, 0, 0, tzinfo=timezone.utc)


def _plugin(**overrides) -> PluginManifest:
    base = PluginManifest(
        plugin_id="plugin.core",
        name="Core",
        version="1.0.0",
        description="Core plugin",
        owner="tests",
        origin=PluginOrigin.BUILTIN,
        trust_level=TrustLevel.HIGH,
        status=PluginStatus.ACTIVE,
        created_at=_now(),
        updated_at=_now(),
        tools=["tool.read"],
        required_permissions=[],
        data_residency=DataResidency.LOCAL,
        network_policy=NetworkPolicy.NONE,
        filesystem_policy=FilesystemPolicy.READ_ONLY,
        secret_policy=SecretPolicy.FORBIDDEN,
        runtime_surfaces=["runtime"],
        compatibility={},
        integrity_hash=None,
    )
    return replace(base, **overrides) if overrides else base


def _tool(**overrides) -> ToolManifest:
    base = ToolManifest(
        tool_id="tool.read",
        plugin_id="plugin.core",
        name="Read File",
        description="Read file",
        category=ToolCategory.FILESYSTEM,
        capability_types=[CapabilityType.READ, CapabilityType.ANALYZE],
        input_schema={
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"],
        },
        output_schema={"type": "object"},
        side_effects=[SideEffectType.LOCAL_READ],
        risk_class=RiskClass.R1,
        reversibility=Reversibility.NONE,
        requires_approval=False,
        permissions_required=[],
        data_access=[DataAccessType.LOCAL_PROJECT],
        execution_environment=ExecutionEnvironment.RUNTIME,
        dry_run_supported=True,
        simulation_supported=False,
        predicted_effect=None,
        failure_modes=[],
        evidence_required=False,
        trace_level=TraceLevel.MINIMAL,
        timeout_policy=None,
        rate_limit_policy=None,
        enabled=True,
    )
    return replace(base, **overrides) if overrides else base


def _high_risk_tool(**overrides) -> ToolManifest:
    predicted = overrides.pop("predicted_effect", PredictedEffect(
        state_target="file",
        expected_delta="write",
        affected_objects=["file.txt"],
        reversible=True,
        confidence_seed=ConfidenceSeed.MEDIUM,
    ))
    trace = overrides.pop("trace_level", TraceLevel.DETAILED)
    base = {
        "tool_id": "tool.write",
        "side_effects": [SideEffectType.LOCAL_WRITE],
        "capability_types": [CapabilityType.WRITE],
        "reversibility": Reversibility.REVERSIBLE,
        "permissions_required": ["write"],
        "risk_class": RiskClass.R4,
        "requires_approval": True,
        "trace_level": trace,
        "predicted_effect": predicted,
        "input_schema": {
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"],
        },
    }
    base.update(overrides)
    return _tool(**base)


def _context() -> ToolInvocationContext:
    return ToolInvocationContext(
        requested_by="operator",
        purpose="Inspect file",
        request_source="test",
    )


def test_create_manifest_loaded_event():
    result = load_manifest_file(FIXTURES / "valid_builtin_repo.json")
    assert result.status in {ManifestLoadStatus.LOADED, ManifestLoadStatus.LOADED_WITH_WARNINGS}
    event = build_manifest_loaded_event(result)
    assert event.event_type is ToolLifecycleEventType.MANIFEST_LOADED
    assert event.source_path == result.source_path
    assert event.manifest_hash == result.manifest_hash
    assert event.load_status == result.status.value
    assert event.plugin_id == "builtin.repo"
    assert "builtin.repo_scan" in event.metadata.get("tool_ids", [])


def test_create_manifest_rejected_event():
    result = load_manifest_file(FIXTURES / "invalid_empty_tools.json")
    assert result.status is ManifestLoadStatus.INVALID
    event = build_manifest_rejected_event(result)
    assert event.event_type is ToolLifecycleEventType.MANIFEST_REJECTED
    assert event.source_path == result.source_path
    assert event.load_status == ManifestLoadStatus.INVALID.value
    assert event.issues


def test_create_manifest_parse_error_event():
    result = load_manifest_file(FIXTURES / "malformed_manifest.json")
    assert result.status is ManifestLoadStatus.PARSE_ERROR
    event = build_manifest_rejected_event(result)
    assert event.event_type is ToolLifecycleEventType.MANIFEST_PARSE_ERROR
    assert result.parse_error
    assert event.metadata.get("parse_error") == result.parse_error


def test_create_tool_registered_event():
    registry = ToolRegistry()
    result = registry.register_tool_manifest(_tool(), _plugin())
    assert result.status is ToolRegistryOperationStatus.REGISTERED
    event = build_tool_registered_event(result)
    assert event.event_type is ToolLifecycleEventType.TOOL_CAPABILITY_REGISTERED
    assert event.tool_id == "tool.read"
    assert event.plugin_id == "plugin.core"
    assert event.registry_status == ToolRegistryOperationStatus.REGISTERED.value
    assert event.risk_class == RiskClass.R1.value


def test_create_tool_rejected_event():
    registry = ToolRegistry()
    result = registry.register_tool_manifest(
        _high_risk_tool(requires_approval=False, side_effects=[SideEffectType.EXTERNAL_WRITE]),
        _plugin(tools=["tool.write"], network_policy=NetworkPolicy.ALLOWLISTED),
    )
    assert result.status in {
        ToolRegistryOperationStatus.REJECTED,
        ToolRegistryOperationStatus.QUARANTINED,
    }
    event = build_tool_rejected_event(result)
    assert event.event_type is ToolLifecycleEventType.TOOL_CAPABILITY_REJECTED
    assert event.tool_id == "tool.write"


def test_create_duplicate_tool_rejected_event_if_detectable():
    registry = ToolRegistry()
    registry.register_tool_manifest(_tool(), _plugin())
    duplicate = registry.register_tool_manifest(_tool(), _plugin())
    assert duplicate.status is ToolRegistryOperationStatus.ALREADY_EXISTS
    event = build_tool_rejected_event(duplicate)
    assert event.event_type is ToolLifecycleEventType.DUPLICATE_TOOL_REJECTED


def test_create_tool_disabled_event():
    registry = ToolRegistry()
    registry.register_tool_manifest(_tool(), _plugin())
    result = registry.disable_tool("tool.read", reason="maintenance")
    event = build_tool_disabled_event(result)
    assert event.event_type is ToolLifecycleEventType.TOOL_CAPABILITY_DISABLED
    assert event.tool_id == "tool.read"


def test_create_tool_enabled_event():
    registry = ToolRegistry()
    registry.register_tool_manifest(_tool(), _plugin())
    registry.disable_tool("tool.read")
    result = registry.enable_tool("tool.read")
    event = build_tool_enabled_event(result)
    assert event.event_type is ToolLifecycleEventType.TOOL_CAPABILITY_ENABLED
    assert event.tool_id == "tool.read"


def test_create_quarantine_record_event():
    decision = QuarantineDecision(
        should_quarantine=True,
        reasons=[QuarantineReason.HIGH_RISK_WITHOUT_APPROVAL],
        severity_max=ValidationSeverity.ERROR,
        message="high risk without approval",
    )
    issues = [
        ValidationIssue("HIGH_RISK", "approval required", "requires_approval", ValidationSeverity.ERROR),
    ]
    record = create_quarantine_record(
        QuarantineSubjectType.TOOL,
        "tool.risky",
        issues,
        decision,
        plugin_id="plugin.core",
        tool_id="tool.risky",
        source_path="/tmp/manifest.json",
        manifest_hash="abc123",
    )
    event = build_quarantine_record_created_event(record)
    assert event.event_type is ToolLifecycleEventType.QUARANTINE_RECORD_CREATED
    assert event.subject_id == "tool.risky"
    assert QuarantineReason.HIGH_RISK_WITHOUT_APPROVAL.value in event.metadata["quarantine_reasons"]
    assert event.metadata["suggested_action"] == record.suggested_action
    assert event.metadata["can_be_reviewed"] == record.can_be_reviewed
    assert event.metadata["quarantine_status"] in {
        QuarantineRecordStatus.QUARANTINED.value,
        QuarantineRecordStatus.REVIEW_REQUIRED.value,
    }


def test_create_invocation_draft_created_event():
    registry = ToolRegistry()
    registry.register_tool_manifest(_tool(), _plugin())
    draft_result = create_tool_invocation_draft(registry, "tool.read", {"path": "x"}, _context())
    event = build_invocation_draft_event(draft_result)
    assert event.event_type is ToolLifecycleEventType.INVOCATION_DRAFT_CREATED
    assert event.tool_id == "tool.read"
    assert event.draft_id == draft_result.draft.draft_id


def test_create_invocation_draft_blocked_event():
    registry = ToolRegistry()
    registry.register_tool_manifest(
        _tool(tool_id="q.tool"),
        _plugin(tools=["q.tool"], status=PluginStatus.QUARANTINED),
    )
    draft_result = create_tool_invocation_draft(registry, "q.tool", {"path": "x"}, _context())
    event = build_invocation_draft_event(draft_result)
    assert event.event_type is ToolLifecycleEventType.INVOCATION_DRAFT_BLOCKED
    assert draft_result.draft is None


def test_create_invocation_draft_requires_approval_event():
    registry = ToolRegistry()
    registry.register_tool_manifest(
        _high_risk_tool(),
        _plugin(tools=["tool.write"]),
    )
    draft_result = create_tool_invocation_draft(registry, "tool.write", {"path": "x"}, _context())
    event = build_invocation_draft_event(draft_result)
    assert event.event_type is ToolLifecycleEventType.INVOCATION_DRAFT_REQUIRES_APPROVAL
    assert event.approval_required is True


def test_create_invocation_draft_rejected_event():
    registry = ToolRegistry()
    registry.register_tool_manifest(_tool(), _plugin())
    draft_result = create_tool_invocation_draft(registry, "tool.read", {}, _context())
    event = build_invocation_draft_event(draft_result)
    assert event.event_type is ToolLifecycleEventType.INVOCATION_DRAFT_REJECTED
    assert draft_result.draft is None


def test_event_serialization_roundtrip():
    result = load_manifest_file(FIXTURES / "valid_builtin_repo.json")
    event = build_manifest_loaded_event(result)
    payload = event_to_dict(event)
    restored = event_from_dict(payload)
    assert restored.event_id == event.event_id
    assert restored.event_type == event.event_type
    assert restored.plugin_id == event.plugin_id
    assert len(restored.issues) == len(event.issues)


def test_event_recorder_records_event():
    recorder = ToolLifecycleEventRecorder()
    event = build_manifest_loaded_event(load_manifest_file(FIXTURES / "valid_builtin_repo.json"))
    recorded = recorder.record(event)
    assert recorded is event
    assert len(recorder.list_events()) == 1


def test_event_recorder_list_by_tool():
    recorder = ToolLifecycleEventRecorder()
    registry = ToolRegistry()
    reg = registry.register_tool_manifest(_tool(), _plugin())
    recorder.record(build_tool_registered_event(reg))
    assert len(recorder.list_by_tool("tool.read")) == 1
    assert recorder.list_by_tool("missing") == []


def test_event_recorder_list_by_plugin():
    recorder = ToolLifecycleEventRecorder()
    registry = ToolRegistry()
    reg = registry.register_tool_manifest(_tool(), _plugin())
    recorder.record(build_tool_registered_event(reg))
    assert len(recorder.list_by_plugin("plugin.core")) == 1


def test_event_recorder_list_by_type():
    recorder = ToolLifecycleEventRecorder()
    recorder.record(build_manifest_loaded_event(load_manifest_file(FIXTURES / "valid_builtin_repo.json")))
    assert len(recorder.list_by_type(ToolLifecycleEventType.MANIFEST_LOADED)) == 1


def test_event_recorder_get_event():
    recorder = ToolLifecycleEventRecorder()
    event = build_manifest_loaded_event(load_manifest_file(FIXTURES / "valid_builtin_repo.json"))
    recorder.record(event)
    assert recorder.get_event(event.event_id) == event
    assert recorder.get_event("missing") is None


def test_event_recorder_clear():
    recorder = ToolLifecycleEventRecorder()
    recorder.record(build_manifest_loaded_event(load_manifest_file(FIXTURES / "valid_builtin_repo.json")))
    recorder.clear()
    assert recorder.list_events() == []


def test_loader_result_can_emit_manifest_event():
    result = load_manifest_file(FIXTURES / "valid_builtin_repo.json")
    event = build_manifest_loaded_event(result)
    assert event.event_type is ToolLifecycleEventType.MANIFEST_LOADED


def test_registry_result_can_emit_tool_event():
    registry = ToolRegistry()
    result = registry.register_manifest_result(load_manifest_file(FIXTURES / "valid_builtin_repo.json"))
    assert result
    reg_result = registry.register_tool_manifest(
        _tool(tool_id="extra.tool", plugin_id="builtin.repo"),
        _plugin(plugin_id="builtin.repo", tools=["extra.tool"]),
    )
    if reg_result.status is ToolRegistryOperationStatus.REGISTERED:
        event = build_tool_registered_event(reg_result)
        assert event.tool_id == "extra.tool"


def test_quarantine_record_can_emit_event():
    decision = QuarantineDecision(should_quarantine=True, reasons=[QuarantineReason.INVALID_MANIFEST])
    record = create_quarantine_record(
        QuarantineSubjectType.MANIFEST_FILE,
        "bad.json",
        [],
        decision,
        source_path="bad.json",
    )
    event = build_quarantine_record_created_event(record)
    assert event.event_type is ToolLifecycleEventType.QUARANTINE_RECORD_CREATED


def test_invocation_draft_result_can_emit_event():
    registry = ToolRegistry()
    registry.register_tool_manifest(_tool(), _plugin())
    draft_result = create_tool_invocation_draft(registry, "tool.read", {"path": "README.md"}, _context())
    event = build_invocation_draft_event(draft_result)
    assert event.draft_id is not None
    assert event.metadata.get("purpose") == "Inspect file"


def test_p1_3_lifecycle_can_be_traced_without_execution():
    import agentic_runtime.tool_manifest.events as events_mod

    source = inspect.getsource(events_mod)
    for forbidden in ("execute_tool", "invoke_tool", "run_tool", ".invoke(", ".execute("):
        assert forbidden not in source

    recorder = ToolLifecycleEventRecorder()
    load = load_manifest_file(FIXTURES / "valid_builtin_repo.json")
    recorder.record(build_manifest_loaded_event(load))

    registry = ToolRegistry()
    reg_results = registry.register_manifest_result(load)
    for reg_result in reg_results:
        if reg_result.status is ToolRegistryOperationStatus.REGISTERED:
            recorder.record(build_tool_registered_event(reg_result))

    draft_result = create_tool_invocation_draft(
        registry,
        "builtin.repo_scan",
        {"root_path": "."},
        _context(),
    )
    recorder.record(build_invocation_draft_event(draft_result))

    assert len(recorder.list_events()) >= 2
    assert not hasattr(recorder, "execute")
    assert not hasattr(registry, "invoke")


def test_build_registry_built_event_summary():
    registry = ToolRegistry()
    results = [
        registry.register_tool_manifest(_tool(tool_id="a.tool"), _plugin(tools=["a.tool"])),
        registry.register_tool_manifest(_tool(tool_id="a.tool"), _plugin(tools=["a.tool"])),
    ]
    event = build_registry_built_event(results)
    assert event.event_type is ToolLifecycleEventType.REGISTRY_BUILT
    assert event.metadata["registered_count"] == 1
    assert event.metadata["rejected_count"] == 1
