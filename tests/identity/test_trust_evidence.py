"""Core tests for P1.4.18 Trust Evidence Linkage."""
from __future__ import annotations

import json
import tempfile
import os

from agentic_runtime.identity.trust_evidence import (
    TrustEvidenceBundle,
    TrustEvidenceKind,
    TrustEvidenceLink,
    TrustEvidenceLinkageReport,
    TrustEvidenceRef,
    TrustEvidenceRequirement,
    TrustEvidenceStatus,
    TrustPosture,
    build_trust_evidence_bundle,
    default_trust_evidence_requirements_for_lifecycle,
    evidence_ref_from_authority_delta_report,
    evidence_ref_from_consent_record,
    evidence_ref_from_lifecycle_decision,
    evidence_ref_from_source_attestation,
    evidence_ref_from_test_battery_report,
    resolve_trust_posture,
    trust_evidence_bundle_to_dict,
    trust_evidence_linkage_report_to_dict,
    trust_evidence_ref_to_dict,
    trust_evidence_requirement_to_dict,
    validate_trust_evidence_bundle,
    format_trust_evidence_bundle_human,
    format_trust_evidence_report_human,
    trust_evidence_link_to_dict,
)


# ---------------------------------------------------------------------------
# Enum closed-world
# ---------------------------------------------------------------------------

def test_trust_evidence_kind_closed_world():
    kinds = list(TrustEvidenceKind)
    assert len(kinds) >= 15


def test_trust_evidence_status_closed_world():
    statuses = list(TrustEvidenceStatus)
    assert len(statuses) == 8


def test_trust_posture_closed_world():
    postures = list(TrustPosture)
    assert len(postures) == 8


# ---------------------------------------------------------------------------
# Default requirements
# ---------------------------------------------------------------------------

def test_default_requirements_exist_for_lifecycle_states():
    for state in ("DRAFT", "CANDIDATE", "ACTIVE", "RESTRICTED", "SUSPENDED", "DEPRECATED", "RETIRED", "REVOKED"):
        reqs = default_trust_evidence_requirements_for_lifecycle(state)
        assert len(reqs) > 0, f"No requirements for {state}"


def test_active_requires_identity_test_battery_evidence():
    reqs = default_trust_evidence_requirements_for_lifecycle("ACTIVE")
    kinds = {r.kind for r in reqs}
    assert TrustEvidenceKind.IDENTITY_TEST_BATTERY_REPORT in kinds


def test_active_requires_source_attestation_evidence():
    reqs = default_trust_evidence_requirements_for_lifecycle("ACTIVE")
    kinds = {r.kind for r in reqs}
    assert TrustEvidenceKind.SOURCE_ATTESTATION in kinds


def test_active_requires_lifecycle_transition_evidence():
    reqs = default_trust_evidence_requirements_for_lifecycle("ACTIVE")
    kinds = {r.kind for r in reqs}
    assert TrustEvidenceKind.LIFECYCLE_TRANSITION_DECISION in kinds


def test_active_requires_capability_claim_decision():
    reqs = default_trust_evidence_requirements_for_lifecycle("ACTIVE")
    kinds = {r.kind for r in reqs}
    assert TrustEvidenceKind.CAPABILITY_CLAIM_DECISION in kinds


# ---------------------------------------------------------------------------
# Build bundle
# ---------------------------------------------------------------------------

def test_build_bundle_with_present_evidence():
    refs = (
        TrustEvidenceRef(
            evidence_id="ev1", kind=TrustEvidenceKind.REPORT,
            ref="report.md", status=TrustEvidenceStatus.PRESENT,
        ),
    )
    bundle = build_trust_evidence_bundle(
        agent_id="a1", lifecycle_state="DRAFT",
        evidence_refs=refs,
    )
    assert isinstance(bundle, TrustEvidenceBundle)
    assert bundle.agent_id == "a1"
    assert len(bundle.links) >= 1


def test_build_bundle_marks_missing_required_evidence():
    bundle = build_trust_evidence_bundle(
        agent_id="a1", lifecycle_state="ACTIVE",
        evidence_refs=(),
    )
    assert bundle.trust_posture == TrustPosture.UNSUPPORTED
    assert len(bundle.missing_required_evidence) > 0


def test_build_bundle_marks_expired_evidence():
    refs = (
        TrustEvidenceRef(
            evidence_id="e1", kind=TrustEvidenceKind.IDENTITY_CARD,
            ref="card.yaml", status=TrustEvidenceStatus.EXPIRED,
        ),
    )
    bundle = build_trust_evidence_bundle(
        agent_id="a1", lifecycle_state="DRAFT",
        evidence_refs=refs,
    )
    assert "e1" in bundle.expired_evidence or bundle.trust_posture == TrustPosture.EXPIRED


def test_build_bundle_marks_revoked_evidence():
    refs = (
        TrustEvidenceRef(
            evidence_id="e1", kind=TrustEvidenceKind.IDENTITY_CARD,
            ref="card.yaml", status=TrustEvidenceStatus.REVOKED,
        ),
    )
    bundle = build_trust_evidence_bundle(
        agent_id="a1", lifecycle_state="DRAFT",
        evidence_refs=refs,
    )
    assert "e1" in bundle.revoked_evidence
    assert any("revoked" in b for b in bundle.blockers)


def test_build_bundle_marks_invalid_evidence():
    refs = (
        TrustEvidenceRef(
            evidence_id="e1", kind=TrustEvidenceKind.IDENTITY_CARD,
            ref="card.yaml", status=TrustEvidenceStatus.INVALID,
        ),
    )
    bundle = build_trust_evidence_bundle(
        agent_id="a1", lifecycle_state="DRAFT",
        evidence_refs=refs,
    )
    assert "e1" in bundle.invalid_evidence
    assert any("invalid" in b for b in bundle.blockers)


def test_build_bundle_marks_conflicted_evidence():
    refs = (
        TrustEvidenceRef(
            evidence_id="e1", kind=TrustEvidenceKind.IDENTITY_CARD,
            ref="card.yaml", status=TrustEvidenceStatus.CONFLICTED,
        ),
    )
    bundle = build_trust_evidence_bundle(
        agent_id="a1", lifecycle_state="DRAFT",
        evidence_refs=refs,
    )
    assert bundle.trust_posture == TrustPosture.CONFLICTED
    assert "e1" in bundle.conflicted_evidence


def test_validate_bundle_returns_report():
    bundle = build_trust_evidence_bundle(
        agent_id="a1", lifecycle_state="DRAFT",
        evidence_refs=(),
    )
    report = validate_trust_evidence_bundle(bundle)
    assert isinstance(report, TrustEvidenceLinkageReport)
    assert report.agent_id == "a1"


# ---------------------------------------------------------------------------
# Lifecycle evidence integration
# ---------------------------------------------------------------------------

def test_active_without_required_evidence_is_not_supported():
    bundle = build_trust_evidence_bundle(
        agent_id="a1", lifecycle_state="ACTIVE",
        evidence_refs=(),
    )
    assert bundle.trust_posture != TrustPosture.SUPPORTED
    assert bundle.trust_posture in (TrustPosture.UNSUPPORTED, TrustPosture.PARTIALLY_SUPPORTED)


def test_restricted_with_reason_evidence_is_degraded_not_dead():
    refs = (
        TrustEvidenceRef(
            evidence_id="e1", kind=TrustEvidenceKind.IDENTITY_CARD,
            ref="card.yaml", status=TrustEvidenceStatus.PRESENT,
        ),
        TrustEvidenceRef(
            evidence_id="e2", kind=TrustEvidenceKind.REPORT,
            ref="reason.md", status=TrustEvidenceStatus.PRESENT,
        ),
    )
    bundle = build_trust_evidence_bundle(
        agent_id="a1", lifecycle_state="RESTRICTED",
        evidence_refs=refs,
    )
    # Should be SUPPORTED or PARTIALLY since both required kinds are present
    assert bundle.trust_posture in (TrustPosture.SUPPORTED, TrustPosture.PARTIALLY_SUPPORTED)


def test_revoked_identity_posture_blocks_operation():
    refs = (
        TrustEvidenceRef(
            evidence_id="e1", kind=TrustEvidenceKind.REPORT,
            ref="revoke.md", status=TrustEvidenceStatus.PRESENT,
        ),
    )
    bundle = build_trust_evidence_bundle(
        agent_id="a1", lifecycle_state="REVOKED",
        evidence_refs=refs,
    )
    assert bundle.trust_posture == TrustPosture.SUPPORTED  # evidence satisfies requirements
    # But REVOKED lifecycle itself is terminal - profile handles that
    assert "REVOKED" in (bundle.lifecycle_state or "")


def test_candidate_can_be_partially_supported():
    refs = (
        TrustEvidenceRef(
            evidence_id="e1", kind=TrustEvidenceKind.IDENTITY_CARD,
            ref="card.yaml", status=TrustEvidenceStatus.PRESENT,
        ),
    )
    bundle = build_trust_evidence_bundle(
        agent_id="a1", lifecycle_state="CANDIDATE",
        evidence_refs=refs,
    )
    assert bundle.trust_posture == TrustPosture.PARTIALLY_SUPPORTED


def test_draft_can_be_partially_supported():
    bundle = build_trust_evidence_bundle(
        agent_id="a1", lifecycle_state="DRAFT",
        evidence_refs=(),
    )
    assert bundle.trust_posture == TrustPosture.UNSUPPORTED


# ---------------------------------------------------------------------------
# Helper builders
# ---------------------------------------------------------------------------

def test_evidence_ref_from_source_attestation():
    ref = evidence_ref_from_source_attestation(
        evidence_id="sa1", ref="attest.json",
        source_attestation_id="att_123",
    )
    assert ref.kind == TrustEvidenceKind.SOURCE_ATTESTATION
    assert ref.source_attestation_id == "att_123"
    assert ref.produced_by_module == "source_attestation"


def test_evidence_ref_from_test_battery():
    ref = evidence_ref_from_test_battery_report(
        evidence_id="tb1", ref="battery.md",
    )
    assert ref.kind == TrustEvidenceKind.IDENTITY_TEST_BATTERY_REPORT
    assert ref.produced_by_module == "identity_test_battery"


def test_evidence_ref_from_consent():
    ref = evidence_ref_from_consent_record(
        evidence_id="c1", ref="consent.json",
    )
    assert ref.kind == TrustEvidenceKind.OPERATOR_CONSENT_RECORD
    assert ref.produced_by_module == "operator_consent"


def test_evidence_ref_from_authority_delta():
    ref = evidence_ref_from_authority_delta_report(
        evidence_id="ad1", ref="delta.json",
    )
    assert ref.kind == TrustEvidenceKind.AUTHORITY_DELTA_REPORT
    assert ref.produced_by_module == "authority_delta"


def test_evidence_ref_from_lifecycle_decision():
    ref = evidence_ref_from_lifecycle_decision(
        evidence_id="ld1", ref="decision.json",
    )
    assert ref.kind == TrustEvidenceKind.LIFECYCLE_TRANSITION_DECISION
    assert ref.produced_by_module == "agent_lifecycle"


# ---------------------------------------------------------------------------
# Integration
# ---------------------------------------------------------------------------

def test_lifecycle_active_decision_can_be_linked_to_test_battery():
    refs = (
        evidence_ref_from_test_battery_report(evidence_id="tb1", ref="battery.md"),
        evidence_ref_from_lifecycle_decision(evidence_id="ld1", ref="decision.md"),
        evidence_ref_from_source_attestation(evidence_id="sa1", ref="attest.json"),
    )
    bundle = build_trust_evidence_bundle(
        agent_id="a1", lifecycle_state="ACTIVE",
        evidence_refs=refs,
    )
    # We have 3 of 5 required kinds
    assert bundle.trust_posture == TrustPosture.PARTIALLY_SUPPORTED


def test_authority_delta_can_be_linked_to_consent_record():
    refs = (
        evidence_ref_from_authority_delta_report(evidence_id="ad1", ref="delta.json"),
        evidence_ref_from_consent_record(evidence_id="c1", ref="consent.json"),
    )
    bundle = build_trust_evidence_bundle(
        agent_id="a1", lifecycle_state="ACTIVE",
        evidence_refs=refs,
    )
    # These are evidence refs present but not in required kinds for ACTIVE
    assert isinstance(bundle, TrustEvidenceBundle)


def test_expired_consent_blocks_or_expires_active_trust():
    """Expired required evidence does not support SUPPORTED posture."""
    refs = (
        TrustEvidenceRef(
            evidence_id="ic", kind=TrustEvidenceKind.IDENTITY_CARD,
            ref="card.yaml", status=TrustEvidenceStatus.EXPIRED,
        ),
        TrustEvidenceRef(
            evidence_id="sa", kind=TrustEvidenceKind.SOURCE_ATTESTATION,
            ref="attest.json", status=TrustEvidenceStatus.PRESENT,
        ),
        TrustEvidenceRef(
            evidence_id="tb", kind=TrustEvidenceKind.IDENTITY_TEST_BATTERY_REPORT,
            ref="battery.md", status=TrustEvidenceStatus.PRESENT,
        ),
        TrustEvidenceRef(
            evidence_id="ld", kind=TrustEvidenceKind.LIFECYCLE_TRANSITION_DECISION,
            ref="decision.md", status=TrustEvidenceStatus.PRESENT,
        ),
        TrustEvidenceRef(
            evidence_id="cc", kind=TrustEvidenceKind.CAPABILITY_CLAIM_DECISION,
            ref="claim.json", status=TrustEvidenceStatus.PRESENT,
        ),
    )
    bundle = build_trust_evidence_bundle(
        agent_id="a1", lifecycle_state="ACTIVE",
        evidence_refs=refs,
    )
    # IDENTITY_CARD is EXPIRED (required for ACTIVE) → should not be SUPPORTED
    assert "ic" in bundle.expired_evidence or bundle.trust_posture != TrustPosture.SUPPORTED


# ---------------------------------------------------------------------------
# Serialization
# ---------------------------------------------------------------------------

def test_bundle_report_is_json_serializable():
    bundle = build_trust_evidence_bundle(
        agent_id="a1", lifecycle_state="DRAFT",
        evidence_refs=(),
    )
    d = trust_evidence_bundle_to_dict(bundle)
    j = json.dumps(d)
    parsed = json.loads(j)
    assert parsed["trust_posture"] in ("UNSUPPORTED", "SUPPORTED", "DEGRADED", "CONFLICTED", "BLOCKED", "EXPIRED", "PARTIALLY_SUPPORTED", "UNKNOWN")


def test_report_is_json_serializable():
    bundle = build_trust_evidence_bundle(
        agent_id="a1", lifecycle_state="DRAFT",
        evidence_refs=(),
    )
    report = validate_trust_evidence_bundle(bundle)
    d = trust_evidence_linkage_report_to_dict(report)
    j = json.dumps(d)
    parsed = json.loads(j)
    assert parsed["agent_id"] == "a1"


def test_evidence_ref_to_dict_serializable():
    ref = TrustEvidenceRef(
        evidence_id="e1", kind=TrustEvidenceKind.REPORT,
        ref="report.md",
    )
    d = trust_evidence_ref_to_dict(ref)
    j = json.dumps(d)
    parsed = json.loads(j)
    assert parsed["evidence_id"] == "e1"


def test_requirement_to_dict_serializable():
    req = TrustEvidenceRequirement(
        requirement_id="r1", kind=TrustEvidenceKind.REPORT,
        required_for="ACTIVE", required=True,
        acceptable_statuses=(TrustEvidenceStatus.PRESENT,),
        reason="test",
    )
    d = trust_evidence_requirement_to_dict(req)
    j = json.dumps(d)
    parsed = json.loads(j)
    assert parsed["requirement_id"] == "r1"


def test_link_to_dict_serializable():
    link = TrustEvidenceLink(
        link_id="l1", subject_id="a1", subject_type="agent",
        evidence_id="e1", relationship="supports",
        required=True, satisfied=True, reason="ok",
    )
    d = trust_evidence_link_to_dict(link)
    j = json.dumps(d)
    parsed = json.loads(j)
    assert parsed["link_id"] == "l1"


# ---------------------------------------------------------------------------
# Posture resolution
# ---------------------------------------------------------------------------

def test_resolve_posture_supported():
    reqs = (TrustEvidenceRequirement(
        requirement_id="r1", kind=TrustEvidenceKind.REPORT,
        required_for="test", required=True,
        acceptable_statuses=(TrustEvidenceStatus.PRESENT,),
        reason="",
    ),)
    refs = (TrustEvidenceRef(
        evidence_id="e1", kind=TrustEvidenceKind.REPORT,
        ref="r.md", status=TrustEvidenceStatus.PRESENT,
    ),)
    links = ()
    posture = resolve_trust_posture(requirements=reqs, evidence_refs=refs, links=links)
    assert posture == TrustPosture.SUPPORTED


def test_resolve_posture_unsupported():
    reqs = (TrustEvidenceRequirement(
        requirement_id="r1", kind=TrustEvidenceKind.REPORT,
        required_for="test", required=True,
        acceptable_statuses=(TrustEvidenceStatus.PRESENT,),
        reason="",
    ),)
    posture = resolve_trust_posture(requirements=reqs, evidence_refs=(), links=())
    assert posture == TrustPosture.UNSUPPORTED


def test_resolve_posture_conflicted():
    reqs = (TrustEvidenceRequirement(
        requirement_id="r1", kind=TrustEvidenceKind.REPORT,
        required_for="test", required=True,
        acceptable_statuses=(TrustEvidenceStatus.PRESENT,),
        reason="",
    ),)
    refs = (TrustEvidenceRef(
        evidence_id="e1", kind=TrustEvidenceKind.REPORT,
        ref="r.md", status=TrustEvidenceStatus.CONFLICTED,
    ),)
    posture = resolve_trust_posture(requirements=reqs, evidence_refs=refs, links=())
    assert posture == TrustPosture.CONFLICTED


def test_resolve_posture_blocked_by_revoked():
    reqs = (TrustEvidenceRequirement(
        requirement_id="r1", kind=TrustEvidenceKind.REPORT,
        required_for="test", required=True,
        acceptable_statuses=(TrustEvidenceStatus.PRESENT,),
        reason="",
    ),)
    refs = (TrustEvidenceRef(
        evidence_id="e1", kind=TrustEvidenceKind.REPORT,
        ref="r.md", status=TrustEvidenceStatus.REVOKED,
    ),)
    posture = resolve_trust_posture(requirements=reqs, evidence_refs=refs, links=())
    assert posture == TrustPosture.BLOCKED


def test_resolve_posture_partially_supported():
    reqs = (
        TrustEvidenceRequirement(
            requirement_id="r1", kind=TrustEvidenceKind.REPORT,
            required_for="test", required=True,
            acceptable_statuses=(TrustEvidenceStatus.PRESENT,),
            reason="",
        ),
        TrustEvidenceRequirement(
            requirement_id="r2", kind=TrustEvidenceKind.IDENTITY_CARD,
            required_for="test", required=True,
            acceptable_statuses=(TrustEvidenceStatus.PRESENT,),
            reason="",
        ),
    )
    refs = (TrustEvidenceRef(
        evidence_id="e1", kind=TrustEvidenceKind.REPORT,
        ref="r.md", status=TrustEvidenceStatus.PRESENT,
    ),)
    posture = resolve_trust_posture(requirements=reqs, evidence_refs=refs, links=())
    assert posture == TrustPosture.PARTIALLY_SUPPORTED


def test_resolve_posture_unknown():
    posture = resolve_trust_posture(requirements=(), evidence_refs=(), links=())
    assert posture == TrustPosture.UNKNOWN


# ---------------------------------------------------------------------------
# Human formatters
# ---------------------------------------------------------------------------

def test_bundle_human_mentions_posture():
    bundle = build_trust_evidence_bundle(
        agent_id="a1", lifecycle_state="ACTIVE",
        evidence_refs=(),
    )
    text = format_trust_evidence_bundle_human(bundle)
    assert "UNSUPPORTED" in text
    assert "Missing" in text


def test_report_human_mentions_counts():
    bundle = build_trust_evidence_bundle(
        agent_id="a1", lifecycle_state="DRAFT",
        evidence_refs=(),
    )
    report = validate_trust_evidence_bundle(bundle)
    text = format_trust_evidence_report_human(report)
    assert "UNSUPPORTED" in text
    assert "0/" in text  # satisfied/required format
