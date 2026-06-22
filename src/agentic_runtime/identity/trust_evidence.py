"""P1.4.18 Trust Evidence Linkage.

Links evidence references to agent identities and lifecycle states.
Classifies trust posture categorically — never as a numeric score.

P1.4.18 links evidence references and classifies trust posture.
It does not grant authority, execute tools, mutate lifecycle state,
validate legal truth, or calculate a fake numeric trust score.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class TrustEvidenceKind(str, Enum):
    SOURCE_ATTESTATION = "SOURCE_ATTESTATION"
    IDENTITY_CARD = "IDENTITY_CARD"
    SELF_MODEL = "SELF_MODEL"
    OPERATOR_CONTRACT = "OPERATOR_CONTRACT"
    AUTONOMY_DECISION = "AUTONOMY_DECISION"
    MEASURED_AUTONOMY_REPORT = "MEASURED_AUTONOMY_REPORT"
    CAPABILITY_CLAIM_DECISION = "CAPABILITY_CLAIM_DECISION"
    DOCTRINE_ASSIMILATION_DECISION = "DOCTRINE_ASSIMILATION_DECISION"
    AUTHORITY_DELTA_REPORT = "AUTHORITY_DELTA_REPORT"
    OPERATOR_CONSENT_RECORD = "OPERATOR_CONSENT_RECORD"
    IDENTITY_TEST_BATTERY_REPORT = "IDENTITY_TEST_BATTERY_REPORT"
    LIFECYCLE_TRANSITION_DECISION = "LIFECYCLE_TRANSITION_DECISION"
    LIFECYCLE_TRANSITION_EVENT = "LIFECYCLE_TRANSITION_EVENT"
    REPORT = "REPORT"
    MANUAL_OPERATOR_NOTE = "MANUAL_OPERATOR_NOTE"
    UNKNOWN = "UNKNOWN"


class TrustEvidenceStatus(str, Enum):
    PRESENT = "PRESENT"
    MISSING = "MISSING"
    STALE = "STALE"
    CONFLICTED = "CONFLICTED"
    INVALID = "INVALID"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"
    UNKNOWN = "UNKNOWN"


class TrustPosture(str, Enum):
    UNSUPPORTED = "UNSUPPORTED"
    PARTIALLY_SUPPORTED = "PARTIALLY_SUPPORTED"
    SUPPORTED = "SUPPORTED"
    DEGRADED = "DEGRADED"
    CONFLICTED = "CONFLICTED"
    BLOCKED = "BLOCKED"
    EXPIRED = "EXPIRED"
    UNKNOWN = "UNKNOWN"


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TrustEvidenceRef:
    evidence_id: str
    kind: TrustEvidenceKind
    ref: str
    title: str | None = None
    status: TrustEvidenceStatus = TrustEvidenceStatus.PRESENT
    produced_by_module: str | None = None
    created_at: str | None = None
    expires_at: str | None = None
    hash_ref: str | None = None
    source_attestation_id: str | None = None
    summary: str = ""
    warnings: tuple[str, ...] = ()
    blockers: tuple[str, ...] = ()


@dataclass(frozen=True)
class TrustEvidenceRequirement:
    requirement_id: str
    kind: TrustEvidenceKind
    required_for: str
    required: bool
    acceptable_statuses: tuple[TrustEvidenceStatus, ...]
    reason: str


@dataclass(frozen=True)
class TrustEvidenceLink:
    link_id: str
    subject_id: str
    subject_type: str
    evidence_id: str
    relationship: str
    required: bool
    satisfied: bool
    reason: str


@dataclass(frozen=True)
class TrustEvidenceBundle:
    bundle_id: str
    agent_id: str
    lifecycle_state: str | None
    trust_posture: TrustPosture
    evidence_refs: tuple[TrustEvidenceRef, ...]
    requirements: tuple[TrustEvidenceRequirement, ...]
    links: tuple[TrustEvidenceLink, ...]
    missing_required_evidence: tuple[str, ...] = ()
    conflicted_evidence: tuple[str, ...] = ()
    stale_evidence: tuple[str, ...] = ()
    expired_evidence: tuple[str, ...] = ()
    revoked_evidence: tuple[str, ...] = ()
    invalid_evidence: tuple[str, ...] = ()
    blockers: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    summary: str = ""


@dataclass(frozen=True)
class TrustEvidenceLinkageReport:
    report_id: str
    agent_id: str
    posture: TrustPosture
    bundle_id: str
    total_evidence: int
    required_evidence: int
    satisfied_required_evidence: int
    missing_required_evidence: tuple[str, ...] = ()
    conflicted_evidence: tuple[str, ...] = ()
    stale_evidence: tuple[str, ...] = ()
    expired_evidence: tuple[str, ...] = ()
    revoked_evidence: tuple[str, ...] = ()
    invalid_evidence: tuple[str, ...] = ()
    blockers: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    summary: str = ""


# ---------------------------------------------------------------------------
# Default evidence requirements by lifecycle state
# ---------------------------------------------------------------------------


def _mkreq(
    requirement_id: str,
    kind: TrustEvidenceKind,
    required_for: str,
    required: bool = True,
    acceptable_statuses: tuple[TrustEvidenceStatus, ...] = (TrustEvidenceStatus.PRESENT,),
    reason: str = "",
) -> TrustEvidenceRequirement:
    return TrustEvidenceRequirement(
        requirement_id=requirement_id,
        kind=kind,
        required_for=required_for,
        required=required,
        acceptable_statuses=acceptable_statuses,
        reason=reason or f"{kind.value} required for {required_for}",
    )


def default_trust_evidence_requirements_for_lifecycle(
    lifecycle_state: str,
) -> tuple[TrustEvidenceRequirement, ...]:
    ls = lifecycle_state.upper()

    if ls == "DRAFT":
        return (
            _mkreq("draft.identity_card", TrustEvidenceKind.IDENTITY_CARD, "DRAFT lifecycle"),
        )
    if ls == "CANDIDATE":
        return (
            _mkreq("candidate.identity_card", TrustEvidenceKind.IDENTITY_CARD, "CANDIDATE lifecycle"),
            _mkreq("candidate.source_attestation", TrustEvidenceKind.SOURCE_ATTESTATION, "CANDIDATE lifecycle"),
            _mkreq("candidate.capability_claim", TrustEvidenceKind.CAPABILITY_CLAIM_DECISION, "CANDIDATE lifecycle"),
        )
    if ls == "ACTIVE":
        return (
            _mkreq("active.identity_card", TrustEvidenceKind.IDENTITY_CARD, "ACTIVE lifecycle"),
            _mkreq("active.source_attestation", TrustEvidenceKind.SOURCE_ATTESTATION, "ACTIVE lifecycle"),
            _mkreq("active.test_battery", TrustEvidenceKind.IDENTITY_TEST_BATTERY_REPORT, "ACTIVE lifecycle"),
            _mkreq("active.lifecycle_transition", TrustEvidenceKind.LIFECYCLE_TRANSITION_DECISION, "ACTIVE lifecycle"),
            _mkreq("active.capability_claim", TrustEvidenceKind.CAPABILITY_CLAIM_DECISION, "ACTIVE lifecycle"),
        )
    if ls == "RESTRICTED":
        return (
            _mkreq("restricted.identity_card", TrustEvidenceKind.IDENTITY_CARD, "RESTRICTED lifecycle"),
            _mkreq(
                "restricted.restriction_reason", TrustEvidenceKind.REPORT, "RESTRICTED lifecycle",
                reason="RESTRICTED requires restriction reason evidence",
            ),
        )
    if ls == "SUSPENDED":
        return (
            _mkreq("suspended.suspension_reason", TrustEvidenceKind.REPORT, "SUSPENDED lifecycle"),
        )
    if ls == "DEPRECATED":
        return (
            _mkreq("deprecated.deprecation_reason", TrustEvidenceKind.REPORT, "DEPRECATED lifecycle"),
        )
    if ls == "RETIRED":
        return (
            _mkreq("retired.retirement_reason", TrustEvidenceKind.REPORT, "RETIRED lifecycle"),
        )
    if ls == "REVOKED":
        return (
            _mkreq("revoked.revocation_reason", TrustEvidenceKind.REPORT, "REVOKED lifecycle"),
        )
    return ()


# ---------------------------------------------------------------------------
# Trust posture resolver
# ---------------------------------------------------------------------------


# Statuses that are "not OK" for supporting trust
_BAD_STATUSES: frozenset[TrustEvidenceStatus] = frozenset({
    TrustEvidenceStatus.INVALID,
    TrustEvidenceStatus.REVOKED,
})
_SOFT_BAD_STATUSES: frozenset[TrustEvidenceStatus] = frozenset({
    TrustEvidenceStatus.EXPIRED,
    TrustEvidenceStatus.STALE,
    TrustEvidenceStatus.MISSING,
    TrustEvidenceStatus.UNKNOWN,
})
_CONFLICT_STATUSES: frozenset[TrustEvidenceStatus] = frozenset({
    TrustEvidenceStatus.CONFLICTED,
})


def resolve_trust_posture(
    *,
    requirements: tuple[TrustEvidenceRequirement, ...],
    evidence_refs: tuple[TrustEvidenceRef, ...],
    links: tuple[TrustEvidenceLink, ...],
) -> TrustPosture:
    """Resolve categorical trust posture from evidence. No numeric score."""
    if not requirements:
        return TrustPosture.UNKNOWN

    evidence_by_kind: dict[TrustEvidenceKind, list[TrustEvidenceRef]] = {}
    for ev in evidence_refs:
        evidence_by_kind.setdefault(ev.kind, []).append(ev)

    # 1. Check for revoked/invalid required evidence → BLOCKED
    for req in requirements:
        if not req.required:
            continue
        evs = evidence_by_kind.get(req.kind, [])
        # If all evidence of required kind is revoked or invalid → BLOCKED
        if evs and all(e.status in _BAD_STATUSES for e in evs):
            return TrustPosture.BLOCKED

    # 2. Check for conflicted evidence → CONFLICTED
    for ev in evidence_refs:
        if ev.status == TrustEvidenceStatus.CONFLICTED:
            return TrustPosture.CONFLICTED

    # 3. Check required evidence
    satisfied_required = 0
    total_required = sum(1 for r in requirements if r.required)
    has_expired_required = False
    has_stale_required = False

    for req in requirements:
        if not req.required:
            continue
        evs = evidence_by_kind.get(req.kind, [])
        matched = False
        for ev in evs:
            if ev.status in req.acceptable_statuses:
                matched = True
                break
            if ev.status == TrustEvidenceStatus.EXPIRED:
                has_expired_required = True
            if ev.status == TrustEvidenceStatus.STALE:
                has_stale_required = True
        if matched:
            satisfied_required += 1

    # 4. Priority decisions

    # 4a. Required evidence expired → EXPIRED
    if has_expired_required and satisfied_required < total_required:
        return TrustPosture.EXPIRED

    # 4b. Required evidence missing → UNSUPPORTED
    if satisfied_required < total_required:
        if satisfied_required == 0:
            return TrustPosture.UNSUPPORTED
        return TrustPosture.PARTIALLY_SUPPORTED

    # 4c. Stale evidence → DEGRADED
    if has_stale_required:
        return TrustPosture.DEGRADED

    # 4d. All required evidence present and valid → SUPPORTED
    if satisfied_required == total_required:
        return TrustPosture.SUPPORTED

    return TrustPosture.UNKNOWN


# ---------------------------------------------------------------------------
# Bundle builder
# ---------------------------------------------------------------------------


def build_trust_evidence_bundle(
    *,
    agent_id: str,
    lifecycle_state: str | None,
    evidence_refs: tuple[TrustEvidenceRef, ...],
    requirements: tuple[TrustEvidenceRequirement, ...] | None = None,
) -> TrustEvidenceBundle:
    """Build a trust evidence bundle with posture resolution."""
    if requirements is None and lifecycle_state is not None:
        requirements = default_trust_evidence_requirements_for_lifecycle(lifecycle_state)
    if requirements is None:
        requirements = ()

    evidence_by_kind: dict[TrustEvidenceKind, list[TrustEvidenceRef]] = {}
    for ev in evidence_refs:
        evidence_by_kind.setdefault(ev.kind, []).append(ev)

    # Build links
    links: list[TrustEvidenceLink] = []
    for req in requirements:
        evs = evidence_by_kind.get(req.kind, [])
        if not evs:
            links.append(TrustEvidenceLink(
                link_id=f"lnk_{req.requirement_id}",
                subject_id=agent_id,
                subject_type="agent_identity",
                evidence_id="",
                relationship=f"requires_{req.kind.value}",
                required=req.required,
                satisfied=False,
                reason=f"No evidence of kind {req.kind.value} found",
            ))
        else:
            for ev in evs:
                satisfied = ev.status in req.acceptable_statuses
                links.append(TrustEvidenceLink(
                    link_id=f"lnk_{req.requirement_id}_{ev.evidence_id}",
                    subject_id=agent_id,
                    subject_type="agent_identity",
                    evidence_id=ev.evidence_id,
                    relationship=f"requires_{req.kind.value}",
                    required=req.required,
                    satisfied=satisfied,
                    reason=f"Evidence status {ev.status.value} {'acceptable' if satisfied else 'not acceptable'}",
                ))

    posture = resolve_trust_posture(
        requirements=requirements,
        evidence_refs=evidence_refs,
        links=tuple(links),
    )

    missing: list[str] = []
    conflicted: list[str] = []
    stale: list[str] = []
    expired: list[str] = []
    revoked: list[str] = []
    invalid: list[str] = []
    blockers: list[str] = []
    all_warnings: list[str] = []

    for req in requirements:
        if not req.required:
            continue
        evs = evidence_by_kind.get(req.kind, [])
        if not evs:
            missing.append(req.requirement_id)
            continue
        has_acceptable = any(e.status in req.acceptable_statuses for e in evs)
        if not has_acceptable:
            missing.append(req.requirement_id)
        for ev in evs:
            if ev.status == TrustEvidenceStatus.CONFLICTED:
                conflicted.append(ev.evidence_id)
            if ev.status == TrustEvidenceStatus.STALE:
                stale.append(ev.evidence_id)
            if ev.status == TrustEvidenceStatus.EXPIRED:
                expired.append(ev.evidence_id)
            if ev.status == TrustEvidenceStatus.REVOKED:
                revoked.append(ev.evidence_id)
                blockers.append(f"revoked:{ev.evidence_id}")
            if ev.status == TrustEvidenceStatus.INVALID:
                invalid.append(ev.evidence_id)
                blockers.append(f"invalid:{ev.evidence_id}")
            if ev.blockers:
                blockers.extend(ev.blockers)
            if ev.warnings:
                all_warnings.extend(ev.warnings)

    bundle_id = "teb_" + hashlib.sha256(
        f"{agent_id}:{lifecycle_state or ''}".encode()
    ).hexdigest()[:20]

    return TrustEvidenceBundle(
        bundle_id=bundle_id,
        agent_id=agent_id,
        lifecycle_state=lifecycle_state,
        trust_posture=posture,
        evidence_refs=evidence_refs,
        requirements=requirements,
        links=tuple(links),
        missing_required_evidence=tuple(missing),
        conflicted_evidence=tuple(conflicted),
        stale_evidence=tuple(stale),
        expired_evidence=tuple(expired),
        revoked_evidence=tuple(revoked),
        invalid_evidence=tuple(invalid),
        blockers=tuple(blockers),
        warnings=tuple(all_warnings),
        summary=f"Trust posture: {posture.value} for {agent_id} ({lifecycle_state or 'unknown'})",
    )


# ---------------------------------------------------------------------------
# Bundle validator
# ---------------------------------------------------------------------------


def validate_trust_evidence_bundle(
    bundle: TrustEvidenceBundle,
) -> TrustEvidenceLinkageReport:
    """Validate a trust evidence bundle. Does NOT mutate lifecycle or consent."""
    report_id = "telr_" + hashlib.sha256(
        f"{bundle.bundle_id}:{bundle.agent_id}".encode()
    ).hexdigest()[:20]

    total = len(bundle.evidence_refs)
    required_count = sum(1 for r in bundle.requirements if r.required)
    satisfied_count = sum(1 for link in bundle.links if link.required and link.satisfied)

    return TrustEvidenceLinkageReport(
        report_id=report_id,
        agent_id=bundle.agent_id,
        posture=bundle.trust_posture,
        bundle_id=bundle.bundle_id,
        total_evidence=total,
        required_evidence=required_count,
        satisfied_required_evidence=satisfied_count,
        missing_required_evidence=bundle.missing_required_evidence,
        conflicted_evidence=bundle.conflicted_evidence,
        stale_evidence=bundle.stale_evidence,
        expired_evidence=bundle.expired_evidence,
        revoked_evidence=bundle.revoked_evidence,
        invalid_evidence=bundle.invalid_evidence,
        blockers=bundle.blockers,
        warnings=bundle.warnings,
        summary=f"Trust posture: {bundle.trust_posture.value}. "
                f"Required: {satisfied_count}/{required_count} satisfied. "
                f"Total evidence: {total}.",
    )


# ---------------------------------------------------------------------------
# Evidence ref helper builders
# ---------------------------------------------------------------------------


def evidence_ref_from_source_attestation(
    *,
    evidence_id: str,
    ref: str,
    status: TrustEvidenceStatus = TrustEvidenceStatus.PRESENT,
    summary: str = "",
    source_attestation_id: str | None = None,
) -> TrustEvidenceRef:
    return TrustEvidenceRef(
        evidence_id=evidence_id,
        kind=TrustEvidenceKind.SOURCE_ATTESTATION,
        ref=ref,
        status=status,
        produced_by_module="source_attestation",
        source_attestation_id=source_attestation_id,
        summary=summary,
    )


def evidence_ref_from_test_battery_report(
    *,
    evidence_id: str,
    ref: str,
    status: TrustEvidenceStatus = TrustEvidenceStatus.PRESENT,
    summary: str = "",
) -> TrustEvidenceRef:
    return TrustEvidenceRef(
        evidence_id=evidence_id,
        kind=TrustEvidenceKind.IDENTITY_TEST_BATTERY_REPORT,
        ref=ref,
        status=status,
        produced_by_module="identity_test_battery",
        summary=summary,
    )


def evidence_ref_from_consent_record(
    *,
    evidence_id: str,
    ref: str,
    status: TrustEvidenceStatus = TrustEvidenceStatus.PRESENT,
    summary: str = "",
) -> TrustEvidenceRef:
    return TrustEvidenceRef(
        evidence_id=evidence_id,
        kind=TrustEvidenceKind.OPERATOR_CONSENT_RECORD,
        ref=ref,
        status=status,
        produced_by_module="operator_consent",
        summary=summary,
    )


def evidence_ref_from_authority_delta_report(
    *,
    evidence_id: str,
    ref: str,
    status: TrustEvidenceStatus = TrustEvidenceStatus.PRESENT,
    summary: str = "",
) -> TrustEvidenceRef:
    return TrustEvidenceRef(
        evidence_id=evidence_id,
        kind=TrustEvidenceKind.AUTHORITY_DELTA_REPORT,
        ref=ref,
        status=status,
        produced_by_module="authority_delta",
        summary=summary,
    )


def evidence_ref_from_lifecycle_decision(
    *,
    evidence_id: str,
    ref: str,
    status: TrustEvidenceStatus = TrustEvidenceStatus.PRESENT,
    summary: str = "",
) -> TrustEvidenceRef:
    return TrustEvidenceRef(
        evidence_id=evidence_id,
        kind=TrustEvidenceKind.LIFECYCLE_TRANSITION_DECISION,
        ref=ref,
        status=status,
        produced_by_module="agent_lifecycle",
        summary=summary,
    )


# ---------------------------------------------------------------------------
# Serialization helpers
# ---------------------------------------------------------------------------


def _enum_val(v: object) -> str:
    if isinstance(v, Enum):
        return v.value
    return str(v)


def trust_evidence_ref_to_dict(ref: TrustEvidenceRef) -> dict[str, object]:
    return {
        "evidence_id": ref.evidence_id,
        "kind": ref.kind.value,
        "ref": ref.ref,
        "title": ref.title,
        "status": ref.status.value,
        "produced_by_module": ref.produced_by_module,
        "created_at": ref.created_at,
        "expires_at": ref.expires_at,
        "hash_ref": ref.hash_ref,
        "source_attestation_id": ref.source_attestation_id,
        "summary": ref.summary,
        "warnings": list(ref.warnings),
        "blockers": list(ref.blockers),
    }


def trust_evidence_requirement_to_dict(req: TrustEvidenceRequirement) -> dict[str, object]:
    return {
        "requirement_id": req.requirement_id,
        "kind": req.kind.value,
        "required_for": req.required_for,
        "required": req.required,
        "acceptable_statuses": [s.value for s in req.acceptable_statuses],
        "reason": req.reason,
    }


def trust_evidence_link_to_dict(link: TrustEvidenceLink) -> dict[str, object]:
    return {
        "link_id": link.link_id,
        "subject_id": link.subject_id,
        "subject_type": link.subject_type,
        "evidence_id": link.evidence_id,
        "relationship": link.relationship,
        "required": link.required,
        "satisfied": link.satisfied,
        "reason": link.reason,
    }


def trust_evidence_bundle_to_dict(bundle: TrustEvidenceBundle) -> dict[str, object]:
    return {
        "bundle_id": bundle.bundle_id,
        "agent_id": bundle.agent_id,
        "lifecycle_state": bundle.lifecycle_state,
        "trust_posture": bundle.trust_posture.value,
        "evidence_refs": [trust_evidence_ref_to_dict(r) for r in bundle.evidence_refs],
        "requirements": [trust_evidence_requirement_to_dict(r) for r in bundle.requirements],
        "links": [trust_evidence_link_to_dict(lnk) for lnk in bundle.links],
        "missing_required_evidence": list(bundle.missing_required_evidence),
        "conflicted_evidence": list(bundle.conflicted_evidence),
        "stale_evidence": list(bundle.stale_evidence),
        "expired_evidence": list(bundle.expired_evidence),
        "revoked_evidence": list(bundle.revoked_evidence),
        "invalid_evidence": list(bundle.invalid_evidence),
        "blockers": list(bundle.blockers),
        "warnings": list(bundle.warnings),
        "summary": bundle.summary,
    }


def trust_evidence_linkage_report_to_dict(report: TrustEvidenceLinkageReport) -> dict[str, object]:
    return {
        "report_id": report.report_id,
        "agent_id": report.agent_id,
        "posture": report.posture.value,
        "bundle_id": report.bundle_id,
        "total_evidence": report.total_evidence,
        "required_evidence": report.required_evidence,
        "satisfied_required_evidence": report.satisfied_required_evidence,
        "missing_required_evidence": list(report.missing_required_evidence),
        "conflicted_evidence": list(report.conflicted_evidence),
        "stale_evidence": list(report.stale_evidence),
        "expired_evidence": list(report.expired_evidence),
        "revoked_evidence": list(report.revoked_evidence),
        "invalid_evidence": list(report.invalid_evidence),
        "blockers": list(report.blockers),
        "warnings": list(report.warnings),
        "summary": report.summary,
    }


# ---------------------------------------------------------------------------
# Human-readable formatters
# ---------------------------------------------------------------------------


def format_trust_evidence_bundle_human(bundle: TrustEvidenceBundle) -> str:
    lines = [
        f"Trust Evidence Bundle: {bundle.bundle_id}",
        f"  Agent: {bundle.agent_id}",
        f"  Lifecycle: {bundle.lifecycle_state or 'unknown'}",
        f"  Trust posture: {bundle.trust_posture.value}",
        "",
        f"  Evidence refs: {len(bundle.evidence_refs)}",
        f"  Requirements: {len(bundle.requirements)}",
        f"  Links: {len(bundle.links)}",
    ]
    if bundle.missing_required_evidence:
        lines.append("")
        lines.append("  Missing required evidence:")
        for e in bundle.missing_required_evidence:
            lines.append(f"    - {e}")
    if bundle.expired_evidence:
        lines.append("")
        lines.append("  Expired evidence:")
        for e in bundle.expired_evidence:
            lines.append(f"    - {e}")
    if bundle.revoked_evidence:
        lines.append("")
        lines.append("  Revoked evidence:")
        for e in bundle.revoked_evidence:
            lines.append(f"    - {e}")
    if bundle.conflicted_evidence:
        lines.append("")
        lines.append("  Conflicted evidence:")
        for e in bundle.conflicted_evidence:
            lines.append(f"    - {e}")
    if bundle.blockers:
        lines.append("")
        lines.append("  Blockers:")
        for b in bundle.blockers:
            lines.append(f"    - {b}")
    lines.append("")
    lines.append(f"  Summary: {bundle.summary}")
    return "\n".join(lines)


def format_trust_evidence_report_human(report: TrustEvidenceLinkageReport) -> str:
    lines = [
        f"Trust Evidence Linkage Report: {report.report_id}",
        f"  Agent: {report.agent_id}",
        f"  Posture: {report.posture.value}",
        f"  Required evidence: {report.satisfied_required_evidence}/{report.required_evidence}",
        f"  Total evidence: {report.total_evidence}",
    ]
    if report.missing_required_evidence:
        lines.append("  Missing:")
        for e in report.missing_required_evidence:
            lines.append(f"    - {e}")
    if report.blockers:
        lines.append("  Blockers:")
        for b in report.blockers:
            lines.append(f"    - {b}")
    lines.append(f"  {report.summary}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

__all__ = [
    "TrustEvidenceKind",
    "TrustEvidenceStatus",
    "TrustPosture",
    "TrustEvidenceRef",
    "TrustEvidenceRequirement",
    "TrustEvidenceLink",
    "TrustEvidenceBundle",
    "TrustEvidenceLinkageReport",
    "default_trust_evidence_requirements_for_lifecycle",
    "build_trust_evidence_bundle",
    "validate_trust_evidence_bundle",
    "resolve_trust_posture",
    "evidence_ref_from_source_attestation",
    "evidence_ref_from_test_battery_report",
    "evidence_ref_from_consent_record",
    "evidence_ref_from_authority_delta_report",
    "evidence_ref_from_lifecycle_decision",
    "trust_evidence_ref_to_dict",
    "trust_evidence_requirement_to_dict",
    "trust_evidence_link_to_dict",
    "trust_evidence_bundle_to_dict",
    "trust_evidence_linkage_report_to_dict",
    "format_trust_evidence_bundle_human",
    "format_trust_evidence_report_human",
]
