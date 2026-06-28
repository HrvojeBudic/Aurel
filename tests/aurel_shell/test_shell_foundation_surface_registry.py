"""Tests for P2.0-A shell foundation and surface registry."""

from __future__ import annotations

import json

import pytest

from agentic_runtime.aurel_shell import (
    AUREL_SHELL_NEXT_PACK_ID,
    AUREL_SHELL_PACK_CHECKPOINT_IDS,
    AUREL_SHELL_PACK_TASK_ID,
    AurelShellTruthLabel,
    AurelSurfaceKind,
    CANONICAL_SURFACE_ORDER,
    OLD_SURFACE_TAXONOMY,
    assert_hub_is_not_execution_authority,
    assert_ide_is_not_runtime_authority,
    assert_no_old_surface_taxonomy_active,
    assert_settings_is_non_root,
    assert_settings_is_not_system,
    assert_shell_boundary_invariants,
    assert_surface_registry_has_exactly_v5_5_surfaces,
    assert_system_is_operator_only,
    build_aurel_shell_contract,
    build_default_surface_registry,
    build_p2_0_a_shell_foundation_surface_registry_result,
    build_surface_contract,
    build_surface_registry_snapshot,
    detect_surface_taxonomy_drift,
    serialize_aurel_shell_contract,
    serialize_surface_registry_snapshot,
)


def test_module_imports() -> None:
    import agentic_runtime.aurel_shell.contracts  # noqa: F401
    import agentic_runtime.aurel_shell.surface_registry  # noqa: F401
    import agentic_runtime.aurel_shell.read_model  # noqa: F401


def test_p2_0_0_shell_contract_builds_and_serializes() -> None:
    contract = build_aurel_shell_contract()
    assert contract.shell_id == "aurel_shell"
    assert contract.display_name == "AurelShell"
    assert contract.shell_contract_hash
    payload = serialize_aurel_shell_contract(contract)
    parsed = json.loads(payload)
    assert parsed["shell_id"] == "aurel_shell"
    assert parsed["truth_label"] == AurelShellTruthLabel.CONTRACT_ONLY.value


def test_p2_0_0_shell_truth_label_is_not_live() -> None:
    contract = build_aurel_shell_contract()
    assert contract.truth_label != AurelShellTruthLabel.NOT_LIVE
    assert contract.truth_label.value not in {"LIVE", "UI_LIVE", "ROUTE_LIVE"}


def test_p2_0_0_shell_has_no_ui_product_claim() -> None:
    contract = build_aurel_shell_contract()
    side_effects = contract.side_effects
    assert side_effects.ui_created is False
    assert side_effects.route_created is False
    assert "no_product_ui" in contract.non_goals


def test_p2_0_1_shell_boundary_operator_command_skin() -> None:
    contract = build_aurel_shell_contract()
    boundary = contract.boundary
    assert boundary.reveals_state is True
    assert boundary.owns_truth is False
    assert boundary.executes_commands is False
    assert boundary.grants_permission is False
    assert boundary.mutates_runtime is False
    assert_shell_boundary_invariants(contract)


def test_registry_has_exactly_seven_surfaces() -> None:
    registry = build_default_surface_registry()
    assert registry.surface_count == 7
    assert len(registry.surfaces) == 7
    assert_surface_registry_has_exactly_v5_5_surfaces(registry)


def test_registry_order_and_ids_stable() -> None:
    first = build_default_surface_registry()
    second = build_default_surface_registry()
    assert first.canonical_surface_ids == second.canonical_surface_ids
    assert first.canonical_surface_ids == CANONICAL_SURFACE_ORDER
    assert first.registry_hash == second.registry_hash


def test_registry_no_duplicate_or_missing_surfaces() -> None:
    registry = build_default_surface_registry()
    ids = [surface.surface_id for surface in registry.surfaces]
    assert len(ids) == len(set(ids))
    assert set(ids) == set(CANONICAL_SURFACE_ORDER)


def test_registry_excludes_old_surface_taxonomy() -> None:
    registry = build_default_surface_registry()
    active_names = {surface.display_name for surface in registry.surfaces}
    active_ids = {surface.surface_id for surface in registry.surfaces}
    for old in OLD_SURFACE_TAXONOMY:
        assert old not in active_names
        normalized = old.lower().replace("-", "_").replace(" ", "_")
        assert normalized not in active_ids
    assert_no_old_surface_taxonomy_active(registry)


@pytest.mark.parametrize(
    "kind,display_name",
    [
        (AurelSurfaceKind.AUREL_CRO, "Aurel CRO"),
        (AurelSurfaceKind.HQ, "HQ"),
        (AurelSurfaceKind.CORP, "CORP"),
        (AurelSurfaceKind.HUB, "HUB"),
        (AurelSurfaceKind.IDE, "IDE"),
        (AurelSurfaceKind.SYSTEM, "SYSTEM"),
        (AurelSurfaceKind.SETTINGS, "Settings"),
    ],
)
def test_surface_display_names_stable(kind: AurelSurfaceKind, display_name: str) -> None:
    contract = build_surface_contract(kind)
    assert contract.display_name == display_name


def test_p2_0_2_aurel_cro_surface_contract() -> None:
    contract = build_surface_contract(AurelSurfaceKind.AUREL_CRO)
    assert contract.surface_id == "aurel_cro"
    assert "command" in contract.purpose.lower()
    assert contract.authority_boundary.autonomous_execution is False
    assert contract.authority_boundary.runtime_execution is False


def test_p2_0_3_hq_surface_contract() -> None:
    contract = build_surface_contract(AurelSurfaceKind.HQ)
    assert contract.surface_id == "hq"
    assert "operations" in contract.purpose.lower()
    assert contract.source_of_truth_relation.projection_only is True
    assert contract.source_of_truth_relation.owns_truth is False
    assert contract.side_effects.runtime_mutated is False


def test_p2_0_4_corp_surface_contract() -> None:
    contract = build_surface_contract(AurelSurfaceKind.CORP)
    assert "BusinessEnvironment" in contract.purpose
    assert contract.authority_boundary.business_execution is False
    assert contract.source_of_truth_relation.owns_truth is False


def test_p2_0_5_hub_surface_contract() -> None:
    contract = build_surface_contract(AurelSurfaceKind.HUB)
    assert "tool" in contract.purpose.lower()
    assert_hub_is_not_execution_authority(contract)
    assert contract.side_effects.tool_executed is False


def test_p2_0_6_ide_surface_contract() -> None:
    contract = build_surface_contract(AurelSurfaceKind.IDE)
    assert "CodeOps" in contract.purpose
    assert_ide_is_not_runtime_authority(contract)
    assert contract.authority_boundary.bypass_validation_discipline is False


def test_p2_0_7_system_surface_contract() -> None:
    contract = build_surface_contract(AurelSurfaceKind.SYSTEM)
    assert_system_is_operator_only(contract)
    settings = build_surface_contract(AurelSurfaceKind.SETTINGS)
    assert_settings_is_not_system(contract, settings)
    assert contract.side_effects.system_authority_granted is False


def test_p2_0_8_settings_surface_contract() -> None:
    contract = build_surface_contract(AurelSurfaceKind.SETTINGS)
    assert_settings_is_non_root(contract)
    system = build_surface_contract(AurelSurfaceKind.SYSTEM)
    assert_settings_is_not_system(system, contract)
    assert contract.authority_boundary.root_authority_grant is False


def test_registry_snapshot_serializes() -> None:
    snapshot = build_surface_registry_snapshot()
    payload = serialize_surface_registry_snapshot(snapshot)
    parsed = json.loads(payload)
    assert parsed["surface_count"] == 7
    assert parsed["pack_id"] == AUREL_SHELL_PACK_TASK_ID


def test_pack_result_covers_checkpoints() -> None:
    result = build_p2_0_a_shell_foundation_surface_registry_result()
    assert result.pack_id == AUREL_SHELL_PACK_TASK_ID
    assert result.covered_checkpoints == AUREL_SHELL_PACK_CHECKPOINT_IDS
    assert result.next_pack == AUREL_SHELL_NEXT_PACK_ID
    assert all(status == "DONE" for status in result.checkpoint_statuses.values())


def test_pack_result_side_effects_all_false() -> None:
    result = build_p2_0_a_shell_foundation_surface_registry_result()
    proof = result.side_effect_proof
    for field_name in proof.to_canonical_dict():
        if field_name.endswith("_hash"):
            continue
        assert getattr(proof, field_name) is False


def test_surface_taxonomy_drift_detected() -> None:
    drift, details = detect_surface_taxonomy_drift()
    assert drift is True
    assert len(details) >= 1


def test_cro_registered_exactly_once() -> None:
    registry = build_default_surface_registry()
    cro = [surface for surface in registry.surfaces if surface.surface_kind == AurelSurfaceKind.AUREL_CRO]
    assert len(cro) == 1
