"""P1.5.14/15 Evaluation Mirror runtime hook.

A minimal runtime-callable boundary for Evaluation Mirror. Future AurelFlow
can call this hook without knowing Evaluation Mirror internals.

P1.5.14: target validation, trace event emission, chain verification.
P1.5.15: brain-aware context diagnostics via classify_evaluation_context().

The hook validates the target against AurelTraceLog, emits evaluation trace
events, classifies evaluation context diagnostically, and returns an
EvaluationRunResult. It never promotes capability, commits memory, creates
skills, creates reflexes, or changes policy.
"""
from __future__ import annotations

import uuid
from typing import Any

from agentic_runtime.contracts.capability import CapabilityEvidenceRecord
from agentic_runtime.contracts.context import ContextAdequacyReport, ContextBindingRef
from agentic_runtime.contracts.evaluation_context import (
    BrainAwareEvaluationContext,
    ContextRiskLevel,
    EvaluationFailureClassification,
    EvaluationFailureReason,
)
from agentic_runtime.contracts.evaluation_runtime import (
    EvaluationEvent,
    EvaluationEventKind,
    EvaluationMode,
    EvaluationRequest,
    EvaluationRun,
    EvaluationRunResult,
    EvaluationRunStatus,
    EvaluationTargetRef,
    EvaluationTargetType,
)
from agentic_runtime.contracts.trace import (
    AurelTraceLog,
    TraceEventRef,
    TraceEventStatus,
    TraceEventType,
    hash_json,
    trace_event_ref,
)
from agentic_runtime.contracts.verifier import VerifierResult
from agentic_runtime.evaluation.context_diagnostics import classify_evaluation_context

_RUNTIME_HOOK_TIMESTAMP = "2026-06-22T00:00:00+00:00"
_HOOK_ACTOR_TYPE = "evaluation_runtime_hook"
_HOOK_ACTOR_ID = "p1_5_15_runtime_hook"


def _new_run_id() -> str:
    return f"eval_run_{uuid.uuid4().hex[:12]}"


def _new_event_id() -> str:
    return f"eval_event_{uuid.uuid4().hex[:12]}"


# ---------------------------------------------------------------------------
# Target validation
# ---------------------------------------------------------------------------


def _validate_target(target: EvaluationTargetRef) -> list[str]:
    """Validate that an evaluation target is valid for runtime evaluation.

    Returns a list of error strings (empty if valid).
    """
    errors: list[str] = []

    if target.source_trace_event_ref is None:
        errors.append("target has no source_trace_event_ref")
        return errors

    if not target.source_event_hash:
        errors.append("target has no source_event_hash")
        return errors

    if target.source_event_hash != target.source_trace_event_ref.event_hash:
        errors.append(
            f"source_event_hash {target.source_event_hash} does not "
            f"match trace ref hash {target.source_trace_event_ref.event_hash}"
        )
        return errors

    if target.target_type in (
        EvaluationTargetType.CAPABILITY_EVIDENCE,
        EvaluationTargetType.EVALUATION_CASE,
    ):
        if not target.evidence_refs:
            errors.append(
                f"target_type {target.target_type.value} requires non-empty evidence_refs"
            )

    return errors


# ---------------------------------------------------------------------------
# Trace event emission
# ---------------------------------------------------------------------------


def _emit_eval_event(
    *,
    trace_log: AurelTraceLog,
    event_kind: EvaluationEventKind,
    run_id: str,
    request_id: str,
    source_ref: TraceEventRef,
    message: str = "",
    extra_payload: dict[str, Any] | None = None,
) -> tuple[TraceEventRef, EvaluationEvent]:
    """Emit an evaluation event into AurelTraceLog and return both refs."""
    payload: dict[str, Any] = {
        "evaluation_event_kind": event_kind.value,
        "run_id": run_id,
        "request_id": request_id,
    }
    if message:
        payload["message"] = message
    if extra_payload:
        payload.update(extra_payload)

    trace_event = trace_log.append(
        event_type=TraceEventType.EVALUATION,
        actor_type=_HOOK_ACTOR_TYPE,
        actor_id=_HOOK_ACTOR_ID,
        payload_json=payload,
        timestamp=_RUNTIME_HOOK_TIMESTAMP,
        verifier_result_ref=extra_payload.get("verifier_result_ref") if extra_payload else None,
        object_refs=extra_payload.get("object_refs", ()) if extra_payload else (),
    )
    emitted_ref = trace_event_ref(trace_event)
    eval_event = EvaluationEvent(
        evaluation_event_id=_new_event_id(),
        run_id=run_id,
        request_id=request_id,
        event_kind=event_kind,
        source_trace_event_ref=source_ref,
        emitted_trace_event_ref=emitted_ref,
        message=message,
        payload_hash=trace_event.payload_hash,
        created_at=_RUNTIME_HOOK_TIMESTAMP,
    )
    return emitted_ref, eval_event


# ---------------------------------------------------------------------------
# run_evaluation — the runtime callable hook (P1.5.14 + P1.5.15)
# ---------------------------------------------------------------------------


def run_evaluation(
    request: EvaluationRequest,
    *,
    trace_log: AurelTraceLog,
    verifier_result: VerifierResult | None = None,
    capability_evidence: CapabilityEvidenceRecord | None = None,
    context_binding_ref: ContextBindingRef | None = None,
    context_adequacy_report: ContextAdequacyReport | None = None,
) -> tuple[EvaluationRunResult, EvaluationRun]:
    """Runtime-callable evaluation hook with brain-aware diagnostics.

    P1.5.14: target validation, trace event emission, chain verification.
    P1.5.15: brain-aware context classification.

    Returns:
        (EvaluationRunResult, EvaluationRun)

    The result is trace-bound, limitation-bound, classification-aware,
    and candidate-only. It never promotes capability, memory, skill, reflex,
    or policy.
    """
    run_id = _new_run_id()
    emitted_event_refs: list[str] = []
    verifier_result_refs: list[str] = []
    evaluation_case_refs: list[str] = []
    regression_candidate_refs: list[str] = []

    begun_at = _RUNTIME_HOOK_TIMESTAMP
    source_ref = request.target_ref.source_trace_event_ref

    # 1. Emit evaluation_requested
    requested_ref, _ = _emit_eval_event(
        trace_log=trace_log,
        event_kind=EvaluationEventKind.EVALUATION_REQUESTED,
        run_id=run_id,
        request_id=request.request_id,
        source_ref=source_ref,
        message=f"Evaluation requested by {request.requested_by}: {request.reason}",
        extra_payload={
            "target_id": request.target_ref.target_id,
            "target_type": request.target_ref.target_type.value,
            "evaluation_mode": request.evaluation_mode.value,
        },
    )
    emitted_event_refs.append(requested_ref.event_id)

    # 2. Validate target
    validation_errors = _validate_target(request.target_ref)

    if validation_errors:
        # Emit evaluation_failed
        failed_ref, _ = _emit_eval_event(
            trace_log=trace_log,
            event_kind=EvaluationEventKind.EVALUATION_FAILED,
            run_id=run_id,
            request_id=request.request_id,
            source_ref=source_ref,
            message=f"Target validation failed: {'; '.join(validation_errors)}",
            extra_payload={"errors": validation_errors},
        )
        emitted_event_refs.append(failed_ref.event_id)

        run = EvaluationRun(
            run_id=run_id,
            request_id=request.request_id,
            target_ref=request.target_ref,
            status=EvaluationRunStatus.FAILED,
            started_at=begun_at,
            completed_at=_RUNTIME_HOOK_TIMESTAMP,
            emitted_event_refs=tuple(emitted_event_refs),
        )
        result = EvaluationRunResult(
            run_id=run_id,
            request_id=request.request_id,
            status=EvaluationRunStatus.FAILED,
            summary=f"Evaluation target validation failed: {'; '.join(validation_errors)}",
            emitted_event_refs=tuple(emitted_event_refs),
            limitations=(
                "Target validation is structural and does not verify claim truth.",
            ),
            errors=tuple(validation_errors),
            warnings=(),
            completed_at=_RUNTIME_HOOK_TIMESTAMP,
        )
        return result, run

    # 3. Emit evaluation_started
    started_ref, _ = _emit_eval_event(
        trace_log=trace_log,
        event_kind=EvaluationEventKind.EVALUATION_STARTED,
        run_id=run_id,
        request_id=request.request_id,
        source_ref=source_ref,
        message="Evaluation run started.",
    )
    emitted_event_refs.append(started_ref.event_id)

    # 4. Emit evaluation_target_validated
    validated_ref, _ = _emit_eval_event(
        trace_log=trace_log,
        event_kind=EvaluationEventKind.EVALUATION_TARGET_VALIDATED,
        run_id=run_id,
        request_id=request.request_id,
        source_ref=source_ref,
        message=f"Target {request.target_ref.target_id} validated against trace.",
    )
    emitted_event_refs.append(validated_ref.event_id)

    # 5. Trace chain verification
    chain_report = trace_log.verify_chain(source_ref.trace_id)
    if not chain_report.is_valid:
        failed_ref2, _ = _emit_eval_event(
            trace_log=trace_log,
            event_kind=EvaluationEventKind.EVALUATION_FAILED,
            run_id=run_id,
            request_id=request.request_id,
            source_ref=source_ref,
            message=f"Trace chain verification failed: {'; '.join(chain_report.errors)}",
            extra_payload={"errors": list(chain_report.errors)},
        )
        emitted_event_refs.append(failed_ref2.event_id)

        run = EvaluationRun(
            run_id=run_id,
            request_id=request.request_id,
            target_ref=request.target_ref,
            status=EvaluationRunStatus.FAILED,
            started_at=begun_at,
            completed_at=_RUNTIME_HOOK_TIMESTAMP,
            emitted_event_refs=tuple(emitted_event_refs),
        )
        result = EvaluationRunResult(
            run_id=run_id,
            request_id=request.request_id,
            status=EvaluationRunStatus.FAILED,
            summary="Trace chain verification failed.",
            emitted_event_refs=tuple(emitted_event_refs),
            limitations=(
                "Chain verification checks structural integrity, not claim truth.",
            ),
            errors=tuple(chain_report.errors),
            warnings=(),
            completed_at=_RUNTIME_HOOK_TIMESTAMP,
        )
        return result, run

    # --- P1.5.15: Brain-aware evaluation context classification ---

    # Only run classification when diagnostic parameters are explicitly provided.
    _has_diagnostic_inputs = (
        verifier_result is not None
        or capability_evidence is not None
        or context_binding_ref is not None
        or context_adequacy_report is not None
    )

    if _has_diagnostic_inputs:
        return _finish_with_classification(
            run_id=run_id,
            request=request,
            trace_log=trace_log,
            source_ref=source_ref,
            begun_at=begun_at,
            emitted_event_refs=emitted_event_refs,
            verifier_result_refs=verifier_result_refs,
            evaluation_case_refs=evaluation_case_refs,
            regression_candidate_refs=regression_candidate_refs,
            verifier_result=verifier_result,
            capability_evidence=capability_evidence,
            context_binding_ref=context_binding_ref,
            context_adequacy_report=context_adequacy_report,
        )

    # --- P1.5.14-style fallback: no diagnostic inputs → PASSED ---

    # 6. Emit evaluation_completed
    completed_ref, _ = _emit_eval_event(
        trace_log=trace_log,
        event_kind=EvaluationEventKind.EVALUATION_COMPLETED,
        run_id=run_id,
        request_id=request.request_id,
        source_ref=source_ref,
        message=f"Evaluation completed: target {request.target_ref.target_id} is trace-bound.",
        extra_payload={
            "status": EvaluationRunStatus.PASSED.value,
            "evaluation_case_refs": evaluation_case_refs,
            "verifier_result_refs": verifier_result_refs,
        },
    )
    emitted_event_refs.append(completed_ref.event_id)

    # 7. Build and return result
    run = EvaluationRun(
        run_id=run_id,
        request_id=request.request_id,
        target_ref=request.target_ref,
        status=EvaluationRunStatus.PASSED,
        started_at=begun_at,
        completed_at=_RUNTIME_HOOK_TIMESTAMP,
        emitted_event_refs=tuple(emitted_event_refs),
        verifier_result_refs=tuple(verifier_result_refs),
        evaluation_case_refs=tuple(evaluation_case_refs),
        regression_candidate_refs=tuple(regression_candidate_refs),
    )
    result = EvaluationRunResult(
        run_id=run_id,
        request_id=request.request_id,
        status=EvaluationRunStatus.PASSED,
        summary=f"Target {request.target_ref.target_id} is valid, trace-bound, and chain-verified.",
        emitted_event_refs=tuple(emitted_event_refs),
        limitations=(
            "Evaluation runtime hook is deterministic and limited to structural "
            "target validation, trace binding, and chain integrity checks. "
            "It does not verify claim truth, task correctness, or semantic validity.",
            "This hook does not promote capability, memory, skill, reflex, or policy.",
        ),
        errors=(),
        warnings=(),
        completed_at=_RUNTIME_HOOK_TIMESTAMP,
    )
    return result, run


# ---------------------------------------------------------------------------
# _finish_with_classification — P1.5.15 brain-aware path
# ---------------------------------------------------------------------------


def _finish_with_classification(
    *,
    run_id: str,
    request: EvaluationRequest,
    trace_log: AurelTraceLog,
    source_ref: TraceEventRef,
    begun_at: str,
    emitted_event_refs: list[str],
    verifier_result_refs: list[str],
    evaluation_case_refs: list[str],
    regression_candidate_refs: list[str],
    verifier_result: VerifierResult | None = None,
    capability_evidence: CapabilityEvidenceRecord | None = None,
    context_binding_ref: ContextBindingRef | None = None,
    context_adequacy_report: ContextAdequacyReport | None = None,
) -> tuple[EvaluationRunResult, EvaluationRun]:
    """P1.5.15: Build result with brain-aware diagnostics."""
    source_ref = request.target_ref.source_trace_event_ref

    # Build verifier refs from provided verifier result
    verifier_results: tuple[VerifierResult, ...] = ()
    if verifier_result is not None:
        verifier_result_refs.append(verifier_result.verifier_id)
        verifier_results = (verifier_result,)

    # Run brain-aware context classification
    brain_ctx, snapshot, classification = classify_evaluation_context(
        context_binding_ref=context_binding_ref,
        context_adequacy_report=context_adequacy_report,
        verifier_results=verifier_results,
        capability_evidence=capability_evidence,
        trace_event_ref=source_ref,
        source_event_hash=request.target_ref.source_event_hash,
    )

    # Emit evaluation_verifier_used event if a verifier was used
    if verifier_result is not None:
        verifier_used_ref, _ = _emit_eval_event(
            trace_log=trace_log,
            event_kind=EvaluationEventKind.EVALUATION_VERIFIER_USED,
            run_id=run_id,
            request_id=request.request_id,
            source_ref=source_ref,
            message=f"Verifier {verifier_result.verifier_id} used.",
            extra_payload={
                "verifier_result_ref": verifier_result.verifier_id,
                "verifier_status": verifier_result.status.value,
                "classification_id": classification.classification_id,
            },
        )
        emitted_event_refs.append(verifier_used_ref.event_id)

    # Determine final status from classification
    final_status = EvaluationRunStatus.PASSED
    if classification.context_risk_level == ContextRiskLevel.CRITICAL:
        final_status = EvaluationRunStatus.FAILED
    elif classification.blocks_positive_eval_case:
        final_status = EvaluationRunStatus.FAILED
    elif classification.requires_operator_clarification:
        final_status = EvaluationRunStatus.NEEDS_REVIEW
    elif classification.primary_reason != EvaluationFailureReason.NONE:
        final_status = EvaluationRunStatus.NEEDS_REVIEW

    # Collect context limitations for the result
    all_limitations: list[str] = list(brain_ctx.context_limitations) if brain_ctx.context_limitations else []
    all_limitations.extend([
        "Evaluation runtime hook is deterministic and limited to structural "
        "target validation, trace binding, and chain integrity checks. "
        "It does not verify claim truth, task correctness, or semantic validity.",
        "This hook does not promote capability, memory, skill, reflex, or policy.",
    ])

    # Build errors from classification if needed
    result_errors: list[str] = []
    result_warnings: list[str] = []
    if final_status == EvaluationRunStatus.FAILED:
        result_errors.append(
            f"Brain-aware classification: {classification.primary_reason.value} "
            f"(risk={classification.context_risk_level.value})"
        )
    elif final_status == EvaluationRunStatus.NEEDS_REVIEW:
        result_errors.append(
            f"Brain-aware classification: {classification.primary_reason.value} "
            f"(risk={classification.context_risk_level.value})"
        )

    # Emit final event
    if final_status == EvaluationRunStatus.PASSED:
        completed_ref, _ = _emit_eval_event(
            trace_log=trace_log,
            event_kind=EvaluationEventKind.EVALUATION_COMPLETED,
            run_id=run_id,
            request_id=request.request_id,
            source_ref=source_ref,
            message=f"Evaluation completed: target {request.target_ref.target_id} is trace-bound and brain-verified.",
            extra_payload={
                "status": final_status.value,
                "primary_reason": classification.primary_reason.value,
                "context_risk_level": classification.context_risk_level.value,
                "verifier_result_refs": verifier_result_refs,
                "brain_aware_context_ref": brain_ctx.brain_eval_context_id,
            },
        )
        emitted_event_refs.append(completed_ref.event_id)
    elif final_status == EvaluationRunStatus.FAILED:
        _fail_ref, _ = _emit_eval_event(
            trace_log=trace_log,
            event_kind=EvaluationEventKind.EVALUATION_FAILED,
            run_id=run_id,
            request_id=request.request_id,
            source_ref=source_ref,
            message=f"Evaluation failed: {classification.primary_reason.value} (risk={classification.context_risk_level.value}).",
            extra_payload={
                "status": final_status.value,
                "primary_reason": classification.primary_reason.value,
                "context_risk_level": classification.context_risk_level.value,
                "errors": result_errors,
            },
        )
        emitted_event_refs.append(_fail_ref.event_id)
    else:
        _review_ref, _ = _emit_eval_event(
            trace_log=trace_log,
            event_kind=EvaluationEventKind.EVALUATION_NEEDS_REVIEW,
            run_id=run_id,
            request_id=request.request_id,
            source_ref=source_ref,
            message=f"Evaluation needs review: {classification.primary_reason.value} (risk={classification.context_risk_level.value}).",
            extra_payload={
                "status": final_status.value,
                "primary_reason": classification.primary_reason.value,
                "context_risk_level": classification.context_risk_level.value,
            },
        )
        emitted_event_refs.append(_review_ref.event_id)

    # Build and return result
    run = EvaluationRun(
        run_id=run_id,
        request_id=request.request_id,
        target_ref=request.target_ref,
        status=final_status,
        started_at=begun_at,
        completed_at=_RUNTIME_HOOK_TIMESTAMP,
        emitted_event_refs=tuple(emitted_event_refs),
        verifier_result_refs=tuple(verifier_result_refs),
        evaluation_case_refs=tuple(evaluation_case_refs),
        regression_candidate_refs=tuple(regression_candidate_refs),
    )
    result = EvaluationRunResult(
        run_id=run_id,
        request_id=request.request_id,
        status=final_status,
        summary=(
            f"Target {request.target_ref.target_id} evaluated. "
            f"Brain-aware: {classification.primary_reason.value} "
            f"(risk={classification.context_risk_level.value})."
        ),
        emitted_event_refs=tuple(emitted_event_refs),
        verifier_result_refs=tuple(verifier_result_refs),
        limitations=tuple(all_limitations),
        errors=tuple(result_errors),
        warnings=tuple(result_warnings),
        completed_at=_RUNTIME_HOOK_TIMESTAMP,
        brain_aware_context_ref=brain_ctx.brain_eval_context_id,
        failure_classification_ref=classification.classification_id,
        context_limitations=brain_ctx.context_limitations,
        recommended_next_action=brain_ctx.recommended_next_action,
    )
    return result, run
