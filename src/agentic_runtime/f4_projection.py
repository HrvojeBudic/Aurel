"""
f4_projection.py — F4.4 read-only projections over the cognition surface.

Read-models behind the Front (Signal `context_refs`, WorkOPS turn view): project a
finished loop run (turns, context_refs, termination) and a single assembled
ContextLoom bundle (provenance mix, budget outcome, external-fenced render), all
without executing anything.
"""
from __future__ import annotations

from typing import Any

from .context_loom.loom import ContextBundle


def project_loop_run(result: Any) -> dict:
    """Read-only view of a LoopResult (or its to_dict)."""
    d = result.to_dict() if hasattr(result, "to_dict") else dict(result)
    turns = d.get("turns", [])
    return {
        "terminated": d.get("terminated"),
        "executed": d.get("executed"),
        "turn_count": len(turns),
        "context_refs": d.get("context_refs", []),
        "turns": turns,
    }


def project_context_bundle(bundle: ContextBundle) -> dict:
    """Read-only view of one assembled bundle: provenance mix + budget outcome."""
    by_kind: dict[str, int] = {}
    external = 0
    for item in bundle.items:
        by_kind[item.source_kind.value] = by_kind.get(item.source_kind.value, 0) + 1
        if item.is_external_origin:
            external += 1
    return {
        "context_ref": bundle.context_ref,
        "item_count": len(bundle.items),
        "external_items": external,
        "by_source_kind": dict(sorted(by_kind.items())),
        "total_est_tokens": bundle.total_est_tokens,
        "dropped": len(bundle.dropped),
        "compressed": len(bundle.compressed),
        "rendered_chars": len(bundle.to_prompt()),
    }
