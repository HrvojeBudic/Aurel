"""A0 — Bi-temporal stamps for memory records (additive, read-model foundation).

A memory carries two independent time axes:

* **Valid time** — when the fact is true *in the world*.
* **Transaction time** — when the *system believed* it.

Each axis is a half-open interval ``[from, to)``. ``None`` on any endpoint means
the interval is OPEN: a ``valid_to``/``transaction_to`` of ``None`` ⇒ still-current.
This module is pure and clock-free — it only *describes and reads* the stamps that
already live on :class:`~agentic_runtime.core_types.MemoryRecord`. It writes
nothing, mutates nothing, and never enters a hashed trace payload, so records with
default (open) stamps are byte-identical to pre-A0 behavior.

The Track-A umbrella flag ``AUREL_DURABLE_MEMORY`` is defined here for continuity,
but A0 branches on nothing: the stamps are unconditionally additive and the read
model is opt-in by being called. The flag becomes load-bearing at A3 (durable
persistence) / A6 (as-of-filtered retrieval).
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Optional

# Track-A umbrella flag. Defined-not-gating in A0 (see module docstring).
_FLAG = "AUREL_DURABLE_MEMORY"


def _flag_enabled() -> bool:
    """True iff the Track-A durable-memory flag is explicitly enabled.

    A0 does not branch on this — it exists so every Track-A phase reads one
    canonical flag. Default OFF (empty/unknown ⇒ False, fail-closed).
    """
    return os.environ.get(_FLAG, "").strip() in ("1", "true", "TRUE", "on")


@dataclass(frozen=True)
class BiTemporalStamp:
    """The two time intervals of a memory belief. Immutable, pure, clock-free.

    Half-open ``[from, to)`` on each axis; ``None`` ⇒ open on that endpoint.
    """

    valid_from: Optional[float] = None
    valid_to: Optional[float] = None
    transaction_from: Optional[float] = None
    transaction_to: Optional[float] = None

    def is_valid_at(self, t: float) -> bool:
        """Is the fact true in the world at valid-time ``t`` (half-open)?"""
        if self.valid_from is not None and t < self.valid_from:
            return False
        if self.valid_to is not None and t >= self.valid_to:
            return False
        return True

    def was_believed_at(self, tt: float) -> bool:
        """Was the belief recorded in the system at transaction-time ``tt``?"""
        if self.transaction_from is not None and tt < self.transaction_from:
            return False
        if self.transaction_to is not None and tt >= self.transaction_to:
            return False
        return True

    def is_current(self) -> bool:
        """Current ⇔ both axes are open (still valid in-world AND still believed).

        This boolean cannot lie: it is True only when neither ``to`` endpoint is
        closed. A superseded or expired stamp (any ``to`` set) is never current.
        """
        return self.valid_to is None and self.transaction_to is None

    def to_dict(self) -> dict[str, Any]:
        return {
            "valid_from": self.valid_from,
            "valid_to": self.valid_to,
            "transaction_from": self.transaction_from,
            "transaction_to": self.transaction_to,
        }

    @staticmethod
    def from_record(rec: Any) -> "BiTemporalStamp":
        """Adapter: read the four stamp endpoints off a MemoryRecord.

        Duck-typed (``getattr`` with open defaults) so this module imports no
        record type and stays one-directional — ``core_types`` never imports it.
        """
        return BiTemporalStamp(
            valid_from=getattr(rec, "valid_from", None),
            valid_to=getattr(rec, "valid_to", None),
            transaction_from=getattr(rec, "transaction_from", None),
            transaction_to=getattr(rec, "transaction_to", None),
        )


__all__ = ["BiTemporalStamp", "_FLAG", "_flag_enabled"]
