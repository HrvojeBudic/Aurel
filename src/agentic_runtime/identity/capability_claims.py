"""P1.4.10 — Capability Claim Boundary Engine.

Anti-hype firewall. Evaluates capability claims against evidence.
Does NOT grant capabilities, execute tools, or implement new features.

Core question:
  Given a capability claim and available evidence, is Aurel allowed to make this claim?
  If not, what is the safest truthful rewrite?
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

# ── Domain enums ─────────────────────────────────────────────────────────


class CapabilityClaimStatus(str, Enum):
    """Evidence-backed claim status. Roadmap ≠ implementation ≠ verified."""
    FORBIDDEN = "FORBIDDEN"
    ROADMAP_ONLY = "ROADMAP_ONLY"
    DRAFT_ONLY = "DRAFT_ONLY"
    EXPERIMENTAL = "EXPERIMENTAL"
    PARTIALLY_VERIFIED = "PARTIALLY_VERIFIED"
    VERIFIED = "VERIFIED"
    PRODUCTION_ELIGIBLE = "PRODUCTION_ELIGIBLE"


class CapabilityClaimType(str, Enum):
    IDENTITY = "identity"
    AUTONOMY = "autonomy"
    TOOL_USE = "tool_use"
    MEMORY = "memory"
    SANDBOX = "sandbox"
    EVALUATION = "evaluation"
    BUSINESS = "business"
    RESEARCH = "research"
    MULTIMODAL = "multimodal"
    SELF_IMPROVEMENT = "self_improvement"
    PRODUCTION_READINESS = "production_readiness"


# ── Data contracts ───────────────────────────────────────────────────────


@dataclass(frozen=True)
class CapabilityClaim:
    """A specific capability claim that must be evaluated against evidence."""
    claim_id: str
    claim_text: str
    claim_type: CapabilityClaimType
    capability_id: str | None = None
    required_evidence_level: str | None = None
    required_patch_refs: tuple[str, ...] = ()
    required_seals: tuple[str, ...] = ()
    current_evidence_level: str | None = None
    current_patch_refs: tuple[str, ...] = ()
    current_seals: tuple[str, ...] = ()
    measured_autonomy_class: str | None = None
    evidence_refs: tuple[str, ...] = ()


@dataclass(frozen=True)
class ClaimEvidenceContext:
    """Evidence available for claim evaluation."""
    capability_inventory: tuple[Any, ...] | None = None
    measured_autonomy_score: object | None = None
    patch_registry: object | None = None
    seal_tests: object | None = None
    reports: object | None = None
    roadmap_status: object | None = None


@dataclass(frozen=True)
class CapabilityClaimDecision:
    """Audit-friendly decision on a capability claim."""
    claim_id: str
    allowed: bool
    allowed_status: CapabilityClaimStatus
    original_claim_text: str
    safe_claim_text: str | None
    blockers: tuple[str, ...]
    warnings: tuple[str, ...]
    required_evidence: tuple[str, ...]
    current_evidence: tuple[str, ...]
    reason: str


def capability_claim_decision_to_dict(decision: CapabilityClaimDecision) -> dict[str, object]:
    return {
        "claim_id": decision.claim_id,
        "allowed": decision.allowed,
        "allowed_status": decision.allowed_status.value,
        "original_claim_text": decision.original_claim_text,
        "safe_claim_text": decision.safe_claim_text,
        "blockers": list(decision.blockers),
        "warnings": list(decision.warnings),
        "required_evidence": list(decision.required_evidence),
        "current_evidence": list(decision.current_evidence),
        "reason": decision.reason,
    }


# ── Claim registry ───────────────────────────────────────────────────────

_CLAIM_REGISTRY: dict[str, CapabilityClaim] = {}


def _build_default_registry() -> dict[str, CapabilityClaim]:
    """Build the canonical claim registry."""
    registry: dict[str, CapabilityClaim] = {}

    def _reg(
        claim_id: str, claim_text: str, claim_type: CapabilityClaimType,
        current_evidence_level: str | None = None,
        required_evidence_level: str | None = None,
        required_patch_refs: tuple[str, ...] = (),
        required_seals: tuple[str, ...] = (),
        capability_id: str | None = None,
        current_patch_refs: tuple[str, ...] = (),
        current_seals: tuple[str, ...] = (),
        measured_autonomy_class: str | None = None,
        evidence_refs: tuple[str, ...] = (),
    ):
        registry[claim_id] = CapabilityClaim(
            claim_id=claim_id, claim_text=claim_text, claim_type=claim_type,
            capability_id=capability_id,
            required_evidence_level=required_evidence_level,
            required_patch_refs=required_patch_refs,
            required_seals=required_seals,
            current_evidence_level=current_evidence_level,
            current_patch_refs=current_patch_refs,
            current_seals=current_seals,
            measured_autonomy_class=measured_autonomy_class,
            evidence_refs=evidence_refs,
        )

    # ── Identity claims ──────────────────────────────────────────────
    _reg(
        "agent_identity_card", "Aurel has an Agent Identity Card.",
        CapabilityClaimType.IDENTITY,
        current_evidence_level="implemented",
        required_evidence_level="implemented",
        required_patch_refs=("P1.4.7",),
        evidence_refs=("agent/reports/P1.4.7_AGENT_IDENTITY_CARD_REPORT.md",
                        "agent/reports/P1.4.7_MG_AGENT_IDENTITY_CARD_MERGE_GATE_HARDENING.md"),
        current_patch_refs=("P1.4.7",),
    )

    # ── Autonomy claims ──────────────────────────────────────────────
    _reg(
        "action_scoped_autonomy_evaluation",
        "Aurel has action-scoped autonomy evaluation and measured autonomy reporting.",
        CapabilityClaimType.AUTONOMY,
        current_evidence_level="partially_verified",
        required_evidence_level="implemented",
        required_patch_refs=("P1.4.8", "P1.4.9"),
        evidence_refs=("agent/reports/P1.4.8_AUTONOMY_SCALE_ENGINE.md",
                        "agent/reports/P1.4.9_MEASURED_AUTONOMY_SCORE.md"),
        current_patch_refs=("P1.4.8", "P1.4.9"),
    )

    _reg(
        "autonomy_scale_engine",
        "Aurel has an action-scoped autonomy decision engine (A0–A7).",
        CapabilityClaimType.AUTONOMY,
        current_evidence_level="partially_verified",
        required_evidence_level="implemented",
        required_patch_refs=("P1.4.8",),
        evidence_refs=("agent/reports/P1.4.8_AUTONOMY_SCALE_ENGINE.md",),
        current_patch_refs=("P1.4.8",),
    )

    _reg(
        "measured_autonomy_score",
        "Aurel has evidence-backed measured autonomy reporting.",
        CapabilityClaimType.AUTONOMY,
        current_evidence_level="partially_verified",
        required_evidence_level="implemented",
        required_patch_refs=("P1.4.9",),
        evidence_refs=("agent/reports/P1.4.9_MEASURED_AUTONOMY_SCORE.md",),
        current_patch_refs=("P1.4.9",),
    )

    _reg(
        "global_autonomy",
        "Aurel is autonomous.",
        CapabilityClaimType.AUTONOMY,
        current_evidence_level=None,
        required_evidence_level="production_eligible",
    )

    # ── Self-improvement ─────────────────────────────────────────────
    _reg(
        "self_improvement",
        "Aurel is self-improving.",
        CapabilityClaimType.SELF_IMPROVEMENT,
        current_evidence_level=None,
        required_evidence_level="verified",
        required_patch_refs=("P13", "P1.5"),
        required_seals=("verified_skill_promotion", "regression_evidence"),
    )

    # ── Production readiness ─────────────────────────────────────────
    _reg(
        "production_ready_agentic_os",
        "Aurel is a production-ready sovereign agentic OS.",
        CapabilityClaimType.PRODUCTION_READINESS,
        current_evidence_level=None,
        required_evidence_level="production_eligible",
        required_seals=("p20_seal", "sandbox_integrity", "audit_reconstruction",
                         "serious_action_trace"),
    )

    # ── ABOS claims ──────────────────────────────────────────────────
    _reg(
        "abos_roadmap_layer",
        "Aurel roadmap includes an ABOS Deployment Layer.",
        CapabilityClaimType.BUSINESS,
        current_evidence_level="roadmap_only",
        required_evidence_level="roadmap_only",
        required_patch_refs=("P21.8",),
    )

    _reg(
        "abos_deployment_layer",
        "Aurel has ABOS deployment.",
        CapabilityClaimType.BUSINESS,
        current_evidence_level=None,
        required_evidence_level="verified",
        required_patch_refs=("P21.8",),
        required_seals=("business_cockpit", "kpi_engine", "cost_attribution",
                         "compliance_health", "governance_board"),
    )

    # ── AETHER claims ────────────────────────────────────────────────
    _reg(
        "aether_roadmap_layer",
        "Aurel roadmap includes an AETHER-style research and intelligence layer.",
        CapabilityClaimType.RESEARCH,
        current_evidence_level="roadmap_only",
        required_evidence_level="roadmap_only",
        required_patch_refs=("P19",),
    )

    _reg(
        "aether_multimodal_intelligence",
        "Aurel has multimodal intelligence extraction (AETHER).",
        CapabilityClaimType.MULTIMODAL,
        current_evidence_level=None,
        required_evidence_level="verified",
        required_patch_refs=("P19",),
        required_seals=("multi_source_ingestion", "temporal_entity_timeline",
                         "change_intelligence", "cross_modal_reasoning"),
    )

    # ── Sandbox ──────────────────────────────────────────────────────
    _reg(
        "secure_sandboxing",
        "Aurel has production-grade sandboxing.",
        CapabilityClaimType.SANDBOX,
        current_evidence_level="roadmap_only",
        required_evidence_level="verified",
        required_patch_refs=("P9",),
        required_seals=("sandbox_escape_tests", "evaluator_isolation",
                         "network_deny_default"),
    )

    # ── Memory / Skills ──────────────────────────────────────────────
    _reg(
        "procedural_skill_library",
        "Aurel has a procedural skill library.",
        CapabilityClaimType.MEMORY,
        current_evidence_level="roadmap_only",
        required_evidence_level="verified",
        required_patch_refs=("P13",),
    )

    _reg(
        "verified_memory",
        "Aurel has verified memory with promotion gates.",
        CapabilityClaimType.MEMORY,
        current_evidence_level="roadmap_only",
        required_evidence_level="verified",
        required_patch_refs=("P1.5",),
    )

    return registry


def get_claim_registry() -> dict[str, CapabilityClaim]:
    """Return the canonical claim registry (lazy-initialized)."""
    global _CLAIM_REGISTRY
    if not _CLAIM_REGISTRY:
        _CLAIM_REGISTRY = _build_default_registry()
    return _CLAIM_REGISTRY


def list_claims() -> tuple[CapabilityClaim, ...]:
    return tuple(get_claim_registry().values())


def get_claim(claim_id: str) -> CapabilityClaim | None:
    return get_claim_registry().get(claim_id)


# ── Evidence level ordering ──────────────────────────────────────────────

_EVIDENCE_ORDER: dict[str, int] = {
    "": 0,
    "roadmap_only": 1,
    "draft_only": 2,
    "experimental": 3,
    "partially_verified": 4,
    "implemented": 5,
    "verified": 6,
    "production_eligible": 7,
}


def _evidence_rank(level: str | None) -> int:
    if level is None:
        return 0
    return _EVIDENCE_ORDER.get(level, 0)


def _status_for_evidence(evidence_level: str | None) -> CapabilityClaimStatus:
    mapping: dict[str, CapabilityClaimStatus] = {
        "production_eligible": CapabilityClaimStatus.PRODUCTION_ELIGIBLE,
        "verified": CapabilityClaimStatus.VERIFIED,
        "implemented": CapabilityClaimStatus.PARTIALLY_VERIFIED,
        "partially_verified": CapabilityClaimStatus.PARTIALLY_VERIFIED,
        "experimental": CapabilityClaimStatus.EXPERIMENTAL,
        "draft_only": CapabilityClaimStatus.DRAFT_ONLY,
        "roadmap_only": CapabilityClaimStatus.ROADMAP_ONLY,
    }
    return mapping.get(evidence_level or "", CapabilityClaimStatus.FORBIDDEN)


# ── Engine ───────────────────────────────────────────────────────────────


def evaluate_capability_claim(
    claim: CapabilityClaim,
    evidence_context: ClaimEvidenceContext,
) -> CapabilityClaimDecision:
    """Evaluate a capability claim against available evidence.
    Does NOT grant permissions, execute tools, or implement capabilities.
    """
    blockers: list[str] = []
    warnings: list[str] = []
    required_evidence: list[str] = list(claim.required_patch_refs) + list(claim.required_seals)
    current_evidence_list: list[str] = (
        list(claim.current_patch_refs) + list(claim.current_seals) + list(claim.evidence_refs)
    )

    current_rank = _evidence_rank(claim.current_evidence_level)
    required_rank = _evidence_rank(claim.required_evidence_level)

    # ── Rule: no current evidence → FORBIDDEN ──────────────────────
    if claim.current_evidence_level is None and claim.required_evidence_level is not None:
        if claim.required_evidence_level == "roadmap_only":
            return _decision(
                claim, allowed=False, status=CapabilityClaimStatus.ROADMAP_ONLY,
                blockers=(f"missing_evidence_requires_{claim.required_evidence_level}",),
                reason=f"Claim requires {claim.required_evidence_level} evidence, but none is available.",
                required_evidence=tuple(required_evidence),
                current_evidence=(),
            )
        return _decision(
            claim, allowed=False, status=CapabilityClaimStatus.FORBIDDEN,
            blockers=(f"missing_evidence_requires_{claim.required_evidence_level}",),
            reason=f"Claim requires {claim.required_evidence_level} evidence, but none is available.",
            required_evidence=tuple(required_evidence),
            current_evidence=(),
        )

    # ── Rule: evidence insufficient for required level ──────────────
    if current_rank < required_rank:
        status = _status_for_evidence(claim.current_evidence_level)
        blockers.append("insufficient_evidence_for_claim")
        reason = (f"Claim requires {claim.required_evidence_level} evidence "
                  f"(required={required_rank}), but has {claim.current_evidence_level} evidence "
                  f"(current={current_rank}).")
        return _decision(
            claim, allowed=_is_allowed(status), status=status,
            blockers=tuple(blockers),
            reason=reason,
            required_evidence=tuple(required_evidence),
            current_evidence=tuple(current_evidence_list),
            warnings=tuple(warnings),
        )

    # ── Rule: roadmap ≠ implementation ─────────────────────────────
    if claim.required_evidence_level in ("verified", "production_eligible"):
        is_roadmap_only = (
            claim.current_evidence_level is None
            or _evidence_rank(claim.current_evidence_level) <= _evidence_rank("roadmap_only")
        )
        has_verified = _evidence_rank(claim.current_evidence_level) >= _evidence_rank("verified")
        if is_roadmap_only and not has_verified:
            blockers.append("roadmap_is_not_implementation")
            reason = "Roadmap status cannot support this claim. Implementation and verification are required."
            return _decision(
                claim, allowed=False, status=CapabilityClaimStatus.ROADMAP_ONLY,
                blockers=tuple(blockers),
                reason=reason,
                required_evidence=tuple(required_evidence),
                current_evidence=tuple(current_evidence_list),
            )

    # ── Rule: required patch refs must be present ───────────────────
    if claim.required_patch_refs:
        missing_patches = [p for p in claim.required_patch_refs
                           if p not in claim.current_patch_refs]
        if missing_patches:
            blockers.append(f"missing_required_patches:{','.join(missing_patches)}")
            warnings.append("claim_partially_evidenced")

    # ── Rule: required seals must be present ────────────────────────
    if claim.required_seals:
        missing_seals = [s for s in claim.required_seals
                         if s not in claim.current_seals]
        if missing_seals:
            blockers.append(f"missing_required_seals:{','.join(missing_seals)}")

    # ── Build result ────────────────────────────────────────────────
    if blockers:
        evidence_status = _status_for_evidence(claim.current_evidence_level)
        if _evidence_rank(claim.current_evidence_level) >= _evidence_rank("partially_verified"):
            warnings.append("evidence_partial_downgrade_seals_missing")
        reason = f"Claim has evidence gaps: {', '.join(blockers[:3])}"
        return _decision(
            claim, allowed=False, status=evidence_status,
            blockers=tuple(blockers),
            warnings=tuple(warnings),
            reason=reason,
            required_evidence=tuple(required_evidence),
            current_evidence=tuple(current_evidence_list),
        )

    # ── Allowed ─────────────────────────────────────────────────────
    status = _status_for_evidence(claim.current_evidence_level)
    reason = f"Claim supported by {claim.current_evidence_level} evidence."
    return _decision(
        claim, allowed=_is_allowed(status), status=status,
        reason=reason,
        required_evidence=tuple(required_evidence),
        current_evidence=tuple(current_evidence_list),
        warnings=tuple(warnings),
    )


def _decision(
    claim: CapabilityClaim,
    *,
    allowed: bool,
    status: CapabilityClaimStatus,
    reason: str,
    required_evidence: tuple[str, ...] = (),
    current_evidence: tuple[str, ...] = (),
    blockers: tuple[str, ...] = (),
    warnings: tuple[str, ...] = (),
) -> CapabilityClaimDecision:
    safe = rewrite_capability_claim_safely(claim, status)
    return CapabilityClaimDecision(
        claim_id=claim.claim_id,
        allowed=allowed,
        allowed_status=status,
        original_claim_text=claim.claim_text,
        safe_claim_text=safe,
        blockers=blockers,
        warnings=warnings,
        required_evidence=required_evidence,
        current_evidence=current_evidence,
        reason=reason,
    )


def _is_allowed(status: CapabilityClaimStatus) -> bool:
    """FORBIDDEN, ROADMAP_ONLY, DRAFT_ONLY are not allowed as-is.
    Only EXPERIMENTAL and above are allowed to be stated as-is."""
    return status not in (
        CapabilityClaimStatus.FORBIDDEN,
        CapabilityClaimStatus.ROADMAP_ONLY,
        CapabilityClaimStatus.DRAFT_ONLY,
    )


# ── Safe claim rewriting ──────────────────────────────────────────────────

_SAFE_REWRITES: dict[str, str] = {
    "Aurel is autonomous.":
        "Aurel supports action-scoped autonomy evaluation with fail-closed decision rules.",

    "Aurel can act autonomously.":
        "Aurel supports action-scoped autonomy evaluation with fail-closed decision rules.",

    "Aurel has full autonomy.":
        "Aurel supports action-scoped autonomy evaluation with fail-closed decision rules.",

    "Aurel is self-improving.":
        "Aurel has a roadmap path toward verified self-improvement through future skill promotion and evaluation gates.",

    "Aurel is production-ready.":
        "Aurel is progressing toward Sovereign Agentic OS Seal validation.",

    "Aurel is a production-ready sovereign agentic OS.":
        "Aurel is progressing toward Sovereign Agentic OS Seal validation.",

    "Aurel is a production-grade sovereign agentic OS.":
        "Aurel is progressing toward Sovereign Agentic OS Seal validation.",

    "Aurel has ABOS deployment.":
        "Aurel roadmap includes an ABOS Deployment Layer planned for P21.8.",

    "Aurel runs business autonomously.":
        "Aurel roadmap includes an ABOS Deployment Layer planned for P21.8.",

    "Aurel has multimodal intelligence extraction.":
        "Aurel roadmap includes an AETHER-style research and intelligence layer planned through P19.",

    "Aurel has AETHER intelligence.":
        "Aurel roadmap includes an AETHER-style research and intelligence layer planned through P19.",

    "Aurel has production-grade sandboxing.":
        "Aurel sandboxing capabilities are roadmap-only. Current runtime uses UnsafeLocalSandbox.",

    "Aurel has verified memory.":
        "Aurel memory capabilities are in development. Current state supports Praxis experience capture.",

    "Aurel has a procedural skill library.":
        "Aurel skill library capabilities are roadmap-only. Self-improvement requires verified promotion evidence.",
}


def _safe_by_status(claim: CapabilityClaim, status: CapabilityClaimStatus) -> str | None:
    """Generate a safe rewrite based on claim type and status."""
    if status == CapabilityClaimStatus.FORBIDDEN:
        templates: dict[CapabilityClaimType, str] = {
            CapabilityClaimType.AUTONOMY:
                "Aurel supports action-scoped autonomy evaluation with fail-closed decision rules.",
            CapabilityClaimType.SELF_IMPROVEMENT:
                "Aurel has a roadmap path toward verified self-improvement through future skill promotion and evaluation gates.",
            CapabilityClaimType.PRODUCTION_READINESS:
                "Aurel is progressing toward Sovereign Agentic OS Seal validation.",
            CapabilityClaimType.BUSINESS:
                "Aurel roadmap includes an ABOS Deployment Layer planned for P21.8.",
            CapabilityClaimType.MULTIMODAL:
                "Aurel roadmap includes an AETHER-style research and intelligence layer planned through P19.",
            CapabilityClaimType.RESEARCH:
                "Aurel roadmap includes future research capabilities.",
            CapabilityClaimType.SANDBOX:
                "Aurel sandboxing capabilities are under active development.",
            CapabilityClaimType.MEMORY:
                "Aurel memory capabilities are under active development.",
        }
        return templates.get(claim.claim_type)

    if status == CapabilityClaimStatus.ROADMAP_ONLY:
        roadmap_templates: dict[CapabilityClaimType, str] = {
            CapabilityClaimType.AUTONOMY:
                "Aurel supports action-scoped autonomy evaluation. Broader autonomy is roadmap-only.",
            CapabilityClaimType.SELF_IMPROVEMENT:
                "Aurel has a roadmap path toward verified self-improvement through future skill promotion and evaluation gates.",
            CapabilityClaimType.PRODUCTION_READINESS:
                "Aurel is progressing toward Sovereign Agentic OS Seal validation.",
            CapabilityClaimType.BUSINESS:
                "Aurel roadmap includes an ABOS Deployment Layer planned for P21.8.",
            CapabilityClaimType.MULTIMODAL:
                "Aurel roadmap includes an AETHER-style research and intelligence layer planned through P19.",
            CapabilityClaimType.RESEARCH:
                "Aurel roadmap includes future research capabilities.",
            CapabilityClaimType.SANDBOX:
                "Aurel sandboxing capabilities are roadmap-only. Current runtime uses UnsafeLocalSandbox.",
            CapabilityClaimType.MEMORY:
                "Aurel memory capabilities are under active development.",
        }
        return roadmap_templates.get(claim.claim_type)

    return None


def rewrite_capability_claim_safely(
    claim: CapabilityClaim,
    status_or_decision: CapabilityClaimStatus | CapabilityClaimDecision,
) -> str | None:
    """Produce a safe truthful rewrite when a claim is blocked or downgraded.
    Must preserve truth. Must not soften a forbidden claim into a misleading claim.
    """
    if isinstance(status_or_decision, CapabilityClaimDecision):
        status = status_or_decision.allowed_status
    else:
        status = status_or_decision

    # Exact match first
    exact = _SAFE_REWRITES.get(claim.claim_text)
    if exact is not None:
        return exact

    # Fallback by status + type
    return _safe_by_status(claim, status)


def rewrite_claim_text_safely(claim_text: str) -> str | None:
    """Convenience: rewrite a claim text string safely."""
    exact = _SAFE_REWRITES.get(claim_text)
    if exact is not None:
        return exact
    return None
