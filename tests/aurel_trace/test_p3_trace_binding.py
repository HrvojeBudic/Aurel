"""P5.9 — P3 (AurelFlow control-plane) trace binding."""

from __future__ import annotations

import pytest

from agentic_runtime.aurel_trace import (
    AurelTraceError,
    EvidenceKind,
    EvidenceStatus,
    P3SourceObjectKind,
    TraceBindingCoverageStatus,
    TraceTruthLabel,
    build_p3_trace_binding,
    make_evidence_ref,
)
from agentic_runtime.aurel_trace.p3_binding import P3_DOMAIN, make_p3_evidence_ref


def test_every_supported_kind_builds_a_binding():
    for kind in P3SourceObjectKind:
        binding = build_p3_trace_binding(
            source_object_kind=kind, source_object_id=f"{kind.value}-1"
        )
        assert binding.source_object_kind is kind
        assert binding.evidence_refs
        # Without supplied evidence, coverage is honestly MISSING.
        assert binding.coverage_status is TraceBindingCoverageStatus.MISSING


def test_supported_kind_with_present_evidence_is_complete():
    ref = make_p3_evidence_ref(
        source_object_kind=P3SourceObjectKind.SCHEDULING_INTENT,
        source_object_id="si-1",
        status=EvidenceStatus.PRESENT,
    )
    binding = build_p3_trace_binding(
        source_object_kind=P3SourceObjectKind.SCHEDULING_INTENT,
        source_object_id="si-1",
        evidence_refs=(ref,),
    )
    assert binding.coverage_status is TraceBindingCoverageStatus.COMPLETE
    assert binding.truth_label is TraceTruthLabel.TRACE_BOUND


def test_scheduling_intent_maps_to_scheduling_evidence():
    binding = build_p3_trace_binding(
        source_object_kind=P3SourceObjectKind.WORKFLOW_ATOMIC_UNIT,
        source_object_id="wu-1",
    )
    assert binding.evidence_refs[0].evidence_kind is EvidenceKind.P3_WORKFLOW_EVIDENCE
    assert binding.evidence_refs[0].source_domain == P3_DOMAIN


def test_unsupported_kind_fails_closed_with_reason():
    binding = build_p3_trace_binding(
        source_object_kind="TotallyUnknownKind", source_object_id="x-1"
    )
    assert binding.coverage_status is TraceBindingCoverageStatus.UNSUPPORTED
    assert binding.missing_evidence
    assert binding.missing_evidence[0].status is EvidenceStatus.UNSUPPORTED
    assert binding.missing_evidence[0].missing_reason


def test_empty_source_object_id_raises():
    with pytest.raises(AurelTraceError):
        build_p3_trace_binding(
            source_object_kind=P3SourceObjectKind.FLOW_STATE_PROJECTION,
            source_object_id="   ",
        )


def test_binding_side_effect_booleans_unconstructible():
    from agentic_runtime.aurel_trace import P3TraceBinding

    ref = make_evidence_ref(
        evidence_kind=EvidenceKind.P3_SCHEDULING_EVIDENCE,
        source_domain=P3_DOMAIN,
        source_object_id="si-1",
    )
    with pytest.raises(AurelTraceError):
        P3TraceBinding(
            p3_binding_id="b",
            source_object_kind=P3SourceObjectKind.SCHEDULING_INTENT,
            source_object_id="si-1",
            coverage_status=TraceBindingCoverageStatus.COMPLETE,
            evidence_refs=(ref,),
            executes_workflow=True,
        )
