"""P3-FLOW-H gate ladder behavior tests.

A gate decision restricts candidates; it is never authority and never
execution.
"""

from __future__ import annotations

import pytest

from agentic_runtime.aurel_flow import (
    AurelFlowValidationError,
    AutonomyDecisionClass,
    AutonomyGateDecision,
    AutonomyGateInput,
    GovernedAutonomyLevel,
    evaluate_autonomy_gate,
)


def _gate_input(
    *,
    risk_high: bool = False,
    irreversible: bool = False,
    reversibility_available: bool = True,
    external_side_effect: bool = False,
    budget_exhausted: bool = False,
    retry_storm_active: bool = False,
    no_progress_active: bool = False,
) -> AutonomyGateInput:
    return AutonomyGateInput(
        run_id="run-1",
        level=GovernedAutonomyLevel.A2_PREPARE_CANDIDATES,
        decision_class=AutonomyDecisionClass.PREPARE_PLAN,
        risk_high=risk_high,
        irreversible=irreversible,
        reversibility_available=reversibility_available,
        external_side_effect=external_side_effect,
        budget_exhausted=budget_exhausted,
        retry_storm_active=retry_storm_active,
        no_progress_active=no_progress_active,
    )


def test_budget_exhaustion_during_retry_storm_freezes_autonomy() -> None:
    result = evaluate_autonomy_gate(
        _gate_input(budget_exhausted=True, retry_storm_active=True)
    )
    assert result.decision is AutonomyGateDecision.FREEZE_AUTONOMY
    assert result.decision is not AutonomyGateDecision.ALLOW_CANDIDATE
    assert result.requires_operator_review is True


def test_retry_storm_alone_downgrades_not_allows() -> None:
    result = evaluate_autonomy_gate(_gate_input(retry_storm_active=True))
    assert result.decision is AutonomyGateDecision.DOWNGRADE_AUTONOMY


def test_no_progress_never_allows_candidate() -> None:
    result = evaluate_autonomy_gate(_gate_input(no_progress_active=True))
    assert result.decision is not AutonomyGateDecision.ALLOW_CANDIDATE
    assert result.decision is AutonomyGateDecision.REQUIRE_OPERATOR_REVIEW


def test_budget_exhaustion_alone_holds() -> None:
    result = evaluate_autonomy_gate(_gate_input(budget_exhausted=True))
    assert result.decision is AutonomyGateDecision.HOLD


def test_irreversible_without_reversibility_requires_checkpoint() -> None:
    result = evaluate_autonomy_gate(
        _gate_input(irreversible=True, reversibility_available=False)
    )
    assert result.decision is AutonomyGateDecision.REQUIRE_CHECKPOINT
    assert result.decision is not AutonomyGateDecision.ALLOW_CANDIDATE


def test_irreversible_with_reversibility_requires_proof() -> None:
    result = evaluate_autonomy_gate(
        _gate_input(irreversible=True, reversibility_available=True)
    )
    assert result.decision is AutonomyGateDecision.REQUIRE_PROOF
    assert result.future_p5_required is True


def test_high_risk_external_side_effect_blocks() -> None:
    result = evaluate_autonomy_gate(
        _gate_input(risk_high=True, external_side_effect=True)
    )
    assert result.decision is AutonomyGateDecision.BLOCK
    assert result.future_p4_required is True
    assert result.future_p9_required is True


def test_external_side_effect_alone_requires_authority() -> None:
    result = evaluate_autonomy_gate(_gate_input(external_side_effect=True))
    assert result.decision is AutonomyGateDecision.REQUIRE_AUTHORITY
    assert result.future_p9_required is True


def test_high_risk_alone_requires_verifier() -> None:
    result = evaluate_autonomy_gate(_gate_input(risk_high=True))
    assert result.decision is AutonomyGateDecision.REQUIRE_VERIFIER


def test_clean_input_allows_candidate_only() -> None:
    result = evaluate_autonomy_gate(_gate_input())
    assert result.decision is AutonomyGateDecision.ALLOW_CANDIDATE
    assert result.execution_available is False
    assert result.authority_granted is False


def test_gate_result_is_deterministic_and_never_authority() -> None:
    first = evaluate_autonomy_gate(_gate_input(risk_high=True))
    second = evaluate_autonomy_gate(_gate_input(risk_high=True))
    assert first.gate_id == second.gate_id
    assert first.gate_is_not_authority is True
    assert first.gate_is_not_execution is True
    with pytest.raises(AurelFlowValidationError):
        type(first)(
            **{
                **{
                    field.name: getattr(first, field.name)
                    for field in first.__dataclass_fields__.values()
                },
                "authority_granted": True,
            }
        )
