"""Tests for P2.3-B workspace window semantics contracts."""

from __future__ import annotations

import json

import pytest

from agentic_runtime.aurel_shell.contracts import AurelShellValidationError
from agentic_runtime.aurel_shell.surface_registry import CANONICAL_SURFACE_ORDER
from agentic_runtime.aurel_shell.workspace_state import (
    P2_3_A_PACK_ID,
    P2_3_A_REPORT_FILENAME,
    build_p2_3_a_workspace_state_foundation_result,
)
from agentic_runtime.aurel_shell.workspace_window_semantics import (
    AUDIT_REPAIR_001_PACK_ID,
    P2_3_B_DEPENDENCY_PACKS,
    P2_3_B_NEXT_PACK,
    P2_3_B_PACK_CHECKPOINT_IDS,
    P2_3_B_PACK_ID,
    FloatingWindowFocusReason,
    FloatingWindowFocusSource,
    FloatingWindowGroupKind,
    FloatingWindowGroupScope,
    FloatingWindowLayerOrderHint,
    FloatingWindowRestoreMode,
    FloatingWindowRestoreSource,
    FloatingWindowStackRole,
    WorkspaceFocusStackProjectionResult,
    assert_active_window_is_not_browser_focus,
    assert_focus_intent_is_not_focus_manager,
    assert_group_is_not_desktop_workspace_ui,
    assert_group_is_not_frontend_tabs,
    assert_layer_order_is_not_layout_engine,
    assert_p2_3_a_projection_seed_exists,
    assert_p2_3_b_depends_on_p2_3_a,
    assert_p2_3_b_does_not_start_p2_10,
    assert_p2_3_b_does_not_start_p2_13,
    assert_p2_3_b_does_not_start_p2_3_c,
    assert_p2_3_b_side_effects_all_false,
    assert_projection_result_is_not_frontend_state_store,
    assert_projection_result_is_not_product_behavior,
    assert_restore_does_not_use_browser_storage,
    assert_restore_does_not_use_local_storage,
    assert_restore_is_not_persistence,
    assert_resume_state_is_not_memory_write,
    assert_stack_order_is_not_z_index_runtime,
    build_floating_window_focus_intent_contract,
    build_floating_window_focus_intent_contracts,
    build_floating_window_group_contract,
    build_floating_window_restore_contract,
    build_floating_window_stack_order_contract,
    build_p2_3_b_side_effect_proof,
    build_p2_3_b_workspace_window_semantics_result,
    build_workspace_focus_stack_projection_result,
    serialize_p2_3_b_result,
)
from agentic_runtime.aurel_shell.local_navigation_context import (
    AUDIT_REPAIR_001_REPORT_FILENAME,
)


def test_module_imports_p2_3_b() -> None:
    import agentic_runtime.aurel_shell.workspace_window_semantics  # noqa: F401


def test_dependency_constants_and_p2_3_a_projection_seed_reuse() -> None:
    foundation = build_p2_3_a_workspace_state_foundation_result()
    result = build_p2_3_b_workspace_window_semantics_result()

    assert P2_3_B_PACK_ID == "P2.3-B"
    assert P2_3_B_PACK_CHECKPOINT_IDS == (
        "P2.3.6",
        "P2.3.7",
        "P2.3.8",
        "P2.3.9",
        "P2.3.10",
    )
    assert AUDIT_REPAIR_001_PACK_ID in P2_3_B_DEPENDENCY_PACKS
    assert P2_3_A_PACK_ID in P2_3_B_DEPENDENCY_PACKS
    assert AUDIT_REPAIR_001_REPORT_FILENAME in result.audit_repair_ref
    assert P2_3_A_REPORT_FILENAME in result.p2_3_a_ref
    assert foundation.projection_seed.projection_seed_id in result.foundation_ref
    assert foundation.projection_seed.projection_hash in result.foundation_ref
    assert_p2_3_a_projection_seed_exists(foundation)
    assert_p2_3_b_depends_on_p2_3_a(result)


def test_closed_world_enums_reject_unknown_values() -> None:
    with pytest.raises(ValueError):
        FloatingWindowFocusSource("BROWSER_FOCUS")
    with pytest.raises(ValueError):
        FloatingWindowFocusReason("CLICK_HANDLER")
    with pytest.raises(ValueError):
        FloatingWindowStackRole("Z_INDEX_LAYER")
    with pytest.raises(ValueError):
        FloatingWindowLayerOrderHint("CSS_GRID")
    with pytest.raises(ValueError):
        FloatingWindowGroupKind("TABS_UI")
    with pytest.raises(ValueError):
        FloatingWindowGroupScope("DESKTOP_WORKSPACE")
    with pytest.raises(ValueError):
        FloatingWindowRestoreSource("LOCAL_STORAGE")
    with pytest.raises(ValueError):
        FloatingWindowRestoreMode("BROWSER_SESSION_RESTORE")


def test_p2_3_6_focus_intent_contract_semantics() -> None:
    foundation = build_p2_3_a_workspace_state_foundation_result()
    window_ids = tuple(c.window_id for c in foundation.identity_contracts)
    contract = build_floating_window_focus_intent_contract(
        foundation=foundation,
        window_id=window_ids[1],
        focus_source=FloatingWindowFocusSource.OPERATOR_INTENT,
        focus_reason=FloatingWindowFocusReason.OPERATOR_SELECTED_WINDOW,
        previous_active_window_id=window_ids[0],
    )

    assert contract.window_id == window_ids[1]
    assert contract.workspace_state_id == foundation.workspace_state.workspace_state_id
    assert contract.focus_source == FloatingWindowFocusSource.OPERATOR_INTENT
    assert contract.focus_reason == FloatingWindowFocusReason.OPERATOR_SELECTED_WINDOW
    assert contract.active_window_candidate == window_ids[1]
    assert contract.previous_active_window_id == window_ids[0]
    assert contract.focus_available is True
    assert contract.sets_browser_focus is False
    assert contract.activates_frontend_component is False
    assert contract.creates_focus_manager_runtime is False
    assert contract.mutates_runtime is False
    assert contract.writes_memory is False
    assert contract.writes_trace is False
    assert_focus_intent_is_not_focus_manager(contract)
    assert_active_window_is_not_browser_focus(contract)
    assert json.loads(json.dumps(contract.to_canonical_dict()))


def test_p2_3_6_unavailable_focus_requires_reason() -> None:
    contract = build_floating_window_focus_intent_contract(focus_available=False)
    assert contract.unavailable_reason
    payload = contract.to_canonical_dict()
    payload["unavailable_reason"] = ""
    invalid = type(contract)(**payload)
    with pytest.raises(AurelShellValidationError):
        assert_focus_intent_is_not_focus_manager(invalid)


def test_focus_intent_contracts_cover_p2_3_a_windows() -> None:
    foundation = build_p2_3_a_workspace_state_foundation_result()
    contracts = build_floating_window_focus_intent_contracts(foundation=foundation)
    assert tuple(c.window_id for c in contracts) == tuple(
        c.window_id for c in foundation.identity_contracts
    )
    assert contracts[1].previous_active_window_id == contracts[0].window_id


def test_p2_3_7_stack_layer_order_contract_semantics() -> None:
    foundation = build_p2_3_a_workspace_state_foundation_result()
    contract = build_floating_window_stack_order_contract(
        foundation=foundation,
        layer_order_hint=FloatingWindowLayerOrderHint.INSPECTION_LAYER,
    )

    assert contract.workspace_state_id == foundation.workspace_state.workspace_state_id
    assert contract.ordered_window_ids == tuple(
        c.window_id for c in foundation.identity_contracts
    )
    assert contract.active_window_id == contract.ordered_window_ids[0]
    assert contract.stack_role_map[contract.active_window_id] == "ACTIVE"
    assert contract.layer_order_hint == FloatingWindowLayerOrderHint.INSPECTION_LAYER
    assert "hint only" in contract.z_order_hint
    assert contract.ordering_reason
    assert contract.creates_z_index_runtime is False
    assert contract.creates_layout_engine is False
    assert contract.creates_css is False
    assert contract.mutates_runtime is False
    assert contract.writes_memory is False
    assert contract.writes_trace is False
    assert_stack_order_is_not_z_index_runtime(contract)
    assert_layer_order_is_not_layout_engine(contract)
    assert json.loads(json.dumps(contract.to_canonical_dict()))


def test_p2_3_8_group_contract_semantics() -> None:
    foundation = build_p2_3_a_workspace_state_foundation_result()
    contract = build_floating_window_group_contract(
        foundation=foundation,
        group_kind=FloatingWindowGroupKind.REVIEW_GROUP,
        group_scope=FloatingWindowGroupScope.CROSS_SURFACE_READ_MODEL,
    )

    assert contract.group_kind == FloatingWindowGroupKind.REVIEW_GROUP
    assert contract.group_scope == FloatingWindowGroupScope.CROSS_SURFACE_READ_MODEL
    assert contract.window_ids
    assert contract.primary_window_id == contract.window_ids[0]
    assert contract.surface_scope
    assert all(surface_id in CANONICAL_SURFACE_ORDER for surface_id in contract.surface_scope)
    assert contract.group_reason
    assert contract.group_available is True
    assert contract.creates_desktop_workspace is False
    assert contract.creates_frontend_group_ui is False
    assert contract.creates_tab_ui is False
    assert contract.mutates_runtime is False
    assert contract.writes_memory is False
    assert contract.writes_trace is False
    assert_group_is_not_desktop_workspace_ui(contract)
    assert_group_is_not_frontend_tabs(contract)
    assert json.loads(json.dumps(contract.to_canonical_dict()))


def test_p2_3_8_unavailable_group_requires_reason() -> None:
    contract = build_floating_window_group_contract(group_available=False)
    assert contract.unavailable_reason
    payload = contract.to_canonical_dict()
    payload["unavailable_reason"] = ""
    invalid = type(contract)(**payload)
    with pytest.raises(AurelShellValidationError):
        assert_group_is_not_desktop_workspace_ui(invalid)


def test_p2_3_9_restore_resume_contract_semantics() -> None:
    foundation = build_p2_3_a_workspace_state_foundation_result()
    group = build_floating_window_group_contract(foundation=foundation)
    contract = build_floating_window_restore_contract(
        foundation=foundation,
        groups=(group,),
        restore_source=FloatingWindowRestoreSource.OPERATOR_INTENT_CONTRACT,
        restore_mode=FloatingWindowRestoreMode.OPERATOR_INTENT_RESUME,
    )

    assert contract.restore_source == FloatingWindowRestoreSource.OPERATOR_INTENT_CONTRACT
    assert contract.restore_mode == FloatingWindowRestoreMode.OPERATOR_INTENT_RESUME
    assert contract.restored_window_ids == tuple(
        c.window_id for c in foundation.identity_contracts
    )
    assert contract.restored_active_window_id == contract.restored_window_ids[0]
    assert contract.restored_group_ids == (group.group_id,)
    assert contract.resume_reason
    assert contract.uses_local_storage is False
    assert contract.uses_browser_storage is False
    assert contract.writes_memory is False
    assert contract.writes_trace is False
    assert contract.mutates_runtime is False
    assert contract.executes_routes is False
    assert_restore_is_not_persistence(contract)
    assert_resume_state_is_not_memory_write(contract)
    assert_restore_does_not_use_local_storage(contract)
    assert_restore_does_not_use_browser_storage(contract)
    assert json.loads(json.dumps(contract.to_canonical_dict()))


def test_p2_3_9_unavailable_restore_requires_reason() -> None:
    contract = build_floating_window_restore_contract(restore_available=False)
    assert contract.unavailable_reason
    payload = contract.to_canonical_dict()
    payload["unavailable_reason"] = ""
    invalid = type(contract)(**payload)
    with pytest.raises(AurelShellValidationError):
        assert_restore_is_not_persistence(invalid)


def test_p2_3_10_projection_result_bundle_and_future_pack_boundaries() -> None:
    foundation = build_p2_3_a_workspace_state_foundation_result()
    projection = build_workspace_focus_stack_projection_result(foundation=foundation)

    assert projection.section_id == "P2.3"
    assert projection.created_for_pack == "P2.3-B"
    assert foundation.projection_seed.projection_hash in projection.foundation_ref
    assert projection.focus_intent_contracts
    assert projection.stack_order_contracts
    assert projection.window_group_contracts
    assert projection.restore_contracts
    assert projection.side_effect_proof
    assert projection.next_pack == P2_3_B_NEXT_PACK
    assert projection.is_frontend_state_store is False
    assert projection.is_product_behavior is False
    assert projection.starts_p2_3_c is False
    assert projection.starts_p2_10 is False
    assert projection.starts_p2_13 is False
    assert_projection_result_is_not_frontend_state_store(projection)
    assert_projection_result_is_not_product_behavior(projection)
    assert_p2_3_b_does_not_start_p2_3_c(projection)
    assert_p2_3_b_does_not_start_p2_10(projection)
    assert_p2_3_b_does_not_start_p2_13(projection)
    assert json.loads(json.dumps(projection.to_canonical_dict()))


def test_p2_3_10_projection_assertions_reject_future_pack_starts() -> None:
    projection = build_workspace_focus_stack_projection_result()
    payload = projection.to_canonical_dict()
    payload["starts_p2_3_c"] = True
    invalid = WorkspaceFocusStackProjectionResult(**payload)
    with pytest.raises(AurelShellValidationError):
        assert_p2_3_b_does_not_start_p2_3_c(invalid)


def test_p2_3_b_side_effect_proof_all_false() -> None:
    proof = build_p2_3_b_side_effect_proof()
    assert_p2_3_b_side_effects_all_false(proof)
    for field, value in proof.to_canonical_dict().items():
        assert value is False, field


def test_p2_3_b_result_serializes_and_preserves_boundaries() -> None:
    result = build_p2_3_b_workspace_window_semantics_result()
    assert result.pack_id == "P2.3-B"
    assert result.section_id == "P2.3"
    assert result.next_pack == "P2.3-C"
    assert result.canonical_surface_ids == CANONICAL_SURFACE_ORDER
    assert len(result.checkpoint_reads) == 5
    assert all(
        result.checkpoint_statuses[checkpoint_id] == "DONE"
        for checkpoint_id in P2_3_B_PACK_CHECKPOINT_IDS
    )
    assert result.surface_taxonomy_drift is True
    assert result.workspace_focus_stack_projection_result.is_product_behavior is False
    assert result.workspace_focus_stack_projection_result.starts_p2_3_c is False
    assert result.workspace_focus_stack_projection_result.starts_p2_10 is False
    assert result.workspace_focus_stack_projection_result.starts_p2_13 is False
    assert_p2_3_b_depends_on_p2_3_a(result)
    assert json.loads(serialize_p2_3_b_result(result))

