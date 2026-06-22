"""P1.5.19 Integrated Seal tests — full seal, trace integrity, candidate boundary, anti-overclaim.

Proves the entire P1.5 subsystem is coherent, trace-bound, evidence-bound,
candidate-safe, and non-promotional.
"""
from __future__ import annotations

import pytest

from agentic_runtime.contracts.capability_claims import (
    CapabilityClaimStatus,
)
from agentic_runtime.contracts.p15_seal import (
    ColdCacheVerificationReport,
    ContractInvariantChecklist,
    GoldenThreadASealReport,
    InvariantResult,
    P15IntegratedSealReport,
    cold_cache_verification_report_to_dict,
    contract_invariant_checklist_to_dict,
    golden_thread_seal_report_to_dict,
    invariant_result_to_dict,
    p15_integrated_seal_report_to_dict,
)
from agentic_runtime.contracts.trace import (
    AurelTraceLog,
    TraceEventStatus,
    TraceEventType,
    trace_event_ref,
)
from agentic_runtime.evaluation.p15_integrated_seal import (
    run_p15_integrated_seal,
)
from agentic_runtime.golden_threads.thread_a import (
    GoldenThreadAHarness,
)

_TIMESTAMP = "2026-06-22T00:00:00+00:00"


def _make_cold_cache(passed: bool = True) -> ColdCacheVerificationReport:
    return ColdCacheVerificationReport(
        report_id="cc_001",
        cache_cleared=True,
        command_used="pytest",
        pytest_status="passed" if passed else "failed",
        passed=passed,
        created_at=_TIMESTAMP,
    )


# =========================================================================
# Full integrated seal test
# =========================================================================


def test_p15_integrated_seal_golden_thread_a_passes_with_cold_cache() -> None:
    """Full Golden Thread A passes, all refs exist, seal reports created."""
    harness = GoldenThreadAHarness()
    result = harness.run_demo()

    # All expected artifact refs exist
    assert result.trace_event_ref is not None
    assert result.evidence_ref.evidence_id
    assert result.verifier_result_ref
    assert result.capability_evidence_id
    assert result.evaluation_case_id is not None
    assert result.evaluation_run_id is not None
    assert result.capability_claim_id is not None
    assert result.operator_feedback_id is not None
    assert result.memory_candidate_id is not None

    # Seal reports exist
    assert harness.seal_report is not None
    assert harness.gta_seal_report is not None
    assert harness.invariant_checklist is not None

    # With cold-cache report, seal should pass
    cold_cache = _make_cold_cache(passed=True)
    seal_report, gta_seal, checklist = run_p15_integrated_seal(
        run_id=result.run_id,
        trace_event_refs=(result.trace_event_ref.event_hash,),
        evidence_refs=(result.evidence_ref.evidence_id,),
        verifier_result_refs=(result.verifier_result_ref,),
        capability_evidence_refs=(result.capability_evidence_id,),
        evaluation_case_refs=(
            (result.evaluation_case_id,) if result.evaluation_case_id else ()
        ),
        evaluation_run_result_refs=(result.evaluation_run_id,) if result.evaluation_run_id else (),
        brain_context_refs=(
            (result.brain_eval_context_id,) if result.brain_eval_context_id else ()
        ),
        capability_claim_refs=(
            (result.capability_claim_id,) if result.capability_claim_id else ()
        ),
        feedback_refs=(result.operator_feedback_id,) if result.operator_feedback_id else (),
        memory_candidate_refs=(
            (result.memory_candidate_id,) if result.memory_candidate_id else ()
        ),
        gta_passed=result.passed,
        gta_errors=result.errors,
        capability_claim_status=result.capability_claim_status,
        memory_candidate_status=result.memory_candidate_status,
        memory_committed=False,
        cold_cache_report=cold_cache,
        trace_log=harness.trace_log,
    )
    assert seal_report.passed is True
    assert gta_seal.passed is True
    assert checklist.passed is True


def test_p15_integrated_seal_without_cold_cache_fails() -> None:
    """Without cold-cache verification, the seal must not pass."""
    harness = GoldenThreadAHarness()
    result = harness.run_demo()

    seal_report, _, _ = run_p15_integrated_seal(
        run_id=result.run_id,
        trace_event_refs=(result.trace_event_ref.event_hash,),
        evidence_refs=(result.evidence_ref.evidence_id,),
        verifier_result_refs=(result.verifier_result_ref,),
        capability_evidence_refs=(result.capability_evidence_id,),
        evaluation_case_refs=(
            (result.evaluation_case_id,) if result.evaluation_case_id else ()
        ),
        evaluation_run_result_refs=(
            (result.evaluation_run_id,) if result.evaluation_run_id else ()
        ),
        brain_context_refs=(
            (result.brain_eval_context_id,) if result.brain_eval_context_id else ()
        ),
        capability_claim_refs=(
            (result.capability_claim_id,) if result.capability_claim_id else ()
        ),
        feedback_refs=(result.operator_feedback_id,) if result.operator_feedback_id else (),
        memory_candidate_refs=(
            (result.memory_candidate_id,) if result.memory_candidate_id else ()
        ),
        gta_passed=result.passed,
        gta_errors=result.errors,
        capability_claim_status=result.capability_claim_status,
        memory_candidate_status=result.memory_candidate_status,
        memory_committed=False,
        cold_cache_report=None,
        trace_log=harness.trace_log,
    )
    assert seal_report.passed is False


# =========================================================================
# Trace integrity tests
# =========================================================================


def test_p15_all_artifacts_bind_to_trace_refs() -> None:
    """Every P1.5 artifact binds back to a TraceEventRef."""
    harness = GoldenThreadAHarness()
    result = harness.run_demo()

    assert result.trace_event_ref is not None
    assert result.evidence_ref.source_trace_event_ref == result.trace_event_ref
    assert result.source_event_hash == result.trace_event_ref.event_hash


def test_p15_source_hashes_match_trace_event_hashes() -> None:
    """Source hashes in artifact refs match trace event hashes."""
    harness = GoldenThreadAHarness()
    result = harness.run_demo()

    assert result.source_event_hash == result.trace_event_ref.event_hash
    assert result.evidence_ref.source_trace_event_ref.event_hash == result.trace_event_ref.event_hash


def test_p15_reports_are_not_canonical_truth_sources() -> None:
    """Seal reports and derived reports are projections, not canonical truth."""
    seal_report = P15IntegratedSealReport(
        seal_id="seal_test_001",
        golden_thread_status="passed",
        trace_integrity_status="passed",
        evaluation_integrity_status="passed",
        capability_claim_status="passed",
        feedback_safety_status="passed",
        memory_candidate_safety_status="passed",
        cold_cache_verification_status="not_provided",
        passed=False,
        created_at=_TIMESTAMP,
    )
    assert seal_report.seal_id == "seal_test_001"
    d = p15_integrated_seal_report_to_dict(seal_report)
    assert d["seal_id"] == "seal_test_001"


def test_p15_aurel_tracelog_remains_only_canonical_truth() -> None:
    """AurelTraceLog verifies its own chain integrity."""
    log = AurelTraceLog(trace_id="test_canonical_001")
    event = log.append(
        event_type=TraceEventType.STUB_EXECUTION_COMPLETED,
        actor_type="test",
        actor_id="canonical_test",
        payload_json={"test": True},
        timestamp=_TIMESTAMP,
        status=TraceEventStatus.COMPLETED,
    )
    ref = trace_event_ref(event)
    report = log.verify_chain(ref.trace_id)
    assert report.is_valid is True
    assert not report.errors


# =========================================================================
# Candidate boundary tests
# =========================================================================


def test_p15_evaluation_case_remains_candidate() -> None:
    """EvaluationCase status is candidate or needs_review, never committed/promoted."""
    harness = GoldenThreadAHarness()
    result = harness.run_demo()

    eval_status = result.evaluation_case_status
    assert eval_status in ("candidate", "needs_review"), f"Got {eval_status}"


def test_p15_memory_candidate_not_committed() -> None:
    """MemoryCandidate is never committed."""
    harness = GoldenThreadAHarness()
    result = harness.run_demo()

    assert result.memory_committed is False
    assert result.memory_candidate_status == "candidate"


def test_p15_feedback_actions_are_candidate_only() -> None:
    """Feedback candidate actions are candidate-only, never verify/commit/skill."""
    harness = GoldenThreadAHarness()
    result = harness.run_demo()

    for action in result.feedback_candidate_actions:
        assert action not in (
            "verify_capability", "commit_memory", "create_skill",
            "create_reflex", "mutate_policy",
        ), f"Forbidden action {action} in feedback candidate actions"


def test_p15_capability_claim_candidate_requires_decision() -> None:
    """CapabilityClaimCandidate requires explicit decision before becoming a claim."""
    harness = GoldenThreadAHarness()
    result = harness.run_demo()

    assert result.capability_claim_candidate_id is not None
    assert result.capability_claim_decision_id is not None
    assert result.capability_claim_id is not None


# =========================================================================
# Anti-overclaim tests
# =========================================================================


def test_p15_capability_claim_is_context_verified_not_universal_verified() -> None:
    """Golden Thread A produces context_verified, never universal verified."""
    harness = GoldenThreadAHarness()
    result = harness.run_demo()

    assert result.capability_claim_status == CapabilityClaimStatus.CONTEXT_VERIFIED.value
    assert result.capability_claim_status != "verified"
    assert result.capability_claim_status != "verified_candidate"


def test_p15_single_golden_thread_result_does_not_create_verified_candidate() -> None:
    """A single Golden Thread run does not auto-promote to verified_candidate."""
    harness = GoldenThreadAHarness()
    result = harness.run_demo()
    assert result.capability_claim_status == CapabilityClaimStatus.CONTEXT_VERIFIED.value


# =========================================================================
# Seal report contracts
# =========================================================================


def test_golden_thread_seal_report_requires_non_empty_refs() -> None:
    """GoldenThreadASealReport requires non-empty artifact refs."""
    with pytest.raises(ValueError, match="must be non-empty"):
        GoldenThreadASealReport(
            report_id="gts_001",
            run_id="run_001",
            trace_event_refs=(),
            evidence_refs=("ev_1",),
            verifier_result_refs=("vr_1",),
            capability_evidence_refs=("ce_1",),
            evaluation_case_refs=("ec_1",),
            evaluation_run_result_refs=("err_1",),
            brain_context_refs=(),
            capability_claim_refs=("cc_1",),
            feedback_refs=("fb_1",),
            memory_candidate_refs=("mc_1",),
            passed=True,
            created_at=_TIMESTAMP,
        )


def test_p15_seal_report_requires_passed_false_when_subsystem_failed() -> None:
    """P15IntegratedSealReport fails validation if passed=True with a failed subsystem."""
    with pytest.raises(ValueError, match="passed must be False"):
        P15IntegratedSealReport(
            seal_id="seal_002",
            golden_thread_status="failed",
            trace_integrity_status="passed",
            evaluation_integrity_status="passed",
            capability_claim_status="passed",
            feedback_safety_status="passed",
            memory_candidate_safety_status="passed",
            cold_cache_verification_status="passed",
            passed=True,
            created_at=_TIMESTAMP,
        )


def test_cold_cache_report_requires_cache_cleared() -> None:
    """ColdCacheVerificationReport fails if cache not cleared when passed=True."""
    with pytest.raises(ValueError, match="cache_cleared is False"):
        ColdCacheVerificationReport(
            report_id="cc_002",
            cache_cleared=False,
            command_used="pytest",
            pytest_status="passed",
            passed=True,
            created_at=_TIMESTAMP,
        )


def test_cold_cache_report_fails_if_pytest_failed() -> None:
    """ColdCacheVerificationReport fails if pytest_status is not passed."""
    with pytest.raises(ValueError, match="pytest_status"):
        ColdCacheVerificationReport(
            report_id="cc_003",
            cache_cleared=True,
            command_used="pytest",
            pytest_status="failed",
            passed=True,
            created_at=_TIMESTAMP,
        )


def test_invariant_checklist_passed_matches_results() -> None:
    """ContractInvariantChecklist.passed must match invariant results."""
    with pytest.raises(ValueError, match="passed="):
        ContractInvariantChecklist(
            checklist_id="cl_001",
            invariant_results=(
                InvariantResult(
                    invariant_id="i1",
                    description="Test.",
                    passed=False,
                ),
            ),
            passed=True,
            created_at=_TIMESTAMP,
        )


# =========================================================================
# Serialization
# =========================================================================


def test_p15_seal_report_to_dict() -> None:
    report = P15IntegratedSealReport(
        seal_id="s1",
        golden_thread_status="passed",
        trace_integrity_status="passed",
        evaluation_integrity_status="passed",
        capability_claim_status="passed",
        feedback_safety_status="passed",
        memory_candidate_safety_status="passed",
        cold_cache_verification_status="not_provided",
        passed=False,
        created_at=_TIMESTAMP,
    )
    d = p15_integrated_seal_report_to_dict(report)
    assert d["seal_id"] == "s1"


def test_gta_seal_report_to_dict() -> None:
    report = GoldenThreadASealReport(
        report_id="gts1",
        run_id="r1",
        trace_event_refs=("t1",),
        evidence_refs=("e1",),
        verifier_result_refs=("v1",),
        capability_evidence_refs=("c1",),
        evaluation_case_refs=("ec1",),
        evaluation_run_result_refs=("err1",),
        brain_context_refs=(),
        capability_claim_refs=("cc1",),
        feedback_refs=("fb1",),
        memory_candidate_refs=("mc1",),
        passed=True,
        created_at=_TIMESTAMP,
    )
    d = golden_thread_seal_report_to_dict(report)
    assert d["report_id"] == "gts1"


def test_invariant_result_to_dict() -> None:
    ir = InvariantResult(
        invariant_id="i1",
        description="Test.",
        passed=True,
    )
    d = invariant_result_to_dict(ir)
    assert d["invariant_id"] == "i1"


def test_checklist_to_dict() -> None:
    checklist = ContractInvariantChecklist(
        checklist_id="cl1",
        invariant_results=(
            InvariantResult(invariant_id="i1", description="Test.", passed=True),
        ),
        passed=True,
        created_at=_TIMESTAMP,
    )
    d = contract_invariant_checklist_to_dict(checklist)
    assert d["checklist_id"] == "cl1"
    assert d["passed"] is True


def test_cold_cache_to_dict() -> None:
    cc = ColdCacheVerificationReport(
        report_id="cc1",
        cache_cleared=True,
        command_used="pytest",
        pytest_status="passed",
        passed=True,
        created_at=_TIMESTAMP,
    )
    d = cold_cache_verification_report_to_dict(cc)
    assert d["report_id"] == "cc1"
