"""P5.9 — P4 (AurelExec execution) trace binding."""

from __future__ import annotations

import pytest

from agentic_runtime.aurel_trace import (
    AurelTraceError,
    EvidenceKind,
    EvidenceStatus,
    P4SourceObjectKind,
    TraceBindingCoverageStatus,
    TraceTruthLabel,
    build_p4_trace_binding,
    make_evidence_ref,
)
from agentic_runtime.aurel_trace.p4_binding import P4_DOMAIN, make_p4_evidence_ref


def test_every_supported_kind_builds_a_binding():
    for kind in P4SourceObjectKind:
        binding = build_p4_trace_binding(
            source_object_kind=kind, source_object_id=f"{kind.value}-1"
        )
        assert binding.source_object_kind is kind
        assert binding.evidence_refs
        assert binding.coverage_status is TraceBindingCoverageStatus.MISSING


def test_supported_kind_with_present_evidence_is_complete():
    ref = make_p4_evidence_ref(
        source_object_kind=P4SourceObjectKind.EXEC_JOB,
        source_object_id="job-1",
        status=EvidenceStatus.PRESENT,
    )
    binding = build_p4_trace_binding(
        source_object_kind=P4SourceObjectKind.EXEC_JOB,
        source_object_id="job-1",
        evidence_refs=(ref,),
    )
    assert binding.coverage_status is TraceBindingCoverageStatus.COMPLETE
    assert binding.truth_label is TraceTruthLabel.TRACE_BOUND


def test_recovery_plan_maps_to_failure_evidence():
    binding = build_p4_trace_binding(
        source_object_kind=P4SourceObjectKind.RECOVERY_PLAN,
        source_object_id="rp-1",
    )
    assert binding.evidence_refs[0].evidence_kind is EvidenceKind.P4_FAILURE_EVIDENCE
    assert binding.evidence_refs[0].source_domain == P4_DOMAIN


def test_bench_snapshot_maps_to_bench_evidence():
    binding = build_p4_trace_binding(
        source_object_kind=P4SourceObjectKind.EXEC_BENCH_SNAPSHOT,
        source_object_id="bench-1",
    )
    assert binding.evidence_refs[0].evidence_kind is EvidenceKind.P4_BENCH_EVIDENCE


def test_unsupported_kind_fails_closed_with_reason():
    binding = build_p4_trace_binding(
        source_object_kind="TotallyUnknownExecKind", source_object_id="x-1"
    )
    assert binding.coverage_status is TraceBindingCoverageStatus.UNSUPPORTED
    assert binding.missing_evidence[0].status is EvidenceStatus.UNSUPPORTED
    assert binding.missing_evidence[0].missing_reason


def test_binding_side_effect_booleans_unconstructible():
    from agentic_runtime.aurel_trace import P4TraceBinding

    ref = make_evidence_ref(
        evidence_kind=EvidenceKind.P4_JOB_EVIDENCE,
        source_domain=P4_DOMAIN,
        source_object_id="job-1",
    )
    for bad in ("executes_job", "triggers_retry", "triggers_recovery", "dispatches_worker"):
        with pytest.raises(AurelTraceError):
            P4TraceBinding(
                p4_binding_id="b",
                source_object_kind=P4SourceObjectKind.EXEC_JOB,
                source_object_id="job-1",
                coverage_status=TraceBindingCoverageStatus.COMPLETE,
                evidence_refs=(ref,),
                **{bad: True},
            )
