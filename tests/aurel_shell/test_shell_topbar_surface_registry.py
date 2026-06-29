"""Tests for P2.1-A global topbar / surface registry foundation."""

from __future__ import annotations

import json

import pytest

from agentic_runtime.aurel_shell import (
    CANONICAL_SURFACE_ORDER,
    AurelShellValidationError,
    AurelSurfaceKind,
)
from agentic_runtime.aurel_shell.topbar import (
    P2_0_CONTRACT_SCOPE_SEAL,
    P2_1_A_DEPENDENCY_PACKS,
    P2_1_A_NEXT_PACK,
    P2_1_A_PACK_CHECKPOINT_IDS,
    P2_1_A_PACK_ID,
    P2_1_SECTION_ID,
    ActiveSurfaceActivationSource,
    TopbarSurfaceSwitchDisposition,
    assert_active_surface_exists_in_registry,
    assert_agent_cannot_switch_to_system,
    assert_local_navigation_is_deferred_to_p2_2,
    assert_p2_1_a_depends_on_p2_0_contract_scope_seal,
    assert_registry_does_not_activate_future_refs,
    assert_registry_entry_is_not_authority,
    assert_registry_has_no_duplicate_surface_ids,
    assert_registry_preserves_official_p2_0_surfaces,
    assert_settings_is_non_root_configuration,
    assert_switch_intent_does_not_execute_route,
    assert_switch_intent_does_not_grant_permission,
    assert_switch_intent_is_proposal_only,
    assert_system_is_operator_only_and_agent_blocked,
    assert_topbar_does_not_create_global_left_nav,
    assert_topbar_read_model_derives_from_registry,
    assert_topbar_read_model_is_not_live_ui,
    build_active_surface_state,
    build_default_topbar_surface_registry,
    build_global_topbar_read_model,
    build_p2_1_a_global_topbar_surface_registry_result,
    build_p2_1_a_handoff_gate,
    build_p2_1_a_side_effect_proof,
    build_p2_1_section_intake,
    build_surface_registry_entry,
    build_surface_taxonomy_drift_signal,
    propose_topbar_surface_switch,
    serialize_p2_1_a_result,
)


# ---------------------------------------------------------------------------
# Dispatch / dependency
# ---------------------------------------------------------------------------


def test_aurel_shell_module_imports_topbar() -> None:
    import agentic_runtime.aurel_shell.topbar  # noqa: F401


def test_p2_0_f_report_dependency_represented() -> None:
    gate = build_p2_1_a_handoff_gate()
    assert gate.depends_on_pack == "P2.0-F"
    assert gate.p2_0_f_report == "P2_0_F_PROJECTION_CLI_EXIT_SEAL.md"


def test_p2_0_contract_scope_seal_dependency_represented() -> None:
    gate = build_p2_1_a_handoff_gate()
    assert gate.requires_seal == P2_0_CONTRACT_SCOPE_SEAL
    assert_p2_1_a_depends_on_p2_0_contract_scope_seal(gate)


def test_p2_1_a_section_intake_builds() -> None:
    intake = build_p2_1_section_intake()
    assert intake.section_id == P2_1_SECTION_ID
    assert intake.pack_id == P2_1_A_PACK_ID
    assert intake.covered_checkpoints == P2_1_A_PACK_CHECKPOINT_IDS
    assert intake.depends_on_seal == P2_0_CONTRACT_SCOPE_SEAL


def test_p2_1_a_does_not_require_production_live_seal() -> None:
    intake = build_p2_1_section_intake()
    assert intake.production_live_scope_required is False


def test_p2_1_a_does_not_require_trace_verified_seal() -> None:
    intake = build_p2_1_section_intake()
    assert intake.trace_verified_scope_required is False


def test_p2_1_a_does_not_require_release_seal() -> None:
    intake = build_p2_1_section_intake()
    assert intake.release_scope_required is False


def test_p2_1_a_does_not_start_p2_2() -> None:
    intake = build_p2_1_section_intake()
    gate = build_p2_1_a_handoff_gate()
    assert intake.starts_p2_2 is False
    assert gate.starts_p2_2 is False


# ---------------------------------------------------------------------------
# P2.1.1 surface registry entry
# ---------------------------------------------------------------------------


def test_surface_registry_entry_builds() -> None:
    entry = build_surface_registry_entry("hq")
    assert entry.surface_id == "hq"
    assert entry.display_name == "HQ"
    assert entry.surface_kind == AurelSurfaceKind.HQ


def test_invalid_surface_id_rejected() -> None:
    with pytest.raises(AurelShellValidationError):
        build_surface_registry_entry("forum")


def test_system_protected_operator_only() -> None:
    entry = build_surface_registry_entry("system")
    assert_system_is_operator_only_and_agent_blocked(entry)
    assert entry.root_protected is True
    assert entry.operator_only is True


def test_settings_non_root() -> None:
    entry = build_surface_registry_entry("settings")
    assert_settings_is_non_root_configuration(entry)
    assert entry.settings_scope is True


def test_entry_does_not_grant_authority() -> None:
    entry = build_surface_registry_entry("hub")
    assert entry.grants_authority is False
    assert_registry_entry_is_not_authority(entry)


def test_entry_does_not_execute_route() -> None:
    entry = build_surface_registry_entry("ide")
    assert entry.executes_route is False


def test_entry_does_not_mutate_runtime() -> None:
    entry = build_surface_registry_entry("corp")
    assert entry.mutates_runtime is False


def test_entry_does_not_write_memory() -> None:
    entry = build_surface_registry_entry("aurel_cro")
    assert entry.writes_memory is False


def test_entry_does_not_write_trace() -> None:
    entry = build_surface_registry_entry("aurel_cro")
    assert entry.writes_trace is False


# ---------------------------------------------------------------------------
# P2.1.2 canonical registry builder
# ---------------------------------------------------------------------------


def test_default_topbar_surface_registry_builds() -> None:
    registry = build_default_topbar_surface_registry()
    assert len(registry.entries) == 7


def test_official_p2_0_surface_ids_preserved() -> None:
    registry = build_default_topbar_surface_registry()
    assert registry.official_surface_ids == CANONICAL_SURFACE_ORDER
    assert_registry_preserves_official_p2_0_surfaces(registry)


def test_canonical_order_stable() -> None:
    r1 = build_default_topbar_surface_registry()
    r2 = build_default_topbar_surface_registry()
    assert r1.canonical_surface_order == r2.canonical_surface_order == CANONICAL_SURFACE_ORDER


def test_no_duplicate_surface_ids() -> None:
    registry = build_default_topbar_surface_registry()
    assert_registry_has_no_duplicate_surface_ids(registry)


def test_logo_route_target_aurel_cro() -> None:
    registry = build_default_topbar_surface_registry()
    assert registry.logo_route_surface_id == "aurel_cro"


def test_protected_surfaces_include_system() -> None:
    registry = build_default_topbar_surface_registry()
    assert "system" in registry.protected_surface_ids


def test_settings_entry_is_non_root() -> None:
    registry = build_default_topbar_surface_registry()
    settings = next(e for e in registry.entries if e.surface_id == "settings")
    assert_settings_is_non_root_configuration(settings)


def test_forum_archivium_future_refs_not_active() -> None:
    registry = build_default_topbar_surface_registry()
    active_ids = {e.surface_id for e in registry.entries}
    assert "forum" not in active_ids
    assert "archivium" not in active_ids
    assert_registry_does_not_activate_future_refs(registry)
    assert "Forum" in registry.future_surface_refs


def test_taxonomy_drift_signal_produced() -> None:
    signal = build_surface_taxonomy_drift_signal()
    assert signal.detected is True
    assert signal.activated_as_registry_truth is False


def test_registry_grants_no_authority() -> None:
    registry = build_default_topbar_surface_registry()
    assert registry.grants_authority is False


def test_registry_executes_no_routes() -> None:
    registry = build_default_topbar_surface_registry()
    assert registry.executes_routes is False


def test_registry_does_not_mutate_runtime() -> None:
    registry = build_default_topbar_surface_registry()
    assert registry.mutates_runtime is False


# ---------------------------------------------------------------------------
# P2.1.3 active surface state
# ---------------------------------------------------------------------------


def test_active_surface_state_builds() -> None:
    state = build_active_surface_state()
    assert state.active_surface_id == "aurel_cro"


def test_default_active_surface_deterministic() -> None:
    s1 = build_active_surface_state()
    s2 = build_active_surface_state()
    assert s1.active_surface_id == s2.active_surface_id == "aurel_cro"


def test_valid_active_surface_accepted() -> None:
    state = build_active_surface_state("hq")
    assert state.active_surface_id == "hq"


def test_invalid_active_surface_blocked() -> None:
    with pytest.raises(AurelShellValidationError):
        build_active_surface_state("unknown_surface")


def test_system_active_state_protected() -> None:
    state = build_active_surface_state(
        "system",
        activation_source=ActiveSurfaceActivationSource.OPERATOR,
    )
    assert state.active_surface_id == "system"
    agent_state = build_active_surface_state(
        "system",
        activation_source=ActiveSurfaceActivationSource.AGENT,
    )
    assert agent_state.can_switch is False


def test_active_state_is_not_source_of_truth() -> None:
    state = build_active_surface_state()
    assert state.is_source_of_truth is False


def test_active_state_does_not_grant_authority() -> None:
    state = build_active_surface_state()
    assert state.authority_granted is False


def test_active_state_does_not_execute_route() -> None:
    state = build_active_surface_state()
    assert state.route_executed is False


def test_active_state_does_not_mutate_runtime() -> None:
    state = build_active_surface_state()
    assert state.runtime_mutated is False


def test_active_state_does_not_write_memory() -> None:
    state = build_active_surface_state()
    assert state.writes_memory is False


def test_active_state_does_not_write_trace() -> None:
    state = build_active_surface_state()
    assert state.writes_trace is False


def test_active_surface_exists_in_registry_assertion() -> None:
    registry = build_default_topbar_surface_registry()
    state = build_active_surface_state("ide", registry=registry)
    assert_active_surface_exists_in_registry(state, registry)


# ---------------------------------------------------------------------------
# P2.1.4 topbar switch intent
# ---------------------------------------------------------------------------


def test_topbar_switch_intent_builds() -> None:
    intent = propose_topbar_surface_switch("aurel_cro", "hq")
    assert intent.from_surface_id == "aurel_cro"
    assert intent.to_surface_id == "hq"


def test_normal_switch_intent_is_proposal_only() -> None:
    intent = propose_topbar_surface_switch("hq", "corp")
    assert intent.is_proposal is True
    assert_switch_intent_is_proposal_only(intent)


def test_unknown_target_blocked() -> None:
    intent = propose_topbar_surface_switch("hq", "forum")
    assert intent.disposition == TopbarSurfaceSwitchDisposition.BLOCKED


def test_agent_to_system_blocked() -> None:
    intent = propose_topbar_surface_switch(
        "hq",
        "system",
        requested_by="agent",
    )
    assert intent.disposition == TopbarSurfaceSwitchDisposition.BLOCKED
    assert_agent_cannot_switch_to_system(intent)


def test_operator_to_system_protected_not_executed() -> None:
    intent = propose_topbar_surface_switch(
        "hq",
        "system",
        requested_by="operator",
    )
    assert intent.disposition == TopbarSurfaceSwitchDisposition.PROTECTED_PROPOSAL
    assert intent.route_executed is False
    assert intent.requires_operator is True


def test_intent_does_not_grant_authority() -> None:
    intent = propose_topbar_surface_switch("hq", "ide")
    assert intent.authority_granted is False


def test_intent_does_not_grant_permission() -> None:
    intent = propose_topbar_surface_switch("hq", "ide")
    assert intent.permission_granted is False
    assert_switch_intent_does_not_grant_permission(intent)


def test_intent_does_not_execute_route() -> None:
    intent = propose_topbar_surface_switch("hq", "ide")
    assert intent.route_executed is False
    assert_switch_intent_does_not_execute_route(intent)


def test_intent_does_not_mutate_runtime() -> None:
    intent = propose_topbar_surface_switch("hq", "ide")
    assert intent.runtime_mutated is False


def test_intent_does_not_create_proof() -> None:
    intent = propose_topbar_surface_switch("hq", "ide")
    assert intent.proof_created is False


def test_intent_does_not_write_memory() -> None:
    intent = propose_topbar_surface_switch("hq", "ide")
    assert intent.writes_memory is False


def test_intent_does_not_write_trace() -> None:
    intent = propose_topbar_surface_switch("hq", "ide")
    assert intent.writes_trace is False


# ---------------------------------------------------------------------------
# P2.1.5 topbar read model
# ---------------------------------------------------------------------------


def test_topbar_read_model_builds() -> None:
    read_model = build_global_topbar_read_model()
    assert read_model.read_model_id == "global_topbar_read_model_default"


def test_topbar_read_model_derives_from_registry() -> None:
    registry = build_default_topbar_surface_registry()
    read_model = build_global_topbar_read_model(registry=registry)
    assert_topbar_read_model_derives_from_registry(read_model, registry)


def test_active_surface_included() -> None:
    read_model = build_global_topbar_read_model()
    assert read_model.active_surface.active_surface_id == "aurel_cro"


def test_visible_surfaces_match_registry() -> None:
    registry = build_default_topbar_surface_registry()
    read_model = build_global_topbar_read_model(registry=registry)
    visible_ids = {v.surface_id for v in read_model.visible_surfaces}
    assert visible_ids == set(registry.topbar_visible_surface_ids)


def test_protected_surfaces_listed() -> None:
    read_model = build_global_topbar_read_model()
    assert any(p.surface_id == "system" for p in read_model.protected_surfaces)


def test_settings_non_root_in_read_model() -> None:
    read_model = build_global_topbar_read_model()
    assert read_model.settings_entry.settings_scope is True
    assert read_model.settings_entry.root_protected is False


def test_logo_route_aurel_cro() -> None:
    read_model = build_global_topbar_read_model()
    assert read_model.logo_route.target.surface_id == "aurel_cro"
    assert read_model.global_navigation_policy.logo_route_surface_id == "aurel_cro"


def test_no_universal_left_nav() -> None:
    read_model = build_global_topbar_read_model()
    assert_topbar_does_not_create_global_left_nav(read_model)


def test_local_nav_deferred_to_p2_2() -> None:
    read_model = build_global_topbar_read_model()
    assert_local_navigation_is_deferred_to_p2_2(read_model)
    assert "p2_2" in read_model.local_navigation_boundary.lower()


def test_ui_unavailable_reason_present() -> None:
    read_model = build_global_topbar_read_model()
    ui = next(b for b in read_model.unavailable_bindings if b.binding_kind == "ui")
    assert ui.status == "UNAVAILABLE"
    assert "UNAVAILABLE_UI" in ui.unavailable_reason


def test_cli_tui_unavailable_reasons_present() -> None:
    read_model = build_global_topbar_read_model()
    kinds = {b.binding_kind for b in read_model.unavailable_bindings}
    assert "cli_live" in kinds
    assert "tui_live" in kinds


def test_read_model_is_not_live_ui() -> None:
    read_model = build_global_topbar_read_model()
    assert read_model.is_live_ui is False
    assert_topbar_read_model_is_not_live_ui(read_model)


def test_read_model_does_not_create_ui() -> None:
    read_model = build_global_topbar_read_model()
    assert read_model.creates_ui is False


def test_read_model_does_not_execute_routes() -> None:
    read_model = build_global_topbar_read_model()
    assert read_model.executes_routes is False


def test_read_model_does_not_grant_authority() -> None:
    read_model = build_global_topbar_read_model()
    assert read_model.grants_authority is False


def test_read_model_does_not_mutate_runtime() -> None:
    read_model = build_global_topbar_read_model()
    assert read_model.mutates_runtime is False


# ---------------------------------------------------------------------------
# Pack result
# ---------------------------------------------------------------------------


def test_pack_result_covers_p2_1_0_through_p2_1_5() -> None:
    result = build_p2_1_a_global_topbar_surface_registry_result()
    assert result.covered_checkpoints == P2_1_A_PACK_CHECKPOINT_IDS
    assert all(
        result.checkpoint_statuses[c] == "DONE" for c in P2_1_A_PACK_CHECKPOINT_IDS
    )


def test_pack_result_depends_on_p2_0_packs() -> None:
    result = build_p2_1_a_global_topbar_surface_registry_result()
    assert result.dependency_packs == P2_1_A_DEPENDENCY_PACKS


def test_pack_result_records_p2_0_contract_scope_seal() -> None:
    result = build_p2_1_a_global_topbar_surface_registry_result()
    assert result.p2_0_contract_scope_seal == P2_0_CONTRACT_SCOPE_SEAL


def test_pack_result_next_pack_p2_1_b() -> None:
    result = build_p2_1_a_global_topbar_surface_registry_result()
    assert result.next_pack == P2_1_A_NEXT_PACK == "P2.1-B"


def test_side_effect_proof_false_for_forbidden_work() -> None:
    proof = build_p2_1_a_side_effect_proof()
    assert proof.ui_created is False
    assert proof.frontend_component_created is False
    assert proof.route_runtime_created is False
    assert proof.permission_enforcement_created is False
    assert proof.p2_1_b_started is False
    assert proof.p2_2_started is False
    result = build_p2_1_a_global_topbar_surface_registry_result()
    assert result.side_effect_proof == proof


def test_pack_result_serializes() -> None:
    result = build_p2_1_a_global_topbar_surface_registry_result()
    payload = serialize_p2_1_a_result(result)
    parsed = json.loads(payload)
    assert parsed["pack_id"] == P2_1_A_PACK_ID
    assert parsed["result_hash"] == result.result_hash
