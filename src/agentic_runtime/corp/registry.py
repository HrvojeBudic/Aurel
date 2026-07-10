"""
registry.py — Corp domain resolution + reference validation (F7.0).

The registry turns a `job_id`/`client_id` into a concrete record and — the point
of F7.0 — validates the *references* between the business layer and the authority
layer at build time, fail-closed:

  * every job's `client_id` must resolve to a known client, and
  * every `mandate_id` a job references must resolve in the given `MandateRegistry`.

A job that references an unknown client or an unknown mandate cannot be built —
the business layer can never point at authority that does not exist. Resolution is
otherwise fail-closed: an unknown id resolves to `None`. The registry holds the
`MandateRegistry` reference it validated against (reused, not copied) so downstream
projections (F7.1 cost attribution, F7.5 portfolio) can walk job → mandate → scope.
"""
from __future__ import annotations

from typing import Any, Iterable, Optional

from ..core_types import canonical_json, sha
from .domain import ClientRecord, JobRecord


class CorpValidationError(ValueError):
    """A job references an unknown client or mandate. Fail-closed at build time."""


class ClientNotFound(KeyError):
    """A client_id with no registered client. Fail-closed."""


class JobNotFound(KeyError):
    """A job_id with no registered job. Fail-closed."""


class CorpRegistry:
    """Deterministic, in-memory resolution over a fixed set of clients + jobs."""

    def __init__(
        self,
        clients: Iterable[ClientRecord],
        jobs: Iterable[JobRecord],
        *,
        mandate_registry: Any = None,
    ) -> None:
        self._clients: dict[str, ClientRecord] = {}
        for c in clients:
            self._clients[c.client_id] = c
        self._jobs: dict[str, JobRecord] = {}
        for j in jobs:
            self._jobs[j.job_id] = j
        self._mandate_registry = mandate_registry

    @classmethod
    def from_records(
        cls,
        clients: Iterable[ClientRecord],
        jobs: Iterable[JobRecord],
        *,
        mandate_registry: Any = None,
    ) -> "CorpRegistry":
        """Build a registry, validating client + mandate references fail-closed.

        Every job's `client_id` must be among `clients`. When a `mandate_registry`
        is given, every `mandate_id` a job references must resolve there too — a
        job pointing at authority that does not exist is un-buildable.
        """
        clients = tuple(clients)
        jobs = tuple(jobs)
        client_ids = {c.client_id for c in clients}
        for j in jobs:
            if j.client_id not in client_ids:
                raise CorpValidationError(
                    f"job {j.job_id!r} references unknown client {j.client_id!r}"
                )
            if mandate_registry is not None:
                for mid in j.mandate_ids:
                    if mandate_registry.resolve(mid) is None:
                        raise CorpValidationError(
                            f"job {j.job_id!r} references unknown mandate {mid!r}"
                        )
        return cls(clients, jobs, mandate_registry=mandate_registry)

    @property
    def mandate_registry(self) -> Any:
        return self._mandate_registry

    # --- resolution (fail-closed) ----------------------------------------------

    def resolve_client(self, client_id: str) -> Optional[ClientRecord]:
        return self._clients.get(client_id)

    def resolve_job(self, job_id: str) -> Optional[JobRecord]:
        return self._jobs.get(job_id)

    def resolve_client_or_raise(self, client_id: str) -> ClientRecord:
        c = self._clients.get(client_id)
        if c is None:
            raise ClientNotFound(client_id)
        return c

    def resolve_job_or_raise(self, job_id: str) -> JobRecord:
        j = self._jobs.get(job_id)
        if j is None:
            raise JobNotFound(job_id)
        return j

    # --- enumeration (deterministic) -------------------------------------------

    def client_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._clients))

    def job_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._jobs))

    def jobs_for_client(self, client_id: str) -> tuple[JobRecord, ...]:
        """All jobs for a client, deterministically ordered by job_id."""
        return tuple(
            self._jobs[k] for k in sorted(self._jobs)
            if self._jobs[k].client_id == client_id
        )

    def canonical_hash(self) -> str:
        """Deterministic digest of the whole registry (same set ⇒ same hash)."""
        return sha(canonical_json({
            "clients": [self._clients[k].to_dict() for k in sorted(self._clients)],
            "jobs": [self._jobs[k].to_dict() for k in sorted(self._jobs)],
        }))
