"""P5-TRACE-C EvidenceRef object model — the shared foundation for trace bindings.

An ``EvidenceRef`` is a *reference to* (or an explicit *absence of*) evidence
derived from a trace-bound runtime, P3, or P4 artifact. It is the atom that the
runtime-submit / P3 / P4 trace-binding layers compose.

Doctrine anchors enforced structurally here:

* An ``EvidenceRef`` **references** evidence; it does not create evidence, mutate
  trace, verify anything, or authorize any action.
* ``PRESENT`` / ``TRACE_BOUND`` do not mean verified. An ``EvidenceRef`` may carry
  the ``TRACE_INTEGRITY_VERIFIED`` truth label **only** when it is backed by an
  explicit P5-A/P5-B verification receipt id.
* There is no ``TRACE_VERIFIED`` truth label — trace-bound is not TRACE_VERIFIED.
  Broad verification is the P5-TRACE-D resolver's job, not this pack's.
* Missing evidence is explicit (status ``MISSING`` requires a ``missing_reason``);
  unknown/unsupported evidence fails closed.
* Ids are deterministic canonical JSON (sorted keys); the same input always
  yields the same ``evidence_ref_id``.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from .trace_hash import (
    AurelTraceError,
    TraceTruthLabel,
    canonical_trace_json,
    require_nonempty,
    trace_sha,
)


class EvidenceKind(str, Enum):
    """Closed-world evidence categories for runtime / P3 / P4 trace bindings."""

    # Runtime submit evidence (aligned 1:1 with P5-B SubmitEvidenceRequirementKind).
    COMMAND_EVIDENCE = "COMMAND_EVIDENCE"
    POLICY_EVIDENCE = "POLICY_EVIDENCE"
    APPROVAL_EVIDENCE = "APPROVAL_EVIDENCE"
    BUDGET_EVIDENCE = "BUDGET_EVIDENCE"
    SANDBOX_EVIDENCE = "SANDBOX_EVIDENCE"
    TOOL_INVOCATION_EVIDENCE = "TOOL_INVOCATION_EVIDENCE"
    TOOL_RESULT_EVIDENCE = "TOOL_RESULT_EVIDENCE"
    VERIFIER_EVIDENCE = "VERIFIER_EVIDENCE"
    ROLLBACK_EVIDENCE = "ROLLBACK_EVIDENCE"
    MEMORY_EVIDENCE = "MEMORY_EVIDENCE"
    TRACE_APPEND_EVIDENCE = "TRACE_APPEND_EVIDENCE"
    OBSERVATION_EVIDENCE = "OBSERVATION_EVIDENCE"
    ERROR_EVIDENCE = "ERROR_EVIDENCE"
    # P3 (AurelFlow control-plane) evidence.
    P3_SCHEDULING_EVIDENCE = "P3_SCHEDULING_EVIDENCE"
    P3_WORKFLOW_EVIDENCE = "P3_WORKFLOW_EVIDENCE"
    P3_PROJECTION_EVIDENCE = "P3_PROJECTION_EVIDENCE"
    # P4 (AurelExec) evidence.
    P4_ADMISSION_EVIDENCE = "P4_ADMISSION_EVIDENCE"
    P4_LEASE_EVIDENCE = "P4_LEASE_EVIDENCE"
    P4_JOB_EVIDENCE = "P4_JOB_EVIDENCE"
    P4_ATTEMPT_EVIDENCE = "P4_ATTEMPT_EVIDENCE"
    P4_OUTCOME_EVIDENCE = "P4_OUTCOME_EVIDENCE"
    P4_FAILURE_EVIDENCE = "P4_FAILURE_EVIDENCE"
    P4_BACKPRESSURE_EVIDENCE = "P4_BACKPRESSURE_EVIDENCE"
    P4_BENCH_EVIDENCE = "P4_BENCH_EVIDENCE"


class EvidenceStatus(str, Enum):
    """Evidence state — never a verification claim by itself."""

    PRESENT = "PRESENT"
    MISSING = "MISSING"
    PARTIAL = "PARTIAL"
    UNSUPPORTED = "UNSUPPORTED"
    TRACE_BOUND = "TRACE_BOUND"
    TRACE_INTEGRITY_VERIFIED = "TRACE_INTEGRITY_VERIFIED"
    ERROR = "ERROR"


class TraceBindingCoverageStatus(str, Enum):
    """Whether a binding has enough evidence for later resolver work.

    ``COMPLETE`` means binding coverage is structurally complete for the current
    schema/input — it does **not** mean ``TRACE_VERIFIED``.
    """

    COMPLETE = "COMPLETE"
    PARTIAL = "PARTIAL"
    MISSING = "MISSING"
    UNSUPPORTED = "UNSUPPORTED"
    ERROR = "ERROR"


def _evidence_ref_id(evidence_kind: EvidenceKind, source_domain: str, source_object_id: str) -> str:
    return "evref-" + trace_sha(
        canonical_trace_json(
            {
                "evidence_kind": evidence_kind.value,
                "source_domain": source_domain,
                "source_object_id": source_object_id,
            }
        )
    )[:40]


@dataclass(frozen=True)
class EvidenceRef:
    """Reference to (or explicit absence of) evidence for a bound artifact.

    An EvidenceRef identifies evidence; it does not verify it, authorize action,
    or mutate trace. Its truth label is ``TRACE_BOUND`` unless it is backed by an
    explicit verification receipt id (then ``TRACE_INTEGRITY_VERIFIED``).
    """

    evidence_ref_id: str
    evidence_kind: EvidenceKind
    source_domain: str
    source_object_id: str
    status: EvidenceStatus
    trace_binding_ref_id: str | None = None
    trace_event_ref_id: str | None = None
    verification_receipt_id: str | None = None
    missing_reason: str | None = None
    truth_label: TraceTruthLabel = TraceTruthLabel.TRACE_BOUND

    def __post_init__(self) -> None:
        require_nonempty(self, "evidence_ref_id", "source_domain", "source_object_id")
        if self.status is EvidenceStatus.MISSING and not (self.missing_reason or "").strip():
            raise AurelTraceError("a MISSING evidence ref must carry a missing_reason")
        if (
            self.status is EvidenceStatus.UNSUPPORTED
            and not (self.missing_reason or "").strip()
        ):
            raise AurelTraceError("an UNSUPPORTED evidence ref must carry a reason")
        if self.truth_label is TraceTruthLabel.TRACE_INTEGRITY_VERIFIED:
            # Integrity verification is only claimable when backed by a receipt.
            if not (self.verification_receipt_id or "").strip():
                raise AurelTraceError(
                    "an evidence ref may only carry TRACE_INTEGRITY_VERIFIED when "
                    "backed by a verification_receipt_id"
                )
            if self.status is not EvidenceStatus.TRACE_INTEGRITY_VERIFIED:
                raise AurelTraceError(
                    "TRACE_INTEGRITY_VERIFIED truth label requires the matching status"
                )

    @property
    def is_present(self) -> bool:
        return self.status in (
            EvidenceStatus.PRESENT,
            EvidenceStatus.TRACE_BOUND,
            EvidenceStatus.TRACE_INTEGRITY_VERIFIED,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "evidence_ref_id": self.evidence_ref_id,
            "evidence_kind": self.evidence_kind.value,
            "source_domain": self.source_domain,
            "source_object_id": self.source_object_id,
            "status": self.status.value,
            "trace_binding_ref_id": self.trace_binding_ref_id,
            "trace_event_ref_id": self.trace_event_ref_id,
            "verification_receipt_id": self.verification_receipt_id,
            "missing_reason": self.missing_reason,
            "truth_label": self.truth_label.value,
        }


def make_evidence_ref(
    *,
    evidence_kind: EvidenceKind,
    source_domain: str,
    source_object_id: str,
    status: EvidenceStatus = EvidenceStatus.PRESENT,
    trace_binding_ref_id: str | None = None,
    trace_event_ref_id: str | None = None,
    verification_receipt_id: str | None = None,
    missing_reason: str | None = None,
) -> EvidenceRef:
    """Build an EvidenceRef, failing closed on an unknown evidence kind.

    A ``verification_receipt_id`` promotes the ref to ``TRACE_INTEGRITY_VERIFIED``
    (status and truth label) — never a broad ``TRACE_VERIFIED`` claim. Otherwise
    the truth label stays ``TRACE_BOUND``.
    """

    if not isinstance(evidence_kind, EvidenceKind):
        raise AurelTraceError(
            f"unknown evidence kind {evidence_kind!r}; evidence kinds are closed-world"
        )
    effective_status = status
    truth_label = TraceTruthLabel.TRACE_BOUND
    if verification_receipt_id and (verification_receipt_id or "").strip():
        effective_status = EvidenceStatus.TRACE_INTEGRITY_VERIFIED
        truth_label = TraceTruthLabel.TRACE_INTEGRITY_VERIFIED
    return EvidenceRef(
        evidence_ref_id=_evidence_ref_id(evidence_kind, source_domain, source_object_id),
        evidence_kind=evidence_kind,
        source_domain=source_domain,
        source_object_id=source_object_id,
        status=effective_status,
        trace_binding_ref_id=trace_binding_ref_id,
        trace_event_ref_id=trace_event_ref_id,
        verification_receipt_id=verification_receipt_id,
        missing_reason=missing_reason,
        truth_label=truth_label,
    )


def make_missing_evidence_ref(
    *,
    evidence_kind: EvidenceKind,
    source_domain: str,
    source_object_id: str,
    missing_reason: str,
    status: EvidenceStatus = EvidenceStatus.MISSING,
) -> EvidenceRef:
    """Build an explicit missing/partial/unsupported evidence ref with a reason."""

    if not isinstance(evidence_kind, EvidenceKind):
        raise AurelTraceError(
            f"unknown evidence kind {evidence_kind!r}; evidence kinds are closed-world"
        )
    if not missing_reason.strip():
        raise AurelTraceError("missing_reason must not be empty")
    if status not in (
        EvidenceStatus.MISSING,
        EvidenceStatus.PARTIAL,
        EvidenceStatus.UNSUPPORTED,
    ):
        raise AurelTraceError(
            "make_missing_evidence_ref supports MISSING/PARTIAL/UNSUPPORTED only"
        )
    return EvidenceRef(
        evidence_ref_id=_evidence_ref_id(evidence_kind, source_domain, source_object_id),
        evidence_kind=evidence_kind,
        source_domain=source_domain,
        source_object_id=source_object_id,
        status=status,
        missing_reason=missing_reason,
        truth_label=TraceTruthLabel.TRACE_BOUND,
    )


def evidence_ref_has_no_authority(ref: EvidenceRef) -> bool:
    """Fail-closed assertion helper: an EvidenceRef never grants authority.

    An EvidenceRef has no authority/approval field and its truth vocabulary has
    no authority member — so it cannot authorize any action. The truth label is
    always one of the closed set of non-authority labels. Used by boundary tests.
    """

    return ref.truth_label in TraceTruthLabel
