"""Capability evidence contracts gated by trace, evidence and verifier refs."""
from __future__ import annotations

from dataclasses import InitVar, asdict, dataclass
from enum import Enum

from .context import (
    ContextAdequacyReport,
    ContextAdequacyStatus,
    ContextBindingRef,
    context_binding_ref_to_dict,
)
from .evidence import EvidenceRef, evidence_ref_to_dict
from .trace import TraceEventRef
from .verifier import VerifierResult, VerifierResultStatus


_VERIFIED_FACTORY_SEAL = "P1.5.11B_VERIFIED_CAPABILITY_FACTORY"


class CapabilityEvidenceStatus(str, Enum):
    UNVERIFIED = "unverified"
    VERIFIED = "verified"
    FAILED = "failed"
    INCONCLUSIVE = "inconclusive"


class EvidenceStrengthLevel(str, Enum):
    NONE = "none"
    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"
    VERIFIED = "verified"


_VERIFICATION_STRENGTHS = frozenset({
    EvidenceStrengthLevel.STRONG,
    EvidenceStrengthLevel.VERIFIED,
})

_CONTEXT_LIMITATION_MARKERS = (
    "context",
    "partial context",
    "context limitation",
    "limited context",
)


@dataclass(frozen=True)
class CapabilityEvidenceRecord:
    capability_evidence_id: str
    capability_id: str
    status: CapabilityEvidenceStatus
    source_trace_event_ref: TraceEventRef | None
    source_event_hash: str | None
    evidence_refs: tuple[EvidenceRef, ...]
    verifier_result_ref: str | None
    context_binding_ref: ContextBindingRef | None = None
    context_adequacy_ref: str | None = None
    evidence_strength: EvidenceStrengthLevel = EvidenceStrengthLevel.NONE
    limitations: tuple[str, ...] = ()
    created_at: str = ""
    verification_seal: InitVar[str | None] = None

    def __post_init__(self, verification_seal: str | None) -> None:
        if not self.capability_evidence_id or not self.capability_evidence_id.strip():
            raise ValueError("capability_evidence_id must not be empty")
        if not self.capability_id or not self.capability_id.strip():
            raise ValueError("capability_id must not be empty")
        if not self.created_at or not self.created_at.strip():
            raise ValueError("created_at must not be empty")
        if self.status == CapabilityEvidenceStatus.VERIFIED:
            if verification_seal != _VERIFIED_FACTORY_SEAL:
                raise ValueError("verified CapabilityEvidenceRecord must be created by factory")
            errors = _validate_verified_structure(self)
            if errors:
                raise ValueError("; ".join(errors))


def create_verified_capability_evidence_record(
    *,
    capability_evidence_id: str,
    capability_id: str,
    source_trace_event_ref: TraceEventRef | None,
    source_event_hash: str | None,
    evidence_refs: tuple[EvidenceRef, ...],
    verifier_result: VerifierResult | None,
    context_binding_ref: ContextBindingRef | None = None,
    context_adequacy_report: ContextAdequacyReport | None = None,
    evidence_strength: EvidenceStrengthLevel = EvidenceStrengthLevel.VERIFIED,
    limitations: tuple[str, ...],
    created_at: str,
) -> CapabilityEvidenceRecord:
    verifier_result_ref = verifier_result.verifier_id if verifier_result else None
    record = CapabilityEvidenceRecord(
        capability_evidence_id=capability_evidence_id,
        capability_id=capability_id,
        status=CapabilityEvidenceStatus.VERIFIED,
        source_trace_event_ref=source_trace_event_ref,
        source_event_hash=source_event_hash,
        evidence_refs=evidence_refs,
        verifier_result_ref=verifier_result_ref,
        context_binding_ref=context_binding_ref,
        context_adequacy_ref=(
            context_adequacy_report.context_adequacy_id if context_adequacy_report else None
        ),
        evidence_strength=evidence_strength,
        limitations=limitations,
        created_at=created_at,
        verification_seal=_VERIFIED_FACTORY_SEAL,
    )
    errors = validate_capability_evidence(
        record,
        verifier_result=verifier_result,
        context_adequacy_report=context_adequacy_report,
    )
    if errors:
        raise ValueError("; ".join(errors))
    return record


def validate_capability_evidence(
    record: CapabilityEvidenceRecord,
    *,
    verifier_result: VerifierResult | None = None,
    context_adequacy_report: ContextAdequacyReport | None = None,
) -> tuple[str, ...]:
    errors: list[str] = []
    if record.status != CapabilityEvidenceStatus.VERIFIED:
        return tuple(errors)

    errors.extend(_validate_verified_structure(record))
    if record.source_trace_event_ref is not None and record.source_event_hash is not None:
        if record.source_event_hash != record.source_trace_event_ref.event_hash:
            errors.append("source_event_hash must match source_trace_event_ref.event_hash")
    if record.evidence_strength not in _VERIFICATION_STRENGTHS:
        errors.append("verified capability requires evidence_strength strong or verified")
    if verifier_result is None:
        errors.append("verified capability requires linked VerifierResult")
    else:
        if record.verifier_result_ref != verifier_result.verifier_id:
            errors.append("verifier_result_ref must match linked VerifierResult")
        if verifier_result.status != VerifierResultStatus.PASS:
            errors.append("verified capability requires verifier status pass")
        verifier_evidence_ids = {ref.evidence_id for ref in verifier_result.evidence_refs}
        record_evidence_ids = {ref.evidence_id for ref in record.evidence_refs}
        if record_evidence_ids and not record_evidence_ids.issubset(verifier_evidence_ids):
            errors.append("verified capability evidence_refs must be covered by VerifierResult")
        if not verifier_result.limitations:
            errors.append("verified capability requires verifier limitations")

    if context_adequacy_report is not None:
        if record.context_adequacy_ref != context_adequacy_report.context_adequacy_id:
            errors.append("context_adequacy_ref must match ContextAdequacyReport")
        if (
            record.context_binding_ref is not None
            and record.context_binding_ref != context_adequacy_report.context_binding_ref
        ):
            errors.append("context_binding_ref must match ContextAdequacyReport context")
        if context_adequacy_report.status == ContextAdequacyStatus.UNSAFE:
            errors.append("unsafe context blocks verified capability")
        if context_adequacy_report.status == ContextAdequacyStatus.INSUFFICIENT:
            errors.append("insufficient context blocks verified capability")
        if (
            context_adequacy_report.status == ContextAdequacyStatus.PARTIAL
            and not _has_context_limitation(record.limitations)
        ):
            errors.append("partial context requires explicit context limitation")
    return tuple(errors)


def capability_evidence_record_to_dict(record: CapabilityEvidenceRecord) -> dict[str, object]:
    data: dict[str, object] = asdict(record)
    data["status"] = record.status.value
    data["source_trace_event_ref"] = (
        asdict(record.source_trace_event_ref) if record.source_trace_event_ref else None
    )
    data["source_event_hash"] = record.source_event_hash
    data["evidence_refs"] = [evidence_ref_to_dict(ref) for ref in record.evidence_refs]
    data["context_binding_ref"] = (
        context_binding_ref_to_dict(record.context_binding_ref)
        if record.context_binding_ref else None
    )
    data["context_adequacy_ref"] = record.context_adequacy_ref
    data["evidence_strength"] = record.evidence_strength.value
    data["limitations"] = list(record.limitations)
    return data


def _validate_verified_structure(record: CapabilityEvidenceRecord) -> list[str]:
    errors: list[str] = []
    if record.source_trace_event_ref is None:
        errors.append("verified capability requires source_trace_event_ref")
    if not record.source_event_hash:
        errors.append("verified capability requires source_event_hash")
    if not record.evidence_refs:
        errors.append("verified capability requires at least one EvidenceRef")
    if not record.verifier_result_ref:
        errors.append("verified capability requires verifier_result_ref")
    if not record.limitations:
        errors.append("verified capability limitations must be non-empty")
    return errors


def _has_context_limitation(limitations: tuple[str, ...]) -> bool:
    joined = " ".join(limitations).lower()
    return any(marker in joined for marker in _CONTEXT_LIMITATION_MARKERS)
