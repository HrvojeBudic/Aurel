"""Policy Card closed-world validation and dict loading (P1.6.0, updated P1.6.1).

Validates that every policy card is:
- closed-world (no unknown top-level fields)
- safe (no dangerous metadata keys, no shadow authority)
- well-formed (all required fields present, enums valid, types correct)
- schema-versioned (schema_version required, must be supported)

Architectural law:
  - Unknown authority/safety fields must fail closed — never silently ignored.
  - Metadata must not become a shadow control plane.
  - Dangerous keys in metadata must be rejected.
  - Schema version must be explicit and supported.
  - Runtime-future reserved fields are not accepted yet.
"""
from __future__ import annotations

from typing import Any, Mapping

from .errors import PolicyCardUnknownFieldError, PolicyCardUnsafeFieldError
from .models import (
    PolicyCard,
    PolicyCardAuthorityBinding,
    PolicyCardIdentity,
    PolicyCardKind,
    PolicyCardRiskBinding,
    PolicyCardScope,
    PolicyCardScopeType,
    PolicyCardSource,
    PolicyCardStatus,
    PolicyCardValidationIssue,
    PolicyCardValidationResult,
)
from .schema import (
    ALL_KNOWN_TOP_LEVEL_FIELDS,
    POLICY_CARD_DANGEROUS_METADATA_KEYS,
    POLICY_CARD_FORBIDDEN_FIELDS,
    POLICY_CARD_RUNTIME_FUTURE_FIELDS,
    SUPPORTED_POLICY_CARD_SCHEMA_VERSIONS,
)

# ---------------------------------------------------------------------------
# Known fields — anything else is rejected (closed-world)
# NOTE: These are now derived from the centralized schema in schema.py.
# Keep local aliases for backward compatibility within this module.
# ---------------------------------------------------------------------------

KNOWN_TOP_LEVEL_FIELDS: frozenset[str] = ALL_KNOWN_TOP_LEVEL_FIELDS

KNOWN_IDENTITY_FIELDS: frozenset[str] = frozenset({
    "card_id", "slug", "name", "version", "namespace",
})

KNOWN_SCOPE_FIELDS: frozenset[str] = frozenset({
    "scope_type", "scope_id", "applies_to",
})

KNOWN_RISK_BINDING_FIELDS: frozenset[str] = frozenset({
    "risk_tier", "risk_floor", "risk_ceiling", "requires_oversight",
})

KNOWN_AUTHORITY_BINDING_FIELDS: frozenset[str] = frozenset({
    "authority_scope", "required_authority", "operator_required", "delegation_allowed",
})

KNOWN_SOURCE_FIELDS: frozenset[str] = frozenset({
    "source_type", "source_path", "raw_source_hash", "canonical_hash", "loaded_at",
})

# ---------------------------------------------------------------------------
# Dangerous fields — must fail validation if present
# ---------------------------------------------------------------------------

DANGEROUS_TOP_LEVEL_FIELDS: frozenset[str] = POLICY_CARD_FORBIDDEN_FIELDS

DANGEROUS_METADATA_KEYS: frozenset[str] = POLICY_CARD_DANGEROUS_METADATA_KEYS

VALID_SEVERITIES: frozenset[str] = frozenset({"error", "warning", "info"})

# ---------------------------------------------------------------------------
# Valid enum value sets
# ---------------------------------------------------------------------------

VALID_KINDS = frozenset(k.value for k in PolicyCardKind)
VALID_STATUSES = frozenset(s.value for s in PolicyCardStatus)
VALID_SCOPE_TYPES = frozenset(st.value for st in PolicyCardScopeType)

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _make_issue(code: str, message: str, field: str | None = None,
                severity: str = "error") -> PolicyCardValidationIssue:
    return PolicyCardValidationIssue(code=code, message=message,
                                     field=field, severity=severity)


def _check_unknown_fields(present_keys: set[str], known: frozenset[str],
                          label: str) -> list[PolicyCardValidationIssue]:
    """Fail if any unknown field is present under the given label."""
    unknown = present_keys - known
    if not unknown:
        return []
    return [
        _make_issue("UNKNOWN_FIELD",
                     f"{label}: unknown field '{f}' — closed-world violation",
                     field=f)
        for f in sorted(unknown)
    ]


def _check_dangerous_fields(present_keys: set[str], label: str) -> list[PolicyCardValidationIssue]:
    """Fail if any dangerous top-level field is present."""
    dangerous = present_keys & DANGEROUS_TOP_LEVEL_FIELDS
    if not dangerous:
        return []
    return [
        _make_issue("UNSAFE_FIELD",
                     f"{label}: dangerous field '{f}' rejected — policy cards must not "
                     f"silently grant authority, bypass governance, or override safety",
                     field=f)
        for f in sorted(dangerous)
    ]


def _check_dangerous_metadata_keys(metadata: dict[str, Any]) -> list[PolicyCardValidationIssue]:
    """Fail if metadata contains dangerous keys."""
    dangerous = set(metadata.keys()) & DANGEROUS_METADATA_KEYS
    if not dangerous:
        return []
    return [
        _make_issue("UNSAFE_METADATA_KEY",
                     f"metadata: dangerous key '{k}' rejected — metadata must not "
                     f"become a shadow control plane",
                     field=f"metadata.{k}")
        for k in sorted(dangerous)
    ]


# ---------------------------------------------------------------------------
# Sub-object validators
# ---------------------------------------------------------------------------


def _validate_identity(identity: PolicyCardIdentity) -> list[PolicyCardValidationIssue]:
    issues: list[PolicyCardValidationIssue] = []
    if not identity.card_id or not identity.card_id.strip():
        issues.append(_make_issue("MISSING_REQUIRED", "identity.card_id is required",
                                   field="identity.card_id"))
    if not identity.name or not identity.name.strip():
        issues.append(_make_issue("MISSING_REQUIRED", "identity.name is required",
                                   field="identity.name"))
    if not identity.version or not identity.version.strip():
        issues.append(_make_issue("MISSING_REQUIRED", "identity.version is required",
                                   field="identity.version"))
    if not identity.namespace or not identity.namespace.strip():
        issues.append(_make_issue("MISSING_REQUIRED", "identity.namespace is required",
                                   field="identity.namespace"))
    if not identity.slug or not identity.slug.strip():
        issues.append(_make_issue("MISSING_REQUIRED", "identity.slug is required",
                                   field="identity.slug"))
    return issues


def _validate_scope(scope: PolicyCardScope) -> list[PolicyCardValidationIssue]:
    issues: list[PolicyCardValidationIssue] = []
    if scope.scope_type.value not in VALID_SCOPE_TYPES:
        issues.append(_make_issue("INVALID_ENUM",
                                   f"scope.scope_type '{scope.scope_type}' is invalid",
                                   field="scope.scope_type"))
    if scope.scope_id is not None and not isinstance(scope.scope_id, str):
        issues.append(_make_issue("INVALID_TYPE",
                                   "scope.scope_id must be a string or null",
                                   field="scope.scope_id"))
    if not isinstance(scope.applies_to, tuple):
        issues.append(_make_issue("INVALID_TYPE",
                                   "scope.applies_to must be a tuple",
                                   field="scope.applies_to"))
    else:
        for i, item in enumerate(scope.applies_to):
            if not isinstance(item, str):
                issues.append(_make_issue("INVALID_TYPE",
                                           f"scope.applies_to[{i}] must be a string",
                                           field=f"scope.applies_to[{i}]"))
    return issues


def _validate_risk_binding(rb: PolicyCardRiskBinding) -> list[PolicyCardValidationIssue]:
    issues: list[PolicyCardValidationIssue] = []
    for field_name in ("risk_tier", "risk_floor", "risk_ceiling"):
        value = getattr(rb, field_name)
        if value is not None and not isinstance(value, str):
            issues.append(_make_issue("INVALID_TYPE",
                                       f"risk_binding.{field_name} must be string or null",
                                       field=f"risk_binding.{field_name}"))
    if not isinstance(rb.requires_oversight, bool):
        issues.append(_make_issue("INVALID_TYPE",
                                   "risk_binding.requires_oversight must be boolean",
                                   field="risk_binding.requires_oversight"))
    return issues


def _validate_authority_binding(ab: PolicyCardAuthorityBinding) -> list[PolicyCardValidationIssue]:
    issues: list[PolicyCardValidationIssue] = []
    for field_name in ("authority_scope", "required_authority"):
        value = getattr(ab, field_name)
        if value is not None and not isinstance(value, str):
            issues.append(_make_issue("INVALID_TYPE",
                                       f"authority_binding.{field_name} must be string or null",
                                       field=f"authority_binding.{field_name}"))
    if not isinstance(ab.operator_required, bool):
        issues.append(_make_issue("INVALID_TYPE",
                                   "authority_binding.operator_required must be boolean",
                                   field="authority_binding.operator_required"))
    if not isinstance(ab.delegation_allowed, bool):
        issues.append(_make_issue("INVALID_TYPE",
                                   "authority_binding.delegation_allowed must be boolean",
                                   field="authority_binding.delegation_allowed"))
    return issues


def _validate_source(source: PolicyCardSource) -> list[PolicyCardValidationIssue]:
    issues: list[PolicyCardValidationIssue] = []
    if not isinstance(source.source_type, str) or not source.source_type.strip():
        issues.append(_make_issue("MISSING_REQUIRED",
                                   "source.source_type is required",
                                   field="source.source_type"))
    for field_name in ("source_path", "raw_source_hash", "canonical_hash", "loaded_at"):
        value = getattr(source, field_name)
        if value is not None and not isinstance(value, str):
            issues.append(_make_issue("INVALID_TYPE",
                                       f"source.{field_name} must be string or null",
                                       field=f"source.{field_name}"))
    return issues


def _validate_metadata(metadata: dict[str, Any]) -> list[PolicyCardValidationIssue]:
    issues: list[PolicyCardValidationIssue] = []
    if not isinstance(metadata, dict):
        issues.append(_make_issue("INVALID_TYPE",
                                   "metadata must be a mapping",
                                   field="metadata"))
        return issues
    issues.extend(_check_dangerous_metadata_keys(metadata))
    return issues


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def validate_policy_card(card: PolicyCard) -> PolicyCardValidationResult:
    """Run full structured validation on a PolicyCard.

    Returns a PolicyCardValidationResult with errors and warnings.
    """
    errors: list[PolicyCardValidationIssue] = []
    warnings: list[PolicyCardValidationIssue] = []

    # Schema version
    if not isinstance(card.schema_version, str) or not card.schema_version.strip():
        errors.append(_make_issue("MISSING_SCHEMA_VERSION",
                                   "schema_version is required",
                                   field="schema_version"))
    elif card.schema_version not in SUPPORTED_POLICY_CARD_SCHEMA_VERSIONS:
        errors.append(_make_issue("UNSUPPORTED_SCHEMA_VERSION",
                                   f"schema_version '{card.schema_version}' is not supported",
                                   field="schema_version"))

    # Identity
    errors.extend(_validate_identity(card.identity))

    # Kind
    if card.kind.value not in VALID_KINDS:
        errors.append(_make_issue("INVALID_ENUM",
                                   f"kind '{card.kind.value}' is invalid",
                                   field="kind"))

    # Status
    if card.status.value not in VALID_STATUSES:
        errors.append(_make_issue("INVALID_ENUM",
                                   f"status '{card.status.value}' is invalid",
                                   field="status"))

    # Scope
    errors.extend(_validate_scope(card.scope))

    # Description
    if not isinstance(card.description, str) or not card.description.strip():
        errors.append(_make_issue("MISSING_REQUIRED",
                                   "description is required",
                                   field="description"))

    # Optional sub-objects
    if card.risk_binding is not None:
        errors.extend(_validate_risk_binding(card.risk_binding))
    if card.authority_binding is not None:
        errors.extend(_validate_authority_binding(card.authority_binding))
    if card.source is not None:
        errors.extend(_validate_source(card.source))

    # Metadata
    errors.extend(_validate_metadata(dict(card.metadata)))

    valid = len(errors) == 0
    card_id = card.identity.card_id if card.identity else None

    return PolicyCardValidationResult(
        valid=valid,
        errors=tuple(errors),
        warnings=tuple(warnings),
        card_id=card_id,
    )


def load_policy_card_from_dict(data: Mapping[str, Any]) -> PolicyCard:
    """Parse and validate a policy card from a raw dictionary.

    This is a closed-world loader: unknown top-level fields and dangerous
    metadata keys are rejected. Raises PolicyCardUnknownFieldError or
    PolicyCardUnsafeFieldError on violations.

    Returns a validated PolicyCard.
    """
    if not isinstance(data, dict):
        raise PolicyCardUnknownFieldError("policy card data must be a mapping")

    present = set(data.keys())

    # Dangerous field check MUST come first — dangerous fields are not
    # "known" fields and would otherwise be caught as unknown.
    dangerous = present & DANGEROUS_TOP_LEVEL_FIELDS
    if dangerous:
        raise PolicyCardUnsafeFieldError(
            f"dangerous field(s) detected: {', '.join(sorted(dangerous))} — "
            f"policy cards must not silently grant authority or bypass governance"
        )

    # Runtime-future field check — reserved fields not accepted yet
    runtime_future = present & POLICY_CARD_RUNTIME_FUTURE_FIELDS
    if runtime_future:
        raise PolicyCardUnknownFieldError(
            f"runtime-future field(s) not accepted in P1.6.1: "
            f"{', '.join(sorted(runtime_future))} — "
            f"these fields are reserved for future runtime resolver"
        )

    # Closed-world check: reject unknown top-level fields
    unknown = present - KNOWN_TOP_LEVEL_FIELDS
    if unknown:
        raise PolicyCardUnknownFieldError(
            f"unknown top-level field(s): {', '.join(sorted(unknown))} — "
            f"policy cards are closed-world"
        )

    # --- Parse schema_version (required) ---
    schema_version_raw = data.get("schema_version")
    if not isinstance(schema_version_raw, str) or not schema_version_raw.strip():
        raise PolicyCardUnknownFieldError(
            f"schema_version is required and must be one of: "
            f"{', '.join(SUPPORTED_POLICY_CARD_SCHEMA_VERSIONS)}"
        )
    if schema_version_raw not in SUPPORTED_POLICY_CARD_SCHEMA_VERSIONS:
        raise PolicyCardUnknownFieldError(
            f"schema_version '{schema_version_raw}' is not supported; "
            f"supported: {', '.join(SUPPORTED_POLICY_CARD_SCHEMA_VERSIONS)}"
        )
    schema_version = schema_version_raw

    # --- Parse identity ---
    identity_raw = data.get("identity")
    if not isinstance(identity_raw, dict):
        raise PolicyCardUnknownFieldError("identity must be a mapping")
    identity = PolicyCardIdentity(
        card_id=str(identity_raw.get("card_id", "")),
        slug=str(identity_raw.get("slug", "")),
        name=str(identity_raw.get("name", "")),
        version=str(identity_raw.get("version", "")),
        namespace=str(identity_raw.get("namespace", "")),
    )

    # --- Parse kind ---
    kind_raw = data.get("kind")
    if not isinstance(kind_raw, str) or kind_raw not in VALID_KINDS:
        raise PolicyCardUnknownFieldError(
            f"kind must be one of: {', '.join(sorted(VALID_KINDS))}"
        )
    kind = PolicyCardKind(kind_raw)

    # --- Parse status ---
    status_raw = data.get("status")
    if not isinstance(status_raw, str) or status_raw not in VALID_STATUSES:
        raise PolicyCardUnknownFieldError(
            f"status must be one of: {', '.join(sorted(VALID_STATUSES))}"
        )
    status = PolicyCardStatus(status_raw)

    # --- Parse scope ---
    scope_raw = data.get("scope")
    if not isinstance(scope_raw, dict):
        raise PolicyCardUnknownFieldError("scope must be a mapping")
    scope_type_raw = scope_raw.get("scope_type")
    if not isinstance(scope_type_raw, str) or scope_type_raw not in VALID_SCOPE_TYPES:
        raise PolicyCardUnknownFieldError(
            f"scope.scope_type must be one of: {', '.join(sorted(VALID_SCOPE_TYPES))}"
        )
    scope = PolicyCardScope(
        scope_type=PolicyCardScopeType(scope_type_raw),
        scope_id=scope_raw.get("scope_id"),
        applies_to=tuple(scope_raw.get("applies_to", ())),
    )

    # --- Parse description ---
    description = data.get("description", "")
    if not isinstance(description, str):
        raise PolicyCardUnknownFieldError("description must be a string")

    # --- Parse optional risk_binding ---
    rb_raw = data.get("risk_binding")
    risk_binding: PolicyCardRiskBinding | None = None
    if rb_raw is not None:
        if not isinstance(rb_raw, dict):
            raise PolicyCardUnknownFieldError("risk_binding must be a mapping")
        risk_binding = PolicyCardRiskBinding(
            risk_tier=rb_raw.get("risk_tier"),
            risk_floor=rb_raw.get("risk_floor"),
            risk_ceiling=rb_raw.get("risk_ceiling"),
            requires_oversight=bool(rb_raw.get("requires_oversight", False)),
        )

    # --- Parse optional authority_binding ---
    ab_raw = data.get("authority_binding")
    authority_binding: PolicyCardAuthorityBinding | None = None
    if ab_raw is not None:
        if not isinstance(ab_raw, dict):
            raise PolicyCardUnknownFieldError("authority_binding must be a mapping")
        authority_binding = PolicyCardAuthorityBinding(
            authority_scope=ab_raw.get("authority_scope"),
            required_authority=ab_raw.get("required_authority"),
            operator_required=bool(ab_raw.get("operator_required", False)),
            delegation_allowed=bool(ab_raw.get("delegation_allowed", False)),
        )

    # --- Parse optional source ---
    src_raw = data.get("source")
    source: PolicyCardSource | None = None
    if src_raw is not None:
        if not isinstance(src_raw, dict):
            raise PolicyCardUnknownFieldError("source must be a mapping")
        source = PolicyCardSource(
            source_type=str(src_raw.get("source_type", "")),
            source_path=src_raw.get("source_path"),
            raw_source_hash=src_raw.get("raw_source_hash"),
            canonical_hash=src_raw.get("canonical_hash"),
            loaded_at=src_raw.get("loaded_at"),
        )

    # --- Parse metadata ---
    metadata_raw = data.get("metadata")
    if metadata_raw is None:
        metadata: dict[str, Any] = {}
    elif isinstance(metadata_raw, dict):
        # Check dangerous metadata keys
        dangerous_meta = set(metadata_raw.keys()) & DANGEROUS_METADATA_KEYS
        if dangerous_meta:
            raise PolicyCardUnsafeFieldError(
                f"dangerous metadata key(s): {', '.join(sorted(dangerous_meta))} — "
                f"metadata must not become a shadow control plane"
            )
        metadata = dict(metadata_raw)
    else:
        raise PolicyCardUnknownFieldError("metadata must be a mapping")

    card = PolicyCard(
        schema_version=schema_version,
        identity=identity,
        kind=kind,
        status=status,
        scope=scope,
        description=description,
        risk_binding=risk_binding,
        authority_binding=authority_binding,
        source=source,
        metadata=metadata,
    )

    # Run full validation
    result = validate_policy_card(card)
    if not result.valid:
        error_msgs = "; ".join(e.message for e in result.errors)
        raise PolicyCardUnknownFieldError(f"validation failed: {error_msgs}")

    return card
