"""ledger.py — tamper-evident, hash-chained ledger of dual-kernel decisions.

The dual kernel makes real governance decisions (route, merge verdict, which
no-collapse laws fired) that today evaporate. DSD 01H — *Law of Traceable
Authority* — requires serious authority decisions to be traceable. This ledger
records each decision in an append-only, hash-chained log (mirroring the trace
ledger's ``sha(prev_hash, payload_hash)`` discipline), so routing and merge-gate
verdicts can be audited and tamper is detectable.

Boundary (DSD 01I): :meth:`projection` returns a display read-model explicitly
marked ``projection=True`` — a projection is not source truth and the ledger it
reads from is the source of record.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Optional

from ..core_types import canonical_json, now, sha

GENESIS = "dk-genesis"


@dataclass
class DualKernelEvent:
    seq: int
    command_id: str
    task_id: str
    route: str
    autonomy_index: int
    verdict: str
    final_status: str
    blockers: list[str] = field(default_factory=list)
    nc_laws: list[str] = field(default_factory=list)
    simulation_live_status: str = ""
    authority_status: str = ""
    executed: bool = False
    created_at: float = 0.0
    prev_hash: str = ""
    entry_hash: str = ""

    def payload(self) -> dict:
        d = asdict(self)
        d.pop("prev_hash", None)
        d.pop("entry_hash", None)
        return d

    def payload_hash(self) -> str:
        return sha(canonical_json(self.payload()))

    def compute_entry_hash(self) -> str:
        return sha(self.prev_hash, self.payload_hash())


class DualKernelLedger:
    """Append-only, hash-chained decision log. In-memory + optional JSONL."""

    def __init__(self, path: Optional[str] = None) -> None:
        self._path = path
        self._entries: list[DualKernelEvent] = []

    @property
    def head(self) -> str:
        return self._entries[-1].entry_hash if self._entries else GENESIS

    def append(
        self,
        *,
        command_id: str,
        task_id: str,
        route: str,
        autonomy_index: int,
        verdict: str,
        final_status: str,
        blockers: Optional[list[str]] = None,
        nc_laws: Optional[list[str]] = None,
        simulation_live_status: str = "",
        authority_status: str = "",
        executed: bool = False,
    ) -> DualKernelEvent:
        ev = DualKernelEvent(
            seq=len(self._entries),
            command_id=command_id,
            task_id=task_id,
            route=route,
            autonomy_index=autonomy_index,
            verdict=verdict,
            final_status=final_status,
            blockers=list(blockers or []),
            nc_laws=list(nc_laws or []),
            simulation_live_status=simulation_live_status,
            authority_status=authority_status,
            executed=executed,
            created_at=now(),
            prev_hash=self.head,
        )
        ev.entry_hash = ev.compute_entry_hash()
        self._entries.append(ev)
        if self._path:
            with open(self._path, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(asdict(ev), sort_keys=True) + "\n")
        return ev

    def entries(self) -> list[DualKernelEvent]:
        return list(self._entries)

    def verify(self) -> dict:
        """Walk the chain; confirm every entry hash and prev-link is intact."""
        prev = GENESIS
        for ev in self._entries:
            if ev.prev_hash != prev:
                return {"ok": False, "seq": ev.seq, "reason": "prev_hash break"}
            if ev.compute_entry_hash() != ev.entry_hash:
                return {"ok": False, "seq": ev.seq, "reason": "payload tampered"}
            prev = ev.entry_hash
        return {"ok": True, "count": len(self._entries), "head": self.head}

    def projection(self) -> list[dict]:
        """DSD 01I read-model — a projection, not source truth."""
        return [
            {
                "projection": True,
                "seq": ev.seq,
                "command_id": ev.command_id,
                "route": ev.route,
                "final_status": ev.final_status,
                "nc_laws": list(ev.nc_laws),
                "executed": ev.executed,
                "entry_hash": ev.entry_hash,
            }
            for ev in self._entries
        ]

    @classmethod
    def load(cls, path: str) -> "DualKernelLedger":
        led = cls(path=None)
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                led._entries.append(DualKernelEvent(**json.loads(line)))
        return led
