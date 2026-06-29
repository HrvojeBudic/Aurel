"""Tests for P2.4-C command proposal / no-execution boundary foundation."""

from __future__ import annotations

import json

import pytest

from agentic_runtime.aurel_shell.contracts import AurelShellValidationError
from agentic_runtime.aurel_shell.global_command_discovery import (
    build_global_command_query,
    build_global_command_result_set,
)
from agentic_runtime.aurel_shell.global_command_proposal import (
    P2_4_C_DEPENDENCY_PACK,
    P2_4_C_NEXT_PACK,
    P2_4_C_PACK_CHECKPOINT_IDS,
    P2_4_C_PACK_ID,
    P2_4_C_REPORT_PATH,
    P2_4_C_SECTION_ID,
    GlobalCommandInputPreviewStatus,
    GlobalCommandProposalGateStatus,
    GlobalCommandProposalResultStatus,
    GlobalCommandProposalStatus,
    GlobalCommandProposalTruthBoundary,
    GlobalCommandRequirementKind,
    GlobalCommandSelectionSource,
    P24CCommandProposalResult,
    assert_impact_preview_is_not_runtime_mutation,
    assert_input_preview_is_not_invocation,
    assert_no_execution_boundary_is_active,
    assert_omni_evidence_is_ignored_by_operator_instruction,
    assert_p2_4_c_depends_on_p2_4_b,
    assert_p2_4_c_does_not_start_future_work,
    assert_p2_4_c_side_effects_all_false,
    assert_preview_is_not_action,
    assert_proposal_is_not_approval,
    assert_requirement_preview_is_not_permission_enforcement,
    assert_selection_is_not_execution,
    build_global_command_proposal_gate,
    build_global_command_selection_intent,
    build_p2_4_c_command_proposal_result,
    build_p2_4_c_side_effect_proof,
    render_global_command_proposal_summary,
    serialize_p2_4_c_result,
)
from agentic_runtime.aurel_shell.global_command_registry import (
    COMMAND_EXECUTION_UNAVAILABLE_REASON,
    GlobalCommandAvailabilityStatus,
)


def test_module_imports_p2_4_c() -> None:
    import agentic_runtime.aurel_shell.global_command_proposal  # noqa: F401


def test_gate_dependency_and_omni_policy() -> None:
    result = build_p2_4_c_command_proposal_result()
    gate = result.proposal_gate

    assert P2_4_C_PACK_ID == "P2.4-C"
    assert P2_4_C_SECTION_ID == "P2.4"
    assert P2_4_C_PACK_CHECKPOINT_IDS == (
        "P2.4.11",
        "P2.4.12",
        "P2.4.13",
        "P2.4.14",
        "P2.4.15",
    )
    assert P2_4_C_DEPENDENCY_PACK == "P2.4-B"
    assert gate.repo_evidence_gate_passed is True
    assert gate.omni_evidence_required is False
    assert gate.omni_evidence_ignored_by_operator_instruction is True
    assert gate.dependency_result_set_ref.startswith("p2_4_b_global_command_result_set:")
    assert gate.dependency_unavailable_reason_ref == COMMAND_EXECUTION_UNAVAILABLE_REASON
    assert result.next_pack == P2_4_C_NEXT_PACK
    assert result.starts_future_work is False
    assert_p2_4_c_depends_on_p2_4_b(gate)
    assert_omni_evidence_is_ignored_by_operator_instruction(gate)


def test_closed_world_enums_reject_unknown_values() -> None:
    with pytest.raises(ValueError):
        GlobalCommandProposalGateStatus("OMNI_BLOCKED")
    with pytest.raises(ValueError):
        GlobalCommandSelectionSource("KEYBOARD_SHORTCUT")
    with pytest.raises(ValueError):
        GlobalCommandProposalStatus("APPROVED")
    with pytest.raises(ValueError):
        GlobalCommandInputPreviewStatus("HANDLER_VALIDATED")
    with pytest.raises(ValueError):
        GlobalCommandRequirementKind("PERMISSION_GRANTED")
    with pytest.raises(ValueError):
        GlobalCommandProposalResultStatus("EXECUTED")


def test_p2_4_11_selection_intent_builds_and_serializes() -> None:
    result_set = build_global_command_result_set()
    item = result_set.items[0]
    selection = build_global_command_selection_intent(item, result_set)

    assert selection.selection_source == GlobalCommandSelectionSource.RESULT_SET_ITEM
    assert selection.selected_command_id == item.command_id
    assert selection.selected_result_item_ref.startswith(item.result_item_id)
    assert selection.result_set_ref.startswith(result_set.result_set_id)
    assert selection.is_execution is False
    assert selection.is_invocation is False
    assert selection.is_operator_consent is False
    assert selection.is_approval is False
    assert selection.truth_label == "NOT_EXECUTION"
    assert json.loads(json.dumps(selection.to_canonical_dict()))
    assert_selection_is_not_execution(selection)


def test_p2_4_11_selection_assertion_rejects_execution_claim() -> None:
    result_set = build_global_command_result_set()
    selection = build_global_command_selection_intent(result_set.items[0], result_set)
    payload = selection.to_canonical_dict()
    payload["is_execution"] = True
    invalid = type(selection)(**payload)
    with pytest.raises(AurelShellValidationError):
        assert_selection_is_not_execution(invalid)


def test_p2_4_12_command_proposal_builds() -> None:
    result = build_p2_4_c_command_proposal_result()
    proposal = result.proposal

    assert proposal.selection_intent_ref.startswith(result.selection_intent.selection_id)
    assert proposal.command_id == result.selection_intent.selected_command_id
    assert proposal.proposal_status in (
        GlobalCommandProposalStatus.READY_FOR_PREVIEW,
        GlobalCommandProposalStatus.UNAVAILABLE_FOR_EXECUTION,
    )
    assert proposal.is_approval is False
    assert proposal.is_authorization is False
    assert proposal.executes_command is False
    if proposal.availability_status == GlobalCommandAvailabilityStatus.UNAVAILABLE_FOR_EXECUTION:
        assert proposal.unavailable_reason == COMMAND_EXECUTION_UNAVAILABLE_REASON
    assert_proposal_is_not_approval(proposal)


def test_p2_4_13_input_preview_builds() -> None:
    result = build_p2_4_c_command_proposal_result()
    preview = result.input_preview

    assert preview.required_inputs
    assert preview.optional_inputs
    assert preview.input_preview_status in (
        GlobalCommandInputPreviewStatus.READY,
        GlobalCommandInputPreviewStatus.PARTIAL,
        GlobalCommandInputPreviewStatus.EMPTY,
        GlobalCommandInputPreviewStatus.UNAVAILABLE,
    )
    assert preview.is_invocation is False
    assert preview.invokes_handler is False
    assert preview.executes_validation_runtime is False
    assert_input_preview_is_not_invocation(preview)


def test_p2_4_13_missing_input_state_represented() -> None:
    result = build_p2_4_c_command_proposal_result(provided_inputs=())
    preview = result.input_preview
    assert preview.missing_inputs
    assert preview.input_preview_status == GlobalCommandInputPreviewStatus.PARTIAL


def test_p2_4_13_provided_inputs_reduce_missing() -> None:
    result = build_p2_4_c_command_proposal_result(provided_inputs=("surface_id",))
    preview = result.input_preview
    assert "surface_id" in preview.provided_inputs
    assert "surface_id" not in preview.missing_inputs


def test_p2_4_14_impact_and_requirement_previews_build() -> None:
    result = build_p2_4_c_command_proposal_result()
    impact = result.impact_preview
    requirements = result.requirement_previews

    assert impact.declared_intent
    assert impact.declared_target
    assert impact.declared_scope
    assert impact.is_runtime_simulation is False
    assert impact.mutates_runtime is False
    assert impact.writes_memory is False
    assert impact.writes_trace is False
    assert impact.writes_storage is False
    assert_impact_preview_is_not_runtime_mutation(impact)

    assert requirements
    kinds = {preview.requirement_kind for preview in requirements}
    assert GlobalCommandRequirementKind.INPUT_REQUIRED in kinds
    assert GlobalCommandRequirementKind.EXECUTION_RUNTIME_REQUIRED_LATER in kinds
    for preview in requirements:
        assert preview.required_later is True
        assert preview.available_now is False
        assert preview.is_permission_decision is False
        assert preview.grants_permission is False
        assert preview.denies_permission is False
        assert preview.activates_approval is False
        assert_requirement_preview_is_not_permission_enforcement(preview)


def test_p2_4_14_requirement_preview_preserves_unavailable_reasons() -> None:
    result = build_p2_4_c_command_proposal_result()
    execution_requirement = next(
        preview
        for preview in result.requirement_previews
        if preview.requirement_kind
        == GlobalCommandRequirementKind.EXECUTION_RUNTIME_REQUIRED_LATER
    )
    assert execution_requirement.unavailable_reason == COMMAND_EXECUTION_UNAVAILABLE_REASON


def test_p2_4_15_no_execution_boundary_and_proposal_result() -> None:
    result = build_p2_4_c_command_proposal_result()
    boundary = result.no_execution_boundary
    proposal_result = result.proposal_result

    assert boundary.boundary_active is True
    assert boundary.execution_allowed is False
    assert boundary.approval_activated is False
    assert boundary.permission_enforced is False
    assert boundary.route_executed is False
    assert boundary.handler_invoked is False
    assert boundary.tool_invoked is False
    assert boundary.workflow_dispatched is False
    assert boundary.runtime_mutated is False
    assert boundary.memory_written is False
    assert boundary.trace_written is False
    assert boundary.storage_written is False
    assert_no_execution_boundary_is_active(boundary)

    assert proposal_result.result_status in (
        GlobalCommandProposalResultStatus.READY,
        GlobalCommandProposalResultStatus.PARTIAL,
        GlobalCommandProposalResultStatus.UNAVAILABLE_FOR_EXECUTION,
    )
    assert proposal_result.is_command_execution_result is False
    assert proposal_result.is_command_palette_ui is False
    assert proposal_result.is_preview_ui is False
    assert proposal_result.is_source_of_truth is False
    assert proposal_result.executes_commands is False
    assert_preview_is_not_action(proposal_result)


def test_p2_4_15_proposal_result_serializes_deterministically() -> None:
    result = build_p2_4_c_command_proposal_result()
    serialized_a = json.dumps(result.proposal_result.to_canonical_dict(), sort_keys=True)
    serialized_b = json.dumps(result.proposal_result.to_canonical_dict(), sort_keys=True)
    assert serialized_a == serialized_b


def test_result_serializes_and_summary() -> None:
    result = build_p2_4_c_command_proposal_result()
    summary = render_global_command_proposal_summary(result)

    assert result.pack_id == "P2.4-C"
    assert result.dependency_pack == "P2.4-B"
    assert result.next_pack == "P2.4-D"
    assert result.claims_live is False
    assert result.claims_trace_verified is False
    assert result.claims_release_scope is False
    assert result.claims_product_behavior is False
    assert "boundary_active=true" in summary
    assert "execution_allowed=false" in summary
    assert json.loads(serialize_p2_4_c_result(result))
    assert_p2_4_c_does_not_start_future_work(result)


def test_future_work_assertion_rejects_start_flag() -> None:
    result = build_p2_4_c_command_proposal_result()
    payload = result.to_canonical_dict()
    payload["starts_future_work"] = True
    invalid = P24CCommandProposalResult(**payload)
    with pytest.raises(AurelShellValidationError):
        assert_p2_4_c_does_not_start_future_work(invalid)


def test_side_effect_proof_all_false() -> None:
    proof = build_p2_4_c_side_effect_proof()
    assert_p2_4_c_side_effects_all_false(proof)
    for field, value in proof.to_canonical_dict().items():
        assert value is False, field


def test_p2_4_c_does_not_start_future_packs_in_side_effect_proof() -> None:
    proof = build_p2_4_c_side_effect_proof()
    assert proof.p2_4_d_started is False
    assert proof.p2_5_started is False
    assert proof.p2_6_started is False
    assert proof.p2_7_started is False
    assert proof.p2_10_started is False
    assert proof.p2_13_started is False


def test_report_path_constant() -> None:
    assert P2_4_C_REPORT_PATH == (
        "agent/reports/P2_4_C_COMMAND_PROPOSAL_NO_EXECUTION.md"
    )


def test_proposal_gate_builds_from_result_set() -> None:
    result_set = build_global_command_result_set()
    gate = build_global_command_proposal_gate(result_set)
    assert gate.gate_status == GlobalCommandProposalGateStatus.READY
    assert gate.truth_label == GlobalCommandProposalTruthBoundary.CONTRACT_ONLY.value


def test_empty_result_set_rejected() -> None:
    result_set = build_global_command_result_set(
        query=build_global_command_query("nonexistent_command_slug_xyz"),
    )
    if result_set.items:
        pytest.skip("unexpected matches for nonexistent query")
    with pytest.raises(AurelShellValidationError):
        build_p2_4_c_command_proposal_result(result_set=result_set)
