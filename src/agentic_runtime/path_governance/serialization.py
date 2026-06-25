"""Path governance deterministic canonical serialization (P1.7.0)."""
from __future__ import annotations

import hashlib
import json
from enum import Enum
from typing import Any, Mapping

from .errors import PathGovernanceErrorCode, PathGovernanceSerializationError


def _to_jsonable(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if hasattr(value, "to_canonical_dict") and callable(value.to_canonical_dict):
        return value.to_canonical_dict()
    if isinstance(value, Mapping):
        return {
            str(key): _to_jsonable(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    if isinstance(value, (list, tuple)):
        return [_to_jsonable(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    raise PathGovernanceSerializationError(
        f"unsupported canonical value type: {type(value).__name__}",
        code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
    )


def to_canonical_dict(value: Any) -> dict[str, Any]:
    """Convert a path governance object into a deterministic canonical dict."""
    result = _to_jsonable(value)
    if not isinstance(result, dict):
        raise PathGovernanceSerializationError(
            "canonical dict conversion requires a mapping-compatible object",
            code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
        )
    return result


def to_canonical_json(value: Any) -> str:
    """Produce deterministic canonical JSON (sorted keys, compact separators)."""
    canonical = to_canonical_dict(value)
    return json.dumps(canonical, sort_keys=True, separators=(",", ":"))


def stable_hash(value: Any) -> str:
    """Compute stable SHA-256 hex digest of canonical JSON representation."""
    canonical = to_canonical_json(value)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
