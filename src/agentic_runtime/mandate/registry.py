"""
registry.py — mandate resolution (F6.0).

`mandate_id` (a string that today rides every Signal/WorkOPS turn as an unresolved
pass-through) becomes real here: the registry resolves it to a concrete `Mandate`.
Fail-closed: an unknown id resolves to `None` (the gate treats absence as "no
mandate governance available" → deny for governed paths in F6.2). The registry
optionally holds a `PolicyCardRegistry` so a mandate's `policy_card_ids` resolve
into the existing policy-card machinery (reused, not copied).
"""
from __future__ import annotations

from typing import Any, Iterable, Optional

from ..core_types import canonical_json, sha
from .mandate import Mandate


class MandateNotFound(KeyError):
    """A mandate_id with no registered mandate. Fail-closed."""


class MandateRegistry:
    """Deterministic, in-memory mandate resolution over a fixed set of mandates."""

    def __init__(self, mandates: Iterable[Mandate], *, policy_registry: Any = None) -> None:
        self._by_id: dict[str, Mandate] = {}
        for m in mandates:
            self._by_id[m.mandate_id] = m
        self._policy_registry = policy_registry

    @classmethod
    def from_mandates(cls, mandates: Iterable[Mandate], *, policy_registry: Any = None
                      ) -> "MandateRegistry":
        return cls(tuple(mandates), policy_registry=policy_registry)

    @property
    def policy_registry(self) -> Any:
        return self._policy_registry

    def resolve(self, mandate_id: str) -> Optional[Mandate]:
        """Resolve a mandate_id to a Mandate, or None (fail-closed) if unknown."""
        return self._by_id.get(mandate_id)

    def resolve_or_raise(self, mandate_id: str) -> Mandate:
        m = self._by_id.get(mandate_id)
        if m is None:
            raise MandateNotFound(mandate_id)
        return m

    def ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._by_id))

    def canonical_hash(self) -> str:
        """Deterministic digest of the whole registry (same set ⇒ same hash)."""
        return sha(canonical_json([self._by_id[k].to_dict() for k in sorted(self._by_id)]))
