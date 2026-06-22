"""P1.3.9 — Tool Manifest Layer Seal tests.

End-to-end seal proving the declarative manifest layer can:
declare → load → validate → quarantine → register → draft → trace
without becoming an execution layer.
"""

from __future__ import annotations

import importlib
import inspect
import json
import pkgutil
import subprocess
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest

from agentic_runtime.core_types import CommandEnvelope, ObservationEnvelope
from agentic_runtime.prompt_system import PromptRegistry, PromptValidationError
from agentic_runtime.sandbox import UnsafeLocalSandbox
from agentic_runtime.sandbox_policy import SandboxPolicy, SandboxProfileName, create_profiled_sandbox
from agentic_runtime.tools import ToolBus, ToolRuntime
from agentic_runtime.yaml_minimal import YamlParseError, load_yaml
from agentic_runtime.tool_manifest import (
    CapabilityStatus,
    ManifestLoadStatus,
    PluginManifest,
    PluginOrigin,
    PluginStatus,
    QuarantineStore,
    Reversibility,
    SideEffectType,
    ToolManifest,
    QuarantineSubjectType,
    RegistryEntryStatus,
    RiskClass,
    ToolCategory,
    ToolRole,
    ToolCapability,
    ToolInvocationContext,
    ToolInvocationDraft,
    ToolInvocationDraftResultStatus,
    ToolInvocationDraftStatus,
    ToolLifecycleEvent,
    ToolLifecycleEventRecorder,
    ToolLifecycleEventType,
    ToolRegistry,
    ToolRegistryEntry,
    ToolRegistryOperationStatus,
    TraceLevel,
    ValidationSeverity,
    build_invocation_draft_event,
    build_manifest_loaded_event,
    build_quarantine_record_created_event,
    build_registry_built_event,
    build_tool_registered_event,
    compute_manifest_hash,
    create_quarantine_record,
    create_tool_invocation_draft,
    decide_quarantine_for_manifest_result,
    get_builtin_manifest_directory,
    is_tool_invocation_draft_policy_ready,
    load_builtin_tool_manifests,
    load_manifest_directory,
    load_manifest_file,
)
from agentic_runtime.tool_manifest.capability import ToolRegistryEntry as ManifestRegistryEntry
from agentic_runtime.tool_manifest.research_metadata import research_metadata_from_capability

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "tool_manifests"
BUILTIN_DIR = get_builtin_manifest_directory()

EXPECTED_MANIFEST_FILES = frozenset({
    "builtin.repo.json",
    "builtin.filesystem.json",
    "builtin.test.json",
    "builtin.evidence.json",
    "builtin.memory.json",
    "builtin.model.json",
})

EXPECTED_TOOL_IDS = frozenset({
    "builtin.repo_scan",
    "builtin.read_project_file",
    "builtin.write_file_draft",
    "builtin.run_tests_draft",
    "builtin.create_evidence_record",
    "builtin.create_memory_candidate",
    "builtin.model_complete_structured",
})

_LOADABLE_STATUSES = frozenset({
    ManifestLoadStatus.LOADED,
    ManifestLoadStatus.LOADED_WITH_WARNINGS,
})

_FORBIDDEN_SOURCE_TOKENS = (
    "runtime.submit",
    "ToolRuntime",
    "CommandEnvelope",
    "subprocess",
    "execute_tool",
    ".invoke(",
    "run_tool",
)

_TOOL_MANIFEST_PACKAGE = "agentic_runtime.tool_manifest"


def _now() -> datetime:
    return datetime(2026, 6, 21, 12, 0, 0, tzinfo=timezone.utc)


def _context(**overrides) -> ToolInvocationContext:
    base = ToolInvocationContext(
        requested_by="operator",
        purpose="P1.3.9 seal test",
        request_source="test",
    )
    if overrides:
        return replace(base, **overrides)
    return base


def _register_all_builtins(registry: ToolRegistry) -> list:
    outcomes = []
    for result in load_builtin_tool_manifests():
        if result.status in _LOADABLE_STATUSES:
            outcomes.extend(registry.register_manifest_result(result))
    return outcomes


def _all_builtin_tools():
    tools = []
    for result in load_builtin_tool_manifests():
        if result.status in _LOADABLE_STATUSES:
            tools.extend(result.tool_manifests)
    return tools


def _iter_tool_manifest_modules():
    package = importlib.import_module(_TOOL_MANIFEST_PACKAGE)
    for module_info in pkgutil.walk_packages(package.__path__, package.__name__ + "."):
        if module_info.name.endswith(".manifests"):
            continue
        yield importlib.import_module(module_info.name)


def _scan_tool_manifest_modules_for_forbidden_tokens() -> list[str]:
    violations: list[str] = []
    for module in _iter_tool_manifest_modules():
        source = inspect.getsource(module)
        for token in _FORBIDDEN_SOURCE_TOKENS:
            if token in source:
                violations.append(f"{module.__name__} contains forbidden token {token!r}")
    return violations


def _run_full_builtin_lifecycle(
    recorder: ToolLifecycleEventRecorder,
    registry: ToolRegistry,
) -> dict[str, Any]:
    """Run load → register → draft for built-ins; return summary for assertions."""
    load_results = load_builtin_tool_manifests()
    for load in load_results:
        if load.status in _LOADABLE_STATUSES:
            recorder.record(build_manifest_loaded_event(load))

    reg_outcomes = _register_all_builtins(registry)
    for reg_result in reg_outcomes:
        if reg_result.status is ToolRegistryOperationStatus.REGISTERED:
            recorder.record(build_tool_registered_event(reg_result))
    recorder.record(build_registry_built_event(reg_outcomes))

    safe_draft = create_tool_invocation_draft(
        registry,
        "builtin.read_project_file",
        {"path": "README.md"},
        _context(purpose="Safe read draft"),
    )
    recorder.record(build_invocation_draft_event(safe_draft))

    high_risk_draft = create_tool_invocation_draft(
        registry,
        "builtin.run_tests_draft",
        {"test_target": "pytest tests/"},
        _context(purpose="High-risk draft"),
    )
    recorder.record(build_invocation_draft_event(high_risk_draft))

    return {
        "load_results": load_results,
        "reg_outcomes": reg_outcomes,
        "safe_draft": safe_draft,
        "high_risk_draft": high_risk_draft,
    }


def _quarantine_plugin(**overrides) -> PluginManifest:
    from agentic_runtime.tool_manifest import (
        CapabilityType,
        DataAccessType,
        DataResidency,
        ExecutionEnvironment,
        FilesystemPolicy,
        NetworkPolicy,
        PluginManifest,
        SecretPolicy,
        TrustLevel,
    )

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


def _quarantine_tool(**overrides) -> ToolManifest:
    from agentic_runtime.tool_manifest import (
        CapabilityType,
        DataAccessType,
        ExecutionEnvironment,
    )

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


@pytest.fixture
def execution_guard(monkeypatch):
    """Track calls to execution surfaces; P1.3 lifecycle must not invoke them."""
    calls = {
        "submit": 0,
        "dispatch": 0,
        "command_envelope_make": 0,
        "subprocess_run": 0,
    }

    from agentic_runtime.runtime import AgenticRuntime

    def track_submit(self, *args, **kwargs):
        calls["submit"] += 1
        raise AssertionError("AgenticRuntime.submit must not be called from P1.3")

    def track_dispatch(self, *args, **kwargs):
        calls["dispatch"] += 1
        raise AssertionError("ToolRuntime.dispatch must not be called from P1.3")

    def track_command_envelope_make(*args, **kwargs):
        calls["command_envelope_make"] += 1
        raise AssertionError("CommandEnvelope.make must not be called from P1.3")

    def track_subprocess_run(*args, **kwargs):
        calls["subprocess_run"] += 1
        raise AssertionError("subprocess.run must not be called from P1.3")

    monkeypatch.setattr(AgenticRuntime, "submit", track_submit)
    monkeypatch.setattr(ToolRuntime, "dispatch", track_dispatch)
    monkeypatch.setattr(CommandEnvelope, "make", staticmethod(track_command_envelope_make))
    monkeypatch.setattr(subprocess, "run", track_subprocess_run)
    return calls


# --------------------------------------------------------------------------- #
# 1. End-to-end lifecycle seal
# --------------------------------------------------------------------------- #


def test_p13_full_lifecycle_builtin_to_event_without_execution(execution_guard):
    recorder = ToolLifecycleEventRecorder()
    registry = ToolRegistry()
    summary = _run_full_builtin_lifecycle(recorder, registry)

    for load in summary["load_results"]:
        assert load.status in _LOADABLE_STATUSES

    registered = [
        outcome for outcome in summary["reg_outcomes"]
        if outcome.status is ToolRegistryOperationStatus.REGISTERED
    ]
    assert len(registered) == len(EXPECTED_TOOL_IDS)

    safe = summary["safe_draft"]
    assert safe.status is ToolInvocationDraftResultStatus.CREATED
    assert safe.draft is not None
    assert safe.draft_status in {
        ToolInvocationDraftStatus.DRAFT,
        ToolInvocationDraftStatus.READY_FOR_POLICY,
    }

    high_risk = summary["high_risk_draft"]
    assert high_risk.status is ToolInvocationDraftResultStatus.REQUIRES_APPROVAL
    assert high_risk.approval_required is True

    events = recorder.list_events()
    assert len(events) >= 10
    assert recorder.list_by_type(ToolLifecycleEventType.MANIFEST_LOADED)
    assert recorder.list_by_type(ToolLifecycleEventType.TOOL_CAPABILITY_REGISTERED)
    assert recorder.list_by_type(ToolLifecycleEventType.INVOCATION_DRAFT_CREATED)

    assert execution_guard["submit"] == 0
    assert execution_guard["dispatch"] == 0
    assert execution_guard["command_envelope_make"] == 0
    assert execution_guard["subprocess_run"] == 0


# --------------------------------------------------------------------------- #
# 2. Built-in manifest integrity
# --------------------------------------------------------------------------- #


def test_all_builtin_manifests_exist():
    assert BUILTIN_DIR.is_dir()
    present = {path.name for path in BUILTIN_DIR.glob("*.json")}
    assert EXPECTED_MANIFEST_FILES <= present


def test_all_builtin_manifests_are_valid_json():
    for filename in sorted(EXPECTED_MANIFEST_FILES):
        data = json.loads((BUILTIN_DIR / filename).read_text(encoding="utf-8"))
        assert isinstance(data, dict)
        assert "plugin" in data
        assert "tools" in data


def test_all_builtin_tools_have_unique_tool_ids():
    seen: set[str] = set()
    for tool in _all_builtin_tools():
        assert tool.tool_id not in seen, f"duplicate tool_id: {tool.tool_id}"
        seen.add(tool.tool_id)
    assert seen == EXPECTED_TOOL_IDS


def test_all_builtin_tools_have_required_contract_fields():
    for tool in _all_builtin_tools():
        assert tool.tool_id
        assert tool.input_schema
        assert tool.output_schema is not None
        assert tool.permissions_required is not None
        assert tool.risk_class is not None


def test_all_builtin_tools_have_risk_class():
    for tool in _all_builtin_tools():
        assert tool.risk_class.value.startswith("R")


def test_all_builtin_tools_have_trace_level():
    for tool in _all_builtin_tools():
        assert tool.trace_level is not None
        assert isinstance(tool.trace_level, TraceLevel)


def test_all_builtin_tools_have_tool_roles():
    for tool in _all_builtin_tools():
        assert tool.tool_roles


def test_state_changing_builtin_tools_have_state_delta_contract():
    read_only = {"none", "local_read", "external_read"}
    for tool in _all_builtin_tools():
        effects = {effect.value for effect in tool.side_effects}
        if effects - read_only or tool.risk_class.value >= "R3":
            assert tool.state_delta_contract is not None, tool.tool_id


def test_high_risk_builtin_tools_have_safety_surface():
    for tool in _all_builtin_tools():
        if tool.risk_class.value >= "R3":
            assert tool.safety_surface is not None, tool.tool_id


def test_builtin_manifest_registration_does_not_register_executable_handlers():
    manifest_registry = ToolRegistry()
    _register_all_builtins(manifest_registry)

    exec_registry = ToolBus(UnsafeLocalSandbox(root=str(REPO_ROOT)))

    for tool_id in EXPECTED_TOOL_IDS:
        entry = manifest_registry.get_tool(tool_id)
        assert entry is not None
        assert isinstance(entry, ManifestRegistryEntry)
        assert isinstance(entry.capability, ToolCapability)
        assert exec_registry.get(tool_id) is None


# --------------------------------------------------------------------------- #
# 3. Loader + validation seal
# --------------------------------------------------------------------------- #


def test_builtin_manifest_directory_loads_deterministically():
    first = load_manifest_directory(BUILTIN_DIR)
    second = load_manifest_directory(BUILTIN_DIR)
    assert len(first) == len(second) == len(EXPECTED_MANIFEST_FILES)

    first_hashes = sorted(result.manifest_hash for result in first if result.manifest_hash)
    second_hashes = sorted(result.manifest_hash for result in second if result.manifest_hash)
    assert first_hashes == second_hashes

    first_tool_ids = sorted(
        tool.tool_id
        for result in first
        if result.status in _LOADABLE_STATUSES
        for tool in result.tool_manifests
    )
    second_tool_ids = sorted(
        tool.tool_id
        for result in second
        if result.status in _LOADABLE_STATUSES
        for tool in result.tool_manifests
    )
    assert first_tool_ids == second_tool_ids


def test_builtin_manifests_validate_without_unexpected_blockers():
    for result in load_builtin_tool_manifests():
        assert result.status in _LOADABLE_STATUSES
        blocking = [
            issue for issue in result.validation_issues
            if issue.severity in {ValidationSeverity.ERROR, ValidationSeverity.CRITICAL}
        ]
        assert not blocking, f"{result.source_path} has blockers: {blocking}"


def test_bad_manifest_does_not_break_directory_load():
    mixed_dir = FIXTURES
    results = load_manifest_directory(mixed_dir)
    assert len(results) >= 2
    statuses = {result.status for result in results}
    assert ManifestLoadStatus.INVALID in statuses or ManifestLoadStatus.PARSE_ERROR in statuses
    assert ManifestLoadStatus.LOADED in statuses or ManifestLoadStatus.LOADED_WITH_WARNINGS in statuses


def test_manifest_hash_is_stable():
    path = BUILTIN_DIR / "builtin.repo.json"
    content = path.read_bytes()
    assert compute_manifest_hash(content) == compute_manifest_hash(content)


def test_manifest_parse_errors_are_structured():
    malformed = load_manifest_file(FIXTURES / "malformed_manifest.json")
    assert malformed.status is ManifestLoadStatus.PARSE_ERROR
    assert malformed.source_path is not None
    assert any(issue.code for issue in malformed.validation_issues)

    unsupported = load_manifest_file(FIXTURES / "unsupported_manifest.txt")
    assert unsupported.status is ManifestLoadStatus.UNSUPPORTED_FORMAT
    assert unsupported.validation_issues or unsupported.parse_error

    bad_enum = load_manifest_file(FIXTURES / "invalid_bad_enum.json")
    assert bad_enum.status in {ManifestLoadStatus.INVALID, ManifestLoadStatus.PARSE_ERROR}
    assert bad_enum.validation_issues or bad_enum.parse_error


def test_warning_only_manifest_preserves_warnings():
    from agentic_runtime.tool_manifest import TrustLevel, validate_tool_manifest

    plugin = _quarantine_plugin(origin=PluginOrigin.EXTERNAL, trust_level=TrustLevel.HIGH)
    tool = _quarantine_tool(tool_id="warn.tool")
    plugin = replace(plugin, tools=["warn.tool"])
    issues = validate_tool_manifest(tool, plugin)
    assert any(issue.severity is ValidationSeverity.WARNING for issue in issues)

    registry = ToolRegistry()
    result = registry.register_tool_manifest(tool, plugin)
    assert result.status is ToolRegistryOperationStatus.REGISTERED
    assert any(issue.severity is ValidationSeverity.WARNING for issue in result.issues)


def test_yaml_list_of_maps_does_not_truncate():
    text = (
        "items:\n"
        "  - name: first\n"
        "    value: 1\n"
        "  - name: second\n"
        "    value: 2\n"
    )
    parsed = load_yaml(text)
    assert parsed["items"] == [{"name": "first", "value": 1}, {"name": "second", "value": 2}]


def test_yaml_unsupported_shape_fails_loudly():
    with pytest.raises(YamlParseError, match="unsupported nested scalar list item"):
        load_yaml(
            "items:\n"
            "  - first\n"
            "    description: one\n"
        )


# --------------------------------------------------------------------------- #
# 4. Registry seal + declarative boundary
# --------------------------------------------------------------------------- #


def test_valid_builtin_tools_register():
    registry = ToolRegistry()
    outcomes = _register_all_builtins(registry)
    registered = [
        outcome for outcome in outcomes
        if outcome.status is ToolRegistryOperationStatus.REGISTERED
    ]
    assert len(registered) == len(EXPECTED_TOOL_IDS)


def test_invalid_tools_do_not_become_active():
    registry = ToolRegistry()
    _register_all_builtins(registry)
    invalid = load_manifest_file(FIXTURES / "invalid_high_risk_no_approval.json")
    registry.register_manifest_result(invalid)
    active_ids = {entry.capability.tool_id for entry in registry.list_active_tools()}
    assert "risky.repo_write" not in active_ids
    assert EXPECTED_TOOL_IDS <= active_ids


def test_duplicate_tool_ids_are_rejected():
    registry = ToolRegistry()
    tool = next(t for t in _all_builtin_tools() if t.tool_id == "builtin.read_project_file")
    plugin = next(
        r.plugin_manifest
        for r in load_builtin_tool_manifests()
        if r.plugin_manifest and r.plugin_manifest.plugin_id == "builtin.filesystem"
    )
    first = registry.register_tool_manifest(tool, plugin)
    second = registry.register_tool_manifest(tool, plugin)
    assert first.status is ToolRegistryOperationStatus.REGISTERED
    assert second.status is ToolRegistryOperationStatus.ALREADY_EXISTS


def test_quarantined_tools_are_not_active():
    registry = ToolRegistry()
    result = registry.register_tool_manifest(
        _quarantine_tool(tool_id="q.tool"),
        _quarantine_plugin(tools=["q.tool"], status=PluginStatus.QUARANTINED),
    )
    assert result.status is ToolRegistryOperationStatus.QUARANTINED
    assert registry.has_tool("q.tool")
    assert not registry.is_active("q.tool")


def test_registry_visibility_does_not_grant_authority(execution_guard):
    registry = ToolRegistry()
    _register_all_builtins(registry)
    active = registry.list_active_tools()
    assert active

    draft_result = create_tool_invocation_draft(
        registry,
        "builtin.read_project_file",
        {"path": "README.md"},
        _context(),
    )
    assert draft_result.draft is not None
    assert isinstance(draft_result.draft, ToolInvocationDraft)
    assert not isinstance(draft_result.draft, CommandEnvelope)
    assert execution_guard["command_envelope_make"] == 0


def test_registry_queries_by_role_risk_category_work():
    registry = ToolRegistry()
    _register_all_builtins(registry)
    assert registry.list_by_risk_class(RiskClass.R1)
    assert registry.list_by_category(ToolCategory.FILESYSTEM)
    assert registry.list_by_category(ToolCategory.CODE)
    assert registry.list_by_tool_role(ToolRole.PERCEPTION)


def test_tool_manifest_registry_is_declarative_not_executable_registry(execution_guard):
    assert ToolRegistry is not ToolBus

    registry = ToolRegistry()
    _run_full_builtin_lifecycle(ToolLifecycleEventRecorder(), registry)

    for forbidden_method in ("submit", "dispatch", "invoke", "execute", "run_tool"):
        assert not hasattr(registry, forbidden_method)

    assert execution_guard["submit"] == 0
    assert execution_guard["dispatch"] == 0
    assert execution_guard["command_envelope_make"] == 0


# --------------------------------------------------------------------------- #
# 5. Quarantine seal
# --------------------------------------------------------------------------- #


def test_r6_enabled_tool_is_quarantined_or_rejected():
    registry = ToolRegistry()
    r6_tool = next(
        tool for tool in _all_builtin_tools() if tool.tool_id == "builtin.read_project_file"
    )
    r6_tool = replace(
        r6_tool,
        tool_id="seal.r6.tool",
        risk_class=RiskClass.R6,
        enabled=True,
        requires_approval=True,
        permissions_required=["blocked"],
        trace_level=TraceLevel.FORENSIC,
    )
    plugin = replace(
        load_builtin_tool_manifests()[0].plugin_manifest,
        plugin_id="seal.r6.plugin",
        tools=["seal.r6.tool"],
    )
    result = registry.register_tool_manifest(r6_tool, plugin)
    assert result.status in {
        ToolRegistryOperationStatus.REJECTED,
        ToolRegistryOperationStatus.QUARANTINED,
    }


def test_unknown_origin_high_risk_tool_is_quarantined():
    result = load_manifest_file(FIXTURES / "invalid_high_risk_no_approval.json")
    decision = decide_quarantine_for_manifest_result(result)
    assert decision.should_quarantine or decision.should_reject


def test_untrusted_plugin_high_risk_tool_is_quarantined():
    from agentic_runtime.tool_manifest import TrustLevel, decide_quarantine_for_plugin, validate_tool_manifest

    plugin = load_builtin_tool_manifests()[0].plugin_manifest
    plugin = replace(
        plugin,
        plugin_id="seal.untrusted",
        origin=PluginOrigin.EXPERIMENTAL,
        trust_level=TrustLevel.LOW,
        tools=["builtin.repo_scan"],
    )
    tool = next(t for t in _all_builtin_tools() if t.tool_id == "builtin.repo_scan")
    tool = replace(tool, risk_class=RiskClass.R4, requires_approval=True, permissions_required=["shell"])
    issues = validate_tool_manifest(tool, plugin)
    decision = decide_quarantine_for_plugin(plugin, issues)
    assert decision.should_quarantine or any(
        issue.severity in {ValidationSeverity.ERROR, ValidationSeverity.CRITICAL}
        for issue in issues
    )


def test_quarantine_record_preserves_reasons_and_issues():
    result = load_manifest_file(FIXTURES / "invalid_high_risk_no_approval.json")
    decision = decide_quarantine_for_manifest_result(result)
    record = create_quarantine_record(
        QuarantineSubjectType.TOOL,
        result.tool_manifests[0].tool_id if result.tool_manifests else "unknown",
        result.validation_issues,
        decision,
        plugin_id=result.plugin_manifest.plugin_id if result.plugin_manifest else "unknown",
        tool_id=result.tool_manifests[0].tool_id if result.tool_manifests else None,
        source_path=result.source_path,
    )
    assert record.reasons
    assert record.validation_issues
    assert record.source_path is not None


def test_quarantine_isolation_does_not_delete_manifest_data():
    result = load_manifest_file(FIXTURES / "invalid_high_risk_no_approval.json")
    original_tool_count = len(result.tool_manifests)
    original_plugin = result.plugin_manifest

    decision = decide_quarantine_for_manifest_result(result)
    record = create_quarantine_record(
        QuarantineSubjectType.PLUGIN,
        original_plugin.plugin_id if original_plugin else "unknown",
        result.validation_issues,
        decision,
        plugin_id=original_plugin.plugin_id if original_plugin else "unknown",
        source_path=result.source_path,
    )
    store = QuarantineStore()
    store.add_record(record)

    assert len(result.tool_manifests) == original_tool_count
    assert result.plugin_manifest is original_plugin
    assert store.get_record(record.record_id) is not None
    assert store.get_record(record.record_id).validation_issues


# --------------------------------------------------------------------------- #
# 6. Invocation draft seal
# --------------------------------------------------------------------------- #


def test_safe_builtin_tool_can_create_invocation_draft():
    registry = ToolRegistry()
    _register_all_builtins(registry)
    result = create_tool_invocation_draft(
        registry,
        "builtin.repo_scan",
        {"root_path": "."},
        _context(),
    )
    assert result.status is ToolInvocationDraftResultStatus.CREATED
    assert result.draft is not None


def test_high_risk_builtin_tool_requires_approval_in_draft():
    registry = ToolRegistry()
    _register_all_builtins(registry)
    result = create_tool_invocation_draft(
        registry,
        "builtin.run_tests_draft",
        {"test_target": "pytest tests/"},
        _context(),
    )
    assert result.status is ToolInvocationDraftResultStatus.REQUIRES_APPROVAL
    assert result.approval_required is True


def test_invalid_input_blocks_draft():
    registry = ToolRegistry()
    _register_all_builtins(registry)
    result = create_tool_invocation_draft(
        registry,
        "builtin.read_project_file",
        {},
        _context(),
    )
    assert result.status is ToolInvocationDraftResultStatus.INVALID_INPUT


def test_quarantined_tool_blocks_draft():
    registry = ToolRegistry()
    reg_result = registry.register_tool_manifest(
        _quarantine_tool(tool_id="q.tool"),
        _quarantine_plugin(tools=["q.tool"], status=PluginStatus.QUARANTINED),
    )
    assert reg_result.status is ToolRegistryOperationStatus.QUARANTINED
    result = create_tool_invocation_draft(
        registry,
        "q.tool",
        {"path": "README.md"},
        _context(),
    )
    assert result.status in {
        ToolInvocationDraftResultStatus.TOOL_NOT_ACTIVE,
        ToolInvocationDraftResultStatus.TOOL_QUARANTINED,
        ToolInvocationDraftResultStatus.BLOCKED,
    }


def test_draft_contains_risk_reversibility_evidence_plan():
    registry = ToolRegistry()
    _register_all_builtins(registry)
    result = create_tool_invocation_draft(
        registry,
        "builtin.run_tests_draft",
        {"test_target": "pytest tests/"},
        _context(),
    )
    assert result.draft is not None
    assert result.draft.risk_class is not None
    assert result.draft.reversibility is not None
    assert result.draft.evidence_plan is not None


def test_draft_preserves_predicted_effect_and_state_delta_metadata():
    registry = ToolRegistry()
    _register_all_builtins(registry)
    result = create_tool_invocation_draft(
        registry,
        "builtin.write_file_draft",
        {"path": "example.txt", "content": "draft"},
        _context(),
    )
    assert result.draft is not None
    metadata = result.research_metadata
    assert metadata["state_delta_contract"]["delta_type"] == "local_state_change"
    assert metadata["simulation_profile"]["simulation_strategy"] == "draft_only"
    assert result.draft.predicted_effect is not None


def test_invocation_draft_is_not_execution(execution_guard):
    registry = ToolRegistry()
    _register_all_builtins(registry)
    result = create_tool_invocation_draft(
        registry,
        "builtin.read_project_file",
        {"path": "README.md"},
        _context(),
    )
    assert result.draft is not None
    assert not hasattr(result.draft, "invoke")
    assert not hasattr(result.draft, "execute")
    assert execution_guard["dispatch"] == 0


def test_invocation_draft_does_not_become_command_envelope(execution_guard):
    registry = ToolRegistry()
    _register_all_builtins(registry)
    result = create_tool_invocation_draft(
        registry,
        "builtin.read_project_file",
        {"path": "README.md"},
        _context(),
    )
    draft = result.draft
    assert draft is not None
    assert type(draft) is ToolInvocationDraft
    assert not isinstance(draft, CommandEnvelope)
    assert execution_guard["command_envelope_make"] == 0
    assert execution_guard["submit"] == 0


# --------------------------------------------------------------------------- #
# 7. Lifecycle event seal
# --------------------------------------------------------------------------- #


def test_manifest_load_event_created():
    result = load_manifest_file(BUILTIN_DIR / "builtin.repo.json")
    event = build_manifest_loaded_event(result)
    assert event.event_type is ToolLifecycleEventType.MANIFEST_LOADED


def test_registry_event_created():
    registry = ToolRegistry()
    outcomes = _register_all_builtins(registry)
    event = build_tool_registered_event(outcomes[0])
    assert event.event_type is ToolLifecycleEventType.TOOL_CAPABILITY_REGISTERED


def test_quarantine_event_created():
    result = load_manifest_file(FIXTURES / "invalid_high_risk_no_approval.json")
    decision = decide_quarantine_for_manifest_result(result)
    record = create_quarantine_record(
        QuarantineSubjectType.PLUGIN,
        "test.plugin",
        result.validation_issues,
        decision,
        plugin_id="test.plugin",
    )
    event = build_quarantine_record_created_event(record)
    assert event.event_type is ToolLifecycleEventType.QUARANTINE_RECORD_CREATED


def test_invocation_draft_event_created():
    registry = ToolRegistry()
    _register_all_builtins(registry)
    draft_result = create_tool_invocation_draft(
        registry,
        "builtin.repo_scan",
        {"root_path": "."},
        _context(),
    )
    event = build_invocation_draft_event(draft_result)
    assert event.event_type is ToolLifecycleEventType.INVOCATION_DRAFT_CREATED


def test_event_recorder_tracks_lifecycle():
    recorder = ToolLifecycleEventRecorder()
    registry = ToolRegistry()
    _run_full_builtin_lifecycle(recorder, registry)
    assert len(recorder.list_events()) >= 10
    assert recorder.list_by_tool("builtin.read_project_file")


def test_trace_event_is_not_verified_evidence():
    registry = ToolRegistry()
    _register_all_builtins(registry)
    draft_result = create_tool_invocation_draft(
        registry,
        "builtin.read_project_file",
        {"path": "README.md"},
        _context(),
    )
    event = build_invocation_draft_event(draft_result)
    assert isinstance(event, ToolLifecycleEvent)
    assert not hasattr(event, "verified")
    assert not hasattr(event, "evidence_hash")
    assert event.metadata.get("verified") is None


def test_lifecycle_trace_without_execution(execution_guard):
    recorder = ToolLifecycleEventRecorder()
    registry = ToolRegistry()
    _run_full_builtin_lifecycle(recorder, registry)
    assert len(recorder.list_events()) >= 10
    assert execution_guard["submit"] == 0
    assert execution_guard["dispatch"] == 0


# --------------------------------------------------------------------------- #
# 8. Central no-execution invariant
# --------------------------------------------------------------------------- #


def test_p13_manifest_layer_has_no_execution_power(execution_guard):
    violations = _scan_tool_manifest_modules_for_forbidden_tokens()
    assert not violations, "\n".join(violations)

    recorder = ToolLifecycleEventRecorder()
    registry = ToolRegistry()
    _run_full_builtin_lifecycle(recorder, registry)

    invalid = load_manifest_file(FIXTURES / "invalid_high_risk_no_approval.json")
    registry.register_manifest_result(invalid)
    decision = decide_quarantine_for_manifest_result(invalid)
    record = create_quarantine_record(
        QuarantineSubjectType.PLUGIN,
        "seal.invalid",
        invalid.validation_issues,
        decision,
        plugin_id="seal.invalid",
    )
    recorder.record(build_quarantine_record_created_event(record))

    assert execution_guard["submit"] == 0
    assert execution_guard["dispatch"] == 0
    assert execution_guard["command_envelope_make"] == 0
    assert execution_guard["subprocess_run"] == 0


# --------------------------------------------------------------------------- #
# 9. Authority boundary tests
# --------------------------------------------------------------------------- #


def test_tool_registration_does_not_create_authority_grant():
    registry = ToolRegistry()
    outcomes = _register_all_builtins(registry)
    for outcome in outcomes:
        if outcome.status is ToolRegistryOperationStatus.REGISTERED:
            assert outcome.entry is not None
            assert outcome.entry.capability is not None
            assert not hasattr(outcome, "approval_grant")
            assert not hasattr(outcome.entry.capability, "approved")


def test_invocation_draft_does_not_create_command_execution(execution_guard):
    registry = ToolRegistry()
    _register_all_builtins(registry)
    result = create_tool_invocation_draft(
        registry,
        "builtin.read_project_file",
        {"path": "README.md"},
        _context(),
    )
    assert result.draft is not None
    assert not isinstance(result, ObservationEnvelope)
    assert execution_guard["submit"] == 0


def test_high_risk_draft_requires_future_policy_path():
    registry = ToolRegistry()
    _register_all_builtins(registry)
    result = create_tool_invocation_draft(
        registry,
        "builtin.run_tests_draft",
        {"test_target": "pytest tests/"},
        _context(),
    )
    assert result.status is ToolInvocationDraftResultStatus.REQUIRES_APPROVAL
    assert result.draft is not None
    assert result.draft_status is ToolInvocationDraftStatus.REQUIRES_APPROVAL
    assert is_tool_invocation_draft_policy_ready(result.draft) is True
    assert result.approval_required is True


def test_registry_active_tool_still_not_executable(execution_guard):
    registry = ToolRegistry()
    _register_all_builtins(registry)
    assert registry.is_active("builtin.read_project_file")
    create_tool_invocation_draft(
        registry,
        "builtin.read_project_file",
        {"path": "README.md"},
        _context(),
    )
    assert execution_guard["submit"] == 0
    assert execution_guard["dispatch"] == 0


def test_p13_does_not_bypass_p2_authority_layer():
    forbidden_import_roots = (
        "agentic_runtime.runtime",
        "agentic_runtime.policy",
        "agentic_runtime.approval",
    )
    for module in _iter_tool_manifest_modules():
        for name, value in vars(module).items():
            if name.startswith("_"):
                continue
            mod_name = getattr(value, "__module__", "")
            if mod_name.startswith(forbidden_import_roots):
                pytest.fail(f"{module.__name__} references forbidden module {mod_name} via {name}")

    source_roots = (
        "from ..runtime",
        "from ..policy",
        "from ..approval",
        "import agentic_runtime.runtime",
        "import agentic_runtime.policy",
    )
    for module in _iter_tool_manifest_modules():
        source = inspect.getsource(module)
        for token in source_roots:
            assert token not in source, f"{module.__name__} imports forbidden authority path: {token}"


# --------------------------------------------------------------------------- #
# 10. Governance hotfix confirmation (canonical tests in p10/p11/p12/p15/p17)
# --------------------------------------------------------------------------- #


class TestGovHotfixConfirmation:
    """Lightweight smoke checks; full coverage lives in phase-specific test files."""

    def test_unknown_risk_tier_rejected(self, tmp_path):
        text = (
            "id: bad_prompt\nversion: 0.1.0\nowner: tests\nstatus: active\n"
            "purpose: test\nrisk_tier: unknown_tier\n"
            "allowed_model_profiles:\n  - planning\n"
            "input_schema:\n  type: object\n"
            "output_schema:\n  type: object\n"
            "policy:\n  raw_prompt_trace_allowed: false\n"
            "template:\n  - Hello\n"
        )
        root = tmp_path / "prompts"
        root.mkdir()
        (root / "bad.yaml").write_text(text, encoding="utf-8")
        with pytest.raises(PromptValidationError, match="risk_tier"):
            PromptRegistry(root).load()

    def test_blank_risk_tier_rejected(self, tmp_path):
        text = (
            "id: blank_prompt\nversion: 0.1.0\nowner: tests\nstatus: active\n"
            "purpose: test\nrisk_tier: \"\"\n"
            "allowed_model_profiles:\n  - planning\n"
            "input_schema:\n  type: object\n"
            "output_schema:\n  type: object\n"
            "policy:\n  raw_prompt_trace_allowed: false\n"
            "template:\n  - Hello\n"
        )
        root = tmp_path / "prompts"
        root.mkdir()
        (root / "blank.yaml").write_text(text, encoding="utf-8")
        with pytest.raises(PromptValidationError, match="risk_tier"):
            PromptRegistry(root).load()

    def test_yaml_list_of_maps_does_not_truncate(self):
        # Canonical: tests/test_model_config_p11.py::test_yaml_minimal_parses_list_of_mappings_without_truncation
        parsed = load_yaml("items:\n  - a: 1\n  - b: 2\n")
        assert len(parsed["items"]) == 2

    def test_restricted_local_reports_honest_sandbox_boundary(self, tmp_path):
        # Canonical: tests/test_sandbox_p17.py::test_restricted_local_diagnostics_report_policy_not_hard_isolation
        sandbox, policy = create_profiled_sandbox(
            SandboxProfileName.RESTRICTED_LOCAL.value,
            str(tmp_path),
        )
        diag = policy.diagnostics(sandbox)
        assert diag.backend_name == "UnsafeLocalSandbox"
        assert diag.unsafe is True
        assert diag.policy_restricted is True
        assert diag.hard_isolated is False

    def test_run_shell_remains_r4(self):
        # Canonical: tests/test_hitl_p15.py::test_policy_r4_warning_for_run_shell
        from agentic_runtime import AgentCard, AgentClass, ApprovalPolicy, ApprovalRiskClass, AuthorityScope, RiskLevel
        from agentic_runtime.policy import PolicyDecision, PolicyVerdict

        card = AgentCard.make(
            name="Seal Test Agent",
            agent_class=AgentClass.EXECUTION,
            mission="seal tests",
            authority=AuthorityScope(write_paths=["*"], read_paths=["*"], max_risk=RiskLevel.HIGH),
            allowed_tools=["run_shell"],
        )
        cmd = CommandEnvelope.make(
            card.id,
            "run_shell",
            {"cmd": ["echo", "hi"]},
            "req-seal",
            RiskLevel.MEDIUM,
            "fx-seal",
        )
        decision = PolicyDecision(PolicyVerdict.ALLOW, RiskLevel.HIGH, ["shell"])
        req = ApprovalPolicy().resolve(cmd, decision)
        assert req.strong_warning
        assert req.risk_class is ApprovalRiskClass.R4


# --------------------------------------------------------------------------- #
# 11. Research metadata preservation through lifecycle
# --------------------------------------------------------------------------- #


def test_research_metadata_survives_loader_to_event():
    """Prediction/simulation/learning metadata is preserved, not executed.

    Prediction metadata is not calibrated prediction.
    Simulation metadata does not execute simulation or dry-run.
    Learning profile does not trigger learning, memory write, or promotion.
    """
    load = load_manifest_file(BUILTIN_DIR / "builtin.filesystem.json")
    write_tool = next(t for t in load.tool_manifests if t.tool_id == "builtin.write_file_draft")

    assert write_tool.state_delta_contract is not None
    assert write_tool.state_delta_contract.affected_objects
    assert write_tool.state_delta_contract.expected_delta
    assert write_tool.predicted_effect is not None
    assert write_tool.prediction_observable is True
    assert write_tool.simulation_profile is not None
    assert write_tool.simulation_profile.dry_run_strategy == "diff_preview"
    assert write_tool.simulation_profile.simulation_strategy == "draft_only"
    assert write_tool.simulation_profile.safe_preview_mode == "draft_only"
    assert write_tool.tool_roles
    assert write_tool.learning_profile is not None
    assert write_tool.learning_profile.failure_should_be_remembered is True

    registry = ToolRegistry()
    registry.register_manifest_result(load)
    entry = registry.get_tool("builtin.write_file_draft")
    assert entry is not None
    capability_meta = research_metadata_from_capability(entry.capability)
    assert capability_meta["state_delta_contract"]["delta_type"] == "local_state_change"

    draft_result = create_tool_invocation_draft(
        registry,
        "builtin.write_file_draft",
        {"path": "example.txt", "content": "draft"},
        _context(),
    )
    assert draft_result.research_metadata["simulation_profile"]["simulation_strategy"] == "draft_only"
    assert draft_result.research_metadata["state_delta_contract"]["expected_delta"] == "draft_diff_created"

    event = build_invocation_draft_event(draft_result)
    assert event.metadata.get("state_delta_contract")
    assert event.metadata.get("simulation_profile")
    assert event.metadata.get("tool_roles")
    assert not hasattr(event, "execute")
