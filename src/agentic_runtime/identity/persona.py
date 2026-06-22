"""Aurel Persona Manifest — machine-readable expression contract (P1.4.2).

Persona is not authority. Persona is not policy. Persona is not autonomy.
Persona is not the Operator Contract. Persona is not the Identity Kernel.
This module defines expression and interaction behavior only.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, Mapping

from ..yaml_minimal import YamlParseError, load_yaml

PERSONA_VALIDATOR_VERSION = "1.0.0"

Severity = Literal["info", "warning", "critical"]
ViolationAction = Literal["warn", "block", "fail_boot"]
HashAlgorithm = Literal["sha256"]
ValidationStatus = Literal["valid", "invalid"]


class PersonaManifestError(ValueError):
    """Raised when persona manifest config cannot be loaded or parsed."""


@dataclass(frozen=True)
class PersonaVoice:
    default_style: str
    default_tone: str
    verbosity: str
    language_behavior: str
    markdown_preferred: bool
    symbolic_layer_allowed: bool
    poetic_layer_allowed: bool
    excessive_flattery_forbidden: bool
    false_certainty_forbidden: bool


@dataclass(frozen=True)
class PersonaPosture:
    mentor: bool
    architect: bool
    challenger: bool
    mirror: bool
    execution_assistant: bool
    passive_servility: bool
    manipulative_persuasion: bool


@dataclass(frozen=True)
class PersonaHonesty:
    explain_uncertainty: bool
    admit_missing_context: bool
    distinguish_fact_from_inference: bool
    distinguish_planned_from_implemented: bool
    distinguish_implemented_from_verified: bool
    never_claim_unverified_capability: bool
    cite_sources_when_required: bool


@dataclass(frozen=True)
class PersonaRiskCommunication:
    surface_material_risk: bool
    challenge_unsafe_instructions: bool
    warn_on_irreversible_actions: bool
    warn_on_high_uncertainty: bool
    warn_on_unverified_capability_claims: bool


@dataclass(frozen=True)
class PersonaChallengeBehavior:
    challenge_weak_assumptions: bool
    challenge_architectural_collapse: bool
    challenge_governance_theater: bool
    challenge_fake_capability: bool
    challenge_overbuilding: bool
    challenge_when_user_requests_speed_over_safety: bool


@dataclass(frozen=True)
class PersonaOperatorInteraction:
    respect_operator_final_authority: bool
    may_disagree_with_operator: bool
    must_explain_disagreement: bool
    must_not_replace_operator_judgment: bool
    must_not_hide_tradeoffs: bool
    must_not_pressure_operator: bool


@dataclass(frozen=True)
class PersonaBoundaries:
    cannot_override_identity_kernel: bool
    cannot_modify_operator_contract: bool
    cannot_grant_tool_rights: bool
    cannot_increase_autonomy: bool
    cannot_disable_constitutional_floor: bool
    cannot_canonize_untrusted_input: bool
    cannot_convert_style_into_authority: bool


@dataclass(frozen=True)
class PersonaPromptSafety:
    raw_manifest_in_prompt_forbidden: bool
    compile_to_safe_summary_required: bool
    include_authority_boundaries_in_summary: bool
    include_capability_honesty_in_summary: bool


@dataclass(frozen=True)
class PersonaInvariant:
    id: str
    key: str
    statement: str
    expected_value: bool
    mutable: bool
    severity: Severity
    violation_action: ViolationAction
    rationale: str


@dataclass(frozen=True)
class PersonaManifestHash:
    algorithm: HashAlgorithm
    value: str


@dataclass(frozen=True)
class PersonaManifestValidationResult:
    valid: bool
    errors: tuple[str, ...]
    warnings: tuple[str, ...]
    critical_failures: tuple[str, ...]


@dataclass(frozen=True)
class PersonaManifestAttestation:
    schema_version: str
    persona_hash: str
    hash_algorithm: str
    config_path: str
    validation_status: ValidationStatus
    validator_version: str
    critical_failures: tuple[str, ...]


@dataclass(frozen=True)
class PersonaSafeSummary:
    manifest_name: str
    applies_to_agent: str
    voice_summary: str
    posture_summary: str
    honesty_rules: tuple[str, ...]
    risk_communication_rules: tuple[str, ...]
    challenge_rules: tuple[str, ...]
    authority_boundaries: tuple[str, ...]
    capability_honesty_rules: tuple[str, ...]


@dataclass(frozen=True)
class AurelPersonaManifest:
    schema_version: str
    name: str
    applies_to_agent: str
    manifest_class: str
    authority_level: str
    can_grant_permissions: bool
    can_override_identity_kernel: bool
    can_override_policy: bool
    can_change_autonomy: bool
    voice: PersonaVoice
    posture: PersonaPosture
    honesty: PersonaHonesty
    risk_communication: PersonaRiskCommunication
    challenge_behavior: PersonaChallengeBehavior
    operator_interaction: PersonaOperatorInteraction
    boundaries: PersonaBoundaries
    prompt_safety: PersonaPromptSafety
    invariants: tuple[PersonaInvariant, ...]
    notes: Mapping[str, Any] | None = None


def default_persona_manifest_path() -> Path:
    """Return canonical repo-root path to persona_manifest.yaml."""
    return Path(__file__).resolve().parents[3] / "config" / "aurel" / "persona_manifest.yaml"


def _require_mapping(data: object, label: str) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise PersonaManifestError(f"{label} must be a mapping")
    return data


def _require_bool(data: dict[str, Any], key: str, label: str) -> bool:
    if key not in data:
        raise PersonaManifestError(f"missing required field: {label}.{key}")
    value = data[key]
    if not isinstance(value, bool):
        raise PersonaManifestError(f"{label}.{key} must be a boolean")
    return value


def _require_str(data: dict[str, Any], key: str, label: str) -> str:
    if key not in data or not isinstance(data[key], str) or not data[key].strip():
        raise PersonaManifestError(f"missing or empty {label}.{key}")
    return data[key]


def _parse_voice(data: dict[str, Any]) -> PersonaVoice:
    label = "persona_manifest.voice"
    return PersonaVoice(
        default_style=_require_str(data, "default_style", label),
        default_tone=_require_str(data, "default_tone", label),
        verbosity=_require_str(data, "verbosity", label),
        language_behavior=_require_str(data, "language_behavior", label),
        markdown_preferred=_require_bool(data, "markdown_preferred", label),
        symbolic_layer_allowed=_require_bool(data, "symbolic_layer_allowed", label),
        poetic_layer_allowed=_require_bool(data, "poetic_layer_allowed", label),
        excessive_flattery_forbidden=_require_bool(data, "excessive_flattery_forbidden", label),
        false_certainty_forbidden=_require_bool(data, "false_certainty_forbidden", label),
    )


def _parse_posture(data: dict[str, Any]) -> PersonaPosture:
    label = "persona_manifest.posture"
    return PersonaPosture(
        mentor=_require_bool(data, "mentor", label),
        architect=_require_bool(data, "architect", label),
        challenger=_require_bool(data, "challenger", label),
        mirror=_require_bool(data, "mirror", label),
        execution_assistant=_require_bool(data, "execution_assistant", label),
        passive_servility=_require_bool(data, "passive_servility", label),
        manipulative_persuasion=_require_bool(data, "manipulative_persuasion", label),
    )


def _parse_honesty(data: dict[str, Any]) -> PersonaHonesty:
    label = "persona_manifest.honesty"
    return PersonaHonesty(
        explain_uncertainty=_require_bool(data, "explain_uncertainty", label),
        admit_missing_context=_require_bool(data, "admit_missing_context", label),
        distinguish_fact_from_inference=_require_bool(
            data, "distinguish_fact_from_inference", label
        ),
        distinguish_planned_from_implemented=_require_bool(
            data, "distinguish_planned_from_implemented", label
        ),
        distinguish_implemented_from_verified=_require_bool(
            data, "distinguish_implemented_from_verified", label
        ),
        never_claim_unverified_capability=_require_bool(
            data, "never_claim_unverified_capability", label
        ),
        cite_sources_when_required=_require_bool(data, "cite_sources_when_required", label),
    )


def _parse_risk_communication(data: dict[str, Any]) -> PersonaRiskCommunication:
    label = "persona_manifest.risk_communication"
    return PersonaRiskCommunication(
        surface_material_risk=_require_bool(data, "surface_material_risk", label),
        challenge_unsafe_instructions=_require_bool(data, "challenge_unsafe_instructions", label),
        warn_on_irreversible_actions=_require_bool(data, "warn_on_irreversible_actions", label),
        warn_on_high_uncertainty=_require_bool(data, "warn_on_high_uncertainty", label),
        warn_on_unverified_capability_claims=_require_bool(
            data, "warn_on_unverified_capability_claims", label
        ),
    )


def _parse_challenge_behavior(data: dict[str, Any]) -> PersonaChallengeBehavior:
    label = "persona_manifest.challenge_behavior"
    return PersonaChallengeBehavior(
        challenge_weak_assumptions=_require_bool(data, "challenge_weak_assumptions", label),
        challenge_architectural_collapse=_require_bool(
            data, "challenge_architectural_collapse", label
        ),
        challenge_governance_theater=_require_bool(data, "challenge_governance_theater", label),
        challenge_fake_capability=_require_bool(data, "challenge_fake_capability", label),
        challenge_overbuilding=_require_bool(data, "challenge_overbuilding", label),
        challenge_when_user_requests_speed_over_safety=_require_bool(
            data, "challenge_when_user_requests_speed_over_safety", label
        ),
    )


def _parse_operator_interaction(data: dict[str, Any]) -> PersonaOperatorInteraction:
    label = "persona_manifest.operator_interaction"
    return PersonaOperatorInteraction(
        respect_operator_final_authority=_require_bool(
            data, "respect_operator_final_authority", label
        ),
        may_disagree_with_operator=_require_bool(data, "may_disagree_with_operator", label),
        must_explain_disagreement=_require_bool(data, "must_explain_disagreement", label),
        must_not_replace_operator_judgment=_require_bool(
            data, "must_not_replace_operator_judgment", label
        ),
        must_not_hide_tradeoffs=_require_bool(data, "must_not_hide_tradeoffs", label),
        must_not_pressure_operator=_require_bool(data, "must_not_pressure_operator", label),
    )


def _parse_boundaries(data: dict[str, Any]) -> PersonaBoundaries:
    label = "persona_manifest.boundaries"
    return PersonaBoundaries(
        cannot_override_identity_kernel=_require_bool(
            data, "cannot_override_identity_kernel", label
        ),
        cannot_modify_operator_contract=_require_bool(
            data, "cannot_modify_operator_contract", label
        ),
        cannot_grant_tool_rights=_require_bool(data, "cannot_grant_tool_rights", label),
        cannot_increase_autonomy=_require_bool(data, "cannot_increase_autonomy", label),
        cannot_disable_constitutional_floor=_require_bool(
            data, "cannot_disable_constitutional_floor", label
        ),
        cannot_canonize_untrusted_input=_require_bool(
            data, "cannot_canonize_untrusted_input", label
        ),
        cannot_convert_style_into_authority=_require_bool(
            data, "cannot_convert_style_into_authority", label
        ),
    )


def _parse_prompt_safety(data: dict[str, Any]) -> PersonaPromptSafety:
    label = "persona_manifest.prompt_safety"
    return PersonaPromptSafety(
        raw_manifest_in_prompt_forbidden=_require_bool(
            data, "raw_manifest_in_prompt_forbidden", label
        ),
        compile_to_safe_summary_required=_require_bool(
            data, "compile_to_safe_summary_required", label
        ),
        include_authority_boundaries_in_summary=_require_bool(
            data, "include_authority_boundaries_in_summary", label
        ),
        include_capability_honesty_in_summary=_require_bool(
            data, "include_capability_honesty_in_summary", label
        ),
    )


def _parse_invariant(raw: dict[str, Any]) -> PersonaInvariant:
    inv_id = raw.get("id")
    if not isinstance(inv_id, str) or not inv_id.strip():
        raise PersonaManifestError("invariant id must be a non-empty string")
    key = raw.get("key")
    if not isinstance(key, str) or not key.strip():
        raise PersonaManifestError(f"invariant {inv_id}: key must be a non-empty string")
    statement = raw.get("statement")
    if not isinstance(statement, str) or not statement.strip():
        raise PersonaManifestError(f"invariant {inv_id}: statement must be a non-empty string")
    if "expected_value" not in raw or not isinstance(raw["expected_value"], bool):
        raise PersonaManifestError(f"invariant {inv_id}: expected_value must be a boolean")
    if "mutable" not in raw or not isinstance(raw["mutable"], bool):
        raise PersonaManifestError(f"invariant {inv_id}: mutable must be a boolean")
    severity = raw.get("severity")
    if severity not in {"info", "warning", "critical"}:
        raise PersonaManifestError(f"invariant {inv_id}: invalid severity")
    violation_action = raw.get("violation_action")
    if violation_action not in {"warn", "block", "fail_boot"}:
        raise PersonaManifestError(f"invariant {inv_id}: invalid violation_action")
    rationale = raw.get("rationale")
    if not isinstance(rationale, str) or not rationale.strip():
        raise PersonaManifestError(f"invariant {inv_id}: rationale must be a non-empty string")
    return PersonaInvariant(
        id=inv_id,
        key=key,
        statement=statement,
        expected_value=raw["expected_value"],
        mutable=raw["mutable"],
        severity=severity,
        violation_action=violation_action,
        rationale=rationale,
    )


def parse_persona_manifest_document(data: dict[str, Any]) -> AurelPersonaManifest:
    """Parse a loaded YAML document into a typed persona manifest."""
    root = _require_mapping(data.get("persona_manifest"), "persona_manifest")
    for field in ("schema_version", "name", "applies_to_agent", "manifest_class", "authority_level"):
        _require_str(root, field, "persona_manifest")
    for field in (
        "can_grant_permissions",
        "can_override_identity_kernel",
        "can_override_policy",
        "can_change_autonomy",
    ):
        _require_bool(root, field, "persona_manifest")
    for section in (
        "voice",
        "posture",
        "honesty",
        "risk_communication",
        "challenge_behavior",
        "operator_interaction",
        "boundaries",
        "prompt_safety",
        "invariants",
    ):
        if section not in root:
            raise PersonaManifestError(f"missing required section: persona_manifest.{section}")

    raw_invariants = root["invariants"]
    if not isinstance(raw_invariants, list) or not raw_invariants:
        raise PersonaManifestError("persona_manifest.invariants must be a non-empty list")
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
        raise PersonaManifestError("persona_manifest.notes must be a mapping when present")

    return AurelPersonaManifest(
        schema_version=root["schema_version"],
        name=root["name"],
        applies_to_agent=root["applies_to_agent"],
        manifest_class=root["manifest_class"],
        authority_level=root["authority_level"],
        can_grant_permissions=root["can_grant_permissions"],
        can_override_identity_kernel=root["can_override_identity_kernel"],
        can_override_policy=root["can_override_policy"],
        can_change_autonomy=root["can_change_autonomy"],
        voice=_parse_voice(_require_mapping(root["voice"], "voice")),
        posture=_parse_posture(_require_mapping(root["posture"], "posture")),
        honesty=_parse_honesty(_require_mapping(root["honesty"], "honesty")),
        risk_communication=_parse_risk_communication(
            _require_mapping(root["risk_communication"], "risk_communication")
        ),
        challenge_behavior=_parse_challenge_behavior(
            _require_mapping(root["challenge_behavior"], "challenge_behavior")
        ),
        operator_interaction=_parse_operator_interaction(
            _require_mapping(root["operator_interaction"], "operator_interaction")
        ),
        boundaries=_parse_boundaries(_require_mapping(root["boundaries"], "boundaries")),
        prompt_safety=_parse_prompt_safety(
            _require_mapping(root["prompt_safety"], "prompt_safety")
        ),
        invariants=invariants,
        notes=notes,
    )


def load_persona_manifest(path: str | Path | None = None) -> AurelPersonaManifest:
    """Load and parse persona manifest from a local YAML file."""
    config_path = Path(path) if path is not None else default_persona_manifest_path()
    if not config_path.is_file():
        raise PersonaManifestError(f"persona manifest file not found: {config_path}")
    try:
        document = load_yaml(config_path.read_text(encoding="utf-8"))
    except YamlParseError as exc:
        raise PersonaManifestError(f"YAML parse error: {exc}") from exc
    if not document:
        raise PersonaManifestError("persona manifest document is empty")
    return parse_persona_manifest_document(document)
