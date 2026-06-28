"""Focused P1.9.30 seal criteria boundary tests."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, "src")

from agentic_runtime.output_passport import (
    LIVE_PATH_UNAVAILABLE_REASON,
    P19ExitSealDecision,
    P19ExitSealQualification,
    P19ExitSealScope,
    P19LiveDemoStatus,
    P19P2ReadinessStatus,
    P19TraceVerificationStatus,
    OutputPassportTruthLabel,
    OutputPassportVerificationStatus,
    TRACE_VERIFICATION_UNAVAILABLE_REASON,
    assert_seal_honest,
    build_evidence_trace_binding,
    build_p1_9_exit_seal_checklist,
    build_p1_9_live_integration_demo_result,
    build_p1_9_trace_verification_result,
    derive_p1_9_p2_readiness,
    run_p1_9_exit_seal_checklist,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_p1_contract_scope_can_seal_with_unavailable_live_path_disclosed():
    seal = run_p1_9_exit_seal_checklist(
        repo_root=REPO_ROOT,
        seal_scope=P19ExitSealScope.P1_CONTRACT_SCOPE,
    )

    assert seal.decision is P19ExitSealDecision.SEALED
    assert (
        seal.seal_qualification
        is P19ExitSealQualification.SEALED_FOR_P1_CONTRACT_SCOPE
    )
    assert seal.production_live_required is False
    assert seal.production_live_available is False
    assert LIVE_PATH_UNAVAILABLE_REASON in seal.live_demo.unavailable_reason
    assert seal.live_demo.truth_label is not OutputPassportTruthLabel.LIVE
    assert seal.truth_label is not OutputPassportTruthLabel.EXIT_SEALED
    assert_seal_honest(seal)


def test_p1_contract_scope_can_seal_with_trace_verification_unavailable():
    seal = run_p1_9_exit_seal_checklist(
        repo_root=REPO_ROOT,
        seal_scope=P19ExitSealScope.P1_CONTRACT_SCOPE,
    )

    assert seal.decision is P19ExitSealDecision.SEALED
    assert seal.trace_verified_required is False
    assert seal.trace_verification_available is False
    assert (
        seal.trace_verification.status
        is P19TraceVerificationStatus.TRACE_VERIFICATION_UNAVAILABLE
    )
    assert seal.trace_verification.truth_label is OutputPassportTruthLabel.NOT_VERIFIED
    assert seal.trace_verification.unavailable_reason == (
        TRACE_VERIFICATION_UNAVAILABLE_REASON
    )


def test_production_live_scope_cannot_seal_with_unavailable_live_path():
    seal = run_p1_9_exit_seal_checklist(
        repo_root=REPO_ROOT,
        seal_scope=P19ExitSealScope.PRODUCTION_LIVE_SCOPE,
    )

    assert seal.production_live_required is True
    assert seal.production_live_available is False
    assert seal.decision is P19ExitSealDecision.PARTIAL
    assert seal.seal_qualification is P19ExitSealQualification.NONE


def test_trace_verified_scope_cannot_seal_with_unavailable_trace_verification():
    seal = run_p1_9_exit_seal_checklist(
        repo_root=REPO_ROOT,
        seal_scope=P19ExitSealScope.TRACE_VERIFIED_SCOPE,
    )

    assert seal.trace_verified_required is True
    assert seal.trace_verification_available is False
    assert seal.decision is P19ExitSealDecision.PARTIAL
    assert seal.seal_qualification is P19ExitSealQualification.NONE


def test_release_scope_cannot_seal_with_dev_fixture_only():
    seal = run_p1_9_exit_seal_checklist(
        repo_root=REPO_ROOT,
        seal_scope=P19ExitSealScope.RELEASE_SCOPE,
    )

    assert seal.production_live_required is True
    assert seal.trace_verified_required is True
    assert seal.live_demo.demo_status is P19LiveDemoStatus.DEV_FIXTURE_TESTED
    assert seal.decision is P19ExitSealDecision.PARTIAL


def test_fake_truth_claims_still_fail_contract_scope_seal():
    checklist = build_p1_9_exit_seal_checklist(
        repo_root=REPO_ROOT,
        truth_labels=[
            OutputPassportTruthLabel.LIVE,
            OutputPassportTruthLabel.TRACE_VERIFIED,
            OutputPassportTruthLabel.EXIT_SEALED,
        ],
    )
    seal = run_p1_9_exit_seal_checklist(checklist)

    assert seal.decision is P19ExitSealDecision.NOT_SEALED
    assert seal.checklist.fake_live_detected is True
    assert seal.checklist.fake_trace_verified_detected is True
    assert seal.checklist.fake_exit_sealed_detected is True
    assert seal.p2_readiness_status is P19P2ReadinessStatus.NOT_READY_FOR_P2


def test_trace_ref_and_payload_do_not_become_trace_verified():
    trace = build_p1_9_trace_verification_result()

    assert trace.trace_ref_present is True
    assert trace.trace_payload_present is True
    assert trace.status is P19TraceVerificationStatus.TRACE_VERIFICATION_UNAVAILABLE
    assert trace.trace_verified is False
    assert trace.truth_label is not OutputPassportTruthLabel.TRACE_VERIFIED


def test_evidence_ref_does_not_become_evidence_finality():
    binding = build_evidence_trace_binding()

    assert binding.truth_label is not OutputPassportTruthLabel.EVIDENCE_FINAL
    assert binding.verification_status is OutputPassportVerificationStatus.NOT_VERIFIED
    assert binding.trace_ref is not None
    assert binding.trace_ref.verification_status is (
        OutputPassportVerificationStatus.NOT_VERIFIED
    )


def test_dev_fixture_tested_does_not_become_production_live_tested():
    demo = build_p1_9_live_integration_demo_result()

    assert demo.demo_status is P19LiveDemoStatus.DEV_FIXTURE_TESTED
    assert demo.demo_status is not P19LiveDemoStatus.PRODUCTION_LIVE_TESTED
    assert demo.demo_status is not P19LiveDemoStatus.LIVE_TESTED
    assert demo.truth_label is not OutputPassportTruthLabel.LIVE


def test_p2_readiness_ready_only_for_p1_contract_scope_seal():
    status, blocked, reason = derive_p1_9_p2_readiness(
        P19ExitSealDecision.SEALED,
        P19ExitSealQualification.SEALED_FOR_P1_CONTRACT_SCOPE,
    )

    assert status is P19P2ReadinessStatus.READY_FOR_P2_REVIEW
    assert blocked is False
    assert "coding remains gated" in reason
    assert status.value != "READY_FOR_P2_CODING"


def test_p2_readiness_blocks_unqualified_or_incomplete_seals():
    unqualified = derive_p1_9_p2_readiness(P19ExitSealDecision.SEALED)
    partial = derive_p1_9_p2_readiness(P19ExitSealDecision.PARTIAL)
    not_sealed = derive_p1_9_p2_readiness(P19ExitSealDecision.NOT_SEALED)
    blocked = derive_p1_9_p2_readiness(P19ExitSealDecision.BLOCKED)

    assert unqualified[0] is P19P2ReadinessStatus.NOT_READY_FOR_P2
    assert partial[0] is P19P2ReadinessStatus.NOT_READY_FOR_P2
    assert not_sealed[0] is P19P2ReadinessStatus.NOT_READY_FOR_P2
    assert blocked[0] is P19P2ReadinessStatus.BLOCKED
