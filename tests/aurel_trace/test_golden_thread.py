"""P5.15 — Golden Thread causal continuity refs and segments."""

from __future__ import annotations

import pytest

from agentic_runtime.aurel_trace import (
    AurelTraceError,
    GoldenThreadSegment,
    TraceTruthLabel,
    build_golden_thread_ref,
    build_golden_thread_segment,
)


def _segments():
    return [
        build_golden_thread_segment(
            segment_kind="P3->P4", source_ref="si-1", target_ref="job-1", causal_order=0
        ),
        build_golden_thread_segment(
            segment_kind="P4->P5",
            source_ref="job-1",
            target_ref="evt-1",
            causal_order=1,
            missing_links=("no outcome ref bound",),
        ),
    ]


def test_golden_thread_ref_stable():
    segs = _segments()
    a = build_golden_thread_ref(
        root_target_id="si-1", root_target_kind="P3_INTENT", segments=segs
    )
    b = build_golden_thread_ref(
        root_target_id="si-1", root_target_kind="P3_INTENT", segments=segs
    )
    assert a.golden_thread_ref_id == b.golden_thread_ref_id
    assert a.segment_count == 2


def test_golden_thread_ref_changes_with_root_and_segment_count():
    segs = _segments()
    base = build_golden_thread_ref(
        root_target_id="si-1", root_target_kind="P3_INTENT", segments=segs
    )
    other_root = build_golden_thread_ref(
        root_target_id="si-2", root_target_kind="P3_INTENT", segments=segs
    )
    fewer = build_golden_thread_ref(
        root_target_id="si-1", root_target_kind="P3_INTENT", segments=segs[:1]
    )
    assert base.golden_thread_ref_id != other_root.golden_thread_ref_id
    assert base.golden_thread_ref_id != fewer.golden_thread_ref_id
    assert base.head_segment_id != fewer.head_segment_id


def test_segment_links_refs_and_keeps_missing_links_explicit():
    seg = _segments()[1]
    assert seg.source_ref == "job-1"
    assert seg.target_ref == "evt-1"
    assert seg.missing_links == ("no outcome ref bound",)
    assert seg.truth_label is TraceTruthLabel.TRACE_BOUND


def test_segment_cannot_claim_integrity_verified():
    with pytest.raises(AurelTraceError):
        GoldenThreadSegment(
            segment_id="s",
            segment_kind="k",
            source_ref="a",
            target_ref="b",
            causal_order=0,
            truth_label=TraceTruthLabel.TRACE_INTEGRITY_VERIFIED,
        )


def test_negative_causal_order_rejected():
    with pytest.raises(AurelTraceError):
        build_golden_thread_segment(
            segment_kind="k", source_ref="a", target_ref="b", causal_order=-1
        )
