"""P1.3.4 — Quarantine + Validation Error Handling tests."""

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
    QuarantineStore,
    QuarantineSubjectType,
    Reversibility,
    RiskClass,
    SecretPolicy,
    SideEffectType,
    ToolCategory,
    ToolManifest,
    ToolRegistry,
    ToolRegistryOperationStatus,
    TraceLevel,
    TrustLevel,
    ValidationIssue,
    ValidationSeverity,
    classify_validation_issues,
    create_quarantine_record,
    decide_quarantine_for_manifest_result,
    decide_quarantine_for_plugin,
    decide_quarantine_for_tool,
    load_manifest_file,
    reasons_from_issues,
    validate_tool_manifest,
)
from agentic_runtime.tool_manifest.loader import DUPLICATE_TOOL_ID_IN_BUNDLE
from agentic_runtime.tool_manifest.validation import (
    HIGH_RISK_REQUIRES_APPROVAL,
    NETWORK_REQUIRES_NETWORK_POLICY,
    SECRET_ACCESS_REQUIRES_SECRET_POLICY,
    STATE_CHANGE_MISSING_PREDICTED_EFFECT,
)

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "tool_manifests"


def _now() -> datetime:
    return datetime(2026, 6, 20, 12, 0, 0, tzinfo=timezone.utc)


def _plugin(**overrides) -> PluginManifest:
    base = PluginManifest(
        plugin_id="plugin.test",
        name="Test Plugin",
        version="0.1.0",
        description="Test",
        owner="tests",
        origin=PluginOrigin.BUILTIN,
        trust_level=TrustLevel.HIGH,
        status=PluginStatus.ACTIVE,
        created_at=_now(),
        updated_at=_now(),
        tools=["tool.test"],
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
        tool_id="tool.test",
        plugin_id="plugin.test",
        name="Test Tool",
        description="Test tool",
        category=ToolCategory.CODE,
        capability_types=[CapabilityType.READ],
        input_schema={"type": "object"},
        output_schema={"type": "object"},
        side_effects=[SideEffectType.LOCAL_READ],
        risk_class=RiskClass.R1,
        reversibility=Reversibility.NONE,
        requires_approval=False,
        permissions_required=[],
        data_access=[DataAccessType.LOCAL_PROJECT],
        execution_environment=ExecutionEnvironment.RUNTIME,
        dry_run_supported=False,
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


def test_validation_report_counts_severity():
    issues = [
        ValidationIssue("A", "info", None, ValidationSeverity.INFO),
        ValidationIssue("B", "warn", None, ValidationSeverity.WARNING),
        ValidationIssue("C", "err", None, ValidationSeverity.ERROR),
        ValidationIssue("D", "crit", None, ValidationSeverity.CRITICAL),
    ]
    report = classify_validation_issues(issues, subject_id="tool.test", subject_type="tool")
    assert report.issue_count == 4
    assert report.info_count == 1
    assert report.warning_count == 1
    assert report.error_count == 1
    assert report.critical_count == 1
    assert report.blocking_count == 2
    assert report.severity_max is ValidationSeverity.CRITICAL


def test_validation_report_detects_blocking_issues():
    blocking = classify_validation_issues([
        ValidationIssue("E", "err", None, ValidationSeverity.ERROR),
    ])
    assert blocking.is_blocking is True

    warnings = classify_validation_issues([
        ValidationIssue("W", "warn", None, ValidationSeverity.WARNING),
    ])
    assert warnings.is_blocking is False


def test_plugin_unknown_active_origin_quarantined():
    plugin = _plugin(origin=PluginOrigin.UNKNOWN, status=PluginStatus.ACTIVE)
    issues = validate_tool_manifest(_tool(), plugin)
    decision = decide_quarantine_for_plugin(plugin, issues)
    assert decision.should_quarantine is True
    assert QuarantineReason.UNKNOWN_ORIGIN in decision.reasons


def test_untrusted_active_plugin_quarantined():
    plugin = _plugin(trust_level=TrustLevel.UNTRUSTED, status=PluginStatus.ACTIVE)
    decision = decide_quarantine_for_plugin(plugin, [])
    assert decision.should_quarantine is True
    assert QuarantineReason.UNTRUSTED_PLUGIN in decision.reasons


def test_quarantined_plugin_creates_quarantine_decision():
    plugin = _plugin(status=PluginStatus.QUARANTINED)
    decision = decide_quarantine_for_plugin(plugin, [])
    assert decision.should_quarantine is True
    assert QuarantineReason.PLUGIN_STATUS_QUARANTINED in decision.reasons


def test_invalid_plugin_status_rejected_or_quarantined():
    plugin = _plugin(status=PluginStatus.INVALID)
    decision = decide_quarantine_for_plugin(plugin, [])
    assert decision.should_quarantine is True
    assert decision.should_reject is True
    assert QuarantineReason.PLUGIN_STATUS_INVALID in decision.reasons


def test_r6_enabled_tool_quarantined():
    tool = _tool(risk_class=RiskClass.R6, enabled=True, requires_approval=True,
                 permissions_required=["x"], trace_level=TraceLevel.FORENSIC)
    decision = decide_quarantine_for_tool(tool, _plugin(), validate_tool_manifest(tool, _plugin()))
    assert decision.should_quarantine is True
    assert decision.should_reject is True
    assert QuarantineReason.R6_ENABLED in decision.reasons


def test_r5_without_evidence_quarantined():
    tool = _tool(
        risk_class=RiskClass.R5,
        requires_approval=True,
        evidence_required=False,
        permissions_required=["write"],
        trace_level=TraceLevel.FORENSIC,
    )
    issues = validate_tool_manifest(tool, _plugin())
    decision = decide_quarantine_for_tool(tool, _plugin(), issues)
    assert decision.should_quarantine is True
    assert QuarantineReason.HIGH_RISK_WITHOUT_APPROVAL in decision.reasons


def test_high_risk_without_approval_quarantined():
    tool = _tool(risk_class=RiskClass.R4, requires_approval=False, trace_level=TraceLevel.DETAILED)
    issues = validate_tool_manifest(tool, _plugin())
    decision = decide_quarantine_for_tool(tool, _plugin(), issues)
    assert decision.should_quarantine is True
    assert QuarantineReason.HIGH_RISK_WITHOUT_APPROVAL in decision.reasons


def test_secret_access_without_secret_policy_quarantined():
    tool = _tool(
        risk_class=RiskClass.R4,
        side_effects=[SideEffectType.SECRET_ACCESS],
        requires_approval=True,
        permissions_required=["secrets.read"],
        trace_level=TraceLevel.DETAILED,
        evidence_required=True,
        data_access=[DataAccessType.LOCAL_PROJECT],
    )
    plugin = _plugin(secret_policy=None)
    issues = validate_tool_manifest(tool, plugin)
    decision = decide_quarantine_for_tool(tool, plugin, issues)
    assert QuarantineReason.SECRET_POLICY_MISSING in decision.reasons
    assert decision.should_quarantine is True


def test_network_without_network_policy_quarantined():
    tool = _tool(
        risk_class=RiskClass.R3,
        side_effects=[SideEffectType.NETWORK],
        requires_approval=True,
        permissions_required=["network.read"],
        trace_level=TraceLevel.STANDARD,
        data_access=[DataAccessType.EXTERNAL],
    )
    plugin = _plugin(network_policy=None)
    issues = validate_tool_manifest(tool, plugin)
    decision = decide_quarantine_for_tool(tool, plugin, issues)
    assert QuarantineReason.NETWORK_POLICY_MISSING in decision.reasons
    assert decision.should_quarantine is True


def test_state_change_high_risk_missing_predicted_effect_quarantined():
    tool = _tool(
        risk_class=RiskClass.R4,
        side_effects=[SideEffectType.STATE_CHANGE],
        requires_approval=True,
        permissions_required=["state.write"],
        trace_level=TraceLevel.DETAILED,
        evidence_required=True,
        predicted_effect=None,
    )
    issues = validate_tool_manifest(tool, _plugin())
    decision = decide_quarantine_for_tool(tool, _plugin(), issues)
    assert QuarantineReason.MISSING_PREDICTED_EFFECT in decision.reasons
    assert decision.should_quarantine is True


def test_duplicate_tool_id_can_create_quarantine_reason():
    issue = ValidationIssue(
        DUPLICATE_TOOL_ID_IN_BUNDLE,
        "duplicate",
        "tools",
        ValidationSeverity.ERROR,
    )
    reasons = reasons_from_issues([issue])
    assert QuarantineReason.DUPLICATE_TOOL_ID in reasons


def test_create_quarantine_record():
    issues = [
        ValidationIssue(
            HIGH_RISK_REQUIRES_APPROVAL,
            "approval required",
            "requires_approval",
            ValidationSeverity.ERROR,
        ),
    ]
    decision = decide_quarantine_for_tool(
        _tool(risk_class=RiskClass.R4, requires_approval=False, trace_level=TraceLevel.DETAILED),
        _plugin(),
        issues,
    )
    record = create_quarantine_record(
        QuarantineSubjectType.TOOL,
        "tool.test",
        issues,
        decision,
        plugin_id="plugin.test",
        tool_id="tool.test",
        source_path="/tmp/manifest.json",
        manifest_hash="abc",
    )
    assert record.subject_id == "tool.test"
    assert record.reasons
    assert record.validation_issues
    assert record.severity_max is ValidationSeverity.ERROR
    assert record.suggested_action is not None


def test_quarantine_store_add_and_get_record():
    store = QuarantineStore()
    record = create_quarantine_record(
        QuarantineSubjectType.TOOL,
        "tool.a",
        [],
        decide_quarantine_for_plugin(_plugin(status=PluginStatus.QUARANTINED), []),
        tool_id="tool.a",
    )
    store.add_record(record)
    assert store.get_record(record.record_id) is record


def test_quarantine_store_list_by_plugin():
    store = QuarantineStore()
    record = create_quarantine_record(
        QuarantineSubjectType.PLUGIN,
        "plugin.a",
        [],
        decide_quarantine_for_plugin(_plugin(plugin_id="plugin.a", status=PluginStatus.QUARANTINED), []),
        plugin_id="plugin.a",
    )
    store.add_record(record)
    assert len(store.list_by_plugin("plugin.a")) == 1


def test_quarantine_store_list_by_tool():
    store = QuarantineStore()
    record = create_quarantine_record(
        QuarantineSubjectType.TOOL,
        "tool.a",
        [],
        decide_quarantine_for_tool(_tool(tool_id="tool.a", risk_class=RiskClass.R6, enabled=True), _plugin(), []),
        tool_id="tool.a",
    )
    store.add_record(record)
    assert len(store.list_by_tool("tool.a")) == 1


def test_quarantine_store_list_review_required():
    store = QuarantineStore()
    record = create_quarantine_record(
        QuarantineSubjectType.TOOL,
        "tool.a",
        [ValidationIssue(HIGH_RISK_REQUIRES_APPROVAL, "x", None, ValidationSeverity.ERROR)],
        decide_quarantine_for_tool(
            _tool(risk_class=RiskClass.R4, requires_approval=False, trace_level=TraceLevel.DETAILED),
            _plugin(),
            [],
        ),
        tool_id="tool.a",
    )
    store.add_record(record)
    assert len(store.list_review_required()) >= 1


def test_invalid_loader_result_creates_quarantine_decision():
    result = load_manifest_file(FIXTURES / "invalid_high_risk_no_approval.json")
    decision = decide_quarantine_for_manifest_result(result)
    assert result.status is ManifestLoadStatus.INVALID
    assert decision.should_quarantine is True
    assert decision.should_reject is True


def test_loaded_with_warnings_not_automatically_quarantined():
    plugin = _plugin(origin=PluginOrigin.EXTERNAL, trust_level=TrustLevel.HIGH)
    issues = validate_tool_manifest(_tool(), plugin)
    decision = decide_quarantine_for_plugin(plugin, issues)
    assert any(issue.severity is ValidationSeverity.WARNING for issue in issues)
    assert decision.should_quarantine is False


def test_registry_does_not_activate_quarantined_tool():
    registry = ToolRegistry()
    result = registry.register_tool_manifest(
        _tool(tool_id="q.tool"),
        _plugin(tools=["q.tool"], status=PluginStatus.QUARANTINED),
    )
    assert result.status is ToolRegistryOperationStatus.QUARANTINED
    assert registry.has_tool("q.tool")
    assert not registry.is_active("q.tool")
    assert registry.list_active_tools() == []


def test_registry_preserves_validation_issues():
    plugin = _plugin(origin=PluginOrigin.EXTERNAL, trust_level=TrustLevel.HIGH)
    tool = _tool(tool_id="warn.tool")
    plugin = replace(plugin, tools=["warn.tool"])
    registry = ToolRegistry()
    result = registry.register_tool_manifest(tool, plugin)
    assert any(issue.severity is ValidationSeverity.WARNING for issue in result.issues)
    entry = registry.get_tool("warn.tool")
    assert entry is not None
    assert any(issue.severity is ValidationSeverity.WARNING for issue in entry.validation_errors)


def test_warning_only_tool_can_register_but_not_lose_warnings():
    plugin = _plugin(origin=PluginOrigin.EXTERNAL, trust_level=TrustLevel.HIGH, tools=["warn.tool"])
    registry = ToolRegistry()
    result = registry.register_tool_manifest(_tool(tool_id="warn.tool"), plugin)
    assert result.status is ToolRegistryOperationStatus.REGISTERED
    assert registry.is_active("warn.tool")
    assert any(issue.severity is ValidationSeverity.WARNING for issue in result.issues)


def test_quarantine_is_not_execution():
    source = inspect.getsource(classify_validation_issues)
    assert "execute" not in source
    store = QuarantineStore()
    assert not hasattr(store, "invoke")


def test_registry_rejects_r6_with_quarantine_record():
    registry = ToolRegistry()
    result = registry.register_tool_manifest(
        _tool(
            tool_id="r6.tool",
            risk_class=RiskClass.R6,
            enabled=True,
            requires_approval=True,
            permissions_required=["blocked"],
            trace_level=TraceLevel.FORENSIC,
        ),
        _plugin(tools=["r6.tool"]),
    )
    assert result.status in {
        ToolRegistryOperationStatus.REJECTED,
        ToolRegistryOperationStatus.QUARANTINED,
    }
    assert result.quarantine_record_id is not None
    assert not registry.is_active("r6.tool")
    assert registry.quarantine_store.has_quarantined_subject("r6.tool")
