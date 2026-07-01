from __future__ import annotations

from agentic_runtime.aurel_shell.surface_permission_projection import (
    P2_11_C_NEXT_PACK,
    P2_11_C_NEXT_TITLE,
    build_p2_11_b_handoff,
    build_p2_11_b_surface_permission_projection_result,
)


def test_p211b_handoff_points_to_p211c_operator_inspection_binding() -> None:
    handoff = build_p2_11_b_handoff()

    assert handoff.next_pack == P2_11_C_NEXT_PACK == "P2.11-C"
    assert handoff.next_title == P2_11_C_NEXT_TITLE
    assert "not implemented" in handoff.handoff_status
    assert any("cli shell" in need.lower() for need in handoff.cli_shell_binding_needs)
    assert any("operator" in need.lower() for need in handoff.operator_view_needs)


def test_p211b_result_keeps_p211c_and_p212_unimplemented() -> None:
    result = build_p2_11_b_surface_permission_projection_result()

    assert result.handoff.next_pack == "P2.11-C"
    assert result.p211c_not_done is True
    assert result.p212_not_started is True
    assert result.read_model.next_pack_pointer == "P2.11-C"
    assert result.side_effect_proof.p2_11_c_implemented is False
    assert result.side_effect_proof.p2_11_claimed_complete is False
    assert result.side_effect_proof.p2_12_plus_implemented is False


def test_p211b_handoff_summarizes_projection_without_claiming_enforcement() -> None:
    result = build_p2_11_b_surface_permission_projection_result()

    assert result.projection_summary.total_entries == 700
    assert any("700 matrix entries projected" in item for item in result.handoff.projection_summary)
    assert any(
        "not runtime enforcement" in item for item in result.handoff.remaining_risks
    )
