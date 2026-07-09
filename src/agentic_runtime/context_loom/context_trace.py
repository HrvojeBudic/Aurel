"""
context_trace.py — F4.2 bind an assembled context bundle into the trace.

Every context an entity reasons over must be auditable and replayable: this emits
a hash-chained ``context_assembly`` praxis event carrying the bundle's
``context_ref`` (the Front Signal reference) plus leak-safe provenance — item
hashes, source kinds, taint labels, drops, and compressions — but **never the raw
content**. ``ContextBundle.to_dict`` already excludes content, so the trace holds
references, not the data itself.

The ``context_ref`` is placed in the event **summary** (not only details) so it
survives a pure trace replay (the replay projection carries summaries, not
details) — that is what makes the Front Signal ``context_refs`` reconstructable
from the trace alone.
"""
from __future__ import annotations

from typing import Any, Iterable

from ..core_types import PraxisEventRecord
from .loom import ContextBundle

CONTEXT_ASSEMBLY_EVENT = "context_assembly"


def context_assembly_summary(bundle: ContextBundle) -> str:
    """One-line, replay-surviving summary. Carries the full context_ref."""
    return (
        f"context_ref={bundle.context_ref} items={len(bundle.items)} "
        f"est_tokens={bundle.total_est_tokens} external={bundle.has_external} "
        f"dropped={len(bundle.dropped)} compressed={len(bundle.compressed)}"
    )


def context_assembly_details(bundle: ContextBundle) -> dict:
    """Leak-safe rich details: hashes + provenance, never raw content."""
    return bundle.to_dict()


def bind_context_to_trace(
    trace: Any,
    *,
    run_id: str,
    agent_id: str,
    subject_id: str,
    bundle: ContextBundle,
) -> PraxisEventRecord:
    """Append a hash-chained context_assembly event; return the record."""
    rec = PraxisEventRecord.make(
        run_id=run_id,
        agent_id=agent_id,
        event_type=CONTEXT_ASSEMBLY_EVENT,
        subject_id=subject_id,
        summary=context_assembly_summary(bundle),
        details=context_assembly_details(bundle),
    )
    return trace.append_praxis_event(rec)


def context_refs_from_replay(replay: Iterable[dict]) -> list[str]:
    """Reconstruct the Front Signal context_refs from a pure trace replay.

    Reads only replayed summaries, proving the refs survive replay without the
    original records.
    """
    refs: list[str] = []
    for ev in replay:
        if ev.get("kind") != "praxis_event":
            continue
        if ev.get("event_type") != CONTEXT_ASSEMBLY_EVENT:
            continue
        for tok in str(ev.get("summary", "")).split():
            if tok.startswith("context_ref="):
                refs.append(tok.split("=", 1)[1])
                break
    return refs
