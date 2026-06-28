"""Output Passport trace payload vs verification truth boundary (P1.9-C / P1.9.17).

Separates trace payload/reference from trace verification without AurelTrace
mutation, Ledger writes, or fake TRACE_VERIFIED claims.

Architectural law:
  - Trace payload is not trace verification.
  - TraceRef is not TRACE_VERIFIED.
  - PAYLOAD_ONLY is not proof.
  - REFERENCE_ONLY is not verification.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
from typing import Any

from .foundation import (
    FORBIDDEN_DEFAULT_TRUTH_LABELS,
    OutputPassportErrorCode,
    OutputPassportSideEffectProof,
    OutputPassportSourceLabel,
    OutputPassportTruthLabel,
    OutputPassportValidationError,
    stable_hash,
    to_canonical_json,
)

OUTPUT_PASSPORT_TRACE_BOUNDARY_TASK_ID = "P1.9.17"
OUTPUT_PASSPORT_TRACE_BOUNDARY_VERSION = "output_passport_trace_boundary.v1"
OUTPUT_PASSPORT_TRACE_PAYLOAD_DISCLOSURE_VERSION = (
    "output_passport_trace_payload_disclosure.v1"
)
OUTPUT_PASSPORT_TRACE_VERIFICATION_BOUNDARY_VERSION = (
    "output_passport_trace_verification_boundary.v1"
)


class TracePayloadStatus(str, Enum):
    """Trace payload attachment status."""

    PAYLOAD_PRESENT = "payload_present"
    REFERENCE_ONLY = "reference_only"
    PAYLOAD_AND_REFERENCE = "payload_and_reference"
    UNAVAILABLE = "unavailable"
    NOT_PRESENT = "not_present"


class TraceVerificationClaimStatus(str, Enum):
    """Trace verification claim status — not verification execution."""

    NOT_VERIFIED = "not_verified"
    VERIFICATION_UNAVAILABLE = "verification_unavailable"
    UNAVAILABLE_TRACE_VERIFICATION = "unavailable_trace_verification"
    REFERENCE_ONLY = "reference_only"
    CONTRACT_ONLY = "contract_only"


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


def _reject_forbidden_truth_label(
    truth_label: OutputPassportTruthLabel,
    *,
    field_name: str = "truth_label",
) -> None:
    if truth_label in FORBIDDEN_DEFAULT_TRUTH_LABELS:
        raise OutputPassportValidationError(
            f"forbidden {field_name}: {truth_label.value}",
            code=OutputPassportErrorCode.FORBIDDEN_VERIFICATION_LABEL,
            field=field_name,
        )


@dataclass(frozen=True)
class TracePayloadDisclosure(_CanonicalMixin):
    """Trace payload disclosure — payload presence does not imply verification."""

    schema_version: str
    checkpoint_id: str
    trace_payload_present: bool
    trace_ref_present: bool
    trace_payload_status: TracePayloadStatus
    payload_ref: str | None
    trace_ref: str | None
    payload_only_state: bool
    reference_only_state: bool
    truth_label: OutputPassportTruthLabel
    source_label: OutputPassportSourceLabel
    side_effects: OutputPassportSideEffectProof
    trace_payload_disclosure_hash: str


@dataclass(frozen=True)
class TraceVerificationTruthBoundary(_CanonicalMixin):
    """P1.9.17 trace verification truth boundary — contract only."""

    schema_version: str
    checkpoint_id: str
    trace_verification_status: TraceVerificationClaimStatus
    verification_unavailable_reason: str
    payload_only_state: bool
    reference_only_state: bool
    trace_verified: bool
    ledger_written: bool
    global_trace_written: bool
    invariants: tuple[str, ...]
    truth_label: OutputPassportTruthLabel
    source_label: OutputPassportSourceLabel
    side_effects: OutputPassportSideEffectProof
    trace_verification_boundary_hash: str


TRACE_BOUNDARY_INVARIANTS: tuple[str, ...] = (
    "trace_payload_is_not_trace_verification",
    "trace_ref_is_not_trace_verified",
    "payload_only_is_not_proof",
    "reference_only_is_not_verification",
    "no_ledger_write",
    "no_global_trace_write",
)


def build_trace_payload_vs_verification_boundary(
    *,
    checkpoint_id: str = "P1.9.17",
    trace_payload_present: bool = True,
    trace_ref_present: bool = True,
    payload_ref: str | None = "dev-trace-payload-ref-001",
    trace_ref: str | None = "dev-trace-ref-001",
    trace_payload_status: TracePayloadStatus | str = (
        TracePayloadStatus.PAYLOAD_AND_REFERENCE
    ),
    verification_unavailable_reason: str = (
        "trace_verification_runtime_unavailable_in_p1_9_c"
    ),
    source_label: OutputPassportSourceLabel | str = OutputPassportSourceLabel.DEV_FIXTURE,
) -> tuple[TracePayloadDisclosure, TraceVerificationTruthBoundary]:
    if isinstance(trace_payload_status, str):
        trace_payload_status = TracePayloadStatus(trace_payload_status)
    if isinstance(source_label, str):
        source_label = OutputPassportSourceLabel(source_label)

    payload_only = (
        trace_payload_present
        and not trace_ref_present
        and trace_payload_status is TracePayloadStatus.PAYLOAD_PRESENT
    )
    reference_only = (
        trace_ref_present
        and trace_payload_status is TracePayloadStatus.REFERENCE_ONLY
    )

    side_effects = _all_false_side_effects()
    payload_truth = (
        OutputPassportTruthLabel.PAYLOAD_ONLY
        if payload_only
        else OutputPassportTruthLabel.REFERENCE_ONLY
    )
    _reject_forbidden_truth_label(payload_truth)

    payload_disclosure_payload = {
        "schema_version": OUTPUT_PASSPORT_TRACE_PAYLOAD_DISCLOSURE_VERSION,
        "checkpoint_id": checkpoint_id,
        "trace_payload_present": trace_payload_present,
        "trace_ref_present": trace_ref_present,
        "trace_payload_status": trace_payload_status,
        "payload_ref": payload_ref,
        "trace_ref": trace_ref,
        "payload_only_state": payload_only,
        "reference_only_state": reference_only,
        "truth_label": payload_truth,
        "source_label": source_label,
        "side_effects": side_effects,
    }
    payload_disclosure = TracePayloadDisclosure(
        **payload_disclosure_payload,
        trace_payload_disclosure_hash=_hash_payload(payload_disclosure_payload),
    )

    boundary_payload = {
        "schema_version": OUTPUT_PASSPORT_TRACE_VERIFICATION_BOUNDARY_VERSION,
        "checkpoint_id": checkpoint_id,
        "trace_verification_status": TraceVerificationClaimStatus.NOT_VERIFIED,
        "verification_unavailable_reason": verification_unavailable_reason,
        "payload_only_state": payload_only,
        "reference_only_state": reference_only,
        "trace_verified": False,
        "ledger_written": False,
        "global_trace_written": False,
        "invariants": TRACE_BOUNDARY_INVARIANTS,
        "truth_label": OutputPassportTruthLabel.NOT_VERIFIED,
        "source_label": source_label,
        "side_effects": side_effects,
    }
    boundary = TraceVerificationTruthBoundary(
        **boundary_payload,
        trace_verification_boundary_hash=_hash_payload(boundary_payload),
    )
    return payload_disclosure, boundary


def serialize_trace_verification_boundary(
    boundary: TraceVerificationTruthBoundary,
) -> str:
    return to_canonical_json(boundary)
