"""P1.3.2 — Tool Manifest Loader tests."""

from __future__ import annotations

import inspect
import json
from pathlib import Path

import pytest

from agentic_runtime.tool_manifest import (
    CapabilityType,
    ManifestLoadStatus,
    ManifestType,
    PluginOrigin,
    RiskClass,
    SideEffectType,
    ToolCategory,
    TraceLevel,
    compute_manifest_hash,
    determine_manifest_load_status,
    has_blocking_validation_issues,
    load_manifest_directory,
    load_manifest_file,
    parse_manifest_bundle,
    validate_manifest_bundle,
)
from agentic_runtime.tool_manifest.loader import (
    DUPLICATE_TOOL_ID_IN_BUNDLE,
    MANIFEST_ENUM_PARSE_ERROR,
    MANIFEST_TOOLS_EMPTY,
    PLUGIN_REFERENCES_MISSING_TOOL,
    TOOL_PLUGIN_ID_MISMATCH,
)
from agentic_runtime.tool_manifest.validation import (
    HIGH_RISK_REQUIRES_APPROVAL,
    TOOL_ID_MISSING,
)

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "tool_manifests"


def _fixture(name: str) -> Path:
    return FIXTURES / name


def _read_json(name: str) -> dict:
    return json.loads(_fixture(name).read_text(encoding="utf-8"))


def test_compute_manifest_hash_is_stable():
    content = '{"plugin": {}, "tools": []}'
    assert compute_manifest_hash(content) == compute_manifest_hash(content)
    assert compute_manifest_hash(content) != compute_manifest_hash(content + " ")


def test_load_valid_manifest_file():
    result = load_manifest_file(_fixture("valid_builtin_repo.json"))
    assert result.status in {
        ManifestLoadStatus.LOADED,
        ManifestLoadStatus.LOADED_WITH_WARNINGS,
    }
    assert result.plugin_manifest is not None
    assert result.plugin_manifest.plugin_id == "builtin.repo"
    assert len(result.tool_manifests) == 1
    assert result.tool_manifests[0].tool_id == "builtin.repo_scan"
    assert result.manifest_hash
    assert not has_blocking_validation_issues(result.validation_issues)


def test_load_missing_file_returns_not_found():
    result = load_manifest_file(FIXTURES / "does_not_exist.json")
    assert result.status is ManifestLoadStatus.NOT_FOUND
    assert result.parse_error is not None


def test_load_unsupported_format_returns_unsupported_format():
    result = load_manifest_file(_fixture("unsupported_manifest.txt"))
    assert result.status is ManifestLoadStatus.UNSUPPORTED_FORMAT
    assert result.parse_error is not None


def test_load_malformed_json_returns_parse_error():
    result = load_manifest_file(_fixture("malformed_manifest.json"))
    assert result.status is ManifestLoadStatus.PARSE_ERROR
    assert result.parse_error


def test_parse_valid_manifest_bundle():
    data = _read_json("valid_builtin_repo.json")
    bundle = parse_manifest_bundle(data, source_path="test.json", manifest_hash="abc")
    assert bundle.plugin.plugin_id == "builtin.repo"
    assert bundle.plugin.origin is PluginOrigin.BUILTIN
    assert len(bundle.tools) == 1
    tool = bundle.tools[0]
    assert tool.risk_class is RiskClass.R1
    assert tool.category is ToolCategory.CODE
    assert tool.capability_types == [CapabilityType.READ, CapabilityType.ANALYZE]
    assert tool.side_effects == [SideEffectType.LOCAL_READ]
    assert tool.trace_level is TraceLevel.MINIMAL


def test_plugin_tool_id_mismatch_produces_issue():
    bundle = parse_manifest_bundle(_read_json("invalid_plugin_tool_mismatch.json"))
    issues = validate_manifest_bundle(bundle)
    codes = {issue.code for issue in issues}
    assert TOOL_PLUGIN_ID_MISMATCH in codes
    assert has_blocking_validation_issues(issues)


def test_plugin_references_missing_tool_produces_issue():
    bundle = parse_manifest_bundle(_read_json("invalid_plugin_references_missing_tool.json"))
    issues = validate_manifest_bundle(bundle)
    assert PLUGIN_REFERENCES_MISSING_TOOL in {issue.code for issue in issues}
    assert has_blocking_validation_issues(issues)


def test_duplicate_tool_id_in_bundle_produces_issue():
    bundle = parse_manifest_bundle(_read_json("invalid_duplicate_tool_id.json"))
    issues = validate_manifest_bundle(bundle)
    assert DUPLICATE_TOOL_ID_IN_BUNDLE in {issue.code for issue in issues}
    assert has_blocking_validation_issues(issues)


def test_empty_tools_list_is_invalid():
    bundle = parse_manifest_bundle(_read_json("invalid_empty_tools.json"))
    issues = validate_manifest_bundle(bundle)
    assert MANIFEST_TOOLS_EMPTY in {issue.code for issue in issues}
    assert determine_manifest_load_status(issues) is ManifestLoadStatus.INVALID


def test_invalid_high_risk_tool_manifest_returns_validation_issue():
    result = load_manifest_file(_fixture("invalid_high_risk_no_approval.json"))
    assert result.status is ManifestLoadStatus.INVALID
    codes = {issue.code for issue in result.validation_issues}
    assert HIGH_RISK_REQUIRES_APPROVAL in codes


def test_load_directory_loads_multiple_manifests(tmp_path):
    for name in ("valid_builtin_repo.json", "valid_builtin_model.json"):
        (_fixture(name)).read_text(encoding="utf-8")
        dest = tmp_path / name
        dest.write_text(_fixture(name).read_text(encoding="utf-8"), encoding="utf-8")

    results = load_manifest_directory(tmp_path)
    assert len(results) == 2
    assert [r.source_path for r in results] == sorted(r.source_path for r in results)
    assert all(r.manifest_type is ManifestType.PLUGIN_BUNDLE for r in results)


def test_load_directory_continues_after_bad_manifest(tmp_path):
    (tmp_path / "valid_builtin_repo.json").write_text(
        _fixture("valid_builtin_repo.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (tmp_path / "malformed_manifest.json").write_text("{ broken", encoding="utf-8")

    results = load_manifest_directory(tmp_path)
    assert len(results) == 2
    by_name = {Path(r.source_path).name: r for r in results}
    assert by_name["valid_builtin_repo.json"].status in {
        ManifestLoadStatus.LOADED,
        ManifestLoadStatus.LOADED_WITH_WARNINGS,
    }
    assert by_name["malformed_manifest.json"].status is ManifestLoadStatus.PARSE_ERROR


def test_invalid_enum_value_returns_invalid_or_parse_error():
    result = load_manifest_file(_fixture("invalid_bad_enum.json"))
    assert result.status in {ManifestLoadStatus.PARSE_ERROR, ManifestLoadStatus.INVALID}
    if result.status is ManifestLoadStatus.PARSE_ERROR:
        assert MANIFEST_ENUM_PARSE_ERROR in {i.code for i in result.validation_issues}
    else:
        assert result.validation_issues


def test_load_missing_tool_id_fails_validation():
    result = load_manifest_file(_fixture("invalid_missing_tool_id.json"))
    assert result.status is ManifestLoadStatus.INVALID
    assert TOOL_ID_MISSING in {issue.code for issue in result.validation_issues}


def test_load_directory_missing_returns_not_found():
    results = load_manifest_directory(FIXTURES / "missing_dir")
    assert len(results) == 1
    assert results[0].status is ManifestLoadStatus.NOT_FOUND


def test_loader_does_not_register_or_execute_tools():
    source = inspect.getsource(load_manifest_file)
    assert "execute" not in source
    assert "register" not in source
    result = load_manifest_file(_fixture("valid_builtin_repo.json"))
    assert not hasattr(result, "invoke")
    assert not hasattr(result, "register")
