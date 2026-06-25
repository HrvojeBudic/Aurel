"""P1.6.16 Policy Test Harness — pure harness object and comparator tests."""
from __future__ import annotations

import inspect
import json

import pytest

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
    compare_policy_harness_expected_actual,
    evaluate_policy_harness_case,
    run_policy_harness_suite,
    build_policy_harness_report,
)
from agentic_runtime.policy_cards import test_harness as harness_mod
from agentic_runtime.policy_cards.test_harness import (
    PolicyHarnessFailure,
    PolicyHarnessFailureType,
    PolicyHarnessInput,
    PolicyHarnessMatrix,
    PolicyHarnessRun,
    canonical_policy_harness_dict,
    policy_harness_case_hash,
    policy_harness_case_to_canonical_dict,
    policy_harness_result_hash,
)


def _fd(
    family: PolicyFamily,
    decision: FamilyDecision,
    *,
    reasons: tuple[str, ...] = ("REASON",),
) -> PolicyFamilyDecision:
    shadow_map = {
        FamilyDecision.ALLOW: ShadowAction.WOULD_ALLOW,
        FamilyDecision.WARN: ShadowAction.WOULD_WARN,
        FamilyDecision.REQUIRE_APPROVAL: ShadowAction.WOULD_REQUIRE_APPROVAL,
        FamilyDecision.DENY: ShadowAction.WOULD_DENY,
        FamilyDecision.NOT_APPLICABLE: ShadowAction.WOULD_NOT_APPLY,
        FamilyDecision.ERROR: ShadowAction.WOULD_ERROR,
    }
    return PolicyFamilyDecision(
        family=family,
        decision=decision,
        effective_shadow_action=shadow_map[decision],
        reason_codes=reasons,
        applicable_card_ids=("card-a",),
    )


class TestSchemaConstruction:
    def test_policy_harness_case_constructs(self):
        case = PolicyHarnessCase(
            case_id="c1",
            title="title",
            description="desc",
            input=PolicyHarnessInput(risk_tier="R2"),
            expected=PolicyHarnessExpected(expected_shadow_action="would_allow"),
            tags=("a", "b"),
            metadata={"tier": "R2"},
        )
        assert case.case_id == "c1"

    def test_policy_harness_expected_constructs(self):
        exp = PolicyHarnessExpected(
            expected_shadow_action="would_deny",
            expected_strictest_rank="DENY",
            expected_conflict_types=("strictness_conflict",),
            expected_violation_types=("POLICY_TRACE_INCOMPLETE",),
        )
        assert exp.expected_shadow_only is True
        assert exp.expected_enforced is False

    def test_policy_harness_actual_constructs(self):
        actual = PolicyHarnessActual(
            actual_shadow_action="would_allow",
            actual_strictest_rank="ALLOW",
            shadow_only=True,
            enforced=False,
        )
        assert actual.shadow_only is True

    def test_policy_harness_result_constructs(self):
        result = PolicyHarnessResult(
            case_id="c1",
            verdict=PolicyHarnessVerdict.PASS,
            actual=PolicyHarnessActual(),
        )
        assert result.verdict == PolicyHarnessVerdict.PASS

    def test_policy_harness_suite_constructs(self):
        suite = PolicyHarnessSuite(suite_id="s1", cases=())
        assert suite.suite_id == "s1"

    def test_policy_harness_report_constructs(self):
        report = PolicyHarnessReport(suite_id="s1")
        assert report.case_count == 0

    def test_policy_harness_matrix_constructs(self):
        matrix = PolicyHarnessMatrix(scenarios={})
        assert matrix.scenarios == {}


class TestCanonicalizationAndHash:
    def test_same_case_same_hash(self):
        case = PolicyHarnessCase(
            case_id="c1",
            tags=("x",),
            expected=PolicyHarnessExpected(
                expected_conflict_types=("strictness_conflict",),
                expected_violation_types=("POLICY_TRACE_INCOMPLETE",),
            ),
        )
        assert policy_harness_case_hash(case) == policy_harness_case_hash(case)

    def test_shuffled_tags_same_case_hash(self):
        c1 = PolicyHarnessCase(case_id="c1", tags=("b", "a"))
        c2 = PolicyHarnessCase(case_id="c1", tags=("a", "b"))
        assert policy_harness_case_hash(c1) == policy_harness_case_hash(c2)

    def test_shuffled_expected_conflict_types_same_hash(self):
        c1 = PolicyHarnessCase(
            case_id="c1",
            expected=PolicyHarnessExpected(
                expected_conflict_types=("b", "a"),
            ),
        )
        c2 = PolicyHarnessCase(
            case_id="c1",
            expected=PolicyHarnessExpected(
                expected_conflict_types=("a", "b"),
            ),
        )
        assert policy_harness_case_hash(c1) == policy_harness_case_hash(c2)

    def test_shuffled_expected_violation_types_same_hash(self):
        c1 = PolicyHarnessCase(
            case_id="c1",
            expected=PolicyHarnessExpected(
                expected_violation_types=("B", "A"),
            ),
        )
        c2 = PolicyHarnessCase(
            case_id="c1",
            expected=PolicyHarnessExpected(
                expected_violation_types=("A", "B"),
            ),
        )
        assert policy_harness_case_hash(c1) == policy_harness_case_hash(c2)

    def test_same_result_same_hash(self):
        result = PolicyHarnessResult(
            case_id="c1",
            verdict=PolicyHarnessVerdict.PASS,
            actual=PolicyHarnessActual(actual_shadow_action="would_allow"),
        )
        assert policy_harness_result_hash(result) == policy_harness_result_hash(result)

    def test_json_safe_canonical_payload(self):
        case = PolicyHarnessCase(
            case_id="c1",
            metadata={"safe_key": "value"},
        )
        payload = policy_harness_case_to_canonical_dict(case)
        json.loads(json.dumps(payload, sort_keys=True))

    def test_canonical_policy_harness_dict_sorted(self):
        payload = canonical_policy_harness_dict({"z": 1, "a": 2})
        assert list(payload.keys()) == sorted(payload.keys())


class TestComparator:
    def _actual(self, **kw) -> PolicyHarnessActual:
        return PolicyHarnessActual(**kw)

    def _expected(self, **kw) -> PolicyHarnessExpected:
        return PolicyHarnessExpected(**kw)

    def test_matching_expected_actual_passes(self):
        verdict, failures, _, _ = compare_policy_harness_expected_actual(
            self._expected(expected_shadow_action="would_allow"),
            self._actual(actual_shadow_action="would_allow"),
        )
        assert verdict == PolicyHarnessVerdict.PASS
        assert failures == ()

    def test_rank_mismatch(self):
        verdict, failures, _, _ = compare_policy_harness_expected_actual(
            self._expected(expected_strictest_rank="DENY"),
            self._actual(actual_strictest_rank="ALLOW"),
        )
        assert verdict == PolicyHarnessVerdict.FAIL
        assert failures[0].failure_type == PolicyHarnessFailureType.EXPECTED_RANK_MISMATCH

    def test_action_mismatch(self):
        verdict, failures, _, _ = compare_policy_harness_expected_actual(
            self._expected(expected_shadow_action="would_deny"),
            self._actual(actual_shadow_action="would_allow"),
        )
        assert verdict == PolicyHarnessVerdict.FAIL
        assert failures[0].failure_type == PolicyHarnessFailureType.EXPECTED_ACTION_MISMATCH

    def test_expected_conflict_missing(self):
        verdict, failures, _, _ = compare_policy_harness_expected_actual(
            self._expected(expected_conflict_types=("tool_permission_conflict",)),
            self._actual(actual_conflict_types=("strictness_conflict",)),
        )
        assert verdict == PolicyHarnessVerdict.FAIL
        assert any(
            f.failure_type == PolicyHarnessFailureType.EXPECTED_CONFLICT_MISSING
            for f in failures
        )

    def test_unexpected_conflict_warns(self):
        verdict, failures, _, _ = compare_policy_harness_expected_actual(
            self._expected(expected_conflict_types=("strictness_conflict",)),
            self._actual(
                actual_conflict_types=("strictness_conflict", "tool_permission_conflict"),
            ),
        )
        assert verdict == PolicyHarnessVerdict.WARN
        assert any(
            f.failure_type == PolicyHarnessFailureType.UNEXPECTED_CONFLICT
            for f in failures
        )

    def test_expected_resolution_trace_missing(self):
        verdict, failures, _, _ = compare_policy_harness_expected_actual(
            self._expected(expected_resolution_trace=True),
            self._actual(resolution_trace_hash=""),
        )
        assert verdict == PolicyHarnessVerdict.FAIL
        assert failures[0].failure_type == PolicyHarnessFailureType.EXPECTED_TRACE_MISSING

    def test_expected_violation_missing(self):
        verdict, failures, _, _ = compare_policy_harness_expected_actual(
            self._expected(expected_violation_types=("POLICY_TRACE_INCOMPLETE",)),
            self._actual(actual_violation_types=()),
        )
        assert verdict == PolicyHarnessVerdict.FAIL
        assert failures[0].failure_type == PolicyHarnessFailureType.EXPECTED_VIOLATION_MISSING

    def test_enforced_true_when_expected_false(self):
        verdict, failures, _, _ = compare_policy_harness_expected_actual(
            self._expected(expected_enforced=False),
            self._actual(enforced=True, shadow_only=True),
        )
        assert verdict == PolicyHarnessVerdict.FAIL
        assert failures[0].failure_type == PolicyHarnessFailureType.UNEXPECTED_ENFORCEMENT

    def test_shadow_only_false_when_expected_true(self):
        verdict, failures, _, _ = compare_policy_harness_expected_actual(
            self._expected(expected_shadow_only=True),
            self._actual(shadow_only=False, enforced=False),
        )
        assert verdict == PolicyHarnessVerdict.FAIL
        assert failures[0].failure_type == PolicyHarnessFailureType.UNEXPECTED_ENFORCEMENT


class TestSafety:
    def test_harness_payload_excludes_secret_metadata(self):
        case = PolicyHarnessCase(
            case_id="c1",
            metadata={"password": "secret-value", "tier": "R2"},
        )
        payload = policy_harness_case_to_canonical_dict(case)
        assert "password" not in payload.get("metadata", {})

    def test_harness_payload_excludes_command_body(self):
        case = PolicyHarnessCase(
            case_id="c1",
            metadata={"command_body": "rm -rf /", "tier": "R2"},
        )
        payload = policy_harness_case_to_canonical_dict(case)
        assert "command_body" not in payload.get("metadata", {})

    def test_harness_objects_have_no_enforcement_methods(self):
        forbidden = {"enforce", "block", "apply", "approve", "write_ledger"}
        for cls in (
            PolicyHarnessCase,
            PolicyHarnessResult,
            PolicyHarnessReport,
            PolicyHarnessSuite,
        ):
            methods = {n for n, _ in inspect.getmembers(cls) if not n.startswith("_")}
            assert not forbidden & methods

    def test_harness_module_no_runtime_import(self):
        for name in dir(harness_mod):
            obj = getattr(harness_mod, name, None)
            if obj is not None and hasattr(obj, "__module__"):
                mod = getattr(obj, "__module__", "")
                assert not mod.startswith("agentic_runtime.runtime")

    def test_evaluate_all_allow_scenario_passes(self):
        case = PolicyHarnessCase(
            case_id="all_allow",
            input=PolicyHarnessInput(
                family_decisions=(
                    _fd(PolicyFamily.RISK_TIER, FamilyDecision.ALLOW),
                    _fd(PolicyFamily.TOOL_PERMISSION, FamilyDecision.ALLOW),
                ),
            ),
            expected=PolicyHarnessExpected(
                expected_shadow_action="would_allow",
                expected_strictest_rank="ALLOW",
            ),
        )
        result = evaluate_policy_harness_case(case)
        assert result.verdict == PolicyHarnessVerdict.PASS

    def test_suite_and_report_build(self):
        case = PolicyHarnessCase(
            case_id="c1",
            input=PolicyHarnessInput(
                family_decisions=(_fd(PolicyFamily.RISK_TIER, FamilyDecision.ALLOW),),
            ),
            expected=PolicyHarnessExpected(expected_shadow_action="would_allow"),
        )
        run = run_policy_harness_suite(PolicyHarnessSuite(suite_id="s1", cases=(case,)))
        report = build_policy_harness_report(run)
        assert report.passed == 1
        assert report.report_hash is not None
        assert len(report.report_hash) == 64
