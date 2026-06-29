"""P1.4.10 — Capability Claim Boundary Engine tests.

Covers: unit tests, next-level tests, CLI tests, seal tests.
"""
from __future__ import annotations

import json
import subprocess
import sys

import pytest

from tests.repo_root import REPO_ROOT
from agentic_runtime.identity.capability_claims import (
    CapabilityClaim,
    CapabilityClaimDecision,
    CapabilityClaimStatus,
    CapabilityClaimType,
    ClaimEvidenceContext,
    _EVIDENCE_ORDER as _EVIDENCE_ORDER,
    _evidence_rank,
    _safe_by_status,
    _status_for_evidence,
    _build_default_registry,
    capability_claim_decision_to_dict,
    evaluate_capability_claim,
    get_claim,
    get_claim_registry,
    list_claims,
    rewrite_capability_claim_safely,
    rewrite_claim_text_safely,
)

# ── Fixtures ──────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def _clear_registry():
    """Ensure clean registry per test."""
    from agentic_runtime.identity import capability_claims
    capability_claims._CLAIM_REGISTRY.clear()
    yield
    capability_claims._CLAIM_REGISTRY.clear()


def _ctx() -> ClaimEvidenceContext:
    return ClaimEvidenceContext()


# ── Unit: Domain types ────────────────────────────────────────────────────


def test_capability_claim_status_values():
    assert CapabilityClaimStatus.FORBIDDEN.value == "FORBIDDEN"
    assert CapabilityClaimStatus.ROADMAP_ONLY.value == "ROADMAP_ONLY"
    assert CapabilityClaimStatus.PRODUCTION_ELIGIBLE.value == "PRODUCTION_ELIGIBLE"
    assert len(CapabilityClaimStatus) == 7


def test_capability_claim_type_values():
    assert CapabilityClaimType.AUTONOMY.value == "autonomy"
    assert CapabilityClaimType.SELF_IMPROVEMENT.value == "self_improvement"
    assert CapabilityClaimType.PRODUCTION_READINESS.value == "production_readiness"
    assert len(CapabilityClaimType) == 11


def test_claim_decision_is_json_serializable():
    d = CapabilityClaimDecision(
        claim_id="test",
        allowed=False,
        allowed_status=CapabilityClaimStatus.FORBIDDEN,
        original_claim_text="test",
        safe_claim_text="safe test",
        blockers=("block1",),
        warnings=("warn1",),
        required_evidence=("ev1",),
        current_evidence=(),
        reason="because",
    )
    jd = capability_claim_decision_to_dict(d)
    assert json.loads(json.dumps(jd)) == jd
    assert jd["claim_id"] == "test"
    assert jd["blockers"] == ["block1"]


def test_capability_claim_frozen():
    claim = CapabilityClaim(
        claim_id="test", claim_text="text", claim_type=CapabilityClaimType.AUTONOMY,
    )
    with pytest.raises(Exception):
        claim.claim_text = "new"  # type: ignore[misc]


# ── Unit: Evidence ranking ────────────────────────────────────────────────


def test_evidence_rank_none_is_zero():
    assert _evidence_rank(None) == 0


def test_evidence_rank_roadmap_only():
    assert _evidence_rank("roadmap_only") == 1


def test_evidence_rank_verified():
    assert _evidence_rank("verified") == 6


def test_evidence_rank_production_eligible():
    assert _evidence_rank("production_eligible") == 7


def test_status_for_evidence():
    assert _status_for_evidence("verified") == CapabilityClaimStatus.VERIFIED
    assert _status_for_evidence("implemented") == CapabilityClaimStatus.PARTIALLY_VERIFIED
    assert _status_for_evidence(None) == CapabilityClaimStatus.FORBIDDEN


# ── Unit: Registry ────────────────────────────────────────────────────────


def test_registry_has_all_expected_claims():
    reg = get_claim_registry()
    expected_ids = {
        "agent_identity_card", "autonomy_scale_engine", "measured_autonomy_score",
        "action_scoped_autonomy_evaluation", "global_autonomy", "self_improvement",
        "production_ready_agentic_os", "abos_roadmap_layer", "abos_deployment_layer",
        "aether_roadmap_layer", "aether_multimodal_intelligence",
        "secure_sandboxing", "procedural_skill_library", "verified_memory",
    }
    assert set(reg.keys()) == expected_ids


def test_list_claims_returns_all():
    claims = list_claims()
    assert len(claims) == 14


def test_get_claim_unknown():
    assert get_claim("nonexistent") is None


# ── Basic claim evaluation tests ──────────────────────────────────────────


def test_global_autonomy_claim_is_forbidden():
    claim = get_claim("global_autonomy")
    d = evaluate_capability_claim(claim, _ctx())
    assert not d.allowed
    assert d.allowed_status == CapabilityClaimStatus.FORBIDDEN
    assert d.reason


def test_self_improvement_claim_is_blocked():
    claim = get_claim("self_improvement")
    d = evaluate_capability_claim(claim, _ctx())
    assert not d.allowed, f"Expected blocked, got {d.allowed_status.value}"
    assert d.allowed_status in (CapabilityClaimStatus.FORBIDDEN, CapabilityClaimStatus.ROADMAP_ONLY)


def test_production_ready_claim_is_forbidden():
    claim = get_claim("production_ready_agentic_os")
    d = evaluate_capability_claim(claim, _ctx())
    assert not d.allowed
    assert d.allowed_status == CapabilityClaimStatus.FORBIDDEN


def test_abos_deployment_claim_is_roadmap_only():
    claim = get_claim("abos_deployment_layer")
    d = evaluate_capability_claim(claim, _ctx())
    assert not d.allowed
    assert d.allowed_status in (CapabilityClaimStatus.FORBIDDEN, CapabilityClaimStatus.ROADMAP_ONLY)


def test_aether_multimodal_claim_is_roadmap_only():
    claim = get_claim("aether_multimodal_intelligence")
    d = evaluate_capability_claim(claim, _ctx())
    assert not d.allowed
    assert d.allowed_status in (CapabilityClaimStatus.FORBIDDEN, CapabilityClaimStatus.ROADMAP_ONLY)


def test_action_scoped_autonomy_claim_is_allowed_after_p148_p149():
    claim = get_claim("action_scoped_autonomy_evaluation")
    d = evaluate_capability_claim(claim, _ctx())
    assert d.allowed, f"Expected allowed but got {d.allowed_status.value}"
    assert d.allowed_status in (CapabilityClaimStatus.PARTIALLY_VERIFIED, CapabilityClaimStatus.VERIFIED)


def test_claim_decision_has_reason():
    claim = get_claim("global_autonomy")
    d = evaluate_capability_claim(claim, _ctx())
    assert d.reason, "Decision must have a reason"


def test_claim_decision_has_blockers_when_blocked():
    claim = get_claim("self_improvement")
    d = evaluate_capability_claim(claim, _ctx())
    assert d.blockers, "Blocked claims must have blockers"


# ── Next-level tests ──────────────────────────────────────────────────────


def test_claim_cannot_exceed_evidence_level():
    """A claim with no evidence cannot be partially_verified."""
    claim = CapabilityClaim(
        claim_id="test", claim_text="test", claim_type=CapabilityClaimType.AUTONOMY,
        required_evidence_level="verified",
        current_evidence_level=None,
    )
    d = evaluate_capability_claim(claim, _ctx())
    assert not d.allowed
    assert d.allowed_status == CapabilityClaimStatus.FORBIDDEN


def test_roadmap_status_is_not_implementation():
    """Roadmap-only evidence cannot support a verified claim."""
    claim = CapabilityClaim(
        claim_id="test", claim_text="test", claim_type=CapabilityClaimType.BUSINESS,
        required_evidence_level="verified",
        current_evidence_level="roadmap_only",
    )
    d = evaluate_capability_claim(claim, _ctx())
    assert not d.allowed
    assert d.allowed_status == CapabilityClaimStatus.ROADMAP_ONLY


def test_planned_capability_cannot_support_verified_claim():
    claim = CapabilityClaim(
        claim_id="test", claim_text="test", claim_type=CapabilityClaimType.AUTONOMY,
        required_evidence_level="verified",
        current_evidence_level=None,
    )
    d = evaluate_capability_claim(claim, _ctx())
    assert d.allowed_status == CapabilityClaimStatus.FORBIDDEN


def test_safe_claim_rewrite_preserves_truth():
    """Safe rewrite must not lie."""
    claim = get_claim("global_autonomy")
    safe = rewrite_capability_claim_safely(claim, CapabilityClaimStatus.FORBIDDEN)
    assert safe is not None
    assert "action-scoped autonomy evaluation" in safe
    assert "fail-closed" in safe
    # Must not claim "autonomous" in the safe rewrite
    assert "is autonomous" not in safe.lower()


def test_safe_claim_rewrite_does_not_create_marketing_spin():
    """Safe rewrite must not be 'almost' marketing spin."""
    claim = get_claim("self_improvement")
    safe = rewrite_capability_claim_safely(claim, CapabilityClaimStatus.ROADMAP_ONLY)
    assert safe is not None
    assert "almost" not in safe.lower()
    assert "nearly" not in safe.lower()
    assert "roadmap" in safe.lower() or "future" in safe.lower()


def test_production_claim_requires_seal_evidence():
    claim = get_claim("production_ready_agentic_os")
    d = evaluate_capability_claim(claim, _ctx())
    assert d.allowed_status == CapabilityClaimStatus.FORBIDDEN
    assert "p20_seal" in claim.required_seals


def test_self_improvement_requires_verified_promotion_evidence():
    claim = get_claim("self_improvement")
    assert "verified_skill_promotion" in claim.required_seals
    assert "regression_evidence" in claim.required_seals


def test_agent_identity_card_claim_evaluates():
    claim = get_claim("agent_identity_card")
    d = evaluate_capability_claim(claim, _ctx())
    assert d.allowed, f"Expected allowed, got {d.allowed_status.value}"


def test_abos_roadmap_layer_is_roadmap_status():
    claim = get_claim("abos_roadmap_layer")
    d = evaluate_capability_claim(claim, _ctx())
    # Roadmap-only claims are not allowed as-is, but status is ROADMAP_ONLY
    assert not d.allowed
    assert d.allowed_status == CapabilityClaimStatus.ROADMAP_ONLY


def test_aether_roadmap_layer_is_roadmap_status():
    claim = get_claim("aether_roadmap_layer")
    d = evaluate_capability_claim(claim, _ctx())
    assert not d.allowed
    assert d.allowed_status == CapabilityClaimStatus.ROADMAP_ONLY


def test_secure_sandboxing_is_roadmap_only():
    claim = get_claim("secure_sandboxing")
    d = evaluate_capability_claim(claim, _ctx())
    assert not d.allowed
    assert d.allowed_status == CapabilityClaimStatus.ROADMAP_ONLY


def test_rewrite_claim_text_safely_known_claims():
    safe = rewrite_claim_text_safely("Aurel is autonomous.")
    assert safe is not None
    assert "action-scoped" in safe

    safe2 = rewrite_claim_text_safely("Aurel is self-improving.")
    assert safe2 is not None
    assert "roadmap" in safe2.lower()


def test_rewrite_claim_text_safely_unknown_returns_none():
    assert rewrite_claim_text_safely("Unknown claim about something.") is None


def test_evaluate_ad_hoc_claim():
    claim = CapabilityClaim(
        claim_id="ad-hoc", claim_text="Test claim", claim_type=CapabilityClaimType.AUTONOMY,
    )
    d = evaluate_capability_claim(claim, _ctx())
    assert d.claim_id == "ad-hoc"
    # No evidence = FORBIDDEN
    assert not d.allowed


# ── Seal tests ────────────────────────────────────────────────────────────


def test_p1410_blocks_global_autonomy_overclaim():
    claim = get_claim("global_autonomy")
    d = evaluate_capability_claim(claim, _ctx())
    assert not d.allowed, "P1.4.10 must block global autonomy overclaim"
    assert d.allowed_status == CapabilityClaimStatus.FORBIDDEN


def test_p1410_blocks_self_improvement_overclaim():
    claim = get_claim("self_improvement")
    d = evaluate_capability_claim(claim, _ctx())
    assert not d.allowed, "P1.4.10 must block self-improvement overclaim"
    assert d.allowed_status in (CapabilityClaimStatus.FORBIDDEN, CapabilityClaimStatus.ROADMAP_ONLY)


def test_p1410_blocks_production_ready_overclaim():
    claim = get_claim("production_ready_agentic_os")
    d = evaluate_capability_claim(claim, _ctx())
    assert not d.allowed, "P1.4.10 must block production-ready overclaim"
    assert d.allowed_status == CapabilityClaimStatus.FORBIDDEN


def test_p1410_blocks_abos_implementation_overclaim():
    claim = get_claim("abos_deployment_layer")
    d = evaluate_capability_claim(claim, _ctx())
    assert not d.allowed, "P1.4.10 must block ABOS implementation overclaim"
    assert d.allowed_status in (CapabilityClaimStatus.FORBIDDEN, CapabilityClaimStatus.ROADMAP_ONLY)


def test_p1410_blocks_aether_implementation_overclaim():
    claim = get_claim("aether_multimodal_intelligence")
    d = evaluate_capability_claim(claim, _ctx())
    assert not d.allowed, "P1.4.10 must block AETHER implementation overclaim"
    assert d.allowed_status in (CapabilityClaimStatus.FORBIDDEN, CapabilityClaimStatus.ROADMAP_ONLY)


def test_p1410_does_not_grant_capability():
    """Evaluating a claim must not grant any capability."""
    claim = get_claim("action_scoped_autonomy_evaluation")
    d = evaluate_capability_claim(claim, _ctx())
    # Decision is readonly, no side effects
    assert isinstance(d, CapabilityClaimDecision)
    # Allowed but hasn't changed any state
    assert d.allowed


def test_p1410_claim_status_requires_evidence():
    """Claims without evidence cannot be above ROADMAP_ONLY or FORBIDDEN."""
    claim = CapabilityClaim(
        claim_id="test", claim_text="test", claim_type=CapabilityClaimType.AUTONOMY,
        required_evidence_level="verified",
        current_evidence_level=None,
    )
    d = evaluate_capability_claim(claim, _ctx())
    assert d.allowed_status in (CapabilityClaimStatus.FORBIDDEN, CapabilityClaimStatus.ROADMAP_ONLY)


def test_p1410_roadmap_only_is_not_implemented():
    """Roadmap-only status means NOT implemented."""
    claim = get_claim("abos_deployment_layer")
    assert claim.current_evidence_level is None
    assert "P21.8" in claim.required_patch_refs


def test_p1410_safe_rewrite_does_not_overclaim():
    """Safe rewrite must never overclaim."""
    unsafe_phrases = ["is autonomous", "is self-improving", "is production-ready",
                       "has ABOS deployed", "has AETHER", "production-grade"]
    for phrase in unsafe_phrases:
        safe = rewrite_claim_text_safely(f"Aurel {phrase}.")
        if safe is not None:
            # The rewrite must not contain the original overclaim
            assert phrase not in safe.lower(), f"Rewrite still overclaims: {safe}"


# ── CLI tests ─────────────────────────────────────────────────────────────

def _run_cli(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "agentic_runtime.cli"] + args,
        capture_output=True, text=True, cwd=str(REPO_ROOT), timeout=15,
    )


def test_claims_cli_help():
    r = _run_cli(["identity", "claims", "--help"])
    assert r.returncode == 0
    assert "evaluate" in r.stdout
    assert "list" in r.stdout
    assert "show" in r.stdout
    assert "validate" in r.stdout
    assert "rewrite" in r.stdout


def test_claims_cli_evaluate_outputs_json():
    r = _run_cli(["identity", "claims", "evaluate", "--claim",
                   "Aurel is autonomous.", "--json"])
    assert r.returncode == 0
    data = json.loads(r.stdout)
    assert data["claim_id"] == "ad-hoc"
    assert not data["allowed"]
    assert data["allowed_status"] == "FORBIDDEN"
    assert data["safe_claim_text"]


def test_claims_cli_list_outputs_registry():
    r = _run_cli(["identity", "claims", "list", "--json"])
    assert r.returncode == 0
    data = json.loads(r.stdout)
    assert isinstance(data, list)
    assert len(data) == 14
    ids = {item["claim_id"] for item in data}
    assert "global_autonomy" in ids
    assert "self_improvement" in ids
    assert "production_ready_agentic_os" in ids


def test_claims_cli_show_outputs_claim():
    r = _run_cli(["identity", "claims", "show", "self_improvement", "--json"])
    assert r.returncode == 0
    data = json.loads(r.stdout)
    assert data["claim_id"] == "self_improvement"
    assert "self-improving" in data["original_claim_text"]
    assert not data["allowed"]


def test_claims_cli_validate_passes_registry():
    r = _run_cli(["identity", "claims", "validate", "--json"])
    assert r.returncode == 0
    data = json.loads(r.stdout)
    assert data["claims"] == 14
    assert isinstance(data["failures"], int)
    assert isinstance(data["warnings"], int)


def test_claims_cli_rewrite_outputs_safe_claim():
    r = _run_cli(["identity", "claims", "rewrite", "--claim",
                   "Aurel is self-improving.", "--json"])
    assert r.returncode == 0
    data = json.loads(r.stdout)
    assert data["original"] == "Aurel is self-improving."
    assert data["safe_rewrite"]
    assert "roadmap" in data["safe_rewrite"].lower()


def test_claims_cli_show_unknown_claim():
    r = _run_cli(["identity", "claims", "show", "nonexistent_claim"])
    assert r.returncode == 1


def test_claims_cli_rewrite_global_autonomy():
    r = _run_cli(["identity", "claims", "rewrite", "--claim-id", "global_autonomy", "--json"])
    assert r.returncode == 0
    data = json.loads(r.stdout)
    assert not data["allowed"]
    assert data["safe_rewrite"]
    assert "action-scoped" in data["safe_rewrite"]
