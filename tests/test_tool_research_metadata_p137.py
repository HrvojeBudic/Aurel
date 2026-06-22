"""P1.3.7 — Research-Inspired Tool Metadata tests."""

from __future__ import annotations

import inspect
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

from agentic_runtime.tool_manifest import (
    CapabilityType,
    DataAccessType,
    DataResidency,
    DriftRisk,
    ExecutionEnvironment,
    ExternalityLevel,
    FilesystemPolicy,
    NetworkPolicy,
    PluginManifest,
    PluginOrigin,
    PluginStatus,
    Reversibility,
    RiskClass,
    SecretPolicy,
    SideEffectType,
    StateDeltaContract,
    StateDeltaType,
    ToolCategory,
    ToolInvocationContext,
    ToolManifest,
    ToolRegistry,
    ToolRole,
    TraceLevel,
    TrustLevel,
    ValidationSeverity,
    build_invocation_draft_event,
    build_tool_registered_event,
    create_tool_capability_from_manifest,
    create_tool_invocation_draft,
    derive_default_simulation_profile,
    derive_default_state_delta_contract,
    derive_learning_profile,
    derive_safety_surface,
    derive_state_delta_type,
    derive_tool_roles,
    has_blocking_validation_issues,
    load_manifest_file,
    validate_tool_manifest,
    validate_tool_research_metadata,
)
from agentic_runtime.tool_manifest.validation import (
    EXTERNAL_STATE_CHANGE_MISSING_DELTA_CONTRACT,
    HIGH_RISK_ACTION_MISSING_SAFETY_SURFACE,
    R5_TOOL_MISSING_STATE_DELTA_CONTRACT,
    SECRET_TOOL_MISSING_SAFETY_SURFACE,
)

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
        input_schema={"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]},
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


def _context() -> ToolInvocationContext:
    return ToolInvocationContext(
        requested_by="operator",
        purpose="Inspect",
        request_source="test",
    )


def test_tool_role_derivation_for_read_tool():
    roles = derive_tool_roles(_tool())
    assert ToolRole.PERCEPTION in roles


def test_tool_role_derivation_for_test_tool():
    roles = derive_tool_roles(
        _tool(
            tool_id="tool.test",
            category=ToolCategory.TEST,
            capability_types=[CapabilityType.VERIFY, CapabilityType.EVALUATE],
            side_effects=[SideEffectType.PROCESS_EXECUTION],
            risk_class=RiskClass.R2,
        )
    )
    assert ToolRole.VERIFICATION in roles


def test_tool_role_derivation_for_write_tool():
    roles = derive_tool_roles(
        _tool(
            capability_types=[CapabilityType.WRITE],
            side_effects=[SideEffectType.LOCAL_WRITE, SideEffectType.STATE_CHANGE],
            risk_class=RiskClass.R3,
        )
    )
    assert ToolRole.ACTION in roles


def test_state_delta_type_read_only():
    assert derive_state_delta_type(_tool()) is StateDeltaType.READ_ONLY_OBSERVATION


def test_state_delta_type_local_write():
    tool = _tool(side_effects=[SideEffectType.LOCAL_WRITE], capability_types=[CapabilityType.WRITE])
    assert derive_state_delta_type(tool) is StateDeltaType.LOCAL_STATE_CHANGE


def test_state_delta_type_external_write():
    tool = _tool(
        side_effects=[SideEffectType.EXTERNAL_WRITE],
        capability_types=[CapabilityType.SEND],
        risk_class=RiskClass.R4,
        requires_approval=True,
    )
    assert derive_state_delta_type(tool) is StateDeltaType.EXTERNAL_STATE_CHANGE


def test_default_state_delta_contract_for_read_tool():
    contract = derive_default_state_delta_contract(_tool())
    assert contract.delta_type is StateDeltaType.READ_ONLY_OBSERVATION
    assert contract.drift_risk is DriftRisk.NONE


def test_default_state_delta_contract_for_write_tool():
    contract = derive_default_state_delta_contract(
        _tool(side_effects=[SideEffectType.LOCAL_WRITE], capability_types=[CapabilityType.WRITE])
    )
    assert contract.delta_type is StateDeltaType.LOCAL_STATE_CHANGE
    assert contract.dynamic_delta is not None


def test_default_simulation_profile_for_draft_tool():
    profile = derive_default_simulation_profile(
        _tool(
            side_effects=[SideEffectType.LOCAL_WRITE],
            capability_types=[CapabilityType.WRITE],
            reversibility=Reversibility.DRAFT_ONLY,
            dry_run_supported=True,
        )
    )
    assert profile.dry_run_supported is True
    assert profile.dry_run_strategy in {"diff_preview", "draft_only"}


def test_default_simulation_profile_for_external_write():
    profile = derive_default_simulation_profile(
        _tool(
            side_effects=[SideEffectType.EXTERNAL_WRITE],
            capability_types=[CapabilityType.SEND],
            risk_class=RiskClass.R4,
            requires_approval=True,
        )
    )
    assert profile.dry_run_strategy == "mock_external_call"
    assert profile.safe_preview_mode == "manual_review"


def test_safety_surface_for_secret_access_tool():
    surface = derive_safety_surface(
        _tool(
            side_effects=[SideEffectType.SECRET_ACCESS],
            data_access=[DataAccessType.SECRETS],
            risk_class=RiskClass.R4,
            requires_approval=True,
        )
    )
    assert "secrets" in surface.threat_surfaces
    assert surface.operator_attention_required is True


def test_safety_surface_for_external_write_tool():
    surface = derive_safety_surface(
        _tool(
            side_effects=[SideEffectType.EXTERNAL_WRITE, SideEffectType.NETWORK],
            risk_class=RiskClass.R4,
            requires_approval=True,
        )
    )
    assert "external_io" in surface.threat_surfaces
    assert surface.externality_level is ExternalityLevel.EXTERNAL_WRITE


def test_learning_profile_for_verification_tool():
    profile = derive_learning_profile(
        _tool(category=ToolCategory.EVALUATION, capability_types=[CapabilityType.EVALUATE])
    )
    assert profile.useful_for_evaluation is True


def test_high_risk_action_missing_state_delta_contract_errors():
    tool = _tool(
        tool_id="risky.write",
        capability_types=[CapabilityType.WRITE],
        side_effects=[SideEffectType.EXTERNAL_WRITE],
        risk_class=RiskClass.R5,
        requires_approval=True,
        evidence_required=True,
        trace_level=TraceLevel.FORENSIC,
    )
    issues = validate_tool_research_metadata(tool)
    codes = {issue.code for issue in issues}
    assert R5_TOOL_MISSING_STATE_DELTA_CONTRACT in codes or EXTERNAL_STATE_CHANGE_MISSING_DELTA_CONTRACT in codes
    assert any(issue.severity is ValidationSeverity.ERROR for issue in issues)


def test_external_state_change_missing_delta_contract_errors():
    tool = _tool(
        side_effects=[SideEffectType.EXTERNAL_WRITE],
        capability_types=[CapabilityType.SEND],
        risk_class=RiskClass.R3,
        requires_approval=True,
        trace_level=TraceLevel.DETAILED,
    )
    issues = validate_tool_research_metadata(tool)
    assert EXTERNAL_STATE_CHANGE_MISSING_DELTA_CONTRACT in {i.code for i in issues}


def test_r5_tool_missing_safety_surface_errors():
    tool = _tool(
        capability_types=[CapabilityType.WRITE],
        side_effects=[SideEffectType.LOCAL_WRITE],
        risk_class=RiskClass.R5,
        requires_approval=True,
        evidence_required=True,
        trace_level=TraceLevel.FORENSIC,
    )
    issues = validate_tool_research_metadata(tool)
    assert HIGH_RISK_ACTION_MISSING_SAFETY_SURFACE in {i.code for i in issues}


def test_secret_tool_missing_safety_surface_errors():
    tool = _tool(
        side_effects=[SideEffectType.SECRET_ACCESS],
        data_access=[DataAccessType.SECRETS],
        risk_class=RiskClass.R4,
        requires_approval=True,
        trace_level=TraceLevel.DETAILED,
    )
    issues = validate_tool_research_metadata(tool)
    assert SECRET_TOOL_MISSING_SAFETY_SURFACE in {i.code for i in issues}


def test_warning_only_metadata_does_not_break_low_risk_tool():
    issues = validate_tool_manifest(_tool(), _plugin())
    assert not has_blocking_validation_issues(issues)


def test_old_low_risk_manifest_remains_valid_with_derived_metadata():
    result = load_manifest_file(FIXTURES / "valid_builtin_repo.json")
    registry = ToolRegistry()
    registry.register_manifest_result(result)
    assert registry.get_tool("builtin.repo_scan") is not None


def test_loader_parses_research_metadata_fields():
    result = load_manifest_file(FIXTURES / "valid_research_metadata.json")
    assert result.status.value in {"loaded", "loaded_with_warnings"}
    tool = result.tool_manifests[0]
    assert tool.tool_roles == [ToolRole.PERCEPTION]
    assert tool.state_delta_contract is not None
    assert tool.state_delta_contract.delta_type is StateDeltaType.READ_ONLY_OBSERVATION


def test_registry_capability_preserves_tool_roles():
    tool = _tool(tool_roles=[ToolRole.PERCEPTION, ToolRole.COGNITION])
    cap = create_tool_capability_from_manifest(tool, _plugin())
    assert ToolRole.PERCEPTION in cap.tool_roles


def test_registry_capability_preserves_state_delta_contract():
    contract = StateDeltaContract(
        delta_type=StateDeltaType.LOCAL_STATE_CHANGE,
        affected_objects=["file.txt"],
        expected_delta="write",
        drift_risk=DriftRisk.LOW,
    )
    tool = _tool(
        side_effects=[SideEffectType.LOCAL_WRITE],
        capability_types=[CapabilityType.WRITE],
        state_delta_contract=contract,
    )
    cap = create_tool_capability_from_manifest(tool, _plugin())
    assert cap.state_delta_contract is not None
    assert cap.state_delta_contract.affected_objects == ["file.txt"]


def test_registry_list_by_tool_role():
    registry = ToolRegistry()
    registry.register_tool_manifest(_tool(), _plugin())
    assert registry.list_by_tool_role(ToolRole.PERCEPTION)


def test_registry_list_state_changing_tools():
    registry = ToolRegistry()
    registry.register_tool_manifest(_tool(), _plugin())
    registry.register_tool_manifest(
        _tool(
            tool_id="tool.write",
            side_effects=[SideEffectType.LOCAL_WRITE],
            capability_types=[CapabilityType.WRITE],
            risk_class=RiskClass.R2,
            reversibility=Reversibility.REVERSIBLE,
            permissions_required=["write"],
            trace_level=TraceLevel.STANDARD,
            dry_run_supported=True,
        ),
        _plugin(tools=["tool.read", "tool.write"]),
    )
    changing = registry.list_state_changing_tools()
    assert any(entry.tool_id == "tool.write" for entry in changing)
    assert all(entry.tool_id != "tool.read" for entry in changing)


def test_registry_list_simulation_ready_tools_if_implemented():
    registry = ToolRegistry()
    registry.register_tool_manifest(
        _tool(
            tool_id="tool.write",
            side_effects=[SideEffectType.LOCAL_WRITE],
            capability_types=[CapabilityType.WRITE],
            dry_run_supported=True,
            risk_class=RiskClass.R2,
            reversibility=Reversibility.REVERSIBLE,
            permissions_required=["write"],
            trace_level=TraceLevel.STANDARD,
        ),
        _plugin(tools=["tool.write"]),
    )
    assert registry.list_simulation_ready_tools()


def test_invocation_draft_preserves_state_delta_metadata():
    registry = ToolRegistry()
    registry.register_tool_manifest(_tool(), _plugin())
    result = create_tool_invocation_draft(registry, "tool.read", {"path": "x"}, _context())
    assert result.research_metadata.get("state_delta_contract") is not None


def test_invocation_draft_preserves_simulation_metadata():
    registry = ToolRegistry()
    registry.register_tool_manifest(_tool(), _plugin())
    result = create_tool_invocation_draft(registry, "tool.read", {"path": "x"}, _context())
    assert result.research_metadata.get("simulation_profile") is not None


def test_lifecycle_event_preserves_research_metadata():
    registry = ToolRegistry()
    reg = registry.register_tool_manifest(_tool(), _plugin())
    event = build_tool_registered_event(reg)
    assert "tool_roles" in event.metadata
    assert "state_delta_contract" in event.metadata
    assert "simulation_profile" in event.metadata


def test_metadata_does_not_execute_or_simulate():
    import agentic_runtime.tool_manifest.research_metadata as rm

    source = inspect.getsource(rm)
    for forbidden in ("execute_tool", "run_simulation", "dry_run(", ".invoke("):
        assert forbidden not in source
    profile = derive_default_simulation_profile(_tool())
    assert profile.dry_run_strategy != "executed"
