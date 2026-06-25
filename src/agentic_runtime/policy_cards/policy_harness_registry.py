"""Built-in policy harness case registry for CLI and operator surfaces (P1.6.18)."""
from __future__ import annotations

from .conflict_algebra import PolicyConflictType
from .resolution_context import EnforcementMode
from .resolution_result import (
    FamilyDecision,
    PolicyFamily,
    PolicyFamilyDecision,
    ResolvedPolicySet,
    ShadowAction,
)
from .test_harness import PolicyHarnessCase, PolicyHarnessExpected, PolicyHarnessInput, PolicyHarnessSuite
from .violation_trace import PolicyViolationType

DEFAULT_POLICY_HARNESS_SUITE_ID = "custos-v0-default"


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


def _builtin_cases() -> tuple[PolicyHarnessCase, ...]:
    return (
        PolicyHarnessCase(
            case_id="all_allow_no_conflict",
            title="All allow no conflict",
            input=PolicyHarnessInput(
                family_decisions=(_allow(), _allow(PolicyFamily.TOOL_PERMISSION)),
            ),
            expected=PolicyHarnessExpected(
                expected_shadow_action="would_allow",
                expected_strictest_rank="ALLOW",
            ),
        ),
        PolicyHarnessCase(
            case_id="deny_beats_allow",
            title="Deny beats allow",
            input=PolicyHarnessInput(
                family_decisions=(_allow(), _deny(PolicyFamily.SANDBOX)),
            ),
            expected=PolicyHarnessExpected(
                expected_shadow_action="would_deny",
                expected_strictest_rank="DENY",
                expected_conflict_types=(PolicyConflictType.STRICTNESS_CONFLICT.value,),
                allow_unexpected_conflicts=True,
            ),
        ),
        PolicyHarnessCase(
            case_id="require_approval_beats_warn",
            title="Require approval beats warn",
            input=PolicyHarnessInput(
                family_decisions=(_warn(), _approval(PolicyFamily.HUMAN_OVERSIGHT)),
            ),
            expected=PolicyHarnessExpected(
                expected_strictest_rank="REQUIRE_APPROVAL",
                expected_conflict_types=(PolicyConflictType.STRICTNESS_CONFLICT.value,),
                allow_unexpected_conflicts=True,
            ),
        ),
        PolicyHarnessCase(
            case_id="warn_beats_allow",
            title="Warn beats allow",
            input=PolicyHarnessInput(
                family_decisions=(_allow(), _warn(PolicyFamily.PROMPT)),
            ),
            expected=PolicyHarnessExpected(
                expected_strictest_rank="WARN",
                expected_conflict_types=(PolicyConflictType.STRICTNESS_CONFLICT.value,),
                allow_unexpected_conflicts=True,
            ),
        ),
        PolicyHarnessCase(
            case_id="adapter_error_is_conservative",
            title="Adapter error is conservative",
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
        ),
        PolicyHarnessCase(
            case_id="missing_context_is_explicit",
            title="Missing context is explicit",
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
        ),
        PolicyHarnessCase(
            case_id="tool_permission_conflict",
            title="Tool permission conflict",
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
        ),
        PolicyHarnessCase(
            case_id="sandbox_posture_conflict",
            title="Sandbox posture conflict",
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
        ),
        PolicyHarnessCase(
            case_id="data_residency_conflict",
            title="Data residency conflict",
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
        ),
        PolicyHarnessCase(
            case_id="memory_write_conflict",
            title="Memory write conflict",
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
        ),
        PolicyHarnessCase(
            case_id="prompt_authority_conflict",
            title="Prompt authority conflict",
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
        ),
        PolicyHarnessCase(
            case_id="p0_allow_custos_deny_violation_candidate",
            title="P0 allow Custos deny violation candidate",
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
        ),
        PolicyHarnessCase(
            case_id="p0_deny_custos_allow_runtime_stricter",
            title="P0 deny Custos allow runtime stricter",
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
        ),
        PolicyHarnessCase(
            case_id="trace_missing_becomes_policy_trace_incomplete",
            title="Trace missing becomes policy trace incomplete",
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
        ),
    )


def list_policy_harness_cases() -> tuple[PolicyHarnessCase, ...]:
    return _builtin_cases()


def get_policy_harness_case(case_id: str) -> PolicyHarnessCase | None:
    for case in _builtin_cases():
        if case.case_id == case_id:
            return case
    return None


def default_policy_harness_suite() -> PolicyHarnessSuite:
    cases = _builtin_cases()
    return PolicyHarnessSuite(
        suite_id=DEFAULT_POLICY_HARNESS_SUITE_ID,
        title="Custos v0 default policy harness matrix",
        cases=cases,
    )
