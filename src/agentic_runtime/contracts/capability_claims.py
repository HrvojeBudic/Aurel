"""P1.5.16 Capability Claim Registry v2 contracts.

The anti-overclaim layer. Aurel must not claim capability beyond evidence.
Every positive capability claim must be trace-bound, evidence-bound,
verifier-bound, context-bound, limitation-bound, scope-bound, and
status-controlled.

These contracts are projections over canonical AurelTraceLog.
They are not a second source of truth.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum

from .trace import TraceEventRef


# ---------------------------------------------------------------------------
# CapabilityClaimStatus
# ---------------------------------------------------------------------------


class CapabilityClaimStatus(str, Enum):
    """What is known about a capability claim.

    'verified' does not mean universally capable.
    'verified' always means verified under declared scope and limitations.
    """
    UNVERIFIED = "unverified"
    WEAKLY_SUPPORTED = "weakly_supported"
    EXPERIMENTAL = "experimental"
    CONTEXT_VERIFIED = "context_verified"
    VERIFIED_CANDIDATE = "verified_candidate"
    VERIFIED = "verified"
    FAILED = "failed"
    CONTRADICTED = "contradicted"
    DEPRECATED = "deprecated"


# Positive claim statuses (claim is making an affirmative claim).
_POSITIVE_STATUSES = frozenset({
    CapabilityClaimStatus.WEAKLY_SUPPORTED,
    CapabilityClaimStatus.EXPERIMENTAL,
    CapabilityClaimStatus.CONTEXT_VERIFIED,
    CapabilityClaimStatus.VERIFIED_CANDIDATE,
    CapabilityClaimStatus.VERIFIED,
})


def is_positive_claim_status(status: CapabilityClaimStatus) -> bool:
    """Return True if the status represents an affirmative capability claim."""
    return status in _POSITIVE_STATUSES


# ---------------------------------------------------------------------------
# CapabilityClaimScope
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CapabilityClaimScope:
    """Defines where the claim applies.

    No empty/global scope for positive claims — explicit scope is mandatory.
    """

    task_type: str
    allowed_contexts: tuple[str, ...] = ()
    required_inputs: tuple[str, ...] = ()
    allowed_tools: tuple[str, ...] = ()
    required_verifier_kinds: tuple[str, ...] = ()
    risk_tier: str | None = None
    autonomy_level: str | None = None
    environment_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.task_type or not self.task_type.strip():
            raise ValueError("task_type must not be empty")


# ---------------------------------------------------------------------------
# KnownLimit
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class KnownLimit:
    """A limitation on a capability claim.

    Forces every serious capability claim to carry limitations.
    """

    limit_id: str
    description: str
    severity: str = "info"
    source_ref: str | None = None
    created_at: str = ""

    def __post_init__(self) -> None:
        if not self.limit_id or not self.limit_id.strip():
            raise ValueError("limit_id must not be empty")
        if not self.description or not self.description.strip():
            raise ValueError("description must not be empty")
        if self.severity not in ("info", "warning", "blocking"):
            raise ValueError(f"severity must be one of info|warning|blocking, got {self.severity}")
        if not self.created_at or not self.created_at.strip():
            raise ValueError("created_at must not be empty")


# ---------------------------------------------------------------------------
# VerifiedContext
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class VerifiedContext:
    """Records the exact context in which a capability was verified."""

    context_id: str
    context_summary: str
    source_trace_event_ref: TraceEventRef
    evaluation_run_result_ref: str | None = None
    evidence_refs: tuple[str, ...] = ()
    verifier_result_refs: tuple[str, ...] = ()
    created_at: str = ""

    def __post_init__(self) -> None:
        if not self.context_id or not self.context_id.strip():
            raise ValueError("context_id must not be empty")
        if not self.context_summary or not self.context_summary.strip():
            raise ValueError("context_summary must not be empty")
        if self.source_trace_event_ref is None:
            raise ValueError("source_trace_event_ref is required")
        if not self.created_at or not self.created_at.strip():
            raise ValueError("created_at must not be empty")


# ---------------------------------------------------------------------------
# ClaimEvidenceLink
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ClaimEvidenceLink:
    """Binds claim status to actual evidence chain.

    source_event_hash must match source_trace_event_ref.event_hash.
    """

    link_id: str
    capability_evidence_id: str
    source_trace_event_ref: TraceEventRef
    source_event_hash: str
    evidence_refs: tuple[str, ...] = ()
    verifier_result_refs: tuple[str, ...] = ()
    evaluation_case_refs: tuple[str, ...] = ()
    evaluation_run_result_refs: tuple[str, ...] = ()
    brain_aware_context_ref: str | None = None

    def __post_init__(self) -> None:
        if not self.link_id or not self.link_id.strip():
            raise ValueError("link_id must not be empty")
        if not self.capability_evidence_id or not self.capability_evidence_id.strip():
            raise ValueError("capability_evidence_id must not be empty")
        if self.source_trace_event_ref is None:
            raise ValueError("source_trace_event_ref is required")
        if not self.source_event_hash or not self.source_event_hash.strip():
            raise ValueError("source_event_hash must not be empty")
        if self.source_event_hash != self.source_trace_event_ref.event_hash:
            raise ValueError(
                "source_event_hash must match source_trace_event_ref.event_hash"
            )


# ---------------------------------------------------------------------------
# CapabilityClaim
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CapabilityClaim:
    """A bounded capability claim Aurel may assert.

    'verified' does not mean universally capable.
    Positive claims require evidence, scope, and limitations.
    """

    claim_id: str
    capability_id: str
    claim_text: str
    status: CapabilityClaimStatus
    scope: CapabilityClaimScope
    evidence_links: tuple[ClaimEvidenceLink, ...] = ()
    verified_contexts: tuple[VerifiedContext, ...] = ()
    known_limits: tuple[KnownLimit, ...] = ()
    confidence_label: str = "none"
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self) -> None:
        if not self.claim_id or not self.claim_id.strip():
            raise ValueError("claim_id must not be empty")
        if not self.capability_id or not self.capability_id.strip():
            raise ValueError("capability_id must not be empty")
        if not self.claim_text or not self.claim_text.strip():
            raise ValueError("claim_text must not be empty")
        if self.confidence_label not in ("none", "low", "medium", "high", "bounded_high"):
            raise ValueError(
                f"confidence_label must be one of none|low|medium|high|bounded_high, "
                f"got {self.confidence_label}"
            )
        if not self.created_at or not self.created_at.strip():
            raise ValueError("created_at must not be empty")
        if not self.updated_at or not self.updated_at.strip():
            raise ValueError("updated_at must not be empty")

        if is_positive_claim_status(self.status):
            if not self.evidence_links:
                raise ValueError("positive claims require non-empty evidence_links")
            if (
                self.status in (
                    CapabilityClaimStatus.CONTEXT_VERIFIED,
                    CapabilityClaimStatus.VERIFIED_CANDIDATE,
                    CapabilityClaimStatus.VERIFIED,
                )
                and not self.known_limits
            ):
                raise ValueError(
                    f"{self.status.value} claim requires non-empty known_limits"
                )


# ---------------------------------------------------------------------------
# CapabilityClaimCandidate
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CapabilityClaimCandidate:
    """Proposes a claim update without mutating registry truth."""

    candidate_id: str
    proposed_claim_text: str
    capability_id: str
    source_evaluation_run_result_ref: str
    source_capability_evidence_id: str
    proposed_status: CapabilityClaimStatus
    proposed_scope: CapabilityClaimScope | None = None
    proposed_limits: tuple[KnownLimit, ...] = ()
    reason: str = ""
    created_at: str = ""

    def __post_init__(self) -> None:
        if not self.candidate_id or not self.candidate_id.strip():
            raise ValueError("candidate_id must not be empty")
        if not self.proposed_claim_text or not self.proposed_claim_text.strip():
            raise ValueError("proposed_claim_text must not be empty")
        if not self.capability_id or not self.capability_id.strip():
            raise ValueError("capability_id must not be empty")
        if not self.source_evaluation_run_result_ref or not self.source_evaluation_run_result_ref.strip():
            raise ValueError("source_evaluation_run_result_ref must not be empty")
        if not self.source_capability_evidence_id or not self.source_capability_evidence_id.strip():
            raise ValueError("source_capability_evidence_id must not be empty")
        if not self.reason or not self.reason.strip():
            raise ValueError("reason must not be empty")
        if not self.created_at or not self.created_at.strip():
            raise ValueError("created_at must not be empty")


# ---------------------------------------------------------------------------
# CapabilityClaimDecision
# ---------------------------------------------------------------------------


class CapabilityClaimDecisionKind(str, Enum):
    ACCEPT = "accept"
    REJECT = "reject"
    NEEDS_REVIEW = "needs_review"


@dataclass(frozen=True)
class CapabilityClaimDecision:
    """Keeps claim promotion governed and auditable.

    For P1.5.16, decisions are deterministic/system-stub only.
    Operator feedback comes later in P1.5.17.
    """

    decision_id: str
    candidate_id: str
    decision: CapabilityClaimDecisionKind
    decided_by: str
    reason: str = ""
    created_at: str = ""

    def __post_init__(self) -> None:
        if not self.decision_id or not self.decision_id.strip():
            raise ValueError("decision_id must not be empty")
        if not self.candidate_id or not self.candidate_id.strip():
            raise ValueError("candidate_id must not be empty")
        if not self.decided_by or not self.decided_by.strip():
            raise ValueError("decided_by must not be empty")
        if not self.reason or not self.reason.strip():
            raise ValueError("reason must not be empty")
        if not self.created_at or not self.created_at.strip():
            raise ValueError("created_at must not be empty")


# ---------------------------------------------------------------------------
# CapabilityClaimReport
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CapabilityClaimReport:
    """Lets Aurel explain what it can claim and why.

    Must not say or imply universal capability unless scope explicitly supports it.
    """

    report_id: str
    claim_id: str
    status: CapabilityClaimStatus
    claim_text: str
    scope_summary: str
    evidence_summary: str
    limitations: tuple[str, ...] = ()
    verified_context_count: int = 0
    warnings: tuple[str, ...] = ()
    created_at: str = ""

    def __post_init__(self) -> None:
        if not self.report_id or not self.report_id.strip():
            raise ValueError("report_id must not be empty")
        if not self.claim_id or not self.claim_id.strip():
            raise ValueError("claim_id must not be empty")
        if not self.claim_text or not self.claim_text.strip():
            raise ValueError("claim_text must not be empty")
        if not self.scope_summary or not self.scope_summary.strip():
            raise ValueError("scope_summary must not be empty")
        if not self.evidence_summary or not self.evidence_summary.strip():
            raise ValueError("evidence_summary must not be empty")
        if not self.created_at or not self.created_at.strip():
            raise ValueError("created_at must not be empty")


# ---------------------------------------------------------------------------
# CapabilityClaimRegistry (minimal in-memory)
# ---------------------------------------------------------------------------


class CapabilityClaimRegistry:
    """Minimal in-memory claim registry.

    Enforces candidate-before-decision rule:
      - Evaluation output → CapabilityClaimCandidate
      - Candidate + Decision → CapabilityClaim (only when accepted)
      - Rejected / needs_review candidates do not create claims.
    """

    def __init__(self) -> None:
        self._claims: dict[str, CapabilityClaim] = {}
        self._candidates: dict[str, CapabilityClaimCandidate] = {}
        self._decisions: dict[str, CapabilityClaimDecision] = {}

    def propose(self, candidate: CapabilityClaimCandidate) -> CapabilityClaimCandidate:
        """Register a proposed capability claim candidate."""
        self._candidates[candidate.candidate_id] = candidate
        return candidate

    def decide(
        self, candidate_id: str, decision: CapabilityClaimDecision
    ) -> CapabilityClaimDecision:
        """Record a decision on a candidate."""
        if candidate_id not in self._candidates:
            raise KeyError(f"candidate {candidate_id} not found")
        self._decisions[decision.decision_id] = decision
        return decision

    def apply_decision(
        self,
        decision: CapabilityClaimDecision,
        *,
        evidence_link: ClaimEvidenceLink | None = None,
    ) -> CapabilityClaim | None:
        """Apply an accepted decision to create/update a claim.

        Returns None if the decision is not accepted (rejected/needs_review).
        """
        if decision.decision != CapabilityClaimDecisionKind.ACCEPT:
            return None

        candidate = self._candidates.get(decision.candidate_id)
        if candidate is None:
            raise KeyError(f"candidate {decision.candidate_id} not found")

        scope = candidate.proposed_scope or CapabilityClaimScope(
            task_type=candidate.capability_id
        )

        evidence_links: tuple[ClaimEvidenceLink, ...] = ()
        if evidence_link is not None:
            evidence_links = (evidence_link,)

        claim = CapabilityClaim(
            claim_id=candidate.candidate_id,
            capability_id=candidate.capability_id,
            claim_text=candidate.proposed_claim_text,
            status=candidate.proposed_status,
            scope=scope,
            evidence_links=evidence_links,
            known_limits=candidate.proposed_limits,
            created_at=candidate.created_at,
            updated_at=candidate.created_at,
        )
        self._claims[claim.claim_id] = claim
        return claim

    def get_claim(self, claim_id: str) -> CapabilityClaim:
        return self._claims[claim_id]

    def list_claims(
        self, status: CapabilityClaimStatus | None = None
    ) -> list[CapabilityClaim]:
        if status is None:
            return list(self._claims.values())
        return [c for c in self._claims.values() if c.status == status]

    def get_candidate(self, candidate_id: str) -> CapabilityClaimCandidate:
        return self._candidates[candidate_id]

    def get_decision(self, decision_id: str) -> CapabilityClaimDecision:
        return self._decisions[decision_id]

    @property
    def claim_count(self) -> int:
        return len(self._claims)

    @property
    def candidate_count(self) -> int:
        return len(self._candidates)

    @property
    def decision_count(self) -> int:
        return len(self._decisions)


# ---------------------------------------------------------------------------
# Serialization helpers
# ---------------------------------------------------------------------------


def capability_claim_scope_to_dict(scope: CapabilityClaimScope) -> dict[str, object]:
    return {
        "task_type": scope.task_type,
        "allowed_contexts": list(scope.allowed_contexts),
        "required_inputs": list(scope.required_inputs),
        "allowed_tools": list(scope.allowed_tools),
        "required_verifier_kinds": list(scope.required_verifier_kinds),
        "risk_tier": scope.risk_tier,
        "autonomy_level": scope.autonomy_level,
        "environment_refs": list(scope.environment_refs),
    }


def known_limit_to_dict(limit: KnownLimit) -> dict[str, object]:
    return {
        "limit_id": limit.limit_id,
        "description": limit.description,
        "severity": limit.severity,
        "source_ref": limit.source_ref,
        "created_at": limit.created_at,
    }


def verified_context_to_dict(vc: VerifiedContext) -> dict[str, object]:
    return {
        "context_id": vc.context_id,
        "context_summary": vc.context_summary,
        "source_trace_event_ref": asdict(vc.source_trace_event_ref),
        "evaluation_run_result_ref": vc.evaluation_run_result_ref,
        "evidence_refs": list(vc.evidence_refs),
        "verifier_result_refs": list(vc.verifier_result_refs),
        "created_at": vc.created_at,
    }


def claim_evidence_link_to_dict(link: ClaimEvidenceLink) -> dict[str, object]:
    return {
        "link_id": link.link_id,
        "capability_evidence_id": link.capability_evidence_id,
        "source_trace_event_ref": asdict(link.source_trace_event_ref),
        "source_event_hash": link.source_event_hash,
        "evidence_refs": list(link.evidence_refs),
        "verifier_result_refs": list(link.verifier_result_refs),
        "evaluation_case_refs": list(link.evaluation_case_refs),
        "evaluation_run_result_refs": list(link.evaluation_run_result_refs),
        "brain_aware_context_ref": link.brain_aware_context_ref,
    }


def capability_claim_to_dict(claim: CapabilityClaim) -> dict[str, object]:
    return {
        "claim_id": claim.claim_id,
        "capability_id": claim.capability_id,
        "claim_text": claim.claim_text,
        "status": claim.status.value,
        "scope": capability_claim_scope_to_dict(claim.scope),
        "evidence_links": [claim_evidence_link_to_dict(e) for e in claim.evidence_links],
        "verified_contexts": [verified_context_to_dict(v) for v in claim.verified_contexts],
        "known_limits": [known_limit_to_dict(kp) for kp in claim.known_limits],
        "confidence_label": claim.confidence_label,
        "created_at": claim.created_at,
        "updated_at": claim.updated_at,
    }


def capability_claim_candidate_to_dict(
    candidate: CapabilityClaimCandidate,
) -> dict[str, object]:
    return {
        "candidate_id": candidate.candidate_id,
        "proposed_claim_text": candidate.proposed_claim_text,
        "capability_id": candidate.capability_id,
        "source_evaluation_run_result_ref": candidate.source_evaluation_run_result_ref,
        "source_capability_evidence_id": candidate.source_capability_evidence_id,
        "proposed_status": candidate.proposed_status.value,
        "proposed_scope": (
            capability_claim_scope_to_dict(candidate.proposed_scope)
            if candidate.proposed_scope else None
        ),
        "proposed_limits": [known_limit_to_dict(kp) for kp in candidate.proposed_limits],
        "reason": candidate.reason,
        "created_at": candidate.created_at,
    }


def capability_claim_report_to_dict(report: CapabilityClaimReport) -> dict[str, object]:
    return {
        "report_id": report.report_id,
        "claim_id": report.claim_id,
        "status": report.status.value,
        "claim_text": report.claim_text,
        "scope_summary": report.scope_summary,
        "evidence_summary": report.evidence_summary,
        "limitations": list(report.limitations),
        "verified_context_count": report.verified_context_count,
        "warnings": list(report.warnings),
        "created_at": report.created_at,
    }
