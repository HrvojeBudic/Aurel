"""P1.5.18 Evaluation <-> Memory Candidate Bridge.

Derives MemoryCandidate records from evaluation, feedback, and capability outputs.
MemoryCandidate is NOT committed memory. It is NOT active recall.
It does NOT create skills, reflexes, policies, or canon.
"""
from __future__ import annotations

import uuid

from agentic_runtime.contracts.capability_claims import (
    CapabilityClaim,
    CapabilityClaimReport,
)
from agentic_runtime.contracts.memory_candidates import (
    MemoryCandidate,
    MemoryCandidateBridgeReport,
    MemoryCandidateEvidenceLink,
    MemoryCandidateRiskClass,
    MemoryCandidateScope,
    MemoryCandidateScopeType,
    MemoryCandidateSourceType,
    MemoryCandidateStatus,
    MemoryCandidateType,
    MemoryCandidateValidationReport,
)
from agentic_runtime.contracts.operator_feedback import (
    FeedbackCandidateAction,
    FeedbackProcessingReport,
    OperatorFeedbackRecord,
    OperatorFeedbackType,
)
from agentic_runtime.contracts.trace import TraceEventRef

_BRIDGE_TIMESTAMP = "2026-06-22T00:00:00+00:00"


def _new_mem_id() -> str:
    return f"mem_{uuid.uuid4().hex[:12]}"


def _new_report_id() -> str:
    return f"mem_report_{uuid.uuid4().hex[:12]}"


def _new_validation_id() -> str:
    return f"mem_val_{uuid.uuid4().hex[:12]}"


def derive_memory_candidates(
    *,
    operator_feedback: OperatorFeedbackRecord | None = None,
    feedback_report: FeedbackProcessingReport | None = None,
    capability_claim: CapabilityClaim | None = None,
    capability_claim_report: CapabilityClaimReport | None = None,
    trace_event_ref: TraceEventRef | None = None,
) -> MemoryCandidateBridgeReport:
    """Derive MemoryCandidate records from available sources.

    Creates candidates only - never commits memory, never enters retrieval,
    never creates skills/reflexes/policies.
    """
    created_ids: list[str] = []
    blocked_ids: list[str] = []
    validation_ids: list[str] = []
    warnings: list[str] = []
    reason_parts: list[str] = []

    trace_ref = trace_event_ref or (
        operator_feedback.source_trace_event_ref if operator_feedback else None
    )
    source_event_hash = trace_ref.event_hash if trace_ref else ""
    source_ref = "memory_bridge_default"

    # --- From operator feedback + feedback report ---
    if feedback_report is not None and operator_feedback is not None:
        fb_type = operator_feedback.feedback_type
        source_ref = operator_feedback.feedback_id

        # Operator says "remember this"
        if (
            FeedbackCandidateAction.CREATE_MEMORY_CANDIDATE in feedback_report.candidate_actions
            or fb_type == OperatorFeedbackType.MEMORY_CANDIDATE
        ):
            cand, val = _build_candidate(
                candidate_type=MemoryCandidateType.OPERATOR_PREFERENCE,
                status=MemoryCandidateStatus.NEEDS_REVIEW,
                source_type=MemoryCandidateSourceType.OPERATOR_FEEDBACK,
                scope_type=MemoryCandidateScopeType.OPERATOR,
                proposed_text=operator_feedback.raw_text or "Operator requested memory.",
                risk_class=MemoryCandidateRiskClass.MEDIUM,
                trace_ref=trace_ref,
                source_event_hash=source_event_hash,
                review_reason="Operator explicitly requested a memory candidate.",
            )
            if cand is not None:
                created_ids.append(cand.memory_candidate_id)
                validation_ids.append(val.validation_id)
                reason_parts.append("Created operator_preference memory candidate.")
            else:
                blocked_ids.append("operator_preference_blocked")

        # Correction
        if fb_type == OperatorFeedbackType.CORRECTION:
            cand, val = _build_candidate(
                candidate_type=MemoryCandidateType.OPERATOR_CORRECTION,
                status=MemoryCandidateStatus.NEEDS_REVIEW,
                source_type=MemoryCandidateSourceType.OPERATOR_FEEDBACK,
                scope_type=MemoryCandidateScopeType.OPERATOR,
                proposed_text=(
                    operator_feedback.correction_text or operator_feedback.raw_text
                    or "Operator correction."
                ),
                risk_class=MemoryCandidateRiskClass.MEDIUM,
                trace_ref=trace_ref,
                source_event_hash=source_event_hash,
                review_reason="Operator provided a correction.",
            )
            if cand is not None:
                created_ids.append(cand.memory_candidate_id)
                validation_ids.append(val.validation_id)
                reason_parts.append("Created operator_correction memory candidate.")

        # Safety concern
        if fb_type == OperatorFeedbackType.SAFETY_CONCERN:
            cand, val = _build_candidate(
                candidate_type=MemoryCandidateType.SAFETY_NOTE,
                status=MemoryCandidateStatus.NEEDS_REVIEW,
                source_type=MemoryCandidateSourceType.OPERATOR_FEEDBACK,
                scope_type=MemoryCandidateScopeType.POLICY,
                proposed_text=(
                    operator_feedback.raw_text or "Safety concern raised."
                ),
                risk_class=MemoryCandidateRiskClass.AUTHORITY_SENSITIVE,
                trace_ref=trace_ref,
                source_event_hash=source_event_hash,
                review_reason="Safety concern requires authoritative review.",
            )
            if cand is not None:
                created_ids.append(cand.memory_candidate_id)
                validation_ids.append(val.validation_id)
                reason_parts.append("Created safety_note memory candidate (authority_sensitive).")
                warnings.append("Safety note candidate is authority_sensitive - review required.")

        # Policy concern
        if fb_type == OperatorFeedbackType.POLICY_CONCERN:
            cand, val = _build_candidate(
                candidate_type=MemoryCandidateType.POLICY_NOTE,
                status=MemoryCandidateStatus.NEEDS_REVIEW,
                source_type=MemoryCandidateSourceType.OPERATOR_FEEDBACK,
                scope_type=MemoryCandidateScopeType.POLICY,
                proposed_text=(
                    operator_feedback.raw_text or "Policy concern raised."
                ),
                risk_class=MemoryCandidateRiskClass.AUTHORITY_SENSITIVE,
                trace_ref=trace_ref,
                source_event_hash=source_event_hash,
                review_reason="Policy concern requires authoritative review.",
            )
            if cand is not None:
                created_ids.append(cand.memory_candidate_id)
                validation_ids.append(val.validation_id)
                reason_parts.append("Created policy_note memory candidate (authority_sensitive).")
                warnings.append("Policy note candidate is authority_sensitive - review required.")

    # --- From capability claim ---
    if capability_claim is not None:
        claim_ref = capability_claim.claim_id
        if not source_ref or source_ref == "memory_bridge_default":
            source_ref = claim_ref

        # Capability with limitations -> limitation_note
        if capability_claim_report is not None and capability_claim_report.limitations:
            cand, val = _build_candidate(
                candidate_type=MemoryCandidateType.LIMITATION_NOTE,
                status=MemoryCandidateStatus.CANDIDATE,
                source_type=MemoryCandidateSourceType.CAPABILITY_CLAIM,
                scope_type=MemoryCandidateScopeType.CAPABILITY,
                proposed_text=(
                    f"Capability {capability_claim.capability_id} has known limitations: "
                    f"{', '.join(capability_claim_report.limitations)}"
                ),
                risk_class=MemoryCandidateRiskClass.LOW,
                trace_ref=trace_ref,
                source_event_hash=source_event_hash,
                capability_id=capability_claim.capability_id,
            )
            if cand is not None:
                created_ids.append(cand.memory_candidate_id)
                validation_ids.append(val.validation_id)
                reason_parts.append("Created limitation_note memory candidate.")

        # Capability lesson from the claim itself
        cand, val = _build_candidate(
            candidate_type=MemoryCandidateType.CAPABILITY_LESSON,
            status=MemoryCandidateStatus.CANDIDATE,
            source_type=MemoryCandidateSourceType.CAPABILITY_CLAIM,
            scope_type=MemoryCandidateScopeType.CAPABILITY,
            proposed_text=(
                f"Capability {capability_claim.capability_id} is {capability_claim.status.value} "
                f"under scope {capability_claim.scope.task_type}. "
                "This is a governed capability claim, not universal capability."
            ),
            risk_class=MemoryCandidateRiskClass.LOW,
            trace_ref=trace_ref,
            source_event_hash=source_event_hash,
            capability_id=capability_claim.capability_id,
        )
        if cand is not None:
            created_ids.append(cand.memory_candidate_id)
            validation_ids.append(val.validation_id)
            reason_parts.append("Created capability_lesson memory candidate.")

    # --- Assemble report ---
    if reason_parts:
        reason = ". ".join(reason_parts) + "."
    else:
        reason = "No memory candidates derived from available sources."

    return MemoryCandidateBridgeReport(
        report_id=_new_report_id(),
        source_ref=source_ref,
        reason=reason,
        created_memory_candidate_ids=tuple(created_ids),
        blocked_candidate_ids=tuple(blocked_ids),
        validation_report_ids=tuple(validation_ids),
        warnings=tuple(warnings),
        errors=(),
        created_at=_BRIDGE_TIMESTAMP,
    )


def _build_candidate(
    *,
    candidate_type: MemoryCandidateType,
    status: MemoryCandidateStatus,
    source_type: MemoryCandidateSourceType,
    scope_type: MemoryCandidateScopeType,
    proposed_text: str,
    risk_class: MemoryCandidateRiskClass,
    trace_ref: TraceEventRef | None,
    source_event_hash: str,
    review_reason: str | None = None,
    capability_id: str | None = None,
) -> tuple[MemoryCandidate | None, MemoryCandidateValidationReport]:
    """Build a MemoryCandidate and its validation report.

    Returns (None, validation_report) if the candidate fails validation.
    """
    mem_id = _new_mem_id()
    val_id = _new_validation_id()

    scope = MemoryCandidateScope(
        scope_type=scope_type,
        allowed_use_contexts=("future_review", "evaluation_context"),
        capability_id=capability_id,
    )

    evidence_links: tuple[MemoryCandidateEvidenceLink, ...] = ()
    if trace_ref is not None and source_event_hash:
        evidence_links = (
            MemoryCandidateEvidenceLink(
                link_id=f"link_{mem_id}",
                source_trace_event_ref=trace_ref,
                source_event_hash=source_event_hash,
                evidence_refs=(),
            ),
        )

    limitations: list[str] = [
        "This is a memory candidate only - NOT committed memory.",
        "This candidate may not become active recall without future governed review.",
        "P1.5.18 does not implement memory retrieval, ranking, consolidation, or decay.",
    ]
    if candidate_type == MemoryCandidateType.OPERATOR_CORRECTION:
        limitations.append(
            "Operator correction does not rewrite canonical trace or overwrite committed memory."
        )
    if candidate_type in (
        MemoryCandidateType.SAFETY_NOTE,
        MemoryCandidateType.POLICY_NOTE,
    ):
        limitations.append(
            "Safety/policy note does not mutate policy, canonize roadmap, or auto-block execution."
        )

    try:
        candidate = MemoryCandidate(
            memory_candidate_id=mem_id,
            candidate_type=candidate_type,
            status=status,
            source_type=source_type,
            scope=scope,
            proposed_memory_text=proposed_text,
            risk_class=risk_class,
            limitations=tuple(limitations),
            evidence_links=evidence_links,
            review_reason=review_reason,
            created_at=_BRIDGE_TIMESTAMP,
        )
    except ValueError as exc:
        val = MemoryCandidateValidationReport(
            validation_id=val_id,
            memory_candidate_id=mem_id,
            is_valid=False,
            risk_class=risk_class,
            required_review=True,
            blocked_reasons=(str(exc),),
            warnings=(f"Candidate blocked: {exc}",),
            created_at=_BRIDGE_TIMESTAMP,
        )
        return None, val

    # Build validation report
    is_valid = True
    required_review = risk_class in (
        MemoryCandidateRiskClass.SENSITIVE,
        MemoryCandidateRiskClass.AUTHORITY_SENSITIVE,
    )
    blocked_reasons: list[str] = []

    val = MemoryCandidateValidationReport(
        validation_id=val_id,
        memory_candidate_id=mem_id,
        is_valid=is_valid,
        risk_class=risk_class,
        required_review=required_review,
        blocked_reasons=tuple(blocked_reasons),
        warnings=(),
        created_at=_BRIDGE_TIMESTAMP,
    )

    return candidate, val
