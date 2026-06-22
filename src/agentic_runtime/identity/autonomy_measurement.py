"""P1.4.9 — Measured Autonomy Score (evidence-backed measurement layer).

Measures autonomy from AutonomyDecision records. Does NOT grant autonomy,
execute tools, or compute a global autonomy percentage.
"""

from __future__ import annotations

import json
import uuid
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path

from agentic_runtime.identity.autonomy_scale_engine import (
    ActionCategory,
    AutonomyDecision,
    AutonomyLevel,
    ReversibilityTier,
    RiskTier,
    is_denied,
)


# ── Measured Autonomy Class ──────────────────────────────────────────────


class MeasuredAutonomyClass(str, Enum):
    """Measured autonomy class derived from decision records.
    This is a measurement, NOT a permission grant.
    """
    NO_MEASURED_AUTONOMY = "NO_MEASURED_AUTONOMY"
    ANSWER_ONLY_AUTONOMY = "ANSWER_ONLY_AUTONOMY"
    DRAFT_AUTONOMY = "DRAFT_AUTONOMY"
    LOCAL_REVERSIBLE_AUTONOMY = "LOCAL_REVERSIBLE_AUTONOMY"
    GOVERNED_TOOL_AUTONOMY = "GOVERNED_TOOL_AUTONOMY"
    CONDITIONAL_AUTONOMY = "CONDITIONAL_AUTONOMY"
    APPROVAL_GATED_HIGH_RISK_AUTONOMY = "APPROVAL_GATED_HIGH_RISK_AUTONOMY"
    DENIED_OR_UNTRUSTED = "DENIED_OR_UNTRUSTED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


# ── Level ordering for verified level computation ────────────────────────
# A7 is EXCLUDED — it is denial, not autonomy.

AUTONOMY_LEVEL_ORDER: tuple[AutonomyLevel, ...] = (
    AutonomyLevel.A0_ANSWER_ONLY,
    AutonomyLevel.A1_SUGGESTION,
    AutonomyLevel.A2_DRAFT,
    AutonomyLevel.A3_REVERSIBLE_LOCAL_ACTION,
    AutonomyLevel.A4_GOVERNED_TOOL_ACTION,
    AutonomyLevel.A5_CONDITIONAL_EXECUTION,
    AutonomyLevel.A6_APPROVAL_GATED_HIGH_RISK,
)

_AUTONOMY_LEVEL_RANK: dict[AutonomyLevel, int] = {
    lvl: i for i, lvl in enumerate(AUTONOMY_LEVEL_ORDER)
}


# ── Contracts ─────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class AutonomyMeasurementWindow:
    """Window over which autonomy decisions are measured."""
    agent_id: str
    since: str | None = None
    until: str | None = None
    max_decisions: int = 100
    include_denied: bool = True
    include_approval_required: bool = True
    minimum_decisions: int = 5


@dataclass(frozen=True)
class AutonomyDecisionRecord:
    """Lightweight read model for a single autonomy decision."""
    decision: AutonomyDecision
    trace_id: str | None = None
    source: str = "autonomy_engine"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass(frozen=True)
class MeasuredAutonomyScore:
    """Evidence-backed autonomy score from decision records.
    Does NOT grant permissions. Does NOT represent a global score.
    """
    agent_id: str
    measurement_id: str
    window_start: str | None
    window_end: str | None

    total_decisions: int
    allowed_count: int
    denied_count: int
    approval_required_count: int

    allowed_ratio: float
    denied_ratio: float
    approval_required_ratio: float

    level_distribution: Mapping[str, int]
    denial_reasons: Mapping[str, int]
    warning_reasons: Mapping[str, int]

    highest_allowed_level: AutonomyLevel | None
    highest_verified_level: AutonomyLevel | None
    dominant_level: AutonomyLevel | None

    autonomy_class: MeasuredAutonomyClass
    confidence: str

    evidence_refs: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()


@dataclass(frozen=True)
class MeasuredAutonomyReport:
    """Human/audit-friendly summary of a MeasuredAutonomyScore."""
    score: MeasuredAutonomyScore
    narrative_summary: str
    top_blockers: tuple[str, ...]
    recommended_next_gates: tuple[str, ...]
    raw_decision_refs: tuple[str, ...] = ()


# ── Serialization ─────────────────────────────────────────────────────────


def measured_autonomy_score_to_dict(score: MeasuredAutonomyScore) -> dict[str, object]:
    """Stable JSON-friendly serialization of a MeasuredAutonomyScore."""
    return {
        "agent_id": score.agent_id,
        "measurement_id": score.measurement_id,
        "window_start": score.window_start,
        "window_end": score.window_end,
        "total_decisions": score.total_decisions,
        "allowed_count": score.allowed_count,
        "denied_count": score.denied_count,
        "approval_required_count": score.approval_required_count,
        "allowed_ratio": score.allowed_ratio,
        "denied_ratio": score.denied_ratio,
        "approval_required_ratio": score.approval_required_ratio,
        "level_distribution": dict(score.level_distribution),
        "denial_reasons": dict(score.denial_reasons),
        "warning_reasons": dict(score.warning_reasons),
        "highest_allowed_level": score.highest_allowed_level.value if score.highest_allowed_level else None,
        "highest_verified_level": score.highest_verified_level.value if score.highest_verified_level else None,
        "dominant_level": score.dominant_level.value if score.dominant_level else None,
        "autonomy_class": score.autonomy_class.value,
        "confidence": score.confidence,
        "evidence_refs": list(score.evidence_refs),
        "limitations": list(score.limitations),
    }


def measured_autonomy_report_to_dict(report: MeasuredAutonomyReport) -> dict[str, object]:
    """Stable JSON-friendly serialization of a MeasuredAutonomyReport."""
    return {
        "score": measured_autonomy_score_to_dict(report.score),
        "narrative_summary": report.narrative_summary,
        "top_blockers": list(report.top_blockers),
        "recommended_next_gates": list(report.recommended_next_gates),
        "raw_decision_refs": list(report.raw_decision_refs),
    }


# ── Measurement engine ────────────────────────────────────────────────────


def measure_autonomy_score(
    records: Sequence[AutonomyDecisionRecord],
    window: AutonomyMeasurementWindow,
) -> MeasuredAutonomyScore:
    """Measure autonomy from AutonomyDecision records."""
    limitations: list[str] = []

    # 1. Filter by agent_id
    filtered = [r for r in records if r.decision.agent_id == window.agent_id]

    # 2. Respect max_decisions
    if len(filtered) > window.max_decisions:
        filtered = filtered[-window.max_decisions:]
        limitations.append(f"truncated to {window.max_decisions} decisions")

    # 3. Filter denied if requested
    if not window.include_denied:
        filtered = [r for r in filtered if r.decision.allowed]

    total = len(filtered)

    # 4. Insufficient evidence check
    if total < window.minimum_decisions:
        return _insufficient_evidence(window, total, limitations)

    # 5. Count decisions
    allowed = [r for r in filtered if r.decision.allowed]
    denied = [r for r in filtered if not r.decision.allowed]
    approval_required = [r for r in filtered if r.decision.requires_human_approval]

    allowed_count = len(allowed)
    denied_count = len(denied)
    approval_required_count = len(approval_required)

    allowed_ratio = allowed_count / total if total > 0 else 0.0
    denied_ratio = denied_count / total if total > 0 else 0.0
    approval_required_ratio = approval_required_count / total if total > 0 else 0.0

    # 6. Level distribution
    level_dist: dict[str, int] = {}
    for r in filtered:
        lvl = r.decision.autonomy_level.value
        level_dist[lvl] = level_dist.get(lvl, 0) + 1

    # 7. Denial reason distribution
    denial_reasons: dict[str, int] = {}
    for r in denied:
        for blocker in r.decision.blockers:
            denial_reasons[blocker] = denial_reasons.get(blocker, 0) + 1

    # 8. Warning distribution
    warning_reasons: dict[str, int] = {}
    for r in filtered:
        for warning in r.decision.warnings:
            warning_reasons[warning] = warning_reasons.get(warning, 0) + 1

    # 9. Dominant level
    dominant_level: AutonomyLevel | None = None
    if level_dist:
        max_count = max(level_dist.values())
        for lvl_str, count in level_dist.items():
            if count == max_count:
                dominant_level = AutonomyLevel(lvl_str)
                break

    # 10. Highest allowed level (among allowed decisions)
    highest_allowed = _compute_highest_allowed(allowed)

    # 11. Highest verified level (allowed + no hard blockers + capability evidence)
    highest_verified = _compute_highest_verified(allowed)

    # 12. Classify
    autonomy_class, classification_limits = _classify(
        total=total,
        allowed_count=allowed_count,
        denied_count=denied_count,
        highest_verified=highest_verified,
        level_dist=level_dist,
        window=window,
        approval_required_count=approval_required_count,
    )
    limitations.extend(classification_limits)

    # 13. Confidence
    if total >= 50:
        confidence = "high"
    elif total >= 20:
        confidence = "medium"
    elif total >= window.minimum_decisions:
        confidence = "low"
    else:
        confidence = "insufficient"

    # 14. Evidence refs
    evidence_refs: list[str] = []
    for i, r in enumerate(filtered):
        evidence_refs.append(r.decision.decision_id)
    if len(evidence_refs) > 50:
        evidence_refs = evidence_refs[:50]
        limitations.append("evidence refs truncated to 50")

    measurement_id = f"measured_autonomy_{uuid.uuid4().hex[:12]}"

    return MeasuredAutonomyScore(
        agent_id=window.agent_id,
        measurement_id=measurement_id,
        window_start=window.since,
        window_end=window.until,
        total_decisions=total,
        allowed_count=allowed_count,
        denied_count=denied_count,
        approval_required_count=approval_required_count,
        allowed_ratio=round(allowed_ratio, 4),
        denied_ratio=round(denied_ratio, 4),
        approval_required_ratio=round(approval_required_ratio, 4),
        level_distribution=level_dist,
        denial_reasons=denial_reasons,
        warning_reasons=warning_reasons,
        highest_allowed_level=highest_allowed,
        highest_verified_level=highest_verified,
        dominant_level=dominant_level,
        autonomy_class=autonomy_class,
        confidence=confidence,
        evidence_refs=tuple(sorted(set(evidence_refs))),
        limitations=tuple(sorted(set(limitations))),
    )


# ── Classification ────────────────────────────────────────────────────────


def _classify(
    *,
    total: int,
    allowed_count: int,
    denied_count: int,
    highest_verified: AutonomyLevel | None,
    level_dist: dict[str, int],
    window: AutonomyMeasurementWindow,
    approval_required_count: int,
) -> tuple[MeasuredAutonomyClass, list[str]]:
    """Classify measured autonomy from computed statistics."""
    limits: list[str] = []

    if total < window.minimum_decisions:
        return MeasuredAutonomyClass.INSUFFICIENT_EVIDENCE, limits

    # Empty: no decisions at all → INSUFFICIENT_EVIDENCE
    if total == 0:
        return MeasuredAutonomyClass.INSUFFICIENT_EVIDENCE, limits

    # Check if all are denied → DENIED_OR_UNTRUSTED
    if allowed_count == 0:
        return MeasuredAutonomyClass.DENIED_OR_UNTRUSTED, limits

    # If denied majority and no verified level above A1
    if denied_count > allowed_count and (
        highest_verified is None
        or _level_rank(highest_verified) <= _level_rank(AutonomyLevel.A1_SUGGESTION)
    ):
        return MeasuredAutonomyClass.DENIED_OR_UNTRUSTED, limits

    if highest_verified is None:
        return MeasuredAutonomyClass.NO_MEASURED_AUTONOMY, limits

    verified = highest_verified

    if verified == AutonomyLevel.A0_ANSWER_ONLY:
        return MeasuredAutonomyClass.ANSWER_ONLY_AUTONOMY, limits
    elif verified == AutonomyLevel.A1_SUGGESTION:
        # A1 not explicitly listed as a class in the spec but maps to answer-only+
        return MeasuredAutonomyClass.ANSWER_ONLY_AUTONOMY, limits
    elif verified == AutonomyLevel.A2_DRAFT:
        return MeasuredAutonomyClass.DRAFT_AUTONOMY, limits
    elif verified == AutonomyLevel.A3_REVERSIBLE_LOCAL_ACTION:
        return MeasuredAutonomyClass.LOCAL_REVERSIBLE_AUTONOMY, limits
    elif verified == AutonomyLevel.A4_GOVERNED_TOOL_ACTION:
        return MeasuredAutonomyClass.GOVERNED_TOOL_AUTONOMY, limits
    elif verified == AutonomyLevel.A5_CONDITIONAL_EXECUTION:
        return MeasuredAutonomyClass.CONDITIONAL_AUTONOMY, limits
    elif verified == AutonomyLevel.A6_APPROVAL_GATED_HIGH_RISK:
        # Only classify if all A6 cases required approval
        a6_count = level_dist.get(AutonomyLevel.A6_APPROVAL_GATED_HIGH_RISK.value, 0)
        if approval_required_count >= a6_count:
            return MeasuredAutonomyClass.APPROVAL_GATED_HIGH_RISK_AUTONOMY, limits
        else:
            limits.append("A6 present but not all required approval — downgrading to conditional")
            return MeasuredAutonomyClass.CONDITIONAL_AUTONOMY, limits

    return MeasuredAutonomyClass.NO_MEASURED_AUTONOMY, limits


# ── Helpers ───────────────────────────────────────────────────────────────


def _compute_highest_allowed(
    allowed: list[AutonomyDecisionRecord],
) -> AutonomyLevel | None:
    """Highest autonomy level among allowed decisions (A7 excluded)."""
    if not allowed:
        return None
    best: AutonomyLevel | None = None
    best_rank = -1
    for r in allowed:
        lvl = r.decision.autonomy_level
        if is_denied(lvl):
            continue
        rank = _level_rank(lvl)
        if rank > best_rank:
            best_rank = rank
            best = lvl
    return best


def _compute_highest_verified(
    allowed: list[AutonomyDecisionRecord],
) -> AutonomyLevel | None:
    """Highest autonomy level among allowed decisions with no hard blockers.
    Only levels with all decisions having no blockers are considered verified.
    """
    if not allowed:
        return None
    # Group by level
    by_level: dict[AutonomyLevel, list[AutonomyDecisionRecord]] = {}
    for r in allowed:
        lvl = r.decision.autonomy_level
        if is_denied(lvl):
            continue
        by_level.setdefault(lvl, []).append(r)

    # A level is verified only if ALL decisions at that level have no blockers
    verified_levels: list[AutonomyLevel] = []
    for lvl, recs in by_level.items():
        if all(len(r.decision.blockers) == 0 for r in recs):
            verified_levels.append(lvl)

    if not verified_levels:
        return None

    verified_levels.sort(key=lambda lvl: _level_rank(lvl), reverse=True)
    return verified_levels[0]


def _level_rank(level: AutonomyLevel) -> int:
    """Numeric rank of autonomy level (A7 excluded from order)."""
    return _AUTONOMY_LEVEL_RANK.get(level, -1)


def _insufficient_evidence(
    window: AutonomyMeasurementWindow,
    total: int,
    limitations: list[str],
) -> MeasuredAutonomyScore:
    """Build an INSUFFICIENT_EVIDENCE score."""
    return MeasuredAutonomyScore(
        agent_id=window.agent_id,
        measurement_id=f"measured_autonomy_{uuid.uuid4().hex[:12]}",
        window_start=window.since,
        window_end=window.until,
        total_decisions=total,
        allowed_count=0,
        denied_count=0,
        approval_required_count=0,
        allowed_ratio=0.0,
        denied_ratio=0.0,
        approval_required_ratio=0.0,
        level_distribution={},
        denial_reasons={},
        warning_reasons={},
        highest_allowed_level=None,
        highest_verified_level=None,
        dominant_level=None,
        autonomy_class=MeasuredAutonomyClass.INSUFFICIENT_EVIDENCE,
        confidence="insufficient",
        limitations=tuple(sorted(set(limitations + [
            f"need {window.minimum_decisions} decisions, have {total}"
        ]))),
    )


# ── Decision record persistence (JSONL) ───────────────────────────────────


def _record_to_dict(record: AutonomyDecisionRecord) -> dict[str, object]:
    """Serialize a decision record to a stable dict for JSONL storage."""
    d = record.decision
    return {
        "decision_id": d.decision_id,
        "request_id": d.request_id,
        "agent_id": d.agent_id,
        "allowed": d.allowed,
        "autonomy_level": d.autonomy_level.value,
        "requires_human_approval": d.requires_human_approval,
        "action_category": d.action_category.value,
        "risk_tier": d.risk_tier.value,
        "reversibility_tier": d.reversibility_tier.value,
        "authority_scope": d.authority_scope,
        "capability_evidence_level": d.capability_evidence_level,
        "reason": d.reason,
        "blockers": list(d.blockers),
        "warnings": list(d.warnings),
        "required_gates": list(d.required_gates),
        "evidence_refs": list(d.evidence_refs),
        "source_hash": d.source_hash,
        "created_at": d.created_at,
        "trace_id": record.trace_id,
        "source": record.source,
    }


def _dict_to_record(data: dict[str, object]) -> AutonomyDecisionRecord:
    """Deserialize a JSONL line dict back to an AutonomyDecisionRecord."""
    decision = AutonomyDecision(
        decision_id=str(data["decision_id"]),
        request_id=str(data["request_id"]),
        agent_id=str(data["agent_id"]),
        allowed=bool(data["allowed"]),
        autonomy_level=AutonomyLevel(str(data["autonomy_level"])),
        requires_human_approval=bool(data["requires_human_approval"]),
        action_category=ActionCategory(str(data["action_category"])),
        risk_tier=RiskTier(str(data["risk_tier"])),
        reversibility_tier=ReversibilityTier(str(data["reversibility_tier"])),
        authority_scope=str(data.get("authority_scope", "")) or None,
        capability_evidence_level=str(data.get("capability_evidence_level", "")) or None,
        reason=str(data.get("reason", "")),
        blockers=_tuple_str(data.get("blockers", [])),
        warnings=_tuple_str(data.get("warnings", [])),
        required_gates=_tuple_str(data.get("required_gates", [])),
        evidence_refs=_tuple_str(data.get("evidence_refs", [])),
        source_hash=str(data.get("source_hash", "")) or None,
        created_at=str(data.get("created_at", "")),
    )
    return AutonomyDecisionRecord(
        decision=decision,
        trace_id=str(data.get("trace_id", "")) or None,
        source=str(data.get("source", "autonomy_engine")),
        created_at=str(data.get("created_at_ts", str(data.get("created_at", "")))),
    )


def _tuple_str(value: object) -> tuple[str, ...]:
    """Convert a dict value to a tuple of strings safely."""
    if isinstance(value, list):
        return tuple(str(item) for item in value)
    return ()


def append_autonomy_decision_record(path: Path, record: AutonomyDecisionRecord) -> None:
    """Append a single decision record as JSONL line. Creates path if needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(_record_to_dict(record), sort_keys=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def load_autonomy_decision_records(
    path: Path,
    *,
    max_records: int = 1000,
) -> tuple[AutonomyDecisionRecord, ...]:
    """Load decision records from JSONL file. Invalid lines are skipped."""
    records: list[AutonomyDecisionRecord] = []
    if not path.exists():
        return ()

    with path.open("r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                if not isinstance(data, dict):
                    continue
                record = _dict_to_record(data)
                records.append(record)
            except (json.JSONDecodeError, KeyError, ValueError):
                # Skip invalid records silently — fail closed
                continue
            if len(records) >= max_records:
                break

    return tuple(records)
