"""P5-TRACE-A canonical trace event envelope adapter.

A :class:`CanonicalTraceEventEnvelope` is a canonical, serializable wrapper
*around* an existing operational ledger record. It never mutates the record,
never appends to a ledger, and never becomes a second source of truth: the
envelope's ``payload_hash``/``entry_hash``/``previous_entry_hash`` are captured
from what the existing ledger already computed.

Supported records are the closed set of hash-chained ledger records defined in
``agentic_runtime.core_types`` and unioned in ``agentic_runtime.trace`` as
``TraceEntry``. Any other object is *unsupported* and must produce an explicit
result/finding — it must never silently pass.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..core_types import (
    ApprovalReceiptRecord,
    BudgetDecisionRecord,
    MemoryGovernanceRecord,
    PlanningFailureRecord,
    PraxisEventRecord,
    RuntimeStatusTransitionRecord,
    SandboxViolationRecord,
    StateTransitionRecord,
    ToolContractViolationRecord,
)
from .trace_hash import (
    CANONICAL_ENVELOPE_SCHEMA_VERSION,
    AurelTraceError,
    TraceIntegrityStatus,
    TraceTruthLabel,
    canonical_event_hash_material,
    canonical_event_id_from_hash_material,
    canonical_payload_hash,
)
from .trace_refs import (
    TraceEntryRef,
    TraceEventRef,
    TraceRunRef,
    build_trace_entry_ref,
    build_trace_event_ref,
)

# Closed-world map of supported ledger record types -> canonical event kind.
# Built from the actual imported classes so it cannot drift from repo truth.
SUPPORTED_RECORD_EVENT_KINDS: dict[str, str] = {
    StateTransitionRecord.__name__: "state_transition",
    PlanningFailureRecord.__name__: "planning_failure",
    RuntimeStatusTransitionRecord.__name__: "runtime_status_transition",
    BudgetDecisionRecord.__name__: "budget_decision",
    MemoryGovernanceRecord.__name__: "memory_governance",
    ToolContractViolationRecord.__name__: "tool_contract_violation",
    ApprovalReceiptRecord.__name__: "approval_receipt",
    PraxisEventRecord.__name__: "praxis_event",
    SandboxViolationRecord.__name__: "sandbox_violation",
}


class TraceEnvelopeUnsupportedError(AurelTraceError):
    """Raised when an unsupported record is passed to the strict adapter."""


@dataclass(frozen=True)
class CanonicalTraceEventEnvelope:
    """Canonical wrapper around one existing ledger record.

    The envelope is TRACE_BOUND by construction: it references a real record
    but makes no verification claim. Integrity verification is produced only by
    the P5 hash verification kernel and is never asserted at construction.
    """

    canonical_event_id: str
    trace_run_ref: TraceRunRef
    trace_entry_ref: TraceEntryRef
    source_record_type: str
    event_kind: str
    payload_hash: str
    entry_hash: str
    previous_entry_hash: str
    schema_version: str = CANONICAL_ENVELOPE_SCHEMA_VERSION
    causal_refs: tuple[str, ...] = ()
    created_at: float | None = None
    source_truth_label: TraceTruthLabel = TraceTruthLabel.TRACE_BOUND
    verification_status: TraceIntegrityStatus = TraceIntegrityStatus.NOT_VERIFIED
    truth_label: TraceTruthLabel = TraceTruthLabel.TRACE_BOUND

    def __post_init__(self) -> None:
        if not self.canonical_event_id.strip():
            raise AurelTraceError("canonical_event_id must not be empty")
        if not self.entry_hash.strip():
            raise AurelTraceError("entry_hash must not be empty")
        if not self.payload_hash.strip():
            raise AurelTraceError("payload_hash must not be empty")
        if self.source_record_type not in SUPPORTED_RECORD_EVENT_KINDS:
            raise TraceEnvelopeUnsupportedError(
                f"unsupported source record type: {self.source_record_type}"
            )
        if SUPPORTED_RECORD_EVENT_KINDS[self.source_record_type] != self.event_kind:
            raise AurelTraceError(
                "event_kind does not match the supported record type mapping"
            )
        if self.verification_status is TraceIntegrityStatus.INTEGRITY_VERIFIED:
            raise AurelTraceError(
                "an envelope is trace-bound, not integrity-verified; "
                "verification is produced only by the P5 hash kernel"
            )
        if self.truth_label is TraceTruthLabel.TRACE_INTEGRITY_VERIFIED:
            raise AurelTraceError(
                "an envelope must carry TRACE_BOUND, not TRACE_INTEGRITY_VERIFIED"
            )
        if self.entry_hash != self.trace_entry_ref.entry_hash:
            raise AurelTraceError("entry_hash must match the trace_entry_ref")

    def to_dict(self) -> dict[str, Any]:
        return {
            "canonical_event_id": self.canonical_event_id,
            "trace_run_ref": self.trace_run_ref.to_dict(),
            "trace_entry_ref": self.trace_entry_ref.to_dict(),
            "source_record_type": self.source_record_type,
            "event_kind": self.event_kind,
            "payload_hash": self.payload_hash,
            "entry_hash": self.entry_hash,
            "previous_entry_hash": self.previous_entry_hash,
            "schema_version": self.schema_version,
            "causal_refs": list(self.causal_refs),
            "created_at": self.created_at,
            "source_truth_label": self.source_truth_label.value,
            "verification_status": self.verification_status.value,
            "truth_label": self.truth_label.value,
        }

    def event_ref(self) -> TraceEventRef:
        return build_trace_event_ref(
            canonical_event_id=self.canonical_event_id,
            trace_entry_ref=self.trace_entry_ref,
            event_kind=self.event_kind,
            payload_hash=self.payload_hash,
        )


def is_supported_record(record: Any) -> bool:
    return type(record).__name__ in SUPPORTED_RECORD_EVENT_KINDS


def canonical_envelope_from_existing_record(
    record: Any,
    *,
    trace_run_ref: TraceRunRef,
    sequence_index: int,
    include_created_at: bool = True,
) -> CanonicalTraceEventEnvelope:
    """Wrap one supported ledger record into a canonical envelope.

    Raises :class:`TraceEnvelopeUnsupportedError` for unsupported records so
    they can never silently pass. ``created_at`` (if captured) is metadata only
    and is deliberately excluded from the canonical hash material.
    """

    record_type = type(record).__name__
    if record_type not in SUPPORTED_RECORD_EVENT_KINDS:
        raise TraceEnvelopeUnsupportedError(
            f"unsupported source record type: {record_type}"
        )
    entry_hash = str(getattr(record, "entry_hash", "") or "")
    if not entry_hash:
        raise AurelTraceError(
            f"{record_type} has no entry_hash; append it to a ledger first"
        )
    previous_entry_hash = str(getattr(record, "prev_entry_hash", "") or "")
    event_kind = SUPPORTED_RECORD_EVENT_KINDS[record_type]
    payload_hash = canonical_payload_hash(record)

    entry_ref = build_trace_entry_ref(
        trace_run_id=trace_run_ref.trace_run_id,
        entry_hash=entry_hash,
        record_type=record_type,
        previous_entry_hash=previous_entry_hash,
        entry_index=sequence_index,
    )
    material = canonical_event_hash_material(
        trace_run_id=trace_run_ref.trace_run_id,
        source_record_type=record_type,
        event_kind=event_kind,
        sequence_index=sequence_index,
        payload_hash=payload_hash,
        entry_hash=entry_hash,
        previous_entry_hash=previous_entry_hash,
    )
    canonical_event_id = canonical_event_id_from_hash_material(material)
    created_at = getattr(record, "created_at", None) if include_created_at else None

    return CanonicalTraceEventEnvelope(
        canonical_event_id=canonical_event_id,
        trace_run_ref=trace_run_ref,
        trace_entry_ref=entry_ref,
        source_record_type=record_type,
        event_kind=event_kind,
        payload_hash=payload_hash,
        entry_hash=entry_hash,
        previous_entry_hash=previous_entry_hash,
        created_at=created_at,
    )


@dataclass(frozen=True)
class EnvelopeAdaptationResult:
    """Result of a lenient adaptation attempt over one record.

    Exactly one of ``envelope`` / ``unsupported_record_type`` is populated.
    """

    supported: bool
    envelope: CanonicalTraceEventEnvelope | None = None
    unsupported_record_type: str | None = None
    reason: str | None = None


def try_canonical_envelope(
    record: Any,
    *,
    trace_run_ref: TraceRunRef,
    sequence_index: int,
) -> EnvelopeAdaptationResult:
    """Lenient adapter: never raises for unsupported records, reports instead."""

    record_type = type(record).__name__
    if record_type not in SUPPORTED_RECORD_EVENT_KINDS:
        return EnvelopeAdaptationResult(
            supported=False,
            unsupported_record_type=record_type,
            reason=f"record type {record_type} is not a supported ledger record",
        )
    try:
        envelope = canonical_envelope_from_existing_record(
            record,
            trace_run_ref=trace_run_ref,
            sequence_index=sequence_index,
        )
    except AurelTraceError as exc:  # insufficient data (e.g. missing entry_hash)
        return EnvelopeAdaptationResult(
            supported=False,
            unsupported_record_type=record_type,
            reason=str(exc),
        )
    return EnvelopeAdaptationResult(supported=True, envelope=envelope)


def envelopes_from_ledger(
    ledger: Any,
    *,
    trace_run_ref: TraceRunRef | None = None,
) -> tuple[CanonicalTraceEventEnvelope, ...]:
    """Wrap every record in an existing ledger into canonical envelopes.

    Read-only: iterates the ledger and never mutates or appends. The ledger
    remains the source of truth.
    """

    run_ref = trace_run_ref or trace_run_ref_from_ledger(ledger)
    envelopes: list[CanonicalTraceEventEnvelope] = []
    for index, record in enumerate(ledger):
        envelopes.append(
            canonical_envelope_from_existing_record(
                record,
                trace_run_ref=run_ref,
                sequence_index=index,
            )
        )
    return tuple(envelopes)


def trace_run_ref_from_ledger(ledger: Any) -> TraceRunRef:
    """Build a run ref from a live ledger without mutating it."""

    trace_run_id = str(getattr(ledger, "run_id", "") or "unknown-run")
    chain_head = getattr(ledger, "head", None)
    try:
        event_count: int | None = len(ledger)
    except TypeError:
        event_count = None
    return TraceRunRef(
        trace_run_id=trace_run_id,
        ledger_backend=type(ledger).__name__,
        chain_head_hash=str(chain_head) if chain_head is not None else None,
        event_count=event_count,
    )
