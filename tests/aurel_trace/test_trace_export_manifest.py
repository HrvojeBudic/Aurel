"""P5.18 — Export manifest lists included/excluded/redacted/hashed refs."""

from __future__ import annotations

import pytest

from agentic_runtime.aurel_trace import (
    AurelTraceError,
    TraceExportManifest,
    TraceLocalityLabel,
    TracePrivacyLabel,
    build_redacted_trace_view,
    build_trace_export_manifest,
    build_trace_projection_feed,
    make_trace_redaction_decision,
)
from agentic_runtime.aurel_trace.trace_demo import build_demo_trace_substrate


def _substrate_feed():
    sub = build_demo_trace_substrate()
    return sub, build_trace_projection_feed(sub.decisions)


def _decisions(feed, labels):
    return [
        make_trace_redaction_decision(
            target_ref=e.target_id,
            target_kind="PROJECTION_FEED_ENTRY",
            privacy_label=labels[e.target_id][0],
            locality_label=labels[e.target_id][1],
        )
        for e in feed.entries
    ]


def test_manifest_routes_refs_by_mode():
    sub, feed = _substrate_feed()
    refs = [e.target_id for e in feed.entries]
    labels = {
        refs[0]: (TracePrivacyLabel.PUBLIC, TraceLocalityLabel.EXPORT_ALLOWED),
        refs[1]: (TracePrivacyLabel.LOCAL_ONLY, TraceLocalityLabel.LOCAL_ONLY),
    }
    manifest = build_trace_export_manifest(
        redaction_decisions=_decisions(feed, labels),
        feed=feed,
        resolver_decision_ids=[d.decision_id for d in sub.decisions],
    )
    assert refs[0] in manifest.included_refs
    assert refs[1] in manifest.excluded_refs
    assert refs[1] not in manifest.included_refs


def test_local_only_secret_unknown_never_raw_included():
    sub, feed = _substrate_feed()
    refs = [e.target_id for e in feed.entries]
    labels = {
        refs[0]: (TracePrivacyLabel.SECRET, TraceLocalityLabel.TENANT_LOCAL),
        refs[1]: (TracePrivacyLabel.UNKNOWN, TraceLocalityLabel.UNKNOWN),
    }
    manifest = build_trace_export_manifest(redaction_decisions=_decisions(feed, labels))
    for ref in refs:
        assert ref not in manifest.included_refs


def test_checksums_deterministic_and_unavailable_claims_present():
    sub, feed = _substrate_feed()
    refs = [e.target_id for e in feed.entries]
    labels = {r: (TracePrivacyLabel.PUBLIC, TraceLocalityLabel.EXPORT_ALLOWED) for r in refs}
    a = build_trace_export_manifest(redaction_decisions=_decisions(feed, labels), feed=feed)
    b = build_trace_export_manifest(redaction_decisions=_decisions(feed, labels), feed=feed)
    assert a.checksums == b.checksums
    assert a.unavailable_compliance_claims


def test_p5_refs_preserved():
    sub, feed = _substrate_feed()
    refs = [e.target_id for e in feed.entries]
    labels = {r: (TracePrivacyLabel.PUBLIC, TraceLocalityLabel.EXPORT_ALLOWED) for r in refs}
    manifest = build_trace_export_manifest(
        redaction_decisions=_decisions(feed, labels),
        feed=feed,
        resolver_decision_ids=[d.decision_id for d in sub.decisions],
    )
    assert set(manifest.source_feed_entries) == {e.feed_entry_id for e in feed.entries}
    assert set(manifest.source_resolver_decisions) == {d.decision_id for d in sub.decisions}


def test_manifest_cannot_export_or_certify():
    with pytest.raises(AurelTraceError):
        TraceExportManifest(manifest_id="m", is_external_export=True)
    with pytest.raises(AurelTraceError):
        TraceExportManifest(manifest_id="m", certifies_compliance=True)
    with pytest.raises(AurelTraceError):
        TraceExportManifest(manifest_id="m", uploads=True)
