"""P1.5.11A/B/12/13/14/15/16/17/18/19 Golden Thread A minimal contract harness.

This module proves the vertical evidence path without real workflow runtime,
tool execution, shell execution, model calls, or memory promotion.

P1.5.12 extends the harness to produce candidate EvaluationCase records.
P1.5.13 routes verifier creation through the normalization layer.
P1.5.14 calls the Evaluation Mirror runtime hook on the completed target.
P1.5.15 adds brain-aware evaluation context diagnostics.
P1.5.16 wires CapabilityClaimRegistry — Golden Thread A now creates
a context_verified claim, not a universal verified claim.
P1.5.17 captures operator feedback on the capability claim — approval is
a support signal, not automatic truth.
P1.5.18 bridges evaluation/feedback/capability output to MemoryCandidate
records — candidates only, never committed memory.
P1.5.19 runs the integrated seal check over the full Golden Thread A chain:
trace → evidence → verifier → capability evidence → evaluation case →
evaluation run → brain diagnostics → capability claim → operator feedback →
memory candidate → seal reports.
"""
from __future__ import annotations

from dataclasses import dataclass

from agentic_runtime.contracts.capability import (
    CapabilityEvidenceRecord,
    CapabilityEvidenceStatus,
    EvidenceStrengthLevel,
    create_verified_capability_evidence_record,
    validate_capability_evidence,
)
from agentic_runtime.contracts.context import (
    ContextAdequacyReport,
    ContextAdequacyStatus,
    ContextBindingRef,
)
from agentic_runtime.contracts.evaluation_cases import (
    EvaluationCase,
    EvaluationCaseExtractionReport,
    EvaluationCaseKind,
    EvaluationCaseStatus,
    ExtractionStatus,
)
from agentic_runtime.contracts.evidence import EvidenceRef, build_evidence_ref
from agentic_runtime.contracts.trace import (
    AurelTraceLog,
    TraceEventRef,
    TraceEventStatus,
    TraceEventType,
    hash_json,
    trace_event_ref,
)
from agentic_runtime.contracts.verifier import (
    VerifierKind,
    VerifierNormalizationReport,
    VerifierResult,
    VerifierResultStatus,
)
from agentic_runtime.contracts.evaluation_runtime import (
    EvaluationMode,
    EvaluationRequest,
    EvaluationRun,
    EvaluationRunResult,
    EvaluationTargetRef,
    EvaluationTargetType,
)
from agentic_runtime.contracts.evaluation_context import (
    BrainAwareEvaluationContext,
)
from agentic_runtime.contracts.capability_claims import (
    CapabilityClaim,
    CapabilityClaimCandidate,
    CapabilityClaimDecision,
    CapabilityClaimDecisionKind,
    CapabilityClaimRegistry,
    CapabilityClaimReport,
    CapabilityClaimStatus,
    ClaimEvidenceLink,
)
from agentic_runtime.evaluation.extraction import extract_evaluation_case_from_capability_evidence
from agentic_runtime.evaluation.verifier_normalization import normalize_evidence_integrity
from agentic_runtime.evaluation.runtime_hook import run_evaluation
from agentic_runtime.evaluation.capability_claim_derivation import (
    derive_capability_claim_candidate,
)
from agentic_runtime.contracts.operator_feedback import (
    FeedbackProcessingReport,
    OperatorFeedbackRecord,
    OperatorFeedbackSentiment,
    OperatorFeedbackTargetRef,
    OperatorFeedbackTargetType,
    OperatorFeedbackType,
)
from agentic_runtime.evaluation.feedback_processing import (
    process_operator_feedback,
)
from agentic_runtime.evaluation.memory_candidate_bridge import (
    derive_memory_candidates,
)
from agentic_runtime.contracts.memory_candidates import (
    MemoryCandidate,
    MemoryCandidateBridgeReport,
    MemoryCandidateValidationReport,
)
from agentic_runtime.contracts.p15_seal import (
    ColdCacheVerificationReport,
    ContractInvariantChecklist,
    GoldenThreadASealReport,
    P15IntegratedSealReport,
)
from agentic_runtime.evaluation.p15_integrated_seal import (
    run_p15_integrated_seal,
)


GOLDEN_THREAD_A_TIMESTAMP = "2026-06-22T00:00:00+00:00"


def _run_evaluation_with_diagnostics(
    *,
    request: EvaluationRequest,
    trace_log: AurelTraceLog,
    verifier_result: VerifierResult | None = None,
    capability_evidence: CapabilityEvidenceRecord | None = None,
    context_binding_ref: ContextBindingRef | None = None,
    context_adequacy_report: ContextAdequacyReport | None = None,
) -> tuple[EvaluationRunResult, EvaluationRun, BrainAwareEvaluationContext]:
    """Run evaluation and also return brain-aware diagnostics.

    Calls run_evaluation() then classify_evaluation_context() to
    produce the BrainAwareEvaluationContext used by Golden Thread A.
    """
    from agentic_runtime.evaluation.context_diagnostics import classify_evaluation_context

    eval_result, eval_run = run_evaluation(
        request,
        trace_log=trace_log,
        verifier_result=verifier_result,
        capability_evidence=capability_evidence,
        context_binding_ref=context_binding_ref,
        context_adequacy_report=context_adequacy_report,
    )

    source_ref = request.target_ref.source_trace_event_ref
    verifier_results: tuple[VerifierResult, ...] = ()
    if verifier_result is not None:
        verifier_results = (verifier_result,)

    brain_ctx, _snapshot, _classification = classify_evaluation_context(
        context_binding_ref=context_binding_ref,
        context_adequacy_report=context_adequacy_report,
        verifier_results=verifier_results,
        capability_evidence=capability_evidence,
        trace_event_ref=source_ref,
        source_event_hash=request.target_ref.source_event_hash,
    )
    return eval_result, eval_run, brain_ctx


def _build_claim_report(
    *,
    claim: CapabilityClaim,
    report_id: str,
) -> CapabilityClaimReport:
    """Build a CapabilityClaimReport that honestly reflects what the claim proves."""
    limitations = list(claim.known_limits)
    limitation_texts = tuple(lim.description for lim in limitations)

    warnings: list[str] = []
    if claim.status == CapabilityClaimStatus.CONTEXT_VERIFIED:
        warnings.append(
            "This claim is CONTEXT_VERIFIED only — it does NOT represent universal "
            "verified capability. It applies only under the documented scope and "
            "conditions of a single Golden Thread A deterministic stub run."
        )
    warnings.append(
        "This claim is derived from a single Golden Thread A result. "
        "It does not generalize across tasks, environments, or tool configurations."
    )

    return CapabilityClaimReport(
        report_id=report_id,
        claim_id=claim.claim_id,
        status=claim.status,
        claim_text=claim.claim_text,
        scope_summary=(
            f"Task type: {claim.scope.task_type}. "
            "Evidence source: Golden Thread A deterministic stub execution. "
            "Verifier: evidence_integrity (normalized). "
            "Context: adequate, deterministic Golden Thread A context."
        ),
        evidence_summary=(
            f"Capability evidence {claim.capability_id} is trace-bound, "
            "verifier-bound (PASS), context-bound (ADEQUATE), and limitation-bound. "
            f"Confidence label: {claim.confidence_label}."
        ),
        limitations=limitation_texts,
        verified_context_count=len(claim.verified_contexts),
        warnings=tuple(warnings),
        created_at=GOLDEN_THREAD_A_TIMESTAMP,
    )


def _build_gta_memory_candidate(
    *,
    operator_feedback: OperatorFeedbackRecord | None,
    feedback_report: FeedbackProcessingReport | None,
    capability_claim: CapabilityClaim | None,
    trace_event_ref: TraceEventRef | None,
) -> tuple[MemoryCandidate | None, MemoryCandidateValidationReport | None]:
    """Build a representative MemoryCandidate for Golden Thread A.

    This mirrors the bridge module's logic but returns the actual objects.
    """
    from agentic_runtime.contracts.memory_candidates import (
        MemoryCandidateEvidenceLink,
        MemoryCandidateRiskClass,
        MemoryCandidateScope,
        MemoryCandidateScopeType,
        MemoryCandidateSourceType,
        MemoryCandidateStatus,
        MemoryCandidateType,
    )

    source_event_hash = trace_event_ref.event_hash if trace_event_ref else ""

    evidence_links: tuple[MemoryCandidateEvidenceLink, ...] = ()
    if trace_event_ref is not None and source_event_hash:
        evidence_links = (
            MemoryCandidateEvidenceLink(
                link_id="link_mem_gta_001",
                source_trace_event_ref=trace_event_ref,
                source_event_hash=source_event_hash,
                evidence_refs=(),
            ),
        )

    claim_text = ""
    capability_id = None
    if capability_claim is not None:
        claim_text = (
            f"Capability {capability_claim.capability_id} is "
            f"{capability_claim.status.value} under scope "
            f"{capability_claim.scope.task_type}. This is a governed "
            f"capability claim, not universal capability. "
            f"Approval is a support signal, not automatic truth."
        )
        capability_id = capability_claim.capability_id

    scope = MemoryCandidateScope(
        scope_type=MemoryCandidateScopeType.CAPABILITY,
        allowed_use_contexts=("future_review", "evaluation_context"),
        capability_id=capability_id,
    )

    limitations = (
        "This is a memory candidate only - NOT committed memory.",
        "This candidate may not become active recall without future governed review.",
        "P1.5.18 does not implement memory retrieval, ranking, consolidation, or decay.",
        "This is derived from a single Golden Thread A deterministic stub run.",
        "It does NOT verify, commit memory, mutate policy, or create skills/reflexes.",
    )

    try:
        memory_candidate = MemoryCandidate(
            memory_candidate_id="mem_gta_001",
            candidate_type=MemoryCandidateType.CAPABILITY_LESSON,
            status=MemoryCandidateStatus.CANDIDATE,
            source_type=MemoryCandidateSourceType.CAPABILITY_CLAIM,
            scope=scope,
            proposed_memory_text=claim_text,
            risk_class=MemoryCandidateRiskClass.LOW,
            limitations=limitations,
            evidence_links=evidence_links,
            review_reason=None,
            created_at=GOLDEN_THREAD_A_TIMESTAMP,
        )
    except ValueError:
        return None, None

    validation = MemoryCandidateValidationReport(
        validation_id="mem_val_gta_001",
        memory_candidate_id=memory_candidate.memory_candidate_id,
        is_valid=True,
        risk_class=MemoryCandidateRiskClass.LOW,
        required_review=False,
        blocked_reasons=(),
        warnings=(),
        created_at=GOLDEN_THREAD_A_TIMESTAMP,
    )

    return memory_candidate, validation


@dataclass(frozen=True)
class OperatorIntentStub:
    intent_id: str
    raw_text: str
    created_at: str
    actor_id: str


@dataclass(frozen=True)
class AurelContextStub:
    context_id: str
    intent_id: str
    project_ref: str | None
    source_refs: tuple[str, ...]
    assumptions: tuple[str, ...]


@dataclass(frozen=True)
class PolicyDecisionStub:
    policy_decision_id: str
    allowed: bool
    reason: str
    risk_tier: str
    policy_hash: str
    required_evidence: tuple[str, ...]


@dataclass(frozen=True)
class LeaseStub:
    lease_id: str
    policy_decision_id: str
    allowed_action: str
    allowed_tools: tuple[str, ...]
    allowed_data_refs: tuple[str, ...]
    expires_at: str
    lease_hash: str


@dataclass(frozen=True)
class StubExecutionResult:
    execution_id: str
    lease_id: str
    status: str
    output_summary: str
    output_hash: str
    created_at: str


@dataclass(frozen=True)
class GoldenThreadAResult:
    run_id: str
    intent_id: str
    context_id: str
    policy_decision_id: str
    lease_id: str
    execution_id: str
    context_binding_ref: ContextBindingRef
    context_adequacy_ref: ContextAdequacyReport
    trace_event_ref: TraceEventRef
    source_event_hash: str
    evidence_ref: EvidenceRef
    evidence_strength: EvidenceStrengthLevel
    verifier_result_ref: str
    capability_evidence_id: str
    capability_evidence_status: CapabilityEvidenceStatus
    passed: bool
    errors: tuple[str, ...]
    verifier_kind: str | None = None
    normalization_report_id: str | None = None
    normalization_status: str | None = None
    evaluation_case_id: str | None = None
    regression_candidate_id: str | None = None
    extraction_report_id: str | None = None
    evaluation_case_kind: str | None = None
    evaluation_case_status: str | None = None
    extraction_status: str | None = None
    evaluation_request_id: str | None = None
    evaluation_run_id: str | None = None
    evaluation_run_status: str | None = None
    evaluation_result_status: str | None = None
    evaluation_event_refs: tuple[str, ...] = ()
    brain_eval_context_id: str | None = None
    failure_classification_id: str | None = None
    failure_reason: str | None = None
    context_risk_level: str | None = None
    recommended_next_action: str | None = None
    capability_claim_candidate_id: str | None = None
    capability_claim_decision_id: str | None = None
    capability_claim_id: str | None = None
    capability_claim_status: str | None = None
    capability_claim_report_id: str | None = None
    operator_feedback_id: str | None = None
    feedback_processing_report_id: str | None = None
    feedback_signal_strength: str | None = None
    feedback_candidate_actions: tuple[str, ...] = ()
    claim_status_after_feedback: str | None = None
    memory_candidate_id: str | None = None
    memory_candidate_type: str | None = None
    memory_candidate_status: str | None = None
    memory_validation_report_id: str | None = None
    memory_bridge_report_id: str | None = None
    memory_committed: bool = False
    p15_seal_report_id: str | None = None
    p15_seal_passed: bool = False
    golden_thread_seal_passed: bool = False
    contract_invariants_passed: bool = False
    gta_seal_report_id: str | None = None
    invariant_checklist_id: str | None = None
    invariant_failed_count: int = 0


class GoldenThreadAHarness:
    """Deterministic vertical contract harness for P1.5.11A/B/12/13/14/15/16/17."""

    def __init__(self, trace_log: AurelTraceLog | None = None) -> None:
        self.trace_log = trace_log or AurelTraceLog(trace_id="trace_golden_thread_a_001")
        self.verifier_result: VerifierResult | None = None
        self.normalization_report: VerifierNormalizationReport | None = None
        self.capability_evidence: CapabilityEvidenceRecord | None = None
        self.context_binding_ref: ContextBindingRef | None = None
        self.context_adequacy_report: ContextAdequacyReport | None = None
        self.evaluation_run_result: EvaluationRunResult | None = None
        self.evaluation_run: EvaluationRun | None = None
        self.brain_aware_evaluation_context: BrainAwareEvaluationContext | None = None
        self.claim_registry: CapabilityClaimRegistry = CapabilityClaimRegistry()
        self.claim_candidate: CapabilityClaimCandidate | None = None
        self.claim_decision: CapabilityClaimDecision | None = None
        self.claim: CapabilityClaim | None = None
        self.claim_report: CapabilityClaimReport | None = None
        self.operator_feedback: OperatorFeedbackRecord | None = None
        self.feedback_report: FeedbackProcessingReport | None = None
        self.memory_candidate: MemoryCandidate | None = None
        self.memory_validation_report: MemoryCandidateValidationReport | None = None
        self.memory_bridge_report: MemoryCandidateBridgeReport | None = None
        self.seal_report: P15IntegratedSealReport | None = None
        self.gta_seal_report: GoldenThreadASealReport | None = None
        self.invariant_checklist: ContractInvariantChecklist | None = None

    def run_demo(self) -> GoldenThreadAResult:
        run_id = "gta_run_001"
        intent = OperatorIntentStub(
            intent_id="intent_gta_001",
            raw_text="Demonstrate a governed evidence path with stub execution.",
            created_at=GOLDEN_THREAD_A_TIMESTAMP,
            actor_id="operator_golden_thread",
        )
        context = ContextBindingRef(
            context_id="context_gta_001",
            context_type="golden_thread_stub",
            source_refs=("docs/roadmap/P1.5.10X_TRACELOG_INTEGRITY_PATCH.md",),
            assumptions=("No real tools, shell, models, or workflow runtime are executed.",),
            created_at=GOLDEN_THREAD_A_TIMESTAMP,
        )
        policy = self._build_policy_decision()
        lease = self._build_lease(policy)
        execution = self._build_stub_execution(lease)

        event = self.trace_log.append(
            event_type=TraceEventType.STUB_EXECUTION_COMPLETED,
            actor_type="golden_thread_harness",
            actor_id="golden_thread_a",
            payload_json={
                "intent_id": intent.intent_id,
                "context_id": context.context_id,
                "context_type": context.context_type,
                "policy_decision_id": policy.policy_decision_id,
                "lease_id": lease.lease_id,
                "execution_id": execution.execution_id,
                "status": execution.status,
            },
            timestamp=GOLDEN_THREAD_A_TIMESTAMP,
            input_hash=policy.policy_hash,
            output_hash=execution.output_hash,
            context_packet_ref=context.context_id,
            status=TraceEventStatus.COMPLETED,
        )
        trace_ref = trace_event_ref(event)
        evidence = build_evidence_ref(
            evidence_id="evidence_gta_001",
            source_trace_event_ref=trace_ref,
            evidence_type="stub_execution",
            content={
                "execution_id": execution.execution_id,
                "status": execution.status,
                "output_hash": execution.output_hash,
            },
            summary="Stub execution completed under policy and lease stubs.",
        )
        context_adequacy = ContextAdequacyReport(
            context_adequacy_id="context_adequacy_gta_001",
            context_binding_ref=context,
            status=ContextAdequacyStatus.ADEQUATE,
            missing_context_flags=(),
            stale_context_flags=(),
            contradicted_context_flags=(),
            uncertainty_notes=(
                "Context adequacy is deterministic and limited to Golden Thread A.",
            ),
            safe_to_act=True,
            requires_operator_clarification=False,
            created_at=GOLDEN_THREAD_A_TIMESTAMP,
            adequacy_score=1.0,
        )
        self.context_binding_ref = context
        self.context_adequacy_report = context_adequacy

        # --- P1.5.13: Verifier via normalization layer ---
        norm_report, verifier = normalize_evidence_integrity(
            evidence_ref=evidence,
            source_trace_event_ref=trace_ref,
            expected_source_event_hash=trace_ref.event_hash,
            target_ref=execution.execution_id,
        )
        self.normalization_report = norm_report
        self.verifier_result = verifier

        capability = create_verified_capability_evidence_record(
            capability_evidence_id="capability_evidence_gta_001",
            capability_id="capability.golden_thread_a.stub_execution",
            source_trace_event_ref=trace_ref,
            source_event_hash=trace_ref.event_hash,
            evidence_refs=(evidence,),
            verifier_result=verifier,
            context_binding_ref=context,
            context_adequacy_report=context_adequacy,
            evidence_strength=EvidenceStrengthLevel.VERIFIED,
            limitations=(
                "Capability evidence is limited to Golden Thread A deterministic stub execution.",
                "This does not verify general runtime, tool, shell, model, or workflow capability.",
                "Context adequacy is limited to deterministic Golden Thread A context.",
            ),
            created_at=GOLDEN_THREAD_A_TIMESTAMP,
        )
        self.capability_evidence = capability

        errors = list(
            validate_capability_evidence(
                capability,
                verifier_result=verifier,
                context_adequacy_report=context_adequacy,
            )
        )
        chain_report = self.trace_log.verify_chain(trace_ref.trace_id)
        if not chain_report.is_valid:
            errors.extend(chain_report.errors)

        extraction_report, eval_case = extract_evaluation_case_from_capability_evidence(
            capability=capability,
            verifier=verifier,
            context_adequacy=context_adequacy,
            trace_event_ref=trace_ref,
        )

        # --- P1.5.14: Evaluation Mirror runtime hook ---
        target = EvaluationTargetRef(
            target_id=capability.capability_evidence_id,
            target_type=EvaluationTargetType.CAPABILITY_EVIDENCE,
            source_trace_event_ref=trace_ref,
            source_event_hash=trace_ref.event_hash,
            evidence_refs=(evidence.evidence_id,),
            created_at=GOLDEN_THREAD_A_TIMESTAMP,
        )
        request = EvaluationRequest(
            request_id="eval_request_gta_001",
            target_ref=target,
            requested_by="golden_thread_a",
            reason="Demonstrate Evaluation Mirror runtime hook on Golden Thread A target.",
            evaluation_mode=EvaluationMode.CAPABILITY_CHECK,
            required_verifier_kinds=(VerifierKind.EVIDENCE_INTEGRITY.value,),
            created_at=GOLDEN_THREAD_A_TIMESTAMP,
        )
        eval_result, eval_run, brain_ctx = _run_evaluation_with_diagnostics(
            request=request,
            trace_log=self.trace_log,
            verifier_result=verifier,
            capability_evidence=capability,
            context_binding_ref=context,
            context_adequacy_report=context_adequacy,
        )
        self.evaluation_run_result = eval_result
        self.evaluation_run = eval_run
        self.brain_aware_evaluation_context = brain_ctx

        # --- P1.5.16: Capability Claim Registry v2 ---
        candidate = derive_capability_claim_candidate(
            evaluation_result=eval_result,
            brain_context=brain_ctx,
            capability_evidence=capability,
            verifier_result=verifier,
            context_adequacy=context_adequacy,
            capability_id=capability.capability_id,
            claim_text_prefix="Golden Thread A deterministic stub execution claim",
        )
        self.claim_registry.propose(candidate)
        self.claim_candidate = candidate

        evidence_link = ClaimEvidenceLink(
            link_id="evidence_link_gta_001",
            capability_evidence_id=capability.capability_evidence_id,
            source_trace_event_ref=trace_ref,
            source_event_hash=trace_ref.event_hash,
            evidence_refs=(evidence.evidence_id,),
            verifier_result_refs=(verifier.verifier_id,),
            evaluation_run_result_refs=(eval_result.run_id,),
            brain_aware_context_ref=brain_ctx.brain_eval_context_id,
        )

        decision = CapabilityClaimDecision(
            decision_id="decision_gta_001",
            candidate_id=candidate.candidate_id,
            decision=CapabilityClaimDecisionKind.ACCEPT,
            decided_by="golden_thread_a_harness",
            reason="Default Golden Thread A path: context_verified claim from passed evaluation.",
            created_at=GOLDEN_THREAD_A_TIMESTAMP,
        )
        self.claim_registry.decide(candidate.candidate_id, decision)
        self.claim_decision = decision

        claim = self.claim_registry.apply_decision(decision, evidence_link=evidence_link)
        self.claim = claim

        # Build CapabilityClaimReport
        report = _build_claim_report(
            claim=claim,
            report_id="claim_report_gta_001",
        )
        self.claim_report = report

        # --- P1.5.17: Operator Feedback Capture v2 ---
        feedback_target = OperatorFeedbackTargetRef(
            target_id=claim.claim_id if claim else "claim_unknown",
            target_type=OperatorFeedbackTargetType.CAPABILITY_CLAIM,
            source_trace_event_ref=trace_ref,
            source_event_hash=trace_ref.event_hash,
        )
        operator_feedback = OperatorFeedbackRecord(
            feedback_id="feedback_gta_001",
            feedback_type=OperatorFeedbackType.APPROVAL,
            sentiment=OperatorFeedbackSentiment.POSITIVE,
            target_ref=feedback_target,
            actor_id="operator_golden_thread",
            raw_text="Approved. The claim is legitimate and the evidence path is sound.",
            salience=0.9,
            limitations=(
                "Operator approval is a support signal, not automatic verification.",
                "This feedback does not universalize the context_verified claim.",
                "Feedback is captured as trace/target-bound evidence input only.",
            ),
            source_trace_event_ref=trace_ref,
            created_at=GOLDEN_THREAD_A_TIMESTAMP,
        )
        self.operator_feedback = operator_feedback

        fb_report = process_operator_feedback(
            operator_feedback,
            capability_claim=claim,
        )
        self.feedback_report = fb_report

        # --- P1.5.18: Evaluation <-> Memory Candidate Bridge ---
        bridge_report = derive_memory_candidates(
            operator_feedback=operator_feedback,
            feedback_report=fb_report,
            capability_claim=claim,
            capability_claim_report=report if report else None,
            trace_event_ref=trace_ref,
        )
        self.memory_bridge_report = bridge_report

        # Build a representative memory candidate for Golden Thread A
        memory_candidate, memory_validation = _build_gta_memory_candidate(
            operator_feedback=operator_feedback,
            feedback_report=fb_report,
            capability_claim=claim,
            trace_event_ref=trace_ref,
        )
        self.memory_candidate = memory_candidate
        self.memory_validation_report = memory_validation

        # --- P1.5.19: Integrated Seal ---
        eval_case_id = eval_case.case_id if eval_case else ""
        brain_ctx_id = brain_ctx.brain_eval_context_id if brain_ctx else ""
        claim_id = claim.claim_id if claim else ""
        feedback_id = operator_feedback.feedback_id

        seal_report_obj, gta_seal_obj, checklist_obj = run_p15_integrated_seal(
            run_id=run_id,
            trace_event_refs=(trace_ref.event_hash,),
            evidence_refs=(evidence.evidence_id,),
            verifier_result_refs=(verifier.verifier_id,),
            capability_evidence_refs=(capability.capability_evidence_id,),
            evaluation_case_refs=(eval_case_id,) if eval_case_id else (),
            evaluation_run_result_refs=(eval_result.run_id,),
            brain_context_refs=(brain_ctx_id,) if brain_ctx_id else (),
            capability_claim_refs=(claim_id,) if claim_id else (),
            feedback_refs=(feedback_id,),
            memory_candidate_refs=(
                (memory_candidate.memory_candidate_id,)
                if memory_candidate else ()
            ),
            gta_passed=not errors,
            gta_errors=tuple(errors),
            capability_claim_status=claim.status.value if claim else None,
            memory_candidate_status=(
                memory_candidate.status.value if memory_candidate else None
            ),
            memory_committed=False,
            cold_cache_report=None,
            trace_log=self.trace_log,
        )
        self.seal_report = seal_report_obj
        self.gta_seal_report = gta_seal_obj
        self.invariant_checklist = checklist_obj

        return GoldenThreadAResult(
            run_id=run_id,
            intent_id=intent.intent_id,
            context_id=context.context_id,
            policy_decision_id=policy.policy_decision_id,
            lease_id=lease.lease_id,
            execution_id=execution.execution_id,
            context_binding_ref=context,
            context_adequacy_ref=context_adequacy,
            trace_event_ref=trace_ref,
            source_event_hash=trace_ref.event_hash,
            evidence_ref=evidence,
            evidence_strength=capability.evidence_strength,
            verifier_result_ref=verifier.verifier_id,
            capability_evidence_id=capability.capability_evidence_id,
            capability_evidence_status=capability.status,
            passed=not errors,
            errors=tuple(errors),
            verifier_kind=verifier.verifier_kind.value,
            normalization_report_id=norm_report.normalization_id,
            normalization_status=norm_report.normalization_status.value,
            evaluation_case_id=eval_case.case_id if eval_case else None,
            regression_candidate_id=None,
            extraction_report_id=extraction_report.extraction_id,
            evaluation_case_kind=eval_case.case_kind.value if eval_case else None,
            evaluation_case_status=eval_case.status.value if eval_case else None,
            extraction_status=extraction_report.extraction_status.value,
            evaluation_request_id=request.request_id,
            evaluation_run_id=eval_run.run_id,
            evaluation_run_status=eval_run.status.value,
            evaluation_result_status=eval_result.status.value,
            evaluation_event_refs=eval_result.emitted_event_refs,
            brain_eval_context_id=brain_ctx.brain_eval_context_id,
            failure_classification_id=(
                brain_ctx.failure_classification.classification_id
            ),
            failure_reason=brain_ctx.failure_classification.primary_reason.value,
            context_risk_level=brain_ctx.failure_classification.context_risk_level.value,
            recommended_next_action=brain_ctx.recommended_next_action,
            capability_claim_candidate_id=candidate.candidate_id,
            capability_claim_decision_id=decision.decision_id,
            capability_claim_id=claim.claim_id if claim else None,
            capability_claim_status=claim.status.value if claim else None,
            capability_claim_report_id=report.report_id if report else None,
            operator_feedback_id=operator_feedback.feedback_id,
            feedback_processing_report_id=fb_report.report_id,
            feedback_signal_strength=fb_report.signal_strength.value,
            feedback_candidate_actions=tuple(
                a.value for a in fb_report.candidate_actions
            ),
            claim_status_after_feedback=(
                claim.status.value if claim else None
            ),
            memory_candidate_id=(
                self.memory_candidate.memory_candidate_id
                if self.memory_candidate else None
            ),
            memory_candidate_type=(
                self.memory_candidate.candidate_type.value
                if self.memory_candidate else None
            ),
            memory_candidate_status=(
                self.memory_candidate.status.value
                if self.memory_candidate else None
            ),
            memory_validation_report_id=(
                self.memory_validation_report.validation_id
                if self.memory_validation_report else None
            ),
            memory_bridge_report_id=(
                self.memory_bridge_report.report_id
                if self.memory_bridge_report else None
            ),
            memory_committed=False,
            p15_seal_report_id=seal_report_obj.seal_id,
            p15_seal_passed=seal_report_obj.passed,
            golden_thread_seal_passed=gta_seal_obj.passed,
            contract_invariants_passed=checklist_obj.passed,
            gta_seal_report_id=gta_seal_obj.report_id,
            invariant_checklist_id=checklist_obj.checklist_id,
            invariant_failed_count=len(checklist_obj.failed_invariants),
        )

    def _build_policy_decision(self) -> PolicyDecisionStub:
        content = {
            "allowed": True,
            "reason": "Golden Thread A deterministic stub path is allowed.",
            "risk_tier": "R0_STUB_ONLY",
            "required_evidence": ["trace_event_ref", "evidence_ref", "verifier_result"],
        }
        return PolicyDecisionStub(
            policy_decision_id="policy_gta_001",
            allowed=True,
            reason=content["reason"],
            risk_tier=content["risk_tier"],
            policy_hash=hash_json(content),
            required_evidence=tuple(content["required_evidence"]),
        )

    def _build_lease(self, policy: PolicyDecisionStub) -> LeaseStub:
        content = {
            "policy_decision_id": policy.policy_decision_id,
            "allowed_action": "stub_execution",
            "allowed_tools": [],
            "allowed_data_refs": ["project:aurel"],
            "expires_at": "2026-06-22T01:00:00+00:00",
        }
        return LeaseStub(
            lease_id="lease_gta_001",
            policy_decision_id=policy.policy_decision_id,
            allowed_action=content["allowed_action"],
            allowed_tools=(),
            allowed_data_refs=tuple(content["allowed_data_refs"]),
            expires_at=content["expires_at"],
            lease_hash=hash_json(content),
        )

    def _build_stub_execution(self, lease: LeaseStub) -> StubExecutionResult:
        content = {
            "lease_id": lease.lease_id,
            "status": "success",
            "output_summary": "Golden Thread A stub execution completed.",
        }
        return StubExecutionResult(
            execution_id="execution_gta_001",
            lease_id=lease.lease_id,
            status="success",
            output_summary=content["output_summary"],
            output_hash=hash_json(content),
            created_at=GOLDEN_THREAD_A_TIMESTAMP,
        )
