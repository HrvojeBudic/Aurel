"""P1.5.10X canonical AurelTraceLog integrity tests."""
from __future__ import annotations

from dataclasses import FrozenInstanceError, replace

import pytest

from agentic_runtime.contracts.trace import (
    GENESIS_EVENT_HASH,
    AurelTraceLog,
    TraceEventStatus,
    TraceEventType,
    canonical_json_dumps,
    compute_event_hash,
    compute_payload_hash,
    hash_json,
    trace_event_to_dict,
)


def _append_event(log: AurelTraceLog, payload: dict | None = None):
    return log.append(
        event_type=TraceEventType.RUNTIME,
        actor_type="runtime",
        actor_id="runtime_001",
        payload_json=payload or {"action": "created", "ok": True},
        timestamp="2026-06-21T00:00:00+00:00",
        status=TraceEventStatus.CREATED,
    )


def test_append_creates_event():
    log = AurelTraceLog(trace_id="trace_test")
    event = _append_event(log)

    assert event.trace_id == "trace_test"
    assert event.sequence_no == 0
    assert event.event_hash
    assert log.get_event(event.event_id) == event
    assert log.get_trace("trace_test") == [event]


def test_appended_event_cannot_be_mutated():
    log = AurelTraceLog(trace_id="trace_test")
    event = _append_event(log)

    with pytest.raises(FrozenInstanceError):
        event.event_hash = "tampered"  # type: ignore[misc]

    with pytest.raises(TypeError):
        event.payload_json["action"] = "tampered"  # type: ignore[index]


def test_no_update_method_exists():
    assert not hasattr(AurelTraceLog, "update")


def test_no_delete_method_exists():
    assert not hasattr(AurelTraceLog, "delete")
    assert not hasattr(AurelTraceLog, "remove")


def test_event_hash_is_deterministic():
    payload_hash = compute_payload_hash({"b": 2, "a": 1})
    kwargs = dict(
        trace_id="trace_test",
        sequence_no=0,
        event_type=TraceEventType.RUNTIME,
        timestamp="2026-06-21T00:00:00+00:00",
        actor_type="runtime",
        actor_id="runtime_001",
        payload_hash=payload_hash,
        previous_event_hash=GENESIS_EVENT_HASH,
        status=TraceEventStatus.CREATED,
    )

    assert compute_event_hash(**kwargs) == compute_event_hash(**kwargs)


def test_event_hash_changes_when_payload_changes():
    base = dict(
        trace_id="trace_test",
        sequence_no=0,
        event_type=TraceEventType.RUNTIME,
        timestamp="2026-06-21T00:00:00+00:00",
        actor_type="runtime",
        actor_id="runtime_001",
        previous_event_hash=GENESIS_EVENT_HASH,
        status=TraceEventStatus.CREATED,
    )
    first = compute_event_hash(payload_hash=compute_payload_hash({"x": 1}), **base)
    second = compute_event_hash(payload_hash=compute_payload_hash({"x": 2}), **base)
    assert first != second


def test_payload_hash_is_stable_for_sorted_json():
    assert compute_payload_hash({"a": 1, "b": 2}) == compute_payload_hash({"b": 2, "a": 1})
    assert canonical_json_dumps({"b": 2, "a": None}) == '{"a":null,"b":2}'
    assert hash_json({"b": 2, "a": 1}) == hash_json({"a": 1, "b": 2})


def test_genesis_event_uses_genesis_previous_hash():
    log = AurelTraceLog(trace_id="trace_test")
    event = _append_event(log)
    assert event.previous_event_hash == GENESIS_EVENT_HASH


def test_second_event_previous_hash_matches_first_event_hash():
    log = AurelTraceLog(trace_id="trace_test")
    first = _append_event(log, {"step": 1})
    second = _append_event(log, {"step": 2})
    assert second.sequence_no == 1
    assert second.previous_event_hash == first.event_hash


def test_verify_chain_passes_for_valid_trace():
    log = AurelTraceLog(trace_id="trace_test")
    _append_event(log, {"step": 1})
    _append_event(log, {"step": 2})

    report = log.verify_chain("trace_test")
    assert report.is_valid is True
    assert report.checked_events == 2
    assert report.errors == ()


def test_verify_chain_fails_when_previous_hash_is_wrong():
    log = AurelTraceLog(trace_id="trace_test")
    first = _append_event(log, {"step": 1})
    second = _append_event(log, {"step": 2})
    corrupted = replace(second, previous_event_hash="wrong")
    corrupted_log = AurelTraceLog(trace_id="trace_test", events=(first, corrupted))

    report = corrupted_log.verify_chain("trace_test")
    assert report.is_valid is False
    assert report.broken_at_event_id == second.event_id
    assert report.expected_previous_hash == first.event_hash
    assert report.actual_previous_hash == "wrong"


def test_verify_chain_fails_when_event_payload_is_tampered():
    log = AurelTraceLog(trace_id="trace_test")
    event = _append_event(log, {"step": 1})
    corrupted = replace(event, payload_json={"step": 999})
    corrupted_log = AurelTraceLog(trace_id="trace_test", events=(corrupted,))

    report = corrupted_log.verify_chain("trace_test")
    assert report.is_valid is False
    assert report.broken_at_event_id == event.event_id
    assert "payload_hash mismatch" in report.errors


def test_verify_chain_reports_broken_event():
    log = AurelTraceLog(trace_id="trace_test")
    first = _append_event(log, {"step": 1})
    second = _append_event(log, {"step": 2})
    corrupted = replace(second, event_hash="bad")
    corrupted_log = AurelTraceLog(trace_id="trace_test", events=(first, corrupted))

    report = corrupted_log.verify_chain("trace_test")
    assert report.is_valid is False
    assert report.broken_at_event_id == second.event_id
    assert "event_hash mismatch" in report.errors


def test_trace_id_is_identity_not_content_addressable():
    first = AurelTraceLog(trace_id="trace_alpha")
    second = AurelTraceLog(trace_id="trace_beta")
    payload = {"same": "payload"}
    event_a = _append_event(first, payload)
    event_b = _append_event(second, payload)

    assert first.trace_id == "trace_alpha"
    assert second.trace_id == "trace_beta"
    assert event_a.payload_hash == event_b.payload_hash
    assert event_a.event_hash != event_b.event_hash


def test_trace_event_to_dict_serializes_frozen_payload_as_json():
    log = AurelTraceLog(trace_id="trace_test")
    event = _append_event(log, {"nested": {"a": [1, 2]}})
    payload = trace_event_to_dict(event)
    assert payload["payload_json"] == {"nested": {"a": [1, 2]}}
