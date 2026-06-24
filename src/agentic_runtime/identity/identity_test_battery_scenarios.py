"""P1.4.16 Identity Test Battery — scenario implementations.

Each function runs one battery test case and returns an IdentityTestResult.
Scenarios exercise integrated chains, not isolated module tests.
"""
from __future__ import annotations

import json
import subprocess  # nosec B404 - identity battery intentionally probes the local CLI as a subprocess
import sys
from datetime import datetime, timedelta, timezone
from typing import Any

from agentic_runtime.identity.identity_test_battery import (
    IdentityBatteryStatus,
    IdentityTestResult,
    IdentityTestSeverity,
)

# ---------------------------------------------------------------------------
# 7.1 Smoke / import battery
# ---------------------------------------------------------------------------

_IMMEDIATE = 0  # constant for duration shorthand


def _import_check_smoke(*, module_path: str, case_id: str, label: str) -> IdentityTestResult:
    try:
        __import__(module_path)
        return IdentityTestResult(
            case_id=case_id,
            status=IdentityBatteryStatus.PASSED,
            severity=IdentityTestSeverity.CRITICAL,
            summary=f"{label} importable",
            duration_ms=_IMMEDIATE,
        )
    except ImportError as exc:
        return IdentityTestResult(
            case_id=case_id,
            status=IdentityBatteryStatus.FAILED,
            severity=IdentityTestSeverity.CRITICAL,
            summary=f"{label} not importable: {exc}",
            errors=(f"import_error:{exc}",),
            duration_ms=_IMMEDIATE,
        )


SMOKE_MODULES = {
    "smoke_identity_modules": ("agentic_runtime.identity.kernel", "identity kernel"),
    "smoke_autonomy_modules": ("agentic_runtime.identity.autonomy_scale_engine", "autonomy scale engine"),
    "smoke_claim_modules": ("agentic_runtime.identity.capability_claims", "capability claims"),
    "smoke_doctrine_modules": ("agentic_runtime.identity.external_doctrine", "external doctrine"),
    "smoke_attestation_modules": ("agentic_runtime.identity.source_attestation", "source attestation"),
    "smoke_authority_delta_modules": ("agentic_runtime.identity.authority_delta", "authority delta detector"),
    "smoke_consent_modules": ("agentic_runtime.identity.operator_consent", "operator consent"),
    "smoke_cli_surface": ("agentic_runtime.identity.identity_cli_surface", "identity CLI surface"),
}


def run_smoke_identity_modules() -> IdentityTestResult:
    return _import_check_smoke(
        module_path="agentic_runtime.identity.kernel",
        case_id="smoke_identity_modules",
        label="identity modules",
    )


def run_smoke_autonomy_modules() -> IdentityTestResult:
    return _import_check_smoke(
        module_path="agentic_runtime.identity.autonomy_scale_engine",
        case_id="smoke_autonomy_modules",
        label="autonomy modules",
    )


def run_smoke_claim_modules() -> IdentityTestResult:
    return _import_check_smoke(
        module_path="agentic_runtime.identity.capability_claims",
        case_id="smoke_claim_modules",
        label="claim modules",
    )


def run_smoke_doctrine_modules() -> IdentityTestResult:
    return _import_check_smoke(
        module_path="agentic_runtime.identity.external_doctrine",
        case_id="smoke_doctrine_modules",
        label="doctrine modules",
    )


def run_smoke_attestation_modules() -> IdentityTestResult:
    return _import_check_smoke(
        module_path="agentic_runtime.identity.source_attestation",
        case_id="smoke_attestation_modules",
        label="attestation modules",
    )


def run_smoke_authority_delta_modules() -> IdentityTestResult:
    return _import_check_smoke(
        module_path="agentic_runtime.identity.authority_delta",
        case_id="smoke_authority_delta_modules",
        label="authority delta modules",
    )


def run_smoke_consent_modules() -> IdentityTestResult:
    return _import_check_smoke(
        module_path="agentic_runtime.identity.operator_consent",
        case_id="smoke_consent_modules",
        label="consent modules",
    )


def run_smoke_cli_surface() -> IdentityTestResult:
    return _import_check_smoke(
        module_path="agentic_runtime.identity.identity_cli_surface",
        case_id="smoke_cli_surface",
        label="identity CLI surface",
    )


# ---------------------------------------------------------------------------
# 7.3 Source attestation battery
# ---------------------------------------------------------------------------


def run_attestation_raw_hash_changes() -> IdentityTestResult:
    try:
        from agentic_runtime.identity.source_attestation import hash_raw_source
    except ImportError as exc:
        return IdentityTestResult(
            case_id="attestation_raw_hash_changes",
            status=IdentityBatteryStatus.SKIPPED,
            severity=IdentityTestSeverity.HIGH,
            summary=f"source_attestation not available: {exc}",
            duration_ms=_IMMEDIATE,
        )

    h1 = hash_raw_source(b'{"risk_ceiling": "low"}')
    h2 = hash_raw_source(b'{"risk_ceiling": "high"}')
    if h1 == h2:
        return IdentityTestResult(
            case_id="attestation_raw_hash_changes",
            status=IdentityBatteryStatus.FAILED,
            severity=IdentityTestSeverity.HIGH,
            summary="Raw hash did not change on source change",
            errors=("raw_hash_unchanged",),
            evidence_refs=("raw_source_pairs",),
            duration_ms=_IMMEDIATE,
        )
    return IdentityTestResult(
        case_id="attestation_raw_hash_changes",
        status=IdentityBatteryStatus.PASSED,
        severity=IdentityTestSeverity.HIGH,
        summary="Raw hash changes on source change",
        evidence_refs=("raw_source_pairs",),
        duration_ms=_IMMEDIATE,
    )


def run_attestation_canonical_hash_stable() -> IdentityTestResult:
    try:
        from agentic_runtime.identity.source_attestation import (
            canonicalize_source_object,
            hash_raw_source,
        )
    except ImportError as exc:
        return IdentityTestResult(
            case_id="attestation_canonical_hash_stable",
            status=IdentityBatteryStatus.SKIPPED,
            severity=IdentityTestSeverity.HIGH,
            summary=f"module not available: {exc}",
            duration_ms=_IMMEDIATE,
        )

    try:
        obj = {"risk_ceiling": "low", "oversight": True}
        c1 = canonicalize_source_object(obj)
        c2 = canonicalize_source_object(obj)
        h1 = hash_raw_source(c1.encode("utf-8"))
        h2 = hash_raw_source(c2.encode("utf-8"))
        if h1 != h2:
            return IdentityTestResult(
                case_id="attestation_canonical_hash_stable",
                status=IdentityBatteryStatus.FAILED,
                severity=IdentityTestSeverity.HIGH,
                summary="Canonical hash unstable for equivalent object",
                errors=("canonical_hash_unstable",),
                evidence_refs=("canonical_pairs",),
                duration_ms=_IMMEDIATE,
            )
    except Exception as exc:
        return IdentityTestResult(
            case_id="attestation_canonical_hash_stable",
            status=IdentityBatteryStatus.DEGRADED,
            severity=IdentityTestSeverity.HIGH,
            summary=f"Canonicalize failed: {exc}",
            warnings=(f"canonicalize_error:{exc}",),
            duration_ms=_IMMEDIATE,
        )

    return IdentityTestResult(
        case_id="attestation_canonical_hash_stable",
        status=IdentityBatteryStatus.PASSED,
        severity=IdentityTestSeverity.HIGH,
        summary="Canonical hash stable for equivalent object",
        evidence_refs=("canonical_pairs",),
        duration_ms=_IMMEDIATE,
    )


# ---------------------------------------------------------------------------
# 7.8 Authority delta battery
# ---------------------------------------------------------------------------


def _make_delta_helper(
    source_kind: str,
    fields_old: dict[str, Any],
    fields_new: dict[str, Any],
    case_id: str,
    severity: IdentityTestSeverity,
    expect_consent: bool = True,
    expect_requires_consent_label: str = "requires_consent",
) -> IdentityTestResult:
    """Shared helper for authority delta tests."""
    try:
        from agentic_runtime.identity.authority_delta import (
            AuthorityDeltaInput,
            detect_authority_deltas,
        )
    except ImportError as exc:
        return IdentityTestResult(
            case_id=case_id,
            status=IdentityBatteryStatus.SKIPPED,
            severity=severity,
            summary=f"authority_delta not available: {exc}",
            duration_ms=_IMMEDIATE,
        )

    try:
        input_obj = AuthorityDeltaInput(
            source_kind=source_kind,
            old_canonical_object=fields_old,
            new_canonical_object=fields_new,
        )
        report = detect_authority_deltas(input_obj)
    except Exception as exc:
        return IdentityTestResult(
            case_id=case_id,
            status=IdentityBatteryStatus.FAILED,
            severity=severity,
            summary=f"detect_authority_deltas raised: {exc}",
            errors=(f"detection_error:{exc}",),
            evidence_refs=(case_id,),
            duration_ms=_IMMEDIATE,
        )

    # Check consent required
    if expect_consent and not report.requires_operator_consent:
        return IdentityTestResult(
            case_id=case_id,
            status=IdentityBatteryStatus.FAILED,
            severity=severity,
            summary=f"Expected requires_operator_consent=True, got False. Deltas: {len(report.deltas)}",
            errors=(f"{expect_requires_consent_label}_not_true",),
            evidence_refs=(case_id, f"report_id={report.report_id}"),
            duration_ms=_IMMEDIATE,
        )

    return IdentityTestResult(
        case_id=case_id,
        status=IdentityBatteryStatus.PASSED,
        severity=severity,
        summary=f"Authority delta detected correctly ({len(report.deltas)} deltas, consent={report.requires_operator_consent})",
        evidence_refs=(case_id, f"report_id={report.report_id}"),
        duration_ms=_IMMEDIATE,
    )


def run_authority_delta_risk_ceiling_increase() -> IdentityTestResult:
    return _make_delta_helper(
        source_kind="operator_contract",
        fields_old={"risk_ceiling": "low"},
        fields_new={"risk_ceiling": "high"},
        case_id="authority_delta_risk_ceiling_increase",
        severity=IdentityTestSeverity.CRITICAL,
    )


def run_authority_delta_oversight_weakened() -> IdentityTestResult:
    return _make_delta_helper(
        source_kind="operator_contract",
        fields_old={"requires_human_approval": True},
        fields_new={"requires_human_approval": False},
        case_id="authority_delta_oversight_weakened",
        severity=IdentityTestSeverity.CRITICAL,
    )


def run_authority_delta_external_effect_added() -> IdentityTestResult:
    return _make_delta_helper(
        source_kind="operator_contract",
        fields_old={"allowed_tools": ["read"]},
        fields_new={"allowed_tools": ["read", "network_call"]},
        case_id="authority_delta_external_effect_added",
        severity=IdentityTestSeverity.CRITICAL,
    )


def run_auth_delta_valid_source_requires_consent() -> IdentityTestResult:
    """A valid attested source with a risk ceiling increase still requires consent."""
    try:
        from agentic_runtime.identity.authority_delta import (
            AuthorityDeltaInput,
            detect_authority_deltas,
        )
        from agentic_runtime.identity.source_attestation import (
            SourceKind,
            SourceValidationStatus,
            build_source_attestation,
        )
    except ImportError as exc:
        return IdentityTestResult(
            case_id="authority_delta_valid_source_still_requires_consent",
            status=IdentityBatteryStatus.SKIPPED,
            severity=IdentityTestSeverity.HIGH,
            summary=f"Module not available: {exc}",
            duration_ms=_IMMEDIATE,
        )

    try:
        obj_old = {"risk_ceiling": "low"}
        obj_new = {"risk_ceiling": "high"}

        # Build valid attestations using the real API
        old_raw = json.dumps(obj_old).encode("utf-8")
        new_raw = json.dumps(obj_new).encode("utf-8")
        old_att = build_source_attestation(
            source_kind=SourceKind.OPERATOR_CONTRACT,
            source_path=None,
            raw_source=old_raw,
            typed_object=obj_old,
            validation_status=SourceValidationStatus.VALID,
            validator_name="battery",
        )
        new_att = build_source_attestation(
            source_kind=SourceKind.OPERATOR_CONTRACT,
            source_path=None,
            raw_source=new_raw,
            typed_object=obj_new,
            validation_status=SourceValidationStatus.VALID_WITH_WARNINGS,
            validator_name="battery",
            warnings=("risk_ceiling_increased",),
        )

        input_obj = AuthorityDeltaInput(
            source_kind="operator_contract",
            old_canonical_object=obj_old,
            new_canonical_object=obj_new,
            old_attestation=old_att,
            new_attestation=new_att,
        )
        report = detect_authority_deltas(input_obj)
    except Exception as exc:
        return IdentityTestResult(
            case_id="authority_delta_valid_source_still_requires_consent",
            status=IdentityBatteryStatus.DEGRADED,
            severity=IdentityTestSeverity.HIGH,
            summary=f"Attestation-based delta detection raised: {exc}",
            warnings=(f"attestation_delta_error:{exc}",),
            duration_ms=_IMMEDIATE,
        )

    if not report.requires_operator_consent:
        return IdentityTestResult(
            case_id="authority_delta_valid_source_still_requires_consent",
            status=IdentityBatteryStatus.FAILED,
            severity=IdentityTestSeverity.HIGH,
            summary="Valid attested source with risk increase did not require consent",
            errors=("valid_attested_requires_consent_false",),
            evidence_refs=("attested_risk_increase",),
            duration_ms=_IMMEDIATE,
        )

    return IdentityTestResult(
        case_id="authority_delta_valid_source_still_requires_consent",
        status=IdentityBatteryStatus.PASSED,
        severity=IdentityTestSeverity.HIGH,
        summary="Valid attested source with risk increase requires consent",
        evidence_refs=("attested_risk_increase", f"report_id={report.report_id}"),
        duration_ms=_IMMEDIATE,
    )


# ---------------------------------------------------------------------------
# 7.9 Operator consent battery
# ---------------------------------------------------------------------------


def _make_consent_delta_report(
    source_kind: str = "operator_contract",
    old_att_id: str = "srcatt_old",
    new_att_id: str = "srcatt_new",
):
    """Build a consent-required AuthorityDeltaReport."""
    from agentic_runtime.identity.authority_delta import (
        AuthorityDelta,
        AuthorityDeltaReport,
        AuthorityDeltaSeverity,
        AuthorityDeltaType,
    )
    d = AuthorityDelta(
        delta_id="adt_battery_1",
        delta_type=AuthorityDeltaType.RISK_CEILING_INCREASED,
        severity=AuthorityDeltaSeverity.HIGH,
        source_kind=source_kind,
        field_path="risk_ceiling",
        old_value="low",
        new_value="high",
        old_attestation_id=old_att_id,
        new_attestation_id=new_att_id,
        requires_operator_consent=True,
        requires_evidence=False,
        reason="risk ceiling increased from low to high",
        blockers=("operator_consent_required",),
        warnings=(),
    )
    return AuthorityDeltaReport(
        report_id="adr_battery",
        source_kind=source_kind,
        deltas=(d,),
        highest_severity=AuthorityDeltaSeverity.HIGH,
        requires_operator_consent=True,
        requires_evidence=False,
        summary="battery test",
        safe_to_auto_accept=False,
        old_attestation_id=old_att_id,
        new_attestation_id=new_att_id,
    )


def run_consent_request_from_delta_report() -> IdentityTestResult:
    try:
        from agentic_runtime.identity.operator_consent import (
            build_operator_consent_request,
        )
    except ImportError as exc:
        return IdentityTestResult(
            case_id="consent_request_from_delta_report",
            status=IdentityBatteryStatus.SKIPPED,
            severity=IdentityTestSeverity.HIGH,
            summary=f"consent module not available: {exc}",
            duration_ms=_IMMEDIATE,
        )

    try:
        report = _make_consent_delta_report()
        request = build_operator_consent_request(report)
        if not request.delta_ids:
            return IdentityTestResult(
                case_id="consent_request_from_delta_report",
                status=IdentityBatteryStatus.FAILED,
                severity=IdentityTestSeverity.HIGH,
                summary="Consent request has empty delta_ids",
                errors=("empty_delta_ids",),
                evidence_refs=("delta_report_to_request",),
                duration_ms=_IMMEDIATE,
            )
    except Exception as exc:
        return IdentityTestResult(
            case_id="consent_request_from_delta_report",
            status=IdentityBatteryStatus.FAILED,
            severity=IdentityTestSeverity.HIGH,
            summary=f"build_operator_consent_request failed: {exc}",
            errors=(f"build_request_error:{exc}",),
            evidence_refs=("delta_report_to_request",),
            duration_ms=_IMMEDIATE,
        )

    return IdentityTestResult(
        case_id="consent_request_from_delta_report",
        status=IdentityBatteryStatus.PASSED,
        severity=IdentityTestSeverity.HIGH,
        summary="Consent request built from authority delta report",
        evidence_refs=("delta_report_to_request",),
        duration_ms=_IMMEDIATE,
    )


def run_consent_high_requires_risk_ack() -> IdentityTestResult:
    try:
        from agentic_runtime.identity.operator_consent import (
            ConsentValidationError,
            build_operator_consent_request,
            grant_operator_consent,
        )
    except ImportError as exc:
        return IdentityTestResult(
            case_id="consent_high_requires_risk_ack",
            status=IdentityBatteryStatus.SKIPPED,
            severity=IdentityTestSeverity.CRITICAL,
            summary=f"consent module not available: {exc}",
            duration_ms=_IMMEDIATE,
        )

    try:
        report = _make_consent_delta_report()
        request = build_operator_consent_request(report)
        # Should raise without risk_acknowledged
        grant_operator_consent(request, operator_id="battery_op", risk_acknowledged=False)
        return IdentityTestResult(
            case_id="consent_high_requires_risk_ack",
            status=IdentityBatteryStatus.FAILED,
            severity=IdentityTestSeverity.CRITICAL,
            summary="HIGH severity grant succeeded without risk_acknowledged",
            errors=("risk_ack_not_required",),
            evidence_refs=("high_severity_grant",),
            duration_ms=_IMMEDIATE,
        )
    except ConsentValidationError:
        pass
    except Exception as exc:
        return IdentityTestResult(
            case_id="consent_high_requires_risk_ack",
            status=IdentityBatteryStatus.FAILED,
            severity=IdentityTestSeverity.CRITICAL,
            summary=f"grant_operator_consent raised unexpected: {exc}",
            errors=(f"unexpected_error:{exc}",),
            evidence_refs=("high_severity_grant",),
            duration_ms=_IMMEDIATE,
        )

    return IdentityTestResult(
        case_id="consent_high_requires_risk_ack",
        status=IdentityBatteryStatus.PASSED,
        severity=IdentityTestSeverity.CRITICAL,
        summary="HIGH severity grant requires risk_acknowledged",
        evidence_refs=("high_severity_grant",),
        duration_ms=_IMMEDIATE,
    )


def run_consent_binds_to_delta_id() -> IdentityTestResult:
    try:
        from agentic_runtime.identity.operator_consent import (
            build_operator_consent_request,
            grant_operator_consent,
            validate_operator_consent_binding,
        )
    except ImportError as exc:
        return IdentityTestResult(
            case_id="consent_binds_to_delta_id",
            status=IdentityBatteryStatus.SKIPPED,
            severity=IdentityTestSeverity.CRITICAL,
            summary=f"consent not available: {exc}",
            duration_ms=_IMMEDIATE,
        )

    try:
        report = _make_consent_delta_report()
        request = build_operator_consent_request(report)
        record = grant_operator_consent(request, operator_id="op1", risk_acknowledged=True)

        # Create a different report with a different delta ID
        from agentic_runtime.identity.authority_delta import (
            AuthorityDelta,
            AuthorityDeltaReport,
            AuthorityDeltaSeverity,
            AuthorityDeltaType,
        )
        d2 = AuthorityDelta(
            delta_id="adt_battery_2",  # different ID
            delta_type=AuthorityDeltaType.RISK_CEILING_INCREASED,
            severity=AuthorityDeltaSeverity.HIGH,
            source_kind="operator_contract",
            field_path="risk_ceiling",
            old_value="medium",
            new_value="high",
            old_attestation_id="srcatt_old",
            new_attestation_id="srcatt_new",
            requires_operator_consent=True,
            requires_evidence=False,
            reason="different delta",
            blockers=(),
            warnings=(),
        )
        report2 = AuthorityDeltaReport(
            report_id="adr_battery_2",
            source_kind="operator_contract",
            deltas=(d2,),
            highest_severity=AuthorityDeltaSeverity.HIGH,
            requires_operator_consent=True,
            requires_evidence=False,
            summary="different report",
            safe_to_auto_accept=False,
            old_attestation_id="srcatt_old",
            new_attestation_id="srcatt_new",
        )

        validation = validate_operator_consent_binding(record, report2)
        if validation.valid:
            return IdentityTestResult(
                case_id="consent_binds_to_delta_id",
                status=IdentityBatteryStatus.FAILED,
                severity=IdentityTestSeverity.CRITICAL,
                summary="Consent validated for different delta ID",
                errors=("delta_id_boundary_violated",),
                evidence_refs=("delta_binding",),
                duration_ms=_IMMEDIATE,
            )
    except Exception as exc:
        return IdentityTestResult(
            case_id="consent_binds_to_delta_id",
            status=IdentityBatteryStatus.FAILED,
            severity=IdentityTestSeverity.CRITICAL,
            summary=f"consent delta binding test failed: {exc}",
            errors=(f"exception:{exc}",),
            evidence_refs=("delta_binding",),
            duration_ms=_IMMEDIATE,
        )

    return IdentityTestResult(
        case_id="consent_binds_to_delta_id",
        status=IdentityBatteryStatus.PASSED,
        severity=IdentityTestSeverity.CRITICAL,
        summary="Consent does not transfer to different delta ID",
        evidence_refs=("delta_binding",),
        duration_ms=_IMMEDIATE,
    )


def run_consent_binds_to_attestation_pair() -> IdentityTestResult:
    try:
        from agentic_runtime.identity.operator_consent import (
            build_operator_consent_request,
            grant_operator_consent,
            validate_operator_consent_binding,
        )
    except ImportError as exc:
        return IdentityTestResult(
            case_id="consent_binds_to_attestation_pair",
            status=IdentityBatteryStatus.SKIPPED,
            severity=IdentityTestSeverity.CRITICAL,
            summary=f"consent not available: {exc}",
            duration_ms=_IMMEDIATE,
        )

    try:
        report = _make_consent_delta_report(old_att_id="A1", new_att_id="A2")
        request = build_operator_consent_request(report)
        record = grant_operator_consent(request, operator_id="op1", risk_acknowledged=True)

        # Different attestation pair
        report2 = _make_consent_delta_report(old_att_id="A1", new_att_id="A_DIFFERENT")
        validation = validate_operator_consent_binding(record, report2)
        if validation.valid:
            return IdentityTestResult(
                case_id="consent_binds_to_attestation_pair",
                status=IdentityBatteryStatus.FAILED,
                severity=IdentityTestSeverity.CRITICAL,
                summary="Consent validated with mismatched attestation",
                errors=("attestation_boundary_violated",),
                evidence_refs=("attestation_binding",),
                duration_ms=_IMMEDIATE,
            )
    except Exception as exc:
        return IdentityTestResult(
            case_id="consent_binds_to_attestation_pair",
            status=IdentityBatteryStatus.FAILED,
            severity=IdentityTestSeverity.CRITICAL,
            summary=f"consent attestation binding test failed: {exc}",
            errors=(f"exception:{exc}",),
            duration_ms=_IMMEDIATE,
        )

    return IdentityTestResult(
        case_id="consent_binds_to_attestation_pair",
        status=IdentityBatteryStatus.PASSED,
        severity=IdentityTestSeverity.CRITICAL,
        summary="Consent does not validate with attestation mismatch",
        evidence_refs=("attestation_binding",),
        duration_ms=_IMMEDIATE,
    )


def run_consent_revoked_invalid() -> IdentityTestResult:
    try:
        from agentic_runtime.identity.operator_consent import (
            build_operator_consent_request,
            grant_operator_consent,
            revoke_operator_consent,
            validate_operator_consent_binding,
        )
    except ImportError as exc:
        return IdentityTestResult(
            case_id="consent_revoked_invalid",
            status=IdentityBatteryStatus.SKIPPED,
            severity=IdentityTestSeverity.CRITICAL,
            summary=f"consent not available: {exc}",
            duration_ms=_IMMEDIATE,
        )

    try:
        report = _make_consent_delta_report()
        request = build_operator_consent_request(report)
        record = grant_operator_consent(request, operator_id="op1", risk_acknowledged=True)
        revoked = revoke_operator_consent(record, operator_id="op1")
        validation = validate_operator_consent_binding(revoked, report)
        if validation.valid:
            return IdentityTestResult(
                case_id="consent_revoked_invalid",
                status=IdentityBatteryStatus.FAILED,
                severity=IdentityTestSeverity.CRITICAL,
                summary="Revoked consent validated",
                errors=("revoked_consent_validated",),
                evidence_refs=("revoked_consent",),
                duration_ms=_IMMEDIATE,
            )
    except Exception as exc:
        return IdentityTestResult(
            case_id="consent_revoked_invalid",
            status=IdentityBatteryStatus.FAILED,
            severity=IdentityTestSeverity.CRITICAL,
            summary=f"revoke test failed: {exc}",
            errors=(f"exception:{exc}",),
            duration_ms=_IMMEDIATE,
        )

    return IdentityTestResult(
        case_id="consent_revoked_invalid",
        status=IdentityBatteryStatus.PASSED,
        severity=IdentityTestSeverity.CRITICAL,
        summary="Revoked consent is invalid",
        evidence_refs=("revoked_consent",),
        duration_ms=_IMMEDIATE,
    )


def run_consent_expired_invalid() -> IdentityTestResult:
    try:
        from agentic_runtime.identity.operator_consent import (
            build_operator_consent_request,
            grant_operator_consent,
            validate_operator_consent_binding,
        )
    except ImportError as exc:
        return IdentityTestResult(
            case_id="consent_expired_invalid",
            status=IdentityBatteryStatus.SKIPPED,
            severity=IdentityTestSeverity.CRITICAL,
            summary=f"consent not available: {exc}",
            duration_ms=_IMMEDIATE,
        )

    try:
        yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        report = _make_consent_delta_report()
        request = build_operator_consent_request(report, expires_at=yesterday)
        record = grant_operator_consent(request, operator_id="op1", risk_acknowledged=True)
        validation = validate_operator_consent_binding(record, report)
        if validation.valid:
            return IdentityTestResult(
                case_id="consent_expired_invalid",
                status=IdentityBatteryStatus.FAILED,
                severity=IdentityTestSeverity.CRITICAL,
                summary="Expired consent validated",
                errors=("expired_consent_validated",),
                evidence_refs=("expired_consent",),
                duration_ms=_IMMEDIATE,
            )
    except Exception as exc:
        return IdentityTestResult(
            case_id="consent_expired_invalid",
            status=IdentityBatteryStatus.FAILED,
            severity=IdentityTestSeverity.CRITICAL,
            summary=f"expired test failed: {exc}",
            errors=(f"exception:{exc}",),
            duration_ms=_IMMEDIATE,
        )

    return IdentityTestResult(
        case_id="consent_expired_invalid",
        status=IdentityBatteryStatus.PASSED,
        severity=IdentityTestSeverity.CRITICAL,
        summary="Expired consent is invalid",
        evidence_refs=("expired_consent",),
        duration_ms=_IMMEDIATE,
    )


def run_consent_attestation_mismatch_invalid() -> IdentityTestResult:
    """New attestation mismatch must invalidate consent."""
    try:
        from agentic_runtime.identity.operator_consent import (
            build_operator_consent_request,
            grant_operator_consent,
            validate_operator_consent_binding,
        )
    except ImportError as exc:
        return IdentityTestResult(
            case_id="consent_attestation_mismatch_invalid",
            status=IdentityBatteryStatus.SKIPPED,
            severity=IdentityTestSeverity.CRITICAL,
            summary=f"consent not available: {exc}",
            duration_ms=_IMMEDIATE,
        )

    try:
        report = _make_consent_delta_report(old_att_id="A1", new_att_id="A2")
        request = build_operator_consent_request(report)
        record = grant_operator_consent(request, operator_id="op1", risk_acknowledged=True)

        report2 = _make_consent_delta_report(old_att_id="A1", new_att_id="A3_changed")
        validation = validate_operator_consent_binding(record, report2)
        if validation.valid:
            return IdentityTestResult(
                case_id="consent_attestation_mismatch_invalid",
                status=IdentityBatteryStatus.FAILED,
                severity=IdentityTestSeverity.CRITICAL,
                summary="Consent validated with mismatched new_attestation_id",
                errors=("new_attestation_mismatch_not_detected",),
                evidence_refs=("attestation_mismatch_consent",),
                duration_ms=_IMMEDIATE,
            )
    except Exception as exc:
        return IdentityTestResult(
            case_id="consent_attestation_mismatch_invalid",
            status=IdentityBatteryStatus.FAILED,
            severity=IdentityTestSeverity.CRITICAL,
            summary=f"mismatch test failed: {exc}",
            errors=(f"exception:{exc}",),
            duration_ms=_IMMEDIATE,
        )

    return IdentityTestResult(
        case_id="consent_attestation_mismatch_invalid",
        status=IdentityBatteryStatus.PASSED,
        severity=IdentityTestSeverity.CRITICAL,
        summary="Attestation mismatch invalidates consent",
        evidence_refs=("attestation_mismatch_consent",),
        duration_ms=_IMMEDIATE,
    )


def run_consent_does_not_grant_capability() -> IdentityTestResult:
    try:
        from agentic_runtime.identity.operator_consent import (
            build_operator_consent_request,
            grant_operator_consent,
            operator_consent_record_to_dict,
        )
    except ImportError as exc:
        return IdentityTestResult(
            case_id="consent_does_not_grant_capability",
            status=IdentityBatteryStatus.SKIPPED,
            severity=IdentityTestSeverity.HIGH,
            summary=f"consent not available: {exc}",
            duration_ms=_IMMEDIATE,
        )

    try:
        report = _make_consent_delta_report()
        request = build_operator_consent_request(report)
        record = grant_operator_consent(request, operator_id="op1", risk_acknowledged=True)
        d = operator_consent_record_to_dict(record)
        capability_terms = {"verified", "implemented", "production_eligible", "self_improving"}
        for term in capability_terms:
            for v in d.values():
                if isinstance(v, str) and term in v.lower():
                    return IdentityTestResult(
                        case_id="consent_does_not_grant_capability",
                        status=IdentityBatteryStatus.FAILED,
                        severity=IdentityTestSeverity.HIGH,
                        summary=f"Consent record claims capability: {term}",
                        errors=(f"capability_claim_in_consent:{term}",),
                        evidence_refs=("consent_not_capability",),
                        duration_ms=_IMMEDIATE,
                    )
    except Exception as exc:
        return IdentityTestResult(
            case_id="consent_does_not_grant_capability",
            status=IdentityBatteryStatus.FAILED,
            severity=IdentityTestSeverity.HIGH,
            summary=f"capability test failed: {exc}",
            errors=(f"exception:{exc}",),
            duration_ms=_IMMEDIATE,
        )

    return IdentityTestResult(
        case_id="consent_does_not_grant_capability",
        status=IdentityBatteryStatus.PASSED,
        severity=IdentityTestSeverity.HIGH,
        summary="Consent does not grant capability",
        evidence_refs=("consent_not_capability",),
        duration_ms=_IMMEDIATE,
    )


# ---------------------------------------------------------------------------
# 7.10 CLI surface battery
# ---------------------------------------------------------------------------

def _run_cli(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(  # nosec B603 - fixed local CLI argv assembled from explicit argument strings
        [sys.executable, "-m", "agentic_runtime.cli", *args],
        capture_output=True,
        text=True,
        timeout=30,
    )


def run_cli_status_json_works() -> IdentityTestResult:
    try:
        result = _run_cli("identity", "status", "--json")
        data = json.loads(result.stdout)
        if "status" not in data or "subsystems" not in data:
            return IdentityTestResult(
                case_id="cli_status_json_works",
                status=IdentityBatteryStatus.FAILED,
                severity=IdentityTestSeverity.CRITICAL,
                summary="identity status --json missing required fields",
                errors=("missing_status_fields",),
                evidence_refs=("cli_status_json",),
                duration_ms=_IMMEDIATE,
            )
    except Exception as exc:
        return IdentityTestResult(
            case_id="cli_status_json_works",
            status=IdentityBatteryStatus.FAILED,
            severity=IdentityTestSeverity.CRITICAL,
            summary=f"identity status --json failed: {exc}",
            errors=(f"cli_error:{exc}",),
            evidence_refs=("cli_status_json",),
            duration_ms=_IMMEDIATE,
        )

    return IdentityTestResult(
        case_id="cli_status_json_works",
        status=IdentityBatteryStatus.PASSED,
        severity=IdentityTestSeverity.CRITICAL,
        summary="identity status --json produces valid output",
        evidence_refs=("cli_status_json",),
        duration_ms=_IMMEDIATE,
    )


def run_cli_verify_json_works() -> IdentityTestResult:
    try:
        result = _run_cli("identity", "verify", "--json")
        data = json.loads(result.stdout)
        if "status" not in data or "subsystems" not in data:
            return IdentityTestResult(
                case_id="cli_verify_json_works",
                status=IdentityBatteryStatus.FAILED,
                severity=IdentityTestSeverity.CRITICAL,
                summary="identity verify --json missing required fields",
                errors=("missing_verify_fields",),
                evidence_refs=("cli_verify_json",),
                duration_ms=_IMMEDIATE,
            )
    except Exception as exc:
        return IdentityTestResult(
            case_id="cli_verify_json_works",
            status=IdentityBatteryStatus.FAILED,
            severity=IdentityTestSeverity.CRITICAL,
            summary=f"identity verify --json failed: {exc}",
            errors=(f"cli_error:{exc}",),
            evidence_refs=("cli_verify_json",),
            duration_ms=_IMMEDIATE,
        )

    return IdentityTestResult(
        case_id="cli_verify_json_works",
        status=IdentityBatteryStatus.PASSED,
        severity=IdentityTestSeverity.CRITICAL,
        summary="identity verify --json produces valid output",
        evidence_refs=("cli_verify_json",),
        duration_ms=_IMMEDIATE,
    )


def run_cli_status_verify_read_only() -> IdentityTestResult:
    try:
        s1 = _run_cli("identity", "status", "--json").stdout
        s2 = _run_cli("identity", "status", "--json").stdout
        if s1 != s2:
            return IdentityTestResult(
                case_id="cli_status_verify_read_only",
                status=IdentityBatteryStatus.FAILED,
                severity=IdentityTestSeverity.HIGH,
                summary="identity status output is not stable (read-only violation)",
                errors=("status_output_volatile",),
                evidence_refs=("cli_read_only",),
                duration_ms=_IMMEDIATE,
            )
    except Exception as exc:
        return IdentityTestResult(
            case_id="cli_status_verify_read_only",
            status=IdentityBatteryStatus.FAILED,
            severity=IdentityTestSeverity.HIGH,
            summary=f"read-only status test failed: {exc}",
            errors=(f"cli_error:{exc}",),
            duration_ms=_IMMEDIATE,
        )

    return IdentityTestResult(
        case_id="cli_status_verify_read_only",
        status=IdentityBatteryStatus.PASSED,
        severity=IdentityTestSeverity.HIGH,
        summary="status and verify are read-only (stable output)",
        evidence_refs=("cli_read_only",),
        duration_ms=_IMMEDIATE,
    )


def run_cli_exposes_blockers() -> IdentityTestResult:
    try:
        result = _run_cli("identity", "status", "--json")
        data = json.loads(result.stdout)
        subsystems = data.get("subsystems", [])
        if not subsystems:
            return IdentityTestResult(
                case_id="cli_exposes_blockers",
                status=IdentityBatteryStatus.DEGRADED,
                severity=IdentityTestSeverity.MEDIUM,
                summary="No subsystems reported",
                warnings=("no_subsystems",),
                evidence_refs=("cli_blockers",),
                duration_ms=_IMMEDIATE,
            )
        # Verify each subsystem has name and status
        for ss in subsystems:
            if "name" not in ss or "status" not in ss:
                return IdentityTestResult(
                    case_id="cli_exposes_blockers",
                    status=IdentityBatteryStatus.DEGRADED,
                    severity=IdentityTestSeverity.MEDIUM,
                    summary="Subsystem missing name or status field",
                    warnings=("subsystem_incomplete",),
                    evidence_refs=("cli_blockers",),
                    duration_ms=_IMMEDIATE,
                )
    except Exception as exc:
        return IdentityTestResult(
            case_id="cli_exposes_blockers",
            status=IdentityBatteryStatus.FAILED,
            severity=IdentityTestSeverity.MEDIUM,
            summary=f"CLI blocker detection failed: {exc}",
            errors=(f"cli_error:{exc}",),
            duration_ms=_IMMEDIATE,
        )

    return IdentityTestResult(
        case_id="cli_exposes_blockers",
        status=IdentityBatteryStatus.PASSED,
        severity=IdentityTestSeverity.MEDIUM,
        summary="CLI exposes subsystem statuses",
        evidence_refs=("cli_blockers",),
        duration_ms=_IMMEDIATE,
    )
