"""P5-TRACE-D TRACE_VERIFIED resolver — the single verification authority.

``TRACE_VERIFIED`` is a *resolver decision*, never a label any object can
self-assign. This module is the **only** place a ``TRACE_VERIFIED`` verdict can
be produced, and it is added **only** as a member of the resolver-local
:class:`TraceVerificationStatus` enum — the ``TraceTruthLabel`` vocabulary from
P5-A/B/C is untouched and still has no ``TRACE_VERIFIED`` member.

Gate law (all required for ``TRACE_VERIFIED``):

* a PASS integrity proof that is a :class:`TraceVerificationReceipt` — a bare
  ``TraceHashVerificationResult`` caps at ``TRACE_BOUND`` (a receipt binds the
  verification to a scope/chain head);
* every required evidence kind covered by a PRESENT / TRACE_INTEGRITY_VERIFIED
  ``EvidenceRef``;
* binding coverage COMPLETE, when a binding is supplied;
* a COMPATIBLE (or COMPATIBLE_WITH_WARNINGS) schema decision, when supplied;
* zero blocking findings (``TraceHashFinding`` of severity ERROR/CRITICAL).

Each dimension alone downgrades — hash PASS alone, a receipt alone, an evidence
ref alone, and a COMPLETE binding alone are each *not enough*. When uncertain the
resolver downgrades (TRACE_BOUND / PARTIAL / UNAVAILABLE / DENIED / ERROR); it
never fakes ``TRACE_VERIFIED``. The resolver is pure: no mutation, no trace
append, no execution, no authority, and no semantic/business/policy claim.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum
from typing import Any

from .evidence_ref import EvidenceRef, EvidenceStatus, TraceBindingCoverageStatus
from .p3_binding import P3TraceBinding
from .p4_binding import P4TraceBinding
from .runtime_submit_bridge import RuntimeSubmitTraceBinding
from .trace_hash import (
    AurelTraceError,
    TraceTruthLabel,
    canonical_trace_json,
    require_nonempty,
    trace_sha,
)
from .trace_receipts import TraceVerificationReceipt
from .trace_schema import TraceSchemaCompatibility, TraceSchemaCompatibilityDecision
from .trace_verify import (
    TraceFindingSeverity,
    TraceHashFinding,
    TraceHashVerificationResult,
    TraceVerificationStatus as HashVerificationStatus,
)


class TraceVerificationTargetKind(str, Enum):
    """Closed-world targets the resolver can evaluate."""

    TRACE_RUN = "TRACE_RUN"
    TRACE_EVENT = "TRACE_EVENT"
    TRACE_BINDING = "TRACE_BINDING"
    EVIDENCE_SET = "EVIDENCE_SET"
    RUNTIME_SUBMIT_BINDING = "RUNTIME_SUBMIT_BINDING"
    P3_BINDING = "P3_BINDING"
    P4_BINDING = "P4_BINDING"
    CHAIN_HEAD = "CHAIN_HEAD"


class TraceVerificationStatus(str, Enum):
    """Resolver output status. ``TRACE_VERIFIED`` lives here, not in labels."""

    TRACE_VERIFIED = "TRACE_VERIFIED"
    TRACE_BOUND = "TRACE_BOUND"
    PARTIAL = "PARTIAL"
    UNAVAILABLE = "UNAVAILABLE"
    DENIED = "DENIED"
    ERROR = "ERROR"


@dataclass(frozen=True)
class TraceVerificationDecision:
    """Structured result of one resolver evaluation. Deterministic, read-only."""

    decision_id: str
    target_kind: TraceVerificationTargetKind
    target_id: str
    status: TraceVerificationStatus
    verified: bool
    reason: str
    blocking_findings: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    required_evidence: tuple[str, ...] = ()
    missing_evidence: tuple[str, ...] = ()
    source_receipt_ids: tuple[str, ...] = ()
    source_binding_ids: tuple[str, ...] = ()
    source_evidence_ref_ids: tuple[str, ...] = ()
    source_schema_decision_ids: tuple[str, ...] = ()
    truth_label: TraceTruthLabel = TraceTruthLabel.LIVE

    def __post_init__(self) -> None:
        require_nonempty(self, "decision_id", "target_id", "reason")
        verified_status = self.status is TraceVerificationStatus.TRACE_VERIFIED
        if self.verified != verified_status:
            raise AurelTraceError(
                "verified must be True iff status is TRACE_VERIFIED"
            )
        if verified_status:
            if self.blocking_findings:
                raise AurelTraceError(
                    "a TRACE_VERIFIED decision must have no blocking findings"
                )
            if self.missing_evidence:
                raise AurelTraceError(
                    "a TRACE_VERIFIED decision must have no missing evidence"
                )
        if self.truth_label is TraceTruthLabel.TRACE_INTEGRITY_VERIFIED:
            raise AurelTraceError(
                "a resolver decision is a LIVE record; the status carries the verdict"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "target_kind": self.target_kind.value,
            "target_id": self.target_id,
            "status": self.status.value,
            "verified": self.verified,
            "reason": self.reason,
            "blocking_findings": list(self.blocking_findings),
            "warnings": list(self.warnings),
            "required_evidence": list(self.required_evidence),
            "missing_evidence": list(self.missing_evidence),
            "source_receipt_ids": list(self.source_receipt_ids),
            "source_binding_ids": list(self.source_binding_ids),
            "source_evidence_ref_ids": list(self.source_evidence_ref_ids),
            "source_schema_decision_ids": list(self.source_schema_decision_ids),
            "truth_label": self.truth_label.value,
        }


def _decision_id(
    target_kind: TraceVerificationTargetKind,
    target_id: str,
    status: TraceVerificationStatus,
    source_ids: Sequence[str],
) -> str:
    return "tvdec-" + trace_sha(
        canonical_trace_json(
            {
                "target_kind": target_kind.value,
                "target_id": target_id,
                "status": status.value,
                "source_ids": list(source_ids),
            }
        )
    )[:40]


def _blocking_findings(findings: Sequence[TraceHashFinding]) -> tuple[str, ...]:
    return tuple(
        f.message
        for f in findings
        if f.severity in (TraceFindingSeverity.ERROR, TraceFindingSeverity.CRITICAL)
    )


def _build_decision(
    *,
    target_kind: TraceVerificationTargetKind,
    target_id: str,
    status: TraceVerificationStatus,
    reason: str,
    blocking_findings: tuple[str, ...] = (),
    warnings: tuple[str, ...] = (),
    required_evidence: tuple[str, ...] = (),
    missing_evidence: tuple[str, ...] = (),
    source_receipt_ids: tuple[str, ...] = (),
    source_binding_ids: tuple[str, ...] = (),
    source_evidence_ref_ids: tuple[str, ...] = (),
    source_schema_decision_ids: tuple[str, ...] = (),
) -> TraceVerificationDecision:
    all_source_ids = (
        source_receipt_ids
        + source_binding_ids
        + source_evidence_ref_ids
        + source_schema_decision_ids
    )
    return TraceVerificationDecision(
        decision_id=_decision_id(target_kind, target_id, status, all_source_ids),
        target_kind=target_kind,
        target_id=target_id,
        status=status,
        verified=status is TraceVerificationStatus.TRACE_VERIFIED,
        reason=reason,
        blocking_findings=blocking_findings,
        warnings=warnings,
        required_evidence=required_evidence,
        missing_evidence=missing_evidence,
        source_receipt_ids=source_receipt_ids,
        source_binding_ids=source_binding_ids,
        source_evidence_ref_ids=source_evidence_ref_ids,
        source_schema_decision_ids=source_schema_decision_ids,
    )


def _evidence_gap(
    required_evidence_kinds: Sequence[str],
    evidence_refs: Sequence[EvidenceRef],
) -> tuple[tuple[str, ...], tuple[str, ...], bool]:
    """Return (missing_kinds, error_reasons, any_error)."""

    present_kinds = {
        r.evidence_kind.value
        for r in evidence_refs
        if r.status
        in (EvidenceStatus.PRESENT, EvidenceStatus.TRACE_INTEGRITY_VERIFIED)
    }
    missing = tuple(k for k in required_evidence_kinds if k not in present_kinds)
    error_reasons = tuple(
        f"{r.evidence_kind.value}: {r.missing_reason or 'evidence error'}"
        for r in evidence_refs
        if r.status is EvidenceStatus.ERROR
    )
    return missing, error_reasons, bool(error_reasons)


def resolve_trace_target(
    *,
    target_kind: TraceVerificationTargetKind,
    target_id: str,
    receipt: TraceVerificationReceipt | None = None,
    hash_result: TraceHashVerificationResult | None = None,
    schema_decision: TraceSchemaCompatibilityDecision | None = None,
    evidence_refs: Sequence[EvidenceRef] = (),
    required_evidence_kinds: Sequence[str] = (),
    binding_coverage: TraceBindingCoverageStatus | None = None,
    findings: Sequence[TraceHashFinding] = (),
) -> TraceVerificationDecision:
    """Evaluate one target against the closed gate law. Pure and deterministic."""

    if not isinstance(target_kind, TraceVerificationTargetKind):
        return _build_decision(
            target_kind=TraceVerificationTargetKind.TRACE_RUN,
            target_id=str(target_id) or "unknown",
            status=TraceVerificationStatus.ERROR,
            reason=(
                f"unknown target kind {target_kind!r}; target kinds are closed-world"
            ),
        )
    if not target_id or not target_id.strip():
        return _build_decision(
            target_kind=target_kind,
            target_id="unknown",
            status=TraceVerificationStatus.ERROR,
            reason="target_id must not be empty",
        )

    receipt_ids = (receipt.receipt_id,) if receipt else ()
    schema_ids = (schema_decision.decision_id,) if schema_decision else ()
    evidence_ids = tuple(r.evidence_ref_id for r in evidence_refs)
    required = tuple(required_evidence_kinds)

    # (1) Blocking findings deny outright.
    blocking = _blocking_findings(findings)
    if blocking:
        return _build_decision(
            target_kind=target_kind,
            target_id=target_id,
            status=TraceVerificationStatus.DENIED,
            reason="blocking findings prevent verification",
            blocking_findings=blocking,
            source_receipt_ids=receipt_ids,
            source_evidence_ref_ids=evidence_ids,
            source_schema_decision_ids=schema_ids,
        )

    # (2) Schema must be compatible when supplied.
    warnings: tuple[str, ...] = ()
    if schema_decision is not None:
        decision = schema_decision.decision
        if decision in (
            TraceSchemaCompatibility.UNSUPPORTED,
            TraceSchemaCompatibility.UNKNOWN,
            TraceSchemaCompatibility.ERROR,
            TraceSchemaCompatibility.REQUIRES_UPCASTER,
        ):
            return _build_decision(
                target_kind=target_kind,
                target_id=target_id,
                status=TraceVerificationStatus.DENIED,
                reason=f"schema decision {decision.value} blocks verification: "
                f"{schema_decision.reason}",
                source_schema_decision_ids=schema_ids,
                source_receipt_ids=receipt_ids,
            )
        if decision is TraceSchemaCompatibility.COMPATIBLE_WITH_WARNINGS:
            warnings = warnings + (f"schema warning: {schema_decision.reason}",)

    # (3) Evidence errors are inconsistent input.
    missing_evidence, evidence_error_reasons, any_evidence_error = _evidence_gap(
        required, evidence_refs
    )
    if any_evidence_error:
        return _build_decision(
            target_kind=target_kind,
            target_id=target_id,
            status=TraceVerificationStatus.ERROR,
            reason="one or more evidence refs are in ERROR state",
            warnings=warnings + evidence_error_reasons,
            required_evidence=required,
            missing_evidence=missing_evidence,
            source_evidence_ref_ids=evidence_ids,
            source_receipt_ids=receipt_ids,
        )

    # (4) Integrity proof. A receipt is required for TRACE_VERIFIED; a bare hash
    # result (or a receipt that did not PASS) caps below it.
    has_pass_receipt = receipt is not None and receipt.verified
    has_failing_receipt = receipt is not None and not receipt.verified
    has_pass_hash = (
        hash_result is not None
        and hash_result.status is HashVerificationStatus.PASS
    )
    has_failing_hash = (
        hash_result is not None
        and hash_result.status
        in (HashVerificationStatus.FAIL,)
    )

    if has_failing_receipt or has_failing_hash:
        return _build_decision(
            target_kind=target_kind,
            target_id=target_id,
            status=TraceVerificationStatus.DENIED,
            reason="integrity proof did not pass",
            warnings=warnings,
            required_evidence=required,
            missing_evidence=missing_evidence,
            source_receipt_ids=receipt_ids,
        )

    if not has_pass_receipt and not has_pass_hash:
        return _build_decision(
            target_kind=target_kind,
            target_id=target_id,
            status=TraceVerificationStatus.UNAVAILABLE,
            reason="no integrity proof (hash result or verification receipt) supplied",
            warnings=warnings,
            required_evidence=required,
            missing_evidence=missing_evidence,
        )

    # (5) A passing hash result without a receipt is bound but not verifiable.
    if not has_pass_receipt:
        return _build_decision(
            target_kind=target_kind,
            target_id=target_id,
            status=TraceVerificationStatus.TRACE_BOUND,
            reason=(
                "hash verification passed but no verification receipt binds it to a "
                "scope/chain head; hash PASS alone is not TRACE_VERIFIED"
            ),
            warnings=warnings,
            required_evidence=required,
            missing_evidence=missing_evidence,
            source_evidence_ref_ids=evidence_ids,
        )

    # (6) Required evidence must be fully present.
    if missing_evidence:
        return _build_decision(
            target_kind=target_kind,
            target_id=target_id,
            status=TraceVerificationStatus.PARTIAL,
            reason="integrity proven but required evidence is missing",
            warnings=warnings,
            required_evidence=required,
            missing_evidence=missing_evidence,
            source_receipt_ids=receipt_ids,
            source_evidence_ref_ids=evidence_ids,
        )

    # (7) Binding coverage must be COMPLETE when supplied.
    if binding_coverage is not None and binding_coverage is not (
        TraceBindingCoverageStatus.COMPLETE
    ):
        return _build_decision(
            target_kind=target_kind,
            target_id=target_id,
            status=TraceVerificationStatus.PARTIAL,
            reason=(
                f"binding coverage is {binding_coverage.value}, not COMPLETE; "
                "binding COMPLETE is required but not sufficient alone"
            ),
            warnings=warnings,
            required_evidence=required,
            missing_evidence=missing_evidence,
            source_receipt_ids=receipt_ids,
            source_evidence_ref_ids=evidence_ids,
        )

    # (8) A PASS receipt with no corroborating evidence/binding is integrity-only:
    # a receipt alone is not TRACE_VERIFIED.
    corroborated = bool(required) or binding_coverage is not None
    if not corroborated:
        return _build_decision(
            target_kind=target_kind,
            target_id=target_id,
            status=TraceVerificationStatus.TRACE_BOUND,
            reason=(
                "verification receipt present but no evidence/binding corroborates "
                "the target; receipt alone is not TRACE_VERIFIED"
            ),
            warnings=warnings,
            source_receipt_ids=receipt_ids,
        )

    # All gates satisfied.
    return _build_decision(
        target_kind=target_kind,
        target_id=target_id,
        status=TraceVerificationStatus.TRACE_VERIFIED,
        reason="all resolver gates satisfied",
        warnings=warnings,
        required_evidence=required,
        source_receipt_ids=receipt_ids,
        source_evidence_ref_ids=evidence_ids,
        source_schema_decision_ids=schema_ids,
    )


# --------------------------------------------------------------------------- #
#  Target-specific helpers (thin wrappers over resolve_trace_target).
# --------------------------------------------------------------------------- #
def resolve_trace_run(
    *,
    trace_run_id: str,
    receipt: TraceVerificationReceipt | None = None,
    hash_result: TraceHashVerificationResult | None = None,
    schema_decision: TraceSchemaCompatibilityDecision | None = None,
    evidence_refs: Sequence[EvidenceRef] = (),
    required_evidence_kinds: Sequence[str] = (),
    findings: Sequence[TraceHashFinding] = (),
) -> TraceVerificationDecision:
    return resolve_trace_target(
        target_kind=TraceVerificationTargetKind.TRACE_RUN,
        target_id=trace_run_id,
        receipt=receipt,
        hash_result=hash_result,
        schema_decision=schema_decision,
        evidence_refs=evidence_refs,
        required_evidence_kinds=required_evidence_kinds,
        findings=findings,
    )


def resolve_chain_head(
    *,
    trace_run_id: str,
    receipt: TraceVerificationReceipt | None = None,
    hash_result: TraceHashVerificationResult | None = None,
    evidence_refs: Sequence[EvidenceRef] = (),
    required_evidence_kinds: Sequence[str] = (),
    findings: Sequence[TraceHashFinding] = (),
) -> TraceVerificationDecision:
    return resolve_trace_target(
        target_kind=TraceVerificationTargetKind.CHAIN_HEAD,
        target_id=trace_run_id,
        receipt=receipt,
        hash_result=hash_result,
        evidence_refs=evidence_refs,
        required_evidence_kinds=required_evidence_kinds,
        findings=findings,
    )


def resolve_trace_event(
    *,
    trace_event_id: str,
    receipt: TraceVerificationReceipt | None = None,
    evidence_refs: Sequence[EvidenceRef] = (),
    required_evidence_kinds: Sequence[str] = (),
    findings: Sequence[TraceHashFinding] = (),
) -> TraceVerificationDecision:
    return resolve_trace_target(
        target_kind=TraceVerificationTargetKind.TRACE_EVENT,
        target_id=trace_event_id,
        receipt=receipt,
        evidence_refs=evidence_refs,
        required_evidence_kinds=required_evidence_kinds,
        findings=findings,
    )


def resolve_evidence_set(
    *,
    evidence_set_id: str,
    evidence_refs: Sequence[EvidenceRef],
    receipt: TraceVerificationReceipt | None = None,
    required_evidence_kinds: Sequence[str] = (),
    findings: Sequence[TraceHashFinding] = (),
) -> TraceVerificationDecision:
    return resolve_trace_target(
        target_kind=TraceVerificationTargetKind.EVIDENCE_SET,
        target_id=evidence_set_id,
        receipt=receipt,
        evidence_refs=evidence_refs,
        required_evidence_kinds=required_evidence_kinds,
        findings=findings,
    )


def resolve_runtime_submit_binding(
    binding: RuntimeSubmitTraceBinding,
    *,
    receipt: TraceVerificationReceipt | None = None,
    required_evidence_kinds: Sequence[str] = (),
    findings: Sequence[TraceHashFinding] = (),
) -> TraceVerificationDecision:
    return resolve_trace_target(
        target_kind=TraceVerificationTargetKind.RUNTIME_SUBMIT_BINDING,
        target_id=binding.binding_id,
        receipt=receipt,
        evidence_refs=binding.evidence_refs,
        required_evidence_kinds=required_evidence_kinds,
        binding_coverage=binding.coverage_status,
        findings=findings,
    )


def resolve_p3_binding(
    binding: P3TraceBinding,
    *,
    receipt: TraceVerificationReceipt | None = None,
    required_evidence_kinds: Sequence[str] = (),
    findings: Sequence[TraceHashFinding] = (),
) -> TraceVerificationDecision:
    return resolve_trace_target(
        target_kind=TraceVerificationTargetKind.P3_BINDING,
        target_id=binding.p3_binding_id,
        receipt=receipt,
        evidence_refs=binding.evidence_refs,
        required_evidence_kinds=required_evidence_kinds,
        binding_coverage=binding.coverage_status,
        findings=findings,
    )


def resolve_p4_binding(
    binding: P4TraceBinding,
    *,
    receipt: TraceVerificationReceipt | None = None,
    required_evidence_kinds: Sequence[str] = (),
    findings: Sequence[TraceHashFinding] = (),
) -> TraceVerificationDecision:
    return resolve_trace_target(
        target_kind=TraceVerificationTargetKind.P4_BINDING,
        target_id=binding.p4_binding_id,
        receipt=receipt,
        evidence_refs=binding.evidence_refs,
        required_evidence_kinds=required_evidence_kinds,
        binding_coverage=binding.coverage_status,
        findings=findings,
    )


@dataclass(frozen=True)
class TraceVerifiedResolver:
    """Stateless single authority for the TRACE_VERIFIED verdict.

    Holds no runtime handle and performs no side effects. Every method is a thin
    wrapper over the pure ``resolve_*`` functions.
    """

    resolver_id: str = "trace-verified-resolver.p5-trace-d.v1"
    truth_label: TraceTruthLabel = TraceTruthLabel.LIVE

    # Locked: the resolver decides; it never mutates, appends, or executes.
    mutates: bool = False
    appends_trace: bool = False
    executes: bool = False

    def __post_init__(self) -> None:
        for field_name in ("mutates", "appends_trace", "executes"):
            if getattr(self, field_name) is True:
                raise AurelTraceError(
                    f"{field_name} must be False — the resolver is a pure decision gate"
                )

    def resolve(self, **kwargs: Any) -> TraceVerificationDecision:
        return resolve_trace_target(**kwargs)

    resolve_trace_run = staticmethod(resolve_trace_run)
    resolve_chain_head = staticmethod(resolve_chain_head)
    resolve_trace_event = staticmethod(resolve_trace_event)
    resolve_evidence_set = staticmethod(resolve_evidence_set)
    resolve_runtime_submit_binding = staticmethod(resolve_runtime_submit_binding)
    resolve_p3_binding = staticmethod(resolve_p3_binding)
    resolve_p4_binding = staticmethod(resolve_p4_binding)
