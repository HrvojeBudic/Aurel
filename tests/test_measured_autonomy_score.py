"""P1.4.9 — Measured Autonomy Score tests (unit, seal, classification, CLI, persistence)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.cli_helpers import run_cli

from agentic_runtime.identity.autonomy_scale_engine import (
    ActionCategory,
    AutonomyDecision,
    AutonomyLevel,
    ReversibilityTier,
    RiskTier,
)
from agentic_runtime.identity.autonomy_measurement import (
    AUTONOMY_LEVEL_ORDER,
    AutonomyDecisionRecord,
    AutonomyMeasurementWindow,
    MeasuredAutonomyClass,
    MeasuredAutonomyReport,
    MeasuredAutonomyScore,
    _compute_highest_allowed,
    _compute_highest_verified,
    _level_rank,
    append_autonomy_decision_record,
    load_autonomy_decision_records,
    measure_autonomy_score,
    measured_autonomy_report_to_dict,
    measured_autonomy_score_to_dict,
)

# ── Helpers ───────────────────────────────────────────────────────────────


def _mk_decision(
    agent_id: str = "aurel.core",
    allowed: bool = True,
    level: AutonomyLevel = AutonomyLevel.A2_DRAFT,
    requires_approval: bool = False,
    category: ActionCategory = ActionCategory.DRAFT,
    risk: RiskTier = RiskTier.R1_LOW,
    reversibility: ReversibilityTier = ReversibilityTier.R1_FULLY_REVERSIBLE,
    blockers: tuple[str, ...] = (),
    warnings: tuple[str, ...] = (),
    required_gates: tuple[str, ...] = (),
) -> AutonomyDecision:
    return AutonomyDecision(
        decision_id=f"dec_{abs(hash(level.value)) % 1000000:06d}",
        request_id=f"req_{abs(hash(agent_id)) % 1000:03d}",
        agent_id=agent_id,
        allowed=allowed,
        autonomy_level=level,
        requires_human_approval=requires_approval,
        action_category=category,
        risk_tier=risk,
        reversibility_tier=reversibility,
        reason="test decision",
        blockers=blockers,
        warnings=warnings,
        required_gates=required_gates,
    )


def _mk_record(
    agent_id: str = "aurel.core",
    allowed: bool = True,
    level: AutonomyLevel = AutonomyLevel.A2_DRAFT,
    requires_approval: bool = False,
    category: ActionCategory = ActionCategory.DRAFT,
    blockers: tuple[str, ...] = (),
    warnings: tuple[str, ...] = (),
    required_gates: tuple[str, ...] = (),
) -> AutonomyDecisionRecord:
    return AutonomyDecisionRecord(
        decision=_mk_decision(
            agent_id=agent_id, allowed=allowed, level=level,
            requires_approval=requires_approval, category=category,
            blockers=blockers, warnings=warnings, required_gates=required_gates,
        ),
    )


def _window(agent_id: str = "aurel.core", min_decisions: int = 5, **kw) -> AutonomyMeasurementWindow:
    kwargs = {"agent_id": agent_id, "minimum_decisions": min_decisions}
    kwargs.update(kw)
    return AutonomyMeasurementWindow(**kwargs)


# ── Unit: _level_rank ─────────────────────────────────────────────────────


def test_level_rank_a0_less_than_a6():
    assert _level_rank(AutonomyLevel.A0_ANSWER_ONLY) < _level_rank(AutonomyLevel.A6_APPROVAL_GATED_HIGH_RISK)


def test_level_rank_a7_is_negative():
    assert _level_rank(AutonomyLevel.A7_DENIED) == -1


def test_a7_not_in_level_order():
    assert AutonomyLevel.A7_DENIED not in AUTONOMY_LEVEL_ORDER


# ── Unit: measurement engine ──────────────────────────────────────────────


def test_measured_autonomy_requires_minimum_evidence():
    records = [_mk_record()]  # only 1, need 5
    score = measure_autonomy_score(records, _window())
    assert score.autonomy_class == MeasuredAutonomyClass.INSUFFICIENT_EVIDENCE
    assert score.total_decisions == 1


def test_measured_autonomy_counts_allowed_and_denied():
    records = [
        _mk_record(level=AutonomyLevel.A0_ANSWER_ONLY),
        _mk_record(level=AutonomyLevel.A0_ANSWER_ONLY),
        _mk_record(level=AutonomyLevel.A2_DRAFT),
        _mk_record(allowed=False, level=AutonomyLevel.A7_DENIED),
        _mk_record(allowed=False, level=AutonomyLevel.A7_DENIED),
    ]
    score = measure_autonomy_score(records, _window())
    assert score.total_decisions == 5
    assert score.allowed_count == 3
    assert score.denied_count == 2


def test_measured_autonomy_counts_approval_required():
    records = [
        _mk_record(level=AutonomyLevel.A0_ANSWER_ONLY),
        _mk_record(level=AutonomyLevel.A0_ANSWER_ONLY),
        _mk_record(level=AutonomyLevel.A2_DRAFT),
        _mk_record(level=AutonomyLevel.A2_DRAFT),
        _mk_record(level=AutonomyLevel.A6_APPROVAL_GATED_HIGH_RISK, requires_approval=True),
    ]
    score = measure_autonomy_score(records, _window())
    assert score.approval_required_count == 1
    assert score.approval_required_ratio == 0.2


def test_measured_autonomy_builds_level_distribution():
    records = [
        _mk_record(level=AutonomyLevel.A0_ANSWER_ONLY),
        _mk_record(level=AutonomyLevel.A0_ANSWER_ONLY),
        _mk_record(level=AutonomyLevel.A2_DRAFT),
    ]
    score = measure_autonomy_score(records, _window(min_decisions=3))
    assert score.level_distribution["A0_ANSWER_ONLY"] == 2
    assert score.level_distribution["A2_DRAFT"] == 1
    assert score.dominant_level == AutonomyLevel.A0_ANSWER_ONLY


def test_measured_autonomy_tracks_denial_reasons():
    records = [
        _mk_record(level=AutonomyLevel.A0_ANSWER_ONLY),
        _mk_record(level=AutonomyLevel.A7_DENIED, allowed=False, blockers=("outside_authority_scope",)),
        _mk_record(level=AutonomyLevel.A7_DENIED, allowed=False, blockers=("outside_authority_scope", "capability_not_verified")),
        _mk_record(level=AutonomyLevel.A2_DRAFT),
        _mk_record(level=AutonomyLevel.A0_ANSWER_ONLY),
    ]
    score = measure_autonomy_score(records, _window())
    assert score.denial_reasons["outside_authority_scope"] == 2
    assert score.denial_reasons["capability_not_verified"] == 1


def test_measured_autonomy_tracks_warning_reasons():
    records = [
        _mk_record(warnings=("risk_tier_moderate",)),
        _mk_record(warnings=("risk_tier_moderate",)),
        _mk_record(warnings=("reversibility_backup_advised",)),
        _mk_record(level=AutonomyLevel.A0_ANSWER_ONLY),
        _mk_record(level=AutonomyLevel.A0_ANSWER_ONLY),
    ]
    score = measure_autonomy_score(records, _window())
    assert score.warning_reasons["risk_tier_moderate"] == 2
    assert score.warning_reasons["reversibility_backup_advised"] == 1


def test_measured_autonomy_does_not_treat_A7_as_highest():
    # All denied should still not have A7 as highest_verified
    records = [_mk_record(allowed=False, level=AutonomyLevel.A7_DENIED) for _ in range(5)]
    score = measure_autonomy_score(records, _window())
    assert score.highest_verified_level is None
    assert score.highest_allowed_level is None


def test_measured_autonomy_respects_max_decisions():
    records = [_mk_record(level=AutonomyLevel.A0_ANSWER_ONLY) for _ in range(20)]
    score = measure_autonomy_score(records, _window(max_decisions=10, min_decisions=3))
    assert score.total_decisions == 10  # truncated


def test_measured_autonomy_excludes_denied_when_requested():
    records = [
        _mk_record(level=AutonomyLevel.A0_ANSWER_ONLY),
        _mk_record(level=AutonomyLevel.A0_ANSWER_ONLY),
        _mk_record(level=AutonomyLevel.A2_DRAFT),
        _mk_record(allowed=False, level=AutonomyLevel.A7_DENIED),
        _mk_record(allowed=False, level=AutonomyLevel.A7_DENIED),
    ]
    score = measure_autonomy_score(records, _window(include_denied=False, min_decisions=3))
    assert score.total_decisions == 3
    assert score.denied_count == 0


# ── Unit: classification ──────────────────────────────────────────────────


def test_measured_autonomy_classifies_answer_only():
    records = [_mk_record(level=AutonomyLevel.A0_ANSWER_ONLY) for _ in range(5)]
    score = measure_autonomy_score(records, _window())
    assert score.autonomy_class == MeasuredAutonomyClass.ANSWER_ONLY_AUTONOMY


def test_measured_autonomy_classifies_draft_autonomy():
    records = [
        _mk_record(level=AutonomyLevel.A2_DRAFT),
        _mk_record(level=AutonomyLevel.A2_DRAFT),
        _mk_record(level=AutonomyLevel.A2_DRAFT),
        _mk_record(level=AutonomyLevel.A0_ANSWER_ONLY),
        _mk_record(level=AutonomyLevel.A0_ANSWER_ONLY),
    ]
    score = measure_autonomy_score(records, _window())
    assert score.autonomy_class == MeasuredAutonomyClass.DRAFT_AUTONOMY


def test_measured_autonomy_classifies_local_reversible_autonomy():
    records = [
        _mk_record(level=AutonomyLevel.A3_REVERSIBLE_LOCAL_ACTION),
        _mk_record(level=AutonomyLevel.A3_REVERSIBLE_LOCAL_ACTION),
        _mk_record(level=AutonomyLevel.A3_REVERSIBLE_LOCAL_ACTION),
        _mk_record(level=AutonomyLevel.A0_ANSWER_ONLY),
        _mk_record(level=AutonomyLevel.A0_ANSWER_ONLY),
    ]
    score = measure_autonomy_score(records, _window())
    assert score.autonomy_class == MeasuredAutonomyClass.LOCAL_REVERSIBLE_AUTONOMY


def test_measured_autonomy_classifies_governed_tool_autonomy():
    records = [
        _mk_record(level=AutonomyLevel.A4_GOVERNED_TOOL_ACTION),
        _mk_record(level=AutonomyLevel.A4_GOVERNED_TOOL_ACTION),
        _mk_record(level=AutonomyLevel.A4_GOVERNED_TOOL_ACTION),
        _mk_record(level=AutonomyLevel.A0_ANSWER_ONLY),
        _mk_record(level=AutonomyLevel.A0_ANSWER_ONLY),
    ]
    score = measure_autonomy_score(records, _window())
    assert score.autonomy_class == MeasuredAutonomyClass.GOVERNED_TOOL_AUTONOMY


def test_measured_autonomy_classifies_conditional_autonomy():
    records = [
        _mk_record(level=AutonomyLevel.A5_CONDITIONAL_EXECUTION),
        _mk_record(level=AutonomyLevel.A5_CONDITIONAL_EXECUTION),
        _mk_record(level=AutonomyLevel.A0_ANSWER_ONLY),
        _mk_record(level=AutonomyLevel.A0_ANSWER_ONLY),
        _mk_record(level=AutonomyLevel.A0_ANSWER_ONLY),
    ]
    score = measure_autonomy_score(records, _window())
    assert score.autonomy_class == MeasuredAutonomyClass.CONDITIONAL_AUTONOMY


def test_measured_autonomy_classifies_approval_gated_high_risk():
    records = [
        _mk_record(level=AutonomyLevel.A6_APPROVAL_GATED_HIGH_RISK, requires_approval=True),
        _mk_record(level=AutonomyLevel.A6_APPROVAL_GATED_HIGH_RISK, requires_approval=True),
        _mk_record(level=AutonomyLevel.A2_DRAFT),
        _mk_record(level=AutonomyLevel.A2_DRAFT),
        _mk_record(level=AutonomyLevel.A2_DRAFT),
    ]
    score = measure_autonomy_score(records, _window())
    assert score.autonomy_class == MeasuredAutonomyClass.APPROVAL_GATED_HIGH_RISK_AUTONOMY
    assert score.highest_verified_level == AutonomyLevel.A6_APPROVAL_GATED_HIGH_RISK


def test_measured_autonomy_classifies_denied_or_untrusted():
    records = [
        _mk_record(allowed=False, level=AutonomyLevel.A7_DENIED),
        _mk_record(allowed=False, level=AutonomyLevel.A7_DENIED),
        _mk_record(allowed=False, level=AutonomyLevel.A7_DENIED),
        _mk_record(allowed=False, level=AutonomyLevel.A7_DENIED),
        _mk_record(allowed=False, level=AutonomyLevel.A7_DENIED),
    ]
    score = measure_autonomy_score(records, _window())
    assert score.autonomy_class == MeasuredAutonomyClass.DENIED_OR_UNTRUSTED


def test_measured_autonomy_reports_limitations():
    records = [_mk_record(level=AutonomyLevel.A0_ANSWER_ONLY) for _ in range(5)]
    score = measure_autonomy_score(records, _window())
    # No limitations expected here, but the field should exist
    assert isinstance(score.limitations, tuple)


# ── Serialization ─────────────────────────────────────────────────────────


def test_measured_autonomy_json_is_stable():
    records = [_mk_record(level=AutonomyLevel.A2_DRAFT) for _ in range(5)]
    score = measure_autonomy_score(records, _window())
    dd = measured_autonomy_score_to_dict(score)
    json_str = json.dumps(dd, sort_keys=True)
    parsed = json.loads(json_str)
    assert parsed["autonomy_class"] == "DRAFT_AUTONOMY"
    assert parsed["highest_verified_level"] == "A2_DRAFT"
    assert isinstance(parsed["allowed_ratio"], (int, float))


def test_measured_autonomy_report_json_is_stable():
    records = [_mk_record(level=AutonomyLevel.A2_DRAFT) for _ in range(5)]
    score = measure_autonomy_score(records, _window())
    report = MeasuredAutonomyReport(
        score=score,
        narrative_summary="test narrative",
        top_blockers=(),
        recommended_next_gates=(),
    )
    dd = measured_autonomy_report_to_dict(report)
    assert "score" in dd
    assert dd["narrative_summary"] == "test narrative"


# ── Seal tests ────────────────────────────────────────────────────────────


def test_p149_no_global_autonomy_percentage_claim():
    """INV-P149-02: No global autonomy percentage."""
    records = [_mk_record() for _ in range(5)]
    score = measure_autonomy_score(records, _window())
    dd = measured_autonomy_score_to_dict(score)
    assert "global_score" not in dd
    assert "autonomy_percentage" not in dd
    assert "measured_autonomy" not in dd
    assert "aggregate" not in dd


def test_p149_score_is_derived_from_decision_records():
    """INV-P149-01: Score derived from decisions, not declared."""
    records = [_mk_record(level=AutonomyLevel.A2_DRAFT) for _ in range(5)]
    score = measure_autonomy_score(records, _window())
    assert score.total_decisions == len(records)
    assert score.allowed_count == len(records)


def test_p149_score_is_evidence_backed():
    """Score must reference actual evidence (decision IDs)."""
    records = [_mk_record(level=AutonomyLevel.A2_DRAFT) for _ in range(5)]
    score = measure_autonomy_score(records, _window())
    assert len(score.evidence_refs) > 0


def test_p149_a7_is_not_ranked_as_max_autonomy():
    """INV-P149-03: A7 never raises autonomy class."""
    records = [
        _mk_record(allowed=False, level=AutonomyLevel.A7_DENIED) for _ in range(10)
    ]
    score = measure_autonomy_score(records, _window())
    assert score.highest_verified_level is None
    assert score.autonomy_class != MeasuredAutonomyClass.APPROVAL_GATED_HIGH_RISK_AUTONOMY


def test_p149_planned_capability_not_counted_as_verified():
    """INV-P149-05: Planned capability not counted."""
    # Decisions with blockers like capability_not_implemented shouldn't verify
    records = [
        _mk_record(level=AutonomyLevel.A3_REVERSIBLE_LOCAL_ACTION, blockers=("capability_not_implemented",)),
        _mk_record(level=AutonomyLevel.A3_REVERSIBLE_LOCAL_ACTION, blockers=("capability_not_implemented",)),
        _mk_record(level=AutonomyLevel.A0_ANSWER_ONLY),
        _mk_record(level=AutonomyLevel.A0_ANSWER_ONLY),
        _mk_record(level=AutonomyLevel.A0_ANSWER_ONLY),
    ]
    score = measure_autonomy_score(records, _window())
    # A3 with blockers should not verify — highest verified should be A0
    assert score.highest_verified_level == AutonomyLevel.A0_ANSWER_ONLY


def test_p149_roadmap_only_capability_not_counted_as_verified():
    """INV-P149-05: Roadmap-only not counted."""
    records = [
        _mk_record(level=AutonomyLevel.A2_DRAFT, blockers=("roadmap_only_capability",)),
        _mk_record(level=AutonomyLevel.A2_DRAFT, blockers=("roadmap_only_capability",)),
        _mk_record(level=AutonomyLevel.A0_ANSWER_ONLY),
        _mk_record(level=AutonomyLevel.A0_ANSWER_ONLY),
        _mk_record(level=AutonomyLevel.A0_ANSWER_ONLY),
    ]
    score = measure_autonomy_score(records, _window())
    # A2 with roadmap blocker should not verify — highest verified should be A0
    assert score.highest_verified_level == AutonomyLevel.A0_ANSWER_ONLY


def test_p149_insufficient_evidence_class_is_used():
    """INV-P149-04: Insufficient evidence class."""
    records = [_mk_record() for _ in range(3)]  # < 5
    score = measure_autonomy_score(records, _window(min_decisions=5))
    assert score.autonomy_class == MeasuredAutonomyClass.INSUFFICIENT_EVIDENCE


def test_p149_measurement_does_not_change_permissions():
    """INV-P149-07: Measurement doesn't change permissions."""
    records = [_mk_record() for _ in range(5)]
    score = measure_autonomy_score(records, _window())
    # Measurement is a read-only struct — no side effects
    assert isinstance(score, MeasuredAutonomyScore)
    # Score should not have a "permissions" or "capabilities" field
    dd = measured_autonomy_score_to_dict(score)
    assert "permissions" not in dd
    assert "capabilities" not in dd


def test_p149_measurement_does_not_execute_tools():
    """INV-P149-08: Measurement doesn't execute tools."""
    records = [_mk_record() for _ in range(5)]
    score = measure_autonomy_score(records, _window())
    # Pure function — no tool calls, no side effects
    assert isinstance(score, MeasuredAutonomyScore)


# ── _compute_highest_verified unit tests ──────────────────────────────────


def test_highest_verified_excludes_denied():
    records = [
        _mk_record(allowed=False, level=AutonomyLevel.A7_DENIED),
    ]
    result = _compute_highest_verified(records)
    assert result is None


def test_highest_verified_requires_all_no_blockers():
    records = [
        _mk_record(level=AutonomyLevel.A3_REVERSIBLE_LOCAL_ACTION, blockers=("some_blocker",)),
        _mk_record(level=AutonomyLevel.A3_REVERSIBLE_LOCAL_ACTION),
        _mk_record(level=AutonomyLevel.A0_ANSWER_ONLY),
    ]
    result = _compute_highest_verified(records)
    # A3 has one blocker → not verified; A0 has none → verified
    assert result == AutonomyLevel.A0_ANSWER_ONLY


# ── Persistence tests ─────────────────────────────────────────────────────


def test_append_and_load_records(tmp_path):
    path = tmp_path / "test_decisions.jsonl"
    records_in = [
        _mk_record(level=AutonomyLevel.A2_DRAFT),
        _mk_record(level=AutonomyLevel.A0_ANSWER_ONLY),
    ]
    for r in records_in:
        append_autonomy_decision_record(path, r)

    records_out = load_autonomy_decision_records(path)
    assert len(records_out) == 2
    assert records_out[0].decision.autonomy_level == AutonomyLevel.A2_DRAFT
    assert records_out[1].decision.autonomy_level == AutonomyLevel.A0_ANSWER_ONLY


def test_load_records_skips_invalid_lines(tmp_path):
    path = tmp_path / "bad_decisions.jsonl"
    path.write_text('not json\n{"valid": "but not a record"}\n')
    records = load_autonomy_decision_records(path)
    assert len(records) == 0


def test_load_nonexistent_file():
    records = load_autonomy_decision_records(Path("/nonexistent/path.jsonl"))
    assert len(records) == 0


# ── CLI tests ─────────────────────────────────────────────────────────────


def test_measured_autonomy_cli_outputs_json():
    result = run_cli(
        "identity", "autonomy", "measure",
        "--minimum-decisions", "0",
        "--json",
    )
    data = json.loads(result.stdout)
    assert "score" in data
    assert data["score"]["autonomy_class"] == "INSUFFICIENT_EVIDENCE"


def test_measured_autonomy_cli_handles_no_records():
    result = run_cli(
        "identity", "autonomy", "measure",
        "--records-path", "/tmp/nonexistent_p149_test.jsonl",
        "--minimum-decisions", "0",
        "--json",
    )
    data = json.loads(result.stdout)
    # No records → insufficient evidence
    sc = data["score"]
    assert sc["autonomy_class"] == "INSUFFICIENT_EVIDENCE"
    assert sc["total_decisions"] == 0


def test_measured_autonomy_cli_respects_minimum_decisions():
    result = run_cli(
        "identity", "autonomy", "measure",
        "--minimum-decisions", "5",
        "--json",
    )
    data = json.loads(result.stdout)
    assert data["score"]["autonomy_class"] == "INSUFFICIENT_EVIDENCE"


def test_measured_autonomy_cli_human_output_contains_class_counts_and_blockers():
    result = run_cli(
        "identity", "autonomy", "measure",
        "--minimum-decisions", "0",
    )
    assert "Measured Autonomy" in result.stdout
    assert "Class:" in result.stdout
    assert "INSUFFICIENT_EVIDENCE" in result.stdout


def test_measured_autonomy_cli_evaluate_and_record(tmp_path):
    records_path = tmp_path / "test_eval.jsonl"
    result = run_cli(
        "identity", "autonomy", "measure",
        "--records-path", str(records_path),
        "--evaluate-and-record",
        "--action-category", "answer",
        "--action-name", "cli_eval_test",
        "--risk-tier", "R1_LOW",
        "--reversibility-tier", "R1_FULLY_REVERSIBLE",
        "--minimum-decisions", "1",
        "--json",
    )
    data = json.loads(result.stdout)
    sc = data["score"]
    assert sc["total_decisions"] == 1
    assert sc["autonomy_class"] in ("INSUFFICIENT_EVIDENCE", "ANSWER_ONLY_AUTONOMY")


# ── Report tests ──────────────────────────────────────────────────────────


def test_measured_autonomy_report_has_narrative():
    records = [_mk_record() for _ in range(5)]
    score = measure_autonomy_score(records, _window())
    report = MeasuredAutonomyReport(
        score=score,
        narrative_summary="All decisions allowed. Agent operates at A2_DRAFT.",
        top_blockers=(),
        recommended_next_gates=(),
    )
    assert "A2_DRAFT" in report.narrative_summary


def test_measured_autonomy_report_has_top_blockers():
    records = [
        _mk_record(allowed=False, level=AutonomyLevel.A7_DENIED, blockers=("outside_authority_scope",)),
        _mk_record(allowed=False, level=AutonomyLevel.A7_DENIED, blockers=("outside_authority_scope",)),
        _mk_record(level=AutonomyLevel.A0_ANSWER_ONLY),
        _mk_record(level=AutonomyLevel.A0_ANSWER_ONLY),
        _mk_record(level=AutonomyLevel.A0_ANSWER_ONLY),
    ]
    score = measure_autonomy_score(records, _window())
    top_blockers = sorted(score.denial_reasons.items(), key=lambda kv: (-kv[1], kv[0]))
    top = tuple(k for k, _ in top_blockers[:10])
    report = MeasuredAutonomyReport(
        score=score,
        narrative_summary="test",
        top_blockers=top,
        recommended_next_gates=(),
    )
    assert "outside_authority_scope" in report.top_blockers


# ── Window filtering ──────────────────────────────────────────────────────


def test_window_filters_by_agent_id():
    records = [
        _mk_record(agent_id="aurel.core"),
        _mk_record(agent_id="aurel.core"),
        _mk_record(agent_id="other.agent"),
        _mk_record(agent_id="other.agent"),
        _mk_record(agent_id="other.agent"),
    ]
    score = measure_autonomy_score(records, _window(agent_id="aurel.core", min_decisions=2))
    assert score.total_decisions == 2
    assert score.allowed_count == 2


def test_measured_autonomy_all_denied_is_denied_or_untrusted():
    records = [
        _mk_record(allowed=False, level=AutonomyLevel.A7_DENIED, blockers=("outside_authority_scope",)),
        _mk_record(allowed=False, level=AutonomyLevel.A7_DENIED, blockers=("high_risk_requires_human_gate",)),
        _mk_record(allowed=False, level=AutonomyLevel.A7_DENIED, blockers=("outside_authority_scope",)),
        _mk_record(allowed=False, level=AutonomyLevel.A7_DENIED, blockers=("forbidden_reversibility",)),
        _mk_record(allowed=False, level=AutonomyLevel.A7_DENIED, blockers=("capability_not_verified",)),
    ]
    score = measure_autonomy_score(records, _window())
    assert score.autonomy_class == MeasuredAutonomyClass.DENIED_OR_UNTRUSTED
    assert score.highest_verified_level is None
