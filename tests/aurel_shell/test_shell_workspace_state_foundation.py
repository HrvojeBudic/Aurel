"""Tests for P2.3-A floating windows / workspace state foundation."""

from __future__ import annotations

import json

import pytest

from agentic_runtime.aurel_shell.contracts import AurelShellValidationError
from agentic_runtime.aurel_shell.surface_registry import CANONICAL_SURFACE_ORDER
from agentic_runtime.aurel_shell.workspace_state import (
    AUDIT_REPAIR_001_PACK_ID,
    AUDIT_REPAIR_001_REPORT_FILENAME,
    P2_3_A_DEPENDENCY_PACKS,
    P2_3_A_NEXT_PACK,
    P2_3_A_PACK_CHECKPOINT_IDS,
    P2_3_A_PACK_ID,
    P2_3_A_PREVIOUS_COMMIT,
    P2_3_A_PREVIOUS_REPORT,
    P2_3_A_REQUIRED_PREVIOUS_READINESS,
    P2_3_A_REQUIRED_PREVIOUS_SEAL,
    P23SectionIntakeGate,
    FloatingWindowAvailability,
    FloatingWindowKind,
    FloatingWindowLifecycleState,
    LayerRole,
    OwnerScope,
    PlacementIntent,
    TruthBoundaryLabel,
    WorkspaceMode,
    assert_floating_window_identity_has_no_authority,
    assert_floating_window_identity_has_refs,
    assert_floating_window_identity_uses_canonical_surfaces,
    assert_lifecycle_has_no_runtime_effects,
    assert_lifecycle_unavailable_deferred_error_have_reasons,
    assert_p2_3_a_depends_on_audit_repair_001_and_p2_2_d,
    assert_p2_3_a_side_effects_all_false,
    assert_p2_3_section_gate_open_or_blocked_with_reasons,
    assert_p2_3_section_gate_does_not_start_implementation,
    assert_placement_intent_has_no_layout_runtime,
    assert_projection_seed_is_contract_only,
    assert_workspace_state_is_not_old_workspace_or_storage,
    assert_workspace_state_preserves_canonical_surfaces,
    build_floating_window_identity_contract,
    build_floating_window_identity_contracts,
    build_floating_window_lifecycle_contract,
    build_floating_window_placement_intent_contract,
    build_p2_3_a_side_effect_proof,
    build_p2_3_a_workspace_state_foundation_result,
    build_p2_3_section_intake_gate,
    build_shell_workspace_state_contract,
    build_workspace_state_projection_seed,
    serialize_p2_3_a_result,
)
from agentic_runtime.aurel_shell.local_navigation_integration_tail import (
    P2_2_D_PACK_ID,
    P2_2_D_REPORT_FILENAME,
)


def test_module_imports_p2_3_a() -> None:
    import agentic_runtime.aurel_shell.workspace_state  # noqa: F401


def test_p2_3_a_dependency_constants_and_gate_semantics() -> None:
    assert P2_3_A_PACK_ID == "P2.3-A"
    assert P2_3_A_PACK_CHECKPOINT_IDS == (
        "P2.3.0",
        "P2.3.1",
        "P2.3.2",
        "P2.3.3",
        "P2.3.4",
        "P2.3.5",
    )
    assert AUDIT_REPAIR_001_PACK_ID in P2_3_A_DEPENDENCY_PACKS
    assert P2_2_D_PACK_ID in P2_3_A_DEPENDENCY_PACKS
    gate = build_p2_3_section_intake_gate()
    assert gate.required_previous_seal == P2_3_A_REQUIRED_PREVIOUS_SEAL
    assert gate.required_previous_readiness == P2_3_A_REQUIRED_PREVIOUS_READINESS
    assert gate.previous_report_ref == P2_3_A_PREVIOUS_REPORT
    assert gate.previous_commit == P2_3_A_PREVIOUS_COMMIT
    assert gate.gate_open is True
    assert gate.blocked_reasons == ()
    assert gate.starts_implementation is False
    assert_p2_3_section_gate_does_not_start_implementation(gate)


def test_p2_3_0_intake_gate_serializes_and_validates_blocked_reasons() -> None:
    gate = build_p2_3_section_intake_gate()
    assert AUDIT_REPAIR_001_REPORT_FILENAME in gate.audit_repair_report_ref
    assert json.loads(json.dumps(gate.to_canonical_dict()))
    assert_p2_3_section_gate_open_or_blocked_with_reasons(gate)
    payload = gate.to_canonical_dict()
    payload["gate_open"] = False
    payload["blocked_reasons"] = ()
    invalid = P23SectionIntakeGate(**payload)
    with pytest.raises(AurelShellValidationError):
        assert_p2_3_section_gate_open_or_blocked_with_reasons(invalid)


def test_closed_world_enums_reject_unknown_values() -> None:
    with pytest.raises(ValueError):
        FloatingWindowKind("legacy_workspace_window")
    with pytest.raises(ValueError):
        WorkspaceMode("BROWSER_WORKSPACE")
    with pytest.raises(ValueError):
        FloatingWindowLifecycleState("MOUNTED")
    with pytest.raises(ValueError):
        FloatingWindowAvailability("LIVE")
    with pytest.raises(ValueError):
        PlacementIntent("CSS_GRID")
    with pytest.raises(ValueError):
        LayerRole("Z_INDEX_999")
    with pytest.raises(ValueError):
        OwnerScope("RUNTIME_OWNED")
    with pytest.raises(ValueError):
        TruthBoundaryLabel("SOURCE_OF_TRUTH")


def test_p2_3_1_identity_owner_source_target_content_context_refs() -> None:
    contract = build_floating_window_identity_contract(
        window_kind=FloatingWindowKind.CONTEXT_CARD,
        owner_surface_id="corp",
        source_surface_id="hq",
        target_surface_id="corp",
        content_ref="read_model:corp_context_card",
        context_ref="context:corp_context_card",
        title="CORP Context Card",
    )
    assert contract.window_kind == FloatingWindowKind.CONTEXT_CARD
    assert contract.owner_scope == OwnerScope.SURFACE_OWNED
    assert contract.owner_surface_id == "corp"
    assert contract.source_surface_id == "hq"
    assert contract.target_surface_id == "corp"
    assert contract.content_ref
    assert contract.context_ref
    assert contract.source_truth_boundary == TruthBoundaryLabel.READ_MODEL_ONLY
    assert_floating_window_identity_uses_canonical_surfaces(contract)
    assert_floating_window_identity_has_refs(contract)
    assert_floating_window_identity_has_no_authority(contract)


def test_p2_3_1_identity_contracts_cover_canonical_refs_without_new_registry() -> None:
    contracts = build_floating_window_identity_contracts()
    assert len(contracts) == 3
    for contract in contracts:
        assert contract.owner_surface_id in CANONICAL_SURFACE_ORDER
        assert contract.source_surface_id in CANONICAL_SURFACE_ORDER
        assert contract.target_surface_id in CANONICAL_SURFACE_ORDER
        assert contract.owns_truth is False
        assert contract.grants_authority is False
        assert contract.creates_ui is False
        assert json.loads(json.dumps(contract.to_canonical_dict()))


def test_p2_3_2_workspace_read_model_and_old_workspace_boundaries() -> None:
    identities = build_floating_window_identity_contracts()
    workspace = build_shell_workspace_state_contract(identity_contracts=identities)
    assert workspace.workspace_mode == WorkspaceMode.MULTI_WINDOW_READ_MODEL
    assert workspace.canonical_surface_ids == CANONICAL_SURFACE_ORDER
    assert workspace.floating_window_refs == tuple(c.window_id for c in identities)
    assert workspace.workspace_is_surface is False
    assert workspace.old_workspace_surface_activated is False
    assert workspace.uses_browser_storage is False
    assert workspace.uses_local_storage is False
    assert workspace.creates_route_runtime is False
    assert_workspace_state_preserves_canonical_surfaces(workspace)
    assert_workspace_state_is_not_old_workspace_or_storage(workspace)


def test_p2_3_3_lifecycle_unavailable_deferred_error_reason_requirements() -> None:
    identity = build_floating_window_identity_contract()
    declared = build_floating_window_lifecycle_contract(identity_contract=identity)
    assert declared.lifecycle_state == FloatingWindowLifecycleState.DECLARED
    assert declared.availability == FloatingWindowAvailability.CONTRACT_AVAILABLE
    assert_lifecycle_has_no_runtime_effects(declared)

    unavailable = build_floating_window_lifecycle_contract(
        identity_contract=identity,
        lifecycle_state=FloatingWindowLifecycleState.UNAVAILABLE,
    )
    assert unavailable.unavailable_reason
    assert unavailable.availability == FloatingWindowAvailability.UNAVAILABLE

    deferred = build_floating_window_lifecycle_contract(
        identity_contract=identity,
        lifecycle_state=FloatingWindowLifecycleState.DEFERRED,
    )
    assert deferred.deferred_to_pack == P2_3_A_NEXT_PACK
    assert deferred.unavailable_reason

    error = build_floating_window_lifecycle_contract(
        identity_contract=identity,
        lifecycle_state=FloatingWindowLifecycleState.ERROR_BOUNDARY,
    )
    assert error.error_boundary_reason
    assert error.unavailable_reason

    for contract in (declared, unavailable, deferred, error):
        assert_lifecycle_unavailable_deferred_error_have_reasons(contract)
        assert_lifecycle_has_no_runtime_effects(contract)


def test_p2_3_4_placement_intent_hints_without_layout_runtime() -> None:
    identity = build_floating_window_identity_contract(
        window_kind=FloatingWindowKind.INSPECTOR,
        owner_surface_id="ide",
        source_surface_id="hub",
        target_surface_id="ide",
    )
    placement = build_floating_window_placement_intent_contract(
        identity_contract=identity,
        placement_intent=PlacementIntent.SIDE_PANEL,
        layer_role=LayerRole.INSPECTION_LAYER,
        order_hint=20,
    )
    assert placement.placement_intent == PlacementIntent.SIDE_PANEL
    assert placement.layer_role == LayerRole.INSPECTION_LAYER
    assert placement.anchor_surface_id == "ide"
    assert placement.order_hint == 20
    assert placement.creates_css_layout is False
    assert placement.creates_z_index_runtime is False
    assert placement.creates_drag_drop is False
    assert_placement_intent_has_no_layout_runtime(placement)


def test_p2_3_5_projection_seed_bundle_and_next_pack() -> None:
    seed = build_workspace_state_projection_seed()
    assert seed.pack_id == "P2.3-A"
    assert seed.section_id == "P2.3"
    assert seed.canonical_surface_ids == CANONICAL_SURFACE_ORDER
    assert seed.next_pack == "P2.3-B"
    assert seed.projection_only is True
    assert seed.creates_ui is False
    assert seed.creates_api_server is False
    assert seed.creates_event_bus is False
    assert seed.mutates_runtime is False
    assert seed.writes_memory is False
    assert seed.writes_trace is False
    assert seed.identity_contract_refs
    assert seed.lifecycle_contract_refs
    assert seed.placement_intent_refs
    assert_projection_seed_is_contract_only(seed)
    assert json.loads(json.dumps(seed.to_canonical_dict()))


def test_p2_3_a_side_effect_proof_all_false() -> None:
    proof = build_p2_3_a_side_effect_proof()
    assert_p2_3_a_side_effects_all_false(proof)
    for field, value in proof.to_canonical_dict().items():
        assert value is False, field


def test_p2_3_a_result_envelope_serializes_and_preserves_boundaries() -> None:
    result = build_p2_3_a_workspace_state_foundation_result()
    assert result.pack_id == "P2.3-A"
    assert result.section_id == "P2.3"
    assert result.next_pack == "P2.3-B"
    assert result.canonical_surface_ids == CANONICAL_SURFACE_ORDER
    assert len(result.checkpoint_reads) == 6
    assert all(
        result.checkpoint_statuses[checkpoint_id] == "DONE"
        for checkpoint_id in P2_3_A_PACK_CHECKPOINT_IDS
    )
    assert AUDIT_REPAIR_001_REPORT_FILENAME in result.audit_repair_ref
    assert P2_2_D_REPORT_FILENAME in result.p2_2_d_ref
    assert result.surface_taxonomy_drift is True
    assert result.workspace_state.workspace_is_surface is False
    assert result.projection_seed.next_pack == "P2.3-B"
    assert_p2_3_a_depends_on_audit_repair_001_and_p2_2_d(result)
    assert json.loads(serialize_p2_3_a_result(result))
