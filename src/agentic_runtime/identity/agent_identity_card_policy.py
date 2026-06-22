"""Aurel Agent Identity Card config (P1.4.7)."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, Mapping

from ..yaml_minimal import YamlParseError, load_yaml

AGENT_IDENTITY_CARD_VALIDATOR_VERSION = "1.0.0"

Severity = Literal["info", "warning", "critical"]
ViolationAction = Literal["warn", "block", "fail_build"]
HashAlgorithm = Literal["sha256"]
ValidationStatus = Literal["valid", "invalid"]
AgentType = Literal["ai_agent"]


class AgentIdentityCardError(ValueError):
    """Raised when agent identity card config or build cannot proceed."""


@dataclass(frozen=True)
class AgentIdentityConfig:
    agent_id: str
    agent_name: str
    agent_type: AgentType
    agent_class: str
    identity_version: str
    deployment_scope: str
    machine_scope: str


@dataclass(frozen=True)
class AgentAuthorityBinding:
    authority_source: str
    final_authority: str
    self_escalation_allowed: bool
    delegated_authority_required_for_actions: bool
    tool_access_implies_authority: bool


@dataclass(frozen=True)
class AgentSourceBindings:
    identity_kernel_hash: str | None
    persona_manifest_hash: str | None
    operator_contract_hash: str | None
    communication_modes_hash: str | None
    identity_prompt_compiler_policy_hash: str | None
    self_model_hash: str | None


@dataclass(frozen=True)
class AgentRuntimeIdentity:
    runtime_instance_id: str | None
    runtime_instance_id_strategy: str
    runtime_version: str | None
    runtime_started_at: str | None
    runtime_machine_scope: str
    local_first: bool


@dataclass(frozen=True)
class AgentIdentityTaxonomy:
    model_identity: str | None
    agent_identity: str
    workload_identity: str | None
    delegated_identity: str | None
    human_principal_identity: str


@dataclass(frozen=True)
class AgentFuturePlaceholders:
    workload_identity_ref: str | None
    delegation_grant_ref: str | None
    delegation_chain_ref: str | None
    non_repudiation_key_ref: str | None
    ledger_identity_ref: str | None
    output_passport_producer_ref: str | None


@dataclass(frozen=True)
class AgentIdentityBoundaries:
    card_can_grant_authority: bool
    card_can_change_identity_kernel: bool
    card_can_change_autonomy: bool
    card_can_create_delegation: bool
    card_can_authorize_tools: bool
    card_can_replace_operator: bool
    card_can_override_policy: bool


@dataclass(frozen=True)
class AgentIdentityInvariant:
    id: str
    key: str
    statement: str
    expected_value: bool | str
    mutable: bool
    severity: Severity
    violation_action: ViolationAction
    rationale: str


@dataclass(frozen=True)
class AgentIdentityCardValidationResult:
    valid: bool
    errors: tuple[str, ...]
    warnings: tuple[str, ...]
    critical_failures: tuple[str, ...]


@dataclass(frozen=True)
class AgentIdentityCardConfig:
    schema_version: str
    card_name: str
    card_class: str
    applies_to_agent: str
    agent: AgentIdentityConfig
    authority: AgentAuthorityBinding
    source_bindings: AgentSourceBindings
    runtime: AgentRuntimeIdentity
    identity_taxonomy: AgentIdentityTaxonomy
    future_placeholders: AgentFuturePlaceholders
    boundaries: AgentIdentityBoundaries
    invariants: tuple[AgentIdentityInvariant, ...]
    notes: Mapping[str, Any] | None = None


def default_agent_identity_card_path() -> Path:
    """Return canonical repo-root path to agent_identity_card.yaml."""
    return Path(__file__).resolve().parents[3] / "config" / "aurel" / "agent_identity_card.yaml"


def _require_mapping(data: object, label: str) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise AgentIdentityCardError(f"{label} must be a mapping")
    return data


def _require_bool(data: dict[str, Any], key: str, label: str) -> bool:
    if key not in data:
        raise AgentIdentityCardError(f"missing required field: {label}.{key}")
    value = data[key]
    if not isinstance(value, bool):
        raise AgentIdentityCardError(f"{label}.{key} must be a boolean")
    return value


def _require_str(data: dict[str, Any], key: str, label: str) -> str:
    if key not in data or not isinstance(data[key], str) or not data[key].strip():
        raise AgentIdentityCardError(f"missing or empty {label}.{key}")
    return data[key]


def _optional_str(data: dict[str, Any], key: str) -> str | None:
    if key not in data or data[key] is None:
        return None
    value = data[key]
    if not isinstance(value, str):
        raise AgentIdentityCardError(f"{key} must be a string or null")
    return value


def _optional_hash(data: dict[str, Any], key: str, label: str) -> str | None:
    value = _optional_str(data, key)
    if value is None:
        return None
    if not value.strip():
        raise AgentIdentityCardError(f"{label}.{key} must be non-empty when provided")
    return value


def _parse_agent(data: dict[str, Any]) -> AgentIdentityConfig:
    label = "agent_identity_card.agent"
    agent_type = _require_str(data, "agent_type", label)
    if agent_type != "ai_agent":
        raise AgentIdentityCardError(f"{label}.agent_type must be 'ai_agent'")
    return AgentIdentityConfig(
        agent_id=_require_str(data, "agent_id", label),
        agent_name=_require_str(data, "agent_name", label),
        agent_type="ai_agent",
        agent_class=_require_str(data, "agent_class", label),
        identity_version=_require_str(data, "identity_version", label),
        deployment_scope=_require_str(data, "deployment_scope", label),
        machine_scope=_require_str(data, "machine_scope", label),
    )


def _parse_authority(data: dict[str, Any]) -> AgentAuthorityBinding:
    label = "agent_identity_card.authority"
    return AgentAuthorityBinding(
        authority_source=_require_str(data, "authority_source", label),
        final_authority=_require_str(data, "final_authority", label),
        self_escalation_allowed=_require_bool(data, "self_escalation_allowed", label),
        delegated_authority_required_for_actions=_require_bool(
            data, "delegated_authority_required_for_actions", label
        ),
        tool_access_implies_authority=_require_bool(data, "tool_access_implies_authority", label),
    )


def _parse_source_bindings(data: dict[str, Any]) -> AgentSourceBindings:
    label = "agent_identity_card.source_bindings"
    return AgentSourceBindings(
        identity_kernel_hash=_optional_hash(data, "identity_kernel_hash", label),
        persona_manifest_hash=_optional_hash(data, "persona_manifest_hash", label),
        operator_contract_hash=_optional_hash(data, "operator_contract_hash", label),
        communication_modes_hash=_optional_hash(data, "communication_modes_hash", label),
        identity_prompt_compiler_policy_hash=_optional_hash(
            data, "identity_prompt_compiler_policy_hash", label
        ),
        self_model_hash=_optional_hash(data, "self_model_hash", label),
    )


def _parse_runtime(data: dict[str, Any]) -> AgentRuntimeIdentity:
    label = "agent_identity_card.runtime"
    return AgentRuntimeIdentity(
        runtime_instance_id=_optional_str(data, "runtime_instance_id"),
        runtime_instance_id_strategy=_require_str(data, "runtime_instance_id_strategy", label),
        runtime_version=_optional_str(data, "runtime_version"),
        runtime_started_at=_optional_str(data, "runtime_started_at"),
        runtime_machine_scope=_require_str(data, "runtime_machine_scope", label),
        local_first=_require_bool(data, "local_first", label),
    )


def _parse_taxonomy(data: dict[str, Any]) -> AgentIdentityTaxonomy:
    label = "agent_identity_card.identity_taxonomy"
    return AgentIdentityTaxonomy(
        model_identity=_optional_str(data, "model_identity"),
        agent_identity=_require_str(data, "agent_identity", label),
        workload_identity=_optional_str(data, "workload_identity"),
        delegated_identity=_optional_str(data, "delegated_identity"),
        human_principal_identity=_require_str(data, "human_principal_identity", label),
    )


def _parse_future_placeholders(data: dict[str, Any]) -> AgentFuturePlaceholders:
    return AgentFuturePlaceholders(
        workload_identity_ref=_optional_str(data, "workload_identity_ref"),
        delegation_grant_ref=_optional_str(data, "delegation_grant_ref"),
        delegation_chain_ref=_optional_str(data, "delegation_chain_ref"),
        non_repudiation_key_ref=_optional_str(data, "non_repudiation_key_ref"),
        ledger_identity_ref=_optional_str(data, "ledger_identity_ref"),
        output_passport_producer_ref=_optional_str(data, "output_passport_producer_ref"),
    )


def _parse_boundaries(data: dict[str, Any]) -> AgentIdentityBoundaries:
    label = "agent_identity_card.boundaries"
    return AgentIdentityBoundaries(
        card_can_grant_authority=_require_bool(data, "card_can_grant_authority", label),
        card_can_change_identity_kernel=_require_bool(
            data, "card_can_change_identity_kernel", label
        ),
        card_can_change_autonomy=_require_bool(data, "card_can_change_autonomy", label),
        card_can_create_delegation=_require_bool(data, "card_can_create_delegation", label),
        card_can_authorize_tools=_require_bool(data, "card_can_authorize_tools", label),
        card_can_replace_operator=_require_bool(data, "card_can_replace_operator", label),
        card_can_override_policy=_require_bool(data, "card_can_override_policy", label),
    )


def _parse_invariant(data: dict[str, Any]) -> AgentIdentityInvariant:
    inv_id = _require_str(data, "id", "invariant")
    key = _require_str(data, "key", f"invariant[{inv_id}]")
    statement = _require_str(data, "statement", f"invariant[{inv_id}]")
    rationale = _require_str(data, "rationale", f"invariant[{inv_id}]")
    severity = _require_str(data, "severity", f"invariant[{inv_id}]")
    violation_action = _require_str(data, "violation_action", f"invariant[{inv_id}]")
    if "expected_value" not in data:
        raise AgentIdentityCardError(f"invariant[{inv_id}].expected_value is required")
    expected = data["expected_value"]
    if not isinstance(expected, (bool, str)):
        raise AgentIdentityCardError(
            f"invariant[{inv_id}].expected_value must be boolean or string"
        )
    if "mutable" not in data or not isinstance(data["mutable"], bool):
        raise AgentIdentityCardError(f"invariant[{inv_id}].mutable must be a boolean")
    return AgentIdentityInvariant(
        id=inv_id,
        key=key,
        statement=statement,
        expected_value=expected,
        mutable=data["mutable"],
        severity=severity,
        violation_action=violation_action,
        rationale=rationale,
    )


def parse_agent_identity_card_document(doc: Mapping[str, Any]) -> AgentIdentityCardConfig:
    """Parse a loaded YAML document into AgentIdentityCardConfig."""
    root = _require_mapping(doc.get("agent_identity_card"), "agent_identity_card")
    label = "agent_identity_card"
    invariants_raw = root.get("invariants")
    if not isinstance(invariants_raw, list) or not invariants_raw:
        raise AgentIdentityCardError("agent_identity_card.invariants must be non-empty")
    invariants = tuple(
        _parse_invariant(_require_mapping(item, "invariant")) for item in invariants_raw
    )
    notes_raw = root.get("notes")
    notes: Mapping[str, Any] | None
    if notes_raw is None:
        notes = None
    elif isinstance(notes_raw, dict):
        notes = dict(notes_raw)
    else:
        raise AgentIdentityCardError("agent_identity_card.notes must be a mapping")
    return AgentIdentityCardConfig(
        schema_version=_require_str(root, "schema_version", label),
        card_name=_require_str(root, "card_name", label),
        card_class=_require_str(root, "card_class", label),
        applies_to_agent=_require_str(root, "applies_to_agent", label),
        agent=_parse_agent(_require_mapping(root.get("agent"), f"{label}.agent")),
        authority=_parse_authority(_require_mapping(root.get("authority"), f"{label}.authority")),
        source_bindings=_parse_source_bindings(
            _require_mapping(root.get("source_bindings"), f"{label}.source_bindings")
        ),
        runtime=_parse_runtime(_require_mapping(root.get("runtime"), f"{label}.runtime")),
        identity_taxonomy=_parse_taxonomy(
            _require_mapping(root.get("identity_taxonomy"), f"{label}.identity_taxonomy")
        ),
        future_placeholders=_parse_future_placeholders(
            _require_mapping(root.get("future_placeholders"), f"{label}.future_placeholders")
        ),
        boundaries=_parse_boundaries(_require_mapping(root.get("boundaries"), f"{label}.boundaries")),
        invariants=invariants,
        notes=notes,
    )


def load_agent_identity_card_config(path: str | Path | None = None) -> AgentIdentityCardConfig:
    """Load agent identity card config from YAML file."""
    target = Path(path) if path is not None else default_agent_identity_card_path()
    try:
        doc = load_yaml(target.read_text(encoding="utf-8"))
    except (OSError, YamlParseError) as exc:
        raise AgentIdentityCardError(
            f"failed to load agent identity card config from {target}: {exc}"
        ) from exc
    return parse_agent_identity_card_document(doc)
