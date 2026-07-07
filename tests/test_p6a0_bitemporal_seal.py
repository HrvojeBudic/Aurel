"""A0 seal — bi-temporal stamps + as-of read model.

Proves the six A0 invariants:

1. Additive construction (open defaults; ``to_dict`` gains the 6 keys).
2. Trace/funnel unaffected (governed writes never serialize the new fields;
   the chain still verifies) — byte-identity at the trace level.
3. As-of correctness (past belief vs current belief; deterministic history).
4. No-collapse: retrieval/storage untouched (closing a stamp does NOT hide a
   record from the live ``retrieve``/``assemble_context`` path in A0).
5. No-overclaim: ``is_current()`` is True only for fully-open intervals.
6. Fail-closed: empty view / unknown id ⇒ ``[]``, never a fabricated belief.
"""

from __future__ import annotations

import json

from agentic_runtime import MemoryFabric, MemoryTruthState, MemoryWriteRequest
from agentic_runtime.core_types import MemoryRecord, MemoryTier
from agentic_runtime.memory_asof import AsOfView
from agentic_runtime.memory_bitemporal import (
    BiTemporalStamp,
    _flag_enabled,
)
from agentic_runtime.trace import InMemoryTraceLedger

RUN = "run_a0"

_BITEMPORAL_FIELDS = (
    "superseded_by",
    "revises",
    "valid_from",
    "valid_to",
    "transaction_from",
    "transaction_to",
)


def _fabric():
    trace = InMemoryTraceLedger(run_id=RUN)
    fab = MemoryFabric()
    fab.bind_trace(trace)
    return fab, trace


def _gov_rows(trace):
    return [r for r in trace.replay() if r.get("kind") == "memory_governance"]


# --------------------------------------------------------------------------- #
# 1. Additive construction — open defaults, to_dict gains the keys.
# --------------------------------------------------------------------------- #
def test_memory_record_bitemporal_fields_default_open():
    rec = MemoryRecord.make(MemoryTier.SEMANTIC, "a fact", "src")
    for f in _BITEMPORAL_FIELDS:
        assert getattr(rec, f) is None, f
    d = rec.to_dict()
    for f in _BITEMPORAL_FIELDS:
        assert f in d and d[f] is None, f
    # A default record is current on both axes.
    assert BiTemporalStamp.from_record(rec).is_current() is True


# --------------------------------------------------------------------------- #
# 2. Trace/funnel unaffected — governed writes never carry the new fields and
#    the hash chain still verifies. (Byte-identity at the trace level.)
# --------------------------------------------------------------------------- #
def test_governed_writes_do_not_serialize_bitemporal_fields():
    fab, trace = _fabric()
    # deny (agent cannot write CANON) + allow (system RAW) — a realistic mix.
    fab.request_write(MemoryWriteRequest(
        content="denied", source_run_id=RUN, writer_kind="agent",
        proposed_truth_state=MemoryTruthState.CANON))
    dec = fab.request_write(MemoryWriteRequest(
        content="allowed", source_run_id=RUN, writer_kind="system",
        proposed_truth_state=MemoryTruthState.RAW))
    assert dec.allowed
    rows = _gov_rows(trace)
    assert rows, "expected memory-governance trace rows"
    for row in rows:
        blob = json.dumps(row, default=str)
        for f in _BITEMPORAL_FIELDS:
            assert f not in blob, f"{f} leaked into memory-governance trace"
    # the funnel-built record carries open stamps (write path unchanged)
    assert dec.record is not None
    for f in _BITEMPORAL_FIELDS:
        assert getattr(dec.record, f) is None, f
    # chain integrity intact
    ok, broken = trace.verify_chain()
    assert ok and broken is None


# --------------------------------------------------------------------------- #
# 3. As-of correctness — past vs current belief; deterministic history.
# --------------------------------------------------------------------------- #
def _versioned_pair():
    v1 = MemoryRecord.make(MemoryTier.SEMANTIC, "VALUE is 1", "src")
    v1.memory_id = "m1"
    v1.transaction_from, v1.transaction_to = 0.0, 100.0
    v1.superseded_by = "m2"
    v2 = MemoryRecord.make(MemoryTier.SEMANTIC, "VALUE is 2", "src")
    v2.memory_id = "m2"
    v2.transaction_from, v2.transaction_to = 100.0, None
    v2.revises = "m1"
    return v1, v2


def test_as_of_returns_past_then_current_belief():
    v1, v2 = _versioned_pair()
    view = AsOfView([v2, v1])  # unsorted input on purpose
    # believed at t=50 ⇒ the old belief
    assert [r.memory_id for r in view.as_of(transaction_time=50.0)] == ["m1"]
    # believed at t=150 ⇒ the new belief
    assert [r.memory_id for r in view.as_of(transaction_time=150.0)] == ["m2"]
    # "now" (None) ⇒ only the open belief
    assert [r.memory_id for r in view.as_of()] == ["m2"]
    assert [r.memory_id for r in view.current()] == ["m2"]


def test_belief_history_is_ordered_and_deterministic():
    v1, v2 = _versioned_pair()
    view = AsOfView([v2, v1])
    # from either end, oldest → newest, deterministically
    assert [r.memory_id for r in view.belief_history("m2")] == ["m1", "m2"]
    assert [r.memory_id for r in view.belief_history("m1")] == ["m1", "m2"]


def test_valid_time_axis_is_half_open():
    s = BiTemporalStamp(valid_from=0.0, valid_to=10.0)
    assert s.is_valid_at(5.0) is True
    assert s.is_valid_at(0.0) is True
    assert s.is_valid_at(10.0) is False   # half-open [from, to)
    assert s.is_valid_at(-1.0) is False


# --------------------------------------------------------------------------- #
# 4. No-collapse — closing a stamp does NOT hide a record from live retrieval
#    (A0 does not wire as-of into retrieve/assemble_context).
# --------------------------------------------------------------------------- #
def test_retrieval_ignores_stamps_in_a0():
    fab, _ = _fabric()
    rec = fab.assert_canon("the north star", source="operator")
    assert rec is not None
    # close both stamps — "no longer current" bi-temporally
    rec.valid_to = 1.0
    rec.transaction_to = 1.0
    assert BiTemporalStamp.from_record(rec).is_current() is False
    # ...yet the live retrieval path (canon) still returns it: A0 changed nothing
    got = fab.retrieve("north star", k=5)
    assert any(r.memory_id == rec.memory_id for r in got)
    assert "the north star" in fab.assemble_context("north star", k=5)


# --------------------------------------------------------------------------- #
# 5. No-overclaim — is_current only for fully-open intervals.
# --------------------------------------------------------------------------- #
def test_is_current_cannot_lie():
    assert BiTemporalStamp().is_current() is True
    assert BiTemporalStamp(valid_to=10.0).is_current() is False
    assert BiTemporalStamp(transaction_to=10.0).is_current() is False
    assert BiTemporalStamp(valid_to=1.0, transaction_to=1.0).is_current() is False


# --------------------------------------------------------------------------- #
# 6. Fail-closed — empty / unknown ⇒ [], never fabricated.
# --------------------------------------------------------------------------- #
def test_fail_closed_empty_and_unknown():
    empty = AsOfView([])
    assert empty.as_of() == []
    assert empty.current() == []
    assert empty.belief_history("nope") == []
    v1, v2 = _versioned_pair()
    view = AsOfView([v1, v2])
    assert view.belief_history("does-not-exist") == []


def test_as_of_view_from_fabric_snapshot():
    fab, _ = _fabric()
    fab.assert_canon("canon fact", source="operator")
    view = AsOfView.from_fabric(fab)
    # snapshot is independent; a later write does not change this view
    n_before = len(view.as_of())
    fab.assert_canon("another canon", source="operator")
    assert len(view.as_of()) == n_before


# --------------------------------------------------------------------------- #
# Flag is defined-not-gating in A0: default OFF.
# --------------------------------------------------------------------------- #
def test_durable_memory_flag_defaults_off(monkeypatch):
    monkeypatch.delenv("AUREL_DURABLE_MEMORY", raising=False)
    assert _flag_enabled() is False
    monkeypatch.setenv("AUREL_DURABLE_MEMORY", "1")
    assert _flag_enabled() is True
