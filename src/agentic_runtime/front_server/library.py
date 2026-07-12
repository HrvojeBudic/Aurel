"""
library.py — the unified Library read-model (F5.4).

"Library" is the **name of a projection, not a new store.** It composes three
trace-derived ingredients into one read-only view:

  - `MemoryProjection.from_trace` — governed memory: current records by tier,
    supersession (version) chains, provenance edges, and rejected writes.
  - `doc_registry` — the canonical document assets (path + existence), read-only.
  - `TraceExportManifest` — the export bundle listing, **injected** when the P5
    export pipeline has built one; otherwise an honest UNAVAILABLE seam (never a
    fabricated manifest).

Invariants: zero writes (pure projection over the trace + read-only fs existence
checks); deterministic (sorted); the overall truth label propagates as the **MIN**
(weakest) of the composed memory tiers; **time-travel / as-of replay is F8.4**
(``AUREL_SYSTEM``), derived via ``claims_library_time_travel()``, never faked.
"""
from __future__ import annotations

from typing import Any, Optional

from ..core_types import MemoryTruthState
from ..doc_registry import DocId, doc_path, repo_root
from ..memory_asof import AsOfView
from ..memory_projection import MemoryProjection

# Tier ordering weakest → strongest for MIN truth-label propagation. REJECTED is
# inactive (kept for audit) and is not part of the active min.
_TIER_ORDER: tuple[MemoryTruthState, ...] = (
    MemoryTruthState.RAW,
    MemoryTruthState.EPISODIC,
    MemoryTruthState.CANDIDATE,
    MemoryTruthState.VERIFIED,
    MemoryTruthState.PROCEDURAL,
    MemoryTruthState.CANON,
)
_TIER_RANK = {t.value: i for i, t in enumerate(_TIER_ORDER)}


def memory_asof_available() -> bool:
    """True when Library as-of replay is live (F8.4, ``AUREL_SYSTEM``)."""
    from .system_read_model import flag_enabled
    return flag_enabled()


def claims_library_time_travel() -> bool:
    """Derived seam flip (F7-carried): live iff bitemporal as-of is available."""
    return memory_asof_available()


# Backward-compatible alias for imports expecting the old constant name.
CLAIMS_LIBRARY_TIME_TRAVEL = False  # noqa: deprecated — use claims_library_time_travel()


class LibraryReadModel:
    """A read-only composition of memory + docs + (optional) export manifest."""

    def __init__(
        self,
        memory: MemoryProjection,
        *,
        manifest: Any = None,
        fabric: Any = None,
    ) -> None:
        self._memory = memory
        self._manifest = manifest
        self._fabric = fabric

    @staticmethod
    def from_trace(
        trace: Any,
        *,
        backend: Any = None,
        manifest: Any = None,
        fabric: Any = None,
    ) -> "LibraryReadModel":
        return LibraryReadModel(
            MemoryProjection.from_trace(trace, backend=backend),
            manifest=manifest,
            fabric=fabric,
        )

    # -- assets (docs) --------------------------------------------------------- #
    def assets(self) -> list[dict]:
        """Canonical document assets: repo-relative path + existence. Read-only."""
        root = repo_root()
        out: list[dict] = []
        for doc_id in DocId:
            path = doc_path(doc_id)
            try:
                rel = str(path.relative_to(root))
            except ValueError:
                rel = str(path)
            out.append({"doc_id": doc_id.value, "path": rel, "exists": path.exists()})
        out.sort(key=lambda a: a["doc_id"])
        return out

    # -- memory views ---------------------------------------------------------- #
    def memory_by_tier(self) -> dict[str, list[str]]:
        """Current memory ids grouped by truth tier, deterministically sorted."""
        tiers: dict[str, list[str]] = {}
        for mid in self._memory.current_ids:
            tiers.setdefault(self._memory.states.get(mid, ""), []).append(mid)
        return {tier: sorted(ids) for tier, ids in sorted(tiers.items())}

    def versions(self, memory_id: str) -> list[str]:
        """The supersession chain containing `memory_id`, oldest → newest ([] if unknown)."""
        return self._memory.belief_history(memory_id)

    def provenance_chain(self, memory_id: str) -> dict:
        """The version chain for `memory_id` plus the provenance edges incident to it."""
        chain = self._memory.belief_history(memory_id)
        in_chain = set(chain)
        edges = [list(t) for t in self._memory.edge_tuples()
                 if t[0] in in_chain or t[1] in in_chain]
        return {"memory_id": memory_id, "versions": chain, "edges": edges}

    def rejected(self) -> list[dict]:
        """Governance-rejected writes, kept for audit (inactive)."""
        return list(self._memory.rejected)

    def min_truth_state(self) -> Optional[str]:
        """The weakest active tier across current records (MIN propagation), or None."""
        ranks = [
            _TIER_RANK[state]
            for mid in self._memory.current_ids
            if (state := self._memory.states.get(mid, "")) in _TIER_RANK
        ]
        return _TIER_ORDER[min(ranks)].value if ranks else None

    # -- export manifest (optional, honest when absent) ------------------------ #
    def manifest(self) -> dict:
        if self._manifest is None:
            return {
                "status": "UNAVAILABLE",
                "reason": "trace export manifest is composed by the P5 export "
                          "pipeline; none injected into this Library projection",
                "owner": "P5 trace-export / F8 as-of replay",
            }
        return {"status": "AVAILABLE", **self._manifest.to_dict()}

    def as_of(
        self,
        valid_time: Optional[float] = None,
        transaction_time: Optional[float] = None,
        *,
        fabric: Any = None,
    ) -> "LibraryReadModel":
        """Bitemporal library view at ``T``. Both axes ``None`` ⇒ ``current()``."""
        if valid_time is None and transaction_time is None:
            return self
        if not memory_asof_available():
            raise ValueError("library as-of UNAVAILABLE (AUREL_SYSTEM off)")

        src = fabric if fabric is not None else self._fabric
        if src is None:
            raise ValueError("library as-of requires a memory fabric snapshot")

        records = AsOfView.from_fabric(src).as_of(valid_time, transaction_time)
        projection = MemoryProjection.from_as_of_records(records)
        return LibraryReadModel(projection, manifest=self._manifest, fabric=src)

    def current(self) -> "LibraryReadModel":
        """Current belief on both axes — byte-identical to the default projection."""
        return self

    # -- composition ----------------------------------------------------------- #
    def to_dict(
        self,
        *,
        valid_time: Optional[float] = None,
        transaction_time: Optional[float] = None,
        fabric: Any = None,
    ) -> dict:
        if valid_time is not None or transaction_time is not None:
            return self.as_of(
                valid_time, transaction_time, fabric=fabric,
            ).to_dict()
        return {
            "assets": self.assets(),
            "memory_by_tier": self.memory_by_tier(),
            "rejected": self.rejected(),
            "min_truth_state": self.min_truth_state(),
            "manifest": self.manifest(),
            "claims_time_travel": claims_library_time_travel(),
        }
