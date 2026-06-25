"""Path governance closed-world validation (P1.7.0)."""
from __future__ import annotations

from typing import Any, Mapping

from .errors import PathGovernanceErrorCode, PathGovernanceUnknownFieldError


def validate_known_fields(
    raw: Mapping[str, Any],
    known_fields: frozenset[str],
    *,
    label: str = "payload",
) -> None:
    """Reject unknown fields in dict/factory inputs (closed-world)."""
    unknown = set(raw.keys()) - known_fields
    if unknown:
        raise PathGovernanceUnknownFieldError(
            f"{label}: unknown field(s): {', '.join(sorted(unknown))} — closed-world",
            code=PathGovernanceErrorCode.UNKNOWN_FIELD,
            field=sorted(unknown)[0],
            details={"unknown_fields": sorted(unknown), "label": label},
        )
