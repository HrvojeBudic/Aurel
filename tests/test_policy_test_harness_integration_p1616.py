"""P1.6.16 Policy Test Harness — integration scenario matrix tests."""
from __future__ import annotations

from agentic_runtime.policy_cards import (
    EnforcementMode,
    FamilyDecision,
    PolicyFamily,
    PolicyFamilyDecision,
    PolicyHarnessCase,
    PolicyHarnessExpected,
    PolicyHarnessVerdict,
    ResolvedPolicySet,
    ShadowAction,
    evaluate_policy_harness_case,
)
from agentic_runtime.policy_cards.test_harness import PolicyHarnessInput
from agentic_runtime.policy_cards.conflict_algebra import PolicyConflictType
from agentic_runtime.policy_cards.violation_trace import PolicyViolationType


def _fd(
    family: PolicyFamily,
    decision: FamilyDecision,
    *,
    reasons: tuple[str, ...] = ("REASON",),
    card: str = "card-a",
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
        applicable_card_ids=(card,),
    )


def _allow(family: PolicyFamily = PolicyFamily.RISK_TIER) -> PolicyFamilyDecision:
    return _fd(family, FamilyDecision.ALLOW)


def _warn(family: PolicyFamily = PolicyFamily.RISK_TIER) -> PolicyFamilyDecision:
    return _fd(family, FamilyDecision.WARN)


def _approval(family: PolicyFamily = PolicyFamily.RISK_TIER) -> PolicyFamilyDecision:
    return _fd(family, FamilyDecision.REQUIRE_APPROVAL)


def _deny(family: PolicyFamily = PolicyFamily.RISK_TIER) -> PolicyFamilyDecision:
    return _fd(family, FamilyDecision.DENY)


def _error(family: PolicyFamily = PolicyFamily.RISK_TIER) -> PolicyFamilyDecision:
    return _fd(family, FamilyDecision.ERROR, reasons=("ADAPTER_ERROR",))


def _run(case: PolicyHarnessCase):
    result = evaluate_policy_harness_case(case)
    assert result.verdict == PolicyHarnessVerdict.PASS, (
        f"{case.case_id}: {result.verdict} failures={result.failures}"
    )
    return result


class TestScenarioMatrix:
    def test_all_allow_no_conflict(self):
        result = _run(PolicyHarnessCase(
            case_id="all_allow_no_conflict",
            input=PolicyHarnessInput(
                family_decisions=(_allow(), _allow(PolicyFamily.TOOL_PERMISSION)),
            ),
            expected=PolicyHarnessExpected(
                expected_shadow_action="would_allow",
                expected_strictest_rank="ALLOW",
            ),
        ))
        assert result.actual.actual_shadow_action == "would_allow"

    def test_deny_beats_allow(self):
        result = _run(PolicyHarnessCase(
            case_id="deny_beats_allow",
            input=PolicyHarnessInput(
                family_decisions=(_allow(), _deny(PolicyFamily.SANDBOX)),
            ),
            expected=PolicyHarnessExpected(
                expected_shadow_action="would_deny",
                expected_strictest_rank="DENY",
                expected_conflict_types=(PolicyConflictType.STRICTNESS_CONFLICT.value,),
                allow_unexpected_conflicts=True,
            ),
        ))
        assert result.actual.actual_strictest_rank == "DENY"

    def test_require_approval_beats_warn(self):
        result = _run(PolicyHarnessCase(
            case_id="require_approval_beats_warn",
            input=PolicyHarnessInput(
                family_decisions=(_warn(), _approval(PolicyFamily.HUMAN_OVERSIGHT)),
            ),
            expected=PolicyHarnessExpected(
                expected_strictest_rank="REQUIRE_APPROVAL",
                expected_conflict_types=(PolicyConflictType.STRICTNESS_CONFLICT.value,),
                allow_unexpected_conflicts=True,
            ),
        ))
        assert "REQUIRE_APPROVAL" in result.actual.actual_strictest_rank

    def test_warn_beats_allow(self):
        result = _run(PolicyHarnessCase(
            case_id="warn_beats_allow",
            input=PolicyHarnessInput(
                family_decisions=(_allow(), _warn(PolicyFamily.PROMPT)),
            ),
            expected=PolicyHarnessExpected(
                expected_strictest_rank="WARN",
                expected_conflict_types=(PolicyConflictType.STRICTNESS_CONFLICT.value,),
                allow_unexpected_conflicts=True,
            ),
        ))
        assert result.actual.actual_strictest_rank == "WARN"

    def test_adapter_error_is_conservative(self):
        result = _run(PolicyHarnessCase(
            case_id="adapter_error_is_conservative",
            input=PolicyHarnessInput(
                family_decisions=(_error(PolicyFamily.SANDBOX), _allow()),
            ),
            expected=PolicyHarnessExpected(
                expected_shadow_action="would_require_approval",
                expected_conflict_types=(
                    PolicyConflictType.ADAPTER_ERROR.value,
                    PolicyConflictType.STRICTNESS_CONFLICT.value,
                ),
                allow_unexpected_conflicts=True,
            ),
        ))
        assert result.actual.actual_shadow_action == "would_require_approval"

    def test_missing_context_is_explicit(self):
        result = _run(PolicyHarnessCase(
            case_id="missing_context_is_explicit",
            input=PolicyHarnessInput(
                resolved_policy=ResolvedPolicySet(
                    resolution_id="rps-missing-ctx",
                    context_hash="",
                    enforcement_mode=EnforcementMode.SHADOW,
                    overall_decision=FamilyDecision.ALLOW,
                    effective_shadow_action=ShadowAction.WOULD_ALLOW,
                ),
            ),
            expected=PolicyHarnessExpected(
                expected_violation_types=(PolicyViolationType.POLICY_CONTEXT_MISSING.value,),
            ),
        ))
        assert PolicyViolationType.POLICY_CONTEXT_MISSING.value in (
            result.actual.actual_violation_types
        )

    def test_tool_permission_conflict(self):
        result = _run(PolicyHarnessCase(
            case_id="tool_permission_conflict",
            input=PolicyHarnessInput(
                family_decisions=(
                    _fd(
                        PolicyFamily.TOOL_PERMISSION,
                        FamilyDecision.DENY,
                        reasons=("TOOL_DENIED",),
                    ),
                    _allow(PolicyFamily.RISK_TIER),
                ),
            ),
            expected=PolicyHarnessExpected(
                expected_strictest_rank="DENY",
                expected_conflict_types=(PolicyConflictType.TOOL_PERMISSION_CONFLICT.value,),
                allow_unexpected_conflicts=True,
            ),
        ))
        assert PolicyConflictType.TOOL_PERMISSION_CONFLICT.value in (
            result.actual.actual_conflict_types
        )

    def test_sandbox_posture_conflict(self):
        result = _run(PolicyHarnessCase(
            case_id="sandbox_posture_conflict",
            input=PolicyHarnessInput(
                family_decisions=(
                    _fd(
                        PolicyFamily.SANDBOX,
                        FamilyDecision.WARN,
                        reasons=("SANDBOX_RESTRICTED",),
                    ),
                    _allow(),
                ),
            ),
            expected=PolicyHarnessExpected(
                expected_conflict_types=(PolicyConflictType.SANDBOX_POSTURE_CONFLICT.value,),
                allow_unexpected_conflicts=True,
            ),
        ))
        assert PolicyConflictType.SANDBOX_POSTURE_CONFLICT.value in (
            result.actual.actual_conflict_types
        )

    def test_data_residency_conflict(self):
        result = _run(PolicyHarnessCase(
            case_id="data_residency_conflict",
            input=PolicyHarnessInput(
                family_decisions=(
                    _fd(
                        PolicyFamily.DATA_RESIDENCY,
                        FamilyDecision.REQUIRE_APPROVAL,
                        reasons=("DATA_EGRESS_BLOCKED",),
                    ),
                    _allow(),
                ),
            ),
            expected=PolicyHarnessExpected(
                expected_conflict_types=(PolicyConflictType.DATA_RESIDENCY_CONFLICT.value,),
                allow_unexpected_conflicts=True,
            ),
        ))
        assert PolicyConflictType.DATA_RESIDENCY_CONFLICT.value in (
            result.actual.actual_conflict_types
        )

    def test_memory_write_conflict(self):
        result = _run(PolicyHarnessCase(
            case_id="memory_write_conflict",
            input=PolicyHarnessInput(
                family_decisions=(
                    _fd(
                        PolicyFamily.MEMORY_WRITE,
                        FamilyDecision.DENY,
                        reasons=("MEMORY_WRITE_DENIED",),
                    ),
                    _allow(),
                ),
            ),
            expected=PolicyHarnessExpected(
                expected_conflict_types=(PolicyConflictType.MEMORY_WRITE_CONFLICT.value,),
                allow_unexpected_conflicts=True,
            ),
        ))
        assert PolicyConflictType.MEMORY_WRITE_CONFLICT.value in (
            result.actual.actual_conflict_types
        )

    def test_prompt_authority_conflict(self):
        result = _run(PolicyHarnessCase(
            case_id="prompt_authority_conflict",
            input=PolicyHarnessInput(
                family_decisions=(
                    _fd(
                        PolicyFamily.PROMPT,
                        FamilyDecision.WARN,
                        reasons=("PROMPT_UNTRUSTED",),
                    ),
                    _allow(),
                ),
            ),
            expected=PolicyHarnessExpected(
                expected_conflict_types=(PolicyConflictType.PROMPT_AUTHORITY_CONFLICT.value,),
                allow_unexpected_conflicts=True,
            ),
        ))
        assert PolicyConflictType.PROMPT_AUTHORITY_CONFLICT.value in (
            result.actual.actual_conflict_types
        )

    def test_p0_allow_custos_deny_violation_candidate(self):
        result = _run(PolicyHarnessCase(
            case_id="p0_allow_custos_deny_violation_candidate",
            input=PolicyHarnessInput(
                p0_verdict="allow",
                family_decisions=(_deny(),),
            ),
            expected=PolicyHarnessExpected(
                expected_shadow_action="would_deny",
                expected_violation_types=(
                    PolicyViolationType.CUSTOS_STRICTER_THAN_RUNTIME.value,
                ),
            ),
        ))
        assert result.actual.actual_shadow_action == "would_deny"

    def test_p0_deny_custos_allow_runtime_stricter(self):
        result = _run(PolicyHarnessCase(
            case_id="p0_deny_custos_allow_runtime_stricter",
            input=PolicyHarnessInput(
                p0_verdict="deny",
                family_decisions=(_allow(),),
            ),
            expected=PolicyHarnessExpected(
                expected_shadow_action="would_allow",
                expected_violation_types=(
                    PolicyViolationType.RUNTIME_STRICTER_THAN_CUSTOS.value,
                ),
            ),
        ))
        assert result.actual.actual_shadow_action == "would_allow"

    def test_trace_missing_becomes_policy_trace_incomplete(self):
        result = _run(PolicyHarnessCase(
            case_id="trace_missing_becomes_policy_trace_incomplete",
            input=PolicyHarnessInput(
                resolved_policy=ResolvedPolicySet(
                    resolution_id="rps-no-trace",
                    context_hash="a" * 64,
                    enforcement_mode=EnforcementMode.SHADOW,
                    overall_decision=FamilyDecision.ALLOW,
                    effective_shadow_action=ShadowAction.WOULD_ALLOW,
                ),
            ),
            expected=PolicyHarnessExpected(
                expected_violation_types=(PolicyViolationType.POLICY_TRACE_INCOMPLETE.value,),
            ),
        ))
        assert PolicyViolationType.POLICY_TRACE_INCOMPLETE.value in (
            result.actual.actual_violation_types
        )
