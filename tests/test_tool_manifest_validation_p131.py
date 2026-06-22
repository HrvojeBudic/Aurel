"""P1.3.1 — Tool Manifest Risk + Permission Metadata Validation tests."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone

import pytest

from agentic_runtime.tool_manifest import (
    CapabilityType,
    ConfidenceSeed,
    DataAccessType,
    DataResidency,
    ExecutionEnvironment,
    FilesystemPolicy,
    NetworkPolicy,
    PluginManifest,
    PluginOrigin,
    PluginStatus,
    PredictedEffect,
    Reversibility,
    RiskClass,
    SecretPolicy,
    SideEffectType,
    ToolCategory,
    ToolManifest,
    TraceLevel,
    TrustLevel,
    ValidationIssue,
    ValidationSeverity,
    has_blocking_validation_issues,
    is_plugin_manifest_valid,
    is_tool_manifest_valid,
    validate_plugin_manifest,
    validate_tool_manifest,
    validation_summary,
)
from agentic_runtime.tool_manifest.validation import (
    INPUT_SCHEMA_MISSING,
    DISABLED_R6_REQUIRED,
    EXTERNAL_WRITE_REQUIRES_APPROVAL,
    HIGH_RISK_EMPTY_PERMISSIONS,
    HIGH_RISK_REQUIRES_APPROVAL,
    IRREVERSIBLE_TOOL_TOO_LOW_RISK,
    LOCAL_WRITE_REQUIRES_REVERSIBILITY,
    NETWORK_REQUIRES_NETWORK_POLICY,
    R0_HAS_SIDE_EFFECTS,
    R5_REQUIRES_EVIDENCE,
    SECRET_ACCESS_REQUIRES_DATA_ACCESS,
    SECRET_ACCESS_REQUIRES_SECRET_POLICY,
    STATE_CHANGE_MISSING_PREDICTED_EFFECT,
    TOOL_ID_MISSING,
    UNKNOWN_ORIGIN_HIGH_RISK,
    UNTRUSTED_PLUGIN_HIGH_RISK,
)


def _now() -> datetime:
    return datetime(2026, 6, 20, 12, 0, 0, tzinfo=timezone.utc)


def _valid_plugin(**overrides) -> PluginManifest:
    base = PluginManifest(
        plugin_id="plugin.core",
        name="Core Plugin",
        version="1.0.0",
        description="Built-in runtime tools",
        owner="runtime",
        origin=PluginOrigin.BUILTIN,
        trust_level=TrustLevel.HIGH,
        status=PluginStatus.ACTIVE,
        created_at=_now(),
        updated_at=_now(),
        tools=["tool.read"],
        required_permissions=[],
        data_residency=DataResidency.LOCAL,
        network_policy=NetworkPolicy.NONE,
        filesystem_policy=FilesystemPolicy.WORKSPACE_SCOPED,
        secret_policy=SecretPolicy.FORBIDDEN,
        runtime_surfaces=["runtime"],
        compatibility={"runtime": ">=0.2.0"},
        integrity_hash=None,
    )
    return replace(base, **overrides) if overrides else base


def _valid_read_tool(**overrides) -> ToolManifest:
    base = ToolManifest(
        tool_id="tool.read",
        plugin_id="plugin.core",
        name="Read File",
        description="Read a workspace file",
        category=ToolCategory.FILESYSTEM,
        capability_types=[CapabilityType.READ],
        input_schema={"type": "object"},
        output_schema={"type": "object"},
        side_effects=[SideEffectType.LOCAL_READ],
        risk_class=RiskClass.R1,
        reversibility=Reversibility.REVERSIBLE,
        requires_approval=False,
        permissions_required=[],
        data_access=[DataAccessType.LOCAL_PROJECT],
        execution_environment=ExecutionEnvironment.SANDBOX,
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


def _codes(issues: list[ValidationIssue]) -> set[str]:
    return {issue.code for issue in issues}


def test_valid_low_risk_read_only_tool_passes_validation():
    tool = _valid_read_tool()
    plugin = _valid_plugin()
    issues = validate_tool_manifest(tool, plugin)
    assert not has_blocking_validation_issues(issues)
    assert is_tool_manifest_valid(tool, plugin)


def test_missing_tool_id_fails_validation():
    tool = _valid_read_tool(tool_id="")
    issues = validate_tool_manifest(tool)
    assert TOOL_ID_MISSING in _codes(issues)
    assert not is_tool_manifest_valid(tool)


def test_missing_input_schema_fails_validation():
    tool = _valid_read_tool()
    tool.input_schema = None  # type: ignore[assignment]
    issues = validate_tool_manifest(tool)
    assert INPUT_SCHEMA_MISSING in _codes(issues)
    assert not is_tool_manifest_valid(tool)


def test_r0_tool_with_local_write_side_effect_fails():
    tool = _valid_read_tool(
        risk_class=RiskClass.R0,
        side_effects=[SideEffectType.LOCAL_WRITE],
        reversibility=Reversibility.REVERSIBLE,
        data_access=[DataAccessType.NONE],
    )
    issues = validate_tool_manifest(tool)
    assert R0_HAS_SIDE_EFFECTS in _codes(issues)
    assert not is_tool_manifest_valid(tool)


def test_r4_tool_without_approval_fails():
    tool = _valid_read_tool(
        risk_class=RiskClass.R4,
        requires_approval=False,
        permissions_required=["filesystem.write"],
        trace_level=TraceLevel.DETAILED,
        evidence_required=False,
    )
    issues = validate_tool_manifest(tool)
    assert HIGH_RISK_REQUIRES_APPROVAL in _codes(issues)
    assert not is_tool_manifest_valid(tool)


def test_r5_tool_without_evidence_required_fails():
    tool = _valid_read_tool(
        risk_class=RiskClass.R5,
        requires_approval=True,
        permissions_required=["filesystem.write"],
        trace_level=TraceLevel.FORENSIC,
        evidence_required=False,
    )
    issues = validate_tool_manifest(tool)
    assert R5_REQUIRES_EVIDENCE in _codes(issues)
    assert not is_tool_manifest_valid(tool)


def test_external_write_requires_approval():
    tool = _valid_read_tool(
        risk_class=RiskClass.R4,
        side_effects=[SideEffectType.EXTERNAL_WRITE],
        capability_types=[CapabilityType.WRITE],
        permissions_required=["external.write"],
        requires_approval=False,
        trace_level=TraceLevel.DETAILED,
        predicted_effect=PredictedEffect(
            state_target="remote",
            expected_delta="write",
            affected_objects=["remote/object"],
            reversible=False,
            confidence_seed=ConfidenceSeed.LOW,
        ),
        reversibility=Reversibility.PARTIALLY_REVERSIBLE,
    )
    plugin = _valid_plugin(network_policy=NetworkPolicy.ALLOWLISTED)
    issues = validate_tool_manifest(tool, plugin)
    assert EXTERNAL_WRITE_REQUIRES_APPROVAL in _codes(issues)
    assert not is_tool_manifest_valid(tool, plugin)


def test_secret_access_requires_secret_data_access_and_secret_policy():
    tool = _valid_read_tool(
        risk_class=RiskClass.R4,
        side_effects=[SideEffectType.SECRET_ACCESS],
        capability_types=[CapabilityType.READ],
        permissions_required=["secrets.read"],
        requires_approval=True,
        trace_level=TraceLevel.DETAILED,
        evidence_required=True,
        data_access=[DataAccessType.LOCAL_PROJECT],
    )
    plugin = _valid_plugin(secret_policy=None)
    issues = validate_tool_manifest(tool, plugin)
    assert SECRET_ACCESS_REQUIRES_DATA_ACCESS in _codes(issues)
    assert SECRET_ACCESS_REQUIRES_SECRET_POLICY in _codes(issues)
    assert not is_tool_manifest_valid(tool, plugin)


def test_network_side_effect_requires_network_policy():
    tool = _valid_read_tool(
        risk_class=RiskClass.R3,
        side_effects=[SideEffectType.NETWORK, SideEffectType.EXTERNAL_READ],
        capability_types=[CapabilityType.RETRIEVE],
        permissions_required=["network.read"],
        requires_approval=True,
        trace_level=TraceLevel.STANDARD,
        data_access=[DataAccessType.EXTERNAL],
    )
    plugin = _valid_plugin(network_policy=None)
    issues = validate_tool_manifest(tool, plugin)
    assert NETWORK_REQUIRES_NETWORK_POLICY in _codes(issues)
    assert not is_tool_manifest_valid(tool, plugin)


def test_local_write_requires_reversibility_metadata():
    tool = _valid_read_tool(
        risk_class=RiskClass.R2,
        side_effects=[SideEffectType.LOCAL_WRITE],
        capability_types=[CapabilityType.WRITE],
        permissions_required=["filesystem.write"],
        reversibility=Reversibility.UNKNOWN,
        trace_level=TraceLevel.STANDARD,
        predicted_effect=PredictedEffect(
            state_target="file",
            expected_delta="write",
            affected_objects=["file.txt"],
            reversible=True,
            confidence_seed=ConfidenceSeed.MEDIUM,
        ),
    )
    issues = validate_tool_manifest(tool)
    assert LOCAL_WRITE_REQUIRES_REVERSIBILITY in _codes(issues)
    assert not is_tool_manifest_valid(tool)


def test_state_change_without_predicted_effect_produces_issue():
    tool = _valid_read_tool(
        risk_class=RiskClass.R2,
        side_effects=[SideEffectType.STATE_CHANGE],
        capability_types=[CapabilityType.TRANSFORM],
        permissions_required=["state.write"],
        trace_level=TraceLevel.STANDARD,
        predicted_effect=None,
    )
    issues = validate_tool_manifest(tool)
    assert STATE_CHANGE_MISSING_PREDICTED_EFFECT in _codes(issues)
    assert any(issue.severity is ValidationSeverity.WARNING for issue in issues)


def test_high_risk_state_change_without_predicted_effect_blocks_validation():
    tool = _valid_read_tool(
        risk_class=RiskClass.R4,
        side_effects=[SideEffectType.STATE_CHANGE],
        capability_types=[CapabilityType.WRITE],
        permissions_required=["state.write"],
        requires_approval=True,
        trace_level=TraceLevel.DETAILED,
        evidence_required=True,
        predicted_effect=None,
    )
    issues = validate_tool_manifest(tool)
    assert STATE_CHANGE_MISSING_PREDICTED_EFFECT in _codes(issues)
    assert any(
        issue.code == STATE_CHANGE_MISSING_PREDICTED_EFFECT
        and issue.severity is ValidationSeverity.ERROR
        for issue in issues
    )
    assert not is_tool_manifest_valid(tool)


def test_unknown_origin_high_risk_enabled_tool_produces_critical_issue():
    tool = _valid_read_tool(
        risk_class=RiskClass.R4,
        requires_approval=True,
        permissions_required=["filesystem.write"],
        trace_level=TraceLevel.DETAILED,
        evidence_required=True,
        enabled=True,
    )
    plugin = _valid_plugin(
        origin=PluginOrigin.UNKNOWN,
        trust_level=TrustLevel.LOW,
        status=PluginStatus.EXPERIMENTAL,
    )
    issues = validate_tool_manifest(tool, plugin)
    assert UNKNOWN_ORIGIN_HIGH_RISK in _codes(issues)
    assert any(
        issue.code == UNKNOWN_ORIGIN_HIGH_RISK
        and issue.severity is ValidationSeverity.CRITICAL
        for issue in issues
    )
    assert not is_tool_manifest_valid(tool, plugin)


def test_untrusted_plugin_with_r3_plus_tool_produces_blocking_issue():
    tool = _valid_read_tool(
        risk_class=RiskClass.R3,
        side_effects=[SideEffectType.EXTERNAL_READ],
        capability_types=[CapabilityType.RETRIEVE],
        permissions_required=["external.read"],
        requires_approval=True,
        trace_level=TraceLevel.STANDARD,
        data_access=[DataAccessType.EXTERNAL],
        enabled=True,
    )
    plugin = _valid_plugin(
        origin=PluginOrigin.IMPORTED,
        trust_level=TrustLevel.UNTRUSTED,
        network_policy=NetworkPolicy.ALLOWLISTED,
    )
    issues = validate_tool_manifest(tool, plugin)
    assert UNTRUSTED_PLUGIN_HIGH_RISK in _codes(issues)
    assert not is_tool_manifest_valid(tool, plugin)


def test_r6_enabled_tool_fails_validation():
    tool = _valid_read_tool(
        risk_class=RiskClass.R6,
        enabled=True,
        requires_approval=True,
        permissions_required=["blocked"],
        trace_level=TraceLevel.FORENSIC,
    )
    issues = validate_tool_manifest(tool)
    assert DISABLED_R6_REQUIRED in _codes(issues)
    assert not is_tool_manifest_valid(tool)


def test_irreversible_tool_below_r4_fails():
    tool = _valid_read_tool(
        risk_class=RiskClass.R2,
        side_effects=[SideEffectType.LOCAL_WRITE],
        capability_types=[CapabilityType.WRITE],
        permissions_required=["filesystem.write"],
        reversibility=Reversibility.IRREVERSIBLE,
        trace_level=TraceLevel.STANDARD,
        predicted_effect=PredictedEffect(
            state_target="file",
            expected_delta="delete",
            affected_objects=["file.txt"],
            reversible=False,
            confidence_seed=ConfidenceSeed.LOW,
        ),
    )
    issues = validate_tool_manifest(tool)
    assert IRREVERSIBLE_TOOL_TOO_LOW_RISK in _codes(issues)
    assert not is_tool_manifest_valid(tool)


def test_validation_summary_counts_severities_correctly():
    issues = [
        ValidationIssue("A", "info", None, ValidationSeverity.INFO),
        ValidationIssue("B", "warn", None, ValidationSeverity.WARNING),
        ValidationIssue("C", "err", None, ValidationSeverity.ERROR),
        ValidationIssue("D", "crit", None, ValidationSeverity.CRITICAL),
        ValidationIssue("E", "warn2", None, ValidationSeverity.WARNING),
    ]
    summary = validation_summary(issues)
    assert summary["total"] == 5
    assert summary["info"] == 1
    assert summary["warning"] == 2
    assert summary["error"] == 1
    assert summary["critical"] == 1
    assert summary["blocking"] is True
    assert summary["codes"] == ["A", "B", "C", "D", "E"]


@pytest.mark.parametrize(
    "severity",
    [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL],
)
def test_has_blocking_validation_issues_detects_error_and_critical(severity):
    issues = [ValidationIssue("X", "msg", None, severity)]
    assert has_blocking_validation_issues(issues) is True
    assert has_blocking_validation_issues([]) is False
    assert has_blocking_validation_issues([
        ValidationIssue("Y", "msg", None, ValidationSeverity.WARNING),
    ]) is False


def test_valid_plugin_manifest_passes_validation():
    plugin = _valid_plugin()
    issues = validate_plugin_manifest(plugin)
    assert is_plugin_manifest_valid(plugin)
    assert not has_blocking_validation_issues(issues)


def test_invalid_plugin_manifest_fails_validation():
    plugin = _valid_plugin(plugin_id="", version="")
    issues = validate_plugin_manifest(plugin)
    assert not is_plugin_manifest_valid(plugin)
    assert has_blocking_validation_issues(issues)


def test_r4_empty_permissions_produces_critical_issue():
    tool = _valid_read_tool(
        risk_class=RiskClass.R4,
        requires_approval=True,
        permissions_required=[],
        side_effects=[SideEffectType.LOCAL_WRITE],
        capability_types=[CapabilityType.WRITE],
        trace_level=TraceLevel.DETAILED,
        evidence_required=False,
        predicted_effect=PredictedEffect(
            state_target="file",
            expected_delta="write",
            affected_objects=["file.txt"],
            reversible=True,
            confidence_seed=ConfidenceSeed.MEDIUM,
        ),
    )
    issues = validate_tool_manifest(tool)
    assert HIGH_RISK_EMPTY_PERMISSIONS in _codes(issues)
