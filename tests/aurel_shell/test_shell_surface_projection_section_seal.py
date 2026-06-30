"""Tests for P2.6-D surface projection section seal contracts."""

from __future__ import annotations

import json
from dataclasses import fields

import pytest

from agentic_runtime.aurel_shell.surface_projection_events import P2_6_C_REPORT_PATH
from agentic_runtime.aurel_shell.surface_projection_foundation import P2_6_A_REPORT_PATH
from agentic_runtime.aurel_shell.surface_projection_schemas import P2_6_B_REPORT_PATH
from agentic_runtime.aurel_shell.surface_projection_section_seal import (
    P2_6_A_COMMIT_REF,
    P2_6_B_COMMIT_REF,
    P2_6_C_COMMIT_REF,
    P2_6_D_DEPENDENCY_PACK,
    P2_6_D_FULL_SECTION_CHECKPOINTS,
    P2_6_D_NEXT_PACK,
    P2_6_D_OFFICIAL_SECTION_NAME,
    P2_6_D_PACK_CHECKPOINT_IDS,
    P2_6_D_PACK_ID,
    P2_6_D_REPORT_PATH,
    P2_6_D_SECTION_ID,
    P2_6_D_VALIDATION_COMMANDS,
    P26DSideEffectProof,
    P26DSurfaceProjectionSectionSealResult,
    SurfaceProjectionBindingAvailabilityStatus,
    SurfaceProjectionSectionContractEntryStatus,
    SurfaceProjectionSectionReadModelStatus,
    SurfaceProjectionSectionSealGateStatus,
    SurfaceProjectionSectionSealStatus,
    SurfaceProjectionSectionSealTruthBoundary,
    assert_binding_availability_is_not_binding,
    assert_contract_inventory_is_not_source_of_truth_duplication,
    assert_contract_scope_demo_is_not_product_demo,
    assert_evidence_rollup_is_not_trace_verified,
    assert_no_live_infrastructure_proof_is_active,
    assert_no_p2_7_started_boundary_is_active,
    assert_omni_evidence_is_ignored_by_operator_instruction,
    assert_p2_6_d_does_not_start_future_work,
    assert_p2_6_d_side_effects_all_false,
    assert_section_gate_depends_on_p2_6_c,
    assert_section_read_model_is_not_live_endpoint,
    assert_section_seal_is_not_release_seal,
    assert_validation_rollup_does_not_invent_pass,
    build_p2_6_d_side_effect_proof,
    build_p2_6_d_surface_projection_section_seal_result,
    build_surface_projection_binding_availability,
    build_surface_projection_bridge_availability_rollup,
    build_surface_projection_contract_scope_demo,
    build_surface_projection_no_live_infrastructure_proof,
    build_surface_projection_section_contract_inventory,
    build_surface_projection_section_read_model,
    build_surface_projection_section_read_model_version,
    build_surface_projection_section_seal_gate,
    build_surface_projection_section_seal_result,
    build_surface_projection_section_validation_rollup,
    render_surface_projection_section_seal_summary,
    serialize_p2_6_d_result,
)
from agentic_runtime.aurel_shell.surface_registry import OLD_SURFACE_TAXONOMY


def test_module_imports_p2_6_d() -> None:
    import agentic_runtime.aurel_shell.surface_projection_section_seal  # noqa: F401


def test_gate_dependency_and_omni_policy() -> None:
    result = build_p2_6_d_surface_projection_section_seal_result()
    gate = result.section_seal_gate

    assert P2_6_D_PACK_ID == "P2.6-D"
    assert P2_6_D_SECTION_ID == "P2.6"
    assert P2_6_D_OFFICIAL_SECTION_NAME == "Surface Projection / API / Event Bridge"
    assert P2_6_D_DEPENDENCY_PACK == "P2.6-C"
    assert gate.dependency_pack == "P2.6-C"
    assert gate.dependency_report_ref == P2_6_C_REPORT_PATH
    assert gate.dependency_commit_ref == P2_6_C_COMMIT_REF
    assert gate.p2_6_a_report_ref == P2_6_A_REPORT_PATH
    assert gate.p2_6_b_report_ref == P2_6_B_REPORT_PATH
    assert gate.p2_6_c_report_ref == P2_6_C_REPORT_PATH
    assert gate.dependency_event_bridge_boundary_result_ref
    assert gate.dependency_no_runtime_dispatch_boundary_ref
    assert gate.dependency_side_effect_proof_ref == "P26CSideEffectProof:all_false"
    assert gate.repo_evidence_gate_passed is True
    assert gate.omni_evidence_required is False
    assert gate.omni_evidence_ignored_by_operator_instruction is True
    assert_section_gate_depends_on_p2_6_c(gate)
    assert_omni_evidence_is_ignored_by_operator_instruction(gate)


def test_p2_6_section_title_not_attention_inbox() -> None:
    result = build_p2_6_d_surface_projection_section_seal_result()
    blob = serialize_p2_6_d_result(result).lower()
    assert "attention" not in blob
    assert "notification" not in blob
    assert "inbox" not in blob


def test_p2_6_d_does_not_start_future_work() -> None:
    result = build_p2_6_d_surface_projection_section_seal_result()
    assert result.next_pack == P2_6_D_NEXT_PACK == "P2.7-A"
    assert result.starts_future_work is False
    assert result.side_effect_proof.p2_7_started is False
    assert result.side_effect_proof.p2_10_started is False
    assert result.side_effect_proof.p2_13_started is False
    assert_p2_6_d_does_not_start_future_work(result)


def test_closed_world_enums_reject_unknown_values() -> None:
    with pytest.raises(ValueError):
        SurfaceProjectionSectionSealGateStatus("OMNI_BLOCKED")
    with pytest.raises(ValueError):
        SurfaceProjectionSectionContractEntryStatus("LIVE")
    with pytest.raises(ValueError):
        SurfaceProjectionBindingAvailabilityStatus("BOUND")
    with pytest.raises(ValueError):
        SurfaceProjectionSectionSealStatus("RELEASE_SEALED")


def test_p2_6_16_section_seal_gate_and_inventory() -> None:
    gate = build_surface_projection_section_seal_gate()
    inventory = build_surface_projection_section_contract_inventory()

    assert gate.gate_status in set(SurfaceProjectionSectionSealGateStatus)
    assert gate.created_for_pack == "P2.6-D"
    assert inventory.created_for_pack == "P2.6-D"
    assert inventory.covered_checkpoints == P2_6_D_FULL_SECTION_CHECKPOINTS
    assert len(inventory.contract_entries) == 21
    assert inventory.duplicates_source_of_truth is False
    assert inventory.is_source_of_truth is False
    assert inventory.source_pack_refs == ("P2.6-A", "P2.6-B", "P2.6-C", "P2.6-D")
    assert all(
        entry.status == SurfaceProjectionSectionContractEntryStatus.DONE
        for entry in inventory.contract_entries
    )
    assert_contract_inventory_is_not_source_of_truth_duplication(inventory)
    assert json.loads(json.dumps(inventory.to_canonical_dict(), sort_keys=True))


def test_p2_6_17_section_read_model() -> None:
    read_model = build_surface_projection_section_read_model()
    version = build_surface_projection_section_read_model_version()

    assert read_model.is_live_endpoint is False
    assert read_model.is_api_server is False
    assert read_model.is_event_bus is False
    assert read_model.section_status in {
        SurfaceProjectionSectionReadModelStatus.CONTRACT_ONLY,
        SurfaceProjectionSectionReadModelStatus.SEALED_CONTRACT_ONLY,
    }
    assert version.compatible_section == "P2.6"
    assert version.compatible_pack == "P2.6-D"
    assert version.breaking_change is False
    assert_section_read_model_is_not_live_endpoint(read_model)
    assert json.loads(json.dumps(read_model.to_canonical_dict(), sort_keys=True))


def test_p2_6_18_binding_availability_and_rollup() -> None:
    binding = build_surface_projection_binding_availability()
    rollup = build_surface_projection_bridge_availability_rollup()

    assert (
        binding.availability_status
        is SurfaceProjectionBindingAvailabilityStatus.UNAVAILABLE_P2_7_REQUIRED
    )
    assert binding.next_required_pack == "P2.7-A"
    assert binding.next_required_section == "P2.7"
    assert binding.creates_cli_binding is False
    assert binding.creates_shell_execution_binding is False
    assert binding.creates_tui_binding is False
    assert binding.starts_p2_7 is False
    assert rollup.grants_permission is False
    assert rollup.denies_permission is False
    assert rollup.activates_approval is False
    assert rollup.enforces_policy is False
    assert "live API server" in rollup.unavailable_capabilities
    assert "CLI/Shell/TUI binding" in rollup.unavailable_capabilities
    assert_binding_availability_is_not_binding(binding)
    assert_no_p2_7_started_boundary_is_active(binding)


def test_p2_6_19_validation_rollup_and_report_refs() -> None:
    rollup = build_surface_projection_section_validation_rollup()
    result = build_p2_6_d_surface_projection_section_seal_result()

    assert rollup.p2_6_a_validation_ref
    assert rollup.p2_6_b_validation_ref
    assert rollup.p2_6_c_validation_ref
    assert rollup.p2_6_d_validation_commands == P2_6_D_VALIDATION_COMMANDS
    assert rollup.invented_pass is False
    assert rollup.ruff_result == "NOT_RUN_AT_BUILD"
    assert result.validation_rollup.invented_pass is False
    assert_validation_rollup_does_not_invent_pass(rollup)
    assert_evidence_rollup_is_not_trace_verified(result)
    assert result.side_effect_proof.trace_written is False
    serialized = serialize_p2_6_d_result(result)
    assert P2_6_D_REPORT_PATH.replace("/", "") in serialized.replace("/", "")
    assert "agent/reports" in serialized


def test_p2_6_20_section_seal_demo_and_no_live_proof() -> None:
    demo = build_surface_projection_contract_scope_demo()
    seal = build_surface_projection_section_seal_result()
    proof = build_surface_projection_no_live_infrastructure_proof()

    assert demo.is_product_demo is False
    assert demo.requires_live_api is False
    assert demo.requires_event_bridge is False
    assert demo.requires_cli_binding is False
    assert demo.demo_scope == "CONTRACT_SCOPE_ONLY"
    assert_contract_scope_demo_is_not_product_demo(demo)

    assert seal.seal_status is SurfaceProjectionSectionSealStatus.SEALED_CONTRACT_ONLY
    assert seal.creates_api_server is False
    assert seal.creates_event_bus is False
    assert seal.creates_runtime_bridge is False
    assert seal.creates_cli_binding is False
    assert seal.claims_release_scope is False
    assert seal.claims_shell_complete is False
    assert seal.claims_p2_complete is False
    assert seal.next_pack == "P2.7-A"
    assert_section_seal_is_not_release_seal(seal)
    assert_no_live_infrastructure_proof_is_active(proof)


def test_side_effect_proof_all_false() -> None:
    proof = build_p2_6_d_side_effect_proof()
    assert isinstance(proof, P26DSideEffectProof)
    for field in fields(proof):
        assert getattr(proof, field.name) is False
    assert_p2_6_d_side_effects_all_false(proof)


def test_pack_result_integrity() -> None:
    result = build_p2_6_d_surface_projection_section_seal_result()
    assert isinstance(result, P26DSurfaceProjectionSectionSealResult)
    assert result.pack_id == "P2.6-D"
    assert result.covered_checkpoints == P2_6_D_PACK_CHECKPOINT_IDS
    assert result.full_section_coverage == P2_6_D_FULL_SECTION_CHECKPOINTS
    assert result.p2_6_a_evidence_ref.startswith(P2_6_A_REPORT_PATH)
    assert result.p2_6_b_evidence_ref.startswith(P2_6_B_REPORT_PATH)
    assert result.p2_6_c_evidence_ref.startswith(P2_6_C_REPORT_PATH)
    assert result.claims_live is False
    assert result.claims_trace_verified is False
    assert result.claims_release_scope is False
    assert result.claims_product_behavior is False
    assert result.claims_shell_complete is False
    assert result.claims_p2_complete is False
    assert result.surface_taxonomy_drift is True
    assert OLD_SURFACE_TAXONOMY
    assert SurfaceProjectionSectionSealTruthBoundary.NOT_LIVE.value in result.truth_labels


def test_a_b_c_commit_refs_represented_in_inventory() -> None:
    inventory = build_surface_projection_section_contract_inventory()
    commits = {entry.source_commit_ref for entry in inventory.contract_entries}
    assert P2_6_A_COMMIT_REF in commits
    assert P2_6_B_COMMIT_REF in commits
    assert P2_6_C_COMMIT_REF in commits


def test_deterministic_serialization() -> None:
    first = serialize_p2_6_d_result(build_p2_6_d_surface_projection_section_seal_result())
    second = serialize_p2_6_d_result(build_p2_6_d_surface_projection_section_seal_result())
    assert first == second
    assert json.loads(first)


def test_render_summary() -> None:
    summary = render_surface_projection_section_seal_summary()
    assert "P2.6" in summary
    assert "SEALED_CONTRACT_ONLY" in summary
    assert "UNAVAILABLE_P2_7_REQUIRED" in summary
    assert "P2.7-A" in summary
