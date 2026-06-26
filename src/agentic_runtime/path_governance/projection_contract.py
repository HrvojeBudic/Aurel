"""Path Governance Projection/API/Event Contract (P1.7.17).

Deterministic, JSON-safe, hash-ready read-model for P1.7 path governance state.

Projection contract exposes state. It does not execute state.
API/event contract is not CLI binding. Read model is not source of truth.
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
from .serialization import stable_hash
from .validation import validate_known_fields

PATH_GOVERNANCE_PROJECTION_TASK_ID = "P1.7.17"
PATH_GOVERNANCE_PROJECTION_RECORD_SCHEMA = "path_governance_projection_record.v1"
PATH_GOVERNANCE_READ_MODEL_SCHEMA = "path_governance_read_model.v1"
PATH_GOVERNANCE_PROJECTION_EVENT_SCHEMA = "path_governance_projection_event.v1"
PATH_GOVERNANCE_API_ENVELOPE_CONTRACT_NAME = "path_governance_projection_api_event_contract"
PATH_GOVERNANCE_API_ENVELOPE_CONTRACT_VERSION = "v1"

CLI_TUI_BINDING_UNAVAILABLE_REASON = (
    "UNAVAILABLE: CLI/TUI binding begins in P1.7.18"
)
SHELL_BINDING_UNAVAILABLE_REASON = (
    "UNAVAILABLE: Shell binding not implemented in P1.7.17"
)
HTTP_SERVER_UNAVAILABLE_REASON = (
    "UNAVAILABLE: HTTP server not implemented in P1.7.17"
)
POLICY_RUNTIME_UNAVAILABLE_REASON = (
    "UNAVAILABLE: Policy runtime not called in P1.7.17"
)
LEDGER_WRITE_UNAVAILABLE_REASON = (
    "UNAVAILABLE: Ledger write not part of P1.7.17"
)

PATH_GOVERNANCE_PROJECTION_RECORD_KNOWN_FIELDS: frozenset[str] = frozenset({
    "record_id",
    "capability_kind",
    "state_label",
    "summary",
    "subject_refs",
    "unavailable_reason",
    "evidence_refs",
    "source_label",
    "schema_version",
    "created_by_task",
    "record_hash",
    "metadata",
})

PATH_GOVERNANCE_READ_MODEL_KNOWN_FIELDS: frozenset[str] = frozenset({
    "read_model_id",
    "records",
    "overall_state",
    "capability_count",
    "live_count",
    "trace_verified_count",
    "simulated_count",
    "dev_fixture_count",
    "unavailable_count",
    "error_count",
    "source_label",
    "schema_version",
    "created_by_task",
    "read_model_hash",
    "metadata",
})

PATH_GOVERNANCE_PROJECTION_EVENT_KNOWN_FIELDS: frozenset[str] = frozenset({
    "event_id",
    "event_kind",
    "record_refs",
    "read_model_ref",
    "summary",
    "source_label",
    "schema_version",
    "created_by_task",
    "event_hash",
    "metadata",
})

PATH_GOVERNANCE_API_ENVELOPE_KNOWN_FIELDS: frozenset[str] = frozenset({
    "envelope_id",
    "contract_name",
    "contract_version",
    "read_model",
    "events",
    "state_labels",
    "unavailable_bindings",
    "source_label",
    "envelope_hash",
    "metadata",
})

_SUPPORTED_STATE_LABELS: tuple[str, ...] = tuple(
    label.value for label in ProjectionSourceLabel
)


class PathGovernanceCapabilityKind(str, Enum):
    """P1.7 capability taxonomy for projection records."""

    PATH_GOVERNANCE_FOUNDATION = "PATH_GOVERNANCE_FOUNDATION"
    PATH_IDENTITY = "PATH_IDENTITY"
    SOURCE_IDENTITY = "SOURCE_IDENTITY"
    SOURCE_TRUST_TAXONOMY = "SOURCE_TRUST_TAXONOMY"
    TRUSTED_ROOT_REGISTRY = "TRUSTED_ROOT_REGISTRY"
    PATH_NORMALIZATION_ESCAPE_DETECTION = "PATH_NORMALIZATION_ESCAPE_DETECTION"
    PATH_AUTHORITY_SCOPE = "PATH_AUTHORITY_SCOPE"
    UNTRUSTED_CONTENT_BOUNDARY = "UNTRUSTED_CONTENT_BOUNDARY"
    SOURCE_PROVENANCE_EVIDENCE_BINDING = "SOURCE_PROVENANCE_EVIDENCE_BINDING"
    PATH_SOURCE_RISK_CLASSIFICATION = "PATH_SOURCE_RISK_CLASSIFICATION"
    PATH_GOVERNANCE_RESOLVER_SHADOW = "PATH_GOVERNANCE_RESOLVER_SHADOW"
    SOURCE_TRUST_RESOLVER_SHADOW = "SOURCE_TRUST_RESOLVER_SHADOW"
    CONFLICT_PRECEDENCE_SHADOW = "CONFLICT_PRECEDENCE_SHADOW"
    PATH_RESOLUTION_TRACE_HOOK = "PATH_RESOLUTION_TRACE_HOOK"
    PATH_VIOLATION_DRIFT_TRACE_HOOK = "PATH_VIOLATION_DRIFT_TRACE_HOOK"
    PATH_GOVERNANCE_TEST_HARNESS = "PATH_GOVERNANCE_TEST_HARNESS"
    POLICY_CONTEXT_BRIDGE = "POLICY_CONTEXT_BRIDGE"
    PROJECTION_API_EVENT_CONTRACT = "PROJECTION_API_EVENT_CONTRACT"
    CLI_TUI_BINDING = "CLI_TUI_BINDING"
    UNKNOWN = "UNKNOWN"


class PathGovernanceProjectionEventKind(str, Enum):
    """Projection event contract classification; not global trace emission."""

    CAPABILITY_PROJECTED = "CAPABILITY_PROJECTED"
    READ_MODEL_CREATED = "READ_MODEL_CREATED"
    POLICY_CONTEXT_PROJECTED = "POLICY_CONTEXT_PROJECTED"
    TRACE_HOOK_PROJECTED = "TRACE_HOOK_PROJECTED"
    VIOLATION_DRIFT_PROJECTED = "VIOLATION_DRIFT_PROJECTED"
    HARNESS_RESULT_PROJECTED = "HARNESS_RESULT_PROJECTED"
    CLI_BINDING_UNAVAILABLE = "CLI_BINDING_UNAVAILABLE"
    SHELL_BINDING_UNAVAILABLE = "SHELL_BINDING_UNAVAILABLE"
    POLICY_RUNTIME_UNAVAILABLE = "POLICY_RUNTIME_UNAVAILABLE"
    LEDGER_WRITE_UNAVAILABLE = "LEDGER_WRITE_UNAVAILABLE"
    UNKNOWN = "UNKNOWN"


_DEFAULT_CAPABILITY_ORDER: tuple[PathGovernanceCapabilityKind, ...] = (
    PathGovernanceCapabilityKind.PATH_GOVERNANCE_FOUNDATION,
    PathGovernanceCapabilityKind.PATH_IDENTITY,
    PathGovernanceCapabilityKind.SOURCE_IDENTITY,
    PathGovernanceCapabilityKind.SOURCE_TRUST_TAXONOMY,
    PathGovernanceCapabilityKind.TRUSTED_ROOT_REGISTRY,
    PathGovernanceCapabilityKind.PATH_NORMALIZATION_ESCAPE_DETECTION,
    PathGovernanceCapabilityKind.PATH_AUTHORITY_SCOPE,
    PathGovernanceCapabilityKind.UNTRUSTED_CONTENT_BOUNDARY,
    PathGovernanceCapabilityKind.SOURCE_PROVENANCE_EVIDENCE_BINDING,
    PathGovernanceCapabilityKind.PATH_SOURCE_RISK_CLASSIFICATION,
    PathGovernanceCapabilityKind.PATH_GOVERNANCE_RESOLVER_SHADOW,
    PathGovernanceCapabilityKind.SOURCE_TRUST_RESOLVER_SHADOW,
    PathGovernanceCapabilityKind.CONFLICT_PRECEDENCE_SHADOW,
    PathGovernanceCapabilityKind.PATH_RESOLUTION_TRACE_HOOK,
    PathGovernanceCapabilityKind.PATH_VIOLATION_DRIFT_TRACE_HOOK,
    PathGovernanceCapabilityKind.PATH_GOVERNANCE_TEST_HARNESS,
    PathGovernanceCapabilityKind.POLICY_CONTEXT_BRIDGE,
    PathGovernanceCapabilityKind.PROJECTION_API_EVENT_CONTRACT,
    PathGovernanceCapabilityKind.CLI_TUI_BINDING,
)

_DEFAULT_CAPABILITY_MODULES: dict[PathGovernanceCapabilityKind, str] = {
    PathGovernanceCapabilityKind.PATH_GOVERNANCE_FOUNDATION: (
        "agentic_runtime.path_governance.foundation"
    ),
    PathGovernanceCapabilityKind.PATH_IDENTITY: (
        "agentic_runtime.path_governance.path_identity"
    ),
    PathGovernanceCapabilityKind.SOURCE_IDENTITY: (
        "agentic_runtime.path_governance.source_identity"
    ),
    PathGovernanceCapabilityKind.SOURCE_TRUST_TAXONOMY: (
        "agentic_runtime.path_governance.source_trust_taxonomy"
    ),
    PathGovernanceCapabilityKind.TRUSTED_ROOT_REGISTRY: (
        "agentic_runtime.path_governance.trusted_roots"
    ),
    PathGovernanceCapabilityKind.PATH_NORMALIZATION_ESCAPE_DETECTION: (
        "agentic_runtime.path_governance.path_normalization"
    ),
    PathGovernanceCapabilityKind.PATH_AUTHORITY_SCOPE: (
        "agentic_runtime.path_governance.path_authority_scope"
    ),
    PathGovernanceCapabilityKind.UNTRUSTED_CONTENT_BOUNDARY: (
        "agentic_runtime.path_governance.untrusted_content_boundary"
    ),
    PathGovernanceCapabilityKind.SOURCE_PROVENANCE_EVIDENCE_BINDING: (
        "agentic_runtime.path_governance.source_provenance"
    ),
    PathGovernanceCapabilityKind.PATH_SOURCE_RISK_CLASSIFICATION: (
        "agentic_runtime.path_governance.risk_classification"
    ),
    PathGovernanceCapabilityKind.PATH_GOVERNANCE_RESOLVER_SHADOW: (
        "agentic_runtime.path_governance.path_resolver"
    ),
    PathGovernanceCapabilityKind.SOURCE_TRUST_RESOLVER_SHADOW: (
        "agentic_runtime.path_governance.source_trust_resolver"
    ),
    PathGovernanceCapabilityKind.CONFLICT_PRECEDENCE_SHADOW: (
        "agentic_runtime.path_governance.conflict_precedence"
    ),
    PathGovernanceCapabilityKind.PATH_RESOLUTION_TRACE_HOOK: (
        "agentic_runtime.path_governance.path_resolution_trace"
    ),
    PathGovernanceCapabilityKind.PATH_VIOLATION_DRIFT_TRACE_HOOK: (
        "agentic_runtime.path_governance.path_violation_trace"
    ),
    PathGovernanceCapabilityKind.PATH_GOVERNANCE_TEST_HARNESS: (
        "agentic_runtime.path_governance.test_harness"
    ),
    PathGovernanceCapabilityKind.POLICY_CONTEXT_BRIDGE: (
        "agentic_runtime.path_governance.policy_context_bridge"
    ),
    PathGovernanceCapabilityKind.PROJECTION_API_EVENT_CONTRACT: (
        "agentic_runtime.path_governance.projection_contract"
    ),
}


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


def _parse_capability_kind(
    value: PathGovernanceCapabilityKind | str,
) -> PathGovernanceCapabilityKind:
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


def _parse_event_kind(
    value: PathGovernanceProjectionEventKind | str,
) -> PathGovernanceProjectionEventKind:
    if isinstance(value, PathGovernanceProjectionEventKind):
        return value
    if isinstance(value, str):
        try:
            return PathGovernanceProjectionEventKind(value)
        except ValueError as exc:
            raise PathGovernanceError(
                f"invalid event_kind: {value!r}",
                code=PathGovernanceErrorCode.INVALID_ENUM,
                field="event_kind",
            ) from exc
    raise PathGovernanceError(
        "event_kind must be a string or PathGovernanceProjectionEventKind",
        code=PathGovernanceErrorCode.INVALID_ENUM,
        field="event_kind",
    )


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


def _normalize_ref_list(
    refs: Sequence[Mapping[str, Any] | str] | None,
) -> tuple[dict[str, str], ...]:
    if refs is None:
        return ()
    normalized: list[dict[str, str]] = []
    for item in refs:
        if isinstance(item, str):
            normalized.append({"ref": item})
        elif isinstance(item, MappingABC):
            normalized.append({
                str(key): str(value)
                for key, value in sorted(item.items(), key=lambda pair: str(pair[0]))
            })
        else:
            raise PathGovernanceValidationError(
                "subject_refs and evidence_refs must contain mappings or strings",
                code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
                field="refs",
            )
    return tuple(
        sorted(normalized, key=lambda ref: stable_hash(ref))
    )


def _sort_records(
    records: Sequence[PathGovernanceProjectionRecord],
) -> tuple[PathGovernanceProjectionRecord, ...]:
    return tuple(sorted(records, key=lambda record: record.capability_kind.value))


def _record_ref(record: PathGovernanceProjectionRecord) -> dict[str, str]:
    return {
        "record_hash": record.record_hash,
        "record_id": record.record_id,
    }


def _read_model_ref(read_model: PathGovernanceReadModel) -> dict[str, str]:
    return {
        "read_model_hash": read_model.read_model_hash,
        "read_model_id": read_model.read_model_id,
    }


def _compute_label_counts(
    records: Sequence[PathGovernanceProjectionRecord],
) -> dict[str, int]:
    counts = {
        "live": 0,
        "trace_verified": 0,
        "simulated": 0,
        "dev_fixture": 0,
        "unavailable": 0,
        "error": 0,
    }
    for record in records:
        label = record.state_label
        if label is ProjectionSourceLabel.LIVE:
            counts["live"] += 1
        elif label is ProjectionSourceLabel.TRACE_VERIFIED:
            counts["trace_verified"] += 1
        elif label is ProjectionSourceLabel.SIMULATED:
            counts["simulated"] += 1
        elif label is ProjectionSourceLabel.DEV_FIXTURE:
            counts["dev_fixture"] += 1
        elif label is ProjectionSourceLabel.UNAVAILABLE:
            counts["unavailable"] += 1
        elif label is ProjectionSourceLabel.ERROR:
            counts["error"] += 1
    return counts


def _compute_overall_state(
    records: Sequence[PathGovernanceProjectionRecord],
) -> ProjectionSourceLabel:
    if not records:
        return ProjectionSourceLabel.UNAVAILABLE
    counts = _compute_label_counts(records)
    if counts["error"] > 0:
        return ProjectionSourceLabel.ERROR
    if counts["live"] > 0:
        return ProjectionSourceLabel.LIVE
    if counts["trace_verified"] > 0:
        return ProjectionSourceLabel.TRACE_VERIFIED
    if counts["simulated"] > 0:
        return ProjectionSourceLabel.SIMULATED
    if counts["dev_fixture"] > 0 and counts["unavailable"] == 0:
        return ProjectionSourceLabel.DEV_FIXTURE
    if counts["unavailable"] == len(records):
        return ProjectionSourceLabel.UNAVAILABLE
    if counts["dev_fixture"] > 0:
        return ProjectionSourceLabel.DEV_FIXTURE
    return ProjectionSourceLabel.UNAVAILABLE


def compute_path_governance_projection_record_id(
    *,
    capability_kind: PathGovernanceCapabilityKind,
    state_label: ProjectionSourceLabel,
    subject_refs: Sequence[Mapping[str, Any] | str],
    evidence_refs: Sequence[Mapping[str, Any] | str],
    schema_version: str,
) -> str:
    return stable_hash({
        "capability_kind": capability_kind.value,
        "evidence_refs": _normalize_ref_list(evidence_refs),
        "schema_version": schema_version,
        "state_label": state_label.value,
        "subject_refs": _normalize_ref_list(subject_refs),
    })


def compute_path_governance_read_model_id(
    *,
    record_refs: Sequence[Mapping[str, str]],
    schema_version: str,
) -> str:
    return stable_hash({
        "record_refs": sorted(
            [
                {"record_hash": ref["record_hash"], "record_id": ref["record_id"]}
                for ref in record_refs
            ],
            key=lambda item: item["record_id"],
        ),
        "schema_version": schema_version,
    })


def compute_path_governance_projection_event_id(
    *,
    event_kind: PathGovernanceProjectionEventKind,
    record_refs: Sequence[Mapping[str, str]],
    read_model_ref: Mapping[str, str],
    schema_version: str,
) -> str:
    return stable_hash({
        "event_kind": event_kind.value,
        "read_model_ref": dict(sorted(read_model_ref.items())),
        "record_refs": sorted(
            [
                {"record_hash": ref["record_hash"], "record_id": ref["record_id"]}
                for ref in record_refs
            ],
            key=lambda item: item["record_id"],
        ),
        "schema_version": schema_version,
    })


def compute_path_governance_api_envelope_id(
    *,
    contract_name: str,
    contract_version: str,
    read_model_hash: str,
    event_hashes: Sequence[str],
    unavailable_bindings: Mapping[str, Any],
) -> str:
    return stable_hash({
        "contract_name": contract_name,
        "contract_version": contract_version,
        "event_hashes": sorted(event_hashes),
        "read_model_hash": read_model_hash,
        "unavailable_bindings": _sorted_metadata_dict(dict(unavailable_bindings)),
    })


@dataclass(frozen=True)
class PathGovernanceProjectionRecord:
    """Projection state card; not source of truth."""

    record_id: str
    capability_kind: PathGovernanceCapabilityKind
    state_label: ProjectionSourceLabel
    summary: str
    subject_refs: tuple[dict[str, str], ...] = ()
    unavailable_reason: str | None = None
    evidence_refs: tuple[dict[str, str], ...] = ()
    source_label: ProjectionSourceLabel = ProjectionSourceLabel.LIVE
    schema_version: str = PATH_GOVERNANCE_PROJECTION_RECORD_SCHEMA
    created_by_task: str = PATH_GOVERNANCE_PROJECTION_TASK_ID
    record_hash: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.state_label is ProjectionSourceLabel.UNAVAILABLE:
            if not self.unavailable_reason or not self.unavailable_reason.strip():
                raise PathGovernanceValidationError(
                    "UNAVAILABLE projection record requires unavailable_reason",
                    code=PathGovernanceErrorCode.PATH_GOVERNANCE_UNAVAILABLE,
                    field="unavailable_reason",
                )

    def to_canonical_dict(self, *, include_hash: bool = True) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "capability_kind": self.capability_kind.value,
            "created_by_task": self.created_by_task,
            "evidence_refs": list(self.evidence_refs),
            "metadata": _sorted_metadata_dict(self.metadata),
            "schema_version": self.schema_version,
            "source_label": self.source_label.value,
            "state_label": self.state_label.value,
            "subject_refs": list(self.subject_refs),
            "summary": self.summary,
        }
        if self.unavailable_reason is not None:
            payload["unavailable_reason"] = self.unavailable_reason
        if include_hash:
            payload["record_hash"] = self.record_hash
            payload["record_id"] = self.record_id
        return dict(sorted(payload.items(), key=lambda item: item[0]))

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> PathGovernanceProjectionRecord:
        validate_known_fields(
            data,
            PATH_GOVERNANCE_PROJECTION_RECORD_KNOWN_FIELDS,
            label="PathGovernanceProjectionRecord",
        )
        return cls(
            record_id=str(data["record_id"]),
            capability_kind=_parse_capability_kind(data["capability_kind"]),
            state_label=_parse_source_label(data["state_label"]),
            summary=str(data["summary"]),
            subject_refs=_normalize_ref_list(data.get("subject_refs")),
            unavailable_reason=data.get("unavailable_reason"),
            evidence_refs=_normalize_ref_list(data.get("evidence_refs")),
            source_label=_parse_source_label(
                data.get("source_label", ProjectionSourceLabel.LIVE),
            ),
            schema_version=str(
                data.get("schema_version", PATH_GOVERNANCE_PROJECTION_RECORD_SCHEMA),
            ),
            created_by_task=str(
                data.get("created_by_task", PATH_GOVERNANCE_PROJECTION_TASK_ID),
            ),
            record_hash=str(data.get("record_hash", "")),
            metadata=_freeze_metadata(data.get("metadata")),
        )


@dataclass(frozen=True)
class PathGovernanceReadModel:
    """Aggregated projection read model; not source of truth."""

    read_model_id: str
    records: tuple[PathGovernanceProjectionRecord, ...]
    overall_state: ProjectionSourceLabel
    capability_count: int
    live_count: int
    trace_verified_count: int
    simulated_count: int
    dev_fixture_count: int
    unavailable_count: int
    error_count: int
    source_label: ProjectionSourceLabel = ProjectionSourceLabel.LIVE
    schema_version: str = PATH_GOVERNANCE_READ_MODEL_SCHEMA
    created_by_task: str = PATH_GOVERNANCE_PROJECTION_TASK_ID
    read_model_hash: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def to_canonical_dict(self, *, include_hash: bool = True) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "capability_count": self.capability_count,
            "created_by_task": self.created_by_task,
            "dev_fixture_count": self.dev_fixture_count,
            "error_count": self.error_count,
            "live_count": self.live_count,
            "metadata": _sorted_metadata_dict(self.metadata),
            "overall_state": self.overall_state.value,
            "records": [
                record.to_canonical_dict(include_hash=True)
                for record in self.records
            ],
            "schema_version": self.schema_version,
            "simulated_count": self.simulated_count,
            "source_label": self.source_label.value,
            "trace_verified_count": self.trace_verified_count,
            "unavailable_count": self.unavailable_count,
        }
        if include_hash:
            payload["read_model_hash"] = self.read_model_hash
            payload["read_model_id"] = self.read_model_id
        return dict(sorted(payload.items(), key=lambda item: item[0]))

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> PathGovernanceReadModel:
        validate_known_fields(
            data,
            PATH_GOVERNANCE_READ_MODEL_KNOWN_FIELDS,
            label="PathGovernanceReadModel",
        )
        raw_records = data.get("records", ())
        records = tuple(
            PathGovernanceProjectionRecord.from_dict(item)
            if isinstance(item, MappingABC)
            else item
            for item in raw_records
        )
        return cls(
            read_model_id=str(data["read_model_id"]),
            records=records,
            overall_state=_parse_source_label(data["overall_state"]),
            capability_count=int(data["capability_count"]),
            live_count=int(data["live_count"]),
            trace_verified_count=int(data["trace_verified_count"]),
            simulated_count=int(data["simulated_count"]),
            dev_fixture_count=int(data["dev_fixture_count"]),
            unavailable_count=int(data["unavailable_count"]),
            error_count=int(data["error_count"]),
            source_label=_parse_source_label(
                data.get("source_label", ProjectionSourceLabel.LIVE),
            ),
            schema_version=str(
                data.get("schema_version", PATH_GOVERNANCE_READ_MODEL_SCHEMA),
            ),
            created_by_task=str(
                data.get("created_by_task", PATH_GOVERNANCE_PROJECTION_TASK_ID),
            ),
            read_model_hash=str(data.get("read_model_hash", "")),
            metadata=_freeze_metadata(data.get("metadata")),
        )


@dataclass(frozen=True)
class PathGovernanceProjectionEvent:
    """Event contract object; not global trace emission."""

    event_id: str
    event_kind: PathGovernanceProjectionEventKind
    record_refs: tuple[dict[str, str], ...] = ()
    read_model_ref: Mapping[str, str] = field(default_factory=dict)
    summary: str = ""
    source_label: ProjectionSourceLabel = ProjectionSourceLabel.LIVE
    schema_version: str = PATH_GOVERNANCE_PROJECTION_EVENT_SCHEMA
    created_by_task: str = PATH_GOVERNANCE_PROJECTION_TASK_ID
    event_hash: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def to_canonical_dict(self, *, include_hash: bool = True) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "created_by_task": self.created_by_task,
            "event_kind": self.event_kind.value,
            "metadata": _sorted_metadata_dict(self.metadata),
            "read_model_ref": dict(sorted(self.read_model_ref.items())),
            "record_refs": list(self.record_refs),
            "schema_version": self.schema_version,
            "source_label": self.source_label.value,
            "summary": self.summary,
        }
        if include_hash:
            payload["event_hash"] = self.event_hash
            payload["event_id"] = self.event_id
        return dict(sorted(payload.items(), key=lambda item: item[0]))

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> PathGovernanceProjectionEvent:
        validate_known_fields(
            data,
            PATH_GOVERNANCE_PROJECTION_EVENT_KNOWN_FIELDS,
            label="PathGovernanceProjectionEvent",
        )
        raw_refs = data.get("record_refs", ())
        record_refs = tuple(
            {
                str(key): str(value)
                for key, value in sorted(item.items(), key=lambda pair: str(pair[0]))
            }
            for item in raw_refs
        )
        raw_read_model_ref = data.get("read_model_ref", {})
        read_model_ref = {
            str(key): str(value)
            for key, value in sorted(raw_read_model_ref.items(), key=lambda pair: str(pair[0]))
        }
        return cls(
            event_id=str(data["event_id"]),
            event_kind=_parse_event_kind(data["event_kind"]),
            record_refs=record_refs,
            read_model_ref=read_model_ref,
            summary=str(data.get("summary", "")),
            source_label=_parse_source_label(
                data.get("source_label", ProjectionSourceLabel.LIVE),
            ),
            schema_version=str(
                data.get("schema_version", PATH_GOVERNANCE_PROJECTION_EVENT_SCHEMA),
            ),
            created_by_task=str(
                data.get("created_by_task", PATH_GOVERNANCE_PROJECTION_TASK_ID),
            ),
            event_hash=str(data.get("event_hash", "")),
            metadata=_freeze_metadata(data.get("metadata")),
        )


@dataclass(frozen=True)
class PathGovernanceApiEnvelope:
    """API-ready envelope object; not an HTTP server."""

    envelope_id: str
    contract_name: str = PATH_GOVERNANCE_API_ENVELOPE_CONTRACT_NAME
    contract_version: str = PATH_GOVERNANCE_API_ENVELOPE_CONTRACT_VERSION
    read_model: PathGovernanceReadModel | None = None
    events: tuple[PathGovernanceProjectionEvent, ...] = ()
    state_labels: tuple[str, ...] = _SUPPORTED_STATE_LABELS
    unavailable_bindings: Mapping[str, Any] = field(default_factory=dict)
    source_label: ProjectionSourceLabel = ProjectionSourceLabel.LIVE
    envelope_hash: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def to_canonical_dict(self, *, include_hash: bool = True) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "contract_name": self.contract_name,
            "contract_version": self.contract_version,
            "events": [
                event.to_canonical_dict(include_hash=True)
                for event in self.events
            ],
            "metadata": _sorted_metadata_dict(self.metadata),
            "source_label": self.source_label.value,
            "state_labels": list(self.state_labels),
            "unavailable_bindings": _sorted_metadata_dict(dict(self.unavailable_bindings)),
        }
        if self.read_model is not None:
            payload["read_model"] = self.read_model.to_canonical_dict(include_hash=True)
        if include_hash:
            payload["envelope_hash"] = self.envelope_hash
            payload["envelope_id"] = self.envelope_id
        return dict(sorted(payload.items(), key=lambda item: item[0]))

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> PathGovernanceApiEnvelope:
        validate_known_fields(
            data,
            PATH_GOVERNANCE_API_ENVELOPE_KNOWN_FIELDS,
            label="PathGovernanceApiEnvelope",
        )
        raw_read_model = data.get("read_model")
        read_model = (
            PathGovernanceReadModel.from_dict(raw_read_model)
            if isinstance(raw_read_model, MappingABC)
            else raw_read_model
        )
        raw_events = data.get("events", ())
        events = tuple(
            PathGovernanceProjectionEvent.from_dict(item)
            if isinstance(item, MappingABC)
            else item
            for item in raw_events
        )
        return cls(
            envelope_id=str(data["envelope_id"]),
            contract_name=str(
                data.get("contract_name", PATH_GOVERNANCE_API_ENVELOPE_CONTRACT_NAME),
            ),
            contract_version=str(
                data.get("contract_version", PATH_GOVERNANCE_API_ENVELOPE_CONTRACT_VERSION),
            ),
            read_model=read_model,
            events=events,
            state_labels=tuple(data.get("state_labels", _SUPPORTED_STATE_LABELS)),
            unavailable_bindings=_freeze_metadata(data.get("unavailable_bindings")),
            source_label=_parse_source_label(
                data.get("source_label", ProjectionSourceLabel.LIVE),
            ),
            envelope_hash=str(data.get("envelope_hash", "")),
            metadata=_freeze_metadata(data.get("metadata")),
        )


def _compute_record_hash(record: PathGovernanceProjectionRecord) -> str:
    return stable_hash(record.to_canonical_dict(include_hash=False))


def _compute_read_model_hash(read_model: PathGovernanceReadModel) -> str:
    return stable_hash(read_model.to_canonical_dict(include_hash=False))


def _compute_event_hash(event: PathGovernanceProjectionEvent) -> str:
    return stable_hash(event.to_canonical_dict(include_hash=False))


def _compute_envelope_hash(envelope: PathGovernanceApiEnvelope) -> str:
    return stable_hash(envelope.to_canonical_dict(include_hash=False))


def _default_unavailable_bindings() -> dict[str, dict[str, str]]:
    return {
        "cli_tui": {
            "reason": CLI_TUI_BINDING_UNAVAILABLE_REASON,
            "status": ProjectionSourceLabel.UNAVAILABLE.value,
        },
        "http_server": {
            "reason": HTTP_SERVER_UNAVAILABLE_REASON,
            "status": ProjectionSourceLabel.UNAVAILABLE.value,
        },
        "ledger_write": {
            "reason": LEDGER_WRITE_UNAVAILABLE_REASON,
            "status": ProjectionSourceLabel.UNAVAILABLE.value,
        },
        "policy_runtime": {
            "reason": POLICY_RUNTIME_UNAVAILABLE_REASON,
            "status": ProjectionSourceLabel.UNAVAILABLE.value,
        },
        "shell": {
            "reason": SHELL_BINDING_UNAVAILABLE_REASON,
            "status": ProjectionSourceLabel.UNAVAILABLE.value,
        },
    }


def build_path_governance_projection_record(
    capability_kind: PathGovernanceCapabilityKind | str,
    state_label: ProjectionSourceLabel | str,
    summary: str,
    *,
    subject_refs: Sequence[Mapping[str, Any] | str] | None = None,
    unavailable_reason: str | None = None,
    evidence_refs: Sequence[Mapping[str, Any] | str] | None = None,
    source_label: ProjectionSourceLabel | str | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> PathGovernanceProjectionRecord:
    """Build a projection record; does not mutate runtime or emit trace."""
    parsed_kind = _parse_capability_kind(capability_kind)
    parsed_state = _parse_source_label(state_label)
    parsed_source = (
        parsed_state
        if source_label is None
        else _parse_source_label(source_label)
    )
    normalized_subject_refs = _normalize_ref_list(subject_refs)
    normalized_evidence_refs = _normalize_ref_list(evidence_refs)
    frozen_metadata = _freeze_metadata(metadata)

    record_id = compute_path_governance_projection_record_id(
        capability_kind=parsed_kind,
        state_label=parsed_state,
        subject_refs=normalized_subject_refs,
        evidence_refs=normalized_evidence_refs,
        schema_version=PATH_GOVERNANCE_PROJECTION_RECORD_SCHEMA,
    )

    partial = PathGovernanceProjectionRecord(
        record_id=record_id,
        capability_kind=parsed_kind,
        state_label=parsed_state,
        summary=summary,
        subject_refs=normalized_subject_refs,
        unavailable_reason=unavailable_reason,
        evidence_refs=normalized_evidence_refs,
        source_label=parsed_source,
        metadata=frozen_metadata,
    )
    record_hash = _compute_record_hash(partial)
    return PathGovernanceProjectionRecord(
        record_id=record_id,
        capability_kind=parsed_kind,
        state_label=parsed_state,
        summary=summary,
        subject_refs=normalized_subject_refs,
        unavailable_reason=unavailable_reason,
        evidence_refs=normalized_evidence_refs,
        source_label=parsed_source,
        metadata=frozen_metadata,
        record_hash=record_hash,
    )


def build_path_governance_read_model(
    records: Sequence[PathGovernanceProjectionRecord],
    *,
    source_label: ProjectionSourceLabel | str | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> PathGovernanceReadModel:
    """Build aggregated read model from projection records."""
    sorted_records = _sort_records(records)
    counts = _compute_label_counts(sorted_records)
    overall_state = _compute_overall_state(sorted_records)
    parsed_source = (
        overall_state
        if source_label is None
        else _parse_source_label(source_label)
    )
    frozen_metadata = _freeze_metadata(metadata)
    record_refs = [_record_ref(record) for record in sorted_records]

    read_model_id = compute_path_governance_read_model_id(
        record_refs=record_refs,
        schema_version=PATH_GOVERNANCE_READ_MODEL_SCHEMA,
    )

    partial = PathGovernanceReadModel(
        read_model_id=read_model_id,
        records=sorted_records,
        overall_state=overall_state,
        capability_count=len(sorted_records),
        live_count=counts["live"],
        trace_verified_count=counts["trace_verified"],
        simulated_count=counts["simulated"],
        dev_fixture_count=counts["dev_fixture"],
        unavailable_count=counts["unavailable"],
        error_count=counts["error"],
        source_label=parsed_source,
        metadata=frozen_metadata,
    )
    read_model_hash = _compute_read_model_hash(partial)
    return PathGovernanceReadModel(
        read_model_id=read_model_id,
        records=sorted_records,
        overall_state=overall_state,
        capability_count=len(sorted_records),
        live_count=counts["live"],
        trace_verified_count=counts["trace_verified"],
        simulated_count=counts["simulated"],
        dev_fixture_count=counts["dev_fixture"],
        unavailable_count=counts["unavailable"],
        error_count=counts["error"],
        source_label=parsed_source,
        read_model_hash=read_model_hash,
        metadata=frozen_metadata,
    )


def build_path_governance_projection_event(
    event_kind: PathGovernanceProjectionEventKind | str,
    *,
    records: Sequence[PathGovernanceProjectionRecord] | None = None,
    read_model: PathGovernanceReadModel | None = None,
    summary: str | None = None,
    source_label: ProjectionSourceLabel | str | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> PathGovernanceProjectionEvent:
    """Build projection event contract object; does not emit global trace."""
    parsed_kind = _parse_event_kind(event_kind)
    record_list = list(records or ())
    record_refs = tuple(_record_ref(record) for record in record_list)
    read_model_ref = _read_model_ref(read_model) if read_model is not None else {}
    parsed_source = (
        ProjectionSourceLabel.LIVE
        if source_label is None
        else _parse_source_label(source_label)
    )
    frozen_metadata = _freeze_metadata(metadata)
    event_summary = summary or f"projection event {parsed_kind.value}"

    event_id = compute_path_governance_projection_event_id(
        event_kind=parsed_kind,
        record_refs=record_refs,
        read_model_ref=read_model_ref,
        schema_version=PATH_GOVERNANCE_PROJECTION_EVENT_SCHEMA,
    )

    partial = PathGovernanceProjectionEvent(
        event_id=event_id,
        event_kind=parsed_kind,
        record_refs=record_refs,
        read_model_ref=read_model_ref,
        summary=event_summary,
        source_label=parsed_source,
        metadata=frozen_metadata,
    )
    event_hash = _compute_event_hash(partial)
    return PathGovernanceProjectionEvent(
        event_id=event_id,
        event_kind=parsed_kind,
        record_refs=record_refs,
        read_model_ref=read_model_ref,
        summary=event_summary,
        source_label=parsed_source,
        event_hash=event_hash,
        metadata=frozen_metadata,
    )


def _default_projection_events(
    *,
    records: Sequence[PathGovernanceProjectionRecord],
    read_model: PathGovernanceReadModel,
    source_label: ProjectionSourceLabel,
) -> tuple[PathGovernanceProjectionEvent, ...]:
    events = [
        build_path_governance_projection_event(
            PathGovernanceProjectionEventKind.READ_MODEL_CREATED,
            records=records,
            read_model=read_model,
            summary="path governance read model created",
            source_label=source_label,
        ),
        build_path_governance_projection_event(
            PathGovernanceProjectionEventKind.CLI_BINDING_UNAVAILABLE,
            summary=CLI_TUI_BINDING_UNAVAILABLE_REASON,
            source_label=ProjectionSourceLabel.UNAVAILABLE,
        ),
        build_path_governance_projection_event(
            PathGovernanceProjectionEventKind.SHELL_BINDING_UNAVAILABLE,
            summary=SHELL_BINDING_UNAVAILABLE_REASON,
            source_label=ProjectionSourceLabel.UNAVAILABLE,
        ),
        build_path_governance_projection_event(
            PathGovernanceProjectionEventKind.POLICY_RUNTIME_UNAVAILABLE,
            summary=POLICY_RUNTIME_UNAVAILABLE_REASON,
            source_label=ProjectionSourceLabel.UNAVAILABLE,
        ),
        build_path_governance_projection_event(
            PathGovernanceProjectionEventKind.LEDGER_WRITE_UNAVAILABLE,
            summary=LEDGER_WRITE_UNAVAILABLE_REASON,
            source_label=ProjectionSourceLabel.UNAVAILABLE,
        ),
    ]
    for record in records:
        if record.capability_kind is PathGovernanceCapabilityKind.POLICY_CONTEXT_BRIDGE:
            events.append(
                build_path_governance_projection_event(
                    PathGovernanceProjectionEventKind.POLICY_CONTEXT_PROJECTED,
                    records=[record],
                    read_model=read_model,
                    summary="policy context bridge projected",
                    source_label=source_label,
                ),
            )
        elif record.capability_kind is PathGovernanceCapabilityKind.PATH_RESOLUTION_TRACE_HOOK:
            events.append(
                build_path_governance_projection_event(
                    PathGovernanceProjectionEventKind.TRACE_HOOK_PROJECTED,
                    records=[record],
                    read_model=read_model,
                    summary="path resolution trace hook projected",
                    source_label=source_label,
                ),
            )
        elif record.capability_kind is PathGovernanceCapabilityKind.PATH_VIOLATION_DRIFT_TRACE_HOOK:
            events.append(
                build_path_governance_projection_event(
                    PathGovernanceProjectionEventKind.VIOLATION_DRIFT_PROJECTED,
                    records=[record],
                    read_model=read_model,
                    summary="violation drift trace hook projected",
                    source_label=source_label,
                ),
            )
        elif record.capability_kind is PathGovernanceCapabilityKind.PATH_GOVERNANCE_TEST_HARNESS:
            events.append(
                build_path_governance_projection_event(
                    PathGovernanceProjectionEventKind.HARNESS_RESULT_PROJECTED,
                    records=[record],
                    read_model=read_model,
                    summary="path governance harness projected",
                    source_label=source_label,
                ),
            )
        else:
            events.append(
                build_path_governance_projection_event(
                    PathGovernanceProjectionEventKind.CAPABILITY_PROJECTED,
                    records=[record],
                    read_model=read_model,
                    summary=f"{record.capability_kind.value} projected",
                    source_label=record.source_label,
                ),
            )
    return tuple(events)


def build_path_governance_api_envelope(
    *,
    read_model: PathGovernanceReadModel | None = None,
    events: Sequence[PathGovernanceProjectionEvent] | None = None,
    records: Sequence[PathGovernanceProjectionRecord] | None = None,
    unavailable_bindings: Mapping[str, Any] | None = None,
    source_label: ProjectionSourceLabel | str | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> PathGovernanceApiEnvelope:
    """Build API envelope object; does not start HTTP server or CLI."""
    effective_records = list(records or ())
    if read_model is None:
        if not effective_records:
            raise PathGovernanceValidationError(
                "read_model or records required to build API envelope",
                code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
                field="read_model",
            )
        read_model = build_path_governance_read_model(
            effective_records,
            source_label=source_label,
            metadata=metadata,
        )
    parsed_source = read_model.source_label if source_label is None else _parse_source_label(source_label)
    frozen_metadata = _freeze_metadata(metadata)
    bindings = _default_unavailable_bindings()
    if unavailable_bindings:
        bindings.update(dict(unavailable_bindings))

    effective_events = tuple(events) if events is not None else _default_projection_events(
        records=read_model.records,
        read_model=read_model,
        source_label=parsed_source,
    )

    envelope_id = compute_path_governance_api_envelope_id(
        contract_name=PATH_GOVERNANCE_API_ENVELOPE_CONTRACT_NAME,
        contract_version=PATH_GOVERNANCE_API_ENVELOPE_CONTRACT_VERSION,
        read_model_hash=read_model.read_model_hash,
        event_hashes=[event.event_hash for event in effective_events],
        unavailable_bindings=bindings,
    )

    partial = PathGovernanceApiEnvelope(
        envelope_id=envelope_id,
        read_model=read_model,
        events=effective_events,
        unavailable_bindings=MappingProxyType(bindings),
        source_label=parsed_source,
        metadata=frozen_metadata,
    )
    envelope_hash = _compute_envelope_hash(partial)
    return PathGovernanceApiEnvelope(
        envelope_id=envelope_id,
        read_model=read_model,
        events=effective_events,
        unavailable_bindings=MappingProxyType(bindings),
        source_label=parsed_source,
        envelope_hash=envelope_hash,
        metadata=frozen_metadata,
    )


def _default_capability_summary(kind: PathGovernanceCapabilityKind) -> str:
    if kind is PathGovernanceCapabilityKind.CLI_TUI_BINDING:
        return "CLI/TUI binding unavailable until P1.7.18"
    module = _DEFAULT_CAPABILITY_MODULES.get(kind, "")
    if module:
        return f"Backend capability available via {module}"
    return f"Capability {kind.value}"


def build_default_path_governance_capability_projection(
    *,
    source_label: ProjectionSourceLabel | str | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> PathGovernanceApiEnvelope:
    """Build default P1.7.0–P1.7.17 capability projection envelope."""
    parsed_source = (
        ProjectionSourceLabel.LIVE
        if source_label is None
        else _parse_source_label(source_label)
    )
    records: list[PathGovernanceProjectionRecord] = []
    for kind in _DEFAULT_CAPABILITY_ORDER:
        if kind is PathGovernanceCapabilityKind.CLI_TUI_BINDING:
            records.append(
                build_path_governance_projection_record(
                    kind,
                    ProjectionSourceLabel.UNAVAILABLE,
                    _default_capability_summary(kind),
                    unavailable_reason=CLI_TUI_BINDING_UNAVAILABLE_REASON,
                    source_label=ProjectionSourceLabel.UNAVAILABLE,
                ),
            )
            continue
        module = _DEFAULT_CAPABILITY_MODULES.get(kind, "")
        records.append(
            build_path_governance_projection_record(
                kind,
                ProjectionSourceLabel.LIVE,
                _default_capability_summary(kind),
                subject_refs=[{"module": module}] if module else None,
                evidence_refs=[{"task": kind.value.lower()}],
                source_label=parsed_source,
            ),
        )
    return build_path_governance_api_envelope(
        records=records,
        source_label=parsed_source,
        metadata=metadata,
    )
