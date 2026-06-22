"""Aurel Identity Prompt Context Compiler policy (P1.4.5)."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, Mapping

from ..yaml_minimal import YamlParseError, load_yaml

IPC_VALIDATOR_VERSION = "1.0.0"

Severity = Literal["info", "warning", "critical"]
ViolationAction = Literal["warn", "block", "fail_compile"]
HashAlgorithm = Literal["sha256"]
ValidationStatus = Literal["valid", "invalid"]


class IdentityPromptCompilerError(ValueError):
    """Raised when compiler policy config cannot be loaded or parsed."""


@dataclass(frozen=True)
class IdentityPromptCompilerSourceRequirements:
    identity_kernel_required: bool
    persona_manifest_required: bool
    operator_contract_required: bool
    communication_mode_registry_required: bool
    selected_mode_required: bool


@dataclass(frozen=True)
class IdentityPromptCompilerSafety:
    raw_yaml_in_prompt_forbidden: bool
    raw_config_dump_forbidden: bool
    include_source_hashes: bool
    include_compiler_version: bool
    include_authority_boundaries: bool
    include_capability_honesty: bool
    include_no_self_escalation: bool
    include_operator_final_authority: bool
    include_mode_boundaries: bool
    include_no_tool_authority_statement: bool
    include_no_action_authority_statement: bool
    include_no_memory_write_statement: bool
    include_no_policy_bypass_statement: bool
    include_no_canonization_statement: bool


@dataclass(frozen=True)
class IdentityPromptCompilerDominance:
    identity_kernel_overrides_all: bool
    operator_contract_overrides_persona_and_mode: bool
    persona_boundaries_override_mode_style: bool
    mode_never_overrides_authority: bool
    lower_layer_contradiction_fails: bool


@dataclass(frozen=True)
class IdentityPromptCompilerSections:
    include_agent_identity_section: bool
    include_operator_relationship_section: bool
    include_persona_expression_section: bool
    include_active_mode_section: bool
    include_authority_boundaries_section: bool
    include_capability_honesty_section: bool
    include_non_goals_section: bool
    include_source_integrity_section: bool


@dataclass(frozen=True)
class IdentityPromptCompilerInvariant:
    id: str
    key: str
    statement: str
    expected_value: bool
    mutable: bool
    severity: Severity
    violation_action: ViolationAction
    rationale: str


@dataclass(frozen=True)
class IdentityPromptCompilerPolicyHash:
    algorithm: HashAlgorithm
    value: str


@dataclass(frozen=True)
class IdentityPromptCompilerPolicyValidationResult:
    valid: bool
    errors: tuple[str, ...]
    warnings: tuple[str, ...]
    critical_failures: tuple[str, ...]


@dataclass(frozen=True)
class IdentityPromptCompilerPolicy:
    schema_version: str
    name: str
    compiler_class: str
    applies_to_agent: str
    compiler_version: str
    source_requirements: IdentityPromptCompilerSourceRequirements
    safety: IdentityPromptCompilerSafety
    dominance: IdentityPromptCompilerDominance
    prompt_sections: IdentityPromptCompilerSections
    invariants: tuple[IdentityPromptCompilerInvariant, ...]
    notes: Mapping[str, Any] | None = None


def default_identity_prompt_compiler_path() -> Path:
    """Return canonical repo-root path to identity_prompt_compiler.yaml."""
    return Path(__file__).resolve().parents[3] / "config" / "aurel" / "identity_prompt_compiler.yaml"


def _require_mapping(data: object, label: str) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise IdentityPromptCompilerError(f"{label} must be a mapping")
    return data


def _require_bool(data: dict[str, Any], key: str, label: str) -> bool:
    if key not in data:
        raise IdentityPromptCompilerError(f"missing required field: {label}.{key}")
    value = data[key]
    if not isinstance(value, bool):
        raise IdentityPromptCompilerError(f"{label}.{key} must be a boolean")
    return value


def _require_str(data: dict[str, Any], key: str, label: str) -> str:
    if key not in data or not isinstance(data[key], str) or not data[key].strip():
        raise IdentityPromptCompilerError(f"missing or empty {label}.{key}")
    return data[key]


def _parse_source_requirements(data: dict[str, Any]) -> IdentityPromptCompilerSourceRequirements:
    label = "identity_prompt_compiler.source_requirements"
    return IdentityPromptCompilerSourceRequirements(
        identity_kernel_required=_require_bool(data, "identity_kernel_required", label),
        persona_manifest_required=_require_bool(data, "persona_manifest_required", label),
        operator_contract_required=_require_bool(data, "operator_contract_required", label),
        communication_mode_registry_required=_require_bool(
            data, "communication_mode_registry_required", label
        ),
        selected_mode_required=_require_bool(data, "selected_mode_required", label),
    )


def _parse_safety(data: dict[str, Any]) -> IdentityPromptCompilerSafety:
    label = "identity_prompt_compiler.safety"
    return IdentityPromptCompilerSafety(
        raw_yaml_in_prompt_forbidden=_require_bool(data, "raw_yaml_in_prompt_forbidden", label),
        raw_config_dump_forbidden=_require_bool(data, "raw_config_dump_forbidden", label),
        include_source_hashes=_require_bool(data, "include_source_hashes", label),
        include_compiler_version=_require_bool(data, "include_compiler_version", label),
        include_authority_boundaries=_require_bool(data, "include_authority_boundaries", label),
        include_capability_honesty=_require_bool(data, "include_capability_honesty", label),
        include_no_self_escalation=_require_bool(data, "include_no_self_escalation", label),
        include_operator_final_authority=_require_bool(
            data, "include_operator_final_authority", label
        ),
        include_mode_boundaries=_require_bool(data, "include_mode_boundaries", label),
        include_no_tool_authority_statement=_require_bool(
            data, "include_no_tool_authority_statement", label
        ),
        include_no_action_authority_statement=_require_bool(
            data, "include_no_action_authority_statement", label
        ),
        include_no_memory_write_statement=_require_bool(
            data, "include_no_memory_write_statement", label
        ),
        include_no_policy_bypass_statement=_require_bool(
            data, "include_no_policy_bypass_statement", label
        ),
        include_no_canonization_statement=_require_bool(
            data, "include_no_canonization_statement", label
        ),
    )


def _parse_dominance(data: dict[str, Any]) -> IdentityPromptCompilerDominance:
    label = "identity_prompt_compiler.dominance"
    return IdentityPromptCompilerDominance(
        identity_kernel_overrides_all=_require_bool(data, "identity_kernel_overrides_all", label),
        operator_contract_overrides_persona_and_mode=_require_bool(
            data, "operator_contract_overrides_persona_and_mode", label
        ),
        persona_boundaries_override_mode_style=_require_bool(
            data, "persona_boundaries_override_mode_style", label
        ),
        mode_never_overrides_authority=_require_bool(data, "mode_never_overrides_authority", label),
        lower_layer_contradiction_fails=_require_bool(
            data, "lower_layer_contradiction_fails", label
        ),
    )


def _parse_prompt_sections(data: dict[str, Any]) -> IdentityPromptCompilerSections:
    label = "identity_prompt_compiler.prompt_sections"
    return IdentityPromptCompilerSections(
        include_agent_identity_section=_require_bool(
            data, "include_agent_identity_section", label
        ),
        include_operator_relationship_section=_require_bool(
            data, "include_operator_relationship_section", label
        ),
        include_persona_expression_section=_require_bool(
            data, "include_persona_expression_section", label
        ),
        include_active_mode_section=_require_bool(data, "include_active_mode_section", label),
        include_authority_boundaries_section=_require_bool(
            data, "include_authority_boundaries_section", label
        ),
        include_capability_honesty_section=_require_bool(
            data, "include_capability_honesty_section", label
        ),
        include_non_goals_section=_require_bool(data, "include_non_goals_section", label),
        include_source_integrity_section=_require_bool(
            data, "include_source_integrity_section", label
        ),
    )


def _parse_invariant(data: dict[str, Any]) -> IdentityPromptCompilerInvariant:
    inv_id = _require_str(data, "id", "invariant")
    key = _require_str(data, "key", f"invariant[{inv_id}]")
    statement = _require_str(data, "statement", f"invariant[{inv_id}]")
    rationale = _require_str(data, "rationale", f"invariant[{inv_id}]")
    severity = _require_str(data, "severity", f"invariant[{inv_id}]")
    violation_action = _require_str(data, "violation_action", f"invariant[{inv_id}]")
    if "expected_value" not in data or not isinstance(data["expected_value"], bool):
        raise IdentityPromptCompilerError(f"invariant[{inv_id}].expected_value must be a boolean")
    if "mutable" not in data or not isinstance(data["mutable"], bool):
        raise IdentityPromptCompilerError(f"invariant[{inv_id}].mutable must be a boolean")
    return IdentityPromptCompilerInvariant(
        id=inv_id,
        key=key,
        statement=statement,
        expected_value=data["expected_value"],
        mutable=data["mutable"],
        severity=severity,
        violation_action=violation_action,
        rationale=rationale,
    )


def parse_identity_prompt_compiler_document(doc: Mapping[str, Any]) -> IdentityPromptCompilerPolicy:
    """Parse a loaded YAML document into IdentityPromptCompilerPolicy."""
    root = _require_mapping(doc.get("identity_prompt_compiler"), "identity_prompt_compiler")
    label = "identity_prompt_compiler"
    invariants_raw = root.get("invariants")
    if not isinstance(invariants_raw, list) or not invariants_raw:
        raise IdentityPromptCompilerError("identity_prompt_compiler.invariants must be non-empty")
    invariants = tuple(_parse_invariant(_require_mapping(item, "invariant")) for item in invariants_raw)
    notes_raw = root.get("notes")
    notes: Mapping[str, Any] | None
    if notes_raw is None:
        notes = None
    elif isinstance(notes_raw, dict):
        notes = dict(notes_raw)
    else:
        raise IdentityPromptCompilerError("identity_prompt_compiler.notes must be a mapping")
    return IdentityPromptCompilerPolicy(
        schema_version=_require_str(root, "schema_version", label),
        name=_require_str(root, "name", label),
        compiler_class=_require_str(root, "compiler_class", label),
        applies_to_agent=_require_str(root, "applies_to_agent", label),
        compiler_version=_require_str(root, "compiler_version", label),
        source_requirements=_parse_source_requirements(
            _require_mapping(root.get("source_requirements"), f"{label}.source_requirements")
        ),
        safety=_parse_safety(_require_mapping(root.get("safety"), f"{label}.safety")),
        dominance=_parse_dominance(_require_mapping(root.get("dominance"), f"{label}.dominance")),
        prompt_sections=_parse_prompt_sections(
            _require_mapping(root.get("prompt_sections"), f"{label}.prompt_sections")
        ),
        invariants=invariants,
        notes=notes,
    )


def load_identity_prompt_compiler_policy(
    path: str | Path | None = None,
) -> IdentityPromptCompilerPolicy:
    """Load compiler policy from YAML file."""
    target = Path(path) if path is not None else default_identity_prompt_compiler_path()
    try:
        doc = load_yaml(target.read_text(encoding="utf-8"))
    except (OSError, YamlParseError) as exc:
        raise IdentityPromptCompilerError(f"failed to load compiler policy from {target}: {exc}") from exc
    return parse_identity_prompt_compiler_document(doc)
