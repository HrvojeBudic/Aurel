"""A5 — Deterministic memory consolidation to CANDIDATE.

Consolidation clusters related memories and proposes a single *summary* memory
for each cluster. The summary is always a **CANDIDATE** written through the
existing governed funnel (``request_write``) — never VERIFIED/PROCEDURAL/CANON,
never auto-canonized — and it is linked back to every source with A2
``SUMMARIZES`` edges. Sources are read-only: consolidation never destroys or
alters the memories it summarizes.

Boundary (cross-cutting invariants):

* **Entity proposes, runtime disposes.** The summary is proposed at CANDIDATE and
  re-scored by ``MemoryWritePolicy.evaluate_write`` like any write. The truth
  state is hard-coded CANDIDATE, so no caller (agent or operator) can elevate
  trust through consolidation.
* **Deterministic / stdlib-only.** Clustering is a reproducible greedy pass over
  records sorted by ``memory_id`` using the deterministic ``HashingEmbedder``
  cosine — no ``hash()`` ordering, no randomness. Same inputs ⇒ same clusters and
  same summary text.
* **Provenance preserved.** The summary carries every source id in
  ``evidence_refs``/``links`` and a ``SUMMARIZES`` edge to each source; the source
  records are never mutated.
* **Fail-closed.** Empty input or degenerate clusters (fewer than ``min_size``
  members) produce NOTHING — never a fabricated summary.

Reuses the governed funnels only: ``fabric.request_write`` (the summary) and
``fabric.link`` (the edges). No parallel write path.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from .core_types import MemoryTruthState
from .memory import cosine


@dataclass
class ConsolidationSummary:
    summary_id: str
    source_ids: list[str]
    truth_state: str
    edge_ids: list[str] = field(default_factory=list)
    reason_code: str = "consolidated"

    def to_dict(self) -> dict:
        return {
            "summary_id": self.summary_id,
            "source_ids": self.source_ids,
            "truth_state": self.truth_state,
            "edge_ids": self.edge_ids,
            "reason_code": self.reason_code,
        }


@dataclass
class ConsolidationResult:
    summaries: list[ConsolidationSummary]
    clusters_found: int
    reason_code: str            # "consolidated" | "no_consolidatable_cluster"

    @property
    def produced(self) -> bool:
        return any(s.summary_id for s in self.summaries)


def cluster_memories(
    records: list[Any],
    embedder: Any,
    *,
    threshold: float = 0.5,
    min_size: int = 2,
) -> list[list[Any]]:
    """Deterministically group records by content similarity.

    A greedy single-pass over records sorted by ``memory_id``: each not-yet-taken
    record seeds a cluster and pulls in every later untaken record whose cosine
    similarity to the seed is ``>= threshold``. Embeddings are computed fresh from
    content via the deterministic ``HashingEmbedder``, so the result is fully
    reproducible. Only clusters with at least ``min_size`` members are returned
    (degenerate singletons are dropped — fail-closed)."""
    ordered = sorted(records, key=lambda r: str(getattr(r, "memory_id", "") or ""))
    vectors = {id(r): embedder.embed(r.content) for r in ordered}
    taken: set[int] = set()
    clusters: list[list[Any]] = []
    for seed in ordered:
        if id(seed) in taken:
            continue
        cluster = [seed]
        taken.add(id(seed))
        for other in ordered:
            if id(other) in taken:
                continue
            if cosine(vectors[id(seed)], vectors[id(other)]) >= threshold:
                cluster.append(other)
                taken.add(id(other))
        if len(cluster) >= min_size:
            clusters.append(cluster)
    return clusters


def summarize_cluster(cluster: list[Any]) -> str:
    """Deterministic summary text for a cluster (stdlib-only, no LLM).

    Sources are ordered by ``(content, memory_id)`` and joined — keying on content
    (not the uuid ``memory_id``) so the same set of contents yields byte-identical
    summary text across processes and fresh fabrics."""
    ordered = sorted(cluster, key=lambda r: (r.content, str(getattr(r, "memory_id", "") or "")))
    joined = " | ".join(r.content for r in ordered)
    return f"Consolidated summary of {len(ordered)} memories: {joined}"


def consolidate(
    fabric: Any,
    records: list[Any],
    *,
    writer_kind: str = "runtime",
    created_by: str = "",
    source_run_id: str = "",
    threshold: float = 0.5,
    min_size: int = 2,
    charge: Optional[Callable[[], None]] = None,
) -> ConsolidationResult:
    """Cluster ``records`` and write one governed CANDIDATE summary per cluster,
    with ``SUMMARIZES`` edges back to each source. ``charge`` (if given) is called
    once before each governed sub-write (summary + each edge), so a tool session
    can meter honestly. Fail-closed: no qualifying cluster ⇒ no summary."""
    from .memory_governance import MemoryLinkRequest, MemoryWriteRequest

    on_charge = charge or (lambda: None)
    clusters = cluster_memories(records, fabric.embedder,
                                threshold=threshold, min_size=min_size)
    summaries: list[ConsolidationSummary] = []
    for cluster in clusters:
        source_ids = sorted(str(r.memory_id) for r in cluster)
        content = summarize_cluster(cluster)
        # Summary is ALWAYS candidate — never elevates trust. Provenance to the
        # sources rides evidence_refs/links + the SUMMARIZES edges (memory ids are
        # not trace ids, so they cannot go in source_trace_ids without a governance
        # invalid_trace_reference — see report drift note).
        on_charge()
        decision = fabric.request_write(MemoryWriteRequest(
            content=content,
            proposed_truth_state=MemoryTruthState.CANDIDATE,
            writer_kind=writer_kind,
            created_by=created_by,
            source_run_id=source_run_id,
            evidence_refs=list(source_ids),
            links=list(source_ids),
            confidence=0.5,
            importance=0.5,
        ))
        if not decision.allowed or decision.record is None:
            summaries.append(ConsolidationSummary(
                "", source_ids, decision.effective_truth_state.value,
                reason_code=decision.reason_code))
            continue
        summary_id = decision.record.memory_id
        edge_ids: list[str] = []
        for sid in source_ids:
            on_charge()
            ld = fabric.link(MemoryLinkRequest(
                from_id=summary_id, to_id=sid, relation="summarizes",
                writer_kind=writer_kind, created_by=created_by,
                source_run_id=source_run_id))
            if ld.allowed and ld.edge is not None:
                edge_ids.append(ld.edge.edge_id)
        summaries.append(ConsolidationSummary(
            summary_id, source_ids, decision.effective_truth_state.value,
            edge_ids=edge_ids, reason_code="consolidated"))

    reason = "consolidated" if any(s.summary_id for s in summaries) \
        else "no_consolidatable_cluster"
    return ConsolidationResult(summaries, len(clusters), reason)


__all__ = [
    "ConsolidationSummary",
    "ConsolidationResult",
    "cluster_memories",
    "summarize_cluster",
    "consolidate",
]
