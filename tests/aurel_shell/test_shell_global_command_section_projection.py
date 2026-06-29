"""Tests for P2.4-D command palette section projection and seal."""

from __future__ import annotations

import json

import pytest

from agentic_runtime.aurel_shell.contracts import AurelShellValidationError
from agentic_runtime.aurel_shell.global_command_section_projection import (
    COMMAND_SECTION_BINDING_UNAVAILABLE_REASON,
    P2_4_C_COMMIT_REF,
    P2_4_D_DEPENDENCY_PACK,
    P2_4_D_NEXT_PACK,
    P2_4_D_PACK_CHECKPOINT_IDS,
    P2_4_D_PACK_ID,
    P2_4_D_REPORT_PATH,
    P2_4_D_SECTION_ID,
    GlobalCommandBindingMode,
    GlobalCommandBindingStatus,
    GlobalCommandCapabilityStatus,
    GlobalCommandPackStatus,
    GlobalCommandSectionAuditCategory,
    GlobalCommandSectionGateStatus,
    GlobalCommandSectionProjection,
    GlobalCommandSectionSealStatus,
    P24DCommandPaletteSectionResult,
    assert_audit_catches_forbidden_behavior,
    assert_binding_is_read_only_or_unavailable,
    assert_demo_is_contract_scope_only,
    assert_omni_evidence_is_ignored_by_operator_instruction,
    assert_p2_4_c_proposal_result_available,
    assert_p2_4_d_does_not_start_future_work,
    assert_p2_4_d_side_effects_all_false,
    assert_projection_is_not_live_ui,
    assert_section_gate_depends_on_p2_4_c,
    assert_section_seal_is_not_release,
    build_global_command_binding_status,
    build_global_command_contract_inventory,
    build_global_command_contract_scope_demo,
    build_global_command_docs_state_report_sync,
    build_global_command_pack_rollup,
    build_global_command_section_gate,
    build_global_command_section_projection,
    build_global_command_section_readiness_audit,
    build_global_command_section_seal,
    build_global_command_section_capabilities,
    build_global_command_unavailable_capabilities,
    build_p2_4_d_command_palette_section_result,
    build_p2_4_d_side_effect_proof,
    render_global_command_section_summary,
    serialize_p2_4_d_result,
)
from agentic_runtime.aurel_shell.global_command_proposal import (
    P2_4_C_REPORT_PATH,
    build_p2_4_c_command_proposal_result,
)
from agentic_runtime.aurel_shell.surface_registry import CANONICAL_SURFACE_ORDER


def test_module_imports_p2_4_d() -> None:
    import agentic_runtime.aurel_shell.global_command_section_projection  # noqa: F401


def test_gate_dependency_and_omni_policy() -> None:
    proposal = build_p2_4_c_command_proposal_result()
    result = build_p2_4_d_command_palette_section_result()
    gate = result.section_gate

    assert P2_4_D_PACK_ID == "P2.4-D"
    assert P2_4_D_SECTION_ID == "P2.4"
    assert P2_4_D_PACK_CHECKPOINT_IDS == (
        "P2.4.16",
        "P2.4.17",
        "P2.4.18",
        "P2.4.19",
        "P2.4.20",
    )
    assert P2_4_D_DEPENDENCY_PACK == "P2.4-C"
    assert gate.dependency_pack == "P2.4-C"
    assert gate.dependency_report_ref == P2_4_C_REPORT_PATH
    assert gate.dependency_commit_ref == P2_4_C_COMMIT_REF
    assert gate.repo_evidence_gate_passed is True
    assert gate.omni_evidence_required is False
    assert gate.omni_evidence_ignored_by_operator_instruction is True
    assert gate.dependency_proposal_result_ref.startswith(
        proposal.proposal_result.proposal_result_id
    )
    assert "active=true" in gate.dependency_no_execution_boundary_ref
    assert result.next_pack == P2_4_D_NEXT_PACK
    assert result.starts_future_work is False
    assert_p2_4_c_proposal_result_available(proposal)
    assert_section_gate_depends_on_p2_4_c(gate)
    assert_omni_evidence_is_ignored_by_operator_instruction(gate)


def test_closed_world_enums_reject_unknown_values() -> None:
    with pytest.raises(ValueError):
        GlobalCommandSectionGateStatus("OMNI_BLOCKED")
    with pytest.raises(ValueError):
        GlobalCommandPackStatus("LIVE")
    with pytest.raises(ValueError):
        GlobalCommandCapabilityStatus("PRODUCT_READY")
    with pytest.raises(ValueError):
        GlobalCommandBindingMode("EXECUTE")
    with pytest.raises(ValueError):
        GlobalCommandSectionSealStatus("RELEASE_SEALED")


def test_p2_4_16_section_projection_inventory_and_rollup() -> None:
    result = build_p2_4_d_command_palette_section_result()
    projection = result.section_projection
    inventory = result.contract_inventory
    rollups = result.pack_rollups

    assert projection.section_id == "P2.4"
    assert projection.created_for_pack == "P2.4-D"
    assert projection.official_section_name == "Command Palette / Global Commands"
    assert projection.section_status == GlobalCommandSectionGateStatus.READY
    assert projection.is_live_ui is False
    assert projection.is_source_of_truth is False
    assert projection.claims_live is False
    assert projection.claims_trace_verified is False
    assert projection.claims_product_behavior is False
    assert projection.claims_release_scope is False
    assert_projection_is_not_live_ui(projection)

    assert inventory.registry_contracts
    assert inventory.discovery_contracts
    assert inventory.proposal_contracts
    assert inventory.section_projection_contracts
    assert inventory.missing_contracts == ()
    assert inventory.duplicate_contracts_detected is False
    assert any("P2_4_A" in ref for ref in inventory.source_of_truth_refs)
    assert tuple(rollup.pack_id for rollup in rollups) == (
        "P2.4-A",
        "P2.4-B",
        "P2.4-C",
        "P2.4-D",
    )
    assert all(rollup.pack_status == GlobalCommandPackStatus.DONE for rollup in rollups)
    assert result.canonical_surface_ids == CANONICAL_SURFACE_ORDER
    assert json.loads(serialize_p2_4_d_result(result))


def test_p2_4_16_capabilities_and_unavailable_capabilities_represented() -> None:
    capabilities = build_global_command_section_capabilities()
    unavailable = build_global_command_unavailable_capabilities()

    names = {capability.name for capability in capabilities}
    assert "command registry foundation" in names
    assert "command discovery/result-set read model" in names
    assert "command proposal/no-execution boundary" in names
    assert "section projection/read model" in names
    assert "section readiness audit" in names
    assert "section contract-scope seal" in names
    assert all(
        capability.status
        in (
            GlobalCommandCapabilityStatus.AVAILABLE_CONTRACT_ONLY,
            GlobalCommandCapabilityStatus.READ_MODEL_ONLY,
        )
        for capability in capabilities
    )

    unavailable_names = {capability.name for capability in unavailable}
    assert "actual command palette UI" in unavailable_names
    assert "selection UI" in unavailable_names
    assert "preview panel UI" in unavailable_names
    assert "command execution" in unavailable_names
    assert "command router" in unavailable_names
    assert "approval activation" in unavailable_names
    assert "permission enforcement" in unavailable_names
    assert "Custos integration" in unavailable_names
    assert "trace write" in unavailable_names
    assert "TRACE_VERIFIED seal" in unavailable_names
    assert all(
        capability.status == GlobalCommandCapabilityStatus.UNAVAILABLE
        for capability in unavailable
    )
    assert all(capability.unavailable_reason for capability in unavailable)


def test_p2_4_17_binding_unavailable_and_non_executing() -> None:
    binding = build_global_command_binding_status()

    assert binding.binding_mode == GlobalCommandBindingMode.UNAVAILABLE
    assert binding.binding_available is False
    assert binding.binding_kind == "COMMAND_SECTION_BINDING_CONTRACT"
    assert binding.read_only is False
    assert binding.executes_commands is False
    assert binding.invokes_handlers is False
    assert binding.routes_commands is False
    assert binding.mutates_runtime is False
    assert binding.unavailable_reason == COMMAND_SECTION_BINDING_UNAVAILABLE_REASON
    assert_binding_is_read_only_or_unavailable(binding)
    assert json.loads(json.dumps(binding.to_canonical_dict()))


def test_p2_4_17_binding_assertion_rejects_execution_claim() -> None:
    binding = build_global_command_binding_status()
    payload = binding.to_canonical_dict()
    payload["executes_commands"] = True
    invalid = GlobalCommandBindingStatus(**payload)
    with pytest.raises(AurelShellValidationError):
        assert_binding_is_read_only_or_unavailable(invalid)


def test_p2_4_18_docs_state_report_sync_representation() -> None:
    sync = build_global_command_docs_state_report_sync()

    assert sync.section_id == "P2.4"
    assert sync.created_for_pack == "P2.4-D"
    assert sync.report_created is True
    assert sync.report_indexed is True
    assert sync.active_task_updated is True
    assert sync.roadmap_mirror_updated is True
    assert sync.state_updated is True
    assert sync.duplicate_agent_state_created is False
    assert sync.product_release_claim_created is False
    assert P2_4_D_REPORT_PATH == "agent/reports/P2_4_D_COMMAND_PALETTE_SECTION_SEAL.md"
    assert json.loads(json.dumps(sync.to_canonical_dict()))


def test_p2_4_19_readiness_audit_no_fake_product_gate() -> None:
    audit = build_global_command_section_readiness_audit()

    assert audit.findings
    categories = {finding.category for finding in audit.findings}
    assert GlobalCommandSectionAuditCategory.CONTRACT_COVERAGE in categories
    assert GlobalCommandSectionAuditCategory.NO_UI in categories
    assert GlobalCommandSectionAuditCategory.NO_EXECUTION in categories
    assert GlobalCommandSectionAuditCategory.NO_PERMISSION in categories
    assert GlobalCommandSectionAuditCategory.NO_TRACE_VERIFIED in categories
    assert GlobalCommandSectionAuditCategory.FUTURE_WORK in categories
    assert audit.passes_contract_scope is True
    assert audit.passes_product_scope is False
    assert audit.ui_available is False
    assert audit.execution_available is False
    assert audit.approval_available is False
    assert audit.permission_available is False
    assert audit.trace_verified_available is False
    assert audit.release_ready is False
    assert audit.authority_granted is False
    assert_audit_catches_forbidden_behavior(audit)
    assert json.loads(json.dumps(audit.to_canonical_dict()))


def test_p2_4_19_audit_assertion_rejects_fake_product_scope() -> None:
    audit = build_global_command_section_readiness_audit()
    payload = audit.to_canonical_dict()
    payload["passes_product_scope"] = True
    invalid = type(audit)(**payload)
    with pytest.raises(AurelShellValidationError):
        assert_audit_catches_forbidden_behavior(invalid)


def test_p2_4_20_exit_seal_and_contract_scope_demo() -> None:
    seal = build_global_command_section_seal()
    demo = build_global_command_contract_scope_demo(seal)

    assert seal.section_id == "P2.4"
    assert seal.created_for_pack == "P2.4-D"
    assert seal.seal_status == GlobalCommandSectionSealStatus.SEALED_CONTRACT_SCOPE
    assert seal.sealed_scope == "CONTRACT_READ_MODEL_ONLY"
    assert seal.sealed_as_product is False
    assert seal.sealed_as_live is False
    assert seal.sealed_as_trace_verified is False
    assert seal.sealed_as_release is False
    assert seal.next_pack == "P2.5-A"
    assert_section_seal_is_not_release(seal)

    assert demo.demo_kind == "CONTRACT_SCOPE_DEMO"
    assert demo.uses_dev_fixture is True
    assert demo.uses_live_runtime is False
    assert demo.executes_commands is False
    assert demo.creates_ui is False
    assert demo.mutates_runtime is False
    assert demo.writes_memory is False
    assert demo.writes_trace is False
    assert "serialize_p2_4_d_result()" in demo.output_refs
    assert_demo_is_contract_scope_only(demo)
    assert json.loads(json.dumps(demo.to_canonical_dict()))


def test_p2_4_d_result_serializes_summary_and_next_pack() -> None:
    result = build_p2_4_d_command_palette_section_result()
    summary = render_global_command_section_summary(result)

    assert result.pack_id == "P2.4-D"
    assert result.section_id == "P2.4"
    assert result.official_section_name == "Command Palette / Global Commands"
    assert result.dependency_pack == "P2.4-C"
    assert result.covered_checkpoints == P2_4_D_PACK_CHECKPOINT_IDS
    assert result.next_pack == "P2.5-A"
    assert result.claims_live is False
    assert result.claims_trace_verified is False
    assert result.claims_release_scope is False
    assert result.claims_product_behavior is False
    assert result.starts_future_work is False
    assert "pack=P2.4-D" in summary
    assert "status=SEALED_CONTRACT_SCOPE" in summary
    assert "binding=UNAVAILABLE" in summary
    assert "live=false" in summary
    assert "trace_verified=false" in summary
    assert json.loads(serialize_p2_4_d_result(result))
    assert_p2_4_d_does_not_start_future_work(result)


def test_projection_assertion_rejects_live_ui_claim() -> None:
    projection = build_global_command_section_projection()
    payload = projection.to_canonical_dict()
    payload["is_live_ui"] = True
    invalid = GlobalCommandSectionProjection(**payload)
    with pytest.raises(AurelShellValidationError):
        assert_projection_is_not_live_ui(invalid)


def test_future_work_assertion_rejects_start_flag() -> None:
    result = build_p2_4_d_command_palette_section_result()
    payload = result.to_canonical_dict()
    payload["starts_future_work"] = True
    invalid = P24DCommandPaletteSectionResult(**payload)
    with pytest.raises(AurelShellValidationError):
        assert_p2_4_d_does_not_start_future_work(invalid)


def test_side_effect_proof_all_false() -> None:
    proof = build_p2_4_d_side_effect_proof()
    assert_p2_4_d_side_effects_all_false(proof)
    for field, value in proof.to_canonical_dict().items():
        assert value is False, field


def test_p2_4_d_side_effect_future_pack_flags_false() -> None:
    proof = build_p2_4_d_side_effect_proof()
    assert proof.p2_5_started is False
    assert proof.p2_6_started is False
    assert proof.p2_7_started is False
    assert proof.p2_10_started is False
    assert proof.p2_13_started is False
