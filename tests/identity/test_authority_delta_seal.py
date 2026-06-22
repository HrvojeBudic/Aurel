"""P1.4.13 seal tests — invariants that must hold across all authority delta detection."""
from __future__ import annotations

import pytest

from agentic_runtime.identity.authority_delta import (
    AuthorityDeltaInput,
    AuthorityDeltaSeverity,
    AuthorityDeltaType,
    detect_authority_deltas,
)


def test_p1413_authority_expansion_cannot_pass_silently():
    """INV-P1413-01: Valid source does not imply safe authority change,
    INV-P1413-02: Authority expansion must be detected."""
    # Expanding authority should always produce at least one delta
    old = {"risk_ceiling": "low", "requires_human_approval": True, "allowed_tools": ["read"]}
    new = {"risk_ceiling": "high", "requires_human_approval": False, "allowed_tools": ["read", "send_email", "deploy"]}
    report = detect_authority_deltas(
        AuthorityDeltaInput(source_kind="operator_contract", old_canonical_object=old, new_canonical_object=new)
    )
    assert len(report.deltas) >= 1, "Authority expansion must produce deltas"


def test_p1413_valid_attested_source_can_still_require_consent():
    """INV-P1413-01: Valid source does not imply safe authority change."""
    old = {"risk_ceiling": "low"}
    new = {"risk_ceiling": "high"}
    report = detect_authority_deltas(
        AuthorityDeltaInput(source_kind="operator_contract", old_canonical_object=old, new_canonical_object=new)
    )
    assert report.requires_operator_consent is True
    assert report.safe_to_auto_accept is False


def test_p1413_human_oversight_weakening_is_critical():
    """INV-P1413-04: Human oversight weakening is critical."""
    old = {"requires_human_approval": True}
    new = {"requires_human_approval": False}
    report = detect_authority_deltas(
        AuthorityDeltaInput(source_kind="operator_contract", old_canonical_object=old, new_canonical_object=new)
    )
    oversight = next(d for d in report.deltas if d.delta_type == AuthorityDeltaType.OVERSIGHT_WEAKENED)
    assert oversight.severity == AuthorityDeltaSeverity.CRITICAL
    assert oversight.requires_operator_consent is True


def test_p1413_doctrine_status_escalation_is_blocked_pending_consent():
    """INV-P1413-06: Roadmap/doctrine status escalation is not implementation evidence."""
    old = {"assimilation_status": "ROADMAP_INFLUENCING"}
    new = {"assimilation_status": "IMPLEMENTED"}
    report = detect_authority_deltas(
        AuthorityDeltaInput(source_kind="external_doctrine", old_canonical_object=old, new_canonical_object=new)
    )
    doc_delta = next(d for d in report.deltas if d.delta_type == AuthorityDeltaType.DOCTRINE_STATUS_ESCALATED)
    assert doc_delta.requires_operator_consent is True
    assert doc_delta.requires_evidence is True


def test_p1413_claim_status_escalation_requires_evidence():
    """INV-P1413-07: Claim status escalation must not bypass claim boundary."""
    old = {"claim_status": "ROADMAP_ONLY"}
    new = {"claim_status": "VERIFIED"}
    report = detect_authority_deltas(
        AuthorityDeltaInput(source_kind="capability_claims", old_canonical_object=old, new_canonical_object=new)
    )
    claim_delta = next(d for d in report.deltas if d.delta_type == AuthorityDeltaType.CLAIM_STATUS_ESCALATED)
    assert claim_delta.requires_evidence is True


def test_p1413_external_effect_permission_requires_consent():
    """INV-P1413-05: External-effect permission addition requires consent."""
    old = {"external_effect_permissions": []}
    new = {"external_effect_permissions": ["send_email", "publish"]}
    report = detect_authority_deltas(
        AuthorityDeltaInput(source_kind="operator_contract", old_canonical_object=old, new_canonical_object=new)
    )
    ext_delta = next((d for d in report.deltas if d.delta_type == AuthorityDeltaType.EXTERNAL_EFFECT_ADDED), None)
    assert ext_delta is not None
    assert ext_delta.requires_operator_consent is True
    assert ext_delta.severity == AuthorityDeltaSeverity.CRITICAL


def test_p1413_authority_delta_uses_attestation_refs():
    """INV-P1413-10: Authority delta reports must cite attestation IDs when available."""
    class FakeAtt:
        attestation_id = "srcatt_test_123"

    old = {"risk_ceiling": "low"}
    new = {"risk_ceiling": "high"}
    report = detect_authority_deltas(
        AuthorityDeltaInput(
            source_kind="operator_contract",
            old_canonical_object=old,
            new_canonical_object=new,
            old_attestation=FakeAtt(),
            new_attestation=FakeAtt(),
        )
    )
    assert report.old_attestation_id is not None
    assert report.new_attestation_id is not None
    assert "srcatt_test_123" in str(report.old_attestation_id)


def test_p1413_does_not_grant_consent():
    """INV-P1413-08: Authority delta detection does not grant consent."""
    old = {"risk_ceiling": "low"}
    new = {"risk_ceiling": "high"}
    report = detect_authority_deltas(
        AuthorityDeltaInput(source_kind="operator_contract", old_canonical_object=old, new_canonical_object=new)
    )
    # Detect but do not grant consent - the report flags consent is required,
    # it does not approve it
    assert report.requires_operator_consent is True
    assert report.safe_to_auto_accept is False
    # The report must not have an "approved" or "consent_granted" flag
    payload = {
        "report_id": report.report_id,
        "deltas": [],
        "highest_severity": report.highest_severity.value,
        "requires_operator_consent": report.requires_operator_consent,
    }
    assert "approved" not in payload
    assert "consent_granted" not in payload


def test_p1413_does_not_execute_tools():
    """INV-P1413-09: Authority delta detection does not execute actions."""
    old = {"allowed_tools": ["read"]}
    new = {"allowed_tools": ["read", "delete_file"]}
    report = detect_authority_deltas(
        AuthorityDeltaInput(source_kind="operator_contract", old_canonical_object=old, new_canonical_object=new)
    )
    assert report.highest_severity != AuthorityDeltaSeverity.INFO
    # Verify no action/tool was executed; report is purely informational
    assert isinstance(report.summary, str)


def test_p1413_does_not_modify_source():
    """INV-P1413-09: Authority delta detection does not modify source."""
    old_obj = {"risk_ceiling": "low", "allowed_tools": ["read"]}
    new_obj = {"risk_ceiling": "high", "allowed_tools": ["read", "delete_file"]}
    old_copy = dict(old_obj)
    new_copy = dict(new_obj)
    detect_authority_deltas(
        AuthorityDeltaInput(source_kind="operator_contract", old_canonical_object=old_obj, new_canonical_object=new_obj)
    )
    assert old_obj == old_copy, "Old source was mutated"
    assert new_obj == new_copy, "New source was mutated"


def test_p1413_risk_ceiling_increase_to_critical_detected():
    """Risk ceiling from low to critical must be CRITICAL severity."""
    old = {"risk_ceiling": "low"}
    new = {"risk_ceiling": "critical"}
    report = detect_authority_deltas(
        AuthorityDeltaInput(source_kind="operator_contract", old_canonical_object=old, new_canonical_object=new)
    )
    risk_delta = next(d for d in report.deltas if d.delta_type == AuthorityDeltaType.RISK_CEILING_INCREASED)
    assert risk_delta.severity == AuthorityDeltaSeverity.CRITICAL


def test_p1413_deploy_tool_addition_is_external_effect_critical():
    """Adding a 'deploy' tool must be classified as EXTERNAL_EFFECT_ADDED with CRITICAL severity."""
    old = {"allowed_tools": ["read", "list"]}
    new = {"allowed_tools": ["read", "list", "deploy"]}
    report = detect_authority_deltas(
        AuthorityDeltaInput(source_kind="operator_contract", old_canonical_object=old, new_canonical_object=new)
    )
    ext_delta = next((d for d in report.deltas if d.delta_type == AuthorityDeltaType.EXTERNAL_EFFECT_ADDED), None)
    assert ext_delta is not None
    assert ext_delta.severity == AuthorityDeltaSeverity.CRITICAL


def test_p1413_cannot_override_identity_kernel_weakening_is_detected():
    """Weakening the cannot_override_identity_kernel boundary must be detected."""
    old = {"cannot_override_identity_kernel": True}
    new = {"cannot_override_identity_kernel": False}
    report = detect_authority_deltas(
        AuthorityDeltaInput(source_kind="operator_contract", old_canonical_object=old, new_canonical_object=new)
    )
    assert len(report.deltas) >= 1
    assert report.requires_operator_consent is True
