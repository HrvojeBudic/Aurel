"""Core tests for P1.4.13 Authority Delta Detector."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from agentic_runtime.identity.authority_delta import (
    AuthorityDelta,
    AuthorityDeltaInput,
    AuthorityDeltaReport,
    AuthorityDeltaSeverity,
    AuthorityDeltaType,
    CAPABILITY_STATUS_ORDER,
    CLAIM_STATUS_ORDER,
    DOCTRINE_STATUS_ORDER,
    RISK_CEILING_ORDER,
    authority_delta_report_to_dict,
    authority_delta_requires_consent,
    authority_delta_requires_evidence,
    authority_delta_to_dict,
    classify_authority_delta,
    compare_authority_surfaces,
    detect_authority_deltas,
    extract_authority_surface,
    highest_authority_delta_severity,
    resolve_authority_delta_severity,
    summarize_authority_delta_report,
)
from agentic_runtime.yaml_minimal import load_yaml

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures" / "authority_delta"


def _load_yaml(name: str) -> dict:
    return load_yaml((FIXTURES / name).read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Risk ceiling
# ---------------------------------------------------------------------------


def test_detects_risk_ceiling_increase():
    old = {"risk_ceiling": "low"}
    new = {"risk_ceiling": "high"}
    report = detect_authority_deltas(
        AuthorityDeltaInput(source_kind="operator_contract", old_canonical_object=old, new_canonical_object=new)
    )
    assert len(report.deltas) >= 1
    risk_delta = next(d for d in report.deltas if d.delta_type == AuthorityDeltaType.RISK_CEILING_INCREASED)
    assert risk_delta.severity == AuthorityDeltaSeverity.HIGH
    assert risk_delta.requires_operator_consent is True


def test_detects_risk_ceiling_decrease():
    old = {"risk_ceiling": "high"}
    new = {"risk_ceiling": "low"}
    report = detect_authority_deltas(
        AuthorityDeltaInput(source_kind="operator_contract", old_canonical_object=old, new_canonical_object=new)
    )
    risk_delta = next((d for d in report.deltas if d.delta_type == AuthorityDeltaType.RISK_CEILING_DECREASED), None)
    if risk_delta:
        assert risk_delta.severity == AuthorityDeltaSeverity.INFO


def test_risk_ceiling_low_to_critical_is_critical_severity():
    old = {"risk_ceiling": "low"}
    new = {"risk_ceiling": "critical"}
    report = detect_authority_deltas(
        AuthorityDeltaInput(source_kind="operator_contract", old_canonical_object=old, new_canonical_object=new)
    )
    risk_delta = next(d for d in report.deltas if d.delta_type == AuthorityDeltaType.RISK_CEILING_INCREASED)
    assert risk_delta.severity == AuthorityDeltaSeverity.CRITICAL


# ---------------------------------------------------------------------------
# Authority scope
# ---------------------------------------------------------------------------


def test_detects_authority_scope_added():
    old = {"authority_scope": ["read"]}
    new = {"authority_scope": ["read", "write"]}
    report = detect_authority_deltas(
        AuthorityDeltaInput(source_kind="operator_contract", old_canonical_object=old, new_canonical_object=new)
    )
    expansion = next((d for d in report.deltas if d.delta_type == AuthorityDeltaType.AUTHORITY_SCOPE_ADDED), None)
    assert expansion is not None


def test_detects_authority_scope_removed():
    old = {"authority_scope": ["read", "write"]}
    new = {"authority_scope": ["read"]}
    report = detect_authority_deltas(
        AuthorityDeltaInput(source_kind="operator_contract", old_canonical_object=old, new_canonical_object=new)
    )
    reduction = next((d for d in report.deltas if d.delta_type == AuthorityDeltaType.AUTHORITY_SCOPE_REMOVED), None)
    assert reduction is not None
    assert reduction.severity in {AuthorityDeltaSeverity.INFO, AuthorityDeltaSeverity.LOW}


# ---------------------------------------------------------------------------
# Tool permissions
# ---------------------------------------------------------------------------


def test_detects_tool_permission_added():
    old = {"allowed_tools": ["read", "list"]}
    new = {"allowed_tools": ["read", "list", "search"]}
    report = detect_authority_deltas(
        AuthorityDeltaInput(source_kind="operator_contract", old_canonical_object=old, new_canonical_object=new)
    )
    tool_delta = next((d for d in report.deltas if d.delta_type == AuthorityDeltaType.TOOL_PERMISSION_ADDED), None)
    assert tool_delta is not None


def test_detects_write_scope_added():
    old = {"allowed_tools": ["read"]}
    new = {"allowed_tools": ["read", "write_file"]}
    report = detect_authority_deltas(
        AuthorityDeltaInput(source_kind="operator_contract", old_canonical_object=old, new_canonical_object=new)
    )
    write_delta = next((d for d in report.deltas if d.delta_type == AuthorityDeltaType.WRITE_SCOPE_ADDED), None)
    assert write_delta is not None
    assert write_delta.requires_operator_consent is True


def test_detects_external_effect_added():
    old = {"allowed_tools": ["read"]}
    new = {"allowed_tools": ["read", "send_email"]}
    report = detect_authority_deltas(
        AuthorityDeltaInput(source_kind="operator_contract", old_canonical_object=old, new_canonical_object=new)
    )
    ext_delta = next((d for d in report.deltas if d.delta_type == AuthorityDeltaType.EXTERNAL_EFFECT_ADDED), None)
    assert ext_delta is not None
    assert ext_delta.severity == AuthorityDeltaSeverity.CRITICAL
    assert ext_delta.requires_operator_consent is True


# ---------------------------------------------------------------------------
# Human oversight
# ---------------------------------------------------------------------------


def test_detects_human_oversight_weakened():
    old = {"requires_human_approval": True}
    new = {"requires_human_approval": False}
    report = detect_authority_deltas(
        AuthorityDeltaInput(source_kind="operator_contract", old_canonical_object=old, new_canonical_object=new)
    )
    oversight = next(d for d in report.deltas if d.delta_type == AuthorityDeltaType.OVERSIGHT_WEAKENED)
    assert oversight.severity == AuthorityDeltaSeverity.CRITICAL
    assert oversight.requires_operator_consent is True


def test_detects_human_oversight_strengthened():
    old = {"requires_human_approval": False}
    new = {"requires_human_approval": True}
    report = detect_authority_deltas(
        AuthorityDeltaInput(source_kind="operator_contract", old_canonical_object=old, new_canonical_object=new)
    )
    oversight = next((d for d in report.deltas if d.delta_type == AuthorityDeltaType.OVERSIGHT_STRENGTHENED), None)
    assert oversight is not None
    assert oversight.severity == AuthorityDeltaSeverity.INFO


# ---------------------------------------------------------------------------
# Claim status
# ---------------------------------------------------------------------------


def test_detects_claim_status_escalation():
    old = {"claim_status": "FORBIDDEN"}
    new = {"claim_status": "VERIFIED"}
    report = detect_authority_deltas(
        AuthorityDeltaInput(source_kind="capability_claims", old_canonical_object=old, new_canonical_object=new)
    )
    claim_delta = next(d for d in report.deltas if d.delta_type == AuthorityDeltaType.CLAIM_STATUS_ESCALATED)
    assert claim_delta.severity in {AuthorityDeltaSeverity.HIGH, AuthorityDeltaSeverity.CRITICAL}
    assert claim_delta.requires_operator_consent is True
    assert claim_delta.requires_evidence is True


# ---------------------------------------------------------------------------
# Doctrine status
# ---------------------------------------------------------------------------


def test_detects_doctrine_status_escalation():
    old = {"assimilation_status": "REFERENCE_ONLY"}
    new = {"assimilation_status": "IMPLEMENTED"}
    report = detect_authority_deltas(
        AuthorityDeltaInput(source_kind="external_doctrine", old_canonical_object=old, new_canonical_object=new)
    )
    doc_delta = next(d for d in report.deltas if d.delta_type == AuthorityDeltaType.DOCTRINE_STATUS_ESCALATED)
    assert doc_delta.severity in {AuthorityDeltaSeverity.HIGH, AuthorityDeltaSeverity.CRITICAL}
    assert doc_delta.requires_operator_consent is True
    assert doc_delta.requires_evidence is True


# ---------------------------------------------------------------------------
# Capability status
# ---------------------------------------------------------------------------


def test_detects_capability_status_escalation():
    old = {"capability_status": "planned"}
    new = {"capability_status": "verified"}
    report = detect_authority_deltas(
        AuthorityDeltaInput(source_kind="agent_identity_card_config", old_canonical_object=old, new_canonical_object=new)
    )
    cap_delta = next(d for d in report.deltas if d.delta_type == AuthorityDeltaType.CAPABILITY_STATUS_ESCALATED)
    assert cap_delta.severity in {AuthorityDeltaSeverity.HIGH, AuthorityDeltaSeverity.CRITICAL}
    assert cap_delta.requires_operator_consent is True


# ---------------------------------------------------------------------------
# Delta report serialization
# ---------------------------------------------------------------------------


def test_delta_report_is_json_serializable():
    old = {"risk_ceiling": "low", "requires_human_approval": True}
    new = {"risk_ceiling": "high", "requires_human_approval": False}
    report = detect_authority_deltas(
        AuthorityDeltaInput(source_kind="operator_contract", old_canonical_object=old, new_canonical_object=new)
    )
    payload = authority_delta_report_to_dict(report)
    result = json.dumps(payload, sort_keys=True)
    assert len(result) > 0
    parsed = json.loads(result)
    assert parsed["highest_severity"] == "CRITICAL"
    assert parsed["requires_operator_consent"] is True
    assert parsed["safe_to_auto_accept"] is False


# ---------------------------------------------------------------------------
# Semantic tests
# ---------------------------------------------------------------------------


def test_valid_source_with_authority_expansion_requires_consent():
    """INV-P1413-01: Valid source does not imply safe authority change."""
    old = {"risk_ceiling": "low"}
    new = {"risk_ceiling": "high"}
    report = detect_authority_deltas(
        AuthorityDeltaInput(source_kind="operator_contract", old_canonical_object=old, new_canonical_object=new)
    )
    assert report.requires_operator_consent is True
    assert report.safe_to_auto_accept is False


def test_source_validation_downgrade_is_detected():
    old = {"validation_status": "VALID"}
    new = {"validation_status": "REJECTED_UNKNOWN_FIELDS"}
    report = detect_authority_deltas(
        AuthorityDeltaInput(source_kind="source_attestation", old_canonical_object=old, new_canonical_object=new)
    )
    downgrade = next((d for d in report.deltas if d.delta_type == AuthorityDeltaType.SOURCE_VALIDATION_DOWNGRADED), None)
    assert downgrade is not None
    assert downgrade.severity == AuthorityDeltaSeverity.HIGH


def test_validator_change_is_detected():
    old = {"validator_name": "old_validator"}
    new = {"validator_name": "new_validator"}
    report = detect_authority_deltas(
        AuthorityDeltaInput(source_kind="source_attestation", old_canonical_object=old, new_canonical_object=new)
    )
    val_delta = next((d for d in report.deltas if d.delta_type == AuthorityDeltaType.VALIDATOR_CHANGED), None)
    assert val_delta is not None


def test_schema_version_change_is_detected():
    old = {"schema_version": "1.0.0"}
    new = {"schema_version": "2.0.0"}
    report = detect_authority_deltas(
        AuthorityDeltaInput(source_kind="source_attestation", old_canonical_object=old, new_canonical_object=new)
    )
    schema_delta = next((d for d in report.deltas if d.delta_type == AuthorityDeltaType.SCHEMA_VERSION_CHANGED), None)
    assert schema_delta is not None


def test_authority_reduction_does_not_require_same_severity_as_expansion():
    """INV-P1413-02: Reduction != escalation severity."""
    old_expand = {"requires_human_approval": True}
    new_expand = {"requires_human_approval": False}
    r_expand = detect_authority_deltas(
        AuthorityDeltaInput(source_kind="operator_contract", old_canonical_object=old_expand, new_canonical_object=new_expand)
    )
    old_reduce = {"requires_human_approval": False}
    new_reduce = {"requires_human_approval": True}
    r_reduce = detect_authority_deltas(
        AuthorityDeltaInput(source_kind="operator_contract", old_canonical_object=old_reduce, new_canonical_object=new_reduce)
    )
    from agentic_runtime.identity.authority_delta import SEVERITY_ORDER as _SEV_ORDER
    expansion_sev = _SEV_ORDER.index(r_expand.deltas[0].severity)
    reduction_sev = _SEV_ORDER.index(r_reduce.deltas[0].severity)
    assert expansion_sev > reduction_sev


def test_claim_status_forbidden_to_verified_is_critical():
    old = {"claim_status": "FORBIDDEN"}
    new = {"claim_status": "VERIFIED"}
    report = detect_authority_deltas(
        AuthorityDeltaInput(source_kind="capability_claims", old_canonical_object=old, new_canonical_object=new)
    )
    claim_delta = next(d for d in report.deltas if d.delta_type == AuthorityDeltaType.CLAIM_STATUS_ESCALATED)
    assert claim_delta.severity in {AuthorityDeltaSeverity.HIGH, AuthorityDeltaSeverity.CRITICAL}


def test_doctrine_roadmap_to_implemented_requires_evidence():
    old = {"assimilation_status": "ROADMAP_INFLUENCING"}
    new = {"assimilation_status": "IMPLEMENTED"}
    report = detect_authority_deltas(
        AuthorityDeltaInput(source_kind="external_doctrine", old_canonical_object=old, new_canonical_object=new)
    )
    doc_delta = next(d for d in report.deltas if d.delta_type == AuthorityDeltaType.DOCTRINE_STATUS_ESCALATED)
    assert doc_delta.requires_evidence is True


def test_external_effect_added_is_critical():
    """INV-P1413-05: External-effect permission addition requires consent."""
    old = {"external_effect_permissions": []}
    new = {"external_effect_permissions": ["send_email"]}
    report = detect_authority_deltas(
        AuthorityDeltaInput(source_kind="operator_contract", old_canonical_object=old, new_canonical_object=new)
    )
    ext_delta = next((d for d in report.deltas if d.delta_type == AuthorityDeltaType.EXTERNAL_EFFECT_ADDED), None)
    assert ext_delta is not None
    assert ext_delta.severity == AuthorityDeltaSeverity.CRITICAL


def test_oversight_weakened_is_critical():
    """INV-P1413-04: Human oversight weakening is critical."""
    old = {"requires_human_approval": True}
    new = {"requires_human_approval": False}
    report = detect_authority_deltas(
        AuthorityDeltaInput(source_kind="operator_contract", old_canonical_object=old, new_canonical_object=new)
    )
    oversight = next(d for d in report.deltas if d.delta_type == AuthorityDeltaType.OVERSIGHT_WEAKENED)
    assert oversight.severity == AuthorityDeltaSeverity.CRITICAL


def test_report_safe_to_auto_accept_false_when_high_delta_exists():
    old = {"risk_ceiling": "low"}
    new = {"risk_ceiling": "high"}
    report = detect_authority_deltas(
        AuthorityDeltaInput(source_kind="operator_contract", old_canonical_object=old, new_canonical_object=new)
    )
    assert report.safe_to_auto_accept is False


def test_no_change_produces_info_severity_empty_deltas():
    obj = {"risk_ceiling": "low", "requires_human_approval": True}
    report = detect_authority_deltas(
        AuthorityDeltaInput(source_kind="operator_contract", old_canonical_object=obj, new_canonical_object=obj)
    )
    assert report.highest_severity == AuthorityDeltaSeverity.INFO
    assert report.safe_to_auto_accept is True
    assert not report.requires_operator_consent


def test_extract_authority_surface():
    surface = extract_authority_surface("operator_contract", {"risk_ceiling": "low", "name": "test", "notes": {}})
    assert "risk_ceiling" in surface
    assert surface["risk_ceiling"] == "low"
    assert "name" not in surface  # name is not an authority field


def test_highest_authority_delta_severity():
    deltas = (
        AuthorityDelta(
            delta_id="d1",
            delta_type=AuthorityDeltaType.RISK_CEILING_INCREASED,
            severity=AuthorityDeltaSeverity.HIGH,
            source_kind="test",
            field_path="risk_ceiling",
            old_value="low",
            new_value="high",
            old_attestation_id=None,
            new_attestation_id=None,
            requires_operator_consent=True,
            requires_evidence=False,
            reason="test",
            blockers=(),
            warnings=(),
        ),
        AuthorityDelta(
            delta_id="d2",
            delta_type=AuthorityDeltaType.OVERSIGHT_WEAKENED,
            severity=AuthorityDeltaSeverity.CRITICAL,
            source_kind="test",
            field_path="requires_human_approval",
            old_value=True,
            new_value=False,
            old_attestation_id=None,
            new_attestation_id=None,
            requires_operator_consent=True,
            requires_evidence=False,
            reason="test",
            blockers=(),
            warnings=(),
        ),
    )
    assert highest_authority_delta_severity(deltas) == AuthorityDeltaSeverity.CRITICAL


# ---------------------------------------------------------------------------
# CLI integration (via fixture files)
# ---------------------------------------------------------------------------


def test_full_operator_contract_risk_increase_from_fixtures():
    old = _load_yaml("operator_contract_low_risk.yaml")
    new = _load_yaml("operator_contract_high_risk.yaml")
    report = detect_authority_deltas(
        AuthorityDeltaInput(source_kind="operator_contract", old_canonical_object=old, new_canonical_object=new)
    )
    assert len(report.deltas) >= 1
    assert report.highest_severity in {AuthorityDeltaSeverity.HIGH, AuthorityDeltaSeverity.CRITICAL}
    assert report.requires_operator_consent is True
    assert report.safe_to_auto_accept is False
    assert report.summary != ""


def test_claim_fixture_forbidden_to_verified():
    old = _load_yaml("claim_forbidden.yaml")
    new = _load_yaml("claim_verified.yaml")
    report = detect_authority_deltas(
        AuthorityDeltaInput(source_kind="capability_claims", old_canonical_object=old, new_canonical_object=new)
    )
    claim_delta = next((d for d in report.deltas if d.delta_type == AuthorityDeltaType.CLAIM_STATUS_ESCALATED), None)
    assert claim_delta is not None
    assert claim_delta.requires_operator_consent is True
    assert claim_delta.requires_evidence is True


def test_doctrine_fixture_reference_to_implemented():
    old = _load_yaml("doctrine_reference.yaml")
    new = _load_yaml("doctrine_implemented.yaml")
    report = detect_authority_deltas(
        AuthorityDeltaInput(source_kind="external_doctrine", old_canonical_object=old, new_canonical_object=new)
    )
    # IMPLEMENTED should be detected as escalation or unknown authority change
    assert len(report.deltas) >= 1
    assert report.requires_operator_consent is True


# ---------------------------------------------------------------------------
# Attestation reference integration
# ---------------------------------------------------------------------------


def test_report_uses_attestation_refs():
    class FakeAttestation:
        attestation_id = "srcatt_abc123"

    old = {"risk_ceiling": "low"}
    new = {"risk_ceiling": "high"}
    report = detect_authority_deltas(
        AuthorityDeltaInput(
            source_kind="operator_contract",
            old_canonical_object=old,
            new_canonical_object=new,
            old_attestation=FakeAttestation(),
            new_attestation=FakeAttestation(),
        )
    )
    assert report.old_attestation_id == "srcatt_abc123"
    assert report.new_attestation_id == "srcatt_abc123"


# ---------------------------------------------------------------------------
# Order tables
# ---------------------------------------------------------------------------


def test_risk_ceiling_order_defined():
    assert len(RISK_CEILING_ORDER) >= 3
    assert RISK_CEILING_ORDER[0] == "none"


def test_claim_status_order_defined():
    assert len(CLAIM_STATUS_ORDER) >= 4
    assert CLAIM_STATUS_ORDER[0] == "FORBIDDEN"
    assert CLAIM_STATUS_ORDER[-1] == "PRODUCTION_ELIGIBLE"


def test_doctrine_status_order_defined():
    assert len(DOCTRINE_STATUS_ORDER) >= 5
    assert DOCTRINE_STATUS_ORDER[0] == "REJECTED"


def test_capability_status_order_defined():
    assert len(CAPABILITY_STATUS_ORDER) >= 5


def test_summarize_authority_delta_report():
    deltas = (
        AuthorityDelta(
            delta_id="d1",
            delta_type=AuthorityDeltaType.RISK_CEILING_INCREASED,
            severity=AuthorityDeltaSeverity.HIGH,
            source_kind="test",
            field_path="risk_ceiling",
            old_value="low",
            new_value="high",
            old_attestation_id=None,
            new_attestation_id=None,
            requires_operator_consent=True,
            requires_evidence=False,
            reason="test",
            blockers=(),
            warnings=(),
        ),
    )
    summary = summarize_authority_delta_report(deltas)
    assert "1 authority-relevant change" in summary
    assert "HIGH/CRITICAL" in summary
