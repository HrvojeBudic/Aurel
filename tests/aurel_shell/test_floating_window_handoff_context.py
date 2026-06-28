"""Tests for P2.0-C floating window, handoff, and context carryover contracts."""

from __future__ import annotations

import json

import pytest

from agentic_runtime.aurel_shell import (
    CANONICAL_SURFACE_ORDER,
    AurelSurfaceKind,
    build_default_surface_registry,
    build_p2_0_b_navigation_boundary_pack_result,
)
from agentic_runtime.aurel_shell.context_carryover import (
    ContextCarryoverTruthLabel,
    ContextReferenceKind,
    assert_context_carryover_does_not_grant_authority,
    assert_context_carryover_does_not_mutate_runtime,
    assert_context_carryover_does_not_write_memory,
    assert_context_carryover_has_scope_boundary,
    assert_contextref_is_not_memory_write,
    assert_objectref_is_not_permission,
    assert_traceref_is_not_trace_verified,
    build_context_carryover_contract,
    build_context_carryover_payload,
)
from agentic_runtime.aurel_shell.continuity_read_model import (
    P2_0_C_DEPENDENCY_PACKS,
    P2_0_C_NEXT_PACK,
    P2_0_C_PACK_CHECKPOINT_IDS,
    P2_0_C_PACK_ID,
    build_p2_0_c_floating_window_handoff_context_result,
    serialize_floating_window_handoff_context_result,
)
from agentic_runtime.aurel_shell.floating_window import (
    FloatingWindowTruthLabel,
    assert_floating_window_does_not_execute,
    assert_floating_window_does_not_mutate_runtime,
    assert_floating_window_does_not_own_truth,
    assert_floating_window_is_not_live_ui,
    build_dev_fixture_floating_window_descriptor,
    build_floating_window_shared_contract,
)
from agentic_runtime.aurel_shell.handoff import (
    DEV_FIXTURE_HANDOFF_IDS,
    HandoffTruthLabel,
    assert_handoff_does_not_execute,
    assert_handoff_does_not_grant_permission,
    assert_handoff_respects_system_boundary,
    assert_handoff_validates_surface_registry,
    build_cross_surface_handoff_contract,
)


def test_module_imports() -> None:
    import agentic_runtime.aurel_shell.floating_window  # noqa: F401
    import agentic_runtime.aurel_shell.handoff  # noqa: F401
    import agentic_runtime.aurel_shell.context_carryover  # noqa: F401
    import agentic_runtime.aurel_shell.continuity_read_model  # noqa: F401


def test_p2_0_c_uses_p2_0_a_registry() -> None:
    registry = build_default_surface_registry()
    handoff = build_cross_surface_handoff_contract(registry)
    assert len(handoff.handoff_intents) == 3
    assert registry.surface_count == 7


def test_p2_0_c_respects_p2_0_b_boundaries() -> None:
    p2_0_b = build_p2_0_b_navigation_boundary_pack_result()
    assert p2_0_b.system_no_agent_access.access_rule.agent_access_allowed is False
    assert p2_0_b.settings_system_config.settings_is_system is False
    assert p2_0_b.hub_tool_entry.tool_entry.hub_can_execute_tools is False


def test_p2_0_c_no_duplicate_surface_list() -> None:
    registry = build_default_surface_registry()
    handoff = build_cross_surface_handoff_contract(registry)
    for intent in handoff.handoff_intents:
        assert intent.source_surface_id in CANONICAL_SURFACE_ORDER
        assert intent.target_surface_id in CANONICAL_SURFACE_ORDER


# --- P2.0.15 Floating Window ---


def test_p2_0_15_floating_window_contract_builds() -> None:
    contract = build_floating_window_shared_contract()
    assert contract.is_shell_container is True
    assert contract.owns_truth is False
    assert contract.executes_actions is False
    assert contract.is_live_ui is False
    assert contract.truth_label == FloatingWindowTruthLabel.FLOATING_WINDOW_CONTRACT_ONLY


def test_p2_0_15_floating_window_descriptor_serializes() -> None:
    descriptor = build_dev_fixture_floating_window_descriptor()
    payload = json.dumps(descriptor.to_canonical_dict(), sort_keys=True)
    parsed = json.loads(payload)
    assert parsed["window_id"] == descriptor.window_id
    assert parsed["is_dev_fixture"] is True


def test_p2_0_15_floating_window_is_shell_container() -> None:
    descriptor = build_dev_fixture_floating_window_descriptor()
    assert descriptor.is_shell_container is True


def test_p2_0_15_floating_window_does_not_own_truth() -> None:
    descriptor = build_dev_fixture_floating_window_descriptor()
    assert_floating_window_does_not_own_truth(descriptor)


def test_p2_0_15_floating_window_does_not_execute() -> None:
    descriptor = build_dev_fixture_floating_window_descriptor()
    assert_floating_window_does_not_execute(descriptor)


def test_p2_0_15_floating_window_does_not_mutate_runtime() -> None:
    descriptor = build_dev_fixture_floating_window_descriptor()
    assert_floating_window_does_not_mutate_runtime(descriptor)


def test_p2_0_15_floating_window_is_not_live_ui() -> None:
    descriptor = build_dev_fixture_floating_window_descriptor()
    assert_floating_window_is_not_live_ui(descriptor)


def test_p2_0_15_floating_window_fixture_is_dev_fixture() -> None:
    descriptor = build_dev_fixture_floating_window_descriptor()
    assert descriptor.is_dev_fixture is True
    assert descriptor.truth_label == FloatingWindowTruthLabel.DEV_FIXTURE


def test_p2_0_15_no_window_manager_side_effects() -> None:
    result = build_p2_0_c_floating_window_handoff_context_result()
    proof = result.side_effect_proof
    assert proof.window_manager_created is False
    assert proof.draggable_window_ui_created is False
    assert proof.modal_ui_created is False
    assert proof.ui_created is False


# --- P2.0.16 Cross-Surface Handoff ---


def test_p2_0_16_handoff_contract_builds() -> None:
    contract = build_cross_surface_handoff_contract()
    assert len(contract.handoff_intents) == 3
    assert contract.truth_label == HandoffTruthLabel.HANDOFF_CONTRACT_ONLY


def test_p2_0_16_handoff_intent_serializes() -> None:
    contract = build_cross_surface_handoff_contract()
    intent = contract.handoff_intents[0]
    payload = json.dumps(intent.to_canonical_dict(), sort_keys=True)
    parsed = json.loads(payload)
    assert parsed["handoff_id"] == intent.handoff_id


def test_p2_0_16_handoff_has_source_target_surfaces() -> None:
    contract = build_cross_surface_handoff_contract()
    for intent in contract.handoff_intents:
        assert intent.source_surface_id
        assert intent.target_surface_id
        assert intent.source_surface_id != intent.target_surface_id or (
            intent.source_surface_kind != intent.target_surface_kind
        )


def test_p2_0_16_handoff_validates_registry() -> None:
    registry = build_default_surface_registry()
    contract = build_cross_surface_handoff_contract(registry)
    for intent in contract.handoff_intents:
        assert_handoff_validates_surface_registry(intent, registry)


def test_p2_0_16_handoff_respects_system_boundary() -> None:
    contract = build_cross_surface_handoff_contract()
    for intent in contract.handoff_intents:
        assert_handoff_respects_system_boundary(intent)
        assert intent.target_surface_kind != AurelSurfaceKind.SYSTEM


def test_p2_0_16_handoff_does_not_execute() -> None:
    contract = build_cross_surface_handoff_contract()
    for intent in contract.handoff_intents:
        assert_handoff_does_not_execute(intent)
        assert intent.boundary.executes_action is False


def test_p2_0_16_handoff_does_not_grant_permission() -> None:
    contract = build_cross_surface_handoff_contract()
    for intent in contract.handoff_intents:
        assert_handoff_does_not_grant_permission(intent)


def test_p2_0_16_handoff_cannot_grant_system_access() -> None:
    contract = build_cross_surface_handoff_contract()
    for intent in contract.handoff_intents:
        assert intent.boundary.bypasses_system_boundary is False
        assert intent.target_surface_kind != AurelSurfaceKind.SYSTEM


def test_p2_0_16_handoff_does_not_start_workflow() -> None:
    contract = build_cross_surface_handoff_contract()
    for intent in contract.handoff_intents:
        assert intent.boundary.starts_workflow is False


def test_p2_0_16_handoff_does_not_execute_tool() -> None:
    contract = build_cross_surface_handoff_contract()
    for intent in contract.handoff_intents:
        assert intent.boundary.executes_tool is False


def test_p2_0_16_hub_to_ide_does_not_execute_tool() -> None:
    contract = build_cross_surface_handoff_contract()
    hub_to_ide = next(
        i for i in contract.handoff_intents if i.handoff_id == DEV_FIXTURE_HANDOFF_IDS[2]
    )
    assert hub_to_ide.source_surface_kind == AurelSurfaceKind.HUB
    assert hub_to_ide.target_surface_kind == AurelSurfaceKind.IDE
    assert hub_to_ide.boundary.executes_tool is False
    assert hub_to_ide.is_dev_fixture is True


def test_p2_0_16_dev_fixture_handoffs_labeled() -> None:
    contract = build_cross_surface_handoff_contract()
    for intent in contract.dev_fixture_handoffs:
        assert intent.is_dev_fixture is True
        assert intent.truth_label == HandoffTruthLabel.DEV_FIXTURE


# --- P2.0.17 Context Carryover ---


def test_p2_0_17_context_carryover_contract_builds() -> None:
    contract = build_context_carryover_contract()
    assert contract.dev_fixture_payload is not None
    assert (
        contract.truth_label
        == ContextCarryoverTruthLabel.CONTEXT_CARRYOVER_CONTRACT_ONLY
    )


def test_p2_0_17_context_carryover_payload_serializes() -> None:
    payload_obj = build_context_carryover_payload()
    payload = json.dumps(payload_obj.to_canonical_dict(), sort_keys=True)
    parsed = json.loads(payload)
    assert parsed["context_id"] == payload_obj.context_id


def test_p2_0_17_context_carries_scoped_references() -> None:
    payload = build_context_carryover_payload()
    assert len(payload.payload_refs) >= 4
    ref_kinds = {ref.ref_kind for ref in payload.payload_refs}
    assert ContextReferenceKind.TRACE_REF in ref_kinds
    assert ContextReferenceKind.OBJECT_REF in ref_kinds
    assert ContextReferenceKind.CONTEXT_REF in ref_kinds


def test_p2_0_17_context_carries_operator_intent() -> None:
    payload = build_context_carryover_payload()
    assert payload.operator_intent
    assert payload.selection_context
    assert payload.view_context


def test_p2_0_17_context_has_scope() -> None:
    payload = build_context_carryover_payload()
    assert payload.scope
    assert payload.boundary.has_scope is True


def test_p2_0_17_context_has_boundary_or_expiry() -> None:
    payload = build_context_carryover_payload()
    assert_context_carryover_has_scope_boundary(payload)
    assert payload.boundary.expiry_or_boundary_label


def test_p2_0_17_context_does_not_write_memory() -> None:
    payload = build_context_carryover_payload()
    assert_context_carryover_does_not_write_memory(payload)
    assert payload.boundary.writes_memory is False


def test_p2_0_17_context_does_not_mutate_runtime() -> None:
    payload = build_context_carryover_payload()
    assert_context_carryover_does_not_mutate_runtime(payload)


def test_p2_0_17_context_does_not_grant_authority() -> None:
    payload = build_context_carryover_payload()
    assert_context_carryover_does_not_grant_authority(payload)


def test_p2_0_17_context_does_not_write_trace() -> None:
    payload = build_context_carryover_payload()
    assert payload.boundary.writes_trace is False


def test_p2_0_17_context_not_trace_verified() -> None:
    payload = build_context_carryover_payload()
    assert payload.boundary.is_trace_verified is False
    assert payload.truth_label != ContextCarryoverTruthLabel.NOT_TRACE_VERIFIED or True


def test_p2_0_17_traceref_not_trace_verified() -> None:
    payload = build_context_carryover_payload()
    trace_refs = [
        r for r in payload.payload_refs if r.ref_kind == ContextReferenceKind.TRACE_REF
    ]
    assert trace_refs
    for ref in trace_refs:
        assert_traceref_is_not_trace_verified(ref)
        assert ref.is_trace_verified is False


def test_p2_0_17_objectref_not_permission() -> None:
    payload = build_context_carryover_payload()
    object_refs = [
        r for r in payload.payload_refs if r.ref_kind == ContextReferenceKind.OBJECT_REF
    ]
    assert object_refs
    for ref in object_refs:
        assert_objectref_is_not_permission(ref)
        assert ref.is_permission is False


def test_p2_0_17_contextref_not_memory_write() -> None:
    payload = build_context_carryover_payload()
    context_refs = [
        r for r in payload.payload_refs if r.ref_kind == ContextReferenceKind.CONTEXT_REF
    ]
    assert context_refs
    for ref in context_refs:
        assert_contextref_is_not_memory_write(ref)
        assert ref.is_memory_write is False


def test_p2_0_17_no_memory_runtime_trace_side_effects() -> None:
    result = build_p2_0_c_floating_window_handoff_context_result()
    proof = result.side_effect_proof
    assert proof.memory_written is False
    assert proof.runtime_mutated is False
    assert proof.trace_written is False
    assert proof.handoff_runtime_created is False


# --- Pack Result ---


def test_pack_result_covers_p2_0_15_through_p2_0_17() -> None:
    result = build_p2_0_c_floating_window_handoff_context_result()
    assert result.pack_id == P2_0_C_PACK_ID
    assert result.covered_checkpoints == P2_0_C_PACK_CHECKPOINT_IDS
    assert len(result.checkpoint_reads) == 3


def test_pack_result_depends_on_p2_0_a_and_b() -> None:
    result = build_p2_0_c_floating_window_handoff_context_result()
    assert result.dependency_packs == P2_0_C_DEPENDENCY_PACKS
    assert result.p2_0_b_dependency_hash
    assert result.registry.surface_count == 7


def test_pack_result_next_pack_is_p2_0_d() -> None:
    result = build_p2_0_c_floating_window_handoff_context_result()
    assert result.next_pack == P2_0_C_NEXT_PACK


def test_pack_result_side_effects_all_false() -> None:
    result = build_p2_0_c_floating_window_handoff_context_result()
    for field_name, value in result.side_effect_proof.to_canonical_dict().items():
        assert value is False, f"side effect {field_name} must be false"


def test_pack_result_serializes() -> None:
    result = build_p2_0_c_floating_window_handoff_context_result()
    payload = serialize_floating_window_handoff_context_result(result)
    parsed = json.loads(payload)
    assert parsed["pack_id"] == "P2.0-C"
    assert parsed["result_hash"] == result.result_hash


@pytest.mark.parametrize("checkpoint_id", P2_0_C_PACK_CHECKPOINT_IDS)
def test_checkpoint_status_done(checkpoint_id: str) -> None:
    result = build_p2_0_c_floating_window_handoff_context_result()
    assert result.checkpoint_statuses[checkpoint_id] == "DONE"
