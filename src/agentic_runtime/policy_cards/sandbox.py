"""Sandbox Policy Card model (P1.6.9).

Defines sandbox policy semantics for AurelCore policy cards. Sandbox policy
cards govern sandbox backends, filesystem scope, egress, command classes, risk
tier-to-posture mappings, and approval requirements. They are declarative,
deterministic, closed-world, hash-ready, and deny-by-default.

P1.6.9 defines sandbox law. P1.6.10 begins interpreting that law.
P1.6.17 later bridges sandbox policy into runtime sandbox behavior.

Architectural law:
  - Sandbox policy cards do not grant authority.
  - Sandbox policy cards do not enforce sandbox behavior at runtime.
  - Sandbox policy cards do not implement Docker or Bubblewrap backends.
  - Sandbox policy cards do not modify AgenticRuntime.submit().
  - Sandbox policy cards do not implement the Custos resolver.
  - Sandbox policy cards remain compatible with generic PolicyCard(kind="sandbox").
  - UNSAFE_LOCAL must be treated as dangerous for high-risk contexts.
  - Filesystem default posture is deny / least privilege.
  - Egress default posture is NO_EGRESS / DENY_NETWORK.
  - Command class default posture is deny unknown/destructive/secret-touching.
  - ANY_EGRESS requires explicit high-authority policy semantics.
  - UNKNOWN_COMMAND should deny or require approval.
  - DESTRUCTIVE_COMMAND should deny unless explicitly permitted by high authority.
  - NETWORK_COMMAND must require compatible egress posture.
  - PACKAGE_INSTALL should require approval or isolated backend.
  - SHELL_COMMAND should require approval or explicit policy allowance.
"""
from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping as MappingABC
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping, TypeVar

from .errors import (
    PolicyCardError,
    SandboxPolicyCardError,
    SandboxPolicyCardDecisionError,
    SandboxPolicyCardUnknownFieldError,
    SandboxPolicyCardUnsafeFieldError,
    SandboxPolicyCardValidationError,
)
from .models import (
    PolicyCard,
    PolicyCardIdentity,
    PolicyCardKind,
    PolicyCardScope,
    PolicyCardScopeType,
    PolicyCardStatus,
)
from .risk_tiers import RiskTier
from .serialization import policy_card_to_canonical_dict
from .validation import load_policy_card_from_dict


# ---------------------------------------------------------------------------
# Enums (sandbox policy vocabulary)
# ---------------------------------------------------------------------------


class SandboxBackend(str, Enum):
    """Sandbox backend/posture options — semantic only, not runtime backends."""
    UNSAFE_LOCAL = "unsafe_local"
    RESTRICTED_LOCAL = "restricted_local"
    DOCKER = "docker"
    BUBBLEWRAP = "bubblewrap"
    DENY_EXECUTION = "deny_execution"


class FilesystemScope(str, Enum):
    """Filesystem access scope postures."""
    NO_FILESYSTEM = "no_filesystem"
    TEMP_ONLY = "temp_only"
    READ_ONLY_PROJECT = "read_only_project"
    READ_WRITE_PROJECT = "read_write_project"
    READ_ONLY_ALLOWLIST = "read_only_allowlist"
    READ_WRITE_ALLOWLIST = "read_write_allowlist"
    DENY_HOST_FS = "deny_host_fs"


class EgressPolicy(str, Enum):
    """Network/egress permission postures."""
    NO_EGRESS = "no_egress"
    LOCALHOST_ONLY = "localhost_only"
    ALLOWLIST_ONLY = "allowlist_only"
    PRIVATE_NETWORK_ONLY = "private_network_only"
    ANY_EGRESS = "any_egress"
    DENY_NETWORK = "deny_network"


class CommandClass(str, Enum):
    """Command classification for sandbox policy."""
    READ_ONLY_COMMAND = "read_only_command"
    WRITE_COMMAND = "write_command"
    SHELL_COMMAND = "shell_command"
    PACKAGE_INSTALL = "package_install"
    NETWORK_COMMAND = "network_command"
    PROCESS_CONTROL = "process_control"
    SECRET_TOUCHING_COMMAND = "secret_touching_command"  # nosec B105 - command-class taxonomy label, not a credential
    DESTRUCTIVE_COMMAND = "destructive_command"
    UNKNOWN_COMMAND = "unknown_command"


class SandboxCommandDecision(str, Enum):
    """Per-rule decision outcome within a command class rule — semantic, not enforced."""
    ALLOW = "allow"
    DENY = "deny"
    APPROVAL_REQUIRED = "approval_required"
    EXPLICIT_CONFIRMATION_REQUIRED = "explicit_confirmation_required"
    SANDBOX_REQUIRED = "sandbox_required"
    READ_ONLY = "read_only"
    LOCAL_ONLY = "local_only"


class ApprovalRequirement(str, Enum):
    """Approval requirement flags for risky sandbox behavior."""
    APPROVAL_REQUIRED_FOR_WRITE = "approval_required_for_write"
    APPROVAL_REQUIRED_FOR_NETWORK = "approval_required_for_network"
    APPROVAL_REQUIRED_FOR_SHELL = "approval_required_for_shell"
    APPROVAL_REQUIRED_FOR_PACKAGE_INSTALL = "approval_required_for_package_install"
    APPROVAL_REQUIRED_FOR_SECRETS = "approval_required_for_secrets"
    APPROVAL_REQUIRED_FOR_DESTRUCTIVE = "approval_required_for_destructive"
    APPROVAL_REQUIRED_FOR_UNSAFE_LOCAL = "approval_required_for_unsafe_local"


# ---------------------------------------------------------------------------
# Valid value sets
# ---------------------------------------------------------------------------

_VALID_BACKENDS = frozenset(b.value for b in SandboxBackend)
_VALID_FILESYSTEM_SCOPES = frozenset(s.value for s in FilesystemScope)
_VALID_EGRESS_POLICIES = frozenset(e.value for e in EgressPolicy)
_VALID_COMMAND_CLASSES = frozenset(c.value for c in CommandClass)
_VALID_SANDBOX_DECISIONS = frozenset(d.value for d in SandboxCommandDecision)
_VALID_APPROVAL_REQUIREMENTS = frozenset(a.value for a in ApprovalRequirement)
_VALID_RISK_TIER_VALUES = frozenset(t.value for t in RiskTier)

# Backend ordering for posture comparison (higher index = more restrictive/isolated)
_BACKEND_ORDER: dict[str, int] = {
    "unsafe_local": 0,
    "restricted_local": 1,
    "bubblewrap": 2,
    "docker": 2,
    "deny_execution": 3,
}

# Filesystem scope ordering (higher index = more restrictive)
_FS_SCOPE_ORDER: dict[str, int] = {
    "read_write_project": 0,
    "read_only_project": 1,
    "read_write_allowlist": 2,
    "read_only_allowlist": 3,
    "temp_only": 4,
    "no_filesystem": 5,
    "deny_host_fs": 6,
}

# Egress policy ordering (higher index = more restrictive)
_EGRESS_ORDER: dict[str, int] = {
    "any_egress": 0,
    "private_network_only": 1,
    "allowlist_only": 2,
    "localhost_only": 3,
    "no_egress": 4,
    "deny_network": 5,
}

# Known danger patterns for path validation
_SECRETS_PATH_PATTERNS = frozenset({
    "/etc/passwd", "/etc/shadow", "/root/", "/home/*/.ssh",
    "/home/*/.aws", "/home/*/.gcloud", ".env", "*.env",
    "secrets/", "credentials/", "tokens/", "*.key", "*.pem",
    "/var/run/docker.sock", "/proc/", "/sys/",
})

_PATH_ESCAPE_PATTERNS = frozenset({
    "..", "/..", "../", "/../",
})


# ---------------------------------------------------------------------------
# Frozen Dataclasses — Rule objects
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SandboxBackendRule:
    """A single backend posture rule within a sandbox policy card."""
    rule_id: str
    allowed_backends: tuple[SandboxBackend, ...] = ()
    denied_backends: tuple[SandboxBackend, ...] = ()
    minimum_posture: SandboxBackend | None = None
    description: str = ""


@dataclass(frozen=True)
class SandboxFilesystemScopeRule:
    """A single filesystem scope rule within a sandbox policy card."""
    rule_id: str
    scope: FilesystemScope | None = None
    allowed_paths: tuple[str, ...] = ()
    denied_paths: tuple[str, ...] = ()
    allowlist_paths: tuple[str, ...] = ()
    description: str = ""


@dataclass(frozen=True)
class SandboxEgressRule:
    """A single egress policy rule within a sandbox policy card."""
    rule_id: str
    egress_policy: EgressPolicy | None = None
    allowed_targets: tuple[str, ...] = ()
    denied_targets: tuple[str, ...] = ()
    description: str = ""


@dataclass(frozen=True)
class SandboxCommandClassRule:
    """A single command class rule within a sandbox policy card."""
    rule_id: str
    command_class: CommandClass
    decision: SandboxCommandDecision = SandboxCommandDecision.DENY
    required_egress_policy: EgressPolicy | None = None
    required_backend: SandboxBackend | None = None
    risk_ceiling: str | None = None
    required_oversight: str | None = None
    description: str = ""


@dataclass(frozen=True)
class RiskTierSandboxMapping:
    """Maps a risk tier to minimum sandbox posture requirements."""
    risk_tier: RiskTier
    minimum_backend: SandboxBackend
    minimum_filesystem_scope: FilesystemScope = FilesystemScope.NO_FILESYSTEM
    minimum_egress_policy: EgressPolicy = EgressPolicy.NO_EGRESS
    requires_approval: bool = False
    requires_isolated_backend: bool = False
    description: str = ""


# ---------------------------------------------------------------------------
# Frozen Dataclasses — Decision structures
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SandboxPolicyViolation:
    """A policy violation found during evaluation."""
    code: str
    message: str
    field: str | None = None
    severity: str = "error"


@dataclass(frozen=True)
class SandboxPolicyWarning:
    """A policy warning found during evaluation."""
    code: str
    message: str
    field: str | None = None


@dataclass(frozen=True)
class SandboxPolicyDecisionInput:
    """Resolver-ready input structure for P1.6.10 Custos consumption."""
    command_class: CommandClass | None = None
    risk_tier: RiskTier | None = None
    requested_backend: SandboxBackend | None = None
    requested_filesystem_scope: FilesystemScope | None = None
    requested_egress: EgressPolicy | None = None
    touches_secrets: bool = False
    writes_files: bool = False
    runs_shell: bool = False
    installs_packages: bool = False
    requested_paths: tuple[str, ...] = ()
    requested_network_targets: tuple[str, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SandboxPolicyDecision:
    """Resolver-ready decision output structure for P1.6.10 Custos consumption."""
    allowed: bool
    approval_required: bool
    required_backend_minimum: SandboxBackend | None = None
    allowed_backends: tuple[SandboxBackend, ...] = ()
    denied_backends: tuple[SandboxBackend, ...] = ()
    effective_filesystem_scope: FilesystemScope | None = None
    effective_egress_policy: EgressPolicy | None = None
    violations: tuple[SandboxPolicyViolation, ...] = ()
    warnings: tuple[SandboxPolicyWarning, ...] = ()
    reason_codes: tuple[str, ...] = ()
    source_card_id: str | None = None
    canonical_hash: str | None = None


# ---------------------------------------------------------------------------
# Frozen Dataclasses — Validation
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SandboxValidationIssue:
    code: str
    message: str
    field: str | None = None
    severity: str = "error"


@dataclass(frozen=True)
class SandboxValidationResult:
    valid: bool
    errors: tuple[SandboxValidationIssue, ...]
    warnings: tuple[SandboxValidationIssue, ...]
    card_id: str | None = None
    canonical_hash: str | None = None


@dataclass(frozen=True)
class SandboxPolicyCard:
    policy_card: PolicyCard
    schema_version: str
    backend_rules: tuple[SandboxBackendRule, ...] = ()
    filesystem_rules: tuple[SandboxFilesystemScopeRule, ...] = ()
    egress_rules: tuple[SandboxEgressRule, ...] = ()
    command_rules: tuple[SandboxCommandClassRule, ...] = ()
    risk_tier_mappings: tuple[RiskTierSandboxMapping, ...] = ()
    approval_policy: frozenset[ApprovalRequirement] = field(default_factory=frozenset)
    metadata: Mapping[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Default rule tuples (used by create_default_sandbox_policy_card and schema export)
# ---------------------------------------------------------------------------

DEFAULT_BACKEND_RULES: tuple[SandboxBackendRule, ...] = (
    SandboxBackendRule(
        rule_id="backend-restricted-local-default",
        allowed_backends=(SandboxBackend.RESTRICTED_LOCAL,),
        denied_backends=(
            SandboxBackend.UNSAFE_LOCAL,
        ),
        minimum_posture=SandboxBackend.RESTRICTED_LOCAL,
        description="Default posture: restricted local only. Unsafe local denied.",
    ),
)

DEFAULT_FILESYSTEM_RULES: tuple[SandboxFilesystemScopeRule, ...] = (
    SandboxFilesystemScopeRule(
        rule_id="filesystem-default-deny",
        scope=FilesystemScope.NO_FILESYSTEM,
        denied_paths=(
            "/etc/passwd", "/etc/shadow", "/root", "/home/*/.ssh",
            "/home/*/.aws", "/home/*/.gcloud", "*.env", ".env",
            "secrets/", "credentials/", "tokens/", "*.key", "*.pem",
        ),
        description="Default deny-by-default filesystem posture. Secrets paths denied.",
    ),
    SandboxFilesystemScopeRule(
        rule_id="filesystem-readonly-project",
        scope=FilesystemScope.READ_ONLY_PROJECT,
        denied_paths=(
            "/etc/passwd", "/etc/shadow", "/root", "/home/*/.ssh",
            "/home/*/.aws", "/home/*/.gcloud", "*.env", ".env",
            "secrets/", "credentials/", "tokens/", "*.key", "*.pem",
        ),
        description="Read-only project filesystem with secrets paths denied.",
    ),
)

DEFAULT_EGRESS_RULES: tuple[SandboxEgressRule, ...] = (
    SandboxEgressRule(
        rule_id="egress-default-deny",
        egress_policy=EgressPolicy.NO_EGRESS,
        denied_targets=("*",),
        description="Default deny-by-default egress posture: no egress.",
    ),
    SandboxEgressRule(
        rule_id="egress-localhost-only",
        egress_policy=EgressPolicy.LOCALHOST_ONLY,
        allowed_targets=("127.0.0.0/8", "::1"),
        description="Localhost-only egress for safe local operations.",
    ),
)

DEFAULT_COMMAND_RULES: tuple[SandboxCommandClassRule, ...] = (
    SandboxCommandClassRule(
        rule_id="command-unknown-deny",
        command_class=CommandClass.UNKNOWN_COMMAND,
        decision=SandboxCommandDecision.DENY,
        description="Unknown command class denied by default.",
    ),
    SandboxCommandClassRule(
        rule_id="command-destructive-deny",
        command_class=CommandClass.DESTRUCTIVE_COMMAND,
        decision=SandboxCommandDecision.DENY,
        required_oversight="explicit_confirmation_required",
        risk_ceiling="R5",
        description="Destructive commands denied except by explicit high-authority allowance.",
    ),
    SandboxCommandClassRule(
        rule_id="command-secret-touching-deny",
        command_class=CommandClass.SECRET_TOUCHING_COMMAND,
        decision=SandboxCommandDecision.DENY,
        risk_ceiling="R4",
        description="Secret-touching commands denied by default.",
    ),
    SandboxCommandClassRule(
        rule_id="command-shell-approval-required",
        command_class=CommandClass.SHELL_COMMAND,
        decision=SandboxCommandDecision.APPROVAL_REQUIRED,
        required_backend=SandboxBackend.RESTRICTED_LOCAL,
        risk_ceiling="R4",
        required_oversight="approval_required",
        description="Shell commands require approval or explicit policy allowance.",
    ),
    SandboxCommandClassRule(
        rule_id="command-package-install-approval",
        command_class=CommandClass.PACKAGE_INSTALL,
        decision=SandboxCommandDecision.APPROVAL_REQUIRED,
        required_backend=SandboxBackend.DOCKER,
        risk_ceiling="R3",
        required_oversight="approval_required",
        description="Package install requires approval or isolated backend.",
    ),
    SandboxCommandClassRule(
        rule_id="command-network-restricted",
        command_class=CommandClass.NETWORK_COMMAND,
        decision=SandboxCommandDecision.SANDBOX_REQUIRED,
        required_egress_policy=EgressPolicy.ALLOWLIST_ONLY,
        risk_ceiling="R3",
        required_oversight="approval_required",
        description="Network commands require compatible egress posture.",
    ),
    SandboxCommandClassRule(
        rule_id="command-process-control-approval",
        command_class=CommandClass.PROCESS_CONTROL,
        decision=SandboxCommandDecision.SANDBOX_REQUIRED,
        required_backend=SandboxBackend.DOCKER,
        risk_ceiling="R4",
        required_oversight="approval_required",
        description="Process control commands require isolated backend.",
    ),
    SandboxCommandClassRule(
        rule_id="command-readonly-allowed",
        command_class=CommandClass.READ_ONLY_COMMAND,
        decision=SandboxCommandDecision.ALLOW,
        description="Read-only commands allowed.",
    ),
    SandboxCommandClassRule(
        rule_id="command-write-approval",
        command_class=CommandClass.WRITE_COMMAND,
        decision=SandboxCommandDecision.APPROVAL_REQUIRED,
        risk_ceiling="R3",
        required_oversight="review_recommended",
        description="Write commands require approval.",
    ),
)

DEFAULT_RISK_TIER_SANDBOX_MAPPINGS: tuple[RiskTierSandboxMapping, ...] = (
    RiskTierSandboxMapping(
        risk_tier=RiskTier.R0,
        minimum_backend=SandboxBackend.RESTRICTED_LOCAL,
        minimum_filesystem_scope=FilesystemScope.READ_ONLY_PROJECT,
        minimum_egress_policy=EgressPolicy.NO_EGRESS,
        requires_approval=False,
        requires_isolated_backend=False,
        description="R0 informational: restricted local sufficient.",
    ),
    RiskTierSandboxMapping(
        risk_tier=RiskTier.R1,
        minimum_backend=SandboxBackend.RESTRICTED_LOCAL,
        minimum_filesystem_scope=FilesystemScope.READ_ONLY_PROJECT,
        minimum_egress_policy=EgressPolicy.LOCALHOST_ONLY,
        requires_approval=False,
        requires_isolated_backend=False,
        description="R1 safe local read: restricted local allowed.",
    ),
    RiskTierSandboxMapping(
        risk_tier=RiskTier.R2,
        minimum_backend=SandboxBackend.RESTRICTED_LOCAL,
        minimum_filesystem_scope=FilesystemScope.READ_WRITE_PROJECT,
        minimum_egress_policy=EgressPolicy.LOCALHOST_ONLY,
        requires_approval=False,
        requires_isolated_backend=False,
        description="R2 reversible write: restricted local allowed, write scope permitted.",
    ),
    RiskTierSandboxMapping(
        risk_tier=RiskTier.R3,
        minimum_backend=SandboxBackend.RESTRICTED_LOCAL,
        minimum_filesystem_scope=FilesystemScope.READ_WRITE_PROJECT,
        minimum_egress_policy=EgressPolicy.ALLOWLIST_ONLY,
        requires_approval=True,
        requires_isolated_backend=False,
        description="R3 meaningful state change: restricted local or isolated, approval required.",
    ),
    RiskTierSandboxMapping(
        risk_tier=RiskTier.R4,
        minimum_backend=SandboxBackend.DOCKER,
        minimum_filesystem_scope=FilesystemScope.READ_WRITE_ALLOWLIST,
        minimum_egress_policy=EgressPolicy.ALLOWLIST_ONLY,
        requires_approval=True,
        requires_isolated_backend=True,
        description="R4 high impact: isolated backend required with approval.",
    ),
    RiskTierSandboxMapping(
        risk_tier=RiskTier.R5,
        minimum_backend=SandboxBackend.DOCKER,
        minimum_filesystem_scope=FilesystemScope.READ_WRITE_ALLOWLIST,
        minimum_egress_policy=EgressPolicy.ALLOWLIST_ONLY,
        requires_approval=True,
        requires_isolated_backend=True,
        description="R5 serious/irreversible: strict isolated backend with explicit operator approval.",
    ),
    RiskTierSandboxMapping(
        risk_tier=RiskTier.R6,
        minimum_backend=SandboxBackend.DENY_EXECUTION,
        minimum_filesystem_scope=FilesystemScope.NO_FILESYSTEM,
        minimum_egress_policy=EgressPolicy.DENY_NETWORK,
        requires_approval=True,
        requires_isolated_backend=False,
        description="R6 denied: execution denied.",
    ),
)

DEFAULT_APPROVAL_REQUIREMENTS: frozenset[ApprovalRequirement] = frozenset({
    ApprovalRequirement.APPROVAL_REQUIRED_FOR_WRITE,
    ApprovalRequirement.APPROVAL_REQUIRED_FOR_NETWORK,
    ApprovalRequirement.APPROVAL_REQUIRED_FOR_SHELL,
    ApprovalRequirement.APPROVAL_REQUIRED_FOR_PACKAGE_INSTALL,
    ApprovalRequirement.APPROVAL_REQUIRED_FOR_SECRETS,
    ApprovalRequirement.APPROVAL_REQUIRED_FOR_DESTRUCTIVE,
    ApprovalRequirement.APPROVAL_REQUIRED_FOR_UNSAFE_LOCAL,
})


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


_EnumT = TypeVar("_EnumT", bound=Enum)


def _make_issue(
    code: str,
    message: str,
    field: str | None = None,
    severity: str = "error",
) -> SandboxValidationIssue:
    return SandboxValidationIssue(
        code=code, message=message, field=field, severity=severity,
    )


def _enum_value(value: object) -> str | None:
    if isinstance(value, Enum):
        return str(value.value)
    if isinstance(value, str):
        return value
    return None


def _coerce_enum(
    raw: object,
    enum_type: type[_EnumT],
    valid_values: frozenset[str],
    field_name: str,
) -> _EnumT:
    if not isinstance(raw, str) or raw not in valid_values:
        raise SandboxPolicyCardValidationError(
            f"{field_name} value {raw!r} must be one of: "
            f"{', '.join(sorted(valid_values))}"
        )
    return enum_type(raw)


def _require_bool(raw: object, field_name: str) -> bool:
    if not isinstance(raw, bool):
        raise SandboxPolicyCardValidationError(f"{field_name} must be boolean")
    return raw


def _require_mapping(raw: object, field_name: str) -> Mapping[str, Any]:
    if not isinstance(raw, MappingABC):
        raise SandboxPolicyCardValidationError(f"{field_name} must be a mapping")
    return raw


def _check_mapping_fields(
    raw: Mapping[str, Any],
    known_fields: frozenset[str],
    dangerous_fields: frozenset[str],
    field_name: str,
) -> None:
    present = set(raw.keys())
    dangerous = present & dangerous_fields
    if dangerous:
        raise SandboxPolicyCardUnsafeFieldError(
            f"{field_name}: dangerous field(s): {', '.join(sorted(dangerous))}"
        )
    unknown = present - known_fields
    if unknown:
        raise SandboxPolicyCardUnknownFieldError(
            f"{field_name}: unknown field(s): {', '.join(sorted(unknown))} - closed-world"
        )


def _path_is_suspicious(path: str) -> bool:
    """Check if a path looks like a secrets path or escape attempt."""
    if not isinstance(path, str):
        return False

    # Check for escape patterns
    for escape in _PATH_ESCAPE_PATTERNS:
        if escape in path:
            return True

    # Check for absolute host paths that are suspicious
    if path.startswith("/etc/") or path.startswith("/root/"):
        return True
    if "/.ssh" in path or "/.aws" in path or "/.gcloud" in path:
        return True

    # Check for secrets-related patterns
    lowered = path.lower()
    for secret_pat in ("secrets/", "credentials/", "tokens/", ".env", ".key", ".pem"):
        if secret_pat in lowered:
            return True

    return False


def _backend_meets_minimum(backend: str | None, minimum: str | None) -> bool:
    """Check if a backend meets or exceeds minimum posture requirements."""
    if backend is None or minimum is None:
        return True
    backend_rank = _BACKEND_ORDER.get(backend, -1)
    min_rank = _BACKEND_ORDER.get(minimum, -1)
    return backend_rank >= min_rank


def _fs_scope_meets_minimum(scope: str | None, minimum: str | None) -> bool:
    """Check if a filesystem scope meets the minimum restrictiveness."""
    if scope is None or minimum is None:
        return True
    fs_rank = _FS_SCOPE_ORDER.get(scope, -1)
    min_rank = _FS_SCOPE_ORDER.get(minimum, -1)
    return fs_rank >= min_rank


def _egress_meets_minimum(policy: str | None, minimum: str | None) -> bool:
    """Check if an egress policy is at least as restrictive as the minimum."""
    if policy is None or minimum is None:
        return True
    eg_rank = _EGRESS_ORDER.get(policy, -1)
    min_rank = _EGRESS_ORDER.get(minimum, -1)
    return eg_rank >= min_rank


# ---------------------------------------------------------------------------
# Sub-object loaders
# ---------------------------------------------------------------------------


def _load_backend_rule(
    raw: Mapping[str, Any],
    index: int,
) -> SandboxBackendRule:
    from .sandbox_schema import (
        SANDBOX_BACKEND_RULE_OPTIONAL_FIELDS,
        SANDBOX_BACKEND_RULE_REQUIRED_FIELDS,
        SANDBOX_DANGEROUS_FIELD_NAMES,
    )

    field_prefix = f"backend_rules[{index}]"
    known_fields = frozenset(
        SANDBOX_BACKEND_RULE_REQUIRED_FIELDS + SANDBOX_BACKEND_RULE_OPTIONAL_FIELDS
    )
    _check_mapping_fields(
        raw, known_fields, SANDBOX_DANGEROUS_FIELD_NAMES, field_prefix,
    )

    missing = frozenset(SANDBOX_BACKEND_RULE_REQUIRED_FIELDS) - set(raw.keys())
    if missing:
        raise SandboxPolicyCardValidationError(
            f"{field_prefix}: missing required field(s): {', '.join(sorted(missing))}"
        )

    allowed_raw = raw.get("allowed_backends", ())
    if not isinstance(allowed_raw, (list, tuple)):
        raise SandboxPolicyCardValidationError(
            f"{field_prefix}.allowed_backends must be a list/tuple"
        )
    allowed_backends = tuple(
        _coerce_enum(b, SandboxBackend, _VALID_BACKENDS,
                    f"{field_prefix}.allowed_backends[{i}]")
        for i, b in enumerate(allowed_raw)
    )

    denied_raw = raw.get("denied_backends", ())
    if not isinstance(denied_raw, (list, tuple)):
        raise SandboxPolicyCardValidationError(
            f"{field_prefix}.denied_backends must be a list/tuple"
        )
    denied_backends = tuple(
        _coerce_enum(b, SandboxBackend, _VALID_BACKENDS,
                    f"{field_prefix}.denied_backends[{i}]")
        for i, b in enumerate(denied_raw)
    )

    mp_raw = raw.get("minimum_posture")
    minimum_posture = None
    if mp_raw is not None:
        minimum_posture = _coerce_enum(
            mp_raw, SandboxBackend, _VALID_BACKENDS,
            f"{field_prefix}.minimum_posture",
        )

    return SandboxBackendRule(
        rule_id=str(raw["rule_id"]),
        allowed_backends=allowed_backends,
        denied_backends=denied_backends,
        minimum_posture=minimum_posture,
        description=str(raw.get("description", "")),
    )


def _load_filesystem_rule(
    raw: Mapping[str, Any],
    index: int,
) -> SandboxFilesystemScopeRule:
    from .sandbox_schema import (
        SANDBOX_DANGEROUS_FIELD_NAMES,
        SANDBOX_FILESYSTEM_RULE_OPTIONAL_FIELDS,
        SANDBOX_FILESYSTEM_RULE_REQUIRED_FIELDS,
    )

    field_prefix = f"filesystem_rules[{index}]"
    known_fields = frozenset(
        SANDBOX_FILESYSTEM_RULE_REQUIRED_FIELDS + SANDBOX_FILESYSTEM_RULE_OPTIONAL_FIELDS
    )
    _check_mapping_fields(
        raw, known_fields, SANDBOX_DANGEROUS_FIELD_NAMES, field_prefix,
    )

    missing = frozenset(SANDBOX_FILESYSTEM_RULE_REQUIRED_FIELDS) - set(raw.keys())
    if missing:
        raise SandboxPolicyCardValidationError(
            f"{field_prefix}: missing required field(s): {', '.join(sorted(missing))}"
        )

    scope_raw = raw.get("scope")
    scope = None
    if scope_raw is not None:
        scope = _coerce_enum(
            scope_raw, FilesystemScope, _VALID_FILESYSTEM_SCOPES,
            f"{field_prefix}.scope",
        )

    allowed_paths_raw = raw.get("allowed_paths", ())
    if not isinstance(allowed_paths_raw, (list, tuple)):
        raise SandboxPolicyCardValidationError(
            f"{field_prefix}.allowed_paths must be a list/tuple"
        )
    allowed_paths = tuple(str(p) for p in allowed_paths_raw)

    denied_paths_raw = raw.get("denied_paths", ())
    if not isinstance(denied_paths_raw, (list, tuple)):
        raise SandboxPolicyCardValidationError(
            f"{field_prefix}.denied_paths must be a list/tuple"
        )
    denied_paths = tuple(str(p) for p in denied_paths_raw)

    allowlist_raw = raw.get("allowlist_paths", ())
    if not isinstance(allowlist_raw, (list, tuple)):
        raise SandboxPolicyCardValidationError(
            f"{field_prefix}.allowlist_paths must be a list/tuple"
        )
    allowlist_paths = tuple(str(p) for p in allowlist_raw)

    return SandboxFilesystemScopeRule(
        rule_id=str(raw["rule_id"]),
        scope=scope,
        allowed_paths=allowed_paths,
        denied_paths=denied_paths,
        allowlist_paths=allowlist_paths,
        description=str(raw.get("description", "")),
    )


def _load_egress_rule(
    raw: Mapping[str, Any],
    index: int,
) -> SandboxEgressRule:
    from .sandbox_schema import (
        SANDBOX_DANGEROUS_FIELD_NAMES,
        SANDBOX_EGRESS_RULE_OPTIONAL_FIELDS,
        SANDBOX_EGRESS_RULE_REQUIRED_FIELDS,
    )

    field_prefix = f"egress_rules[{index}]"
    known_fields = frozenset(
        SANDBOX_EGRESS_RULE_REQUIRED_FIELDS + SANDBOX_EGRESS_RULE_OPTIONAL_FIELDS
    )
    _check_mapping_fields(
        raw, known_fields, SANDBOX_DANGEROUS_FIELD_NAMES, field_prefix,
    )

    missing = frozenset(SANDBOX_EGRESS_RULE_REQUIRED_FIELDS) - set(raw.keys())
    if missing:
        raise SandboxPolicyCardValidationError(
            f"{field_prefix}: missing required field(s): {', '.join(sorted(missing))}"
        )

    ep_raw = raw.get("egress_policy")
    egress_policy = None
    if ep_raw is not None:
        egress_policy = _coerce_enum(
            ep_raw, EgressPolicy, _VALID_EGRESS_POLICIES,
            f"{field_prefix}.egress_policy",
        )

    allowed_raw = raw.get("allowed_targets", ())
    if not isinstance(allowed_raw, (list, tuple)):
        raise SandboxPolicyCardValidationError(
            f"{field_prefix}.allowed_targets must be a list/tuple"
        )
    allowed_targets = tuple(str(t) for t in allowed_raw)

    denied_raw = raw.get("denied_targets", ())
    if not isinstance(denied_raw, (list, tuple)):
        raise SandboxPolicyCardValidationError(
            f"{field_prefix}.denied_targets must be a list/tuple"
        )
    denied_targets = tuple(str(t) for t in denied_raw)

    return SandboxEgressRule(
        rule_id=str(raw["rule_id"]),
        egress_policy=egress_policy,
        allowed_targets=allowed_targets,
        denied_targets=denied_targets,
        description=str(raw.get("description", "")),
    )


def _load_command_rule(
    raw: Mapping[str, Any],
    index: int,
) -> SandboxCommandClassRule:
    from .sandbox_schema import (
        SANDBOX_COMMAND_RULE_OPTIONAL_FIELDS,
        SANDBOX_COMMAND_RULE_REQUIRED_FIELDS,
        SANDBOX_DANGEROUS_FIELD_NAMES,
    )

    field_prefix = f"command_rules[{index}]"
    known_fields = frozenset(
        SANDBOX_COMMAND_RULE_REQUIRED_FIELDS + SANDBOX_COMMAND_RULE_OPTIONAL_FIELDS
    )
    _check_mapping_fields(
        raw, known_fields, SANDBOX_DANGEROUS_FIELD_NAMES, field_prefix,
    )

    missing = frozenset(SANDBOX_COMMAND_RULE_REQUIRED_FIELDS) - set(raw.keys())
    if missing:
        raise SandboxPolicyCardValidationError(
            f"{field_prefix}: missing required field(s): {', '.join(sorted(missing))}"
        )

    decision_raw = raw.get("decision", "deny")
    decision = _coerce_enum(
        decision_raw, SandboxCommandDecision, _VALID_SANDBOX_DECISIONS,
        f"{field_prefix}.decision",
    )

    rep_raw = raw.get("required_egress_policy")
    required_egress_policy = None
    if rep_raw is not None:
        required_egress_policy = _coerce_enum(
            rep_raw, EgressPolicy, _VALID_EGRESS_POLICIES,
            f"{field_prefix}.required_egress_policy",
        )

    rb_raw = raw.get("required_backend")
    required_backend = None
    if rb_raw is not None:
        required_backend = _coerce_enum(
            rb_raw, SandboxBackend, _VALID_BACKENDS,
            f"{field_prefix}.required_backend",
        )

    risk_ceiling = raw.get("risk_ceiling")
    if risk_ceiling is not None and not isinstance(risk_ceiling, str):
        raise SandboxPolicyCardValidationError(
            f"{field_prefix}.risk_ceiling must be a string or None"
        )

    required_oversight = raw.get("required_oversight")
    if required_oversight is not None and not isinstance(required_oversight, str):
        raise SandboxPolicyCardValidationError(
            f"{field_prefix}.required_oversight must be a string or None"
        )

    return SandboxCommandClassRule(
        rule_id=str(raw["rule_id"]),
        command_class=_coerce_enum(
            raw["command_class"], CommandClass, _VALID_COMMAND_CLASSES,
            f"{field_prefix}.command_class",
        ),
        decision=decision,
        required_egress_policy=required_egress_policy,
        required_backend=required_backend,
        risk_ceiling=risk_ceiling,
        required_oversight=required_oversight,
        description=str(raw.get("description", "")),
    )


def _load_risk_tier_mapping(
    raw: Mapping[str, Any],
    index: int,
) -> RiskTierSandboxMapping:
    from .sandbox_schema import (
        SANDBOX_DANGEROUS_FIELD_NAMES,
        SANDBOX_RISK_TIER_MAPPING_OPTIONAL_FIELDS,
        SANDBOX_RISK_TIER_MAPPING_REQUIRED_FIELDS,
    )

    field_prefix = f"risk_tier_mappings[{index}]"
    known_fields = frozenset(
        SANDBOX_RISK_TIER_MAPPING_REQUIRED_FIELDS + SANDBOX_RISK_TIER_MAPPING_OPTIONAL_FIELDS
    )
    _check_mapping_fields(
        raw, known_fields, SANDBOX_DANGEROUS_FIELD_NAMES, field_prefix,
    )

    missing = frozenset(SANDBOX_RISK_TIER_MAPPING_REQUIRED_FIELDS) - set(raw.keys())
    if missing:
        raise SandboxPolicyCardValidationError(
            f"{field_prefix}: missing required field(s): {', '.join(sorted(missing))}"
        )

    return RiskTierSandboxMapping(
        risk_tier=_coerce_enum(
            raw["risk_tier"], RiskTier, _VALID_RISK_TIER_VALUES,
            f"{field_prefix}.risk_tier",
        ),
        minimum_backend=_coerce_enum(
            raw["minimum_backend"], SandboxBackend, _VALID_BACKENDS,
            f"{field_prefix}.minimum_backend",
        ),
        minimum_filesystem_scope=_coerce_enum(
            raw.get("minimum_filesystem_scope", "no_filesystem"),
            FilesystemScope, _VALID_FILESYSTEM_SCOPES,
            f"{field_prefix}.minimum_filesystem_scope",
        ),
        minimum_egress_policy=_coerce_enum(
            raw.get("minimum_egress_policy", "no_egress"),
            EgressPolicy, _VALID_EGRESS_POLICIES,
            f"{field_prefix}.minimum_egress_policy",
        ),
        requires_approval=_require_bool(
            raw.get("requires_approval", False),
            f"{field_prefix}.requires_approval",
        ),
        requires_isolated_backend=_require_bool(
            raw.get("requires_isolated_backend", False),
            f"{field_prefix}.requires_isolated_backend",
        ),
        description=str(raw.get("description", "")),
    )


def _metadata_issues(
    metadata: object,
    field_name: str,
) -> list[SandboxValidationIssue]:
    from .sandbox_schema import SANDBOX_DANGEROUS_METADATA_KEYS

    issues: list[SandboxValidationIssue] = []
    if not isinstance(metadata, MappingABC):
        issues.append(
            _make_issue("INVALID_TYPE", f"{field_name} must be a mapping", field=field_name)
        )
        return issues

    dangerous = set(metadata.keys()) & SANDBOX_DANGEROUS_METADATA_KEYS
    for key in sorted(dangerous):
        issues.append(
            _make_issue(
                "UNSAFE_METADATA_KEY",
                f"{field_name}: dangerous key '{key}' rejected",
                field=f"{field_name}.{key}",
            )
        )
    return issues


# ---------------------------------------------------------------------------
# Canonical serialization helpers
# ---------------------------------------------------------------------------


def _backend_rule_to_canonical_dict(rule: SandboxBackendRule) -> dict[str, Any]:
    result: dict[str, Any] = {
        "description": rule.description,
        "rule_id": rule.rule_id,
    }
    if rule.allowed_backends:
        result["allowed_backends"] = sorted([b.value for b in rule.allowed_backends])
    if rule.denied_backends:
        result["denied_backends"] = sorted([b.value for b in rule.denied_backends])
    if rule.minimum_posture is not None:
        result["minimum_posture"] = rule.minimum_posture.value
    return dict(sorted(result.items(), key=lambda i: i[0]))


def _filesystem_rule_to_canonical_dict(rule: SandboxFilesystemScopeRule) -> dict[str, Any]:
    result: dict[str, Any] = {
        "description": rule.description,
        "rule_id": rule.rule_id,
    }
    if rule.scope is not None:
        result["scope"] = rule.scope.value
    if rule.allowed_paths:
        result["allowed_paths"] = sorted(rule.allowed_paths)
    if rule.denied_paths:
        result["denied_paths"] = sorted(rule.denied_paths)
    if rule.allowlist_paths:
        result["allowlist_paths"] = sorted(rule.allowlist_paths)
    return dict(sorted(result.items(), key=lambda i: i[0]))


def _egress_rule_to_canonical_dict(rule: SandboxEgressRule) -> dict[str, Any]:
    result: dict[str, Any] = {
        "description": rule.description,
        "rule_id": rule.rule_id,
    }
    if rule.egress_policy is not None:
        result["egress_policy"] = rule.egress_policy.value
    if rule.allowed_targets:
        result["allowed_targets"] = sorted(rule.allowed_targets)
    if rule.denied_targets:
        result["denied_targets"] = sorted(rule.denied_targets)
    return dict(sorted(result.items(), key=lambda i: i[0]))


def _command_rule_to_canonical_dict(rule: SandboxCommandClassRule) -> dict[str, Any]:
    result: dict[str, Any] = {
        "command_class": rule.command_class.value,
        "decision": rule.decision.value,
        "description": rule.description,
        "rule_id": rule.rule_id,
    }
    if rule.required_egress_policy is not None:
        result["required_egress_policy"] = rule.required_egress_policy.value
    if rule.required_backend is not None:
        result["required_backend"] = rule.required_backend.value
    if rule.risk_ceiling is not None:
        result["risk_ceiling"] = rule.risk_ceiling
    if rule.required_oversight is not None:
        result["required_oversight"] = rule.required_oversight
    return dict(sorted(result.items(), key=lambda i: i[0]))


def _risk_tier_mapping_to_canonical_dict(mapping: RiskTierSandboxMapping) -> dict[str, Any]:
    return {
        "description": mapping.description,
        "minimum_backend": mapping.minimum_backend.value,
        "minimum_egress_policy": mapping.minimum_egress_policy.value,
        "minimum_filesystem_scope": mapping.minimum_filesystem_scope.value,
        "requires_approval": mapping.requires_approval,
        "requires_isolated_backend": mapping.requires_isolated_backend,
        "risk_tier": mapping.risk_tier.value,
    }


def _decision_input_to_canonical_dict(inp: SandboxPolicyDecisionInput) -> dict[str, Any]:
    result: dict[str, Any] = {
        "installs_packages": inp.installs_packages,
        "runs_shell": inp.runs_shell,
        "touches_secrets": inp.touches_secrets,
        "writes_files": inp.writes_files,
    }
    if inp.command_class is not None:
        result["command_class"] = inp.command_class.value
    if inp.risk_tier is not None:
        result["risk_tier"] = inp.risk_tier.value
    if inp.requested_backend is not None:
        result["requested_backend"] = inp.requested_backend.value
    if inp.requested_filesystem_scope is not None:
        result["requested_filesystem_scope"] = inp.requested_filesystem_scope.value
    if inp.requested_egress is not None:
        result["requested_egress"] = inp.requested_egress.value
    if inp.requested_paths:
        result["requested_paths"] = sorted(inp.requested_paths)
    if inp.requested_network_targets:
        result["requested_network_targets"] = sorted(inp.requested_network_targets)
    if inp.metadata:
        result["metadata"] = dict(sorted(dict(inp.metadata).items(), key=lambda i: i[0]))
    return dict(sorted(result.items(), key=lambda i: i[0]))


def _violation_to_canonical_dict(v: SandboxPolicyViolation) -> dict[str, Any]:
    result: dict[str, Any] = {
        "code": v.code,
        "message": v.message,
        "severity": v.severity,
    }
    if v.field is not None:
        result["field"] = v.field
    return result


def _warning_to_canonical_dict(w: SandboxPolicyWarning) -> dict[str, Any]:
    result: dict[str, Any] = {
        "code": w.code,
        "message": w.message,
    }
    if w.field is not None:
        result["field"] = w.field
    return result


# ---------------------------------------------------------------------------
# Public serialization / hash API
# ---------------------------------------------------------------------------


def sandbox_policy_card_to_canonical_dict(
    card: SandboxPolicyCard,
) -> dict[str, Any]:
    backend = sorted(
        [_backend_rule_to_canonical_dict(r) for r in card.backend_rules],
        key=lambda item: item["rule_id"],
    )
    filesystem = sorted(
        [_filesystem_rule_to_canonical_dict(r) for r in card.filesystem_rules],
        key=lambda item: item["rule_id"],
    )
    egress = sorted(
        [_egress_rule_to_canonical_dict(r) for r in card.egress_rules],
        key=lambda item: item["rule_id"],
    )
    commands = sorted(
        [_command_rule_to_canonical_dict(r) for r in card.command_rules],
        key=lambda item: item["rule_id"],
    )
    mappings = sorted(
        [_risk_tier_mapping_to_canonical_dict(m) for m in card.risk_tier_mappings],
        key=lambda item: item["risk_tier"],
    )

    canonical: dict[str, Any] = {
        "approval_policy": sorted([a.value for a in card.approval_policy]),
        "backend_rules": backend,
        "command_rules": commands,
        "egress_rules": egress,
        "filesystem_rules": filesystem,
        "metadata": dict(sorted(dict(card.metadata).items(), key=lambda i: i[0])),
        "policy_card": policy_card_to_canonical_dict(card.policy_card),
        "risk_tier_mappings": mappings,
        "schema_version": card.schema_version,
    }
    return dict(sorted(canonical.items(), key=lambda i: i[0]))


def serialize_sandbox_policy_card_canonical(card: SandboxPolicyCard) -> str:
    canonical = sandbox_policy_card_to_canonical_dict(card)
    return json.dumps(canonical, sort_keys=True, separators=(",", ":"))


def compute_sandbox_policy_card_hash(card: SandboxPolicyCard) -> str:
    canonical = serialize_sandbox_policy_card_canonical(card)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def serialize_sandbox_policy_decision_canonical(decision: SandboxPolicyDecision) -> str:
    """Serialize a SandboxPolicyDecision deterministically (same input + same card
    → same decision)."""
    violations = sorted(
        [_violation_to_canonical_dict(v) for v in decision.violations],
        key=lambda i: (i["code"], i.get("field", "")),
    )
    warnings = sorted(
        [_warning_to_canonical_dict(w) for w in decision.warnings],
        key=lambda i: (i["code"], i.get("field", "")),
    )
    canonical: dict[str, Any] = {
        "allowed": decision.allowed,
        "approval_required": decision.approval_required,
    }
    if decision.required_backend_minimum is not None:
        canonical["required_backend_minimum"] = decision.required_backend_minimum.value
    if decision.allowed_backends:
        canonical["allowed_backends"] = sorted([b.value for b in decision.allowed_backends])
    if decision.denied_backends:
        canonical["denied_backends"] = sorted([b.value for b in decision.denied_backends])
    if decision.effective_filesystem_scope is not None:
        canonical["effective_filesystem_scope"] = decision.effective_filesystem_scope.value
    if decision.effective_egress_policy is not None:
        canonical["effective_egress_policy"] = decision.effective_egress_policy.value
    if decision.violations:
        canonical["violations"] = violations
    if decision.warnings:
        canonical["warnings"] = warnings
    if decision.reason_codes:
        canonical["reason_codes"] = sorted(decision.reason_codes)
    if decision.source_card_id is not None:
        canonical["source_card_id"] = decision.source_card_id
    if decision.canonical_hash is not None:
        canonical["canonical_hash"] = decision.canonical_hash
    return json.dumps(canonical, sort_keys=True, separators=(",", ":"))


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def _check_backend_rule_safety(
    rule: SandboxBackendRule,
    field_prefix: str,
    errors: list[SandboxValidationIssue],
) -> None:
    # UNSAFE_LOCAL must not be in allowed backends without explicit denial
    allowed_vals = frozenset(b.value for b in rule.allowed_backends)
    denied_vals = frozenset(b.value for b in rule.denied_backends)

    if "unsafe_local" in allowed_vals:
        errors.append(_make_issue(
            "UNSAFE_LOCAL_ALLOWED",
            f"{field_prefix}: unsafe_local should not be in allowed_backends; "
            "UNSAFE_LOCAL is dangerous for high-risk contexts",
            field=f"{field_prefix}.allowed_backends",
            severity="warning",
        ))

    # DENY_EXECUTION should be in denied if not explicitly the allowed posture
    if "deny_execution" in allowed_vals and len(allowed_vals) > 1:
        errors.append(_make_issue(
            "DENY_EXECUTION_WITH_OTHER_BACKENDS",
            f"{field_prefix}: deny_execution should not coexist with other allowed backends",
            field=f"{field_prefix}.allowed_backends",
            severity="warning",
        ))

    # Contradictory deny/allow
    overlap = allowed_vals & denied_vals
    if overlap:
        errors.append(_make_issue(
            "CONTRADICTORY_BACKEND_RULES",
            f"{field_prefix}: backend(s) both allowed and denied: {', '.join(sorted(overlap))}",
            field=f"{field_prefix}",
            severity="warning",
        ))


def _check_filesystem_rule_safety(
    rule: SandboxFilesystemScopeRule,
    field_prefix: str,
    errors: list[SandboxValidationIssue],
) -> None:
    scope_val = rule.scope.value if rule.scope else None

    # Write scope without explicit rule
    if scope_val in ("read_write_project", "read_write_allowlist"):
        if not rule.allowed_paths and not rule.allowlist_paths:
            errors.append(_make_issue(
                "WRITE_SCOPE_NO_PATHS",
                f"{field_prefix}: write scope '{scope_val}' without allowed_paths or allowlist_paths",
                field=f"{field_prefix}.scope",
                severity="warning",
            ))

    # Check denied paths for secret-like patterns
    for path in rule.denied_paths:
        if _path_is_suspicious(path) and scope_val in (
            "read_write_project", "read_write_allowlist",
        ):
            # This is actually good — having secret paths denied is correct
            pass

    # Check allowed/allowlist paths for escape attempts
    for path in rule.allowed_paths:
        if _path_is_suspicious(path):
            errors.append(_make_issue(
                "SUSPICIOUS_ALLOWED_PATH",
                f"{field_prefix}: allowed_path '{path}' appears to be a secrets path or escape attempt",
                field=f"{field_prefix}.allowed_paths",
                severity="warning",
            ))
    for path in rule.allowlist_paths:
        if _path_is_suspicious(path):
            errors.append(_make_issue(
                "SUSPICIOUS_ALLOWLIST_PATH",
                f"{field_prefix}: allowlist_path '{path}' appears to be a secrets path or escape attempt",
                field=f"{field_prefix}.allowlist_paths",
                severity="warning",
            ))


def _check_egress_rule_safety(
    rule: SandboxEgressRule,
    field_prefix: str,
    errors: list[SandboxValidationIssue],
) -> None:
    policy_val = rule.egress_policy.value if rule.egress_policy else None

    # ANY_EGRESS requires explicit high-authority semantics
    if policy_val == "any_egress":
        errors.append(_make_issue(
            "ANY_EGRESS_REQUIRES_AUTHORITY",
            f"{field_prefix}: any_egress requires explicit high-authority policy semantics",
            field=f"{field_prefix}.egress_policy",
            severity="warning",
        ))

    # ALLOWLIST_ONLY without any allowed targets
    if policy_val == "allowlist_only" and not rule.allowed_targets and not rule.denied_targets:
        errors.append(_make_issue(
            "ALLOWLIST_NO_TARGETS",
            f"{field_prefix}: allowlist_only egress without allowed_targets or denied_targets",
            field=f"{field_prefix}.egress_policy",
            severity="warning",
        ))


def _check_command_rule_safety(
    rule: SandboxCommandClassRule,
    field_prefix: str,
    errors: list[SandboxValidationIssue],
) -> None:
    cc = rule.command_class.value
    decision = rule.decision.value

    # UNKNOWN_COMMAND should deny or require approval
    if cc == "unknown_command":
        if decision not in ("deny", "approval_required", "explicit_confirmation_required"):
            errors.append(_make_issue(
                "UNKNOWN_COMMAND_PERMISSIVE",
                f"{field_prefix}: unknown_command must deny or require approval, not '{decision}'",
                field=f"{field_prefix}.decision",
            ))

    # DESTRUCTIVE_COMMAND should deny unless explicitly permitted
    if cc == "destructive_command":
        if decision not in ("deny", "explicit_confirmation_required"):
            errors.append(_make_issue(
                "DESTRUCTIVE_COMMAND_NOT_DENIED",
                f"{field_prefix}: destructive_command must deny unless permitted by high authority",
                field=f"{field_prefix}.decision",
            ))

    # SECRET_TOUCHING_COMMAND should deny by default
    if cc == "secret_touching_command":
        if decision not in ("deny", "approval_required", "explicit_confirmation_required"):
            errors.append(_make_issue(
                "SECRET_TOUCHING_NOT_DENIED",
                f"{field_prefix}: secret_touching_command must deny by default",
                field=f"{field_prefix}.decision",
            ))

    # NETWORK_COMMAND must have compatible egress policy
    if cc == "network_command" and rule.required_egress_policy is None:
        errors.append(_make_issue(
            "NETWORK_COMMAND_NO_EGRESS",
            f"{field_prefix}: network_command must require a compatible egress policy",
            field=f"{field_prefix}.required_egress_policy",
            severity="warning",
        ))

    # PACKAGE_INSTALL should require approval or isolated backend
    if cc == "package_install":
        if decision not in ("approval_required", "sandbox_required", "explicit_confirmation_required"):
            errors.append(_make_issue(
                "PACKAGE_INSTALL_PERMISSIVE",
                f"{field_prefix}: package_install should require approval or isolated backend",
                field=f"{field_prefix}.decision",
            ))

    # SHELL_COMMAND should require approval or explicit policy allowance
    if cc == "shell_command":
        if decision not in ("approval_required", "sandbox_required", "explicit_confirmation_required"):
            errors.append(_make_issue(
                "SHELL_COMMAND_PERMISSIVE",
                f"{field_prefix}: shell_command should require approval or explicit policy allowance",
                field=f"{field_prefix}.decision",
            ))


def validate_sandbox_policy_card(
    card: SandboxPolicyCard,
) -> SandboxValidationResult:
    from .sandbox_schema import (
        REQUIRED_SANDBOX_RISK_TIERS,
        SUPPORTED_SANDBOX_POLICY_CARD_SCHEMA_VERSIONS,
    )

    errors: list[SandboxValidationIssue] = []
    warnings: list[SandboxValidationIssue] = []

    if not isinstance(card, SandboxPolicyCard):
        errors.append(
            _make_issue("INVALID_TYPE", "card must be a SandboxPolicyCard", field="card")
        )
        return SandboxValidationResult(False, tuple(errors), tuple(warnings))

    if (
        not isinstance(card.schema_version, str)
        or not card.schema_version.strip()
        or card.schema_version not in SUPPORTED_SANDBOX_POLICY_CARD_SCHEMA_VERSIONS
    ):
        errors.append(
            _make_issue(
                "UNSUPPORTED_SCHEMA_VERSION",
                f"schema_version '{card.schema_version}' is not supported",
                field="schema_version",
            )
        )

    if not isinstance(card.policy_card, PolicyCard):
        errors.append(
            _make_issue("INVALID_TYPE", "policy_card must be a PolicyCard", field="policy_card")
        )
    else:
        try:
            from .validation import validate_policy_card as _vp
            policy_result = _vp(card.policy_card)
        except Exception as exc:
            errors.append(_make_issue(
                "INVALID_POLICY_CARD",
                f"embedded policy_card validation failed: {exc}",
                field="policy_card",
            ))
            policy_result = None
        if policy_result is not None and hasattr(policy_result, 'errors'):
            for issue in policy_result.errors:
                errors.append(
                    _make_issue(
                        f"POLICY_CARD_{issue.code}",
                        issue.message,
                        field=f"policy_card.{issue.field}" if issue.field else "policy_card",
                        severity=issue.severity,
                    )
                )
        kind_value = _enum_value(card.policy_card.kind)
        if kind_value != PolicyCardKind.SANDBOX.value:
            errors.append(
                _make_issue(
                    "INVALID_POLICY_CARD_KIND",
                    "SandboxPolicyCard requires generic PolicyCard kind 'sandbox'",
                    field="policy_card.kind",
                )
            )

    errors.extend(_metadata_issues(card.metadata, "metadata"))

    # Validate backend rules
    if not isinstance(card.backend_rules, tuple):
        errors.append(
            _make_issue("INVALID_TYPE", "backend_rules must be a tuple", field="backend_rules")
        )
    else:
        backend_rule_ids: set[str] = set()
        for index, backend_rule in enumerate(card.backend_rules):
            field_prefix = f"backend_rules[{index}]"
            if not isinstance(backend_rule, SandboxBackendRule):
                errors.append(_make_issue(
                    "INVALID_TYPE", f"{field_prefix} must be a SandboxBackendRule",
                    field=field_prefix,
                ))
                continue
            if not backend_rule.rule_id.strip():
                errors.append(_make_issue(
                    "MISSING_RULE_ID", f"{field_prefix}.rule_id is required",
                    field=f"{field_prefix}.rule_id",
                ))
            elif backend_rule.rule_id in backend_rule_ids:
                errors.append(_make_issue(
                    "DUPLICATE_RULE_ID",
                    f"{field_prefix}: duplicate rule_id '{backend_rule.rule_id}'",
                    field=f"{field_prefix}.rule_id",
                ))
            backend_rule_ids.add(backend_rule.rule_id)

            for bi, backend in enumerate(backend_rule.allowed_backends):
                if _enum_value(backend) not in _VALID_BACKENDS:
                    errors.append(_make_issue(
                        "INVALID_BACKEND",
                        f"{field_prefix}.allowed_backends[{bi}] is invalid",
                        field=f"{field_prefix}.allowed_backends[{bi}]",
                    ))
            for bi, backend in enumerate(backend_rule.denied_backends):
                if _enum_value(backend) not in _VALID_BACKENDS:
                    errors.append(_make_issue(
                        "INVALID_BACKEND",
                        f"{field_prefix}.denied_backends[{bi}] is invalid",
                        field=f"{field_prefix}.denied_backends[{bi}]",
                    ))
            _check_backend_rule_safety(backend_rule, field_prefix, warnings)

    # Validate filesystem rules
    if not isinstance(card.filesystem_rules, tuple):
        errors.append(
            _make_issue("INVALID_TYPE", "filesystem_rules must be a tuple",
                        field="filesystem_rules")
        )
    else:
        filesystem_rule_ids: set[str] = set()
        for index, filesystem_rule in enumerate(card.filesystem_rules):
            field_prefix = f"filesystem_rules[{index}]"
            if not isinstance(filesystem_rule, SandboxFilesystemScopeRule):
                errors.append(_make_issue(
                    "INVALID_TYPE", f"{field_prefix} must be a SandboxFilesystemScopeRule",
                    field=field_prefix,
                ))
                continue
            if not filesystem_rule.rule_id.strip():
                errors.append(_make_issue(
                    "MISSING_RULE_ID", f"{field_prefix}.rule_id is required",
                    field=f"{field_prefix}.rule_id",
                ))
            elif filesystem_rule.rule_id in filesystem_rule_ids:
                errors.append(_make_issue(
                    "DUPLICATE_RULE_ID",
                    f"{field_prefix}: duplicate rule_id '{filesystem_rule.rule_id}'",
                    field=f"{field_prefix}.rule_id",
                ))
            filesystem_rule_ids.add(filesystem_rule.rule_id)

            if (
                filesystem_rule.scope is not None
                and _enum_value(filesystem_rule.scope) not in _VALID_FILESYSTEM_SCOPES
            ):
                errors.append(_make_issue(
                    "INVALID_FILESYSTEM_SCOPE",
                    f"{field_prefix}.scope is invalid",
                    field=f"{field_prefix}.scope",
                ))
            _check_filesystem_rule_safety(filesystem_rule, field_prefix, warnings)

    # Validate egress rules
    if not isinstance(card.egress_rules, tuple):
        errors.append(
            _make_issue("INVALID_TYPE", "egress_rules must be a tuple", field="egress_rules")
        )
    else:
        egress_rule_ids: set[str] = set()
        for index, egress_rule in enumerate(card.egress_rules):
            field_prefix = f"egress_rules[{index}]"
            if not isinstance(egress_rule, SandboxEgressRule):
                errors.append(_make_issue(
                    "INVALID_TYPE", f"{field_prefix} must be a SandboxEgressRule",
                    field=field_prefix,
                ))
                continue
            if not egress_rule.rule_id.strip():
                errors.append(_make_issue(
                    "MISSING_RULE_ID", f"{field_prefix}.rule_id is required",
                    field=f"{field_prefix}.rule_id",
                ))
            elif egress_rule.rule_id in egress_rule_ids:
                errors.append(_make_issue(
                    "DUPLICATE_RULE_ID",
                    f"{field_prefix}: duplicate rule_id '{egress_rule.rule_id}'",
                    field=f"{field_prefix}.rule_id",
                ))
            egress_rule_ids.add(egress_rule.rule_id)

            if (
                egress_rule.egress_policy is not None
                and _enum_value(egress_rule.egress_policy) not in _VALID_EGRESS_POLICIES
            ):
                errors.append(_make_issue(
                    "INVALID_EGRESS_POLICY",
                    f"{field_prefix}.egress_policy is invalid",
                    field=f"{field_prefix}.egress_policy",
                ))
            _check_egress_rule_safety(egress_rule, field_prefix, warnings)

    # Validate command rules
    if not isinstance(card.command_rules, tuple):
        errors.append(
            _make_issue("INVALID_TYPE", "command_rules must be a tuple",
                        field="command_rules")
        )
    else:
        command_rule_ids: set[str] = set()
        for index, command_rule in enumerate(card.command_rules):
            field_prefix = f"command_rules[{index}]"
            if not isinstance(command_rule, SandboxCommandClassRule):
                errors.append(_make_issue(
                    "INVALID_TYPE", f"{field_prefix} must be a SandboxCommandClassRule",
                    field=field_prefix,
                ))
                continue
            if not command_rule.rule_id.strip():
                errors.append(_make_issue(
                    "MISSING_RULE_ID", f"{field_prefix}.rule_id is required",
                    field=f"{field_prefix}.rule_id",
                ))
            elif command_rule.rule_id in command_rule_ids:
                errors.append(_make_issue(
                    "DUPLICATE_RULE_ID",
                    f"{field_prefix}: duplicate rule_id '{command_rule.rule_id}'",
                    field=f"{field_prefix}.rule_id",
                ))
            command_rule_ids.add(command_rule.rule_id)

            if _enum_value(command_rule.command_class) not in _VALID_COMMAND_CLASSES:
                errors.append(_make_issue(
                    "INVALID_COMMAND_CLASS",
                    f"{field_prefix}.command_class is invalid",
                    field=f"{field_prefix}.command_class",
                ))
            if _enum_value(command_rule.decision) not in _VALID_SANDBOX_DECISIONS:
                errors.append(_make_issue(
                    "INVALID_DECISION",
                    f"{field_prefix}.decision is invalid",
                    field=f"{field_prefix}.decision",
                ))
            _check_command_rule_safety(command_rule, field_prefix, warnings)

    # Validate risk tier mappings
    if not isinstance(card.risk_tier_mappings, tuple):
        errors.append(
            _make_issue("INVALID_TYPE", "risk_tier_mappings must be a tuple",
                        field="risk_tier_mappings")
        )
        mapping_items: tuple[object, ...] = ()
    else:
        mapping_items = card.risk_tier_mappings

    required_tier_values = frozenset(tier.value for tier in REQUIRED_SANDBOX_RISK_TIERS)
    seen_tiers: set[str] = set()
    duplicates: set[str] = set()

    for index, mapping in enumerate(mapping_items):
        field_prefix = f"risk_tier_mappings[{index}]"
        if not isinstance(mapping, RiskTierSandboxMapping):
            errors.append(_make_issue(
                "INVALID_TYPE", f"{field_prefix} must be a RiskTierSandboxMapping",
                field=field_prefix,
            ))
            continue

        tier_value = _enum_value(mapping.risk_tier)
        if tier_value not in _VALID_RISK_TIER_VALUES:
            errors.append(_make_issue(
                "INVALID_RISK_TIER",
                f"{field_prefix}.risk_tier is invalid",
                field=f"{field_prefix}.risk_tier",
            ))
            continue
        if tier_value in seen_tiers:
            duplicates.add(tier_value)
        seen_tiers.add(tier_value)

        if _enum_value(mapping.minimum_backend) not in _VALID_BACKENDS:
            errors.append(_make_issue(
                "INVALID_BACKEND",
                f"{field_prefix}.minimum_backend is invalid",
                field=f"{field_prefix}.minimum_backend",
            ))
        if _enum_value(mapping.minimum_filesystem_scope) not in _VALID_FILESYSTEM_SCOPES:
            errors.append(_make_issue(
                "INVALID_FILESYSTEM_SCOPE",
                f"{field_prefix}.minimum_filesystem_scope is invalid",
                field=f"{field_prefix}.minimum_filesystem_scope",
            ))
        if _enum_value(mapping.minimum_egress_policy) not in _VALID_EGRESS_POLICIES:
            errors.append(_make_issue(
                "INVALID_EGRESS_POLICY",
                f"{field_prefix}.minimum_egress_policy is invalid",
                field=f"{field_prefix}.minimum_egress_policy",
            ))

    missing = required_tier_values - seen_tiers
    if missing and len(seen_tiers) > 1:
        errors.append(_make_issue(
            "MISSING_REQUIRED_TIER",
            f"missing required risk tier mapping(s): {', '.join(sorted(missing))}",
            field="risk_tier_mappings",
        ))
    if duplicates:
        errors.append(_make_issue(
            "DUPLICATE_TIER",
            f"duplicate risk tier mapping(s): {', '.join(sorted(duplicates))}",
            field="risk_tier_mappings",
        ))

    # Validate approval policy
    if not isinstance(card.approval_policy, frozenset):
        errors.append(_make_issue(
            "INVALID_TYPE", "approval_policy must be a frozenset",
            field="approval_policy",
        ))
    else:
        for req in card.approval_policy:
            if _enum_value(req) not in _VALID_APPROVAL_REQUIREMENTS:
                errors.append(_make_issue(
                    "INVALID_APPROVAL_REQUIREMENT",
                    f"approval_policy contains invalid value '{_enum_value(req)}'",
                    field="approval_policy",
                ))
                break

    canonical_hash: str | None = None
    try:
        canonical_hash = compute_sandbox_policy_card_hash(card)
    except Exception as exc:
        errors.append(
            _make_issue(
                "CANONICAL_HASH_FAILED",
                f"canonical hash could not be computed: {exc}",
                field="canonical_hash",
            )
        )

    card_id = None
    if isinstance(card.policy_card, PolicyCard):
        card_id = card.policy_card.identity.card_id

    return SandboxValidationResult(
        valid=len(errors) == 0,
        errors=tuple(errors),
        warnings=tuple(warnings),
        card_id=card_id,
        canonical_hash=canonical_hash,
    )


# ---------------------------------------------------------------------------
# Dict loader
# ---------------------------------------------------------------------------


def load_sandbox_policy_card_from_dict(
    data: Mapping[str, Any],
) -> SandboxPolicyCard:
    from .sandbox_schema import (
        SANDBOX_DANGEROUS_FIELD_NAMES,
        SANDBOX_DANGEROUS_METADATA_KEYS,
        SANDBOX_OPTIONAL_FIELDS,
        SANDBOX_REQUIRED_FIELDS,
        SUPPORTED_SANDBOX_POLICY_CARD_SCHEMA_VERSIONS,
    )

    raw = _require_mapping(data, "sandbox policy card data")
    known_fields = frozenset(SANDBOX_REQUIRED_FIELDS + SANDBOX_OPTIONAL_FIELDS)
    _check_mapping_fields(
        raw, known_fields, SANDBOX_DANGEROUS_FIELD_NAMES,
        "sandbox_policy_card",
    )

    missing = frozenset(SANDBOX_REQUIRED_FIELDS) - set(raw.keys())
    if missing:
        raise SandboxPolicyCardValidationError(
            f"missing required field(s): {', '.join(sorted(missing))}"
        )

    schema_version = raw.get("schema_version")
    if (
        not isinstance(schema_version, str)
        or not schema_version.strip()
        or schema_version not in SUPPORTED_SANDBOX_POLICY_CARD_SCHEMA_VERSIONS
    ):
        raise SandboxPolicyCardValidationError(
            f"schema_version must be one of: "
            f"{', '.join(SUPPORTED_SANDBOX_POLICY_CARD_SCHEMA_VERSIONS)}"
        )

    policy_card_raw = _require_mapping(raw.get("policy_card"), "policy_card")
    try:
        policy_card = load_policy_card_from_dict(dict(policy_card_raw))
    except PolicyCardError as exc:
        raise SandboxPolicyCardValidationError(
            f"embedded policy_card invalid: {exc}"
        ) from exc

    # Load backend rules
    backend_raw = raw.get("backend_rules", ())
    if not isinstance(backend_raw, (list, tuple)):
        raise SandboxPolicyCardValidationError("backend_rules must be a list/tuple")
    backend_rules = tuple(
        _load_backend_rule(
            _require_mapping(item, f"backend_rules[{index}]"), index,
        )
        for index, item in enumerate(backend_raw)
    )

    # Load filesystem rules
    fs_raw = raw.get("filesystem_rules", ())
    if not isinstance(fs_raw, (list, tuple)):
        raise SandboxPolicyCardValidationError("filesystem_rules must be a list/tuple")
    filesystem_rules = tuple(
        _load_filesystem_rule(
            _require_mapping(item, f"filesystem_rules[{index}]"), index,
        )
        for index, item in enumerate(fs_raw)
    )

    # Load egress rules
    eg_raw = raw.get("egress_rules", ())
    if not isinstance(eg_raw, (list, tuple)):
        raise SandboxPolicyCardValidationError("egress_rules must be a list/tuple")
    egress_rules = tuple(
        _load_egress_rule(
            _require_mapping(item, f"egress_rules[{index}]"), index,
        )
        for index, item in enumerate(eg_raw)
    )

    # Load command rules
    cmd_raw = raw.get("command_rules", ())
    if not isinstance(cmd_raw, (list, tuple)):
        raise SandboxPolicyCardValidationError("command_rules must be a list/tuple")
    command_rules = tuple(
        _load_command_rule(
            _require_mapping(item, f"command_rules[{index}]"), index,
        )
        for index, item in enumerate(cmd_raw)
    )

    # Load risk tier mappings
    mappings_raw = raw.get("risk_tier_mappings", ())
    if not isinstance(mappings_raw, (list, tuple)):
        raise SandboxPolicyCardValidationError("risk_tier_mappings must be a list/tuple")
    risk_tier_mappings = tuple(
        _load_risk_tier_mapping(
            _require_mapping(item, f"risk_tier_mappings[{index}]"), index,
        )
        for index, item in enumerate(mappings_raw)
    )

    # Load approval policy
    approval_raw = raw.get("approval_policy", ())
    if not isinstance(approval_raw, (list, tuple)):
        raise SandboxPolicyCardValidationError("approval_policy must be a list/tuple")
    approval_policy: frozenset[ApprovalRequirement] = frozenset()
    for i, a in enumerate(approval_raw):
        if isinstance(a, ApprovalRequirement):
            req = a
        else:
            req = _coerce_enum(
                a, ApprovalRequirement, _VALID_APPROVAL_REQUIREMENTS,
                f"approval_policy[{i}]",
            )
        approval_policy = approval_policy | {req}

    # Load metadata
    metadata_raw = raw.get("metadata")
    if metadata_raw is None:
        metadata: dict[str, Any] = {}
    elif isinstance(metadata_raw, MappingABC):
        dangerous_meta = set(metadata_raw.keys()) & SANDBOX_DANGEROUS_METADATA_KEYS
        if dangerous_meta:
            raise SandboxPolicyCardUnsafeFieldError(
                f"dangerous metadata key(s): {', '.join(sorted(dangerous_meta))}"
            )
        metadata = dict(metadata_raw)
    else:
        raise SandboxPolicyCardValidationError("metadata must be a mapping")

    card = SandboxPolicyCard(
        policy_card=policy_card,
        schema_version=schema_version,
        backend_rules=backend_rules,
        filesystem_rules=filesystem_rules,
        egress_rules=egress_rules,
        command_rules=command_rules,
        risk_tier_mappings=risk_tier_mappings,
        approval_policy=approval_policy,
        metadata=metadata,
    )

    result = validate_sandbox_policy_card(card)
    if not result.valid:
        messages = "; ".join(e.message for e in result.errors)
        raise SandboxPolicyCardValidationError(f"validation failed: {messages}")

    return card


def validate_sandbox_policy_card_dict(
    data: Mapping[str, Any],
) -> SandboxValidationResult:
    try:
        card = load_sandbox_policy_card_from_dict(data)
    except SandboxPolicyCardError as exc:
        card_id = None
        if isinstance(data, MappingABC):
            policy_card_raw = data.get("policy_card")
            if isinstance(policy_card_raw, MappingABC):
                identity = policy_card_raw.get("identity")
                if isinstance(identity, MappingABC):
                    raw_card_id = identity.get("card_id")
                    if isinstance(raw_card_id, str):
                        card_id = raw_card_id
        return SandboxValidationResult(
            valid=False,
            errors=(
                _make_issue("INVALID_DATA_SANDBOX_POLICY_CARD_DICT", str(exc), field=None),
            ),
            warnings=(),
            card_id=card_id,
            canonical_hash=None,
        )
    return validate_sandbox_policy_card(card)


# ---------------------------------------------------------------------------
# Default factory
# ---------------------------------------------------------------------------


def create_default_sandbox_policy_card() -> SandboxPolicyCard:
    from .sandbox_schema import (  # noqa: PLC0415
        SANDBOX_POLICY_CARD_SCHEMA_VERSION,
    )

    policy_card = PolicyCard(
        schema_version="1.0",
        identity=PolicyCardIdentity(
            card_id="aurel-core-sandbox-policy-v1",
            slug="aurel-core-sandbox-policy",
            name="AurelCore Sandbox Policy",
            version="1.0",
            namespace="aurel_core",
        ),
        kind=PolicyCardKind.SANDBOX,
        status=PolicyCardStatus.ACTIVE,
        scope=PolicyCardScope(scope_type=PolicyCardScopeType.SANDBOX),
        description=(
            "Defines sandbox policy semantics for AurelCore: backend postures, "
            "filesystem scope, egress, command classes, risk-tier-to-posture mappings, "
            "and approval requirements. Does not enforce runtime sandbox behavior."
        ),
    )

    return SandboxPolicyCard(
        policy_card=policy_card,
        schema_version=SANDBOX_POLICY_CARD_SCHEMA_VERSION,
        backend_rules=DEFAULT_BACKEND_RULES,
        filesystem_rules=DEFAULT_FILESYSTEM_RULES,
        egress_rules=DEFAULT_EGRESS_RULES,
        command_rules=DEFAULT_COMMAND_RULES,
        risk_tier_mappings=DEFAULT_RISK_TIER_SANDBOX_MAPPINGS,
        approval_policy=DEFAULT_APPROVAL_REQUIREMENTS,
        metadata={"owner_note": "default sandbox policy: deny-by-default at every level"},
    )


# ---------------------------------------------------------------------------
# Decision evaluation (semantic-only, no runtime enforcement)
# ---------------------------------------------------------------------------


def evaluate_sandbox_policy_decision(
    card: SandboxPolicyCard,
    inp: SandboxPolicyDecisionInput,
) -> SandboxPolicyDecision:
    """Evaluate sandbox policy against a decision input.

    This is semantic only — no runtime enforcement. P1.6.10 Custos v0 will
    consume this structure for shadow-mode resolution.

    Args:
        card: The sandbox policy card to evaluate against.
        inp: The decision input (command class, risk tier, requested
            backends/scopes/egress, etc.).

    Returns:
        A SandboxPolicyDecision with allowed, approval_required, effective
        backends/scopes/egress, violations, warnings, and reason codes.
    """
    violations: list[SandboxPolicyViolation] = []
    warnings: list[SandboxPolicyWarning] = []
    reason_codes: list[str] = []

    card_id = None
    if isinstance(card.policy_card, PolicyCard):
        card_id = card.policy_card.identity.card_id

    # Determine effective risk tier
    risk_tier = inp.risk_tier
    if risk_tier is None:
        risk_tier = RiskTier.R3  # default: meaningful state change
        warnings.append(SandboxPolicyWarning(
            "RISK_TIER_DEFAULTED",
            "No risk tier provided; defaulting to R3",
            field="risk_tier",
        ))

    # Find risk tier mapping
    tier_mapping = None
    for mapping in card.risk_tier_mappings:
        if mapping.risk_tier == risk_tier:
            tier_mapping = mapping
            break

    if tier_mapping is None:
        violations.append(SandboxPolicyViolation(
            "UNKNOWN_RISK_TIER",
            f"Risk tier {risk_tier.value} has no sandbox mapping; denying",
            field="risk_tier",
        ))
        return SandboxPolicyDecision(
            allowed=False,
            approval_required=True,
            violations=tuple(violations),
            warnings=tuple(warnings),
            reason_codes=("UNKNOWN_RISK_TIER",),
            source_card_id=card_id,
        )

    # If R6 (denied), immediately deny
    if risk_tier == RiskTier.R6:
        return SandboxPolicyDecision(
            allowed=False,
            approval_required=True,
            required_backend_minimum=SandboxBackend.DENY_EXECUTION,
            effective_filesystem_scope=FilesystemScope.NO_FILESYSTEM,
            effective_egress_policy=EgressPolicy.DENY_NETWORK,
            violations=tuple(violations),
            warnings=tuple(warnings),
            reason_codes=("R6_DENIED",),
            source_card_id=card_id,
        )

    # Collect effective backends from rules
    allowed_backends_set: set[SandboxBackend] = set()
    denied_backends_set: set[SandboxBackend] = set()
    min_posture: SandboxBackend | None = None

    for backend_rule in card.backend_rules:
        for b in backend_rule.allowed_backends:
            allowed_backends_set.add(b)
        for b in backend_rule.denied_backends:
            denied_backends_set.add(b)
        if backend_rule.minimum_posture is not None:
            if min_posture is None:
                min_posture = backend_rule.minimum_posture
            else:
                # Take the more restrictive minimum
                if (
                    _BACKEND_ORDER.get(backend_rule.minimum_posture.value, 0)
                    > _BACKEND_ORDER.get(min_posture.value, 0)
                ):
                    min_posture = backend_rule.minimum_posture

    # Apply risk tier minimum
    tier_min = tier_mapping.minimum_backend
    if tier_min is not None and (min_posture is None or _BACKEND_ORDER.get(tier_min.value, 0) > _BACKEND_ORDER.get(min_posture.value, 0)):
        min_posture = tier_min

    # Check requested backend
    if inp.requested_backend is not None:
        req_backend = inp.requested_backend
        if req_backend in denied_backends_set:
            violations.append(SandboxPolicyViolation(
                "REQUESTED_BACKEND_DENIED",
                f"Requested backend '{req_backend.value}' is denied by policy",
                field="requested_backend",
            ))
        elif allowed_backends_set and req_backend not in allowed_backends_set:
            violations.append(SandboxPolicyViolation(
                "REQUESTED_BACKEND_NOT_ALLOWLISTED",
                f"Requested backend '{req_backend.value}' is not in allowed backends",
                field="requested_backend",
            ))
        elif not _backend_meets_minimum(req_backend.value, tier_min.value if tier_min else None):
            violations.append(SandboxPolicyViolation(
                "REQUESTED_BACKEND_BELOW_MINIMUM",
                f"Requested backend '{req_backend.value}' is below minimum "
                f"'{tier_min.value if tier_min else 'any'}' for risk tier {risk_tier.value}",
                field="requested_backend",
            ))

    # UNSAFE_LOCAL check
    if inp.requested_backend == SandboxBackend.UNSAFE_LOCAL:
        if risk_tier in (RiskTier.R4, RiskTier.R5, RiskTier.R6):
            violations.append(SandboxPolicyViolation(
                "UNSAFE_LOCAL_HIGH_RISK",
                f"UNSAFE_LOCAL is not permitted at risk tier {risk_tier.value}",
                field="requested_backend",
            ))
        elif ApprovalRequirement.APPROVAL_REQUIRED_FOR_UNSAFE_LOCAL in card.approval_policy:
            reason_codes.append("UNSAFE_LOCAL_APPROVAL_REQUIRED")

    # Determine effective filesystem scope
    effective_fs: FilesystemScope = tier_mapping.minimum_filesystem_scope
    for filesystem_rule in card.filesystem_rules:
        if filesystem_rule.scope is not None:
            if _fs_scope_meets_minimum(
                filesystem_rule.scope.value,
                tier_mapping.minimum_filesystem_scope.value,
            ):
                effective_fs = filesystem_rule.scope
                break

    # Check requested filesystem scope
    if inp.requested_filesystem_scope is not None:
        req_fs = inp.requested_filesystem_scope
        if not _fs_scope_meets_minimum(req_fs.value, effective_fs.value):
            violations.append(SandboxPolicyViolation(
                "REQUESTED_FS_SCOPE_INSUFFICIENT",
                f"Requested filesystem scope '{req_fs.value}' is less restrictive "
                f"than required minimum '{effective_fs.value}'",
                field="requested_filesystem_scope",
            ))

    # Check requested paths
    if inp.requested_paths:
        for path in inp.requested_paths:
            if _path_is_suspicious(path):
                violations.append(SandboxPolicyViolation(
                    "SUSPICIOUS_REQUESTED_PATH",
                    f"Requested path '{path}' appears to be a secrets path or escape attempt",
                    field="requested_paths",
                ))

    # Determine effective egress policy
    effective_egress: EgressPolicy = tier_mapping.minimum_egress_policy
    for egress_rule in card.egress_rules:
        if egress_rule.egress_policy is not None:
            if _egress_meets_minimum(
                egress_rule.egress_policy.value,
                tier_mapping.minimum_egress_policy.value,
            ):
                effective_egress = egress_rule.egress_policy
                break

    # Check requested egress
    if inp.requested_egress is not None:
        req_eg = inp.requested_egress
        if not _egress_meets_minimum(req_eg.value, effective_egress.value):
            violations.append(SandboxPolicyViolation(
                "REQUESTED_EGRESS_INSUFFICIENT",
                f"Requested egress '{req_eg.value}' is less restrictive "
                f"than required minimum '{effective_egress.value}'",
                field="requested_egress",
            ))

    # ANY_EGRESS check
    if inp.requested_egress == EgressPolicy.ANY_EGRESS:
        warnings.append(SandboxPolicyWarning(
            "ANY_EGRESS_REQUESTED",
            "ANY_EGRESS requires explicit high-authority policy semantics",
            field="requested_egress",
        ))
        reason_codes.append("ANY_EGRESS_AUTHORITY_REQUIRED")

    # Command class evaluation
    command_class = inp.command_class
    if command_class is None:
        command_class = CommandClass.UNKNOWN_COMMAND
        warnings.append(SandboxPolicyWarning(
            "COMMAND_CLASS_DEFAULTED",
            "No command class provided; defaulting to unknown_command",
            field="command_class",
        ))

    command_decision: str = "deny"
    for command_rule in card.command_rules:
        if command_rule.command_class == command_class:
            command_decision = command_rule.decision.value
            break

    # Check for additional safety flags
    approval_required = tier_mapping.requires_approval
    allowed = True

    if command_decision in ("deny",):
        violations.append(SandboxPolicyViolation(
            "COMMAND_CLASS_DENIED",
            f"Command class '{command_class.value}' is denied by policy",
            field="command_class",
        ))
        allowed = False

    if command_decision in ("approval_required", "explicit_confirmation_required"):
        approval_required = True
        reason_codes.append(f"COMMAND_{command_decision.upper()}")

    if command_decision in ("sandbox_required",):
        reason_codes.append("SANDBOX_REQUIRED")

    # Behavior flag checks against approval policy
    if inp.touches_secrets and ApprovalRequirement.APPROVAL_REQUIRED_FOR_SECRETS in card.approval_policy:
        approval_required = True
        reason_codes.append("SECRETS_TOUCHED")

    if inp.writes_files and ApprovalRequirement.APPROVAL_REQUIRED_FOR_WRITE in card.approval_policy:
        approval_required = True
        reason_codes.append("WRITE_OPERATION")

    if inp.runs_shell and ApprovalRequirement.APPROVAL_REQUIRED_FOR_SHELL in card.approval_policy:
        approval_required = True
        reason_codes.append("SHELL_EXECUTION")

    if inp.installs_packages and ApprovalRequirement.APPROVAL_REQUIRED_FOR_PACKAGE_INSTALL in card.approval_policy:
        approval_required = True
        reason_codes.append("PACKAGE_INSTALL")

    # Network command without compatible egress
    if command_class == CommandClass.NETWORK_COMMAND:
        if effective_egress in (EgressPolicy.NO_EGRESS, EgressPolicy.DENY_NETWORK):
            violations.append(SandboxPolicyViolation(
                "NETWORK_COMMAND_NO_EGRESS_COMPAT",
                "Network command class requires compatible egress posture; "
                f"current effective egress is '{effective_egress.value}'",
                field="command_class",
            ))
            allowed = False

    # Determine canonical hash for decision determinism
    decision_hash: str | None = None
    try:
        decision_hash = compute_sandbox_policy_card_hash(card)
    except Exception as exc:
        warnings.append(SandboxPolicyWarning(
            "CANONICAL_HASH_UNAVAILABLE",
            f"Could not compute sandbox policy card hash: {exc}",
            field="canonical_hash",
        ))
        reason_codes.append("CANONICAL_HASH_UNAVAILABLE")

    return SandboxPolicyDecision(
        allowed=allowed and len(violations) == 0,
        approval_required=approval_required,
        required_backend_minimum=min_posture or tier_min,
        allowed_backends=tuple(sorted(allowed_backends_set, key=lambda b: b.value)),
        denied_backends=tuple(sorted(denied_backends_set, key=lambda b: b.value)),
        effective_filesystem_scope=effective_fs,
        effective_egress_policy=effective_egress,
        violations=tuple(violations),
        warnings=tuple(warnings),
        reason_codes=tuple(sorted(reason_codes)),
        source_card_id=card_id,
        canonical_hash=decision_hash,
    )
