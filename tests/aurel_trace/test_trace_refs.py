"""P5.3 — TraceRef / TraceBindingRef Normalization."""

from __future__ import annotations

import dataclasses
import json

import pytest

from agentic_runtime.aurel_trace import (
    AurelTraceError,
    TraceBindingRef,
    TraceEntryRef,
    TraceEventRef,
    TraceIntegrityStatus,
    TraceRunRef,
    TraceTruthLabel,
    build_trace_binding_ref,
    build_trace_run_ref,
    trace_run_ref_from_ledger,
)


def test_run_ref_is_stable_and_serializable(demo_ledger):
    a = trace_run_ref_from_ledger(demo_ledger)
    b = trace_run_ref_from_ledger(demo_ledger)
    assert a == b
    assert a.trace_run_id == "run_p5_demo"
    assert a.ledger_backend == "InMemoryTraceLedger"
    assert a.event_count == len(demo_ledger)
    assert json.loads(json.dumps(a.to_dict()))["trace_run_id"] == "run_p5_demo"


def test_entry_and_event_refs_are_stable_same_record_same_ref(demo_envelopes):
    env = demo_envelopes[0]
    entry_ref_a = env.trace_entry_ref
    event_ref_a = env.event_ref()
    event_ref_b = env.event_ref()
    assert isinstance(entry_ref_a, TraceEntryRef)
    assert isinstance(event_ref_a, TraceEventRef)
    # same envelope -> same event ref
    assert event_ref_a == event_ref_b


def test_different_records_produce_different_refs(demo_envelopes):
    entry_ids = {env.trace_entry_ref.trace_entry_id for env in demo_envelopes}
    event_ids = {env.event_ref().trace_event_ref_id for env in demo_envelopes}
    assert len(entry_ids) == len(demo_envelopes)
    assert len(event_ids) == len(demo_envelopes)


def test_refs_do_not_carry_integrity_verified_label(demo_envelopes):
    env = demo_envelopes[0]
    assert env.trace_entry_ref.truth_label is TraceTruthLabel.TRACE_BOUND
    with pytest.raises(AurelTraceError):
        dataclasses.replace(
            env.trace_entry_ref,
            truth_label=TraceTruthLabel.TRACE_INTEGRITY_VERIFIED,
        )
    run_ref = build_trace_run_ref(trace_run_id="r", ledger_backend="mem")
    with pytest.raises(AurelTraceError):
        dataclasses.replace(
            run_ref, truth_label=TraceTruthLabel.TRACE_INTEGRITY_VERIFIED
        )


def test_binding_ref_does_not_imply_verification(demo_envelopes):
    event_ref = demo_envelopes[0].event_ref()
    binding = build_trace_binding_ref(
        domain="P4_AUREL_EXEC",
        domain_object_id="exec-outcome-1",
        trace_event_ref=event_ref,
        binding_kind="execution_outcome",
    )
    assert isinstance(binding, TraceBindingRef)
    assert binding.verification_status is TraceIntegrityStatus.NOT_VERIFIED
    assert binding.truth_label is TraceTruthLabel.TRACE_BOUND
    # a binding may never claim integrity verification or that label
    with pytest.raises(AurelTraceError):
        dataclasses.replace(
            binding, verification_status=TraceIntegrityStatus.INTEGRITY_VERIFIED
        )
    with pytest.raises(AurelTraceError):
        dataclasses.replace(
            binding, truth_label=TraceTruthLabel.TRACE_INTEGRITY_VERIFIED
        )


def test_binding_ref_is_stable_and_serializable(demo_envelopes):
    event_ref = demo_envelopes[0].event_ref()
    a = build_trace_binding_ref(
        domain="P2_PROJECTION",
        domain_object_id="proj-1",
        trace_event_ref=event_ref,
        binding_kind="projection_record",
    )
    b = build_trace_binding_ref(
        domain="P2_PROJECTION",
        domain_object_id="proj-1",
        trace_event_ref=event_ref,
        binding_kind="projection_record",
    )
    assert a == b
    assert json.loads(json.dumps(a.to_dict()))["domain"] == "P2_PROJECTION"


def test_run_ref_rejects_negative_event_count():
    with pytest.raises(AurelTraceError):
        TraceRunRef(trace_run_id="r", ledger_backend="mem", event_count=-1)
