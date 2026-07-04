"""P5.2 — Canonical Trace Event Envelope Adapter."""

from __future__ import annotations

import dataclasses
import json

import pytest

from agentic_runtime.aurel_trace import (
    AurelTraceError,
    CanonicalTraceEventEnvelope,
    TraceEnvelopeUnsupportedError,
    TraceIntegrityStatus,
    TraceTruthLabel,
    canonical_envelope_from_existing_record,
    is_supported_record,
    try_canonical_envelope,
)
from agentic_runtime.contracts.trace import AurelTraceLog
from agentic_runtime.core_types import PlanningFailureRecord


def test_existing_record_wraps_into_envelope(demo_ledger, demo_run_ref):
    record = next(iter(demo_ledger))
    envelope = canonical_envelope_from_existing_record(
        record, trace_run_ref=demo_run_ref, sequence_index=0
    )
    assert isinstance(envelope, CanonicalTraceEventEnvelope)
    assert envelope.entry_hash == record.entry_hash
    assert envelope.previous_entry_hash == record.prev_entry_hash
    assert envelope.payload_hash == record.payload_hash()
    assert envelope.source_record_type == type(record).__name__
    # wrapping does not mutate the record
    assert record.entry_hash == envelope.entry_hash


def test_payload_hash_and_event_id_are_deterministic(demo_ledger, demo_run_ref):
    record = next(iter(demo_ledger))
    a = canonical_envelope_from_existing_record(
        record, trace_run_ref=demo_run_ref, sequence_index=0
    )
    b = canonical_envelope_from_existing_record(
        record, trace_run_ref=demo_run_ref, sequence_index=0
    )
    assert a.canonical_event_id == b.canonical_event_id
    assert a.payload_hash == b.payload_hash
    assert a == b


def test_canonical_serialization_is_stable(demo_envelopes):
    first = json.dumps(demo_envelopes[0].to_dict(), sort_keys=True)
    second = json.dumps(demo_envelopes[0].to_dict(), sort_keys=True)
    assert first == second
    # different records produce different canonical ids
    ids = {env.canonical_event_id for env in demo_envelopes}
    assert len(ids) == len(demo_envelopes)


def test_envelope_hash_material_excludes_nondeterministic_timestamp(demo_ledger, demo_run_ref):
    record = next(iter(demo_ledger))
    original = canonical_envelope_from_existing_record(
        record, trace_run_ref=demo_run_ref, sequence_index=0
    )
    # a different wall-clock created_at must not change the canonical event id
    shifted = canonical_envelope_from_existing_record(
        dataclasses.replace(record, created_at=record.created_at + 999.0),
        trace_run_ref=demo_run_ref,
        sequence_index=0,
    )
    assert shifted.canonical_event_id == original.canonical_event_id


def test_envelope_is_trace_bound_not_integrity_verified(demo_envelopes):
    for env in demo_envelopes:
        assert env.truth_label is TraceTruthLabel.TRACE_BOUND
        assert env.verification_status is TraceIntegrityStatus.NOT_VERIFIED
    with pytest.raises(AurelTraceError):
        dataclasses.replace(
            demo_envelopes[0], truth_label=TraceTruthLabel.TRACE_INTEGRITY_VERIFIED
        )
    with pytest.raises(AurelTraceError):
        dataclasses.replace(
            demo_envelopes[0],
            verification_status=TraceIntegrityStatus.INTEGRITY_VERIFIED,
        )


def test_unsupported_record_raises_in_strict_adapter(demo_run_ref):
    log = AurelTraceLog(trace_id="t")
    event = log.append(event_type="runtime", actor_type="test", actor_id="a", payload_json={"x": 1})
    with pytest.raises(TraceEnvelopeUnsupportedError):
        canonical_envelope_from_existing_record(
            event, trace_run_ref=demo_run_ref, sequence_index=0
        )
    assert is_supported_record(event) is False


def test_unsupported_record_does_not_silently_pass_in_lenient_adapter(demo_run_ref):
    result = try_canonical_envelope(
        {"not": "a record"}, trace_run_ref=demo_run_ref, sequence_index=0
    )
    assert result.supported is False
    assert result.envelope is None
    assert result.unsupported_record_type == "dict"
    assert result.reason


def test_record_without_entry_hash_is_insufficient(demo_run_ref):
    # a fresh, un-appended record has no entry_hash yet
    record = PlanningFailureRecord.make("i", "card1", "rejected", "r")
    assert record.entry_hash == ""
    result = try_canonical_envelope(
        record, trace_run_ref=demo_run_ref, sequence_index=0
    )
    assert result.supported is False
    assert "entry_hash" in (result.reason or "")
    with pytest.raises(AurelTraceError):
        canonical_envelope_from_existing_record(
            record, trace_run_ref=demo_run_ref, sequence_index=0
        )
