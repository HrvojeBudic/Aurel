"""P1.ENF-C Golden Thread B governance continuity tests."""
from __future__ import annotations

from pathlib import Path

import pytest

from agentic_runtime.golden_thread_b import (
    GOLDEN_THREAD_B_NODE_SPECS,
    GoldenThreadBHarness,
    GoldenThreadBNodeType,
    GoldenThreadBTruthLabel,
    NodeSpec,
    evaluate_golden_thread_b,
    simulate_missing_commit_gap,
    simulate_missing_report_gap,
)
from agentic_runtime.golden_threads.thread_a import GoldenThreadAHarness


REPO_ROOT = Path(__file__).resolve().parents[1]

REQUIRED_CHAIN_NODE_IDS = (
    "p1_8",
    "p1_9",
    "p2_1",
    "p2_2",
    "p2_3",
    "p2_4",
    "p2_5",
    "p2_6",
    "p2_7",
    "p2_8",
    "p2_9_a",
    "p2_9_a_r1",
    "p1_enf_a",
    "p1_enf_a_omni_r1",
    "p1_enf_b",
    "p1_enf_f_a",
    "p2_9_b",
)

P2_SHELL_NODE_IDS = (
    "p2_1",
    "p2_2",
    "p2_3",
    "p2_4",
    "p2_5",
    "p2_6",
    "p2_7",
    "p2_8",
    "p2_9_a",
)

ENF_NODE_IDS = (
    "p1_enf_a",
    "p1_enf_a_omni_r1",
    "p1_enf_b",
    "p1_enf_f_a",
)


@pytest.fixture
def thread_b_result():
    return evaluate_golden_thread_b(repo_root=REPO_ROOT)


def test_golden_thread_b_preserves_thread_a(thread_b_result):
    assert thread_b_result.golden_thread_a_preserved is True
    harness = GoldenThreadAHarness()
    result = harness.run_demo()
    assert result.passed is True
    assert result.errors == ()


def test_golden_thread_b_contains_p1_8_to_p2_9_a_chain(thread_b_result):
    node_ids = {node.node_id for node in thread_b_result.nodes}
    for node_id in REQUIRED_CHAIN_NODE_IDS:
        assert node_id in node_ids


def test_golden_thread_b_requires_p1_enf_a_evidence(thread_b_result):
    node = thread_b_result.node_by_id("p1_enf_a")
    assert node is not None
    assert node.report_exists is True
    assert node.truth_label is GoldenThreadBTruthLabel.ENFORCEMENT_BRIDGE
    assert node.node_type is GoldenThreadBNodeType.RUNTIME_ENFORCEMENT


def test_golden_thread_b_requires_omni_r1_evidence(thread_b_result):
    node = thread_b_result.node_by_id("p1_enf_a_omni_r1")
    assert node is not None
    assert node.report_exists is True
    assert node.truth_label is GoldenThreadBTruthLabel.VALIDATION_TRUTH_REPAIR
    assert node.validation_evidence is True


def test_golden_thread_b_requires_p1_enf_b_evidence(thread_b_result):
    node = thread_b_result.node_by_id("p1_enf_b")
    assert node is not None
    assert node.report_exists is True
    assert node.truth_label is GoldenThreadBTruthLabel.NO_BYPASS_EVIDENCE
    assert node.node_type is GoldenThreadBNodeType.ENTRYPOINT_AUDIT


def test_golden_thread_b_requires_p1_enf_f_a_gate_evidence(thread_b_result):
    node = thread_b_result.node_by_id("p1_enf_f_a")
    assert node is not None
    assert node.report_exists is True
    assert node.truth_label is GoldenThreadBTruthLabel.DRIFT_GATED
    assert node.node_type is GoldenThreadBNodeType.DRIFT_GATE


def test_golden_thread_b_marks_p2_shell_as_contract_only(thread_b_result):
    for node_id in P2_SHELL_NODE_IDS:
        node = thread_b_result.node_by_id(node_id)
        assert node is not None
        assert node.truth_label is GoldenThreadBTruthLabel.CONTRACT_ONLY
        assert node.node_type is GoldenThreadBNodeType.SHELL_CONTRACT


def test_golden_thread_b_marks_p2_6_as_surface_projection_not_inbox(thread_b_result):
    node = thread_b_result.node_by_id("p2_6")
    assert node is not None
    assert "Surface Projection" in node.title
    assert "Event Bridge" in node.title
    assert "inbox" not in node.title.lower()


def test_golden_thread_b_marks_p2_9_b_not_done(thread_b_result):
    node = thread_b_result.node_by_id("p2_9_b")
    assert node is not None
    assert node.truth_label is GoldenThreadBTruthLabel.NOT_DONE
    assert thread_b_result.p2_9_b_status == "NOT_DONE"
    assert node.node_type is GoldenThreadBNodeType.NEXT_TASK_HANDOFF


def test_golden_thread_b_does_not_claim_live(thread_b_result):
    assert thread_b_result.live_claimed is False
    check = next(
        c for c in thread_b_result.continuity_checks if c.check_id == "no_live_claim"
    )
    assert check.passed is True


def test_golden_thread_b_does_not_claim_trace_verified_without_trace_proof(
    thread_b_result,
):
    assert thread_b_result.trace_verified_claimed is False
    check = next(
        c
        for c in thread_b_result.continuity_checks
        if c.check_id == "no_trace_verified_claim"
    )
    assert check.passed is True


def test_golden_thread_b_reports_missing_report_as_gap():
    gap = simulate_missing_report_gap(
        repo_root=REPO_ROOT,
        missing_report_path="agent/reports/DOES_NOT_EXIST.md",
    )
    assert gap is not None
    assert gap.severity is GoldenThreadBTruthLabel.GAP


def test_golden_thread_b_reports_missing_commit_as_gap():
    gap = simulate_missing_commit_gap(commit_recorded=False)
    assert gap is not None
    assert gap.severity is GoldenThreadBTruthLabel.GAP


def test_golden_thread_b_side_effect_proof_blocks_product_scope(thread_b_result):
    proof = thread_b_result.side_effect_proof
    assert proof.blocks_product_scope() is True
    assert proof.p2_9_b_implemented is False
    assert proof.shell_command_router_created is False
    assert proof.product_ui_created is False
    assert proof.golden_thread_a_rewritten is False


def test_golden_thread_b_p1_enf_a_commit_gap_visible(thread_b_result):
    """P1.ENF-A report lacks recorded commit hash — must surface as WARNING/GAP."""
    node = thread_b_result.node_by_id("p1_enf_a")
    assert node is not None
    assert node.commit_evidence is False
    enf_gaps = [g for g in thread_b_result.gaps if g.node_id == "p1_enf_a"]
    assert enf_gaps
    assert any(
        g.severity in {GoldenThreadBTruthLabel.WARNING, GoldenThreadBTruthLabel.GAP}
        for g in enf_gaps
    )


def test_golden_thread_b_separate_from_thread_a():
    from agentic_runtime import golden_thread_b
    from agentic_runtime.golden_threads import thread_a

    assert golden_thread_b.__name__ != thread_a.__name__
    assert "GoldenThreadBHarness" in dir(golden_thread_b)
    assert "GoldenThreadAHarness" in dir(thread_a)


def test_golden_thread_b_custom_missing_report_produces_gap_node():
    specs = (
        NodeSpec(
            node_id="missing_test",
            title="Missing Report Test",
            roadmap_ref="TEST",
            node_type=GoldenThreadBNodeType.AGENT_REPORT,
            report_path="agent/reports/DOES_NOT_EXIST_FOR_GTB_TEST.md",
            truth_label=GoldenThreadBTruthLabel.GAP,
        ),
    )
    result = GoldenThreadBHarness(repo_root=REPO_ROOT, node_specs=specs).assemble()
    node = result.nodes[0]
    assert node.report_exists is False
    assert node.truth_label is GoldenThreadBTruthLabel.GAP
    assert result.has_gaps is True
