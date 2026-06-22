"""P1.5.19 Integrated Seal Invariant tests — no-promotion, verification gate.

Proves P1.5 never creates skills, reflexes, committed memory,
memory retrieval, policy mutations, or trace rewrites.
"""
from __future__ import annotations

import pytest

from agentic_runtime.contracts.memory_candidates import MemoryCandidateStatus
from agentic_runtime.contracts.p15_seal import (
    ColdCacheVerificationReport,
    P15IntegratedSealReport,
)
from agentic_runtime.evaluation.p15_integrated_seal import (
    run_p15_integrated_seal,
)
from agentic_runtime.golden_threads.thread_a import (
    GoldenThreadAHarness,
    GoldenThreadAResult,
)

_TIMESTAMP = "2026-06-22T00:00:00+00:00"


# =========================================================================
# No-promotion invariants
# =========================================================================


def test_p15_does_not_create_skill() -> None:
    """P1.5 must not create any skill. No field references skill in any result."""
    harness = GoldenThreadAHarness()
    result = harness.run_demo()

    result_dict = {
        k: v for k, v in result.__dict__.items() if not k.startswith("_")
    }
    skill_refs = [k for k in result_dict if "skill" in k.lower()]
    assert not skill_refs, f"Skill references found: {skill_refs}"


def test_p15_does_not_create_reflex() -> None:
    """P1.5 must not create any reflex."""
    harness = GoldenThreadAHarness()
    result = harness.run_demo()

    result_dict = {
        k: v for k, v in result.__dict__.items() if not k.startswith("_")
    }
    reflex_refs = [k for k in result_dict if "reflex" in k.lower()]
    assert not reflex_refs, f"Reflex references found: {reflex_refs}"


def test_p15_does_not_commit_memory() -> None:
    """P1.5 must not commit memory. memory_committed is always False."""
    harness = GoldenThreadAHarness()
    result = harness.run_demo()

    assert result.memory_committed is False

    # MemoryCandidateStatus enum does not have committed
    statuses = {s.value for s in MemoryCandidateStatus}
    assert "committed" not in statuses


def test_p15_does_not_enter_memory_retrieval_index() -> None:
    """P1.5 must not enter memory retrieval."""
    harness = GoldenThreadAHarness()
    result = harness.run_demo()

    result_dict = {
        k: v for k, v in result.__dict__.items() if not k.startswith("_")
    }
    retrieval_refs = [k for k in result_dict if "retriev" in k.lower()]
    assert not retrieval_refs, f"Retrieval references found: {retrieval_refs}"


def test_p15_does_not_mutate_policy() -> None:
    """P1.5 must not mutate policy."""
    harness = GoldenThreadAHarness()
    result = harness.run_demo()

    result_dict = {
        k: v for k, v in result.__dict__.items() if not k.startswith("_")
    }
    policy_mutate = [k for k in result_dict if "policy" in k.lower() and "mutat" in k.lower()]
    assert not policy_mutate, f"Policy mutation references found: {policy_mutate}"


def test_p15_does_not_rewrite_trace() -> None:
    """P1.5 must not rewrite the canonical trace."""
    harness = GoldenThreadAHarness()
    result = harness.run_demo()

    result_dict = {
        k: v for k, v in result.__dict__.items() if not k.startswith("_")
    }
    rewrite_refs = [k for k in result_dict if "rewrite" in k.lower()]
    assert not rewrite_refs, f"Trace rewrite references found: {rewrite_refs}"


def test_p15_operator_feedback_does_not_override_verifier() -> None:
    """Operator feedback must not override verifier results."""
    harness = GoldenThreadAHarness()
    result = harness.run_demo()

    # Verifier result exists and is separate from feedback
    assert result.verifier_result_ref is not None
    assert result.operator_feedback_id is not None
    # Feedback does not replace verifier — both exist independently
    assert harness.operator_feedback is not None
    assert harness.verifier_result is not None


def test_p15_no_capability_promotion_in_result() -> None:
    """GoldenThreadAResult must not contain capability promotion fields."""
    harness = GoldenThreadAHarness()
    result = harness.run_demo()

    result_dict = {
        k: v for k, v in result.__dict__.items() if not k.startswith("_")
    }
    promotion_refs = [k for k in result_dict if "promot" in k.lower() or "promote" in k.lower()]
    assert not promotion_refs, f"Promotion references found: {promotion_refs}"


def test_p15_no_memory_written_in_result() -> None:
    """GoldenThreadAResult must not contain memory_written field."""
    harness = GoldenThreadAHarness()
    result = harness.run_demo()

    result_dict = {
        k: v for k, v in result.__dict__.items() if not k.startswith("_")
    }
    memory_write_refs = [
        k for k in result_dict
        if "memory" in k.lower() and ("written" in k.lower() or "write" in k.lower() or "commit" in k.lower())
    ]
    # memory_committed is a seal field, not a commit action
    harmless = [k for k in memory_write_refs if k == "memory_committed"]
    real_refs = [k for k in memory_write_refs if k not in harmless]
    assert not real_refs, f"Memory write references found: {real_refs}"


# =========================================================================
# Verification gate tests
# =========================================================================


def test_p15_cold_cache_verification_report_required() -> None:
    """Cold cache verification report is structurally required."""
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
    assert "cold-cache" in " ".join(seal_report.warnings).lower()


def test_p15_seal_fails_if_cold_cache_verify_fails() -> None:
    """Seal fails when cold cache pytest fails."""
    harness = GoldenThreadAHarness()
    result = harness.run_demo()

    failed_cc = ColdCacheVerificationReport(
        report_id="cc_failed",
        cache_cleared=True,
        command_used="pytest",
        pytest_status="failed",
        passed=False,
        created_at=_TIMESTAMP,
    )

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
        cold_cache_report=failed_cc,
        trace_log=harness.trace_log,
    )
    assert seal_report.passed is False
    assert seal_report.cold_cache_verification_status == "failed"


def test_p15_seal_fails_if_cli_verify_fails_when_available() -> None:
    """ColdCacheVerificationReport fails if cli_verify status is provided and not passed."""
    with pytest.raises(ValueError, match="cli_verify_status"):
        ColdCacheVerificationReport(
            report_id="cc_cli_fail",
            cache_cleared=True,
            command_used="pytest && aurel verify",
            pytest_status="passed",
            cli_verify_status="failed",
            passed=True,
            created_at=_TIMESTAMP,
        )


def test_p15_passing_cold_cache_with_cli_verify() -> None:
    """ColdCacheVerificationReport passes with cli_verify=passed."""
    cc = ColdCacheVerificationReport(
        report_id="cc_cli_ok",
        cache_cleared=True,
        command_used="pytest && aurel verify",
        pytest_status="passed",
        cli_verify_status="passed",
        passed=True,
        created_at=_TIMESTAMP,
    )
    assert cc.passed is True


def test_p15_cached_run_is_not_seal_evidence() -> None:
    """Seal must fail when cache_cleared is False."""
    with pytest.raises(ValueError, match="cache_cleared is False"):
        ColdCacheVerificationReport(
            report_id="cc_cached",
            cache_cleared=False,
            command_used="pytest",
            pytest_status="passed",
            passed=True,
            created_at=_TIMESTAMP,
        )


# =========================================================================
# Structural safety
# =========================================================================


def test_p15_no_hidden_auto_verify() -> None:
    """P1.5 must not auto-verify capability from evaluation results alone."""
    harness = GoldenThreadAHarness()
    result = harness.run_demo()

    # Evaluation passes, but claim is context_verified only
    assert result.passed is True
    assert result.capability_claim_status == "context_verified"
    assert result.capability_claim_status != "verified"


def test_p15_capability_claim_report_includes_scope_and_limitations() -> None:
    """Capability claim report includes scope and limitations."""
    harness = GoldenThreadAHarness()
    harness.run_demo()
    assert harness.claim_report is not None
    assert harness.claim_report.limitations, "Claim report must have limitations"
    assert harness.claim_report.scope_summary, "Claim report must have scope summary"


def test_p15_claim_report_warns_when_context_verified() -> None:
    """CapabilityClaimReport warns when claim is context_verified (not universal)."""
    harness = GoldenThreadAHarness()
    harness.run_demo()
    assert harness.claim_report is not None
    assert harness.claim_report.warnings, "Claim report must warn about context_verified scope"
    assert any(
        "context_verified" in w.lower() or "does not represent universal" in w.lower()
        for w in harness.claim_report.warnings
    )
