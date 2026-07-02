"""P3-FLOW-H drift/violation and safety-candidate behavior tests.

A violation creates a review need, never punishment or enforcement; a
downgrade candidate must strictly lower the tier; freeze/resume/escalation
candidates never stop, permit, or approve anything.
"""

from __future__ import annotations

import pytest

from agentic_runtime.aurel_flow import (
    AurelFlowValidationError,
    AutonomyModeSource,
    AutonomySafetyCandidateKind,
    AutonomySafetyTrigger,
    AutonomyViolationKind,
    GovernedAutonomyLevel,
    build_autonomy_safety_candidate,
    build_autonomy_violation_signal,
    detect_self_upgrade_violation,
    select_autonomy_mode,
)


def _mode(level: GovernedAutonomyLevel = GovernedAutonomyLevel.A2_PREPARE_CANDIDATES):
    return select_autonomy_mode(
        run_id="run-1",
        level=level,
        mode_source=AutonomyModeSource.OPERATOR_SELECTED,
        selected_by="op-1",
    )


def test_non_operator_upgrade_request_is_a_self_upgrade_violation() -> None:
    violation = detect_self_upgrade_violation(
        _mode(),
        requested_level=GovernedAutonomyLevel.A7_HIGH_AUTONOMY_BOUNDED,
        requested_by_operator=False,
    )
    assert violation is not None
    assert violation.kind is AutonomyViolationKind.SELF_UPGRADE_ATTEMPTED
    assert violation.attempted_self_upgrade is True
    assert violation.requires_freeze_candidate is True
    assert violation.requires_operator_review is True
    assert violation.execution_available is False
    assert violation.authority_granted is False


def test_operator_upgrade_request_is_not_a_violation() -> None:
    assert (
        detect_self_upgrade_violation(
            _mode(),
            requested_level=GovernedAutonomyLevel.A7_HIGH_AUTONOMY_BOUNDED,
            requested_by_operator=True,
        )
        is None
    )


def test_non_operator_downgrade_request_is_not_a_violation() -> None:
    assert (
        detect_self_upgrade_violation(
            _mode(),
            requested_level=GovernedAutonomyLevel.A0_OBSERVE_ONLY,
            requested_by_operator=False,
        )
        is None
    )


def test_non_operator_request_for_a9_is_a_violation() -> None:
    violation = detect_self_upgrade_violation(
        _mode(),
        requested_level=(
            GovernedAutonomyLevel.A9_HERETIC_MODE_LIVE_LOCKED_UNAVAILABLE
        ),
        requested_by_operator=False,
    )
    assert violation is not None
    assert violation.attempted_self_upgrade is True


def test_violation_is_not_punishment_or_enforcement() -> None:
    violation = build_autonomy_violation_signal(
        run_id="run-1",
        kind=AutonomyViolationKind.EXTERNAL_SIDE_EFFECT_ATTEMPTED,
        detail="candidate tried an external side effect",
    )
    assert violation.violation_is_not_punishment is True
    assert violation.violation_is_not_enforcement is True
    with pytest.raises(AurelFlowValidationError):
        type(violation)(
            **{
                **{
                    field.name: getattr(violation, field.name)
                    for field in violation.__dataclass_fields__.values()
                },
                "execution_available": True,
            }
        )


def test_self_upgrade_violation_cannot_be_constructed_unmarked() -> None:
    violation = build_autonomy_violation_signal(
        run_id="run-1",
        kind=AutonomyViolationKind.SELF_UPGRADE_ATTEMPTED,
        detail="attempted self-upgrade",
    )
    with pytest.raises(AurelFlowValidationError):
        type(violation)(
            **{
                **{
                    field.name: getattr(violation, field.name)
                    for field in violation.__dataclass_fields__.values()
                },
                "attempted_self_upgrade": False,
            }
        )


def test_downgrade_candidate_must_strictly_lower_the_tier() -> None:
    candidate = build_autonomy_safety_candidate(
        run_id="run-1",
        kind=AutonomySafetyCandidateKind.DOWNGRADE_CANDIDATE,
        trigger=AutonomySafetyTrigger.RETRY_STORM,
        from_level=GovernedAutonomyLevel.A4_INTERNAL_BOUNDED_AUTO,
        to_level=GovernedAutonomyLevel.A1_SUGGEST_ONLY,
        reason="retry storm",
    )
    assert candidate.mode_changed is False
    with pytest.raises(AurelFlowValidationError):
        build_autonomy_safety_candidate(
            run_id="run-1",
            kind=AutonomySafetyCandidateKind.DOWNGRADE_CANDIDATE,
            trigger=AutonomySafetyTrigger.RETRY_STORM,
            from_level=GovernedAutonomyLevel.A1_SUGGEST_ONLY,
            to_level=GovernedAutonomyLevel.A4_INTERNAL_BOUNDED_AUTO,
            reason="an upward 'downgrade' is a self-upgrade attempt",
        )
    with pytest.raises(AurelFlowValidationError):
        build_autonomy_safety_candidate(
            run_id="run-1",
            kind=AutonomySafetyCandidateKind.DOWNGRADE_CANDIDATE,
            trigger=AutonomySafetyTrigger.RETRY_STORM,
            from_level=GovernedAutonomyLevel.A1_SUGGEST_ONLY,
            to_level=None,
            reason="downgrade without target",
        )


def test_freeze_resume_escalation_candidates_do_not_act() -> None:
    freeze = build_autonomy_safety_candidate(
        run_id="run-1",
        kind=AutonomySafetyCandidateKind.FREEZE_CANDIDATE,
        trigger=AutonomySafetyTrigger.BUDGET_EXHAUSTED,
        from_level=GovernedAutonomyLevel.A3_INTERNAL_LOW_RISK_AUTO,
        reason="budget exhausted",
    )
    resume = build_autonomy_safety_candidate(
        run_id="run-1",
        kind=AutonomySafetyCandidateKind.RESUME_CANDIDATE,
        trigger=AutonomySafetyTrigger.OPERATOR_REVIEW_REQUIRED,
        from_level=GovernedAutonomyLevel.A3_INTERNAL_LOW_RISK_AUTO,
        reason="operator reviewed",
    )
    escalation = build_autonomy_safety_candidate(
        run_id="run-1",
        kind=AutonomySafetyCandidateKind.ESCALATION_CANDIDATE,
        trigger=AutonomySafetyTrigger.EVIDENCE_MISSING,
        from_level=GovernedAutonomyLevel.A3_INTERNAL_LOW_RISK_AUTO,
        reason="evidence missing",
    )
    assert freeze.execution_stopped is False
    assert resume.permission_granted is False
    assert escalation.approval_granted is False
    for candidate in (freeze, resume, escalation):
        assert candidate.mode_changed is False
        assert candidate.authority_granted is False
        assert candidate.requires_operator_review is True
