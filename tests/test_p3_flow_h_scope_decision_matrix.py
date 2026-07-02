"""P3-FLOW-H scope envelope + total decision resolver tests.

Seed fixtures pin representative pairs; the property tests iterate every
known (level, decision class) pair and verify totality, no authority/
execution/proof leak, side-effect safety, the A9 lock, and monotonicity.
"""

from __future__ import annotations

import pytest

from agentic_runtime.aurel_flow import (
    ALLOWED_AUTONOMY_PERMISSION_STATES,
    AurelFlowValidationError,
    AutonomyDecisionClass,
    AutonomyPermissionState,
    AutonomyScopeDimension,
    GOVERNED_AUTONOMY_TIER_ORDER,
    GovernedAutonomyLevel,
    SIDE_EFFECT_DECISION_CLASSES,
    build_autonomy_scope_envelope,
    create_autonomy_scope_limit,
    resolve_action_boundary,
    resolve_permission_state,
)

_TIERED_LEVELS = sorted(
    GOVERNED_AUTONOMY_TIER_ORDER, key=GOVERNED_AUTONOMY_TIER_ORDER.__getitem__
)


@pytest.mark.parametrize(
    ("level", "decision_class", "expected_state"),
    [
        (
            GovernedAutonomyLevel.A0_OBSERVE_ONLY,
            AutonomyDecisionClass.OBSERVE_STATE,
            AutonomyPermissionState.ALLOWED_READ_ONLY,
        ),
        (
            GovernedAutonomyLevel.A0_OBSERVE_ONLY,
            AutonomyDecisionClass.SUGGEST_NEXT_STEP,
            AutonomyPermissionState.REQUIRES_OPERATOR_REVIEW,
        ),
        (
            GovernedAutonomyLevel.A1_SUGGEST_ONLY,
            AutonomyDecisionClass.SUGGEST_NEXT_STEP,
            AutonomyPermissionState.ALLOWED_CANDIDATE_ONLY,
        ),
        (
            GovernedAutonomyLevel.A2_PREPARE_CANDIDATES,
            AutonomyDecisionClass.PREPARE_PLAN,
            AutonomyPermissionState.ALLOWED_CANDIDATE_ONLY,
        ),
        (
            GovernedAutonomyLevel.A2_PREPARE_CANDIDATES,
            AutonomyDecisionClass.REQUEST_EXECUTION,
            AutonomyPermissionState.REQUIRES_P4_EXECUTION,
        ),
        (
            GovernedAutonomyLevel.A5_OPERATOR_REVIEWED_EXTERNAL,
            AutonomyDecisionClass.EXTERNAL_SIDE_EFFECT,
            AutonomyPermissionState.FORBIDDEN_IN_P3,
        ),
        (
            GovernedAutonomyLevel.A6_POLICY_GATED_EXTERNAL,
            AutonomyDecisionClass.TOOL_EXECUTION,
            AutonomyPermissionState.FORBIDDEN_IN_P3,
        ),
        (
            GovernedAutonomyLevel.A8_HERETIC_MODE_SIMULATED,
            AutonomyDecisionClass.ROLLBACK_EXECUTION,
            AutonomyPermissionState.FORBIDDEN_IN_P3,
        ),
        (
            GovernedAutonomyLevel.A9_HERETIC_MODE_LIVE_LOCKED_UNAVAILABLE,
            AutonomyDecisionClass.EXTERNAL_SIDE_EFFECT,
            AutonomyPermissionState.FORBIDDEN_IN_P3,
        ),
        (
            GovernedAutonomyLevel.A3_INTERNAL_LOW_RISK_AUTO,
            AutonomyDecisionClass.REQUEST_PROOF,
            AutonomyPermissionState.REQUIRES_P5_PROOF,
        ),
        (
            GovernedAutonomyLevel.A7_HIGH_AUTONOMY_BOUNDED,
            AutonomyDecisionClass.REQUEST_AUTHORITY,
            AutonomyPermissionState.REQUIRES_P9_AUTHORITY,
        ),
        (
            GovernedAutonomyLevel.A4_INTERNAL_BOUNDED_AUTO,
            AutonomyDecisionClass.MEMORY_WRITE,
            AutonomyPermissionState.FORBIDDEN_IN_P3,
        ),
    ],
)
def test_resolver_seed_fixtures(
    level: GovernedAutonomyLevel,
    decision_class: AutonomyDecisionClass,
    expected_state: AutonomyPermissionState,
) -> None:
    resolution = resolve_permission_state(level, decision_class)
    assert resolution.permission_state is expected_state
    assert resolution.execution_available is False
    assert resolution.authority_granted is False


def test_seed_request_execution_requires_operator_review_and_p4() -> None:
    resolution = resolve_permission_state(
        GovernedAutonomyLevel.A2_PREPARE_CANDIDATES,
        AutonomyDecisionClass.REQUEST_EXECUTION,
    )
    assert resolution.requires_operator_review is True
    assert resolution.future_p4_required is True


def test_seed_rollback_at_a8_is_future_p4_bound_never_live() -> None:
    resolution = resolve_permission_state(
        GovernedAutonomyLevel.A8_HERETIC_MODE_SIMULATED,
        AutonomyDecisionClass.ROLLBACK_EXECUTION,
    )
    assert resolution.permission_state not in ALLOWED_AUTONOMY_PERMISSION_STATES
    assert resolution.future_p4_required is True
    assert resolution.execution_available is False


def test_resolver_is_total_with_safety_invariants() -> None:
    for level in GovernedAutonomyLevel:
        for decision_class in AutonomyDecisionClass:
            resolution = resolve_permission_state(level, decision_class)
            # Totality: a defined permission state for every known pair.
            assert isinstance(
                resolution.permission_state, AutonomyPermissionState
            )
            # No authority/execution/proof leak anywhere.
            assert resolution.authority_granted is False
            assert resolution.permission_granted is False
            assert resolution.execution_available is False
            assert resolution.proof_available is False
            assert resolution.trace_verified is False
            assert resolution.runtime_submit_wired is False
            # Side-effect classes never resolve bare ALLOWED_*; outside the
            # ERROR/UNAVAILABLE level overrides they are future-bound P4+P9.
            if decision_class in SIDE_EFFECT_DECISION_CLASSES:
                assert resolution.permission_state not in (
                    ALLOWED_AUTONOMY_PERMISSION_STATES
                )
                if level not in (
                    GovernedAutonomyLevel.UNAVAILABLE,
                    GovernedAutonomyLevel.ERROR,
                ):
                    assert resolution.future_p4_required is True
                    assert resolution.future_p9_required is True


def test_resolver_hard_overrides() -> None:
    # ERROR/UNAVAILABLE input levels win over every class rule.
    for level in GovernedAutonomyLevel:
        assert (
            resolve_permission_state(level, AutonomyDecisionClass.ERROR)
        ).permission_state is AutonomyPermissionState.ERROR
        if level is not GovernedAutonomyLevel.ERROR:
            assert (
                resolve_permission_state(level, AutonomyDecisionClass.UNAVAILABLE)
            ).permission_state is AutonomyPermissionState.UNAVAILABLE
    # Below the ERROR/UNAVAILABLE overrides, proof and authority requests are
    # future-bound at every remaining level, including locked A9.
    for level in GovernedAutonomyLevel:
        if level in (
            GovernedAutonomyLevel.UNAVAILABLE,
            GovernedAutonomyLevel.ERROR,
        ):
            continue
        proof = resolve_permission_state(level, AutonomyDecisionClass.REQUEST_PROOF)
        assert proof.permission_state is AutonomyPermissionState.REQUIRES_P5_PROOF
        assert proof.future_p5_required is True
        authority = resolve_permission_state(
            level, AutonomyDecisionClass.REQUEST_AUTHORITY
        )
        assert authority.permission_state is (
            AutonomyPermissionState.REQUIRES_P9_AUTHORITY
        )
        assert authority.future_p9_required is True


def test_no_unavailable_or_error_leakage_for_tiered_pairs() -> None:
    hard_override_classes = {
        AutonomyDecisionClass.UNAVAILABLE,
        AutonomyDecisionClass.ERROR,
    }
    for level in _TIERED_LEVELS:
        for decision_class in AutonomyDecisionClass:
            if decision_class in hard_override_classes:
                continue
            resolution = resolve_permission_state(level, decision_class)
            assert resolution.permission_state not in (
                AutonomyPermissionState.UNAVAILABLE,
                AutonomyPermissionState.ERROR,
            ), f"{level.value} + {decision_class.value} leaked"


def test_monotonicity_over_the_tier_ladder() -> None:
    """Once a class is allowed at a tier it stays allowed at higher tiers."""

    for decision_class in AutonomyDecisionClass:
        allowed_seen = False
        for level in _TIERED_LEVELS:
            resolution = resolve_permission_state(level, decision_class)
            is_allowed = (
                resolution.permission_state in ALLOWED_AUTONOMY_PERMISSION_STATES
            )
            if allowed_seen:
                assert is_allowed, (
                    f"{decision_class.value} regressed at {level.value}"
                )
            allowed_seen = allowed_seen or is_allowed


def test_unknown_raw_inputs_fail_closed() -> None:
    for raw_level, raw_class in (
        ("A99_GODMODE", "OBSERVE_STATE"),
        ("A2_PREPARE_CANDIDATES", "LAUNCH_MISSILES"),
        ("", ""),
    ):
        resolution = resolve_permission_state(raw_level, raw_class)
        assert resolution.permission_state is (
            AutonomyPermissionState.FORBIDDEN_IN_P3
        )
        assert resolution.requires_operator_review is True


def test_action_boundary_wraps_resolver_without_new_authority() -> None:
    boundary = resolve_action_boundary(
        GovernedAutonomyLevel.A2_PREPARE_CANDIDATES,
        AutonomyDecisionClass.PREPARE_RECOVERY_CANDIDATE,
    )
    assert boundary.candidate_only_allowed is True
    assert boundary.read_only_allowed is False
    assert boundary.execution_available is False
    assert boundary.runtime_submit_wired is False
    read_boundary = resolve_action_boundary(
        GovernedAutonomyLevel.A0_OBSERVE_ONLY,
        AutonomyDecisionClass.MARK_INTERNAL_READ_MODEL,
    )
    assert read_boundary.read_only_allowed is True
    assert read_boundary.candidate_only_allowed is False


def test_scope_envelope_bounds_without_authorizing() -> None:
    limits = (
        create_autonomy_scope_limit(
            dimension=AutonomyScopeDimension.RUN_SCOPE,
            limit_description="this run only",
        ),
        create_autonomy_scope_limit(
            dimension=AutonomyScopeDimension.COST_SCOPE,
            limit_description="100 cost units",
        ),
    )
    envelope = build_autonomy_scope_envelope(
        run_id="run-1",
        level=GovernedAutonomyLevel.A2_PREPARE_CANDIDATES,
        limits=limits,
    )
    assert envelope.covers(AutonomyScopeDimension.RUN_SCOPE) is True
    assert envelope.covers(AutonomyScopeDimension.NETWORK_SCOPE) is False
    assert envelope.scope_authorizes_action is False
    assert envelope.external_side_effects_allowed is False
    assert envelope.memory_write_allowed is False
    assert envelope.network_call_allowed is False
    assert envelope.tool_execution_allowed is False


def test_scope_envelope_rejects_duplicate_dimension_and_authority_claim() -> None:
    limit = create_autonomy_scope_limit(
        dimension=AutonomyScopeDimension.RUN_SCOPE, limit_description="run"
    )
    with pytest.raises(AurelFlowValidationError):
        build_autonomy_scope_envelope(
            run_id="run-1",
            level=GovernedAutonomyLevel.A1_SUGGEST_ONLY,
            limits=(limit, limit),
        )
    envelope = build_autonomy_scope_envelope(
        run_id="run-1",
        level=GovernedAutonomyLevel.A1_SUGGEST_ONLY,
        limits=(limit,),
    )
    with pytest.raises(AurelFlowValidationError):
        type(envelope)(
            **{
                **{
                    field.name: getattr(envelope, field.name)
                    for field in envelope.__dataclass_fields__.values()
                },
                "scope_authorizes_action": True,
            }
        )
