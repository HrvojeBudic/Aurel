"""P1.3.3 — Tool Registry Seed tests."""

from __future__ import annotations

import inspect
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

import pytest

from agentic_runtime.tool_manifest import (
    CapabilityStatus,
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
    RegistryEntryStatus,
    Reversibility,
    RiskClass,
    SecretPolicy,
    SideEffectType,
    StateDeltaContract,
    StateDeltaType,
    ToolCategory,
    ToolManifest,
    ToolRegistry,
    ToolRegistryOperationStatus,
    ToolSafetySurface,
    TraceLevel,
    TrustLevel,
    DriftRisk,
    ExternalityLevel,
    PredictedEffect,
    create_tool_capability_from_manifest,
    load_manifest_directory,
    load_manifest_file,
    parse_manifest_bundle,
)
from agentic_runtime.tool_manifest.registry import ToolRegistryResult

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "tool_manifests"


def _now() -> datetime:
    return datetime(2026, 6, 20, 12, 0, 0, tzinfo=timezone.utc)


def _valid_plugin(**overrides) -> PluginManifest:
    base = PluginManifest(
        plugin_id="plugin.core",
        name="Core Plugin",
        version="1.2.0",
        description="Core plugin",
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
        filesystem_policy=FilesystemPolicy.READ_ONLY,
        secret_policy=SecretPolicy.FORBIDDEN,
        runtime_surfaces=["runtime"],
        compatibility={},
        integrity_hash=None,
    )
    return replace(base, **overrides) if overrides else base


def _valid_tool(**overrides) -> ToolManifest:
    base = ToolManifest(
        tool_id="tool.read",
        plugin_id="plugin.core",
        name="Read File",
        description="Read a workspace file",
        category=ToolCategory.FILESYSTEM,
        capability_types=[CapabilityType.READ, CapabilityType.ANALYZE],
        input_schema={"type": "object"},
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


def _predicted_effect() -> PredictedEffect:
    return PredictedEffect(
        state_target="file",
        expected_delta="write",
        affected_objects=["file.txt"],
        reversible=True,
        confidence_seed=ConfidenceSeed.MEDIUM,
    )


def _high_risk_tool(**overrides) -> ToolManifest:
    predicted = overrides.pop("predicted_effect", _predicted_effect())
    trace_level = overrides.pop("trace_level", TraceLevel.DETAILED)
    base = {
        "side_effects": [SideEffectType.LOCAL_WRITE],
        "capability_types": [CapabilityType.WRITE],
        "reversibility": Reversibility.REVERSIBLE,
        "permissions_required": ["write"],
        "risk_class": RiskClass.R4,
        "requires_approval": True,
        "trace_level": trace_level,
        "predicted_effect": predicted,
    }
    base.update(overrides)
    return _valid_tool(**base)


def _verify_tool(**overrides) -> ToolManifest:
    return _valid_tool(
        tool_id="tool.verify",
        name="Verify Tests",
        category=ToolCategory.TEST,
        capability_types=[CapabilityType.VERIFY, CapabilityType.EVALUATE],
        side_effects=[SideEffectType.NONE],
        risk_class=RiskClass.R0,
        data_access=[DataAccessType.NONE],
        **overrides,
    )


def test_create_tool_capability_from_manifest():
    tool = _valid_tool()
    plugin = _valid_plugin()
    cap = create_tool_capability_from_manifest(tool, plugin, registry_source="/tmp/manifest.json")

    assert cap.tool_id == "tool.read"
    assert cap.plugin_id == "plugin.core"
    assert cap.canonical_name == "Read File"
    assert cap.version == "1.2.0"
    assert cap.capability_types == [CapabilityType.READ, CapabilityType.ANALYZE]
    assert cap.risk_class is RiskClass.R1
    assert cap.input_contract == tool.input_schema
    assert cap.output_contract == tool.output_schema
    assert cap.side_effect_profile == [SideEffectType.LOCAL_READ]
    assert cap.data_access_profile == [DataAccessType.LOCAL_PROJECT]
    assert cap.dry_run_capable is True
    assert cap.simulation_capable is False
    assert cap.trust_score_seed is TrustLevel.HIGH
    assert cap.registry_source == "/tmp/manifest.json"
    assert cap.current_status is CapabilityStatus.ACTIVE


def test_register_valid_manifest_result():
    result = load_manifest_file(FIXTURES / "valid_builtin_repo.json")
    registry = ToolRegistry()
    outcomes = registry.register_manifest_result(result)

    assert len(outcomes) == 1
    assert outcomes[0].status is ToolRegistryOperationStatus.REGISTERED
    assert registry.is_active("builtin.repo_scan")
    assert registry.list_active_tools()


def test_invalid_manifest_result_not_registered_as_active():
    result = load_manifest_file(FIXTURES / "invalid_high_risk_no_approval.json")
    registry = ToolRegistry()
    outcomes = registry.register_manifest_result(result)

    assert outcomes[0].status in {
        ToolRegistryOperationStatus.REJECTED,
        ToolRegistryOperationStatus.QUARANTINED,
    }
    assert registry.list_active_tools() == []
    assert not registry.is_registered("risky.repo_write")


def test_duplicate_tool_id_rejected():
    registry = ToolRegistry()
    tool = _valid_tool()
    plugin = _valid_plugin()

    first = registry.register_tool_manifest(tool, plugin)
    second = registry.register_tool_manifest(tool, plugin)

    assert first.status is ToolRegistryOperationStatus.REGISTERED
    assert second.status is ToolRegistryOperationStatus.ALREADY_EXISTS
    assert registry.get_tool("tool.read") is first.entry
    assert len(registry.list_tools()) == 1


def test_get_tool_returns_entry():
    registry = ToolRegistry()
    registry.register_tool_manifest(_valid_tool(), _valid_plugin())
    entry = registry.get_tool("tool.read")
    assert entry is not None
    assert entry.tool_id == "tool.read"
    assert entry.capability is not None


def test_list_tools_returns_registered_entries():
    registry = ToolRegistry()
    registry.register_tool_manifest(_valid_tool(), _valid_plugin())
    assert len(registry.list_tools()) == 1


def test_list_active_tools_excludes_disabled_invalid_quarantined_deprecated():
    registry = ToolRegistry()

    active = registry.register_tool_manifest(_valid_tool(tool_id="active.tool"), _valid_plugin(tools=["active.tool"]))
    disabled_tool = _valid_tool(tool_id="disabled.tool", enabled=False)
    registry.register_tool_manifest(disabled_tool, _valid_plugin(tools=["disabled.tool"]))

    quarantined = registry.register_tool_manifest(
        _valid_tool(tool_id="q.tool"),
        _valid_plugin(tools=["q.tool"], status=PluginStatus.QUARANTINED),
    )

    registry.register_tool_manifest(
        _valid_tool(tool_id="d.tool"),
        _valid_plugin(tools=["d.tool"], status=PluginStatus.DEPRECATED),
    )

    active_ids = {entry.tool_id for entry in registry.list_active_tools()}
    assert "active.tool" in active_ids
    assert "disabled.tool" not in active_ids
    assert "q.tool" not in active_ids
    assert "d.tool" not in active_ids
    assert active.status is ToolRegistryOperationStatus.REGISTERED
    assert quarantined.status is ToolRegistryOperationStatus.QUARANTINED


def test_list_by_plugin():
    registry = ToolRegistry()
    registry.register_tool_manifest(_valid_tool(), _valid_plugin())
    entries = registry.list_by_plugin("plugin.core")
    assert len(entries) == 1
    assert entries[0].plugin_id == "plugin.core"


def test_list_by_category():
    registry = ToolRegistry()
    registry.register_tool_manifest(_valid_tool(), _valid_plugin())
    assert len(registry.list_by_category(ToolCategory.FILESYSTEM)) == 1
    assert len(registry.list_by_category(ToolCategory.TEST)) == 0


def test_list_by_capability_type():
    registry = ToolRegistry()
    registry.register_tool_manifest(_valid_tool(), _valid_plugin())
    assert len(registry.list_by_capability_type(CapabilityType.READ)) == 1
    assert len(registry.list_by_capability_type(CapabilityType.WRITE)) == 0


def test_list_by_risk_class():
    registry = ToolRegistry()
    registry.register_tool_manifest(_valid_tool(risk_class=RiskClass.R1), _valid_plugin())
    assert len(registry.list_by_risk_class(RiskClass.R1)) == 1
    assert len(registry.list_by_risk_class(RiskClass.R4)) == 0


def test_disable_tool():
    registry = ToolRegistry()
    registry.register_tool_manifest(_valid_tool(), _valid_plugin())
    assert registry.is_active("tool.read")

    result = registry.disable_tool("tool.read", reason="maintenance")
    assert result.status is ToolRegistryOperationStatus.DISABLED
    assert not registry.is_active("tool.read")
    entry = registry.get_tool("tool.read")
    assert entry is not None
    assert entry.status is RegistryEntryStatus.DISABLED


def test_enable_tool():
    registry = ToolRegistry()
    registry.register_tool_manifest(_valid_tool(), _valid_plugin())
    registry.disable_tool("tool.read")
    assert not registry.is_active("tool.read")

    enabled = registry.enable_tool("tool.read")
    assert enabled.status is ToolRegistryOperationStatus.ENABLED
    assert registry.is_active("tool.read")

    r6 = registry.register_tool_manifest(
        _valid_tool(
            tool_id="r6.tool",
            risk_class=RiskClass.R6,
            enabled=False,
            requires_approval=True,
            permissions_required=["blocked"],
            trace_level=TraceLevel.FORENSIC,
        ),
        _valid_plugin(tools=["r6.tool"]),
    )
    assert r6.entry is not None
    assert not registry.is_active("r6.tool")
    assert registry.enable_tool("r6.tool").status is ToolRegistryOperationStatus.REJECTED

    quarantined = registry.register_tool_manifest(
        _valid_tool(tool_id="q2.tool"),
        _valid_plugin(tools=["q2.tool"], status=PluginStatus.QUARANTINED),
    )
    assert quarantined.status is ToolRegistryOperationStatus.QUARANTINED
    assert registry.enable_tool("q2.tool").status is ToolRegistryOperationStatus.REJECTED


def test_high_risk_helper():
    registry = ToolRegistry()
    registry.register_tool_manifest(
        _valid_tool(tool_id="low.tool", risk_class=RiskClass.R1),
        _valid_plugin(tools=["low.tool"]),
    )
    registry.register_tool_manifest(
        _high_risk_tool(
            tool_id="high.tool",
            risk_class=RiskClass.R4,
            requires_approval=True,
        ),
        _valid_plugin(tools=["high.tool"]),
    )

    assert not registry.is_high_risk("low.tool")
    assert registry.is_high_risk("high.tool")
    assert len(registry.list_high_risk_tools()) == 1


def test_requires_approval_helper():
    registry = ToolRegistry()
    registry.register_tool_manifest(
        _valid_tool(tool_id="low.tool"),
        _valid_plugin(tools=["low.tool"]),
    )
    registry.register_tool_manifest(
        _high_risk_tool(
            tool_id="high.tool",
            risk_class=RiskClass.R5,
            requires_approval=True,
            trace_level=TraceLevel.FORENSIC,
            evidence_required=True,
            state_delta_contract=StateDeltaContract(
                delta_type=StateDeltaType.LOCAL_STATE_CHANGE,
                drift_risk=DriftRisk.MEDIUM,
            ),
            safety_surface=ToolSafetySurface(
                threat_surfaces=["action"],
                externality_level=ExternalityLevel.LOCAL_ONLY,
                operator_attention_required=True,
            ),
        ),
        _valid_plugin(tools=["high.tool"]),
    )

    assert not registry.requires_approval("low.tool")
    assert registry.requires_approval("high.tool")
    assert not registry.requires_approval("missing.tool")


def test_loader_result_registers_valid_tool():
    result = load_manifest_file(FIXTURES / "valid_builtin_repo.json")
    registry = ToolRegistry()
    registry.register_manifest_result(result)
    assert registry.has_tool("builtin.repo_scan")
    assert registry.is_active("builtin.repo_scan")


def test_directory_loaded_manifests_build_registry(tmp_path):
    for name in ("valid_builtin_repo.json", "valid_builtin_model.json"):
        (tmp_path / name).write_text(
            (FIXTURES / name).read_text(encoding="utf-8"),
            encoding="utf-8",
        )

    registry = ToolRegistry()
    for result in load_manifest_directory(tmp_path):
        if result.status in {ManifestLoadStatus.LOADED, ManifestLoadStatus.LOADED_WITH_WARNINGS}:
            registry.register_manifest_result(result)

    assert registry.has_tool("builtin.repo_scan")
    assert registry.has_tool("builtin.model_status")
    assert len(registry.list_active_tools()) >= 2


def test_invalid_manifest_from_loader_is_rejected():
    result = load_manifest_file(FIXTURES / "invalid_high_risk_no_approval.json")
    registry = ToolRegistry()
    registry.register_manifest_result(result)
    assert not registry.is_active("risky.repo_write")
    assert registry.list_active_tools() == []


def test_registry_does_not_execute_tools():
    source = inspect.getsource(ToolRegistry.register_tool_manifest)
    assert "execute" not in source
    registry = ToolRegistry()
    registry.register_tool_manifest(_valid_tool(), _valid_plugin())
    assert not hasattr(registry, "invoke")
    assert not hasattr(registry, "run_tool")


def test_capability_roles_are_derived_if_implemented():
    registry = ToolRegistry()
    registry.register_tool_manifest(_valid_tool(), _valid_plugin())
    registry.register_tool_manifest(
        _verify_tool(),
        _valid_plugin(tools=["tool.read", "tool.verify"]),
    )

    read_roles = registry.get_capability_roles("tool.read")
    verify_roles = registry.get_capability_roles("tool.verify")

    assert "perception" in read_roles
    assert "verification" in verify_roles


def test_register_bundle():
    import json

    data = json.loads((FIXTURES / "valid_builtin_repo.json").read_text(encoding="utf-8"))
    bundle = parse_manifest_bundle(data, source_path="bundle.json", manifest_hash="abc")
    registry = ToolRegistry()
    outcomes = registry.register_bundle(bundle)
    assert outcomes[0].status is ToolRegistryOperationStatus.REGISTERED
    assert registry.has_tool("builtin.repo_scan")
