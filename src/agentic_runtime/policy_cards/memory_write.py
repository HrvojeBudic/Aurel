"""Memory Write Policy Card model (P1.6.7).

Defines memory write semantics for AurelCore policy cards. Memory write cards
declare what is allowed to become memory, who/what may write it, which memory
zone may receive a write, which write type is attempted, which evidence and
provenance must exist, and which writes may become candidate, verified or canon.
They are declarative, deterministic, closed-world, hash-ready, and
deny-by-default.

Core Aurel law:
  Raw experience does not become capability directly.
  Memory write requires policy, evidence, scope, provenance and review posture.

Architectural law:
  - Memory write cards do not grant authority.
  - Memory write cards do not write memory.
  - Memory write cards do not enforce runtime memory policy yet.
  - Memory write cards do not promote memory to canon.
  - Memory write cards do not promote skills.
  - Memory write cards do not implement Mneme.
  - Memory write cards do not implement Verification Court.
  - Memory write cards remain compatible with generic PolicyCard(kind="memory_write").
  - Candidate memory is not verified memory.
  - Verified memory is not canon.
  - No silent canonical / policy / verified-skill memory writes.
  - Operator profile writes require strict review/consent/provenance semantics.
  - Credentials must not become durable memory by default.
  - Sensitive data memory writes are strict by default.
"""
from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping as MappingABC
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping, TypeVar

from .errors import (
    MemoryWritePolicyCardError,
    MemoryWritePolicyCardUnknownFieldError,
    MemoryWritePolicyCardUnsafeFieldError,
    MemoryWritePolicyCardValidationError,
    PolicyCardError,
)
from .models import (
    PolicyCard,
    PolicyCardIdentity,
    PolicyCardKind,
    PolicyCardScope,
    PolicyCardScopeType,
    PolicyCardStatus,
)
from .serialization import policy_card_to_canonical_dict
from .validation import load_policy_card_from_dict


# ---------------------------------------------------------------------------
# Enums (memory write vocabulary)
# ---------------------------------------------------------------------------


class MemoryZone(str, Enum):
    SCRATCHPAD = "scratchpad"
    WORKING_MEMORY = "working_memory"
    EPISODIC_MEMORY = "episodic_memory"
    SEMANTIC_MEMORY = "semantic_memory"
    PROCEDURAL_MEMORY = "procedural_memory"
    OPERATOR_PROFILE = "operator_profile"
    PROJECT_MEMORY = "project_memory"
    CANON_MEMORY = "canon_memory"
    POLICY_MEMORY = "policy_memory"
    EVALUATION_MEMORY = "evaluation_memory"
    SKILL_CANDIDATE_MEMORY = "skill_candidate_memory"
    VERIFIED_SKILL_MEMORY = "verified_skill_memory"
    AUDIT_MEMORY = "audit_memory"
    FORBIDDEN = "forbidden"


class MemoryWriteType(str, Enum):
    OBSERVATION = "observation"
    USER_PREFERENCE = "user_preference"
    OPERATOR_INSTRUCTION = "operator_instruction"
    PROJECT_STATE = "project_state"
    DECISION = "decision"
    EVIDENCE_SUMMARY = "evidence_summary"
    TOOL_RESULT_SUMMARY = "tool_result_summary"
    EVALUATION_RESULT = "evaluation_result"
    POLICY_RECORD = "policy_record"
    CANON_UPDATE = "canon_update"
    SKILL_CANDIDATE = "skill_candidate"
    VERIFIED_SKILL = "verified_skill"
    BEHAVIORAL_NOTE = "behavioral_note"
    RISK_NOTE = "risk_note"
    DATA_RESIDENCY_NOTE = "data_residency_note"
    TOOL_PERMISSION_NOTE = "tool_permission_note"
    TEMPORARY_NOTE = "temporary_note"
    AUDIT_NOTE = "audit_note"


class MemoryWriteDecision(str, Enum):
    ALLOW = "allow"
    DENY = "deny"
    CANDIDATE_ONLY = "candidate_only"
    REQUIRES_REVIEW = "requires_review"
    REQUIRES_EVIDENCE = "requires_evidence"
    REQUIRES_PROVENANCE = "requires_provenance"
    REQUIRES_CONFIRMATION = "requires_confirmation"
    EPHEMERAL_ONLY = "ephemeral_only"
    CANONICALIZE_ALLOWED = "canonicalize_allowed"
    FORBIDDEN = "forbidden"


class MemoryVerificationStatus(str, Enum):
    UNVERIFIED = "unverified"
    CANDIDATE = "candidate"
    OPERATOR_REVIEWED = "operator_reviewed"
    EVIDENCE_SUPPORTED = "evidence_supported"
    VERIFIED = "verified"
    CANONIZED = "canonized"
    REJECTED = "rejected"
    EXPIRED = "expired"


class MemoryRetentionClass(str, Enum):
    EPHEMERAL = "ephemeral"
    SESSION = "session"
    PROJECT_SCOPED = "project_scoped"
    LONG_LIVED = "long_lived"
    AUDIT_RETAINED = "audit_retained"
    DO_NOT_STORE = "do_not_store"


class MemoryWriteRequirementType(str, Enum):
    REQUIRES_SOURCE_REFERENCE = "requires_source_reference"
    REQUIRES_EVIDENCE_REF = "requires_evidence_ref"
    REQUIRES_TRACE_REF = "requires_trace_ref"
    REQUIRES_OPERATOR_REVIEW = "requires_operator_review"
    REQUIRES_EXPLICIT_CONFIRMATION = "requires_explicit_confirmation"
    REQUIRES_DATA_CLASSIFICATION = "requires_data_classification"
    REQUIRES_RESIDENCY_CHECK = "requires_residency_check"
    REQUIRES_CONFLICT_CHECK = "requires_conflict_check"
    REQUIRES_EXPIRY = "requires_expiry"
    REQUIRES_EVALUATION_RESULT = "requires_evaluation_result"
    REQUIRES_VERIFICATION = "requires_verification"
    REQUIRES_POLICY_AUTHORITY = "requires_policy_authority"
    REQUIRES_USER_CONSENT = "requires_user_consent"


# ---------------------------------------------------------------------------
# Valid value sets
# ---------------------------------------------------------------------------

_VALID_ZONES = frozenset(z.value for z in MemoryZone)
_VALID_WRITE_TYPES = frozenset(t.value for t in MemoryWriteType)
_VALID_DECISIONS = frozenset(d.value for d in MemoryWriteDecision)
_VALID_STATUSES = frozenset(s.value for s in MemoryVerificationStatus)
_VALID_RETENTION = frozenset(r.value for r in MemoryRetentionClass)
_VALID_REQUIREMENT_TYPES = frozenset(r.value for r in MemoryWriteRequirementType)


# ---------------------------------------------------------------------------
# Dataclass models
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class MemoryWriteRequirement:
    requirement_type: MemoryWriteRequirementType
    required: bool = True
    description: str = ""


@dataclass(frozen=True)
class MemoryWriteRule:
    memory_zone: MemoryZone
    write_type: MemoryWriteType
    decision: MemoryWriteDecision
    verification_status: MemoryVerificationStatus
    retention_class: MemoryRetentionClass
    requirements: tuple[MemoryWriteRequirement, ...] = ()
    allowed_data_classes: tuple[str, ...] = ()
    forbidden_data_classes: tuple[str, ...] = ()
    risk_ceiling: str | None = None
    required_oversight: str | None = None
    trace_required: bool = True
    evidence_required: bool = False
    provenance_required: bool = False
    description: str = ""


@dataclass(frozen=True)
class MemoryWriteValidationIssue:
    code: str
    message: str
    field: str | None = None
    severity: str = "error"


@dataclass(frozen=True)
class MemoryWriteValidationResult:
    valid: bool
    errors: tuple[MemoryWriteValidationIssue, ...]
    warnings: tuple[MemoryWriteValidationIssue, ...]
    card_id: str | None = None
    canonical_hash: str | None = None


@dataclass(frozen=True)
class MemoryWritePolicyCard:
    policy_card: PolicyCard
    schema_version: str
    memory_rules: tuple[MemoryWriteRule, ...]
    default_decision: MemoryWriteDecision = MemoryWriteDecision.DENY
    metadata: Mapping[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


_EnumT = TypeVar("_EnumT", bound=Enum)


def _make_issue(
    code: str,
    message: str,
    field: str | None = None,
    severity: str = "error",
) -> MemoryWriteValidationIssue:
    return MemoryWriteValidationIssue(
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
        raise MemoryWritePolicyCardValidationError(
            f"{field_name} value {raw!r} must be one of: "
            f"{', '.join(sorted(valid_values))}"
        )
    return enum_type(raw)


def _require_bool(raw: object, field_name: str) -> bool:
    if not isinstance(raw, bool):
        raise MemoryWritePolicyCardValidationError(f"{field_name} must be boolean")
    return raw


def _require_mapping(raw: object, field_name: str) -> Mapping[str, Any]:
    if not isinstance(raw, MappingABC):
        raise MemoryWritePolicyCardValidationError(f"{field_name} must be a mapping")
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
        raise MemoryWritePolicyCardUnsafeFieldError(
            f"{field_name}: dangerous field(s): {', '.join(sorted(dangerous))}"
        )
    unknown = present - known_fields
    if unknown:
        raise MemoryWritePolicyCardUnknownFieldError(
            f"{field_name}: unknown field(s): {', '.join(sorted(unknown))} - closed-world"
        )


def _rule_required_requirement_types(rule: MemoryWriteRule) -> set[str]:
    return {
        req.requirement_type.value
        for req in rule.requirements
        if req.required
    }


# ---------------------------------------------------------------------------
# Sub-object loaders
# ---------------------------------------------------------------------------


def _load_requirement(
    raw: Mapping[str, Any],
    field_name: str,
) -> MemoryWriteRequirement:
    from .memory_write_schema import (
        MEMORY_WRITE_DANGEROUS_FIELD_NAMES,
        MEMORY_WRITE_REQUIREMENT_OPTIONAL_FIELDS,
        MEMORY_WRITE_REQUIREMENT_REQUIRED_FIELDS,
    )

    known_fields = frozenset(
        MEMORY_WRITE_REQUIREMENT_REQUIRED_FIELDS
        + MEMORY_WRITE_REQUIREMENT_OPTIONAL_FIELDS
    )
    _check_mapping_fields(
        raw, known_fields, MEMORY_WRITE_DANGEROUS_FIELD_NAMES, field_name,
    )

    missing = frozenset(MEMORY_WRITE_REQUIREMENT_REQUIRED_FIELDS) - set(raw.keys())
    if missing:
        raise MemoryWritePolicyCardValidationError(
            f"{field_name}: missing required field(s): {', '.join(sorted(missing))}"
        )

    return MemoryWriteRequirement(
        requirement_type=_coerce_enum(
            raw["requirement_type"], MemoryWriteRequirementType,
            _VALID_REQUIREMENT_TYPES, f"{field_name}.requirement_type",
        ),
        required=_require_bool(raw.get("required", True), f"{field_name}.required"),
        description=str(raw.get("description", "")),
    )


def _load_memory_rule(
    raw: Mapping[str, Any],
    index: int,
) -> MemoryWriteRule:
    from .memory_write_schema import (
        MEMORY_WRITE_DANGEROUS_FIELD_NAMES,
        MEMORY_WRITE_RULE_OPTIONAL_FIELDS,
        MEMORY_WRITE_RULE_REQUIRED_FIELDS,
    )

    field_prefix = f"memory_rules[{index}]"
    known_fields = frozenset(
        MEMORY_WRITE_RULE_REQUIRED_FIELDS + MEMORY_WRITE_RULE_OPTIONAL_FIELDS
    )
    _check_mapping_fields(
        raw, known_fields, MEMORY_WRITE_DANGEROUS_FIELD_NAMES, field_prefix,
    )

    missing = frozenset(MEMORY_WRITE_RULE_REQUIRED_FIELDS) - set(raw.keys())
    if missing:
        raise MemoryWritePolicyCardValidationError(
            f"{field_prefix}: missing required field(s): {', '.join(sorted(missing))}"
        )

    reqs_raw = raw.get("requirements", ())
    if not isinstance(reqs_raw, (list, tuple)):
        raise MemoryWritePolicyCardValidationError(
            f"{field_prefix}.requirements must be a list/tuple"
        )
    requirements = tuple(
        _load_requirement(
            _require_mapping(item, f"{field_prefix}.requirements[{i}]"),
            f"{field_prefix}.requirements[{i}]",
        )
        for i, item in enumerate(reqs_raw)
    )

    adc_raw = raw.get("allowed_data_classes", ())
    if not isinstance(adc_raw, (list, tuple)):
        raise MemoryWritePolicyCardValidationError(
            f"{field_prefix}.allowed_data_classes must be a list/tuple"
        )
    allowed_data_classes = tuple(str(dc) for dc in adc_raw)

    fdc_raw = raw.get("forbidden_data_classes", ())
    if not isinstance(fdc_raw, (list, tuple)):
        raise MemoryWritePolicyCardValidationError(
            f"{field_prefix}.forbidden_data_classes must be a list/tuple"
        )
    forbidden_data_classes = tuple(str(dc) for dc in fdc_raw)

    return MemoryWriteRule(
        memory_zone=_coerce_enum(
            raw["memory_zone"], MemoryZone, _VALID_ZONES,
            f"{field_prefix}.memory_zone",
        ),
        write_type=_coerce_enum(
            raw["write_type"], MemoryWriteType, _VALID_WRITE_TYPES,
            f"{field_prefix}.write_type",
        ),
        decision=_coerce_enum(
            raw["decision"], MemoryWriteDecision, _VALID_DECISIONS,
            f"{field_prefix}.decision",
        ),
        verification_status=_coerce_enum(
            raw["verification_status"], MemoryVerificationStatus, _VALID_STATUSES,
            f"{field_prefix}.verification_status",
        ),
        retention_class=_coerce_enum(
            raw["retention_class"], MemoryRetentionClass, _VALID_RETENTION,
            f"{field_prefix}.retention_class",
        ),
        requirements=requirements,
        allowed_data_classes=allowed_data_classes,
        forbidden_data_classes=forbidden_data_classes,
        risk_ceiling=raw.get("risk_ceiling"),
        required_oversight=raw.get("required_oversight"),
        trace_required=_require_bool(
            raw.get("trace_required", True), f"{field_prefix}.trace_required",
        ),
        evidence_required=_require_bool(
            raw.get("evidence_required", False), f"{field_prefix}.evidence_required",
        ),
        provenance_required=_require_bool(
            raw.get("provenance_required", False), f"{field_prefix}.provenance_required",
        ),
        description=str(raw.get("description", "")),
    )


def _metadata_issues(
    metadata: object,
    field_name: str,
) -> list[MemoryWriteValidationIssue]:
    from .memory_write_schema import MEMORY_WRITE_DANGEROUS_METADATA_KEYS

    issues: list[MemoryWriteValidationIssue] = []
    if not isinstance(metadata, MappingABC):
        issues.append(
            _make_issue("INVALID_TYPE", f"{field_name} must be a mapping", field=field_name)
        )
        return issues

    dangerous = set(metadata.keys()) & MEMORY_WRITE_DANGEROUS_METADATA_KEYS
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


def _requirement_to_canonical_dict(req: MemoryWriteRequirement) -> dict[str, Any]:
    return {
        "description": req.description,
        "required": req.required,
        "requirement_type": req.requirement_type.value,
    }


def _rule_to_canonical_dict(rule: MemoryWriteRule) -> dict[str, Any]:
    result: dict[str, Any] = {
        "decision": rule.decision.value,
        "description": rule.description,
        "evidence_required": rule.evidence_required,
        "memory_zone": rule.memory_zone.value,
        "provenance_required": rule.provenance_required,
        "retention_class": rule.retention_class.value,
        "trace_required": rule.trace_required,
        "verification_status": rule.verification_status.value,
        "write_type": rule.write_type.value,
    }
    if rule.requirements:
        result["requirements"] = [
            _requirement_to_canonical_dict(r) for r in rule.requirements
        ]
    if rule.allowed_data_classes:
        result["allowed_data_classes"] = list(rule.allowed_data_classes)
    if rule.forbidden_data_classes:
        result["forbidden_data_classes"] = list(rule.forbidden_data_classes)
    if rule.risk_ceiling is not None:
        result["risk_ceiling"] = rule.risk_ceiling
    if rule.required_oversight is not None:
        result["required_oversight"] = rule.required_oversight
    return dict(sorted(result.items(), key=lambda i: i[0]))


# ---------------------------------------------------------------------------
# Public serialization / hash API
# ---------------------------------------------------------------------------


def memory_write_policy_card_to_canonical_dict(
    card: MemoryWritePolicyCard,
) -> dict[str, Any]:
    rules = [_rule_to_canonical_dict(r) for r in card.memory_rules]

    canonical: dict[str, Any] = {
        "default_decision": card.default_decision.value,
        "memory_rules": rules,
        "metadata": dict(sorted(dict(card.metadata).items(), key=lambda i: i[0])),
        "policy_card": policy_card_to_canonical_dict(card.policy_card),
        "schema_version": card.schema_version,
    }
    return dict(sorted(canonical.items(), key=lambda i: i[0]))


def serialize_memory_write_policy_card_canonical(
    card: MemoryWritePolicyCard,
) -> str:
    canonical = memory_write_policy_card_to_canonical_dict(card)
    return json.dumps(canonical, sort_keys=True, separators=(",", ":"))


def compute_memory_write_policy_card_hash(card: MemoryWritePolicyCard) -> str:
    canonical = serialize_memory_write_policy_card_canonical(card)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def _check_zone_protection(
    rule: MemoryWriteRule,
    field_prefix: str,
    errors: list[MemoryWriteValidationIssue],
) -> None:
    """Enforce protected zone semantics: canon, policy, verified skill,
    skill candidate and operator profile zones."""
    zone = rule.memory_zone.value
    decision = rule.decision.value
    status = rule.verification_status.value
    have = _rule_required_requirement_types(rule)

    # --- Canon memory: no silent canon writes ---
    if zone == "canon_memory":
        if decision == "allow":
            errors.append(_make_issue(
                "CANON_SILENT_ALLOW",
                f"{field_prefix}: canon_memory write cannot be a silent allow",
                field=f"{field_prefix}.decision",
            ))
        canon_required = {
            "requires_source_reference",
            "requires_evidence_ref",
            "requires_trace_ref",
            "requires_operator_review",
            "requires_explicit_confirmation",
            "requires_conflict_check",
        }
        missing = canon_required - have
        if missing:
            errors.append(_make_issue(
                "CANON_MISSING_REQUIREMENTS",
                f"{field_prefix}: canon_memory requires {', '.join(sorted(missing))}",
                field=f"{field_prefix}.requirements",
            ))
        if not (rule.evidence_required and rule.provenance_required and rule.trace_required):
            errors.append(_make_issue(
                "CANON_WEAK_BINDING",
                f"{field_prefix}: canon_memory requires evidence, provenance and trace binding",
                field=f"{field_prefix}",
            ))

    # --- Policy memory: no silent policy writes ---
    if zone == "policy_memory":
        if decision == "allow":
            errors.append(_make_issue(
                "POLICY_MEMORY_SILENT_ALLOW",
                f"{field_prefix}: policy_memory write cannot be a silent allow",
                field=f"{field_prefix}.decision",
            ))
        policy_required = {
            "requires_policy_authority",
            "requires_source_reference",
            "requires_evidence_ref",
            "requires_trace_ref",
        }
        missing = policy_required - have
        if missing:
            errors.append(_make_issue(
                "POLICY_MEMORY_MISSING_REQUIREMENTS",
                f"{field_prefix}: policy_memory requires {', '.join(sorted(missing))}",
                field=f"{field_prefix}.requirements",
            ))
        if not ({"requires_operator_review", "requires_explicit_confirmation"} & have):
            errors.append(_make_issue(
                "POLICY_MEMORY_NO_REVIEW",
                f"{field_prefix}: policy_memory requires operator review or explicit confirmation",
                field=f"{field_prefix}.requirements",
            ))
        if not (rule.evidence_required and rule.provenance_required and rule.trace_required):
            errors.append(_make_issue(
                "POLICY_MEMORY_WEAK_BINDING",
                f"{field_prefix}: policy_memory requires evidence, provenance and trace binding",
                field=f"{field_prefix}",
            ))

    # --- Verified skill memory: requires evaluation/verification ---
    if zone == "verified_skill_memory":
        verified_required = {
            "requires_evaluation_result",
            "requires_verification",
            "requires_evidence_ref",
            "requires_trace_ref",
        }
        missing = verified_required - have
        if missing:
            errors.append(_make_issue(
                "VERIFIED_SKILL_MISSING_VERIFICATION",
                f"{field_prefix}: verified_skill_memory requires {', '.join(sorted(missing))}",
                field=f"{field_prefix}.requirements",
            ))

    # --- Skill candidate memory: candidate is not verified ---
    if zone == "skill_candidate_memory":
        if status in ("verified", "canonized"):
            errors.append(_make_issue(
                "SKILL_CANDIDATE_OVERSTATED_STATUS",
                f"{field_prefix}: skill_candidate_memory cannot be '{status}'; "
                "candidate memory is not verified memory",
                field=f"{field_prefix}.verification_status",
            ))

    # --- Operator profile: protected ---
    if zone == "operator_profile":
        if decision == "allow":
            errors.append(_make_issue(
                "OPERATOR_PROFILE_SILENT_ALLOW",
                f"{field_prefix}: operator_profile write cannot be a silent allow",
                field=f"{field_prefix}.decision",
            ))
        if not ({"requires_user_consent", "requires_operator_review"} & have):
            errors.append(_make_issue(
                "OPERATOR_PROFILE_NO_REVIEW",
                f"{field_prefix}: operator_profile requires user consent or operator review",
                field=f"{field_prefix}.requirements",
            ))
        if "requires_source_reference" not in have and not rule.provenance_required:
            errors.append(_make_issue(
                "OPERATOR_PROFILE_NO_PROVENANCE",
                f"{field_prefix}: operator_profile requires source/provenance semantics",
                field=f"{field_prefix}.provenance_required",
            ))
        if rule.retention_class.value in _DURABLE_RETENTION and not rule.trace_required:
            errors.append(_make_issue(
                "OPERATOR_PROFILE_NO_TRACE",
                f"{field_prefix}: durable operator_profile writes require trace",
                field=f"{field_prefix}.trace_required",
            ))

    # --- Forbidden zone must not allow durable writes ---
    if zone == "forbidden":
        if decision not in ("forbidden", "deny"):
            errors.append(_make_issue(
                "FORBIDDEN_ZONE_NOT_DENIED",
                f"{field_prefix}: forbidden zone must deny/forbidden, not '{decision}'",
                field=f"{field_prefix}.decision",
            ))
        if rule.retention_class.value != "do_not_store":
            errors.append(_make_issue(
                "FORBIDDEN_ZONE_DURABLE_RETENTION",
                f"{field_prefix}: forbidden zone must use do_not_store retention",
                field=f"{field_prefix}.retention_class",
            ))


def _check_data_class_strictness(
    rule: MemoryWriteRule,
    field_prefix: str,
    errors: list[MemoryWriteValidationIssue],
) -> None:
    """Enforce credential and sensitive-data strictness (data residency
    compatibility with P1.6.5)."""
    decision = rule.decision.value
    have = _rule_required_requirement_types(rule)
    allowed = set(rule.allowed_data_classes)

    # --- Credentials: must not become durable memory by default ---
    if "credentials" in allowed:
        errors.append(_make_issue(
            "CREDENTIALS_NOT_DURABLE_MEMORY",
            f"{field_prefix}: credentials must not be written to memory by default; "
            "credentials are deny / do_not_store",
            field=f"{field_prefix}.allowed_data_classes",
        ))

    # --- Sensitive personal data: strict by default ---
    if "sensitive_personal_data" in allowed and decision not in ("deny", "forbidden"):
        if not (rule.evidence_required and rule.provenance_required):
            errors.append(_make_issue(
                "SENSITIVE_DATA_WEAK_BINDING",
                f"{field_prefix}: sensitive_personal_data memory write requires "
                "evidence and provenance",
                field=f"{field_prefix}",
            ))
        if not ({"requires_residency_check", "requires_data_classification"} & have):
            errors.append(_make_issue(
                "SENSITIVE_DATA_NO_RESIDENCY_CHECK",
                f"{field_prefix}: sensitive_personal_data memory write requires "
                "residency check or data classification",
                field=f"{field_prefix}.requirements",
            ))
        if not ({"requires_operator_review"} & have) and decision not in (
            "requires_review", "requires_confirmation",
        ):
            errors.append(_make_issue(
                "SENSITIVE_DATA_NO_REVIEW",
                f"{field_prefix}: sensitive_personal_data memory write requires review",
                field=f"{field_prefix}.decision",
            ))


def validate_memory_write_policy_card(
    card: MemoryWritePolicyCard,
) -> MemoryWriteValidationResult:
    from .memory_write_schema import (
        SUPPORTED_MEMORY_WRITE_POLICY_CARD_SCHEMA_VERSIONS,
    )

    errors: list[MemoryWriteValidationIssue] = []
    warnings: list[MemoryWriteValidationIssue] = []

    if not isinstance(card, MemoryWritePolicyCard):
        errors.append(
            _make_issue("INVALID_TYPE", "card must be a MemoryWritePolicyCard", field="card")
        )
        return MemoryWriteValidationResult(False, tuple(errors), tuple(warnings))

    if (
        not isinstance(card.schema_version, str)
        or not card.schema_version.strip()
        or card.schema_version not in SUPPORTED_MEMORY_WRITE_POLICY_CARD_SCHEMA_VERSIONS
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
        if kind_value != PolicyCardKind.MEMORY_WRITE.value:
            errors.append(
                _make_issue(
                    "INVALID_POLICY_CARD_KIND",
                    "MemoryWritePolicyCard requires generic PolicyCard kind 'memory_write'",
                    field="policy_card.kind",
                )
            )

    decision_value = _enum_value(card.default_decision)
    if decision_value not in _VALID_DECISIONS:
        errors.append(
            _make_issue("INVALID_DEFAULT_DECISION", "default_decision is invalid",
                        field="default_decision")
        )
    elif decision_value not in ("deny", "forbidden"):
        errors.append(
            _make_issue(
                "PERMISSIVE_DEFAULT_DECISION",
                f"default_decision must be deny-by-default, not '{decision_value}'",
                field="default_decision",
            )
        )

    errors.extend(_metadata_issues(card.metadata, "metadata"))

    if not isinstance(card.memory_rules, tuple):
        errors.append(
            _make_issue("INVALID_TYPE", "memory_rules must be a tuple", field="memory_rules")
        )
        rule_items: tuple[object, ...] = ()
    else:
        rule_items = card.memory_rules

    if isinstance(card.memory_rules, tuple) and not card.memory_rules:
        errors.append(
            _make_issue("EMPTY_MEMORY_RULES", "memory_rules must not be empty",
                        field="memory_rules")
        )

    for index, rule in enumerate(rule_items):
        field_prefix = f"memory_rules[{index}]"
        if not isinstance(rule, MemoryWriteRule):
            errors.append(
                _make_issue("INVALID_TYPE", f"{field_prefix} must be a MemoryWriteRule",
                            field=field_prefix)
            )
            continue

        zone = _enum_value(rule.memory_zone)
        if zone not in _VALID_ZONES:
            errors.append(_make_issue(
                "INVALID_MEMORY_ZONE",
                f"{field_prefix}.memory_zone '{zone}' is invalid",
                field=f"{field_prefix}.memory_zone",
            ))
        wt = _enum_value(rule.write_type)
        if wt not in _VALID_WRITE_TYPES:
            errors.append(_make_issue(
                "INVALID_WRITE_TYPE",
                f"{field_prefix}.write_type '{wt}' is invalid",
                field=f"{field_prefix}.write_type",
            ))
        dec = _enum_value(rule.decision)
        if dec not in _VALID_DECISIONS:
            errors.append(_make_issue(
                "INVALID_DECISION",
                f"{field_prefix}.decision '{dec}' is invalid",
                field=f"{field_prefix}.decision",
            ))
        st = _enum_value(rule.verification_status)
        if st not in _VALID_STATUSES:
            errors.append(_make_issue(
                "INVALID_VERIFICATION_STATUS",
                f"{field_prefix}.verification_status '{st}' is invalid",
                field=f"{field_prefix}.verification_status",
            ))
        rc = _enum_value(rule.retention_class)
        if rc not in _VALID_RETENTION:
            errors.append(_make_issue(
                "INVALID_RETENTION_CLASS",
                f"{field_prefix}.retention_class '{rc}' is invalid",
                field=f"{field_prefix}.retention_class",
            ))

        for ri, req in enumerate(rule.requirements):
            rt = _enum_value(req.requirement_type)
            if rt not in _VALID_REQUIREMENT_TYPES:
                errors.append(_make_issue(
                    "INVALID_REQUIREMENT_TYPE",
                    f"{field_prefix}.requirements[{ri}] '{rt}' is invalid",
                    field=f"{field_prefix}.requirements[{ri}]",
                ))

        _check_zone_protection(rule, field_prefix, errors)
        _check_data_class_strictness(rule, field_prefix, errors)

    canonical_hash: str | None = None
    try:
        canonical_hash = compute_memory_write_policy_card_hash(card)
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

    return MemoryWriteValidationResult(
        valid=len(errors) == 0,
        errors=tuple(errors),
        warnings=tuple(warnings),
        card_id=card_id,
        canonical_hash=canonical_hash,
    )


# ---------------------------------------------------------------------------
# Dict loader
# ---------------------------------------------------------------------------


def load_memory_write_policy_card_from_dict(
    data: Mapping[str, Any],
) -> MemoryWritePolicyCard:
    from .memory_write_schema import (
        MEMORY_WRITE_DANGEROUS_FIELD_NAMES,
        MEMORY_WRITE_DANGEROUS_METADATA_KEYS,
        MEMORY_WRITE_OPTIONAL_FIELDS,
        MEMORY_WRITE_REQUIRED_FIELDS,
        SUPPORTED_MEMORY_WRITE_POLICY_CARD_SCHEMA_VERSIONS,
    )

    raw = _require_mapping(data, "memory write policy card data")
    known_fields = frozenset(MEMORY_WRITE_REQUIRED_FIELDS + MEMORY_WRITE_OPTIONAL_FIELDS)
    _check_mapping_fields(
        raw, known_fields, MEMORY_WRITE_DANGEROUS_FIELD_NAMES,
        "memory_write_policy_card",
    )

    missing = frozenset(MEMORY_WRITE_REQUIRED_FIELDS) - set(raw.keys())
    if missing:
        raise MemoryWritePolicyCardValidationError(
            f"missing required field(s): {', '.join(sorted(missing))}"
        )

    schema_version = raw.get("schema_version")
    if (
        not isinstance(schema_version, str)
        or not schema_version.strip()
        or schema_version not in SUPPORTED_MEMORY_WRITE_POLICY_CARD_SCHEMA_VERSIONS
    ):
        raise MemoryWritePolicyCardValidationError(
            f"schema_version must be one of: "
            f"{', '.join(SUPPORTED_MEMORY_WRITE_POLICY_CARD_SCHEMA_VERSIONS)}"
        )

    policy_card_raw = _require_mapping(raw.get("policy_card"), "policy_card")
    try:
        policy_card = load_policy_card_from_dict(dict(policy_card_raw))
    except PolicyCardError as exc:
        raise MemoryWritePolicyCardValidationError(
            f"embedded policy_card invalid: {exc}"
        ) from exc

    rules_raw = raw.get("memory_rules")
    if not isinstance(rules_raw, (list, tuple)):
        raise MemoryWritePolicyCardValidationError("memory_rules must be a list/tuple")
    memory_rules = tuple(
        _load_memory_rule(
            _require_mapping(item, f"memory_rules[{index}]"), index,
        )
        for index, item in enumerate(rules_raw)
    )

    dd_raw = raw.get("default_decision", "deny")
    if isinstance(dd_raw, str) and dd_raw in _VALID_DECISIONS:
        default_decision = MemoryWriteDecision(dd_raw)
    else:
        raise MemoryWritePolicyCardValidationError(
            f"default_decision must be one of: {', '.join(sorted(_VALID_DECISIONS))}"
        )

    metadata_raw = raw.get("metadata")
    if metadata_raw is None:
        metadata: dict[str, Any] = {}
    elif isinstance(metadata_raw, MappingABC):
        dangerous_meta = set(metadata_raw.keys()) & MEMORY_WRITE_DANGEROUS_METADATA_KEYS
        if dangerous_meta:
            raise MemoryWritePolicyCardUnsafeFieldError(
                f"dangerous metadata key(s): {', '.join(sorted(dangerous_meta))}"
            )
        metadata = dict(metadata_raw)
    else:
        raise MemoryWritePolicyCardValidationError("metadata must be a mapping")

    card = MemoryWritePolicyCard(
        policy_card=policy_card,
        schema_version=schema_version,
        memory_rules=memory_rules,
        default_decision=default_decision,
        metadata=metadata,
    )

    result = validate_memory_write_policy_card(card)
    if not result.valid:
        messages = "; ".join(e.message for e in result.errors)
        raise MemoryWritePolicyCardValidationError(f"validation failed: {messages}")

    return card


def validate_memory_write_policy_card_dict(
    data: Mapping[str, Any],
) -> MemoryWriteValidationResult:
    try:
        card = load_memory_write_policy_card_from_dict(data)
    except MemoryWritePolicyCardError as exc:
        card_id = None
        if isinstance(data, MappingABC):
            policy_card_raw = data.get("policy_card")
            if isinstance(policy_card_raw, MappingABC):
                identity = policy_card_raw.get("identity")
                if isinstance(identity, MappingABC):
                    raw_card_id = identity.get("card_id")
                    if isinstance(raw_card_id, str):
                        card_id = raw_card_id
        return MemoryWriteValidationResult(
            valid=False,
            errors=(
                _make_issue("INVALID_DATA_MEMORY_WRITE_POLICY_CARD_DICT", str(exc), field=None),
            ),
            warnings=(),
            card_id=card_id,
            canonical_hash=None,
        )
    return validate_memory_write_policy_card(card)


# ---------------------------------------------------------------------------
# Durable retention / zone constants used by validation
# ---------------------------------------------------------------------------

_DURABLE_RETENTION = frozenset({
    "project_scoped",
    "long_lived",
    "audit_retained",
})


# ---------------------------------------------------------------------------
# Default factory
# ---------------------------------------------------------------------------


def create_default_memory_write_policy_card() -> MemoryWritePolicyCard:
    from .memory_write_schema import (
        DEFAULT_MEMORY_WRITE_RULES,
        MEMORY_WRITE_POLICY_CARD_SCHEMA_VERSION,
    )

    policy_card = PolicyCard(
        schema_version="1.0",
        identity=PolicyCardIdentity(
            card_id="aurel-core-memory-write-policy-v1",
            slug="aurel-core-memory-write-policy",
            name="AurelCore Memory Write Policy",
            version="1.0",
            namespace="aurel_core",
        ),
        kind=PolicyCardKind.MEMORY_WRITE,
        status=PolicyCardStatus.ACTIVE,
        scope=PolicyCardScope(scope_type=PolicyCardScopeType.MEMORY),
        description=(
            "Defines strict deny-by-default memory write semantics for AurelCore; "
            "does not store, retrieve, consolidate, promote, canonize or enforce "
            "memory at runtime, and does not implement Mneme."
        ),
    )

    return MemoryWritePolicyCard(
        policy_card=policy_card,
        schema_version=MEMORY_WRITE_POLICY_CARD_SCHEMA_VERSION,
        memory_rules=DEFAULT_MEMORY_WRITE_RULES,
        default_decision=MemoryWriteDecision.DENY,
        metadata={"owner_note": "conservative default deny-by-default memory write policy"},
    )
