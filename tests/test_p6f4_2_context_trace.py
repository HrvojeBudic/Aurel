"""F4.2 seal — bind an assembled context bundle into the trace.

  1. Binding emits a hash-chained context_assembly praxis event (head advances).
  2. Replay-safe — the context_ref survives a pure trace replay (it lives in the
     summary), so context_refs_from_replay reconstructs the Front Signal refs.
  3. Leak-safe — neither the summary nor the details carry raw item content; only
     hashes / provenance / drops / compressions.
  4. Deterministic details; multiple assemblies → multiple refs in order.
"""
from __future__ import annotations

import json

from agentic_runtime.context_loom import (
    assemble,
    bind_context_to_trace,
    context_refs_from_replay,
    make_context_item,
)
from agentic_runtime.context_loom.context_trace import (
    CONTEXT_ASSEMBLY_EVENT,
    context_assembly_details,
)
from agentic_runtime.external_ingress import SourceKind
from agentic_runtime.trace import InMemoryTraceLedger

SECRET = "TOP-SECRET-SCRAPED-PAYLOAD-42"


def _bundle():
    return assemble([
        make_context_item("operator goal", SourceKind.OPERATOR, "op"),
        make_context_item(SECRET, SourceKind.SCRAPE, "scrape"),
    ])


# --------------------------------------------------------------------------- #
# 1. Emits a hash-chained event.
# --------------------------------------------------------------------------- #
def test_bind_appends_hash_chained_event():
    trace = InMemoryTraceLedger(run_id="run_f42")
    before = trace.head
    rec = bind_context_to_trace(
        trace, run_id="run_f42", agent_id="agent", subject_id="intent1",
        bundle=_bundle(),
    )
    assert rec.event_type == CONTEXT_ASSEMBLY_EVENT
    assert rec.entry_hash and rec.entry_hash != before  # chain advanced
    assert trace.head == rec.entry_hash


# --------------------------------------------------------------------------- #
# 2. Replay-safe context_ref.
# --------------------------------------------------------------------------- #
def test_context_ref_survives_replay():
    trace = InMemoryTraceLedger(run_id="run_f42")
    bundle = _bundle()
    bind_context_to_trace(
        trace, run_id="run_f42", agent_id="agent", subject_id="i", bundle=bundle,
    )
    refs = context_refs_from_replay(trace.replay())
    assert refs == [bundle.context_ref]


def test_multiple_assemblies_yield_ordered_refs():
    trace = InMemoryTraceLedger(run_id="run_f42")
    b1 = assemble([make_context_item("a", SourceKind.OPERATOR, "op")])
    b2 = assemble([make_context_item("b", SourceKind.OPERATOR, "op")])
    for b in (b1, b2):
        bind_context_to_trace(trace, run_id="run_f42", agent_id="ag",
                              subject_id="i", bundle=b)
    assert context_refs_from_replay(trace.replay()) == [b1.context_ref, b2.context_ref]


# --------------------------------------------------------------------------- #
# 3. Leak-safe.
# --------------------------------------------------------------------------- #
def test_details_and_summary_do_not_leak_raw_content():
    bundle = _bundle()
    details = context_assembly_details(bundle)
    blob = json.dumps(details)
    assert SECRET not in blob                      # raw scraped content absent
    # But the provenance/hash IS present (auditable).
    ext_hash = next(i.content_hash for i in bundle.items if i.is_external_origin)
    assert ext_hash in blob

    trace = InMemoryTraceLedger(run_id="r")
    rec = bind_context_to_trace(trace, run_id="r", agent_id="a",
                                subject_id="i", bundle=bundle)
    assert SECRET not in rec.summary
    assert bundle.context_ref in rec.summary


# --------------------------------------------------------------------------- #
# 4. Deterministic details.
# --------------------------------------------------------------------------- #
def test_details_are_deterministic():
    bundle = _bundle()
    assert context_assembly_details(bundle) == context_assembly_details(bundle)
