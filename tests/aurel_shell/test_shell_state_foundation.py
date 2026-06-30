"""Tests for P2.8-A Shell State / Reports / Docs foundation contracts."""

from __future__ import annotations

import json
from dataclasses import fields

import pytest

from agentic_runtime.aurel_shell.shell_state_foundation import (
    P2_7_D_REPORT_PATH,
    P2_8_A_DEPENDENCY_PACK,
    P2_8_A_NEXT_PACK,
    P2_8_A_OFFICIAL_SECTION_NAME,
    P2_8_A_PACK_CHECKPOINT_IDS,
    P2_8_A_PACK_ID,
    P2_8_A_REPORT_PATH,
    P2_8_A_SECTION_ID,
    P2_8_A_VALIDATION_COMMANDS,
    P28ASideEffectProof,
    P28AShellStateFoundationResult,
    ShellReportDocsAvailabilityStatus,
    ShellStateFoundationGateStatus,
    ShellStateSnapshotScope,
    assert_docs_registry_is_not_docs_source_of_truth,
    assert_no_runtime_state_mutation,
    assert_no_trace_memory_storage_writes,
    assert_omni_evidence_is_ignored_by_operator_instruction,
    assert_p2_8_a_does_not_start_future_work,
    assert_p2_8_a_side_effects_all_false,
    assert_report_docs_availability_is_not_permission_enforcement,
    assert_report_registry_is_not_agent_reports_replacement,
    assert_shell_state_snapshot_is_not_live_state,
    assert_source_reference_is_not_storage_persistence,
    build_p2_8_a_shell_state_foundation_result,
    build_p2_8_a_side_effect_proof,
    build_shell_docs_reference_registry,
    build_shell_report_docs_availability_contract,
    build_shell_report_reference_registry,
    build_shell_state_foundation_gate,
    build_shell_state_foundation_identity,
    build_shell_state_foundation_result,
    build_shell_state_governance_source_boundary,
    build_shell_state_no_runtime_mutation_boundary,
    build_shell_state_no_trace_memory_storage_write_boundary,
    build_shell_state_snapshot_contract,
    build_shell_state_source_reference,
    render_shell_state_foundation_summary,
    serialize_p2_8_a_result,
)
from agentic_runtime.aurel_shell.surface_projection_foundation import (
    OFFICIAL_ACTIVE_SURFACE_NAMES,
)
from agentic_runtime.aurel_shell.surface_registry import OLD_SURFACE_TAXONOMY


def test_module_imports_p2_8_a() -> None:
    import agentic_runtime.aurel_shell.shell_state_foundation  # noqa: F401


def test_gate_dependency_and_omni_policy() -> None:
    result = build_p2_8_a_shell_state_foundation_result()
    gate = result.foundation_gate

    assert P2_8_A_PACK_ID == "P2.8-A"
    assert P2_8_A_SECTION_ID == "P2.8"
    assert P2_8_A_OFFICIAL_SECTION_NAME == "Shell State / Reports / Docs"
    assert P2_8_A_DEPENDENCY_PACK == "P2.7-D"
    assert gate.dependency_pack == "P2.7-D"
    assert gate.dependency_report_ref == P2_7_D_REPORT_PATH
    assert gate.dependency_section_seal_result_ref
    assert gate.dependency_p2_8_handoff_ref
    assert gate.dependency_no_live_binding_proof_ref
    assert gate.dependency_side_effect_proof_ref == "P27DSideEffectProof:all_false"
    assert gate.repo_evidence_gate_passed is True
    assert gate.omni_evidence_required is False
    assert gate.omni_evidence_ignored_by_operator_instruction is True
    assert_omni_evidence_is_ignored_by_operator_instruction(gate)


def test_p2_8_a_does_not_start_future_work() -> None:
    result = build_p2_8_a_shell_state_foundation_result()
    assert result.next_pack == P2_8_A_NEXT_PACK == "P2.8-B"
    assert result.starts_future_work is False
    assert result.side_effect_proof.p2_8_b_started is False
    assert result.side_effect_proof.p2_9_started is False
    assert result.side_effect_proof.p2_10_started is False
    assert result.side_effect_proof.p2_13_started is False
    assert_p2_8_a_does_not_start_future_work(result)


def test_closed_world_enums_reject_unknown_values() -> None:
    with pytest.raises(ValueError):
        ShellStateFoundationGateStatus("LIVE")
    with pytest.raises(ValueError):
        ShellStateSnapshotScope("SESSION_ENGINE")
    with pytest.raises(ValueError):
        ShellReportDocsAvailabilityStatus("GRANTED")


def test_p2_7_d_dependency_refs() -> None:
    result = build_p2_8_a_shell_state_foundation_result()
    assert result.p2_7_d_evidence_ref.startswith(P2_7_D_REPORT_PATH)
    assert result.p2_7_d_section_seal_ref
    assert result.p2_7_d_handoff_ref
    assert result.p2_7_d_no_live_binding_proof_ref


def test_p2_8_0_foundation_gate() -> None:
    gate = build_shell_state_foundation_gate()
    assert gate.gate_status in set(ShellStateFoundationGateStatus)
    assert gate.created_for_pack == "P2.8-A"
    assert gate.official_section_name == "Shell State / Reports / Docs"
    assert gate.truth_label == "SHELL_STATE_FOUNDATION_ONLY"
    assert json.loads(json.dumps(gate.to_canonical_dict(), sort_keys=True))


def test_p2_8_1_identity_snapshot_and_source_reference() -> None:
    identity = build_shell_state_foundation_identity()
    snapshot = build_shell_state_snapshot_contract()
    source_ref = build_shell_state_source_reference()

    assert identity.is_runtime_identity is False
    assert identity.is_product_identity is False
    assert identity.active_surface_set == OFFICIAL_ACTIVE_SURFACE_NAMES
    for old_surface in OLD_SURFACE_TAXONOMY:
        assert old_surface not in identity.active_surface_set

    assert snapshot.snapshot_scope in set(ShellStateSnapshotScope)
    assert snapshot.is_live_shell_state is False
    assert snapshot.mutates_runtime_state is False
    assert snapshot.mutates_shell_state is False
    assert_shell_state_snapshot_is_not_live_state(snapshot)

    assert source_ref.is_storage_persistence is False
    assert source_ref.writes_storage is False
    assert source_ref.writes_trace is False
    assert source_ref.writes_memory is False
    assert_source_reference_is_not_storage_persistence(source_ref)

    assert json.loads(json.dumps(snapshot.to_canonical_dict(), sort_keys=True))
    assert json.loads(json.dumps(source_ref.to_canonical_dict(), sort_keys=True))


def test_p2_8_2_report_reference_registry() -> None:
    registry = build_shell_report_reference_registry()
    assert registry.source_reports_index_ref == "agent/REPORTS.md"
    assert registry.is_agent_reports_replacement is False
    assert registry.generates_reports is False
    assert registry.publishes_reports is False
    assert registry.writes_reports_runtime is False
    assert len(registry.report_entries) >= 1
    for entry in registry.report_entries:
        assert entry.available_as_reference is True
        assert entry.available_as_generated_report is False
    assert_report_registry_is_not_agent_reports_replacement(registry)
    assert json.loads(json.dumps(registry.to_canonical_dict(), sort_keys=True))


def test_p2_8_3_docs_reference_registry() -> None:
    registry = build_shell_docs_reference_registry()
    assert registry.is_docs_source_of_truth is False
    assert registry.generates_docs is False
    assert registry.publishes_docs is False
    assert registry.writes_docs_runtime is False
    assert len(registry.docs_entries) >= 1
    assert len(registry.source_docs_refs) == len(registry.docs_entries)
    for entry in registry.docs_entries:
        assert entry.available_as_reference is True
        assert entry.available_as_generated_docs is False
    assert_docs_registry_is_not_docs_source_of_truth(registry)
    assert json.loads(json.dumps(registry.to_canonical_dict(), sort_keys=True))


def test_p2_8_4_availability_governance_and_boundaries() -> None:
    availability = build_shell_report_docs_availability_contract()
    governance = build_shell_state_governance_source_boundary()
    no_runtime = build_shell_state_no_runtime_mutation_boundary()
    no_write = build_shell_state_no_trace_memory_storage_write_boundary()

    assert availability.availability_status in set(ShellReportDocsAvailabilityStatus)
    assert availability.enforces_permission is False
    assert availability.grants_permission is False
    assert availability.denies_permission is False
    assert_report_docs_availability_is_not_permission_enforcement(availability)

    assert governance.agent_governance_source == "agent/"
    assert governance.agent_reports_source == "agent/REPORTS.md"
    assert governance.replaces_agent_governance is False
    assert governance.replaces_agent_reports is False
    assert governance.creates_new_governance_source is False
    assert governance.creates_docs_source_of_truth is False

    assert_no_runtime_state_mutation(no_runtime)
    assert_no_trace_memory_storage_writes(no_write)
    assert json.loads(json.dumps(availability.to_canonical_dict(), sort_keys=True))
    assert json.loads(json.dumps(governance.to_canonical_dict(), sort_keys=True))


def test_p2_8_5_foundation_result_and_pack_result() -> None:
    foundation = build_shell_state_foundation_result()
    result = build_p2_8_a_shell_state_foundation_result()

    assert foundation.creates_live_shell_state is False
    assert foundation.creates_shell_runtime is False
    assert foundation.creates_persistent_store is False
    assert foundation.creates_report_generator is False
    assert foundation.creates_docs_generator is False
    assert foundation.creates_product_behavior is False

    assert result.claims_live is False
    assert result.claims_trace_verified is False
    assert result.claims_release_scope is False
    assert result.claims_product_behavior is False
    assert result.covered_checkpoints == P2_8_A_PACK_CHECKPOINT_IDS
    assert json.loads(json.dumps(foundation.to_canonical_dict(), sort_keys=True))
    assert json.loads(json.dumps(result.to_canonical_dict(), sort_keys=True))


def test_side_effect_proof_all_false() -> None:
    proof = build_p2_8_a_side_effect_proof()
    assert_p2_8_a_side_effects_all_false(proof)
    for field in fields(P28ASideEffectProof):
        assert getattr(proof, field.name) is False


def test_serialization_and_summary() -> None:
    result = build_p2_8_a_shell_state_foundation_result()
    serialized = serialize_p2_8_a_result(result)
    parsed = json.loads(serialized)
    assert parsed["pack_id"] == P2_8_A_PACK_ID
    assert parsed["section_id"] == P2_8_A_SECTION_ID

    summary = render_shell_state_foundation_summary(result)
    assert "Shell State / Reports / Docs" in summary
    assert "P2.8-B" in summary
    assert "live_shell_state=false" in summary


def test_validation_commands_recorded() -> None:
    assert P2_8_A_VALIDATION_COMMANDS
    assert P2_8_A_REPORT_PATH.endswith(".md")
    assert "test_shell_state_foundation.py" in P2_8_A_VALIDATION_COMMANDS[1]
