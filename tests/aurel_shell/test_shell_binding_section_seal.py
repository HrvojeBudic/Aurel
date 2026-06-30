"""Tests for P2.7-D Shell / CLI / TUI binding section seal contracts."""

from __future__ import annotations

import json
from dataclasses import fields

import pytest

from agentic_runtime.aurel_shell.shell_binding_preview_selection import (
    P2_7_C_PACK_ID,
    build_p2_7_c_shell_binding_preview_selection_result,
)
from agentic_runtime.aurel_shell.shell_binding_section_seal import (
    P2_7_A_REPORT_PATH,
    P2_7_B_REPORT_PATH,
    P2_7_C_REPORT_PATH,
    P2_7_D_DEPENDENCY_PACK,
    P2_7_D_FULL_SECTION_CHECKPOINTS,
    P2_7_D_NEXT_PACK,
    P2_7_D_OFFICIAL_SECTION_NAME,
    P2_7_D_PACK_CHECKPOINT_IDS,
    P2_7_D_PACK_ID,
    P2_7_D_REPORT_PATH,
    P2_7_D_SECTION_ID,
    P2_7_D_TEST_REF,
    P2_7_D_VALIDATION_COMMANDS,
    P27DShellBindingSectionSealResult,
    P27DSideEffectProof,
    ShellBindingP28HandoffStatus,
    ShellBindingSectionContractEntryStatus,
    ShellBindingSectionSealGateStatus,
    ShellBindingSectionSealStatus,
    ShellBindingSectionSealTruthBoundary,
    ShellBindingSectionValidationStatus,
    assert_availability_rollup_is_not_permission_enforcement,
    assert_binding_section_complete_is_not_live_binding,
    assert_contract_inventory_is_not_source_of_truth_duplication,
    assert_contract_scope_demo_is_not_product_demo,
    assert_evidence_rollup_is_not_trace_verified,
    assert_no_live_binding_proof_is_active,
    assert_omni_evidence_is_ignored_by_operator_instruction,
    assert_p2_7_complete_is_not_p2_complete,
    assert_p2_7_d_does_not_start_future_work,
    assert_p2_7_d_side_effects_all_false,
    assert_p2_8_handoff_is_not_p2_8_implementation,
    assert_runtime_unavailable_rollup_is_not_runtime_implementation,
    assert_section_gate_depends_on_p2_7_c,
    assert_section_seal_is_not_release_seal,
    assert_validation_rollup_does_not_invent_pass,
    build_p2_7_d_shell_binding_section_seal_result,
    build_p2_7_d_side_effect_proof,
    build_shell_binding_availability_rollup,
    build_shell_binding_contract_scope_demo,
    build_shell_binding_no_live_binding_proof,
    build_shell_binding_p2_8_handoff_contract,
    build_shell_binding_runtime_unavailable_rollup,
    build_shell_binding_section_contract_inventory,
    build_shell_binding_section_read_model,
    build_shell_binding_section_read_model_version,
    build_shell_binding_section_seal_gate,
    build_shell_binding_section_seal_result,
    build_shell_binding_section_validation_rollup,
    render_shell_binding_section_seal_summary,
    serialize_p2_7_d_result,
)
from agentic_runtime.aurel_shell.surface_registry import OLD_SURFACE_TAXONOMY


def _roundtrip(obj) -> dict:
    return json.loads(json.dumps(obj.to_canonical_dict(), sort_keys=True))


def test_module_imports_p2_7_d() -> None:
    import agentic_runtime.aurel_shell.shell_binding_section_seal  # noqa: F401


def test_gate_dependency_and_omni_policy() -> None:
    result = build_p2_7_d_shell_binding_section_seal_result()
    gate = result.section_seal_gate

    assert P2_7_D_PACK_ID == "P2.7-D"
    assert P2_7_D_SECTION_ID == "P2.7"
    assert P2_7_D_OFFICIAL_SECTION_NAME == "Shell / CLI / TUI Binding"
    assert P2_7_D_DEPENDENCY_PACK == "P2.7-C"
    assert gate.dependency_pack == P2_7_C_PACK_ID
    assert gate.dependency_report_ref == P2_7_C_REPORT_PATH
    assert gate.dependency_confirmation_boundary_result_ref
    assert gate.dependency_side_effect_proof_ref == "P27CSideEffectProof:all_false"
    assert gate.p2_7_a_evidence_ref == P2_7_A_REPORT_PATH
    assert gate.p2_7_b_evidence_ref == P2_7_B_REPORT_PATH
    assert gate.p2_7_c_evidence_ref == P2_7_C_REPORT_PATH
    assert gate.repo_evidence_gate_passed is True
    assert gate.omni_evidence_required is False
    assert gate.omni_evidence_ignored_by_operator_instruction is True
    assert gate.gate_status is ShellBindingSectionSealGateStatus.READY
    assert_section_gate_depends_on_p2_7_c(gate)
    assert_omni_evidence_is_ignored_by_operator_instruction(gate)


def test_p2_7_c_confirmation_boundary_and_side_effect_represented() -> None:
    preview = build_p2_7_c_shell_binding_preview_selection_result()
    result = build_p2_7_d_shell_binding_section_seal_result()

    assert preview.pack_id == "P2.7-C"
    assert result.p2_7_c_evidence_ref.startswith(P2_7_C_REPORT_PATH)
    assert (
        preview.confirmation_boundary_result.confirmation_boundary_result_id
        in result.section_seal_gate.dependency_confirmation_boundary_result_ref
    )
    assert result.section_seal_gate.dependency_side_effect_proof_ref


def test_p2_7_d_does_not_start_future_work() -> None:
    result = build_p2_7_d_shell_binding_section_seal_result()
    assert result.next_pack == P2_7_D_NEXT_PACK == "P2.8-A"
    assert result.starts_future_work is False
    assert result.side_effect_proof.p2_8_started is False
    assert result.side_effect_proof.p2_10_started is False
    assert result.side_effect_proof.p2_13_started is False
    assert_p2_7_d_does_not_start_future_work(result)


def test_closed_world_enums_reject_unknown_values() -> None:
    with pytest.raises(ValueError):
        ShellBindingSectionSealGateStatus("LIVE")
    with pytest.raises(ValueError):
        ShellBindingSectionContractEntryStatus("TRACE_VERIFIED")
    with pytest.raises(ValueError):
        ShellBindingSectionSealStatus("RELEASE_SEALED")
    with pytest.raises(ValueError):
        ShellBindingP28HandoffStatus("P2_8_STARTED")
    with pytest.raises(ValueError):
        ShellBindingSectionValidationStatus("PASS")


def test_p2_7_16_section_seal_gate_and_inventory() -> None:
    gate = build_shell_binding_section_seal_gate()
    inventory = build_shell_binding_section_contract_inventory()

    assert gate.gate_status in set(ShellBindingSectionSealGateStatus)
    assert gate.created_for_pack == "P2.7-D"
    assert inventory.created_for_pack == "P2.7-D"
    assert inventory.covered_checkpoints == P2_7_D_FULL_SECTION_CHECKPOINTS
    assert len(inventory.contract_entries) == 21
    assert inventory.is_source_of_truth is False
    assert inventory.duplicates_source_evidence is False
    assert inventory.source_pack_refs == ("P2.7-A", "P2.7-B", "P2.7-C", "P2.7-D")
    assert inventory.source_report_refs == (
        P2_7_A_REPORT_PATH,
        P2_7_B_REPORT_PATH,
        P2_7_C_REPORT_PATH,
        P2_7_D_REPORT_PATH,
    )
    assert inventory.source_validation_refs
    assert all(
        entry.status is ShellBindingSectionContractEntryStatus.DONE
        for entry in inventory.contract_entries
    )
    assert inventory.contract_entries[0].source_contract_ref
    assert_contract_inventory_is_not_source_of_truth_duplication(inventory)
    assert _roundtrip(gate)
    assert _roundtrip(inventory)


def test_p2_7_17_section_read_model_status_contract() -> None:
    read_model = build_shell_binding_section_read_model()
    version = build_shell_binding_section_read_model_version()

    assert version.compatible_section == "P2.7"
    assert version.compatible_pack == "P2.7-D"
    assert version.breaking_change is False
    assert read_model.section_status is ShellBindingSectionSealStatus.SEALED_CONTRACT_ONLY
    assert read_model.sealed_contract_only is True
    assert read_model.is_release_seal is False
    assert read_model.is_shell_complete is False
    assert read_model.is_p2_complete is False
    assert read_model.is_live_binding is False
    assert read_model.next_pack == "P2.8-A"
    assert_binding_section_complete_is_not_live_binding(read_model)
    assert_p2_7_complete_is_not_p2_complete(read_model)
    assert _roundtrip(read_model)


def test_p2_7_18_availability_runtime_unavailable_and_handoff() -> None:
    availability = build_shell_binding_availability_rollup()
    unavailable = build_shell_binding_runtime_unavailable_rollup()
    handoff = build_shell_binding_p2_8_handoff_contract()

    assert availability.contract_binding_available is True
    assert availability.live_binding_available is False
    assert availability.cli_descriptor_available is True
    assert availability.tui_descriptor_available is True
    assert availability.shell_descriptor_available is True
    assert availability.command_surface_descriptor_available is True
    assert availability.preview_selection_available is True
    assert availability.confirmation_boundary_available is True
    assert availability.permission_enforcement_available is False
    assert availability.approval_runtime_available is False
    assert_availability_rollup_is_not_permission_enforcement(availability)

    for capability in (
        "CLI runner",
        "TUI runtime",
        "Shell state runtime",
        "Command execution",
        "Approval runtime",
        "Permission enforcement",
        "Custos decisioning",
        "P2.8 implementation",
    ):
        assert capability in unavailable.unavailable_capabilities
    assert unavailable.creates_runtime is False
    assert_runtime_unavailable_rollup_is_not_runtime_implementation(unavailable)

    assert handoff.handoff_to_pack == "P2.8-A"
    assert handoff.handoff_to_section == "P2.8 — Shell State / Reports / Docs"
    assert handoff.requires_p2_8 is True
    assert handoff.starts_p2_8 is False
    assert handoff.implements_p2_8 is False
    assert handoff.creates_shell_state_runtime is False
    assert_p2_8_handoff_is_not_p2_8_implementation(handoff)


def test_p2_7_19_validation_rollup_and_report_refs() -> None:
    rollup = build_shell_binding_section_validation_rollup()
    result = build_p2_7_d_shell_binding_section_seal_result()

    assert rollup.source_validation_refs
    assert rollup.commands_recorded == P2_7_D_VALIDATION_COMMANDS
    assert rollup.focused_tests_recorded == P2_7_D_TEST_REF
    assert rollup.nearby_tests_recorded == "tests/aurel_shell"
    assert rollup.ruff_recorded == "NOT_RUN_AT_BUILD"
    assert rollup.mypy_recorded == "NOT_RUN_AT_BUILD"
    assert rollup.invented_pass is False
    assert rollup.validation_status is ShellBindingSectionValidationStatus.NOT_RUN_AT_BUILD
    assert_validation_rollup_does_not_invent_pass(rollup)
    assert_evidence_rollup_is_not_trace_verified(result)
    assert result.side_effect_proof.runtime_mutated is False
    assert result.side_effect_proof.trace_written is False
    assert P2_7_D_REPORT_PATH.replace("/", "") in serialize_p2_7_d_result(result).replace("/", "")


def test_p2_7_20_section_seal_demo_and_no_live_proof() -> None:
    demo = build_shell_binding_contract_scope_demo()
    proof = build_shell_binding_no_live_binding_proof()
    seal = build_shell_binding_section_seal_result()
    result = build_p2_7_d_shell_binding_section_seal_result()

    assert demo.demo_scope == "CONTRACT_SCOPE_ONLY"
    assert demo.is_product_demo is False
    assert demo.is_live_demo is False
    assert demo.requires_runtime is False
    assert_contract_scope_demo_is_not_product_demo(demo)

    assert proof.proof_active is True
    assert proof.live_cli_runner_created is False
    assert proof.live_tui_runtime_created is False
    assert proof.live_shell_runtime_created is False
    assert proof.live_command_execution_created is False
    assert proof.live_runtime_dispatch_created is False
    assert proof.live_trace_write_created is False
    assert proof.live_product_behavior_created is False
    assert_no_live_binding_proof_is_active(proof)

    assert seal.section_status is ShellBindingSectionSealStatus.SEALED_CONTRACT_ONLY
    assert seal.is_release_seal is False
    assert seal.claims_live is False
    assert seal.claims_trace_verified is False
    assert seal.claims_shell_complete is False
    assert seal.claims_p2_complete is False
    assert seal.claims_product_behavior is False
    assert_section_seal_is_not_release_seal(seal)

    assert result.covered_checkpoints == P2_7_D_PACK_CHECKPOINT_IDS
    assert result.full_section_coverage == P2_7_D_FULL_SECTION_CHECKPOINTS
    assert result.next_pack == "P2.8-A"
    assert result.claims_live is False
    assert result.claims_trace_verified is False
    assert result.claims_release_scope is False
    assert result.claims_shell_complete is False
    assert result.claims_p2_complete is False
    assert result.claims_product_behavior is False


def test_side_effect_proof_all_false() -> None:
    proof = build_p2_7_d_side_effect_proof()
    assert isinstance(proof, P27DSideEffectProof)
    assert_p2_7_d_side_effects_all_false(proof)
    for field in fields(P27DSideEffectProof):
        assert getattr(proof, field.name) is False


def test_side_effect_proof_required_fields() -> None:
    proof = build_p2_7_d_side_effect_proof()
    for field_name in (
        "cli_app_created",
        "cli_runner_created",
        "cli_entrypoint_created",
        "tui_runtime_created",
        "tui_app_created",
        "shell_runtime_created",
        "shell_execution_runtime_created",
        "shell_state_runtime_created",
        "command_parser_created",
        "command_router_created",
        "command_handler_created",
        "command_execution_created",
        "command_invocation_created",
        "tool_invocation_created",
        "workflow_dispatch_created",
        "runtime_dispatch_created",
        "runtime_bridge_created",
        "runtime_mutated",
        "shell_state_mutated",
        "surface_switch_created",
        "navigation_mutation_created",
        "output_writer_created",
        "render_runtime_created",
        "operator_confirmation_runtime_created",
        "approval_created",
        "approval_activated",
        "hitl_approval_activated",
        "authorization_created",
        "permission_enforcement_created",
        "permission_granted",
        "permission_denied",
        "custos_decisioning_created",
        "custos_integration_created",
        "mneme_integration_created",
        "api_server_created",
        "http_routes_created",
        "live_endpoint_created",
        "event_bus_created",
        "trace_written",
        "memory_written",
        "storage_written",
        "source_of_truth_created",
        "product_ui_created",
        "product_behavior_claimed",
        "release_scope_claimed",
        "shell_complete_claimed",
        "p2_complete_claimed",
        "live_claimed",
        "trace_verified_claimed",
        "p2_8_started",
        "p2_10_started",
        "p2_13_started",
    ):
        assert getattr(proof, field_name) is False


def test_surface_taxonomy_drift_does_not_activate_old_surfaces() -> None:
    result = build_p2_7_d_shell_binding_section_seal_result()
    for old_surface in OLD_SURFACE_TAXONOMY:
        assert old_surface not in result.official_surface_ids


def test_serialization_and_summary() -> None:
    result = build_p2_7_d_shell_binding_section_seal_result()
    serialized = serialize_p2_7_d_result(result)
    assert isinstance(serialized, str)
    assert "P2.7" in serialized
    assert serialize_p2_7_d_result() == serialized

    summary = render_shell_binding_section_seal_summary(result)
    assert "Shell / CLI / TUI Binding" in summary
    assert "P2.8-A" in summary
    assert "live=false" in summary
    assert "trace_verified=false" in summary
    assert "shell_complete=false" in summary
    assert "p2_complete=false" in summary
    assert "p2_8_started=false" in summary


def test_pack_result_type_and_truth_labels() -> None:
    result = build_p2_7_d_shell_binding_section_seal_result()
    assert isinstance(result, P27DShellBindingSectionSealResult)
    assert result.pack_id == P2_7_D_PACK_ID
    assert P2_7_D_REPORT_PATH.endswith(".md")
    assert len(P2_7_D_VALIDATION_COMMANDS) == 5
    assert ShellBindingSectionSealTruthBoundary.NOT_LIVE.value in result.truth_labels
    assert ShellBindingSectionSealTruthBoundary.NOT_TRACE_VERIFIED.value in result.truth_labels
    assert ShellBindingSectionSealTruthBoundary.NOT_P2_8_IMPLEMENTATION.value in result.truth_labels
