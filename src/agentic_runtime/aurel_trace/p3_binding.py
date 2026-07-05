"""P5-TRACE-C P3 (AurelFlow control-plane) trace binding.

Binds an AurelFlow control-plane artifact to P5 trace/evidence refs using a
**closed-world source-object-kind descriptor + a string id** — it does **not**
import ``aurel_flow`` or accept live objects, so it cannot execute a workflow,
mutate scheduling state, or append trace. Unknown/unsupported source kinds fail
closed; missing expected evidence stays explicit.

Repo-truth note (canon rule): the enum values name the real AurelFlow classes
they conceptually reference — ``SCHEDULING_INTENT``->``SchedulingIntent``,
``WORKFLOW_ATOMIC_UNIT``->``WorkflowAtomicUnit``,
``FLOW_STATE_PROJECTION``->``FlowStateProjection``,
``READY_CANDIDATE``->``ExecutionRequestCandidateSurface`` (there is no
``ReadyCandidate`` class), ``FLOW_SEAL_REPORT``->``P3DomainSeal`` (there is no
``FlowSealReport`` class). Because no AurelFlow module is imported, side-effect
freedom is structural.
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

P3_DOMAIN = "aurel_flow"


class P3SourceObjectKind(str, Enum):
    """Closed-world P3 control-plane source object kinds (repo-truth mapped)."""

    SCHEDULING_INTENT = "SCHEDULING_INTENT"  # SchedulingIntent
    WORKFLOW_ATOMIC_UNIT = "WORKFLOW_ATOMIC_UNIT"  # WorkflowAtomicUnit
    READY_CANDIDATE = "READY_CANDIDATE"  # ExecutionRequestCandidateSurface
    FLOW_STATE_PROJECTION = "FLOW_STATE_PROJECTION"  # FlowStateProjection
    FLOW_SEAL_REPORT = "FLOW_SEAL_REPORT"  # P3DomainSeal


_P3_KIND_TO_EVIDENCE_KIND: dict[P3SourceObjectKind, EvidenceKind] = {
    P3SourceObjectKind.SCHEDULING_INTENT: EvidenceKind.P3_SCHEDULING_EVIDENCE,
    P3SourceObjectKind.WORKFLOW_ATOMIC_UNIT: EvidenceKind.P3_WORKFLOW_EVIDENCE,
    P3SourceObjectKind.READY_CANDIDATE: EvidenceKind.P3_SCHEDULING_EVIDENCE,
    P3SourceObjectKind.FLOW_STATE_PROJECTION: EvidenceKind.P3_PROJECTION_EVIDENCE,
    P3SourceObjectKind.FLOW_SEAL_REPORT: EvidenceKind.P3_PROJECTION_EVIDENCE,
}


@dataclass(frozen=True)
class P3TraceBinding:
    """Binding from a P3 control-plane artifact to trace/evidence refs."""

    p3_binding_id: str
    source_object_kind: P3SourceObjectKind
    source_object_id: str
    coverage_status: TraceBindingCoverageStatus
    evidence_refs: tuple[EvidenceRef, ...]
    missing_evidence: tuple[EvidenceRef, ...] = ()
    trace_binding_ref_id: str | None = None
    truth_label: TraceTruthLabel = TraceTruthLabel.TRACE_BOUND

    # Locked: a P3 binding references; it does not schedule/execute/mutate.
    executes_workflow: bool = False
    mutates_scheduling: bool = False
    appends_trace: bool = False

    def __post_init__(self) -> None:
        require_nonempty(self, "p3_binding_id", "source_object_id")
        for field_name in ("executes_workflow", "mutates_scheduling", "appends_trace"):
            if getattr(self, field_name) is True:
                raise AurelTraceError(
                    f"{field_name} must be False — a P3 binding references, it does "
                    "not schedule/execute/mutate"
                )
        if self.truth_label is TraceTruthLabel.TRACE_INTEGRITY_VERIFIED:
            raise AurelTraceError(
                "a P3 binding is TRACE_BOUND; the resolver (P5-D) verifies"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "p3_binding_id": self.p3_binding_id,
            "source_object_kind": self.source_object_kind.value,
            "source_object_id": self.source_object_id,
            "coverage_status": self.coverage_status.value,
            "evidence_refs": [r.to_dict() for r in self.evidence_refs],
            "missing_evidence": [r.to_dict() for r in self.missing_evidence],
            "trace_binding_ref_id": self.trace_binding_ref_id,
            "executes_workflow": self.executes_workflow,
            "mutates_scheduling": self.mutates_scheduling,
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


def build_p3_trace_binding(
    *,
    source_object_kind: P3SourceObjectKind | str,
    source_object_id: str,
    trace_binding_ref_id: str | None = None,
    evidence_refs: tuple[EvidenceRef, ...] = (),
    missing_reason: str | None = None,
) -> P3TraceBinding:
    """Build a P3 trace binding, failing closed on an unsupported source kind.

    A supported kind with no supplied evidence yields a binding whose single
    expected ``EvidenceRef`` is ``MISSING`` (evidence stays explicit). An
    unknown/unsupported string yields an ``UNSUPPORTED`` binding with a reason.
    """

    if not source_object_id or not source_object_id.strip():
        raise AurelTraceError("source_object_id must not be empty")
    if not isinstance(source_object_kind, P3SourceObjectKind):
        # Fail closed: unknown source object kind is UNSUPPORTED, not coerced.
        reason = (
            f"unsupported P3 source object kind {source_object_kind!r}; "
            "P3 source kinds are closed-world"
        )
        unsupported_ref = make_missing_evidence_ref(
            evidence_kind=EvidenceKind.P3_PROJECTION_EVIDENCE,
            source_domain=P3_DOMAIN,
            source_object_id=source_object_id,
            missing_reason=reason,
            status=EvidenceStatus.UNSUPPORTED,
        )
        return P3TraceBinding(
            p3_binding_id=_p3_binding_id("UNSUPPORTED", source_object_id),
            source_object_kind=P3SourceObjectKind.FLOW_STATE_PROJECTION,
            source_object_id=source_object_id,
            coverage_status=TraceBindingCoverageStatus.UNSUPPORTED,
            evidence_refs=(unsupported_ref,),
            missing_evidence=(unsupported_ref,),
            trace_binding_ref_id=trace_binding_ref_id,
        )

    evidence_kind = _P3_KIND_TO_EVIDENCE_KIND[source_object_kind]
    refs: tuple[EvidenceRef, ...]
    if evidence_refs:
        refs = tuple(evidence_refs)
    else:
        refs = (
            make_missing_evidence_ref(
                evidence_kind=evidence_kind,
                source_domain=P3_DOMAIN,
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
    return P3TraceBinding(
        p3_binding_id=_p3_binding_id(source_object_kind.value, source_object_id),
        source_object_kind=source_object_kind,
        source_object_id=source_object_id,
        coverage_status=coverage,
        evidence_refs=refs,
        missing_evidence=missing,
        trace_binding_ref_id=trace_binding_ref_id,
    )


def make_p3_evidence_ref(
    *,
    source_object_kind: P3SourceObjectKind,
    source_object_id: str,
    status: EvidenceStatus = EvidenceStatus.PRESENT,
    trace_binding_ref_id: str | None = None,
    verification_receipt_id: str | None = None,
) -> EvidenceRef:
    """Convenience: an evidence ref for a supported P3 source object kind."""

    return make_evidence_ref(
        evidence_kind=_P3_KIND_TO_EVIDENCE_KIND[source_object_kind],
        source_domain=P3_DOMAIN,
        source_object_id=source_object_id,
        status=status,
        trace_binding_ref_id=trace_binding_ref_id,
        verification_receipt_id=verification_receipt_id,
    )


def _p3_binding_id(kind_value: str, source_object_id: str) -> str:
    return "p3bind-" + trace_sha(
        canonical_trace_json({"kind": kind_value, "source_object_id": source_object_id})
    )[:40]
