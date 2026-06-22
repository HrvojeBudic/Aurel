"""P1.5.16 Capability claim status derivation from evaluation results.

Converts evaluation outputs into bounded CapabilityClaimCandidates.
The derivation is deterministic: same inputs always produce same proposed status.
It never overclaims (verified candidate / universal verified) from a single
Golden Thread result.
"""
from __future__ import annotations

import uuid

from agentic_runtime.contracts.capability import (
    CapabilityEvidenceRecord,
    CapabilityEvidenceStatus,
    EvidenceStrengthLevel,
)
from agentic_runtime.contracts.capability_claims import (
    CapabilityClaimCandidate,
    CapabilityClaimRegistry,
    CapabilityClaimScope,
    CapabilityClaimStatus,
    KnownLimit,
)
from agentic_runtime.contracts.context import ContextAdequacyReport, ContextAdequacyStatus
from agentic_runtime.contracts.evaluation_context import (
    BrainAwareEvaluationContext,
    ContextRiskLevel,
    EvaluationFailureReason,
)
from agentic_runtime.contracts.evaluation_runtime import (
    EvaluationRunResult,
    EvaluationRunStatus,
)
from agentic_runtime.contracts.trace import TraceEventRef
from agentic_runtime.contracts.verifier import (
    VerifierResult,
    VerifierResultStatus,
)

_DERIVATION_TIMESTAMP = "2026-06-22T00:00:00+00:00"


def _new_candidate_id() -> str:
    return f"cand_{uuid.uuid4().hex[:12]}"


def _new_limit_id() -> str:
    return f"limit_{uuid.uuid4().hex[:12]}"


# ---------------------------------------------------------------------------
# derive_capability_claim_candidate
# ---------------------------------------------------------------------------


def derive_capability_claim_candidate(
    *,
    evaluation_result: EvaluationRunResult,
    brain_context: BrainAwareEvaluationContext,
    capability_evidence: CapabilityEvidenceRecord | None = None,
    verifier_result: VerifierResult | None = None,
    context_adequacy: ContextAdequacyReport | None = None,
    capability_id: str = "",
    claim_text_prefix: str = "",
) -> CapabilityClaimCandidate:
    """Derive a CapabilityClaimCandidate from evaluation output.

    Rules (in priority order):
    1. UNSAFE context or CRITICAL risk → cannot create positive claim → FAILED
    2. Verifier FAILED or EvaluationRunResult FAILED → FAILED
    3. context_adequacy INSUFFICIENT → FAILED
    4. EvidenceStrength weak/moderate/none → WEAKLY_SUPPORTED
    5. EvaluationRunResult INCONCLUSIVE → EXPERIMENTAL
    6. CONTEXT_VERIFIED when everything passes (default Golden Thread A)
    7. VERIFIED_CANDIDATE and VERIFIED are explicitly NOT derived by default
    """
    classification = brain_context.failure_classification

    # Rule 1: Unsafe / critical context blocks positive claims entirely
    if (
        context_adequacy is not None
        and context_adequacy.status == ContextAdequacyStatus.UNSAFE
    ):
        return _build_candidate(
            capability_id=capability_id,
            claim_text_prefix=claim_text_prefix,
            proposed_status=CapabilityClaimStatus.FAILED,
            reason="Unsafe context blocks positive capability claims.",
            evaluation_result=evaluation_result,
            capability_evidence=capability_evidence,
            limits=(
                KnownLimit(
                    limit_id=_new_limit_id(),
                    description="Context is unsafe — capability cannot be claimed.",
                    severity="blocking",
                    created_at=_DERIVATION_TIMESTAMP,
                ),
            ),
        )

    if classification.context_risk_level == ContextRiskLevel.CRITICAL:
        return _build_candidate(
            capability_id=capability_id,
            claim_text_prefix=claim_text_prefix,
            proposed_status=CapabilityClaimStatus.FAILED,
            reason=f"Critical context risk ({classification.primary_reason.value}) blocks positive claims.",
            evaluation_result=evaluation_result,
            capability_evidence=capability_evidence,
            limits=(
                KnownLimit(
                    limit_id=_new_limit_id(),
                    description=f"Context risk is critical: {classification.primary_reason.value}.",
                    severity="blocking",
                    created_at=_DERIVATION_TIMESTAMP,
                ),
            ),
        )

    # Rule 2: Verifier failed
    if (
        verifier_result is not None
        and verifier_result.status == VerifierResultStatus.FAIL
    ):
        return _build_candidate(
            capability_id=capability_id,
            claim_text_prefix=claim_text_prefix,
            proposed_status=CapabilityClaimStatus.FAILED,
            reason="Verifier failed — capability claim cannot be positive.",
            evaluation_result=evaluation_result,
            capability_evidence=capability_evidence,
            limits=(
                KnownLimit(
                    limit_id=_new_limit_id(),
                    description="Verifier result is FAIL.",
                    severity="blocking",
                    created_at=_DERIVATION_TIMESTAMP,
                ),
            ),
        )

    # Rule 2b: EvaluationRunResult FAILED
    if evaluation_result.status == EvaluationRunStatus.FAILED:
        return _build_candidate(
            capability_id=capability_id,
            claim_text_prefix=claim_text_prefix,
            proposed_status=CapabilityClaimStatus.FAILED,
            reason="Evaluation result is failed.",
            evaluation_result=evaluation_result,
            capability_evidence=capability_evidence,
            limits=(
                KnownLimit(
                    limit_id=_new_limit_id(),
                    description="Evaluation result status is FAILED.",
                    severity="blocking",
                    created_at=_DERIVATION_TIMESTAMP,
                ),
            ),
        )

    # Rule 3: context_adequacy INSUFFICIENT
    if (
        context_adequacy is not None
        and context_adequacy.status == ContextAdequacyStatus.INSUFFICIENT
    ):
        return _build_candidate(
            capability_id=capability_id,
            claim_text_prefix=claim_text_prefix,
            proposed_status=CapabilityClaimStatus.FAILED,
            reason="Insufficient context — cannot make positive claim.",
            evaluation_result=evaluation_result,
            capability_evidence=capability_evidence,
            limits=(
                KnownLimit(
                    limit_id=_new_limit_id(),
                    description="Context adequacy is INSUFFICIENT.",
                    severity="blocking",
                    created_at=_DERIVATION_TIMESTAMP,
                ),
            ),
        )

    # Rule 4: Weak evidence
    if capability_evidence is not None and capability_evidence.evidence_strength in (
        EvidenceStrengthLevel.NONE,
        EvidenceStrengthLevel.WEAK,
        EvidenceStrengthLevel.MODERATE,
    ):
        return _build_candidate(
            capability_id=capability_id,
            claim_text_prefix=claim_text_prefix,
            proposed_status=CapabilityClaimStatus.WEAKLY_SUPPORTED,
            reason=f"Evidence strength is {capability_evidence.evidence_strength.value}.",
            evaluation_result=evaluation_result,
            capability_evidence=capability_evidence,
            limits=(
                KnownLimit(
                    limit_id=_new_limit_id(),
                    description=f"Evidence strength is only {capability_evidence.evidence_strength.value}.",
                    severity="warning",
                    created_at=_DERIVATION_TIMESTAMP,
                ),
                KnownLimit(
                    limit_id=_new_limit_id(),
                    description="Weakly supported claims are not verified and may not generalize.",
                    severity="warning",
                    created_at=_DERIVATION_TIMESTAMP,
                ),
            ),
        )

    # Rule 5: Inconclusive result
    if evaluation_result.status == EvaluationRunStatus.INCONCLUSIVE:
        return _build_candidate(
            capability_id=capability_id,
            claim_text_prefix=claim_text_prefix,
            proposed_status=CapabilityClaimStatus.EXPERIMENTAL,
            reason="Evaluation result is inconclusive.",
            evaluation_result=evaluation_result,
            capability_evidence=capability_evidence,
            limits=(
                KnownLimit(
                    limit_id=_new_limit_id(),
                    description="Evaluation was inconclusive — claim is experimental only.",
                    severity="warning",
                    created_at=_DERIVATION_TIMESTAMP,
                ),
            ),
        )

    # Rule 6: Verifier inconclusive
    if (
        verifier_result is not None
        and verifier_result.status == VerifierResultStatus.INCONCLUSIVE
    ):
        return _build_candidate(
            capability_id=capability_id,
            claim_text_prefix=claim_text_prefix,
            proposed_status=CapabilityClaimStatus.EXPERIMENTAL,
            reason="Verifier result is inconclusive.",
            evaluation_result=evaluation_result,
            capability_evidence=capability_evidence,
            limits=(
                KnownLimit(
                    limit_id=_new_limit_id(),
                    description="Verifier was inconclusive — claim is experimental only.",
                    severity="warning",
                    created_at=_DERIVATION_TIMESTAMP,
                ),
            ),
        )

    # Rule 7: Partial context → experimental
    if (
        context_adequacy is not None
        and context_adequacy.status == ContextAdequacyStatus.PARTIAL
    ):
        return _build_candidate(
            capability_id=capability_id,
            claim_text_prefix=claim_text_prefix,
            proposed_status=CapabilityClaimStatus.EXPERIMENTAL,
            reason="Context adequacy is partial.",
            evaluation_result=evaluation_result,
            capability_evidence=capability_evidence,
            limits=(
                KnownLimit(
                    limit_id=_new_limit_id(),
                    description="Context adequacy is PARTIAL — claim is experimental only.",
                    severity="warning",
                    created_at=_DERIVATION_TIMESTAMP,
                ),
            ),
        )

    # Rule 8: NEEDS_REVIEW → experimental
    if evaluation_result.status == EvaluationRunStatus.NEEDS_REVIEW:
        return _build_candidate(
            capability_id=capability_id,
            claim_text_prefix=claim_text_prefix,
            proposed_status=CapabilityClaimStatus.EXPERIMENTAL,
            reason="Evaluation result needs review.",
            evaluation_result=evaluation_result,
            capability_evidence=capability_evidence,
            limits=(
                KnownLimit(
                    limit_id=_new_limit_id(),
                    description="Evaluation needs review — claim is experimental only.",
                    severity="warning",
                    created_at=_DERIVATION_TIMESTAMP,
                ),
            ),
        )

    # Rule 9: Golden Thread A default — PASSED, context ADEQUATE, verifier PASS,
    # evidence STRONG/VERIFIED
    limits = (
        KnownLimit(
            limit_id=_new_limit_id(),
            description="Claim derived from a single Golden Thread A run. "
            "It is context-verified only under the explicit scope of that run. "
            "This is NOT universal verified capability.",
            severity="warning",
            created_at=_DERIVATION_TIMESTAMP,
        ),
        KnownLimit(
            limit_id=_new_limit_id(),
            description="Context_verified does not mean universally capable. "
            "This claim applies only under the documented scope and conditions.",
            severity="warning",
            created_at=_DERIVATION_TIMESTAMP,
        ),
        KnownLimit(
            limit_id=_new_limit_id(),
            description="This claim is trace-bound, evidence-bound, "
            "verifier-bound, and limitation-bound.",
            severity="info",
            created_at=_DERIVATION_TIMESTAMP,
        ),
    )

    return _build_candidate(
        capability_id=capability_id,
        claim_text_prefix=claim_text_prefix,
        proposed_status=CapabilityClaimStatus.CONTEXT_VERIFIED,
        reason=(
            "Golden Thread A evaluation passed with adequate context, "
            "strong/verified evidence, and passed verifier. "
            "Claim is context_verified, NOT universal verified."
        ),
        evaluation_result=evaluation_result,
        capability_evidence=capability_evidence,
        limits=limits,
    )


# ---------------------------------------------------------------------------
# _build_candidate helper
# ---------------------------------------------------------------------------


def _build_candidate(
    *,
    capability_id: str,
    claim_text_prefix: str,
    proposed_status: CapabilityClaimStatus,
    reason: str,
    evaluation_result: EvaluationRunResult,
    capability_evidence: CapabilityEvidenceRecord | None = None,
    limits: tuple[KnownLimit, ...] = (),
) -> CapabilityClaimCandidate:
    cap_id = capability_id or (
        capability_evidence.capability_id if capability_evidence else "capability.unknown"
    )
    claim_text = (
        f"{claim_text_prefix}: Capability claim for {cap_id} "
        f"is {proposed_status.value}."
    ) if claim_text_prefix else (
        f"Capability claim for {cap_id} is {proposed_status.value}."
    )

    scope = CapabilityClaimScope(
        task_type=cap_id,
        allowed_contexts=("golden_thread_a_stub",),
        required_verifier_kinds=("evidence_integrity",),
    )

    return CapabilityClaimCandidate(
        candidate_id=_new_candidate_id(),
        proposed_claim_text=claim_text,
        capability_id=cap_id,
        source_evaluation_run_result_ref=evaluation_result.run_id,
        source_capability_evidence_id=(
            capability_evidence.capability_evidence_id if capability_evidence else ""
        ),
        proposed_status=proposed_status,
        proposed_scope=scope,
        proposed_limits=limits,
        reason=reason,
        created_at=_DERIVATION_TIMESTAMP,
    )
