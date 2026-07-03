"""P3-FLOW-K no-proof boundary tests.

Evaluation output can never claim proof: no K object carries LIVE or
TRACE_VERIFIED, harness results are not P5 proof, and the no-proof proof is
itself explicitly not a P5 trace proof.
"""

from __future__ import annotations

import dataclasses
import re
from pathlib import Path

import pytest

import agentic_runtime.aurel_flow as aurel_flow
from agentic_runtime.aurel_flow import (
    AurelFlowValidationError,
    ContractCoverageArea,
    ContractCoverageStatus,
    FORBIDDEN_FLOW_TRUTH_LABELS,
    HarnessScenarioKind,
    build_contract_coverage_matrix,
    build_harness_evaluation_suite,
    build_harness_no_proof_boundary_proof,
    create_contract_coverage_item,
    create_harness_evaluation_case,
    create_harness_scenario_fixture,
    derive_harness_evaluation_run,
)

_FLOW_PACKAGE_DIR = Path(aurel_flow.__file__).resolve().parent
_K_MODULES = (
    "flow_harness_evaluation.py",
    "flow_boundary_probes.py",
    "flow_quality_ops.py",
    "flow_harness_projection.py",
)


def _run():
    fixture = create_harness_scenario_fixture(
        fixture_kind=HarnessScenarioKind.READY_NODE_FIXTURE,
        fixture_label="ready",
        target_contracts=("WorkflowGraph",),
    )
    return derive_harness_evaluation_run(
        build_harness_evaluation_suite(
            suite_label="s",
            target_pack_range="P3",
            cases=(
                create_harness_evaluation_case(case_label="c", fixture=fixture),
            ),
        )
    )


def test_k_sources_never_assign_live_or_trace_verified() -> None:
    forbidden_assignments = (
        r"truth_label\s*=\s*FlowTruthLabel\.LIVE\b",
        r"truth_label\s*=\s*FlowTruthLabel\.TRACE_VERIFIED\b",
        r"proof_available\s*:\s*bool\s*=\s*True",
        r"trace_verified\s*:\s*bool\s*=\s*True",
    )
    for filename in _K_MODULES:
        source = (_FLOW_PACKAGE_DIR / filename).read_text(encoding="utf-8")
        for pattern in forbidden_assignments:
            assert not re.search(pattern, source), (
                f"{filename} matches forbidden pattern {pattern!r}"
            )


def test_evaluation_objects_never_carry_forbidden_truth_labels() -> None:
    run = _run()
    matrix = build_contract_coverage_matrix(
        run=run,
        coverage_items=(
            create_contract_coverage_item(
                coverage_area=ContractCoverageArea.WORKFLOW_GRAPH,
                status=ContractCoverageStatus.COVERED,
                evidence_note="x",
            ),
        ),
    )
    for obj in (run, matrix, *matrix.coverage_items):
        assert obj.truth_label not in FORBIDDEN_FLOW_TRUTH_LABELS


def test_harness_result_cannot_become_proof_structurally() -> None:
    run = _run()
    for forbidden_field in ("proof_available", "trace_verified"):
        assert getattr(run, forbidden_field) is False
        with pytest.raises(AurelFlowValidationError):
            dataclasses.replace(run, **{forbidden_field: True})


def test_no_proof_proof_is_all_false_and_fail_closed() -> None:
    proof = build_harness_no_proof_boundary_proof()
    for boundary_field in (
        "is_p5_trace_proof",
        "proof_available",
        "trace_verified",
        "harness_result_is_proof",
        "coverage_is_proof",
        "score_is_proof",
    ):
        assert getattr(proof, boundary_field) is False
        with pytest.raises(AurelFlowValidationError):
            dataclasses.replace(proof, **{boundary_field: True})
