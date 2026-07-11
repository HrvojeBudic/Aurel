"""
domain.py — the Corp business-domain objects (F7.0).

The **Business Plane** wraps the mature governance machinery in a thin business
layer. A **job** (posao) is the business wrapper around one or more mandates: it
names *what work for which client* runs under *which authority*. A **client** is
the party the work is for (for private use, "klijent nula" = the own repo).

Doctrine (F6 unchanged): a job does **not** grant authority — authority stays the
mandate, enforced fail-closed in `runtime.submit`. Client/Job records are business
metadata + projections; a job's `mandate_ids` are *references* into the existing
`MandateRegistry` (reused, never copied). A `JobRecord` is un-constructible without
a `client_id` — you cannot mint a job that hides who it is for (structural
no-overclaim), mirroring how a `Mandate` is un-constructible without a scope.

This module is the data model + hashing only; resolution + reference validation is
`registry.py`, and the klijent-nula seed is `default.py`. Additive behind
`AUREL_CORP` (default OFF ⇒ no corp read-model, byte-identical F6 world).
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from enum import Enum

from ..core_types import canonical_json, new_id, now, sha

_FLAG = "AUREL_CORP"


def flag_enabled() -> bool:
    """True iff the corp flag is explicitly enabled (default OFF)."""
    return os.environ.get(_FLAG, "").strip() in ("1", "true", "TRUE", "on")


class JobStatus(str, Enum):
    """Closed-world lifecycle of a job. No free-form status strings."""

    PROPOSED = "proposed"   # drafted (e.g. by the Agency wizard), not yet accepted
    ACTIVE = "active"       # accepted and running under its mandates
    PAUSED = "paused"       # temporarily halted
    CLOSED = "closed"       # finished / archived


@dataclass(frozen=True)
class ClientRecord:
    """The party work is for. For private use, klijent nula = the own repo."""

    client_id: str
    name: str
    notes: str = ""
    created_at: float = field(default_factory=now)

    def __post_init__(self) -> None:
        for field_name in ("client_id", "name"):
            if not getattr(self, field_name):
                raise ValueError(f"ClientRecord requires a non-empty {field_name}")

    @staticmethod
    def make(name: str, *, notes: str = "") -> "ClientRecord":
        return ClientRecord(client_id=new_id("client"), name=name, notes=notes)

    def _hashable(self) -> dict:
        # created_at is deliberately excluded — the hash is a content identity.
        return {"client_id": self.client_id, "name": self.name, "notes": self.notes}

    @property
    def content_hash(self) -> str:
        """Deterministic content identity: same content ⇒ same hash."""
        return sha(canonical_json(self._hashable()))

    def to_dict(self) -> dict:
        return {**self._hashable(), "content_hash": self.content_hash}


@dataclass(frozen=True)
class JobRecord:
    """A business wrapper around mandates: what work, for which client, under which authority."""

    job_id: str
    client_id: str                                  # required — a job cannot hide who it is for
    mandate_ids: tuple[str, ...] = ()               # references into a MandateRegistry
    repos: tuple[str, ...] = ()                      # repo roots the job touches
    status: JobStatus = JobStatus.ACTIVE
    title: str = ""
    created_at: float = field(default_factory=now)

    def __post_init__(self) -> None:
        if not self.job_id:
            raise ValueError("JobRecord requires a non-empty job_id")
        if not self.client_id:
            raise ValueError("JobRecord requires a non-empty client_id (no-overclaim)")
        if not isinstance(self.status, JobStatus):
            raise TypeError("JobRecord requires a JobStatus (closed-world)")

    @staticmethod
    def make(
        client_id: str,
        *,
        mandate_ids: tuple[str, ...] = (),
        repos: tuple[str, ...] = (),
        status: JobStatus = JobStatus.ACTIVE,
        title: str = "",
    ) -> "JobRecord":
        return JobRecord(
            job_id=new_id("job"), client_id=client_id,
            mandate_ids=tuple(mandate_ids), repos=tuple(repos),
            status=status, title=title,
        )

    def _hashable(self) -> dict:
        # created_at is deliberately excluded — the hash is a content identity.
        return {
            "job_id": self.job_id,
            "client_id": self.client_id,
            "mandate_ids": list(self.mandate_ids),
            "repos": list(self.repos),
            "status": self.status.value,
            "title": self.title,
        }

    @property
    def content_hash(self) -> str:
        """Deterministic content identity: same content ⇒ same hash."""
        return sha(canonical_json(self._hashable()))

    def to_dict(self) -> dict:
        return {**self._hashable(), "content_hash": self.content_hash}
