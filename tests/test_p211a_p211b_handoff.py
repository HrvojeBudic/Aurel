from __future__ import annotations

from agentic_runtime.aurel_shell.surface_permission_matrix import (
    P2_11_B_NEXT_PACK,
    P2_11_B_NEXT_TITLE,
    build_p2_11_a_handoff,
    build_p2_11_a_surface_permission_matrix_result,
)


def test_p211a_handoff_points_to_p211b_projection_read_model_only() -> None:
    handoff = build_p2_11_a_handoff()

    assert handoff.next_pack == P2_11_B_NEXT_PACK == "P2.11-B"
    assert handoff.next_title == P2_11_B_NEXT_TITLE
    assert "not implemented" in handoff.handoff_status
    assert any("projection" in need for need in handoff.read_model_projection_needs)
    assert "P2.11-B not implemented" in handoff.remaining_risks


def test_p211a_result_keeps_p211b_and_p212_unimplemented() -> None:
    result = build_p2_11_a_surface_permission_matrix_result()

    assert result.handoff.next_pack == "P2.11-B"
    assert result.p211b_not_done is True
    assert result.p212_not_started is True
    assert result.side_effect_proof.p2_11_b_implemented is False
    assert result.side_effect_proof.p2_11_claimed_complete is False
    assert result.side_effect_proof.p2_12_plus_implemented is False
    assert result.side_effect_proof.p2_final_seal_claimed is False
    assert result.side_effect_proof.p3_handoff_claimed is False


def test_p211a_handoff_summarizes_matrix_without_claiming_projection() -> None:
    result = build_p2_11_a_surface_permission_matrix_result()

    assert result.matrix_summary.total_entries == 700
    assert any("5 clients x 7 surfaces x 20 actions" in item for item in result.handoff.permission_baseline_summary)
    assert any("not runtime enforcement" in item for item in result.handoff.remaining_risks)
