"""Path Governance CLI/TUI Binding (P1.7.18).

Read-only terminal-facing projection over P1.7.17 read model/API envelope.

CLI binding exposes projection state. It does not create authority.
CLI output is not source of truth. CLI command is not policy decision.
"""
from __future__ import annotations

from collections.abc import Mapping as MappingABC, Sequence
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping

from .errors import (
    PathGovernanceError,
    PathGovernanceErrorCode,
    PathGovernanceValidationError,
)
from .labels import ProjectionSourceLabel
from .projection_contract import (
    HTTP_SERVER_UNAVAILABLE_REASON,
    LEDGER_WRITE_UNAVAILABLE_REASON,
    POLICY_RUNTIME_UNAVAILABLE_REASON,
    SHELL_BINDING_UNAVAILABLE_REASON,
    PathGovernanceApiEnvelope,
    PathGovernanceCapabilityKind,
    PathGovernanceProjectionEvent,
    PathGovernanceProjectionRecord,
    PathGovernanceReadModel,
    build_default_path_governance_capability_projection,
    build_path_governance_api_envelope,
    build_path_governance_read_model,
)
from .serialization import stable_hash
from .validation import validate_known_fields

PATH_GOVERNANCE_CLI_TASK_ID = "P1.7.18"
PATH_GOVERNANCE_CLI_RESPONSE_SCHEMA = "path_governance_cli_response.v1"
PATH_GOVERNANCE_CLI_REQUEST_SCHEMA = "path_governance_cli_request.v1"
PATH_GOVERNANCE_CLI_SIDE_EFFECTS_SCHEMA = "path_governance_cli_side_effects.v1"
PATH_GOVERNANCE_CLI_RENDERED_LINE_SCHEMA = "path_governance_cli_rendered_line.v1"

ENFORCEMENT_UNAVAILABLE_REASON = (
    "UNAVAILABLE: enforcement not implemented in P1.7.18"
)

PATH_GOVERNANCE_CLI_SIDE_EFFECTS_KNOWN_FIELDS: frozenset[str] = frozenset({
    "policy_called",
    "approval_created",
    "ledger_written",
    "global_trace_written",
    "runtime_mutated",
    "enforcement_triggered",
    "source_mutated",
    "prompt_filtered",
    "memory_written",
    "tool_blocked",
    "side_effects_hash",
    "metadata",
})

PATH_GOVERNANCE_CLI_REQUEST_KNOWN_FIELDS: frozenset[str] = frozenset({
    "request_id",
    "command_kind",
    "output_format",
    "include_events",
    "include_unavailable",
    "include_metadata",
    "source_label",
    "request_hash",
    "schema_version",
    "metadata",
})

PATH_GOVERNANCE_CLI_RENDERED_LINE_KNOWN_FIELDS: frozenset[str] = frozenset({
    "line_id",
    "level",
    "text",
    "state_label",
    "capability_kind",
    "source_label",
    "line_hash",
    "schema_version",
    "metadata",
})

PATH_GOVERNANCE_CLI_RESPONSE_KNOWN_FIELDS: frozenset[str] = frozenset({
    "response_id",
    "request_id",
    "command_kind",
    "output_format",
    "binding_mode",
    "read_model",
    "api_envelope",
    "rendered_output",
    "rendered_lines",
    "json_payload",
    "unavailable_reasons",
    "side_effects",
    "source_label",
    "schema_version",
    "created_by_task",
    "response_hash",
    "metadata",
})


class PathGovernanceCliCommandKind(str, Enum):
    """Read-only CLI command classification."""

    STATUS = "STATUS"
    CAPABILITIES = "CAPABILITIES"
    READ_MODEL = "READ_MODEL"
    API_ENVELOPE = "API_ENVELOPE"
    EVENTS = "EVENTS"
    HARNESS_SUMMARY = "HARNESS_SUMMARY"
    POLICY_CONTEXT_SUMMARY = "POLICY_CONTEXT_SUMMARY"
    TRACE_HOOK_SUMMARY = "TRACE_HOOK_SUMMARY"
    VIOLATION_DRIFT_SUMMARY = "VIOLATION_DRIFT_SUMMARY"
    UNAVAILABLE_BINDINGS = "UNAVAILABLE_BINDINGS"
    UNKNOWN = "UNKNOWN"


class PathGovernanceCliOutputFormat(str, Enum):
    """CLI output format classification."""

    TEXT = "TEXT"
    JSON = "JSON"
    TABLE = "TABLE"
    TUI_TEXT = "TUI_TEXT"
    UNKNOWN = "UNKNOWN"


class PathGovernanceCliBindingMode(str, Enum):
    """CLI binding mode; default is read-only projection."""

    READ_ONLY = "READ_ONLY"
    PROJECTION_ONLY = "PROJECTION_ONLY"
    DEV_FIXTURE_ALLOWED = "DEV_FIXTURE_ALLOWED"
    ERROR = "ERROR"
    UNKNOWN = "UNKNOWN"


class PathGovernanceCliRenderLineLevel(str, Enum):
    """Rendered line severity/style."""

    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"
    HEADER = "HEADER"
    ROW = "ROW"


def _freeze_metadata(metadata: Mapping[str, Any] | None) -> Mapping[str, Any]:
    raw = {} if metadata is None else metadata
    if not isinstance(raw, MappingABC):
        raise PathGovernanceValidationError(
            "metadata must be a mapping",
            code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
            field="metadata",
        )
    frozen = dict(raw)
    stable_hash(frozen)
    return MappingProxyType(frozen)


def _sorted_metadata_dict(metadata: Mapping[str, Any]) -> dict[str, Any]:
    return dict(sorted(metadata.items(), key=lambda item: item[0]))


def _parse_source_label(value: ProjectionSourceLabel | str) -> ProjectionSourceLabel:
    if isinstance(value, ProjectionSourceLabel):
        return value
    if isinstance(value, str):
        try:
            return ProjectionSourceLabel(value)
        except ValueError as exc:
            raise PathGovernanceError(
                f"invalid source_label: {value!r}",
                code=PathGovernanceErrorCode.INVALID_SOURCE_LABEL,
                field="source_label",
            ) from exc
    raise PathGovernanceError(
        "source_label must be a string or ProjectionSourceLabel",
        code=PathGovernanceErrorCode.INVALID_SOURCE_LABEL,
        field="source_label",
    )


def _parse_command_kind(
    value: PathGovernanceCliCommandKind | str,
) -> PathGovernanceCliCommandKind:
    if isinstance(value, PathGovernanceCliCommandKind):
        return value
    if isinstance(value, str):
        try:
            return PathGovernanceCliCommandKind(value)
        except ValueError as exc:
            raise PathGovernanceError(
                f"invalid command_kind: {value!r}",
                code=PathGovernanceErrorCode.INVALID_ENUM,
                field="command_kind",
            ) from exc
    raise PathGovernanceError(
        "command_kind must be a string or PathGovernanceCliCommandKind",
        code=PathGovernanceErrorCode.INVALID_ENUM,
        field="command_kind",
    )


def _parse_output_format(
    value: PathGovernanceCliOutputFormat | str,
) -> PathGovernanceCliOutputFormat:
    if isinstance(value, PathGovernanceCliOutputFormat):
        return value
    if isinstance(value, str):
        try:
            return PathGovernanceCliOutputFormat(value)
        except ValueError as exc:
            raise PathGovernanceError(
                f"invalid output_format: {value!r}",
                code=PathGovernanceErrorCode.INVALID_ENUM,
                field="output_format",
            ) from exc
    raise PathGovernanceError(
        "output_format must be a string or PathGovernanceCliOutputFormat",
        code=PathGovernanceErrorCode.INVALID_ENUM,
        field="output_format",
    )


def _parse_binding_mode(
    value: PathGovernanceCliBindingMode | str,
) -> PathGovernanceCliBindingMode:
    if isinstance(value, PathGovernanceCliBindingMode):
        return value
    if isinstance(value, str):
        try:
            return PathGovernanceCliBindingMode(value)
        except ValueError as exc:
            raise PathGovernanceError(
                f"invalid binding_mode: {value!r}",
                code=PathGovernanceErrorCode.INVALID_ENUM,
                field="binding_mode",
            ) from exc
    raise PathGovernanceError(
        "binding_mode must be a string or PathGovernanceCliBindingMode",
        code=PathGovernanceErrorCode.INVALID_ENUM,
        field="binding_mode",
    )


def _parse_line_level(
    value: PathGovernanceCliRenderLineLevel | str,
) -> PathGovernanceCliRenderLineLevel:
    if isinstance(value, PathGovernanceCliRenderLineLevel):
        return value
    if isinstance(value, str):
        try:
            return PathGovernanceCliRenderLineLevel(value)
        except ValueError as exc:
            raise PathGovernanceError(
                f"invalid level: {value!r}",
                code=PathGovernanceErrorCode.INVALID_ENUM,
                field="level",
            ) from exc
    raise PathGovernanceError(
        "level must be a string or PathGovernanceCliRenderLineLevel",
        code=PathGovernanceErrorCode.INVALID_ENUM,
        field="level",
    )


def _parse_capability_kind(
    value: PathGovernanceCapabilityKind | str | None,
) -> PathGovernanceCapabilityKind | None:
    if value is None:
        return None
    if isinstance(value, PathGovernanceCapabilityKind):
        return value
    if isinstance(value, str):
        try:
            return PathGovernanceCapabilityKind(value)
        except ValueError as exc:
            raise PathGovernanceError(
                f"invalid capability_kind: {value!r}",
                code=PathGovernanceErrorCode.INVALID_ENUM,
                field="capability_kind",
            ) from exc
    raise PathGovernanceError(
        "capability_kind must be a string or PathGovernanceCapabilityKind",
        code=PathGovernanceErrorCode.INVALID_ENUM,
        field="capability_kind",
    )


def _default_side_effects() -> PathGovernanceCliSideEffects:
    return build_path_governance_cli_side_effects()


def compute_path_governance_cli_request_id(
    *,
    command_kind: PathGovernanceCliCommandKind,
    output_format: PathGovernanceCliOutputFormat,
    include_events: bool,
    include_unavailable: bool,
    include_metadata: bool,
    source_label: ProjectionSourceLabel,
    metadata: Mapping[str, Any],
    schema_version: str,
) -> str:
    return stable_hash({
        "command_kind": command_kind.value,
        "include_events": include_events,
        "include_metadata": include_metadata,
        "include_unavailable": include_unavailable,
        "metadata": _sorted_metadata_dict(metadata),
        "output_format": output_format.value,
        "schema_version": schema_version,
        "source_label": source_label.value,
    })


def compute_path_governance_cli_line_id(
    *,
    level: PathGovernanceCliRenderLineLevel,
    text: str,
    state_label: ProjectionSourceLabel | None,
    capability_kind: PathGovernanceCapabilityKind | None,
    source_label: ProjectionSourceLabel,
    metadata: Mapping[str, Any],
    schema_version: str,
) -> str:
    return stable_hash({
        "capability_kind": None if capability_kind is None else capability_kind.value,
        "level": level.value,
        "metadata": _sorted_metadata_dict(metadata),
        "schema_version": schema_version,
        "source_label": source_label.value,
        "state_label": None if state_label is None else state_label.value,
        "text": text,
    })


def compute_path_governance_cli_response_id(
    *,
    request_id: str,
    command_kind: PathGovernanceCliCommandKind,
    output_format: PathGovernanceCliOutputFormat,
    binding_mode: PathGovernanceCliBindingMode,
    read_model_hash: str,
    envelope_hash: str,
    rendered_output: str,
    side_effects_hash: str,
    schema_version: str,
) -> str:
    return stable_hash({
        "binding_mode": binding_mode.value,
        "command_kind": command_kind.value,
        "envelope_hash": envelope_hash,
        "output_format": output_format.value,
        "read_model_hash": read_model_hash,
        "rendered_output": rendered_output,
        "request_id": request_id,
        "schema_version": schema_version,
        "side_effects_hash": side_effects_hash,
    })


@dataclass(frozen=True)
class PathGovernanceCliSideEffects:
    """Side-effect truth booleans; all remain false in P1.7.18."""

    policy_called: bool = False
    approval_created: bool = False
    ledger_written: bool = False
    global_trace_written: bool = False
    runtime_mutated: bool = False
    enforcement_triggered: bool = False
    source_mutated: bool = False
    prompt_filtered: bool = False
    memory_written: bool = False
    tool_blocked: bool = False
    side_effects_hash: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def to_canonical_dict(self, *, include_hash: bool = True) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "approval_created": self.approval_created,
            "enforcement_triggered": self.enforcement_triggered,
            "global_trace_written": self.global_trace_written,
            "ledger_written": self.ledger_written,
            "memory_written": self.memory_written,
            "metadata": _sorted_metadata_dict(self.metadata),
            "policy_called": self.policy_called,
            "prompt_filtered": self.prompt_filtered,
            "runtime_mutated": self.runtime_mutated,
            "source_mutated": self.source_mutated,
            "tool_blocked": self.tool_blocked,
        }
        if include_hash:
            payload["side_effects_hash"] = self.side_effects_hash
        return dict(sorted(payload.items(), key=lambda item: item[0]))

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> PathGovernanceCliSideEffects:
        validate_known_fields(
            data,
            PATH_GOVERNANCE_CLI_SIDE_EFFECTS_KNOWN_FIELDS,
            label="PathGovernanceCliSideEffects",
        )
        partial = cls(
            policy_called=bool(data.get("policy_called", False)),
            approval_created=bool(data.get("approval_created", False)),
            ledger_written=bool(data.get("ledger_written", False)),
            global_trace_written=bool(data.get("global_trace_written", False)),
            runtime_mutated=bool(data.get("runtime_mutated", False)),
            enforcement_triggered=bool(data.get("enforcement_triggered", False)),
            source_mutated=bool(data.get("source_mutated", False)),
            prompt_filtered=bool(data.get("prompt_filtered", False)),
            memory_written=bool(data.get("memory_written", False)),
            tool_blocked=bool(data.get("tool_blocked", False)),
            metadata=_freeze_metadata(data.get("metadata")),
        )
        side_effects_hash = stable_hash(partial.to_canonical_dict(include_hash=False))
        return cls(
            policy_called=partial.policy_called,
            approval_created=partial.approval_created,
            ledger_written=partial.ledger_written,
            global_trace_written=partial.global_trace_written,
            runtime_mutated=partial.runtime_mutated,
            enforcement_triggered=partial.enforcement_triggered,
            source_mutated=partial.source_mutated,
            prompt_filtered=partial.prompt_filtered,
            memory_written=partial.memory_written,
            tool_blocked=partial.tool_blocked,
            side_effects_hash=side_effects_hash,
            metadata=partial.metadata,
        )


def build_path_governance_cli_side_effects(
    *,
    metadata: Mapping[str, Any] | None = None,
) -> PathGovernanceCliSideEffects:
    """Build side-effect truth record with all flags false."""
    frozen_metadata = _freeze_metadata(metadata)
    partial = PathGovernanceCliSideEffects(metadata=frozen_metadata)
    side_effects_hash = stable_hash(partial.to_canonical_dict(include_hash=False))
    return PathGovernanceCliSideEffects(
        side_effects_hash=side_effects_hash,
        metadata=frozen_metadata,
    )


@dataclass(frozen=True)
class PathGovernanceCliRequest:
    """Read-only CLI request envelope."""

    request_id: str
    command_kind: PathGovernanceCliCommandKind
    output_format: PathGovernanceCliOutputFormat
    include_events: bool = True
    include_unavailable: bool = True
    include_metadata: bool = False
    source_label: ProjectionSourceLabel = ProjectionSourceLabel.LIVE
    request_hash: str = ""
    schema_version: str = PATH_GOVERNANCE_CLI_REQUEST_SCHEMA
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def to_canonical_dict(self, *, include_hash: bool = True) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "command_kind": self.command_kind.value,
            "include_events": self.include_events,
            "include_metadata": self.include_metadata,
            "include_unavailable": self.include_unavailable,
            "metadata": _sorted_metadata_dict(self.metadata),
            "output_format": self.output_format.value,
            "schema_version": self.schema_version,
            "source_label": self.source_label.value,
        }
        if include_hash:
            payload["request_hash"] = self.request_hash
            payload["request_id"] = self.request_id
        return dict(sorted(payload.items(), key=lambda item: item[0]))

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> PathGovernanceCliRequest:
        validate_known_fields(
            data,
            PATH_GOVERNANCE_CLI_REQUEST_KNOWN_FIELDS,
            label="PathGovernanceCliRequest",
        )
        parsed_source = _parse_source_label(
            data.get("source_label", ProjectionSourceLabel.LIVE),
        )
        partial = cls(
            request_id=str(data.get("request_id", "")),
            command_kind=_parse_command_kind(data["command_kind"]),
            output_format=_parse_output_format(data["output_format"]),
            include_events=bool(data.get("include_events", True)),
            include_unavailable=bool(data.get("include_unavailable", True)),
            include_metadata=bool(data.get("include_metadata", False)),
            source_label=parsed_source,
            schema_version=str(
                data.get("schema_version", PATH_GOVERNANCE_CLI_REQUEST_SCHEMA),
            ),
            metadata=_freeze_metadata(data.get("metadata")),
        )
        request_id = partial.request_id or compute_path_governance_cli_request_id(
            command_kind=partial.command_kind,
            output_format=partial.output_format,
            include_events=partial.include_events,
            include_unavailable=partial.include_unavailable,
            include_metadata=partial.include_metadata,
            source_label=partial.source_label,
            metadata=partial.metadata,
            schema_version=partial.schema_version,
        )
        partial_with_id = cls(
            request_id=request_id,
            command_kind=partial.command_kind,
            output_format=partial.output_format,
            include_events=partial.include_events,
            include_unavailable=partial.include_unavailable,
            include_metadata=partial.include_metadata,
            source_label=partial.source_label,
            schema_version=partial.schema_version,
            metadata=partial.metadata,
        )
        request_hash = stable_hash(partial_with_id.to_canonical_dict(include_hash=False))
        return cls(
            request_id=request_id,
            command_kind=partial.command_kind,
            output_format=partial.output_format,
            include_events=partial.include_events,
            include_unavailable=partial.include_unavailable,
            include_metadata=partial.include_metadata,
            source_label=partial.source_label,
            request_hash=request_hash,
            schema_version=partial.schema_version,
            metadata=partial.metadata,
        )


def build_path_governance_cli_request(
    command_kind: PathGovernanceCliCommandKind | str = (
        PathGovernanceCliCommandKind.STATUS
    ),
    output_format: PathGovernanceCliOutputFormat | str = (
        PathGovernanceCliOutputFormat.TEXT
    ),
    *,
    include_events: bool = True,
    include_unavailable: bool = True,
    include_metadata: bool = False,
    source_label: ProjectionSourceLabel | str | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> PathGovernanceCliRequest:
    """Build deterministic CLI request; no side effects."""
    parsed_command = _parse_command_kind(command_kind)
    parsed_format = _parse_output_format(output_format)
    parsed_source = (
        ProjectionSourceLabel.LIVE
        if source_label is None
        else _parse_source_label(source_label)
    )
    frozen_metadata = _freeze_metadata(metadata)
    request_id = compute_path_governance_cli_request_id(
        command_kind=parsed_command,
        output_format=parsed_format,
        include_events=include_events,
        include_unavailable=include_unavailable,
        include_metadata=include_metadata,
        source_label=parsed_source,
        metadata=frozen_metadata,
        schema_version=PATH_GOVERNANCE_CLI_REQUEST_SCHEMA,
    )
    partial = PathGovernanceCliRequest(
        request_id=request_id,
        command_kind=parsed_command,
        output_format=parsed_format,
        include_events=include_events,
        include_unavailable=include_unavailable,
        include_metadata=include_metadata,
        source_label=parsed_source,
        metadata=frozen_metadata,
    )
    request_hash = stable_hash(partial.to_canonical_dict(include_hash=False))
    return PathGovernanceCliRequest(
        request_id=request_id,
        command_kind=parsed_command,
        output_format=parsed_format,
        include_events=include_events,
        include_unavailable=include_unavailable,
        include_metadata=include_metadata,
        source_label=parsed_source,
        request_hash=request_hash,
        metadata=frozen_metadata,
    )


@dataclass(frozen=True)
class PathGovernanceCliRenderedLine:
    """Deterministic rendered CLI line."""

    line_id: str
    level: PathGovernanceCliRenderLineLevel
    text: str
    state_label: ProjectionSourceLabel | None = None
    capability_kind: PathGovernanceCapabilityKind | None = None
    source_label: ProjectionSourceLabel = ProjectionSourceLabel.LIVE
    line_hash: str = ""
    schema_version: str = PATH_GOVERNANCE_CLI_RENDERED_LINE_SCHEMA
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def to_canonical_dict(self, *, include_hash: bool = True) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "level": self.level.value,
            "metadata": _sorted_metadata_dict(self.metadata),
            "schema_version": self.schema_version,
            "source_label": self.source_label.value,
            "text": self.text,
        }
        if self.capability_kind is not None:
            payload["capability_kind"] = self.capability_kind.value
        if self.state_label is not None:
            payload["state_label"] = self.state_label.value
        if include_hash:
            payload["line_hash"] = self.line_hash
            payload["line_id"] = self.line_id
        return dict(sorted(payload.items(), key=lambda item: item[0]))

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> PathGovernanceCliRenderedLine:
        validate_known_fields(
            data,
            PATH_GOVERNANCE_CLI_RENDERED_LINE_KNOWN_FIELDS,
            label="PathGovernanceCliRenderedLine",
        )
        parsed_source = _parse_source_label(
            data.get("source_label", ProjectionSourceLabel.LIVE),
        )
        parsed_state = (
            None
            if data.get("state_label") is None
            else _parse_source_label(data["state_label"])
        )
        parsed_capability = _parse_capability_kind(data.get("capability_kind"))
        partial = cls(
            line_id=str(data.get("line_id", "")),
            level=_parse_line_level(data["level"]),
            text=str(data["text"]),
            state_label=parsed_state,
            capability_kind=parsed_capability,
            source_label=parsed_source,
            schema_version=str(
                data.get("schema_version", PATH_GOVERNANCE_CLI_RENDERED_LINE_SCHEMA),
            ),
            metadata=_freeze_metadata(data.get("metadata")),
        )
        line_id = partial.line_id or compute_path_governance_cli_line_id(
            level=partial.level,
            text=partial.text,
            state_label=partial.state_label,
            capability_kind=partial.capability_kind,
            source_label=partial.source_label,
            metadata=partial.metadata,
            schema_version=partial.schema_version,
        )
        partial_with_id = cls(
            line_id=line_id,
            level=partial.level,
            text=partial.text,
            state_label=partial.state_label,
            capability_kind=partial.capability_kind,
            source_label=partial.source_label,
            schema_version=partial.schema_version,
            metadata=partial.metadata,
        )
        line_hash = stable_hash(partial_with_id.to_canonical_dict(include_hash=False))
        return cls(
            line_id=line_id,
            level=partial.level,
            text=partial.text,
            state_label=partial.state_label,
            capability_kind=partial.capability_kind,
            source_label=partial.source_label,
            line_hash=line_hash,
            schema_version=partial.schema_version,
            metadata=partial.metadata,
        )


def _build_rendered_line(
    *,
    level: PathGovernanceCliRenderLineLevel,
    text: str,
    state_label: ProjectionSourceLabel | None = None,
    capability_kind: PathGovernanceCapabilityKind | None = None,
    source_label: ProjectionSourceLabel = ProjectionSourceLabel.LIVE,
    metadata: Mapping[str, Any] | None = None,
) -> PathGovernanceCliRenderedLine:
    frozen_metadata = _freeze_metadata(metadata)
    line_id = compute_path_governance_cli_line_id(
        level=level,
        text=text,
        state_label=state_label,
        capability_kind=capability_kind,
        source_label=source_label,
        metadata=frozen_metadata,
        schema_version=PATH_GOVERNANCE_CLI_RENDERED_LINE_SCHEMA,
    )
    partial = PathGovernanceCliRenderedLine(
        line_id=line_id,
        level=level,
        text=text,
        state_label=state_label,
        capability_kind=capability_kind,
        source_label=source_label,
        metadata=frozen_metadata,
    )
    line_hash = stable_hash(partial.to_canonical_dict(include_hash=False))
    return PathGovernanceCliRenderedLine(
        line_id=line_id,
        level=level,
        text=text,
        state_label=state_label,
        capability_kind=capability_kind,
        source_label=source_label,
        line_hash=line_hash,
        metadata=frozen_metadata,
    )


def _resolve_projection(
    *,
    read_model: PathGovernanceReadModel | None,
    api_envelope: PathGovernanceApiEnvelope | None,
    records: Sequence[PathGovernanceProjectionRecord] | None,
    source_label: ProjectionSourceLabel | None,
) -> tuple[PathGovernanceReadModel, PathGovernanceApiEnvelope]:
    if api_envelope is not None:
        effective_read_model = read_model or api_envelope.read_model
        return effective_read_model, api_envelope
    if read_model is not None:
        envelope = build_path_governance_api_envelope(
            read_model=read_model,
            records=records,
            source_label=source_label,
            cli_binding_available=True,
        )
        return read_model, envelope
    if records:
        read_model = build_path_governance_read_model(
            records,
            source_label=source_label,
        )
        envelope = build_path_governance_api_envelope(
            read_model=read_model,
            cli_binding_available=True,
        )
        return read_model, envelope
    envelope = build_default_path_governance_capability_projection(
        source_label=source_label,
        cli_binding_available=True,
    )
    return envelope.read_model, envelope


def _command_capability_kind(
    command_kind: PathGovernanceCliCommandKind,
) -> PathGovernanceCapabilityKind | None:
    mapping = {
        PathGovernanceCliCommandKind.HARNESS_SUMMARY: (
            PathGovernanceCapabilityKind.PATH_GOVERNANCE_TEST_HARNESS
        ),
        PathGovernanceCliCommandKind.POLICY_CONTEXT_SUMMARY: (
            PathGovernanceCapabilityKind.POLICY_CONTEXT_BRIDGE
        ),
        PathGovernanceCliCommandKind.TRACE_HOOK_SUMMARY: (
            PathGovernanceCapabilityKind.PATH_RESOLUTION_TRACE_HOOK
        ),
        PathGovernanceCliCommandKind.VIOLATION_DRIFT_SUMMARY: (
            PathGovernanceCapabilityKind.PATH_VIOLATION_DRIFT_TRACE_HOOK
        ),
    }
    return mapping.get(command_kind)


def _filter_records_for_command(
    command_kind: PathGovernanceCliCommandKind,
    records: Sequence[PathGovernanceProjectionRecord],
) -> tuple[PathGovernanceProjectionRecord, ...]:
    if command_kind is PathGovernanceCliCommandKind.UNAVAILABLE_BINDINGS:
        return tuple(
            record
            for record in records
            if record.state_label is ProjectionSourceLabel.UNAVAILABLE
        )
    capability = _command_capability_kind(command_kind)
    if capability is None:
        return tuple(records)
    return tuple(
        record for record in records if record.capability_kind is capability
    )


def _collect_unavailable_reasons(
    *,
    read_model: PathGovernanceReadModel,
    api_envelope: PathGovernanceApiEnvelope,
    include_unavailable: bool,
) -> list[dict[str, str]]:
    if not include_unavailable:
        return []
    reasons: list[dict[str, str]] = []
    for key in sorted(api_envelope.unavailable_bindings.keys()):
        binding = api_envelope.unavailable_bindings[key]
        reasons.append({
            "binding": key,
            "reason": str(binding.get("reason", "")),
            "status": str(binding.get("status", ProjectionSourceLabel.UNAVAILABLE.value)),
        })
    for record in read_model.records:
        if record.unavailable_reason:
            reasons.append({
                "binding": record.capability_kind.value,
                "reason": record.unavailable_reason,
                "status": record.state_label.value,
            })
    reasons.extend([
        {
            "binding": "shell_ui",
            "reason": SHELL_BINDING_UNAVAILABLE_REASON,
            "status": ProjectionSourceLabel.UNAVAILABLE.value,
        },
        {
            "binding": "http_server",
            "reason": HTTP_SERVER_UNAVAILABLE_REASON,
            "status": ProjectionSourceLabel.UNAVAILABLE.value,
        },
        {
            "binding": "policy_runtime",
            "reason": POLICY_RUNTIME_UNAVAILABLE_REASON,
            "status": ProjectionSourceLabel.UNAVAILABLE.value,
        },
        {
            "binding": "ledger_write",
            "reason": LEDGER_WRITE_UNAVAILABLE_REASON,
            "status": ProjectionSourceLabel.UNAVAILABLE.value,
        },
        {
            "binding": "enforcement",
            "reason": ENFORCEMENT_UNAVAILABLE_REASON,
            "status": ProjectionSourceLabel.UNAVAILABLE.value,
        },
    ])
    deduped: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for item in reasons:
        key = (item["binding"], item["reason"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return sorted(deduped, key=lambda item: (item["binding"], item["reason"]))


def render_path_governance_status_text(
    *,
    read_model: PathGovernanceReadModel | None = None,
    api_envelope: PathGovernanceApiEnvelope | None = None,
    include_unavailable: bool = True,
    include_metadata: bool = False,
) -> tuple[str, tuple[PathGovernanceCliRenderedLine, ...]]:
    """Render deterministic status text from projection read model."""
    effective_read_model, effective_envelope = _resolve_projection(
        read_model=read_model,
        api_envelope=api_envelope,
        records=None,
        source_label=None,
    )
    lines: list[PathGovernanceCliRenderedLine] = []
    header = _build_rendered_line(
        level=PathGovernanceCliRenderLineLevel.HEADER,
        text="Path Governance Projection Status",
        source_label=effective_read_model.source_label,
    )
    lines.append(header)
    lines.append(
        _build_rendered_line(
            level=PathGovernanceCliRenderLineLevel.INFO,
            text=(
                f"overall_state={effective_read_model.overall_state.value} "
                f"capability_count={effective_read_model.capability_count}"
            ),
            state_label=effective_read_model.overall_state,
            source_label=effective_read_model.source_label,
        ),
    )
    lines.append(
        _build_rendered_line(
            level=PathGovernanceCliRenderLineLevel.INFO,
            text=(
                f"live={effective_read_model.live_count} "
                f"trace_verified={effective_read_model.trace_verified_count} "
                f"simulated={effective_read_model.simulated_count} "
                f"dev_fixture={effective_read_model.dev_fixture_count} "
                f"unavailable={effective_read_model.unavailable_count} "
                f"error={effective_read_model.error_count}"
            ),
            source_label=effective_read_model.source_label,
        ),
    )
    lines.append(
        _build_rendered_line(
            level=PathGovernanceCliRenderLineLevel.INFO,
            text=(
                f"contract={effective_envelope.contract_name}/"
                f"{effective_envelope.contract_version}"
            ),
            source_label=effective_envelope.source_label,
        ),
    )
    if include_unavailable:
        unavailable = _collect_unavailable_reasons(
            read_model=effective_read_model,
            api_envelope=effective_envelope,
            include_unavailable=True,
        )
        if unavailable:
            lines.append(
                _build_rendered_line(
                    level=PathGovernanceCliRenderLineLevel.HEADER,
                    text="Unavailable bindings",
                    source_label=ProjectionSourceLabel.UNAVAILABLE,
                ),
            )
            for item in unavailable:
                lines.append(
                    _build_rendered_line(
                        level=PathGovernanceCliRenderLineLevel.WARN,
                        text=f"{item['binding']}: {item['reason']}",
                        state_label=ProjectionSourceLabel.UNAVAILABLE,
                        source_label=ProjectionSourceLabel.UNAVAILABLE,
                    ),
                )
    if include_metadata:
        lines.append(
            _build_rendered_line(
                level=PathGovernanceCliRenderLineLevel.INFO,
                text=f"read_model_hash={effective_read_model.read_model_hash}",
                source_label=effective_read_model.source_label,
            ),
        )
    rendered_output = "\n".join(line.text for line in lines)
    return rendered_output, tuple(lines)


def render_path_governance_capability_table(
    *,
    read_model: PathGovernanceReadModel | None = None,
    api_envelope: PathGovernanceApiEnvelope | None = None,
    include_unavailable: bool = True,
    records: Sequence[PathGovernanceProjectionRecord] | None = None,
) -> tuple[str, tuple[PathGovernanceCliRenderedLine, ...]]:
    """Render deterministic capability table from projection records."""
    effective_read_model, effective_envelope = _resolve_projection(
        read_model=read_model,
        api_envelope=api_envelope,
        records=records,
        source_label=None,
    )
    effective_records = records or effective_read_model.records
    lines: list[PathGovernanceCliRenderedLine] = []
    lines.append(
        _build_rendered_line(
            level=PathGovernanceCliRenderLineLevel.HEADER,
            text="capability_kind | state_label | source_label | summary",
            source_label=effective_read_model.source_label,
        ),
    )
    for record in sorted(effective_records, key=lambda item: item.capability_kind.value):
        if not include_unavailable and record.state_label is ProjectionSourceLabel.UNAVAILABLE:
            continue
        summary = record.summary
        if record.unavailable_reason:
            summary = f"{summary} | reason={record.unavailable_reason}"
        lines.append(
            _build_rendered_line(
                level=PathGovernanceCliRenderLineLevel.ROW,
                text=(
                    f"{record.capability_kind.value} | "
                    f"{record.state_label.value} | "
                    f"{record.source_label.value} | {summary}"
                ),
                state_label=record.state_label,
                capability_kind=record.capability_kind,
                source_label=record.source_label,
            ),
        )
    rendered_output = "\n".join(line.text for line in lines)
    return rendered_output, tuple(lines)


def render_path_governance_json_payload(
    *,
    read_model: PathGovernanceReadModel | None = None,
    api_envelope: PathGovernanceApiEnvelope | None = None,
    command_kind: PathGovernanceCliCommandKind | str = (
        PathGovernanceCliCommandKind.READ_MODEL
    ),
    include_events: bool = True,
    include_unavailable: bool = True,
    include_metadata: bool = False,
    records: Sequence[PathGovernanceProjectionRecord] | None = None,
) -> dict[str, Any]:
    """Render JSON-safe payload for CLI response."""
    parsed_command = _parse_command_kind(command_kind)
    effective_read_model, effective_envelope = _resolve_projection(
        read_model=read_model,
        api_envelope=api_envelope,
        records=records,
        source_label=None,
    )
    side_effects = _default_side_effects()
    payload: dict[str, Any] = {
        "binding_mode": PathGovernanceCliBindingMode.READ_ONLY.value,
        "command_kind": parsed_command.value,
        "created_by_task": PATH_GOVERNANCE_CLI_TASK_ID,
        "schema_version": PATH_GOVERNANCE_CLI_RESPONSE_SCHEMA,
        "side_effects": side_effects.to_canonical_dict(),
        "source_label": effective_read_model.source_label.value,
    }
    if parsed_command is PathGovernanceCliCommandKind.API_ENVELOPE:
        payload["api_envelope"] = effective_envelope.to_canonical_dict()
    elif parsed_command is PathGovernanceCliCommandKind.EVENTS:
        events = effective_envelope.events if include_events else ()
        payload["events"] = [
            event.to_canonical_dict() for event in events
        ]
    elif parsed_command is PathGovernanceCliCommandKind.UNAVAILABLE_BINDINGS:
        payload["unavailable_reasons"] = _collect_unavailable_reasons(
            read_model=effective_read_model,
            api_envelope=effective_envelope,
            include_unavailable=True,
        )
    else:
        filtered = _filter_records_for_command(
            parsed_command,
            effective_read_model.records,
        )
        if parsed_command in {
            PathGovernanceCliCommandKind.STATUS,
            PathGovernanceCliCommandKind.CAPABILITIES,
            PathGovernanceCliCommandKind.HARNESS_SUMMARY,
            PathGovernanceCliCommandKind.POLICY_CONTEXT_SUMMARY,
            PathGovernanceCliCommandKind.TRACE_HOOK_SUMMARY,
            PathGovernanceCliCommandKind.VIOLATION_DRIFT_SUMMARY,
        }:
            payload["records"] = [
                record.to_canonical_dict() for record in filtered
            ]
        payload["read_model"] = effective_read_model.to_canonical_dict()
        if parsed_command is PathGovernanceCliCommandKind.STATUS:
            payload["capability_count"] = effective_read_model.capability_count
            payload["overall_state"] = effective_read_model.overall_state.value
        if parsed_command is PathGovernanceCliCommandKind.READ_MODEL:
            payload["read_model"] = effective_read_model.to_canonical_dict()
    if include_unavailable and parsed_command is not PathGovernanceCliCommandKind.UNAVAILABLE_BINDINGS:
        payload["unavailable_reasons"] = _collect_unavailable_reasons(
            read_model=effective_read_model,
            api_envelope=effective_envelope,
            include_unavailable=True,
        )
    if include_metadata:
        payload["metadata"] = _sorted_metadata_dict(effective_envelope.metadata)
    return payload


def _render_tui_text(lines: Sequence[PathGovernanceCliRenderedLine]) -> str:
    width = max((len(line.text) for line in lines), default=40)
    width = max(width, 40)
    border = "+" + ("-" * (width + 2)) + "+"
    body_lines = [border]
    for line in lines:
        padded = line.text[:width].ljust(width)
        body_lines.append(f"| {padded} |")
    body_lines.append(border)
    return "\n".join(body_lines)


@dataclass(frozen=True)
class PathGovernanceCliResponse:
    """Read-only CLI response envelope."""

    response_id: str
    request_id: str
    command_kind: PathGovernanceCliCommandKind
    output_format: PathGovernanceCliOutputFormat
    binding_mode: PathGovernanceCliBindingMode
    read_model: PathGovernanceReadModel | None = None
    api_envelope: PathGovernanceApiEnvelope | None = None
    rendered_output: str = ""
    rendered_lines: tuple[PathGovernanceCliRenderedLine, ...] = ()
    json_payload: Mapping[str, Any] = field(default_factory=dict)
    unavailable_reasons: tuple[dict[str, str], ...] = ()
    side_effects: PathGovernanceCliSideEffects = field(
        default_factory=_default_side_effects,
    )
    source_label: ProjectionSourceLabel = ProjectionSourceLabel.LIVE
    schema_version: str = PATH_GOVERNANCE_CLI_RESPONSE_SCHEMA
    created_by_task: str = PATH_GOVERNANCE_CLI_TASK_ID
    response_hash: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def to_canonical_dict(self, *, include_hash: bool = True) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "binding_mode": self.binding_mode.value,
            "command_kind": self.command_kind.value,
            "created_by_task": self.created_by_task,
            "json_payload": _sorted_metadata_dict(self.json_payload)
            if isinstance(self.json_payload, MappingABC)
            else dict(self.json_payload),
            "metadata": _sorted_metadata_dict(self.metadata),
            "output_format": self.output_format.value,
            "rendered_lines": [
                line.to_canonical_dict() for line in self.rendered_lines
            ],
            "rendered_output": self.rendered_output,
            "request_id": self.request_id,
            "schema_version": self.schema_version,
            "side_effects": self.side_effects.to_canonical_dict(),
            "source_label": self.source_label.value,
            "unavailable_reasons": list(self.unavailable_reasons),
        }
        if self.read_model is not None:
            payload["read_model"] = self.read_model.to_canonical_dict()
        if self.api_envelope is not None:
            payload["api_envelope"] = self.api_envelope.to_canonical_dict()
        if include_hash:
            payload["response_hash"] = self.response_hash
            payload["response_id"] = self.response_id
        return dict(sorted(payload.items(), key=lambda item: item[0]))

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> PathGovernanceCliResponse:
        validate_known_fields(
            data,
            PATH_GOVERNANCE_CLI_RESPONSE_KNOWN_FIELDS,
            label="PathGovernanceCliResponse",
        )
        raw_read_model = data.get("read_model")
        read_model = (
            PathGovernanceReadModel.from_dict(raw_read_model)
            if isinstance(raw_read_model, MappingABC)
            else raw_read_model
        )
        raw_envelope = data.get("api_envelope")
        api_envelope = (
            PathGovernanceApiEnvelope.from_dict(raw_envelope)
            if isinstance(raw_envelope, MappingABC)
            else raw_envelope
        )
        raw_side_effects = data.get("side_effects", {})
        side_effects = (
            PathGovernanceCliSideEffects.from_dict(raw_side_effects)
            if isinstance(raw_side_effects, MappingABC)
            else raw_side_effects
        )
        raw_lines = data.get("rendered_lines", ())
        rendered_lines = tuple(
            PathGovernanceCliRenderedLine.from_dict(item)
            if isinstance(item, MappingABC)
            else item
            for item in raw_lines
        )
        partial = cls(
            response_id=str(data.get("response_id", "")),
            request_id=str(data["request_id"]),
            command_kind=_parse_command_kind(data["command_kind"]),
            output_format=_parse_output_format(data["output_format"]),
            binding_mode=_parse_binding_mode(
                data.get("binding_mode", PathGovernanceCliBindingMode.READ_ONLY),
            ),
            read_model=read_model,
            api_envelope=api_envelope,
            rendered_output=str(data.get("rendered_output", "")),
            rendered_lines=rendered_lines,
            json_payload=_freeze_metadata(data.get("json_payload")),
            unavailable_reasons=tuple(data.get("unavailable_reasons", ())),
            side_effects=side_effects,
            source_label=_parse_source_label(
                data.get("source_label", ProjectionSourceLabel.LIVE),
            ),
            schema_version=str(
                data.get("schema_version", PATH_GOVERNANCE_CLI_RESPONSE_SCHEMA),
            ),
            created_by_task=str(data.get("created_by_task", PATH_GOVERNANCE_CLI_TASK_ID)),
            metadata=_freeze_metadata(data.get("metadata")),
        )
        response_id = partial.response_id or compute_path_governance_cli_response_id(
            request_id=partial.request_id,
            command_kind=partial.command_kind,
            output_format=partial.output_format,
            binding_mode=partial.binding_mode,
            read_model_hash=(
                "" if partial.read_model is None else partial.read_model.read_model_hash
            ),
            envelope_hash=(
                "" if partial.api_envelope is None else partial.api_envelope.envelope_hash
            ),
            rendered_output=partial.rendered_output,
            side_effects_hash=partial.side_effects.side_effects_hash,
            schema_version=partial.schema_version,
        )
        partial_with_id = cls(
            response_id=response_id,
            request_id=partial.request_id,
            command_kind=partial.command_kind,
            output_format=partial.output_format,
            binding_mode=partial.binding_mode,
            read_model=partial.read_model,
            api_envelope=partial.api_envelope,
            rendered_output=partial.rendered_output,
            rendered_lines=partial.rendered_lines,
            json_payload=partial.json_payload,
            unavailable_reasons=partial.unavailable_reasons,
            side_effects=partial.side_effects,
            source_label=partial.source_label,
            schema_version=partial.schema_version,
            created_by_task=partial.created_by_task,
            metadata=partial.metadata,
        )
        response_hash = stable_hash(
            partial_with_id.to_canonical_dict(include_hash=False),
        )
        return cls(
            response_id=response_id,
            request_id=partial.request_id,
            command_kind=partial.command_kind,
            output_format=partial.output_format,
            binding_mode=partial.binding_mode,
            read_model=partial.read_model,
            api_envelope=partial.api_envelope,
            rendered_output=partial.rendered_output,
            rendered_lines=partial.rendered_lines,
            json_payload=partial.json_payload,
            unavailable_reasons=partial.unavailable_reasons,
            side_effects=partial.side_effects,
            source_label=partial.source_label,
            schema_version=partial.schema_version,
            created_by_task=partial.created_by_task,
            response_hash=response_hash,
            metadata=partial.metadata,
        )


def render_path_governance_cli_response(
    *,
    request: PathGovernanceCliRequest | None = None,
    read_model: PathGovernanceReadModel | None = None,
    api_envelope: PathGovernanceApiEnvelope | None = None,
    records: Sequence[PathGovernanceProjectionRecord] | None = None,
    source_label: ProjectionSourceLabel | str | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> PathGovernanceCliResponse:
    """Build CLI response from projection read model; no runtime side effects."""
    effective_request = request or build_path_governance_cli_request()
    parsed_source = (
        _parse_source_label(source_label)
        if source_label is not None
        else effective_request.source_label
    )
    effective_read_model, effective_envelope = _resolve_projection(
        read_model=read_model,
        api_envelope=api_envelope,
        records=records,
        source_label=parsed_source if source_label is not None else None,
    )
    if source_label is None:
        parsed_source = effective_read_model.source_label
    filtered_records = _filter_records_for_command(
        effective_request.command_kind,
        effective_read_model.records,
    )
    side_effects = _default_side_effects()
    unavailable_reasons = tuple(
        _collect_unavailable_reasons(
            read_model=effective_read_model,
            api_envelope=effective_envelope,
            include_unavailable=effective_request.include_unavailable,
        ),
    )
    json_payload = render_path_governance_json_payload(
        read_model=effective_read_model,
        api_envelope=effective_envelope,
        command_kind=effective_request.command_kind,
        include_events=effective_request.include_events,
        include_unavailable=effective_request.include_unavailable,
        include_metadata=effective_request.include_metadata,
        records=filtered_records if filtered_records else None,
    )
    rendered_output = ""
    rendered_lines: tuple[PathGovernanceCliRenderedLine, ...] = ()
    command = effective_request.command_kind
    output_format = effective_request.output_format

    if output_format is PathGovernanceCliOutputFormat.JSON:
        rendered_output = stable_hash(json_payload)
    elif command is PathGovernanceCliCommandKind.CAPABILITIES and output_format in {
        PathGovernanceCliOutputFormat.TABLE,
        PathGovernanceCliOutputFormat.TUI_TEXT,
    }:
        rendered_output, rendered_lines = render_path_governance_capability_table(
            read_model=effective_read_model,
            api_envelope=effective_envelope,
            include_unavailable=effective_request.include_unavailable,
            records=filtered_records or None,
        )
    elif command is PathGovernanceCliCommandKind.CAPABILITIES:
        rendered_output, rendered_lines = render_path_governance_capability_table(
            read_model=effective_read_model,
            api_envelope=effective_envelope,
            include_unavailable=effective_request.include_unavailable,
            records=filtered_records or None,
        )
    elif command is PathGovernanceCliCommandKind.UNAVAILABLE_BINDINGS:
        lines: list[PathGovernanceCliRenderedLine] = []
        for item in unavailable_reasons:
            lines.append(
                _build_rendered_line(
                    level=PathGovernanceCliRenderLineLevel.WARN,
                    text=f"{item['binding']}: {item['reason']}",
                    state_label=ProjectionSourceLabel.UNAVAILABLE,
                    source_label=ProjectionSourceLabel.UNAVAILABLE,
                ),
            )
        rendered_lines = tuple(lines)
        rendered_output = "\n".join(line.text for line in lines)
    elif command is PathGovernanceCliCommandKind.EVENTS:
        lines = []
        for event in effective_envelope.events:
            lines.append(
                _build_rendered_line(
                    level=PathGovernanceCliRenderLineLevel.INFO,
                    text=(
                        f"{event.event_kind.value} | "
                        f"{event.source_label.value} | {event.summary}"
                    ),
                    source_label=event.source_label,
                ),
            )
        rendered_lines = tuple(lines)
        rendered_output = "\n".join(line.text for line in lines)
    elif command in {
        PathGovernanceCliCommandKind.HARNESS_SUMMARY,
        PathGovernanceCliCommandKind.POLICY_CONTEXT_SUMMARY,
        PathGovernanceCliCommandKind.TRACE_HOOK_SUMMARY,
        PathGovernanceCliCommandKind.VIOLATION_DRIFT_SUMMARY,
    }:
        lines = []
        for record in filtered_records:
            text = (
                f"{record.capability_kind.value} | "
                f"{record.state_label.value} | {record.summary}"
            )
            if record.unavailable_reason:
                text = f"{text} | reason={record.unavailable_reason}"
            lines.append(
                _build_rendered_line(
                    level=PathGovernanceCliRenderLineLevel.INFO,
                    text=text,
                    state_label=record.state_label,
                    capability_kind=record.capability_kind,
                    source_label=record.source_label,
                ),
            )
        rendered_lines = tuple(lines)
        rendered_output = "\n".join(line.text for line in lines) or "no records"
    else:
        rendered_output, rendered_lines = render_path_governance_status_text(
            read_model=effective_read_model,
            api_envelope=effective_envelope,
            include_unavailable=effective_request.include_unavailable,
            include_metadata=effective_request.include_metadata,
        )

    if output_format is PathGovernanceCliOutputFormat.TUI_TEXT and rendered_lines:
        rendered_output = _render_tui_text(rendered_lines)

    response_id = compute_path_governance_cli_response_id(
        request_id=effective_request.request_id,
        command_kind=effective_request.command_kind,
        output_format=effective_request.output_format,
        binding_mode=PathGovernanceCliBindingMode.READ_ONLY,
        read_model_hash=effective_read_model.read_model_hash,
        envelope_hash=effective_envelope.envelope_hash,
        rendered_output=rendered_output,
        side_effects_hash=side_effects.side_effects_hash,
        schema_version=PATH_GOVERNANCE_CLI_RESPONSE_SCHEMA,
    )
    frozen_metadata = _freeze_metadata(metadata)
    partial = PathGovernanceCliResponse(
        response_id=response_id,
        request_id=effective_request.request_id,
        command_kind=effective_request.command_kind,
        output_format=effective_request.output_format,
        binding_mode=PathGovernanceCliBindingMode.READ_ONLY,
        read_model=effective_read_model,
        api_envelope=effective_envelope,
        rendered_output=rendered_output,
        rendered_lines=rendered_lines,
        json_payload=MappingProxyType(json_payload),
        unavailable_reasons=unavailable_reasons,
        side_effects=side_effects,
        source_label=parsed_source,
        metadata=frozen_metadata,
    )
    response_hash = stable_hash(partial.to_canonical_dict(include_hash=False))
    return PathGovernanceCliResponse(
        response_id=response_id,
        request_id=effective_request.request_id,
        command_kind=effective_request.command_kind,
        output_format=effective_request.output_format,
        binding_mode=PathGovernanceCliBindingMode.READ_ONLY,
        read_model=effective_read_model,
        api_envelope=effective_envelope,
        rendered_output=rendered_output,
        rendered_lines=rendered_lines,
        json_payload=MappingProxyType(json_payload),
        unavailable_reasons=unavailable_reasons,
        side_effects=side_effects,
        source_label=parsed_source,
        response_hash=response_hash,
        metadata=frozen_metadata,
    )


def handle_path_governance_cli_request(
    *,
    request: PathGovernanceCliRequest | None = None,
    command_kind: PathGovernanceCliCommandKind | str | None = None,
    output_format: PathGovernanceCliOutputFormat | str | None = None,
    read_model: PathGovernanceReadModel | None = None,
    api_envelope: PathGovernanceApiEnvelope | None = None,
    records: Sequence[PathGovernanceProjectionRecord] | None = None,
    source_label: ProjectionSourceLabel | str | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> PathGovernanceCliResponse:
    """Handle read-only CLI request; no policy, approval, Ledger, or runtime effects."""
    if request is None:
        request = build_path_governance_cli_request(
            command_kind=command_kind or PathGovernanceCliCommandKind.STATUS,
            output_format=output_format or PathGovernanceCliOutputFormat.TEXT,
            source_label=source_label,
        )
    elif command_kind is not None or output_format is not None:
        request = build_path_governance_cli_request(
            command_kind=command_kind or request.command_kind,
            output_format=output_format or request.output_format,
            include_events=request.include_events,
            include_unavailable=request.include_unavailable,
            include_metadata=request.include_metadata,
            source_label=source_label or request.source_label,
            metadata=metadata or request.metadata,
        )
    return render_path_governance_cli_response(
        request=request,
        read_model=read_model,
        api_envelope=api_envelope,
        records=records,
        source_label=source_label,
        metadata=metadata,
    )
