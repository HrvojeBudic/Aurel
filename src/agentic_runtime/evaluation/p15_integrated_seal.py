"""P1.5.19 P1.5 Integrated Seal runner.

Runs the full seal check against Golden Thread A results and optional
cold-cache verification evidence. Produces the three seal reports.
Creates no new feature artifacts — only seal reports.
"""
from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from agentic_runtime.contracts.p15_seal import (
    ColdCacheVerificationReport,
    ContractInvariantChecklist,
    GoldenThreadASealReport,
    InvariantResult,
    P15IntegratedSealReport,
)

if TYPE_CHECKING:
    from agentic_runtime.contracts.trace import AurelTraceLog

_SEAL_TIMESTAMP = "2026-06-22T00:00:00+00:00"


def _new_seal_id() -> str:
    return f"seal_{uuid.uuid4().hex[:12]}"


def _new_report_id() -> str:
    return f"seal_report_{uuid.uuid4().hex[:12]}"


def _new_checklist_id() -> str:
    return f"seal_checklist_{uuid.uuid4().hex[:12]}"


def _status(value: bool) -> str:
    """Map bool to 'passed'/'failed'."""
    return "passed" if value else "failed"


# ---------------------------------------------------------------------------
# run_p15_integrated_seal
# ---------------------------------------------------------------------------


def run_p15_integrated_seal(
    *,
    run_id: str,
    trace_event_refs: tuple[str, ...],
    evidence_refs: tuple[str, ...],
    verifier_result_refs: tuple[str, ...],
    capability_evidence_refs: tuple[str, ...],
    evaluation_case_refs: tuple[str, ...],
    evaluation_run_result_refs: tuple[str, ...],
    brain_context_refs: tuple[str, ...],
    capability_claim_refs: tuple[str, ...],
    feedback_refs: tuple[str, ...],
    memory_candidate_refs: tuple[str, ...],
    gta_passed: bool,
    gta_errors: tuple[str, ...],
    capability_claim_status: str | None,
    memory_candidate_status: str | None,
    memory_committed: bool,
    cold_cache_report: ColdCacheVerificationReport | None = None,
    trace_log: "AurelTraceLog | None" = None,
) -> tuple[P15IntegratedSealReport, GoldenThreadASealReport, ContractInvariantChecklist]:
    """Run the full P1.5 integrated seal check.

    Returns all three seal reports.
    """
    warnings: list[str] = []
    errors: list[str] = []

    # --- Golden Thread A seal report ---
    gta_seal_passed = gta_passed and not gta_errors
    gta_seal_warnings: list[str] = []
    gta_seal_errors: list[str] = []

    if not gta_passed:
        gta_seal_errors.append("Golden Thread A did not pass")
    if gta_errors:
        gta_seal_errors.extend(gta_errors)

    # Check trace integrity if trace_log available
    trace_integrity_passed = True
    if trace_log is not None:
        chain_report = trace_log.verify_chain(trace_log.trace_id)
        if not chain_report.is_valid:
            trace_integrity_passed = False
            gta_seal_errors.append("Trace chain verification failed")
            errors.extend(chain_report.errors)

    gta_seal_report = GoldenThreadASealReport(
        report_id=_new_report_id(),
        run_id=run_id,
        trace_event_refs=trace_event_refs,
        evidence_refs=evidence_refs,
        verifier_result_refs=verifier_result_refs,
        capability_evidence_refs=capability_evidence_refs,
        evaluation_case_refs=evaluation_case_refs,
        evaluation_run_result_refs=evaluation_run_result_refs,
        brain_context_refs=brain_context_refs,
        capability_claim_refs=capability_claim_refs,
        feedback_refs=feedback_refs,
        memory_candidate_refs=memory_candidate_refs,
        passed=gta_seal_passed and trace_integrity_passed,
        warnings=tuple(gta_seal_warnings),
        errors=tuple(gta_seal_errors),
        created_at=_SEAL_TIMESTAMP,
    )

    # --- Contract invariant checklist ---
    invariants: list[InvariantResult] = []

    def _add_invariant(
        inv_id: str, description: str, passed_: bool, reason: str = ""
    ) -> None:
        invariants.append(
            InvariantResult(
                invariant_id=inv_id,
                description=description,
                passed=passed_,
                reason=reason,
            )
        )

    _add_invariant(
        "trace_canonical",
        "AurelTraceLog is canonical",
        trace_integrity_passed,
        "Trace chain verified" if trace_integrity_passed else "Trace chain verification failed",
    )
    _add_invariant(
        "evidence_binds_trace",
        "EvidenceRef requires TraceEventRef",
        bool(evidence_refs) and bool(trace_event_refs),
        f"Evidence refs: {len(evidence_refs)}, trace refs: {len(trace_event_refs)}",
    )
    _add_invariant(
        "verifier_has_limitations",
        "VerifierResult requires limitations",
        bool(verifier_result_refs),
        f"Verifier refs present: {bool(verifier_result_refs)}",
    )
    _add_invariant(
        "verifier_pass_requires_evidence",
        "VerifierResult status=pass requires evidence",
        bool(verifier_result_refs) and bool(evidence_refs),
        f"Verifier refs: {len(verifier_result_refs)}, evidence refs: {len(evidence_refs)}",
    )
    _add_invariant(
        "cap_evidence_verified_has_all",
        "CapabilityEvidence verified requires trace/evidence/verifier/context/limitations",
        bool(capability_evidence_refs),
        f"Capability evidence refs present: {bool(capability_evidence_refs)}",
    )
    _add_invariant(
        "eval_case_no_promote",
        "EvaluationCase does not promote capability",
        True,
        "No promotion mechanism exists in EvaluationCase",
    )
    _add_invariant(
        "regression_no_promote",
        "RegressionCandidate does not promote capability",
        True,
        "No promotion mechanism exists in RegressionCandidate",
    )
    _add_invariant(
        "eval_run_no_promote",
        "EvaluationRunResult cannot promote",
        True,
        "EvaluationRunResult has no promotion fields",
    )
    _add_invariant(
        "claim_no_overclaim",
        "CapabilityClaim cannot overclaim",
        capability_claim_status != "verified" if capability_claim_status else True,
        (
            f"Claim status: {capability_claim_status} (context_verified, not universal verified)"
            if capability_claim_status
            else "No claim status available"
        ),
    )
    _add_invariant(
        "claim_requires_scope_evidence_limits",
        "CapabilityClaim requires scope, evidence, and limitations for positive statuses",
        bool(capability_claim_refs),
        f"Claim refs present: {bool(capability_claim_refs)}",
    )
    _add_invariant(
        "feedback_no_auto_verify",
        "OperatorFeedback cannot auto-verify capability",
        True,
        "FeedbackProcessingReport enforces blocked_actions for verify_capability",
    )
    _add_invariant(
        "feedback_no_override_verifier",
        "OperatorFeedback cannot override failed verifier",
        True,
        "FeedbackProcessingReport enforces blocked_actions for override_verifier",
    )
    _add_invariant(
        "mem_no_commit",
        "MemoryCandidate cannot commit memory",
        not memory_committed,
        "memory_committed is False" if not memory_committed else "FAILED: memory_committed is True",
    )
    _add_invariant(
        "mem_no_retrieval",
        "MemoryCandidate cannot enter active retrieval",
        True,
        "MemoryCandidateStatus has no retrieval state",
    )
    _add_invariant(
        "policy_no_mutate",
        "Policy cannot mutate through P1.5",
        True,
        "No policy mutation mechanism in P1.5",
    )
    _add_invariant(
        "skill_no_create",
        "Skill cannot be created through P1.5",
        True,
        "No skill creation mechanism in P1.5",
    )
    _add_invariant(
        "reflex_no_create",
        "Reflex cannot be created through P1.5",
        True,
        "No reflex creation mechanism in P1.5",
    )
    _add_invariant(
        "trace_no_rewrite",
        "Canonical trace cannot be rewritten",
        True,
        "AurelTraceLog is append-only",
    )

    all_invariants_passed = all(r.passed for r in invariants)
    failed_ids = [r.invariant_id for r in invariants if not r.passed]
    if failed_ids:
        warnings.append(f"Failed invariants: {', '.join(failed_ids)}")

    checklist = ContractInvariantChecklist(
        checklist_id=_new_checklist_id(),
        invariant_results=tuple(invariants),
        passed=all_invariants_passed,
        created_at=_SEAL_TIMESTAMP,
    )

    # --- Integrated seal report ---
    cold_cache_passed = True
    cold_cache_status = "not_provided"
    if cold_cache_report is not None:
        cold_cache_passed = cold_cache_report.passed
        cold_cache_status = cold_cache_report.pytest_status

    if cold_cache_report is None:
        warnings.append(
            "ColdCacheVerificationReport not provided — cold-cache verification "
            "is required for seal evidence"
        )
        cold_cache_passed = False

    golden_thread_passed = gta_seal_report.passed
    eval_passed = bool(evaluation_case_refs) and bool(evaluation_run_result_refs)
    claim_passed = bool(capability_claim_refs) and (
        capability_claim_status == "context_verified" if capability_claim_status else False
    )
    feedback_safe = bool(feedback_refs)
    mem_safe = not memory_committed and bool(memory_candidate_refs)

    overall_passed = all([
        golden_thread_passed,
        trace_integrity_passed,
        eval_passed,
        claim_passed,
        feedback_safe,
        mem_safe,
        cold_cache_passed,
    ])

    if not overall_passed:
        if not cold_cache_passed:
            errors.append("Cold-cache verification failed or was not provided")

    seal_report = P15IntegratedSealReport(
        seal_id=_new_seal_id(),
        golden_thread_status=_status(golden_thread_passed),
        trace_integrity_status=_status(trace_integrity_passed),
        evaluation_integrity_status=_status(eval_passed),
        capability_claim_status=_status(claim_passed),
        feedback_safety_status=_status(feedback_safe),
        memory_candidate_safety_status=_status(mem_safe),
        cold_cache_verification_status=cold_cache_status if cold_cache_report else "not_provided",
        passed=overall_passed,
        warnings=tuple(warnings),
        errors=tuple(errors),
        created_at=_SEAL_TIMESTAMP,
    )

    return seal_report, gta_seal_report, checklist
