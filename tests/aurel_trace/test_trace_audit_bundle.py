"""P5.18 — Audit bundle preserves refs, respects redaction, claims no certification."""

from __future__ import annotations

import pytest

from agentic_runtime.aurel_trace import (
    AurelTraceError,
    TraceAuditBundle,
    TraceLocalityLabel,
    TracePrivacyLabel,
    build_causal_graph,
    build_golden_thread_ref,
    build_golden_thread_segment,
    build_redacted_trace_view,
    build_trace_audit_bundle,
    build_trace_export_manifest,
    build_trace_projection_feed,
    make_trace_redaction_decision,
)
from agentic_runtime.aurel_trace.trace_demo import build_demo_trace_substrate


def _bundle_with_labels(labels):
    sub = build_demo_trace_substrate()
    feed = build_trace_projection_feed(sub.decisions)
    label_map = {e.target_id: labels[e.target_id] for e in feed.entries}
    view = build_redacted_trace_view(feed=feed, label_map=label_map)
    manifest = build_trace_export_manifest(
        redaction_decisions=view.redaction_decisions,
        feed=feed,
        resolver_decision_ids=[d.decision_id for d in sub.decisions],
    )
    bundle = build_trace_audit_bundle(
        manifest=manifest,
        redacted_view=view,
        source_refs=[e.target_id for e in feed.entries],
    )
    return sub, feed, bundle


def test_bundle_respects_local_only_exclusion():
    sub = build_demo_trace_substrate()
    feed = build_trace_projection_feed(sub.decisions)
    refs = [e.target_id for e in feed.entries]
    labels = {
        refs[0]: (TracePrivacyLabel.LOCAL_ONLY, TraceLocalityLabel.LOCAL_ONLY),
        refs[1]: (TracePrivacyLabel.PUBLIC, TraceLocalityLabel.EXPORT_ALLOWED),
    }
    _s, _f, bundle = _bundle_with_labels(labels)
    assert refs[0] in bundle.excluded_refs
    # excluded item is not among included items
    assert all(i.source_ref != refs[0] for i in bundle.included_items)


def test_bundle_preserves_source_refs():
    sub = build_demo_trace_substrate()
    feed = build_trace_projection_feed(sub.decisions)
    refs = [e.target_id for e in feed.entries]
    labels = {r: (TracePrivacyLabel.PUBLIC, TraceLocalityLabel.EXPORT_ALLOWED) for r in refs}
    _s, _f, bundle = _bundle_with_labels(labels)
    assert set(bundle.source_refs) == set(refs)
    # manifest inside the bundle preserves resolver + feed refs
    assert bundle.manifest.source_resolver_decisions
    assert bundle.manifest.source_feed_entries


def test_bundle_includes_golden_thread_and_replay_material():
    segs = [
        build_golden_thread_segment(
            segment_kind="P3->P4", source_ref="si-1", target_ref="job-1", causal_order=0
        )
    ]
    ref = build_golden_thread_ref(
        root_target_id="si-1", root_target_kind="P3_INTENT", segments=segs
    )
    graph = build_causal_graph(golden_thread_ref=ref, segments=segs)
    # replay assessment fixture
    from agentic_runtime.aurel_trace import (
        assess_replay_readiness,
        build_trace_time_slice_ref,
    )

    ts = build_trace_time_slice_ref(start_ref="evt-0", end_ref="evt-1", start_index=0, end_index=1)
    assessment = assess_replay_readiness(
        time_slice_ref=ts, required_inputs=("trace_run_ref",), present_inputs=("trace_run_ref",)
    )
    label_map = {
        "si-1": (TracePrivacyLabel.PUBLIC, TraceLocalityLabel.EXPORT_ALLOWED),
        "job-1": (TracePrivacyLabel.INTERNAL, TraceLocalityLabel.EXPORT_ALLOWED),
        ts.time_slice_ref_id: (TracePrivacyLabel.PUBLIC, TraceLocalityLabel.EXPORT_ALLOWED),
    }
    view = build_redacted_trace_view(
        golden_thread_graph=graph, replay_assessment=assessment, label_map=label_map
    )
    manifest = build_trace_export_manifest(
        redaction_decisions=view.redaction_decisions,
        golden_thread_graph=graph,
        replay_assessment=assessment,
    )
    assert manifest.source_golden_thread_refs == (ref.golden_thread_ref_id,)
    assert manifest.source_replay_readiness_assessments == (assessment.assessment_id,)


def test_bundle_is_deterministic():
    labels_a = {
        r: (TracePrivacyLabel.PUBLIC, TraceLocalityLabel.EXPORT_ALLOWED)
        for r in [e.target_id for e in build_trace_projection_feed(build_demo_trace_substrate().decisions).entries]
    }
    _s1, _f1, b1 = _bundle_with_labels(labels_a)
    _s2, _f2, b2 = _bundle_with_labels(labels_a)
    assert b1.to_dict() == b2.to_dict()


def test_bundle_claims_no_certification_or_upload():
    labels = {
        r: (TracePrivacyLabel.PUBLIC, TraceLocalityLabel.EXPORT_ALLOWED)
        for r in [e.target_id for e in build_trace_projection_feed(build_demo_trace_substrate().decisions).entries]
    }
    _s, _f, bundle = _bundle_with_labels(labels)
    assert bundle.is_external_export is False
    assert bundle.is_legal_certification is False
    assert bundle.is_encrypted is False
    assert bundle.uploads is False
    with pytest.raises(AurelTraceError):
        TraceAuditBundle(
            bundle_id="b",
            manifest=bundle.manifest,
            redacted_view=bundle.redacted_view,
            is_legal_certification=True,
        )
