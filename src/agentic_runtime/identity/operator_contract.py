"""Aurel Operator Relationship Contract — authority relationship anchor (P1.4.3).

Operator Relationship Contract is not persona. It is not autonomy. It is not policy
cards. It is not full delegation mesh. It is not the approval workbench. It is not
the non-repudiation ledger. This module defines the principal/delegate relationship
and authority posture only.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, Mapping

from ..yaml_minimal import YamlParseError, load_yaml

OPERATOR_CONTRACT_VALIDATOR_VERSION = "1.0.0"

Severity = Literal["info", "warning", "critical"]
ViolationAction = Literal["warn", "block", "fail_boot"]
HashAlgorithm = Literal["sha256"]
ValidationStatus = Literal["valid", "invalid"]


class OperatorContractError(ValueError):
    """Raised when operator contract config cannot be loaded or parsed."""


@dataclass(frozen=True)
class ContractParty:
    id: str
    role: str
    type: str


@dataclass(frozen=True)
class OperatorContractParties:
    principal: ContractParty
    delegate: ContractParty


@dataclass(frozen=True)
class OperatorAuthorityRules:
    operator_final_authority: bool
    aurel_final_authority: bool
    aurel_can_self_escalate: bool
    aurel_can_replace_operator: bool
    aurel_can_override_operator_judgment: bool
    aurel_can_refuse_forbidden_action: bool
    aurel_can_challenge_operator: bool
    aurel_must_challenge_when_risk_detected: bool


@dataclass(frozen=True)
class RelationshipBehaviorRules:
    disagreement_allowed: bool
    disagreement_must_be_explained: bool
    risk_challenge_required: bool
    uncertainty_must_be_disclosed: bool
    tradeoffs_must_be_disclosed: bool
    passive_obedience_required: bool
    blind_execution_forbidden: bool


@dataclass(frozen=True)
class NonManipulationRules:
    manipulation_forbidden: bool
    hidden_persuasion_forbidden: bool
    flattery_over_truth_forbidden: bool
    emotional_pressure_forbidden: bool
    dark_pattern_guidance_forbidden: bool
    coercive_language_forbidden: bool


@dataclass(frozen=True)
class ExecutionAuthorityRules:
    tool_access_implies_authority: bool
    serious_actions_require_authority_check: bool
    irreversible_actions_require_operator_approval: bool
    external_side_effects_require_policy_allowance: bool
    memory_canon_changes_require_approval_or_future_policy: bool


@dataclass(frozen=True)
class AccountabilityRules:
    serious_actions_must_be_traceable: bool
    operator_authorization_ref_required_for_high_risk: bool
    aurel_must_explain_action_basis: bool
    aurel_must_surface_reversibility: bool
    aurel_must_surface_known_limitations: bool


@dataclass(frozen=True)
class OperatorFuturePlaceholders:
    autonomy_session_ref: str | None
    delegation_grant_ref: str | None
    approval_workbench_ref: str | None
    non_repudiation_attestation_ref: str | None


@dataclass(frozen=True)
class OperatorContractBoundaries:
    cannot_override_identity_kernel: bool
    cannot_override_persona_manifest_boundaries: bool
    cannot_grant_tool_rights: bool
    cannot_change_autonomy: bool
    cannot_disable_constitutional_floor: bool
    cannot_canonize_untrusted_input: bool
    cannot_expand_delegation_scope: bool


@dataclass(frozen=True)
class OperatorContractInvariant:
    id: str
    key: str
    statement: str
    expected_value: bool
    mutable: bool
    severity: Severity
    violation_action: ViolationAction
    rationale: str


@dataclass(frozen=True)
class OperatorContractHash:
    algorithm: HashAlgorithm
    value: str


@dataclass(frozen=True)
class OperatorContractValidationResult:
    valid: bool
    errors: tuple[str, ...]
    warnings: tuple[str, ...]
    critical_failures: tuple[str, ...]


@dataclass(frozen=True)
class OperatorContractAttestation:
    schema_version: str
    contract_hash: str
    hash_algorithm: str
    config_path: str
    validation_status: ValidationStatus
    validator_version: str
    critical_failures: tuple[str, ...]


@dataclass(frozen=True)
class OperatorContractSafeSummary:
    contract_name: str
    principal_summary: str
    delegate_summary: str
    authority_rules: tuple[str, ...]
    disagreement_rules: tuple[str, ...]
    challenge_rules: tuple[str, ...]
    non_manipulation_rules: tuple[str, ...]
    execution_authority_boundaries: tuple[str, ...]
    accountability_rules: tuple[str, ...]


@dataclass(frozen=True)
class AuthorityRelation:
    principal_id: str
    principal_role: str
    delegate_id: str
    delegate_role: str
    final_authority: str
    delegate_can_self_escalate: bool
    delegate_can_replace_principal: bool


@dataclass(frozen=True)
class AurelOperatorContract:
    schema_version: str
    name: str
    contract_class: str
    applies_to_agent: str
    parties: OperatorContractParties
    authority: OperatorAuthorityRules
    relationship_behavior: RelationshipBehaviorRules
    non_manipulation: NonManipulationRules
    execution_authority: ExecutionAuthorityRules
    accountability: AccountabilityRules
    future_placeholders: OperatorFuturePlaceholders
    boundaries: OperatorContractBoundaries
    invariants: tuple[OperatorContractInvariant, ...]
    notes: Mapping[str, Any] | None = None


def default_operator_contract_path() -> Path:
    """Return canonical repo-root path to operator_contract.yaml."""
    return Path(__file__).resolve().parents[3] / "config" / "aurel" / "operator_contract.yaml"


def _require_mapping(data: object, label: str) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise OperatorContractError(f"{label} must be a mapping")
    return data


def _require_bool(data: dict[str, Any], key: str, label: str) -> bool:
    if key not in data:
        raise OperatorContractError(f"missing required field: {label}.{key}")
    value = data[key]
    if not isinstance(value, bool):
        raise OperatorContractError(f"{label}.{key} must be a boolean")
    return value


def _require_str(data: dict[str, Any], key: str, label: str) -> str:
    if key not in data or not isinstance(data[key], str) or not data[key].strip():
        raise OperatorContractError(f"missing or empty {label}.{key}")
    return data[key]


def _parse_party(data: dict[str, Any], label: str) -> ContractParty:
    return ContractParty(
        id=_require_str(data, "id", label),
        role=_require_str(data, "role", label),
        type=_require_str(data, "type", label),
    )


def _parse_parties(data: dict[str, Any]) -> OperatorContractParties:
    label = "operator_contract.parties"
    if "principal" not in data or "delegate" not in data:
        raise OperatorContractError(f"missing required section: {label}.principal or delegate")
    return OperatorContractParties(
        principal=_parse_party(_require_mapping(data["principal"], "principal"), f"{label}.principal"),
        delegate=_parse_party(_require_mapping(data["delegate"], "delegate"), f"{label}.delegate"),
    )


def _parse_authority(data: dict[str, Any]) -> OperatorAuthorityRules:
    label = "operator_contract.authority"
    return OperatorAuthorityRules(
        operator_final_authority=_require_bool(data, "operator_final_authority", label),
        aurel_final_authority=_require_bool(data, "aurel_final_authority", label),
        aurel_can_self_escalate=_require_bool(data, "aurel_can_self_escalate", label),
        aurel_can_replace_operator=_require_bool(data, "aurel_can_replace_operator", label),
        aurel_can_override_operator_judgment=_require_bool(
            data, "aurel_can_override_operator_judgment", label
        ),
        aurel_can_refuse_forbidden_action=_require_bool(
            data, "aurel_can_refuse_forbidden_action", label
        ),
        aurel_can_challenge_operator=_require_bool(data, "aurel_can_challenge_operator", label),
        aurel_must_challenge_when_risk_detected=_require_bool(
            data, "aurel_must_challenge_when_risk_detected", label
        ),
    )


def _parse_relationship_behavior(data: dict[str, Any]) -> RelationshipBehaviorRules:
    label = "operator_contract.relationship_behavior"
    return RelationshipBehaviorRules(
        disagreement_allowed=_require_bool(data, "disagreement_allowed", label),
        disagreement_must_be_explained=_require_bool(data, "disagreement_must_be_explained", label),
        risk_challenge_required=_require_bool(data, "risk_challenge_required", label),
        uncertainty_must_be_disclosed=_require_bool(data, "uncertainty_must_be_disclosed", label),
        tradeoffs_must_be_disclosed=_require_bool(data, "tradeoffs_must_be_disclosed", label),
        passive_obedience_required=_require_bool(data, "passive_obedience_required", label),
        blind_execution_forbidden=_require_bool(data, "blind_execution_forbidden", label),
    )


def _parse_non_manipulation(data: dict[str, Any]) -> NonManipulationRules:
    label = "operator_contract.non_manipulation"
    return NonManipulationRules(
        manipulation_forbidden=_require_bool(data, "manipulation_forbidden", label),
        hidden_persuasion_forbidden=_require_bool(data, "hidden_persuasion_forbidden", label),
        flattery_over_truth_forbidden=_require_bool(data, "flattery_over_truth_forbidden", label),
        emotional_pressure_forbidden=_require_bool(data, "emotional_pressure_forbidden", label),
        dark_pattern_guidance_forbidden=_require_bool(data, "dark_pattern_guidance_forbidden", label),
        coercive_language_forbidden=_require_bool(data, "coercive_language_forbidden", label),
    )


def _parse_execution_authority(data: dict[str, Any]) -> ExecutionAuthorityRules:
    label = "operator_contract.execution_authority"
    return ExecutionAuthorityRules(
        tool_access_implies_authority=_require_bool(data, "tool_access_implies_authority", label),
        serious_actions_require_authority_check=_require_bool(
            data, "serious_actions_require_authority_check", label
        ),
        irreversible_actions_require_operator_approval=_require_bool(
            data, "irreversible_actions_require_operator_approval", label
        ),
        external_side_effects_require_policy_allowance=_require_bool(
            data, "external_side_effects_require_policy_allowance", label
        ),
        memory_canon_changes_require_approval_or_future_policy=_require_bool(
            data, "memory_canon_changes_require_approval_or_future_policy", label
        ),
    )


def _parse_accountability(data: dict[str, Any]) -> AccountabilityRules:
    label = "operator_contract.accountability"
    return AccountabilityRules(
        serious_actions_must_be_traceable=_require_bool(
            data, "serious_actions_must_be_traceable", label
        ),
        operator_authorization_ref_required_for_high_risk=_require_bool(
            data, "operator_authorization_ref_required_for_high_risk", label
        ),
        aurel_must_explain_action_basis=_require_bool(
            data, "aurel_must_explain_action_basis", label
        ),
        aurel_must_surface_reversibility=_require_bool(
            data, "aurel_must_surface_reversibility", label
        ),
        aurel_must_surface_known_limitations=_require_bool(
            data, "aurel_must_surface_known_limitations", label
        ),
    )


def _parse_future_placeholders(data: dict[str, Any]) -> OperatorFuturePlaceholders:
    label = "operator_contract.future_placeholders"
    placeholders: dict[str, str | None] = {}
    for key in (
        "autonomy_session_ref",
        "delegation_grant_ref",
        "approval_workbench_ref",
        "non_repudiation_attestation_ref",
    ):
        if key not in data:
            raise OperatorContractError(f"missing required field: {label}.{key}")
        value = data[key]
        if value is not None and not isinstance(value, str):
            raise OperatorContractError(f"{label}.{key} must be null or a string")
        placeholders[key] = value
    return OperatorFuturePlaceholders(**placeholders)


def _parse_boundaries(data: dict[str, Any]) -> OperatorContractBoundaries:
    label = "operator_contract.boundaries"
    return OperatorContractBoundaries(
        cannot_override_identity_kernel=_require_bool(
            data, "cannot_override_identity_kernel", label
        ),
        cannot_override_persona_manifest_boundaries=_require_bool(
            data, "cannot_override_persona_manifest_boundaries", label
        ),
        cannot_grant_tool_rights=_require_bool(data, "cannot_grant_tool_rights", label),
        cannot_change_autonomy=_require_bool(data, "cannot_change_autonomy", label),
        cannot_disable_constitutional_floor=_require_bool(
            data, "cannot_disable_constitutional_floor", label
        ),
        cannot_canonize_untrusted_input=_require_bool(
            data, "cannot_canonize_untrusted_input", label
        ),
        cannot_expand_delegation_scope=_require_bool(
            data, "cannot_expand_delegation_scope", label
        ),
    )


def _parse_invariant(raw: dict[str, Any]) -> OperatorContractInvariant:
    inv_id = raw.get("id")
    if not isinstance(inv_id, str) or not inv_id.strip():
        raise OperatorContractError("invariant id must be a non-empty string")
    key = raw.get("key")
    if not isinstance(key, str) or not key.strip():
        raise OperatorContractError(f"invariant {inv_id}: key must be a non-empty string")
    statement = raw.get("statement")
    if not isinstance(statement, str) or not statement.strip():
        raise OperatorContractError(f"invariant {inv_id}: statement must be a non-empty string")
    if "expected_value" not in raw or not isinstance(raw["expected_value"], bool):
        raise OperatorContractError(f"invariant {inv_id}: expected_value must be a boolean")
    if "mutable" not in raw or not isinstance(raw["mutable"], bool):
        raise OperatorContractError(f"invariant {inv_id}: mutable must be a boolean")
    severity = raw.get("severity")
    if severity not in {"info", "warning", "critical"}:
        raise OperatorContractError(f"invariant {inv_id}: invalid severity")
    violation_action = raw.get("violation_action")
    if violation_action not in {"warn", "block", "fail_boot"}:
        raise OperatorContractError(f"invariant {inv_id}: invalid violation_action")
    rationale = raw.get("rationale")
    if not isinstance(rationale, str) or not rationale.strip():
        raise OperatorContractError(f"invariant {inv_id}: rationale must be a non-empty string")
    return OperatorContractInvariant(
        id=inv_id,
        key=key,
        statement=statement,
        expected_value=raw["expected_value"],
        mutable=raw["mutable"],
        severity=severity,
        violation_action=violation_action,
        rationale=rationale,
    )


def parse_operator_contract_document(data: dict[str, Any]) -> AurelOperatorContract:
    """Parse a loaded YAML document into a typed operator contract."""
    root = _require_mapping(data.get("operator_contract"), "operator_contract")
    for field in ("schema_version", "name", "contract_class", "applies_to_agent"):
        _require_str(root, field, "operator_contract")
    for section in (
        "parties",
        "authority",
        "relationship_behavior",
        "non_manipulation",
        "execution_authority",
        "accountability",
        "future_placeholders",
        "boundaries",
        "invariants",
    ):
        if section not in root:
            raise OperatorContractError(f"missing required section: operator_contract.{section}")

    raw_invariants = root["invariants"]
    if not isinstance(raw_invariants, list) or not raw_invariants:
        raise OperatorContractError("operator_contract.invariants must be a non-empty list")
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
        raise OperatorContractError("operator_contract.notes must be a mapping when present")

    return AurelOperatorContract(
        schema_version=root["schema_version"],
        name=root["name"],
        contract_class=root["contract_class"],
        applies_to_agent=root["applies_to_agent"],
        parties=_parse_parties(_require_mapping(root["parties"], "parties")),
        authority=_parse_authority(_require_mapping(root["authority"], "authority")),
        relationship_behavior=_parse_relationship_behavior(
            _require_mapping(root["relationship_behavior"], "relationship_behavior")
        ),
        non_manipulation=_parse_non_manipulation(
            _require_mapping(root["non_manipulation"], "non_manipulation")
        ),
        execution_authority=_parse_execution_authority(
            _require_mapping(root["execution_authority"], "execution_authority")
        ),
        accountability=_parse_accountability(
            _require_mapping(root["accountability"], "accountability")
        ),
        future_placeholders=_parse_future_placeholders(
            _require_mapping(root["future_placeholders"], "future_placeholders")
        ),
        boundaries=_parse_boundaries(_require_mapping(root["boundaries"], "boundaries")),
        invariants=invariants,
        notes=notes,
    )


def load_operator_contract(path: str | Path | None = None) -> AurelOperatorContract:
    """Load and parse operator contract from a local YAML file."""
    config_path = Path(path) if path is not None else default_operator_contract_path()
    if not config_path.is_file():
        raise OperatorContractError(f"operator contract file not found: {config_path}")
    try:
        document = load_yaml(config_path.read_text(encoding="utf-8"))
    except YamlParseError as exc:
        raise OperatorContractError(f"YAML parse error: {exc}") from exc
    if not document:
        raise OperatorContractError("operator contract document is empty")
    return parse_operator_contract_document(document)
