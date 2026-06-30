"""Tests for P2.7-C Shell binding preview / selection / confirmation boundary."""

from __future__ import annotations

import json
from dataclasses import fields

import pytest

from agentic_runtime.aurel_shell.shell_binding_preview_selection import (
    P2_7_B_REPORT_PATH,
    P2_7_C_DEPENDENCY_PACK,
    P2_7_C_NEXT_PACK,
    P2_7_C_OFFICIAL_SECTION_NAME,
    P2_7_C_PACK_CHECKPOINT_IDS,
    P2_7_C_PACK_ID,
    P2_7_C_REPORT_PATH,
    P2_7_C_SECTION_ID,
    P2_7_C_VALIDATION_COMMANDS,
    P27CShellBindingPreviewSelectionResult,
    P27CSideEffectProof,
    ShellBindingConfirmationOutcomeStatus,
    ShellBindingConfirmationRequirementStatus,
    ShellBindingPreviewGateStatus,
    ShellBindingPreviewItemKind,
    ShellBindingPreviewRiskKind,
    ShellBindingSelectionMode,
    assert_cancel_reject_defer_are_not_runtime_transitions,
    assert_confirmation_boundary_result_is_not_execution,
    assert_confirmation_intent_is_not_authority,
    assert_confirmation_outcome_is_not_custos_decision,
    assert_confirmation_requirement_is_not_approval,
    assert_confirmed_state_is_not_permission_grant,
    assert_omni_evidence_is_ignored_by_operator_instruction,
    assert_p2_7_c_does_not_start_future_work,
    assert_p2_7_c_side_effects_all_false,
    assert_preview_bundle_is_not_ui,
    assert_preview_gate_depends_on_p2_7_b,
    assert_preview_item_is_not_product_ui,
    assert_selected_binding_is_not_invoked_binding,
    assert_selection_intent_is_not_execution,
    assert_selection_state_does_not_mutate_runtime,
    build_p2_7_c_shell_binding_preview_selection_result,
    build_p2_7_c_side_effect_proof,
    build_shell_binding_cancel_descriptor,
    build_shell_binding_confirmation_boundary_result,
    build_shell_binding_confirmation_intent,
    build_shell_binding_confirmation_outcome_read_model,
    build_shell_binding_confirmation_requirement,
    build_shell_binding_defer_descriptor,
    build_shell_binding_preview_bundle,
    build_shell_binding_preview_gate,
    build_shell_binding_preview_item,
    build_shell_binding_preview_items,
    build_shell_binding_preview_risk_note,
    build_shell_binding_reject_descriptor,
    build_shell_binding_selected_intent,
    build_shell_binding_selection_candidate,
    build_shell_binding_selection_state,
    render_shell_binding_preview_summary,
    serialize_p2_7_c_result,
)
from agentic_runtime.aurel_shell.shell_binding_read_models import (
    P2_7_B_PACK_ID,
    build_p2_7_b_shell_binding_read_model_result,
)
from agentic_runtime.aurel_shell.surface_registry import OLD_SURFACE_TAXONOMY


def _roundtrip(obj) -> dict:
    return json.loads(json.dumps(obj.to_canonical_dict(), sort_keys=True))


def test_module_imports_p2_7_c() -> None:
    import agentic_runtime.aurel_shell.shell_binding_preview_selection  # noqa: F401


# ---------------------------------------------------------------------------
# Gate / dependency tests
# ---------------------------------------------------------------------------


def test_gate_dependency_and_omni_policy() -> None:
    result = build_p2_7_c_shell_binding_preview_selection_result()
    gate = result.preview_gate

    assert P2_7_C_PACK_ID == "P2.7-C"
    assert P2_7_C_SECTION_ID == "P2.7"
    assert P2_7_C_OFFICIAL_SECTION_NAME == "Shell / CLI / TUI Binding"
    assert P2_7_C_DEPENDENCY_PACK == "P2.7-B"
    assert gate.dependency_pack == "P2.7-B"
    assert gate.dependency_report_ref == P2_7_B_REPORT_PATH
    assert gate.dependency_adapter_expansion_result_ref
    assert gate.dependency_side_effect_proof_ref == "P27BSideEffectProof:all_false"
    assert gate.repo_evidence_gate_passed is True
    assert gate.omni_evidence_required is False
    assert gate.omni_evidence_ignored_by_operator_instruction is True
    assert_preview_gate_depends_on_p2_7_b(gate)
    assert_omni_evidence_is_ignored_by_operator_instruction(gate)


def test_p2_7_b_evidence_represented() -> None:
    read_model = build_p2_7_b_shell_binding_read_model_result()
    result = build_p2_7_c_shell_binding_preview_selection_result()

    assert read_model.pack_id == P2_7_B_PACK_ID
    assert result.p2_7_b_evidence_ref.startswith(P2_7_B_REPORT_PATH)
    assert (
        read_model.adapter_expansion_result.adapter_expansion_result_id
        in result.preview_gate.dependency_adapter_expansion_result_ref
    )


def test_p2_7_c_does_not_start_future_work() -> None:
    result = build_p2_7_c_shell_binding_preview_selection_result()
    assert result.next_pack == P2_7_C_NEXT_PACK == "P2.7-D"
    assert result.starts_future_work is False
    assert result.side_effect_proof.p2_7_d_started is False
    assert result.side_effect_proof.p2_8_started is False
    assert result.side_effect_proof.p2_10_started is False
    assert result.side_effect_proof.p2_13_started is False
    assert_p2_7_c_does_not_start_future_work(result)


def test_closed_world_enums_reject_unknown_values() -> None:
    with pytest.raises(ValueError):
        ShellBindingPreviewGateStatus("LIVE")
    with pytest.raises(ValueError):
        ShellBindingPreviewItemKind("EXECUTABLE")
    with pytest.raises(ValueError):
        ShellBindingPreviewRiskKind("LIVE")
    with pytest.raises(ValueError):
        ShellBindingSelectionMode("EXECUTE")
    with pytest.raises(ValueError):
        ShellBindingConfirmationRequirementStatus("APPROVED")
    with pytest.raises(ValueError):
        ShellBindingConfirmationOutcomeStatus("EXECUTED")


# ---------------------------------------------------------------------------
# P2.7.11 — Binding Preview Bundle / Safe Preview Contract
# ---------------------------------------------------------------------------


def test_p2_7_11_preview_gate_bundle_items_risk_notes() -> None:
    gate = build_shell_binding_preview_gate()
    bundle = build_shell_binding_preview_bundle()
    item = build_shell_binding_preview_item()
    risk = build_shell_binding_preview_risk_note()

    assert gate.gate_status in set(ShellBindingPreviewGateStatus)
    assert gate.created_for_pack == "P2.7-C"
    assert gate.official_section_name == "Shell / CLI / TUI Binding"

    assert bundle.is_ui is False
    assert bundle.is_product_ui is False
    assert bundle.source_pack_ref == "P2.7-B"
    assert len(bundle.preview_items) > 0
    assert len(bundle.risk_notes) > 0
    assert len(bundle.selection_candidates) > 0
    assert bundle.confirmation_requirement_ref

    assert item.available_as_preview is True
    assert item.renders_ui is False
    assert item.creates_product_ui is False

    assert risk.enforces_policy is False
    assert risk.activates_approval is False

    for preview_item in bundle.preview_items:
        assert preview_item.renders_ui is False
        assert preview_item.creates_product_ui is False
    for risk_note in bundle.risk_notes:
        assert risk_note.enforces_policy is False
        assert risk_note.activates_approval is False

    assert_preview_bundle_is_not_ui(bundle)
    assert_preview_item_is_not_product_ui(item)
    assert _roundtrip(gate)
    assert _roundtrip(bundle)
    assert _roundtrip(item)
    assert _roundtrip(risk)


# ---------------------------------------------------------------------------
# P2.7.12 — Binding Selection Intent / Non-Executable Selection Contract
# ---------------------------------------------------------------------------


def test_p2_7_12_selection_intent_candidate_state() -> None:
    items = build_shell_binding_preview_items()
    candidate = build_shell_binding_selection_candidate(source_preview_item=items[0])
    state = build_shell_binding_selection_state()
    intent = build_shell_binding_selected_intent(
        source_preview_item=items[0],
        source_selection_candidate=candidate,
        selection_state=state,
    )

    assert state.selection_mode in set(ShellBindingSelectionMode)
    assert candidate.selectable_as_contract is True
    assert candidate.selectable_as_runtime_action is False

    assert intent.invokes_binding is False
    assert intent.executes_command is False
    assert intent.dispatches_runtime is False

    assert state.mutates_runtime_state is False
    assert state.mutates_shell_state is False
    assert state.executes_selection is False

    assert_selection_intent_is_not_execution(intent)
    assert_selected_binding_is_not_invoked_binding(intent)
    assert_selection_state_does_not_mutate_runtime(state)
    assert _roundtrip(candidate)
    assert _roundtrip(state)
    assert _roundtrip(intent)


# ---------------------------------------------------------------------------
# P2.7.13 — Operator Confirmation Requirement / Confirmation Intent Boundary
# ---------------------------------------------------------------------------


def test_p2_7_13_confirmation_requirement_and_intent() -> None:
    requirement = build_shell_binding_confirmation_requirement()
    intent = build_shell_binding_confirmation_intent()

    assert requirement.requirement_status in set(
        ShellBindingConfirmationRequirementStatus
    )
    assert requirement.requires_approval_runtime is False
    assert requirement.activates_approval is False
    assert requirement.activates_hitl is False

    assert intent.operator_intent_recorded_as_contract is True
    assert intent.grants_authority is False
    assert intent.grants_permission is False
    assert intent.activates_approval is False
    assert intent.executes_binding is False

    assert_confirmation_requirement_is_not_approval(requirement)
    assert_confirmation_intent_is_not_authority(intent)
    assert _roundtrip(requirement)
    assert _roundtrip(intent)


# ---------------------------------------------------------------------------
# P2.7.14 — Confirmation Outcome / Cancel / Reject / Defer Read Model
# ---------------------------------------------------------------------------


def test_p2_7_14_outcome_cancel_reject_defer() -> None:
    outcome = build_shell_binding_confirmation_outcome_read_model()
    cancel = build_shell_binding_cancel_descriptor()
    reject = build_shell_binding_reject_descriptor()
    defer = build_shell_binding_defer_descriptor()

    assert outcome.outcome_status in set(ShellBindingConfirmationOutcomeStatus)
    assert outcome.confirmed_state_is_contract_only is True
    assert outcome.is_custos_decision is False
    assert outcome.is_permission_grant is False
    assert outcome.is_runtime_transition is False

    assert cancel.cancels_runtime is False
    assert cancel.mutates_runtime is False
    assert reject.denies_permission is False
    assert reject.mutates_runtime is False
    assert defer.creates_schedule is False
    assert defer.mutates_runtime is False

    assert_confirmation_outcome_is_not_custos_decision(outcome)
    assert_confirmed_state_is_not_permission_grant(outcome)
    assert_cancel_reject_defer_are_not_runtime_transitions(
        cancel=cancel, reject=reject, defer=defer
    )
    assert _roundtrip(outcome)
    assert _roundtrip(cancel)
    assert _roundtrip(reject)
    assert _roundtrip(defer)


# ---------------------------------------------------------------------------
# P2.7.15 — Preview Selection Boundary Result / No-Execution Contract
# ---------------------------------------------------------------------------


def test_p2_7_15_confirmation_boundary_result() -> None:
    boundary = build_shell_binding_confirmation_boundary_result()
    result = build_p2_7_c_shell_binding_preview_selection_result()

    assert boundary.creates_ui is False
    assert boundary.creates_product_ui is False
    assert boundary.creates_command_execution is False
    assert boundary.creates_operator_confirmation_runtime is False
    assert boundary.creates_approval_runtime is False
    assert boundary.activates_hitl_approval is False
    assert boundary.creates_permission_enforcement is False
    assert boundary.creates_custos_decision is False
    assert boundary.creates_runtime_dispatch is False
    assert boundary.creates_runtime_mutation is False
    assert boundary.creates_trace_write is False
    assert boundary.creates_product_behavior is False
    assert_confirmation_boundary_result_is_not_execution(boundary)

    assert result.covered_checkpoints == P2_7_C_PACK_CHECKPOINT_IDS
    assert result.next_pack == "P2.7-D"
    assert result.claims_live is False
    assert result.claims_trace_verified is False
    assert result.claims_release_scope is False
    assert result.claims_product_behavior is False
    assert _roundtrip(boundary)


def test_surface_taxonomy_drift_does_not_activate_old_surfaces() -> None:
    result = build_p2_7_c_shell_binding_preview_selection_result()
    surface_set = result.preview_bundle.official_surface_set
    for old_surface in OLD_SURFACE_TAXONOMY:
        assert old_surface not in surface_set


# ---------------------------------------------------------------------------
# Side-effect proof
# ---------------------------------------------------------------------------


def test_side_effect_proof_all_false() -> None:
    proof = build_p2_7_c_side_effect_proof()
    assert_p2_7_c_side_effects_all_false(proof)
    for field in fields(P27CSideEffectProof):
        assert getattr(proof, field.name) is False


def test_serialization_and_summary() -> None:
    result = build_p2_7_c_shell_binding_preview_selection_result()
    serialized = serialize_p2_7_c_result(result)
    assert isinstance(serialized, str)
    assert "P2.7" in serialized
    # Determinism: serialization is stable across builds.
    assert serialize_p2_7_c_result() == serialized

    summary = render_shell_binding_preview_summary(result)
    assert "Shell / CLI / TUI Binding" in summary
    assert "P2.7-D" in summary
    assert "command_execution=false" in summary
    assert "approval_runtime=false" in summary
    assert "custos_decision=false" in summary


def test_pack_result_type() -> None:
    result = build_p2_7_c_shell_binding_preview_selection_result()
    assert isinstance(result, P27CShellBindingPreviewSelectionResult)
    assert result.pack_id == P2_7_C_PACK_ID
    assert P2_7_C_REPORT_PATH.endswith(".md")
    assert len(P2_7_C_VALIDATION_COMMANDS) == 5
