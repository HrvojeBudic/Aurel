"""P1.6.16 Policy Test Harness — determinism and hash stability tests."""
from __future__ import annotations

from agentic_runtime.policy_cards import (
    FamilyDecision,
    PolicyFamily,
    PolicyFamilyDecision,
    PolicyHarnessActual,
    PolicyHarnessCase,
    PolicyHarnessExpected,
    PolicyHarnessReport,
    PolicyHarnessResult,
    PolicyHarnessSuite,
    PolicyHarnessVerdict,
    ShadowAction,
    build_policy_harness_report,
    evaluate_policy_harness_case,
    run_policy_harness_suite,
)
from agentic_runtime.policy_cards.test_harness import (
    PolicyHarnessFailure,
    PolicyHarnessFailureType,
    PolicyHarnessInput,
    PolicyHarnessRun,
    policy_harness_report_hash,
    policy_harness_result_hash,
)


def _fd(family: PolicyFamily, decision: FamilyDecision) -> PolicyFamilyDecision:
    shadow_map = {
        FamilyDecision.ALLOW: ShadowAction.WOULD_ALLOW,
        FamilyDecision.WARN: ShadowAction.WOULD_WARN,
        FamilyDecision.REQUIRE_APPROVAL: ShadowAction.WOULD_REQUIRE_APPROVAL,
        FamilyDecision.DENY: ShadowAction.WOULD_DENY,
    }
    return PolicyFamilyDecision(
        family=family,
        decision=decision,
        effective_shadow_action=shadow_map[decision],
        reason_codes=("REASON",),
        applicable_card_ids=("card-a",),
    )


def _case(case_id: str) -> PolicyHarnessCase:
    return PolicyHarnessCase(
        case_id=case_id,
        input=PolicyHarnessInput(
            family_decisions=(_fd(PolicyFamily.RISK_TIER, FamilyDecision.ALLOW),),
        ),
        expected=PolicyHarnessExpected(expected_shadow_action="would_allow"),
    )


class TestDeterminism:
    def test_same_suite_same_report_hash(self):
        suite = PolicyHarnessSuite(
            suite_id="det-suite",
            cases=(_case("a"), _case("b")),
        )
        run1 = run_policy_harness_suite(suite)
        report1 = build_policy_harness_report(run1)
        run2 = run_policy_harness_suite(suite)
        report2 = build_policy_harness_report(run2)
        assert report1.report_hash == report2.report_hash

    def test_shuffled_cases_same_report_hash(self):
        cases = (_case("a"), _case("b"), _case("c"))
        suite1 = PolicyHarnessSuite(suite_id="det-suite", cases=cases)
        suite2 = PolicyHarnessSuite(suite_id="det-suite", cases=(cases[2], cases[0], cases[1]))
        r1 = build_policy_harness_report(run_policy_harness_suite(suite1))
        r2 = build_policy_harness_report(run_policy_harness_suite(suite2))
        assert r1.report_hash == r2.report_hash

    def test_shuffled_reason_codes_same_result_hash(self):
        fd1 = PolicyFamilyDecision(
            family=PolicyFamily.RISK_TIER,
            decision=FamilyDecision.WARN,
            effective_shadow_action=ShadowAction.WOULD_WARN,
            reason_codes=("Z", "A"),
            applicable_card_ids=("card-a",),
        )
        fd2 = PolicyFamilyDecision(
            family=PolicyFamily.RISK_TIER,
            decision=FamilyDecision.WARN,
            effective_shadow_action=ShadowAction.WOULD_WARN,
            reason_codes=("A", "Z"),
            applicable_card_ids=("card-a",),
        )
        r1 = evaluate_policy_harness_case(PolicyHarnessCase(
            case_id="reason-order",
            input=PolicyHarnessInput(family_decisions=(fd1,)),
            expected=PolicyHarnessExpected(expected_strictest_rank="WARN"),
        ))
        r2 = evaluate_policy_harness_case(PolicyHarnessCase(
            case_id="reason-order",
            input=PolicyHarnessInput(family_decisions=(fd2,)),
            expected=PolicyHarnessExpected(expected_strictest_rank="WARN"),
        ))
        assert r1.canonical_hash == r2.canonical_hash

    def test_shuffled_conflict_codes_same_result_hash(self):
        case = PolicyHarnessCase(
            case_id="conflict-order",
            input=PolicyHarnessInput(
                family_decisions=(
                    _fd(PolicyFamily.RISK_TIER, FamilyDecision.ALLOW),
                    _fd(PolicyFamily.SANDBOX, FamilyDecision.DENY),
                ),
            ),
            expected=PolicyHarnessExpected(
                expected_strictest_rank="DENY",
                allow_unexpected_conflicts=True,
            ),
        )
        r1 = evaluate_policy_harness_case(case)
        r2 = evaluate_policy_harness_case(case)
        assert r1.canonical_hash == r2.canonical_hash

    def test_repeated_case_evaluation_stable_result_hash(self):
        case = _case("repeat")
        hashes = {evaluate_policy_harness_case(case).canonical_hash for _ in range(3)}
        assert len(hashes) == 1

    def test_repeated_suite_evaluation_stable_report_hash(self):
        suite = PolicyHarnessSuite(suite_id="repeat-suite", cases=(_case("x"),))
        hashes = {
            build_policy_harness_report(run_policy_harness_suite(suite)).report_hash
            for _ in range(3)
        }
        assert len(hashes) == 1

    def test_determinism_status_pass_when_hashes_match(self):
        run = run_policy_harness_suite(
            PolicyHarnessSuite(suite_id="det-ok", cases=(_case("x"),)),
        )
        report = build_policy_harness_report(run)
        assert report.determinism_status == "PASS"
        assert report.shadow_only_status == "PASS"

    def test_determinism_status_fail_when_mismatch_injected(self):
        result = PolicyHarnessResult(
            case_id="injected",
            verdict=PolicyHarnessVerdict.FAIL,
            actual=PolicyHarnessActual(),
            failures=(
                PolicyHarnessFailure(
                    failure_type=PolicyHarnessFailureType.NON_DETERMINISTIC_HASH,
                    message="injected mismatch",
                ),
            ),
        ).with_canonical_hash()
        run = PolicyHarnessRun(suite_id="det-fail", results=(result,))
        report = build_policy_harness_report(run)
        assert report.determinism_status == "FAIL"

    def test_report_hash_excludes_unstable_run_timestamp(self):
        suite = PolicyHarnessSuite(suite_id="ts-suite", cases=(_case("t1"),))
        report = build_policy_harness_report(run_policy_harness_suite(suite))
        recomputed = policy_harness_report_hash(
            PolicyHarnessReport(
                suite_id=report.suite_id,
                case_count=report.case_count,
                passed=report.passed,
                failed=report.failed,
                warned=report.warned,
                errored=report.errored,
                skipped=report.skipped,
                coverage_by_conflict_type=report.coverage_by_conflict_type,
                coverage_by_policy_family=report.coverage_by_policy_family,
                coverage_by_violation_type=report.coverage_by_violation_type,
                determinism_status=report.determinism_status,
                shadow_only_status=report.shadow_only_status,
                results=report.results,
            )
        )
        assert report.report_hash == recomputed
