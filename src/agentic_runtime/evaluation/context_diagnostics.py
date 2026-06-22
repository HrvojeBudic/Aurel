"""P1.5.15 Deterministic brain/context diagnostics for Evaluation Mirror.

classify_evaluation_context() examines explicit trace/context/evidence/verifier
signals and produces a BrainAwareEvaluationContext without open-domain cognition,
semantic reasoning, LLMs, NLI, or Theory-of-Mind.
"""
from __future__ import annotations

import uuid
from typing import Any, Optional, Union

from agentic_runtime.contracts.capability import (
    CapabilityEvidenceRecord,
    EvidenceStrengthLevel,
)
from agentic_runtime.contracts.context import (
    ContextAdequacyReport,
    ContextAdequacyStatus,
    ContextBindingRef,
)
from agentic_runtime.contracts.evaluation_context import (
    BrainAwareEvaluationContext,
    ContextRiskLevel,
    ContextSignal,
    EvaluationContextSnapshot,
    EvaluationFailureClassification,
    EvaluationFailureReason,
)
from agentic_runtime.contracts.trace import TraceEventRef
from agentic_runtime.contracts.verifier import (
    VerifierResult,
    VerifierResultStatus,
)

_DIAGNOSTICS_TIMESTAMP = "2026-06-22T00:00:00+00:00"


def _new_classification_id() -> str:
    return f"class_{uuid.uuid4().hex[:12]}"


def _new_signal_id() -> str:
    return f"signal_{uuid.uuid4().hex[:12]}"


def _new_snapshot_id() -> str:
    return f"snap_{uuid.uuid4().hex[:12]}"


def _new_brain_id() -> str:
    return f"brain_{uuid.uuid4().hex[:12]}"


# ---------------------------------------------------------------------------
# Signal helpers
# ---------------------------------------------------------------------------


def _make_signal(
    *,
    signal_type: str,
    severity: str,
    reason: str,
    source_ref: str | None = None,
) -> ContextSignal:
    return ContextSignal(
        signal_id=_new_signal_id(),
        signal_type=signal_type,
        severity=severity,
        reason=reason,
        source_ref=source_ref,
        created_at=_DIAGNOSTICS_TIMESTAMP,
    )


# ---------------------------------------------------------------------------
# Classification result helper
# ---------------------------------------------------------------------------


def _build_classification(
    *,
    primary_reason: EvaluationFailureReason,
    context_risk_level: ContextRiskLevel,
    signals: tuple[ContextSignal, ...],
    secondary_reasons: tuple[str, ...] = (),
    requires_operator_clarification: bool = False,
    blocks_verified_capability: bool = False,
    blocks_positive_eval_case: bool = False,
) -> EvaluationFailureClassification:
    """Construct a failure classification with automatic signal validation."""
    if primary_reason == EvaluationFailureReason.NONE:
        return EvaluationFailureClassification(
            classification_id=_new_classification_id(),
            primary_reason=EvaluationFailureReason.NONE,
            secondary_reasons=(),
            context_risk_level=ContextRiskLevel.LOW,
            signals=(),
            requires_operator_clarification=False,
            blocks_verified_capability=False,
            blocks_positive_eval_case=False,
            created_at=_DIAGNOSTICS_TIMESTAMP,
        )
    return EvaluationFailureClassification(
        classification_id=_new_classification_id(),
        primary_reason=primary_reason,
        secondary_reasons=secondary_reasons,
        context_risk_level=context_risk_level,
        signals=signals,
        requires_operator_clarification=requires_operator_clarification,
        blocks_verified_capability=blocks_verified_capability,
        blocks_positive_eval_case=blocks_positive_eval_case,
        created_at=_DIAGNOSTICS_TIMESTAMP,
    )


# ---------------------------------------------------------------------------
# Main classifier
# ---------------------------------------------------------------------------


def classify_evaluation_context(
    *,
    context_binding_ref: ContextBindingRef | None = None,
    context_adequacy_report: ContextAdequacyReport | None = None,
    verifier_results: tuple[VerifierResult, ...] = (),
    capability_evidence: CapabilityEvidenceRecord | None = None,
    trace_event_ref: TraceEventRef | None = None,
    source_event_hash: str | None = None,
) -> tuple[BrainAwareEvaluationContext, EvaluationContextSnapshot, EvaluationFailureClassification]:
    """Classify why an evaluation passed, failed, or needs review.

    Uses only explicit trace/context/evidence/verifier signals.
    Never performs open-domain cognition, semantic reasoning, LLM calls, or NLI.

    Returns:
        (BrainAwareEvaluationContext, EvaluationContextSnapshot, EvaluationFailureClassification)
    """
    # --- Build snapshot ---
    safe_trace_ref = trace_event_ref
    if safe_trace_ref is None and capability_evidence is not None:
        safe_trace_ref = capability_evidence.source_trace_event_ref
    if safe_trace_ref is None and verifier_results:
        safe_trace_ref = verifier_results[0].source_trace_event_ref

    if safe_trace_ref is None:
        raise ValueError("No TraceEventRef available — cannot build EvaluationContextSnapshot")

    snapshot = EvaluationContextSnapshot(
        snapshot_id=_new_snapshot_id(),
        source_trace_event_ref=safe_trace_ref,
        context_binding_ref=context_binding_ref.context_id if context_binding_ref else None,
        context_adequacy_ref=(
            context_adequacy_report.context_adequacy_id if context_adequacy_report else None
        ),
        verifier_result_refs=tuple(v.verifier_id for v in verifier_results),
        evidence_refs=capability_evidence.evidence_refs if capability_evidence and hasattr(capability_evidence, "evidence_refs") else (),
        capability_evidence_ref=capability_evidence.capability_evidence_id if capability_evidence else None,
        created_at=_DIAGNOSTICS_TIMESTAMP,
    )

    # --- Apply classification rules in priority order ---

    # Rule 1: Unsafe context
    if context_adequacy_report is not None and context_adequacy_report.status == ContextAdequacyStatus.UNSAFE:
        classification = _build_classification(
            primary_reason=EvaluationFailureReason.UNSAFE_CONTEXT,
            context_risk_level=ContextRiskLevel.CRITICAL,
            signals=(
                _make_signal(
                    signal_type="unsafe_context",
                    severity="critical",
                    reason=f"Context adequacy is unsafe: safe_to_act={context_adequacy_report.safe_to_act}",
                    source_ref=context_adequacy_report.context_adequacy_id,
                ),
            ),
            requires_operator_clarification=True,
            blocks_verified_capability=True,
            blocks_positive_eval_case=True,
        )
        return _assemble_brain(classification, snapshot)

    # Rule 2: Hash mismatch / trace integrity
    hash_ok = True
    if trace_event_ref is not None and source_event_hash is not None:
        hash_ok = source_event_hash == trace_event_ref.event_hash
    if capability_evidence is not None and capability_evidence.source_event_hash is not None:
        cap_ref = capability_evidence.source_trace_event_ref
        if cap_ref is not None:
            ev_hash = capability_evidence.source_event_hash
            if ev_hash != cap_ref.event_hash:
                hash_ok = False

    if not hash_ok:
        classification = _build_classification(
            primary_reason=EvaluationFailureReason.HASH_MISMATCH,
            context_risk_level=ContextRiskLevel.CRITICAL,
            signals=(
                _make_signal(
                    signal_type="hash_mismatch",
                    severity="critical",
                    reason="source_event_hash does not match TraceEventRef.event_hash",
                    source_ref=trace_event_ref.event_id if trace_event_ref else None,
                ),
            ),
            requires_operator_clarification=True,
            blocks_verified_capability=True,
            blocks_positive_eval_case=True,
        )
        return _assemble_brain(classification, snapshot)

    # Rule 3: Missing context
    if context_binding_ref is None or (
        context_adequacy_report is not None
        and context_adequacy_report.status == ContextAdequacyStatus.INSUFFICIENT
    ):
        signals: list[ContextSignal] = []
        if context_binding_ref is None:
            signals.append(
                _make_signal(
                    signal_type="missing_context",
                    severity="error",
                    reason="No context binding reference available.",
                )
            )
        if context_adequacy_report is not None and context_adequacy_report.status == ContextAdequacyStatus.INSUFFICIENT:
            signals.append(
                _make_signal(
                    signal_type="missing_context",
                    severity="error",
                    reason="Context adequacy is insufficient.",
                    source_ref=context_adequacy_report.context_adequacy_id,
                )
            )
        classification = _build_classification(
            primary_reason=EvaluationFailureReason.MISSING_CONTEXT,
            context_risk_level=ContextRiskLevel.HIGH,
            signals=tuple(signals),
            requires_operator_clarification=True,
            blocks_verified_capability=False,
            blocks_positive_eval_case=True,
        )
        return _assemble_brain(classification, snapshot)

    # Rule 4: Verifier failed
    failed_verifiers = [v for v in verifier_results if v.status == VerifierResultStatus.FAIL]
    if failed_verifiers:
        classification = _build_classification(
            primary_reason=EvaluationFailureReason.VERIFIER_FAILED,
            context_risk_level=ContextRiskLevel.HIGH,
            signals=tuple(
                _make_signal(
                    signal_type="verifier_failed",
                    severity="error",
                    reason=f"Verifier {v.verifier_id} ({v.verifier_kind.value}) failed: {v.reason}",
                    source_ref=v.verifier_id,
                )
                for v in failed_verifiers
            ),
            requires_operator_clarification=False,
            blocks_verified_capability=False,
            blocks_positive_eval_case=True,
        )
        return _assemble_brain(classification, snapshot)

    # Rule 5: Partial context
    if context_adequacy_report is not None and context_adequacy_report.status == ContextAdequacyStatus.PARTIAL:
        classification = _build_classification(
            primary_reason=EvaluationFailureReason.MISSING_CONTEXT,
            context_risk_level=ContextRiskLevel.MEDIUM,
            signals=(
                _make_signal(
                    signal_type="partial_context",
                    severity="warning",
                    reason="Context adequacy is partial.",
                    source_ref=context_adequacy_report.context_adequacy_id,
                ),
            ),
            requires_operator_clarification=True,
            blocks_verified_capability=False,
            blocks_positive_eval_case=True,
        )
        return _assemble_brain(classification, snapshot)

    # Rule 6: Weak evidence
    if capability_evidence is not None and capability_evidence.evidence_strength not in (
        EvidenceStrengthLevel.STRONG,
        EvidenceStrengthLevel.VERIFIED,
    ):
        strength_str = capability_evidence.evidence_strength.value
        classification = _build_classification(
            primary_reason=EvaluationFailureReason.WEAK_EVIDENCE,
            context_risk_level=ContextRiskLevel.MEDIUM,
            signals=(
                _make_signal(
                    signal_type="weak_evidence",
                    severity="warning",
                    reason=f"Evidence strength is {strength_str}.",
                    source_ref=capability_evidence.capability_evidence_id,
                ),
            ),
            requires_operator_clarification=False,
            blocks_verified_capability=False,
            blocks_positive_eval_case=True,
        )
        return _assemble_brain(classification, snapshot)

    # Rule 7: Verifier inconclusive
    inconclusive_verifiers = [v for v in verifier_results if v.status == VerifierResultStatus.INCONCLUSIVE]
    if inconclusive_verifiers:
        classification = _build_classification(
            primary_reason=EvaluationFailureReason.VERIFIER_INCONCLUSIVE,
            context_risk_level=ContextRiskLevel.MEDIUM,
            signals=tuple(
                _make_signal(
                    signal_type="verifier_inconclusive",
                    severity="warning",
                    reason=f"Verifier {v.verifier_id} ({v.verifier_kind.value}) is inconclusive: {v.reason}",
                    source_ref=v.verifier_id,
                )
                for v in inconclusive_verifiers
            ),
            requires_operator_clarification=True,
            blocks_verified_capability=False,
            blocks_positive_eval_case=False,
        )
        return _assemble_brain(classification, snapshot)

    # Rule 8: Success — no failure
    classification = EvaluationFailureClassification(
        classification_id=_new_classification_id(),
        primary_reason=EvaluationFailureReason.NONE,
        secondary_reasons=(),
        context_risk_level=ContextRiskLevel.LOW,
        signals=(),
        requires_operator_clarification=False,
        blocks_verified_capability=False,
        blocks_positive_eval_case=False,
        created_at=_DIAGNOSTICS_TIMESTAMP,
    )
    return _assemble_brain(classification, snapshot)


def _assemble_brain(
    classification: EvaluationFailureClassification,
    snapshot: EvaluationContextSnapshot,
) -> tuple[BrainAwareEvaluationContext, EvaluationContextSnapshot, EvaluationFailureClassification]:
    """Assemble the BrainAwareEvaluationContext wrapper."""
    # Determine recommended next action based on classification
    if classification.blocks_verified_capability:
        action = "block_promotion"
    elif classification.primary_reason in (
        EvaluationFailureReason.MISSING_CONTEXT,
        EvaluationFailureReason.UNSAFE_CONTEXT,
    ):
        action = "ask_operator_for_clarification"
    elif classification.primary_reason == EvaluationFailureReason.WEAK_EVIDENCE:
        action = "collect_more_evidence"
    elif classification.primary_reason == EvaluationFailureReason.VERIFIER_FAILED:
        action = "mark_as_regression_candidate"
    elif classification.primary_reason == EvaluationFailureReason.VERIFIER_INCONCLUSIVE:
        action = "keep_as_needs_review"
    elif classification.requires_operator_clarification:
        action = "ask_operator_for_clarification"
    else:
        action = "none"

    context_limitations: tuple[str, ...] = ()
    if classification.primary_reason != EvaluationFailureReason.NONE:
        context_limitations = (
            f"Brain-aware evaluation diagnostics: primary_reason={classification.primary_reason.value}, "
            f"context_risk_level={classification.context_risk_level.value}.",
        )

    brain = BrainAwareEvaluationContext(
        brain_eval_context_id=_new_brain_id(),
        evaluation_context_snapshot=snapshot,
        failure_classification=classification,
        context_limitations=context_limitations,
        recommended_next_action=action,
        created_at=_DIAGNOSTICS_TIMESTAMP,
    )
    return brain, snapshot, classification
