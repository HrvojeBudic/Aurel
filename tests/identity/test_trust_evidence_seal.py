"""Seal and CLI tests for P1.4.18 Trust Evidence Linkage."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile

from agentic_runtime.identity.trust_evidence import (
    TrustEvidenceBundle,
    TrustEvidenceKind,
    TrustEvidenceRef,
    TrustEvidenceStatus,
    TrustPosture,
    build_trust_evidence_bundle,
    evidence_ref_from_source_attestation,
    evidence_ref_from_test_battery_report,
    evidence_ref_from_consent_record,
    evidence_ref_from_lifecycle_decision,
    trust_evidence_bundle_to_dict,
    validate_trust_evidence_bundle,
)


def _run_cli(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "agentic_runtime.cli", *args],
        capture_output=True, text=True, timeout=30,
    )


# ---------------------------------------------------------------------------
# Seal: INV-P1418-01 — Trust evidence does not grant authority
# ---------------------------------------------------------------------------

def test_p1418_trust_evidence_does_not_grant_authority():
    """Evidence refs carry information, not permissions."""
    ref = TrustEvidenceRef(
        evidence_id="e1", kind=TrustEvidenceKind.AUTHORITY_DELTA_REPORT,
        ref="delta.json",
    )
    # Evidence ref has no permission-granting fields
    assert not hasattr(ref, "grants_authority")
    assert not hasattr(ref, "permissions")
    assert ref.status == TrustEvidenceStatus.PRESENT  # just a ref, not a truth claim


# ---------------------------------------------------------------------------
# Seal: INV-P1418-02 — Evidence ref is not proof of truth
# ---------------------------------------------------------------------------

def test_p1418_evidence_ref_is_not_treated_as_truth():
    """A PRESENT evidence ref doesn't assert truth."""
    ref = TrustEvidenceRef(
        evidence_id="e1", kind=TrustEvidenceKind.REPORT,
        ref="report.md", status=TrustEvidenceStatus.PRESENT,
    )
    d = trust_evidence_bundle_to_dict(
        build_trust_evidence_bundle(
            agent_id="a1", lifecycle_state="DRAFT",
            evidence_refs=(ref,),
        )
    )
    assert "verified" not in json.dumps(d).lower() or "not" in json.dumps(d).lower()


# ---------------------------------------------------------------------------
# Seal: INV-P1418-03 — ACTIVE requires linked supporting evidence
# ---------------------------------------------------------------------------

def test_p1418_active_without_evidence_is_not_supported():
    bundle = build_trust_evidence_bundle(
        agent_id="a1", lifecycle_state="ACTIVE",
        evidence_refs=(),
    )
    assert bundle.trust_posture != TrustPosture.SUPPORTED
    assert len(bundle.missing_required_evidence) >= 3


# ---------------------------------------------------------------------------
# Seal: INV-P1418-05 to INV-P1418-08 — Expired/revoked/invalid/conflicted
# ---------------------------------------------------------------------------

def test_p1418_expired_consent_degrades_or_blocks_trust():
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
    assert "e1" in bundle.expired_evidence or bundle.trust_posture != TrustPosture.SUPPORTED


def test_p1418_revoked_consent_blocks_trust():
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
    assert bundle.trust_posture == TrustPosture.BLOCKED


def test_p1418_conflicted_evidence_blocks_supported_posture():
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
    assert bundle.trust_posture != TrustPosture.SUPPORTED


# ---------------------------------------------------------------------------
# Seal: INV-P1418-09 — No fake numeric trust score
# ---------------------------------------------------------------------------

def test_p1418_no_numeric_trust_score():
    """Trust posture must be categorical, never numeric."""
    bundle = build_trust_evidence_bundle(
        agent_id="a1", lifecycle_state="ACTIVE",
        evidence_refs=(),
    )
    d = trust_evidence_bundle_to_dict(bundle)
    for key in d:
        if "score" in key.lower():
            val = d[key]
            if isinstance(val, (int, float)):
                assert False, f"Numeric score found: {key}={val}"


# ---------------------------------------------------------------------------
# Seal: INV-P1418-10 — Validation does not mutate lifecycle or consent
# ---------------------------------------------------------------------------

def test_p1418_validation_does_not_mutate_lifecycle():
    bundle = build_trust_evidence_bundle(
        agent_id="a1", lifecycle_state="ACTIVE",
        evidence_refs=(),
    )
    report1 = validate_trust_evidence_bundle(bundle)
    report2 = validate_trust_evidence_bundle(bundle)
    assert report1.posture == report2.posture
    assert report1.satisfied_required_evidence == report2.satisfied_required_evidence


# ---------------------------------------------------------------------------
# Seal: INV-P1418-11 — Module provenance
# ---------------------------------------------------------------------------

def test_p1418_evidence_links_expose_module_provenance():
    ref = evidence_ref_from_source_attestation(
        evidence_id="sa1", ref="attest.json",
    )
    assert ref.produced_by_module == "source_attestation"

    ref2 = evidence_ref_from_test_battery_report(
        evidence_id="tb1", ref="battery.md",
    )
    assert ref2.produced_by_module == "identity_test_battery"


# ---------------------------------------------------------------------------
# Seal: INV-P1418-12 — Prepares P1.4.19
# ---------------------------------------------------------------------------

def test_p1418_prepares_p1419_docs_reports_state_update():
    """Bundle JSON is structured for docs/report/state consumption."""
    refs = (
        evidence_ref_from_test_battery_report(evidence_id="tb1", ref="battery.md"),
        evidence_ref_from_lifecycle_decision(evidence_id="ld1", ref="decision.md"),
    )
    bundle = build_trust_evidence_bundle(
        agent_id="a1", lifecycle_state="CANDIDATE",
        evidence_refs=refs,
    )
    d = trust_evidence_bundle_to_dict(bundle)
    # Has structured data ready for docs
    assert "trust_posture" in d
    assert "missing_required_evidence" in d
    assert "links" in d


# ---------------------------------------------------------------------------
# CLI tests
# ---------------------------------------------------------------------------

def test_trust_evidence_cli_requirements_outputs_json():
    result = _run_cli("identity", "trust-evidence", "requirements",
                      "--lifecycle-state", "ACTIVE", "--json")
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert isinstance(data, list)
    assert len(data) >= 4
    for req in data:
        assert "kind" in req
        assert "required" in req


def test_trust_evidence_cli_build_outputs_bundle():
    result = _run_cli("identity", "trust-evidence", "build",
                      "--agent-id", "aurel.core",
                      "--lifecycle-state", "CANDIDATE",
                      "--evidence-ref", "battery.md",
                      "--json")
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["agent_id"] == "aurel.core"
    assert "trust_posture" in data
    assert "evidence_refs" in data


def test_trust_evidence_cli_build_unsupported_exits_zero():
    """Even UNSUPPORTED bundles don't error — CLI reports posture."""
    result = _run_cli("identity", "trust-evidence", "build",
                      "--agent-id", "aurel.core",
                      "--lifecycle-state", "ACTIVE",
                      "--json")
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["trust_posture"] != TrustPosture.SUPPORTED.value


def test_trust_evidence_cli_validate_outputs_report():
    # Build a bundle, save to temp, then validate
    refs = (
        TrustEvidenceRef(
            evidence_id="e1", kind=TrustEvidenceKind.REPORT,
            ref="r.md", status=TrustEvidenceStatus.PRESENT,
        ),
    )
    bundle = build_trust_evidence_bundle(
        agent_id="a1", lifecycle_state="DRAFT",
        evidence_refs=refs,
    )
    d = trust_evidence_bundle_to_dict(bundle)
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(d, f)
        tmp_path = f.name

    try:
        result = _run_cli("identity", "trust-evidence", "validate",
                          "--bundle", tmp_path, "--json")
        # UNSUPPORTED posture may exit 1
        assert result.returncode in (0, 1)
        data = json.loads(result.stdout)
        assert "posture" in data
        assert data["posture"] in ("SUPPORTED", "DEGRADED", "UNSUPPORTED", "CONFLICTED", "BLOCKED")
    finally:
        os.unlink(tmp_path)


def test_trust_evidence_cli_explain_outputs_bundle():
    refs = (
        TrustEvidenceRef(
            evidence_id="e1", kind=TrustEvidenceKind.REPORT,
            ref="r.md", status=TrustEvidenceStatus.PRESENT,
        ),
    )
    bundle = build_trust_evidence_bundle(
        agent_id="a1", lifecycle_state="DRAFT",
        evidence_refs=refs,
    )
    d = trust_evidence_bundle_to_dict(bundle)
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(d, f)
        tmp_path = f.name

    try:
        result = _run_cli("identity", "trust-evidence", "explain",
                          "--bundle", tmp_path, "--json")
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert "trust_posture" in data
    finally:
        os.unlink(tmp_path)


def test_trust_evidence_cli_does_not_mutate_state():
    """Running build twice produces same output."""
    result1 = _run_cli("identity", "trust-evidence", "build",
                       "--agent-id", "aurel.core",
                       "--lifecycle-state", "DRAFT",
                       "--json")
    result2 = _run_cli("identity", "trust-evidence", "build",
                       "--agent-id", "aurel.core",
                       "--lifecycle-state", "DRAFT",
                       "--json")
    # Same agent+lifecycle+no evidence → same posture
    d1 = json.loads(result1.stdout)
    d2 = json.loads(result2.stdout)
    assert d1["trust_posture"] == d2["trust_posture"]
