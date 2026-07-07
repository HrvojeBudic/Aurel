"""step_verifier.py — deterministic PRM step scoring (Track B, B5).

A heuristic Process-Reward-Model that scores a proposed plan's steps and decides
whether to escalate to a bounded LLM replan. It is pure and deterministic (no
LLM judge — ``model_judge_available()`` is structurally False), advisory only,
and its verdict is NEVER recorded as verified truth: StateVerifier remains the
sole truth source. Escalation is bounded by the thinking budget's pass cap.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Sequence

_ESCALATE_THRESHOLD = 0.5
_MAX_CLEAN_STEPS = 8
_DESTRUCTIVE_TOOLS = frozenset({"delete_file"})


def model_judge_available() -> bool:
    """Structurally False: no LLM judge participates in scoring. The PRM is
    deterministic and advisory; there is no code path that makes this True."""
    return False


@dataclass(frozen=True)
class StepScore:
    index: int
    score: float           # 0.0 (bad) … 1.0 (clean)
    issues: tuple[str, ...]


@dataclass(frozen=True)
class PlanScore:
    scores: tuple[StepScore, ...]
    min_score: float
    mean_score: float
    should_escalate: bool   # advisory: replan may help — never a truth verdict

    def to_summary(self) -> dict:
        return {
            "min_score": round(self.min_score, 3),
            "mean_score": round(self.mean_score, 3),
            "should_escalate": self.should_escalate,
            "advisory": True,
            "model_judge_available": model_judge_available(),
        }


def _score_one(index: int, step: Any) -> StepScore:
    issues: list[str] = []
    penalty = 0.0
    step = step if isinstance(step, dict) else {}
    tool = str(step.get("tool") or "").strip()
    if not tool:
        issues.append("missing_tool")
        penalty += 0.6
    args = step.get("args")
    if not isinstance(args, dict) or not args:
        issues.append("missing_args")
        penalty += 0.3
    reason = str(step.get("reason") or step.get("rationale") or "").strip()
    if len(reason) < 3:
        issues.append("vague_reason")
        penalty += 0.1
    if tool in _DESTRUCTIVE_TOOLS and "confirm" not in json.dumps(step, default=str).lower():
        issues.append("unconfirmed_destructive")
        penalty += 0.2
    return StepScore(index=index, score=max(0.0, 1.0 - penalty), issues=tuple(issues))


def _has_duplicates(steps: Sequence[Any]) -> bool:
    seen: set[tuple[str, str]] = set()
    for s in steps:
        s = s if isinstance(s, dict) else {}
        key = (str(s.get("tool")), json.dumps(s.get("args"), sort_keys=True, default=str))
        if key in seen:
            return True
        seen.add(key)
    return False


def score_steps(steps: Sequence[Any]) -> PlanScore:
    """Deterministically score a plan's steps and decide escalation (advisory)."""
    scores = tuple(_score_one(i, s) for i, s in enumerate(steps))
    if not scores:
        return PlanScore((), 1.0, 1.0, False)
    min_score = min(s.score for s in scores)
    mean_score = sum(s.score for s in scores) / len(scores)
    escalate = (min_score < _ESCALATE_THRESHOLD
                or len(scores) > _MAX_CLEAN_STEPS
                or _has_duplicates(steps))
    return PlanScore(scores, min_score, mean_score, escalate)
