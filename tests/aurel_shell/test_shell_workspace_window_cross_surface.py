"""Tests for P2.3-C cross-surface window semantics contracts."""

from __future__ import annotations

import json

import pytest

from agentic_runtime.aurel_shell.contracts import AurelShellValidationError
from agentic_runtime.aurel_shell.surface_registry import CANONICAL_SURFACE_ORDER
from agentic_runtime.aurel_shell.workspace_state import (
    FloatingWindowKind,
    P2_3_A_PACK_ID,
    build_p2_3_a_workspace_state_foundation_result,
)
from agentic_runtime.aurel_shell.workspace_window_cross_surface import (
    AUDIT_REPAIR_001_PACK_ID,
    P2_3_B_PACK_ID,
    P2_3_C_DEPENDENCY_PACKS,
    P2_3_C_NEXT_PACK,
    P2_3_C_PACK_CHECKPOINT_IDS,
    P2_3_C_PACK_ID,
    CrossSurfaceWindowHandoffIntent,
    CrossSurfaceWindowHandoffReason,
    CrossSurfaceWindowProjectionResult,
    WindowCompatibilityKind,
    WindowConflictKind,
    WindowConflictSeverity,
    WindowDockingMode,
    WindowDockingRegion,
    assert_collision_contract_is_not_layout_engine,
    assert_compatibility_does_not_deny_permission,
    assert_compatibility_does_not_grant_permission,
    assert_compatibility_is_not_permission_enforcement,
    assert_conflict_state_is_not_conflict_resolver_runtime,
    assert_docking_intent_is_not_docking_ui,
    assert_p2_3_a_foundation_exists,
    assert_p2_3_b_projection_result_exists,
    assert_p2_3_c_depends_on_p2_3_b,
    assert_p2_3_c_does_not_start_p2_10,
    assert_p2_3_c_does_not_start_p2_13,
    assert_p2_3_c_does_not_start_p2_3_d,
    assert_p2_3_c_side_effects_all_false,
    assert_projection_result_is_not_frontend_state_store,
    assert_projection_result_is_not_product_behavior,
    assert_undocking_intent_is_not_drag_drop,
    assert_window_handoff_does_not_move_frontend_window,
    assert_window_handoff_does_not_switch_surface_runtime,
    assert_window_handoff_is_not_route_runtime,
    build_cross_surface_window_handoff_contract,
    build_cross_surface_window_handoff_contracts,
    build_cross_surface_window_projection_result,
    build_p2_3_c_side_effect_proof,
    build_p2_3_c_window_cross_surface_semantics_result,
    build_window_conflict_contract,
    build_window_docking_intent_contract,
    build_window_surface_compatibility_contract,
    serialize_p2_3_c_result,
)
from agentic_runtime.aurel_shell.workspace_window_semantics import (
    P2_3_B_REPORT_FILENAME,
    build_p2_3_b_workspace_window_semantics_result,
)


def test_module_imports_p2_3_c() -> None:
    import agentic_runtime.aurel_shell.workspace_window_cross_surface  # noqa: F401


def test_dependency_constants_and_p2_3_a_b_projection_reuse() -> None:
    foundation = build_p2_3_a_workspace_state_foundation_result()
    semantics = build_p2_3_b_workspace_window_semantics_result()
    result = build_p2_3_c_window_cross_surface_semantics_result()

    assert P2_3_C_PACK_ID == "P2.3-C"
    assert P2_3_C_PACK_CHECKPOINT_IDS == (
        "P2.3.11",
        "P2.3.12",
        "P2.3.13",
        "P2.3.14",
        "P2.3.15",
    )
    assert AUDIT_REPAIR_001_PACK_ID in P2_3_C_DEPENDENCY_PACKS
    assert P2_3_A_PACK_ID in P2_3_C_DEPENDENCY_PACKS
    assert P2_3_B_PACK_ID in P2_3_C_DEPENDENCY_PACKS
    assert P2_3_B_REPORT_FILENAME in result.p2_3_b_ref
    assert foundation.projection_seed.projection_hash in result.foundation_ref
    assert (
        semantics.workspace_focus_stack_projection_result.projection_hash
        in result.semantics_ref
    )
    assert_p2_3_a_foundation_exists(foundation)
    assert_p2_3_b_projection_result_exists(semantics)
    assert_p2_3_c_depends_on_p2_3_b(result)


def test_closed_world_enums_reject_unknown_values() -> None:
    with pytest.raises(ValueError):
        CrossSurfaceWindowHandoffIntent("ROUTE_EXECUTION")
    with pytest.raises(ValueError):
        CrossSurfaceWindowHandoffReason("BROWSER_NAVIGATION")
    with pytest.raises(ValueError):
        WindowDockingMode("DRAG_DROP_DOCK")
    with pytest.raises(ValueError):
        WindowDockingRegion("CSS_GRID_AREA")
    with pytest.raises(ValueError):
        WindowConflictKind("REAL_COLLISION")
    with pytest.raises(ValueError):
        WindowConflictSeverity("RUNTIME_BLOCK")
    with pytest.raises(ValueError):
        WindowCompatibilityKind("PERMISSION_GRANTED")


def test_p2_3_11_cross_surface_handoff_contract_semantics() -> None:
    foundation = build_p2_3_a_workspace_state_foundation_result()
    identity = foundation.identity_contracts[0]
    contract = build_cross_surface_window_handoff_contract(
        foundation=foundation,
        window_id=identity.window_id,
        handoff_intent=CrossSurfaceWindowHandoffIntent.HANDOFF_REQUESTED,
        handoff_reason=CrossSurfaceWindowHandoffReason.OPERATOR_INTENT_TRANSFER,
    )

    assert contract.window_id == identity.window_id
    assert contract.source_surface_id == identity.source_surface_id
    assert contract.target_surface_id == identity.target_surface_id
    assert contract.workspace_state_id == foundation.workspace_state.workspace_state_id
    assert contract.handoff_reason == (
        CrossSurfaceWindowHandoffReason.OPERATOR_INTENT_TRANSFER
    )
    assert contract.handoff_payload_refs == (identity.content_ref, identity.context_ref)
    assert contract.handoff_available is True
    assert contract.executes_route is False
    assert contract.switches_surface_runtime is False
    assert contract.moves_frontend_window is False
    assert contract.mutates_runtime is False
    assert contract.writes_memory is False
    assert contract.writes_trace is False
    assert_window_handoff_is_not_route_runtime(contract)
    assert_window_handoff_does_not_switch_surface_runtime(contract)
    assert_window_handoff_does_not_move_frontend_window(contract)
    assert json.loads(json.dumps(contract.to_canonical_dict()))


def test_p2_3_11_unavailable_handoff_requires_reason() -> None:
    contract = build_cross_surface_window_handoff_contract(handoff_available=False)
    assert contract.unavailable_reason
    payload = contract.to_canonical_dict()
    payload["unavailable_reason"] = ""
    invalid = type(contract)(**payload)
    with pytest.raises(AurelShellValidationError):
        assert_window_handoff_is_not_route_runtime(invalid)


def test_handoff_contracts_cover_p2_3_a_windows() -> None:
    foundation = build_p2_3_a_workspace_state_foundation_result()
    contracts = build_cross_surface_window_handoff_contracts(foundation=foundation)
    assert tuple(contract.window_id for contract in contracts) == tuple(
        contract.window_id for contract in foundation.identity_contracts
    )


def test_p2_3_12_docking_undocking_intent_contract_semantics() -> None:
    foundation = build_p2_3_a_workspace_state_foundation_result()
    identity = foundation.identity_contracts[1]
    contract = build_window_docking_intent_contract(
        foundation=foundation,
        window_id=identity.window_id,
        dock_region=WindowDockingRegion.FLOATING_REGION,
        docking_mode=WindowDockingMode.UNDOCK_REPRESENTED,
    )

    assert contract.window_id == identity.window_id
    assert contract.workspace_state_id == foundation.workspace_state.workspace_state_id
    assert contract.dock_target_surface_id == identity.owner_surface_id
    assert contract.dock_region == WindowDockingRegion.FLOATING_REGION
    assert contract.docking_mode == WindowDockingMode.UNDOCK_REPRESENTED
    assert contract.docking_reason
    assert contract.dock_available is True
    assert contract.creates_docking_ui is False
    assert contract.executes_drag_drop is False
    assert contract.changes_real_layout is False
    assert contract.mutates_runtime is False
    assert contract.writes_memory is False
    assert contract.writes_trace is False
    assert_docking_intent_is_not_docking_ui(contract)
    assert_undocking_intent_is_not_drag_drop(contract)
    assert json.loads(json.dumps(contract.to_canonical_dict()))


def test_p2_3_12_unavailable_docking_requires_reason() -> None:
    contract = build_window_docking_intent_contract(dock_available=False)
    assert contract.unavailable_reason
    payload = contract.to_canonical_dict()
    payload["unavailable_reason"] = ""
    invalid = type(contract)(**payload)
    with pytest.raises(AurelShellValidationError):
        assert_docking_intent_is_not_docking_ui(invalid)


def test_p2_3_13_conflict_collision_contract_semantics() -> None:
    foundation = build_p2_3_a_workspace_state_foundation_result()
    window_ids = tuple(contract.window_id for contract in foundation.identity_contracts)
    contract = build_window_conflict_contract(
        foundation=foundation,
        window_ids=window_ids[:2],
        conflict_kind=WindowConflictKind.STACK_ORDER_CONFLICT,
        severity=WindowConflictSeverity.DEFERRED_REVIEW,
        suggested_resolution_intent="operator_review_required_later",
    )

    assert contract.workspace_state_id == foundation.workspace_state.workspace_state_id
    assert contract.window_ids == window_ids[:2]
    assert contract.conflict_kind == WindowConflictKind.STACK_ORDER_CONFLICT
    assert contract.severity == WindowConflictSeverity.DEFERRED_REVIEW
    assert contract.conflict_reason
    assert contract.suggested_resolution_intent == "operator_review_required_later"
    assert contract.conflict_available is True
    assert contract.detects_real_collision is False
    assert contract.resolves_conflict_runtime is False
    assert contract.changes_layout is False
    assert contract.mutates_runtime is False
    assert contract.writes_memory is False
    assert contract.writes_trace is False
    assert_conflict_state_is_not_conflict_resolver_runtime(contract)
    assert_collision_contract_is_not_layout_engine(contract)
    assert json.loads(json.dumps(contract.to_canonical_dict()))


def test_p2_3_13_unavailable_conflict_requires_reason() -> None:
    contract = build_window_conflict_contract(conflict_available=False)
    assert contract.unavailable_reason
    payload = contract.to_canonical_dict()
    payload["unavailable_reason"] = ""
    invalid = type(contract)(**payload)
    with pytest.raises(AurelShellValidationError):
        assert_conflict_state_is_not_conflict_resolver_runtime(invalid)


def test_p2_3_14_window_surface_compatibility_contract_semantics() -> None:
    foundation = build_p2_3_a_workspace_state_foundation_result()
    identity = foundation.identity_contracts[2]
    contract = build_window_surface_compatibility_contract(
        foundation=foundation,
        window_id=identity.window_id,
        compatibility_kind=WindowCompatibilityKind.REQUIRES_FUTURE_PERMISSION_CHECK,
        requires_operator_review=True,
        requires_permission_check_later=True,
    )

    assert contract.window_kind == FloatingWindowKind.SYSTEM_STATUS_PANEL
    assert contract.source_surface_id == identity.source_surface_id
    assert contract.target_surface_id == identity.target_surface_id
    assert contract.allowed_as_contract is True
    assert contract.compatibility_kind == (
        WindowCompatibilityKind.REQUIRES_FUTURE_PERMISSION_CHECK
    )
    assert contract.compatibility_reason
    assert contract.requires_operator_review is True
    assert contract.requires_permission_check_later is True
    assert contract.enforces_permission is False
    assert contract.grants_permission is False
    assert contract.denies_permission is False
    assert contract.blocks_runtime is False
    assert contract.mutates_runtime is False
    assert_compatibility_is_not_permission_enforcement(contract)
    assert_compatibility_does_not_grant_permission(contract)
    assert_compatibility_does_not_deny_permission(contract)
    assert json.loads(json.dumps(contract.to_canonical_dict()))


def test_p2_3_15_projection_result_bundle_and_future_pack_boundaries() -> None:
    foundation = build_p2_3_a_workspace_state_foundation_result()
    semantics = build_p2_3_b_workspace_window_semantics_result()
    projection = build_cross_surface_window_projection_result(
        foundation=foundation,
        semantics=semantics,
    )

    assert projection.section_id == "P2.3"
    assert projection.created_for_pack == "P2.3-C"
    assert foundation.projection_seed.projection_hash in projection.foundation_ref
    assert (
        semantics.workspace_focus_stack_projection_result.projection_hash
        in projection.semantics_ref
    )
    assert projection.handoff_contracts
    assert projection.docking_intent_contracts
    assert projection.conflict_contracts
    assert projection.compatibility_contracts
    assert projection.side_effect_proof
    assert projection.next_pack == P2_3_C_NEXT_PACK
    assert projection.is_frontend_state_store is False
    assert projection.is_product_behavior is False
    assert projection.starts_p2_3_d is False
    assert projection.starts_p2_10 is False
    assert projection.starts_p2_13 is False
    assert_projection_result_is_not_frontend_state_store(projection)
    assert_projection_result_is_not_product_behavior(projection)
    assert_p2_3_c_does_not_start_p2_3_d(projection)
    assert_p2_3_c_does_not_start_p2_10(projection)
    assert_p2_3_c_does_not_start_p2_13(projection)
    assert json.loads(json.dumps(projection.to_canonical_dict()))


def test_p2_3_15_projection_assertions_reject_future_pack_starts() -> None:
    projection = build_cross_surface_window_projection_result()
    payload = projection.to_canonical_dict()
    payload["starts_p2_3_d"] = True
    invalid = CrossSurfaceWindowProjectionResult(**payload)
    with pytest.raises(AurelShellValidationError):
        assert_p2_3_c_does_not_start_p2_3_d(invalid)


def test_p2_3_c_side_effect_proof_all_false() -> None:
    proof = build_p2_3_c_side_effect_proof()
    assert_p2_3_c_side_effects_all_false(proof)
    for field, value in proof.to_canonical_dict().items():
        assert value is False, field


def test_p2_3_c_result_serializes_and_preserves_boundaries() -> None:
    result = build_p2_3_c_window_cross_surface_semantics_result()
    assert result.pack_id == "P2.3-C"
    assert result.section_id == "P2.3"
    assert result.next_pack == "P2.3-D"
    assert result.canonical_surface_ids == CANONICAL_SURFACE_ORDER
    assert len(result.checkpoint_reads) == 5
    assert all(
        result.checkpoint_statuses[checkpoint_id] == "DONE"
        for checkpoint_id in P2_3_C_PACK_CHECKPOINT_IDS
    )
    assert result.surface_taxonomy_drift is True
    assert result.cross_surface_window_projection_result.is_product_behavior is False
    assert result.cross_surface_window_projection_result.starts_p2_3_d is False
    assert result.cross_surface_window_projection_result.starts_p2_10 is False
    assert result.cross_surface_window_projection_result.starts_p2_13 is False
    assert all(surface_id in CANONICAL_SURFACE_ORDER for surface_id in result.canonical_surface_ids)
    assert_p2_3_c_depends_on_p2_3_b(result)
    assert json.loads(serialize_p2_3_c_result(result))
