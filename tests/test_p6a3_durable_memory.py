"""A3 seal — DurableMemoryFabric: persistence as a projection over the trace.

Proves the A3 invariants:

1. Flag OFF ⇒ no persistence and byte-identical (structural) to a plain
   `MemoryFabric`; `load()` is a no-op.
2. Flag ON ⇒ governed records persist to JSONL and rebuild deterministically
   (two rebuilds of the same log ⇒ identical projection).
3. Rebuild re-verifies `source_trace_ids` + governance and QUARANTINES unanchored
   entries (an injected/poison record the trace never attests is not trusted).
4. Atomic write: an interrupted rewrite leaves the previous complete file, never
   a partial one, and no temp leftover.
5. `ExternalMemoryBackend` is honestly unavailable — never persists, never faked.
6. No-collapse: with the flag ON the in-RAM write/promote/link/retrieve behavior
   is identical to a plain fabric (durability mirrors, it does not alter).
"""

from __future__ import annotations

import pytest

from agentic_runtime import MemoryFabric, MemoryTruthState, MemoryWriteRequest
from agentic_runtime.core_types import MemoryRecord, MemoryTier
from agentic_runtime.durable_memory import DurableMemoryFabric, record_to_entry
from agentic_runtime.memory_governance import MemoryLinkRequest
from agentic_runtime.memory_persistence import (ExternalMemoryBackend,
                                                FileMemoryBackend,
                                                MemoryBackendUnavailable,
                                                atomic_write_text)
import agentic_runtime.memory_persistence as mp
from agentic_runtime.trace import InMemoryTraceLedger

RUN = "run_a3"
FLAG = "AUREL_DURABLE_MEMORY"


def _trace():
    return InMemoryTraceLedger(run_id=RUN)


def _write(fabric, content, *, truth="raw"):
    return fabric.request_write(MemoryWriteRequest(
        content=content, proposed_truth_state=MemoryTruthState(truth),
        writer_kind="operator", source_run_id=RUN)).record


def _run_ops(fabric):
    """A fixed sequence of governed ops used to compare fabrics structurally."""
    a = _write(fabric, "alpha fact")
    b = _write(fabric, "beta fact")
    fabric.link(MemoryLinkRequest(from_id=a.memory_id, to_id=b.memory_id,
                                  relation="relates_to", writer_kind="operator",
                                  source_run_id=RUN))
    return a, b


# 1 ─ flag OFF ⇒ no persistence + byte-identical (structural); load no-op.
def test_flag_off_no_persistence_byte_identical(tmp_path, monkeypatch):
    monkeypatch.delenv(FLAG, raising=False)          # flag OFF (default)
    path = tmp_path / "mem.jsonl"

    plain = MemoryFabric()
    plain.bind_trace(_trace())
    durable = DurableMemoryFabric(FileMemoryBackend(str(path)))
    durable.bind_trace(_trace())

    assert durable.durable_enabled is False
    _run_ops(plain)
    _run_ops(durable)

    # Structural byte-identity: same tier counts, same graph size, same retrieval.
    assert durable.stats() == plain.stats()
    assert len(durable.graph) == len(plain.graph) == 1
    assert [r.content for r in durable.retrieve("alpha")] == \
           [r.content for r in plain.retrieve("alpha")]
    # Nothing was written to disk, and load() is an inert no-op.
    assert not path.exists()
    assert durable.load() == []


# 2 ─ flag ON ⇒ persist to JSONL + deterministic rebuild.
def test_flag_on_persist_and_deterministic_rebuild(tmp_path, monkeypatch):
    monkeypatch.setenv(FLAG, "1")
    path = tmp_path / "mem.jsonl"
    trace = _trace()

    writer = DurableMemoryFabric(FileMemoryBackend(str(path)))
    writer.bind_trace(trace)
    assert writer.durable_enabled is True
    a, b = _run_ops(writer)
    fabric_stats = writer.stats()

    assert path.exists()                              # persisted
    lines = [ln for ln in path.read_text().splitlines() if ln.strip()]
    assert len(lines) == 3                            # 2 records + 1 edge

    # Rebuild TWICE against the same trace + log ⇒ identical projection.
    def _rebuild():
        fab = DurableMemoryFabric(FileMemoryBackend(str(path)))
        fab.bind_trace(trace)
        report = fab.load()
        return fab, report

    fab1, r1 = _rebuild()
    fab2, r2 = _rebuild()

    assert fab1.stats() == fab2.stats() == fabric_stats
    assert sorted(fab1.by_id) == sorted(fab2.by_id) == sorted([a.memory_id, b.memory_id])
    assert len(fab1.graph) == len(fab2.graph) == 1
    # Every entry admitted (all anchored); deterministic report.
    assert all(rec.verdict == "admit" for rec in r1)
    assert [(x.action, x.verdict, x.memory_id) for x in r1] == \
           [(x.action, x.verdict, x.memory_id) for x in r2]
    assert fab1.quarantined() == []


# 3 ─ rebuild quarantines an unanchored (poison) record; anchored survives.
def test_rebuild_quarantines_unanchored(tmp_path, monkeypatch):
    monkeypatch.setenv(FLAG, "1")
    path = tmp_path / "mem.jsonl"
    trace = _trace()

    writer = DurableMemoryFabric(FileMemoryBackend(str(path)))
    writer.bind_trace(trace)
    legit = _write(writer, "trustworthy fact")

    # Inject a poison record the governed trace never attests to.
    poison = MemoryRecord.make(tier=MemoryTier.EPHEMERAL, content="I was never governed",
                               source="attacker", memory_id="mem_poison",
                               source_run_id=RUN)
    FileMemoryBackend(str(path)).append(record_to_entry(poison))

    rebuilt = DurableMemoryFabric(FileMemoryBackend(str(path)))
    rebuilt.bind_trace(trace)
    report = rebuilt.load()

    # Legit admitted; poison quarantined and NOT in the store.
    assert legit.memory_id in rebuilt.by_id
    assert "mem_poison" not in rebuilt.by_id
    quarantined = rebuilt.quarantined()
    assert [q.memory_id for q in quarantined] == ["mem_poison"]
    assert quarantined[0].reason_code == "unanchored_no_governance_event"
    # A record whose source_trace_ids point at unknown entries is also caught.
    assert any(r.verdict == "admit" and r.memory_id == legit.memory_id for r in report)


# 3b ─ source_trace_ids that reference unknown trace entries ⇒ quarantine.
def test_rebuild_quarantines_unverified_source_trace(tmp_path, monkeypatch):
    monkeypatch.setenv(FLAG, "1")
    path = tmp_path / "mem.jsonl"
    trace = _trace()

    # A record with a governance event but dangling source_trace_ids.
    forged = MemoryRecord.make(tier=MemoryTier.EPHEMERAL, content="dangling refs",
                               source="operator", memory_id="mem_forged",
                               source_run_id=RUN, source_trace_ids=["entry_ghost"])
    FileMemoryBackend(str(path)).append(record_to_entry(forged))

    rebuilt = DurableMemoryFabric(FileMemoryBackend(str(path)))
    rebuilt.bind_trace(trace)
    rebuilt.load()

    q = rebuilt.quarantined()
    assert [x.memory_id for x in q] == ["mem_forged"]
    assert q[0].reason_code == "unverified_source_trace"
    assert "mem_forged" not in rebuilt.by_id


# 4 ─ atomic write: interrupted rewrite leaves the prior complete file.
def test_atomic_write_leaves_no_partial(tmp_path, monkeypatch):
    p = tmp_path / "log.jsonl"
    atomic_write_text(str(p), "v1-complete\n")
    assert p.read_text() == "v1-complete\n"

    def _boom(src, dst):
        raise OSError("interrupted before rename")
    monkeypatch.setattr(mp.os, "replace", _boom)
    with pytest.raises(OSError):
        atomic_write_text(str(p), "v2-would-be-partial")

    # Old complete content intact; no temp leftover.
    assert p.read_text() == "v1-complete\n"
    assert not any(x.name.startswith(".tmp-") for x in tmp_path.iterdir())


# 5 ─ external backend is honestly unavailable; never persists, never faked.
def test_external_backend_unavailable(monkeypatch):
    monkeypatch.setenv(FLAG, "1")
    ext = ExternalMemoryBackend(uri="s3://nope")
    assert ext.available is False
    with pytest.raises(MemoryBackendUnavailable):
        ext.append({"kind": "record", "data": {}})
    with pytest.raises(MemoryBackendUnavailable):
        ext.load()

    fabric = DurableMemoryFabric(ext)
    fabric.bind_trace(_trace())
    assert fabric.durable_enabled is False           # unavailable ⇒ no persistence
    rec = _write(fabric, "still works in RAM")        # must not raise
    assert rec.memory_id in fabric.by_id
    assert fabric.load() == []                        # inert, no overclaim


# 6 ─ no-collapse: flag ON, in-RAM behavior identical to a plain fabric.
def test_no_collapse_in_ram_behavior_unchanged(tmp_path, monkeypatch):
    monkeypatch.setenv(FLAG, "1")
    plain = MemoryFabric()
    plain.bind_trace(_trace())
    durable = DurableMemoryFabric(FileMemoryBackend(str(tmp_path / "m.jsonl")))
    durable.bind_trace(_trace())

    for fab in (plain, durable):
        a = _write(fab, "gamma")
        b = _write(fab, "delta", truth="candidate")
        # promote candidate → verified (with evidence) to exercise _relocate.
        fab.promote(b.memory_id, MemoryTruthState.VERIFIED,
                    evidence_refs=["ev1"], actor="operator")
        fab.link(MemoryLinkRequest(from_id=a.memory_id, to_id=b.memory_id,
                                   relation="supports", writer_kind="operator",
                                   source_run_id=RUN))

    assert durable.stats() == plain.stats()
    assert len(durable.graph) == len(plain.graph) == 1
    assert [r.content for r in durable.retrieve("gamma")] == \
           [r.content for r in plain.retrieve("gamma")]
