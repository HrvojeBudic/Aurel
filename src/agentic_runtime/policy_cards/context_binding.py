"""Policy resolution context binding helpers (P1.6.11).

The helpers in this module translate runtime-like request metadata into a
PolicyResolutionContext without importing or invoking the runtime. Dict inputs
are closed-world; lightweight objects are read by attribute only.
"""
from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping as MappingABC, Sequence as SequenceABC, Set as SetABC
from enum import Enum
from typing import Any, Mapping

from .errors import PolicyContextBindingError
from .resolution_context import (
    CONTEXT_DANGEROUS_METADATA_KEYS,
    CONTEXT_KNOWN_FIELDS,
    PolicyResolutionContext,
    policy_resolution_context_to_canonical_dict,
)
from .risk_mapping import (
    RiskMappingResult,
    map_approval_risk_to_policy_tier,
    map_identity_risk_to_policy_tier,
    map_runtime_risk_to_policy_tier,
    normalize_risk_tier,
)

_BINDING_ALIAS_FIELDS: frozenset[str] = frozenset({
    "action",
    "approval_risk_class",
    "category",
    "command_name",
    "identity_risk",
    "policy_risk_tier",
    "risk",
    "runtime_risk",
    "summary",
    "tool",
})

BINDING_KNOWN_FIELDS: frozenset[str] = CONTEXT_KNOWN_FIELDS | _BINDING_ALIAS_FIELDS

_STR_FIELDS: tuple[str, ...] = (
    "agent_id", "operator_id", "command_id", "requested_action",
    "tool_name", "tool_category", "command_class",
    "requested_sandbox_backend", "requested_filesystem_scope",
    "requested_egress", "requested_model",
)
_TUPLE_FIELDS: tuple[str, ...] = (
    "requested_paths", "requested_network_targets",
    "prompt_source_types", "data_classes",
)
_BOOL_FIELDS: tuple[str, ...] = (
    "memory_write_intent", "touches_secrets", "writes_files",
    "runs_shell", "installs_packages", "requires_network",
)

_OBJECT_FIELDS: tuple[str, ...] = tuple(sorted(BINDING_KNOWN_FIELDS))


def _ensure_mapping(data: Mapping[str, Any] | None) -> dict[str, Any]:
    if data is None:
        return {}
    if not isinstance(data, MappingABC):
        raise PolicyContextBindingError("context binding data must be a mapping")
    unknown = set(data.keys()) - BINDING_KNOWN_FIELDS
    if unknown:
        raise PolicyContextBindingError(
            f"unknown context binding field(s): {', '.join(sorted(unknown))} - closed-world"
        )
    return dict(data)


def _enum_or_str(value: object, field: str) -> str:
    if isinstance(value, Enum) and isinstance(value.value, str):
        value = value.value
    if not isinstance(value, str) or not value.strip():
        raise PolicyContextBindingError(f"{field} must be a non-empty string")
    return value.strip()


def _optional_str(raw: Mapping[str, Any], field: str) -> str | None:
    value = raw.get(field)
    if value is None:
        return None
    return _enum_or_str(value, field)


def _bool_value(raw: Mapping[str, Any], field: str) -> bool:
    value = raw.get(field, False)
    if value is None:
        return False
    if not isinstance(value, bool):
        raise PolicyContextBindingError(f"{field} must be boolean")
    return value


def _string_tuple(raw: Mapping[str, Any], field: str) -> tuple[str, ...]:
    value = raw.get(field, ())
    if value is None:
        return ()
    if isinstance(value, str) or not isinstance(value, (SequenceABC, SetABC)):
        raise PolicyContextBindingError(f"{field} must be a list/tuple/set of strings")
    normalized: list[str] = []
    for item in value:
        normalized.append(_enum_or_str(item, field))
    return tuple(sorted(set(normalized)))


def _json_safe(value: object, path: str) -> None:
    if value is None or isinstance(value, (str, int, float, bool)):
        return
    if isinstance(value, list | tuple):
        for idx, item in enumerate(value):
            _json_safe(item, f"{path}[{idx}]")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise PolicyContextBindingError(f"metadata key at {path} must be a string")
            _json_safe(item, f"{path}.{key}")
        return
    raise PolicyContextBindingError(f"metadata value at {path} is not JSON-safe")


def _metadata(raw: Mapping[str, Any]) -> dict[str, Any]:
    value = raw.get("metadata", {})
    if value is None:
        return {}
    if not isinstance(value, MappingABC):
        raise PolicyContextBindingError("metadata must be a mapping")
    metadata = dict(value)
    bad_keys = set(metadata.keys()) & CONTEXT_DANGEROUS_METADATA_KEYS
    if bad_keys:
        raise PolicyContextBindingError(
            f"dangerous metadata key(s): {', '.join(sorted(bad_keys))}"
        )
    _json_safe(metadata, "metadata")
    json.dumps(metadata, sort_keys=True, separators=(",", ":"))
    return dict(sorted(metadata.items(), key=lambda item: item[0]))


def _take_alias(raw: dict[str, Any], canonical: str, aliases: tuple[str, ...]) -> None:
    present = [name for name in (canonical, *aliases) if name in raw and raw[name] is not None]
    if not present:
        return
    first = present[0]
    first_value = raw[first]
    for name in present[1:]:
        if raw[name] != first_value:
            raise PolicyContextBindingError(
                f"conflicting values for {canonical}: {first} and {name}"
            )
    raw[canonical] = first_value
    for alias in aliases:
        raw.pop(alias, None)


def _risk_result(raw: Mapping[str, Any]) -> RiskMappingResult:
    if raw.get("risk_tier") is not None:
        return normalize_risk_tier(raw["risk_tier"])
    if raw.get("policy_risk_tier") is not None:
        return normalize_risk_tier(raw["policy_risk_tier"])
    if raw.get("approval_risk_class") is not None:
        return map_approval_risk_to_policy_tier(raw["approval_risk_class"])
    if raw.get("runtime_risk") is not None:
        return map_runtime_risk_to_policy_tier(raw["runtime_risk"])
    if raw.get("risk") is not None:
        return normalize_risk_tier(raw["risk"])
    if raw.get("identity_risk") is not None:
        return map_identity_risk_to_policy_tier(raw["identity_risk"])
    return normalize_risk_tier(None)


def _default_context_id(kwargs: Mapping[str, Any]) -> str:
    payload = json.dumps(kwargs, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return f"ctx-{digest[:24]}"


def build_policy_resolution_context(
    data: Mapping[str, Any] | None = None,
    **kwargs: Any,
) -> PolicyResolutionContext:
    """Build a deterministic PolicyResolutionContext from runtime-like metadata."""
    raw = _ensure_mapping(data)
    if kwargs:
        raw.update(_ensure_mapping(kwargs))

    _take_alias(raw, "requested_action", ("action", "command_name"))
    _take_alias(raw, "command_summary", ("summary",))
    _take_alias(raw, "tool_name", ("tool",))
    _take_alias(raw, "tool_category", ("category",))

    risk = _risk_result(raw)

    normalized: dict[str, Any] = {}
    for field in _STR_FIELDS:
        value = _optional_str(raw, field)
        if value is not None:
            normalized[field] = value
    for field in _TUPLE_FIELDS:
        value = _string_tuple(raw, field)
        if value:
            normalized[field] = value
    for field in _BOOL_FIELDS:
        normalized[field] = _bool_value(raw, field)

    if raw.get("command_summary") is not None:
        normalized["command_summary"] = _enum_or_str(raw["command_summary"], "command_summary")
    if risk.normalized_tier is not None:
        normalized["risk_tier"] = risk.normalized_tier

    meta = _metadata(raw)
    if risk.source_value is not None:
        meta = {
            **meta,
            "risk_mapping_known": risk.known,
            "risk_mapping_reason": risk.reason_code,
            "risk_mapping_source_family": risk.source_family,
        }
    normalized["metadata"] = meta

    context_id = raw.get("context_id")
    if context_id is None:
        context_id = raw.get("command_id")
    if context_id is None:
        context_id = _default_context_id(normalized)
    normalized["context_id"] = _enum_or_str(context_id, "context_id")

    return PolicyResolutionContext(**normalized)


def normalize_resolution_context(
    value: PolicyResolutionContext | Mapping[str, Any],
) -> PolicyResolutionContext:
    """Normalize an existing context or closed-world dict into stable field order."""
    if isinstance(value, PolicyResolutionContext):
        return PolicyResolutionContext.from_dict(
            policy_resolution_context_to_canonical_dict(value)
        )
    return build_policy_resolution_context(value)


def _object_to_binding_dict(obj: object) -> dict[str, Any]:
    if isinstance(obj, MappingABC):
        return _ensure_mapping(obj)
    result: dict[str, Any] = {}
    for field in _OBJECT_FIELDS:
        if hasattr(obj, field):
            result[field] = getattr(obj, field)
    return result


def context_from_command_like(
    command_like: object,
    **overrides: Any,
) -> PolicyResolutionContext:
    """Build context from a command-shaped dict or lightweight object."""
    data = _object_to_binding_dict(command_like)
    data.update(_ensure_mapping(overrides))
    return build_policy_resolution_context(data)


def context_from_tool_invocation_like(
    tool_invocation_like: object,
    **overrides: Any,
) -> PolicyResolutionContext:
    """Build context from a tool-invocation-shaped dict or lightweight object."""
    data = _object_to_binding_dict(tool_invocation_like)
    data.update(_ensure_mapping(overrides))
    return build_policy_resolution_context(data)


def context_from_runtime_request_like(
    runtime_request_like: object,
    **overrides: Any,
) -> PolicyResolutionContext:
    """Build context from runtime-like metadata without importing runtime code."""
    data = _object_to_binding_dict(runtime_request_like)
    data.update(_ensure_mapping(overrides))
    return build_policy_resolution_context(data)
