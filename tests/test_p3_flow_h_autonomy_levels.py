"""P3-FLOW-H autonomy level / mode behavior tests.

A level is not authority, the mode source is explicit, Aurel never
self-selects, and A9 heretic live mode is locked unavailable.
"""

from __future__ import annotations

import pytest

from agentic_runtime.aurel_flow import (
    ALLOWED_AUTONOMY_PERMISSION_STATES,
    AurelFlowValidationError,
    AutonomyDecisionClass,
    AutonomyModeSource,
    GOVERNED_AUTONOMY_TIER_ORDER,
    GovernedAutonomyLevel,
    resolve_permission_state,
    select_autonomy_mode,
)


def test_autonomy_level_vocabulary_is_exactly_the_closed_world_set() -> None:
    assert {level.value for level in GovernedAutonomyLevel} == {
        "A0_OBSERVE_ONLY",
        "A1_SUGGEST_ONLY",
        "A2_PREPARE_CANDIDATES",
        "A3_INTERNAL_LOW_RISK_AUTO",
        "A4_INTERNAL_BOUNDED_AUTO",
        "A5_OPERATOR_REVIEWED_EXTERNAL",
        "A6_POLICY_GATED_EXTERNAL",
        "A7_HIGH_AUTONOMY_BOUNDED",
        "A8_HERETIC_MODE_SIMULATED",
        "A9_HERETIC_MODE_LIVE_LOCKED_UNAVAILABLE",
        "UNAVAILABLE",
        "ERROR",
    }


def test_tier_order_excludes_a9_unavailable_and_error() -> None:
    assert GovernedAutonomyLevel.A9_HERETIC_MODE_LIVE_LOCKED_UNAVAILABLE not in (
        GOVERNED_AUTONOMY_TIER_ORDER
    )
    assert GovernedAutonomyLevel.UNAVAILABLE not in GOVERNED_AUTONOMY_TIER_ORDER
    assert GovernedAutonomyLevel.ERROR not in GOVERNED_AUTONOMY_TIER_ORDER
    assert sorted(GOVERNED_AUTONOMY_TIER_ORDER.values()) == list(range(9))


def test_a9_heretic_live_mode_is_locked_unavailable() -> None:
    mode = select_autonomy_mode(
        run_id="run-1",
        level=GovernedAutonomyLevel.A9_HERETIC_MODE_LIVE_LOCKED_UNAVAILABLE,
        mode_source=AutonomyModeSource.OPERATOR_SELECTED,
        selected_by="op-1",
    )
    assert mode.live_execution_available is False
    assert mode.authority_granted is False
    assert mode.self_upgrade_allowed is False
    for decision_class in AutonomyDecisionClass:
        resolution = resolve_permission_state(mode.level, decision_class)
        assert resolution.permission_state not in (
            ALLOWED_AUTONOMY_PERMISSION_STATES
        ), f"A9 must never allow {decision_class.value}"


def test_mode_source_is_explicit_and_operator_selection_needs_operator() -> None:
    mode = select_autonomy_mode(
        run_id="run-1",
        level=GovernedAutonomyLevel.A2_PREPARE_CANDIDATES,
        mode_source=AutonomyModeSource.SAFETY_DOWNGRADE,
    )
    assert mode.mode_source is AutonomyModeSource.SAFETY_DOWNGRADE
    with pytest.raises(AurelFlowValidationError):
        select_autonomy_mode(
            run_id="run-1",
            level=GovernedAutonomyLevel.A2_PREPARE_CANDIDATES,
            mode_source=AutonomyModeSource.OPERATOR_SELECTED,
            selected_by="",
        )


def test_mode_cannot_be_constructed_self_selected_or_self_upgrading() -> None:
    mode = select_autonomy_mode(
        run_id="run-1",
        level=GovernedAutonomyLevel.A1_SUGGEST_ONLY,
        mode_source=AutonomyModeSource.POLICY_DEFAULT,
    )
    for forbidden_field in ("self_selected", "self_upgrade_allowed"):
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


def test_higher_autonomy_never_grants_authority() -> None:
    for level in (
        GovernedAutonomyLevel.A7_HIGH_AUTONOMY_BOUNDED,
        GovernedAutonomyLevel.A8_HERETIC_MODE_SIMULATED,
    ):
        mode = select_autonomy_mode(
            run_id="run-1",
            level=level,
            mode_source=AutonomyModeSource.OPERATOR_SELECTED,
            selected_by="op-1",
        )
        assert mode.authority_granted is False
        assert mode.permission_granted is False
        assert mode.execution_available is False
