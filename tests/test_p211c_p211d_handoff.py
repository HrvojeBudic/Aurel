from __future__ import annotations

from agentic_runtime.aurel_shell.surface_permission_inspection import (
    P2_11_D_NEXT_PACK,
    P2_11_D_NEXT_TITLE,
    build_p2_11_c_handoff,
    build_p2_11_c_surface_permission_inspection_result,
)


def test_p211c_handoff_points_to_p211d_parity_gate() -> None:
    handoff = build_p2_11_c_handoff()

    assert handoff.next_pack == P2_11_D_NEXT_PACK == "P2.11-D"
    assert handoff.next_title == P2_11_D_NEXT_TITLE
    assert "not implemented" in handoff.handoff_status
    assert any("validate" in item.lower() for item in handoff.parity_validation_needs)
    assert any(
        "evidence" in item.lower() for item in handoff.evidence_consistency_needs
    )


def test_p211c_result_keeps_p211d_and_p212_unimplemented() -> None:
    result = build_p2_11_c_surface_permission_inspection_result()

    assert result.handoff.next_pack == "P2.11-D"
    assert result.p211d_not_done is True
    assert result.p212_not_started is True


def test_p211c_handoff_summarizes_inspection_without_claiming_enforcement() -> None:
    result = build_p2_11_c_surface_permission_inspection_result()

    assert any(
        "not complete" in item for item in result.handoff.inspection_summary
    )
    assert any(
        "not runtime enforcement" in item for item in result.handoff.remaining_risks
    )
    assert any(
        "Shell LIVE" in item for item in result.handoff.remaining_risks
    )
