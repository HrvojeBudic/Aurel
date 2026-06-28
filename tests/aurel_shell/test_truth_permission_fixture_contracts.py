"""Tests for P2.0-D truth labels, permission matrix, unavailable states, fixtures."""

from __future__ import annotations

import json

import pytest

from agentic_runtime.aurel_shell import (
    CANONICAL_SURFACE_ORDER,
    AurelShellValidationError,
    AurelSurfaceKind,
    build_default_surface_registry,
    build_p2_0_b_navigation_boundary_pack_result,
    build_p2_0_c_floating_window_handoff_context_result,
)
from agentic_runtime.aurel_shell.fixture_discipline import (
    SurfaceFixtureKind,
    assert_fixture_disclosure_not_live,
    assert_fixture_disclosure_not_production_data,
    assert_fixture_requires_source_scope_or_expiry,
    assert_fixture_requires_visible_label,
    build_surface_dev_fixture_disclosure,
    build_surface_fixture_discipline_contract,
    build_surface_mock_disclosure,
    build_surface_simulated_disclosure,
)
from agentic_runtime.aurel_shell.permission_matrix import (
    SurfacePermissionMeaning,
    assert_hub_is_tool_entry_only,
    assert_ide_is_not_runtime_authority,
    assert_permission_entry_is_contract_only,
    assert_permission_matrix_does_not_authorize,
    assert_permission_matrix_does_not_execute,
    assert_permission_matrix_does_not_grant_permission,
    assert_permission_matrix_does_not_replace_custos,
    assert_permission_matrix_references_canonical_surfaces,
    assert_settings_is_non_root_config,
    assert_system_is_operator_only_agent_forbidden,
    build_default_surface_permission_matrix,
    build_surface_permission_matrix_contract,
)
from agentic_runtime.aurel_shell.truth_labels import (
    SurfaceTruthEvidenceRequirement,
    SurfaceTruthLabel,
    assert_dev_fixture_is_not_live,
    assert_live_requires_tested_path,
    assert_mock_is_not_live,
    assert_simulated_is_not_live,
    assert_trace_verified_requires_actual_verification,
    assert_unavailable_is_not_live,
    build_surface_truth_claim,
    build_surface_truth_label_contract,
    build_surface_truth_snapshot,
)
from agentic_runtime.aurel_shell.truth_permission_fixture_read_model import (
    P2_0_D_DEPENDENCY_PACKS,
    P2_0_D_NEXT_PACK,
    P2_0_D_PACK_CHECKPOINT_IDS,
    P2_0_D_PACK_ID,
    build_p2_0_d_truth_permission_fixture_result,
    serialize_truth_permission_fixture_result,
)
from agentic_runtime.aurel_shell.unavailable_state import (
    SurfaceUnavailableReason,
    assert_unavailable_has_reason_and_next_action,
    assert_unavailable_is_not_error_hiding,
    assert_unavailable_is_not_live as assert_unavailable_state_is_not_live,
    assert_unavailable_is_operator_visible,
    build_surface_unavailable_state,
    build_surface_unavailable_state_contract,
)


def test_module_imports() -> None:
    import agentic_runtime.aurel_shell.fixture_discipline  # noqa: F401
    import agentic_runtime.aurel_shell.permission_matrix  # noqa: F401
    import agentic_runtime.aurel_shell.truth_labels  # noqa: F401
    import agentic_runtime.aurel_shell.truth_permission_fixture_read_model  # noqa: F401
    import agentic_runtime.aurel_shell.unavailable_state  # noqa: F401


def test_p2_0_d_dependencies_exist() -> None:
    registry = build_default_surface_registry()
    p2_0_b = build_p2_0_b_navigation_boundary_pack_result()
    p2_0_c = build_p2_0_c_floating_window_handoff_context_result()
    assert registry.surface_count == 7
    assert p2_0_b.result_hash
    assert p2_0_c.result_hash


def test_p2_0_d_uses_p2_0_a_registry() -> None:
    registry = build_default_surface_registry()
    truth_snapshot = build_surface_truth_snapshot(registry)
    permission_matrix = build_default_surface_permission_matrix(registry)
    assert tuple(claim.surface_id for claim in truth_snapshot) == registry.canonical_surface_ids
    assert permission_matrix.canonical_surface_ids == registry.canonical_surface_ids


def test_p2_0_d_respects_p2_0_b_boundaries() -> None:
    p2_0_b = build_p2_0_b_navigation_boundary_pack_result()
    permission_matrix = build_default_surface_permission_matrix()
    assert p2_0_b.system_no_agent_access.access_rule.agent_access_allowed is False
    assert p2_0_b.settings_system_config.settings_is_system is False
    assert p2_0_b.hub_tool_entry.tool_entry.hub_can_execute_tools is False
    assert_system_is_operator_only_agent_forbidden(permission_matrix)
    assert_settings_is_non_root_config(permission_matrix)
    assert_hub_is_tool_entry_only(permission_matrix)


def test_p2_0_d_respects_p2_0_c_continuity_semantics() -> None:
    p2_0_c = build_p2_0_c_floating_window_handoff_context_result()
    result = build_p2_0_d_truth_permission_fixture_result()
    assert result.p2_0_c_dependency_hash == p2_0_c.result_hash
    assert p2_0_c.side_effect_proof.memory_written is False
    assert p2_0_c.side_effect_proof.trace_written is False
    assert p2_0_c.side_effect_proof.permission_granted is False


def test_p2_0_d_no_duplicate_surface_list_in_production() -> None:
    registry = build_default_surface_registry()
    matrix = build_default_surface_permission_matrix(registry)
    truth_snapshot = build_surface_truth_snapshot(registry)
    matrix_ids = tuple(entry.surface_id for entry in matrix.entries)
    truth_ids = tuple(claim.surface_id for claim in truth_snapshot)
    assert matrix_ids == truth_ids == CANONICAL_SURFACE_ORDER


# --- P2.0.18 truth labels ---


def test_p2_0_18_truth_label_contract_builds() -> None:
    contract = build_surface_truth_label_contract()
    assert contract.surface_state_has_truth_label is True
    assert contract.truth_label_requires_evidence is True
    assert contract.truth_boundary.live_requires_tested_path is True
    assert contract.truth_boundary.trace_verified_requires_actual_verification is True


def test_p2_0_18_surface_truth_claim_serializes() -> None:
    claim = build_surface_truth_claim(
        surface_id="hq",
        surface_kind=AurelSurfaceKind.HQ,
        claim_id="hq:contract_truth",
        evidence_refs=("surface_contract_hash:dev",),
    )
    payload = json.dumps(claim.to_canonical_dict(), sort_keys=True)
    parsed = json.loads(payload)
    assert parsed["surface_id"] == "hq"
    assert parsed["truth_label"] == SurfaceTruthLabel.CONTRACT_ONLY.value


def test_p2_0_18_every_surface_state_requires_truth_label() -> None:
    claims = build_surface_truth_snapshot()
    assert len(claims) == 7
    assert all(claim.truth_label for claim in claims)
    assert all(claim.evidence_requirement for claim in claims)


def test_p2_0_18_live_cannot_be_assigned_without_tested_path_evidence() -> None:
    with pytest.raises(AurelShellValidationError):
        build_surface_truth_claim(
            surface_id="hq",
            surface_kind=AurelSurfaceKind.HQ,
            claim_id="hq:bad_live",
            truth_label=SurfaceTruthLabel.LIVE,
        )


def test_p2_0_18_live_with_tested_path_evidence_is_scoped_claim() -> None:
    claim = build_surface_truth_claim(
        surface_id="hq",
        surface_kind=AurelSurfaceKind.HQ,
        claim_id="hq:scoped_live",
        truth_label=SurfaceTruthLabel.LIVE,
        evidence_refs=("tested_live_path:operator_verified_scope",),
    )
    assert claim.requires_tested_path is True
    assert claim.evidence_requirement == SurfaceTruthEvidenceRequirement.TESTED_LIVE_PATH_REQUIRED
    assert_live_requires_tested_path(claim)


def test_p2_0_18_trace_verified_cannot_be_assigned_without_verification() -> None:
    with pytest.raises(AurelShellValidationError):
        build_surface_truth_claim(
            surface_id="hq",
            surface_kind=AurelSurfaceKind.HQ,
            claim_id="hq:bad_trace_verified",
            truth_label=SurfaceTruthLabel.TRACE_VERIFIED,
        )


def test_p2_0_18_trace_verified_with_actual_verification_is_scoped_claim() -> None:
    claim = build_surface_truth_claim(
        surface_id="hq",
        surface_kind=AurelSurfaceKind.HQ,
        claim_id="hq:scoped_trace_verified",
        truth_label=SurfaceTruthLabel.TRACE_VERIFIED,
        evidence_refs=("trace_verifier:actual_verification_scope",),
    )
    assert claim.requires_actual_verification is True
    assert (
        claim.evidence_requirement
        == SurfaceTruthEvidenceRequirement.ACTUAL_TRACE_VERIFICATION_REQUIRED
    )
    assert_trace_verified_requires_actual_verification(claim)


def test_p2_0_18_dev_fixture_mock_simulated_unavailable_are_not_live() -> None:
    labels = (
        SurfaceTruthLabel.DEV_FIXTURE,
        SurfaceTruthLabel.MOCK,
        SurfaceTruthLabel.SIMULATED,
        SurfaceTruthLabel.UNAVAILABLE,
    )
    claims = [
        build_surface_truth_claim(
            surface_id="hub",
            surface_kind=AurelSurfaceKind.HUB,
            claim_id=f"hub:{label.value.lower()}",
            truth_label=label,
            evidence_refs=(f"disclosure:{label.value.lower()}",),
        )
        for label in labels
    ]
    assert_dev_fixture_is_not_live(claims[0])
    assert_mock_is_not_live(claims[1])
    assert_simulated_is_not_live(claims[2])
    assert_unavailable_is_not_live(claims[3])
    assert all(not claim.is_live_claim for claim in claims)


def test_p2_0_18_no_live_surface_or_trace_verifier_created() -> None:
    result = build_p2_0_d_truth_permission_fixture_result()
    proof = result.side_effect_proof
    assert proof.live_surface_created is False
    assert proof.trace_verification_created is False


# --- P2.0.19 permission matrix ---


def test_p2_0_19_permission_matrix_contract_builds() -> None:
    contract = build_surface_permission_matrix_contract()
    assert contract.permission_matrix_exists is True
    assert contract.permission_matrix_is_contract_only is True
    assert contract.permission_matrix_does_not_authorize is True


def test_p2_0_19_permission_matrix_references_canonical_surfaces() -> None:
    registry = build_default_surface_registry()
    matrix = build_default_surface_permission_matrix(registry)
    assert matrix.entry_count == registry.surface_count == 7
    assert_permission_matrix_references_canonical_surfaces(matrix, registry)


def test_p2_0_19_permission_matrix_is_contract_only() -> None:
    matrix = build_default_surface_permission_matrix()
    for entry in matrix.entries:
        assert entry.is_contract_only is True
        assert_permission_entry_is_contract_only(entry)


def test_p2_0_19_permission_matrix_does_not_authorize_execute_or_replace_custos() -> None:
    matrix = build_default_surface_permission_matrix()
    for entry in matrix.entries:
        assert_permission_matrix_does_not_authorize(entry)
        assert_permission_matrix_does_not_execute(entry)
        assert_permission_matrix_does_not_replace_custos(entry)
        assert_permission_matrix_does_not_grant_permission(entry)
        assert entry.authorizes_action is False
        assert entry.executes_action is False
        assert entry.replaces_custos is False
        assert entry.grants_permission is False


def test_p2_0_19_system_operator_only_agent_forbidden() -> None:
    matrix = build_default_surface_permission_matrix()
    system_entry = next(e for e in matrix.entries if e.surface_kind == AurelSurfaceKind.SYSTEM)
    assert system_entry.permission_meaning == SurfacePermissionMeaning.AGENT_FORBIDDEN
    assert system_entry.operator_required is True
    assert system_entry.agent_allowed is False
    assert_system_is_operator_only_agent_forbidden(matrix)


def test_p2_0_19_settings_hub_ide_boundaries() -> None:
    matrix = build_default_surface_permission_matrix()
    settings = next(e for e in matrix.entries if e.surface_kind == AurelSurfaceKind.SETTINGS)
    hub = next(e for e in matrix.entries if e.surface_kind == AurelSurfaceKind.HUB)
    ide = next(e for e in matrix.entries if e.surface_kind == AurelSurfaceKind.IDE)
    assert "non_root_config" in settings.action_class
    assert "tool_entry" in hub.action_class
    assert any("runtime_authority" in non_goal for non_goal in ide.non_goals)
    assert_settings_is_non_root_config(matrix)
    assert_hub_is_tool_entry_only(matrix)
    assert_ide_is_not_runtime_authority(matrix)


# --- P2.0.20 unavailable state ---


def test_p2_0_20_unavailable_state_contract_builds() -> None:
    contract = build_surface_unavailable_state_contract()
    assert contract.unavailable_state_has_reason is True
    assert contract.unavailable_state_has_next_action is True
    assert contract.unavailable_is_operator_visible is True


def test_p2_0_20_unavailable_state_serializes() -> None:
    state = build_surface_unavailable_state(surface_kind=AurelSurfaceKind.HQ)
    payload = json.dumps(state.to_canonical_dict(), sort_keys=True)
    parsed = json.loads(payload)
    assert parsed["surface_id"] == "hq"
    assert parsed["truth_label"] == SurfaceTruthLabel.UNAVAILABLE.value


def test_p2_0_20_unavailable_requires_reason() -> None:
    with pytest.raises(AurelShellValidationError):
        build_surface_unavailable_state(unavailable_reason=None)


def test_p2_0_20_unavailable_requires_next_action() -> None:
    with pytest.raises(AurelShellValidationError):
        build_surface_unavailable_state(next_action=None)


def test_p2_0_20_unavailable_is_not_live_hidden_error_and_operator_visible() -> None:
    state = build_surface_unavailable_state(
        surface_kind=AurelSurfaceKind.CORP,
        unavailable_reason=SurfaceUnavailableReason.MISSING_LIVE_PATH,
    )
    assert_unavailable_has_reason_and_next_action(state)
    assert_unavailable_state_is_not_live(state)
    assert_unavailable_is_not_error_hiding(state)
    assert_unavailable_is_operator_visible(state)
    assert state.is_live is False
    assert state.is_error_hiding is False
    assert state.is_operator_visible is True


# --- P2.0.21 fixture discipline ---


def test_p2_0_21_fixture_discipline_contract_builds() -> None:
    contract = build_surface_fixture_discipline_contract()
    assert contract.dev_fixture_must_be_labeled is True
    assert contract.mock_must_be_labeled is True
    assert contract.simulated_must_be_labeled is True
    assert contract.fixture_requires_source is True


def test_p2_0_21_fixture_disclosures_serialize() -> None:
    disclosures = (
        build_surface_dev_fixture_disclosure(),
        build_surface_mock_disclosure(),
        build_surface_simulated_disclosure(),
    )
    for disclosure in disclosures:
        payload = json.dumps(disclosure.to_canonical_dict(), sort_keys=True)
        parsed = json.loads(payload)
        assert parsed["surface_id"] == disclosure.surface_id
        assert parsed["requires_visible_label"] is True


def test_p2_0_21_dev_fixture_mock_simulated_require_source_and_scope_or_expiry() -> None:
    disclosures = (
        build_surface_dev_fixture_disclosure(),
        build_surface_mock_disclosure(),
        build_surface_simulated_disclosure(),
    )
    for disclosure in disclosures:
        assert disclosure.source
        assert disclosure.scope or disclosure.expires_or_boundary
        assert_fixture_requires_source_scope_or_expiry(disclosure)


def test_p2_0_21_disclosure_missing_source_or_scope_is_rejected() -> None:
    with pytest.raises(AurelShellValidationError):
        build_surface_dev_fixture_disclosure(source="")
    with pytest.raises(AurelShellValidationError):
        build_surface_mock_disclosure(scope="", expires_or_boundary="")
    with pytest.raises(AurelShellValidationError):
        build_surface_simulated_disclosure(scope="", expires_or_boundary="")


def test_p2_0_21_dev_fixture_mock_simulated_are_not_live() -> None:
    disclosures = (
        build_surface_dev_fixture_disclosure(),
        build_surface_mock_disclosure(),
        build_surface_simulated_disclosure(),
    )
    expected = (
        SurfaceFixtureKind.DEV_FIXTURE,
        SurfaceFixtureKind.MOCK,
        SurfaceFixtureKind.SIMULATED,
    )
    for disclosure, kind in zip(disclosures, expected, strict=True):
        assert disclosure.fixture_kind == kind
        assert disclosure.is_live is False
        assert_fixture_disclosure_not_live(disclosure)


def test_p2_0_21_fixture_mock_simulated_cannot_be_production_truth() -> None:
    disclosures = (
        build_surface_dev_fixture_disclosure(),
        build_surface_mock_disclosure(),
        build_surface_simulated_disclosure(),
    )
    for disclosure in disclosures:
        assert disclosure.is_production_data is False
        assert disclosure.can_be_used_as_truth is False
        assert_fixture_requires_visible_label(disclosure)
        assert_fixture_disclosure_not_production_data(disclosure)


def test_p2_0_21_no_demo_harness_or_production_data_created() -> None:
    result = build_p2_0_d_truth_permission_fixture_result()
    proof = result.side_effect_proof
    assert proof.demo_harness_created is False
    assert proof.production_data_created is False


# --- Pack result ---


def test_pack_result_covers_p2_0_18_through_p2_0_21() -> None:
    result = build_p2_0_d_truth_permission_fixture_result()
    assert result.pack_id == P2_0_D_PACK_ID
    assert result.covered_checkpoints == P2_0_D_PACK_CHECKPOINT_IDS
    assert len(result.checkpoint_reads) == 4
    assert all(status == "DONE" for status in result.checkpoint_statuses.values())


def test_pack_result_depends_on_p2_0_a_b_and_c() -> None:
    result = build_p2_0_d_truth_permission_fixture_result()
    assert result.dependency_packs == P2_0_D_DEPENDENCY_PACKS
    assert result.registry.surface_count == 7
    assert result.p2_0_c_dependency_hash


def test_pack_result_next_pack_is_p2_0_e() -> None:
    result = build_p2_0_d_truth_permission_fixture_result()
    assert result.next_pack == P2_0_D_NEXT_PACK


def test_pack_result_side_effects_false_for_forbidden_work() -> None:
    result = build_p2_0_d_truth_permission_fixture_result()
    for field_name, value in result.side_effect_proof.to_canonical_dict().items():
        assert value is False, f"side effect {field_name} must be false"


def test_pack_result_serializes() -> None:
    result = build_p2_0_d_truth_permission_fixture_result()
    payload = serialize_truth_permission_fixture_result(result)
    parsed = json.loads(payload)
    assert parsed["pack_id"] == "P2.0-D"
    assert parsed["result_hash"] == result.result_hash
