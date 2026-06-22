"""P1.4.14 seal tests — consent invariants that must hold."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from agentic_runtime.identity.authority_delta import (
    AuthorityDelta,
    AuthorityDeltaReport,
    AuthorityDeltaSeverity,
    AuthorityDeltaType,
)
from agentic_runtime.identity.operator_consent import (
    ConsentValidationError,
    OperatorConsentScope,
    OperatorConsentStatus,
    build_operator_consent_request,
    deny_operator_consent,
    grant_operator_consent,
    operator_consent_record_to_dict,
    revoke_operator_consent,
    validate_operator_consent_binding,
)


def _make_report(deltas=None, old_att=None, new_att=None):
    if deltas is None:
        d = AuthorityDelta(
            delta_id="adt_seal_1",
            delta_type=AuthorityDeltaType.RISK_CEILING_INCREASED,
            severity=AuthorityDeltaSeverity.HIGH,
            source_kind="operator_contract",
            field_path="risk_ceiling",
            old_value="low",
            new_value="high",
            old_attestation_id=old_att,
            new_attestation_id=new_att,
            requires_operator_consent=True,
            requires_evidence=False,
            reason="seal test",
            blockers=(),
            warnings=(),
        )
        deltas = (d,)
    highest = max(
        (d.severity for d in deltas),
        key=lambda s: {"INFO": 0, "LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}[s.value],
    )
    consent = any(getattr(d, "requires_operator_consent", False) for d in deltas)
    sk = deltas[0].source_kind if deltas else "operator_contract"
    return AuthorityDeltaReport(
        report_id="adr_seal",
        source_kind=sk,
        deltas=deltas,
        highest_severity=highest,
        requires_operator_consent=consent,
        requires_evidence=False,
        summary="seal",
        safe_to_auto_accept=not consent,
        old_attestation_id=old_att,
        new_attestation_id=new_att,
    )


def test_p1414_no_global_consent():
    """INV-P1414-03: Consent is not global."""
    report1 = _make_report(old_att="A1", new_att="A2")
    request1 = build_operator_consent_request(report1)
    record = grant_operator_consent(request1, operator_id="op1", risk_acknowledged=True)

    # Same operator, different delta report (different attestation pair)
    report2 = _make_report(old_att="A3", new_att="A4")
    validation = validate_operator_consent_binding(record, report2)
    assert validation.valid is False, "Consent must not be global"


def test_p1414_consent_is_bound_to_delta_id():
    """INV-P1414-01: Consent is bound to exact delta IDs."""
    d1 = AuthorityDelta(
        delta_id="adt_bound_1",
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
        reason="bound test",
        blockers=(),
        warnings=(),
    )
    report1 = _make_report(deltas=(d1,), old_att="A1", new_att="A2")
    request1 = build_operator_consent_request(report1)
    record = grant_operator_consent(request1, operator_id="op1", risk_acknowledged=True)

    d2 = AuthorityDelta(
        delta_id="adt_bound_2",  # different ID
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
        reason="bound test 2",
        blockers=(),
        warnings=(),
    )
    report2 = _make_report(deltas=(d2,), old_att="A1", new_att="A2")
    validation = validate_operator_consent_binding(record, report2)
    assert validation.valid is False
    assert "delta_not_covered" in validation.blockers


def test_p1414_consent_is_bound_to_attestation_pair():
    """INV-P1414-02: Consent is bound to old/new attestation IDs."""
    report = _make_report(old_att="A_GOOD", new_att="B_GOOD")
    request = build_operator_consent_request(report)
    record = grant_operator_consent(request, operator_id="op1", risk_acknowledged=True)

    # Different attestation pair
    report_different = _make_report(old_att="A_GOOD", new_att="B_DIFFERENT")
    validation = validate_operator_consent_binding(record, report_different)
    assert validation.valid is False
    assert "new_attestation_mismatch" in validation.blockers


def test_p1414_revoked_consent_is_invalid():
    """INV-P1414-05: Revoked consent is invalid."""
    report = _make_report(old_att="A1", new_att="A2")
    request = build_operator_consent_request(report)
    record = grant_operator_consent(request, operator_id="op1", risk_acknowledged=True)
    revoked = revoke_operator_consent(record, operator_id="op1")

    validation = validate_operator_consent_binding(revoked, report)
    assert validation.valid is False
    assert "consent_revoked" in validation.blockers


def test_p1414_expired_consent_is_invalid():
    """INV-P1414-06: Expired consent is invalid."""
    report = _make_report(old_att="A1", new_att="A2")
    yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    request = build_operator_consent_request(report, expires_at=yesterday)
    record = grant_operator_consent(request, operator_id="op1", risk_acknowledged=True)

    validation = validate_operator_consent_binding(record, report)
    assert validation.valid is False
    assert "consent_expired" in validation.blockers


def test_p1414_high_critical_requires_risk_ack():
    """INV-P1414-07: HIGH/CRITICAL requires explicit risk acknowledgement."""
    report = _make_report(old_att="A1", new_att="A2")
    request = build_operator_consent_request(report)
    assert request.requires_explicit_risk_acknowledgement is True

    with pytest.raises(ConsentValidationError) as exc_info:
        grant_operator_consent(request, operator_id="op1", risk_acknowledged=False)
    assert "risk_acknowledgement_required" in exc_info.value.blockers

    # With risk_ack → works
    record = grant_operator_consent(request, operator_id="op1", risk_acknowledged=True)
    assert record.risk_acknowledged is True


def test_p1414_consent_does_not_execute_tools():
    """INV-P1414-08: Consent does not execute actions."""
    report = _make_report()
    request = build_operator_consent_request(report)
    record = grant_operator_consent(request, operator_id="op1", risk_acknowledged=True)

    # Verify no tool/action execution markers
    d = operator_consent_record_to_dict(record)
    assert "execution_result" not in d
    assert "action_taken" not in d
    assert "tool_executed" not in d


def test_p1414_consent_does_not_modify_source():
    """INV-P1414-09: Consent does not modify source."""
    report = _make_report()
    original_old = report.old_attestation_id
    original_new = report.new_attestation_id

    request = build_operator_consent_request(report)
    grant_operator_consent(request, operator_id="op1", risk_acknowledged=True)

    assert report.old_attestation_id == original_old
    assert report.new_attestation_id == original_new


def test_p1414_consent_does_not_grant_capability():
    """INV-P1414-09: Consent does not grant capability verification."""
    report = _make_report()
    request = build_operator_consent_request(report)
    record = grant_operator_consent(request, operator_id="op1", risk_acknowledged=True)

    d = operator_consent_record_to_dict(record)
    capability_terms = {"verified", "implemented", "production_eligible", "self_improving"}
    for term in capability_terms:
        for v in d.values():
            if isinstance(v, str) and term in v.lower():
                pytest.fail(f"Consent record must not claim capability: found '{term}'")


def test_p1414_consent_prepares_p1415_cli_surface():
    """INV-P1414-10: Consent validation exposes blockers."""
    report = _make_report(old_att="A1", new_att="A2")
    request = build_operator_consent_request(report)
    record = grant_operator_consent(request, operator_id="op1", risk_acknowledged=True)
    revoked = revoke_operator_consent(record, operator_id="op1")

    validation = validate_operator_consent_binding(revoked, report)
    assert validation.valid is False
    assert validation.blockers
    assert "consent_revoked" in validation.blockers
    assert validation.reason


def test_p1414_source_kind_mismatch_is_detected():
    report_op = _make_report(old_att="A1", new_att="A2")
    request = build_operator_consent_request(report_op)
    record = grant_operator_consent(request, operator_id="op1", risk_acknowledged=True)

    # Different source kind
    d2 = AuthorityDelta(
        delta_id="adt_seal_1",
        delta_type=AuthorityDeltaType.RISK_CEILING_INCREASED,
        severity=AuthorityDeltaSeverity.HIGH,
        source_kind="agent_identity_card_config",  # different kind
        field_path="risk_ceiling",
        old_value="low",
        new_value="high",
        old_attestation_id="A1",
        new_attestation_id="A2",
        requires_operator_consent=True,
        requires_evidence=False,
        reason="different kind",
        blockers=(),
        warnings=(),
    )
    report_diff = _make_report(deltas=(d2,), old_att="A1", new_att="A2")
    validation = validate_operator_consent_binding(record, report_diff)
    assert validation.valid is False
    assert "source_kind_mismatch" in validation.blockers


def test_p1414_denied_consent_is_invalid():
    report = _make_report(old_att="A1", new_att="A2")
    request = build_operator_consent_request(report)
    denied = deny_operator_consent(request, operator_id="op1", reason="too risky")

    validation = validate_operator_consent_binding(denied, report)
    assert validation.valid is False
    assert "consent_denied" in validation.blockers


def test_p1414_high_severity_without_risk_ack_fails_validation():
    d = AuthorityDelta(
        delta_id="adt_no_risk",
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
        reason="no risk ack",
        blockers=(),
        warnings=(),
    )
    report = _make_report(deltas=(d,), old_att="A1", new_att="A2")
    request = build_operator_consent_request(report)

    # Force-grant without risk_ack by using a LOW severity report then validating against HIGH
    # The validation should catch risk_not_acknowledged
    record = grant_operator_consent(request, operator_id="op1", risk_acknowledged=True)

    # Create a modified record with risk_acknowledged=False manually
    from agentic_runtime.identity.operator_consent import OperatorConsentRecord

    no_risk_record = OperatorConsentRecord(
        consent_id=record.consent_id,
        request_id=record.request_id,
        status=OperatorConsentStatus.GRANTED,
        scope=record.scope,
        operator_id=record.operator_id,
        operator_display_name=record.operator_display_name,
        source_kind=record.source_kind,
        delta_ids=record.delta_ids,
        old_attestation_id=record.old_attestation_id,
        new_attestation_id=record.new_attestation_id,
        highest_severity=record.highest_severity,
        risk_acknowledged=False,  # explicitly no risk ack
        granted_at=record.granted_at,
    )

    validation = validate_operator_consent_binding(no_risk_record, report)
    assert validation.valid is False
    assert "risk_not_acknowledged" in validation.blockers
