"""Aurel Self-Model policy (P1.4.6)."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, Mapping

from ..yaml_minimal import YamlParseError, load_yaml

SELF_MODEL_VALIDATOR_VERSION = "1.0.0"

Severity = Literal["info", "warning", "critical"]
ViolationAction = Literal["warn", "block", "fail_build"]
HashAlgorithm = Literal["sha256"]
ValidationStatus = Literal["valid", "invalid"]


class SelfModelError(ValueError):
    """Raised when self-model policy or build cannot proceed."""


@dataclass(frozen=True)
class SelfModelSourceRequirements:
    identity_kernel_required: bool
    persona_manifest_required: bool
    operator_contract_required: bool
    communication_mode_registry_required: bool
    identity_prompt_compiler_policy_required: bool


@dataclass(frozen=True)
class SelfModelHonestyRules:
    distinguish_planned_from_implemented: bool
    distinguish_implemented_from_verified: bool
    distinguish_unavailable_from_unverified: bool
    never_claim_roadmap_as_runtime: bool
    never_claim_verification_without_evidence: bool
    mark_unknown_as_unknown: bool
    expose_known_limitations: bool


@dataclass(frozen=True)
class SelfModelCapabilityStatuses:
    allowed_statuses: tuple[str, ...]


@dataclass(frozen=True)
class SelfModelBoundaries:
    self_model_can_grant_authority: bool
    self_model_can_change_identity: bool
    self_model_can_change_autonomy: bool
    self_model_can_verify_capability_by_itself: bool
    self_model_can_write_memory: bool
    self_model_can_modify_policy: bool


@dataclass(frozen=True)
class SelfModelRequiredSections:
    include_identity_summary: bool
    include_source_hashes: bool
    include_authority_boundaries: bool
    include_capability_inventory: bool
    include_known_limitations: bool
    include_non_goals: bool
    include_evidence_posture: bool
    include_next_unimplemented_modules: bool


@dataclass(frozen=True)
class SelfModelInvariant:
    id: str
    key: str
    statement: str
    expected_value: bool
    mutable: bool
    severity: Severity
    violation_action: ViolationAction
    rationale: str


@dataclass(frozen=True)
class SelfModelPolicyHash:
    algorithm: HashAlgorithm
    value: str


@dataclass(frozen=True)
class SelfModelPolicyValidationResult:
    valid: bool
    errors: tuple[str, ...]
    warnings: tuple[str, ...]
    critical_failures: tuple[str, ...]


@dataclass(frozen=True)
class SelfModelPolicy:
    schema_version: str
    name: str
    policy_class: str
    applies_to_agent: str
    policy_version: str
    source_requirements: SelfModelSourceRequirements
    honesty: SelfModelHonestyRules
    capability_statuses: SelfModelCapabilityStatuses
    boundaries: SelfModelBoundaries
    required_sections: SelfModelRequiredSections
    invariants: tuple[SelfModelInvariant, ...]
    notes: Mapping[str, Any] | None = None


def default_self_model_policy_path() -> Path:
    """Return canonical repo-root path to self_model_policy.yaml."""
    return Path(__file__).resolve().parents[3] / "config" / "aurel" / "self_model_policy.yaml"


def _require_mapping(data: object, label: str) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise SelfModelError(f"{label} must be a mapping")
    return data


def _require_bool(data: dict[str, Any], key: str, label: str) -> bool:
    if key not in data:
        raise SelfModelError(f"missing required field: {label}.{key}")
    value = data[key]
    if not isinstance(value, bool):
        raise SelfModelError(f"{label}.{key} must be a boolean")
    return value


def _require_str(data: dict[str, Any], key: str, label: str) -> str:
    if key not in data or not isinstance(data[key], str) or not data[key].strip():
        raise SelfModelError(f"missing or empty {label}.{key}")
    return data[key]


def _parse_source_requirements(data: dict[str, Any]) -> SelfModelSourceRequirements:
    label = "self_model_policy.source_requirements"
    return SelfModelSourceRequirements(
        identity_kernel_required=_require_bool(data, "identity_kernel_required", label),
        persona_manifest_required=_require_bool(data, "persona_manifest_required", label),
        operator_contract_required=_require_bool(data, "operator_contract_required", label),
        communication_mode_registry_required=_require_bool(
            data, "communication_mode_registry_required", label
        ),
        identity_prompt_compiler_policy_required=_require_bool(
            data, "identity_prompt_compiler_policy_required", label
        ),
    )


def _parse_honesty(data: dict[str, Any]) -> SelfModelHonestyRules:
    label = "self_model_policy.honesty"
    return SelfModelHonestyRules(
        distinguish_planned_from_implemented=_require_bool(
            data, "distinguish_planned_from_implemented", label
        ),
        distinguish_implemented_from_verified=_require_bool(
            data, "distinguish_implemented_from_verified", label
        ),
        distinguish_unavailable_from_unverified=_require_bool(
            data, "distinguish_unavailable_from_unverified", label
        ),
        never_claim_roadmap_as_runtime=_require_bool(
            data, "never_claim_roadmap_as_runtime", label
        ),
        never_claim_verification_without_evidence=_require_bool(
            data, "never_claim_verification_without_evidence", label
        ),
        mark_unknown_as_unknown=_require_bool(data, "mark_unknown_as_unknown", label),
        expose_known_limitations=_require_bool(data, "expose_known_limitations", label),
    )


def _parse_capability_statuses(data: dict[str, Any]) -> SelfModelCapabilityStatuses:
    label = "self_model_policy.capability_statuses"
    raw = data.get("allowed_statuses")
    if not isinstance(raw, list) or not raw:
        raise SelfModelError(f"{label}.allowed_statuses must be a non-empty list")
    statuses: list[str] = []
    for item in raw:
        if not isinstance(item, str) or not item.strip():
            raise SelfModelError(f"{label}.allowed_statuses entries must be non-empty strings")
        statuses.append(item.strip())
    return SelfModelCapabilityStatuses(allowed_statuses=tuple(statuses))


def _parse_boundaries(data: dict[str, Any]) -> SelfModelBoundaries:
    label = "self_model_policy.boundaries"
    return SelfModelBoundaries(
        self_model_can_grant_authority=_require_bool(data, "self_model_can_grant_authority", label),
        self_model_can_change_identity=_require_bool(data, "self_model_can_change_identity", label),
        self_model_can_change_autonomy=_require_bool(data, "self_model_can_change_autonomy", label),
        self_model_can_verify_capability_by_itself=_require_bool(
            data, "self_model_can_verify_capability_by_itself", label
        ),
        self_model_can_write_memory=_require_bool(data, "self_model_can_write_memory", label),
        self_model_can_modify_policy=_require_bool(data, "self_model_can_modify_policy", label),
    )


def _parse_required_sections(data: dict[str, Any]) -> SelfModelRequiredSections:
    label = "self_model_policy.required_sections"
    return SelfModelRequiredSections(
        include_identity_summary=_require_bool(data, "include_identity_summary", label),
        include_source_hashes=_require_bool(data, "include_source_hashes", label),
        include_authority_boundaries=_require_bool(data, "include_authority_boundaries", label),
        include_capability_inventory=_require_bool(data, "include_capability_inventory", label),
        include_known_limitations=_require_bool(data, "include_known_limitations", label),
        include_non_goals=_require_bool(data, "include_non_goals", label),
        include_evidence_posture=_require_bool(data, "include_evidence_posture", label),
        include_next_unimplemented_modules=_require_bool(
            data, "include_next_unimplemented_modules", label
        ),
    )


def _parse_invariant(data: dict[str, Any]) -> SelfModelInvariant:
    inv_id = _require_str(data, "id", "invariant")
    key = _require_str(data, "key", f"invariant[{inv_id}]")
    statement = _require_str(data, "statement", f"invariant[{inv_id}]")
    rationale = _require_str(data, "rationale", f"invariant[{inv_id}]")
    severity = _require_str(data, "severity", f"invariant[{inv_id}]")
    violation_action = _require_str(data, "violation_action", f"invariant[{inv_id}]")
    if "expected_value" not in data or not isinstance(data["expected_value"], bool):
        raise SelfModelError(f"invariant[{inv_id}].expected_value must be a boolean")
    if "mutable" not in data or not isinstance(data["mutable"], bool):
        raise SelfModelError(f"invariant[{inv_id}].mutable must be a boolean")
    return SelfModelInvariant(
        id=inv_id,
        key=key,
        statement=statement,
        expected_value=data["expected_value"],
        mutable=data["mutable"],
        severity=severity,
        violation_action=violation_action,
        rationale=rationale,
    )


def parse_self_model_policy_document(doc: Mapping[str, Any]) -> SelfModelPolicy:
    """Parse a loaded YAML document into SelfModelPolicy."""
    root = _require_mapping(doc.get("self_model_policy"), "self_model_policy")
    label = "self_model_policy"
    invariants_raw = root.get("invariants")
    if not isinstance(invariants_raw, list) or not invariants_raw:
        raise SelfModelError("self_model_policy.invariants must be non-empty")
    invariants = tuple(_parse_invariant(_require_mapping(item, "invariant")) for item in invariants_raw)
    notes_raw = root.get("notes")
    notes: Mapping[str, Any] | None
    if notes_raw is None:
        notes = None
    elif isinstance(notes_raw, dict):
        notes = dict(notes_raw)
    else:
        raise SelfModelError("self_model_policy.notes must be a mapping")
    return SelfModelPolicy(
        schema_version=_require_str(root, "schema_version", label),
        name=_require_str(root, "name", label),
        policy_class=_require_str(root, "policy_class", label),
        applies_to_agent=_require_str(root, "applies_to_agent", label),
        policy_version=_require_str(root, "policy_version", label),
        source_requirements=_parse_source_requirements(
            _require_mapping(root.get("source_requirements"), f"{label}.source_requirements")
        ),
        honesty=_parse_honesty(_require_mapping(root.get("honesty"), f"{label}.honesty")),
        capability_statuses=_parse_capability_statuses(
            _require_mapping(root.get("capability_statuses"), f"{label}.capability_statuses")
        ),
        boundaries=_parse_boundaries(_require_mapping(root.get("boundaries"), f"{label}.boundaries")),
        required_sections=_parse_required_sections(
            _require_mapping(root.get("required_sections"), f"{label}.required_sections")
        ),
        invariants=invariants,
        notes=notes,
    )


def load_self_model_policy(path: str | Path | None = None) -> SelfModelPolicy:
    """Load self-model policy from YAML file."""
    target = Path(path) if path is not None else default_self_model_policy_path()
    try:
        doc = load_yaml(target.read_text(encoding="utf-8"))
    except (OSError, YamlParseError) as exc:
        raise SelfModelError(f"failed to load self-model policy from {target}: {exc}") from exc
    return parse_self_model_policy_document(doc)
