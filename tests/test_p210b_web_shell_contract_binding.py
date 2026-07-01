"""Contract binding tests for P2.10-B web Shell read model vs P2.10-A."""

from __future__ import annotations

import json
from pathlib import Path

from agentic_runtime.aurel_shell.multi_client_foundation import (
    ShellClientKind,
    ShellClientTruthLabel,
    build_p2_10_a_multi_client_foundation_result,
    build_shell_client_state,
)
from agentic_runtime.aurel_shell.web_shell_read_model import (
    P2_10_B_FIXTURE_REL_PATH,
    build_p2_10_b_web_shell_result,
    build_web_shell_read_model,
    export_web_shell_read_model_fixture,
)


def test_p210b_surfaces_match_p210a_web_client_state() -> None:
    web_state = build_shell_client_state(ShellClientKind.WEB)
    rm = build_web_shell_read_model()
    contract_by_id = {s.surface_id: s for s in web_state.surface_availability}
    for view in rm.surfaces:
        contract = contract_by_id[view.surface_id]
        assert view.surface_label == contract.surface_label
        assert view.available == contract.available
        assert view.truth_label == contract.truth_label
        assert view.evidence_refs == contract.evidence_refs


def test_p210b_truth_labels_from_contract_not_invented() -> None:
    web_state = build_shell_client_state(ShellClientKind.WEB)
    rm = build_web_shell_read_model()
    for view in rm.surfaces:
        contract = next(
            s for s in web_state.surface_availability if s.surface_id == view.surface_id
        )
        assert view.truth_label == contract.truth_label
    assert rm.command_palette_availability == web_state.command_palette_availability
    assert rm.local_run_mode == web_state.local_run_mode.value


def test_p210b_topbar_contract_preserved() -> None:
    web_state = build_shell_client_state(ShellClientKind.WEB)
    rm = build_web_shell_read_model()
    topbar = web_state.global_topbar_contract
    selector = {s.surface_id for s in rm.surfaces if s.in_surface_selector}
    right = {s.surface_id for s in rm.surfaces if s.in_topbar_right}
    assert selector == set(topbar.surface_selector_surface_ids)
    assert right == set(topbar.right_side_surface_ids)


def test_p210b_nav_inspector_contract_preserved() -> None:
    web_state = build_shell_client_state(ShellClientKind.WEB)
    rm = build_web_shell_read_model()
    nav_by_id = {c.surface_id: c for c in web_state.per_surface_nav_inspector}
    for view in rm.surfaces:
        nav = nav_by_id[view.surface_id]
        assert view.left_nav_owned_by_surface == nav.left_nav_owned_by_surface
        assert (
            view.right_inspector_owned_by_surface
            == nav.right_inspector_owned_by_surface
        )


def test_p210b_fixture_matches_live_read_model() -> None:
    export_web_shell_read_model_fixture()
    fixture_path = Path(__file__).resolve().parents[1] / P2_10_B_FIXTURE_REL_PATH
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    live = json.loads(
        json.dumps(build_web_shell_read_model().to_canonical_dict(), sort_keys=True)
    )
    assert fixture["read_model_hash"] == live["read_model_hash"]
    assert fixture["surfaces"] == live["surfaces"]


def test_p210b_p210a_foundation_still_points_to_b_before_side_effects() -> None:
    p210a = build_p2_10_a_multi_client_foundation_result()
    assert p210a.next_pack == "P2.10-B"
    assert p210a.p210b_ready is True
    assert p210a.side_effect_proof.p2_10_b_implemented is False


def test_p210b_result_binding_integrity() -> None:
    result = build_p2_10_b_web_shell_result()
    assert result.covered_pack == "P2.10-B"
    assert result.read_model.client_status.active_client is ShellClientKind.WEB
    assert all(
        b.active for b in result.read_model.no_overclaim_boundaries
    )
    assert result.read_model.p2_vslice_a_status is ShellClientTruthLabel.PREFLIGHT_ONLY
