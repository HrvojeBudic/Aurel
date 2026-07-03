"""P3-FLOW-I model/tool/sandbox/data requirement frame tests.

A requirement is not invocation: naming a model, tool, sandbox, or data
requirement never calls, invokes, executes, or accesses anything.
"""

from __future__ import annotations

import dataclasses

import pytest

from agentic_runtime.aurel_flow import (
    AurelFlowValidationError,
    FlowTruthLabel,
    WorkflowAtomicUnitKind,
    build_execution_resource_requirement_read_model,
    create_data_access_requirement_frame,
    create_model_requirement_frame,
    create_sandbox_requirement_frame,
    create_tool_requirement_frame,
    create_workflow_atomic_unit,
)


def _unit(node_ids: tuple[str, ...] = ("n1",)):
    return create_workflow_atomic_unit(
        run_id="run-1",
        unit_kind=WorkflowAtomicUnitKind.SINGLE_NODE,
        node_ids=node_ids,
    )


def test_model_requirement_is_not_llm_call() -> None:
    frame = create_model_requirement_frame(
        unit=_unit(), model_required=True, model_class="frontier"
    )
    assert frame.model_invoked is False
    assert frame.tokens_consumed is False
    assert frame.requires_p4_execution is True
    assert frame.requires_p9_authority is True
    for forbidden_field in ("model_invoked", "tokens_consumed"):
        with pytest.raises(AurelFlowValidationError):
            dataclasses.replace(frame, **{forbidden_field: True})
    for required_field in ("requires_p4_execution", "requires_p9_authority"):
        with pytest.raises(AurelFlowValidationError):
            dataclasses.replace(frame, **{required_field: False})


def test_tool_requirement_is_not_tool_call() -> None:
    frame = create_tool_requirement_frame(
        unit=_unit(), tool_required=True, tool_names=("git", "fs")
    )
    assert frame.tool_names == ("fs", "git")
    assert frame.tool_invoked is False
    with pytest.raises(AurelFlowValidationError):
        dataclasses.replace(frame, tool_invoked=True)


def test_sandbox_requirement_is_not_sandbox_execution() -> None:
    frame = create_sandbox_requirement_frame(
        unit=_unit(), sandbox_required=True, sandbox_profile="restricted"
    )
    assert frame.sandbox_executed is False
    assert frame.subprocess_spawned is False
    for forbidden_field in ("sandbox_executed", "subprocess_spawned"):
        with pytest.raises(AurelFlowValidationError):
            dataclasses.replace(frame, **{forbidden_field: True})


def test_data_access_requirement_is_not_data_access() -> None:
    frame = create_data_access_requirement_frame(
        unit=_unit(),
        data_access_required=True,
        network_required=True,
        memory_required=True,
    )
    assert frame.data_access_performed is False
    assert frame.network_called is False
    assert frame.memory_access_performed is False
    for forbidden_field in (
        "data_access_performed",
        "network_called",
        "memory_access_performed",
    ):
        with pytest.raises(AurelFlowValidationError):
            dataclasses.replace(frame, **{forbidden_field: True})


def test_requirement_frames_are_deterministic() -> None:
    unit = _unit()
    first = create_model_requirement_frame(unit=unit, model_required=True)
    second = create_model_requirement_frame(unit=unit, model_required=True)
    assert first.requirement_id == second.requirement_id


def test_requirement_read_model_aggregates_presence() -> None:
    unit = _unit()
    read_model = build_execution_resource_requirement_read_model(
        unit=unit,
        model_requirement=create_model_requirement_frame(
            unit=unit, model_required=True
        ),
        tool_requirement=create_tool_requirement_frame(
            unit=unit, tool_required=False
        ),
    )
    assert read_model.any_requirement_present is True
    assert read_model.truth_label is FlowTruthLabel.READ_MODEL_ONLY
    assert read_model.model_invoked is False
    assert read_model.tool_invoked is False
    assert read_model.sandbox_executed is False
    assert read_model.network_called is False
    empty = build_execution_resource_requirement_read_model(unit=unit)
    assert empty.any_requirement_present is False


def test_requirement_read_model_rejects_foreign_unit_frames() -> None:
    unit = _unit()
    other = _unit(node_ids=("n2",))
    with pytest.raises(AurelFlowValidationError):
        build_execution_resource_requirement_read_model(
            unit=unit,
            model_requirement=create_model_requirement_frame(
                unit=other, model_required=True
            ),
        )


def test_requirement_read_model_cannot_claim_invocation() -> None:
    read_model = build_execution_resource_requirement_read_model(unit=_unit())
    for forbidden_field in (
        "model_invoked",
        "tool_invoked",
        "sandbox_executed",
        "network_called",
        "data_access_performed",
        "memory_access_performed",
    ):
        with pytest.raises(AurelFlowValidationError):
            dataclasses.replace(read_model, **{forbidden_field: True})
