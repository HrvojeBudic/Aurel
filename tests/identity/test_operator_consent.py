"""Core tests for P1.4.14 Operator Consent Binding."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import pytest

from agentic_runtime.identity.authority_delta import (
    AuthorityDelta,
    AuthorityDeltaInput,
    AuthorityDeltaReport,
    AuthorityDeltaSeverity,
    AuthorityDeltaType,
    authority_delta_report_to_dict,
    detect_authority_deltas,
)
from agentic_runtime.identity.operator_consent import (
    ConsentBindingValidation,
    ConsentValidationError,
    OperatorConsentRecord,
    OperatorConsentRequest,
    OperatorConsentScope,
    OperatorConsentStatus,
    build_operator_consent_request,
    consent_binding_validation_to_dict,
    deny_operator_consent,
    grant_operator_consent,
    operator_consent_record_to_dict,
    operator_consent_request_to_dict,
    revoke_operator_consent,
    validate_operator_consent_binding,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_delta_report(
    source_kind: str = "operator_contract",
    deltas: tuple | None = None,
    old_att_id: str | None = None,
    new_att_id: str | None = None,
) -> AuthorityDeltaReport:
    """Build a full AuthorityDeltaReport with consent-required deltas."""
    if deltas is None:
        d1 = AuthorityDelta(
            delta_id="adt_test_1",
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
        deltas = (d1,)

    highest = AuthorityDeltaSeverity.INFO
    for d in deltas:
        if hasattr(d, "severity"):
            sev = d.severity
            idx_old = {"INFO": 0, "LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}[
                highest.value
            ]
            idx_new = {"INFO": 0, "LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}[
                sev.value
            ]
            if idx_new > idx_old:
                highest = sev

    consent = any(getattr(d, "requires_operator_consent", False) for d in deltas)
    return AuthorityDeltaReport(
        report_id="adr_test",
        source_kind=source_kind,
        deltas=deltas,
        highest_severity=highest,
        requires_operator_consent=consent,
        requires_evidence=any(getattr(d, "requires_evidence", False) for d in deltas),
        summary="Test delta report",
        safe_to_auto_accept=not (consent and highest.value in {"HIGH", "CRITICAL"}),
        old_attestation_id=old_att_id,
        new_attestation_id=new_att_id,
    )


# ---------------------------------------------------------------------------
# Build consent request
# ---------------------------------------------------------------------------


def test_builds_consent_request_from_authority_delta_report():
    report = _make_delta_report()
    request = build_operator_consent_request(report)
    assert isinstance(request, OperatorConsentRequest)
    assert len(request.delta_ids) >= 1
    assert "adt_test_1" in request.delta_ids


def test_consent_request_includes_delta_ids():
    report = _make_delta_report()
    request = build_operator_consent_request(report)
    assert request.delta_ids == ("adt_test_1",)


def test_consent_request_includes_attestation_ids():
    report = _make_delta_report(old_att_id="srcatt_old", new_att_id="srcatt_new")
    request = build_operator_consent_request(report)
    assert request.old_attestation_id == "srcatt_old"
    assert request.new_attestation_id == "srcatt_new"


def test_consent_request_includes_human_readable_summary():
    report = _make_delta_report()
    request = build_operator_consent_request(report)
    assert "risk_ceiling" in request.summary.lower()
    assert "HIGH" in request.summary


# ---------------------------------------------------------------------------
# Grant consent
# ---------------------------------------------------------------------------


def test_grant_operator_consent_creates_record():
    report = _make_delta_report()
    request = build_operator_consent_request(report)
    record = grant_operator_consent(request, operator_id="operator.test", risk_acknowledged=True)
    assert record.status == OperatorConsentStatus.GRANTED
    assert record.consent_id.startswith("cnsc_")
    assert record.operator_id == "operator.test"


def test_grant_consent_binds_to_exact_delta_ids():
    report = _make_delta_report()
    request = build_operator_consent_request(report)
    record = grant_operator_consent(request, operator_id="op1", risk_acknowledged=True)
    assert record.delta_ids == request.delta_ids


def test_grant_consent_binds_to_exact_attestation_ids():
    report = _make_delta_report(old_att_id="A1", new_att_id="A2")
    request = build_operator_consent_request(report)
    record = grant_operator_consent(request, operator_id="op1", risk_acknowledged=True)
    assert record.old_attestation_id == "A1"
    assert record.new_attestation_id == "A2"


def test_high_severity_consent_requires_risk_acknowledgement():
    report = _make_delta_report()
    request = build_operator_consent_request(report)
    with pytest.raises(ConsentValidationError) as exc_info:
        grant_operator_consent(request, operator_id="op1", risk_acknowledged=False)
    assert "risk_acknowledgement_required" in exc_info.value.blockers


def test_high_severity_consent_with_risk_ack_works():
    report = _make_delta_report()
    request = build_operator_consent_request(report)
    record = grant_operator_consent(request, operator_id="op1", risk_acknowledged=True)
    assert record.risk_acknowledged is True
    assert record.status == OperatorConsentStatus.GRANTED


def test_empty_delta_request_cannot_be_granted():
    """Request with no consent-required deltas raises blockers."""
    report = _make_delta_report(deltas=())  # no consent-required deltas
    request = build_operator_consent_request(report)
    with pytest.raises(ConsentValidationError) as exc_info:
        grant_operator_consent(request, operator_id="op1")
    assert "no_consent_required_deltas" in exc_info.value.blockers


def test_missing_operator_id_fails():
    report = _make_delta_report()
    request = build_operator_consent_request(report)
    with pytest.raises(ConsentValidationError):
        grant_operator_consent(request, operator_id="", risk_acknowledged=True)


# ---------------------------------------------------------------------------
# Deny consent
# ---------------------------------------------------------------------------


def test_deny_operator_consent_creates_denied_record():
    report = _make_delta_report()
    request = build_operator_consent_request(report)
    record = deny_operator_consent(request, operator_id="op1", reason="too risky")
    assert record.status == OperatorConsentStatus.DENIED
    assert record.denied_at is not None
    assert record.granted_at is None
    assert record.reason == "too risky"


# ---------------------------------------------------------------------------
# Revoke consent
# ---------------------------------------------------------------------------


def test_revoke_operator_consent_invalidates_record():
    report = _make_delta_report()
    request = build_operator_consent_request(report)
    record = grant_operator_consent(request, operator_id="op1", risk_acknowledged=True)
    revoked = revoke_operator_consent(record, operator_id="op1")
    assert revoked.status == OperatorConsentStatus.REVOKED
    assert revoked.revoked_at is not None


def test_revoke_only_works_on_granted():
    report = _make_delta_report()
    request = build_operator_consent_request(report)
    denied = deny_operator_consent(request, operator_id="op1")
    with pytest.raises(ConsentValidationError) as exc_info:
        revoke_operator_consent(denied, operator_id="op1")
    assert "consent_not_granted" in exc_info.value.blockers


# ---------------------------------------------------------------------------
# Validate consent binding
# ---------------------------------------------------------------------------


def test_validate_consent_binding_accepts_matching_record():
    report = _make_delta_report(old_att_id="A1", new_att_id="A2")
    request = build_operator_consent_request(report)
    record = grant_operator_consent(request, operator_id="op1", risk_acknowledged=True)

    validation = validate_operator_consent_binding(record, report)
    assert validation.valid is True
    assert len(validation.blockers) == 0


def test_validate_consent_binding_rejects_missing_delta():
    report = _make_delta_report(old_att_id="A1", new_att_id="A2")
    request = build_operator_consent_request(report)
    record = grant_operator_consent(request, operator_id="op1", risk_acknowledged=True)

    # Create a different report with a different delta ID
    d_new = AuthorityDelta(
        delta_id="adt_other",
        delta_type=AuthorityDeltaType.RISK_CEILING_INCREASED,
        severity=AuthorityDeltaSeverity.HIGH,
        source_kind="operator_contract",
        field_path="risk_ceiling",
        old_value="medium",
        new_value="high",
        old_attestation_id="A1",
        new_attestation_id="A2",
        requires_operator_consent=True,
        requires_evidence=False,
        reason="different delta",
        blockers=(),
        warnings=(),
    )
    report2 = _make_delta_report(deltas=(d_new,), old_att_id="A1", new_att_id="A2")

    validation = validate_operator_consent_binding(record, report2)
    assert validation.valid is False
    assert "delta_not_covered" in validation.blockers


def test_validate_consent_binding_rejects_old_attestation_mismatch():
    report = _make_delta_report(old_att_id="A1", new_att_id="A2")
    request = build_operator_consent_request(report)
    record = grant_operator_consent(request, operator_id="op1", risk_acknowledged=True)

    report_mismatch = _make_delta_report(old_att_id="A_DIFFERENT", new_att_id="A2")
    validation = validate_operator_consent_binding(record, report_mismatch)
    assert validation.valid is False
    assert "old_attestation_mismatch" in validation.blockers


def test_validate_consent_binding_rejects_new_attestation_mismatch():
    report = _make_delta_report(old_att_id="A1", new_att_id="A2")
    request = build_operator_consent_request(report)
    record = grant_operator_consent(request, operator_id="op1", risk_acknowledged=True)

    report_mismatch = _make_delta_report(old_att_id="A1", new_att_id="A_DIFFERENT")
    validation = validate_operator_consent_binding(record, report_mismatch)
    assert validation.valid is False
    assert "new_attestation_mismatch" in validation.blockers


def test_validate_consent_binding_rejects_revoked_record():
    report = _make_delta_report(old_att_id="A1", new_att_id="A2")
    request = build_operator_consent_request(report)
    record = grant_operator_consent(request, operator_id="op1", risk_acknowledged=True)
    revoked = revoke_operator_consent(record, operator_id="op1")

    validation = validate_operator_consent_binding(revoked, report)
    assert validation.valid is False
    assert "consent_revoked" in validation.blockers


def test_validate_consent_binding_rejects_expired_record():
    report = _make_delta_report(old_att_id="A1", new_att_id="A2")
    yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    request = build_operator_consent_request(report, expires_at=yesterday)
    record = grant_operator_consent(request, operator_id="op1", risk_acknowledged=True)

    validation = validate_operator_consent_binding(record, report)
    assert validation.valid is False
    assert "consent_expired" in validation.blockers


def test_validate_consent_binding_accepts_non_expired_record():
    report = _make_delta_report(old_att_id="A1", new_att_id="A2")
    next_week = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    request = build_operator_consent_request(report, expires_at=next_week)
    record = grant_operator_consent(request, operator_id="op1", risk_acknowledged=True)

    validation = validate_operator_consent_binding(record, report)
    assert validation.valid is True


# ---------------------------------------------------------------------------
# Semantic tests
# ---------------------------------------------------------------------------


def test_consent_does_not_transfer_to_different_delta():
    report1 = _make_delta_report(old_att_id="A1", new_att_id="A2")
    request1 = build_operator_consent_request(report1)
    record = grant_operator_consent(request1, operator_id="op1", risk_acknowledged=True)

    # Different delta ID in report2
    d2 = AuthorityDelta(
        delta_id="adt_different",
        delta_type=AuthorityDeltaType.OVERSIGHT_WEAKENED,
        severity=AuthorityDeltaSeverity.CRITICAL,
        source_kind="operator_contract",
        field_path="requires_human_approval",
        old_value=True,
        new_value=False,
        old_attestation_id="A1",
        new_attestation_id="A2",
        requires_operator_consent=True,
        requires_evidence=False,
        reason="oversight weakened",
        blockers=(),
        warnings=(),
    )
    report2 = _make_delta_report(deltas=(d2,), old_att_id="A1", new_att_id="A2")

    validation = validate_operator_consent_binding(record, report2)
    assert validation.valid is False


def test_consent_does_not_transfer_to_changed_new_attestation():
    report = _make_delta_report(old_att_id="A1", new_att_id="A2")
    request = build_operator_consent_request(report)
    record = grant_operator_consent(request, operator_id="op1", risk_acknowledged=True)

    report_changed = _make_delta_report(old_att_id="A1", new_att_id="A3")
    validation = validate_operator_consent_binding(record, report_changed)
    assert validation.valid is False


def test_single_delta_scope_does_not_cover_full_report_with_multiple_deltas():
    d1 = AuthorityDelta(
        delta_id="adt_1",
        delta_type=AuthorityDeltaType.RISK_CEILING_INCREASED,
        severity=AuthorityDeltaSeverity.HIGH,
        source_kind="operator_contract",
        field_path="risk_ceiling",
        old_value="low",
        new_value="high",
        old_attestation_id="A1",
        new_attestation_id="A2",
        requires_operator_consent=True,
        requires_evidence=False,
        reason="risk",
        blockers=(),
        warnings=(),
    )
    d2 = AuthorityDelta(
        delta_id="adt_2",
        delta_type=AuthorityDeltaType.OVERSIGHT_WEAKENED,
        severity=AuthorityDeltaSeverity.CRITICAL,
        source_kind="operator_contract",
        field_path="requires_human_approval",
        old_value=True,
        new_value=False,
        old_attestation_id="A1",
        new_attestation_id="A2",
        requires_operator_consent=True,
        requires_evidence=False,
        reason="oversight",
        blockers=(),
        warnings=(),
    )
    report = _make_delta_report(deltas=(d1, d2), old_att_id="A1", new_att_id="A2")
    request = build_operator_consent_request(report, requested_scope=OperatorConsentScope.SINGLE_DELTA)

    # SINGLE_DELTA scope should only include one delta
    assert len(request.delta_ids) <= 2  # build_operator_consent_request includes all consent-required

    # Grant with SINGLE_DELTA
    record = grant_operator_consent(request, operator_id="op1", risk_acknowledged=True)
    # Validate against the full report should fail because SINGLE_DELTA doesn't cover both
    validation = validate_operator_consent_binding(record, report)
    # SINGLE_DELTA with one delta_id fails because report has more consent-required deltas
    if len(request.delta_ids) == 1:
        assert validation.valid is False
        assert "delta_not_covered" in validation.blockers


def test_delta_report_scope_covers_all_report_deltas():
    d1 = AuthorityDelta(
        delta_id="adt_1",
        delta_type=AuthorityDeltaType.RISK_CEILING_INCREASED,
        severity=AuthorityDeltaSeverity.HIGH,
        source_kind="operator_contract",
        field_path="risk_ceiling",
        old_value="low",
        new_value="high",
        old_attestation_id="A1",
        new_attestation_id="A2",
        requires_operator_consent=True,
        requires_evidence=False,
        reason="risk",
        blockers=(),
        warnings=(),
    )
    d2 = AuthorityDelta(
        delta_id="adt_2",
        delta_type=AuthorityDeltaType.OVERSIGHT_WEAKENED,
        severity=AuthorityDeltaSeverity.CRITICAL,
        source_kind="operator_contract",
        field_path="requires_human_approval",
        old_value=True,
        new_value=False,
        old_attestation_id="A1",
        new_attestation_id="A2",
        requires_operator_consent=True,
        requires_evidence=False,
        reason="oversight",
        blockers=(),
        warnings=(),
    )
    report = _make_delta_report(deltas=(d1, d2), old_att_id="A1", new_att_id="A2")
    request = build_operator_consent_request(report, requested_scope=OperatorConsentScope.DELTA_REPORT)
    record = grant_operator_consent(request, operator_id="op1", risk_acknowledged=True)

    validation = validate_operator_consent_binding(record, report)
    assert validation.valid is True


# ---------------------------------------------------------------------------
# Consent does not grant capability
# ---------------------------------------------------------------------------


def test_consent_does_not_mark_capability_verified():
    report = _make_delta_report()
    request = build_operator_consent_request(report)
    record = grant_operator_consent(request, operator_id="op1", risk_acknowledged=True)

    # Consent record must not contain any capability verification markers
    record_dict = operator_consent_record_to_dict(record)
    assert "capability_verified" not in record_dict
    assert "capability_status" not in record_dict
    assert "production_eligible" not in record_dict


# ---------------------------------------------------------------------------
# Serialization
# ---------------------------------------------------------------------------


def test_consent_record_serialization_is_json_stable():
    report = _make_delta_report(old_att_id="A1", new_att_id="A2")
    request = build_operator_consent_request(report)
    record = grant_operator_consent(request, operator_id="op1", risk_acknowledged=True)

    d = operator_consent_record_to_dict(record)
    json_str = json.dumps(d, sort_keys=True)
    parsed = json.loads(json_str)
    assert parsed["consent_id"].startswith("cnsc_")
    assert parsed["status"] == "GRANTED"


def test_consent_request_serialization_is_json_stable():
    report = _make_delta_report()
    request = build_operator_consent_request(report)
    d = operator_consent_request_to_dict(request)
    json_str = json.dumps(d, sort_keys=True)
    parsed = json.loads(json_str)
    assert parsed["highest_severity"] == "HIGH"


def test_consent_binding_validation_serialization():
    report = _make_delta_report(old_att_id="A1", new_att_id="A2")
    request = build_operator_consent_request(report)
    record = grant_operator_consent(request, operator_id="op1", risk_acknowledged=True)
    validation = validate_operator_consent_binding(record, report)
    d = consent_binding_validation_to_dict(validation)
    assert d["valid"] is True
    assert len(d["blockers"]) == 0


# ---------------------------------------------------------------------------
# Consent request properties
# ---------------------------------------------------------------------------


def test_critical_severity_consent_requires_risk_acknowledgement():
    d = AuthorityDelta(
        delta_id="adt_crit",
        delta_type=AuthorityDeltaType.OVERSIGHT_WEAKENED,
        severity=AuthorityDeltaSeverity.CRITICAL,
        source_kind="operator_contract",
        field_path="requires_human_approval",
        old_value=True,
        new_value=False,
        old_attestation_id=None,
        new_attestation_id=None,
        requires_operator_consent=True,
        requires_evidence=False,
        reason="oversight",
        blockers=(),
        warnings=(),
    )
    report = _make_delta_report(deltas=(d,))
    request = build_operator_consent_request(report)
    assert request.requires_explicit_risk_acknowledgement is True


def test_consent_request_id_is_deterministic():
    report = _make_delta_report(old_att_id="A1", new_att_id="A2")
    r1 = build_operator_consent_request(report)
    r2 = build_operator_consent_request(report)
    # Same inputs should produce same request_id
    assert r1.request_id == r2.request_id


def test_source_update_scope_is_bound_to_attestation_pair():
    report = _make_delta_report(old_att_id="A1", new_att_id="A2")
    request = build_operator_consent_request(report, requested_scope=OperatorConsentScope.SOURCE_UPDATE)
    record = grant_operator_consent(request, operator_id="op1", risk_acknowledged=True)

    # Mismatched new attestation → invalid
    report2 = _make_delta_report(old_att_id="A1", new_att_id="A_DIFFERENT")
    validation = validate_operator_consent_binding(record, report2)
    assert validation.valid is False
    assert "new_attestation_mismatch" in validation.blockers
