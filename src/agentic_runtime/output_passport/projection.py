"""Output Passport projection/API/event contract (P1.9.27).

Projection exposes read-model state. It does not execute runtime.
API contract is not API server. Event contract is not emitted event.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
from typing import Any

from .foundation import (
    OutputPassportCheckpointRead,
    OutputPassportCheckpointStatus,
    OutputPassportSideEffectProof,
    OutputPassportSourceLabel,
    OutputPassportTruthLabel,
    OutputPassportUnavailableReason,
    build_dev_fixture_output_passport_payload,
    stable_hash,
    to_canonical_json,
)
from .read_model import build_output_passport_read_model
from .readiness_audit import build_p1_9_c_truth_boundary_failure_readiness_pack_result
from .truth_boundary import build_trace_payload_vs_verification_boundary

OUTPUT_PASSPORT_P1_9_27_TASK_ID = "P1.9.27"
OUTPUT_PASSPORT_PROJECTION_CONTRACT_VERSION = (
    "output_passport_projection_contract.v1"
)
OUTPUT_PASSPORT_PROJECTION_PAYLOAD_VERSION = (
    "output_passport_projection_payload.v1"
)
OUTPUT_PASSPORT_API_CONTRACT_VERSION = "output_passport_api_contract.v1"
OUTPUT_PASSPORT_EVENT_CONTRACT_VERSION = "output_passport_event_contract.v1"
OUTPUT_PASSPORT_EVENT_PAYLOAD_VERSION = "output_passport_event_payload.v1"

API_RUNTIME_UNAVAILABLE_REASON = (
    "UNAVAILABLE_API_RUNTIME: HTTP API server not implemented in P1.9-D; "
    "contract-only envelope"
)
EVENT_RUNTIME_UNAVAILABLE_REASON = (
    "UNAVAILABLE_EVENT_RUNTIME: event bus dispatch not implemented in P1.9-D; "
    "contract-only payload shape"
)


class OutputPassportProjectionStatus(str, Enum):
    """Projection layer status — not execution."""

    PROJECTION_ONLY = "PROJECTION_ONLY"
    CONTRACT_ONLY = "CONTRACT_ONLY"
    API_CONTRACT_ONLY = "API_CONTRACT_ONLY"
    EVENT_CONTRACT_ONLY = "EVENT_CONTRACT_ONLY"
    UNAVAILABLE = "UNAVAILABLE"


class OutputPassportAPIRuntimeStatus(str, Enum):
    """API runtime availability."""

    API_CONTRACT_ONLY = "API_CONTRACT_ONLY"
    UNAVAILABLE_API_RUNTIME = "UNAVAILABLE_API_RUNTIME"


class OutputPassportEventRuntimeStatus(str, Enum):
    """Event runtime availability."""

    EVENT_CONTRACT_ONLY = "EVENT_CONTRACT_ONLY"
    UNAVAILABLE_EVENT_RUNTIME = "UNAVAILABLE_EVENT_RUNTIME"


class _CanonicalMixin:
    def to_canonical_dict(self) -> dict[str, Any]:
        return _canonical_dataclass_dict(self)


def _canonical_value(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return _canonical_dataclass_dict(value)
    if isinstance(value, Mapping):
        return {
            str(_canonical_value(key)): _canonical_value(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    if isinstance(value, (list, tuple)):
        return [_canonical_value(item) for item in value]
    return value


def _canonical_dataclass_dict(value: Any) -> dict[str, Any]:
    return {
        field.name: _canonical_value(getattr(value, field.name))
        for field in fields(value)
    }


def _hash_payload(payload: Mapping[str, Any]) -> str:
    return stable_hash(dict(payload))


def _all_false_side_effects() -> OutputPassportSideEffectProof:
    return OutputPassportSideEffectProof()


@dataclass(frozen=True)
class OutputPassportAPIContract(_CanonicalMixin):
    """API payload contract — not live HTTP server."""

    schema_version: str
    contract_name: str
    contract_version: str
    api_payload_schema: Mapping[str, str]
    runtime_status: OutputPassportAPIRuntimeStatus
    unavailable_reason: str
    truth_label: OutputPassportTruthLabel
    source_label: OutputPassportSourceLabel
    side_effects: OutputPassportSideEffectProof
    contract_hash: str


@dataclass(frozen=True)
class OutputPassportEventPayload(_CanonicalMixin):
    """Event payload shape — not emitted event."""

    schema_version: str
    event_kind: str
    projection_ref: str
    read_model_ref: str
    summary: str
    truth_label: OutputPassportTruthLabel
    source_label: OutputPassportSourceLabel
    side_effects: OutputPassportSideEffectProof
    event_payload_hash: str


@dataclass(frozen=True)
class OutputPassportEventContract(_CanonicalMixin):
    """Event contract envelope — not event bus."""

    schema_version: str
    contract_name: str
    contract_version: str
    event_payload_schema: Mapping[str, str]
    runtime_status: OutputPassportEventRuntimeStatus
    unavailable_reason: str
    event_payload: OutputPassportEventPayload
    truth_label: OutputPassportTruthLabel
    source_label: OutputPassportSourceLabel
    side_effects: OutputPassportSideEffectProof
    contract_hash: str


@dataclass(frozen=True)
class OutputPassportProjectionPayload(_CanonicalMixin):
    """Projection payload derived from P1.9-A/B/C read model."""

    schema_version: str
    projection_version: str
    passport_read_model_ref: str
    passport_projection_payload: Mapping[str, Any]
    truth_labels: tuple[OutputPassportTruthLabel, ...]
    verification_status: str
    trace_truth_boundary_summary: str
    failure_unavailable_summary: str
    projection_status: OutputPassportProjectionStatus
    source_label: OutputPassportSourceLabel
    side_effects: OutputPassportSideEffectProof
    projection_payload_hash: str


@dataclass(frozen=True)
class OutputPassportProjectionContract(_CanonicalMixin):
    """Projection/API/event contract bundle."""

    schema_version: str
    projection_payload: OutputPassportProjectionPayload
    api_contract: OutputPassportAPIContract
    event_contract: OutputPassportEventContract
    projection_status: OutputPassportProjectionStatus
    truth_labels: tuple[OutputPassportTruthLabel, ...]
    source_label: OutputPassportSourceLabel
    side_effects: OutputPassportSideEffectProof
    contract_hash: str


def build_output_passport_api_contract(
    *,
    projection_ref: str = "",
    read_model_ref: str = "",
    source_label: OutputPassportSourceLabel | str = OutputPassportSourceLabel.DEV_FIXTURE,
) -> OutputPassportAPIContract:
    if isinstance(source_label, str):
        source_label = OutputPassportSourceLabel(source_label)

    side_effects = _all_false_side_effects()
    api_payload_schema = {
        "projection_ref": "string",
        "read_model_ref": "string",
        "truth_labels": "array[string]",
        "verification_status": "string",
        "trace_truth_boundary_summary": "string",
        "failure_unavailable_summary": "string",
        "projection_status": "string",
        "source_label": "string",
        "runtime_status": OutputPassportAPIRuntimeStatus.UNAVAILABLE_API_RUNTIME.value,
    }
    payload = {
        "schema_version": OUTPUT_PASSPORT_API_CONTRACT_VERSION,
        "contract_name": "output_passport_projection_api",
        "contract_version": "v1",
        "api_payload_schema": api_payload_schema,
        "runtime_status": OutputPassportAPIRuntimeStatus.UNAVAILABLE_API_RUNTIME,
        "unavailable_reason": API_RUNTIME_UNAVAILABLE_REASON,
        "truth_label": OutputPassportTruthLabel.CONTRACT_ONLY,
        "source_label": source_label,
        "side_effects": side_effects,
    }
    return OutputPassportAPIContract(
        **payload,
        contract_hash=_hash_payload({
            **payload,
            "projection_ref": projection_ref,
            "read_model_ref": read_model_ref,
        }),
    )


def build_output_passport_event_contract(
    *,
    projection_ref: str = "",
    read_model_ref: str = "",
    source_label: OutputPassportSourceLabel | str = OutputPassportSourceLabel.DEV_FIXTURE,
) -> OutputPassportEventContract:
    if isinstance(source_label, str):
        source_label = OutputPassportSourceLabel(source_label)

    side_effects = _all_false_side_effects()
    event_payload_schema = {
        "event_kind": "string",
        "projection_ref": "string",
        "read_model_ref": "string",
        "summary": "string",
        "truth_label": "string",
        "source_label": "string",
        "runtime_status": OutputPassportEventRuntimeStatus.UNAVAILABLE_EVENT_RUNTIME.value,
    }
    event_payload_body = {
        "schema_version": OUTPUT_PASSPORT_EVENT_PAYLOAD_VERSION,
        "event_kind": "output_passport_projection_updated",
        "projection_ref": projection_ref,
        "read_model_ref": read_model_ref,
        "summary": "DEV_FIXTURE projection contract seed; not emitted",
        "truth_label": OutputPassportTruthLabel.CONTRACT_ONLY,
        "source_label": source_label,
        "side_effects": side_effects,
    }
    event_payload = OutputPassportEventPayload(
        **event_payload_body,
        event_payload_hash=_hash_payload(event_payload_body),
    )
    payload = {
        "schema_version": OUTPUT_PASSPORT_EVENT_CONTRACT_VERSION,
        "contract_name": "output_passport_projection_event",
        "contract_version": "v1",
        "event_payload_schema": event_payload_schema,
        "runtime_status": OutputPassportEventRuntimeStatus.UNAVAILABLE_EVENT_RUNTIME,
        "unavailable_reason": EVENT_RUNTIME_UNAVAILABLE_REASON,
        "event_payload": event_payload,
        "truth_label": OutputPassportTruthLabel.CONTRACT_ONLY,
        "source_label": source_label,
        "side_effects": side_effects,
    }
    return OutputPassportEventContract(
        **payload,
        contract_hash=_hash_payload(payload),
    )


def build_output_passport_projection_payload(
    *,
    source_label: OutputPassportSourceLabel | str = OutputPassportSourceLabel.DEV_FIXTURE,
) -> OutputPassportProjectionPayload:
    if isinstance(source_label, str):
        source_label = OutputPassportSourceLabel(source_label)

    payload_obj = build_dev_fixture_output_passport_payload()
    read_model = build_output_passport_read_model(payload=payload_obj)
    p1_9_c = build_p1_9_c_truth_boundary_failure_readiness_pack_result()
    trace_payload, trace_boundary = build_trace_payload_vs_verification_boundary()

    truth_labels = (
        OutputPassportTruthLabel.CONTRACT_ONLY,
        OutputPassportTruthLabel.DEV_FIXTURE,
        OutputPassportTruthLabel.NOT_VERIFIED,
        OutputPassportTruthLabel.NOT_SEAL,
    )
    trace_summary = (
        f"payload_status={trace_payload.trace_payload_status.value}; "
        f"trace_verified={trace_boundary.trace_verified}; "
        f"verification={trace_boundary.trace_verification_status.value}"
    )
    failure_summary = p1_9_c.revision_replay_failure_summary
    passport_projection_payload = {
        "read_model_hash": read_model.read_model_hash,
        "passport_payload_hash": payload_obj.payload_hash,
        "checkpoint_count": len(p1_9_c.checkpoint_reads),
        "harness_passed": p1_9_c.readiness_audit_summary,
    }
    side_effects = _all_false_side_effects()
    body = {
        "schema_version": OUTPUT_PASSPORT_PROJECTION_PAYLOAD_VERSION,
        "projection_version": "v1",
        "passport_read_model_ref": read_model.read_model_hash,
        "passport_projection_payload": passport_projection_payload,
        "truth_labels": truth_labels,
        "verification_status": "NOT_VERIFIED",
        "trace_truth_boundary_summary": trace_summary,
        "failure_unavailable_summary": failure_summary,
        "projection_status": OutputPassportProjectionStatus.PROJECTION_ONLY,
        "source_label": source_label,
        "side_effects": side_effects,
    }
    return OutputPassportProjectionPayload(
        **body,
        projection_payload_hash=_hash_payload(body),
    )


def build_output_passport_projection_contract(
    *,
    source_label: OutputPassportSourceLabel | str = OutputPassportSourceLabel.DEV_FIXTURE,
) -> OutputPassportProjectionContract:
    if isinstance(source_label, str):
        source_label = OutputPassportSourceLabel(source_label)

    projection_payload = build_output_passport_projection_payload(
        source_label=source_label,
    )
    api_contract = build_output_passport_api_contract(
        projection_ref=projection_payload.projection_payload_hash,
        read_model_ref=projection_payload.passport_read_model_ref,
        source_label=source_label,
    )
    event_contract = build_output_passport_event_contract(
        projection_ref=projection_payload.projection_payload_hash,
        read_model_ref=projection_payload.passport_read_model_ref,
        source_label=source_label,
    )
    truth_labels = (
        OutputPassportTruthLabel.CONTRACT_ONLY,
        OutputPassportTruthLabel.DEV_FIXTURE,
        OutputPassportTruthLabel.NOT_VERIFIED,
        OutputPassportTruthLabel.NOT_SEAL,
    )
    side_effects = _all_false_side_effects()
    body = {
        "schema_version": OUTPUT_PASSPORT_PROJECTION_CONTRACT_VERSION,
        "projection_payload": projection_payload,
        "api_contract": api_contract,
        "event_contract": event_contract,
        "projection_status": OutputPassportProjectionStatus.PROJECTION_ONLY,
        "truth_labels": truth_labels,
        "source_label": source_label,
        "side_effects": side_effects,
    }
    return OutputPassportProjectionContract(
        **body,
        contract_hash=_hash_payload(body),
    )


def serialize_output_passport_projection_payload(
    payload: OutputPassportProjectionPayload | OutputPassportProjectionContract,
) -> str:
    return to_canonical_json(payload)


def _default_p1_9_27_checkpoint_read() -> OutputPassportCheckpointRead:
    return OutputPassportCheckpointRead(
        checkpoint_id="P1.9.27",
        canonical_name="Output Passport Projection/API/Event Contract",
        status=OutputPassportCheckpointStatus.DONE,
        truth_label=OutputPassportTruthLabel.CONTRACT_ONLY,
        unavailable_reason=None,
        limitations=(
            "Projection is not execution.",
            "API contract is not API server.",
            "Event contract is not emitted event.",
        ),
        evidence_ref="output_passport_projection_contract",
    )
