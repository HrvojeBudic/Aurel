"""P1.5.10X projection boundary tests."""
from __future__ import annotations

import pytest

from agentic_runtime.contracts.projections import (
    ProjectionKind,
    ProjectionRecord,
    projection_record_to_dict,
    validate_projection_record,
)
from agentic_runtime.contracts.trace import (
    AurelTraceLog,
    TraceBindingRef,
    TraceEventType,
    trace_event_ref,
)


def _source_event():
    log = AurelTraceLog(trace_id="trace_projection_test")
    return log.append(
        event_type=TraceEventType.EVIDENCE,
        actor_type="evaluation",
        actor_id="eval_001",
        payload_json={"evidence": "created"},
        timestamp="2026-06-21T00:00:00+00:00",
    )


def test_projection_requires_source_event_ref():
    event = _source_event()
    ref = trace_event_ref(event)
    record = ProjectionRecord(
        projection_id="projection_001",
        projection_kind=ProjectionKind.LEDGER,
        source_event_ref=ref,
        source_event_hash=ref.event_hash,
    )
    assert validate_projection_record(record) == ()


def test_projection_cannot_claim_canonical_status():
    event = _source_event()
    ref = trace_event_ref(event)
    with pytest.raises(ValueError, match="cannot claim canonical"):
        ProjectionRecord(
            projection_id="projection_001",
            projection_kind=ProjectionKind.LEDGER,
            source_event_ref=ref,
            source_event_hash=ref.event_hash,
            is_canonical=True,
        )


def test_evidence_projection_requires_trace_binding():
    event = _source_event()
    ref = trace_event_ref(event)
    binding = TraceBindingRef(
        source_event_ref=ref,
        source_event_hash=ref.event_hash,
        source_trace_id=ref.trace_id,
        projection_type=ProjectionKind.EVIDENCE.value,
        projection_id="evidence_projection_001",
    )
    record = ProjectionRecord(
        projection_id=binding.projection_id or "evidence_projection_001",
        projection_kind=ProjectionKind.EVIDENCE,
        source_event_ref=binding.source_event_ref,
        source_event_hash=binding.source_event_hash,
    )

    assert record.is_canonical is False
    assert validate_projection_record(record) == ()


def test_evaluation_projection_requires_trace_binding():
    event = _source_event()
    ref = trace_event_ref(event)
    binding = TraceBindingRef(
        source_event_ref=ref,
        source_event_hash=ref.event_hash,
        source_trace_id=ref.trace_id,
        projection_type=ProjectionKind.EVALUATION.value,
        projection_id="evaluation_projection_001",
    )
    record = ProjectionRecord(
        projection_id=binding.projection_id or "evaluation_projection_001",
        projection_kind=ProjectionKind.EVALUATION,
        source_event_ref=binding.source_event_ref,
        source_event_hash=binding.source_event_hash,
    )

    assert record.is_canonical is False
    assert validate_projection_record(record) == ()


def test_trace_binding_ref_rejects_mismatched_source_hash_or_trace():
    event = _source_event()
    ref = trace_event_ref(event)

    with pytest.raises(ValueError, match="source_event_hash"):
        TraceBindingRef(
            source_event_ref=ref,
            source_event_hash="wrong",
            source_trace_id=ref.trace_id,
        )

    with pytest.raises(ValueError, match="source_trace_id"):
        TraceBindingRef(
            source_event_ref=ref,
            source_event_hash=ref.event_hash,
            source_trace_id="wrong_trace",
        )


def test_projection_record_rejects_hash_mismatch():
    event = _source_event()
    ref = trace_event_ref(event)
    with pytest.raises(ValueError, match="source_event_hash"):
        ProjectionRecord(
            projection_id="projection_bad",
            projection_kind=ProjectionKind.REPORT,
            source_event_ref=ref,
            source_event_hash="wrong",
        )


def test_projection_record_serialization_marks_non_canonical():
    event = _source_event()
    ref = trace_event_ref(event)
    record = ProjectionRecord(
        projection_id="projection_001",
        projection_kind=ProjectionKind.REPORT,
        source_event_ref=ref,
        source_event_hash=ref.event_hash,
    )
    payload = projection_record_to_dict(record)
    assert payload["projection_kind"] == "report"
    assert payload["is_canonical"] is False
    assert payload["source_event_ref"]["event_hash"] == ref.event_hash
