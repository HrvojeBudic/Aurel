"""Data Residency Policy Card model (P1.6.5).

Defines data locality/egress/exposure semantics for AurelCore policy cards.
Data residency cards define which data must stay local, which may be processed in
EU/EEA regions, which may be sent to trusted external regions, etc. They are
declarative, deterministic, closed-world, and hash-ready.

Architectural law:
  - Data residency cards do not grant authority.
  - Data residency cards do not enforce runtime egress yet.
  - Data residency cards do not route models yet.
  - Data residency cards do not classify arbitrary data yet.
  - Data residency cards do not perform redaction/encryption yet.
  - Data residency cards remain compatible with generic PolicyCard(kind="data_residency").
  - local_only means zero outbound by definition.
  - credentials must never allow external egress by default.
"""
from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping as MappingABC
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping, TypeVar

from .errors import (
    DataResidencyPolicyCardError,
    DataResidencyPolicyCardUnknownFieldError,
    DataResidencyPolicyCardUnsafeFieldError,
    DataResidencyPolicyCardValidationError,
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
from .validation import load_policy_card_from_dict, validate_policy_card


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class DataResidencyZone(str, Enum):
    LOCAL_ONLY = "local_only"
    LOCAL_PRIVATE = "local_private"
    EU_ONLY = "eu_only"
    TRUSTED_REGION = "trusted_region"
    EXTERNAL_ALLOWED = "external_allowed"
    PUBLIC = "public"
    FORBIDDEN = "forbidden"


class DataClass(str, Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    SECRET = "secret"  # nosec B105 - data-class vocabulary, not a credential
    OPERATOR_PRIVATE = "operator_private"
    PERSONAL_DATA = "personal_data"
    SENSITIVE_PERSONAL_DATA = "sensitive_personal_data"
    BUSINESS_CONFIDENTIAL = "business_confidential"
    FINANCIAL = "financial"
    CREDENTIALS = "credentials"
    SOURCE_CODE = "source_code"
    MEMORY_RECORD = "memory_record"
    TRACE_RECORD = "trace_record"
    EVALUATION_RECORD = "evaluation_record"
    MODEL_PROMPT = "model_prompt"
    TOOL_OUTPUT = "tool_output"
    ARTIFACT = "artifact"
    SYSTEM_CONFIG = "system_config"
    POLICY_RECORD = "policy_record"
    IDENTITY_RECORD = "identity_record"


class ProcessingLocation(str, Enum):
    LOCAL_DEVICE = "local_device"
    LOCAL_NETWORK = "local_network"
    EU_REGION = "eu_region"
    TRUSTED_REGION = "trusted_region"
    EXTERNAL_API = "external_api"
    PUBLIC_WEB = "public_web"
    FORBIDDEN = "forbidden"


class RedactionRequirementType(str, Enum):
    NONE = "none"
    MASK_PERSONAL_DATA = "mask_personal_data"
    REMOVE_CREDENTIALS = "remove_credentials"
    SUMMARIZE_ONLY = "summarize_only"
    HASH_IDENTIFIERS = "hash_identifiers"
    STRIP_SOURCE_PATHS = "strip_source_paths"
    STRIP_MEMORY_METADATA = "strip_memory_metadata"
    OPERATOR_REVIEW_REQUIRED = "operator_review_required"
    DENY_EXTERNALIZATION = "deny_externalization"


class StorageRequirementType(str, Enum):
    STORE_LOCAL_ONLY = "store_local_only"
    STORE_ENCRYPTED = "store_encrypted"
    STORE_EPHEMERAL = "store_ephemeral"
    STORE_WITH_TTL = "store_with_ttl"
    DO_NOT_STORE = "do_not_store"
    AUDIT_REQUIRED = "audit_required"


class DataExposurePermission(str, Enum):
    LOCAL_MODEL_ALLOWED = "local_model_allowed"
    EXTERNAL_MODEL_ALLOWED = "external_model_allowed"
    TOOL_ACCESS_ALLOWED = "tool_access_allowed"
    WEB_SEARCH_ALLOWED = "web_search_allowed"
    ARTIFACT_EXPORT_ALLOWED = "artifact_export_allowed"
    MEMORY_WRITE_ALLOWED = "memory_write_allowed"
    EXTERNAL_API_ALLOWED = "external_api_allowed"
    HUMAN_REVIEW_REQUIRED = "human_review_required"


# ---------------------------------------------------------------------------
# Valid value sets
# ---------------------------------------------------------------------------

_VALID_ZONES = frozenset(z.value for z in DataResidencyZone)
_VALID_DATA_CLASSES = frozenset(dc.value for dc in DataClass)
_VALID_LOCATIONS = frozenset(pl.value for pl in ProcessingLocation)
_VALID_REDACTION_TYPES = frozenset(rt.value for rt in RedactionRequirementType)
_VALID_STORAGE_TYPES = frozenset(st.value for st in StorageRequirementType)


# ---------------------------------------------------------------------------
# Dataclass models
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RedactionRequirement:
    requirement_type: RedactionRequirementType
    required: bool = True
    description: str = ""


@dataclass(frozen=True)
class StorageRequirement:
    requirement_type: StorageRequirementType
    required: bool = True
    ttl_seconds: int | None = None
    description: str = ""


@dataclass(frozen=True)
class DataEgressRule:
    egress_allowed: bool
    requires_redaction: bool = False
    requires_operator_approval: bool = False
    requires_encryption: bool = False
    requires_audit_trace: bool = True
    allowed_destinations: tuple[ProcessingLocation, ...] = ()
    forbidden_destinations: tuple[ProcessingLocation, ...] = ()


@dataclass(frozen=True)
class DataExposureRule:
    local_model_allowed: bool = True
    external_model_allowed: bool = False
    tool_access_allowed: bool = False
    web_search_allowed: bool = False
    artifact_export_allowed: bool = False
    memory_write_allowed: bool = False
    external_api_allowed: bool = False
    human_review_required: bool = False


@dataclass(frozen=True)
class DataResidencyRule:
    data_class: DataClass
    residency_zone: DataResidencyZone
    allowed_processing_locations: tuple[ProcessingLocation, ...] = ()
    egress_rule: DataEgressRule = field(default_factory=lambda: DataEgressRule(False))
    redaction_requirements: tuple[RedactionRequirement, ...] = ()
    storage_requirements: tuple[StorageRequirement, ...] = ()
    exposure_rule: DataExposureRule | None = None
    description: str = ""


@dataclass(frozen=True)
class DataResidencyValidationIssue:
    code: str
    message: str
    field: str | None = None
    severity: str = "error"


@dataclass(frozen=True)
class DataResidencyValidationResult:
    valid: bool
    errors: tuple[DataResidencyValidationIssue, ...]
    warnings: tuple[DataResidencyValidationIssue, ...]
    card_id: str | None = None
    canonical_hash: str | None = None


@dataclass(frozen=True)
class DataResidencyPolicyCard:
    policy_card: PolicyCard
    schema_version: str
    residency_rules: tuple[DataResidencyRule, ...]
    default_zone: DataResidencyZone = DataResidencyZone.LOCAL_ONLY
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
) -> DataResidencyValidationIssue:
    return DataResidencyValidationIssue(
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
        raise DataResidencyPolicyCardValidationError(
            f"{field_name} value {raw!r} must be one of: "
            f"{', '.join(sorted(valid_values))}"
        )
    return enum_type(raw)


def _require_bool(raw: object, field_name: str) -> bool:
    if not isinstance(raw, bool):
        raise DataResidencyPolicyCardValidationError(f"{field_name} must be boolean")
    return raw


def _require_mapping(raw: object, field_name: str) -> Mapping[str, Any]:
    if not isinstance(raw, MappingABC):
        raise DataResidencyPolicyCardValidationError(f"{field_name} must be a mapping")
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
        raise DataResidencyPolicyCardUnsafeFieldError(
            f"{field_name}: dangerous field(s): {', '.join(sorted(dangerous))}"
        )
    unknown = present - known_fields
    if unknown:
        raise DataResidencyPolicyCardUnknownFieldError(
            f"{field_name}: unknown field(s): {', '.join(sorted(unknown))} - closed-world"
        )


# ---------------------------------------------------------------------------
# Sub-object loaders
# ---------------------------------------------------------------------------


def _load_redaction_requirement(
    raw: Mapping[str, Any],
    field_name: str,
) -> RedactionRequirement:
    from .data_residency_schema import (
        DATA_RESIDENCY_DANGEROUS_FIELD_NAMES,
        REDACTION_REQUIREMENT_REQUIRED_FIELDS,
    )

    known_fields = frozenset(REDACTION_REQUIREMENT_REQUIRED_FIELDS)
    _check_mapping_fields(raw, known_fields, DATA_RESIDENCY_DANGEROUS_FIELD_NAMES, field_name)

    return RedactionRequirement(
        requirement_type=_coerce_enum(
            raw["requirement_type"], RedactionRequirementType, _VALID_REDACTION_TYPES,
            f"{field_name}.requirement_type",
        ),
        required=_require_bool(raw.get("required", True), f"{field_name}.required"),
        description=str(raw.get("description", "")),
    )


def _load_storage_requirement(
    raw: Mapping[str, Any],
    field_name: str,
) -> StorageRequirement:
    from .data_residency_schema import (
        DATA_RESIDENCY_DANGEROUS_FIELD_NAMES,
        STORAGE_REQUIREMENT_REQUIRED_FIELDS,
    )

    known_fields = frozenset(STORAGE_REQUIREMENT_REQUIRED_FIELDS)
    _check_mapping_fields(raw, known_fields, DATA_RESIDENCY_DANGEROUS_FIELD_NAMES, field_name)

    return StorageRequirement(
        requirement_type=_coerce_enum(
            raw["requirement_type"], StorageRequirementType, _VALID_STORAGE_TYPES,
            f"{field_name}.requirement_type",
        ),
        required=_require_bool(raw.get("required", True), f"{field_name}.required"),
        ttl_seconds=raw.get("ttl_seconds"),
        description=str(raw.get("description", "")),
    )


def _load_egress_rule(
    raw: Mapping[str, Any],
    field_name: str,
) -> DataEgressRule:
    from .data_residency_schema import (
        DATA_EGRESS_RULE_OPTIONAL_FIELDS,
        DATA_EGRESS_RULE_REQUIRED_FIELDS,
        DATA_RESIDENCY_DANGEROUS_FIELD_NAMES,
    )

    known_fields = frozenset(DATA_EGRESS_RULE_REQUIRED_FIELDS + DATA_EGRESS_RULE_OPTIONAL_FIELDS)
    _check_mapping_fields(raw, known_fields, DATA_RESIDENCY_DANGEROUS_FIELD_NAMES, field_name)

    egress_allowed = _require_bool(raw["egress_allowed"], f"{field_name}.egress_allowed")

    dests_raw = raw.get("allowed_destinations", ())
    if not isinstance(dests_raw, (list, tuple)):
        raise DataResidencyPolicyCardValidationError(
            f"{field_name}.allowed_destinations must be a list/tuple"
        )
    allowed_destinations = tuple(
        _coerce_enum(d, ProcessingLocation, _VALID_LOCATIONS,
                     f"{field_name}.allowed_destinations[{i}]")
        for i, d in enumerate(dests_raw)
    )

    ford_raw = raw.get("forbidden_destinations", ())
    if not isinstance(ford_raw, (list, tuple)):
        raise DataResidencyPolicyCardValidationError(
            f"{field_name}.forbidden_destinations must be a list/tuple"
        )
    forbidden_destinations = tuple(
        _coerce_enum(d, ProcessingLocation, _VALID_LOCATIONS,
                     f"{field_name}.forbidden_destinations[{i}]")
        for i, d in enumerate(ford_raw)
    )

    return DataEgressRule(
        egress_allowed=egress_allowed,
        requires_redaction=_require_bool(
            raw.get("requires_redaction", False),
            f"{field_name}.requires_redaction",
        ),
        requires_operator_approval=_require_bool(
            raw.get("requires_operator_approval", False),
            f"{field_name}.requires_operator_approval",
        ),
        requires_encryption=_require_bool(
            raw.get("requires_encryption", False),
            f"{field_name}.requires_encryption",
        ),
        requires_audit_trace=_require_bool(
            raw.get("requires_audit_trace", True),
            f"{field_name}.requires_audit_trace",
        ),
        allowed_destinations=allowed_destinations,
        forbidden_destinations=forbidden_destinations,
    )


def _load_exposure_rule(
    raw: Mapping[str, Any],
    field_name: str,
) -> DataExposureRule:
    from .data_residency_schema import (
        DATA_EXPOSURE_RULE_REQUIRED_FIELDS,
        DATA_RESIDENCY_DANGEROUS_FIELD_NAMES,
    )

    known_fields = frozenset(DATA_EXPOSURE_RULE_REQUIRED_FIELDS)
    _check_mapping_fields(raw, known_fields, DATA_RESIDENCY_DANGEROUS_FIELD_NAMES, field_name)

    return DataExposureRule(
        local_model_allowed=_require_bool(
            raw["local_model_allowed"], f"{field_name}.local_model_allowed",
        ),
        external_model_allowed=_require_bool(
            raw["external_model_allowed"], f"{field_name}.external_model_allowed",
        ),
        tool_access_allowed=_require_bool(
            raw["tool_access_allowed"], f"{field_name}.tool_access_allowed",
        ),
        web_search_allowed=_require_bool(
            raw["web_search_allowed"], f"{field_name}.web_search_allowed",
        ),
        artifact_export_allowed=_require_bool(
            raw["artifact_export_allowed"], f"{field_name}.artifact_export_allowed",
        ),
        memory_write_allowed=_require_bool(
            raw["memory_write_allowed"], f"{field_name}.memory_write_allowed",
        ),
        external_api_allowed=_require_bool(
            raw["external_api_allowed"], f"{field_name}.external_api_allowed",
        ),
        human_review_required=_require_bool(
            raw["human_review_required"], f"{field_name}.human_review_required",
        ),
    )


def _load_residency_rule(
    raw: Mapping[str, Any],
    index: int,
) -> DataResidencyRule:
    from .data_residency_schema import (
        DATA_RESIDENCY_DANGEROUS_FIELD_NAMES,
        DATA_RESIDENCY_RULE_OPTIONAL_FIELDS,
        DATA_RESIDENCY_RULE_REQUIRED_FIELDS,
    )

    field_prefix = f"residency_rules[{index}]"
    known_fields = frozenset(
        DATA_RESIDENCY_RULE_REQUIRED_FIELDS + DATA_RESIDENCY_RULE_OPTIONAL_FIELDS
    )
    _check_mapping_fields(
        raw, known_fields, DATA_RESIDENCY_DANGEROUS_FIELD_NAMES, field_prefix,
    )

    missing = frozenset(DATA_RESIDENCY_RULE_REQUIRED_FIELDS) - set(raw.keys())
    if missing:
        raise DataResidencyPolicyCardValidationError(
            f"{field_prefix}: missing required field(s): {', '.join(sorted(missing))}"
        )

    locs_raw = raw.get("allowed_processing_locations", ())
    if not isinstance(locs_raw, (list, tuple)):
        raise DataResidencyPolicyCardValidationError(
            f"{field_prefix}.allowed_processing_locations must be a list/tuple"
        )
    allowed_processing_locations = tuple(
        _coerce_enum(loc, ProcessingLocation, _VALID_LOCATIONS,
                     f"{field_prefix}.allowed_processing_locations[{i}]")
        for i, loc in enumerate(locs_raw)
    )

    egress_raw = raw.get("egress_rule")
    if egress_raw is None:
        egress_rule = DataEgressRule(False)
    else:
        egress_rule = _load_egress_rule(
            _require_mapping(egress_raw, f"{field_prefix}.egress_rule"),
            f"{field_prefix}.egress_rule",
        )

    raws = raw.get("redaction_requirements", ())
    if not isinstance(raws, (list, tuple)):
        raise DataResidencyPolicyCardValidationError(
            f"{field_prefix}.redaction_requirements must be a list/tuple"
        )
    redaction_requirements = tuple(
        _load_redaction_requirement(
            _require_mapping(item, f"{field_prefix}.redaction_requirements[{i}]"),
            f"{field_prefix}.redaction_requirements[{i}]",
        )
        for i, item in enumerate(raws)
    )

    sraws = raw.get("storage_requirements", ())
    if not isinstance(sraws, (list, tuple)):
        raise DataResidencyPolicyCardValidationError(
            f"{field_prefix}.storage_requirements must be a list/tuple"
        )
    storage_requirements = tuple(
        _load_storage_requirement(
            _require_mapping(item, f"{field_prefix}.storage_requirements[{i}]"),
            f"{field_prefix}.storage_requirements[{i}]",
        )
        for i, item in enumerate(sraws)
    )

    exp_raw = raw.get("exposure_rule")
    exposure_rule = None
    if exp_raw is not None:
        exposure_rule = _load_exposure_rule(
            _require_mapping(exp_raw, f"{field_prefix}.exposure_rule"),
            f"{field_prefix}.exposure_rule",
        )

    description = raw.get("description", "")
    if not isinstance(description, str):
        raise DataResidencyPolicyCardValidationError(
            f"{field_prefix}.description must be a string"
        )

    return DataResidencyRule(
        data_class=_coerce_enum(
            raw["data_class"], DataClass, _VALID_DATA_CLASSES,
            f"{field_prefix}.data_class",
        ),
        residency_zone=_coerce_enum(
            raw["residency_zone"], DataResidencyZone, _VALID_ZONES,
            f"{field_prefix}.residency_zone",
        ),
        allowed_processing_locations=allowed_processing_locations,
        egress_rule=egress_rule,
        redaction_requirements=redaction_requirements,
        storage_requirements=storage_requirements,
        exposure_rule=exposure_rule,
        description=description,
    )


def _metadata_issues(
    metadata: object,
    field_name: str,
) -> list[DataResidencyValidationIssue]:
    from .data_residency_schema import DATA_RESIDENCY_DANGEROUS_METADATA_KEYS

    issues: list[DataResidencyValidationIssue] = []
    if not isinstance(metadata, MappingABC):
        issues.append(
            _make_issue("INVALID_TYPE", f"{field_name} must be a mapping", field=field_name)
        )
        return issues

    dangerous = set(metadata.keys()) & DATA_RESIDENCY_DANGEROUS_METADATA_KEYS
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


def _redaction_to_canonical_dict(rr: RedactionRequirement) -> dict[str, Any]:
    return {
        "description": rr.description,
        "required": rr.required,
        "requirement_type": rr.requirement_type.value,
    }


def _storage_to_canonical_dict(sr: StorageRequirement) -> dict[str, Any]:
    result: dict[str, Any] = {
        "description": sr.description,
        "required": sr.required,
        "requirement_type": sr.requirement_type.value,
    }
    if sr.ttl_seconds is not None:
        result["ttl_seconds"] = sr.ttl_seconds
    return result


def _egress_to_canonical_dict(er: DataEgressRule) -> dict[str, Any]:
    result: dict[str, Any] = {
        "egress_allowed": er.egress_allowed,
        "requires_audit_trace": er.requires_audit_trace,
        "requires_encryption": er.requires_encryption,
        "requires_operator_approval": er.requires_operator_approval,
        "requires_redaction": er.requires_redaction,
    }
    if er.allowed_destinations:
        result["allowed_destinations"] = [d.value for d in er.allowed_destinations]
    if er.forbidden_destinations:
        result["forbidden_destinations"] = [d.value for d in er.forbidden_destinations]
    return result


def _exposure_to_canonical_dict(xr: DataExposureRule) -> dict[str, Any]:
    return {
        "artifact_export_allowed": xr.artifact_export_allowed,
        "external_api_allowed": xr.external_api_allowed,
        "external_model_allowed": xr.external_model_allowed,
        "human_review_required": xr.human_review_required,
        "local_model_allowed": xr.local_model_allowed,
        "memory_write_allowed": xr.memory_write_allowed,
        "tool_access_allowed": xr.tool_access_allowed,
        "web_search_allowed": xr.web_search_allowed,
    }


def _rule_to_canonical_dict(rule: DataResidencyRule) -> dict[str, Any]:
    result: dict[str, Any] = {
        "data_class": rule.data_class.value,
        "description": rule.description,
        "egress_rule": _egress_to_canonical_dict(rule.egress_rule),
        "residency_zone": rule.residency_zone.value,
    }
    if rule.allowed_processing_locations:
        result["allowed_processing_locations"] = [
            loc.value for loc in rule.allowed_processing_locations
        ]
    if rule.redaction_requirements:
        result["redaction_requirements"] = [
            _redaction_to_canonical_dict(r) for r in rule.redaction_requirements
        ]
    if rule.storage_requirements:
        result["storage_requirements"] = [
            _storage_to_canonical_dict(s) for s in rule.storage_requirements
        ]
    if rule.exposure_rule is not None:
        result["exposure_rule"] = _exposure_to_canonical_dict(rule.exposure_rule)
    return result


# ---------------------------------------------------------------------------
# Public serialization / hash API
# ---------------------------------------------------------------------------


def data_residency_policy_card_to_canonical_dict(
    card: DataResidencyPolicyCard,
) -> dict[str, Any]:
    rules = sorted(
        (_rule_to_canonical_dict(r) for r in card.residency_rules),
        key=lambda item: item["data_class"],
    )

    canonical: dict[str, Any] = {
        "default_zone": card.default_zone.value,
        "metadata": dict(sorted(dict(card.metadata).items(), key=lambda item: item[0])),
        "policy_card": policy_card_to_canonical_dict(card.policy_card),
        "residency_rules": rules,
        "schema_version": card.schema_version,
    }
    return dict(sorted(canonical.items(), key=lambda item: item[0]))


def serialize_data_residency_policy_card_canonical(
    card: DataResidencyPolicyCard,
) -> str:
    canonical = data_residency_policy_card_to_canonical_dict(card)
    return json.dumps(canonical, sort_keys=True, separators=(",", ":"))


def compute_data_residency_policy_card_hash(card: DataResidencyPolicyCard) -> str:
    canonical = serialize_data_residency_policy_card_canonical(card)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def validate_data_residency_policy_card(
    card: DataResidencyPolicyCard,
) -> DataResidencyValidationResult:
    from .data_residency_schema import (
        REQUIRED_DATA_CLASSES,
        STRICT_LOCAL_ONLY_DATA_CLASSES,
        SUPPORTED_DATA_RESIDENCY_POLICY_CARD_SCHEMA_VERSIONS,
    )

    errors: list[DataResidencyValidationIssue] = []
    warnings: list[DataResidencyValidationIssue] = []

    if not isinstance(card, DataResidencyPolicyCard):
        errors.append(
            _make_issue("INVALID_TYPE", "card must be a DataResidencyPolicyCard", field="card")
        )
        return DataResidencyValidationResult(False, tuple(errors), tuple(warnings))

    if (
        not isinstance(card.schema_version, str)
        or not card.schema_version.strip()
        or card.schema_version not in SUPPORTED_DATA_RESIDENCY_POLICY_CARD_SCHEMA_VERSIONS
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
            policy_result = validate_policy_card(card.policy_card)
        except Exception as exc:
            policy_result = None
            errors.append(
                _make_issue(
                    "INVALID_POLICY_CARD",
                    f"embedded policy_card validation failed: {exc}",
                    field="policy_card",
                )
            )
        if policy_result is not None:
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
        if kind_value != PolicyCardKind.DATA_RESIDENCY.value:
            errors.append(
                _make_issue(
                    "INVALID_POLICY_CARD_KIND",
                    "DataResidencyPolicyCard requires generic PolicyCard kind 'data_residency'",
                    field="policy_card.kind",
                )
            )

    zone_value = _enum_value(card.default_zone)
    if zone_value not in _VALID_ZONES:
        errors.append(
            _make_issue("INVALID_DEFAULT_ZONE", "default_zone is invalid", field="default_zone")
        )

    errors.extend(_metadata_issues(card.metadata, "metadata"))

    if not isinstance(card.residency_rules, tuple):
        errors.append(
            _make_issue("INVALID_TYPE", "residency_rules must be a tuple",
                         field="residency_rules")
        )
        rule_items: tuple[object, ...] = ()
    else:
        rule_items = card.residency_rules

    required_class_values = frozenset(dc.value for dc in REQUIRED_DATA_CLASSES)
    seen: set[str] = set()
    duplicates: set[str] = set()
    by_class: dict[str, DataResidencyRule] = {}

    for index, rule in enumerate(rule_items):
        field_prefix = f"residency_rules[{index}]"
        if not isinstance(rule, DataResidencyRule):
            errors.append(
                _make_issue(
                    "INVALID_TYPE",
                    f"{field_prefix} must be a DataResidencyRule",
                    field=field_prefix,
                )
            )
            continue

        dc_value = _enum_value(rule.data_class)
        if dc_value not in _VALID_DATA_CLASSES:
            errors.append(
                _make_issue(
                    "INVALID_DATA_CLASS",
                    f"{field_prefix}.data_class '{dc_value}' is invalid",
                    field=f"{field_prefix}.data_class",
                )
            )
            continue
        if dc_value in seen:
            duplicates.add(dc_value)
        seen.add(dc_value)
        by_class[dc_value] = rule

        zone = _enum_value(rule.residency_zone)
        if zone not in _VALID_ZONES:
            errors.append(
                _make_issue(
                    "INVALID_ZONE",
                    f"{field_prefix}.residency_zone '{zone}' is invalid",
                    field=f"{field_prefix}.residency_zone",
                )
            )

        er = rule.egress_rule
        locs = {loc.value for loc in rule.allowed_processing_locations}

        # local_only safety
        if zone == DataResidencyZone.LOCAL_ONLY.value and er is not None:
            if er.egress_allowed:
                errors.append(
                    _make_issue(
                        "LOCAL_ONLY_EGRESS",
                        f"{field_prefix}: local_only cannot allow egress",
                        field=f"{field_prefix}.egress_rule.egress_allowed",
                    )
                )
            if rule.exposure_rule is not None:
                xr = rule.exposure_rule
                if xr.external_model_allowed:
                    errors.append(
                        _make_issue(
                            "LOCAL_ONLY_EXTERNAL_MODEL",
                            f"{field_prefix}: local_only cannot allow external model",
                            field=f"{field_prefix}.exposure_rule.external_model_allowed",
                        )
                    )
                if xr.external_api_allowed:
                    errors.append(
                        _make_issue(
                            "LOCAL_ONLY_EXTERNAL_API",
                            f"{field_prefix}: local_only cannot allow external API",
                            field=f"{field_prefix}.exposure_rule.external_api_allowed",
                        )
                    )
                if xr.web_search_allowed:
                    errors.append(
                        _make_issue(
                            "LOCAL_ONLY_WEB_SEARCH",
                            f"{field_prefix}: local_only cannot allow web search",
                            field=f"{field_prefix}.exposure_rule.web_search_allowed",
                        )
                    )
            invalid_locs = locs - {ProcessingLocation.LOCAL_DEVICE.value,
                                   ProcessingLocation.LOCAL_NETWORK.value}
            if invalid_locs:
                errors.append(
                    _make_issue(
                        "LOCAL_ONLY_INVALID_LOCATION",
                        f"{field_prefix}: local_only location(s) not allowed: "
                        f"{', '.join(sorted(invalid_locs))}",
                        field=f"{field_prefix}.allowed_processing_locations",
                    )
                )

        # forbidden safety
        if zone == DataResidencyZone.FORBIDDEN.value:
            if er is not None and er.egress_allowed:
                errors.append(
                    _make_issue(
                        "FORBIDDEN_EGRESS",
                        f"{field_prefix}: forbidden cannot allow egress",
                        field=f"{field_prefix}.egress_rule.egress_allowed",
                    )
                )
            if rule.exposure_rule is not None:
                xr = rule.exposure_rule
                if xr.external_model_allowed:
                    errors.append(
                        _make_issue(
                            "FORBIDDEN_EXTERNAL_MODEL",
                            f"{field_prefix}: forbidden cannot allow external model",
                            field=f"{field_prefix}.exposure_rule.external_model_allowed",
                        )
                    )
                if xr.external_api_allowed:
                    errors.append(
                        _make_issue(
                            "FORBIDDEN_EXTERNAL_API",
                            f"{field_prefix}: forbidden cannot allow external API",
                            field=f"{field_prefix}.exposure_rule.external_api_allowed",
                        )
                    )
                if xr.web_search_allowed:
                    errors.append(
                        _make_issue(
                            "FORBIDDEN_WEB_SEARCH",
                            f"{field_prefix}: forbidden cannot allow web search",
                            field=f"{field_prefix}.exposure_rule.web_search_allowed",
                        )
                    )
            invalid_locs = locs - {ProcessingLocation.FORBIDDEN.value}
            if invalid_locs:
                errors.append(
                    _make_issue(
                        "FORBIDDEN_INVALID_LOCATION",
                        f"{field_prefix}: forbidden location(s) not allowed: "
                        f"{', '.join(sorted(invalid_locs))}",
                        field=f"{field_prefix}.allowed_processing_locations",
                    )
                )

        if not isinstance(rule.description, str):
            errors.append(
                _make_issue(
                    "INVALID_TYPE",
                    f"{field_prefix}.description must be a string",
                    field=f"{field_prefix}.description",
                )
            )

    missing = required_class_values - seen
    if missing:
        errors.append(
            _make_issue(
                "MISSING_REQUIRED_DATA_CLASS",
                f"missing required data class(es): {', '.join(sorted(missing))}",
                field="residency_rules",
            )
        )
    if duplicates:
        errors.append(
            _make_issue(
                "DUPLICATE_DATA_CLASS",
                f"duplicate data class rule(s): {', '.join(sorted(duplicates))}",
                field="residency_rules",
            )
        )

    # credentials safety
    cred = by_class.get(DataClass.CREDENTIALS.value)
    if cred is not None:
        cred_er = cred.egress_rule
        if cred_er.egress_allowed:
            errors.append(
                _make_issue(
                    "CREDENTIALS_EGRESS",
                    "credentials cannot allow external egress",
                    "residency_rules.credentials.egress_rule.egress_allowed",
                )
            )
        if not cred_er.requires_encryption:
            errors.append(
                _make_issue(
                    "CREDENTIALS_ENCRYPTION",
                    "credentials must require encryption",
                    "residency_rules.credentials.egress_rule.requires_encryption",
                )
            )
        if not cred_er.requires_audit_trace:
            errors.append(
                _make_issue(
                    "CREDENTIALS_AUDIT",
                    "credentials must require audit trace",
                    "residency_rules.credentials.egress_rule.requires_audit_trace",
                )
            )
        if cred.exposure_rule is not None:
            c_xr = cred.exposure_rule
            if c_xr.external_model_allowed:
                errors.append(
                    _make_issue("CREDENTIALS_EXTERNAL_MODEL",
                                "credentials cannot allow external model",
                                "residency_rules.credentials.exposure_rule.external_model_allowed"))
            if c_xr.external_api_allowed:
                errors.append(
                    _make_issue("CREDENTIALS_EXTERNAL_API",
                                "credentials cannot allow external API",
                                "residency_rules.credentials.exposure_rule.external_api_allowed"))
            if c_xr.web_search_allowed:
                errors.append(
                    _make_issue("CREDENTIALS_WEB_SEARCH",
                                "credentials cannot allow web search",
                                "residency_rules.credentials.exposure_rule.web_search_allowed"))

    # sensitive_personal_data strict
    spd = by_class.get(DataClass.SENSITIVE_PERSONAL_DATA.value)
    if spd is not None:
        if spd.residency_zone.value != DataResidencyZone.LOCAL_ONLY.value:
            errors.append(
                _make_issue(
                    "SENSITIVE_PERSONAL_DATA_ZONE",
                    "sensitive_personal_data must be local_only by default",
                    "residency_rules.sensitive_personal_data.residency_zone",
                )
            )
        if spd.egress_rule.egress_allowed:
            errors.append(
                _make_issue(
                    "SENSITIVE_PERSONAL_DATA_EGRESS",
                    "sensitive_personal_data cannot allow egress",
                    "residency_rules.sensitive_personal_data.egress_rule.egress_allowed",
                )
            )
        if spd.exposure_rule is not None:
            s_xr = spd.exposure_rule
            if s_xr.external_model_allowed:
                errors.append(
                    _make_issue("SPD_EXTERNAL_MODEL",
                                "sensitive_personal_data cannot allow external model",
                                "residency_rules.sensitive_personal_data.exposure_rule"))
            if s_xr.external_api_allowed:
                errors.append(
                    _make_issue("SPD_EXTERNAL_API",
                                "sensitive_personal_data cannot allow external API",
                                "residency_rules.sensitive_personal_data.exposure_rule"))

    # memory_record strict
    mem = by_class.get(DataClass.MEMORY_RECORD.value)
    if mem is not None:
        if mem.residency_zone.value != DataResidencyZone.LOCAL_ONLY.value:
            errors.append(
                _make_issue(
                    "MEMORY_RECORD_ZONE",
                    "memory_record must be local_only by default",
                    "residency_rules.memory_record.residency_zone",
                )
            )
        if mem.egress_rule.egress_allowed:
            errors.append(
                _make_issue(
                    "MEMORY_RECORD_EGRESS",
                    "memory_record cannot allow egress",
                    "residency_rules.memory_record.egress_rule.egress_allowed",
                )
            )

    # trace_record strict
    tr = by_class.get(DataClass.TRACE_RECORD.value)
    if tr is not None:
        if tr.residency_zone.value != DataResidencyZone.LOCAL_ONLY.value:
            errors.append(
                _make_issue(
                    "TRACE_RECORD_ZONE",
                    "trace_record must be local_only by default",
                    "residency_rules.trace_record.residency_zone",
                )
            )
        if tr.egress_rule.egress_allowed:
            errors.append(
                _make_issue(
                    "TRACE_RECORD_EGRESS",
                    "trace_record cannot allow egress",
                    "residency_rules.trace_record.egress_rule.egress_allowed",
                )
            )

    canonical_hash: str | None = None
    try:
        canonical_hash = compute_data_residency_policy_card_hash(card)
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

    return DataResidencyValidationResult(
        valid=len(errors) == 0,
        errors=tuple(errors),
        warnings=tuple(warnings),
        card_id=card_id,
        canonical_hash=canonical_hash,
    )


# ---------------------------------------------------------------------------
# Dict loader
# ---------------------------------------------------------------------------


def load_data_residency_policy_card_from_dict(
    data: Mapping[str, Any],
) -> DataResidencyPolicyCard:
    from .data_residency_schema import (
        DATA_RESIDENCY_DANGEROUS_FIELD_NAMES,
        DATA_RESIDENCY_DANGEROUS_METADATA_KEYS,
        DATA_RESIDENCY_OPTIONAL_FIELDS,
        DATA_RESIDENCY_REQUIRED_FIELDS,
        SUPPORTED_DATA_RESIDENCY_POLICY_CARD_SCHEMA_VERSIONS,
    )

    raw = _require_mapping(data, "data residency policy card data")
    known_fields = frozenset(DATA_RESIDENCY_REQUIRED_FIELDS + DATA_RESIDENCY_OPTIONAL_FIELDS)
    _check_mapping_fields(
        raw, known_fields, DATA_RESIDENCY_DANGEROUS_FIELD_NAMES, "data_residency_policy_card",
    )

    missing = frozenset(DATA_RESIDENCY_REQUIRED_FIELDS) - set(raw.keys())
    if missing:
        raise DataResidencyPolicyCardValidationError(
            f"missing required field(s): {', '.join(sorted(missing))}"
        )

    schema_version = raw.get("schema_version")
    if (
        not isinstance(schema_version, str)
        or not schema_version.strip()
        or schema_version not in SUPPORTED_DATA_RESIDENCY_POLICY_CARD_SCHEMA_VERSIONS
    ):
        raise DataResidencyPolicyCardValidationError(
            f"schema_version must be one of: "
            f"{', '.join(SUPPORTED_DATA_RESIDENCY_POLICY_CARD_SCHEMA_VERSIONS)}"
        )

    policy_card_raw = _require_mapping(raw.get("policy_card"), "policy_card")
    try:
        policy_card = load_policy_card_from_dict(dict(policy_card_raw))
    except PolicyCardError as exc:
        raise DataResidencyPolicyCardValidationError(
            f"embedded policy_card invalid: {exc}"
        ) from exc

    rules_raw = raw.get("residency_rules")
    if not isinstance(rules_raw, (list, tuple)):
        raise DataResidencyPolicyCardValidationError("residency_rules must be a list/tuple")
    residency_rules = tuple(
        _load_residency_rule(
            _require_mapping(item, f"residency_rules[{index}]"), index,
        )
        for index, item in enumerate(rules_raw)
    )

    dz_raw = raw.get("default_zone", "local_only")
    if isinstance(dz_raw, str) and dz_raw in _VALID_ZONES:
        default_zone = DataResidencyZone(dz_raw)
    else:
        raise DataResidencyPolicyCardValidationError(
            f"default_zone must be one of: {', '.join(sorted(_VALID_ZONES))}"
        )

    metadata_raw = raw.get("metadata")
    if metadata_raw is None:
        metadata: dict[str, Any] = {}
    elif isinstance(metadata_raw, MappingABC):
        dangerous_meta = set(metadata_raw.keys()) & DATA_RESIDENCY_DANGEROUS_METADATA_KEYS
        if dangerous_meta:
            raise DataResidencyPolicyCardUnsafeFieldError(
                f"dangerous metadata key(s): {', '.join(sorted(dangerous_meta))}"
            )
        metadata = dict(metadata_raw)
    else:
        raise DataResidencyPolicyCardValidationError("metadata must be a mapping")

    card = DataResidencyPolicyCard(
        policy_card=policy_card,
        schema_version=schema_version,
        residency_rules=residency_rules,
        default_zone=default_zone,
        metadata=metadata,
    )

    return card


def validate_data_residency_policy_card_dict(
    data: Mapping[str, Any],
) -> DataResidencyValidationResult:
    try:
        card = load_data_residency_policy_card_from_dict(data)
    except DataResidencyPolicyCardError as exc:
        card_id = None
        if isinstance(data, MappingABC):
            policy_card_raw = data.get("policy_card")
            if isinstance(policy_card_raw, MappingABC):
                identity = policy_card_raw.get("identity")
                if isinstance(identity, MappingABC):
                    raw_card_id = identity.get("card_id")
                    if isinstance(raw_card_id, str):
                        card_id = raw_card_id
        return DataResidencyValidationResult(
            valid=False,
            errors=(
                _make_issue("INVALID_DATA_RESIDENCY_POLICY_CARD_DICT", str(exc), field=None),
            ),
            warnings=(),
            card_id=card_id,
            canonical_hash=None,
        )
    return validate_data_residency_policy_card(card)


# ---------------------------------------------------------------------------
# Default factory
# ---------------------------------------------------------------------------


def _make_default_egress(
    egress_allowed: bool,
    requires_encryption: bool = False,
    requires_audit: bool = True,
    requires_redaction: bool = False,
    requires_approval: bool = False,
    allowed_dests: tuple[ProcessingLocation, ...] = (),
) -> DataEgressRule:
    return DataEgressRule(
        egress_allowed=egress_allowed,
        requires_redaction=requires_redaction,
        requires_operator_approval=requires_approval,
        requires_encryption=requires_encryption,
        requires_audit_trace=requires_audit,
        allowed_destinations=allowed_dests,
        forbidden_destinations=(
            ProcessingLocation.EXTERNAL_API, ProcessingLocation.PUBLIC_WEB,
        ),
    )


def _make_strict_exposure() -> DataExposureRule:
    return DataExposureRule(
        local_model_allowed=True,
        external_model_allowed=False,
        tool_access_allowed=False,
        web_search_allowed=False,
        artifact_export_allowed=False,
        memory_write_allowed=False,
        external_api_allowed=False,
        human_review_required=True,
    )


def _make_public_exposure() -> DataExposureRule:
    return DataExposureRule(
        local_model_allowed=True,
        external_model_allowed=True,
        tool_access_allowed=True,
        web_search_allowed=True,
        artifact_export_allowed=True,
        memory_write_allowed=True,
        external_api_allowed=True,
        human_review_required=False,
    )


def create_default_data_residency_policy_card() -> DataResidencyPolicyCard:
    from .data_residency_schema import DATA_RESIDENCY_POLICY_CARD_SCHEMA_VERSION

    LD = ProcessingLocation.LOCAL_DEVICE
    strict_egress = _make_default_egress(False, requires_encryption=True)
    strict_secure_egress = _make_default_egress(
        False, requires_encryption=True, requires_redaction=True, requires_approval=True,
        allowed_dests=(LD,),
    )
    strict_auth_egress = _make_default_egress(
        False, requires_encryption=True, requires_redaction=True, requires_approval=True,
    )

    policy_card = PolicyCard(
        schema_version="1.0",
        identity=PolicyCardIdentity(
            card_id="aurel-core-data-residency-policy-v1",
            slug="aurel-core-data-residency-policy",
            name="AurelCore Data Residency Policy",
            version="1.0",
            namespace="aurel_core",
        ),
        kind=PolicyCardKind.DATA_RESIDENCY,
        status=PolicyCardStatus.ACTIVE,
        scope=PolicyCardScope(scope_type=PolicyCardScopeType.GLOBAL),
        description=(
            "Defines strict local-first data residency semantics for AurelCore; "
            "does not enforce egress, route models, classify data, or perform "
            "redaction/encryption at runtime."
        ),
    )

    rules: tuple[DataResidencyRule, ...] = (
        # public
        DataResidencyRule(
            data_class=DataClass.PUBLIC,
            residency_zone=DataResidencyZone.PUBLIC,
            allowed_processing_locations=(LD, ProcessingLocation.EXTERNAL_API, ProcessingLocation.PUBLIC_WEB),
            egress_rule=_make_default_egress(True, requires_audit=False),
            exposure_rule=_make_public_exposure(),
            description="Public data with low residency restriction.",
        ),
        # internal
        DataResidencyRule(
            data_class=DataClass.INTERNAL,
            residency_zone=DataResidencyZone.LOCAL_ONLY,
            allowed_processing_locations=(LD,),
            egress_rule=strict_egress,
            exposure_rule=_make_strict_exposure(),
            description="Internal operational data, local-only by default.",
        ),
        # confidential
        DataResidencyRule(
            data_class=DataClass.CONFIDENTIAL,
            residency_zone=DataResidencyZone.LOCAL_ONLY,
            allowed_processing_locations=(LD,),
            egress_rule=strict_secure_egress,
            redaction_requirements=(
                RedactionRequirement(RedactionRequirementType.OPERATOR_REVIEW_REQUIRED),
            ),
            exposure_rule=_make_strict_exposure(),
            description="Confidential data, local-only.",
        ),
        # secret
        DataResidencyRule(
            data_class=DataClass.SECRET,
            residency_zone=DataResidencyZone.LOCAL_ONLY,
            allowed_processing_locations=(LD,),
            egress_rule=strict_secure_egress,
            redaction_requirements=(
                RedactionRequirement(RedactionRequirementType.DENY_EXTERNALIZATION),
            ),
            storage_requirements=(
                StorageRequirement(StorageRequirementType.STORE_ENCRYPTED),
            ),
            exposure_rule=_make_strict_exposure(),
            description="Secret data, strict local-only, encrypted storage.",
        ),
        # operator_private
        DataResidencyRule(
            data_class=DataClass.OPERATOR_PRIVATE,
            residency_zone=DataResidencyZone.LOCAL_ONLY,
            allowed_processing_locations=(LD,),
            egress_rule=strict_secure_egress,
            storage_requirements=(
                StorageRequirement(StorageRequirementType.STORE_ENCRYPTED),
            ),
            exposure_rule=_make_strict_exposure(),
            description="Operator private data, strict local-only.",
        ),
        # personal_data
        DataResidencyRule(
            data_class=DataClass.PERSONAL_DATA,
            residency_zone=DataResidencyZone.LOCAL_ONLY,
            allowed_processing_locations=(LD,),
            egress_rule=strict_secure_egress,
            storage_requirements=(
                StorageRequirement(StorageRequirementType.STORE_ENCRYPTED),
            ),
            exposure_rule=_make_strict_exposure(),
            description="Personal data, local-only by default.",
        ),
        # sensitive_personal_data
        DataResidencyRule(
            data_class=DataClass.SENSITIVE_PERSONAL_DATA,
            residency_zone=DataResidencyZone.LOCAL_ONLY,
            allowed_processing_locations=(LD,),
            egress_rule=strict_secure_egress,
            redaction_requirements=(
                RedactionRequirement(RedactionRequirementType.MASK_PERSONAL_DATA),
            ),
            storage_requirements=(
                StorageRequirement(StorageRequirementType.STORE_ENCRYPTED),
                StorageRequirement(StorageRequirementType.AUDIT_REQUIRED),
            ),
            exposure_rule=_make_strict_exposure(),
            description="Sensitive personal data, strict local-only.",
        ),
        # business_confidential
        DataResidencyRule(
            data_class=DataClass.BUSINESS_CONFIDENTIAL,
            residency_zone=DataResidencyZone.LOCAL_ONLY,
            allowed_processing_locations=(LD,),
            egress_rule=strict_secure_egress,
            storage_requirements=(
                StorageRequirement(StorageRequirementType.STORE_ENCRYPTED),
            ),
            exposure_rule=_make_strict_exposure(),
            description="Business confidential data, local-only by default.",
        ),
        # financial
        DataResidencyRule(
            data_class=DataClass.FINANCIAL,
            residency_zone=DataResidencyZone.LOCAL_ONLY,
            allowed_processing_locations=(LD,),
            egress_rule=strict_secure_egress,
            storage_requirements=(
                StorageRequirement(StorageRequirementType.STORE_ENCRYPTED),
            ),
            exposure_rule=_make_strict_exposure(),
            description="Financial data, local-only by default.",
        ),
        # credentials
        DataResidencyRule(
            data_class=DataClass.CREDENTIALS,
            residency_zone=DataResidencyZone.LOCAL_ONLY,
            allowed_processing_locations=(LD,),
            egress_rule=strict_secure_egress,
            redaction_requirements=(
                RedactionRequirement(RedactionRequirementType.REMOVE_CREDENTIALS),
            ),
            storage_requirements=(
                StorageRequirement(StorageRequirementType.STORE_ENCRYPTED),
                StorageRequirement(StorageRequirementType.AUDIT_REQUIRED),
            ),
            exposure_rule=_make_strict_exposure(),
            description="Credentials, strict local-only, never externalize.",
        ),
        # source_code
        DataResidencyRule(
            data_class=DataClass.SOURCE_CODE,
            residency_zone=DataResidencyZone.LOCAL_ONLY,
            allowed_processing_locations=(LD,),
            egress_rule=strict_auth_egress,
            storage_requirements=(
                StorageRequirement(StorageRequirementType.STORE_LOCAL_ONLY),
            ),
            exposure_rule=DataExposureRule(
                local_model_allowed=True,
                external_model_allowed=False,
                tool_access_allowed=True,
                web_search_allowed=False,
                artifact_export_allowed=False,
                memory_write_allowed=False,
                external_api_allowed=False,
                human_review_required=False,
            ),
            description="Source code, local-only by default.",
        ),
        # memory_record
        DataResidencyRule(
            data_class=DataClass.MEMORY_RECORD,
            residency_zone=DataResidencyZone.LOCAL_ONLY,
            allowed_processing_locations=(LD,),
            egress_rule=strict_secure_egress,
            redaction_requirements=(
                RedactionRequirement(RedactionRequirementType.STRIP_MEMORY_METADATA),
            ),
            storage_requirements=(
                StorageRequirement(StorageRequirementType.STORE_ENCRYPTED),
                StorageRequirement(StorageRequirementType.AUDIT_REQUIRED),
            ),
            exposure_rule=_make_strict_exposure(),
            description="Memory records, local-only, encrypted.",
        ),
        # trace_record
        DataResidencyRule(
            data_class=DataClass.TRACE_RECORD,
            residency_zone=DataResidencyZone.LOCAL_ONLY,
            allowed_processing_locations=(LD,),
            egress_rule=strict_auth_egress,
            storage_requirements=(
                StorageRequirement(StorageRequirementType.AUDIT_REQUIRED),
            ),
            exposure_rule=_make_strict_exposure(),
            description="Trace records, local-only, audit-required.",
        ),
        # evaluation_record
        DataResidencyRule(
            data_class=DataClass.EVALUATION_RECORD,
            residency_zone=DataResidencyZone.LOCAL_ONLY,
            allowed_processing_locations=(LD,),
            egress_rule=strict_egress,
            exposure_rule=_make_strict_exposure(),
            description="Evaluation records, local-only.",
        ),
        # model_prompt
        DataResidencyRule(
            data_class=DataClass.MODEL_PROMPT,
            residency_zone=DataResidencyZone.LOCAL_ONLY,
            allowed_processing_locations=(LD,),
            egress_rule=DataEgressRule(
                egress_allowed=False,
                requires_redaction=True,
                requires_operator_approval=True,
                requires_encryption=False,
                requires_audit_trace=True,
            ),
            exposure_rule=DataExposureRule(
                local_model_allowed=True,
                external_model_allowed=False,
                tool_access_allowed=False,
                web_search_allowed=False,
                artifact_export_allowed=False,
                memory_write_allowed=False,
                external_api_allowed=False,
                human_review_required=False,
            ),
            description="Model prompts, local-only by default.",
        ),
        # tool_output
        DataResidencyRule(
            data_class=DataClass.TOOL_OUTPUT,
            residency_zone=DataResidencyZone.LOCAL_ONLY,
            allowed_processing_locations=(LD,),
            egress_rule=strict_egress,
            exposure_rule=_make_strict_exposure(),
            description="Tool outputs, local-only.",
        ),
        # artifact
        DataResidencyRule(
            data_class=DataClass.ARTIFACT,
            residency_zone=DataResidencyZone.LOCAL_ONLY,
            allowed_processing_locations=(LD,),
            egress_rule=strict_egress,
            exposure_rule=DataExposureRule(
                local_model_allowed=True,
                external_model_allowed=False,
                tool_access_allowed=True,
                web_search_allowed=False,
                artifact_export_allowed=False,
                memory_write_allowed=False,
                external_api_allowed=False,
                human_review_required=False,
            ),
            description="Artifacts, local-only by default.",
        ),
        # system_config
        DataResidencyRule(
            data_class=DataClass.SYSTEM_CONFIG,
            residency_zone=DataResidencyZone.LOCAL_ONLY,
            allowed_processing_locations=(LD,),
            egress_rule=strict_egress,
            exposure_rule=_make_strict_exposure(),
            description="System configuration, local-only.",
        ),
        # policy_record
        DataResidencyRule(
            data_class=DataClass.POLICY_RECORD,
            residency_zone=DataResidencyZone.LOCAL_ONLY,
            allowed_processing_locations=(LD,),
            egress_rule=strict_egress,
            exposure_rule=_make_strict_exposure(),
            description="Policy records, local-only.",
        ),
        # identity_record
        DataResidencyRule(
            data_class=DataClass.IDENTITY_RECORD,
            residency_zone=DataResidencyZone.LOCAL_ONLY,
            allowed_processing_locations=(LD,),
            egress_rule=strict_egress,
            exposure_rule=_make_strict_exposure(),
            description="Identity records, local-only.",
        ),
    )

    return DataResidencyPolicyCard(
        policy_card=policy_card,
        schema_version=DATA_RESIDENCY_POLICY_CARD_SCHEMA_VERSION,
        residency_rules=rules,
        default_zone=DataResidencyZone.LOCAL_ONLY,
        metadata={"owner_note": "strict default data residency policy"},
    )
