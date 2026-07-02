"""P3-FLOW-H no-authority boundary tests.

Nothing in the H layer grants authority, permission, or approval: not the
mode, not the resolver, not the gates, not the override candidate, not the
projection.
"""

from __future__ import annotations

import pytest

from agentic_runtime.aurel_flow import (
    AurelFlowValidationError,
    AutonomyDecisionClass,
    AutonomyModeSource,
    GovernedAutonomyLevel,
    build_operator_autonomy_override_candidate,
    resolve_permission_state,
    select_autonomy_mode,
)


def test_operator_override_raising_autonomy_is_not_authority() -> None:
    candidate = build_operator_autonomy_override_candidate(
        run_id="run-1",
        current_level=GovernedAutonomyLevel.A2_PREPARE_CANDIDATES,
        requested_level=GovernedAutonomyLevel.A6_POLICY_GATED_EXTERNAL,
        requested_by_operator="op-1",
        reason="operator wants more autonomy for this run",
    )
    assert candidate.raises_autonomy is True
    assert candidate.future_p9_required is True
    assert candidate.authority_granted is False
    assert candidate.permission_granted is False
    assert candidate.override_is_not_authority is True
    assert candidate.requires_operator_review is True


def test_operator_override_lowering_autonomy_needs_no_future_authority() -> None:
    candidate = build_operator_autonomy_override_candidate(
        run_id="run-1",
        current_level=GovernedAutonomyLevel.A6_POLICY_GATED_EXTERNAL,
        requested_level=GovernedAutonomyLevel.A1_SUGGEST_ONLY,
        requested_by_operator="op-1",
        reason="operator lowers autonomy",
    )
    assert candidate.raises_autonomy is False
    assert candidate.future_p9_required is False
    assert candidate.authority_granted is False


def test_override_candidate_requires_a_named_operator() -> None:
    with pytest.raises(AurelFlowValidationError):
        build_operator_autonomy_override_candidate(
            run_id="run-1",
            current_level=GovernedAutonomyLevel.A2_PREPARE_CANDIDATES,
            requested_level=GovernedAutonomyLevel.A3_INTERNAL_LOW_RISK_AUTO,
            requested_by_operator="",
            reason="anonymous",
        )


def test_raising_override_cannot_be_constructed_without_future_p9() -> None:
    candidate = build_operator_autonomy_override_candidate(
        run_id="run-1",
        current_level=GovernedAutonomyLevel.A2_PREPARE_CANDIDATES,
        requested_level=GovernedAutonomyLevel.A6_POLICY_GATED_EXTERNAL,
        requested_by_operator="op-1",
        reason="raise",
    )
    with pytest.raises(AurelFlowValidationError):
        type(candidate)(
            **{
                **{
                    field.name: getattr(candidate, field.name)
                    for field in candidate.__dataclass_fields__.values()
                },
                "future_p9_required": False,
            }
        )


def test_no_resolver_output_ever_grants_authority_or_permission() -> None:
    for level in GovernedAutonomyLevel:
        for decision_class in AutonomyDecisionClass:
            resolution = resolve_permission_state(level, decision_class)
            assert resolution.authority_granted is False
            assert resolution.permission_granted is False


def test_mode_cannot_be_constructed_with_authority() -> None:
    mode = select_autonomy_mode(
        run_id="run-1",
        level=GovernedAutonomyLevel.A7_HIGH_AUTONOMY_BOUNDED,
        mode_source=AutonomyModeSource.OPERATOR_SELECTED,
        selected_by="op-1",
    )
    for forbidden_field in ("authority_granted", "permission_granted"):
        with pytest.raises(AurelFlowValidationError):
            type(mode)(
                **{
                    **{
                        field.name: getattr(mode, field.name)
                        for field in mode.__dataclass_fields__.values()
                    },
                    forbidden_field: True,
                }
            )
