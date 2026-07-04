"""P5-TRACE-A stable trace references over existing ledger records.

These refs are *pointers*, never a second source of truth. They are derived
deterministically from the existing operational ledger records (see
``agentic_runtime.trace``) so the same record always yields the same ref and
two different records always yield different refs.

Naming note (repo truth over prompt assumption): ``agentic_runtime.contracts``
``.trace`` already defines a ``TraceEventRef`` and ``TraceBindingRef`` for the
canonical ``AurelTraceLog`` event form. The refs here live in the ``aurel_trace``
namespace and reference the *operational* ``trace.py`` ledger records and the
P5 canonical envelope layer. They are a distinct, additive layer — not a
replacement of the ``contracts.trace`` refs. This difference is recorded in the
P5-TRACE-A doctrine and inventory.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .trace_hash import (
    AurelTraceError,
    TraceIntegrityStatus,
    TraceTruthLabel,
    canonical_trace_json,
    require_nonempty,
    trace_sha,
)


def _stable_id(prefix: str, material: dict[str, Any]) -> str:
    return f"{prefix}-" + trace_sha(canonical_trace_json(material))[:40]


@dataclass(frozen=True)
class TraceRunRef:
    """Stable reference to a trace run / ledger sequence."""

    trace_run_id: str
    ledger_backend: str
    chain_head_hash: str | None = None
    event_count: int | None = None
    truth_label: TraceTruthLabel = TraceTruthLabel.TRACE_BOUND

    def __post_init__(self) -> None:
        require_nonempty(self, "trace_run_id", "ledger_backend")
        if self.truth_label is TraceTruthLabel.TRACE_INTEGRITY_VERIFIED:
            raise AurelTraceError(
                "a run ref does not by itself carry integrity verification"
            )
        if self.event_count is not None and self.event_count < 0:
            raise AurelTraceError("event_count must not be negative")

    def to_dict(self) -> dict[str, Any]:
        return {
            "trace_run_id": self.trace_run_id,
            "ledger_backend": self.ledger_backend,
            "chain_head_hash": self.chain_head_hash,
            "event_count": self.event_count,
            "truth_label": self.truth_label.value,
        }


@dataclass(frozen=True)
class TraceEntryRef:
    """Stable reference to one existing ledger entry / record.

    An entry ref proves *identity*, never verification.
    """

    trace_entry_id: str
    entry_hash: str
    record_type: str
    entry_index: int | None = None
    previous_entry_hash: str | None = None
    truth_label: TraceTruthLabel = TraceTruthLabel.TRACE_BOUND

    def __post_init__(self) -> None:
        require_nonempty(self, "trace_entry_id", "entry_hash", "record_type")
        if self.truth_label is TraceTruthLabel.TRACE_INTEGRITY_VERIFIED:
            raise AurelTraceError(
                "an entry ref does not by itself carry integrity verification"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "trace_entry_id": self.trace_entry_id,
            "entry_hash": self.entry_hash,
            "record_type": self.record_type,
            "entry_index": self.entry_index,
            "previous_entry_hash": self.previous_entry_hash,
            "truth_label": self.truth_label.value,
        }


@dataclass(frozen=True)
class TraceEventRef:
    """Stable reference to one canonicalized trace event envelope.

    Distinct from ``contracts.trace.TraceEventRef`` (which refs an
    ``AurelTraceLog`` event); this refs a P5 canonical envelope.
    """

    trace_event_ref_id: str
    canonical_event_id: str
    trace_entry_ref: TraceEntryRef
    event_kind: str
    payload_hash: str
    truth_label: TraceTruthLabel = TraceTruthLabel.TRACE_BOUND

    def __post_init__(self) -> None:
        require_nonempty(
            self,
            "trace_event_ref_id",
            "canonical_event_id",
            "event_kind",
            "payload_hash",
        )
        if not isinstance(self.trace_entry_ref, TraceEntryRef):
            raise AurelTraceError("trace_entry_ref must be a TraceEntryRef")
        if self.truth_label is TraceTruthLabel.TRACE_INTEGRITY_VERIFIED:
            raise AurelTraceError(
                "an event ref does not by itself carry integrity verification"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "trace_event_ref_id": self.trace_event_ref_id,
            "canonical_event_id": self.canonical_event_id,
            "trace_entry_ref": self.trace_entry_ref.to_dict(),
            "event_kind": self.event_kind,
            "payload_hash": self.payload_hash,
            "truth_label": self.truth_label.value,
        }


@dataclass(frozen=True)
class TraceBindingRef:
    """Generic binding from another domain object to a trace event ref.

    Binding means *linked to trace*. It does not mean trace-integrity verified
    and it does not authorize any action. ``verification_status`` therefore may
    not claim integrity here — verification is produced only by the P5 hash
    verification kernel.
    """

    trace_binding_ref_id: str
    domain: str
    domain_object_id: str
    trace_event_ref_id: str
    binding_kind: str
    verification_status: TraceIntegrityStatus = TraceIntegrityStatus.NOT_VERIFIED
    truth_label: TraceTruthLabel = TraceTruthLabel.TRACE_BOUND

    def __post_init__(self) -> None:
        require_nonempty(
            self,
            "trace_binding_ref_id",
            "domain",
            "domain_object_id",
            "trace_event_ref_id",
            "binding_kind",
        )
        if self.verification_status is TraceIntegrityStatus.INTEGRITY_VERIFIED:
            raise AurelTraceError(
                "a trace binding ref must not claim integrity verification; "
                "binding is not verification"
            )
        if self.truth_label is TraceTruthLabel.TRACE_INTEGRITY_VERIFIED:
            raise AurelTraceError(
                "a trace binding ref must not carry the integrity-verified label"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "trace_binding_ref_id": self.trace_binding_ref_id,
            "domain": self.domain,
            "domain_object_id": self.domain_object_id,
            "trace_event_ref_id": self.trace_event_ref_id,
            "binding_kind": self.binding_kind,
            "verification_status": self.verification_status.value,
            "truth_label": self.truth_label.value,
        }


def build_trace_run_ref(
    *,
    trace_run_id: str,
    ledger_backend: str,
    chain_head_hash: str | None = None,
    event_count: int | None = None,
) -> TraceRunRef:
    return TraceRunRef(
        trace_run_id=trace_run_id,
        ledger_backend=ledger_backend,
        chain_head_hash=chain_head_hash,
        event_count=event_count,
    )


def build_trace_entry_ref(
    *,
    trace_run_id: str,
    entry_hash: str,
    record_type: str,
    previous_entry_hash: str | None,
    entry_index: int | None,
) -> TraceEntryRef:
    if not entry_hash or not entry_hash.strip():
        raise AurelTraceError(
            "cannot build an entry ref for a record with no entry_hash "
            "(record has not been appended to a ledger)"
        )
    trace_entry_id = _stable_id(
        "tentry",
        {
            "trace_run_id": trace_run_id,
            "entry_hash": entry_hash,
            "record_type": record_type,
            "entry_index": entry_index,
        },
    )
    return TraceEntryRef(
        trace_entry_id=trace_entry_id,
        entry_hash=entry_hash,
        record_type=record_type,
        entry_index=entry_index,
        previous_entry_hash=previous_entry_hash,
    )


def build_trace_event_ref(
    *,
    canonical_event_id: str,
    trace_entry_ref: TraceEntryRef,
    event_kind: str,
    payload_hash: str,
) -> TraceEventRef:
    trace_event_ref_id = _stable_id(
        "tevent",
        {
            "canonical_event_id": canonical_event_id,
            "entry_hash": trace_entry_ref.entry_hash,
            "event_kind": event_kind,
            "payload_hash": payload_hash,
        },
    )
    return TraceEventRef(
        trace_event_ref_id=trace_event_ref_id,
        canonical_event_id=canonical_event_id,
        trace_entry_ref=trace_entry_ref,
        event_kind=event_kind,
        payload_hash=payload_hash,
    )


def build_trace_binding_ref(
    *,
    domain: str,
    domain_object_id: str,
    trace_event_ref: TraceEventRef,
    binding_kind: str,
) -> TraceBindingRef:
    trace_binding_ref_id = _stable_id(
        "tbind",
        {
            "domain": domain,
            "domain_object_id": domain_object_id,
            "trace_event_ref_id": trace_event_ref.trace_event_ref_id,
            "binding_kind": binding_kind,
        },
    )
    return TraceBindingRef(
        trace_binding_ref_id=trace_binding_ref_id,
        domain=domain,
        domain_object_id=domain_object_id,
        trace_event_ref_id=trace_event_ref.trace_event_ref_id,
        binding_kind=binding_kind,
    )
