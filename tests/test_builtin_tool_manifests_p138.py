"""P1.3.8 — Built-in Tool Manifest Seed tests."""

from __future__ import annotations

import inspect
import json
from dataclasses import replace
from pathlib import Path

from agentic_runtime.tool_manifest import (
    ManifestLoadStatus,
    SideEffectType,
    StateDeltaType,
    ToolInvocationContext,
    ToolInvocationDraftResultStatus,
    ToolLifecycleEventRecorder,
    ToolLifecycleEventType,
    ToolRegistry,
    ToolRegistryOperationStatus,
    ToolRole,
    build_invocation_draft_event,
    build_manifest_loaded_event,
    build_registry_built_event,
    build_tool_registered_event,
    create_tool_invocation_draft,
    get_builtin_manifest_directory,
    load_builtin_tool_manifests,
    load_manifest_directory,
    load_manifest_file,
)
from agentic_runtime.tool_manifest.research_metadata import is_state_changing_capability
from agentic_runtime.tool_manifest import research_metadata as research_metadata_mod
from agentic_runtime.tool_manifest import registry as registry_mod
from agentic_runtime.tool_manifest import invocation as invocation_mod
from agentic_runtime.tool_manifest import loader as loader_mod
from agentic_runtime.tool_manifest import events as events_mod

BUILTIN_DIR = get_builtin_manifest_directory()
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "tool_manifests"

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

STATE_CHANGING_TOOL_IDS = frozenset({
    "builtin.write_file_draft",
    "builtin.run_tests_draft",
    "builtin.create_evidence_record",
    "builtin.create_memory_candidate",
})

_LOADABLE_STATUSES = frozenset({
    ManifestLoadStatus.LOADED,
    ManifestLoadStatus.LOADED_WITH_WARNINGS,
})


def _context(**overrides) -> ToolInvocationContext:
    base = ToolInvocationContext(
        requested_by="operator",
        purpose="Built-in manifest integration test",
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


def test_builtin_manifest_files_exist():
    assert BUILTIN_DIR.is_dir()
    present = {path.name for path in BUILTIN_DIR.glob("*.json")}
    assert EXPECTED_MANIFEST_FILES <= present


def test_builtin_manifests_are_valid_json():
    for filename in sorted(EXPECTED_MANIFEST_FILES):
        path = BUILTIN_DIR / filename
        data = json.loads(path.read_text(encoding="utf-8"))
        assert isinstance(data, dict)
        assert "plugin" in data
        assert "tools" in data


def test_builtin_manifests_load_without_parse_error():
    results = load_builtin_tool_manifests()
    assert len(results) == len(EXPECTED_MANIFEST_FILES)
    for result in results:
        assert result.status not in {
            ManifestLoadStatus.PARSE_ERROR,
            ManifestLoadStatus.UNSUPPORTED_FORMAT,
            ManifestLoadStatus.NOT_FOUND,
        }
        assert result.status in _LOADABLE_STATUSES


def test_builtin_manifests_have_required_research_metadata():
    read_only_effects = {
        SideEffectType.NONE,
        SideEffectType.LOCAL_READ,
        SideEffectType.EXTERNAL_READ,
    }
    for tool in _all_builtin_tools():
        assert tool.tool_roles, f"{tool.tool_id} missing tool_roles"
        effects = set(tool.side_effects)
        is_state_changing = bool(effects - read_only_effects)
        if is_state_changing or tool.risk_class.value >= "R3":
            assert tool.state_delta_contract is not None, tool.tool_id
        if tool.risk_class.value >= "R3" or SideEffectType.PROCESS_EXECUTION in effects:
            assert tool.safety_surface is not None, tool.tool_id


def test_builtin_manifests_have_tool_roles():
    for tool in _all_builtin_tools():
        assert tool.tool_roles


def test_builtin_state_changing_tools_have_state_delta_contract():
    tools = {tool.tool_id: tool for tool in _all_builtin_tools()}
    for tool_id in STATE_CHANGING_TOOL_IDS:
        tool = tools[tool_id]
        assert tool.state_delta_contract is not None
        assert tool.state_delta_contract.delta_type not in {
            StateDeltaType.NONE,
            StateDeltaType.READ_ONLY_OBSERVATION,
        }


def test_builtin_high_risk_tools_have_safety_surface():
    tools = {tool.tool_id: tool for tool in _all_builtin_tools()}
    run_tests = tools["builtin.run_tests_draft"]
    assert run_tests.risk_class.value == "R3"
    assert run_tests.safety_surface is not None
    assert run_tests.safety_surface.operator_attention_required is True


def test_load_builtin_tool_manifests():
    results = load_builtin_tool_manifests()
    assert len(results) == 6
    assert all(result.status in _LOADABLE_STATUSES for result in results)
    tool_count = sum(len(result.tool_manifests) for result in results)
    assert tool_count == len(EXPECTED_TOOL_IDS)


def test_register_builtin_tool_manifests():
    registry = ToolRegistry()
    outcomes = _register_all_builtins(registry)
    registered = [
        outcome for outcome in outcomes
        if outcome.status is ToolRegistryOperationStatus.REGISTERED
    ]
    assert len(registered) == len(EXPECTED_TOOL_IDS)


def test_builtin_tools_appear_in_registry():
    registry = ToolRegistry()
    _register_all_builtins(registry)
    for tool_id in EXPECTED_TOOL_IDS:
        entry = registry.get_tool(tool_id)
        assert entry is not None
        assert entry.capability is not None
        assert entry.capability.tool_id == tool_id


def test_builtin_active_tools_exclude_blocked_or_quarantined():
    registry = ToolRegistry()
    _register_all_builtins(registry)
    quarantined = load_manifest_file(FIXTURES / "invalid_high_risk_no_approval.json")
    registry.register_manifest_result(quarantined)

    active_ids = {entry.capability.tool_id for entry in registry.list_active_tools()}
    assert EXPECTED_TOOL_IDS <= active_ids
    assert "risky.repo_write" not in active_ids


def test_builtin_tools_query_by_role():
    registry = ToolRegistry()
    _register_all_builtins(registry)

    perception = registry.list_by_tool_role(ToolRole.PERCEPTION)
    cognition = registry.list_by_tool_role(ToolRole.COGNITION)
    action = registry.list_by_tool_role(ToolRole.ACTION)
    verification = registry.list_by_tool_role(ToolRole.VERIFICATION)
    memory = registry.list_by_tool_role(ToolRole.MEMORY)
    governance = registry.list_by_tool_role(ToolRole.GOVERNANCE)

    perception_ids = {entry.capability.tool_id for entry in perception}
    assert "builtin.repo_scan" in perception_ids
    assert "builtin.read_project_file" in perception_ids

    cognition_ids = {entry.capability.tool_id for entry in cognition}
    assert "builtin.repo_scan" in cognition_ids
    assert "builtin.model_complete_structured" in cognition_ids

    action_ids = {entry.capability.tool_id for entry in action}
    assert "builtin.write_file_draft" in action_ids

    verification_ids = {entry.capability.tool_id for entry in verification}
    assert "builtin.run_tests_draft" in verification_ids
    assert "builtin.create_evidence_record" in verification_ids

    memory_ids = {entry.capability.tool_id for entry in memory}
    assert "builtin.create_memory_candidate" in memory_ids

    governance_ids = {entry.capability.tool_id for entry in governance}
    assert "builtin.create_evidence_record" in governance_ids


def test_builtin_state_changing_tools_query():
    registry = ToolRegistry()
    _register_all_builtins(registry)
    changing_ids = {
        entry.capability.tool_id
        for entry in registry.list_state_changing_tools()
    }
    assert STATE_CHANGING_TOOL_IDS <= changing_ids
    for entry in registry.list_state_changing_tools():
        assert is_state_changing_capability(entry.capability)


def test_create_draft_for_builtin_repo_scan():
    registry = ToolRegistry()
    _register_all_builtins(registry)
    result = create_tool_invocation_draft(
        registry,
        "builtin.repo_scan",
        {"root_path": "."},
        _context(purpose="Inspect repository layout"),
    )
    assert result.status is ToolInvocationDraftResultStatus.CREATED
    assert result.draft is not None
    assert result.draft.tool_id == "builtin.repo_scan"


def test_create_draft_for_builtin_read_project_file():
    registry = ToolRegistry()
    _register_all_builtins(registry)
    result = create_tool_invocation_draft(
        registry,
        "builtin.read_project_file",
        {"path": "README.md"},
        _context(purpose="Read project file"),
    )
    assert result.status is ToolInvocationDraftResultStatus.CREATED
    assert result.draft is not None


def test_create_draft_for_builtin_write_file_draft():
    registry = ToolRegistry()
    _register_all_builtins(registry)
    result = create_tool_invocation_draft(
        registry,
        "builtin.write_file_draft",
        {"path": "example.txt", "content": "proposed content"},
        _context(purpose="Prepare file diff"),
    )
    assert result.status is ToolInvocationDraftResultStatus.CREATED
    assert result.draft is not None
    metadata = result.research_metadata
    assert metadata["state_delta_contract"]["delta_type"] == "local_state_change"
    assert metadata["simulation_profile"]["simulation_strategy"] == "draft_only"


def test_builtin_run_tests_draft_requires_approval_or_policy_path():
    registry = ToolRegistry()
    _register_all_builtins(registry)
    result = create_tool_invocation_draft(
        registry,
        "builtin.run_tests_draft",
        {"test_target": "pytest tests/"},
        _context(purpose="Plan test execution"),
    )
    assert result.status is ToolInvocationDraftResultStatus.REQUIRES_APPROVAL
    assert result.draft is not None
    assert result.approval_required is True


def test_builtin_memory_candidate_draft():
    registry = ToolRegistry()
    _register_all_builtins(registry)
    result = create_tool_invocation_draft(
        registry,
        "builtin.create_memory_candidate",
        {"summary": "Candidate note", "source_trace_id": "trace-123"},
        _context(purpose="Create memory candidate"),
    )
    assert result.status is ToolInvocationDraftResultStatus.CREATED
    assert result.draft is not None
    assert result.research_metadata["state_delta_contract"]["delta_type"] == "memory_state_change"


def test_builtin_manifest_load_events():
    recorder = ToolLifecycleEventRecorder()
    for result in load_builtin_tool_manifests():
        if result.status in _LOADABLE_STATUSES:
            event = build_manifest_loaded_event(result)
            recorder.record(event)
            assert event.event_type is ToolLifecycleEventType.MANIFEST_LOADED
    assert len(recorder.list_by_type(ToolLifecycleEventType.MANIFEST_LOADED)) == 6


def test_builtin_registry_events():
    registry = ToolRegistry()
    outcomes = _register_all_builtins(registry)
    recorder = ToolLifecycleEventRecorder()
    for outcome in outcomes:
        if outcome.status is ToolRegistryOperationStatus.REGISTERED:
            recorder.record(build_tool_registered_event(outcome))
    recorder.record(build_registry_built_event(outcomes))
    assert len(recorder.list_by_type(ToolLifecycleEventType.TOOL_CAPABILITY_REGISTERED)) == 7
    assert len(recorder.list_by_type(ToolLifecycleEventType.REGISTRY_BUILT)) == 1


def test_builtin_invocation_draft_events():
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
    assert event.metadata.get("tool_roles")


def test_builtin_lifecycle_trace_without_execution():
    forbidden = ("execute_tool", "invoke_tool", "run_tool", ".invoke(", ".execute(", "subprocess")
    for module in (registry_mod, invocation_mod, loader_mod, events_mod, research_metadata_mod):
        source = inspect.getsource(module)
        for token in forbidden:
            assert token not in source, f"{module.__name__} contains forbidden token {token!r}"

    recorder = ToolLifecycleEventRecorder()
    load_results = load_builtin_tool_manifests()
    for load in load_results:
        if load.status in _LOADABLE_STATUSES:
            recorder.record(build_manifest_loaded_event(load))

    registry = ToolRegistry()
    reg_outcomes = _register_all_builtins(registry)
    for reg_result in reg_outcomes:
        if reg_result.status is ToolRegistryOperationStatus.REGISTERED:
            recorder.record(build_tool_registered_event(reg_result))

    draft_result = create_tool_invocation_draft(
        registry,
        "builtin.read_project_file",
        {"path": "README.md"},
        _context(),
    )
    recorder.record(build_invocation_draft_event(draft_result))

    assert len(recorder.list_events()) >= 8
    assert not hasattr(registry, "invoke")
    assert not hasattr(registry, "execute")


def test_get_builtin_manifest_directory_matches_loader():
    assert get_builtin_manifest_directory().exists()
    direct = load_manifest_directory(BUILTIN_DIR)
    helper = load_builtin_tool_manifests()
    assert len(direct) == len(helper)
