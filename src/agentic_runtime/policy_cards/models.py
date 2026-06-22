"""Policy Card foundation models (P1.6.0).

First-class, typed, versioned, scoped, validated, deterministic, hash-ready
governance objects. Policy cards are the behavioral contract substrate for
AurelCore. They do not grant authority, bypass governance, or enforce runtime
behavior — they describe it so the resolver (future) can evaluate it.

Architectural law:
  - Policy is not documentation.
  - Policy is not a prompt.
  - Policy is not advice.
  - Policy is not comments in code.
  - Policy is a governed runtime object.
  - A policy card must never grant authority merely by existing.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class PolicyCardKind(str, Enum):
    """The category of behavioral contract this card represents.

    P1.6.0 defines the taxonomy; P1.6.3–P1.6.11 implement per-kind behavior.
    """
    RISK_TIER = "risk_tier"
    HUMAN_OVERSIGHT = "human_oversight"
    DATA_RESIDENCY = "data_residency"
    TOOL_PERMISSION = "tool_permission"
    MEMORY_WRITE = "memory_write"
    PROMPT = "prompt"
    SANDBOX = "sandbox"
    MODEL_ROUTING = "model_routing"
    BUSINESS_PROCESS = "business_process"
    GENERIC = "generic"


class PolicyCardStatus(str, Enum):
    """Runtime resolvability state.

    draft     — inspectable but not enforceable
    active    — future runtime-resolvable
    deprecated — should not silently enforce
    disabled  — must not resolve
    test_only — simulation/test use only
    """
    DRAFT = "draft"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    DISABLED = "disabled"
    TEST_ONLY = "test_only"


class PolicyCardScopeType(str, Enum):
    """The domain to which this policy card applies."""
    GLOBAL = "global"
    RUNTIME = "runtime"
    TOOL = "tool"
    MODEL = "model"
    MEMORY = "memory"
    PROMPT = "prompt"
    SANDBOX = "sandbox"
    WORKFLOW = "workflow"
    AGENT = "agent"
    BUSINESS = "business"


# ---------------------------------------------------------------------------
# Sub-object dataclasses (frozen)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PolicyCardIdentity:
    """Stable identity for deterministic serialization and hash.

    card_id   — unique identifier for this policy card
    slug      — machine-friendly short name (kebab-case)
    name      — human-readable label
    version   — simple version string (e.g. "1", "1.0", "v1")
    namespace — logical grouping (e.g. "aurel_core", "aurel_exec")
    """
    card_id: str
    slug: str
    name: str
    version: str
    namespace: str


@dataclass(frozen=True)
class PolicyCardScope:
    """Minimal scope object — defines what this policy card applies to.

    scope_type — known scope type enum value
    scope_id   — optional instance identifier (tool name, model id, etc.)
    applies_to — tuple of additional target identifiers
    """
    scope_type: PolicyCardScopeType
    scope_id: str | None = None
    applies_to: tuple[str, ...] = ()


@dataclass(frozen=True)
class PolicyCardRiskBinding:
    """Seed risk structure for future risk-tier engine (P1.6.3+).

    Does not enforce risk semantics yet — only defines shape and validation.
    """
    risk_tier: str | None = None
    risk_floor: str | None = None
    risk_ceiling: str | None = None
    requires_oversight: bool = False


@dataclass(frozen=True)
class PolicyCardAuthorityBinding:
    """Seed authority structure.

    Critical rule: authority binding may define required authority or
    constraints. It must NOT grant authority. It must NOT bypass operator
    authority.

    authority_scope    — e.g. "agent", "runtime", "memory"
    required_authority — e.g. "operator", "runtime_admin"
    operator_required  — operator must explicitly consent
    delegation_allowed — can authority be delegated downstream
    """
    authority_scope: str | None = None
    required_authority: str | None = None
    operator_required: bool = False
    delegation_allowed: bool = False


@dataclass(frozen=True)
class PolicyCardSource:
    """Source/attestation readiness for P1.7 path governance.

    raw_source_hash — SHA-256 of raw source bytes (pre-parsing)
    canonical_hash  — SHA-256 of canonical typed representation
    source_path     — file path or logical source identifier
    loaded_at       — ISO timestamp of load time
    """
    source_type: str
    source_path: str | None = None
    raw_source_hash: str | None = None
    canonical_hash: str | None = None
    loaded_at: str | None = None


@dataclass(frozen=True)
class PolicyCardValidationIssue:
    """Structured validation issue — error or warning."""
    code: str
    message: str
    field: str | None = None
    severity: str = "error"


@dataclass(frozen=True)
class PolicyCardValidationResult:
    """Structured validation result for a policy card.

    valid          — True iff zero errors
    errors         — tuple of blocking issues
    warnings       — tuple of non-blocking issues
    card_id        — the card's identity, if available
    canonical_hash — the card's canonical hash, if computable
    """
    valid: bool
    errors: tuple[PolicyCardValidationIssue, ...]
    warnings: tuple[PolicyCardValidationIssue, ...]
    card_id: str | None = None
    canonical_hash: str | None = None


# ---------------------------------------------------------------------------
# Top-level Policy Card
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PolicyCard:
    """First-class governed policy card.

    schema_version    — Policy Card Schema version (e.g. "1.0")
    identity          — stable identity (id, slug, name, version, namespace)
    kind              — policy category
    status            — resolvability state
    scope             — what this card applies to
    description       — human-readable description of intent
    risk_binding      — optional risk constraints (seed)
    authority_binding — optional authority constraints (seed)
    source            — optional source attestation readiness
    metadata          — non-authoritative descriptive information only
    """
    schema_version: str
    identity: PolicyCardIdentity
    kind: PolicyCardKind
    status: PolicyCardStatus
    scope: PolicyCardScope
    description: str
    risk_binding: PolicyCardRiskBinding | None = None
    authority_binding: PolicyCardAuthorityBinding | None = None
    source: PolicyCardSource | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)
