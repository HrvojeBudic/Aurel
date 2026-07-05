"""P5.14 — Read-only projection feed reflects resolver truth."""

from __future__ import annotations

import pytest

from agentic_runtime.aurel_trace import (
    AurelTraceError,
    TraceProjectionFeed,
    TraceProjectionFeedEntry,
    build_trace_projection_feed,
    build_trace_projection_feed_entry,
    resolve_trace_target,
    summarize_projection_feed,
)
from agentic_runtime.aurel_trace.trace_resolver import (
    TraceVerificationStatus,
    TraceVerificationTargetKind,
)
from agentic_runtime.aurel_trace.trace_demo import build_demo_trace_substrate


def _demo_feed():
    substrate = build_demo_trace_substrate()
    return build_trace_projection_feed(substrate.decisions), substrate


def test_entry_reflects_decision_verbatim():
    feed, substrate = _demo_feed()
    by_target = {e.target_id: e for e in feed.entries}
    for decision in substrate.decisions:
        entry = by_target[decision.target_id]
        assert entry.verification_status is decision.status
        assert entry.verified is decision.verified
        assert entry.summary == decision.reason
        assert entry.missing_evidence == decision.missing_evidence


def test_trace_verified_only_when_source_is_verified():
    feed, _ = _demo_feed()
    for entry in feed.entries:
        if entry.verification_status is TraceVerificationStatus.TRACE_VERIFIED:
            assert entry.verified is True
        else:
            assert entry.verified is False
    # at least one honestly not verified
    assert any(not e.verified for e in feed.entries)


def test_partial_entry_preserves_missing_evidence():
    feed, _ = _demo_feed()
    partial = next(
        e
        for e in feed.entries
        if e.verification_status is TraceVerificationStatus.PARTIAL
    )
    assert partial.missing_evidence


def test_unavailable_reason_preserved():
    decision = resolve_trace_target(
        target_kind=TraceVerificationTargetKind.TRACE_RUN,
        target_id="run-empty",
    )
    assert decision.status is TraceVerificationStatus.UNAVAILABLE
    entry = build_trace_projection_feed_entry(decision)
    assert entry.unavailable_reason
    assert entry.verification_status is TraceVerificationStatus.UNAVAILABLE


def test_blocking_findings_preserved():
    from agentic_runtime.aurel_trace.trace_verify import (
        TraceFindingSeverity,
        TraceHashFinding,
        TraceHashFindingKind,
    )

    finding = TraceHashFinding(
        finding_id="f1",
        finding_kind=TraceHashFindingKind.BROKEN_PREVIOUS_HASH,
        severity=TraceFindingSeverity.CRITICAL,
        message="broken prev hash",
    )
    decision = resolve_trace_target(
        target_kind=TraceVerificationTargetKind.TRACE_RUN,
        target_id="run-blocked",
        findings=[finding],
    )
    entry = build_trace_projection_feed_entry(decision)
    assert entry.verification_status is TraceVerificationStatus.DENIED
    assert "broken prev hash" in entry.blocking_findings


def test_feed_entry_id_deterministic():
    _feed, substrate = _demo_feed()
    d = substrate.decisions[0]
    a = build_trace_projection_feed_entry(d)
    b = build_trace_projection_feed_entry(d)
    assert a.feed_entry_id == b.feed_entry_id


def test_feed_counts_deterministic():
    feed, _ = _demo_feed()
    a = summarize_projection_feed(feed).to_dict()
    b = summarize_projection_feed(feed).to_dict()
    assert a == b
    assert feed.verified_count == 1


def test_entry_cannot_fake_verified():
    with pytest.raises(AurelTraceError):
        TraceProjectionFeedEntry(
            feed_entry_id="e",
            source_decision_id="d",
            target_kind=TraceVerificationTargetKind.TRACE_RUN,
            target_id="t",
            verification_status=TraceVerificationStatus.TRACE_BOUND,
            verified=True,
            summary="x",
        )


def test_feed_is_not_a_live_surface():
    feed, _ = _demo_feed()
    assert feed.is_api_server is False
    assert feed.is_event_bus is False
    assert feed.is_shell_ui is False
    with pytest.raises(AurelTraceError):
        TraceProjectionFeed(feed_id="f", entries=(), is_api_server=True)
    with pytest.raises(AurelTraceError):
        TraceProjectionFeed(feed_id="f", entries=(), is_event_bus=True)
