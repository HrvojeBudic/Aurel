"""Focused P1.9.30 exit seal repair tests."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, "src")

from agentic_runtime.output_passport import (
    LIVE_PATH_UNAVAILABLE_REASON,
    P19_REPORT_CHAIN,
    P19ExitSealCheckStatus,
    P19ExitSealDecision,
    P19ExitSealQualification,
    P19ExitSealScope,
    P19LiveDemoStatus,
    P19P2ReadinessStatus,
    P19TraceVerificationStatus,
    OutputPassportTruthLabel,
    TRACE_VERIFICATION_UNAVAILABLE_REASON,
    build_p1_9_exit_seal_checklist,
    build_p1_9_live_integration_demo_result,
    build_p1_9_trace_verification_result,
    derive_p1_9_exit_seal_decision,
    derive_p1_9_p2_readiness,
    handle_output_passport_cli_inspect,
    run_p1_9_exit_seal_checklist,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def _write_report_chain(root: Path, filenames: tuple[str, ...]) -> None:
    reports = root / "agent" / "reports"
    reports.mkdir(parents=True)
    for filename in filenames:
        (reports / filename).write_text("# report\n", encoding="utf-8")


def _check_status(checklist, check_id: str) -> P19ExitSealCheckStatus:
    for item in checklist.checks:
        if item.check_id == check_id:
            return item.status
    raise AssertionError(f"missing check {check_id}")


def test_seal_fails_when_p1_9_d_report_missing(tmp_path: Path):
    _write_report_chain(tmp_path, P19_REPORT_CHAIN[:3])
    checklist = build_p1_9_exit_seal_checklist(repo_root=tmp_path)

    assert _check_status(checklist, "p1_9_d_report") is P19ExitSealCheckStatus.FAIL
    assert checklist.failed_count >= 1


def test_seal_fails_when_report_chain_missing(tmp_path: Path):
    checklist = build_p1_9_exit_seal_checklist(repo_root=tmp_path)

    assert _check_status(checklist, "p1_9_a_report") is P19ExitSealCheckStatus.FAIL
    assert _check_status(checklist, "p1_9_b_report") is P19ExitSealCheckStatus.FAIL
    assert _check_status(checklist, "p1_9_c_report") is P19ExitSealCheckStatus.FAIL
    assert _check_status(checklist, "p1_9_d_report") is P19ExitSealCheckStatus.FAIL


def test_seal_fails_fake_live_trace_and_exit_sealed():
    checklist = build_p1_9_exit_seal_checklist(
        repo_root=REPO_ROOT,
        truth_labels=[
            OutputPassportTruthLabel.LIVE,
            OutputPassportTruthLabel.TRACE_VERIFIED,
            OutputPassportTruthLabel.EXIT_SEALED,
        ],
    )

    assert checklist.fake_live_detected is True
    assert checklist.fake_trace_verified_detected is True
    assert checklist.fake_exit_sealed_detected is True
    assert _check_status(checklist, "no_fake_live") is P19ExitSealCheckStatus.FAIL
    assert _check_status(checklist, "no_fake_trace_verified") is P19ExitSealCheckStatus.FAIL
    assert _check_status(checklist, "no_fake_exit_sealed") is P19ExitSealCheckStatus.FAIL


@pytest.mark.parametrize(
    ("decision", "qualification", "expected_status", "blocked"),
    [
        (
            P19ExitSealDecision.NOT_SEALED,
            P19ExitSealQualification.NONE,
            P19P2ReadinessStatus.NOT_READY_FOR_P2,
            True,
        ),
        (
            P19ExitSealDecision.PARTIAL,
            P19ExitSealQualification.NONE,
            P19P2ReadinessStatus.NOT_READY_FOR_P2,
            True,
        ),
        (
            P19ExitSealDecision.BLOCKED,
            P19ExitSealQualification.NONE,
            P19P2ReadinessStatus.BLOCKED,
            True,
        ),
        (
            P19ExitSealDecision.SEALED,
            P19ExitSealQualification.SEALED_FOR_P1_CONTRACT_SCOPE,
            P19P2ReadinessStatus.READY_FOR_P2_REVIEW,
            False,
        ),
    ],
)
def test_p2_readiness_derived_from_seal_decision(
    decision,
    qualification,
    expected_status,
    blocked,
):
    status, is_blocked, reason = derive_p1_9_p2_readiness(decision, qualification)

    assert status is expected_status
    assert is_blocked is blocked
    assert "P2" in reason


def test_default_seal_is_p1_contract_scope_and_ready_for_review():
    seal = run_p1_9_exit_seal_checklist(repo_root=REPO_ROOT)

    assert seal.decision is P19ExitSealDecision.SEALED
    assert seal.seal_scope is P19ExitSealScope.P1_CONTRACT_SCOPE
    assert (
        seal.seal_qualification
        is P19ExitSealQualification.SEALED_FOR_P1_CONTRACT_SCOPE
    )
    assert seal.p2_readiness_status is P19P2ReadinessStatus.READY_FOR_P2_REVIEW
    assert seal.p2_readiness_blocked is False
    assert seal.truth_label is OutputPassportTruthLabel.CONTRACT_ONLY
    assert seal.truth_label is not OutputPassportTruthLabel.EXIT_SEALED


def test_live_demo_distinguishes_dev_fixture_from_live():
    demo = build_p1_9_live_integration_demo_result()

    assert demo.demo_status is P19LiveDemoStatus.DEV_FIXTURE_TESTED
    assert demo.truth_label is OutputPassportTruthLabel.DEV_FIXTURE
    assert demo.demo_status is not P19LiveDemoStatus.LIVE_TESTED
    assert demo.truth_label is not OutputPassportTruthLabel.LIVE


def test_projection_only_demo_does_not_become_live():
    demo = build_p1_9_live_integration_demo_result(
        demo_status=P19LiveDemoStatus.PROJECTION_ONLY_TESTED,
    )

    assert demo.demo_status is P19LiveDemoStatus.PROJECTION_ONLY_TESTED
    assert demo.projection_demo is True
    assert demo.cli_inspect_demo is False
    assert demo.truth_label is not OutputPassportTruthLabel.LIVE
    assert LIVE_PATH_UNAVAILABLE_REASON in demo.unavailable_reason


def test_cli_read_only_inspect_does_not_grant_authority():
    result = handle_output_passport_cli_inspect(dev_fixture=True)

    assert result["read_only"] is True
    assert result["authority_granted"] is False
    assert result["approval_created"] is False


def test_unavailable_live_path_carries_reason():
    demo = build_p1_9_live_integration_demo_result(
        demo_status=P19LiveDemoStatus.UNAVAILABLE_LIVE_PATH,
    )

    assert demo.demo_status is P19LiveDemoStatus.UNAVAILABLE_LIVE_PATH
    assert demo.demo_passed is False
    assert demo.unavailable_reason == LIVE_PATH_UNAVAILABLE_REASON


def test_unavailable_trace_verification_carries_reason():
    checklist = build_p1_9_exit_seal_checklist(repo_root=REPO_ROOT)
    trace = build_p1_9_trace_verification_result()
    trace_checks = [
        item for item in checklist.checks
        if item.check_id == "trace_verification_unavailable"
    ]

    assert len(trace_checks) == 1
    assert trace_checks[0].status is P19ExitSealCheckStatus.UNAVAILABLE
    assert trace_checks[0].unavailable_reason == TRACE_VERIFICATION_UNAVAILABLE_REASON
    assert trace.status is P19TraceVerificationStatus.TRACE_VERIFICATION_UNAVAILABLE
    assert trace.unavailable_reason == TRACE_VERIFICATION_UNAVAILABLE_REASON


def test_production_scope_sealed_decision_not_derived_from_non_live_demo():
    demo = build_p1_9_live_integration_demo_result()
    trace = build_p1_9_trace_verification_result()
    decision, qualification, reason = derive_p1_9_exit_seal_decision(
        checklist_passed=True,
        unavailable_count=2,
        live_demo=demo,
        seal_scope=P19ExitSealScope.PRODUCTION_LIVE_SCOPE,
        trace_verification=trace,
    )

    assert decision is P19ExitSealDecision.PARTIAL
    assert qualification is P19ExitSealQualification.NONE
    assert "production LIVE path" in reason


def test_live_tested_builder_requires_external_runtime_evidence():
    with pytest.raises(ValueError, match="PRODUCTION_LIVE_TESTED/LIVE_TESTED"):
        build_p1_9_live_integration_demo_result(
            demo_status=P19LiveDemoStatus.LIVE_TESTED,
        )
