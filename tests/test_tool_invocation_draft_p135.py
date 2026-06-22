"""P1.3.5 — Tool Invocation Draft Seed tests."""

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
    ExecutionEnvironment,
    DataResidency,
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
    ToolCategory,
    ToolInvocationContext,
    ToolInvocationDraftResultStatus,
    ToolInvocationDraftStatus,
    ToolManifest,
    ToolRegistry,
    TraceLevel,
    TrustLevel,
    ValidationSeverity,
    create_tool_invocation_draft,
    derive_evidence_plan,
    is_tool_invocation_draft_policy_ready,
    load_manifest_file,
    validate_tool_input_payload,
)
from agentic_runtime.tool_manifest.invocation import (
    TOOL_INPUT_REQUIRED_FIELD_MISSING,
    TOOL_INPUT_TYPE_MISMATCH,
    TOOL_INPUT_UNEXPECTED_FIELD,
    derive_approval_requirement,
)
from agentic_runtime.tool_manifest.registry import create_tool_capability_from_manifest

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


def _predicted_effect() -> PredictedEffect:
    return PredictedEffect(
        state_target="file.txt",
        expected_delta="read contents",
        affected_objects=["file.txt"],
        reversible=True,
        confidence_seed=ConfidenceSeed.MEDIUM,
    )


def _high_risk_tool(**overrides) -> ToolManifest:
    predicted = overrides.pop("predicted_effect", _predicted_effect())
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
    }
    base.update(overrides)
    return _tool(**base)


def _context(**overrides) -> ToolInvocationContext:
    base = ToolInvocationContext(
        requested_by="operator",
        purpose="Inspect repository file",
        request_source="test",
    )
    return replace(base, **overrides) if overrides else base


def _register(registry: ToolRegistry, tool: ToolManifest, plugin: PluginManifest | None = None) -> None:
    plugin = plugin or _plugin(tools=[tool.tool_id])
    registry.register_tool_manifest(tool, plugin)


def test_create_low_risk_invocation_draft():
    registry = ToolRegistry()
    _register(registry, _tool())
    result = create_tool_invocation_draft(
        registry,
        "tool.read",
        {"path": "README.md"},
        _context(),
    )
    assert result.status is ToolInvocationDraftResultStatus.CREATED
    assert result.draft is not None
    assert result.approval_required is False
    assert result.draft_status is ToolInvocationDraftStatus.READY_FOR_POLICY
    assert not hasattr(result, "execute")


def test_create_high_risk_invocation_draft_requires_approval():
    registry = ToolRegistry()
    _register(registry, _high_risk_tool(), _plugin(tools=["tool.write"]))
    result = create_tool_invocation_draft(
        registry,
        "tool.write",
        {"path": "src/main.py"},
        _context(purpose="Propose write"),
    )
    assert result.status is ToolInvocationDraftResultStatus.REQUIRES_APPROVAL
    assert result.draft is not None
    assert result.approval_required is True
    assert result.draft_status is ToolInvocationDraftStatus.REQUIRES_APPROVAL


def test_tool_not_found_returns_error():
    registry = ToolRegistry()
    result = create_tool_invocation_draft(registry, "missing.tool", {}, _context())
    assert result.status is ToolInvocationDraftResultStatus.TOOL_NOT_FOUND
    assert result.draft is None


def test_disabled_tool_blocks_draft():
    registry = ToolRegistry()
    _register(registry, _tool(tool_id="disabled.tool", enabled=False))
    registry.disable_tool("disabled.tool")
    result = create_tool_invocation_draft(registry, "disabled.tool", {"path": "x"}, _context())
    assert result.draft is None
    assert result.status is ToolInvocationDraftResultStatus.TOOL_NOT_ACTIVE


def test_quarantined_tool_blocks_draft():
    registry = ToolRegistry()
    registry.register_tool_manifest(
        _tool(tool_id="q.tool"),
        _plugin(tools=["q.tool"], status=PluginStatus.QUARANTINED),
    )
    result = create_tool_invocation_draft(registry, "q.tool", {"path": "x"}, _context())
    assert result.draft is None
    assert result.status is ToolInvocationDraftResultStatus.TOOL_QUARANTINED


def test_invalid_or_deprecated_tool_blocks_draft():
    registry = ToolRegistry()
    registry.register_tool_manifest(
        _tool(tool_id="dep.tool"),
        _plugin(tools=["dep.tool"], status=PluginStatus.DEPRECATED),
    )
    result = create_tool_invocation_draft(registry, "dep.tool", {"path": "x"}, _context())
    assert result.draft is None
    assert result.status in {
        ToolInvocationDraftResultStatus.TOOL_NOT_ACTIVE,
        ToolInvocationDraftResultStatus.TOOL_QUARANTINED,
        ToolInvocationDraftResultStatus.BLOCKED,
    }


def test_invalid_input_missing_required_field():
    registry = ToolRegistry()
    _register(registry, _tool())
    result = create_tool_invocation_draft(registry, "tool.read", {}, _context())
    assert result.status is ToolInvocationDraftResultStatus.INVALID_INPUT
    assert result.draft is None
    assert TOOL_INPUT_REQUIRED_FIELD_MISSING in {i.code for i in result.issues}


def test_invalid_input_unexpected_field():
    registry = ToolRegistry()
    _register(registry, _tool())
    result = create_tool_invocation_draft(
        registry,
        "tool.read",
        {"path": "x", "extra": 1},
        _context(),
    )
    assert result.status is ToolInvocationDraftResultStatus.INVALID_INPUT
    assert TOOL_INPUT_UNEXPECTED_FIELD in {i.code for i in result.issues}


def test_invalid_input_type_mismatch():
    schema = {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}
    result = validate_tool_input_payload({"path": 123}, schema)
    assert not result.is_valid
    assert TOOL_INPUT_TYPE_MISMATCH in {i.code for i in result.issues}


def test_valid_input_with_required_fields():
    schema = {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}
    result = validate_tool_input_payload({"path": "README.md"}, schema)
    assert result.is_valid


def test_predicted_effect_copied_to_draft():
    registry = ToolRegistry()
    effect = _predicted_effect()
    _register(registry, _tool(predicted_effect=effect))
    result = create_tool_invocation_draft(registry, "tool.read", {"path": "x"}, _context())
    assert result.draft is not None
    assert result.draft.predicted_effect == effect


def test_predicted_effect_override_allowed():
    registry = ToolRegistry()
    _register(registry, _tool())
    override = _predicted_effect()
    result = create_tool_invocation_draft(
        registry,
        "tool.read",
        {"path": "x"},
        _context(),
        predicted_effect_override=override,
    )
    assert result.draft is not None
    assert result.draft.predicted_effect == override


def test_evidence_plan_derived_for_read_tool():
    registry = ToolRegistry()
    _register(registry, _tool())
    entry = registry.get_tool("tool.read")
    assert entry is not None and entry.capability is not None
    plan = derive_evidence_plan(entry.capability, {"path": "x"})
    assert plan is not None
    assert "trace reference" in plan.lower()


def test_evidence_plan_derived_for_write_or_external_tool():
    tool = _high_risk_tool(side_effects=[SideEffectType.EXTERNAL_WRITE], risk_class=RiskClass.R4)
    capability = create_tool_capability_from_manifest(
        tool,
        _plugin(tools=["tool.write"], network_policy=NetworkPolicy.ALLOWLISTED),
    )
    plan = derive_evidence_plan(capability, {"path": "remote"})
    assert plan is not None
    assert "approval" in plan.lower()


def test_policy_ready_false_for_invalid_draft():
    assert is_tool_invocation_draft_policy_ready(None) is False
    registry = ToolRegistry()
    _register(registry, _tool())
    blocked = create_tool_invocation_draft(registry, "tool.read", {}, _context())
    assert blocked.draft is None
    assert is_tool_invocation_draft_policy_ready(blocked.draft) is False


def test_policy_ready_true_for_valid_draft():
    registry = ToolRegistry()
    _register(registry, _tool())
    result = create_tool_invocation_draft(registry, "tool.read", {"path": "x"}, _context())
    assert result.draft is not None
    assert is_tool_invocation_draft_policy_ready(result.draft) is True


def test_invocation_draft_does_not_execute_tool():
    import agentic_runtime.tool_manifest.invocation as invocation_mod

    source = inspect.getsource(invocation_mod)
    for forbidden in ("execute_tool", "invoke_tool", "run_tool", ".invoke(", ".execute("):
        assert forbidden not in source
    registry = ToolRegistry()
    _register(registry, _tool())
    assert not hasattr(registry, "invoke")
    assert not hasattr(registry, "run_tool")
    result = create_tool_invocation_draft(registry, "tool.read", {"path": "x"}, _context())
    assert result.draft is not None
    assert not hasattr(result.draft, "invoke")


def test_registry_loaded_tool_can_create_draft():
    registry = ToolRegistry()
    load = load_manifest_file(FIXTURES / "valid_builtin_repo.json")
    registry.register_manifest_result(load)
    result = create_tool_invocation_draft(
        registry,
        "builtin.repo_scan",
        {"root_path": "."},
        _context(purpose="Scan repo"),
    )
    assert result.draft is not None
    assert result.status in {
        ToolInvocationDraftResultStatus.CREATED,
        ToolInvocationDraftResultStatus.REQUIRES_APPROVAL,
    }


def test_loader_registry_invocation_path():
    load = load_manifest_file(FIXTURES / "valid_builtin_repo.json")
    registry = ToolRegistry()
    registry.register_manifest_result(load)
    result = create_tool_invocation_draft(
        registry,
        "builtin.repo_scan",
        {"root_path": "/tmp"},
        ToolInvocationContext(
            requested_by="agent.card_1",
            purpose="Repository inspection",
            request_source="loader_test",
        ),
    )
    assert result.draft is not None
    assert result.draft.tool_id == "builtin.repo_scan"


def test_warning_only_registered_tool_can_create_draft_with_warnings():
    plugin = _plugin(origin=PluginOrigin.EXTERNAL, trust_level=TrustLevel.HIGH, tools=["warn.tool"])
    registry = ToolRegistry()
    registry.register_tool_manifest(_tool(tool_id="warn.tool"), plugin)
    result = create_tool_invocation_draft(registry, "warn.tool", {"path": "x"}, _context())
    assert result.draft is not None
    assert any(issue.severity is ValidationSeverity.WARNING for issue in result.issues)


def test_r6_or_quarantined_tool_cannot_create_draft():
    registry = ToolRegistry()
    registry.register_tool_manifest(
        _tool(
            tool_id="r6.tool",
            risk_class=RiskClass.R6,
            enabled=False,
            requires_approval=True,
            permissions_required=["blocked"],
            trace_level=TraceLevel.FORENSIC,
        ),
        _plugin(tools=["r6.tool"]),
    )
    assert create_tool_invocation_draft(registry, "r6.tool", {"path": "x"}, _context()).draft is None

    registry.register_tool_manifest(
        _tool(tool_id="q2.tool"),
        _plugin(tools=["q2.tool"], status=PluginStatus.QUARANTINED),
    )
    assert create_tool_invocation_draft(registry, "q2.tool", {"path": "x"}, _context()).draft is None


def test_derive_approval_requirement_high_risk():
    registry = ToolRegistry()
    _register(registry, _high_risk_tool(), _plugin(tools=["tool.write"]))
    cap = registry.get_tool("tool.write").capability  # type: ignore[union-attr]
    assert derive_approval_requirement(cap, reversibility=Reversibility.REVERSIBLE) is True
