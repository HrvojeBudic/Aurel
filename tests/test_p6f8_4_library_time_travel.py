"""F8.4 seal — Library as-of time-travel via memory_asof (AUREL_SYSTEM)."""
from __future__ import annotations

import pytest

from agentic_runtime import build_runtime
from agentic_runtime.core_types import MemoryRecord, MemoryTier, MemoryTruthState
from agentic_runtime.front_server import (
    LiveReadModels,
    LibraryReadModel,
    claims_library_time_travel,
    memory_asof_available,
)
from agentic_runtime.trace import InMemoryTraceLedger

RUN = "run_f8_4"


def _versioned_pair():
    v1 = MemoryRecord.make(MemoryTier.SEMANTIC, "VALUE is 1", "src")
    v1.memory_id = "m1"
    v1.truth_state = MemoryTruthState.CANDIDATE
    v1.transaction_from, v1.transaction_to = 0.0, 100.0
    v1.superseded_by = "m2"
    v2 = MemoryRecord.make(MemoryTier.SEMANTIC, "VALUE is 2", "src")
    v2.memory_id = "m2"
    v2.truth_state = MemoryTruthState.VERIFIED
    v2.transaction_from, v2.transaction_to = 100.0, None
    v2.revises = "m1"
    return v1, v2


def _seeded_fabric():
    trace = InMemoryTraceLedger(run_id=RUN)
    from agentic_runtime import MemoryFabric

    fab = MemoryFabric()
    fab.bind_trace(trace)
    v1, v2 = _versioned_pair()
    fab.by_id[v1.memory_id] = v1
    fab.by_id[v2.memory_id] = v2
    return trace, fab, v1, v2


@pytest.fixture(autouse=True)
def _system_off(monkeypatch):
    monkeypatch.delenv("AUREL_SYSTEM", raising=False)


def test_claims_time_travel_false_when_flag_off():
    assert memory_asof_available() is False
    assert claims_library_time_travel() is False
    trace, fab, _v1, _v2 = _seeded_fabric()
    lib = LibraryReadModel.from_trace(trace, fabric=fab)
    assert lib.to_dict()["claims_time_travel"] is False


def test_as_of_unavailable_when_flag_off():
    trace, fab, _v1, _v2 = _seeded_fabric()
    lib = LibraryReadModel.from_trace(trace, fabric=fab)
    with pytest.raises(ValueError, match="UNAVAILABLE"):
        lib.as_of(transaction_time=50.0)


def test_as_of_returns_past_then_current_belief(monkeypatch):
    monkeypatch.setenv("AUREL_SYSTEM", "1")
    trace, fab, v1, v2 = _seeded_fabric()
    lib = LibraryReadModel.from_trace(trace, fabric=fab)
    assert claims_library_time_travel() is True

    past = lib.as_of(transaction_time=50.0)
    tiers_past = past.memory_by_tier()
    assert "m1" in tiers_past.get("candidate", [])
    assert "m2" not in sum(tiers_past.values(), [])

    future = lib.as_of(transaction_time=150.0)
    tiers_now = future.memory_by_tier()
    assert "m2" in tiers_now.get("verified", [])
    assert "m1" not in sum(tiers_now.values(), [])

    assert past.versions("m1") == ["m1"]
    assert future.versions("m2") == ["m2"]


def test_empty_as_of_param_byte_identical_to_current(monkeypatch):
    monkeypatch.setenv("AUREL_SYSTEM", "1")
    trace, fab, _v1, _v2 = _seeded_fabric()
    lib = LibraryReadModel.from_trace(trace, fabric=fab)
    baseline = lib.to_dict()
    assert lib.current().to_dict() == baseline
    assert lib.as_of().to_dict() == baseline


def test_library_read_as_of_live(monkeypatch):
    monkeypatch.setenv("AUREL_SYSTEM", "1")
    kernel = build_runtime()
    v1, v2 = _versioned_pair()
    kernel.memory.by_id[v1.memory_id] = v1
    kernel.memory.by_id[v2.memory_id] = v2

    reads = LiveReadModels(kernel)
    status, body = reads.read("/read/library?as_of=50")
    assert status == 200
    assert body["live"] is True
    assert body["claims_time_travel"] is True
    assert body["as_of"] == {"valid_time": None, "transaction_time": 50.0}
    assert "m1" in body["memory_by_tier"].get("candidate", [])

    status2, current = reads.read("/read/library")
    assert status2 == 200
    assert "as_of" not in current
    assert current["claims_time_travel"] is True


def test_library_read_as_of_unavailable_when_flag_off():
    kernel = build_runtime()
    v1, v2 = _versioned_pair()
    kernel.memory.by_id[v1.memory_id] = v1
    kernel.memory.by_id[v2.memory_id] = v2

    status, body = LiveReadModels(kernel).read("/read/library?as_of=50")
    assert status == 200
    assert body["available"] is False
    assert body["status"] == "UNAVAILABLE"
    assert body["claims_time_travel"] is False
