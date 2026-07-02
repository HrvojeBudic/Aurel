from __future__ import annotations

from dataclasses import replace

import pytest

from agentic_runtime.aurel_flow import (
    AurelFlowValidationError,
    FlowTruthLabel,
    build_flow_demo_bundle,
    build_runtime_behavior_timeline,
)


def test_timeline_orders_entries_by_sequence() -> None:
    bundle = build_flow_demo_bundle()
    timeline = build_runtime_behavior_timeline(bundle.event_stream)

    sequences = [entry.sequence for entry in timeline.entries]
    assert sequences == sorted(sequences)
    assert timeline.entry_count == len(bundle.event_stream.events)
    assert timeline.entry_count == 3


def test_timeline_is_deterministic() -> None:
    first = build_runtime_behavior_timeline(build_flow_demo_bundle().event_stream)
    second = build_runtime_behavior_timeline(build_flow_demo_bundle().event_stream)

    assert first.timeline_hash == second.timeline_hash
    assert tuple(entry.entry_id for entry in first.entries) == tuple(
        entry.entry_id for entry in second.entries
    )


def test_timeline_entries_carry_event_truth() -> None:
    bundle = build_flow_demo_bundle()
    timeline = build_runtime_behavior_timeline(bundle.event_stream)

    kinds = tuple(entry.event_kind for entry in timeline.entries)
    assert kinds == ("RUN_CREATED", "SCHEDULER_DECISION_RECORDED", "PAUSED")
    for entry in timeline.entries:
        assert entry.run_id == bundle.run.run_id
        assert entry.source_actor == "aurel-flow-demo"
        assert entry.truth_label is FlowTruthLabel.DEV_FIXTURE


def test_timeline_is_not_trace() -> None:
    timeline = build_runtime_behavior_timeline(build_flow_demo_bundle().event_stream)

    assert timeline.is_trace is False
    assert timeline.is_hash_chain_proof is False
    assert timeline.trace_verified is False
    assert "P5 AurelTrace" in timeline.trace_unavailable_reason
    for entry in timeline.entries:
        assert entry.trace_verified is False
        assert entry.ledger_written is False
        assert entry.execution_available is False


def test_timeline_boundary_booleans_fail_closed() -> None:
    timeline = build_runtime_behavior_timeline(build_flow_demo_bundle().event_stream)

    for forbidden in ("is_trace", "is_hash_chain_proof", "trace_verified"):
        with pytest.raises(AurelFlowValidationError):
            replace(timeline, **{forbidden: True})
    entry = timeline.entries[0]
    for forbidden in ("execution_available", "trace_verified", "ledger_written"):
        with pytest.raises(AurelFlowValidationError):
            replace(entry, **{forbidden: True})


def test_timeline_does_not_mutate_stream() -> None:
    bundle = build_flow_demo_bundle()
    events_before = tuple(event.event_id for event in bundle.event_stream.events)

    build_runtime_behavior_timeline(bundle.event_stream)

    assert (
        tuple(event.event_id for event in bundle.event_stream.events) == events_before
    )
