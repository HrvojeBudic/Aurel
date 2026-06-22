"""Local tool/plugin manifest file loader (P1.3.2).

Manifest loading reads, parses, hashes, and validates declarative files only.
It does not register tools, activate capabilities, or execute anything.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

from ..yaml_minimal import YamlParseError, load_yaml
from . import _serde as s
from .manifest import PluginManifest, ToolManifest, ValidationIssue
from .validation import (
    ValidationSeverity,
    has_blocking_validation_issues,
    validate_plugin_manifest,
    validate_tool_manifest,
)

# --------------------------------------------------------------------------- #
#  Loader-level validation codes
# --------------------------------------------------------------------------- #
MANIFEST_ROOT_NOT_OBJECT = "MANIFEST_ROOT_NOT_OBJECT"
MANIFEST_PLUGIN_MISSING = "MANIFEST_PLUGIN_MISSING"
MANIFEST_TOOLS_MISSING = "MANIFEST_TOOLS_MISSING"
MANIFEST_TOOLS_NOT_LIST = "MANIFEST_TOOLS_NOT_LIST"
MANIFEST_TOOLS_EMPTY = "MANIFEST_TOOLS_EMPTY"
TOOL_PLUGIN_ID_MISMATCH = "TOOL_PLUGIN_ID_MISMATCH"
PLUGIN_REFERENCES_MISSING_TOOL = "PLUGIN_REFERENCES_MISSING_TOOL"
TOOL_NOT_REFERENCED_BY_PLUGIN = "TOOL_NOT_REFERENCED_BY_PLUGIN"
DUPLICATE_TOOL_ID_IN_BUNDLE = "DUPLICATE_TOOL_ID_IN_BUNDLE"
MANIFEST_ENUM_PARSE_ERROR = "MANIFEST_ENUM_PARSE_ERROR"
MANIFEST_PARSE_ERROR = "MANIFEST_PARSE_ERROR"
MANIFEST_UNSUPPORTED_FORMAT = "MANIFEST_UNSUPPORTED_FORMAT"
MANIFEST_FILE_NOT_FOUND = "MANIFEST_FILE_NOT_FOUND"

_SUPPORTED_SUFFIXES = {".json", ".yaml", ".yml"}


class ManifestLoadStatus(str, Enum):
    LOADED = "loaded"
    LOADED_WITH_WARNINGS = "loaded_with_warnings"
    INVALID = "invalid"
    PARSE_ERROR = "parse_error"
    NOT_FOUND = "not_found"
    UNSUPPORTED_FORMAT = "unsupported_format"


class ManifestSourceType(str, Enum):
    FILE = "file"
    DIRECTORY = "directory"
    BUILTIN = "builtin"
    TEST_FIXTURE = "test_fixture"
    UNKNOWN = "unknown"


class ManifestType(str, Enum):
    PLUGIN_BUNDLE = "plugin_bundle"
    TOOL_ONLY = "tool_only"
    UNKNOWN = "unknown"


class ManifestParseError(Exception):
    def __init__(
        self,
        message: str,
        *,
        code: str = MANIFEST_PARSE_ERROR,
        field: str | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.field = field


@dataclass
class ManifestSource:
    path: str
    source_type: ManifestSourceType
    discovered_at: datetime
    hash: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "source_type": self.source_type.value,
            "discovered_at": s.datetime_to_iso(self.discovered_at),
            "hash": self.hash,
        }


@dataclass
class ManifestBundle:
    plugin: PluginManifest
    tools: list[ToolManifest]
    source_path: str | None = None
    bundle_hash: str | None = None
    validation_issues: list[ValidationIssue] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "plugin": self.plugin.to_dict(),
            "tools": [tool.to_dict() for tool in self.tools],
            "source_path": self.source_path,
            "bundle_hash": self.bundle_hash,
            "validation_issues": [issue.to_dict() for issue in self.validation_issues],
        }


@dataclass
class ManifestLoadResult:
    source_path: str
    manifest_type: ManifestType
    plugin_manifest: PluginManifest | None
    tool_manifests: list[ToolManifest]
    manifest_hash: str | None
    loaded_at: datetime
    validation_issues: list[ValidationIssue]
    status: ManifestLoadStatus
    parse_error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_path": self.source_path,
            "manifest_type": self.manifest_type.value,
            "plugin_manifest": (
                self.plugin_manifest.to_dict() if self.plugin_manifest else None
            ),
            "tool_manifests": [tool.to_dict() for tool in self.tool_manifests],
            "manifest_hash": self.manifest_hash,
            "loaded_at": s.datetime_to_iso(self.loaded_at),
            "validation_issues": [issue.to_dict() for issue in self.validation_issues],
            "status": self.status.value,
            "parse_error": self.parse_error,
        }


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _issue(
    code: str,
    message: str,
    field: str | None,
    severity: ValidationSeverity,
) -> ValidationIssue:
    return ValidationIssue(code=code, message=message, field=field, severity=severity)


def compute_manifest_hash(raw_content: str | bytes) -> str:
    if isinstance(raw_content, str):
        payload = raw_content.encode("utf-8")
    else:
        payload = raw_content
    return hashlib.sha256(payload).hexdigest()


def determine_manifest_load_status(
    issues: list[ValidationIssue],
) -> ManifestLoadStatus:
    if has_blocking_validation_issues(issues):
        return ManifestLoadStatus.INVALID
    if any(
        issue.severity in {ValidationSeverity.WARNING, ValidationSeverity.INFO}
        for issue in issues
    ):
        return ManifestLoadStatus.LOADED_WITH_WARNINGS
    return ManifestLoadStatus.LOADED


def _parse_plugin(data: dict[str, Any]) -> PluginManifest:
    try:
        return PluginManifest.from_dict(data)
    except (KeyError, ValueError, TypeError) as exc:
        raise ManifestParseError(
            f"failed to parse plugin manifest: {exc}",
            code=MANIFEST_ENUM_PARSE_ERROR,
            field="plugin",
        ) from exc


def _parse_tool(data: dict[str, Any], index: int) -> ToolManifest:
    if not isinstance(data, dict):
        raise ManifestParseError(
            f"tool entry at index {index} must be an object",
            code=MANIFEST_PARSE_ERROR,
            field=f"tools[{index}]",
        )
    try:
        return ToolManifest.from_dict(data)
    except (KeyError, ValueError, TypeError) as exc:
        raise ManifestParseError(
            f"failed to parse tool manifest at index {index}: {exc}",
            code=MANIFEST_ENUM_PARSE_ERROR,
            field=f"tools[{index}]",
        ) from exc


def parse_manifest_bundle(
    data: dict[str, Any],
    source_path: str | None = None,
    manifest_hash: str | None = None,
) -> ManifestBundle:
    if not isinstance(data, dict):
        raise ManifestParseError(
            "manifest root must be a JSON object",
            code=MANIFEST_ROOT_NOT_OBJECT,
            field="<root>",
        )
    if "plugin" not in data:
        raise ManifestParseError(
            "manifest root must contain 'plugin'",
            code=MANIFEST_PLUGIN_MISSING,
            field="plugin",
        )
    if "tools" not in data:
        raise ManifestParseError(
            "manifest root must contain 'tools'",
            code=MANIFEST_TOOLS_MISSING,
            field="tools",
        )
    if not isinstance(data["plugin"], dict):
        raise ManifestParseError(
            "plugin must be an object",
            code=MANIFEST_PARSE_ERROR,
            field="plugin",
        )
    if not isinstance(data["tools"], list):
        raise ManifestParseError(
            "tools must be a list",
            code=MANIFEST_TOOLS_NOT_LIST,
            field="tools",
        )

    plugin = _parse_plugin(data["plugin"])
    tools = [_parse_tool(item, index) for index, item in enumerate(data["tools"])]

    return ManifestBundle(
        plugin=plugin,
        tools=tools,
        source_path=source_path,
        bundle_hash=manifest_hash,
        validation_issues=[],
    )


def validate_manifest_bundle(bundle: ManifestBundle) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    plugin = bundle.plugin
    tools = bundle.tools

    issues.extend(validate_plugin_manifest(plugin))

    if not tools:
        issues.append(_issue(
            MANIFEST_TOOLS_EMPTY,
            "manifest bundle must declare at least one tool",
            "tools",
            ValidationSeverity.ERROR,
        ))

    tool_ids: set[str] = set()
    for tool in tools:
        if tool.tool_id in tool_ids:
            issues.append(_issue(
                DUPLICATE_TOOL_ID_IN_BUNDLE,
                f"duplicate tool_id '{tool.tool_id}' in bundle",
                "tools",
                ValidationSeverity.ERROR,
            ))
        tool_ids.add(tool.tool_id)

        if tool.plugin_id != plugin.plugin_id:
            issues.append(_issue(
                TOOL_PLUGIN_ID_MISMATCH,
                (
                    f"tool '{tool.tool_id}' plugin_id '{tool.plugin_id}' "
                    f"does not match plugin '{plugin.plugin_id}'"
                ),
                "plugin_id",
                ValidationSeverity.ERROR,
            ))

        issues.extend(validate_tool_manifest(tool, plugin))

    if plugin.tools:
        declared = set(plugin.tools)
        for ref in declared:
            if ref not in tool_ids:
                issues.append(_issue(
                    PLUGIN_REFERENCES_MISSING_TOOL,
                    f"plugin.tools references missing tool_id '{ref}'",
                    "plugin.tools",
                    ValidationSeverity.ERROR,
                ))
        for tool in tools:
            if tool.tool_id not in declared:
                issues.append(_issue(
                    TOOL_NOT_REFERENCED_BY_PLUGIN,
                    f"tool '{tool.tool_id}' is not listed in plugin.tools",
                    "plugin.tools",
                    ValidationSeverity.ERROR,
                ))

    return _dedupe_issues(issues)


def _dedupe_issues(issues: list[ValidationIssue]) -> list[ValidationIssue]:
    severity_rank = {
        ValidationSeverity.INFO: 0,
        ValidationSeverity.WARNING: 1,
        ValidationSeverity.ERROR: 2,
        ValidationSeverity.CRITICAL: 3,
    }
    best: dict[tuple[str, str | None], ValidationIssue] = {}
    for issue in issues:
        key = (issue.code, issue.field)
        existing = best.get(key)
        if existing is None or severity_rank[issue.severity] > severity_rank[existing.severity]:
            best[key] = issue
    return list(best.values())


def _parse_file_content(path: Path, raw: str) -> dict[str, Any]:
    suffix = path.suffix.lower()
    if suffix == ".json":
        data = json.loads(raw)
    elif suffix in {".yaml", ".yml"}:
        data = load_yaml(raw)
    else:
        raise ManifestParseError(
            f"unsupported manifest format '{suffix}'",
            code=MANIFEST_UNSUPPORTED_FORMAT,
        )
    if not isinstance(data, dict):
        raise ManifestParseError(
            "manifest root must be a mapping",
            code=MANIFEST_ROOT_NOT_OBJECT,
        )
    return data


def _result_from_parse_error(
    path: Path,
    *,
    status: ManifestLoadStatus,
    message: str,
    code: str = MANIFEST_PARSE_ERROR,
    field: str | None = None,
) -> ManifestLoadResult:
    issues = [
        _issue(code, message, field, ValidationSeverity.ERROR),
    ]
    return ManifestLoadResult(
        source_path=str(path),
        manifest_type=ManifestType.UNKNOWN,
        plugin_manifest=None,
        tool_manifests=[],
        manifest_hash=None,
        loaded_at=_utc_now(),
        validation_issues=issues,
        status=status,
        parse_error=message,
    )


def load_manifest_file(path: Path | str) -> ManifestLoadResult:
    file_path = Path(path)
    loaded_at = _utc_now()

    if not file_path.exists():
        return ManifestLoadResult(
            source_path=str(file_path),
            manifest_type=ManifestType.UNKNOWN,
            plugin_manifest=None,
            tool_manifests=[],
            manifest_hash=None,
            loaded_at=loaded_at,
            validation_issues=[
                _issue(
                    MANIFEST_FILE_NOT_FOUND,
                    f"manifest file not found: {file_path}",
                    None,
                    ValidationSeverity.ERROR,
                ),
            ],
            status=ManifestLoadStatus.NOT_FOUND,
            parse_error=f"file not found: {file_path}",
        )

    if file_path.suffix.lower() not in _SUPPORTED_SUFFIXES:
        return ManifestLoadResult(
            source_path=str(file_path),
            manifest_type=ManifestType.UNKNOWN,
            plugin_manifest=None,
            tool_manifests=[],
            manifest_hash=None,
            loaded_at=loaded_at,
            validation_issues=[
                _issue(
                    MANIFEST_UNSUPPORTED_FORMAT,
                    f"unsupported manifest format: {file_path.suffix}",
                    None,
                    ValidationSeverity.ERROR,
                ),
            ],
            status=ManifestLoadStatus.UNSUPPORTED_FORMAT,
            parse_error=f"unsupported format: {file_path.suffix}",
        )

    raw_bytes = file_path.read_bytes()
    manifest_hash = compute_manifest_hash(raw_bytes)
    raw_text = raw_bytes.decode("utf-8")

    try:
        data = _parse_file_content(file_path, raw_text)
    except json.JSONDecodeError as exc:
        return _result_from_parse_error(
            file_path,
            status=ManifestLoadStatus.PARSE_ERROR,
            message=f"malformed JSON: {exc.msg}",
            code=MANIFEST_PARSE_ERROR,
        )
    except YamlParseError as exc:
        return _result_from_parse_error(
            file_path,
            status=ManifestLoadStatus.PARSE_ERROR,
            message=f"malformed YAML: {exc}",
            code=MANIFEST_PARSE_ERROR,
        )
    except ManifestParseError as exc:
        return _result_from_parse_error(
            file_path,
            status=ManifestLoadStatus.PARSE_ERROR,
            message=exc.message,
            code=exc.code,
            field=exc.field,
        )

    try:
        bundle = parse_manifest_bundle(
            data,
            source_path=str(file_path),
            manifest_hash=manifest_hash,
        )
    except ManifestParseError as exc:
        return _result_from_parse_error(
            file_path,
            status=ManifestLoadStatus.PARSE_ERROR,
            message=exc.message,
            code=exc.code,
            field=exc.field,
        )

    issues = validate_manifest_bundle(bundle)
    status = determine_manifest_load_status(issues)

    return ManifestLoadResult(
        source_path=str(file_path),
        manifest_type=ManifestType.PLUGIN_BUNDLE,
        plugin_manifest=bundle.plugin,
        tool_manifests=list(bundle.tools),
        manifest_hash=manifest_hash,
        loaded_at=loaded_at,
        validation_issues=issues,
        status=status,
        parse_error=None,
    )


def load_manifest_directory(path: Path | str) -> list[ManifestLoadResult]:
    dir_path = Path(path)
    if not dir_path.exists() or not dir_path.is_dir():
        return [
            ManifestLoadResult(
                source_path=str(dir_path),
                manifest_type=ManifestType.UNKNOWN,
                plugin_manifest=None,
                tool_manifests=[],
                manifest_hash=None,
                loaded_at=_utc_now(),
                validation_issues=[
                    _issue(
                        MANIFEST_FILE_NOT_FOUND,
                        f"manifest directory not found: {dir_path}",
                        None,
                        ValidationSeverity.ERROR,
                    ),
                ],
                status=ManifestLoadStatus.NOT_FOUND,
                parse_error=f"directory not found: {dir_path}",
            ),
        ]

    manifest_files = sorted(
        p for p in dir_path.iterdir()
        if p.is_file() and p.suffix.lower() in _SUPPORTED_SUFFIXES
    )

    results: list[ManifestLoadResult] = []
    for manifest_file in manifest_files:
        try:
            results.append(load_manifest_file(manifest_file))
        except OSError as exc:
            results.append(_result_from_parse_error(
                manifest_file,
                status=ManifestLoadStatus.PARSE_ERROR,
                message=f"failed to read manifest file: {exc}",
            ))
    return results
