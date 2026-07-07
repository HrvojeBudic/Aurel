"""A0 — As-of read model over bi-temporally stamped memory records.

Pure, read-only, snapshot-based projections over an iterable of
:class:`~agentic_runtime.core_types.MemoryRecord`. Nothing here mutates a
fabric, writes a record, or touches the trace — it only *reads* the stamps A0
added. Determinism is structural: results are sorted by
``(transaction_from, valid_from, memory_id)`` (never ``hash()``), and every
lookup fails closed (unknown/empty ⇒ ``[]``, never a fabricated belief).

Semantics of "now/current" are clock-free: passing ``None`` for a time axis
selects records whose interval is OPEN on that axis (``*_to is None``), i.e. the
records the system still holds. This avoids reading a wall clock (which would be
non-deterministic and violate the stdlib-deterministic invariant).
"""

from __future__ import annotations

from typing import Any, Iterable, Optional

from .memory_bitemporal import BiTemporalStamp


class AsOfView:
    """A snapshot read model. Construction copies the records in; it never holds
    or mutates the source fabric."""

    def __init__(self, records: Iterable[Any]) -> None:
        # Snapshot — a list copy so later fabric mutation cannot change results.
        self._records: list[Any] = list(records)

    @staticmethod
    def from_fabric(fabric: Any) -> "AsOfView":
        """Snapshot every known record (active + rejected) from a MemoryFabric.

        Duck-typed on ``by_id`` so this module imports no fabric type.
        """
        by_id = getattr(fabric, "by_id", {}) or {}
        return AsOfView(list(by_id.values()))

    def _sort_key(self, rec: Any) -> tuple[float, float, str]:
        stamp = BiTemporalStamp.from_record(rec)
        return (
            stamp.transaction_from if stamp.transaction_from is not None else 0.0,
            stamp.valid_from if stamp.valid_from is not None else 0.0,
            str(getattr(rec, "memory_id", "") or ""),
        )

    def as_of(
        self,
        valid_time: Optional[float] = None,
        transaction_time: Optional[float] = None,
    ) -> list[Any]:
        """Records that hold as of the given (valid, transaction) times.

        ``None`` on an axis ⇒ "current on that axis" = the interval is OPEN
        (``*_to is None``). A concrete time ⇒ half-open interval containment.
        Deterministically sorted; fail-closed (empty view ⇒ ``[]``).
        """
        out: list[Any] = []
        for rec in self._records:
            stamp = BiTemporalStamp.from_record(rec)
            if valid_time is None:
                vt_ok = stamp.valid_to is None
            else:
                vt_ok = stamp.is_valid_at(valid_time)
            if transaction_time is None:
                tt_ok = stamp.transaction_to is None
            else:
                tt_ok = stamp.was_believed_at(transaction_time)
            if vt_ok and tt_ok:
                out.append(rec)
        return sorted(out, key=self._sort_key)

    def current(self) -> list[Any]:
        """Records that are current on both axes (both intervals open).

        Equivalent to ``as_of()`` and to ``BiTemporalStamp.is_current()`` — a
        record with any closed ``to`` endpoint is excluded.
        """
        return [
            rec for rec in sorted(self._records, key=self._sort_key)
            if BiTemporalStamp.from_record(rec).is_current()
        ]

    def belief_history(self, memory_id: str) -> list[Any]:
        """The supersession chain containing ``memory_id``, oldest → newest.

        Walks ``revises`` backward to the root then ``superseded_by`` forward to
        the head, cycle-guarded. Fail-closed: unknown id ⇒ ``[]``.
        """
        by_id = {str(getattr(r, "memory_id", "") or ""): r for r in self._records}
        start = by_id.get(memory_id)
        if start is None:
            return []
        seen = {memory_id}
        # Walk backward via ``revises`` to the oldest revision.
        back: list[Any] = []
        cur = start
        while True:
            prev_id = getattr(cur, "revises", None)
            if not prev_id or prev_id not in by_id or prev_id in seen:
                break
            cur = by_id[prev_id]
            seen.add(prev_id)
            back.append(cur)
        chain: list[Any] = list(reversed(back)) + [start]
        # Walk forward via ``superseded_by`` to the newest revision.
        cur = start
        while True:
            nxt_id = getattr(cur, "superseded_by", None)
            if not nxt_id or nxt_id not in by_id or nxt_id in seen:
                break
            cur = by_id[nxt_id]
            seen.add(nxt_id)
            chain.append(cur)
        return chain


__all__ = ["AsOfView"]
