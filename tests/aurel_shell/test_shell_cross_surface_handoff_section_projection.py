"""Tests for P2.5-D handoff section projection and seal."""

from __future__ import annotations

import json

import pytest

from agentic_runtime.aurel_shell.contracts import AurelShellValidationError
from agentic_runtime.aurel_shell.cross_surface_handoff_preview import (
    P2_5_C_REPORT_PATH,
    build_p2_5_c_handoff_preview_result,
)
from agentic_runtime.aurel_shell.cross_surface_handoff_section_projection import (
    HANDOFF_SECTION_BINDING_UNAVAILABLE_REASON,
    P2_5_A_REPORT_PATH,
    P2_5_B_REPORT_PATH,
    P2_5_C_COMMIT_REF,
    P2_5_D_DEPENDENCY_PACK,
    P2_5_D_NEXT_CANDIDATE,
    P2_5_D_PACK_CHECKPOINT_IDS,
    P2_5_D_PACK_ID,
    P2_5_D_REPORT_PATH,
    P2_5_D_SECTION_ID,
    CrossSurfaceHandoffAuditFindingKind,
    CrossSurfaceHandoffBindingMode,
    CrossSurfaceHandoffBindingStatus,
    CrossSurfaceHandoffCapabilityStatus,
    CrossSurfaceHandoffPackStatus,
    CrossSurfaceHandoffSectionGateStatus,
    CrossSurfaceHandoffSectionProjection,
    CrossSurfaceHandoffSectionSealStatus,
    P25DHandoffSectionResult,
    assert_binding_status_is_not_live_binding,
    assert_contract_scope_demo_is_not_runtime_demo,
    assert_omni_evidence_is_ignored_by_operator_instruction,
    assert_p2_5_c_preview_result_available,
    assert_p2_5_d_does_not_start_future_work,
    assert_p2_5_d_side_effects_all_false,
    assert_readiness_audit_catches_fake_live_claims,
    assert_section_gate_depends_on_p2_5_c,
    assert_section_projection_is_not_ui,
    assert_section_seal_is_not_release_seal,
    build_cross_surface_handoff_binding_status,
    build_cross_surface_handoff_contract_inventory,
    build_cross_surface_handoff_contract_scope_demo,
    build_cross_surface_handoff_docs_state_report_sync,
    build_cross_surface_handoff_pack_rollup,
    build_cross_surface_handoff_readiness_audit,
    build_cross_surface_handoff_section_gate,
    build_cross_surface_handoff_section_projection,
    build_cross_surface_handoff_section_seal,
    build_cross_surface_handoff_section_capabilities,
    build_cross_surface_handoff_unavailable_capabilities,
    build_p2_5_d_handoff_section_result,
    build_p2_5_d_side_effect_proof,
    render_cross_surface_handoff_section_summary,
    serialize_p2_5_d_result,
)
from agentic_runtime.aurel_shell.surface_registry import CANONICAL_SURFACE_ORDER


def test_module_imports_p2_5_d() -> None:
    import agentic_runtime.aurel_shell.cross_surface_handoff_section_projection  # noqa: F401


def test_gate_dependency_and_omni_policy() -> None:
    preview = build_p2_5_c_handoff_preview_result()
    result = build_p2_5_d_handoff_section_result()
    gate = result.section_gate

    assert P2_5_D_PACK_ID == "P2.5-D"
    assert P2_5_D_SECTION_ID == "P2.5"
    assert P2_5_D_PACK_CHECKPOINT_IDS == (
        "P2.5.16",
        "P2.5.17",
        "P2.5.18",
        "P2.5.19",
        "P2.5.20",
    )
    assert P2_5_D_DEPENDENCY_PACK == "P2.5-C"
    assert gate.dependency_pack == "P2.5-C"
    assert gate.dependency_report_ref == P2_5_C_REPORT_PATH
    assert gate.dependency_commit_ref == P2_5_C_COMMIT_REF
    assert gate.repo_evidence_gate_passed is True
    assert gate.omni_evidence_required is False
    assert gate.omni_evidence_ignored_by_operator_instruction is True
    assert "no_confirmation" in gate.dependency_no_confirmation_boundary_ref
    assert "no_execution" in gate.dependency_no_execution_boundary_ref
    assert result.next_candidate == P2_5_D_NEXT_CANDIDATE
    assert result.next_candidate_requires_canon_read is True
    assert result.starts_future_work is False
    assert_p2_5_c_preview_result_available(preview)
    assert_section_gate_depends_on_p2_5_c(gate)
    assert_omni_evidence_is_ignored_by_operator_instruction(gate)


def test_closed_world_enums_reject_unknown_values() -> None:
    with pytest.raises(ValueError):
        CrossSurfaceHandoffSectionGateStatus("LIVE")
    with pytest.raises(ValueError):
        CrossSurfaceHandoffPackStatus("PRODUCT_READY")
    with pytest.raises(ValueError):
        CrossSurfaceHandoffCapabilityStatus("TRACE_VERIFIED")
    with pytest.raises(ValueError):
        CrossSurfaceHandoffBindingMode("EXECUTE")
    with pytest.raises(ValueError):
        CrossSurfaceHandoffSectionSealStatus("RELEASE_SEALED")


def test_p2_5_16_section_projection_inventory_and_rollup() -> None:
    result = build_p2_5_d_handoff_section_result()
    projection = result.section_projection
    inventory = result.contract_inventory
    rollups = result.pack_rollup

    assert projection.section_id == "P2.5"
    assert projection.created_for_pack == "P2.5-D"
    assert projection.official_section_name == "Cross-Surface Handoff"
    assert projection.is_ui is False
    assert projection.is_live_binding is False
    assert projection.is_api_event_bridge is False
    assert projection.is_source_of_truth is False
    assert projection.claims_live is False
    assert projection.claims_trace_verified is False
    assert projection.claims_product_behavior is False
    assert projection.claims_release_scope is False
    assert_section_projection_is_not_ui(projection)

    assert inventory.included_packs == ("P2.5-A", "P2.5-B", "P2.5-C", "P2.5-D")
    assert inventory.contract_refs
    assert P2_5_A_REPORT_PATH in inventory.report_refs
    assert P2_5_B_REPORT_PATH in inventory.report_refs
    assert P2_5_C_REPORT_PATH in inventory.report_refs
    assert inventory.missing_contracts == ()
    assert inventory.duplicates_source_of_truth is False
    assert tuple(rollup.pack_id for rollup in rollups) == (
        "P2.5-A",
        "P2.5-B",
        "P2.5-C",
        "P2.5-D",
    )
    assert all(rollup.pack_status == CrossSurfaceHandoffPackStatus.DONE for rollup in rollups)
    assert result.canonical_surface_ids == CANONICAL_SURFACE_ORDER
    assert json.loads(serialize_p2_5_d_result(result))


def test_p2_5_16_capabilities_and_unavailable_capabilities() -> None:
    capabilities = build_cross_surface_handoff_section_capabilities()
    unavailable = build_cross_surface_handoff_unavailable_capabilities()

    names = {cap.capability_name for cap in capabilities}
    assert "cross-surface handoff foundation" in names
    assert "handoff context/availability read model" in names
    assert "handoff preview/confirmation boundary" in names
    assert "section projection/read model" in names
    assert all(
        cap.capability_status
        in (
            CrossSurfaceHandoffCapabilityStatus.CONTRACT_ONLY,
            CrossSurfaceHandoffCapabilityStatus.READ_MODEL_ONLY,
        )
        for cap in capabilities
    )

    unavailable_names = {cap.capability_name for cap in unavailable}
    assert "actual cross-surface handoff execution" in unavailable_names
    assert "live surface switching" in unavailable_names
    assert "projection UI" in unavailable_names
    assert "preview UI" in unavailable_names
    assert "operator confirmation UI" in unavailable_names
    assert "Shell execution binding" in unavailable_names
    assert "TUI execution binding" in unavailable_names
    assert "API/event bridge" in unavailable_names
    assert "LIVE handoff" in unavailable_names
    assert "TRACE_VERIFIED handoff" in unavailable_names
    assert all(cap.reason for cap in unavailable)


def test_p2_5_17_binding_read_only_and_non_executing() -> None:
    binding = build_cross_surface_handoff_binding_status()

    assert binding.binding_mode == CrossSurfaceHandoffBindingMode.READ_ONLY_CONTRACT_RENDER
    assert binding.read_only_render_available is True
    assert binding.live_shell_binding_created is False
    assert binding.live_tui_binding_created is False
    assert binding.api_event_bridge_created is False
    assert binding.handoff_execution_bound is False
    assert binding.route_execution_bound is False
    assert_binding_status_is_not_live_binding(binding)
    assert json.loads(json.dumps(binding.to_canonical_dict()))


def test_p2_5_17_binding_assertion_rejects_live_binding() -> None:
    binding = build_cross_surface_handoff_binding_status()
    payload = binding.to_canonical_dict()
    payload["live_shell_binding_created"] = True
    invalid = CrossSurfaceHandoffBindingStatus(**payload)
    with pytest.raises(AurelShellValidationError):
        assert_binding_status_is_not_live_binding(invalid)


def test_p2_5_18_docs_state_report_sync() -> None:
    sync = build_cross_surface_handoff_docs_state_report_sync()

    assert sync.section_id == "P2.5"
    assert sync.created_for_pack == "P2.5-D"
    assert sync.report_created is True
    assert sync.report_indexed is True
    assert sync.active_task_updated is True
    assert sync.roadmap_mirror_updated is True
    assert sync.state_updated is True
    assert sync.tests_updated is True
    assert sync.duplicate_agent_state_created is False
    assert sync.product_release_claim_created is False
    assert sync.next_candidate == "P2.6-A"
    assert sync.next_candidate_requires_canon_read is True
    assert P2_5_D_REPORT_PATH == "agent/reports/P2_5_D_HANDOFF_SECTION_SEAL.md"
    assert json.loads(json.dumps(sync.to_canonical_dict()))


def test_p2_5_19_readiness_audit_no_fake_handoff_gate() -> None:
    audit = build_cross_surface_handoff_readiness_audit()

    assert audit.findings
    kinds = {finding.finding_kind for finding in audit.findings}
    assert CrossSurfaceHandoffAuditFindingKind.FAKE_LIVE_CLAIM in kinds
    assert CrossSurfaceHandoffAuditFindingKind.FAKE_TRACE_VERIFIED_CLAIM in kinds
    assert CrossSurfaceHandoffAuditFindingKind.FAKE_PRODUCT_BEHAVIOR_CLAIM in kinds
    assert CrossSurfaceHandoffAuditFindingKind.FAKE_RELEASE_SCOPE_CLAIM in kinds
    assert CrossSurfaceHandoffAuditFindingKind.FAKE_LIVE_HANDOFF_CLAIM in kinds
    assert CrossSurfaceHandoffAuditFindingKind.FAKE_LIVE_BINDING_CLAIM in kinds
    assert CrossSurfaceHandoffAuditFindingKind.FAKE_UI_PROJECTION_CLAIM in kinds
    assert audit.blocks_live_claim is True
    assert audit.blocks_trace_verified_claim is True
    assert audit.blocks_product_behavior_claim is True
    assert audit.blocks_release_scope_claim is True
    assert audit.blocks_live_handoff_claim is True
    assert audit.blocks_live_binding_claim is True
    assert audit.blocks_ui_projection_claim is True
    assert audit.audit_passed_for_contract_scope is True
    assert audit.audit_passed_for_release_scope is False
    assert_readiness_audit_catches_fake_live_claims(audit)


def test_p2_5_20_exit_seal_and_contract_scope_demo() -> None:
    projection = build_cross_surface_handoff_section_projection()
    seal = build_cross_surface_handoff_section_seal(projection=projection)
    demo = build_cross_surface_handoff_contract_scope_demo()

    assert seal.section_id == "P2.5"
    assert seal.created_for_pack == "P2.5-D"
    assert seal.seal_status == CrossSurfaceHandoffSectionSealStatus.SEALED_CONTRACT_SCOPE
    assert seal.sealed_contract_scope is True
    assert seal.sealed_release_scope is False
    assert seal.claims_live is False
    assert seal.claims_trace_verified is False
    assert seal.claims_product_behavior is False
    assert seal.claims_release_scope is False
    assert_section_seal_is_not_release_seal(seal)

    assert demo.executes_handoff is False
    assert demo.switches_surface is False
    assert demo.executes_route is False
    assert demo.creates_ui is False
    assert demo.creates_live_binding is False
    assert demo.writes_memory is False
    assert demo.writes_trace is False
    assert demo.writes_storage is False
    assert demo.mutates_runtime is False
    assert_contract_scope_demo_is_not_runtime_demo(demo)
    assert json.loads(json.dumps(demo.to_canonical_dict()))


def test_p2_5_d_result_serializes_summary_and_next_candidate() -> None:
    result = build_p2_5_d_handoff_section_result()
    summary = render_cross_surface_handoff_section_summary(result)

    assert result.pack_id == "P2.5-D"
    assert result.dependency_pack == "P2.5-C"
    assert result.covered_checkpoints == P2_5_D_PACK_CHECKPOINT_IDS
    assert result.next_candidate == "P2.6-A"
    assert result.claims_live is False
    assert result.claims_trace_verified is False
    assert result.claims_release_scope is False
    assert result.claims_product_behavior is False
    assert "pack=P2.5-D" in summary
    assert "status=SEALED_CONTRACT_SCOPE" in summary
    assert "binding=READ_ONLY_CONTRACT_RENDER" in summary
    assert "next=P2.6-A" in summary
    assert "live=false" in summary
    assert json.loads(serialize_p2_5_d_result(result))
    assert_p2_5_d_does_not_start_future_work(result)


def test_projection_assertion_rejects_ui_claim() -> None:
    projection = build_cross_surface_handoff_section_projection()
    payload = projection.to_canonical_dict()
    payload["is_ui"] = True
    invalid = CrossSurfaceHandoffSectionProjection(**payload)
    with pytest.raises(AurelShellValidationError):
        assert_section_projection_is_not_ui(invalid)


def test_future_work_assertion_rejects_start_flag() -> None:
    result = build_p2_5_d_handoff_section_result()
    payload = result.to_canonical_dict()
    payload["starts_future_work"] = True
    invalid = P25DHandoffSectionResult(**payload)
    with pytest.raises(AurelShellValidationError):
        assert_p2_5_d_does_not_start_future_work(invalid)


def test_side_effect_proof_all_false() -> None:
    proof = build_p2_5_d_side_effect_proof()
    assert_p2_5_d_side_effects_all_false(proof)
    for field, value in proof.to_canonical_dict().items():
        assert value is False, field


def test_p2_5_d_side_effect_future_pack_flags_false() -> None:
    proof = build_p2_5_d_side_effect_proof()
    assert proof.p2_6_started is False
    assert proof.p2_7_started is False
    assert proof.p2_10_started is False
    assert proof.p2_13_started is False


def test_inventory_and_gate_build_standalone() -> None:
    gate = build_cross_surface_handoff_section_gate()
    inventory = build_cross_surface_handoff_contract_inventory()
    rollups = build_cross_surface_handoff_pack_rollup()
    assert gate.gate_status == CrossSurfaceHandoffSectionGateStatus.READY
    assert inventory.duplicates_source_of_truth is False
    assert len(rollups) == 4
    assert HANDOFF_SECTION_BINDING_UNAVAILABLE_REASON
