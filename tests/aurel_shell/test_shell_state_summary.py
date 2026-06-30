"""Tests for P2.8-C Shell state summary / sync descriptor / read-only summary boundary."""

from __future__ import annotations

import json
from dataclasses import fields

import pytest

from agentic_runtime.aurel_shell.shell_state_read_models import (
    P2_8_B_REPORT_PATH,
    build_p2_8_b_shell_state_read_model_result,
)
from agentic_runtime.aurel_shell.shell_state_summary import (
    P2_8_C_DEPENDENCY_PACK,
    P2_8_C_NEXT_PACK,
    P2_8_C_OFFICIAL_SECTION_NAME,
    P2_8_C_PACK_CHECKPOINT_IDS,
    P2_8_C_PACK_ID,
    P2_8_C_REPORT_PATH,
    P2_8_C_SECTION_ID,
    P2_8_C_VALIDATION_COMMANDS,
    P28CSideEffectProof,
    ShellReadOnlySummaryAvailabilityStatus,
    ShellStateSummaryGateStatus,
    ShellStateSyncDescriptorMode,
    assert_drift_missing_stale_do_not_repair,
    assert_omni_evidence_is_ignored_by_operator_instruction,
    assert_p2_8_c_does_not_start_future_work,
    assert_p2_8_c_side_effects_all_false,
    assert_source_comparison_is_not_authority,
    assert_summary_contract_is_not_generator,
    assert_summary_gate_depends_on_p2_8_b,
    assert_sync_candidate_is_not_reconciliation_execution,
    assert_sync_descriptor_is_not_sync_runtime,
    build_p2_8_c_shell_state_summary_result,
    build_p2_8_c_side_effect_proof,
    build_shell_docs_index_summary,
    build_shell_read_only_summary_availability,
    build_shell_reference_drift_descriptor,
    build_shell_reference_missing_descriptor,
    build_shell_reference_stale_descriptor,
    build_shell_report_index_summary,
    build_shell_source_comparison_descriptor,
    build_shell_state_read_only_summary,
    build_shell_state_summary_boundary_result,
    build_shell_state_summary_bundle,
    build_shell_state_summary_gate,
    build_shell_state_sync_candidate,
    build_shell_state_sync_descriptor,
    build_shell_summary_limitation_descriptor,
    build_shell_summary_no_generation_boundary,
    build_shell_summary_no_sync_runtime_boundary,
    build_shell_summary_no_write_boundary,
    render_shell_state_summary_boundary,
    serialize_p2_8_c_result,
)
from agentic_runtime.aurel_shell.surface_registry import OLD_SURFACE_TAXONOMY


def _roundtrip(obj) -> dict:
    return json.loads(json.dumps(obj.to_canonical_dict(), sort_keys=True))


def test_module_imports_p2_8_c() -> None:
    import agentic_runtime.aurel_shell.shell_state_summary  # noqa: F401


def test_gate_dependency_and_omni_policy() -> None:
    result = build_p2_8_c_shell_state_summary_result()
    gate = result.summary_gate

    assert P2_8_C_PACK_ID == "P2.8-C"
    assert P2_8_C_SECTION_ID == "P2.8"
    assert P2_8_C_OFFICIAL_SECTION_NAME == "Shell State / Reports / Docs"
    assert P2_8_C_DEPENDENCY_PACK == "P2.8-B"
    assert gate.dependency_pack == "P2.8-B"
    assert gate.dependency_report_ref == P2_8_B_REPORT_PATH
    assert gate.dependency_read_model_expansion_result_ref
    assert gate.dependency_report_index_ref
    assert gate.dependency_docs_index_ref
    assert gate.dependency_no_generation_boundary_ref
    assert gate.dependency_no_runtime_mutation_boundary_ref
    assert gate.dependency_no_write_boundary_ref
    assert gate.dependency_side_effect_proof_ref == "P28BSideEffectProof:all_false"
    assert gate.repo_evidence_gate_passed is True
    assert gate.omni_evidence_required is False
    assert gate.omni_evidence_ignored_by_operator_instruction is True
    assert_summary_gate_depends_on_p2_8_b(gate)
    assert_omni_evidence_is_ignored_by_operator_instruction(gate)


def test_p2_8_b_evidence_represented() -> None:
    read_model = build_p2_8_b_shell_state_read_model_result()
    result = build_p2_8_c_shell_state_summary_result()

    assert result.p2_8_b_evidence_ref.startswith(P2_8_B_REPORT_PATH)
    assert read_model.result_hash[:12] in result.p2_8_b_read_model_result_ref
    assert read_model.report_index.report_index_id in result.p2_8_b_report_index_ref
    assert read_model.docs_index.docs_index_id in result.p2_8_b_docs_index_ref


def test_p2_8_c_does_not_start_future_work() -> None:
    result = build_p2_8_c_shell_state_summary_result()
    assert result.next_pack == P2_8_C_NEXT_PACK == "P2.8-D"
    assert result.starts_future_work is False
    assert result.side_effect_proof.p2_8_d_started is False
    assert result.side_effect_proof.p2_9_started is False
    assert result.side_effect_proof.p2_10_started is False
    assert result.side_effect_proof.p2_13_started is False
    assert_p2_8_c_does_not_start_future_work(result)


def test_closed_world_enums_reject_unknown_values() -> None:
    with pytest.raises(ValueError):
        ShellStateSummaryGateStatus("LIVE")
    with pytest.raises(ValueError):
        ShellReadOnlySummaryAvailabilityStatus("GRANTED")
    with pytest.raises(ValueError):
        ShellStateSyncDescriptorMode("EXECUTABLE")


def test_p2_8_11_docs_and_report_index_summaries() -> None:
    gate = build_shell_state_summary_gate()
    docs_summary = build_shell_docs_index_summary()
    report_summary = build_shell_report_index_summary()

    assert gate.gate_status in set(ShellStateSummaryGateStatus)
    assert gate.created_for_pack == "P2.8-C"
    assert gate.official_section_name == "Shell State / Reports / Docs"

    assert docs_summary.is_docs_generation is False
    assert docs_summary.is_docs_source_of_truth is False
    assert docs_summary.writes_docs is False
    assert docs_summary.docs_ref_count > 0

    assert report_summary.is_report_generation is False
    assert report_summary.is_agent_reports_replacement is False
    assert report_summary.writes_reports is False
    assert report_summary.report_ref_count > 0
    assert report_summary.source_agent_reports_ref == "agent/REPORTS.md"

    assert_summary_contract_is_not_generator(docs_summary)
    assert_summary_contract_is_not_generator(report_summary)
    assert _roundtrip(gate)
    assert _roundtrip(docs_summary)
    assert _roundtrip(report_summary)


def test_p2_8_12_state_read_only_summary_and_bundle() -> None:
    state_summary = build_shell_state_read_only_summary()
    bundle = build_shell_state_summary_bundle()
    limitation = build_shell_summary_limitation_descriptor(state_summary)

    assert state_summary.is_read_only is True
    assert state_summary.mutates_shell_state is False
    assert state_summary.mutates_runtime_state is False
    assert state_summary.is_product_ui is False

    assert bundle.is_product_summary is False
    assert bundle.is_generated_summary is False
    assert bundle.requires_runtime is False
    assert limitation.is_policy_enforcement is False

    assert_summary_contract_is_not_generator(state_summary)
    assert _roundtrip(state_summary)
    assert _roundtrip(bundle)
    assert _roundtrip(limitation)


def test_p2_8_13_sync_descriptor_and_candidate() -> None:
    sync_descriptor = build_shell_state_sync_descriptor()
    sync_candidate = build_shell_state_sync_candidate()

    assert sync_descriptor.sync_descriptor_mode in set(ShellStateSyncDescriptorMode)
    assert sync_descriptor.is_sync_runtime is False
    assert sync_descriptor.executes_sync is False
    assert sync_descriptor.mutates_shell_state is False
    assert sync_descriptor.creates_reconciliation_engine is False

    assert sync_candidate.is_reconciliation_execution is False
    assert sync_candidate.executes_candidate is False
    assert sync_candidate.creates_repair_action is False

    assert_sync_descriptor_is_not_sync_runtime(sync_descriptor)
    assert_sync_candidate_is_not_reconciliation_execution(sync_candidate)
    assert _roundtrip(sync_descriptor)
    assert _roundtrip(sync_candidate)


def test_p2_8_14_drift_missing_stale_and_source_comparison() -> None:
    drift = build_shell_reference_drift_descriptor()
    missing = build_shell_reference_missing_descriptor()
    stale = build_shell_reference_stale_descriptor()
    comparison = build_shell_source_comparison_descriptor()

    assert drift.is_repair_action is False
    assert drift.executes_repair is False
    assert drift.writes_fix is False

    assert missing.is_auto_fix is False
    assert missing.executes_auto_fix is False
    assert missing.writes_fix is False

    assert stale.is_refresh_runtime is False
    assert stale.executes_refresh is False
    assert stale.writes_refresh is False

    assert comparison.is_authority_decision is False
    assert comparison.decides_truth is False
    assert comparison.enforces_policy is False

    assert_drift_missing_stale_do_not_repair(drift, missing, stale)
    assert_source_comparison_is_not_authority(comparison)
    assert _roundtrip(drift)
    assert _roundtrip(missing)
    assert _roundtrip(stale)
    assert _roundtrip(comparison)


def test_p2_8_15_boundary_result_and_pack_result() -> None:
    availability = build_shell_read_only_summary_availability()
    no_sync = build_shell_summary_no_sync_runtime_boundary()
    no_generation = build_shell_summary_no_generation_boundary()
    no_write = build_shell_summary_no_write_boundary()
    boundary = build_shell_state_summary_boundary_result()
    result = build_p2_8_c_shell_state_summary_result()

    assert availability.enforces_permission is False
    assert availability.grants_permission is False
    assert availability.denies_permission is False
    assert "sync runtime" in availability.unavailable_capabilities[1].lower()

    assert no_sync.boundary_active is True
    assert no_sync.shell_state_sync_runtime_created is False
    assert no_sync.state_reconciliation_engine_created is False
    assert no_sync.sync_executed is False
    assert no_sync.repair_action_created is False
    assert no_sync.autofix_created is False
    assert no_sync.refresh_runtime_created is False

    assert no_generation.boundary_active is True
    assert no_generation.summary_generator_created is False
    assert no_generation.generated_summary is False

    assert no_write.boundary_active is True
    assert no_write.trace_written is False
    assert no_write.docs_written is False
    assert no_write.reports_written is False

    assert boundary.creates_sync_runtime is False
    assert boundary.creates_reconciliation_engine is False
    assert boundary.creates_generator_runtime is False
    assert boundary.creates_write_path is False
    assert boundary.creates_product_behavior is False

    assert result.covered_checkpoints == P2_8_C_PACK_CHECKPOINT_IDS
    assert result.claims_live is False
    assert result.claims_trace_verified is False
    assert result.claims_release_scope is False
    assert result.claims_product_behavior is False
    assert _roundtrip(boundary)


def test_surface_taxonomy_drift_does_not_activate_old_surfaces() -> None:
    result = build_p2_8_c_shell_state_summary_result()
    for old_surface in OLD_SURFACE_TAXONOMY:
        assert old_surface not in result.official_section_name
    assert result.surface_taxonomy_drift is True
    assert result.surface_taxonomy_drift_details


def test_side_effect_proof_all_false() -> None:
    proof = build_p2_8_c_side_effect_proof()
    assert_p2_8_c_side_effects_all_false(proof)
    for field in fields(P28CSideEffectProof):
        assert getattr(proof, field.name) is False


def test_serialization_and_summary() -> None:
    result = build_p2_8_c_shell_state_summary_result()
    serialized = serialize_p2_8_c_result(result)
    parsed = json.loads(serialized)
    assert parsed["pack_id"] == P2_8_C_PACK_ID
    assert parsed["section_id"] == P2_8_C_SECTION_ID

    summary = render_shell_state_summary_boundary(result)
    assert "Shell State / Reports / Docs" in summary
    assert "P2.8-D" in summary
    assert "sync_runtime=false" in summary
    assert "generator_runtime=false" in summary


def test_validation_commands_recorded() -> None:
    assert P2_8_C_VALIDATION_COMMANDS == (
        ".venv/bin/python -m compileall src tests",
        ".venv/bin/python -m pytest tests/aurel_shell/test_shell_state_summary.py -q",
        ".venv/bin/python -m pytest tests/aurel_shell -q",
        ".venv/bin/python -m ruff check src tests",
        ".venv/bin/python -m mypy src/agentic_runtime",
    )
    assert P2_8_C_REPORT_PATH.endswith("P2_8_C_DOCS_INDEX_STATE_SYNC_READ_ONLY_SUMMARY.md")
