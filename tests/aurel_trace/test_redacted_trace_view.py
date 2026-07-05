"""P5.17 — Redacted trace view is a safe read model that never mutates source."""

from __future__ import annotations

import pytest

from agentic_runtime.aurel_trace import (
    AurelTraceError,
    RedactedTraceItem,
    RedactedTraceView,
    TraceLocalityLabel,
    TracePrivacyLabel,
    TraceRedactionMode,
    build_redacted_trace_view,
    build_trace_projection_feed,
)
from agentic_runtime.aurel_trace.trace_demo import build_demo_trace_substrate


def _feed():
    return build_trace_projection_feed(build_demo_trace_substrate().decisions)


def test_view_builds_from_feed_and_does_not_mutate_source():
    feed = _feed()
    before = feed.to_dict()
    refs = [e.target_id for e in feed.entries]
    label_map = {
        refs[0]: (TracePrivacyLabel.LOCAL_ONLY, TraceLocalityLabel.LOCAL_ONLY),
        refs[1]: (TracePrivacyLabel.PUBLIC, TraceLocalityLabel.EXPORT_ALLOWED),
    }
    view = build_redacted_trace_view(feed=feed, label_map=label_map)
    assert feed.to_dict() == before  # source unchanged
    assert view.source_feed_id == feed.feed_id


def test_local_only_item_is_excluded_with_no_payload():
    feed = _feed()
    refs = [e.target_id for e in feed.entries]
    label_map = {refs[0]: (TracePrivacyLabel.LOCAL_ONLY, TraceLocalityLabel.LOCAL_ONLY)}
    view = build_redacted_trace_view(feed=feed, label_map=label_map)
    excluded = [i for i in view.items if i.source_ref == refs[0]][0]
    assert excluded.excluded is True
    assert excluded.safe_value is None
    assert excluded.safe_summary is None
    assert excluded.content_hash is None


def test_hash_and_summary_carry_no_raw_value():
    feed = _feed()
    refs = [e.target_id for e in feed.entries]
    label_map = {
        refs[0]: (TracePrivacyLabel.SECRET, TraceLocalityLabel.TENANT_LOCAL),
        refs[1]: (TracePrivacyLabel.UNKNOWN, TraceLocalityLabel.UNKNOWN),
    }
    view = build_redacted_trace_view(feed=feed, label_map=label_map)
    for item in view.items:
        if item.redaction_mode is not TraceRedactionMode.NONE:
            assert item.safe_value is None


def test_counts_are_deterministic():
    feed = _feed()
    refs = [e.target_id for e in feed.entries]
    label_map = {
        refs[0]: (TracePrivacyLabel.PUBLIC, TraceLocalityLabel.EXPORT_ALLOWED),
        refs[1]: (TracePrivacyLabel.LOCAL_ONLY, TraceLocalityLabel.LOCAL_ONLY),
    }
    a = build_redacted_trace_view(feed=feed, label_map=label_map).to_dict()
    b = build_redacted_trace_view(feed=feed, label_map=label_map).to_dict()
    assert a == b


def test_unmapped_ref_fails_closed_to_non_raw():
    feed = _feed()
    # empty label_map -> everything UNKNOWN/UNKNOWN -> SUMMARY_ONLY (not raw)
    view = build_redacted_trace_view(feed=feed, label_map={})
    assert view.included_count == 0  # nothing is raw-NONE
    for item in view.items:
        assert item.redaction_mode is not TraceRedactionMode.NONE


def test_view_cannot_be_mutating():
    with pytest.raises(AurelTraceError):
        RedactedTraceView(
            view_id="v", items=(), redaction_decisions=(), mutates=True
        )


def test_redacted_item_cannot_carry_raw_value():
    with pytest.raises(AurelTraceError):
        RedactedTraceItem(
            item_id="i",
            source_ref="r",
            target_kind="X",
            redaction_decision_id="d",
            redaction_mode=TraceRedactionMode.HASH,
            safe_value="raw-secret",
        )
