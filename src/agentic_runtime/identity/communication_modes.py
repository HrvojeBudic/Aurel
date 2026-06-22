"""Aurel Communication Modes — cognitive/output mode registry (P1.4.4).

Communication Modes are not authority. They are not autonomy. They are not tool
permissions. They are not policy. They are not governance profiles. They are not
the Heretic Sandbox engine. They do not execute actions. Mode can shape the mind;
mode cannot move the hand.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, Mapping

from ..yaml_minimal import YamlParseError, load_yaml

COMMUNICATION_MODES_VALIDATOR_VERSION = "1.0.0"

REQUIRED_MODES = frozenset(
    {"FOCUS", "DEBUG", "DEPLOY", "SHADOW", "EVOLVE", "CHANNEL", "HERETIC"}
)

Severity = Literal["info", "warning", "critical"]
ViolationAction = Literal["warn", "block", "fail_boot"]
HashAlgorithm = Literal["sha256"]
ValidationStatus = Literal["valid", "invalid"]


class CommunicationModeError(ValueError):
    """Raised when communication modes config cannot be loaded or parsed."""


@dataclass(frozen=True)
class CommunicationModeGlobalBoundaries:
    modes_can_grant_permissions: bool
    modes_can_change_autonomy: bool
    modes_can_override_identity_kernel: bool
    modes_can_override_persona_manifest: bool
    modes_can_override_operator_contract: bool
    modes_can_override_policy: bool
    modes_can_disable_constitutional_floor: bool
    modes_can_write_memory_directly: bool
    modes_can_canonize_output: bool
    modes_can_execute_actions: bool


@dataclass(frozen=True)
class CommunicationModeSpec:
    name: str
    purpose: str
    cognitive_posture: str
    output_bias: Mapping[str, bool]
    challenge_emphasis: Mapping[str, bool]
    risk_emphasis: Mapping[str, bool]
    boundaries: Mapping[str, bool]


@dataclass(frozen=True)
class CommunicationModeInvariant:
    id: str
    key: str
    statement: str
    expected_value: bool
    mutable: bool
    severity: Severity
    violation_action: ViolationAction
    rationale: str


@dataclass(frozen=True)
class CommunicationModeRegistryHash:
    algorithm: HashAlgorithm
    value: str


@dataclass(frozen=True)
class CommunicationModeValidationResult:
    valid: bool
    errors: tuple[str, ...]
    warnings: tuple[str, ...]
    critical_failures: tuple[str, ...]


@dataclass(frozen=True)
class CommunicationModeAttestation:
    schema_version: str
    registry_hash: str
    hash_algorithm: str
    config_path: str
    validation_status: ValidationStatus
    validator_version: str
    critical_failures: tuple[str, ...]


@dataclass(frozen=True)
class CommunicationModeSafeSummary:
    mode_name: str
    purpose: str
    cognitive_posture: str
    output_rules: tuple[str, ...]
    challenge_rules: tuple[str, ...]
    risk_rules: tuple[str, ...]
    authority_boundaries: tuple[str, ...]


@dataclass(frozen=True)
class CommunicationModeLookupResult:
    found: bool
    mode_name: str | None
    mode: CommunicationModeSpec | None
    error: str | None


@dataclass(frozen=True)
class AurelCommunicationModeRegistry:
    schema_version: str
    registry_name: str
    registry_class: str
    applies_to_agent: str
    global_boundaries: CommunicationModeGlobalBoundaries
    modes: Mapping[str, CommunicationModeSpec]
    invariants: tuple[CommunicationModeInvariant, ...]
    notes: Mapping[str, Any] | None = None


def default_communication_modes_path() -> Path:
    """Return canonical repo-root path to communication_modes.yaml."""
    return Path(__file__).resolve().parents[3] / "config" / "aurel" / "communication_modes.yaml"


def _require_mapping(data: object, label: str) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise CommunicationModeError(f"{label} must be a mapping")
    return data


def _require_bool(data: dict[str, Any], key: str, label: str) -> bool:
    if key not in data:
        raise CommunicationModeError(f"missing required field: {label}.{key}")
    value = data[key]
    if not isinstance(value, bool):
        raise CommunicationModeError(f"{label}.{key} must be a boolean")
    return value


def _require_str(data: dict[str, Any], key: str, label: str) -> str:
    if key not in data or not isinstance(data[key], str) or not data[key].strip():
        raise CommunicationModeError(f"missing or empty {label}.{key}")
    return data[key]


def _parse_bool_map(data: dict[str, Any], label: str) -> dict[str, bool]:
    result: dict[str, bool] = {}
    for key, value in data.items():
        if not isinstance(key, str) or not key.strip():
            raise CommunicationModeError(f"{label}: keys must be non-empty strings")
        if not isinstance(value, bool):
            raise CommunicationModeError(f"{label}.{key} must be a boolean")
        result[key] = value
    return result


def _parse_global_boundaries(data: dict[str, Any]) -> CommunicationModeGlobalBoundaries:
    label = "communication_modes.global_boundaries"
    return CommunicationModeGlobalBoundaries(
        modes_can_grant_permissions=_require_bool(data, "modes_can_grant_permissions", label),
        modes_can_change_autonomy=_require_bool(data, "modes_can_change_autonomy", label),
        modes_can_override_identity_kernel=_require_bool(
            data, "modes_can_override_identity_kernel", label
        ),
        modes_can_override_persona_manifest=_require_bool(
            data, "modes_can_override_persona_manifest", label
        ),
        modes_can_override_operator_contract=_require_bool(
            data, "modes_can_override_operator_contract", label
        ),
        modes_can_override_policy=_require_bool(data, "modes_can_override_policy", label),
        modes_can_disable_constitutional_floor=_require_bool(
            data, "modes_can_disable_constitutional_floor", label
        ),
        modes_can_write_memory_directly=_require_bool(
            data, "modes_can_write_memory_directly", label
        ),
        modes_can_canonize_output=_require_bool(data, "modes_can_canonize_output", label),
        modes_can_execute_actions=_require_bool(data, "modes_can_execute_actions", label),
    )


def _parse_mode(name: str, data: dict[str, Any]) -> CommunicationModeSpec:
    label = f"communication_modes.modes.{name}"
    for section in ("output_bias", "challenge_emphasis", "risk_emphasis", "boundaries"):
        if section not in data:
            raise CommunicationModeError(f"missing required section: {label}.{section}")
    return CommunicationModeSpec(
        name=name,
        purpose=_require_str(data, "purpose", label),
        cognitive_posture=_require_str(data, "cognitive_posture", label),
        output_bias=_parse_bool_map(
            _require_mapping(data["output_bias"], "output_bias"), f"{label}.output_bias"
        ),
        challenge_emphasis=_parse_bool_map(
            _require_mapping(data["challenge_emphasis"], "challenge_emphasis"),
            f"{label}.challenge_emphasis",
        ),
        risk_emphasis=_parse_bool_map(
            _require_mapping(data["risk_emphasis"], "risk_emphasis"), f"{label}.risk_emphasis"
        ),
        boundaries=_parse_bool_map(
            _require_mapping(data["boundaries"], "boundaries"), f"{label}.boundaries"
        ),
    )


def _parse_invariant(raw: dict[str, Any]) -> CommunicationModeInvariant:
    inv_id = raw.get("id")
    if not isinstance(inv_id, str) or not inv_id.strip():
        raise CommunicationModeError("invariant id must be a non-empty string")
    key = raw.get("key")
    if not isinstance(key, str) or not key.strip():
        raise CommunicationModeError(f"invariant {inv_id}: key must be a non-empty string")
    statement = raw.get("statement")
    if not isinstance(statement, str) or not statement.strip():
        raise CommunicationModeError(f"invariant {inv_id}: statement must be a non-empty string")
    if "expected_value" not in raw or not isinstance(raw["expected_value"], bool):
        raise CommunicationModeError(f"invariant {inv_id}: expected_value must be a boolean")
    if "mutable" not in raw or not isinstance(raw["mutable"], bool):
        raise CommunicationModeError(f"invariant {inv_id}: mutable must be a boolean")
    severity = raw.get("severity")
    if severity not in {"info", "warning", "critical"}:
        raise CommunicationModeError(f"invariant {inv_id}: invalid severity")
    violation_action = raw.get("violation_action")
    if violation_action not in {"warn", "block", "fail_boot"}:
        raise CommunicationModeError(f"invariant {inv_id}: invalid violation_action")
    rationale = raw.get("rationale")
    if not isinstance(rationale, str) or not rationale.strip():
        raise CommunicationModeError(f"invariant {inv_id}: rationale must be a non-empty string")
    return CommunicationModeInvariant(
        id=inv_id,
        key=key,
        statement=statement,
        expected_value=raw["expected_value"],
        mutable=raw["mutable"],
        severity=severity,
        violation_action=violation_action,
        rationale=rationale,
    )


def parse_communication_modes_document(data: dict[str, Any]) -> AurelCommunicationModeRegistry:
    """Parse a loaded YAML document into a typed communication mode registry."""
    root = _require_mapping(data.get("communication_modes"), "communication_modes")
    for field in ("schema_version", "registry_name", "registry_class", "applies_to_agent"):
        _require_str(root, field, "communication_modes")
    for section in ("global_boundaries", "modes", "invariants"):
        if section not in root:
            raise CommunicationModeError(f"missing required section: communication_modes.{section}")

    raw_modes = _require_mapping(root["modes"], "modes")
    if not raw_modes:
        raise CommunicationModeError("communication_modes.modes must be a non-empty mapping")
    modes: dict[str, CommunicationModeSpec] = {}
    for mode_name, mode_data in raw_modes.items():
        if not isinstance(mode_name, str) or not mode_name.strip():
            raise CommunicationModeError("mode names must be non-empty strings")
        canonical = mode_name.upper()
        modes[canonical] = _parse_mode(canonical, _require_mapping(mode_data, mode_name))

    raw_invariants = root["invariants"]
    if not isinstance(raw_invariants, list) or not raw_invariants:
        raise CommunicationModeError("communication_modes.invariants must be a non-empty list")
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
        raise CommunicationModeError("communication_modes.notes must be a mapping when present")

    return AurelCommunicationModeRegistry(
        schema_version=root["schema_version"],
        registry_name=root["registry_name"],
        registry_class=root["registry_class"],
        applies_to_agent=root["applies_to_agent"],
        global_boundaries=_parse_global_boundaries(
            _require_mapping(root["global_boundaries"], "global_boundaries")
        ),
        modes=modes,
        invariants=invariants,
        notes=notes,
    )


def load_communication_mode_registry(path: str | Path | None = None) -> AurelCommunicationModeRegistry:
    """Load and parse communication modes registry from a local YAML file."""
    config_path = Path(path) if path is not None else default_communication_modes_path()
    if not config_path.is_file():
        raise CommunicationModeError(f"communication modes file not found: {config_path}")
    try:
        document = load_yaml(config_path.read_text(encoding="utf-8"))
    except YamlParseError as exc:
        raise CommunicationModeError(f"YAML parse error: {exc}") from exc
    if not document:
        raise CommunicationModeError("communication modes document is empty")
    return parse_communication_modes_document(document)
