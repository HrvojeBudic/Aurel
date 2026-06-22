"""P1.5.0 — Evaluation Mirror Foundation Gate.

Minimal evaluation foundation: domains, subjects, scopes, criteria, run envelopes.
Does NOT verify capabilities, run benchmarks, or implement full P4 Evaluation Mirror.

Core law: No capability claim may become VERIFIED without evaluation evidence.
EvaluationRunEnvelope prepares an auditable run — it does not itself verify capability.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class EvaluationDomain(str, Enum):
    AUREL_CORE = "AUREL_CORE"
    IDENTITY_GOVERNANCE = "IDENTITY_GOVERNANCE"
    AUTONOMY = "AUTONOMY"
    CAPABILITY_CLAIM = "CAPABILITY_CLAIM"
    POLICY = "POLICY"
    MEMORY = "MEMORY"
    TOOL_USE = "TOOL_USE"
    HUB_HANDOFF = "HUB_HANDOFF"
    MODEL_ROUTING = "MODEL_ROUTING"
    UNKNOWN = "UNKNOWN"


class EvaluationSubjectType(str, Enum):
    AGENT_IDENTITY = "AGENT_IDENTITY"
    AUTONOMY_DECISION = "AUTONOMY_DECISION"
    CAPABILITY_CLAIM = "CAPABILITY_CLAIM"
    LIFECYCLE_STATE = "LIFECYCLE_STATE"
    TRUST_EVIDENCE_BUNDLE = "TRUST_EVIDENCE_BUNDLE"
    OUTPUT = "OUTPUT"
    PROCEDURE = "PROCEDURE"
    MODEL_LANE = "MODEL_LANE"
    HUB_OUTPUT = "HUB_OUTPUT"
    UNKNOWN = "UNKNOWN"


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class EvaluationSubject:
    subject_id: str
    subject_type: EvaluationSubjectType
    domain: EvaluationDomain
    title: str | None = None
    source_ref: str | None = None
    evidence_refs: tuple[str, ...] = ()


@dataclass(frozen=True)
class EvaluationScope:
    scope_id: str
    domain: EvaluationDomain
    subject_types: tuple[EvaluationSubjectType, ...]
    purpose: str
    non_goals: tuple[str, ...] = ()


@dataclass(frozen=True)
class EvaluationCriterion:
    criterion_id: str
    name: str
    description: str
    required: bool = True
    severity: str = "MEDIUM"
    evidence_required: bool = True


@dataclass(frozen=True)
class EvaluationRunEnvelope:
    run_id: str
    subject: EvaluationSubject
    scope: EvaluationScope
    criteria: tuple[EvaluationCriterion, ...]
    evaluator: str
    created_at: str
    evidence_refs: tuple[str, ...] = ()


@dataclass(frozen=True)
class EvaluationFoundationReport:
    report_id: str
    status: str  # READY, DEGRADED, BLOCKED
    summary: str
    roadmap_alignment_status: str
    docs_updated: tuple[str, ...]
    docs_missing: tuple[str, ...]
    warnings: tuple[str, ...] = ()
    blockers: tuple[str, ...] = ()
    next_module: str = "P1.5.1"


# ---------------------------------------------------------------------------
# Invariants and non-goals
# ---------------------------------------------------------------------------

P150_INVARIANTS: tuple[str, ...] = (
    "INV-P150-01: P1.5.0 starts P1.5 only after P1.4.20 seal.",
    "INV-P150-02: P1.5.0 is Evaluation Mirror foundation, not full P4.",
    "INV-P150-03: Evaluation evidence is required before verified capability claims.",
    "INV-P150-04: EvaluationRunEnvelope does not itself verify capability.",
    "INV-P150-05: P1.5.0 does not implement scoring hype.",
    "INV-P150-06: P1.5.0 updates roadmap-related docs.",
    "INV-P150-07: Roadmap v3.2 is an update, not a reset.",
    "INV-P150-08: Aurel Core is distinct from Hub tools.",
    "INV-P150-09: Hub memory does not automatically become Aurel memory.",
    "INV-P150-10: Open-weight lanes are sovereign foundation; external APIs are escalation.",
    "INV-P150-11: P22–P24 are not started early.",
    "INV-P150-12: P1.5.1 is the next coding module.",
)

P150_NON_GOALS: tuple[str, ...] = (
    "Full P4 Evaluation Mirror",
    "Scoring engine or benchmark runner",
    "Model-of-Models or Model-of-Work scoring",
    "Hub-native evaluation (A-Hub/S-Hub/L-Hub/IDE)",
    "LoRA/adapter training",
    "Capability promotion engine",
    "Production capability certification",
    "Hub runtime implementation",
)


# ---------------------------------------------------------------------------
# Default scopes per domain
# ---------------------------------------------------------------------------

_DOMAIN_SCOPES: dict[EvaluationDomain, EvaluationScope] = {
    EvaluationDomain.AUREL_CORE: EvaluationScope(
        scope_id="scope_aurel_core",
        domain=EvaluationDomain.AUREL_CORE,
        subject_types=(
            EvaluationSubjectType.AGENT_IDENTITY,
            EvaluationSubjectType.OUTPUT,
            EvaluationSubjectType.PROCEDURE,
        ),
        purpose="Evaluate Aurel Core governance and orchestration behavior",
        non_goals=(
            "Does not evaluate Hub-native outputs",
            "Does not certify production readiness",
            "Does not run benchmarks",
        ),
    ),
    EvaluationDomain.IDENTITY_GOVERNANCE: EvaluationScope(
        scope_id="scope_identity_governance",
        domain=EvaluationDomain.IDENTITY_GOVERNANCE,
        subject_types=(
            EvaluationSubjectType.AGENT_IDENTITY,
            EvaluationSubjectType.LIFECYCLE_STATE,
            EvaluationSubjectType.TRUST_EVIDENCE_BUNDLE,
        ),
        purpose="Evaluate identity governance artifacts and lifecycle eligibility",
        non_goals=(
            "Does not grant authority",
            "Does not mutate lifecycle state",
            "Does not verify capability claims",
        ),
    ),
    EvaluationDomain.AUTONOMY: EvaluationScope(
        scope_id="scope_autonomy",
        domain=EvaluationDomain.AUTONOMY,
        subject_types=(EvaluationSubjectType.AUTONOMY_DECISION,),
        purpose="Evaluate action-scoped autonomy decisions",
        non_goals=(
            "Does not measure global autonomy",
            "Does not grant elevated autonomy",
        ),
    ),
    EvaluationDomain.CAPABILITY_CLAIM: EvaluationScope(
        scope_id="scope_capability_claim",
        domain=EvaluationDomain.CAPABILITY_CLAIM,
        subject_types=(EvaluationSubjectType.CAPABILITY_CLAIM,),
        purpose="Prepare evaluation envelope for capability claim verification",
        non_goals=(
            "Does not verify capability by itself",
            "Does not promote claims to VERIFIED without evidence",
            "Does not run benchmark factories",
        ),
    ),
    EvaluationDomain.POLICY: EvaluationScope(
        scope_id="scope_policy",
        domain=EvaluationDomain.POLICY,
        subject_types=(EvaluationSubjectType.PROCEDURE, EvaluationSubjectType.OUTPUT),
        purpose="Evaluate policy compliance of procedures and outputs",
        non_goals=("Does not implement Policy Cards (P1.6)",),
    ),
    EvaluationDomain.MEMORY: EvaluationScope(
        scope_id="scope_memory",
        domain=EvaluationDomain.MEMORY,
        subject_types=(EvaluationSubjectType.OUTPUT, EvaluationSubjectType.PROCEDURE),
        purpose="Evaluate memory write governance and provenance",
        non_goals=(
            "Does not merge Hub memory into Aurel Core memory",
            "Does not auto-promote memory candidates",
        ),
    ),
    EvaluationDomain.TOOL_USE: EvaluationScope(
        scope_id="scope_tool_use",
        domain=EvaluationDomain.TOOL_USE,
        subject_types=(EvaluationSubjectType.OUTPUT, EvaluationSubjectType.PROCEDURE),
        purpose="Evaluate tool invocation governance",
        non_goals=("Does not bind Forge tool runtime (P7)",),
    ),
    EvaluationDomain.HUB_HANDOFF: EvaluationScope(
        scope_id="scope_hub_handoff",
        domain=EvaluationDomain.HUB_HANDOFF,
        subject_types=(EvaluationSubjectType.HUB_OUTPUT,),
        purpose="Prepare evaluation scope for Hub handoff artifacts (future-ready)",
        non_goals=(
            "Hub evaluation is NOT implemented in P1.5.0",
            "Does not implement A-Hub/S-Hub/L-Hub/IDE runtimes",
            "Does not start P22–P24",
        ),
    ),
    EvaluationDomain.MODEL_ROUTING: EvaluationScope(
        scope_id="scope_model_routing",
        domain=EvaluationDomain.MODEL_ROUTING,
        subject_types=(EvaluationSubjectType.MODEL_LANE,),
        purpose="Prepare evaluation scope for model lane selection (future-ready)",
        non_goals=(
            "Model-of-Models is NOT implemented in P1.5.0",
            "Model-of-Work is NOT implemented in P1.5.0",
            "Does not run model benchmarks",
        ),
    ),
}


def default_evaluation_scope_for_domain(domain: EvaluationDomain) -> EvaluationScope:
    """Return a minimal default scope for a known domain."""
    if domain in _DOMAIN_SCOPES:
        return _DOMAIN_SCOPES[domain]
    return EvaluationScope(
        scope_id="scope_unknown",
        domain=EvaluationDomain.UNKNOWN,
        subject_types=(EvaluationSubjectType.UNKNOWN,),
        purpose="Conservative unknown evaluation scope",
        non_goals=(
            "Does not verify capability",
            "Does not run benchmarks",
            "Domain not yet defined — use explicit scope",
        ),
    )


# ---------------------------------------------------------------------------
# Default criteria per domain
# ---------------------------------------------------------------------------

_DEFAULT_CRITERIA: dict[EvaluationDomain, tuple[EvaluationCriterion, ...]] = {
    EvaluationDomain.AUREL_CORE: (
        EvaluationCriterion(
            criterion_id="core_governance_present",
            name="Governance artifacts present",
            description="Required governance artifacts are present and valid",
            required=True,
            severity="HIGH",
            evidence_required=True,
        ),
        EvaluationCriterion(
            criterion_id="core_no_overclaim",
            name="No capability overclaim",
            description="Core does not claim unverified capabilities",
            required=True,
            severity="CRITICAL",
            evidence_required=True,
        ),
    ),
    EvaluationDomain.CAPABILITY_CLAIM: (
        EvaluationCriterion(
            criterion_id="claim_evidence_bound",
            name="Claim is evidence-bound",
            description="Capability claim has linked evaluation evidence refs",
            required=True,
            severity="CRITICAL",
            evidence_required=True,
        ),
        EvaluationCriterion(
            criterion_id="claim_not_verified_without_eval",
            name="Not VERIFIED without evaluation",
            description="Claim status is not VERIFIED without completed evaluation run",
            required=True,
            severity="CRITICAL",
            evidence_required=True,
        ),
    ),
}


def default_criteria_for_domain(domain: EvaluationDomain) -> tuple[EvaluationCriterion, ...]:
    """Return default criteria for a domain, or a minimal generic set."""
    if domain in _DEFAULT_CRITERIA:
        return _DEFAULT_CRITERIA[domain]
    return (
        EvaluationCriterion(
            criterion_id="generic_evidence_present",
            name="Evidence references present",
            description="At least one evidence reference is linked",
            required=True,
            severity="MEDIUM",
            evidence_required=True,
        ),
    )


# ---------------------------------------------------------------------------
# Engine functions
# ---------------------------------------------------------------------------


def build_evaluation_subject(
    *,
    subject_id: str,
    subject_type: EvaluationSubjectType,
    domain: EvaluationDomain,
    title: str | None = None,
    source_ref: str | None = None,
    evidence_refs: tuple[str, ...] = (),
) -> EvaluationSubject:
    """Build an evaluation subject. Fails closed on empty subject_id."""
    if not subject_id or not subject_id.strip():
        raise ValueError("subject_id must not be empty")
    return EvaluationSubject(
        subject_id=subject_id.strip(),
        subject_type=subject_type,
        domain=domain,
        title=title,
        source_ref=source_ref,
        evidence_refs=evidence_refs,
    )


def build_evaluation_run_envelope(
    *,
    run_id: str,
    subject: EvaluationSubject,
    scope: EvaluationScope,
    criteria: tuple[EvaluationCriterion, ...],
    evaluator: str,
    evidence_refs: tuple[str, ...] = (),
    created_at: str | None = None,
) -> EvaluationRunEnvelope:
    """Build an evaluation run envelope. Does NOT verify capability."""
    if not run_id or not run_id.strip():
        raise ValueError("run_id must not be empty")
    if not evaluator or not evaluator.strip():
        raise ValueError("evaluator must not be empty")
    if not criteria:
        raise ValueError("criteria must not be empty")
    ts = created_at or datetime.now(timezone.utc).isoformat()
    return EvaluationRunEnvelope(
        run_id=run_id.strip(),
        subject=subject,
        scope=scope,
        criteria=criteria,
        evaluator=evaluator.strip(),
        created_at=ts,
        evidence_refs=evidence_refs,
    )


def validate_evaluation_run_envelope(envelope: EvaluationRunEnvelope) -> tuple[str, ...]:
    """Validate an evaluation run envelope. Returns blockers as strings. Does not mutate."""
    blockers: list[str] = []

    if not envelope.run_id or not envelope.run_id.strip():
        blockers.append("run_id must not be empty")
    if not envelope.evaluator or not envelope.evaluator.strip():
        blockers.append("evaluator must not be empty")
    if not envelope.criteria:
        blockers.append("criteria must not be empty")

    subj = envelope.subject
    scope = envelope.scope

    if subj.domain != scope.domain and scope.domain != EvaluationDomain.UNKNOWN:
        blockers.append(
            f"subject domain {subj.domain.value} not in scope domain {scope.domain.value}"
        )

    if subj.subject_type not in scope.subject_types:
        blockers.append(
            f"subject type {subj.subject_type.value} not in scope subject_types"
        )

    for crit in envelope.criteria:
        if not crit.criterion_id or not crit.criterion_id.strip():
            blockers.append("criterion with empty criterion_id found")
        if not crit.name or not crit.name.strip():
            blockers.append(f"criterion {crit.criterion_id!r} has empty name")

    return tuple(blockers)


def build_p150_foundation_report(
    *,
    docs_updated: tuple[str, ...],
    docs_missing: tuple[str, ...],
    warnings: tuple[str, ...] = (),
    blockers: tuple[str, ...] = (),
) -> EvaluationFoundationReport:
    """Build P1.5.0 foundation gate report."""
    if blockers:
        status = "BLOCKED"
        summary = f"P1.5.0 foundation gate BLOCKED: {len(blockers)} blocker(s)."
    elif warnings:
        status = "DEGRADED"
        summary = f"P1.5.0 foundation gate DEGRADED: {len(warnings)} warning(s), no blockers."
    else:
        status = "READY"
        summary = "P1.5.0 Evaluation Mirror foundation gate READY. Next: P1.5.1 — Evaluation Object Model."

    roadmap_status = "ALIGNED" if not blockers else "BLOCKED"

    ts = datetime.now(timezone.utc).isoformat()
    report_id = "p150_" + hashlib.sha256(ts.encode()).hexdigest()[:16]

    return EvaluationFoundationReport(
        report_id=report_id,
        status=status,
        summary=summary,
        roadmap_alignment_status=roadmap_status,
        docs_updated=docs_updated,
        docs_missing=docs_missing,
        warnings=warnings,
        blockers=blockers,
        next_module="P1.5.1 — Evaluation Object Model",
    )


# ---------------------------------------------------------------------------
# Serialization helpers
# ---------------------------------------------------------------------------


def evaluation_subject_to_dict(subject: EvaluationSubject) -> dict[str, object]:
    return {
        "subject_id": subject.subject_id,
        "subject_type": subject.subject_type.value,
        "domain": subject.domain.value,
        "title": subject.title,
        "source_ref": subject.source_ref,
        "evidence_refs": list(subject.evidence_refs),
    }


def evaluation_scope_to_dict(scope: EvaluationScope) -> dict[str, object]:
    return {
        "scope_id": scope.scope_id,
        "domain": scope.domain.value,
        "subject_types": [st.value for st in scope.subject_types],
        "purpose": scope.purpose,
        "non_goals": list(scope.non_goals),
    }


def evaluation_criterion_to_dict(criterion: EvaluationCriterion) -> dict[str, object]:
    return {
        "criterion_id": criterion.criterion_id,
        "name": criterion.name,
        "description": criterion.description,
        "required": criterion.required,
        "severity": criterion.severity,
        "evidence_required": criterion.evidence_required,
    }


def evaluation_run_envelope_to_dict(envelope: EvaluationRunEnvelope) -> dict[str, object]:
    return {
        "run_id": envelope.run_id,
        "subject": evaluation_subject_to_dict(envelope.subject),
        "scope": evaluation_scope_to_dict(envelope.scope),
        "criteria": [evaluation_criterion_to_dict(c) for c in envelope.criteria],
        "evaluator": envelope.evaluator,
        "created_at": envelope.created_at,
        "evidence_refs": list(envelope.evidence_refs),
    }


def evaluation_foundation_report_to_dict(report: EvaluationFoundationReport) -> dict[str, object]:
    return {
        "report_id": report.report_id,
        "status": report.status,
        "summary": report.summary,
        "roadmap_alignment_status": report.roadmap_alignment_status,
        "docs_updated": list(report.docs_updated),
        "docs_missing": list(report.docs_missing),
        "warnings": list(report.warnings),
        "blockers": list(report.blockers),
        "next_module": report.next_module,
    }


__all__ = [
    "EvaluationDomain",
    "EvaluationSubjectType",
    "EvaluationSubject",
    "EvaluationScope",
    "EvaluationCriterion",
    "EvaluationRunEnvelope",
    "EvaluationFoundationReport",
    "P150_INVARIANTS",
    "P150_NON_GOALS",
    "default_evaluation_scope_for_domain",
    "default_criteria_for_domain",
    "build_evaluation_subject",
    "build_evaluation_run_envelope",
    "validate_evaluation_run_envelope",
    "build_p150_foundation_report",
    "evaluation_subject_to_dict",
    "evaluation_scope_to_dict",
    "evaluation_criterion_to_dict",
    "evaluation_run_envelope_to_dict",
    "evaluation_foundation_report_to_dict",
]
