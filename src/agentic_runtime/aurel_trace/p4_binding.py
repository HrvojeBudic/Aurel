"""P5-TRACE-C P4 (AurelExec execution) trace binding.

Binds an AurelExec artifact to P5 trace/evidence refs using a **closed-world
source-object-kind descriptor + a string id** — it does **not** import
``aurel_exec`` or accept live objects, so it cannot execute a job, trigger
retry/recovery, dispatch a worker, or append trace. Unknown/unsupported source
kinds fail closed; missing expected evidence stays explicit.

Repo-truth note (canon rule): the enum values name the real AurelExec classes
they conceptually reference — ``EXEC_ADMISSION_DECISION``->``ExecAdmissionDecision``,
``EXECUTION_LEASE``->``ExecutionLease``, ``EXEC_JOB``->``ExecJob``,
``EXECUTION_ATTEMPT``->``ExecutionAttempt``, ``EXECUTION_OUTCOME``->``ExecutionOutcome``,
``EXECUTION_FAILURE``->``FailureClassification`` (there is no ``ExecutionFailure``
class), ``RECOVERY_PLAN``->``BoundedRecoveryPlan`` (there is no ``RecoveryPlan``
class), ``BACKPRESSURE_DECISION``->``BackpressureDecision``,
``EXEC_BENCH_SNAPSHOT``->``ExecBenchSnapshot``. Because no AurelExec module is
imported, side-effect freedom is structural.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from .evidence_ref import (
    EvidenceKind,
    EvidenceRef,
    EvidenceStatus,
    TraceBindingCoverageStatus,
    make_evidence_ref,
    make_missing_evidence_ref,
)
from .trace_hash import (
    AurelTraceError,
    TraceTruthLabel,
    canonical_trace_json,
    require_nonempty,
    trace_sha,
)

P4_DOMAIN = "aurel_exec"


class P4SourceObjectKind(str, Enum):
    """Closed-world P4 execution source object kinds (repo-truth mapped)."""

    EXEC_ADMISSION_DECISION = "EXEC_ADMISSION_DECISION"  # ExecAdmissionDecision
    EXECUTION_LEASE = "EXECUTION_LEASE"  # ExecutionLease
    EXEC_JOB = "EXEC_JOB"  # ExecJob
    EXECUTION_ATTEMPT = "EXECUTION_ATTEMPT"  # ExecutionAttempt
    EXECUTION_OUTCOME = "EXECUTION_OUTCOME"  # ExecutionOutcome
    EXECUTION_FAILURE = "EXECUTION_FAILURE"  # FailureClassification
    RECOVERY_PLAN = "RECOVERY_PLAN"  # BoundedRecoveryPlan
    BACKPRESSURE_DECISION = "BACKPRESSURE_DECISION"  # BackpressureDecision
    EXEC_BENCH_SNAPSHOT = "EXEC_BENCH_SNAPSHOT"  # ExecBenchSnapshot


_P4_KIND_TO_EVIDENCE_KIND: dict[P4SourceObjectKind, EvidenceKind] = {
    P4SourceObjectKind.EXEC_ADMISSION_DECISION: EvidenceKind.P4_ADMISSION_EVIDENCE,
    P4SourceObjectKind.EXECUTION_LEASE: EvidenceKind.P4_LEASE_EVIDENCE,
    P4SourceObjectKind.EXEC_JOB: EvidenceKind.P4_JOB_EVIDENCE,
    P4SourceObjectKind.EXECUTION_ATTEMPT: EvidenceKind.P4_ATTEMPT_EVIDENCE,
    P4SourceObjectKind.EXECUTION_OUTCOME: EvidenceKind.P4_OUTCOME_EVIDENCE,
    P4SourceObjectKind.EXECUTION_FAILURE: EvidenceKind.P4_FAILURE_EVIDENCE,
    P4SourceObjectKind.RECOVERY_PLAN: EvidenceKind.P4_FAILURE_EVIDENCE,
    P4SourceObjectKind.BACKPRESSURE_DECISION: EvidenceKind.P4_BACKPRESSURE_EVIDENCE,
    P4SourceObjectKind.EXEC_BENCH_SNAPSHOT: EvidenceKind.P4_BENCH_EVIDENCE,
}


@dataclass(frozen=True)
class P4TraceBinding:
    """Binding from a P4 execution artifact to trace/evidence refs."""

    p4_binding_id: str
    source_object_kind: P4SourceObjectKind
    source_object_id: str
    coverage_status: TraceBindingCoverageStatus
    evidence_refs: tuple[EvidenceRef, ...]
    missing_evidence: tuple[EvidenceRef, ...] = ()
    trace_binding_ref_id: str | None = None
    truth_label: TraceTruthLabel = TraceTruthLabel.TRACE_BOUND

    # Locked: a P4 binding references; it does not execute/retry/recover/dispatch.
    executes_job: bool = False
    triggers_retry: bool = False
    triggers_recovery: bool = False
    dispatches_worker: bool = False
    appends_trace: bool = False

    def __post_init__(self) -> None:
        require_nonempty(self, "p4_binding_id", "source_object_id")
        for field_name in (
            "executes_job",
            "triggers_retry",
            "triggers_recovery",
            "dispatches_worker",
            "appends_trace",
        ):
            if getattr(self, field_name) is True:
                raise AurelTraceError(
                    f"{field_name} must be False — a P4 binding references, it does "
                    "not execute/retry/recover/dispatch"
                )
        if self.truth_label is TraceTruthLabel.TRACE_INTEGRITY_VERIFIED:
            raise AurelTraceError(
                "a P4 binding is TRACE_BOUND; the resolver (P5-D) verifies"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "p4_binding_id": self.p4_binding_id,
            "source_object_kind": self.source_object_kind.value,
            "source_object_id": self.source_object_id,
            "coverage_status": self.coverage_status.value,
            "evidence_refs": [r.to_dict() for r in self.evidence_refs],
            "missing_evidence": [r.to_dict() for r in self.missing_evidence],
            "trace_binding_ref_id": self.trace_binding_ref_id,
            "executes_job": self.executes_job,
            "triggers_retry": self.triggers_retry,
            "triggers_recovery": self.triggers_recovery,
            "dispatches_worker": self.dispatches_worker,
            "appends_trace": self.appends_trace,
            "truth_label": self.truth_label.value,
        }


def _coverage_from_refs(refs: tuple[EvidenceRef, ...]) -> TraceBindingCoverageStatus:
    if not refs:
        return TraceBindingCoverageStatus.MISSING
    if any(r.status is EvidenceStatus.ERROR for r in refs):
        return TraceBindingCoverageStatus.ERROR
    present = sum(1 for r in refs if r.is_present)
    if present == len(refs):
        return TraceBindingCoverageStatus.COMPLETE
    if present == 0:
        return TraceBindingCoverageStatus.MISSING
    return TraceBindingCoverageStatus.PARTIAL


def build_p4_trace_binding(
    *,
    source_object_kind: P4SourceObjectKind | str,
    source_object_id: str,
    trace_binding_ref_id: str | None = None,
    evidence_refs: tuple[EvidenceRef, ...] = (),
    missing_reason: str | None = None,
) -> P4TraceBinding:
    """Build a P4 trace binding, failing closed on an unsupported source kind.

    A supported kind with no supplied evidence yields a binding whose single
    expected ``EvidenceRef`` is ``MISSING`` (evidence stays explicit). An
    unknown/unsupported string yields an ``UNSUPPORTED`` binding with a reason.
    """

    if not source_object_id or not source_object_id.strip():
        raise AurelTraceError("source_object_id must not be empty")
    if not isinstance(source_object_kind, P4SourceObjectKind):
        reason = (
            f"unsupported P4 source object kind {source_object_kind!r}; "
            "P4 source kinds are closed-world"
        )
        unsupported_ref = make_missing_evidence_ref(
            evidence_kind=EvidenceKind.P4_JOB_EVIDENCE,
            source_domain=P4_DOMAIN,
            source_object_id=source_object_id,
            missing_reason=reason,
            status=EvidenceStatus.UNSUPPORTED,
        )
        return P4TraceBinding(
            p4_binding_id=_p4_binding_id("UNSUPPORTED", source_object_id),
            source_object_kind=P4SourceObjectKind.EXEC_JOB,
            source_object_id=source_object_id,
            coverage_status=TraceBindingCoverageStatus.UNSUPPORTED,
            evidence_refs=(unsupported_ref,),
            missing_evidence=(unsupported_ref,),
            trace_binding_ref_id=trace_binding_ref_id,
        )

    evidence_kind = _P4_KIND_TO_EVIDENCE_KIND[source_object_kind]
    refs: tuple[EvidenceRef, ...]
    if evidence_refs:
        refs = tuple(evidence_refs)
    else:
        refs = (
            make_missing_evidence_ref(
                evidence_kind=evidence_kind,
                source_domain=P4_DOMAIN,
                source_object_id=source_object_id,
                missing_reason=missing_reason
                or f"no {evidence_kind.value} bound for {source_object_kind.value}",
                status=EvidenceStatus.MISSING,
            ),
        )
    coverage = _coverage_from_refs(refs)
    missing = tuple(
        r
        for r in refs
        if r.status in (EvidenceStatus.MISSING, EvidenceStatus.UNSUPPORTED)
    )
    return P4TraceBinding(
        p4_binding_id=_p4_binding_id(source_object_kind.value, source_object_id),
        source_object_kind=source_object_kind,
        source_object_id=source_object_id,
        coverage_status=coverage,
        evidence_refs=refs,
        missing_evidence=missing,
        trace_binding_ref_id=trace_binding_ref_id,
    )


def make_p4_evidence_ref(
    *,
    source_object_kind: P4SourceObjectKind,
    source_object_id: str,
    status: EvidenceStatus = EvidenceStatus.PRESENT,
    trace_binding_ref_id: str | None = None,
    verification_receipt_id: str | None = None,
) -> EvidenceRef:
    """Convenience: an evidence ref for a supported P4 source object kind."""

    return make_evidence_ref(
        evidence_kind=_P4_KIND_TO_EVIDENCE_KIND[source_object_kind],
        source_domain=P4_DOMAIN,
        source_object_id=source_object_id,
        status=status,
        trace_binding_ref_id=trace_binding_ref_id,
        verification_receipt_id=verification_receipt_id,
    )


def _p4_binding_id(kind_value: str, source_object_id: str) -> str:
    return "p4bind-" + trace_sha(
        canonical_trace_json({"kind": kind_value, "source_object_id": source_object_id})
    )[:40]
