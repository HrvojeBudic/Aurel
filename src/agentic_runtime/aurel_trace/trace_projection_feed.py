"""P5-TRACE-E read-only projection feed over P5-D resolver decisions.

A projection feed **packages** resolver truth for future Shell/API/event
consumers; it is not itself a source of truth, an API server, an event bus, or a
Shell UI. Each entry **reflects** a P5-D :class:`TraceVerificationDecision` —
copying its status and ``verified`` flag verbatim — and can never assign
``TRACE_VERIFIED`` on its own. Missing evidence, blocking findings, and
unavailable reasons are always preserved. The feed is deterministic and
side-effect free: no trace append, no runtime mutation.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from .trace_hash import (
    AurelTraceError,
    TraceTruthLabel,
    canonical_trace_json,
    require_nonempty,
    trace_sha,
)
from .trace_resolver import (
    TraceVerificationDecision,
    TraceVerificationStatus,
    TraceVerificationTargetKind,
)


@dataclass(frozen=True)
class TraceProjectionFeedEntry:
    """One read-only projection entry derived from a resolver decision."""

    feed_entry_id: str
    source_decision_id: str
    target_kind: TraceVerificationTargetKind
    target_id: str
    verification_status: TraceVerificationStatus
    verified: bool
    summary: str
    evidence_ref_ids: tuple[str, ...] = ()
    binding_ref_ids: tuple[str, ...] = ()
    missing_evidence: tuple[str, ...] = ()
    blocking_findings: tuple[str, ...] = ()
    unavailable_reason: str | None = None
    created_at: str | None = None
    truth_label: TraceTruthLabel = TraceTruthLabel.LIVE

    def __post_init__(self) -> None:
        require_nonempty(self, "feed_entry_id", "source_decision_id", "target_id")
        verified_status = (
            self.verification_status is TraceVerificationStatus.TRACE_VERIFIED
        )
        if self.verified != verified_status:
            raise AurelTraceError(
                "a feed entry's verified flag must match its source decision "
                "(verified iff verification_status is TRACE_VERIFIED)"
            )
        if self.truth_label is TraceTruthLabel.TRACE_INTEGRITY_VERIFIED:
            raise AurelTraceError(
                "a projection feed entry is a LIVE read model; the resolver status "
                "carries the verdict"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "feed_entry_id": self.feed_entry_id,
            "source_decision_id": self.source_decision_id,
            "target_kind": self.target_kind.value,
            "target_id": self.target_id,
            "verification_status": self.verification_status.value,
            "verified": self.verified,
            "summary": self.summary,
            "evidence_ref_ids": list(self.evidence_ref_ids),
            "binding_ref_ids": list(self.binding_ref_ids),
            "missing_evidence": list(self.missing_evidence),
            "blocking_findings": list(self.blocking_findings),
            "unavailable_reason": self.unavailable_reason,
            "created_at": self.created_at,
            "truth_label": self.truth_label.value,
        }


@dataclass(frozen=True)
class ProjectionFeedSummary:
    """Deterministic per-status counts over a feed."""

    summary_id: str
    total: int
    verified_count: int
    trace_bound_count: int
    partial_count: int
    denied_count: int
    error_count: int
    unavailable_count: int
    truth_label: TraceTruthLabel = TraceTruthLabel.LIVE

    def to_dict(self) -> dict[str, Any]:
        return {
            "summary_id": self.summary_id,
            "total": self.total,
            "verified_count": self.verified_count,
            "trace_bound_count": self.trace_bound_count,
            "partial_count": self.partial_count,
            "denied_count": self.denied_count,
            "error_count": self.error_count,
            "unavailable_count": self.unavailable_count,
            "truth_label": self.truth_label.value,
        }


@dataclass(frozen=True)
class TraceProjectionFeed:
    """Read-only projection feed contract for future Shell/API/event surfaces."""

    feed_id: str
    entries: tuple[TraceProjectionFeedEntry, ...]
    truth_label: TraceTruthLabel = TraceTruthLabel.LIVE

    # Locked: a feed is a read model, not a live surface, and it mutates nothing.
    is_api_server: bool = False
    is_event_bus: bool = False
    is_shell_ui: bool = False
    mutates: bool = False

    def __post_init__(self) -> None:
        require_nonempty(self, "feed_id")
        for field_name in ("is_api_server", "is_event_bus", "is_shell_ui", "mutates"):
            if getattr(self, field_name) is True:
                raise AurelTraceError(
                    f"{field_name} must be False — the projection feed is a read model, "
                    "not an API/event bus/Shell UI, and mutates nothing"
                )
        if self.truth_label is TraceTruthLabel.TRACE_INTEGRITY_VERIFIED:
            raise AurelTraceError("a projection feed is a LIVE read model")

    def _count(self, status: TraceVerificationStatus) -> int:
        return sum(1 for e in self.entries if e.verification_status is status)

    @property
    def verified_count(self) -> int:
        return self._count(TraceVerificationStatus.TRACE_VERIFIED)

    def summary(self) -> ProjectionFeedSummary:
        return summarize_projection_feed(self)

    def to_dict(self) -> dict[str, Any]:
        return {
            "feed_id": self.feed_id,
            "entries": [e.to_dict() for e in self.entries],
            "summary": self.summary().to_dict(),
            "is_api_server": self.is_api_server,
            "is_event_bus": self.is_event_bus,
            "is_shell_ui": self.is_shell_ui,
            "mutates": self.mutates,
            "truth_label": self.truth_label.value,
        }


def build_trace_projection_feed_entry(
    decision: TraceVerificationDecision,
    *,
    evidence_ref_ids: Sequence[str] = (),
    binding_ref_ids: Sequence[str] = (),
    created_at: str | None = None,
) -> TraceProjectionFeedEntry:
    """Reflect one resolver decision as a read-only feed entry.

    The entry copies the decision's status/verified/missing-evidence/blocking-
    findings verbatim; it never re-decides or upgrades. An UNAVAILABLE decision's
    reason is surfaced as ``unavailable_reason``.
    """

    unavailable_reason = (
        decision.reason
        if decision.status is TraceVerificationStatus.UNAVAILABLE
        else None
    )
    feed_entry_id = "tpfe-" + trace_sha(
        canonical_trace_json(
            {
                "source_decision_id": decision.decision_id,
                "target_id": decision.target_id,
            }
        )
    )[:40]
    return TraceProjectionFeedEntry(
        feed_entry_id=feed_entry_id,
        source_decision_id=decision.decision_id,
        target_kind=decision.target_kind,
        target_id=decision.target_id,
        verification_status=decision.status,
        verified=decision.verified,
        summary=decision.reason,
        evidence_ref_ids=tuple(evidence_ref_ids) or decision.source_evidence_ref_ids,
        binding_ref_ids=tuple(binding_ref_ids) or decision.source_binding_ids,
        missing_evidence=decision.missing_evidence,
        blocking_findings=decision.blocking_findings,
        unavailable_reason=unavailable_reason,
        created_at=created_at,
    )


def build_trace_projection_feed(
    decisions: Sequence[TraceVerificationDecision],
    *,
    feed_id: str = "trace-projection-feed.p5-trace-e.v1",
    evidence_ref_ids_by_decision: dict[str, Sequence[str]] | None = None,
    binding_ref_ids_by_decision: dict[str, Sequence[str]] | None = None,
) -> TraceProjectionFeed:
    """Build a read-only feed from resolver decisions (no re-decision)."""

    ev_map = evidence_ref_ids_by_decision or {}
    bind_map = binding_ref_ids_by_decision or {}
    entries = tuple(
        build_trace_projection_feed_entry(
            decision,
            evidence_ref_ids=ev_map.get(decision.decision_id, ()),
            binding_ref_ids=bind_map.get(decision.decision_id, ()),
        )
        for decision in decisions
    )
    return TraceProjectionFeed(feed_id=feed_id, entries=entries)


def summarize_projection_feed(feed: TraceProjectionFeed) -> ProjectionFeedSummary:
    """Deterministic read-only per-status summary of a feed."""

    def _count(status: TraceVerificationStatus) -> int:
        return sum(1 for e in feed.entries if e.verification_status is status)

    summary_id = "tpfsum-" + trace_sha(
        canonical_trace_json({"feed_id": feed.feed_id})
    )[:32]
    return ProjectionFeedSummary(
        summary_id=summary_id,
        total=len(feed.entries),
        verified_count=_count(TraceVerificationStatus.TRACE_VERIFIED),
        trace_bound_count=_count(TraceVerificationStatus.TRACE_BOUND),
        partial_count=_count(TraceVerificationStatus.PARTIAL),
        denied_count=_count(TraceVerificationStatus.DENIED),
        error_count=_count(TraceVerificationStatus.ERROR),
        unavailable_count=_count(TraceVerificationStatus.UNAVAILABLE),
    )
