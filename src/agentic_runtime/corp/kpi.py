"""
kpi.py — the Reflex Flywheel KPIs (F7.9).

Two operator-facing KPIs, each **honest about absence** — an empty system reports
UNAVAILABLE with a reason, never a 0% that lies:

  * **reflex hit rate** — how much work is served by cached, verified reflexes vs.
    fresh planning. Derived from the skill library (uses-weighted:
    reflex-skill successes / all skill successes), a real signal from real data.
  * **cost per task over time** — the per-run cost the budget ledger already
    tracks (F7.1), one entry per run with its cost and start time.

Both are pure read projections; neither computes anything the underlying data does
not already contain.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..core_types import CapabilityState


@dataclass(frozen=True)
class ReflexFlywheelView:
    """Reflex hit rate + cost-per-task, each AVAILABLE or honestly UNAVAILABLE."""

    reflex: dict
    cost_per_task: dict

    @classmethod
    def build(cls, *, skills: Any = None, ledger: Any = None) -> "ReflexFlywheelView":
        return cls(reflex=_reflex_hit_rate(skills), cost_per_task=_cost_per_task(ledger))

    def to_dict(self) -> dict:
        return {"reflex": self.reflex, "cost_per_task": self.cost_per_task}


def _reflex_hit_rate(skills: Any) -> dict:
    if skills is None or not hasattr(skills, "all"):
        return {"status": "UNAVAILABLE", "reason": "no skill library bound"}
    all_skills = list(skills.all())
    total_uses = sum(int(getattr(sk, "success_count", 0) or 0) for sk in all_skills)
    if total_uses == 0:
        return {"status": "UNAVAILABLE", "reason": "no skill usage recorded yet"}
    reflex_uses = sum(
        int(getattr(sk, "success_count", 0) or 0)
        for sk in all_skills
        if getattr(sk, "state", None) is CapabilityState.REFLEX
    )
    by_state: dict[str, int] = {}
    for sk in all_skills:
        key = getattr(getattr(sk, "state", None), "value", "unknown")
        by_state[key] = by_state.get(key, 0) + 1
    return {
        "status": "AVAILABLE",
        "rate": round(reflex_uses / total_uses, 4),
        "reflex_uses": reflex_uses,
        "total_uses": total_uses,
        "skill_count": len(all_skills),
        "by_state": by_state,
    }


def _cost_per_task(ledger: Any) -> dict:
    if ledger is None:
        return {"status": "UNAVAILABLE", "reason": "no budget ledger bound"}
    per_run = dict(getattr(ledger, "per_run", {}) or {})
    if not per_run:
        return {"status": "UNAVAILABLE", "reason": "no runs recorded yet"}
    runs: list[dict] = []
    total = 0.0
    for run_id in sorted(per_run):
        cost = round(float(per_run[run_id].get("estimated_cost_cents", 0.0) or 0.0), 3)
        runs.append({
            "run_id": run_id,
            "cost_cents": cost,
            "started_at": per_run[run_id].get("started_at", 0.0),
        })
        total += cost
    count = len(runs)
    return {
        "status": "AVAILABLE",
        "runs": runs,
        "run_count": count,
        "total_cost_cents": round(total, 3),
        "avg_cost_cents": round(total / count, 3) if count else 0.0,
    }


__all__ = ["ReflexFlywheelView"]
