"""P1.5.2 — Capability Evidence Record.

Bridge between evaluation results and future capability claim verification.
EvaluationResult can become CapabilityEvidenceRecord — not verification itself.

Core law: CapabilityEvidenceRecord does not verify capability by itself.
USABLE is not VERIFIED. No numeric capability score.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum

from .evaluation_objects import (
    EvaluationEvidenceQuality,
    EvaluationOutcome,
    EvaluationResult,
    EvaluationResultSet,
    EvaluationVerdict,
)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class CapabilityEvidenceKind(str, Enum):
    EVALUATION_RESULT = "EVALUATION_RESULT"
    EVALUATION_RESULT_SET = "EVALUATION_RESULT_SET"
    IDENTITY_TEST_BATTERY = "IDENTITY_TEST_BATTERY"
    TRUST_EVIDENCE_BUNDLE = "TRUST_EVIDENCE_BUNDLE"
    OPERATOR_REVIEW = "OPERATOR_REVIEW"
    FIELD_TRACE = "FIELD_TRACE"
    ADVERSARIAL_EVALUATION = "ADVERSARIAL_EVALUATION"
    BENCHMARK_RUN = "BENCHMARK_RUN"
    REGRESSION_RUN = "REGRESSION_RUN"
    HUMAN_FEEDBACK = "HUMAN_FEEDBACK"
    UNKNOWN = "UNKNOWN"


class CapabilityEvidenceStatus(str, Enum):
    DRAFT = "DRAFT"
    CANDIDATE = "CANDIDATE"
    USABLE = "USABLE"
    INSUFFICIENT = "INSUFFICIENT"
    CONFLICTED = "CONFLICTED"
    STALE = "STALE"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"
    INVALID = "INVALID"
    REJECTED = "REJECTED"


class CapabilityEvidenceStrength(str, Enum):
    NONE = "NONE"
    WEAK = "WEAK"
    ADEQUATE = "ADEQUATE"
    STRONG = "STRONG"
    CONFLICTED = "CONFLICTED"
    UNKNOWN = "UNKNOWN"


# ---------------------------------------------------------------------------
# Invariants
# ---------------------------------------------------------------------------

P152_INVARIANTS: tuple[str, ...] = (
    "INV-P152-01: CapabilityEvidenceRecord does not verify capability by itself.",
    "INV-P152-02: EvaluationResult can become evidence, not verification.",
    "INV-P152-03: USABLE evidence requires ADEQUATE or STRONG strength.",
    "INV-P152-04: USABLE evidence requires source/evidence refs.",
    "INV-P152-05: CONFLICTED evidence blocks aggregate USABLE.",
    "INV-P152-06: REVOKED / INVALID evidence cannot support capability.",
    "INV-P152-07: EXPIRED evidence cannot be USABLE.",
    "INV-P152-08: Aggregation is categorical, not numeric.",
    "INV-P152-09: Evidence refs are not proof of truth by themselves.",
    "INV-P152-10: P1.5.7 will bind evidence to claims.",
    "INV-P152-11: P1.5.3 is the next module.",
)

_USABLE_STRENGTHS = frozenset({
    CapabilityEvidenceStrength.ADEQUATE,
    CapabilityEvidenceStrength.STRONG,
})

_STRENGTH_PRIORITY = {
    CapabilityEvidenceStrength.CONFLICTED: 0,
    CapabilityEvidenceStrength.NONE: 1,
    CapabilityEvidenceStrength.UNKNOWN: 2,
    CapabilityEvidenceStrength.WEAK: 3,
    CapabilityEvidenceStrength.ADEQUATE: 4,
    CapabilityEvidenceStrength.STRONG: 5,
}

_STATUS_BLOCKS_USABLE = frozenset({
    CapabilityEvidenceStatus.INVALID,
    CapabilityEvidenceStatus.REVOKED,
    CapabilityEvidenceStatus.CONFLICTED,
    CapabilityEvidenceStatus.EXPIRED,
})


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CapabilityEvidenceRecord:
    evidence_id: str
    kind: CapabilityEvidenceKind
    status: CapabilityEvidenceStatus
    strength: CapabilityEvidenceStrength
    capability_id: str | None = None
    claim_id: str | None = None
    source_result_ids: tuple[str, ...] = ()
    source_result_set_ids: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    supported_subject_id: str | None = None
    supported_subject_type: str | None = None
    produced_by_module: str | None = None
    created_at: str | None = None
    expires_at: str | None = None
    limitations: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    blockers: tuple[str, ...] = ()
    summary: str = ""


@dataclass(frozen=True)
class CapabilityEvidenceRequirement:
    requirement_id: str
    required_kinds: tuple[CapabilityEvidenceKind, ...]
    minimum_strength: CapabilityEvidenceStrength
    reason: str
    capability_id: str | None = None
    claim_id: str | None = None
    allow_stale: bool = False
    allow_conflicted: bool = False


@dataclass(frozen=True)
class CapabilityEvidenceLink:
    link_id: str
    evidence_id: str
    subject_id: str
    subject_type: str
    relationship: str
    supports_claim_id: str | None = None
    supports_capability_id: str | None = None
    required: bool = False
    satisfied: bool = False
    reason: str = ""


@dataclass(frozen=True)
class CapabilityEvidenceRecordSet:
    record_set_id: str
    records: tuple[CapabilityEvidenceRecord, ...]
    aggregate_status: CapabilityEvidenceStatus
    aggregate_strength: CapabilityEvidenceStrength
    capability_id: str | None = None
    claim_id: str | None = None
    usable_records: tuple[str, ...] = ()
    insufficient_records: tuple[str, ...] = ()
    conflicted_records: tuple[str, ...] = ()
    stale_records: tuple[str, ...] = ()
    invalid_records: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    blockers: tuple[str, ...] = ()
    summary: str = ""


@dataclass(frozen=True)
class CapabilityEvidenceRecordReport:
    report_id: str
    status: str  # READY, DEGRADED, BLOCKED
    summary: str
    records_created: int
    record_sets_created: int
    objects_added: tuple[str, ...]
    invariants: tuple[str, ...]
    warnings: tuple[str, ...] = ()
    blockers: tuple[str, ...] = ()
    next_module: str = "P1.5.3 — Evaluation Subject Registry"


# ---------------------------------------------------------------------------
# Mapping helpers
# ---------------------------------------------------------------------------


def _strength_from_evidence_quality(
    quality: EvaluationEvidenceQuality,
) -> CapabilityEvidenceStrength:
    mapping = {
        EvaluationEvidenceQuality.STRONG: CapabilityEvidenceStrength.STRONG,
        EvaluationEvidenceQuality.ADEQUATE: CapabilityEvidenceStrength.ADEQUATE,
        EvaluationEvidenceQuality.WEAK: CapabilityEvidenceStrength.WEAK,
        EvaluationEvidenceQuality.NONE: CapabilityEvidenceStrength.NONE,
        EvaluationEvidenceQuality.CONFLICTED: CapabilityEvidenceStrength.CONFLICTED,
        EvaluationEvidenceQuality.STALE: CapabilityEvidenceStrength.WEAK,
        EvaluationEvidenceQuality.UNKNOWN: CapabilityEvidenceStrength.UNKNOWN,
    }
    return mapping.get(quality, CapabilityEvidenceStrength.UNKNOWN)


def _status_from_verdict_and_outcome(
    verdict: EvaluationVerdict,
    outcome: EvaluationOutcome,
    evidence_quality: EvaluationEvidenceQuality,
) -> CapabilityEvidenceStatus:
    if evidence_quality == EvaluationEvidenceQuality.STALE:
        return CapabilityEvidenceStatus.STALE
    if outcome == EvaluationOutcome.ERROR:
        return CapabilityEvidenceStatus.INVALID
    if verdict == EvaluationVerdict.BLOCKED or outcome == EvaluationOutcome.BLOCKED:
        return CapabilityEvidenceStatus.INVALID
    if verdict == EvaluationVerdict.REJECTED:
        return CapabilityEvidenceStatus.REJECTED
    if verdict == EvaluationVerdict.CONFLICTED:
        return CapabilityEvidenceStatus.CONFLICTED
    if verdict == EvaluationVerdict.INSUFFICIENT_EVIDENCE:
        return CapabilityEvidenceStatus.INSUFFICIENT
    if verdict == EvaluationVerdict.PARTIALLY_SUPPORTED:
        return CapabilityEvidenceStatus.CANDIDATE
    if verdict == EvaluationVerdict.SUPPORTED:
        if evidence_quality in (
            EvaluationEvidenceQuality.ADEQUATE,
            EvaluationEvidenceQuality.STRONG,
        ):
            return CapabilityEvidenceStatus.USABLE
        return CapabilityEvidenceStatus.CANDIDATE
    if verdict == EvaluationVerdict.UNSUPPORTED:
        return CapabilityEvidenceStatus.INSUFFICIENT
    return CapabilityEvidenceStatus.DRAFT


# ---------------------------------------------------------------------------
# Engine: mapping from evaluation results
# ---------------------------------------------------------------------------


def capability_evidence_from_evaluation_result(
    *,
    evidence_id: str,
    result: EvaluationResult,
    capability_id: str | None = None,
    claim_id: str | None = None,
) -> CapabilityEvidenceRecord:
    """Map an EvaluationResult to a CapabilityEvidenceRecord. Does NOT verify capability."""
    if not evidence_id or not evidence_id.strip():
        raise ValueError("evidence_id must not be empty")

    strength = _strength_from_evidence_quality(result.evidence_quality)
    status = _status_from_verdict_and_outcome(
        result.verdict, result.outcome, result.evidence_quality,
    )

    warnings = list(result.warnings)
    blockers = list(result.blockers)
    limitations = list(result.limitations)

    if status == CapabilityEvidenceStatus.CONFLICTED and not warnings and not blockers:
        warnings.append("Conflicting evaluation evidence")

    if status == CapabilityEvidenceStatus.INVALID and not blockers:
        blockers.append("Evaluation result invalid or errored")

    summary = (
        f"Evidence from evaluation result {result.result_id}: "
        f"{result.outcome.value}/{result.verdict.value} → {status.value} "
        f"(not VERIFIED)"
    )

    return CapabilityEvidenceRecord(
        evidence_id=evidence_id.strip(),
        capability_id=capability_id,
        claim_id=claim_id,
        kind=CapabilityEvidenceKind.EVALUATION_RESULT,
        status=status,
        strength=strength,
        source_result_ids=(result.result_id,),
        evidence_refs=result.evidence_refs,
        limitations=tuple(limitations),
        warnings=tuple(warnings),
        blockers=tuple(blockers),
        summary=summary,
        produced_by_module="P1.5.2",
        created_at=datetime.now(timezone.utc).isoformat(),
    )


def capability_evidence_from_result_set(
    *,
    evidence_id: str,
    result_set: EvaluationResultSet,
    capability_id: str | None = None,
    claim_id: str | None = None,
) -> CapabilityEvidenceRecord:
    """Map an EvaluationResultSet to a CapabilityEvidenceRecord. Does NOT verify capability."""
    if not evidence_id or not evidence_id.strip():
        raise ValueError("evidence_id must not be empty")

    # Derive from aggregate fields using same mapping logic
    strength = _strength_from_evidence_quality(result_set.aggregate_evidence_quality)

    # Map aggregate verdict/outcome via a synthetic path
    verdict = result_set.aggregate_verdict
    outcome = result_set.aggregate_outcome

    status = _status_from_verdict_and_outcome(
        verdict, outcome, result_set.aggregate_evidence_quality,
    )

    all_evidence_refs = tuple(
        ref for r in result_set.results for ref in r.evidence_refs
    )
    warnings = list(result_set.warnings)
    blockers = list(result_set.blockers)

    if status == CapabilityEvidenceStatus.CONFLICTED and not warnings and not blockers:
        warnings.append("Conflicting aggregate evaluation evidence")

    if status == CapabilityEvidenceStatus.INVALID and not blockers:
        blockers.append("Aggregate evaluation result set invalid or errored")

    summary = (
        f"Evidence from result set {result_set.result_set_id}: "
        f"{outcome.value}/{verdict.value} → {status.value} "
        f"({len(result_set.results)} result(s), not VERIFIED)"
    )

    return CapabilityEvidenceRecord(
        evidence_id=evidence_id.strip(),
        capability_id=capability_id,
        claim_id=claim_id,
        kind=CapabilityEvidenceKind.EVALUATION_RESULT_SET,
        status=status,
        strength=strength,
        source_result_set_ids=(result_set.result_set_id,),
        source_result_ids=tuple(r.result_id for r in result_set.results),
        evidence_refs=all_evidence_refs,
        warnings=tuple(warnings),
        blockers=tuple(blockers),
        summary=summary,
        produced_by_module="P1.5.2",
        created_at=datetime.now(timezone.utc).isoformat(),
    )


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def validate_capability_evidence_record(
    record: CapabilityEvidenceRecord,
) -> tuple[str, ...]:
    """Validate a capability evidence record. Returns blockers. Does not mutate."""
    errors: list[str] = []

    if not record.evidence_id or not record.evidence_id.strip():
        errors.append("evidence_id must not be empty")

    if record.status == CapabilityEvidenceStatus.USABLE:
        if record.strength not in _USABLE_STRENGTHS:
            errors.append(
                f"USABLE status requires ADEQUATE or STRONG strength, got {record.strength.value}"
            )
        has_source = bool(
            record.source_result_ids or record.source_result_set_ids or record.evidence_refs
        )
        if not has_source:
            errors.append("USABLE status requires source_result_ids, source_result_set_ids, or evidence_refs")

    if record.status == CapabilityEvidenceStatus.CONFLICTED:
        if not record.warnings and not record.blockers:
            errors.append("CONFLICTED status requires warnings or blockers")

    if record.status == CapabilityEvidenceStatus.INVALID:
        if not record.blockers:
            errors.append("INVALID status requires blockers")

    return tuple(errors)


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------


def aggregate_capability_evidence_records(
    *,
    record_set_id: str,
    records: tuple[CapabilityEvidenceRecord, ...],
    capability_id: str | None = None,
    claim_id: str | None = None,
) -> CapabilityEvidenceRecordSet:
    """Aggregate capability evidence records categorically. No numeric scoring."""
    if not record_set_id or not record_set_id.strip():
        raise ValueError("record_set_id must not be empty")

    if not records:
        return CapabilityEvidenceRecordSet(
            record_set_id=record_set_id.strip(),
            capability_id=capability_id,
            claim_id=claim_id,
            records=(),
            aggregate_status=CapabilityEvidenceStatus.INSUFFICIENT,
            aggregate_strength=CapabilityEvidenceStrength.NONE,
            blockers=("No capability evidence records to aggregate",),
            summary="Empty evidence record set — insufficient",
        )

    usable: list[str] = []
    insufficient: list[str] = []
    conflicted: list[str] = []
    stale: list[str] = []
    invalid: list[str] = []
    all_warnings: list[str] = []
    all_blockers: list[str] = []

    for rec in records:
        all_warnings.extend(rec.warnings)
        all_blockers.extend(rec.blockers)
        if rec.status == CapabilityEvidenceStatus.USABLE:
            usable.append(rec.evidence_id)
        elif rec.status == CapabilityEvidenceStatus.CONFLICTED:
            conflicted.append(rec.evidence_id)
        elif rec.status == CapabilityEvidenceStatus.STALE:
            stale.append(rec.evidence_id)
        elif rec.status in (CapabilityEvidenceStatus.INVALID, CapabilityEvidenceStatus.REVOKED):
            invalid.append(rec.evidence_id)
        elif rec.status == CapabilityEvidenceStatus.INSUFFICIENT:
            insufficient.append(rec.evidence_id)

    has_blocking = any(rec.status in _STATUS_BLOCKS_USABLE for rec in records)
    has_conflicted = any(rec.status == CapabilityEvidenceStatus.CONFLICTED for rec in records)
    has_invalid = any(
        rec.status in (CapabilityEvidenceStatus.INVALID, CapabilityEvidenceStatus.REVOKED)
        for rec in records
    )

    if has_invalid:
        agg_status = CapabilityEvidenceStatus.INVALID
        agg_strength = CapabilityEvidenceStrength.NONE
    elif has_conflicted:
        agg_status = CapabilityEvidenceStatus.CONFLICTED
        agg_strength = CapabilityEvidenceStrength.CONFLICTED
    elif usable and not has_blocking:
        agg_status = CapabilityEvidenceStatus.USABLE
        usable_recs = [r for r in records if r.evidence_id in usable]
        strengths = [r.strength for r in usable_recs]
        if CapabilityEvidenceStrength.STRONG in strengths:
            agg_strength = CapabilityEvidenceStrength.STRONG
        else:
            agg_strength = CapabilityEvidenceStrength.ADEQUATE
    elif stale and not usable:
        agg_status = CapabilityEvidenceStatus.STALE
        agg_strength = CapabilityEvidenceStrength.WEAK
    elif insufficient or not usable:
        agg_status = CapabilityEvidenceStatus.INSUFFICIENT
        agg_strength = CapabilityEvidenceStrength.NONE
    else:
        agg_status = CapabilityEvidenceStatus.CANDIDATE
        agg_strength = min(
            (r.strength for r in records),
            key=lambda s: _STRENGTH_PRIORITY.get(s, 99),
        )

    return CapabilityEvidenceRecordSet(
        record_set_id=record_set_id.strip(),
        capability_id=capability_id,
        claim_id=claim_id,
        records=records,
        aggregate_status=agg_status,
        aggregate_strength=agg_strength,
        usable_records=tuple(usable),
        insufficient_records=tuple(insufficient),
        conflicted_records=tuple(conflicted),
        stale_records=tuple(stale),
        invalid_records=tuple(invalid),
        warnings=tuple(all_warnings),
        blockers=tuple(all_blockers),
        summary=f"Aggregated {len(records)} evidence record(s): {agg_status.value}/{agg_strength.value}",
    )


# ---------------------------------------------------------------------------
# Link builder
# ---------------------------------------------------------------------------


def build_capability_evidence_link(
    *,
    link_id: str,
    evidence_id: str,
    subject_id: str,
    subject_type: str,
    relationship: str,
    supports_claim_id: str | None = None,
    supports_capability_id: str | None = None,
    required: bool = False,
    satisfied: bool = False,
    reason: str = "",
) -> CapabilityEvidenceLink:
    """Build a capability evidence link. Does not verify capability."""
    if not link_id or not link_id.strip():
        raise ValueError("link_id must not be empty")
    if not evidence_id or not evidence_id.strip():
        raise ValueError("evidence_id must not be empty")
    if not subject_id or not subject_id.strip():
        raise ValueError("subject_id must not be empty")
    if not subject_type or not subject_type.strip():
        raise ValueError("subject_type must not be empty")
    if not relationship or not relationship.strip():
        raise ValueError("relationship must not be empty")

    return CapabilityEvidenceLink(
        link_id=link_id.strip(),
        evidence_id=evidence_id.strip(),
        subject_id=subject_id.strip(),
        subject_type=subject_type.strip(),
        relationship=relationship.strip(),
        supports_claim_id=supports_claim_id,
        supports_capability_id=supports_capability_id,
        required=required,
        satisfied=satisfied,
        reason=reason,
    )


# ---------------------------------------------------------------------------
# Report builder
# ---------------------------------------------------------------------------


def build_p152_capability_evidence_report(
    *,
    records_created: int = 0,
    record_sets_created: int = 0,
    warnings: tuple[str, ...] = (),
    blockers: tuple[str, ...] = (),
) -> CapabilityEvidenceRecordReport:
    """Build P1.5.2 capability evidence report."""
    objects = (
        "CapabilityEvidenceKind", "CapabilityEvidenceStatus", "CapabilityEvidenceStrength",
        "CapabilityEvidenceRecord", "CapabilityEvidenceRequirement",
        "CapabilityEvidenceLink", "CapabilityEvidenceRecordSet",
        "CapabilityEvidenceRecordReport",
    )

    if blockers:
        status = "BLOCKED"
        summary = f"P1.5.2 capability evidence BLOCKED: {len(blockers)} blocker(s)."
    elif warnings:
        status = "DEGRADED"
        summary = f"P1.5.2 capability evidence DEGRADED: {len(warnings)} warning(s)."
    else:
        status = "READY"
        summary = "P1.5.2 Capability Evidence Record READY. Next: P1.5.3 — Evaluation Subject Registry."

    ts = datetime.now(timezone.utc).isoformat()
    report_id = "p152_" + hashlib.sha256(ts.encode()).hexdigest()[:16]

    return CapabilityEvidenceRecordReport(
        report_id=report_id,
        status=status,
        summary=summary,
        records_created=records_created,
        record_sets_created=record_sets_created,
        objects_added=objects,
        invariants=P152_INVARIANTS,
        warnings=warnings,
        blockers=blockers,
        next_module="P1.5.3 — Evaluation Subject Registry",
    )


# ---------------------------------------------------------------------------
# Examples (for CLI / tests)
# ---------------------------------------------------------------------------


def example_usable_evidence_from_result() -> CapabilityEvidenceRecord:
    """Example USABLE evidence from a supported evaluation result."""
    from .evaluation_objects import example_supported_evaluation_result

    result = example_supported_evaluation_result()
    return capability_evidence_from_evaluation_result(
        evidence_id="ev_example_usable_1",
        result=result,
        capability_id="cap.example",
        claim_id="claim.example",
    )


# ---------------------------------------------------------------------------
# Serialization
# ---------------------------------------------------------------------------


def _enum_val(v: Enum) -> str:
    return v.value


def capability_evidence_record_to_dict(record: CapabilityEvidenceRecord) -> dict[str, object]:
    return {
        "evidence_id": record.evidence_id,
        "capability_id": record.capability_id,
        "claim_id": record.claim_id,
        "kind": _enum_val(record.kind),
        "status": _enum_val(record.status),
        "strength": _enum_val(record.strength),
        "source_result_ids": list(record.source_result_ids),
        "source_result_set_ids": list(record.source_result_set_ids),
        "evidence_refs": list(record.evidence_refs),
        "supported_subject_id": record.supported_subject_id,
        "supported_subject_type": record.supported_subject_type,
        "produced_by_module": record.produced_by_module,
        "created_at": record.created_at,
        "expires_at": record.expires_at,
        "limitations": list(record.limitations),
        "warnings": list(record.warnings),
        "blockers": list(record.blockers),
        "summary": record.summary,
    }


def capability_evidence_requirement_to_dict(
    requirement: CapabilityEvidenceRequirement,
) -> dict[str, object]:
    return {
        "requirement_id": requirement.requirement_id,
        "capability_id": requirement.capability_id,
        "claim_id": requirement.claim_id,
        "required_kinds": [_enum_val(k) for k in requirement.required_kinds],
        "minimum_strength": _enum_val(requirement.minimum_strength),
        "allow_stale": requirement.allow_stale,
        "allow_conflicted": requirement.allow_conflicted,
        "reason": requirement.reason,
    }


def capability_evidence_link_to_dict(link: CapabilityEvidenceLink) -> dict[str, object]:
    return {
        "link_id": link.link_id,
        "evidence_id": link.evidence_id,
        "subject_id": link.subject_id,
        "subject_type": link.subject_type,
        "relationship": link.relationship,
        "supports_claim_id": link.supports_claim_id,
        "supports_capability_id": link.supports_capability_id,
        "required": link.required,
        "satisfied": link.satisfied,
        "reason": link.reason,
    }


def capability_evidence_record_set_to_dict(
    record_set: CapabilityEvidenceRecordSet,
) -> dict[str, object]:
    return {
        "record_set_id": record_set.record_set_id,
        "capability_id": record_set.capability_id,
        "claim_id": record_set.claim_id,
        "records": [capability_evidence_record_to_dict(r) for r in record_set.records],
        "aggregate_status": _enum_val(record_set.aggregate_status),
        "aggregate_strength": _enum_val(record_set.aggregate_strength),
        "usable_records": list(record_set.usable_records),
        "insufficient_records": list(record_set.insufficient_records),
        "conflicted_records": list(record_set.conflicted_records),
        "stale_records": list(record_set.stale_records),
        "invalid_records": list(record_set.invalid_records),
        "warnings": list(record_set.warnings),
        "blockers": list(record_set.blockers),
        "summary": record_set.summary,
    }


def capability_evidence_record_report_to_dict(
    report: CapabilityEvidenceRecordReport,
) -> dict[str, object]:
    return {
        "report_id": report.report_id,
        "status": report.status,
        "summary": report.summary,
        "records_created": report.records_created,
        "record_sets_created": report.record_sets_created,
        "objects_added": list(report.objects_added),
        "invariants": list(report.invariants),
        "warnings": list(report.warnings),
        "blockers": list(report.blockers),
        "next_module": report.next_module,
    }


__all__ = [
    "CapabilityEvidenceKind", "CapabilityEvidenceStatus", "CapabilityEvidenceStrength",
    "CapabilityEvidenceRecord", "CapabilityEvidenceRequirement",
    "CapabilityEvidenceLink", "CapabilityEvidenceRecordSet", "CapabilityEvidenceRecordReport",
    "P152_INVARIANTS",
    "capability_evidence_from_evaluation_result", "capability_evidence_from_result_set",
    "validate_capability_evidence_record", "aggregate_capability_evidence_records",
    "build_capability_evidence_link", "build_p152_capability_evidence_report",
    "example_usable_evidence_from_result",
    "capability_evidence_record_to_dict", "capability_evidence_requirement_to_dict",
    "capability_evidence_link_to_dict", "capability_evidence_record_set_to_dict",
    "capability_evidence_record_report_to_dict",
]
