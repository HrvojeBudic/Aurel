"""Tests for P2.9-A Shell Exit Seal foundation contracts."""

from __future__ import annotations

import json
from dataclasses import fields

import pytest

from agentic_runtime.aurel_shell.shell_exit_seal_foundation import (
    P2_8_D_COMMIT_REF,
    P2_8_D_REPORT_PATH,
    P2_9_A_DEPENDENCY_PACK,
    P2_9_A_NEXT_PACK,
    P2_9_A_OFFICIAL_SECTION_NAME,
    P2_9_A_PACK_CHECKPOINT_IDS,
    P2_9_A_PACK_ID,
    P2_9_A_REPORT_PATH,
    P2_9_A_SECTION_ID,
    P2_9_A_TEST_REF,
    P2_9_A_VALIDATION_COMMANDS,
    P29AShellExitSealFoundationResult,
    P29ASideEffectProof,
    ShellExitP29BHandoffStatus,
    ShellExitReadinessDimensionStatus,
    ShellExitSealFoundationGateStatus,
    ShellExitSealFoundationTruthBoundary,
    _EXIT_CRITERIA_CATEGORIES,
    _PRIOR_SECTION_EVIDENCE_SPECS,
    _UNAVAILABLE_CAPABILITY_SPECS,
    assert_criteria_catalog_does_not_execute_validation,
    assert_evidence_intake_is_not_trace_verified,
    assert_foundation_is_not_final_exit_seal,
    assert_omni_evidence_is_ignored_by_operator_instruction,
    assert_p2_9_a_does_not_start_future_work,
    assert_p2_9_a_side_effects_all_false,
    assert_p2_9_b_handoff_is_not_p2_9_b_implementation,
    assert_readiness_dimension_is_not_product_readiness,
    assert_shell_exit_seal_is_not_release_seal,
    build_p2_9_a_shell_exit_seal_foundation_result,
    build_p2_9_a_side_effect_proof,
    build_shell_exit_criteria_catalog,
    build_shell_exit_no_live_runtime_boundary,
    build_shell_exit_no_p2_complete_boundary,
    build_shell_exit_no_product_readiness_boundary,
    build_shell_exit_no_release_seal_boundary,
    build_shell_exit_no_shell_complete_boundary,
    build_shell_exit_p2_9_b_handoff_contract,
    build_shell_exit_readiness_dimension,
    build_shell_exit_seal_foundation_gate,
    build_shell_exit_seal_foundation_result,
    build_shell_exit_unavailable_capability_declaration,
    build_shell_prior_section_evidence_intake,
    build_shell_section_inventory_intake,
    render_shell_exit_seal_foundation_summary,
    serialize_p2_9_a_result,
)
from agentic_runtime.aurel_shell.shell_state_section_seal import (
    build_p2_8_d_shell_state_section_seal_result,
    build_shell_state_no_generation_proof,
    build_shell_state_no_live_state_proof,
    build_shell_state_no_sync_runtime_proof,
    build_shell_state_no_write_proof,
    build_shell_state_p2_9_handoff_contract,
)


def _roundtrip(obj) -> dict:
    return json.loads(json.dumps(obj.to_canonical_dict(), sort_keys=True))


def test_module_imports_p2_9_a() -> None:
    import agentic_runtime.aurel_shell.shell_exit_seal_foundation  # noqa: F401


def test_gate_dependency_and_omni_policy() -> None:
    result = build_p2_9_a_shell_exit_seal_foundation_result()
    gate = result.foundation_gate

    assert P2_9_A_PACK_ID == "P2.9-A"
    assert P2_9_A_SECTION_ID == "P2.9"
    assert P2_9_A_OFFICIAL_SECTION_NAME == "Shell Exit Seal"
    assert P2_9_A_DEPENDENCY_PACK == "P2.8-D"
    assert gate.dependency_pack == "P2.8-D"
    assert gate.dependency_report_ref == P2_8_D_REPORT_PATH
    assert gate.dependency_commit_ref == P2_8_D_COMMIT_REF
    assert gate.dependency_section_seal_result_ref
    assert gate.dependency_p2_9_handoff_ref
    assert gate.dependency_no_live_state_proof_ref
    assert gate.dependency_no_sync_runtime_proof_ref
    assert gate.dependency_no_generation_proof_ref
    assert gate.dependency_no_write_proof_ref
    assert gate.dependency_side_effect_proof_ref == "P28DSideEffectProof:all_false"
    assert gate.repo_evidence_gate_passed is True
    assert gate.omni_evidence_required is False
    assert gate.omni_evidence_ignored_by_operator_instruction is True
    assert gate.gate_status is ShellExitSealFoundationGateStatus.READY
    assert_omni_evidence_is_ignored_by_operator_instruction(gate)


def test_p2_8_d_dependency_proofs_represented() -> None:
    seal = build_p2_8_d_shell_state_section_seal_result()
    gate = build_shell_exit_seal_foundation_gate(seal)

    assert seal.pack_id == "P2.8-D"
    assert gate.dependency_no_live_state_proof_ref.startswith(
        build_shell_state_no_live_state_proof().no_live_state_proof_id
    )
    assert gate.dependency_no_sync_runtime_proof_ref.startswith(
        build_shell_state_no_sync_runtime_proof().no_sync_runtime_proof_id
    )
    assert gate.dependency_no_generation_proof_ref.startswith(
        build_shell_state_no_generation_proof().no_generation_proof_id
    )
    assert gate.dependency_no_write_proof_ref.startswith(
        build_shell_state_no_write_proof().no_write_proof_id
    )
    handoff = build_shell_state_p2_9_handoff_contract()
    assert handoff.is_p2_9_implementation is False
    assert handoff.starts_p2_9 is False


def test_p2_9_a_does_not_start_future_work() -> None:
    result = build_p2_9_a_shell_exit_seal_foundation_result()
    assert result.next_pack == P2_9_A_NEXT_PACK == "P2.9-B"
    assert result.starts_future_work is False
    assert result.side_effect_proof.p2_9_b_started is False
    assert result.side_effect_proof.p2_9_c_started is False
    assert result.side_effect_proof.p2_9_d_started is False
    assert result.side_effect_proof.p2_10_started is False
    assert result.side_effect_proof.p2_11_started is False
    assert result.side_effect_proof.p2_12_started is False
    assert result.side_effect_proof.p2_13_started is False
    assert_p2_9_a_does_not_start_future_work(result)


def test_closed_world_enums_reject_unknown_values() -> None:
    with pytest.raises(ValueError):
        ShellExitSealFoundationGateStatus("LIVE")
    with pytest.raises(ValueError):
        ShellExitReadinessDimensionStatus("PRODUCT_READY")
    with pytest.raises(ValueError):
        ShellExitP29BHandoffStatus("P2_9_B_STARTED")


def test_p2_9_0_foundation_gate() -> None:
    gate = build_shell_exit_seal_foundation_gate()
    assert gate.gate_status in set(ShellExitSealFoundationGateStatus)
    assert gate.created_for_pack == "P2.9-A"
    assert gate.official_section_name == "Shell Exit Seal"
    assert _roundtrip(gate)


def test_p2_9_1_prior_section_evidence_and_inventory() -> None:
    evidence = build_shell_prior_section_evidence_intake()
    inventory = build_shell_section_inventory_intake()

    assert len(evidence.evidence_entries) == len(_PRIOR_SECTION_EVIDENCE_SPECS)
    assert evidence.source_sections == tuple(spec[0] for spec in _PRIOR_SECTION_EVIDENCE_SPECS)
    assert "P2.0" in evidence.source_sections
    assert "P2.8" in evidence.source_sections
    assert evidence.claims_trace_verified is False
    assert evidence.replaces_agent_governance is False
    assert evidence.duplicates_source_of_truth is False
    assert_evidence_intake_is_not_trace_verified(evidence)

    assert len(inventory.inventory_entries) == len(_PRIOR_SECTION_EVIDENCE_SPECS)
    assert inventory.is_governance_source is False
    assert inventory.duplicates_agent_state is False
    assert _roundtrip(evidence)
    assert _roundtrip(inventory)


def test_p2_9_2_exit_criteria_catalog() -> None:
    catalog = build_shell_exit_criteria_catalog()
    assert catalog.criteria_categories == _EXIT_CRITERIA_CATEGORIES
    assert set(catalog.criteria_categories) == {
        "evidence",
        "coverage",
        "validation",
        "boundaries",
        "availability",
        "unavailable_capabilities",
        "handoff_readiness",
        "no_overclaim",
    }
    assert catalog.is_validation_execution is False
    assert catalog.decides_authority is False
    assert all(not c.is_validation_execution for c in catalog.criteria)
    assert_criteria_catalog_does_not_execute_validation(catalog)
    assert _roundtrip(catalog)


def test_p2_9_3_readiness_dimensions() -> None:
    result = build_p2_9_a_shell_exit_seal_foundation_result()
    dimensions = result.readiness_dimensions
    assert dimensions
    for dimension in dimensions:
        assert dimension.dimension_status in set(ShellExitReadinessDimensionStatus)
        assert dimension.claims_product_readiness is False
        assert_readiness_dimension_is_not_product_readiness(dimension)
    standalone = build_shell_exit_readiness_dimension(
        "test_dimension",
        "contract-only scope",
        ("evidence",),
    )
    assert standalone.dimension_status is ShellExitReadinessDimensionStatus.DEFINED_CONTRACT_ONLY
    assert _roundtrip(standalone)


def test_p2_9_4_unavailable_capabilities_and_boundaries() -> None:
    unavailable = build_shell_exit_unavailable_capability_declaration()
    no_release = build_shell_exit_no_release_seal_boundary()
    no_product = build_shell_exit_no_product_readiness_boundary()
    no_live = build_shell_exit_no_live_runtime_boundary()
    no_p2 = build_shell_exit_no_p2_complete_boundary()
    no_shell = build_shell_exit_no_shell_complete_boundary()

    assert len(unavailable.unavailable_entries) == len(_UNAVAILABLE_CAPABILITY_SPECS)
    assert unavailable.implements_runtime is False

    assert no_release.release_seal_created is False
    assert no_release.release_readiness_claimed is False
    assert no_release.release_scope_claimed is False
    assert_shell_exit_seal_is_not_release_seal(no_release)

    assert no_product.product_readiness_claimed is False
    assert no_product.product_behavior_claimed is False
    assert no_product.operator_testable_product_behavior_claimed is False
    assert no_product.frontend_ui_created is False

    assert no_live.live_shell_runtime_created is False
    assert no_live.multi_client_runtime_created is False
    assert no_live.runtime_dispatch_created is False
    assert no_live.command_execution_created is False

    assert no_p2.p2_complete_claimed is False
    assert no_shell.shell_complete_claimed is False

    for boundary in (no_release, no_product, no_live, no_p2, no_shell):
        assert boundary.boundary_active is True
        assert _roundtrip(boundary)
    assert _roundtrip(unavailable)


def test_p2_9_5_foundation_result_handoff_and_pack_result() -> None:
    handoff = build_shell_exit_p2_9_b_handoff_contract()
    foundation = build_shell_exit_seal_foundation_result()
    result = build_p2_9_a_shell_exit_seal_foundation_result()

    assert handoff.handoff_to_pack == "P2.9-B"
    assert handoff.is_p2_9_b_implementation is False
    assert handoff.starts_p2_9_b is False
    assert handoff.handoff_status is ShellExitP29BHandoffStatus.READY_FOR_P2_9_B_CONTRACT_HANDOFF
    assert_p2_9_b_handoff_is_not_p2_9_b_implementation(handoff)

    assert foundation.is_completed_exit_seal is False
    assert foundation.is_release_seal is False
    assert foundation.claims_product_readiness is False
    assert foundation.claims_p2_complete is False
    assert foundation.claims_shell_complete is False
    assert foundation.claims_live is False
    assert foundation.claims_trace_verified is False
    assert foundation.claims_product_behavior is False
    assert_foundation_is_not_final_exit_seal(foundation)

    assert result.pack_id == "P2.9-A"
    assert result.covered_checkpoints == P2_9_A_PACK_CHECKPOINT_IDS
    assert result.next_pack == "P2.9-B"
    assert result.claims_live is False
    assert result.claims_trace_verified is False
    assert result.claims_release_scope is False
    assert result.claims_product_behavior is False
    assert (
        ShellExitSealFoundationTruthBoundary.EXIT_SEAL_FOUNDATION_ONLY.value
        in result.truth_labels
    )


def test_side_effect_proof_all_false() -> None:
    proof = build_p2_9_a_side_effect_proof()
    assert_p2_9_a_side_effects_all_false(proof)
    for field in fields(P29ASideEffectProof):
        assert getattr(proof, field.name) is False


def test_surface_taxonomy_drift_reported() -> None:
    result = build_p2_9_a_shell_exit_seal_foundation_result()
    assert result.surface_taxonomy_drift is True
    assert result.surface_taxonomy_drift_details


def test_serialization_and_summary() -> None:
    result = build_p2_9_a_shell_exit_seal_foundation_result()
    serialized = serialize_p2_9_a_result(result)
    assert isinstance(serialized, str)
    assert "P2.9-A" in serialized
    summary = render_shell_exit_seal_foundation_summary(result)
    assert "Shell Exit Seal" in summary
    assert "completed_exit_seal=false" in summary
    assert "next=P2.9-B" in summary
    assert _roundtrip(result)


def test_validation_commands_and_report_paths() -> None:
    assert P2_9_A_TEST_REF.endswith("test_shell_exit_seal_foundation.py")
    assert P2_9_A_REPORT_PATH.endswith("P2_9_A_SHELL_EXIT_SEAL_FOUNDATION.md")
    assert len(P2_9_A_VALIDATION_COMMANDS) == 5


def test_pack_result_type() -> None:
    result = build_p2_9_a_shell_exit_seal_foundation_result()
    assert isinstance(result, P29AShellExitSealFoundationResult)
    assert result.result_hash
