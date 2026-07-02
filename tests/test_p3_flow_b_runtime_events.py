from __future__ import annotations

import pytest

from agentic_runtime.aurel_flow import (
    AurelFlowValidationError,
    FlowTruthLabel,
    RuntimeEvent,
    RuntimeEventIsNotTraceBoundary,
    RuntimeEventKind,
    RuntimeEventRelation,
    RuntimeEventSeverity,
    RuntimeEventSource,
    append_runtime_event,
    build_runtime_event_read_model,
    create_runtime_event_stream,
    snapshot_runtime_event_stream,
)

_SOURCE = RuntimeEventSource(source_id="test-source")


def _stream():
    return create_runtime_event_stream("wfrun-test", stream_key="events-test")


def test_p3_flow_b_modules_import_cleanly() -> None:
    import agentic_runtime.aurel_flow as aurel_flow

    assert aurel_flow.AUREL_FLOW_B_PACK_ID == "P3-FLOW-B"


def test_runtime_event_can_be_created_and_appended_deterministically() -> None:
    first = append_runtime_event(
        _stream(), event_kind=RuntimeEventKind.RUN_CREATED, source=_SOURCE
    )
    second = append_runtime_event(
        _stream(), event_kind=RuntimeEventKind.RUN_CREATED, source=_SOURCE
    )

    assert first.accepted is True
    assert first.event is not None
    assert first.event.event_id == second.event.event_id
    assert first.event.sequence == 0
    assert first.event.target_run_id == "wfrun-test"
    assert first.stream.events == (first.event,)
    assert "not a Ledger write" in first.reason


def test_event_stream_snapshot_preserves_order() -> None:
    stream = _stream()
    kinds = (
        RuntimeEventKind.RUN_CREATED,
        RuntimeEventKind.SCHEDULER_DECISION_RECORDED,
        RuntimeEventKind.PAUSED,
    )
    for kind in kinds:
        result = append_runtime_event(stream, event_kind=kind, source=_SOURCE)
        stream = result.stream

    snapshot_a = snapshot_runtime_event_stream(stream)
    snapshot_b = snapshot_runtime_event_stream(stream)

    assert snapshot_a.event_count == 3
    assert snapshot_a.event_ids == tuple(event.event_id for event in stream.events)
    assert [event.event_kind for event in stream.events] == list(kinds)
    assert snapshot_a.snapshot_hash == snapshot_b.snapshot_hash
    assert snapshot_a.kind_counts["PAUSED"] == 1


def test_event_relation_preserves_all_relation_fields() -> None:
    stream = _stream()
    parent = append_runtime_event(
        stream, event_kind=RuntimeEventKind.RUN_CREATED, source=_SOURCE
    )
    stream = parent.stream
    child = append_runtime_event(
        stream,
        event_kind=RuntimeEventKind.SCHEDULER_DECISION_RECORDED,
        source=_SOURCE,
        relation=RuntimeEventRelation(
            parent_event_id=parent.event.event_id,
            correlation_id="corr-1",
            caused_by_event_id=parent.event.event_id,
            affected_node_ids=("a", "b"),
            affected_run_ids=("wfrun-test",),
        ),
    )

    assert child.accepted is True
    relation = child.event.relation
    assert relation.parent_event_id == parent.event.event_id
    assert relation.correlation_id == "corr-1"
    assert relation.caused_by_event_id == parent.event.event_id
    assert relation.affected_node_ids == ("a", "b")
    assert relation.affected_run_ids == ("wfrun-test",)


def test_append_rejects_unknown_relation_refs_and_run_mismatch() -> None:
    stream = _stream()
    unknown_parent = append_runtime_event(
        stream,
        event_kind=RuntimeEventKind.PAUSED,
        source=_SOURCE,
        relation=RuntimeEventRelation(parent_event_id="rtev-ghost"),
    )
    wrong_run = append_runtime_event(
        stream,
        event_kind=RuntimeEventKind.PAUSED,
        source=_SOURCE,
        target_run_id="wfrun-other",
    )

    assert unknown_parent.accepted is False
    assert unknown_parent.reject_code == "UNKNOWN_EVENT_REF"
    assert unknown_parent.event is None
    assert unknown_parent.stream.events == ()
    assert wrong_run.accepted is False
    assert wrong_run.reject_code == "RUN_MISMATCH"


def test_runtime_event_is_not_trace_event() -> None:
    # Canonical TraceEvent in this repo is a dict payload appended to the
    # hash-chained AurelTraceLog (agentic_runtime.trace). RuntimeEvent is a
    # frozen dataclass local to aurel_flow — structurally not a TraceEvent.
    result = append_runtime_event(
        _stream(), event_kind=RuntimeEventKind.RUN_CREATED, source=_SOURCE
    )
    boundary = result.stream.boundary

    assert not isinstance(result.event, dict)
    assert isinstance(boundary, RuntimeEventIsNotTraceBoundary)
    assert boundary.is_trace_event is False
    assert boundary.is_hash_chained_trace is False
    assert boundary.is_global_trace_write is False
    assert boundary.is_ledger_write is False
    assert boundary.can_claim_trace_verified is False
    assert "P5 AurelTrace" in boundary.trace_verification_unavailable_reason


def test_runtime_event_cannot_claim_trace_or_ledger() -> None:
    result = append_runtime_event(
        _stream(), event_kind=RuntimeEventKind.RUN_CREATED, source=_SOURCE
    )

    assert result.event.trace_verified is False
    assert result.event.ledger_written is False
    assert result.event.global_trace_written is False

    with pytest.raises(AurelFlowValidationError):
        RuntimeEvent(
            event_id="rtev-forced",
            sequence=0,
            contract_version="runtime_event.v1",
            event_kind=RuntimeEventKind.RUN_CREATED,
            severity=RuntimeEventSeverity.INFO,
            source=_SOURCE,
            target_run_id="wfrun-test",
            target_node_id="",
            relation=RuntimeEventRelation(),
            payload=result.event.payload,
            local_state_before_ref="",
            local_state_after_ref="",
            feedback_signal="",
            predictability_label="UNSPECIFIED",
            credit_unit_hint="",
            truth_label=FlowTruthLabel.LOCAL_RUNTIME_BEHAVIOR,
            metadata={},
            trace_verified=True,
        )


def test_forbidden_truth_labels_are_rejected_on_append() -> None:
    rejected = append_runtime_event(
        _stream(),
        event_kind=RuntimeEventKind.RUN_CREATED,
        source=_SOURCE,
        truth_label=FlowTruthLabel.TRACE_VERIFIED,
    )

    assert rejected.accepted is False
    assert rejected.reject_code == "FORBIDDEN_TRUTH_LABEL"


def test_event_read_model_exposes_boundary_truth() -> None:
    stream = _stream()
    for kind in (RuntimeEventKind.RUN_CREATED, RuntimeEventKind.PAUSED):
        stream = append_runtime_event(stream, event_kind=kind, source=_SOURCE).stream
    read_model = build_runtime_event_read_model(stream)

    assert read_model.event_count == 2
    assert read_model.trace_verified is False
    assert read_model.ledger_written is False
    assert read_model.global_trace_written is False
    assert len(read_model.relations) == 2
    assert read_model.read_model_hash == build_runtime_event_read_model(stream).read_model_hash
