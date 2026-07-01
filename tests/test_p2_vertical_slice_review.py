"""P2.REVIEW-A vertical slice decision tests."""
from __future__ import annotations

from pathlib import Path

import pytest

from agentic_runtime.p2_vertical_slice_review import (
    P2_6_DISCARDED_TITLE,
    P2_6_OFFICIAL_TITLE,
    P2TruthLabel,
    P2VerticalSliceId,
    evaluate_p2_vertical_slice_review,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def review_result():
    return evaluate_p2_vertical_slice_review(repo_root=REPO_ROOT)


def test_p2_review_preserves_p26_projection_event_bridge_canon(review_result) -> None:
    assert review_result.p26_correction_preserved is True
    assert review_result.p26_official_title == P2_6_OFFICIAL_TITLE
    p26 = next(s for s in review_result.sections if s.section_id == "P2.6")
    assert P2_6_DISCARDED_TITLE not in p26.section_title
    assert "Surface Projection" in p26.section_title
    assert "Event Bridge" in p26.section_title


def test_p2_review_marks_p29b_not_done(review_result) -> None:
    p29b = next(s for s in review_result.sections if s.section_id == "P2.9-B")
    assert p29b.truth_label is P2TruthLabel.NOT_DONE
    assert p29b.current_status == "NOT DONE"
    assert review_result.seal_readiness.p29b_status == "NOT DONE"
    assert review_result.seal_readiness.p29b_executed is False
    assert review_result.side_effect_proof.p29b_marked_done is False


def test_p2_review_selects_first_vertical_slice(review_result) -> None:
    decision = review_result.decision
    assert decision.chosen_slice_id is P2VerticalSliceId.VSLICE_A
    assert "Command Palette" in decision.chosen_slice_title
    assert decision.fallback_slice_id is P2VerticalSliceId.VSLICE_A_FALLBACK
    assert "Surface Registry" in decision.fallback_slice_title


def test_command_palette_slice_requires_governance_identity_sandbox_truth(
    review_result,
) -> None:
    decision = review_result.decision
    assert "P1.ENF-A" in decision.policy_gate_relationship
    assert "P1.ENF-D1" in decision.identity_gate_relationship
    assert "P1.ENF-E" in decision.sandbox_gate_relationship
    assert review_result.p1_enf_a_consumed is True
    assert review_result.p1_enf_d1_consumed is True
    assert review_result.p1_enf_e_consumed is True
    gap_categories = {g.category for g in review_result.evidence_gaps}
    assert "policy_identity_sandbox_gates" in gap_categories


def test_surface_registry_fallback_exists(review_result) -> None:
    fallback = next(
        c for c in review_result.candidates if c.candidate_id == "A"
    )
    assert "Surface Registry" in fallback.title
    assert review_result.decision.fallback_slice_id is P2VerticalSliceId.VSLICE_A_FALLBACK


def test_p2_review_does_not_claim_shell_live(review_result) -> None:
    proof = review_result.side_effect_proof
    decision = review_result.decision
    assert proof.shell_live_claimed is False
    assert proof.p2_live_claimed is False
    assert decision.claims_shell_live is False
    assert decision.claims_live is False


def test_p2_review_does_not_claim_command_execution_if_preflight_only(
    review_result,
) -> None:
    proof = review_result.side_effect_proof
    decision = review_result.decision
    assert proof.command_execution_claimed is False
    assert decision.claims_execution is False
    assert decision.command_preflight_support is True
    p24 = next(s for s in review_result.sections if s.section_id == "P2.4")
    assert p24.truth_label is P2TruthLabel.CONTRACT_ONLY


def test_p2_review_outputs_evidence_gap_matrix(review_result) -> None:
    assert len(review_result.evidence_gaps) >= 5
    categories = {g.category for g in review_result.evidence_gaps}
    assert "operator_testability" in categories
    assert "p29b_seal" in categories


def test_p2_sections_are_mostly_contract_only(review_result) -> None:
    shell_sections = [
        s
        for s in review_result.sections
        if s.section_id.startswith("P2.") and s.section_id not in ("P2.9-B",)
    ]
    contract_only = sum(
        1 for s in shell_sections if s.truth_label is P2TruthLabel.CONTRACT_ONLY
    )
    assert contract_only >= 8
