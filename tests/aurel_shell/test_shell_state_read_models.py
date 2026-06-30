"""Tests for P2.8-B Shell State read models / report-docs index contracts."""

from __future__ import annotations

import json
from dataclasses import fields

import pytest

from agentic_runtime.aurel_shell.shell_state_foundation import (
    P2_8_A_REPORT_PATH,
    build_p2_8_a_shell_state_foundation_result,
)
from agentic_runtime.aurel_shell.shell_state_read_models import (
    P2_8_B_DEPENDENCY_PACK,
    P2_8_B_NEXT_PACK,
    P2_8_B_OFFICIAL_SECTION_NAME,
    P2_8_B_PACK_CHECKPOINT_IDS,
    P2_8_B_PACK_ID,
    P2_8_B_REPORT_PATH,
    P2_8_B_SECTION_ID,
    P2_8_B_VALIDATION_COMMANDS,
    P28BSideEffectProof,
    ShellReadModelAvailabilityStatus,
    ShellReportDocsDescriptorMode,
    ShellStateReadModelGateStatus,
    assert_availability_rollup_is_not_permission_enforcement,
    assert_docs_index_is_not_docs_source_of_truth,
    assert_expansion_result_is_contract_only,
    assert_no_report_docs_generation,
    assert_no_runtime_state_mutation,
    assert_no_trace_memory_storage_writes,
    assert_omni_evidence_is_ignored_by_operator_instruction,
    assert_p2_8_b_does_not_start_future_work,
    assert_p2_8_b_side_effects_all_false,
    assert_query_filter_sort_descriptors_do_not_execute,
    assert_read_model_gate_depends_on_p2_8_a,
    assert_read_model_inventory_does_not_duplicate_source_of_truth,
    assert_read_model_registry_is_not_query_runtime,
    assert_report_docs_grouping_is_not_generation,
    assert_report_index_is_not_agent_reports_replacement,
    assert_section_status_read_model_does_not_mutate_shell_state,
    assert_state_snapshot_read_model_is_not_live_shell_state,
    build_p2_8_b_shell_state_read_model_result,
    build_p2_8_b_side_effect_proof,
    build_shell_docs_family_grouping,
    build_shell_docs_index_entry,
    build_shell_docs_index_read_model,
    build_shell_read_model_availability_rollup,
    build_shell_read_model_no_generation_boundary,
    build_shell_read_model_no_runtime_mutation_boundary,
    build_shell_read_model_no_trace_memory_storage_write_boundary,
    build_shell_report_docs_filter_descriptor,
    build_shell_report_docs_query_descriptor,
    build_shell_report_docs_sort_descriptor,
    build_shell_report_family_grouping,
    build_shell_report_index_entry,
    build_shell_report_index_read_model,
    build_shell_section_status_read_model,
    build_shell_state_read_model_entry,
    build_shell_state_read_model_expansion_result,
    build_shell_state_read_model_gate,
    build_shell_state_read_model_inventory,
    build_shell_state_read_model_registry,
    build_shell_state_snapshot_read_model,
    render_shell_state_read_model_summary,
    serialize_p2_8_b_result,
)
from agentic_runtime.aurel_shell.surface_registry import OLD_SURFACE_TAXONOMY


def _roundtrip(obj) -> dict:
    return json.loads(json.dumps(obj.to_canonical_dict(), sort_keys=True))


def test_module_imports_p2_8_b() -> None:
    import agentic_runtime.aurel_shell.shell_state_read_models  # noqa: F401


def test_gate_dependency_and_omni_policy() -> None:
    result = build_p2_8_b_shell_state_read_model_result()
    gate = result.read_model_gate

    assert P2_8_B_PACK_ID == "P2.8-B"
    assert P2_8_B_SECTION_ID == "P2.8"
    assert P2_8_B_OFFICIAL_SECTION_NAME == "Shell State / Reports / Docs"
    assert P2_8_B_DEPENDENCY_PACK == "P2.8-A"
    assert gate.dependency_pack == "P2.8-A"
    assert gate.dependency_report_ref == P2_8_A_REPORT_PATH
    assert gate.dependency_foundation_result_ref
    assert gate.dependency_state_snapshot_ref
    assert gate.dependency_report_registry_ref
    assert gate.dependency_docs_registry_ref
    assert gate.dependency_governance_source_boundary_ref
    assert gate.dependency_no_runtime_mutation_boundary_ref
    assert gate.dependency_no_write_boundary_ref
    assert gate.dependency_side_effect_proof_ref == "P28ASideEffectProof:all_false"
    assert gate.repo_evidence_gate_passed is True
    assert gate.omni_evidence_required is False
    assert gate.omni_evidence_ignored_by_operator_instruction is True
    assert_read_model_gate_depends_on_p2_8_a(gate)
    assert_omni_evidence_is_ignored_by_operator_instruction(gate)


def test_p2_8_a_evidence_represented() -> None:
    foundation = build_p2_8_a_shell_state_foundation_result()
    result = build_p2_8_b_shell_state_read_model_result()

    assert result.p2_8_a_evidence_ref.startswith(P2_8_A_REPORT_PATH)
    assert foundation.foundation_result.foundation_result_id in (
        result.p2_8_a_foundation_result_ref
    )
    assert foundation.snapshot_contract.snapshot_id in result.p2_8_a_state_snapshot_ref
    assert foundation.report_registry.report_registry_id in (
        result.p2_8_a_report_registry_ref
    )
    assert foundation.docs_registry.docs_registry_id in result.p2_8_a_docs_registry_ref


def test_p2_8_b_does_not_start_future_work() -> None:
    result = build_p2_8_b_shell_state_read_model_result()
    assert result.next_pack == P2_8_B_NEXT_PACK == "P2.8-C"
    assert result.starts_future_work is False
    assert result.side_effect_proof.p2_8_c_started is False
    assert result.side_effect_proof.p2_8_d_started is False
    assert result.side_effect_proof.p2_9_started is False
    assert result.side_effect_proof.p2_10_started is False
    assert result.side_effect_proof.p2_13_started is False
    assert_p2_8_b_does_not_start_future_work(result)


def test_closed_world_enums_reject_unknown_values() -> None:
    with pytest.raises(ValueError):
        ShellStateReadModelGateStatus("LIVE")
    with pytest.raises(ValueError):
        ShellReadModelAvailabilityStatus("GRANTED")
    with pytest.raises(ValueError):
        ShellReportDocsDescriptorMode("EXECUTABLE")


def test_p2_8_6_gate_registry_inventory() -> None:
    gate = build_shell_state_read_model_gate()
    registry = build_shell_state_read_model_registry()
    entry = build_shell_state_read_model_entry()
    inventory = build_shell_state_read_model_inventory()

    assert gate.gate_status in set(ShellStateReadModelGateStatus)
    assert gate.created_for_pack == "P2.8-B"
    assert gate.official_section_name == "Shell State / Reports / Docs"

    assert entry.availability_status in set(ShellReadModelAvailabilityStatus)
    assert len(registry.registry_entries) > 0
    assert registry.is_query_runtime is False
    assert registry.executes_queries is False

    section_status_id = "p2_8_b_shell_section_status_read_model"
    assert section_status_id in inventory.read_model_entries
    assert "ShellStateReadModelGate" in inventory.contract_refs
    assert P2_8_A_REPORT_PATH in inventory.source_report_refs
    assert P2_8_B_REPORT_PATH in inventory.source_report_refs
    assert inventory.is_source_of_truth is False
    assert inventory.duplicates_agent_governance is False

    assert_read_model_registry_is_not_query_runtime(registry)
    assert_read_model_inventory_does_not_duplicate_source_of_truth(inventory)
    assert _roundtrip(gate)
    assert _roundtrip(registry)
    assert _roundtrip(inventory)


def test_p2_8_7_section_status_and_state_snapshot_read_model() -> None:
    section_status = build_shell_section_status_read_model()
    state_snapshot = build_shell_state_snapshot_read_model()

    assert section_status.is_mutable_shell_state is False
    assert section_status.mutates_shell_state is False
    assert section_status.mutates_runtime_state is False
    assert "P2.8.0-P2.8.10" in section_status.section_scope

    assert state_snapshot.is_live_shell_state is False
    assert state_snapshot.is_session_state_engine is False
    assert state_snapshot.mutates_shell_state is False

    assert_section_status_read_model_does_not_mutate_shell_state(section_status)
    assert_state_snapshot_read_model_is_not_live_shell_state(state_snapshot)
    assert _roundtrip(section_status)
    assert _roundtrip(state_snapshot)


def test_p2_8_8_report_index_and_family_grouping() -> None:
    entry = build_shell_report_index_entry()
    grouping = build_shell_report_family_grouping((entry.report_ref,))
    index = build_shell_report_index_read_model()

    assert entry.report_ref == P2_8_A_REPORT_PATH
    assert grouping.is_report_generation is False
    assert len(index.report_index_entries) > 0
    assert len(index.report_family_groupings) == 1
    assert index.source_agent_reports_ref == "agent/REPORTS.md"
    assert index.is_agent_reports_replacement is False
    assert index.is_report_generation is False
    assert index.publishes_reports is False

    assert_report_docs_grouping_is_not_generation(grouping)
    assert_report_index_is_not_agent_reports_replacement(index)
    assert _roundtrip(entry)
    assert _roundtrip(grouping)
    assert _roundtrip(index)


def test_p2_8_9_docs_index_and_query_filter_sort_descriptors() -> None:
    entry = build_shell_docs_index_entry()
    grouping = build_shell_docs_family_grouping((entry.docs_ref,))
    index = build_shell_docs_index_read_model()
    query = build_shell_report_docs_query_descriptor()
    filter_descriptor = build_shell_report_docs_filter_descriptor()
    sort = build_shell_report_docs_sort_descriptor()

    assert grouping.is_docs_generation is False
    assert len(index.docs_index_entries) > 0
    assert len(index.docs_family_groupings) == 1
    assert index.is_docs_source_of_truth is False
    assert index.is_docs_generation is False
    assert index.publishes_docs is False

    assert query.is_query_runtime is False
    assert query.executes_query is False
    assert filter_descriptor.is_filter_runtime is False
    assert filter_descriptor.executes_filter is False
    assert sort.is_sort_runtime is False
    assert sort.executes_sort is False

    assert_report_docs_grouping_is_not_generation(grouping)
    assert_docs_index_is_not_docs_source_of_truth(index)
    assert_query_filter_sort_descriptors_do_not_execute(query, filter_descriptor, sort)
    assert _roundtrip(index)
    assert _roundtrip(query)
    assert _roundtrip(filter_descriptor)
    assert _roundtrip(sort)


def test_p2_8_10_expansion_result_boundaries_and_pack_result() -> None:
    availability = build_shell_read_model_availability_rollup()
    no_generation = build_shell_read_model_no_generation_boundary()
    no_runtime = build_shell_read_model_no_runtime_mutation_boundary()
    no_write = build_shell_read_model_no_trace_memory_storage_write_boundary()
    expansion = build_shell_state_read_model_expansion_result()
    result = build_p2_8_b_shell_state_read_model_result()

    assert availability.enforces_permission is False
    assert availability.grants_permission is False
    assert availability.denies_permission is False
    assert "query runtime" in availability.unavailable_capabilities
    assert "P2.8-C" in availability.future_pack_refs

    assert no_generation.boundary_active is True
    assert no_generation.report_generator_created is False
    assert no_generation.docs_generator_created is False
    assert no_runtime.boundary_active is True
    assert no_runtime.query_runtime_created is False
    assert no_runtime.filter_runtime_created is False
    assert no_runtime.sort_runtime_created is False
    assert no_write.boundary_active is True
    assert no_write.trace_written is False
    assert no_write.memory_written is False
    assert no_write.storage_written is False

    assert expansion.creates_query_runtime is False
    assert expansion.creates_generator_runtime is False
    assert expansion.creates_write_path is False
    assert expansion.creates_product_behavior is False
    assert result.covered_checkpoints == P2_8_B_PACK_CHECKPOINT_IDS
    assert result.next_pack == "P2.8-C"
    assert result.claims_live is False
    assert result.claims_trace_verified is False
    assert result.claims_release_scope is False
    assert result.claims_product_behavior is False

    assert_availability_rollup_is_not_permission_enforcement(availability)
    assert_no_report_docs_generation(no_generation)
    assert_no_runtime_state_mutation(no_runtime)
    assert_no_trace_memory_storage_writes(no_write)
    assert_expansion_result_is_contract_only(expansion)
    assert _roundtrip(expansion)


def test_surface_taxonomy_drift_does_not_activate_old_surfaces() -> None:
    result = build_p2_8_b_shell_state_read_model_result()
    for old_surface in OLD_SURFACE_TAXONOMY:
        assert old_surface not in result.official_section_name
    assert result.surface_taxonomy_drift is True
    assert result.surface_taxonomy_drift_details


def test_side_effect_proof_all_false() -> None:
    proof = build_p2_8_b_side_effect_proof()
    assert_p2_8_b_side_effects_all_false(proof)
    for field in fields(P28BSideEffectProof):
        assert getattr(proof, field.name) is False


def test_serialization_and_summary() -> None:
    result = build_p2_8_b_shell_state_read_model_result()
    serialized = serialize_p2_8_b_result(result)
    parsed = json.loads(serialized)
    assert parsed["pack_id"] == P2_8_B_PACK_ID
    assert parsed["section_id"] == P2_8_B_SECTION_ID

    summary = render_shell_state_read_model_summary(result)
    assert "Shell State / Reports / Docs" in summary
    assert "P2.8-C" in summary
    assert "query_runtime=false" in summary
    assert "generator_runtime=false" in summary


def test_validation_commands_recorded() -> None:
    assert P2_8_B_VALIDATION_COMMANDS == (
        ".venv/bin/python -m compileall src tests",
        ".venv/bin/python -m pytest tests/aurel_shell/test_shell_state_read_models.py -q",
        ".venv/bin/python -m pytest tests/aurel_shell -q",
        ".venv/bin/python -m ruff check src tests",
        ".venv/bin/python -m mypy src/agentic_runtime",
    )
