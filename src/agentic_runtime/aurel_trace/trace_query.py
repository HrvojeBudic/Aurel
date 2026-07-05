"""P5-TRACE-D trace query read model — formats resolver decisions, read-only.

The query model **reflects** resolver decisions; it never decides
``TRACE_VERIFIED`` itself and structurally cannot upgrade a decision's status (it
copies ``status``/``verified`` verbatim). It preserves missing evidence, blocking
findings, warnings, and unavailable reasons. It is side-effect free: no trace
append, no runtime mutation, no repair, no replay.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from .trace_hash import (
    AurelTraceError,
    TraceTruthLabel,
    canonical_trace_json,
    require_nonempty,
    trace_sha,
)
from .trace_resolver import (
    TraceVerificationDecision,
    TraceVerificationStatus,
    TraceVerificationTargetKind,
)


@dataclass(frozen=True)
class TraceRunSummary:
    trace_run_id: str
    verification_status: TraceVerificationStatus
    verified: bool
    decision_id: str
    reason: str
    missing_evidence: tuple[str, ...] = ()
    blocking_findings: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    truth_label: TraceTruthLabel = TraceTruthLabel.LIVE

    def to_dict(self) -> dict[str, Any]:
        return {
            "trace_run_id": self.trace_run_id,
            "verification_status": self.verification_status.value,
            "verified": self.verified,
            "decision_id": self.decision_id,
            "reason": self.reason,
            "missing_evidence": list(self.missing_evidence),
            "blocking_findings": list(self.blocking_findings),
            "warnings": list(self.warnings),
            "truth_label": self.truth_label.value,
        }


@dataclass(frozen=True)
class TraceEventSummary:
    trace_event_id: str
    verification_status: TraceVerificationStatus
    verified: bool
    decision_id: str
    reason: str
    missing_evidence: tuple[str, ...] = ()
    blocking_findings: tuple[str, ...] = ()
    truth_label: TraceTruthLabel = TraceTruthLabel.LIVE

    def to_dict(self) -> dict[str, Any]:
        return {
            "trace_event_id": self.trace_event_id,
            "verification_status": self.verification_status.value,
            "verified": self.verified,
            "decision_id": self.decision_id,
            "reason": self.reason,
            "missing_evidence": list(self.missing_evidence),
            "blocking_findings": list(self.blocking_findings),
            "truth_label": self.truth_label.value,
        }


@dataclass(frozen=True)
class TraceBindingSummary:
    binding_id: str
    binding_kind: str
    verification_status: TraceVerificationStatus
    verified: bool
    decision_id: str
    reason: str
    missing_evidence: tuple[str, ...] = ()
    blocking_findings: tuple[str, ...] = ()
    truth_label: TraceTruthLabel = TraceTruthLabel.LIVE

    def to_dict(self) -> dict[str, Any]:
        return {
            "binding_id": self.binding_id,
            "binding_kind": self.binding_kind,
            "verification_status": self.verification_status.value,
            "verified": self.verified,
            "decision_id": self.decision_id,
            "reason": self.reason,
            "missing_evidence": list(self.missing_evidence),
            "blocking_findings": list(self.blocking_findings),
            "truth_label": self.truth_label.value,
        }


@dataclass(frozen=True)
class TraceEvidenceSummary:
    target_id: str
    verification_status: TraceVerificationStatus
    verified: bool
    decision_id: str
    reason: str
    required_evidence: tuple[str, ...] = ()
    missing_evidence: tuple[str, ...] = ()
    truth_label: TraceTruthLabel = TraceTruthLabel.LIVE

    def to_dict(self) -> dict[str, Any]:
        return {
            "target_id": self.target_id,
            "verification_status": self.verification_status.value,
            "verified": self.verified,
            "decision_id": self.decision_id,
            "reason": self.reason,
            "required_evidence": list(self.required_evidence),
            "missing_evidence": list(self.missing_evidence),
            "truth_label": self.truth_label.value,
        }


@dataclass(frozen=True)
class TraceVerificationSummary:
    summary_id: str
    target_kind: TraceVerificationTargetKind
    target_id: str
    verification_status: TraceVerificationStatus
    verified: bool
    decision_id: str
    reason: str
    warnings: tuple[str, ...] = ()
    missing_evidence: tuple[str, ...] = ()
    blocking_findings: tuple[str, ...] = ()
    truth_label: TraceTruthLabel = TraceTruthLabel.LIVE

    def to_dict(self) -> dict[str, Any]:
        return {
            "summary_id": self.summary_id,
            "target_kind": self.target_kind.value,
            "target_id": self.target_id,
            "verification_status": self.verification_status.value,
            "verified": self.verified,
            "decision_id": self.decision_id,
            "reason": self.reason,
            "warnings": list(self.warnings),
            "missing_evidence": list(self.missing_evidence),
            "blocking_findings": list(self.blocking_findings),
            "truth_label": self.truth_label.value,
        }


@dataclass(frozen=True)
class TraceAuditSummary:
    audit_id: str
    targets_checked: int
    verified_count: int
    trace_bound_count: int
    partial_count: int
    unavailable_count: int
    denied_count: int
    error_count: int
    blocking_findings: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    truth_label: TraceTruthLabel = TraceTruthLabel.LIVE

    def to_dict(self) -> dict[str, Any]:
        return {
            "audit_id": self.audit_id,
            "targets_checked": self.targets_checked,
            "verified_count": self.verified_count,
            "trace_bound_count": self.trace_bound_count,
            "partial_count": self.partial_count,
            "unavailable_count": self.unavailable_count,
            "denied_count": self.denied_count,
            "error_count": self.error_count,
            "blocking_findings": list(self.blocking_findings),
            "warnings": list(self.warnings),
            "truth_label": self.truth_label.value,
        }


@dataclass(frozen=True)
class TraceQueryReadModel:
    """Read-only view over a fixed set of resolver decisions."""

    read_model_id: str
    decisions: tuple[TraceVerificationDecision, ...] = ()
    truth_label: TraceTruthLabel = TraceTruthLabel.LIVE

    # Locked: the query model reflects; it never decides or mutates.
    decides_verification: bool = False
    mutates: bool = False

    def __post_init__(self) -> None:
        require_nonempty(self, "read_model_id")
        for field_name in ("decides_verification", "mutates"):
            if getattr(self, field_name) is True:
                raise AurelTraceError(
                    f"{field_name} must be False — the query model reflects resolver "
                    "decisions, it does not decide or mutate"
                )

    def _decision_for(self, target_id: str) -> TraceVerificationDecision | None:
        for decision in self.decisions:
            if decision.target_id == target_id:
                return decision
        return None

    def summarize_trace_run(self, decision: TraceVerificationDecision) -> TraceRunSummary:
        return TraceRunSummary(
            trace_run_id=decision.target_id,
            verification_status=decision.status,
            verified=decision.verified,
            decision_id=decision.decision_id,
            reason=decision.reason,
            missing_evidence=decision.missing_evidence,
            blocking_findings=decision.blocking_findings,
            warnings=decision.warnings,
        )

    def summarize_trace_event(
        self, decision: TraceVerificationDecision
    ) -> TraceEventSummary:
        return TraceEventSummary(
            trace_event_id=decision.target_id,
            verification_status=decision.status,
            verified=decision.verified,
            decision_id=decision.decision_id,
            reason=decision.reason,
            missing_evidence=decision.missing_evidence,
            blocking_findings=decision.blocking_findings,
        )

    def summarize_trace_binding(
        self, decision: TraceVerificationDecision
    ) -> TraceBindingSummary:
        return TraceBindingSummary(
            binding_id=decision.target_id,
            binding_kind=decision.target_kind.value,
            verification_status=decision.status,
            verified=decision.verified,
            decision_id=decision.decision_id,
            reason=decision.reason,
            missing_evidence=decision.missing_evidence,
            blocking_findings=decision.blocking_findings,
        )

    def summarize_evidence(
        self, decision: TraceVerificationDecision
    ) -> TraceEvidenceSummary:
        return TraceEvidenceSummary(
            target_id=decision.target_id,
            verification_status=decision.status,
            verified=decision.verified,
            decision_id=decision.decision_id,
            reason=decision.reason,
            required_evidence=decision.required_evidence,
            missing_evidence=decision.missing_evidence,
        )

    def summarize_verification(
        self, decision: TraceVerificationDecision
    ) -> TraceVerificationSummary:
        summary_id = "tvsum-" + trace_sha(
            canonical_trace_json({"decision_id": decision.decision_id})
        )[:32]
        return TraceVerificationSummary(
            summary_id=summary_id,
            target_kind=decision.target_kind,
            target_id=decision.target_id,
            verification_status=decision.status,
            verified=decision.verified,
            decision_id=decision.decision_id,
            reason=decision.reason,
            warnings=decision.warnings,
            missing_evidence=decision.missing_evidence,
            blocking_findings=decision.blocking_findings,
        )

    def summarize_audit(
        self, decisions: Sequence[TraceVerificationDecision] | None = None
    ) -> TraceAuditSummary:
        rows = tuple(decisions) if decisions is not None else self.decisions

        def _count(status: TraceVerificationStatus) -> int:
            return sum(1 for d in rows if d.status is status)

        blocking: list[str] = []
        warnings: list[str] = []
        for d in rows:
            blocking.extend(d.blocking_findings)
            warnings.extend(d.warnings)
        audit_id = "tausum-" + trace_sha(
            canonical_trace_json({"decision_ids": [d.decision_id for d in rows]})
        )[:32]
        return TraceAuditSummary(
            audit_id=audit_id,
            targets_checked=len(rows),
            verified_count=_count(TraceVerificationStatus.TRACE_VERIFIED),
            trace_bound_count=_count(TraceVerificationStatus.TRACE_BOUND),
            partial_count=_count(TraceVerificationStatus.PARTIAL),
            unavailable_count=_count(TraceVerificationStatus.UNAVAILABLE),
            denied_count=_count(TraceVerificationStatus.DENIED),
            error_count=_count(TraceVerificationStatus.ERROR),
            blocking_findings=tuple(blocking),
            warnings=tuple(warnings),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "read_model_id": self.read_model_id,
            "decisions": [d.to_dict() for d in self.decisions],
            "audit": self.summarize_audit().to_dict(),
            "decides_verification": self.decides_verification,
            "mutates": self.mutates,
            "truth_label": self.truth_label.value,
        }
