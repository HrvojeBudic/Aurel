"""P5-TRACE-E Golden Thread / causal graph — a read-only causal continuity model.

The Golden Thread links P3→P4→P5→Evidence→Decision→Feed refs into a legible
causal story for operator audit. It is **diagnostic only**: it does not execute,
schedule, replay, repair, or mutate anything, and it is not a scheduler, planner,
or execution DAG. Missing causal links stay explicit as ``MISSING_LINK`` edges
with reasons. Nothing here claims ``TRACE_VERIFIED`` unless it references a P5-D
resolver decision — and even then the verdict lives on the decision, not here.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum
from typing import Any

from .trace_hash import (
    AurelTraceError,
    TraceTruthLabel,
    canonical_trace_json,
    require_nonempty,
    trace_sha,
)


class CausalNodeKind(str, Enum):
    """Closed-world causal node kinds."""

    P3_INTENT = "P3_INTENT"
    P3_WORKFLOW_UNIT = "P3_WORKFLOW_UNIT"
    P4_JOB = "P4_JOB"
    P4_ATTEMPT = "P4_ATTEMPT"
    P4_OUTCOME = "P4_OUTCOME"
    TRACE_EVENT = "TRACE_EVENT"
    EVIDENCE_REF = "EVIDENCE_REF"
    VERIFICATION_DECISION = "VERIFICATION_DECISION"
    PROJECTION_FEED_ENTRY = "PROJECTION_FEED_ENTRY"
    TIME_SLICE = "TIME_SLICE"


class CausalEdgeKind(str, Enum):
    """Closed-world causal edge kinds."""

    CAUSED = "CAUSED"
    PRODUCED = "PRODUCED"
    REFERENCED = "REFERENCED"
    VERIFIED_BY = "VERIFIED_BY"
    PROJECTED_AS = "PROJECTED_AS"
    BELONGS_TO_SLICE = "BELONGS_TO_SLICE"
    MISSING_LINK = "MISSING_LINK"


def _stable_id(prefix: str, material: dict[str, Any]) -> str:
    return f"{prefix}-" + trace_sha(canonical_trace_json(material))[:40]


@dataclass(frozen=True)
class CausalGraphNode:
    """One diagnostic causal node. Not executable."""

    node_id: str
    node_kind: CausalNodeKind
    source_ref: str
    truth_label: TraceTruthLabel = TraceTruthLabel.TRACE_BOUND
    metadata: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        require_nonempty(self, "node_id", "source_ref")
        if not isinstance(self.node_kind, CausalNodeKind):
            raise AurelTraceError(
                f"unknown causal node kind {self.node_kind!r}; node kinds are closed-world"
            )
        if self.truth_label is TraceTruthLabel.TRACE_INTEGRITY_VERIFIED:
            raise AurelTraceError("a causal node is a diagnostic reference, not a verdict")

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "node_kind": self.node_kind.value,
            "source_ref": self.source_ref,
            "metadata": [list(pair) for pair in self.metadata],
            "truth_label": self.truth_label.value,
        }


@dataclass(frozen=True)
class CausalGraphEdge:
    """One diagnostic causal edge. Not executable."""

    edge_id: str
    edge_kind: CausalEdgeKind
    from_node_id: str
    to_node_id: str
    missing_reason: str | None = None
    truth_label: TraceTruthLabel = TraceTruthLabel.TRACE_BOUND

    def __post_init__(self) -> None:
        require_nonempty(self, "edge_id", "from_node_id", "to_node_id")
        if not isinstance(self.edge_kind, CausalEdgeKind):
            raise AurelTraceError(
                f"unknown causal edge kind {self.edge_kind!r}; edge kinds are closed-world"
            )
        if self.edge_kind is CausalEdgeKind.MISSING_LINK and not (
            self.missing_reason or ""
        ).strip():
            raise AurelTraceError("a MISSING_LINK edge must carry a missing_reason")

    def to_dict(self) -> dict[str, Any]:
        return {
            "edge_id": self.edge_id,
            "edge_kind": self.edge_kind.value,
            "from_node_id": self.from_node_id,
            "to_node_id": self.to_node_id,
            "missing_reason": self.missing_reason,
            "truth_label": self.truth_label.value,
        }


@dataclass(frozen=True)
class GoldenThreadSegment:
    """One causal segment inside the Golden Thread. Read-only."""

    segment_id: str
    segment_kind: str
    source_ref: str
    target_ref: str
    causal_order: int
    evidence_ref_ids: tuple[str, ...] = ()
    decision_ref_ids: tuple[str, ...] = ()
    feed_entry_ref_ids: tuple[str, ...] = ()
    missing_links: tuple[str, ...] = ()
    truth_label: TraceTruthLabel = TraceTruthLabel.TRACE_BOUND

    def __post_init__(self) -> None:
        require_nonempty(self, "segment_id", "segment_kind", "source_ref", "target_ref")
        if self.causal_order < 0:
            raise AurelTraceError("causal_order must not be negative")
        if self.truth_label is TraceTruthLabel.TRACE_INTEGRITY_VERIFIED:
            raise AurelTraceError(
                "a golden thread segment links refs; it does not itself verify"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "segment_id": self.segment_id,
            "segment_kind": self.segment_kind,
            "source_ref": self.source_ref,
            "target_ref": self.target_ref,
            "causal_order": self.causal_order,
            "evidence_ref_ids": list(self.evidence_ref_ids),
            "decision_ref_ids": list(self.decision_ref_ids),
            "feed_entry_ref_ids": list(self.feed_entry_ref_ids),
            "missing_links": list(self.missing_links),
            "truth_label": self.truth_label.value,
        }


@dataclass(frozen=True)
class GoldenThreadRef:
    """Stable reference to one causal continuity chain."""

    golden_thread_ref_id: str
    root_target_id: str
    root_target_kind: str
    segment_count: int
    head_segment_id: str | None = None
    truth_label: TraceTruthLabel = TraceTruthLabel.TRACE_BOUND

    def __post_init__(self) -> None:
        require_nonempty(self, "golden_thread_ref_id", "root_target_id", "root_target_kind")
        if self.segment_count < 0:
            raise AurelTraceError("segment_count must not be negative")
        if self.truth_label is TraceTruthLabel.TRACE_INTEGRITY_VERIFIED:
            raise AurelTraceError("a golden thread ref is a link, not a verdict")

    def to_dict(self) -> dict[str, Any]:
        return {
            "golden_thread_ref_id": self.golden_thread_ref_id,
            "root_target_id": self.root_target_id,
            "root_target_kind": self.root_target_kind,
            "segment_count": self.segment_count,
            "head_segment_id": self.head_segment_id,
            "truth_label": self.truth_label.value,
        }


@dataclass(frozen=True)
class GoldenThreadGraph:
    """Read-only graph-shaped causal continuity model. Diagnostic only."""

    graph_id: str
    golden_thread_ref: GoldenThreadRef
    nodes: tuple[CausalGraphNode, ...]
    edges: tuple[CausalGraphEdge, ...]
    missing_links: tuple[str, ...] = ()
    truth_label: TraceTruthLabel = TraceTruthLabel.TRACE_BOUND

    # Locked: a causal graph is diagnostic — never a scheduler/planner/execution DAG.
    executes: bool = False
    schedules: bool = False
    replays: bool = False
    mutates: bool = False
    repairs: bool = False

    def __post_init__(self) -> None:
        require_nonempty(self, "graph_id")
        for field_name in ("executes", "schedules", "replays", "mutates", "repairs"):
            if getattr(self, field_name) is True:
                raise AurelTraceError(
                    f"{field_name} must be False — the causal graph is a diagnostic read "
                    "model, not a scheduler/planner/execution/replay engine"
                )
        if self.truth_label is TraceTruthLabel.TRACE_INTEGRITY_VERIFIED:
            raise AurelTraceError("a causal graph is diagnostic, not a verdict")

    def to_dict(self) -> dict[str, Any]:
        return {
            "graph_id": self.graph_id,
            "golden_thread_ref": self.golden_thread_ref.to_dict(),
            "nodes": [n.to_dict() for n in self.nodes],
            "edges": [e.to_dict() for e in self.edges],
            "missing_links": list(self.missing_links),
            "executes": self.executes,
            "schedules": self.schedules,
            "replays": self.replays,
            "mutates": self.mutates,
            "repairs": self.repairs,
            "truth_label": self.truth_label.value,
        }


def build_golden_thread_segment(
    *,
    segment_kind: str,
    source_ref: str,
    target_ref: str,
    causal_order: int,
    evidence_ref_ids: Sequence[str] = (),
    decision_ref_ids: Sequence[str] = (),
    feed_entry_ref_ids: Sequence[str] = (),
    missing_links: Sequence[str] = (),
) -> GoldenThreadSegment:
    segment_id = _stable_id(
        "gts",
        {
            "segment_kind": segment_kind,
            "source_ref": source_ref,
            "target_ref": target_ref,
            "causal_order": causal_order,
        },
    )
    return GoldenThreadSegment(
        segment_id=segment_id,
        segment_kind=segment_kind,
        source_ref=source_ref,
        target_ref=target_ref,
        causal_order=causal_order,
        evidence_ref_ids=tuple(evidence_ref_ids),
        decision_ref_ids=tuple(decision_ref_ids),
        feed_entry_ref_ids=tuple(feed_entry_ref_ids),
        missing_links=tuple(missing_links),
    )


def build_golden_thread_ref(
    *,
    root_target_id: str,
    root_target_kind: str,
    segments: Sequence[GoldenThreadSegment],
) -> GoldenThreadRef:
    ordered = sorted(segments, key=lambda s: s.causal_order)
    head_segment_id = ordered[-1].segment_id if ordered else None
    golden_thread_ref_id = _stable_id(
        "gtref",
        {
            "root_target_id": root_target_id,
            "root_target_kind": root_target_kind,
            "segment_ids": [s.segment_id for s in ordered],
        },
    )
    return GoldenThreadRef(
        golden_thread_ref_id=golden_thread_ref_id,
        root_target_id=root_target_id,
        root_target_kind=root_target_kind,
        segment_count=len(ordered),
        head_segment_id=head_segment_id,
    )


def build_causal_graph(
    *,
    golden_thread_ref: GoldenThreadRef,
    segments: Sequence[GoldenThreadSegment],
) -> GoldenThreadGraph:
    """Derive a read-only causal graph from Golden Thread segments.

    Each segment becomes a ``source_ref → target_ref`` ``CAUSED`` edge; every
    segment-level missing link becomes a ``MISSING_LINK`` edge carrying its reason.
    Nodes are the distinct refs, kinded generically as ``TRACE_EVENT`` unless a
    caller supplies richer segments later.
    """

    ordered = sorted(segments, key=lambda s: s.causal_order)
    nodes: dict[str, CausalGraphNode] = {}
    edges: list[CausalGraphEdge] = []
    all_missing: list[str] = []

    def _node(ref: str) -> CausalGraphNode:
        if ref not in nodes:
            nodes[ref] = CausalGraphNode(
                node_id=_stable_id("cgn", {"ref": ref}),
                node_kind=CausalNodeKind.TRACE_EVENT,
                source_ref=ref,
            )
        return nodes[ref]

    for segment in ordered:
        src = _node(segment.source_ref)
        dst = _node(segment.target_ref)
        edges.append(
            CausalGraphEdge(
                edge_id=_stable_id(
                    "cge",
                    {"from": src.node_id, "to": dst.node_id, "order": segment.causal_order},
                ),
                edge_kind=CausalEdgeKind.CAUSED,
                from_node_id=src.node_id,
                to_node_id=dst.node_id,
            )
        )
        for missing in segment.missing_links:
            all_missing.append(missing)
            edges.append(
                CausalGraphEdge(
                    edge_id=_stable_id(
                        "cge", {"missing": missing, "segment": segment.segment_id}
                    ),
                    edge_kind=CausalEdgeKind.MISSING_LINK,
                    from_node_id=src.node_id,
                    to_node_id=dst.node_id,
                    missing_reason=missing,
                )
            )

    graph_id = _stable_id(
        "gtg",
        {
            "golden_thread_ref_id": golden_thread_ref.golden_thread_ref_id,
            "node_ids": sorted(n.node_id for n in nodes.values()),
            "edge_ids": [e.edge_id for e in edges],
        },
    )
    return GoldenThreadGraph(
        graph_id=graph_id,
        golden_thread_ref=golden_thread_ref,
        nodes=tuple(nodes.values()),
        edges=tuple(edges),
        missing_links=tuple(all_missing),
    )
