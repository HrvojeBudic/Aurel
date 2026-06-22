"""P1.4.12 raw source + canonical hash attestation.

Hash-based attestation binds what entered to what Aurel interpreted. It does
not prove truth, trust, safety, capability, cryptographic signature, or
tamper-proof storage.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, fields, is_dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

from ..yaml_minimal import YamlParseError, load_yaml

SOURCE_ATTESTATION_SCHEMA_VERSION = "source_attestation.v1"
SOURCE_ATTESTATION_HASH_ALGORITHM = "sha256"

SOURCE_ATTESTATION_NON_GOALS: tuple[str, ...] = (
    "hash_does_not_prove_truth",
    "hash_does_not_prove_trust",
    "hash_does_not_grant_capability",
    "not_cryptographically_signed",
    "not_tamper_proof_storage",
)


class SourceKind(str, Enum):
    IDENTITY_KERNEL = "identity_kernel"
    PERSONA_MANIFEST = "persona_manifest"
    OPERATOR_CONTRACT = "operator_contract"
    COMMUNICATION_MODES = "communication_modes"
    IDENTITY_PROMPT_COMPILER = "identity_prompt_compiler"
    SELF_MODEL_POLICY = "self_model_policy"
    AGENT_IDENTITY_CARD_CONFIG = "agent_identity_card_config"
    EXTERNAL_DOCTRINE = "external_doctrine"
    ROADMAP = "roadmap"
    REPORT = "report"
    CONFIG = "config"


class SourceValidationStatus(str, Enum):
    VALID = "VALID"
    INVALID = "INVALID"
    VALID_WITH_WARNINGS = "VALID_WITH_WARNINGS"
    REJECTED_UNKNOWN_FIELDS = "REJECTED_UNKNOWN_FIELDS"
    MISSING_SOURCE = "MISSING_SOURCE"
    SCHEMA_MISMATCH = "SCHEMA_MISMATCH"


@dataclass(frozen=True)
class SourceHashPair:
    raw_source_hash: str
    canonical_typed_hash: str
    hash_algorithm: str = SOURCE_ATTESTATION_HASH_ALGORITHM


@dataclass(frozen=True)
class SourceAttestation:
    attestation_id: str
    schema_version: str

    source_kind: SourceKind
    source_path: str | None
    source_name: str | None

    raw_source_hash: str
    canonical_typed_hash: str
    hash_algorithm: str

    validation_status: SourceValidationStatus
    validator_name: str
    validator_version: str | None

    rejected_unknown_fields: tuple[str, ...]
    warnings: tuple[str, ...]
    errors: tuple[str, ...]

    created_at: str
    evidence_refs: tuple[str, ...]


def _ensure_bytes(raw: bytes | str) -> bytes:
    if isinstance(raw, bytes):
        return raw
    if isinstance(raw, str):
        return raw.encode("utf-8")
    raise TypeError("raw source must be bytes or str")


def hash_raw_source(raw: bytes | str) -> str:
    """Hash raw unnormalized input with SHA-256."""
    return hashlib.sha256(_ensure_bytes(raw)).hexdigest()


_VOLATILE_CANONICAL_KEYS = {"created_at"}


def _canonical_payload(obj: object) -> object:
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, Path):
        return str(obj)
    if is_dataclass(obj):
        payload: dict[str, object] = {}
        for field in fields(obj):
            if field.name in _VOLATILE_CANONICAL_KEYS:
                continue
            payload[field.name] = _canonical_payload(getattr(obj, field.name))
        return payload
    if isinstance(obj, dict):
        return {
            str(key): _canonical_payload(value)
            for key, value in sorted(obj.items(), key=lambda item: str(item[0]))
            if str(key) not in _VOLATILE_CANONICAL_KEYS
        }
    if isinstance(obj, (tuple, list)):
        return [_canonical_payload(item) for item in obj]
    if isinstance(obj, set | frozenset):
        return sorted(json.dumps(_canonical_payload(item), sort_keys=True) for item in obj)
    if isinstance(obj, (str, int, float, bool)) or obj is None:
        return obj
    if hasattr(obj, "__dict__"):
        return _canonical_payload(vars(obj))
    return str(obj)


def canonicalize_source_object(obj: object) -> str:
    """Return deterministic JSON for the typed object Aurel understood."""
    return json.dumps(
        _canonical_payload(obj),
        sort_keys=True,
        separators=(",", ":"),
    )


def hash_canonical_source(obj: object) -> str:
    """Hash the deterministic typed representation with SHA-256."""
    return hash_raw_source(canonicalize_source_object(obj))


def _sha256_hex(value: str) -> bool:
    return len(value) == 64 and all(ch in "0123456789abcdef" for ch in value.lower())


def _attestation_id(
    source_kind: SourceKind,
    raw_source_hash: str,
    canonical_typed_hash: str,
) -> str:
    seed = f"{source_kind.value}:{raw_source_hash}:{canonical_typed_hash}"
    return "srcatt_" + hashlib.sha256(seed.encode("utf-8")).hexdigest()[:24]


def build_source_attestation(
    *,
    source_kind: SourceKind,
    source_path: Path | None,
    raw_source: bytes | str,
    typed_object: object,
    validation_status: SourceValidationStatus,
    validator_name: str,
    validator_version: str | None = None,
    rejected_unknown_fields: tuple[str, ...] = (),
    warnings: tuple[str, ...] = (),
    errors: tuple[str, ...] = (),
    evidence_refs: tuple[str, ...] = (),
    source_name: str | None = None,
) -> SourceAttestation:
    """Build a hash-based source attestation envelope."""
    if not isinstance(source_kind, SourceKind):
        raise ValueError(f"unknown source_kind: {source_kind!r}")
    if not isinstance(validation_status, SourceValidationStatus):
        raise ValueError(f"unknown validation_status: {validation_status!r}")
    if not validator_name.strip():
        raise ValueError("validator_name is required")
    raw_bytes = _ensure_bytes(raw_source)
    if not raw_bytes:
        raise ValueError("raw_source is required")

    raw_hash = hashlib.sha256(raw_bytes).hexdigest()
    canonical_hash = hash_canonical_source(typed_object)
    return SourceAttestation(
        attestation_id=_attestation_id(source_kind, raw_hash, canonical_hash),
        schema_version=SOURCE_ATTESTATION_SCHEMA_VERSION,
        source_kind=source_kind,
        source_path=str(source_path) if source_path is not None else None,
        source_name=source_name or (source_path.name if source_path is not None else source_kind.value),
        raw_source_hash=raw_hash,
        canonical_typed_hash=canonical_hash,
        hash_algorithm=SOURCE_ATTESTATION_HASH_ALGORITHM,
        validation_status=validation_status,
        validator_name=validator_name,
        validator_version=validator_version,
        rejected_unknown_fields=tuple(rejected_unknown_fields),
        warnings=tuple(warnings),
        errors=tuple(errors),
        created_at=datetime.now(timezone.utc).isoformat(),
        evidence_refs=tuple(evidence_refs),
    )


def source_attestation_to_dict(attestation: SourceAttestation) -> dict[str, object]:
    return {
        "attestation_id": attestation.attestation_id,
        "schema_version": attestation.schema_version,
        "source_kind": attestation.source_kind.value,
        "source_path": attestation.source_path,
        "source_name": attestation.source_name,
        "raw_source_hash": attestation.raw_source_hash,
        "canonical_typed_hash": attestation.canonical_typed_hash,
        "hash_algorithm": attestation.hash_algorithm,
        "validation_status": attestation.validation_status.value,
        "validator_name": attestation.validator_name,
        "validator_version": attestation.validator_version,
        "rejected_unknown_fields": list(attestation.rejected_unknown_fields),
        "warnings": list(attestation.warnings),
        "errors": list(attestation.errors),
        "created_at": attestation.created_at,
        "evidence_refs": list(attestation.evidence_refs),
        "non_goals": list(SOURCE_ATTESTATION_NON_GOALS),
    }


def validate_source_attestation(attestation: SourceAttestation) -> tuple[str, ...]:
    errors: list[str] = []
    if not attestation.schema_version:
        errors.append("missing schema_version")
    if attestation.schema_version != SOURCE_ATTESTATION_SCHEMA_VERSION:
        errors.append("schema_version mismatch")
    if not isinstance(attestation.source_kind, SourceKind):
        errors.append("unknown source_kind")
    if not isinstance(attestation.validation_status, SourceValidationStatus):
        errors.append("unknown validation_status")
    if not attestation.raw_source_hash:
        errors.append("missing raw_source_hash")
    elif not _sha256_hex(attestation.raw_source_hash):
        errors.append("invalid raw_source_hash")
    if not attestation.canonical_typed_hash:
        errors.append("missing canonical_typed_hash")
    elif not _sha256_hex(attestation.canonical_typed_hash):
        errors.append("invalid canonical_typed_hash")
    if attestation.hash_algorithm != SOURCE_ATTESTATION_HASH_ALGORITHM:
        errors.append("unsupported hash_algorithm")
    if not attestation.validator_name.strip():
        errors.append("empty validator_name")
    if attestation.validation_status == SourceValidationStatus.INVALID and not attestation.errors:
        errors.append("INVALID status requires errors")
    if (
        attestation.validation_status == SourceValidationStatus.REJECTED_UNKNOWN_FIELDS
        and not attestation.rejected_unknown_fields
    ):
        errors.append("REJECTED_UNKNOWN_FIELDS requires rejected_unknown_fields")
    if (
        attestation.validation_status == SourceValidationStatus.MISSING_SOURCE
        and not attestation.errors
    ):
        errors.append("MISSING_SOURCE requires errors")
    return tuple(errors)


def validate_source_attestations(
    attestations: tuple[SourceAttestation, ...],
) -> tuple[str, ...]:
    errors: list[str] = []
    seen: set[str] = set()
    for attestation in attestations:
        for error in validate_source_attestation(attestation):
            errors.append(f"{attestation.source_kind.value}: {error}")
        if attestation.attestation_id in seen:
            errors.append(f"duplicate attestation_id: {attestation.attestation_id}")
        seen.add(attestation.attestation_id)
    return tuple(errors)


_SUSPICIOUS_UNKNOWN_TOKENS = (
    "authority",
    "autonomy",
    "safety",
    "governance",
    "permission",
    "policy",
    "operator",
    "grant",
    "override",
    "bypass",
    "canon",
    "capability",
    "secret",
    "shadow",
    "trust",
    "tool",
)

_KNOWN_FIELD_NAMES = frozenset(
    {
        "accountability",
        "agent",
        "agent_class",
        "agent_id",
        "agent_identity",
        "agent_identity_card",
        "agent_name",
        "agent_type",
        "allowed_statuses",
        "applies_to_agent",
        "approval_workbench_ref",
        "aurel_can_challenge_operator",
        "aurel_can_override_operator_judgment",
        "aurel_can_refuse_forbidden_action",
        "aurel_can_replace_operator",
        "aurel_can_self_escalate",
        "aurel_final_authority",
        "aurel_must_challenge_when_risk_detected",
        "aurel_must_explain_action_basis",
        "aurel_must_surface_known_limitations",
        "aurel_must_surface_reversibility",
        "authority",
        "authority_source",
        "autonomy_session_ref",
        "blind_execution_forbidden",
        "boundaries",
        "cannot_canonize_untrusted_input",
        "cannot_change_autonomy",
        "cannot_disable_constitutional_floor",
        "cannot_expand_delegation_scope",
        "cannot_grant_tool_rights",
        "cannot_override_identity_kernel",
        "cannot_override_persona_manifest_boundaries",
        "card_can_authorize_tools",
        "card_can_change_autonomy",
        "card_can_change_identity_kernel",
        "card_can_create_delegation",
        "card_can_grant_authority",
        "card_can_override_policy",
        "card_can_replace_operator",
        "card_class",
        "card_name",
        "capability_statuses",
        "challenge_emphasis",
        "class",
        "coercive_language_forbidden",
        "communication_modes",
        "communication_modes_hash",
        "communication_refinement",
        "compiler_class",
        "compiler_version",
        "contract_class",
        "cognitive_posture",
        "dark_pattern_guidance_forbidden",
        "delegate",
        "delegated_authority_required_for_actions",
        "delegated_identity",
        "delegation_chain_ref",
        "delegation_grant_ref",
        "deployment_scope",
        "development_allowed",
        "development_forbidden",
        "disagreement_allowed",
        "disagreement_must_be_explained",
        "distinguish_implemented_from_verified",
        "distinguish_planned_from_implemented",
        "distinguish_unavailable_from_unverified",
        "dominance",
        "emotional_pressure_forbidden",
        "execution_authority",
        "external_side_effects_require_policy_allowance",
        "expected_value",
        "final_authority",
        "flattery_over_truth_forbidden",
        "future_placeholders",
        "global_boundaries",
        "hidden_goals_allowed",
        "hidden_persuasion_forbidden",
        "honesty",
        "human_principal_identity",
        "id",
        "identity_kernel",
        "identity_kernel_hash",
        "identity_prompt_compiler",
        "identity_prompt_compiler_policy_hash",
        "identity_taxonomy",
        "identity_replacement_allowed",
        "identity_version",
        "immutables",
        "include_action_authority_statement",
        "include_active_mode_section",
        "include_agent_identity_section",
        "include_authority_boundaries",
        "include_authority_boundaries_section",
        "include_capability_honesty",
        "include_capability_honesty_section",
        "include_compiler_version",
        "include_evidence_posture",
        "include_identity_summary",
        "include_known_limitations",
        "include_mode_boundaries",
        "include_next_unimplemented_modules",
        "include_no_action_authority_statement",
        "include_no_canonization_statement",
        "include_no_memory_write_statement",
        "include_no_policy_bypass_statement",
        "include_no_self_escalation",
        "include_no_tool_authority_statement",
        "include_non_goals",
        "include_non_goals_section",
        "include_operator_final_authority",
        "include_operator_relationship_section",
        "include_persona_expression_section",
        "include_policy_bypass_statement",
        "include_prompt_context",
        "include_source_hashes",
        "include_source_integrity_section",
        "invariants",
        "key",
        "ledger_identity_ref",
        "local_first",
        "lower_layer_contradiction_fails",
        "machine_scope",
        "manipulation_forbidden",
        "mark_unknown_as_unknown",
        "memory_canon_changes_require_approval_or_future_policy",
        "memory_growth",
        "model_identity",
        "modes",
        "modes_can_canonize_output",
        "modes_can_change_autonomy",
        "modes_can_disable_constitutional_floor",
        "modes_can_execute_actions",
        "modes_can_grant_permissions",
        "modes_can_override_identity_kernel",
        "modes_can_override_operator_contract",
        "modes_can_override_persona_manifest",
        "modes_can_override_policy",
        "modes_can_write_memory_directly",
        "mode_never_overrides_authority",
        "mutable",
        "name",
        "non_manipulation",
        "non_repudiation_attestation_ref",
        "non_repudiation_key_ref",
        "notes",
        "operator_contract",
        "operator_contract_hash",
        "operator_contract_overrides_persona_and_mode",
        "operator_final_authority",
        "operator_replacement",
        "operator_authorization_ref_required_for_high_risk",
        "output_bias",
        "output_passport_producer_ref",
        "parties",
        "passive_obedience_required",
        "persona_boundaries_override_mode_style",
        "persona_manifest_hash",
        "policy_bypass_self_grant_allowed",
        "policy_class",
        "policy_version",
        "primary_operator",
        "principal",
        "procedure_growth",
        "prompt_sections",
        "purpose",
        "rationale",
        "registry_class",
        "registry_name",
        "relationship_behavior",
        "required_sections",
        "reversibility",
        "risk_challenge_required",
        "risk_emphasis",
        "role",
        "runtime",
        "runtime_instance_id",
        "runtime_instance_id_strategy",
        "runtime_machine_scope",
        "runtime_started_at",
        "runtime_version",
        "schema_version",
        "secret_goal_creation",
        "selected_mode_required",
        "self_authority_expansion",
        "self_escalation_allowed",
        "self_model_can_change_autonomy",
        "self_model_can_change_identity",
        "self_model_can_grant_authority",
        "self_model_can_modify_policy",
        "self_model_can_verify_capability_by_itself",
        "self_model_can_write_memory",
        "self_model_hash",
        "self_unapproved_identity_rewrite",
        "serious_actions_must_be_traceable",
        "serious_actions_require_authority_check",
        "severity",
        "skill_growth",
        "source_bindings",
        "source_requirements",
        "specialist_growth",
        "statement",
        "tool_access_implies_authority",
        "tradeoffs_must_be_disclosed",
        "type",
        "uncertainty_must_be_disclosed",
        "unapproved_identity_rewrite",
        "untrusted_input_can_modify_identity",
        "violation_action",
        "workload_identity",
        "workload_identity_ref",
        "world_model_revision",
    }
)

_CURRENT_CONFIG_KNOWN_FIELD_NAMES = frozenset(
    {
        "authority_confusion",
        "authority_level",
        "can_change_autonomy",
        "can_grant_permissions",
        "can_override_identity_kernel",
        "can_override_policy",
        "cannot_convert_style_into_authority",
        "cannot_increase_autonomy",
        "cannot_modify_operator_contract",
        "canonizes_output",
        "challenge_behavior",
        "challenge_fake_capability",
        "challenge_governance_theater",
        "challenge_when_user_requests_speed_over_safety",
        "changes_autonomy",
        "channel",
        "debug",
        "deploy",
        "evolve",
        "focus",
        "governance_theater",
        "grants_permissions",
        "heretic",
        "identity_kernel_overrides_all",
        "identity_prompt_compiler_policy_required",
        "include_capability_inventory",
        "irreversible_actions_require_operator_approval",
        "include_authority_boundaries_in_summary",
        "include_capability_honesty_in_summary",
        "never_claim_unverified_capability",
        "may_disagree_with_operator",
        "modifies_autonomy",
        "modifies_policy",
        "modifies_tools",
        "must_not_pressure_operator",
        "must_not_replace_operator_judgment",
        "operator_contract_required",
        "operator_interaction",
        "persona_manifest",
        "prompt_safety",
        "respect_operator_final_authority",
        "safety",
        "self_model_policy",
        "shadow",
        "shadow_architecture_allowed",
        "source_requirements",
        "surface_operator_blindspots",
        "warn_on_unverified_capability_claims",
        "weak_canon",
    }
)


_KNOWN_ALL_FIELD_NAMES = _KNOWN_FIELD_NAMES | _CURRENT_CONFIG_KNOWN_FIELD_NAMES


def _flatten_keys(obj: object, prefix: tuple[str, ...] = ()) -> tuple[tuple[str, ...], ...]:
    if isinstance(obj, dict):
        paths: list[tuple[str, ...]] = []
        for key, value in obj.items():
            key_text = str(key)
            path = prefix + (key_text,)
            paths.append(path)
            if key_text == "notes":
                continue
            paths.extend(_flatten_keys(value, path))
        return tuple(paths)
    if isinstance(obj, list):
        list_paths: list[tuple[str, ...]] = []
        for index, value in enumerate(obj):
            list_paths.extend(_flatten_keys(value, prefix + (str(index),)))
        return tuple(list_paths)
    return ()


def detect_rejected_unknown_fields(
    source_kind: SourceKind,
    raw_source: bytes | str,
) -> tuple[str, ...]:
    """Detect unknown authority/safety/governance fields in raw source."""
    if not isinstance(source_kind, SourceKind):
        raise ValueError(f"unknown source_kind: {source_kind!r}")
    if source_kind not in {
        SourceKind.IDENTITY_KERNEL,
        SourceKind.PERSONA_MANIFEST,
        SourceKind.OPERATOR_CONTRACT,
        SourceKind.COMMUNICATION_MODES,
        SourceKind.IDENTITY_PROMPT_COMPILER,
        SourceKind.SELF_MODEL_POLICY,
        SourceKind.AGENT_IDENTITY_CARD_CONFIG,
        SourceKind.CONFIG,
    }:
        return ()
    raw_text = _ensure_bytes(raw_source).decode("utf-8")
    try:
        document = load_yaml(raw_text)
    except YamlParseError:
        return ()
    rejected: list[str] = []
    for path in _flatten_keys(document):
        field_name = path[-1]
        if field_name.isdigit():
            continue
        lowered = field_name.lower()
        if lowered in _KNOWN_ALL_FIELD_NAMES:
            continue
        if any(token in lowered for token in _SUSPICIOUS_UNKNOWN_TOKENS):
            rejected.append(".".join(path))
    return tuple(sorted(set(rejected)))


def validation_status_from_result(
    *,
    errors: tuple[str, ...],
    warnings: tuple[str, ...],
    rejected_unknown_fields: tuple[str, ...] = (),
) -> SourceValidationStatus:
    if rejected_unknown_fields:
        return SourceValidationStatus.REJECTED_UNKNOWN_FIELDS
    if errors:
        return SourceValidationStatus.INVALID
    if warnings:
        return SourceValidationStatus.VALID_WITH_WARNINGS
    return SourceValidationStatus.VALID


def source_hash_pair(attestation: SourceAttestation) -> SourceHashPair:
    return SourceHashPair(
        raw_source_hash=attestation.raw_source_hash,
        canonical_typed_hash=attestation.canonical_typed_hash,
        hash_algorithm=attestation.hash_algorithm,
    )


def _validation_result_parts(result: object) -> tuple[tuple[str, ...], tuple[str, ...]]:
    errors = tuple(getattr(result, "critical_failures", ()) or getattr(result, "errors", ()) or ())
    warnings = tuple(getattr(result, "warnings", ()) or ())
    return errors, warnings


def build_source_attestation_from_validation_result(
    *,
    source_kind: SourceKind,
    source_path: Path | None,
    raw_source: bytes | str,
    typed_object: object,
    validation_result: object,
    validator_name: str,
    validator_version: str | None = None,
    evidence_refs: tuple[str, ...] = (),
) -> SourceAttestation:
    errors, warnings = _validation_result_parts(validation_result)
    rejected = detect_rejected_unknown_fields(source_kind, raw_source)
    if rejected:
        errors = errors + tuple(f"rejected_unknown_field:{field}" for field in rejected)
    return build_source_attestation(
        source_kind=source_kind,
        source_path=source_path,
        raw_source=raw_source,
        typed_object=typed_object,
        validation_status=validation_status_from_result(
            errors=errors,
            warnings=warnings,
            rejected_unknown_fields=rejected,
        ),
        validator_name=validator_name,
        validator_version=validator_version,
        rejected_unknown_fields=rejected,
        warnings=warnings,
        errors=errors,
        evidence_refs=evidence_refs,
    )


def build_doctrine_source_attestation(doctrine: object) -> SourceAttestation:
    from .doctrine_registry import validate_doctrine_registry
    from .external_doctrine import ExternalDoctrineInput, external_doctrine_input_to_dict

    if not isinstance(doctrine, ExternalDoctrineInput):
        raise ValueError("doctrine must be an ExternalDoctrineInput")
    payload = external_doctrine_input_to_dict(doctrine)
    raw_source = json.dumps(
        {
            "source_path": payload.get("source_path"),
            "source_hash": payload.get("source_hash"),
            "name": payload.get("name"),
            "version": payload.get("version"),
            "summary": payload.get("summary"),
            "key_principles": payload.get("key_principles"),
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    errors = validate_doctrine_registry((doctrine,))
    return build_source_attestation(
        source_kind=SourceKind.EXTERNAL_DOCTRINE,
        source_path=None,
        raw_source=raw_source,
        typed_object=doctrine,
        validation_status=SourceValidationStatus.INVALID
        if errors
        else SourceValidationStatus.VALID,
        validator_name="external_doctrine_registry_validator",
        validator_version="P1.4.11",
        errors=tuple(errors),
        evidence_refs=("agent/reports/P1.4.11_EXTERNAL_DOCTRINE_ASSIMILATION_REGISTRY.md",),
        source_name=str(payload.get("doctrine_id")),
    )
