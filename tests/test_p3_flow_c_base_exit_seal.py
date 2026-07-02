from __future__ import annotations

from dataclasses import replace

import pytest

from agentic_runtime.aurel_flow import (
    AurelFlowValidationError,
    FlowBaseExitSealBoundary,
    FlowBaseExitSealCheck,
    FlowBaseExitSealStatus,
    aggregate_seal_status,
    build_flow_base_exit_seal_read_model,
    evaluate_flow_base_exit_seal,
    serialize_flow_base_exit_seal,
)


def _check(check_id: str, status: FlowBaseExitSealStatus) -> FlowBaseExitSealCheck:
    return FlowBaseExitSealCheck(
        check_id=check_id,
        checkpoint_range="P3.x",
        title=check_id,
        status=status,
        evidence="test fixture",
    )


def test_aggregate_status_precedence() -> None:
    p = FlowBaseExitSealStatus.PASS
    assert aggregate_seal_status((_check("a", p),)) is FlowBaseExitSealStatus.PASS
    assert (
        aggregate_seal_status((_check("a", p), _check("b", FlowBaseExitSealStatus.PARTIAL)))
        is FlowBaseExitSealStatus.PARTIAL
    )
    assert (
        aggregate_seal_status(
            (_check("a", FlowBaseExitSealStatus.UNAVAILABLE), _check("b", p))
        )
        is FlowBaseExitSealStatus.PARTIAL
    )
    assert (
        aggregate_seal_status(
            (
                _check("a", FlowBaseExitSealStatus.PARTIAL),
                _check("b", FlowBaseExitSealStatus.BLOCKED),
            )
        )
        is FlowBaseExitSealStatus.BLOCKED
    )
    assert (
        aggregate_seal_status(
            (
                _check("a", FlowBaseExitSealStatus.BLOCKED),
                _check("b", FlowBaseExitSealStatus.FAIL),
            )
        )
        is FlowBaseExitSealStatus.FAIL
    )
    assert aggregate_seal_status(()) is FlowBaseExitSealStatus.UNAVAILABLE


def test_seal_checks_cover_p3_0_through_p3_9() -> None:
    result = evaluate_flow_base_exit_seal(docs_reports_present=True)
    check_ids = tuple(check.check_id for check in result.seal.checks)

    assert check_ids == (
        "p3_0_graph_foundation",
        "p3_1_state_lifecycle",
        "p3_2_scheduler_ready_queue",
        "p3_3_runtime_event_stream",
        "p3_4_pause_resume",
        "p3_5_recovery_candidates",
        "p3_6_projection",
        "p3_7_cli_binding",
        "p3_8_docs_reports",
        "p3_9_seal",
    )
    for check in result.seal.checks:
        assert check.evidence or check.reason


def test_seal_passes_only_with_real_evidence() -> None:
    result = evaluate_flow_base_exit_seal(docs_reports_present=True)

    assert result.seal.status is FlowBaseExitSealStatus.PASS
    assert result.pass_count == 10
    assert result.partial_count == 0
    assert result.fail_count == 0


def test_seal_is_partial_when_evidence_is_missing() -> None:
    result = evaluate_flow_base_exit_seal(
        docs_reports_present=False, cli_binding_implemented=False
    )

    assert result.seal.status is FlowBaseExitSealStatus.PARTIAL
    assert result.partial_count == 2
    by_id = {check.check_id: check for check in result.seal.checks}
    assert by_id["p3_7_cli_binding"].status is FlowBaseExitSealStatus.PARTIAL
    assert by_id["p3_7_cli_binding"].reason
    assert by_id["p3_8_docs_reports"].status is FlowBaseExitSealStatus.PARTIAL
    assert by_id["p3_8_docs_reports"].reason


def test_seal_boundary_booleans_are_stated_and_fail_closed() -> None:
    result = evaluate_flow_base_exit_seal(docs_reports_present=True)
    boundary = result.seal.boundary

    assert boundary.execution_available is False
    assert boundary.trace_verified is False
    assert boundary.ledger_written is False
    assert boundary.policy_enforced_by_flow is False
    assert boundary.runtime_submit_wired is False
    assert boundary.rust_core_active is False
    assert boundary.p4_required_for_execution is True
    assert boundary.p5_required_for_trace_verification is True
    assert boundary.p9_required_for_policy_enforcement is True
    assert boundary.hybrid_ready is True

    with pytest.raises(AurelFlowValidationError):
        FlowBaseExitSealBoundary(execution_available=True)
    with pytest.raises(AurelFlowValidationError):
        FlowBaseExitSealBoundary(rust_core_active=True)
    with pytest.raises(AurelFlowValidationError):
        FlowBaseExitSealBoundary(p4_required_for_execution=False)


def test_seal_never_claims_live_or_trace_verified() -> None:
    result = evaluate_flow_base_exit_seal(docs_reports_present=True)

    assert result.seal.live is False
    assert result.seal.trace_verified is False
    with pytest.raises(AurelFlowValidationError):
        replace(result.seal, live=True)
    with pytest.raises(AurelFlowValidationError):
        replace(result.seal, trace_verified=True)


def test_seal_id_and_hash_are_stable() -> None:
    first = evaluate_flow_base_exit_seal(docs_reports_present=True)
    second = evaluate_flow_base_exit_seal(docs_reports_present=True)

    assert first.seal.seal_id == second.seal.seal_id
    assert first.seal.seal_hash == second.seal.seal_hash


def test_seal_read_model_serializes_deterministically() -> None:
    result = evaluate_flow_base_exit_seal(docs_reports_present=True)
    first = build_flow_base_exit_seal_read_model(result)
    second = build_flow_base_exit_seal_read_model(result)

    assert first.read_model_hash == second.read_model_hash
    assert serialize_flow_base_exit_seal(first) == serialize_flow_base_exit_seal(second)
    assert first.report_paths == (
        "agent/reports/P3_FLOW_A_AURELFLOW_RUNTIME_FOUNDATION_SUPERPACK.md",
        "agent/reports/P3_FLOW_B_RUNTIME_BEHAVIOR_LOOP_PACK.md",
        "agent/reports/P3_FLOW_C_FLOW_STATE_PROJECTION_CLI_DOCS_BASE_SEAL.md",
    )


def test_seal_default_docs_detection_returns_bool() -> None:
    from agentic_runtime.aurel_flow import detect_flow_reports_present

    assert isinstance(detect_flow_reports_present(), bool)
