"""
aureleu_read_model.py — the AUREL_CRO surface read-model (F6.9).

AUREL_CRO is AurelEU's home. This read-model is a pure composition of the F6
governance state — the mandate registry, the delegation windows, the persona-switch
history, and the DN status — all deterministic trace/registry projections (zero
writes). It surfaces `claims_aureleu_dispatcher_live = True`: with F6.4/F6.5 the
role-fluid dispatcher is live (the F5 seam is flipped).
"""
from __future__ import annotations

from typing import Any

from ..constitution.delegation import DelegationLedger
from .aureleu import PERSONA_SWITCH_EVENT
from .dn import DnStatusReadModel

CLAIMS_AURELEU_DISPATCHER_LIVE = True


class AurelEUReadModel:
    """Live AurelEU governance state for `GET /read/aureleu`. Read-only."""

    def __init__(self, runtime: Any) -> None:
        self._inner = getattr(runtime, "runtime", runtime)

    def _persona_switches(self) -> list[dict]:
        out: list[dict] = []
        for ev in self._inner.trace.replay():
            if ev.get("kind") != "praxis_event":
                continue
            if ev.get("event_type") != PERSONA_SWITCH_EVENT:
                continue
            parts = str(ev.get("summary", "")).split("|", 4)
            if len(parts) < 5:
                continue
            out.append({"room_id": parts[1], "from": parts[2], "to": parts[3],
                        "context_hash": parts[4]})
        return out

    def to_dict(self) -> dict:
        registry = getattr(self._inner, "_mandate_registry", None)
        delegations = DelegationLedger.from_trace(self._inner.trace)
        return {
            "mandates": list(registry.ids()) if registry is not None else [],
            "delegations": [d.to_dict() for d in delegations],
            "persona_switches": self._persona_switches(),
            "dn": DnStatusReadModel.status(),
            "claims_aureleu_dispatcher_live": CLAIMS_AURELEU_DISPATCHER_LIVE,
        }
