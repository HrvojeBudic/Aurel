"""workload_projection.py — read-only reasoning workload view (Track B, B6).

A pure fold over the reasoning trace events (reasoning_allocation /
reasoning_step_score) plus an optional live budget snapshot. It is a projection
(DSD 01I: displayed ≠ source) — it grants no allocation and no execution, and it
propagates the ledger's estimate_only / substantiated honesty flags rather than
inventing spend.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Optional

_REASONING_TYPES = frozenset({"reasoning_allocation", "reasoning_step_score"})


def _parse_summary(summary: Any) -> dict:
    """Parse the controlled ``k=v k=v`` summary the scheduler emits. The summary
    is present in both in-memory records and persisted replay (where the details
    dict is dropped), so it is the portable field source."""
    out: dict[str, str] = {}
    for token in str(summary or "").split():
        if "=" in token:
            key, value = token.split("=", 1)
            out[key] = value
    return out


def _reasoning_event(rec: Any) -> Optional[tuple[str, dict]]:
    """Normalize an in-memory record OR a replayed dict into (type, fields).

    ``fields`` merges the parsed summary (portable) with the structured details
    (richer, in-memory only); details win where present.
    """
    etype: Any = None
    details: Any = None
    summary: Any = ""
    if isinstance(rec, dict):
        payload = rec.get("payload")
        if isinstance(payload, dict) and payload.get("event_type") in _REASONING_TYPES:
            etype, details, summary = (payload["event_type"],
                                       payload.get("details"), payload.get("summary"))
        elif rec.get("event_type") in _REASONING_TYPES:
            etype, details, summary = (rec["event_type"],
                                       rec.get("details"), rec.get("summary"))
    else:
        et = getattr(rec, "event_type", None)
        if et in _REASONING_TYPES:
            etype, details, summary = (et, getattr(rec, "details", None),
                                       getattr(rec, "summary", ""))
    if etype is None:
        return None
    fields = _parse_summary(summary)
    if isinstance(details, dict):
        fields.update(details)
    return str(etype), fields


def _bump(hist: dict[str, int], key: Any) -> None:
    k = str(key)
    hist[k] = hist.get(k, 0) + 1


def _as_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _as_bool(primary: Any, fallback: Any) -> bool:
    if isinstance(primary, bool):
        return primary
    if primary is not None:
        return str(primary).strip().lower() == "true"
    return str(fallback).strip().lower() == "true"


@dataclass(frozen=True)
class WorkloadView:
    allocations: int = 0
    escalations: int = 0
    total_attempts: int = 0
    effort_histogram: dict[str, int] = field(default_factory=dict)
    profile_histogram: dict[str, int] = field(default_factory=dict)
    difficulty_histogram: dict[str, int] = field(default_factory=dict)
    reasoning_passes: int = 0
    thinking_tokens: int = 0
    thinking_calls: int = 0
    estimate_only: bool = True
    substantiated: bool = False
    projection: bool = True

    @classmethod
    def from_records(cls, records: Iterable[Any],
                     budget_snapshot: Optional[dict] = None) -> "WorkloadView":
        allocations = escalations = total_attempts = 0
        effort: dict[str, int] = {}
        profile: dict[str, int] = {}
        difficulty: dict[str, int] = {}
        for rec in records:
            parsed = _reasoning_event(rec)
            if parsed is None:
                continue
            etype, fields = parsed
            if etype == "reasoning_allocation":
                allocations += 1
                _bump(effort, fields.get("effort"))
                _bump(profile, fields.get("profile"))
                _bump(difficulty, fields.get("difficulty"))
            elif etype == "reasoning_step_score":
                total_attempts += _as_int(fields.get("attempts"))
                if _as_bool(fields.get("should_escalate"), fields.get("escalate")):
                    escalations += 1

        usage = (budget_snapshot or {}).get("usage", {}) if budget_snapshot else {}
        return cls(
            allocations=allocations,
            escalations=escalations,
            total_attempts=total_attempts,
            effort_histogram=effort,
            profile_histogram=profile,
            difficulty_histogram=difficulty,
            reasoning_passes=int(usage.get("reasoning_passes", 0)),
            thinking_tokens=int(usage.get("thinking_tokens", 0)),
            thinking_calls=int(usage.get("thinking_calls", 0)),
            estimate_only=bool(usage.get("estimate_only", True)),
            substantiated=bool(usage.get("substantiated", False)),
        )

    def to_dict(self) -> dict:
        return {
            "projection": True,
            "allocations": self.allocations,
            "escalations": self.escalations,
            "total_replan_attempts": self.total_attempts,
            "effort_histogram": dict(self.effort_histogram),
            "profile_histogram": dict(self.profile_histogram),
            "difficulty_histogram": dict(self.difficulty_histogram),
            "reasoning_passes": self.reasoning_passes,
            "thinking_tokens": self.thinking_tokens,
            "thinking_calls": self.thinking_calls,
            "estimate_only": self.estimate_only,
            "substantiated": self.substantiated,
        }
