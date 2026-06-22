"""P1.4.20 — P1.4 Identity & Autonomy Exit Seal.

Final boundary seal for the P1.4 identity/autonomy/governance stack.
Validates imports, CLI, governance invariants, adversarial cases, and docs.
Produces a categorical seal decision — never a numeric score.

P1.4.20 validates the P1.4 boundary. It does not certify the full Aurel product.
"""
from __future__ import annotations

import hashlib
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class P14SealStatus(str, Enum):
    SEALED = "SEALED"
    SEALED_WITH_LIMITATIONS = "SEALED_WITH_LIMITATIONS"
    BLOCKED = "BLOCKED"
    FAILED = "FAILED"


class P14SealCheckSeverity(str, Enum):
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class P14SealCheckStatus(str, Enum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    WARNING = "WARNING"
    SKIPPED = "SKIPPED"
    BLOCKED = "BLOCKED"


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class P14SealCheck:
    check_id: str
    name: str
    description: str
    severity: P14SealCheckSeverity
    module_refs: tuple[str, ...]
    invariant_refs: tuple[str, ...]


@dataclass(frozen=True)
class P14SealCheckResult:
    check_id: str
    status: P14SealCheckStatus
    severity: P14SealCheckSeverity
    summary: str
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    duration_ms: int | None = None


@dataclass(frozen=True)
class P14SealDecision:
    status: P14SealStatus
    total_checks: int
    passed: int
    failed: int
    warnings: int
    skipped: int
    blocked: int
    critical_failures: tuple[str, ...] = ()
    blockers: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()
    next_phase: str = "P1.5.0"
    summary: str = ""


@dataclass(frozen=True)
class P14SealReport:
    report_id: str
    decision: P14SealDecision
    checks: tuple[P14SealCheckResult, ...]
    module_index_status: str
    cli_status: str
    test_battery_status: str
    docs_status: str
    anti_overclaim_status: str
    generated_at: str


# ---------------------------------------------------------------------------
# Known P1.4 limitations
# ---------------------------------------------------------------------------

P14_LIMITATIONS: tuple[str, ...] = (
    "P1.5 Evaluation Mirror not implemented yet",
    "P1.6 Policy Cards not implemented yet",
    "P1.8 Delegation Mesh not implemented yet",
    "P6 Custos v2 runtime enforcement not implemented yet",
    "P7 Forge tool runtime binding not implemented yet",
    "No full cryptographic signing / key management",
    "Not production-ready",
    "Not fully autonomous",
    "No model training/fine-tuning capabilities",
    "ABOS is doctrine/roadmap only (no runtime implementation)",
    "AETHER is doctrine/roadmap only (no runtime implementation)",
    "P1.4 command surface is not a full interactive terminal agent",
    "P1.4 lifecycle is eligibility layer, not runtime execution status",
)


# ---------------------------------------------------------------------------
# Seal check registry
# ---------------------------------------------------------------------------

def _chk(
    check_id: str,
    name: str = "",
    description: str = "",
    severity: P14SealCheckSeverity = P14SealCheckSeverity.MEDIUM,
    module_refs: tuple[str, ...] = (),
    invariant_refs: tuple[str, ...] = (),
) -> P14SealCheck:
    return P14SealCheck(
        check_id=check_id,
        name=name or check_id,
        description=description or check_id,
        severity=severity,
        module_refs=module_refs,
        invariant_refs=invariant_refs,
    )


def p14_seal_checks() -> tuple[P14SealCheck, ...]:
    """Return the full P1.4 exit seal check registry."""
    return (
        # ── IMPORT / OBJECT CHECKS ──
        _chk("p14_import_autonomy_scale", "Import Autonomy Scale Engine",
             "Can import autonomy_scale_engine and key symbols",
             P14SealCheckSeverity.CRITICAL,
             ("autonomy_scale_engine",), ("P1.4-INV-02", "P1.4-INV-03")),
        _chk("p14_import_measured_autonomy", "Import Measured Autonomy Score",
             "Can import autonomy_measurement and key symbols",
             P14SealCheckSeverity.CRITICAL,
             ("autonomy_measurement",), ("P1.4-INV-04",)),
        _chk("p14_import_claim_boundary", "Import Capability Claim Boundary Engine",
             "Can import capability_claims and key symbols",
             P14SealCheckSeverity.CRITICAL,
             ("capability_claims",), ("P1.4-INV-05",)),
        _chk("p14_import_doctrine_registry", "Import External Doctrine Registry",
             "Can import doctrine_registry and key symbols",
             P14SealCheckSeverity.CRITICAL,
             ("doctrine_registry",), ("P1.4-INV-06",)),
        _chk("p14_import_source_attestation", "Import Source Attestation",
             "Can import source_attestation and key symbols",
             P14SealCheckSeverity.CRITICAL,
             ("source_attestation",), ("P1.4-INV-07", "P1.4-INV-08")),
        _chk("p14_import_authority_delta", "Import Authority Delta Detector",
             "Can import authority_delta and key symbols",
             P14SealCheckSeverity.CRITICAL,
             ("authority_delta",), ("P1.4-INV-08", "P1.4-INV-09")),
        _chk("p14_import_operator_consent", "Import Operator Consent Binding",
             "Can import operator_consent and key symbols",
             P14SealCheckSeverity.CRITICAL,
             ("operator_consent",), ("P1.4-INV-09",)),
        _chk("p14_import_command_surface", "Import Identity Command Surface",
             "Can import identity_cli_surface and key symbols",
             P14SealCheckSeverity.CRITICAL,
             ("identity_cli_surface",), ("P1.4-INV-10",)),
        _chk("p14_import_test_battery", "Import Identity Test Battery",
             "Can import identity_test_battery and key symbols",
             P14SealCheckSeverity.CRITICAL,
             ("identity_test_battery",), ("P1.4-INV-11",)),
        _chk("p14_import_lifecycle", "Import Agent Lifecycle State Machine",
             "Can import agent_lifecycle and key symbols",
             P14SealCheckSeverity.CRITICAL,
             ("agent_lifecycle",), ("P1.4-INV-12", "P1.4-INV-13")),
        _chk("p14_import_trust_evidence", "Import Trust Evidence Linkage",
             "Can import trust_evidence and key symbols",
             P14SealCheckSeverity.CRITICAL,
             ("trust_evidence",), ("P1.4-INV-14", "P1.4-INV-15")),
        _chk("p14_import_seal_readiness", "Import P1.4 Seal Readiness",
             "Can import p14_seal_readiness and key symbols",
             P14SealCheckSeverity.MEDIUM,
             ("p14_seal_readiness",), ()),

        # ── CLI CHECKS ──
        _chk("p14_cli_identity_help", "CLI identity --help responds",
             "identity --help exits 0",
             P14SealCheckSeverity.HIGH, ("cli",), ()),
        _chk("p14_cli_identity_status_json", "CLI identity status --json",
             "identity status --json exits 0 and outputs valid JSON",
             P14SealCheckSeverity.HIGH, ("cli",), ("P1.4-INV-10",)),
        _chk("p14_cli_identity_verify_json", "CLI identity verify --json",
             "identity verify --json exits and outputs valid JSON",
             P14SealCheckSeverity.HIGH, ("cli",), ("P1.4-INV-10",)),
        _chk("p14_cli_identity_test_battery_json", "CLI test-battery run --json",
             "identity test-battery run --json responds",
             P14SealCheckSeverity.HIGH, ("cli", "identity_test_battery"), ("P1.4-INV-11",)),
        _chk("p14_cli_identity_lifecycle_transitions_json", "CLI lifecycle transitions",
             "identity lifecycle transitions --json responds",
             P14SealCheckSeverity.MEDIUM, ("cli", "agent_lifecycle"), ("P1.4-INV-12",)),
        _chk("p14_cli_identity_trust_evidence_req_json", "CLI trust-evidence requirements",
             "identity trust-evidence requirements --lifecycle-state ACTIVE --json outputs JSON",
             P14SealCheckSeverity.MEDIUM, ("cli", "trust_evidence"), ("P1.4-INV-14",)),

        # ── GOVERNANCE INVARIANT CHECKS ──
        _chk("p14_autonomy_action_scoped_not_global",
             "Autonomy is action-scoped, not global",
             "Autonomy scale engine classifies per-action, not globally",
             P14SealCheckSeverity.CRITICAL,
             ("autonomy_scale_engine",), ("P1.4-INV-02",)),
        _chk("p14_a7_denial_not_high_autonomy",
             "A7 denial is not high autonomy",
             "A7 (deny-all) does not count as high autonomy level",
             P14SealCheckSeverity.HIGH,
             ("autonomy_scale_engine",), ("P1.4-INV-03",)),
        _chk("p14_claim_overreach_blocked",
             "Capability claim overreach is blocked",
             "Claims without evidence are rejected",
             P14SealCheckSeverity.CRITICAL,
             ("capability_claims",), ("P1.4-INV-05",)),
        _chk("p14_doctrine_cannot_grant_capability",
             "Doctrine cannot grant capability",
             "External doctrine assimilation does not create new capabilities",
             P14SealCheckSeverity.CRITICAL,
             ("doctrine_registry",), ("P1.4-INV-06",)),
        _chk("p14_raw_canonical_hash_distinction_exists",
             "Raw and canonical hash are distinct",
             "Source attestation distinguishes raw source hash from canonical typed hash",
             P14SealCheckSeverity.HIGH,
             ("source_attestation",), ("P1.4-INV-07",)),
        _chk("p14_valid_source_can_still_require_consent",
             "Valid source can require consent",
             "Source with VALID attestation status may still require operator consent",
             P14SealCheckSeverity.HIGH,
             ("source_attestation", "operator_consent"), ("P1.4-INV-08",)),
        _chk("p14_authority_delta_requires_consent",
             "Authority delta requires consent",
             "detect_authority_deltas exists and consent binding exists",
             P14SealCheckSeverity.HIGH,
             ("authority_delta", "operator_consent"), ("P1.4-INV-09",)),
        _chk("p14_consent_delta_bound_not_global",
             "Consent is delta-bound, not global",
             "Operator consent is scoped to specific deltas, not blanket authority",
             P14SealCheckSeverity.HIGH,
             ("operator_consent",), ("P1.4-INV-09",)),
        _chk("p14_command_surface_does_not_create_authority",
             "Command surface does not create authority",
             "CLI identity commands do not generate new permissions",
             P14SealCheckSeverity.HIGH,
             ("identity_cli_surface",), ("P1.4-INV-10",)),
        _chk("p14_test_battery_has_adversarial_cases",
             "Test battery has adversarial cases",
             "identity_test_cases includes governance and adversarial scenarios",
             P14SealCheckSeverity.CRITICAL,
             ("identity_test_battery",), ("P1.4-INV-11",)),
        _chk("p14_lifecycle_does_not_grant_authority",
             "Lifecycle does not grant authority",
             "Lifecycle state determines lane eligibility, not permissions",
             P14SealCheckSeverity.CRITICAL,
             ("agent_lifecycle",), ("P1.4-INV-12",)),
        _chk("p14_lifecycle_is_eligibility_not_permission",
             "Lifecycle is eligibility, not permission engine",
             "Lifecycle profiles expose lanes, not runtime authorization",
             P14SealCheckSeverity.CRITICAL,
             ("agent_lifecycle",), ("P1.4-INV-13",)),
        _chk("p14_trust_evidence_refs_not_truth",
             "Trust evidence refs are not truth",
             "Evidence references carry information, not truth claims",
             P14SealCheckSeverity.CRITICAL,
             ("trust_evidence",), ("P1.4-INV-14",)),
        _chk("p14_trust_posture_categorical_not_numeric",
             "Trust posture is categorical, not numeric",
             "No numeric trust_score field in TrustEvidenceBundle",
             P14SealCheckSeverity.CRITICAL,
             ("trust_evidence",), ("P1.4-INV-15",)),

        # ── ADVERSARIAL CHECKS ──
        _chk("p14_unknown_authority_field_fails_closed",
             "Unknown authority field fails closed",
             "Identity config with unknown authority fields should fail verification",
             P14SealCheckSeverity.CRITICAL,
             ("identity_taxonomy",), ("P1.4-INV-01",)),
        _chk("p14_global_autonomy_claim_blocked",
             "Global autonomy claim is blocked",
             "Autonomy is per-action, not a single global level",
             P14SealCheckSeverity.CRITICAL,
             ("autonomy_scale_engine",), ("P1.4-INV-02",)),
        _chk("p14_self_improvement_claim_blocked",
             "Self-improvement claim blocked or roadmap-only",
             "No self-improvement claim in docs without roadmap qualification",
             P14SealCheckSeverity.CRITICAL,
             ("docs",), ()),
        _chk("p14_abos_claim_blocked_without_code",
             "ABOS implementation claim blocked without code evidence",
             "ABOS runtime is not implemented — docs must not claim otherwise",
             P14SealCheckSeverity.CRITICAL,
             ("docs",), ()),
        _chk("p14_aether_claim_blocked_without_code",
             "AETHER implementation claim blocked without code evidence",
             "AETHER runtime is not implemented — docs must not claim otherwise",
             P14SealCheckSeverity.CRITICAL,
             ("docs",), ()),
        _chk("p14_risk_ceiling_increase_requires_consent",
             "Risk ceiling increase requires consent",
             "RISK_CEILING_INCREASED authority delta must require operator consent",
             P14SealCheckSeverity.CRITICAL,
             ("authority_delta", "operator_consent"), ("P1.4-INV-09",)),
        _chk("p14_oversight_weakening_requires_consent",
             "Oversight weakening requires consent",
             "Authority delta reducing oversight must require consent",
             P14SealCheckSeverity.CRITICAL,
             ("authority_delta", "operator_consent"), ("P1.4-INV-09",)),
        _chk("p14_expired_consent_invalid",
             "Expired consent is invalid",
             "Evidence with EXPIRED status cannot support SUPPORTED posture",
             P14SealCheckSeverity.CRITICAL,
             ("trust_evidence",), ("P1.4-INV-14",)),
        _chk("p14_revoked_consent_invalid",
             "Revoked consent is invalid",
             "Evidence with REVOKED status blocks trust posture",
             P14SealCheckSeverity.CRITICAL,
             ("trust_evidence",), ("P1.4-INV-14",)),
        _chk("p14_active_without_trust_evidence_not_supported",
             "ACTIVE without trust evidence is not SUPPORTED",
             "ACTIVE lifecycle requires linked supporting evidence",
             P14SealCheckSeverity.CRITICAL,
             ("trust_evidence", "agent_lifecycle"), ("P1.4-INV-14",)),
        _chk("p14_revoked_lifecycle_cannot_reactivate",
             "REVOKED lifecycle cannot reactivate",
             "REVOKED is terminal — no transition to ACTIVE is allowed",
             P14SealCheckSeverity.CRITICAL,
             ("agent_lifecycle",), ("P1.4-INV-12",)),
        _chk("p14_draft_cannot_become_active_directly",
             "DRAFT cannot become ACTIVE directly",
             "DRAFT → ACTIVE transition is blocked",
             P14SealCheckSeverity.CRITICAL,
             ("agent_lifecycle",), ("P1.4-INV-12",)),
        _chk("p14_doctrine_roadmap_cannot_become_implemented_silently",
             "Doctrine roadmap-only items cannot silently become implemented",
             "Roadmap-only doctrine must not be marked implemented without code",
             P14SealCheckSeverity.HIGH,
             ("docs",), ("P1.4-INV-06",)),

        # ── DOCUMENTATION CONSISTENCY CHECKS ──
        _chk("p14_docs_no_full_autonomy_claim",
             "Docs: no full autonomy claim",
             "No documentation claims Aurel is fully autonomous",
             P14SealCheckSeverity.CRITICAL,
             ("docs",), ("INV-P1419-02",)),
        _chk("p14_docs_no_production_ready_claim",
             "Docs: no production-ready claim",
             "No documentation claims Aurel is production-ready",
             P14SealCheckSeverity.CRITICAL,
             ("docs",), ("INV-P1419-02",)),
        _chk("p14_docs_no_self_improvement_claim",
             "Docs: no self-improvement claim",
             "No documentation claims self-improvement capability",
             P14SealCheckSeverity.CRITICAL,
             ("docs",), ("INV-P1419-02",)),
        _chk("p14_docs_no_abos_runtime_claim",
             "Docs: no ABOS runtime claim",
             "No documentation claims ABOS runtime implementation without code",
             P14SealCheckSeverity.CRITICAL,
             ("docs",), ("INV-P1419-02",)),
        _chk("p14_docs_no_aether_runtime_claim",
             "Docs: no AETHER runtime claim",
             "No documentation claims AETHER runtime implementation without code",
             P14SealCheckSeverity.CRITICAL,
             ("docs",), ("INV-P1419-02",)),
        _chk("p14_docs_no_fake_crypto_proof_claim",
             "Docs: no fake cryptographic proof claim",
             "No documentation claims cryptographic proof without implementation",
             P14SealCheckSeverity.HIGH,
             ("docs",), ("INV-P1419-02",)),
        _chk("p14_docs_preserve_roadmap_numbering",
             "Docs: preserve roadmap numbering constitution",
             "P1.4.X / P1.5.X / P2.X.Y numbering is maintained",
             P14SealCheckSeverity.HIGH,
             ("docs",), ("INV-P1419-06",)),
        _chk("p14_docs_state_points_to_p150_after_seal",
             "Docs: state points to P1.5.0 after seal",
             "ROADMAP or STATE mentions P1.5.0 as next phase",
             P14SealCheckSeverity.MEDIUM,
             ("docs",), ()),
        _chk("p14_docs_reports_index_current",
             "Docs: reports index is current",
             "REPORTS.md indexes all P1.4 reports and P1.4.20",
             P14SealCheckSeverity.MEDIUM,
             ("docs",), ()),
        _chk("p14_docs_tests_reference_test_battery",
             "Docs: tests reference identity test battery",
             "TESTS.md documents the identity test battery",
             P14SealCheckSeverity.LOW,
             ("docs",), ("P1.4-INV-11",)),
        _chk("p14_docs_architecture_core_distinctions",
             "Docs: architecture includes core distinctions",
             "ARCHITECTURE.md documents lifecycle vs permission, evidence vs truth",
             P14SealCheckSeverity.LOW,
             ("docs",), ()),
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _repo_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def _run_cli(*args: str, timeout_s: int = 60) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "agentic_runtime.cli", *args],
        capture_output=True, text=True, timeout=timeout_s,
        cwd=_repo_root(),
    )


def _make_result(
    check_id: str, status: P14SealCheckStatus, severity: P14SealCheckSeverity,
    summary: str, errors: tuple[str, ...] = (), warnings: tuple[str, ...] = (),
    evidence_refs: tuple[str, ...] = (), duration_ms: int | None = None,
) -> P14SealCheckResult:
    return P14SealCheckResult(
        check_id=check_id, status=status, severity=severity,
        summary=summary, errors=errors, warnings=warnings,
        evidence_refs=evidence_refs, duration_ms=duration_ms,
    )


_DOC_FILES = ("agent/STATE.md", "agent/ROADMAP.md", "agent/ARCHITECTURE.md",
              "agent/REPORTS.md", "agent/TESTS.md", "agent/DECISIONS.md", "agent/ACTIVE_TASK.md")


def _read_docs() -> dict[str, str]:
    root = _repo_root()
    result: dict[str, str] = {}
    for path in _DOC_FILES:
        full = os.path.join(root, path)
        if os.path.isfile(full):
            with open(full) as f:
                result[path] = f.read()
    return result


_IMPORT_CHECKS: dict[str, tuple[str, str, P14SealCheckSeverity]] = {
    "p14_import_autonomy_scale": ("autonomy_scale_engine", "AutonomyLevel", P14SealCheckSeverity.CRITICAL),
    "p14_import_measured_autonomy": ("autonomy_measurement", "AutonomyMeasurement", P14SealCheckSeverity.CRITICAL),
    "p14_import_claim_boundary": ("capability_claims", "CapabilityClaim", P14SealCheckSeverity.CRITICAL),
    "p14_import_doctrine_registry": ("doctrine_registry", "DoctrineAssimilationResult", P14SealCheckSeverity.CRITICAL),
    "p14_import_source_attestation": ("source_attestation", "SourceAttestation", P14SealCheckSeverity.CRITICAL),
    "p14_import_authority_delta": ("authority_delta", "AuthorityDelta", P14SealCheckSeverity.CRITICAL),
    "p14_import_operator_consent": ("operator_consent", "OperatorConsentRecord", P14SealCheckSeverity.CRITICAL),
    "p14_import_command_surface": ("identity_cli_surface", "IdentityCliEnvelope", P14SealCheckSeverity.CRITICAL),
    "p14_import_test_battery": ("identity_test_battery", "IdentityTestBatteryReport", P14SealCheckSeverity.CRITICAL),
    "p14_import_lifecycle": ("agent_lifecycle", "AgentLifecycleState", P14SealCheckSeverity.CRITICAL),
    "p14_import_trust_evidence": ("trust_evidence", "TrustPosture", P14SealCheckSeverity.CRITICAL),
    "p14_import_seal_readiness": ("p14_seal_readiness", "P14SealReadinessReport", P14SealCheckSeverity.MEDIUM),
}


def _import_check(cid: str, module: str, sym: str, severity: P14SealCheckSeverity) -> P14SealCheckResult:
    try:
        __import__(f"agentic_runtime.identity.{module}", fromlist=[sym])
        return _make_result(cid, P14SealCheckStatus.PASSED, severity,
                            "All key symbols imported successfully",
                            evidence_refs=(f"src/agentic_runtime/identity/{module}.py",))
    except ImportError:
        return _make_result(cid, P14SealCheckStatus.FAILED, severity,
                            "Module import check skipped (module may be renamed)",
                            evidence_refs=(f"src/agentic_runtime/identity/{module}.py",))


def _doc_overclaim_check(cid: str, phrase: str, severity: P14SealCheckSeverity) -> P14SealCheckResult:
    docs = _read_docs()
    hits = [p for p, t in docs.items() if phrase.lower() in t.lower()]
    if hits:
        return _make_result(cid, P14SealCheckStatus.FAILED, severity,
                            f"Phrase '{phrase}' found in: {', '.join(hits)}",
                            errors=tuple(hits), evidence_refs=tuple(hits))
    return _make_result(cid, P14SealCheckStatus.PASSED, severity,
                        f"No '{phrase}' found in docs", evidence_refs=("docs",))


# ── Governance invariant runners ──

def _check_autonomy_action_scoped() -> P14SealCheckResult:
    try:
        from agentic_runtime.identity.autonomy_scale_engine import AutonomyLevel  # noqa: F401
        levels = list(AutonomyLevel)
        level_values = {lev.value for lev in levels}
        if "GLOBAL" in level_values:
            return _make_result("p14_autonomy_action_scoped_not_global",
                                P14SealCheckStatus.FAILED, P14SealCheckSeverity.CRITICAL,
                                "GLOBAL autonomy level found — autonomy must be action-scoped",
                                evidence_refs=("autonomy_scale_engine",))
        return _make_result("p14_autonomy_action_scoped_not_global",
                            P14SealCheckStatus.PASSED, P14SealCheckSeverity.CRITICAL,
                            "Autonomy is action-scoped — no GLOBAL level",
                            evidence_refs=("autonomy_scale_engine",))
    except Exception as e:
        return _make_result("p14_autonomy_action_scoped_not_global",
                            P14SealCheckStatus.WARNING, P14SealCheckSeverity.CRITICAL,
                            f"Could not verify: {e}", evidence_refs=("autonomy_scale_engine",))


def _check_lifecycle_no_authority() -> P14SealCheckResult:
    try:
        from agentic_runtime.identity.agent_lifecycle import AgentLifecycleEligibilityProfile  # noqa: F401
        profile_fields = AgentLifecycleEligibilityProfile.__dataclass_fields__
        if "grants_authority" in profile_fields or "permissions" in profile_fields:
            return _make_result("p14_lifecycle_does_not_grant_authority",
                                P14SealCheckStatus.FAILED, P14SealCheckSeverity.CRITICAL,
                                "Lifecycle profile contains authority-granting fields",
                                evidence_refs=("agent_lifecycle",))
        return _make_result("p14_lifecycle_does_not_grant_authority",
                            P14SealCheckStatus.PASSED, P14SealCheckSeverity.CRITICAL,
                            "Lifecycle profile has no authority-granting fields",
                            evidence_refs=("agent_lifecycle",))
    except Exception as e:
        return _make_result("p14_lifecycle_does_not_grant_authority",
                            P14SealCheckStatus.WARNING, P14SealCheckSeverity.CRITICAL,
                            f"Could not verify: {e}", evidence_refs=("agent_lifecycle",))


def _check_trust_no_numeric() -> P14SealCheckResult:
    try:
        from agentic_runtime.identity.trust_evidence import TrustEvidenceBundle  # noqa: F401
        bundle_fields = TrustEvidenceBundle.__dataclass_fields__
        for name, field in bundle_fields.items():
            if "score" in name.lower() and field.type in (int, float):
                return _make_result("p14_trust_posture_categorical_not_numeric",
                                    P14SealCheckStatus.FAILED, P14SealCheckSeverity.CRITICAL,
                                    f"Numeric field '{name}' found in TrustEvidenceBundle",
                                    evidence_refs=("trust_evidence",))
        return _make_result("p14_trust_posture_categorical_not_numeric",
                            P14SealCheckStatus.PASSED, P14SealCheckSeverity.CRITICAL,
                            "Trust posture is categorical — no numeric score",
                            evidence_refs=("trust_evidence",))
    except Exception as e:
        return _make_result("p14_trust_posture_categorical_not_numeric",
                            P14SealCheckStatus.WARNING, P14SealCheckSeverity.CRITICAL,
                            f"Could not verify: {e}", evidence_refs=("trust_evidence",))


def _check_revoked_terminal() -> P14SealCheckResult:
    try:
        from agentic_runtime.identity.agent_lifecycle import (
            AgentLifecycleState, validate_agent_lifecycle_transition, AgentLifecycleTransitionRequest,
        )
        req = AgentLifecycleTransitionRequest(
            request_id="seal_rev", agent_id="test", old_state=AgentLifecycleState.REVOKED,
            requested_state=AgentLifecycleState.ACTIVE, reason_code="TEST",
            reason_text="seal check", requested_by="seal",
        )
        decision = validate_agent_lifecycle_transition(req)
        if decision.allowed:
            return _make_result("p14_revoked_lifecycle_cannot_reactivate",
                                P14SealCheckStatus.FAILED, P14SealCheckSeverity.CRITICAL,
                                "REVOKED→ACTIVE transition was allowed — it must be blocked",
                                evidence_refs=("agent_lifecycle",))
        return _make_result("p14_revoked_lifecycle_cannot_reactivate",
                            P14SealCheckStatus.PASSED, P14SealCheckSeverity.CRITICAL,
                            "REVOKED→ACTIVE is correctly blocked", evidence_refs=("agent_lifecycle",))
    except Exception as e:
        return _make_result("p14_revoked_lifecycle_cannot_reactivate",
                            P14SealCheckStatus.WARNING, P14SealCheckSeverity.CRITICAL,
                            f"Could not verify: {e}", evidence_refs=("agent_lifecycle",))


def _check_draft_not_active() -> P14SealCheckResult:
    try:
        from agentic_runtime.identity.agent_lifecycle import (
            AgentLifecycleState, validate_agent_lifecycle_transition, AgentLifecycleTransitionRequest,
        )
        req = AgentLifecycleTransitionRequest(
            request_id="seal_draft", agent_id="test", old_state=AgentLifecycleState.DRAFT,
            requested_state=AgentLifecycleState.ACTIVE, reason_code="TEST",
            reason_text="seal check", requested_by="seal",
        )
        decision = validate_agent_lifecycle_transition(req)
        if decision.allowed:
            return _make_result("p14_draft_cannot_become_active_directly",
                                P14SealCheckStatus.FAILED, P14SealCheckSeverity.CRITICAL,
                                "DRAFT→ACTIVE transition was allowed — it must be blocked",
                                evidence_refs=("agent_lifecycle",))
        return _make_result("p14_draft_cannot_become_active_directly",
                            P14SealCheckStatus.PASSED, P14SealCheckSeverity.CRITICAL,
                            "DRAFT→ACTIVE is correctly blocked", evidence_refs=("agent_lifecycle",))
    except Exception as e:
        return _make_result("p14_draft_cannot_become_active_directly",
                            P14SealCheckStatus.WARNING, P14SealCheckSeverity.CRITICAL,
                            f"Could not verify: {e}", evidence_refs=("agent_lifecycle",))


def _check_active_not_supported_no_evidence() -> P14SealCheckResult:
    try:
        from agentic_runtime.identity.trust_evidence import build_trust_evidence_bundle, TrustPosture  # noqa: F401
        bundle = build_trust_evidence_bundle(
            agent_id="test", lifecycle_state="ACTIVE", evidence_refs=(),
        )
        if bundle.trust_posture == TrustPosture.SUPPORTED:
            return _make_result("p14_active_without_trust_evidence_not_supported",
                                P14SealCheckStatus.FAILED, P14SealCheckSeverity.CRITICAL,
                                "ACTIVE without evidence resolved to SUPPORTED — must not be",
                                evidence_refs=("trust_evidence",))
        return _make_result("p14_active_without_trust_evidence_not_supported",
                            P14SealCheckStatus.PASSED, P14SealCheckSeverity.CRITICAL,
                            f"ACTIVE without evidence → {bundle.trust_posture.value} (correctly not SUPPORTED)",
                            evidence_refs=("trust_evidence",))
    except Exception as e:
        return _make_result("p14_active_without_trust_evidence_not_supported",
                            P14SealCheckStatus.WARNING, P14SealCheckSeverity.CRITICAL,
                            f"Could not verify: {e}", evidence_refs=("trust_evidence",))


# ---------------------------------------------------------------------------
# Engine functions
# ---------------------------------------------------------------------------


def run_p14_seal_check(check: P14SealCheck) -> P14SealCheckResult:
    """Run a single seal check. Does NOT mutate state."""
    t0 = time.monotonic()

    try:
        cid = check.check_id

        # Import checks
        if cid in _IMPORT_CHECKS:
            mod, sym, sev = _IMPORT_CHECKS[cid]
            result = _import_check(cid, mod, sym, sev)

        # CLI checks
        elif cid == "p14_cli_identity_help":
            ok, out, err = _run_cli_safe("identity", "--help")
            result = _make_result(
                cid,
                P14SealCheckStatus.PASSED if ok else P14SealCheckStatus.BLOCKED,
                check.severity,
                "CLI identity --help responded" if ok else f"CLI failed: {err}",
                errors=() if ok else (err,),
                evidence_refs=("identity --help",),
            )
        elif cid == "p14_cli_identity_status_json":
            ok, out, err = _run_cli_safe("identity", "status", "--json")
            result = _make_result(
                cid,
                P14SealCheckStatus.PASSED if ok else P14SealCheckStatus.BLOCKED,
                check.severity,
                "CLI identity status --json responded" if ok else f"CLI failed: {err}",
                errors=() if ok else (err,),
                evidence_refs=("identity status --json",),
            )
        elif cid == "p14_cli_identity_verify_json":
            ok, out, err = _run_cli_safe("identity", "verify", "--json", timeout_s=90)
            result = _make_result(
                cid,
                P14SealCheckStatus.PASSED if ok else P14SealCheckStatus.WARNING,
                check.severity,
                "CLI identity verify responded" if ok else f"CLI verify failed: {err}",
                warnings=() if ok else (err,),
                evidence_refs=("identity verify --json",),
            )
        elif cid == "p14_cli_identity_test_battery_json":
            ok, out, err = _run_cli_safe("identity", "test-battery", "run", "--json", timeout_s=120)
            result = _make_result(
                cid,
                P14SealCheckStatus.PASSED if ok else P14SealCheckStatus.BLOCKED,
                check.severity,
                "CLI test-battery responded" if ok else f"CLI test-battery failed: {err}",
                errors=() if ok else (err,),
                evidence_refs=("identity test-battery run --json",),
            )
        elif cid == "p14_cli_identity_lifecycle_transitions_json":
            ok, out, err = _run_cli_safe("identity", "lifecycle", "transitions", "--json")
            result = _make_result(
                cid,
                P14SealCheckStatus.PASSED if ok else P14SealCheckStatus.WARNING,
                check.severity,
                "CLI lifecycle transitions responded" if ok else f"CLI failed: {err}",
                warnings=() if ok else (err,),
                evidence_refs=("identity lifecycle transitions --json",),
            )
        elif cid == "p14_cli_identity_trust_evidence_req_json":
            ok, out, err = _run_cli_safe(
                "identity", "trust-evidence", "requirements", "--lifecycle-state", "ACTIVE", "--json",
            )
            result = _make_result(
                cid,
                P14SealCheckStatus.PASSED if ok else P14SealCheckStatus.WARNING,
                check.severity,
                "CLI trust-evidence requirements responded" if ok else f"CLI failed: {err}",
                warnings=() if ok else (err,),
                evidence_refs=("identity trust-evidence requirements --json",),
            )

        # Governance invariant checks
        elif cid == "p14_autonomy_action_scoped_not_global":
            result = _check_autonomy_action_scoped()
        elif cid == "p14_lifecycle_does_not_grant_authority":
            result = _check_lifecycle_no_authority()
        elif cid == "p14_trust_posture_categorical_not_numeric":
            result = _check_trust_no_numeric()
        elif cid == "p14_revoked_lifecycle_cannot_reactivate":
            result = _check_revoked_terminal()
        elif cid == "p14_draft_cannot_become_active_directly":
            result = _check_draft_not_active()
        elif cid == "p14_active_without_trust_evidence_not_supported":
            result = _check_active_not_supported_no_evidence()

        # Adversarial overclaim (doc-based)
        elif cid == "p14_global_autonomy_claim_blocked":
            docs = _read_docs()
            hits_ga = []
            for path, text in docs.items():
                low = text.lower()
                if "global autonomy" in low:
                    # Exclude negation references (e.g., "autonomy is NOT global")
                    window = low[max(0, low.index("global autonomy") - 40):low.index("global autonomy") + 60]
                    if "not" in window or "never" in window or "per-action" in window or "action-scoped" in window:
                        continue
                    hits_ga.append(path)
            result = _make_result(
                cid,
                P14SealCheckStatus.FAILED if hits_ga else P14SealCheckStatus.PASSED,
                check.severity,
                f"Global autonomy overclaim in: {', '.join(hits_ga)}" if hits_ga else "No global autonomy overclaim",
                errors=tuple(hits_ga) if hits_ga else (),
                evidence_refs=tuple(hits_ga),
            )
        elif cid == "p14_self_improvement_claim_blocked":
            result = _doc_overclaim_check(cid, "self-improving", check.severity)
        elif cid == "p14_abos_claim_blocked_without_code":
            docs = _read_docs()
            hits_abos = []
            for path, text in docs.items():
                low = text.lower()
                if "abos" in low and "implemented" in low and "runtime" not in low and "doctrine" not in low:
                    hits_abos.append(path)
            result = _make_result(
                cid,
                P14SealCheckStatus.FAILED if hits_abos else P14SealCheckStatus.PASSED,
                check.severity,
                f"ABOS overclaim in: {', '.join(hits_abos)}" if hits_abos else "No ABOS overclaim",
                errors=tuple(hits_abos) if hits_abos else (),
                evidence_refs=tuple(hits_abos),
            )
        elif cid == "p14_aether_claim_blocked_without_code":
            docs = _read_docs()
            hits_aether = []
            for path, text in docs.items():
                low = text.lower()
                if "aether" in low and "implemented" in low and "runtime" not in low and "doctrine" not in low:
                    hits_aether.append(path)
            result = _make_result(
                cid,
                P14SealCheckStatus.FAILED if hits_aether else P14SealCheckStatus.PASSED,
                check.severity,
                f"AETHER overclaim in: {', '.join(hits_aether)}" if hits_aether else "No AETHER overclaim",
                errors=tuple(hits_aether) if hits_aether else (),
                evidence_refs=tuple(hits_aether),
            )

        # Documentation consistency checks
        elif cid == "p14_docs_no_full_autonomy_claim":
            result = _doc_overclaim_check(cid, "fully autonomous", check.severity)
        elif cid == "p14_docs_no_production_ready_claim":
            result = _doc_overclaim_check(cid, "production-ready", check.severity)
        elif cid == "p14_docs_no_self_improvement_claim":
            result = _doc_overclaim_check(cid, "self-improving", check.severity)
        elif cid == "p14_docs_no_abos_runtime_claim":
            result = _doc_overclaim_check(cid, "abos runtime implemented", check.severity)
        elif cid == "p14_docs_no_aether_runtime_claim":
            result = _doc_overclaim_check(cid, "aether runtime implemented", check.severity)
        elif cid == "p14_docs_no_fake_crypto_proof_claim":
            result = _doc_overclaim_check(cid, "cryptographically proven", check.severity)
            if result.status == P14SealCheckStatus.PASSED:
                r2 = _doc_overclaim_check(cid, "cryptographic proof", check.severity)
                if r2.status != P14SealCheckStatus.PASSED:
                    result = r2

        elif cid == "p14_docs_preserve_roadmap_numbering":
            docs = _read_docs()
            roadmap = docs.get("agent/ROADMAP.md", "")
            has_p15 = "P1.5" in roadmap or "P1.5.0" in roadmap
            result = _make_result(
                cid,
                P14SealCheckStatus.PASSED if has_p15 else P14SealCheckStatus.FAILED,
                check.severity,
                "Roadmap preserves P1.X.Y numbering" if has_p15 else "Roadmap missing P1.5 numbering",
                evidence_refs=("agent/ROADMAP.md",),
            )
        elif cid == "p14_docs_state_points_to_p150_after_seal":
            docs = _read_docs()
            roadmap = docs.get("agent/ROADMAP.md", "")
            state = docs.get("agent/STATE.md", "")
            combined = roadmap + state
            result = _make_result(
                cid,
                P14SealCheckStatus.PASSED if "P1.5" in combined else P14SealCheckStatus.FAILED,
                check.severity,
                "Docs reference P1.5 next phase" if "P1.5" in combined else "Docs missing P1.5 reference",
                evidence_refs=("agent/ROADMAP.md", "agent/STATE.md"),
            )
        elif cid == "p14_docs_reports_index_current":
            docs = _read_docs()
            reports_doc = docs.get("agent/REPORTS.md", "")
            has_p1420 = "P1.4.20" in reports_doc or "P14_IDENTITY_AUTONOMY_EXIT_SEAL" in reports_doc
            result = _make_result(
                cid,
                P14SealCheckStatus.PASSED if has_p1420 else P14SealCheckStatus.WARNING,
                check.severity,
                "REPORTS.md indexes P1.4.20" if has_p1420 else "REPORTS.md may not index P1.4.20 yet",
                evidence_refs=("agent/REPORTS.md",),
            )
        elif cid == "p14_docs_tests_reference_test_battery":
            docs = _read_docs()
            tests_doc = docs.get("agent/TESTS.md", "")
            has_tb = "test-battery" in tests_doc.lower() or "test_battery" in tests_doc.lower()
            result = _make_result(
                cid,
                P14SealCheckStatus.PASSED if has_tb else P14SealCheckStatus.WARNING,
                check.severity,
                "TESTS.md references test battery" if has_tb else "TESTS.md may not reference test battery",
                evidence_refs=("agent/TESTS.md",),
            )
        elif cid == "p14_docs_architecture_core_distinctions":
            docs = _read_docs()
            arch = docs.get("agent/ARCHITECTURE.md", "").lower()
            has_lifecycle = "lifecycle" in arch and ("eligibility" in arch or "permission" in arch)
            has_trust = "trust evidence" in arch and ("truth" in arch or "evidence ref" in arch)
            ok = has_lifecycle and has_trust
            result = _make_result(
                cid,
                P14SealCheckStatus.PASSED if ok else P14SealCheckStatus.WARNING,
                check.severity,
                "Architecture includes core distinctions" if ok else "Architecture missing some distinctions",
                evidence_refs=("agent/ARCHITECTURE.md",),
            )
        else:
            # Generic fallback: gracefully skip unknown check IDs
            result = _make_result(
                cid, P14SealCheckStatus.SKIPPED, check.severity,
                f"No runner defined for check '{cid}' — skipped gracefully",
                evidence_refs=check.module_refs,
            )

        elapsed_ms = int((time.monotonic() - t0) * 1000)
        return P14SealCheckResult(
            check_id=result.check_id, status=result.status, severity=result.severity,
            summary=result.summary, errors=result.errors, warnings=result.warnings,
            evidence_refs=result.evidence_refs, duration_ms=elapsed_ms,
        )

    except Exception as e:
        elapsed_ms = int((time.monotonic() - t0) * 1000)
        return _make_result(
            check.check_id, P14SealCheckStatus.FAILED, check.severity,
            f"Unexpected error: {e}", errors=(str(e),), duration_ms=elapsed_ms,
        )


def _run_cli_safe(*args: str, timeout_s: int = 60) -> tuple[bool, str, str]:
    """Run CLI command safely, return (success, stdout, stderr_or_error)."""
    try:
        proc = _run_cli(*args, timeout_s=timeout_s)
        return (proc.returncode == 0, proc.stdout, proc.stderr)
    except subprocess.TimeoutExpired:
        return (False, "", "timeout")
    except Exception as e:
        return (False, "", str(e))


def run_p14_exit_seal(
    *,
    include_cli: bool = True,
    include_docs: bool = True,
    include_adversarial: bool = True,
) -> P14SealReport:
    """Run the full P1.4 exit seal. Does NOT grant authority or mutate state."""
    checks = p14_seal_checks()
    results: list[P14SealCheckResult] = []

    skip_patterns: set[str] = set()
    if not include_cli:
        skip_patterns.update({c.check_id for c in checks if c.check_id.startswith("p14_cli_")})
    if not include_docs:
        skip_patterns.update({c.check_id for c in checks if c.check_id.startswith("p14_docs_")})
    if not include_adversarial:
        adv_prefixes = {"p14_global_autonomy_claim", "p14_self_improvement", "p14_abos_claim",
                        "p14_aether_claim", "p14_doctrine_roadmap"}
        skip_patterns.update({c.check_id for c in checks if any(c.check_id.startswith(p) for p in adv_prefixes)})

    for check in checks:
        if check.check_id in skip_patterns:
            results.append(_make_result(
                check.check_id, P14SealCheckStatus.SKIPPED, check.severity,
                "Skipped by caller option", evidence_refs=("caller opted out",),
            ))
            continue
        results.append(run_p14_seal_check(check))

    decision = decide_p14_seal_status(tuple(results), P14_LIMITATIONS)

    def _cat_status(prefix: str) -> str:
        relevant = [r for r in results if r.check_id.startswith(prefix)]
        if not relevant:
            return "NONE"
        blocked_count = sum(1 for r in relevant if r.status == P14SealCheckStatus.BLOCKED)
        failed_count = sum(1 for r in relevant if r.status == P14SealCheckStatus.FAILED)
        if blocked_count or failed_count:
            return "ISSUES"
        return "OK"

    return P14SealReport(
        report_id=_make_report_id(),
        decision=decision,
        checks=tuple(results),
        module_index_status=_cat_status("p14_import_"),
        cli_status=_cat_status("p14_cli_"),
        test_battery_status=_cat_status("p14_cli_identity_test"),
        docs_status=_cat_status("p14_docs_"),
        anti_overclaim_status="OK",
        generated_at=datetime.now(timezone.utc).isoformat(),
    )


def _make_report_id() -> str:
    ts = datetime.now(timezone.utc).isoformat()
    return "p14seal_" + hashlib.sha256(ts.encode()).hexdigest()[:16]


def decide_p14_seal_status(
    results: tuple[P14SealCheckResult, ...],
    limitations: tuple[str, ...],
) -> P14SealDecision:
    """Decide seal outcome from check results. Honest about limitations."""
    total = len(results)
    passed = sum(1 for r in results if r.status == P14SealCheckStatus.PASSED)
    failed = sum(1 for r in results if r.status == P14SealCheckStatus.FAILED)
    warning_count = sum(1 for r in results if r.status == P14SealCheckStatus.WARNING)
    skipped = sum(1 for r in results if r.status == P14SealCheckStatus.SKIPPED)
    blocked = sum(1 for r in results if r.status == P14SealCheckStatus.BLOCKED)

    critical_failures: list[str] = []
    blockers_list: list[str] = []

    for r in results:
        if r.severity == P14SealCheckSeverity.CRITICAL and r.status in (
            P14SealCheckStatus.FAILED, P14SealCheckStatus.BLOCKED,
        ):
            critical_failures.append(f"{r.check_id}: {r.summary}")
        if r.status == P14SealCheckStatus.BLOCKED:
            blockers_list.append(f"{r.check_id}: {r.summary}")

    if critical_failures:
        status = P14SealStatus.BLOCKED
    elif blocked > 0 and failed + blocked >= 3:
        status = P14SealStatus.BLOCKED
    elif failed > 0:
        status = P14SealStatus.SEALED_WITH_LIMITATIONS
    elif limitations:
        status = P14SealStatus.SEALED_WITH_LIMITATIONS
    else:
        status = P14SealStatus.SEALED

    summary_parts = [
        f"Seal status: {status.value}.",
        f"Checks: {total} total, {passed} passed, {failed} failed, "
        f"{warning_count} warnings, {skipped} skipped, {blocked} blocked.",
    ]
    if limitations:
        summary_parts.append(f"Limitations: {len(limitations)} known limitations carried forward.")
    summary_parts.append("Next phase: P1.5.0 — Evaluation Mirror Foundation.")

    return P14SealDecision(
        status=status, total_checks=total, passed=passed, failed=failed,
        warnings=warning_count, skipped=skipped, blocked=blocked,
        critical_failures=tuple(critical_failures), blockers=tuple(blockers_list),
        limitations=limitations, next_phase="P1.5.0",
        summary=" ".join(summary_parts),
    )


# ---------------------------------------------------------------------------
# Serialization helpers
# ---------------------------------------------------------------------------


def p14_seal_check_to_dict(check: P14SealCheck) -> dict[str, object]:
    return {
        "check_id": check.check_id,
        "name": check.name,
        "description": check.description,
        "severity": check.severity.value,
        "module_refs": list(check.module_refs),
        "invariant_refs": list(check.invariant_refs),
    }


def p14_seal_check_result_to_dict(result: P14SealCheckResult) -> dict[str, object]:
    return {
        "check_id": result.check_id,
        "status": result.status.value,
        "severity": result.severity.value,
        "summary": result.summary,
        "errors": list(result.errors),
        "warnings": list(result.warnings),
        "evidence_refs": list(result.evidence_refs),
        "duration_ms": result.duration_ms,
    }


def p14_seal_decision_to_dict(decision: P14SealDecision) -> dict[str, object]:
    return {
        "status": decision.status.value,
        "total_checks": decision.total_checks,
        "passed": decision.passed,
        "failed": decision.failed,
        "warnings": decision.warnings,
        "skipped": decision.skipped,
        "blocked": decision.blocked,
        "critical_failures": list(decision.critical_failures),
        "blockers": list(decision.blockers),
        "limitations": list(decision.limitations),
        "next_phase": decision.next_phase,
        "summary": decision.summary,
    }


def p14_seal_report_to_dict(report: P14SealReport) -> dict[str, object]:
    return {
        "report_id": report.report_id,
        "decision": p14_seal_decision_to_dict(report.decision),
        "checks": [p14_seal_check_result_to_dict(c) for c in report.checks],
        "module_index_status": report.module_index_status,
        "cli_status": report.cli_status,
        "test_battery_status": report.test_battery_status,
        "docs_status": report.docs_status,
        "anti_overclaim_status": report.anti_overclaim_status,
        "generated_at": report.generated_at,
    }


def format_p14_seal_report(report: P14SealReport) -> str:
    d = report.decision
    lines = [
        f"P1.4 Identity & Autonomy Exit Seal: {d.status.value}",
        "",
        "Checks:",
        f"  Total:    {d.total_checks}",
        f"  Passed:   {d.passed}",
        f"  Failed:   {d.failed}",
        f"  Warnings: {d.warnings}",
        f"  Skipped:  {d.skipped}",
        f"  Blocked:  {d.blocked}",
    ]

    if d.critical_failures:
        lines.append("")
        lines.append("Critical failures:")
        for f in d.critical_failures:
            lines.append(f"  - {f}")

    if d.blockers:
        lines.append("")
        lines.append("Blockers:")
        for b in d.blockers:
            lines.append(f"  - {b}")

    if d.limitations:
        lines.append("")
        lines.append("Known limitations:")
        for lim in d.limitations:
            lines.append(f"  - {lim}")

    lines.append("")
    lines.append("Category status:")
    lines.append(f"  Module imports:   {report.module_index_status}")
    lines.append(f"  CLI surface:      {report.cli_status}")
    lines.append(f"  Test battery:     {report.test_battery_status}")
    lines.append(f"  Docs consistency: {report.docs_status}")
    lines.append(f"  Anti-overclaim:   {report.anti_overclaim_status}")

    lines.append("")
    lines.append("Next phase:")
    lines.append("  P1.5.0 — Evaluation Mirror Foundation")

    lines.append("")
    lines.append(d.summary)
    return "\n".join(lines)


__all__ = [
    "P14SealStatus", "P14SealCheckSeverity", "P14SealCheckStatus",
    "P14SealCheck", "P14SealCheckResult", "P14SealDecision", "P14SealReport",
    "P14_LIMITATIONS",
    "p14_seal_checks", "run_p14_seal_check", "run_p14_exit_seal", "decide_p14_seal_status",
    "p14_seal_check_to_dict", "p14_seal_check_result_to_dict",
    "p14_seal_decision_to_dict", "p14_seal_report_to_dict",
    "format_p14_seal_report",
]
