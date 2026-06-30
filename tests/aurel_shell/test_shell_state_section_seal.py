"""Tests for P2.8-D Shell State / Reports / Docs section seal contracts."""

from __future__ import annotations

import json
from dataclasses import fields

import pytest

from agentic_runtime.aurel_shell.shell_state_foundation import P2_8_A_REPORT_PATH
from agentic_runtime.aurel_shell.shell_state_read_models import P2_8_B_REPORT_PATH
from agentic_runtime.aurel_shell.shell_state_section_seal import (
    P2_8_A_COMMIT_REF,
    P2_8_B_COMMIT_REF,
    P2_8_C_COMMIT_REF,
    P2_8_C_REPORT_PATH,
    P2_8_D_DEPENDENCY_PACK,
    P2_8_D_FULL_SECTION_CHECKPOINTS,
    P2_8_D_NEXT_PACK,
    P2_8_D_OFFICIAL_SECTION_NAME,
    P2_8_D_PACK_CHECKPOINT_IDS,
    P2_8_D_PACK_ID,
    P2_8_D_REPORT_PATH,
    P2_8_D_SECTION_ID,
    P2_8_D_TEST_REF,
    P2_8_D_VALIDATION_COMMANDS,
    P28DShellStateSectionSealResult,
    P28DSideEffectProof,
    ShellStateP29HandoffStatus,
    ShellStateSectionCoverageEntryStatus,
    ShellStateSectionSealGateStatus,
    ShellStateSectionSealTruthBoundary,
    ShellStateSectionStatus,
    assert_availability_rollup_is_not_permission_enforcement,
    assert_contract_inventory_is_not_source_of_truth_duplication,
    assert_contract_scope_demo_is_not_product_demo,
    assert_coverage_matrix_does_not_invent_done,
    assert_evidence_rollup_is_not_trace_verified,
    assert_no_generation_proof_is_active,
    assert_no_live_state_proof_is_active,
    assert_no_sync_runtime_proof_is_active,
    assert_no_write_proof_is_active,
    assert_omni_evidence_is_ignored_by_operator_instruction,
    assert_p2_8_complete_is_not_p2_complete,
    assert_p2_8_d_does_not_start_future_work,
    assert_p2_8_d_side_effects_all_false,
    assert_p2_9_handoff_is_not_p2_9_implementation,
    assert_section_gate_depends_on_p2_8_c,
    assert_section_seal_is_not_release_seal,
    assert_shell_state_section_complete_is_not_live_shell_state,
    assert_validation_rollup_does_not_invent_pass,
    build_p2_8_d_shell_state_section_seal_result,
    build_p2_8_d_side_effect_proof,
    build_shell_state_no_generation_proof,
    build_shell_state_no_live_state_proof,
    build_shell_state_no_sync_runtime_proof,
    build_shell_state_no_write_proof,
    build_shell_state_p2_9_handoff_contract,
    build_shell_state_reports_docs_availability_rollup,
    build_shell_state_runtime_unavailable_rollup,
    build_shell_state_section_contract_inventory,
    build_shell_state_section_contract_scope_demo,
    build_shell_state_section_coverage_matrix,
    build_shell_state_section_evidence_rollup,
    build_shell_state_section_read_model,
    build_shell_state_section_seal_gate,
    build_shell_state_section_seal_result,
    build_shell_state_section_validation_rollup,
    render_shell_state_section_seal_summary,
    serialize_p2_8_d_result,
)
from agentic_runtime.aurel_shell.shell_state_summary import (
    P2_8_C_PACK_ID,
    build_p2_8_c_shell_state_summary_result,
)
from agentic_runtime.aurel_shell.surface_registry import OLD_SURFACE_TAXONOMY


def _roundtrip(obj) -> dict:
    return json.loads(json.dumps(obj.to_canonical_dict(), sort_keys=True))


def test_module_imports_p2_8_d() -> None:
    import agentic_runtime.aurel_shell.shell_state_section_seal  # noqa: F401


def test_gate_dependency_and_omni_policy() -> None:
    result = build_p2_8_d_shell_state_section_seal_result()
    gate = result.section_seal_gate

    assert P2_8_D_PACK_ID == "P2.8-D"
    assert P2_8_D_SECTION_ID == "P2.8"
    assert P2_8_D_OFFICIAL_SECTION_NAME == "Shell State / Reports / Docs"
    assert P2_8_D_DEPENDENCY_PACK == "P2.8-C"
    assert gate.dependency_pack == P2_8_C_PACK_ID
    assert gate.dependency_report_ref == P2_8_C_REPORT_PATH
    assert gate.dependency_summary_boundary_result_ref
    assert gate.dependency_no_sync_runtime_boundary_ref
    assert gate.dependency_no_generation_boundary_ref
    assert gate.dependency_no_write_boundary_ref
    assert gate.dependency_side_effect_proof_ref == "P28CSideEffectProof:all_false"
    assert gate.p2_8_a_evidence_ref == P2_8_A_REPORT_PATH
    assert gate.p2_8_b_evidence_ref == P2_8_B_REPORT_PATH
    assert gate.p2_8_c_evidence_ref == P2_8_C_REPORT_PATH
    assert gate.repo_evidence_gate_passed is True
    assert gate.omni_evidence_required is False
    assert gate.omni_evidence_ignored_by_operator_instruction is True
    assert gate.gate_status is ShellStateSectionSealGateStatus.READY
    assert_section_gate_depends_on_p2_8_c(gate)
    assert_omni_evidence_is_ignored_by_operator_instruction(gate)


def test_p2_8_c_summary_boundary_and_side_effect_represented() -> None:
    summary = build_p2_8_c_shell_state_summary_result()
    result = build_p2_8_d_shell_state_section_seal_result()

    assert summary.pack_id == "P2.8-C"
    assert result.p2_8_c_evidence_ref.startswith(P2_8_C_REPORT_PATH)
    assert (
        summary.boundary_result.boundary_result_id
        in result.section_seal_gate.dependency_summary_boundary_result_ref
    )
    assert result.section_seal_gate.dependency_no_sync_runtime_boundary_ref
    assert result.section_seal_gate.dependency_no_generation_boundary_ref
    assert result.section_seal_gate.dependency_no_write_boundary_ref


def test_p2_8_d_does_not_start_future_work() -> None:
    result = build_p2_8_d_shell_state_section_seal_result()
    assert result.next_pack == P2_8_D_NEXT_PACK == "P2.9-A"
    assert result.starts_future_work is False
    assert result.side_effect_proof.p2_9_started is False
    assert result.side_effect_proof.p2_10_started is False
    assert result.side_effect_proof.p2_11_started is False
    assert result.side_effect_proof.p2_12_started is False
    assert result.side_effect_proof.p2_13_started is False
    assert_p2_8_d_does_not_start_future_work(result)


def test_closed_world_enums_reject_unknown_values() -> None:
    with pytest.raises(ValueError):
        ShellStateSectionSealGateStatus("LIVE")
    with pytest.raises(ValueError):
        ShellStateSectionCoverageEntryStatus("TRACE_VERIFIED")
    with pytest.raises(ValueError):
        ShellStateSectionStatus("RELEASE_SEALED")
    with pytest.raises(ValueError):
        ShellStateP29HandoffStatus("P2_9_STARTED")


def test_p2_8_16_section_seal_gate_inventory_and_coverage() -> None:
    gate = build_shell_state_section_seal_gate()
    inventory = build_shell_state_section_contract_inventory()
    matrix = build_shell_state_section_coverage_matrix()

    assert gate.gate_status in set(ShellStateSectionSealGateStatus)
    assert gate.created_for_pack == "P2.8-D"
    assert inventory.created_for_pack == "P2.8-D"
    assert len(inventory.contract_entries) == 21
    assert inventory.is_source_of_truth is False
    assert inventory.duplicates_agent_governance is False
    assert inventory.source_packs == ("P2.8-A", "P2.8-B", "P2.8-C", "P2.8-D")
    assert inventory.source_report_refs == (
        P2_8_A_REPORT_PATH,
        P2_8_B_REPORT_PATH,
        P2_8_C_REPORT_PATH,
        P2_8_D_REPORT_PATH,
    )
    assert inventory.source_evidence_refs
    assert all(entry.contract_ref for entry in inventory.contract_entries)
    assert_contract_inventory_is_not_source_of_truth_duplication(inventory)

    assert matrix.full_section_range == "P2.8.0-P2.8.20"
    assert matrix.covered_checkpoint_range == "P2.8.16-P2.8.20"
    assert len(matrix.coverage_entries) == 21
    assert matrix.does_invent_done is False
    assert all(
        entry.status is ShellStateSectionCoverageEntryStatus.DONE
        for entry in matrix.coverage_entries
    )
    assert_coverage_matrix_does_not_invent_done(matrix)
    assert _roundtrip(gate)
    assert _roundtrip(inventory)
    assert _roundtrip(matrix)


def test_p2_8_17_section_read_model_status_contract() -> None:
    read_model = build_shell_state_section_read_model()

    assert read_model.section_status is ShellStateSectionStatus.SEALED_CONTRACT_ONLY
    assert read_model.is_release_seal is False
    assert read_model.claims_p2_complete is False
    assert read_model.claims_shell_complete is False
    assert read_model.claims_live_shell_state is False
    assert read_model.coverage_matrix_ref
    assert read_model.contract_inventory_ref
    assert_shell_state_section_complete_is_not_live_shell_state(read_model)
    assert_p2_8_complete_is_not_p2_complete(read_model)
    assert _roundtrip(read_model)


def test_p2_8_18_availability_runtime_unavailable_and_handoff() -> None:
    availability = build_shell_state_reports_docs_availability_rollup()
    unavailable = build_shell_state_runtime_unavailable_rollup()
    handoff = build_shell_state_p2_9_handoff_contract()

    assert availability.available_contracts
    assert availability.available_read_models
    assert availability.available_summary_boundaries
    assert availability.available_reports_docs_refs
    assert availability.enforces_permission is False
    assert availability.grants_permission is False
    assert availability.denies_permission is False
    assert_availability_rollup_is_not_permission_enforcement(availability)

    assert unavailable.live_shell_state_runtime_unavailable is True
    assert unavailable.shell_state_sync_runtime_unavailable is True
    assert unavailable.state_reconciliation_unavailable is True
    assert unavailable.generator_runtime_unavailable is True
    assert unavailable.trace_write_unavailable is True
    assert unavailable.memory_write_unavailable is True
    assert unavailable.storage_write_unavailable is True
    assert unavailable.docs_report_write_unavailable is True
    assert unavailable.product_ui_unavailable is True
    assert unavailable.p2_9_implementation_unavailable is True

    assert handoff.handoff_to_pack == "P2.9-A"
    assert handoff.handoff_to_section == "P2.9 — Shell Exit Seal"
    assert handoff.is_p2_9_implementation is False
    assert handoff.starts_p2_9 is False
    assert_p2_9_handoff_is_not_p2_9_implementation(handoff)


def test_p2_8_19_validation_and_evidence_rollups() -> None:
    validation = build_shell_state_section_validation_rollup()
    evidence = build_shell_state_section_evidence_rollup()
    result = build_p2_8_d_shell_state_section_seal_result()

    assert validation.source_validation_refs
    assert validation.current_validation_refs
    assert validation.validation_commands == P2_8_D_VALIDATION_COMMANDS
    assert validation.invented_pass is False
    assert_validation_rollup_does_not_invent_pass(validation)

    assert evidence.source_packs == ("P2.8-A", "P2.8-B", "P2.8-C", "P2.8-D")
    assert P2_8_A_COMMIT_REF in evidence.source_commits
    assert P2_8_B_COMMIT_REF in evidence.source_commits
    assert P2_8_C_COMMIT_REF in evidence.source_commits
    assert evidence.claims_trace_verified is False
    assert evidence.replaces_agent_governance is False
    assert_evidence_rollup_is_not_trace_verified(evidence)

    assert result.side_effect_proof.runtime_state_mutated is False
    assert result.side_effect_proof.trace_written is False
    assert result.side_effect_proof.memory_written is False
    assert result.side_effect_proof.storage_written is False
    assert result.side_effect_proof.docs_written is False
    assert result.side_effect_proof.reports_written is False


def test_p2_8_20_section_seal_demo_and_proofs() -> None:
    demo = build_shell_state_section_contract_scope_demo()
    no_live = build_shell_state_no_live_state_proof()
    no_sync = build_shell_state_no_sync_runtime_proof()
    no_gen = build_shell_state_no_generation_proof()
    no_write = build_shell_state_no_write_proof()
    seal = build_shell_state_section_seal_result()
    result = build_p2_8_d_shell_state_section_seal_result()

    assert demo.demo_scope == "CONTRACT_ONLY"
    assert demo.uses_live_runtime is False
    assert demo.is_product_demo is False
    assert demo.claims_product_behavior is False
    assert_contract_scope_demo_is_not_product_demo(demo)

    assert_no_live_state_proof_is_active(no_live)
    assert_no_sync_runtime_proof_is_active(no_sync)
    assert_no_generation_proof_is_active(no_gen)
    assert_no_write_proof_is_active(no_write)

    assert seal.section_status is ShellStateSectionStatus.SEALED_CONTRACT_ONLY
    assert seal.is_release_seal is False
    assert seal.claims_live is False
    assert seal.claims_trace_verified is False
    assert seal.claims_shell_complete is False
    assert seal.claims_p2_complete is False
    assert seal.claims_product_behavior is False
    assert seal.claims_release_scope is False
    assert_section_seal_is_not_release_seal(seal)

    assert result.covered_checkpoints == P2_8_D_PACK_CHECKPOINT_IDS
    assert result.full_section_coverage == P2_8_D_FULL_SECTION_CHECKPOINTS
    assert result.next_pack == "P2.9-A"


def test_side_effect_proof_all_false() -> None:
    proof = build_p2_8_d_side_effect_proof()
    assert isinstance(proof, P28DSideEffectProof)
    assert_p2_8_d_side_effects_all_false(proof)
    for field in fields(P28DSideEffectProof):
        assert getattr(proof, field.name) is False


def test_side_effect_proof_required_fields() -> None:
    proof = build_p2_8_d_side_effect_proof()
    for field_name in (
        "shell_runtime_created",
        "shell_state_runtime_created",
        "shell_state_sync_runtime_created",
        "state_reconciliation_engine_created",
        "shell_state_mutated",
        "runtime_state_mutated",
        "sync_executed",
        "repair_action_created",
        "autofix_created",
        "refresh_runtime_created",
        "persistent_state_store_created",
        "database_persistence_created",
        "storage_written",
        "trace_written",
        "memory_written",
        "docs_written",
        "reports_written",
        "report_generator_created",
        "docs_generator_created",
        "summary_generator_created",
        "report_publisher_created",
        "docs_publisher_created",
        "agent_reports_replaced",
        "agent_governance_replaced",
        "docs_source_of_truth_created",
        "product_ui_created",
        "product_behavior_claimed",
        "cli_runner_created",
        "tui_runtime_created",
        "command_execution_created",
        "runtime_dispatch_created",
        "permission_enforcement_created",
        "custos_decisioning_created",
        "approval_runtime_created",
        "live_claimed",
        "trace_verified_claimed",
        "release_scope_claimed",
        "p2_complete_claimed",
        "shell_complete_claimed",
        "p2_9_started",
        "p2_10_started",
        "p2_11_started",
        "p2_12_started",
        "p2_13_started",
    ):
        assert getattr(proof, field_name) is False


def test_surface_taxonomy_drift_does_not_activate_old_surfaces() -> None:
    result = build_p2_8_d_shell_state_section_seal_result()
    assert result.surface_taxonomy_drift is True
    for old_surface in OLD_SURFACE_TAXONOMY:
        assert old_surface not in result.truth_labels


def test_serialization_and_summary() -> None:
    result = build_p2_8_d_shell_state_section_seal_result()
    serialized = serialize_p2_8_d_result(result)
    assert isinstance(serialized, str)
    assert "P2.8" in serialized
    assert serialize_p2_8_d_result() == serialized

    summary = render_shell_state_section_seal_summary(result)
    assert "Shell State / Reports / Docs" in summary
    assert "P2.9-A" in summary
    assert "live=false" in summary
    assert "trace_verified=false" in summary
    assert "shell_complete=false" in summary
    assert "p2_complete=false" in summary
    assert "p2_9_started=false" in summary


def test_pack_result_type_and_truth_labels() -> None:
    result = build_p2_8_d_shell_state_section_seal_result()
    assert isinstance(result, P28DShellStateSectionSealResult)
    assert result.pack_id == P2_8_D_PACK_ID
    assert P2_8_D_REPORT_PATH.endswith(".md")
    assert len(P2_8_D_VALIDATION_COMMANDS) == 5
    assert P2_8_D_TEST_REF.endswith("test_shell_state_section_seal.py")
    assert ShellStateSectionSealTruthBoundary.NOT_LIVE.value in result.truth_labels
    assert (
        ShellStateSectionSealTruthBoundary.NOT_TRACE_VERIFIED.value in result.truth_labels
    )
    assert (
        ShellStateSectionSealTruthBoundary.NOT_P2_9_IMPLEMENTATION.value
        in result.truth_labels
    )
