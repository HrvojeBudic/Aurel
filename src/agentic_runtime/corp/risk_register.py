"""
risk_register.py — Risk Register v1: governed entries + likelihood×impact heatmap (F7.7).

A risk is **governed evidence, not ephemeral state**: an entry is recorded as a
hash-chained `PraxisEventRecord` in the trace (the same append-only channel the
Board journal and AurelEU events use), so the register and its heatmap are pure
projections that survive replay. Doctrine:

  * entry-in through the one door: `risk_proposal()` produces the payload a UI
    posts to `POST /proposals`; the governed write is `record_risk()` (a trace
    append), which the (future) `corp_risk_add` handler would call after approval.
  * **deletion is a status change, never a pop** — closing a risk records a new
    entry for the same `risk_id` with `status=CLOSED`; the projection keeps the
    latest, and history stays in the trace.
  * **auto-detection (drift-gate mined risks) is LATER** — `CLAIMS_AUTO_RISK_DETECTION`
    is hard-wired False; v1 is operator-entered only.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from ..core_types import PraxisEventRecord, RiskLevel, canonical_json

RISK_ENTRY_EVENT = "risk_entry"
_RISK_MARK = "RISK"

# Auto risk detection (mining drift-gates / trace signals) is a LATER seam.
CLAIMS_AUTO_RISK_DETECTION = False


class RiskStatus(str, Enum):
    OPEN = "open"
    MITIGATING = "mitigating"
    ACCEPTED = "accepted"
    CLOSED = "closed"


@dataclass(frozen=True)
class RiskEntry:
    """One register entry: likelihood × impact under a tier, for a job / client."""

    risk_id: str
    job_id: str = ""
    client_id: str = ""
    description: str = ""
    likelihood: int = 1                 # 1..5
    impact: int = 1                     # 1..5
    tier: RiskLevel = RiskLevel.LOW
    mitigation: str = ""
    status: RiskStatus = RiskStatus.OPEN
    source: str = "operator"

    def __post_init__(self) -> None:
        if not self.risk_id:
            raise ValueError("RiskEntry requires a risk_id")
        for name in ("likelihood", "impact"):
            v = getattr(self, name)
            if not isinstance(v, int) or not (1 <= v <= 5):
                raise ValueError(f"RiskEntry {name} must be an int in 1..5")
        if not isinstance(self.tier, RiskLevel):
            raise TypeError("RiskEntry tier must be a RiskLevel")
        if not isinstance(self.status, RiskStatus):
            raise TypeError("RiskEntry status must be a RiskStatus")

    @property
    def score(self) -> int:
        return self.likelihood * self.impact

    def to_dict(self) -> dict:
        return {
            "risk_id": self.risk_id,
            "job_id": self.job_id,
            "client_id": self.client_id,
            "description": self.description,
            "likelihood": self.likelihood,
            "impact": self.impact,
            "tier": self.tier.value,
            "mitigation": self.mitigation,
            "status": self.status.value,
            "source": self.source,
            "score": self.score,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "RiskEntry":
        return cls(
            risk_id=str(d.get("risk_id", "")),
            job_id=str(d.get("job_id", "")),
            client_id=str(d.get("client_id", "")),
            description=str(d.get("description", "")),
            likelihood=int(d.get("likelihood", 1)),
            impact=int(d.get("impact", 1)),
            tier=RiskLevel(d.get("tier", "low")),
            mitigation=str(d.get("mitigation", "")),
            status=RiskStatus(d.get("status", "open")),
            source=str(d.get("source", "operator")),
        )

    def to_summary(self) -> str:
        """Encode the entry into a praxis-event summary that survives replay.

        Uses a mark prefix + one JSON blob (split on the first ``|`` only) so free
        text (description / mitigation) with pipes round-trips safely.
        """
        return f"{_RISK_MARK}|{canonical_json(self.to_dict())}"

    @staticmethod
    def from_summary(summary: str) -> Optional["RiskEntry"]:
        parts = str(summary).split("|", 1)
        if len(parts) != 2 or parts[0] != _RISK_MARK:
            return None
        try:
            return RiskEntry.from_dict(json.loads(parts[1]))
        except (ValueError, TypeError):
            return None

    def risk_proposal(self) -> dict:
        """The one-door proposal payload (kind `act`). Records nothing by itself."""
        return {
            "kind": "act",
            "tool": "corp_risk_add",
            "args": self.to_dict(),
            "risk": "low",
            "rationale": f"register risk {self.risk_id!r}",
            "expected_effect": "append a governed risk entry to the trace",
        }


def record_risk(
    trace: Any, entry: RiskEntry, *, agent_id: str = "operator", mandate_id: str = ""
) -> PraxisEventRecord:
    """The governed write: append the risk entry as a hash-chained praxis record."""
    rec = PraxisEventRecord.make(
        run_id=getattr(trace, "run_id", ""),
        agent_id=agent_id,
        event_type=RISK_ENTRY_EVENT,
        subject_id=entry.risk_id,
        summary=entry.to_summary(),
        mandate_id=mandate_id,
    )
    trace.append_praxis_event(rec)
    return rec


@dataclass(frozen=True)
class RiskRegisterProjection:
    """The current register + heatmap, rebuilt from the trace (survives replay)."""

    _entries: dict[str, RiskEntry] = field(default_factory=dict)

    @classmethod
    def from_trace(cls, trace: Any) -> "RiskRegisterProjection":
        latest: dict[str, RiskEntry] = {}
        if trace is not None and hasattr(trace, "replay"):
            for ev in trace.replay():
                if ev.get("kind") != "praxis_event":
                    continue
                if ev.get("event_type") != RISK_ENTRY_EVENT:
                    continue
                entry = RiskEntry.from_summary(ev.get("summary", ""))
                if entry is not None:
                    latest[entry.risk_id] = entry      # replay is chronological ⇒ last wins
        return cls(latest)

    def entries(self) -> list[RiskEntry]:
        return [self._entries[k] for k in sorted(self._entries)]

    def active(self) -> list[RiskEntry]:
        return [e for e in self.entries() if e.status is not RiskStatus.CLOSED]

    def heatmap(self) -> list[dict]:
        """Deterministic likelihood×impact cells (active entries only), sorted."""
        counts: dict[tuple[int, int], int] = {}
        for e in self.active():
            counts[(e.likelihood, e.impact)] = counts.get((e.likelihood, e.impact), 0) + 1
        return [
            {"likelihood": lk, "impact": im, "count": counts[(lk, im)], "score": lk * im}
            for (lk, im) in sorted(counts)
        ]

    def to_dict(self) -> dict:
        return {
            "entries": [e.to_dict() for e in self.entries()],
            "active_count": len(self.active()),
            "heatmap": self.heatmap(),
            "claims_auto_detection": CLAIMS_AUTO_RISK_DETECTION,
        }


__all__ = [
    "RiskEntry",
    "RiskStatus",
    "RiskRegisterProjection",
    "record_risk",
    "RISK_ENTRY_EVENT",
    "CLAIMS_AUTO_RISK_DETECTION",
]
