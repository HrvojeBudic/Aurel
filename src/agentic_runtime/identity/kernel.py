"""Aurel Identity Kernel — machine-readable trust anchor (P1.4.1)."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, Mapping

from ..yaml_minimal import YamlParseError, load_yaml

VALIDATOR_VERSION = "1.0.0"

Severity = Literal["info", "warning", "critical"]
ViolationAction = Literal["warn", "block", "fail_boot"]
HashAlgorithm = Literal["sha256"]
ValidationStatus = Literal["valid", "invalid"]


class IdentityKernelError(ValueError):
    """Raised when identity kernel config cannot be loaded or parsed."""


@dataclass(frozen=True)
class IdentityImmutables:
    operator_final_authority: bool
    self_escalation_allowed: bool
    hidden_goals_allowed: bool
    identity_replacement_allowed: bool
    policy_bypass_self_grant_allowed: bool
    untrusted_input_can_modify_identity: bool


@dataclass(frozen=True)
class DevelopmentAllowed:
    skill_growth: bool
    memory_growth: bool
    communication_refinement: bool
    procedure_growth: bool
    specialist_growth: bool
    world_model_revision: bool


@dataclass(frozen=True)
class DevelopmentForbidden:
    operator_replacement: bool
    secret_goal_creation: bool
    self_authority_expansion: bool
    unapproved_identity_rewrite: bool


@dataclass(frozen=True)
class IdentityInvariant:
    id: str
    key: str
    statement: str
    expected_value: bool
    mutable: bool
    severity: Severity
    violation_action: ViolationAction
    rationale: str


@dataclass(frozen=True)
class IdentityKernelHash:
    algorithm: HashAlgorithm
    value: str


@dataclass(frozen=True)
class IdentityKernelValidationResult:
    valid: bool
    errors: tuple[str, ...]
    warnings: tuple[str, ...]
    critical_failures: tuple[str, ...]


@dataclass(frozen=True)
class IdentityKernelAttestation:
    schema_version: str
    kernel_hash: str
    hash_algorithm: str
    config_path: str
    validation_status: ValidationStatus
    validator_version: str
    critical_failures: tuple[str, ...]


@dataclass(frozen=True)
class AurelIdentityKernel:
    schema_version: str
    name: str
    agent_class: str
    primary_operator: str
    final_authority: str
    local_first: bool
    immutables: IdentityImmutables
    development_allowed: DevelopmentAllowed
    development_forbidden: DevelopmentForbidden
    invariants: tuple[IdentityInvariant, ...]
    notes: Mapping[str, Any] | None = None


def default_identity_kernel_path() -> Path:
    """Return canonical repo-root path to identity_kernel.yaml."""
    return Path(__file__).resolve().parents[3] / "config" / "aurel" / "identity_kernel.yaml"


def _require_mapping(data: object, label: str) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise IdentityKernelError(f"{label} must be a mapping")
    return data


def _require_bool(data: dict[str, Any], key: str, label: str) -> bool:
    if key not in data:
        raise IdentityKernelError(f"missing required field: {label}.{key}")
    value = data[key]
    if not isinstance(value, bool):
        raise IdentityKernelError(f"{label}.{key} must be a boolean")
    return value


def _parse_immutables(data: dict[str, Any]) -> IdentityImmutables:
    label = "identity_kernel.immutables"
    return IdentityImmutables(
        operator_final_authority=_require_bool(data, "operator_final_authority", label),
        self_escalation_allowed=_require_bool(data, "self_escalation_allowed", label),
        hidden_goals_allowed=_require_bool(data, "hidden_goals_allowed", label),
        identity_replacement_allowed=_require_bool(data, "identity_replacement_allowed", label),
        policy_bypass_self_grant_allowed=_require_bool(
            data, "policy_bypass_self_grant_allowed", label
        ),
        untrusted_input_can_modify_identity=_require_bool(
            data, "untrusted_input_can_modify_identity", label
        ),
    )


def _parse_development_allowed(data: dict[str, Any]) -> DevelopmentAllowed:
    label = "identity_kernel.development_allowed"
    return DevelopmentAllowed(
        skill_growth=_require_bool(data, "skill_growth", label),
        memory_growth=_require_bool(data, "memory_growth", label),
        communication_refinement=_require_bool(data, "communication_refinement", label),
        procedure_growth=_require_bool(data, "procedure_growth", label),
        specialist_growth=_require_bool(data, "specialist_growth", label),
        world_model_revision=_require_bool(data, "world_model_revision", label),
    )


def _parse_development_forbidden(data: dict[str, Any]) -> DevelopmentForbidden:
    label = "identity_kernel.development_forbidden"
    return DevelopmentForbidden(
        operator_replacement=_require_bool(data, "operator_replacement", label),
        secret_goal_creation=_require_bool(data, "secret_goal_creation", label),
        self_authority_expansion=_require_bool(data, "self_authority_expansion", label),
        unapproved_identity_rewrite=_require_bool(data, "unapproved_identity_rewrite", label),
    )


def _parse_invariant(raw: dict[str, Any]) -> IdentityInvariant:
    inv_id = raw.get("id")
    if not isinstance(inv_id, str) or not inv_id.strip():
        raise IdentityKernelError("invariant id must be a non-empty string")
    key = raw.get("key")
    if not isinstance(key, str) or not key.strip():
        raise IdentityKernelError(f"invariant {inv_id}: key must be a non-empty string")
    statement = raw.get("statement")
    if not isinstance(statement, str) or not statement.strip():
        raise IdentityKernelError(f"invariant {inv_id}: statement must be a non-empty string")
    if "expected_value" not in raw or not isinstance(raw["expected_value"], bool):
        raise IdentityKernelError(f"invariant {inv_id}: expected_value must be a boolean")
    if "mutable" not in raw or not isinstance(raw["mutable"], bool):
        raise IdentityKernelError(f"invariant {inv_id}: mutable must be a boolean")
    severity = raw.get("severity")
    if severity not in {"info", "warning", "critical"}:
        raise IdentityKernelError(f"invariant {inv_id}: invalid severity")
    violation_action = raw.get("violation_action")
    if violation_action not in {"warn", "block", "fail_boot"}:
        raise IdentityKernelError(f"invariant {inv_id}: invalid violation_action")
    rationale = raw.get("rationale")
    if not isinstance(rationale, str) or not rationale.strip():
        raise IdentityKernelError(f"invariant {inv_id}: rationale must be a non-empty string")
    return IdentityInvariant(
        id=inv_id,
        key=key,
        statement=statement,
        expected_value=raw["expected_value"],
        mutable=raw["mutable"],
        severity=severity,
        violation_action=violation_action,
        rationale=rationale,
    )


def parse_identity_kernel_document(data: dict[str, Any]) -> AurelIdentityKernel:
    """Parse a loaded YAML document into a typed identity kernel."""
    root = _require_mapping(data.get("identity_kernel"), "identity_kernel")
    for field in (
        "schema_version",
        "name",
        "class",
        "primary_operator",
        "final_authority",
    ):
        if field not in root or not isinstance(root[field], str) or not root[field].strip():
            raise IdentityKernelError(f"missing or empty identity_kernel.{field}")
    if "local_first" not in root or not isinstance(root["local_first"], bool):
        raise IdentityKernelError("missing or invalid identity_kernel.local_first")
    for section in ("immutables", "development_allowed", "development_forbidden", "invariants"):
        if section not in root:
            raise IdentityKernelError(f"missing required section: identity_kernel.{section}")

    immutables = _parse_immutables(_require_mapping(root["immutables"], "immutables"))
    development_allowed = _parse_development_allowed(
        _require_mapping(root["development_allowed"], "development_allowed")
    )
    development_forbidden = _parse_development_forbidden(
        _require_mapping(root["development_forbidden"], "development_forbidden")
    )

    raw_invariants = root["invariants"]
    if not isinstance(raw_invariants, list) or not raw_invariants:
        raise IdentityKernelError("identity_kernel.invariants must be a non-empty list")
    invariants = tuple(
        _parse_invariant(_require_mapping(item, "invariant")) for item in raw_invariants
    )

    notes_raw = root.get("notes")
    notes: Mapping[str, Any] | None
    if notes_raw is None:
        notes = None
    elif isinstance(notes_raw, dict):
        notes = notes_raw
    else:
        raise IdentityKernelError("identity_kernel.notes must be a mapping when present")

    return AurelIdentityKernel(
        schema_version=root["schema_version"],
        name=root["name"],
        agent_class=root["class"],
        primary_operator=root["primary_operator"],
        final_authority=root["final_authority"],
        local_first=root["local_first"],
        immutables=immutables,
        development_allowed=development_allowed,
        development_forbidden=development_forbidden,
        invariants=invariants,
        notes=notes,
    )


def load_identity_kernel(path: str | Path | None = None) -> AurelIdentityKernel:
    """Load and parse identity kernel from a local YAML file."""
    config_path = Path(path) if path is not None else default_identity_kernel_path()
    if not config_path.is_file():
        raise IdentityKernelError(f"identity kernel file not found: {config_path}")
    try:
        document = load_yaml(config_path.read_text(encoding="utf-8"))
    except YamlParseError as exc:
        raise IdentityKernelError(f"YAML parse error: {exc}") from exc
    if not document:
        raise IdentityKernelError("identity kernel document is empty")
    return parse_identity_kernel_document(document)
