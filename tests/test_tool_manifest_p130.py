"""P1.3.0 — Tool Manifest Domain Model tests."""

from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest

from agentic_runtime.tool_manifest import (
    CapabilityStatus,
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
    RegistryEntryStatus,
    Reversibility,
    RiskClass,
    SecretPolicy,
    SideEffectType,
    ToolCapability,
    ToolCategory,
    ToolInvocationDraft,
    ToolManifest,
    ToolRegistryEntry,
    TraceLevel,
    TrustLevel,
    ValidationIssue,
    ValidationSeverity,
    is_high_risk_class,
)


def _now() -> datetime:
    return datetime(2026, 6, 20, 12, 0, 0, tzinfo=timezone.utc)


def _sample_predicted_effect() -> PredictedEffect:
    return PredictedEffect(
        state_target="workspace/src/main.py",
        expected_delta="file content updated",
        affected_objects=["workspace/src/main.py"],
        reversible=True,
        confidence_seed=ConfidenceSeed.MEDIUM,
    )


def _sample_plugin(*, origin: PluginOrigin = PluginOrigin.BUILTIN) -> PluginManifest:
    return PluginManifest(
        plugin_id="plugin.demo",
        name="Demo Plugin",
        version="0.1.0",
        description="Sample plugin manifest",
        owner="runtime",
        origin=origin,
        trust_level=TrustLevel.HIGH,
        status=PluginStatus.ACTIVE,
        created_at=_now(),
        updated_at=_now(),
        tools=["tool.demo.read"],
        required_permissions=["filesystem.read"],
        data_residency=DataResidency.LOCAL,
        network_policy=NetworkPolicy.NONE,
        filesystem_policy=FilesystemPolicy.WORKSPACE_SCOPED,
        secret_policy=SecretPolicy.FORBIDDEN,
        runtime_surfaces=["cli"],
        compatibility={"runtime": ">=0.2.0"},
        integrity_hash="abc123",
    )


def _sample_tool(*, risk_class: RiskClass = RiskClass.R2) -> ToolManifest:
    return ToolManifest(
        tool_id="tool.demo.read",
        plugin_id="plugin.demo",
        name="Read File",
        description="Read a workspace file",
        category=ToolCategory.FILESYSTEM,
        capability_types=[CapabilityType.READ],
        input_schema={"type": "object", "properties": {"path": {"type": "string"}}},
        output_schema={"type": "object", "properties": {"content": {"type": "string"}}},
        side_effects=[SideEffectType.LOCAL_READ],
        risk_class=risk_class,
        reversibility=Reversibility.REVERSIBLE,
        requires_approval=False,
        permissions_required=["filesystem.read"],
        data_access=[DataAccessType.LOCAL_PROJECT],
        execution_environment=ExecutionEnvironment.SANDBOX,
        dry_run_supported=True,
        simulation_supported=False,
        predicted_effect=_sample_predicted_effect(),
        failure_modes=["path_not_found"],
        evidence_required=True,
        trace_level=TraceLevel.STANDARD,
        timeout_policy={"seconds": 30},
        rate_limit_policy=None,
        enabled=True,
    )


def test_create_valid_plugin_manifest():
    plugin = _sample_plugin()
    assert plugin.plugin_id == "plugin.demo"
    assert plugin.tools == ["tool.demo.read"]
    assert plugin.status is PluginStatus.ACTIVE


def test_create_valid_tool_manifest():
    tool = _sample_tool()
    assert tool.tool_id == "tool.demo.read"
    assert tool.category is ToolCategory.FILESYSTEM
    assert CapabilityType.READ in tool.capability_types


def test_create_valid_predicted_effect():
    effect = _sample_predicted_effect()
    assert effect.state_target == "workspace/src/main.py"
    assert effect.reversible is True
    assert effect.confidence_seed is ConfidenceSeed.MEDIUM


def test_create_tool_capability_from_explicit_fields():
    cap = ToolCapability(
        tool_id="tool.demo.read",
        plugin_id="plugin.demo",
        canonical_name="demo.read_file",
        version="0.1.0",
        capability_types=[CapabilityType.READ],
        risk_class=RiskClass.R2,
        authority_required="filesystem.read",
        input_contract={"path": {"type": "string"}},
        output_contract={"content": {"type": "string"}},
        side_effect_profile=[SideEffectType.LOCAL_READ],
        data_access_profile=[DataAccessType.LOCAL_PROJECT],
        dry_run_capable=True,
        simulation_capable=False,
        current_status=CapabilityStatus.ACTIVE,
        trust_score_seed=TrustLevel.HIGH,
        registry_source="builtin",
    )
    assert cap.canonical_name == "demo.read_file"
    assert cap.current_status is CapabilityStatus.ACTIVE


def test_create_tool_invocation_draft_without_execution():
    draft = ToolInvocationDraft(
        draft_id="draft_001",
        tool_id="tool.demo.read",
        requested_by="operator",
        purpose="Inspect candidate patch target",
        input_payload={"path": "src/main.py"},
        expected_output="file contents",
        predicted_effect=_sample_predicted_effect(),
        risk_class=RiskClass.R2,
        reversibility=Reversibility.REVERSIBLE,
        approval_required=False,
        evidence_plan="capture stdout hash",
        created_at=_now(),
    )
    assert draft.draft_id == "draft_001"
    assert draft.input_payload["path"] == "src/main.py"
    # Draft is data only — no execute/run/invoke API exists on the model.
    assert not hasattr(draft, "execute")
    assert not hasattr(draft, "invoke")


@pytest.mark.parametrize(
    "risk_class",
    [RiskClass.R4, RiskClass.R5, RiskClass.R6],
)
def test_high_risk_tool_manifest_requires_approval(risk_class: RiskClass):
    tool = _sample_tool(risk_class=risk_class)
    assert tool.is_high_risk() is True
    assert tool.requires_human_approval() is True


def test_low_risk_tool_without_flag_does_not_require_approval():
    tool = _sample_tool(risk_class=RiskClass.R1)
    assert tool.is_high_risk() is False
    assert tool.requires_human_approval() is False


@pytest.mark.parametrize(
    "origin",
    [PluginOrigin.EXTERNAL, PluginOrigin.GENERATED, PluginOrigin.LOCAL, PluginOrigin.IMPORTED],
)
def test_external_plugin_helper_identifies_non_builtin_origin(origin: PluginOrigin):
    plugin = _sample_plugin(origin=origin)
    assert plugin.is_external() is True


def test_builtin_plugin_is_not_external():
    plugin = _sample_plugin(origin=PluginOrigin.BUILTIN)
    assert plugin.is_external() is False


def test_model_serialization_roundtrip():
    plugin = _sample_plugin(origin=PluginOrigin.EXTERNAL)
    tool = _sample_tool(risk_class=RiskClass.R5)
    effect = _sample_predicted_effect()
    issue = ValidationIssue(
        code="missing_field",
        message="name is required",
        field="name",
        severity=ValidationSeverity.ERROR,
    )
    cap = ToolCapability(
        tool_id=tool.tool_id,
        plugin_id=tool.plugin_id,
        canonical_name="demo.read_file",
        version="0.1.0",
        capability_types=tool.capability_types,
        risk_class=tool.risk_class,
        authority_required=None,
        input_contract=tool.input_schema,
        output_contract=tool.output_schema,
        side_effect_profile=tool.side_effects,
        data_access_profile=tool.data_access,
        dry_run_capable=tool.dry_run_supported,
        simulation_capable=tool.simulation_supported,
        current_status=CapabilityStatus.ACTIVE,
        trust_score_seed=TrustLevel.MEDIUM,
        registry_source="manifest",
    )
    entry = ToolRegistryEntry(
        tool_id=tool.tool_id,
        plugin_id=tool.plugin_id,
        manifest_hash="deadbeef",
        loaded_at=_now(),
        validated_at=_now(),
        status=RegistryEntryStatus.REGISTERED,
        validation_errors=[issue],
        capability=cap,
    )
    draft = ToolInvocationDraft(
        draft_id="draft_002",
        tool_id=tool.tool_id,
        requested_by="entity.card_1",
        purpose="dry-run read",
        input_payload={"path": "README.md"},
        expected_output=None,
        predicted_effect=effect,
        risk_class=tool.risk_class,
        reversibility=tool.reversibility,
        approval_required=True,
        evidence_plan=None,
        created_at=_now(),
    )

    for obj, cls in [
        (plugin, PluginManifest),
        (tool, ToolManifest),
        (effect, PredictedEffect),
        (issue, ValidationIssue),
        (cap, ToolCapability),
        (entry, ToolRegistryEntry),
        (draft, ToolInvocationDraft),
    ]:
        payload = obj.to_dict()
        json.dumps(payload)
        restored = cls.from_dict(payload)
        assert restored.to_dict() == payload


def test_validation_issue_object():
    issue = ValidationIssue(
        code="schema_mismatch",
        message="input_schema must be an object",
        field="input_schema",
        severity=ValidationSeverity.CRITICAL,
    )
    data = issue.to_dict()
    restored = ValidationIssue.from_dict(data)
    assert restored.code == "schema_mismatch"
    assert restored.severity is ValidationSeverity.CRITICAL


def test_all_enums_importable_and_stable():
    enum_cases = {
        PluginOrigin.BUILTIN: "builtin",
        TrustLevel.HIGH: "high",
        PluginStatus.ACTIVE: "active",
        ToolCategory.FILESYSTEM: "filesystem",
        CapabilityType.READ: "read",
        SideEffectType.LOCAL_READ: "local_read",
        RiskClass.R0: "R0",
        Reversibility.REVERSIBLE: "reversible",
        DataAccessType.LOCAL_PROJECT: "local_project",
        ExecutionEnvironment.SANDBOX: "sandbox",
        TraceLevel.STANDARD: "standard",
        CapabilityStatus.ACTIVE: "active",
        RegistryEntryStatus.REGISTERED: "registered",
        ConfidenceSeed.MEDIUM: "medium",
        ValidationSeverity.ERROR: "error",
        DataResidency.LOCAL: "local",
        NetworkPolicy.NONE: "none",
        FilesystemPolicy.READ_ONLY: "read_only",
        SecretPolicy.FORBIDDEN: "forbidden",
    }
    for member, expected in enum_cases.items():
        assert member.value == expected
        assert type(member).__members__[member.name] is member

    assert is_high_risk_class(RiskClass.R4) is True
    assert is_high_risk_class(RiskClass.R1) is False
