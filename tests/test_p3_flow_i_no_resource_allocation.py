"""P3-FLOW-I no-resource-allocation boundary tests.

No resource is allocated or reserved, no cost is billed, no token is
consumed, and no estimate can claim measured usage or proof.
"""

from __future__ import annotations

import dataclasses

import pytest

from agentic_runtime.aurel_flow import (
    AurelFlowValidationError,
    EstimateConfidence,
    WorkflowAtomicUnitKind,
    build_no_resource_allocation_proof,
    build_scheduling_estimate_read_model,
    create_context_window_estimate,
    create_cost_estimate,
    create_latency_estimate,
    create_token_budget_estimate,
    create_workflow_atomic_unit,
)


def _unit(node_ids: tuple[str, ...] = ("n1",)):
    return create_workflow_atomic_unit(
        run_id="run-1",
        unit_kind=WorkflowAtomicUnitKind.SINGLE_NODE,
        node_ids=node_ids,
    )


def _estimates(unit):
    return (
        create_cost_estimate(unit=unit, estimated_cost_micro_usd=1200),
        create_latency_estimate(unit=unit, estimated_latency_steps=4),
        create_token_budget_estimate(
            unit=unit,
            estimated_input_tokens=3000,
            estimated_output_tokens=800,
        ),
        create_context_window_estimate(
            unit=unit,
            estimated_context_window_tokens=16000,
            context_pressure_detected=True,
        ),
    )


def test_estimates_are_deterministic() -> None:
    unit = _unit()
    first = _estimates(unit)
    second = _estimates(unit)
    assert [e.estimate_id for e in first] == [e.estimate_id for e in second]


def test_cost_estimate_does_not_bill_cost() -> None:
    estimate = create_cost_estimate(unit=_unit(), estimated_cost_micro_usd=10)
    assert estimate.billing_performed is False
    with pytest.raises(AurelFlowValidationError):
        dataclasses.replace(estimate, billing_performed=True)


def test_token_estimate_does_not_consume_tokens() -> None:
    estimate = create_token_budget_estimate(
        unit=_unit(), estimated_input_tokens=100
    )
    assert estimate.tokens_consumed is False
    with pytest.raises(AurelFlowValidationError):
        dataclasses.replace(estimate, tokens_consumed=True)


def test_latency_and_context_estimates_are_not_measured_proof() -> None:
    unit = _unit()
    latency = create_latency_estimate(unit=unit, estimated_latency_steps=2)
    context = create_context_window_estimate(
        unit=unit, estimated_context_window_tokens=8000
    )
    for estimate in (latency, context):
        assert estimate.measured_usage is False
        assert estimate.proof_available is False
        for forbidden_field in ("measured_usage", "proof_available"):
            with pytest.raises(AurelFlowValidationError):
                dataclasses.replace(estimate, **{forbidden_field: True})


def test_exceeding_budget_forces_operator_review() -> None:
    estimate = create_cost_estimate(
        unit=_unit(),
        estimated_cost_micro_usd=10_000_000,
        estimate_confidence=EstimateConfidence.MEDIUM,
        exceeds_budget=True,
    )
    assert estimate.requires_operator_review is True
    with pytest.raises(AurelFlowValidationError):
        dataclasses.replace(estimate, requires_operator_review=False)


def test_estimate_read_model_rolls_up_budget_pressure() -> None:
    unit = _unit()
    cost, latency, tokens, context = _estimates(unit)
    over_budget = create_cost_estimate(
        unit=unit, estimated_cost_micro_usd=99, exceeds_budget=True
    )
    read_model = build_scheduling_estimate_read_model(
        unit=unit,
        cost_estimate=over_budget,
        latency_estimate=latency,
        token_budget_estimate=tokens,
        context_window_estimate=context,
    )
    assert read_model.any_exceeds_budget is True
    assert read_model.requires_operator_review is True
    assert read_model.billing_performed is False
    assert read_model.tokens_consumed is False
    calm = build_scheduling_estimate_read_model(unit=unit, cost_estimate=cost)
    assert calm.any_exceeds_budget is False


def test_estimate_read_model_rejects_foreign_unit_estimates() -> None:
    unit = _unit()
    other = _unit(node_ids=("n2",))
    with pytest.raises(AurelFlowValidationError):
        build_scheduling_estimate_read_model(
            unit=unit,
            cost_estimate=create_cost_estimate(
                unit=other, estimated_cost_micro_usd=1
            ),
        )


def test_no_resource_allocation_proof_is_all_false_and_fail_closed() -> None:
    proof = build_no_resource_allocation_proof()
    for boundary_field in (
        "is_p5_trace_proof",
        "resource_allocated",
        "resource_reserved",
        "measured_usage",
        "billing_performed",
        "tokens_consumed",
        "permission_granted",
        "authority_granted",
    ):
        assert getattr(proof, boundary_field) is False
        with pytest.raises(AurelFlowValidationError):
            dataclasses.replace(proof, **{boundary_field: True})
