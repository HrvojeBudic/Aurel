"""Source trust label taxonomy and deterministic hashes (P1.7.3)."""
from __future__ import annotations

from collections.abc import Mapping as MappingABC, Sequence
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping

from .errors import (
    PathGovernanceError,
    PathGovernanceErrorCode,
    PathGovernanceValidationError,
)
from .labels import ProjectionSourceLabel, SourceTrustLabel
from .serialization import stable_hash
from .validation import validate_known_fields

SOURCE_TRUST_TAXONOMY_TASK_ID = "P1.7.3"
SOURCE_TRUST_TAXONOMY_VERSION = "source_trust_taxonomy.v1"

TRUST_LABEL_DEFINITION_KNOWN_FIELDS: frozenset[str] = frozenset({
    "label",
    "definition",
    "default_posture",
    "allowed_interpretations",
    "forbidden_interpretations",
    "authority_statement",
    "requires_review_by_default",
    "definition_hash",
    "taxonomy_version",
    "metadata",
})

SOURCE_TRUST_TAXONOMY_KNOWN_FIELDS: frozenset[str] = frozenset({
    "taxonomy_version",
    "definitions",
    "taxonomy_hash",
    "source_label",
    "created_by_task",
    "notes",
    "metadata",
})


class TrustPosture(str, Enum):
    """Semantic grouping for trust labels; not resolver output or permission."""

    HIGH_CONFIDENCE = "HIGH_CONFIDENCE"
    OPERATOR_ANCHORED = "OPERATOR_ANCHORED"
    INTERNAL_CONTEXT = "INTERNAL_CONTEXT"
    LOCAL_CONTEXT = "LOCAL_CONTEXT"
    GENERATED_CONTEXT = "GENERATED_CONTEXT"
    EXTERNAL_CONTEXT = "EXTERNAL_CONTEXT"
    LOW_TRUST = "LOW_TRUST"
    UNKNOWN_TRUST = "UNKNOWN_TRUST"
    QUARANTINED_CONTEXT = "QUARANTINED_CONTEXT"


def _parse_trust_posture(value: TrustPosture | str) -> TrustPosture:
    if isinstance(value, TrustPosture):
        return value
    if isinstance(value, str):
        try:
            return TrustPosture(value)
        except ValueError as exc:
            raise PathGovernanceError(
                f"invalid default_posture: {value!r}",
                code=PathGovernanceErrorCode.INVALID_ENUM,
                field="default_posture",
            ) from exc
    raise PathGovernanceError(
        "default_posture must be a string or TrustPosture",
        code=PathGovernanceErrorCode.INVALID_ENUM,
        field="default_posture",
    )


def _parse_trust_label(value: SourceTrustLabel | str) -> SourceTrustLabel:
    if isinstance(value, SourceTrustLabel):
        return value
    if isinstance(value, str):
        try:
            return SourceTrustLabel(value)
        except ValueError as exc:
            raise PathGovernanceError(
                f"invalid label: {value!r}",
                code=PathGovernanceErrorCode.INVALID_TRUST_LABEL,
                field="label",
            ) from exc
    raise PathGovernanceError(
        "label must be a string or SourceTrustLabel",
        code=PathGovernanceErrorCode.INVALID_TRUST_LABEL,
        field="label",
    )


def _parse_source_label(value: ProjectionSourceLabel | str) -> ProjectionSourceLabel:
    if isinstance(value, ProjectionSourceLabel):
        return value
    if isinstance(value, str):
        try:
            return ProjectionSourceLabel(value)
        except ValueError as exc:
            raise PathGovernanceError(
                f"invalid source_label: {value!r}",
                code=PathGovernanceErrorCode.INVALID_SOURCE_LABEL,
                field="source_label",
            ) from exc
    raise PathGovernanceError(
        "source_label must be a string or ProjectionSourceLabel",
        code=PathGovernanceErrorCode.INVALID_SOURCE_LABEL,
        field="source_label",
    )


def _required_string(value: Any, *, field_name: str) -> str:
    if not isinstance(value, str) or value == "":
        raise PathGovernanceValidationError(
            f"{field_name} must be a non-empty string",
            code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
            field=field_name,
        )
    return value


def _freeze_strings(value: Sequence[str] | None, *, field_name: str) -> tuple[str, ...]:
    raw = () if value is None else value
    if isinstance(raw, str) or not isinstance(raw, Sequence):
        raise PathGovernanceValidationError(
            f"{field_name} must be a sequence of non-empty strings",
            code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
            field=field_name,
        )
    frozen = tuple(_required_string(item, field_name=field_name) for item in raw)
    if not frozen:
        raise PathGovernanceValidationError(
            f"{field_name} must be non-empty",
            code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
            field=field_name,
        )
    return frozen


def _freeze_optional_strings(
    value: Sequence[str] | None,
    *,
    field_name: str,
) -> tuple[str, ...]:
    raw = () if value is None else value
    if isinstance(raw, str) or not isinstance(raw, Sequence):
        raise PathGovernanceValidationError(
            f"{field_name} must be a sequence of strings",
            code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
            field=field_name,
        )
    return tuple(str(item) for item in raw)


def _freeze_metadata(metadata: Mapping[str, Any] | None) -> Mapping[str, Any]:
    raw = {} if metadata is None else metadata
    if not isinstance(raw, MappingABC):
        raise PathGovernanceValidationError(
            "metadata must be a mapping",
            code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
            field="metadata",
        )
    frozen = dict(raw)
    stable_hash(frozen)
    return MappingProxyType(frozen)


def _definition_hash_payload(
    *,
    label: SourceTrustLabel,
    definition: str,
    default_posture: TrustPosture,
    allowed_interpretations: tuple[str, ...],
    forbidden_interpretations: tuple[str, ...],
    authority_statement: str,
    requires_review_by_default: bool,
    taxonomy_version: str,
) -> dict[str, Any]:
    return {
        "allowed_interpretations": list(allowed_interpretations),
        "authority_statement": authority_statement,
        "default_posture": default_posture.value,
        "definition": definition,
        "forbidden_interpretations": list(forbidden_interpretations),
        "label": label.value,
        "requires_review_by_default": requires_review_by_default,
        "taxonomy_version": taxonomy_version,
    }


def compute_definition_hash(
    *,
    label: SourceTrustLabel,
    definition: str,
    default_posture: TrustPosture,
    allowed_interpretations: tuple[str, ...],
    forbidden_interpretations: tuple[str, ...],
    authority_statement: str,
    requires_review_by_default: bool,
    taxonomy_version: str = SOURCE_TRUST_TAXONOMY_VERSION,
) -> str:
    """Compute deterministic hash for a trust label definition."""
    return stable_hash(_definition_hash_payload(
        label=label,
        definition=definition,
        default_posture=default_posture,
        allowed_interpretations=allowed_interpretations,
        forbidden_interpretations=forbidden_interpretations,
        authority_statement=authority_statement,
        requires_review_by_default=requires_review_by_default,
        taxonomy_version=taxonomy_version,
    ))


@dataclass(frozen=True)
class TrustLabelDefinition:
    """Semantic definition for a SourceTrustLabel; it grants no authority."""

    label: SourceTrustLabel
    definition: str
    default_posture: TrustPosture
    allowed_interpretations: tuple[str, ...]
    forbidden_interpretations: tuple[str, ...]
    authority_statement: str
    requires_review_by_default: bool
    definition_hash: str = ""
    taxonomy_version: str = SOURCE_TRUST_TAXONOMY_VERSION
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        label = _parse_trust_label(self.label)
        default_posture = _parse_trust_posture(self.default_posture)
        definition = _required_string(self.definition, field_name="definition")
        allowed_interpretations = _freeze_strings(
            self.allowed_interpretations,
            field_name="allowed_interpretations",
        )
        forbidden_interpretations = _freeze_strings(
            self.forbidden_interpretations,
            field_name="forbidden_interpretations",
        )
        authority_statement = _required_string(
            self.authority_statement,
            field_name="authority_statement",
        )
        if not isinstance(self.requires_review_by_default, bool):
            raise PathGovernanceValidationError(
                "requires_review_by_default must be boolean",
                code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
                field="requires_review_by_default",
            )
        if self.taxonomy_version != SOURCE_TRUST_TAXONOMY_VERSION:
            raise PathGovernanceValidationError(
                "taxonomy_version must be source_trust_taxonomy.v1",
                code=PathGovernanceErrorCode.INVALID_VERSION,
                field="taxonomy_version",
            )
        metadata = _freeze_metadata(self.metadata)
        definition_hash = compute_definition_hash(
            label=label,
            definition=definition,
            default_posture=default_posture,
            allowed_interpretations=allowed_interpretations,
            forbidden_interpretations=forbidden_interpretations,
            authority_statement=authority_statement,
            requires_review_by_default=self.requires_review_by_default,
            taxonomy_version=self.taxonomy_version,
        )
        if self.definition_hash not in ("", definition_hash):
            raise PathGovernanceValidationError(
                "definition_hash does not match definition content",
                code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
                field="definition_hash",
            )
        object.__setattr__(self, "label", label)
        object.__setattr__(self, "default_posture", default_posture)
        object.__setattr__(self, "definition", definition)
        object.__setattr__(self, "allowed_interpretations", allowed_interpretations)
        object.__setattr__(self, "forbidden_interpretations", forbidden_interpretations)
        object.__setattr__(self, "authority_statement", authority_statement)
        object.__setattr__(self, "definition_hash", definition_hash)
        object.__setattr__(self, "metadata", metadata)

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "allowed_interpretations": list(self.allowed_interpretations),
            "authority_statement": self.authority_statement,
            "default_posture": self.default_posture.value,
            "definition": self.definition,
            "definition_hash": self.definition_hash,
            "forbidden_interpretations": list(self.forbidden_interpretations),
            "label": self.label.value,
            "metadata": dict(sorted(self.metadata.items(), key=lambda item: item[0])),
            "requires_review_by_default": self.requires_review_by_default,
            "taxonomy_version": self.taxonomy_version,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> TrustLabelDefinition:
        validate_known_fields(
            data,
            TRUST_LABEL_DEFINITION_KNOWN_FIELDS,
            label="trust_label_definition",
        )
        return cls(
            label=data["label"],
            definition=data["definition"],
            default_posture=data["default_posture"],
            allowed_interpretations=data["allowed_interpretations"],
            forbidden_interpretations=data["forbidden_interpretations"],
            authority_statement=data["authority_statement"],
            requires_review_by_default=data["requires_review_by_default"],
            definition_hash=data.get("definition_hash", ""),
            taxonomy_version=data.get("taxonomy_version", SOURCE_TRUST_TAXONOMY_VERSION),
            metadata=data.get("metadata", {}),
        )


def compute_taxonomy_hash(
    *,
    taxonomy_version: str,
    definitions: Sequence[TrustLabelDefinition],
    created_by_task: str,
) -> str:
    """Compute deterministic order-insensitive taxonomy hash."""
    return stable_hash({
        "created_by_task": created_by_task,
        "definition_hashes": [
            {
                "definition_hash": definition.definition_hash,
                "label": definition.label.value,
            }
            for definition in sorted(definitions, key=lambda item: item.label.value)
        ],
        "taxonomy_version": taxonomy_version,
    })


@dataclass(frozen=True)
class SourceTrustTaxonomy:
    """Stable taxonomy for SourceTrustLabel meanings; not a resolver."""

    definitions: tuple[TrustLabelDefinition, ...]
    taxonomy_hash: str = ""
    taxonomy_version: str = SOURCE_TRUST_TAXONOMY_VERSION
    source_label: ProjectionSourceLabel = ProjectionSourceLabel.LIVE
    created_by_task: str = SOURCE_TRUST_TAXONOMY_TASK_ID
    notes: tuple[str, ...] = field(default_factory=tuple)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.taxonomy_version != SOURCE_TRUST_TAXONOMY_VERSION:
            raise PathGovernanceValidationError(
                "taxonomy_version must be source_trust_taxonomy.v1",
                code=PathGovernanceErrorCode.INVALID_VERSION,
                field="taxonomy_version",
            )
        if self.created_by_task != SOURCE_TRUST_TAXONOMY_TASK_ID:
            raise PathGovernanceValidationError(
                "created_by_task must be P1.7.3",
                code=PathGovernanceErrorCode.INVALID_VERSION,
                field="created_by_task",
            )
        definitions = tuple(self.definitions)
        if not definitions or not all(
            isinstance(item, TrustLabelDefinition) for item in definitions
        ):
            raise PathGovernanceValidationError(
                "definitions must be a non-empty sequence of TrustLabelDefinition objects",
                code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
                field="definitions",
            )
        labels = [definition.label for definition in definitions]
        if len(labels) != len(set(labels)):
            raise PathGovernanceValidationError(
                "definitions must contain exactly one entry for each SourceTrustLabel",
                code=PathGovernanceErrorCode.INVALID_TRUST_LABEL,
                field="definitions",
            )
        expected = set(SourceTrustLabel)
        if set(labels) != expected:
            missing = sorted(label.value for label in expected - set(labels))
            extra = sorted(label.value for label in set(labels) - expected)
            raise PathGovernanceValidationError(
                "definitions must cover every SourceTrustLabel exactly once",
                code=PathGovernanceErrorCode.INVALID_TRUST_LABEL,
                field="definitions",
                details={"missing": missing, "extra": extra},
            )
        source_label = _parse_source_label(self.source_label)
        notes = _freeze_optional_strings(self.notes, field_name="notes")
        metadata = _freeze_metadata(self.metadata)
        taxonomy_hash = compute_taxonomy_hash(
            taxonomy_version=self.taxonomy_version,
            definitions=definitions,
            created_by_task=self.created_by_task,
        )
        if self.taxonomy_hash not in ("", taxonomy_hash):
            raise PathGovernanceValidationError(
                "taxonomy_hash does not match taxonomy content",
                code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
                field="taxonomy_hash",
            )
        object.__setattr__(
            self,
            "definitions",
            tuple(sorted(definitions, key=lambda item: item.label.value)),
        )
        object.__setattr__(self, "source_label", source_label)
        object.__setattr__(self, "notes", notes)
        object.__setattr__(self, "metadata", metadata)
        object.__setattr__(self, "taxonomy_hash", taxonomy_hash)

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "created_by_task": self.created_by_task,
            "definitions": [
                definition.to_canonical_dict() for definition in self.definitions
            ],
            "metadata": dict(sorted(self.metadata.items(), key=lambda item: item[0])),
            "notes": list(self.notes),
            "source_label": self.source_label.value,
            "taxonomy_hash": self.taxonomy_hash,
            "taxonomy_version": self.taxonomy_version,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> SourceTrustTaxonomy:
        validate_known_fields(
            data,
            SOURCE_TRUST_TAXONOMY_KNOWN_FIELDS,
            label="source_trust_taxonomy",
        )
        definitions_raw = data["definitions"]
        if isinstance(definitions_raw, str) or not isinstance(definitions_raw, Sequence):
            raise PathGovernanceValidationError(
                "definitions must be a sequence",
                code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
                field="definitions",
            )
        return cls(
            definitions=tuple(
                item if isinstance(item, TrustLabelDefinition)
                else TrustLabelDefinition.from_dict(item)
                for item in definitions_raw
            ),
            taxonomy_hash=data.get("taxonomy_hash", ""),
            taxonomy_version=data.get(
                "taxonomy_version",
                SOURCE_TRUST_TAXONOMY_VERSION,
            ),
            source_label=data.get("source_label", ProjectionSourceLabel.LIVE),
            created_by_task=data.get(
                "created_by_task",
                SOURCE_TRUST_TAXONOMY_TASK_ID,
            ),
            notes=data.get("notes", ()),
            metadata=data.get("metadata", {}),
        )


def _definition(
    *,
    label: SourceTrustLabel,
    definition: str,
    default_posture: TrustPosture,
    allowed_interpretations: tuple[str, ...],
    forbidden_interpretations: tuple[str, ...],
    authority_statement: str,
    requires_review_by_default: bool,
) -> TrustLabelDefinition:
    return TrustLabelDefinition(
        label=label,
        definition=definition,
        default_posture=default_posture,
        allowed_interpretations=allowed_interpretations,
        forbidden_interpretations=forbidden_interpretations,
        authority_statement=authority_statement,
        requires_review_by_default=requires_review_by_default,
    )


def _default_definitions() -> tuple[TrustLabelDefinition, ...]:
    return (
        _definition(
            label=SourceTrustLabel.TRUSTED,
            definition=(
                "Source is explicitly trusted by policy/context or "
                "operator-controlled governance state."
            ),
            default_posture=TrustPosture.HIGH_CONFIDENCE,
            allowed_interpretations=(
                "may be treated as higher-confidence context",
                "may be used as internal reference if other policy allows",
                "may be cited with trust label",
            ),
            forbidden_interpretations=(
                "may bypass policy",
                "may grant tool permission",
                "may override operator authority",
                "may write memory automatically",
                "may command the agent without resolver approval",
                "may execute code or mutate state by label alone",
            ),
            authority_statement="TRUSTED does not mean unlimited authority.",
            requires_review_by_default=False,
        ),
        _definition(
            label=SourceTrustLabel.OPERATOR_PROVIDED,
            definition="Source was directly provided by the human operator.",
            default_posture=TrustPosture.OPERATOR_ANCHORED,
            allowed_interpretations=(
                "may be treated as operator-provided context",
                "may be prioritized in context assembly if other policy allows",
                "may be cited as operator-provided",
            ),
            forbidden_interpretations=(
                "may override system/developer/governance policy",
                "may expand tool permissions",
                "may bypass approval",
                "may canonize memory automatically",
                "may command external action without resolver approval",
            ),
            authority_statement="OPERATOR_PROVIDED does not override policy.",
            requires_review_by_default=False,
        ),
        _definition(
            label=SourceTrustLabel.INTERNAL_REPO,
            definition="Source originates from controlled repository context.",
            default_posture=TrustPosture.INTERNAL_CONTEXT,
            allowed_interpretations=(
                "may be used as repository context",
                "may be cited as internal repo source",
                "may inform code/docs reasoning",
            ),
            forbidden_interpretations=(
                "may be executed because it is internal",
                "may be trusted as correct without verification",
                "may override operator authority",
                "may expand permissions",
                "may bypass sandbox or tests",
            ),
            authority_statement="INTERNAL_REPO does not mean executable-safe.",
            requires_review_by_default=False,
        ),
        _definition(
            label=SourceTrustLabel.LOCAL_PRIVATE,
            definition="Source originates from local/private machine context.",
            default_posture=TrustPosture.LOCAL_CONTEXT,
            allowed_interpretations=(
                "may be treated as local/private context",
                "may be cited internally if policy allows",
                "may require privacy-aware handling later",
            ),
            forbidden_interpretations=(
                "may be exposed externally",
                "may be sent to network services automatically",
                "may be written into shared memory automatically",
                "may grant authority because it is local",
                "may bypass privacy/data residency policy",
            ),
            authority_statement="LOCAL_PRIVATE does not mean safe to expose.",
            requires_review_by_default=True,
        ),
        _definition(
            label=SourceTrustLabel.TOOL_GENERATED,
            definition="Source was produced by a governed tool or tool-like process.",
            default_posture=TrustPosture.GENERATED_CONTEXT,
            allowed_interpretations=(
                "may be treated as tool output",
                "may be cited with tool-generated label",
                "may be verified against tool contract if available later",
            ),
            forbidden_interpretations=(
                "may be assumed true",
                "may override policy",
                "may grant memory authority",
                "may command another tool automatically",
                "may bypass validation",
            ),
            authority_statement="TOOL_GENERATED does not mean true.",
            requires_review_by_default=False,
        ),
        _definition(
            label=SourceTrustLabel.EXTERNAL,
            definition=(
                "Source originated outside local/repo/operator-governed boundary."
            ),
            default_posture=TrustPosture.EXTERNAL_CONTEXT,
            allowed_interpretations=(
                "may be identified",
                "may be summarized",
                "may be quoted",
                "may be cited with external label",
                "may inform reasoning as untrusted external context",
            ),
            forbidden_interpretations=(
                "may command the agent",
                "may override authority",
                "may grant permissions",
                "may write memory without review",
                "may redefine policy",
                "may be treated as internal truth",
            ),
            authority_statement="EXTERNAL may inform but cannot command.",
            requires_review_by_default=True,
        ),
        _definition(
            label=SourceTrustLabel.UNTRUSTED,
            definition="Source is known or classified as untrusted.",
            default_posture=TrustPosture.LOW_TRUST,
            allowed_interpretations=(
                "may be identified",
                "may be quoted with label",
                "may be summarized defensively",
                "may be used as evidence of an attempted instruction or claim",
            ),
            forbidden_interpretations=(
                "may command the agent",
                "may grant authority",
                "may write memory without review",
                "may alter policy",
                "may be used as trusted prompt instruction",
                "may expand tool permission",
            ),
            authority_statement=(
                "UNTRUSTED can be read or cited defensively, but cannot command."
            ),
            requires_review_by_default=True,
        ),
        _definition(
            label=SourceTrustLabel.UNKNOWN,
            definition="Source trust cannot be confidently classified.",
            default_posture=TrustPosture.UNKNOWN_TRUST,
            allowed_interpretations=(
                "may be represented explicitly as unknown",
                "may be inspected later",
                "may be handled conservatively by future resolver",
            ),
            forbidden_interpretations=(
                "may be silently treated as trusted",
                "may command the agent",
                "may grant permissions",
                "may write memory without review",
                "may override authority",
            ),
            authority_statement="UNKNOWN is explicit uncertainty, not implicit trust.",
            requires_review_by_default=True,
        ),
        _definition(
            label=SourceTrustLabel.QUARANTINED,
            definition=(
                "Source is isolated/restricted from authority-bearing use until "
                "reviewed or released."
            ),
            default_posture=TrustPosture.QUARANTINED_CONTEXT,
            allowed_interpretations=(
                "may be stored as quarantined reference if policy allows",
                "may be inspected in safe context",
                "may be used as evidence of blocked/unsafe/unreviewed input",
                "may be kept for audit if allowed",
            ),
            forbidden_interpretations=(
                "may command the agent",
                "may enter ordinary prompt context",
                "may write memory as canon",
                "may grant permissions",
                "may be executed",
                "may be silently deleted without policy if audit retention applies",
            ),
            authority_statement="QUARANTINED means restricted, not deleted.",
            requires_review_by_default=True,
        ),
    )


def build_source_trust_taxonomy(
    source_label: ProjectionSourceLabel = ProjectionSourceLabel.LIVE,
    metadata: Mapping[str, Any] | None = None,
) -> SourceTrustTaxonomy:
    """Build deterministic source trust taxonomy without resolving trust."""
    return SourceTrustTaxonomy(
        definitions=_default_definitions(),
        source_label=source_label,
        notes=(
            "P1.7.3 taxonomy defines source trust label meaning only.",
            "A trust label is not permission, command authority, prompt authority, "
            "memory authority, or resolver output.",
        ),
        metadata=metadata,
    )
