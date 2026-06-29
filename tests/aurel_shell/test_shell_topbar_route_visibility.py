"""Tests for P2.1-C topbar route visibility / interaction constraints."""

from __future__ import annotations

import json
from dataclasses import fields, is_dataclass

import pytest

from agentic_runtime.aurel_shell import AurelShellValidationError, CANONICAL_SURFACE_ORDER
from agentic_runtime.aurel_shell.topbar import (
    build_default_topbar_surface_registry,
    build_global_topbar_read_model,
)
from agentic_runtime.aurel_shell.topbar_route_visibility import (
    P2_1_A_REPORT_FILENAME,
    P2_1_B_REPORT_FILENAME,
    P2_1_C_NEXT_PACK,
    P2_1_C_PACK_CHECKPOINT_IDS,
    TopbarBlockedDeferredStateKind,
    TopbarInteractionKind,
    TopbarInteractionTruthBoundary,
    TopbarRegistryRefinementTruthBoundary,
    TopbarRouteVisibilityProjectionTruthBoundary,
    TopbarRouteVisibilityTruthBoundary,
    assert_p2_1_c_depends_on_p2_1_b,
    assert_projection_does_not_start_p2_1_d,
    assert_projection_does_not_start_p2_2,
    assert_route_visibility_extends_p2_1_a_b_read_models,
    build_p2_1_c_side_effect_proof,
    build_p2_1_c_topbar_route_visibility_result,
    build_topbar_blocked_deferred_state,
    build_topbar_blocked_deferred_states,
    build_topbar_interaction_constraint,
    build_topbar_interaction_constraints,
    build_topbar_registry_refinement_result,
    build_topbar_route_visibility_contract,
    build_topbar_route_visibility_contracts,
    build_topbar_route_visibility_projection,
    serialize_p2_1_c_result,
)
from agentic_runtime.aurel_shell.topbar_status import (
    TopbarSurfaceAvailabilityStatus,
    build_surface_availability_slot,
    build_surface_availability_slots,
    build_topbar_status_projection,
)


def _all_dataclass_bools_false(value: object) -> bool:
    assert is_dataclass(value)
    return all(
        getattr(value, field.name) is False
        for field in fields(value)
        if isinstance(getattr(value, field.name), bool)
    )


# ---------------------------------------------------------------------------
# Dispatch / dependency
# ---------------------------------------------------------------------------


def test_aurel_shell_module_imports_topbar_route_visibility() -> None:
    import agentic_runtime.aurel_shell.topbar_route_visibility  # noqa: F401


def test_p2_1_b_report_dependency_represented() -> None:
    result = build_p2_1_c_topbar_route_visibility_result()
    assert result.depends_on_pack == "P2.1-B"
    assert result.depends_on_reports == (
        P2_1_A_REPORT_FILENAME,
        P2_1_B_REPORT_FILENAME,
    )
    assert_p2_1_c_depends_on_p2_1_b(result)


def test_p2_1_a_registry_read_model_dependency_represented() -> None:
    projection = build_topbar_route_visibility_projection()
    assert projection.registry_ref == "topbar_surface_registry_default"
    assert projection.topbar_read_model_ref == "global_topbar_read_model_default"


def test_p2_1_b_status_projection_dependency_represented() -> None:
    projection = build_topbar_route_visibility_projection()
    assert projection.topbar_status_projection_ref == "topbar_status_projection_p2_1_b"


def test_p2_1_c_does_not_start_future_packs() -> None:
    projection = build_topbar_route_visibility_projection()
    assert projection.starts_p2_1_d is False
    assert projection.starts_p2_2 is False
    assert_projection_does_not_start_p2_1_d(projection)
    assert_projection_does_not_start_p2_2(projection)


# ---------------------------------------------------------------------------
# P2.1.11 route visibility
# ---------------------------------------------------------------------------


def test_route_visibility_contracts_build() -> None:
    contracts = build_topbar_route_visibility_contracts()
    assert tuple(contract.surface_id for contract in contracts) == CANONICAL_SURFACE_ORDER


def test_route_visibility_contracts_serialize() -> None:
    result = build_p2_1_c_topbar_route_visibility_result()
    payload = json.loads(serialize_p2_1_c_result(result))
    assert payload["pack_id"] == "P2.1-C"


def test_visible_routes_map_to_registry_surfaces() -> None:
    registry = build_default_topbar_surface_registry()
    contracts = build_topbar_route_visibility_contracts(registry=registry)
    assert {contract.surface_id for contract in contracts} == set(
        registry.topbar_visible_surface_ids
    )


def test_logo_route_is_aurel_cro() -> None:
    contracts = build_topbar_route_visibility_contracts()
    logo = [contract for contract in contracts if contract.is_default_logo_route]
    assert len(logo) == 1
    assert logo[0].surface_id == "aurel_cro"
    assert logo[0].display_name == "Aurel CRO"


def test_system_route_is_protected() -> None:
    system = next(
        contract
        for contract in build_topbar_route_visibility_contracts()
        if contract.surface_id == "system"
    )
    assert system.is_protected_route is True


def test_unavailable_route_requires_reason() -> None:
    with pytest.raises(AurelShellValidationError):
        build_topbar_route_visibility_contract(
            "hq",
            is_unavailable_route=True,
        )


def test_route_visibility_is_not_route_runtime_or_execution() -> None:
    for contract in build_topbar_route_visibility_contracts():
        assert contract.is_route_runtime is False
        assert contract.route_executed is False
        assert contract.creates_route_handler is False
        assert contract.creates_frontend_route is False
        assert contract.creates_cli_route is False
        assert contract.truth_label in {
            TopbarRouteVisibilityTruthBoundary.NOT_ROUTE_RUNTIME.value,
            TopbarRouteVisibilityTruthBoundary.CONTRACT_ONLY.value,
        }


# ---------------------------------------------------------------------------
# P2.1.12 interaction constraints
# ---------------------------------------------------------------------------


def test_interaction_constraints_build_and_serialize() -> None:
    constraints = build_topbar_interaction_constraints()
    assert constraints
    payload = constraints[0].to_canonical_dict()
    assert payload["interaction_kind"] == TopbarInteractionKind.SURFACE_SWITCH_INTENT.value


@pytest.mark.parametrize("kind", tuple(TopbarInteractionKind))
def test_allowed_interaction_kinds_accepted(kind: TopbarInteractionKind) -> None:
    constraint = build_topbar_interaction_constraint(
        f"interaction_{kind.value.lower()}",
        kind,
        "hq",
    )
    assert constraint.interaction_kind == kind


def test_invalid_interaction_kind_rejected() -> None:
    with pytest.raises(AurelShellValidationError):
        build_topbar_interaction_constraint("bad", "OPEN_COMMAND_PALETTE", "hq")


def test_surface_switch_kind_is_intent_only() -> None:
    constraint = build_topbar_interaction_constraint(
        "switch_hq",
        TopbarInteractionKind.SURFACE_SWITCH_INTENT,
        "hq",
    )
    assert constraint.allowed_as_intent is True
    assert constraint.truth_label == TopbarInteractionTruthBoundary.INTENT_ONLY.value


def test_protected_interaction_requires_operator() -> None:
    constraints = build_topbar_interaction_constraints()
    protected = next(c for c in constraints if c.interaction_id == "open_protected_info_system")
    assert protected.requires_operator is True
    assert protected.surface_id == "system"


def test_blocked_interaction_requires_reason() -> None:
    with pytest.raises(AurelShellValidationError):
        build_topbar_interaction_constraint(
            "blocked_without_reason",
            TopbarInteractionKind.SHOW_BLOCKED_REASON,
            "system",
            disposition="BLOCKED_WITH_REASON",
            allowed_as_intent=False,
        )


def test_deferred_to_p2_2_p2_3_p2_4_represented() -> None:
    constraints = build_topbar_interaction_constraints()
    assert any(c.deferred_to_section == "P2.2" for c in constraints)
    assert any(c.deferred_to_section == "P2.3" for c in constraints)
    assert any(c.deferred_to_section == "P2.4" for c in constraints)


def test_interaction_constraints_do_not_execute_or_grant() -> None:
    for constraint in build_topbar_interaction_constraints():
        assert constraint.executes_action is False
        assert constraint.grants_authority is False
        assert constraint.permission_granted is False
        assert constraint.route_executed is False
        assert constraint.mutates_runtime is False
        assert constraint.creates_ui_handler is False
        assert constraint.creates_keyboard_shortcut is False


# ---------------------------------------------------------------------------
# P2.1.13 registry refinement
# ---------------------------------------------------------------------------


def test_registry_refinement_result_builds_and_serializes() -> None:
    result = build_topbar_registry_refinement_result()
    payload = result.to_canonical_dict()
    assert payload["refinement_id"] == "topbar_registry_refinement_p2_1_c"
    assert result.truth_label == (
        TopbarRegistryRefinementTruthBoundary.METADATA_CONSISTENCY_ONLY.value
    )


def test_route_and_status_metadata_maps_to_registry() -> None:
    result = build_topbar_registry_refinement_result()
    assert result.all_visible_routes_map_to_registry_surfaces is True
    assert result.all_status_slots_map_to_registry_surfaces is True


def test_missing_unavailable_reason_fails() -> None:
    registry = build_default_topbar_surface_registry()
    status_slots = (
        build_surface_availability_slot(
            "hq",
            registry=registry,
            availability_status=TopbarSurfaceAvailabilityStatus.UNAVAILABLE_BACKEND_MISSING,
            unavailable_reason="UNAVAILABLE_BACKEND_MISSING: needed for setup",
        ),
        *tuple(
            slot
            for slot in build_surface_availability_slots(registry=registry)
            if slot.surface_id != "hq"
        ),
    )
    status_projection = build_topbar_status_projection(
        registry=registry,
        surface_availability_slots=status_slots,
    )
    broken_contract = build_topbar_route_visibility_contract(
        "hq",
        registry=registry,
        is_unavailable_route=False,
    )
    object.__setattr__(broken_contract, "is_unavailable_route", True)
    object.__setattr__(broken_contract, "unavailable_reason", "")
    with pytest.raises(AurelShellValidationError):
        build_topbar_registry_refinement_result(
            registry=registry,
            status_projection=status_projection,
            route_visibility_contracts=(broken_contract,),
        )


def test_missing_deferred_target_fails() -> None:
    state = build_topbar_blocked_deferred_state(
        "deferred_target_setup",
        TopbarBlockedDeferredStateKind.DEFERRED_TO_P2_2,
        "hq",
        TopbarInteractionKind.SHOW_ROUTE_VISIBILITY,
        reason="setup target before mutation",
        deferred_to_section="P2.2",
        deferred_to_pack="P2.2",
    )
    object.__setattr__(state, "deferred_to_section", "")
    with pytest.raises(AurelShellValidationError):
        build_topbar_registry_refinement_result(blocked_deferred_states=(state,))


def test_registry_refinement_preserves_logo_settings_system_future_refs() -> None:
    result = build_topbar_registry_refinement_result()
    assert result.logo_route_remains_aurel_cro is True
    assert result.settings_remains_non_root is True
    assert result.system_remains_protected is True
    assert result.future_refs_remain_inactive is True


def test_registry_refinement_does_not_rewrite_or_mutate_truth() -> None:
    result = build_topbar_registry_refinement_result()
    assert result.roadmap_rewritten is False
    assert result.registry_truth_mutated is False
    assert result.surface_promoted is False
    assert result.source_of_truth_created is False


# ---------------------------------------------------------------------------
# P2.1.14 blocked/deferred states
# ---------------------------------------------------------------------------


def test_blocked_deferred_states_build_and_serialize() -> None:
    states = build_topbar_blocked_deferred_states()
    assert states
    assert states[0].to_canonical_dict()["state_kind"] == "BLOCKED"


@pytest.mark.parametrize("kind", tuple(TopbarBlockedDeferredStateKind))
def test_allowed_state_kinds_accepted(kind: TopbarBlockedDeferredStateKind) -> None:
    kwargs = {}
    if kind.name.startswith("DEFERRED"):
        section = kind.value.replace("DEFERRED_TO_", "").replace("_", ".")
        kwargs = {"deferred_to_section": section, "deferred_to_pack": section}
    state = build_topbar_blocked_deferred_state(
        f"state_{kind.value.lower()}",
        kind,
        "hq",
        TopbarInteractionKind.SHOW_STATUS_DETAILS,
        reason="reason required",
        **kwargs,
    )
    assert state.state_kind == kind


def test_invalid_state_kind_rejected() -> None:
    with pytest.raises(AurelShellValidationError):
        build_topbar_blocked_deferred_state(
            "bad_state",
            "WAITING",
            "hq",
            TopbarInteractionKind.SHOW_STATUS_DETAILS,
            reason="bad",
        )


def test_blocked_and_unavailable_without_reason_rejected() -> None:
    with pytest.raises(AurelShellValidationError):
        build_topbar_blocked_deferred_state(
            "blocked_without_reason",
            TopbarBlockedDeferredStateKind.BLOCKED,
            "system",
            TopbarInteractionKind.SHOW_BLOCKED_REASON,
            reason="",
        )
    with pytest.raises(AurelShellValidationError):
        build_topbar_blocked_deferred_state(
            "unavailable_without_reason",
            TopbarBlockedDeferredStateKind.UNAVAILABLE,
            "hq",
            TopbarInteractionKind.SHOW_UNAVAILABLE_REASON,
            reason="",
        )


def test_blocked_deferred_states_include_p2_2_p2_3_p2_4() -> None:
    states = build_topbar_blocked_deferred_states()
    assert any(state.deferred_to_section == "P2.2" for state in states)
    assert any(state.deferred_to_section == "P2.3" for state in states)
    assert any(state.deferred_to_section == "P2.4" for state in states)


def test_error_contract_only_is_not_runtime_failure() -> None:
    state = next(
        state
        for state in build_topbar_blocked_deferred_states()
        if state.state_kind == TopbarBlockedDeferredStateKind.ERROR_CONTRACT_ONLY
    )
    assert state.is_error is True
    assert state.is_runtime_failure is False
    assert state.runtime_failure_proven is False


def test_state_does_not_create_notification_or_workflow() -> None:
    for state in build_topbar_blocked_deferred_states():
        assert state.notification_created is False
        assert state.workflow_started is False


# ---------------------------------------------------------------------------
# P2.1.15 projection/result
# ---------------------------------------------------------------------------


def test_route_visibility_projection_builds_and_serializes() -> None:
    projection = build_topbar_route_visibility_projection()
    assert projection.projection_id == "topbar_route_visibility_projection_p2_1_c"
    assert json.loads(
        serialize_p2_1_c_result(build_p2_1_c_topbar_route_visibility_result())
    )


def test_projection_references_p2_1_a_b_read_models() -> None:
    registry = build_default_topbar_surface_registry()
    read_model = build_global_topbar_read_model(registry=registry)
    status_projection = build_topbar_status_projection(
        registry=registry,
        topbar_read_model=read_model,
    )
    assert_route_visibility_extends_p2_1_a_b_read_models(
        read_model,
        status_projection,
        registry,
    )


def test_projection_includes_all_required_groups() -> None:
    projection = build_topbar_route_visibility_projection()
    assert projection.route_visibility_contracts
    assert projection.interaction_constraints
    assert projection.registry_refinement_result
    assert projection.blocked_deferred_states
    assert projection.unavailable_bindings
    assert all(binding.unavailable_reason for binding in projection.unavailable_bindings)


def test_pack_result_covers_p2_1_11_to_p2_1_15_and_next_pack() -> None:
    result = build_p2_1_c_topbar_route_visibility_result()
    assert result.covered_checkpoints == P2_1_C_PACK_CHECKPOINT_IDS
    assert result.checkpoint_statuses == {
        checkpoint: "DONE" for checkpoint in P2_1_C_PACK_CHECKPOINT_IDS
    }
    assert result.next_pack == P2_1_C_NEXT_PACK


def test_side_effect_proof_false_for_forbidden_work() -> None:
    proof = build_p2_1_c_side_effect_proof()
    assert _all_dataclass_bools_false(proof)


def test_projection_has_no_live_ui_runtime_local_nav_command_palette_or_authority() -> None:
    projection = build_topbar_route_visibility_projection()
    assert projection.is_live_ui is False
    assert projection.creates_ui is False
    assert projection.creates_route_runtime is False
    assert projection.creates_frontend_route is False
    assert projection.creates_local_navigation is False
    assert projection.creates_command_palette is False
    assert projection.executes_routes is False
    assert projection.grants_authority is False
    assert projection.permission_granted is False
    assert projection.mutates_runtime is False
    assert projection.writes_memory is False
    assert projection.writes_trace is False
    assert projection.truth_boundary[0] == (
        TopbarRouteVisibilityProjectionTruthBoundary.PROJECTION_ONLY
    )


def test_pack_result_truth_boundaries_not_live_or_trace_verified() -> None:
    result = build_p2_1_c_topbar_route_visibility_result()
    assert result.is_live is False
    assert result.is_trace_verified is False
    assert TopbarRouteVisibilityTruthBoundary.ROUTE_VISIBILITY_ONLY.value in (
        result.truth_labels
    )
