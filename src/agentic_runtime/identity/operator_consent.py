"""P1.4.14 Operator Consent Binding.

Binds Operator consent to exact authority deltas detected by P1.4.13.
Consent is bound to specific delta IDs and attestation pairs — it is NOT
global, NOT permanent by default, NOT transferable, and NOT capability
verification.

P1.4.14 binds consent. It does not execute changes, grant capabilities,
or create global/permanent consent.
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


class OperatorConsentStatus(str, Enum):
    REQUESTED = "REQUESTED"
    GRANTED = "GRANTED"
    DENIED = "DENIED"
    REVOKED = "REVOKED"
    EXPIRED = "EXPIRED"
    SUPERSEDED = "SUPERSEDED"


class OperatorConsentScope(str, Enum):
    SINGLE_DELTA = "SINGLE_DELTA"
    DELTA_REPORT = "DELTA_REPORT"
    SOURCE_UPDATE = "SOURCE_UPDATE"
    SESSION_LIMITED = "SESSION_LIMITED"


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class OperatorConsentRequest:
    request_id: str
    source_kind: str

    delta_ids: tuple[str, ...]
    highest_severity: str

    old_attestation_id: str | None
    new_attestation_id: str | None

    summary: str
    risk_summary: str
    requested_scope: OperatorConsentScope

    requires_explicit_risk_acknowledgement: bool
    created_at: str
    expires_at: str | None = None

    evidence_refs: tuple[str, ...] = ()


@dataclass(frozen=True)
class OperatorConsentRecord:
    consent_id: str
    request_id: str

    status: OperatorConsentStatus
    scope: OperatorConsentScope

    operator_id: str
    operator_display_name: str | None

    source_kind: str
    delta_ids: tuple[str, ...]

    old_attestation_id: str | None
    new_attestation_id: str | None

    highest_severity: str
    risk_acknowledged: bool

    granted_at: str | None = None
    denied_at: str | None = None
    revoked_at: str | None = None
    expires_at: str | None = None

    reason: str | None = None
    evidence_refs: tuple[str, ...] = ()


@dataclass(frozen=True)
class ConsentBindingValidation:
    valid: bool
    consent_id: str | None = None
    status: OperatorConsentStatus | None = None

    covered_delta_ids: tuple[str, ...] = ()
    missing_delta_ids: tuple[str, ...] = ()

    blockers: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    reason: str = ""


@dataclass(frozen=True)
class OperatorConsentDecision:
    request_id: str
    consent_id: str | None = None

    granted: bool = False
    status: OperatorConsentStatus = OperatorConsentStatus.REQUESTED

    reason: str = ""
    blockers: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()


# ---------------------------------------------------------------------------
# Helper: consent / request ID generation
# ---------------------------------------------------------------------------


def _consent_request_id(
    source_kind: str,
    delta_ids: tuple[str, ...],
    old_att_id: str | None,
    new_att_id: str | None,
) -> str:
    seed = json.dumps(
        {
            "source_kind": source_kind,
            "delta_ids": sorted(delta_ids),
            "old_attestation_id": old_att_id,
            "new_attestation_id": new_att_id,
        },
        sort_keys=True,
    )
    return "cnsr_" + hashlib.sha256(seed.encode("utf-8")).hexdigest()[:24]


def _consent_record_id(request_id: str, operator_id: str) -> str:
    seed = f"{request_id}:{operator_id}"
    return "cnsc_" + hashlib.sha256(seed.encode("utf-8")).hexdigest()[:24]


# ---------------------------------------------------------------------------
# Serialization
# ---------------------------------------------------------------------------


def operator_consent_request_to_dict(request: OperatorConsentRequest) -> dict[str, object]:
    return {
        "request_id": request.request_id,
        "source_kind": request.source_kind,
        "delta_ids": list(request.delta_ids),
        "highest_severity": request.highest_severity,
        "old_attestation_id": request.old_attestation_id,
        "new_attestation_id": request.new_attestation_id,
        "summary": request.summary,
        "risk_summary": request.risk_summary,
        "requested_scope": request.requested_scope.value,
        "requires_explicit_risk_acknowledgement": request.requires_explicit_risk_acknowledgement,
        "created_at": request.created_at,
        "expires_at": request.expires_at,
        "evidence_refs": list(request.evidence_refs),
    }


def operator_consent_record_to_dict(record: OperatorConsentRecord) -> dict[str, object]:
    return {
        "consent_id": record.consent_id,
        "request_id": record.request_id,
        "status": record.status.value,
        "scope": record.scope.value,
        "operator_id": record.operator_id,
        "operator_display_name": record.operator_display_name,
        "source_kind": record.source_kind,
        "delta_ids": list(record.delta_ids),
        "old_attestation_id": record.old_attestation_id,
        "new_attestation_id": record.new_attestation_id,
        "highest_severity": record.highest_severity,
        "risk_acknowledged": record.risk_acknowledged,
        "granted_at": record.granted_at,
        "denied_at": record.denied_at,
        "revoked_at": record.revoked_at,
        "expires_at": record.expires_at,
        "reason": record.reason,
        "evidence_refs": list(record.evidence_refs),
    }


def consent_binding_validation_to_dict(validation: ConsentBindingValidation) -> dict[str, object]:
    return {
        "valid": validation.valid,
        "consent_id": validation.consent_id,
        "status": validation.status.value if validation.status else None,
        "covered_delta_ids": list(validation.covered_delta_ids),
        "missing_delta_ids": list(validation.missing_delta_ids),
        "blockers": list(validation.blockers),
        "warnings": list(validation.warnings),
        "reason": validation.reason,
    }


def operator_consent_decision_to_dict(decision: OperatorConsentDecision) -> dict[str, object]:
    return {
        "request_id": decision.request_id,
        "consent_id": decision.consent_id,
        "granted": decision.granted,
        "status": decision.status.value,
        "reason": decision.reason,
        "blockers": list(decision.blockers),
        "warnings": list(decision.warnings),
    }


# ---------------------------------------------------------------------------
# Build consent request from AuthorityDeltaReport
# ---------------------------------------------------------------------------


def build_operator_consent_request(
    report,  # AuthorityDeltaReport
    *,
    requested_scope: OperatorConsentScope = OperatorConsentScope.DELTA_REPORT,
    expires_at: str | None = None,
) -> OperatorConsentRequest:
    """Build a consent request from an AuthorityDeltaReport.

    Only consent-required deltas are included by default.
    """
    # Determine which deltas require consent
    consent_deltas = [d for d in report.deltas if getattr(d, "requires_operator_consent", False)]
    delta_ids: tuple[str, ...] = tuple(d.delta_id for d in consent_deltas)

    highest_sev = report.highest_severity.value if hasattr(report.highest_severity, "value") else str(report.highest_severity)
    is_high_critical = highest_sev in {"HIGH", "CRITICAL"}

    old_att_id = getattr(report, "old_attestation_id", None)
    new_att_id = getattr(report, "new_attestation_id", None)

    # Build human-readable summary
    if consent_deltas:
        summary_lines = [
            f"Authority Delta Report for {report.source_kind}:",
            f"  {len(consent_deltas)} delta(s) requiring operator consent",
            f"  Highest severity: {highest_sev}",
            "",
            "Deltas:",
        ]
        for d in consent_deltas:
            d_type = d.delta_type.value if hasattr(d.delta_type, "value") else str(d.delta_type)
            d_sev = d.severity.value if hasattr(d.severity, "value") else str(d.severity)
            old_v = _safe_repr(getattr(d, "old_value", None))
            new_v = _safe_repr(getattr(d, "new_value", None))
            summary_lines.append(
                f"  [{d_sev}] {d_type}: {d.field_path} ({old_v} -> {new_v})"
            )
    else:
        summary_lines = [
            f"Authority Delta Report for {report.source_kind}:",
            "  No deltas requiring operator consent detected.",
            f"  Highest severity: {highest_sev}",
        ]

    summary = "\n".join(summary_lines)

    # Build risk summary
    if is_high_critical and consent_deltas:
        risk_lines = [
            "HIGH/CRITICAL authority delta(s) detected. Explicit risk acknowledgement required.",
            "The following deltas expand authority or increase risk:",
        ]
        for d in consent_deltas:
            if hasattr(d, "severity") and d.severity.value if hasattr(d.severity, "value") else False:
                d_type = d.delta_type.value if hasattr(d.delta_type, "value") else str(d.delta_type)
                d_sev = d.severity.value if hasattr(d.severity, "value") else str(d.severity)
                if d_sev in {"HIGH", "CRITICAL"}:
                    risk_lines.append(f"  - [{d_sev}] {d_type}: {d.field_path}")
        risk_summary = "\n".join(risk_lines)
    else:
        risk_summary = "No HIGH/CRITICAL risk changes detected."

    request_id = _consent_request_id(report.source_kind, delta_ids, old_att_id, new_att_id)
    return OperatorConsentRequest(
        request_id=request_id,
        source_kind=report.source_kind,
        delta_ids=delta_ids,
        highest_severity=highest_sev,
        old_attestation_id=old_att_id,
        new_attestation_id=new_att_id,
        summary=summary,
        risk_summary=risk_summary,
        requested_scope=requested_scope,
        requires_explicit_risk_acknowledgement=is_high_critical,
        created_at=datetime.now(timezone.utc).isoformat(),
        expires_at=expires_at,
        evidence_refs=(),
    )


def _safe_repr(value: object) -> str:
    if value is None:
        return "None"
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, (list, tuple)):
        return "[" + ", ".join(_safe_repr(v) for v in value) + "]"
    if isinstance(value, str) and len(str(value)) > 60:
        return str(value)[:57] + "..."
    return str(value)[:80]


# ---------------------------------------------------------------------------
# Grant consent
# ---------------------------------------------------------------------------


def grant_operator_consent(
    request: OperatorConsentRequest,
    *,
    operator_id: str,
    operator_display_name: str | None = None,
    risk_acknowledged: bool = False,
    reason: str | None = None,
) -> OperatorConsentRecord:
    """Grant operator consent for a consent request.

    Fails closed: raises ValueError if preconditions are not met.
    """
    blockers: list[str] = []

    if not operator_id or not operator_id.strip():
        blockers.append("operator_id_required")
    if not request.delta_ids:
        blockers.append("no_consent_required_deltas")
    if not request.summary or not request.summary.strip():
        blockers.append("summary_required")
    if request.requires_explicit_risk_acknowledgement and not risk_acknowledged:
        blockers.append("risk_acknowledgement_required")
    if request.highest_severity in {"HIGH", "CRITICAL"} and not risk_acknowledged:
        blockers.append("risk_acknowledgement_required")

    if blockers:
        raise ConsentValidationError("cannot grant consent", blockers=tuple(blockers))

    consent_id = _consent_record_id(request.request_id, operator_id.strip())
    return OperatorConsentRecord(
        consent_id=consent_id,
        request_id=request.request_id,
        status=OperatorConsentStatus.GRANTED,
        scope=request.requested_scope,
        operator_id=operator_id.strip(),
        operator_display_name=operator_display_name,
        source_kind=request.source_kind,
        delta_ids=request.delta_ids,
        old_attestation_id=request.old_attestation_id,
        new_attestation_id=request.new_attestation_id,
        highest_severity=request.highest_severity,
        risk_acknowledged=risk_acknowledged,
        granted_at=datetime.now(timezone.utc).isoformat(),
        expires_at=request.expires_at,
        reason=reason,
        evidence_refs=request.evidence_refs,
    )


# ---------------------------------------------------------------------------
# Deny consent
# ---------------------------------------------------------------------------


def deny_operator_consent(
    request: OperatorConsentRequest,
    *,
    operator_id: str,
    operator_display_name: str | None = None,
    reason: str | None = None,
) -> OperatorConsentRecord:
    """Deny a consent request."""
    if not operator_id or not operator_id.strip():
        raise ConsentValidationError("operator_id required to deny consent")

    consent_id = _consent_record_id(request.request_id, operator_id.strip())
    return OperatorConsentRecord(
        consent_id=consent_id,
        request_id=request.request_id,
        status=OperatorConsentStatus.DENIED,
        scope=request.requested_scope,
        operator_id=operator_id.strip(),
        operator_display_name=operator_display_name,
        source_kind=request.source_kind,
        delta_ids=request.delta_ids,
        old_attestation_id=request.old_attestation_id,
        new_attestation_id=request.new_attestation_id,
        highest_severity=request.highest_severity,
        risk_acknowledged=False,
        denied_at=datetime.now(timezone.utc).isoformat(),
        reason=reason,
    )


# ---------------------------------------------------------------------------
# Revoke consent
# ---------------------------------------------------------------------------


def revoke_operator_consent(
    record: OperatorConsentRecord,
    *,
    operator_id: str,
    reason: str | None = None,
) -> OperatorConsentRecord:
    """Revoke a previously granted consent record.

    Only GRANTED consent can be revoked.
    """
    if record.status != OperatorConsentStatus.GRANTED:
        raise ConsentValidationError(
            f"cannot revoke consent with status {record.status.value}",
            blockers=("consent_not_granted",),
        )
    if not operator_id or not operator_id.strip():
        raise ConsentValidationError("operator_id required to revoke consent")

    return OperatorConsentRecord(
        consent_id=record.consent_id,
        request_id=record.request_id,
        status=OperatorConsentStatus.REVOKED,
        scope=record.scope,
        operator_id=operator_id.strip(),
        operator_display_name=record.operator_display_name,
        source_kind=record.source_kind,
        delta_ids=record.delta_ids,
        old_attestation_id=record.old_attestation_id,
        new_attestation_id=record.new_attestation_id,
        highest_severity=record.highest_severity,
        risk_acknowledged=record.risk_acknowledged,
        granted_at=record.granted_at,
        revoked_at=datetime.now(timezone.utc).isoformat(),
        reason=reason,
        evidence_refs=record.evidence_refs,
    )


# ---------------------------------------------------------------------------
# Validate consent binding against a delta report
# ---------------------------------------------------------------------------


def validate_operator_consent_binding(
    record: OperatorConsentRecord,
    report,  # AuthorityDeltaReport
    *,
    now: str | None = None,
) -> ConsentBindingValidation:
    """Validate whether a consent record covers a given authority delta report."""
    blockers: list[str] = []
    warnings: list[str] = []
    reason_parts: list[str] = []

    current_time = now or datetime.now(timezone.utc).isoformat()

    # 1. Status must be GRANTED
    if record.status != OperatorConsentStatus.GRANTED:
        if record.status == OperatorConsentStatus.REVOKED:
            blockers.append("consent_revoked")
            reason_parts.append("consent has been revoked")
        elif record.status == OperatorConsentStatus.DENIED:
            blockers.append("consent_denied")
            reason_parts.append("consent was denied")
        elif record.status == OperatorConsentStatus.EXPIRED:
            blockers.append("consent_expired")
            reason_parts.append("consent has expired")
        else:
            blockers.append("consent_not_granted")
            reason_parts.append(f"consent status is {record.status.value}")

    # 2. Expiry check
    if record.expires_at and record.expires_at < current_time:
        blockers.append("consent_expired")
        reason_parts.append(f"consent expired at {record.expires_at}")

    # 3. Source kind match
    report_source_kind = getattr(report, "source_kind", None)
    if report_source_kind and record.source_kind != report_source_kind:
        blockers.append("source_kind_mismatch")
        reason_parts.append(
            f"consent is for {record.source_kind}, report is for {report_source_kind}"
        )

    # 4. Attestation ID match
    old_att_id = getattr(report, "old_attestation_id", None)
    new_att_id = getattr(report, "new_attestation_id", None)
    if old_att_id is not None and record.old_attestation_id != old_att_id:
        blockers.append("old_attestation_mismatch")
        reason_parts.append(
            f"consent old_attestation_id {record.old_attestation_id} does not match report {old_att_id}"
        )
    if new_att_id is not None and record.new_attestation_id != new_att_id:
        blockers.append("new_attestation_mismatch")
        reason_parts.append(
            f"consent new_attestation_id {record.new_attestation_id} does not match report {new_att_id}"
        )

    # 5. Delta coverage
    report_deltas = getattr(report, "deltas", ())
    consent_required_ids = frozenset(
        d.delta_id for d in report_deltas if getattr(d, "requires_operator_consent", False)
    )
    record_delta_set = frozenset(record.delta_ids)

    covered = tuple(sorted(consent_required_ids & record_delta_set))
    missing = tuple(sorted(consent_required_ids - record_delta_set))

    if record.scope == OperatorConsentScope.SINGLE_DELTA:
        if len(record.delta_ids) != 1:
            blockers.append("scope_violation")
            reason_parts.append("SINGLE_DELTA scope requires exactly one delta_id")
        if missing:
            blockers.append("delta_not_covered")
            reason_parts.append(f"SINGLE_DELTA consent does not cover deltas: {missing}")
    elif record.scope == OperatorConsentScope.DELTA_REPORT:
        if missing:
            blockers.append("delta_not_covered")
            reason_parts.append(f"DELTA_REPORT consent does not cover deltas: {missing}")
    elif record.scope == OperatorConsentScope.SOURCE_UPDATE:
        if missing:
            blockers.append("delta_not_covered")
            reason_parts.append(f"SOURCE_UPDATE consent does not cover deltas: {missing}")
    elif record.scope == OperatorConsentScope.SESSION_LIMITED:
        blockers.append("scope_not_supported")
        reason_parts.append("SESSION_LIMITED scope not yet supported")
        warnings.append("SESSION_LIMITED scope is not implemented; treat as unsupported")

    # 6. Risk acknowledgement for HIGH/CRITICAL
    highest_sev = getattr(report, "highest_severity", None)
    if highest_sev is not None:
        hsv = highest_sev.value if hasattr(highest_sev, "value") else str(highest_sev)
    else:
        hsv = record.highest_severity
    if hsv in {"HIGH", "CRITICAL"} and not record.risk_acknowledged:
        blockers.append("risk_not_acknowledged")
        reason_parts.append("HIGH/CRITICAL severity consent requires explicit risk acknowledgement")

    valid = len(blockers) == 0
    reason = "; ".join(reason_parts) if reason_parts else "consent binding is valid"
    if not reason_parts:
        reason = "consent binding is valid"

    return ConsentBindingValidation(
        valid=valid,
        consent_id=record.consent_id,
        status=record.status,
        covered_delta_ids=covered,
        missing_delta_ids=missing,
        blockers=tuple(blockers),
        warnings=tuple(warnings),
        reason=reason,
    )


# ---------------------------------------------------------------------------
# Error
# ---------------------------------------------------------------------------


class ConsentValidationError(ValueError):
    """Raised when a consent operation fails precondition checks."""

    def __init__(self, message: str, blockers: tuple[str, ...] = ()) -> None:
        super().__init__(message)
        self.blockers = blockers


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


__all__ = [
    "OperatorConsentStatus",
    "OperatorConsentScope",
    "OperatorConsentRequest",
    "OperatorConsentRecord",
    "ConsentBindingValidation",
    "OperatorConsentDecision",
    "ConsentValidationError",
    "build_operator_consent_request",
    "grant_operator_consent",
    "deny_operator_consent",
    "revoke_operator_consent",
    "validate_operator_consent_binding",
    "operator_consent_request_to_dict",
    "operator_consent_record_to_dict",
    "consent_binding_validation_to_dict",
    "operator_consent_decision_to_dict",
]
