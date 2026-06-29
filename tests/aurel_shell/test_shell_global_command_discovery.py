"""Tests for P2.4-B command discovery read model foundation."""

from __future__ import annotations

import json

import pytest

from agentic_runtime.aurel_shell.contracts import AurelShellValidationError
from agentic_runtime.aurel_shell.global_command_discovery import (
    P2_4_B_DEPENDENCY_PACK,
    P2_4_B_NEXT_PACK,
    P2_4_B_PACK_CHECKPOINT_IDS,
    P2_4_B_PACK_ID,
    P2_4_B_REPORT_PATH,
    P2_4_B_SECTION_ID,
    GlobalCommandContextScope,
    GlobalCommandDiscoveryGateStatus,
    GlobalCommandFilterStatus,
    GlobalCommandMatchReason,
    GlobalCommandQueryMode,
    GlobalCommandRankReason,
    GlobalCommandResultSetStatus,
    P24BCommandDiscoveryResult,
    assert_context_is_not_authority,
    assert_filter_is_not_permission,
    assert_match_is_not_execution,
    assert_omni_evidence_is_ignored_by_operator_instruction,
    assert_p2_4_b_depends_on_p2_4_a,
    assert_p2_4_b_does_not_start_future_work,
    assert_p2_4_b_side_effects_all_false,
    assert_query_is_not_ui,
    assert_ranking_is_not_authorization,
    assert_result_item_is_not_invocation,
    assert_result_set_is_not_invocation,
    build_global_command_discovery_context,
    build_global_command_discovery_gate,
    build_global_command_filter,
    build_global_command_query,
    build_global_command_result_set,
    build_p2_4_b_command_discovery_result,
    build_p2_4_b_side_effect_proof,
    match_global_commands,
    rank_global_command_matches,
    render_global_command_result_set_summary,
    serialize_p2_4_b_result,
)
from agentic_runtime.aurel_shell.global_command_registry import (
    COMMAND_EXECUTION_UNAVAILABLE_REASON,
    GlobalCommandAvailabilityStatus,
    GlobalCommandKind,
    GlobalCommandScopeKind,
    build_global_command_registry,
    build_p2_4_a_global_command_foundation_result,
)
from agentic_runtime.aurel_shell.surface_registry import CANONICAL_SURFACE_ORDER


def test_module_imports_p2_4_b() -> None:
    import agentic_runtime.aurel_shell.global_command_discovery  # noqa: F401


def test_gate_dependency_and_omni_policy() -> None:
    p2_4_a = build_p2_4_a_global_command_foundation_result()
    gate = build_global_command_discovery_gate()
    result = build_p2_4_b_command_discovery_result()

    assert P2_4_B_PACK_ID == "P2.4-B"
    assert P2_4_B_SECTION_ID == "P2.4"
    assert P2_4_B_PACK_CHECKPOINT_IDS == (
        "P2.4.6",
        "P2.4.7",
        "P2.4.8",
        "P2.4.9",
        "P2.4.10",
    )
    assert P2_4_B_DEPENDENCY_PACK == "P2.4-A"
    assert p2_4_a.command_registry.registry_status.value == "READY"
    assert gate.dependency_registry_ref.startswith("p2_4_a_global_command_registry:")
    assert gate.repo_evidence_gate_passed is True
    assert gate.omni_evidence_required is False
    assert gate.omni_evidence_ignored_by_operator_instruction is True
    assert result.next_pack == P2_4_B_NEXT_PACK
    assert result.starts_future_work is False
    assert_p2_4_b_depends_on_p2_4_a(gate)
    assert_omni_evidence_is_ignored_by_operator_instruction(gate)


def test_closed_world_enums_reject_unknown_values() -> None:
    with pytest.raises(ValueError):
        GlobalCommandDiscoveryGateStatus("OMNI_BLOCKED")
    with pytest.raises(ValueError):
        GlobalCommandQueryMode("LIVE_SEARCH")
    with pytest.raises(ValueError):
        GlobalCommandFilterStatus("PERMISSION_GRANTED")
    with pytest.raises(ValueError):
        GlobalCommandContextScope("KEYBOARD_SHORTCUT")
    with pytest.raises(ValueError):
        GlobalCommandResultSetStatus("PALETTE_READY")


def test_p2_4_6_command_query_builds_and_serializes() -> None:
    empty_query = build_global_command_query("")
    prefix_query = build_global_command_query("open")
    exact_query = build_global_command_query(
        "open_hq_surface",
        query_mode=GlobalCommandQueryMode.EXACT,
    )

    assert empty_query.query_mode == GlobalCommandQueryMode.EMPTY_QUERY
    assert empty_query.normalized_query == ""
    assert empty_query.tokens == ()
    assert empty_query.include_unavailable is True
    assert empty_query.is_ui_query is False
    assert empty_query.executes_command is False

    assert prefix_query.query_mode == GlobalCommandQueryMode.PREFIX
    assert prefix_query.normalized_query == "open"
    assert prefix_query.tokens == ("open",)

    assert exact_query.query_mode == GlobalCommandQueryMode.EXACT
    assert json.loads(json.dumps(empty_query.to_canonical_dict()))
    assert_query_is_not_ui(empty_query)


def test_p2_4_6_query_does_not_execute_or_route() -> None:
    query = build_global_command_query("hq")
    assert query.is_ui_query is False
    assert query.executes_command is False
    assert query.truth_label == "NOT_SEARCH_UI"


def test_p2_4_6_query_assertion_rejects_execution_claim() -> None:
    query = build_global_command_query("hq")
    payload = query.to_canonical_dict()
    payload["executes_command"] = True
    invalid = type(query)(**payload)
    with pytest.raises(AurelShellValidationError):
        assert_query_is_not_ui(invalid)


def test_p2_4_7_command_filter_builds() -> None:
    command_filter = build_global_command_filter(
        command_kinds=(GlobalCommandKind.NAVIGATION_PROPOSAL,),
        surface_targets=("hq",),
    )

    assert command_filter.filter_status == GlobalCommandFilterStatus.APPLIED
    assert command_filter.is_permission_decision is False
    assert command_filter.grants_permission is False
    assert command_filter.denies_permission is False
    assert_filter_is_not_permission(command_filter)
    assert json.loads(json.dumps(command_filter.to_canonical_dict()))


def test_p2_4_7_match_builds_and_is_deterministic() -> None:
    registry = build_global_command_registry()
    query = build_global_command_query("open")
    command_filter = build_global_command_filter()
    context = build_global_command_discovery_context(
        context_scope=GlobalCommandContextScope.SURFACE,
        surface_id="hq",
    )

    matches_a = match_global_commands(registry, query, command_filter, context=context)
    matches_b = match_global_commands(registry, query, command_filter, context=context)

    assert matches_a == matches_b
    assert matches_a
    for match in matches_a:
        assert match.is_execution is False
        assert match.is_invocation is False
        assert_match_is_not_execution(match)


def test_p2_4_7_unavailable_command_matches_with_reason_preserved() -> None:
    registry = build_global_command_registry()
    query = build_global_command_query("", query_mode=GlobalCommandQueryMode.EMPTY_QUERY)
    command_filter = build_global_command_filter()
    matches = match_global_commands(registry, query, command_filter)

    unavailable_matches = [match for match in matches if match.unavailable_reason]
    assert unavailable_matches
    assert all(
        match.unavailable_reason == COMMAND_EXECUTION_UNAVAILABLE_REASON
        for match in unavailable_matches
    )
    assert GlobalCommandMatchReason.UNAVAILABLE_INCLUDED in unavailable_matches[0].match_reasons


def test_p2_4_7_excluding_unavailable_filters_execution_unavailable() -> None:
    registry = build_global_command_registry()
    query = build_global_command_query(
        "",
        query_mode=GlobalCommandQueryMode.EMPTY_QUERY,
        include_unavailable=False,
    )
    command_filter = build_global_command_filter(include_unavailable=False)
    matches = match_global_commands(registry, query, command_filter)
    assert matches == ()


def test_p2_4_8_discovery_context_builds() -> None:
    context = build_global_command_discovery_context(
        context_scope=GlobalCommandContextScope.SURFACE,
        surface_id="hq",
        local_navigation_ref="local_nav:hq:overview",
        window_state_ref="workspace_window:hq:main",
    )

    assert context.context_scope == GlobalCommandContextScope.SURFACE
    assert context.surface_id == "hq"
    assert context.surface_display_name == "HQ"
    assert context.uses_official_surface_registry is True
    assert context.is_authority_grant is False
    assert context.is_permission_decision is False
    assert context.switches_surface_runtime is False
    assert context.executes_route is False
    assert_context_is_not_authority(context)
    assert json.loads(json.dumps(context.to_canonical_dict()))


def test_p2_4_8_invalid_surface_context_rejected() -> None:
    with pytest.raises(AurelShellValidationError):
        build_global_command_discovery_context(
            context_scope=GlobalCommandContextScope.SURFACE,
            surface_id="workspace",
        )


def test_p2_4_9_ranking_builds_and_is_deterministic() -> None:
    registry = build_global_command_registry()
    query = build_global_command_query("open")
    command_filter = build_global_command_filter()
    context = build_global_command_discovery_context(
        context_scope=GlobalCommandContextScope.SURFACE,
        surface_id="hq",
    )
    matches = match_global_commands(registry, query, command_filter, context=context)
    ranking_a = rank_global_command_matches(matches, registry, context=context)
    ranking_b = rank_global_command_matches(matches, registry, context=context)

    assert ranking_a == ranking_b
    assert ranking_a.deterministic is True
    assert ranking_a.is_authorization is False
    assert ranking_a.is_recommendation_policy is False
    assert ranking_a.makes_execution_decision is False
    assert ranking_a.ranking_strategy == "DETERMINISTIC_SCORE_THEN_SLUG"
    assert_ranking_is_not_authorization(ranking_a)
    assert any(
        reason == GlobalCommandRankReason.UNAVAILABLE_PRESERVED
        for _, reason in ranking_a.rank_reasons
    )


def test_p2_4_9_surface_context_boosts_hq_command() -> None:
    registry = build_global_command_registry()
    query = build_global_command_query("", query_mode=GlobalCommandQueryMode.EMPTY_QUERY)
    command_filter = build_global_command_filter()
    context = build_global_command_discovery_context(
        context_scope=GlobalCommandContextScope.SURFACE,
        surface_id="hq",
    )
    matches = match_global_commands(registry, query, command_filter, context=context)
    ranking = rank_global_command_matches(matches, registry, context=context)

    assert ranking.ranked_command_ids[0] == "global_command:open_hq_surface"
    assert any(
        command_id == "global_command:open_hq_surface"
        and reason == GlobalCommandRankReason.SURFACE_CONTEXT_BOOST
        for command_id, reason in ranking.rank_reasons
    )


def test_p2_4_10_result_item_and_result_set_build() -> None:
    result_set = build_global_command_result_set()

    assert result_set.section_id == "P2.4"
    assert result_set.created_for_pack == "P2.4-B"
    assert result_set.result_status in (
        GlobalCommandResultSetStatus.READY,
        GlobalCommandResultSetStatus.PARTIAL,
    )
    assert result_set.is_command_palette_ui is False
    assert result_set.is_source_of_truth is False
    assert result_set.executes_commands is False
    assert result_set.mutates_runtime is False
    assert result_set.writes_memory is False
    assert result_set.writes_trace is False
    assert result_set.writes_storage is False
    assert_result_set_is_not_invocation(result_set)

    for item in result_set.items:
        assert item.is_invocation is False
        assert item.executes_command is False
        if item.availability_status == GlobalCommandAvailabilityStatus.UNAVAILABLE_FOR_EXECUTION:
            assert item.unavailable_reason == COMMAND_EXECUTION_UNAVAILABLE_REASON
        assert_result_item_is_not_invocation(item)


def test_p2_4_10_result_set_serializes_deterministically() -> None:
    result_set = build_global_command_result_set()
    serialized_a = json.dumps(result_set.to_canonical_dict(), sort_keys=True)
    serialized_b = json.dumps(result_set.to_canonical_dict(), sort_keys=True)
    assert serialized_a == serialized_b


def test_p2_4_10_prefix_query_filters_commands() -> None:
    result_set = build_global_command_result_set(
        query=build_global_command_query("open_settings"),
        command_filter=build_global_command_filter(),
        context=build_global_command_discovery_context(),
    )
    assert result_set.result_count == 1
    assert result_set.items[0].command_id == "global_command:open_settings_contract"


def test_result_serializes_and_summary() -> None:
    result = build_p2_4_b_command_discovery_result(query_text="hq")
    summary = render_global_command_result_set_summary(result.result_set)

    assert result.pack_id == "P2.4-B"
    assert result.section_id == "P2.4"
    assert result.dependency_pack == "P2.4-A"
    assert result.covered_checkpoints == P2_4_B_PACK_CHECKPOINT_IDS
    assert result.surface_taxonomy_drift is True
    assert result.claims_live is False
    assert result.claims_trace_verified is False
    assert result.claims_release_scope is False
    assert result.claims_product_behavior is False
    assert result.starts_future_work is False
    assert result.next_pack == "P2.4-C"
    assert "result_count=" in summary
    assert "is_command_palette_ui=false" in summary
    assert "executes_commands=false" in summary
    assert json.loads(serialize_p2_4_b_result(result))
    assert_p2_4_b_does_not_start_future_work(result)


def test_future_work_assertion_rejects_start_flag() -> None:
    result = build_p2_4_b_command_discovery_result()
    payload = result.to_canonical_dict()
    payload["starts_future_work"] = True
    invalid = P24BCommandDiscoveryResult(**payload)
    with pytest.raises(AurelShellValidationError):
        assert_p2_4_b_does_not_start_future_work(invalid)


def test_side_effect_proof_all_false() -> None:
    proof = build_p2_4_b_side_effect_proof()
    assert_p2_4_b_side_effects_all_false(proof)
    for field, value in proof.to_canonical_dict().items():
        assert value is False, field


def test_filter_by_scope_kind() -> None:
    registry = build_global_command_registry()
    query = build_global_command_query("", query_mode=GlobalCommandQueryMode.EMPTY_QUERY)
    command_filter = build_global_command_filter(
        scope_kinds=(GlobalCommandScopeKind.SYSTEM,),
    )
    matches = match_global_commands(registry, query, command_filter)
    assert len(matches) == 1
    assert matches[0].command_id == "global_command:inspect_workspace_window_section"


def test_official_surface_ids_used_in_filter() -> None:
    command_filter = build_global_command_filter(surface_targets=("hq", "settings"))
    for surface_id in command_filter.surface_targets:
        assert surface_id in CANONICAL_SURFACE_ORDER


def test_report_path_constant() -> None:
    assert P2_4_B_REPORT_PATH == (
        "agent/reports/P2_4_B_COMMAND_DISCOVERY_READ_MODEL.md"
    )
