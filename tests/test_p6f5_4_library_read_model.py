"""F5.4 seal — the unified Library read-model (memory + docs + export manifest).

Library is a projection name, not a store: it equals a direct trace projection, it
writes nothing, its truth label is the MIN of the composed tiers, and time-travel
is an honest UNAVAILABLE seam (F8).
"""
from __future__ import annotations

from agentic_runtime import (
    MemoryFabric,
    MemoryTruthState,
    MemoryWriteRequest,
    build_runtime,
)
from agentic_runtime.front_server import (
    CLAIMS_LIBRARY_TIME_TRAVEL,
    LibraryReadModel,
    LiveReadModels,
)
from agentic_runtime.memory_governance import MemoryLinkRequest
from agentic_runtime.memory_projection import MemoryProjection
from agentic_runtime.trace import InMemoryTraceLedger

RUN = "run_lib"


def _seeded_trace():
    trace = InMemoryTraceLedger(run_id=RUN)
    fab = MemoryFabric()
    fab.bind_trace(trace)
    a = fab.request_write(MemoryWriteRequest(
        content="the meeting is on monday", proposed_truth_state=MemoryTruthState.CANDIDATE,
        writer_kind="operator", source_run_id=RUN)).record
    b = fab.request_write(MemoryWriteRequest(
        content="project kickoff notes", proposed_truth_state=MemoryTruthState.CANDIDATE,
        writer_kind="operator", source_run_id=RUN)).record
    fab.link(MemoryLinkRequest(from_id=a.memory_id, to_id=b.memory_id,
                               relation="relates_to", writer_kind="operator",
                               source_run_id=RUN))
    fab.promote(b.memory_id, MemoryTruthState.VERIFIED, evidence_refs=["ev"], actor="operator")
    # An agent's CANON write is denied → a rejected/audit record.
    fab.request_write(MemoryWriteRequest(
        content="agent tries canon", proposed_truth_state=MemoryTruthState.CANON,
        writer_kind="agent", source_run_id=RUN))
    return trace, a.memory_id, b.memory_id


class _StubManifest:
    def to_dict(self) -> dict:
        return {"manifest_id": "m1", "included_refs": ["ref-a"]}


# --- composition ------------------------------------------------------------------

def test_library_composes_memory_docs_and_manifest():
    trace, a, b = _seeded_trace()
    lib = LibraryReadModel.from_trace(trace)
    d = lib.to_dict()

    # assets: canonical docs with existence (README exists in the repo).
    ids = {x["doc_id"] for x in d["assets"]}
    assert "README" in ids
    assert any(x["doc_id"] == "README" and x["exists"] for x in d["assets"])

    # memory by tier: b promoted to verified, a stays candidate.
    tiers = d["memory_by_tier"]
    assert b in tiers.get("verified", [])
    assert a in tiers.get("candidate", [])

    # rejected audit record present; manifest UNAVAILABLE (none injected); F8 seam.
    assert d["rejected"]
    assert d["manifest"]["status"] == "UNAVAILABLE"
    assert d["claims_time_travel"] is False and CLAIMS_LIBRARY_TIME_TRAVEL is False


def test_library_equals_direct_projection():
    trace, _a, _b = _seeded_trace()
    lib = LibraryReadModel.from_trace(trace)
    proj = MemoryProjection.from_trace(trace)
    # rejected + tier grouping match the underlying projection exactly.
    assert lib.rejected() == list(proj.rejected)
    direct_tiers: dict[str, list[str]] = {}
    for mid in proj.current_ids:
        direct_tiers.setdefault(proj.states.get(mid, ""), []).append(mid)
    assert lib.memory_by_tier() == {t: sorted(v) for t, v in sorted(direct_tiers.items())}


def test_versions_and_provenance_chain():
    trace, a, b = _seeded_trace()
    lib = LibraryReadModel.from_trace(trace)
    assert lib.versions(b) == [b]          # known id, no supersession ⇒ [itself]
    assert lib.versions("nope") == []      # unknown id ⇒ [] (fail-closed)
    chain = lib.provenance_chain(b)
    assert chain["versions"] == [b]
    assert [a, b, "relates_to"] in chain["edges"]


def test_min_truth_state_is_weakest():
    trace, _a, _b = _seeded_trace()
    lib = LibraryReadModel.from_trace(trace)
    # current = {candidate a, verified b} ⇒ MIN = candidate.
    assert lib.min_truth_state() == "candidate"


def test_injected_manifest_is_available():
    trace, _a, _b = _seeded_trace()
    lib = LibraryReadModel.from_trace(trace, manifest=_StubManifest())
    m = lib.manifest()
    assert m["status"] == "AVAILABLE" and m["manifest_id"] == "m1"


# --- purity / determinism ---------------------------------------------------------

def test_library_is_zero_write_and_deterministic():
    trace, _a, _b = _seeded_trace()
    before = len(list(trace.replay()))
    d1 = LibraryReadModel.from_trace(trace).to_dict()
    d2 = LibraryReadModel.from_trace(trace).to_dict()
    after = len(list(trace.replay()))
    assert after == before          # zero writes
    assert d1 == d2                  # deterministic


# --- live-read integration --------------------------------------------------------

def test_library_via_live_read_registry():
    rt = build_runtime()  # empty memory ⇒ honest empty tiers, docs still listed
    status, payload = LiveReadModels(rt).read("/read/library")
    assert status == 200 and payload["live"] is True and payload["model"] == "library"
    assert payload["memory_by_tier"] == {}
    assert payload["min_truth_state"] is None
    assert payload["manifest"]["status"] == "UNAVAILABLE"
    assert payload["claims_time_travel"] is False
    assert any(a["doc_id"] == "README" for a in payload["assets"])
