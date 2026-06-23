"""Policy Resolution Context (P1.6.10 — Custos v0).

A first-class, deterministic, hash-ready context object describing what the
Custos v0 resolver knows about a requested action. It is the input to shadow-mode
policy resolution.

Architectural law:
  - A resolution context does not grant authority.
  - A resolution context does not enforce anything.
  - A resolution context is a deterministic description of a proposed action.
  - "Entity proposes, runtime disposes" — this object is the proposal surface.

P1.6.10 is shadow mode only. This context never blocks or mutates a command.
"""
from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping as MappingABC
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping

from .errors import PolicyResolutionContextError
from .risk_tiers import RiskTier


# ---------------------------------------------------------------------------
# Enforcement mode
# ---------------------------------------------------------------------------


class EnforcementMode(str, Enum):
    """Resolver enforcement mode.

    P1.6.10 only supports SHADOW. ENFORCE and SIMULATE are reserved names for
    future phases and must NOT be honored as active enforcement in this phase.
    """
    SHADOW = "shadow"
    ENFORCE = "enforce"   # reserved — not implemented in P1.6.10
    SIMULATE = "simulate"  # reserved — not implemented in P1.6.10


_VALID_RISK_TIERS = frozenset(t.value for t in RiskTier)

# Dangerous metadata keys — metadata must never become a shadow control plane.
CONTEXT_DANGEROUS_METADATA_KEYS: frozenset[str] = frozenset({
    "bypass_policy",
    "bypass_resolver",
    "force_allow",
    "force_deny",
    "skip_resolver",
    "disable_policy",
    "grant_authority",
})

# Closed-world top-level field set for from_dict loading.
CONTEXT_KNOWN_FIELDS: frozenset[str] = frozenset({
    "context_id",
    "agent_id",
    "operator_id",
    "command_id",
    "command_summary",
    "requested_action",
    "tool_name",
    "tool_category",
    "command_class",
    "risk_tier",
    "requested_sandbox_backend",
    "requested_filesystem_scope",
    "requested_egress",
    "requested_model",
    "requested_paths",
    "requested_network_targets",
    "prompt_source_types",
    "data_classes",
    "memory_write_intent",
    "touches_secrets",
    "writes_files",
    "runs_shell",
    "installs_packages",
    "requires_network",
    "metadata",
})

_STR_FIELDS = (
    "agent_id", "operator_id", "command_id", "requested_action",
    "tool_name", "tool_category", "command_class",
    "requested_sandbox_backend", "requested_filesystem_scope",
    "requested_egress", "requested_model",
)
_TUPLE_FIELDS = (
    "requested_paths", "requested_network_targets",
    "prompt_source_types", "data_classes",
)
_BOOL_FIELDS = (
    "memory_write_intent", "touches_secrets", "writes_files",
    "runs_shell", "installs_packages", "requires_network",
)


@dataclass(frozen=True)
class PolicyResolutionContext:
    """Deterministic description of a proposed action for shadow resolution."""
    context_id: str
    agent_id: str | None = None
    operator_id: str | None = None
    command_id: str | None = None
    command_summary: str = ""
    requested_action: str | None = None
    tool_name: str | None = None
    tool_category: str | None = None
    command_class: str | None = None
    risk_tier: str | None = None
    requested_sandbox_backend: str | None = None
    requested_filesystem_scope: str | None = None
    requested_egress: str | None = None
    requested_model: str | None = None
    requested_paths: tuple[str, ...] = ()
    requested_network_targets: tuple[str, ...] = ()
    prompt_source_types: tuple[str, ...] = ()
    data_classes: tuple[str, ...] = ()
    memory_write_intent: bool = False
    touches_secrets: bool = False
    writes_files: bool = False
    runs_shell: bool = False
    installs_packages: bool = False
    requires_network: bool = False
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.context_id, str) or not self.context_id.strip():
            raise PolicyResolutionContextError("context_id must be a non-empty string")
        if self.risk_tier is not None and self.risk_tier not in _VALID_RISK_TIERS:
            raise PolicyResolutionContextError(
                f"risk_tier '{self.risk_tier}' must be one of: "
                f"{', '.join(sorted(_VALID_RISK_TIERS))}"
            )
        for name in _BOOL_FIELDS:
            if not isinstance(getattr(self, name), bool):
                raise PolicyResolutionContextError(f"{name} must be boolean")
        for name in _TUPLE_FIELDS:
            value = getattr(self, name)
            if not isinstance(value, tuple) or any(not isinstance(v, str) for v in value):
                raise PolicyResolutionContextError(f"{name} must be a tuple of strings")
        if not isinstance(self.metadata, MappingABC):
            raise PolicyResolutionContextError("metadata must be a mapping")
        dangerous = set(self.metadata.keys()) & CONTEXT_DANGEROUS_METADATA_KEYS
        if dangerous:
            raise PolicyResolutionContextError(
                f"dangerous metadata key(s): {', '.join(sorted(dangerous))}"
            )

    # -- serialization -----------------------------------------------------

    def to_canonical_dict(self) -> dict[str, Any]:
        return policy_resolution_context_to_canonical_dict(self)

    @property
    def context_hash(self) -> str:
        return compute_policy_resolution_context_hash(self)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "PolicyResolutionContext":
        return load_policy_resolution_context_from_dict(data)


# ---------------------------------------------------------------------------
# Canonical serialization / hashing
# ---------------------------------------------------------------------------


def policy_resolution_context_to_canonical_dict(
    ctx: PolicyResolutionContext,
) -> dict[str, Any]:
    """Deterministic, sorted-key canonical dict. None values omitted; list-like
    fields sorted for stable ordering."""
    result: dict[str, Any] = {
        "context_id": ctx.context_id,
        "command_summary": ctx.command_summary,
        "memory_write_intent": ctx.memory_write_intent,
        "touches_secrets": ctx.touches_secrets,
        "writes_files": ctx.writes_files,
        "runs_shell": ctx.runs_shell,
        "installs_packages": ctx.installs_packages,
        "requires_network": ctx.requires_network,
        "metadata": dict(sorted(dict(ctx.metadata).items(), key=lambda i: i[0])),
    }
    for name in _STR_FIELDS + ("risk_tier",):
        value = getattr(ctx, name)
        if value is not None:
            result[name] = value
    for name in _TUPLE_FIELDS:
        value = getattr(ctx, name)
        if value:
            result[name] = sorted(value)
    return dict(sorted(result.items(), key=lambda i: i[0]))


def serialize_policy_resolution_context_canonical(
    ctx: PolicyResolutionContext,
) -> str:
    canonical = policy_resolution_context_to_canonical_dict(ctx)
    return json.dumps(canonical, sort_keys=True, separators=(",", ":"))


def compute_policy_resolution_context_hash(ctx: PolicyResolutionContext) -> str:
    canonical = serialize_policy_resolution_context_canonical(ctx)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Closed-world dict loader
# ---------------------------------------------------------------------------


def load_policy_resolution_context_from_dict(
    data: Mapping[str, Any],
) -> PolicyResolutionContext:
    if not isinstance(data, MappingABC):
        raise PolicyResolutionContextError("context data must be a mapping")

    present = set(data.keys())
    unknown = present - CONTEXT_KNOWN_FIELDS
    if unknown:
        raise PolicyResolutionContextError(
            f"unknown context field(s): {', '.join(sorted(unknown))} - closed-world"
        )
    if "context_id" not in data:
        raise PolicyResolutionContextError("context_id is required")

    kwargs: dict[str, Any] = {"context_id": data["context_id"]}

    for name in _STR_FIELDS + ("risk_tier",):
        if name in data and data[name] is not None:
            value = data[name]
            if not isinstance(value, str):
                raise PolicyResolutionContextError(f"{name} must be a string")
            kwargs[name] = value

    if "command_summary" in data and data["command_summary"] is not None:
        if not isinstance(data["command_summary"], str):
            raise PolicyResolutionContextError("command_summary must be a string")
        kwargs["command_summary"] = data["command_summary"]

    for name in _TUPLE_FIELDS:
        if name in data and data[name] is not None:
            value = data[name]
            if not isinstance(value, (list, tuple)):
                raise PolicyResolutionContextError(f"{name} must be a list/tuple")
            kwargs[name] = tuple(str(v) for v in value)

    for name in _BOOL_FIELDS:
        if name in data and data[name] is not None:
            value = data[name]
            if not isinstance(value, bool):
                raise PolicyResolutionContextError(f"{name} must be boolean")
            kwargs[name] = value

    if "metadata" in data and data["metadata"] is not None:
        meta = data["metadata"]
        if not isinstance(meta, MappingABC):
            raise PolicyResolutionContextError("metadata must be a mapping")
        kwargs["metadata"] = dict(meta)

    return PolicyResolutionContext(**kwargs)
