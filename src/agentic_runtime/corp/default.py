"""
default.py — klijent nula (the own repo as client zero) (F7.0).

The whole F7 Business Plane is proven on **klijent nula** — the own repo — end to
end before any real client. Client zero is the honest baseline seed: a real,
constructible client + one job whose only mandate is the passthrough `default`
mandate (so the seeded job references authority that actually exists). Its build
is validated against the mandate `default_registry`, so the `mandate_ids`
reference is proven at construction, not assumed.
"""
from __future__ import annotations

from typing import Any

from ..mandate import DEFAULT_MANDATE_ID, default_registry
from .domain import ClientRecord, JobRecord, JobStatus
from .registry import CorpRegistry

CLIENT_ZERO_ID = "client-zero"
JOB_ZERO_ID = "job-zero"


def client_zero() -> ClientRecord:
    """Klijent nula: the own repo, the party F7 is proven against first."""
    return ClientRecord(
        client_id=CLIENT_ZERO_ID,
        name="Klijent nula (vlastiti repo)",
        notes="The own repo — every F7 Business Plane slice is proven here first.",
    )


def client_zero_job() -> JobRecord:
    """The seed job for klijent nula, running under the passthrough default mandate."""
    return JobRecord(
        job_id=JOB_ZERO_ID,
        client_id=CLIENT_ZERO_ID,
        mandate_ids=(DEFAULT_MANDATE_ID,),
        repos=("aurel",),
        status=JobStatus.ACTIVE,
        title="Klijent nula — vlastiti razvoj",
    )


def default_corp_registry(*, mandate_registry: Any = None) -> CorpRegistry:
    """A registry containing only klijent nula + its seed job.

    Defaults to validating against the mandate `default_registry` so the seed
    job's `DEFAULT_MANDATE_ID` reference is proven at build (fail-closed).
    """
    if mandate_registry is None:
        mandate_registry = default_registry()
    return CorpRegistry.from_records(
        [client_zero()], [client_zero_job()], mandate_registry=mandate_registry,
    )
