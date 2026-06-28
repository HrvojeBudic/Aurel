"""Output Passport foundation contracts (P1.9-A / P1.9.0-P1.9.7).

Contract-only layer: passport identity, attribution, disclosure, reference
binding, uncertainty fields, and deterministic hash without verification,
enforcement, memory access, trace/Ledger writes, or runtime generation.

Architectural law:
  - Output is not proof.
  - Passport is not verification.
  - Attribution is not trust.
  - TraceRef is not TRACE_VERIFIED.
  - EvidenceRef is not evidence finality.
  - Memory influence disclosure is not memory read permission.
  - Hash is not truth.
  - Disclosure is not permission.
  - Passport is not Ledger.
"""
from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field, fields, is_dataclass
from enum import Enum
from typing import Any, TypeVar

OUTPUT_PASSPORT_PACK_TASK_ID = "P1.9-A"
OUTPUT_PASSPORT_SECTION_ID = "P1.9"
OUTPUT_PASSPORT_PACK_CHECKPOINT_IDS = (
    "P1.9.0",
    "P1.9.1",
    "P1.9.2",
    "P1.9.3",
    "P1.9.4",
    "P1.9.5",
    "P1.9.6",
    "P1.9.7",
)
OUTPUT_PASSPORT_NEXT_PACK_ID = "P1.9-B"
OUTPUT_PASSPORT_MODULE_NAME = "output_passport"
OUTPUT_PASSPORT_SCHEMA_VERSION = "output_passport_foundation.v1"
OUTPUT_PASSPORT_FOUNDATION_VERSION = "output_passport_foundation.v1"
OUTPUT_PASSPORT_IDENTITY_VERSION = "output_passport_identity.v1"
OUTPUT_PASSPORT_ATTRIBUTION_VERSION = "output_passport_attribution.v1"
OUTPUT_PASSPORT_AUTHORITY_POLICY_RISK_VERSION = (
    "output_passport_authority_policy_risk.v1"
)
OUTPUT_PASSPORT_MEMORY_INFLUENCE_VERSION = "output_passport_memory_influence.v1"
OUTPUT_PASSPORT_EVIDENCE_TRACE_BINDING_VERSION = (
    "output_passport_evidence_trace_binding.v1"
)
OUTPUT_PASSPORT_UNCERTAINTY_VERSION = "output_passport_uncertainty.v1"
OUTPUT_PASSPORT_HASH_CONTRACT_VERSION = "output_passport_hash_contract.v1"
OUTPUT_PASSPORT_PAYLOAD_VERSION = "output_passport_payload.v1"
OUTPUT_PASSPORT_PACK_RESULT_VERSION = "output_passport_pack_result.v1"

OUTPUT_PASSPORT_HASH_VOLATILE_FIELDS: frozenset[str] = frozenset({
    "payload_hash",
    "computed_at",
    "result_hash",
    "identity_hash",
    "foundation_hash",
    "attribution_envelope_hash",
    "authority_policy_risk_hash",
    "memory_influence_hash",
    "evidence_trace_binding_hash",
    "uncertainty_envelope_hash",
    "hash_contract_hash",
})

OUTPUT_PASSPORT_UNAVAILABLE_BINDINGS: dict[str, str] = {
    "CLI/Shell/TUI Binding": (
        "CLI/Shell/TUI binding scheduled for P1.9.28; not available in P1.9-A"
    ),
    "Projection/API/Event Contract": (
        "Projection/API/event contract scheduled for P1.9.27; not P1.9-A"
    ),
    "Ledger Write": "Ledger write is not available in P1.9-A foundation",
    "Global Trace Write": (
        "Global trace spine write is not available in P1.9-A foundation"
    ),
    "Trace Verification": (
        "TRACE_VERIFIED is not available in P1.9-A; refs are reference-only"
    ),
    "Evidence Finality": (
        "Evidence finality is not available in P1.9-A; refs are reference-only"
    ),
    "Memory Read/Write": (
        "Memory read/write is not available in P1.9-A; influence is disclosure-only"
    ),
    "Policy/Custos Enforcement": (
        "Policy/Custos enforcement is not available in P1.9-A foundation"
    ),
    "Live Passport Generation": (
        "Live runtime passport generation is not available in P1.9-A"
    ),
    "Passport Verification": (
        "Passport verification is not available in P1.9-A foundation"
    ),
}


class OutputPassportErrorCode(str, Enum):
    OUTPUT_PASSPORT_UNAVAILABLE = "OUTPUT_PASSPORT_UNAVAILABLE"
    UNKNOWN_FIELD = "UNKNOWN_FIELD"
    INVALID_ENUM = "INVALID_ENUM"
    INVALID_VERSION = "INVALID_VERSION"
    INVALID_SOURCE_LABEL = "INVALID_SOURCE_LABEL"
    SERIALIZATION_ERROR = "SERIALIZATION_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    FORBIDDEN_VERIFICATION_LABEL = "FORBIDDEN_VERIFICATION_LABEL"


@dataclass(frozen=True)
class OutputPassportStructuredError:
    code: OutputPassportErrorCode
    message: str
    field: str | None = None
    details: dict[str, Any] | None = None


class OutputPassportError(ValueError):
    """Base error for output passport operations."""

    def __init__(
        self,
        message: str,
        *,
        code: OutputPassportErrorCode | None = None,
        field: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.field = field
        self.details = details

    def to_structured(self) -> OutputPassportStructuredError:
        return OutputPassportStructuredError(
            code=self.code or OutputPassportErrorCode.OUTPUT_PASSPORT_UNAVAILABLE,
            message=str(self),
            field=self.field,
            details=self.details,
        )


class OutputPassportValidationError(OutputPassportError):
    """Raised when output passport payload fails closed-world or enum validation."""


class OutputPassportUnknownFieldError(OutputPassportValidationError):
    """Raised when unknown fields appear in closed-world factory inputs."""


class OutputPassportSourceLabel(str, Enum):
    """Source label for output passport contract data."""

    DEV_FIXTURE = "DEV_FIXTURE"
    CONTRACT_ONLY = "CONTRACT_ONLY"
    REFERENCE_ONLY = "REFERENCE_ONLY"
    UNAVAILABLE = "UNAVAILABLE"
    UNKNOWN = "UNKNOWN"


class OutputPassportTruthLabel(str, Enum):
    """Truth label for output passport contract data."""

    CONTRACT_ONLY = "CONTRACT_ONLY"
    DEV_FIXTURE = "DEV_FIXTURE"
    DISCLOSURE_ONLY = "DISCLOSURE_ONLY"
    REFERENCE_ONLY = "REFERENCE_ONLY"
    DETERMINISTIC_PAYLOAD_HASH = "DETERMINISTIC_PAYLOAD_HASH"
    NOT_VERIFIED = "NOT_VERIFIED"
    VERIFICATION_UNAVAILABLE = "VERIFICATION_UNAVAILABLE"
    UNAVAILABLE_TRACE_VERIFICATION = "UNAVAILABLE_TRACE_VERIFICATION"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"
    DECLARED_ATTRIBUTION = "DECLARED_ATTRIBUTION"
    UNAVAILABLE_ATTRIBUTION = "UNAVAILABLE_ATTRIBUTION"
    MEMORY_INFLUENCE_DECLARED = "MEMORY_INFLUENCE_DECLARED"
    MEMORY_INFLUENCE_UNAVAILABLE = "MEMORY_INFLUENCE_UNAVAILABLE"
    UNAVAILABLE_POLICY_CONTEXT = "UNAVAILABLE_POLICY_CONTEXT"
    READ_MODEL_ONLY = "READ_MODEL_ONLY"
    VERIFICATION_CONTRACT_ONLY = "VERIFICATION_CONTRACT_ONLY"
    TEST_HARNESS_ONLY = "TEST_HARNESS_ONLY"
    REVIEW_STATE_ONLY = "REVIEW_STATE_ONLY"
    LIVE = "LIVE"
    TRACE_VERIFIED = "TRACE_VERIFIED"
    LEDGER_VERIFIED = "LEDGER_VERIFIED"
    EVIDENCE_FINAL = "EVIDENCE_FINAL"


FORBIDDEN_DEFAULT_TRUTH_LABELS: frozenset[OutputPassportTruthLabel] = frozenset({
    OutputPassportTruthLabel.LIVE,
    OutputPassportTruthLabel.TRACE_VERIFIED,
    OutputPassportTruthLabel.LEDGER_VERIFIED,
    OutputPassportTruthLabel.EVIDENCE_FINAL,
})


class OutputPassportVerificationStatus(str, Enum):
    """Verification status for passport components."""

    NOT_VERIFIED = "NOT_VERIFIED"
    VERIFICATION_UNAVAILABLE = "VERIFICATION_UNAVAILABLE"
    REFERENCE_ONLY = "REFERENCE_ONLY"
    CONTRACT_ONLY = "CONTRACT_ONLY"
    VERIFICATION_ERROR = "VERIFICATION_ERROR"
    VERIFIED = "VERIFIED"


class OutputPassportUnavailableReason(str, Enum):
    """Closed-world unavailable reason taxonomy."""

    READ_MODEL_UNAVAILABLE = "READ_MODEL_UNAVAILABLE"
    VERIFICATION_UNAVAILABLE = "VERIFICATION_UNAVAILABLE"
    CLI_SHELL_TUI_UNAVAILABLE = "CLI_SHELL_TUI_UNAVAILABLE"
    PROJECTION_UNAVAILABLE = "PROJECTION_UNAVAILABLE"
    TRACE_VERIFICATION_UNAVAILABLE = "TRACE_VERIFICATION_UNAVAILABLE"
    LEDGER_FINALITY_UNAVAILABLE = "LEDGER_FINALITY_UNAVAILABLE"
    EVIDENCE_FINALITY_UNAVAILABLE = "EVIDENCE_FINALITY_UNAVAILABLE"
    MEMORY_ACCESS_UNAVAILABLE = "MEMORY_ACCESS_UNAVAILABLE"
    POLICY_CONTEXT_UNAVAILABLE = "POLICY_CONTEXT_UNAVAILABLE"
    AUTHORITY_CONTEXT_UNAVAILABLE = "AUTHORITY_CONTEXT_UNAVAILABLE"
    RUNTIME_GENERATION_UNAVAILABLE = "RUNTIME_GENERATION_UNAVAILABLE"
    ATTRIBUTION_UNAVAILABLE = "ATTRIBUTION_UNAVAILABLE"
    UNAVAILABLE_BUSINESS_CONTEXT = "UNAVAILABLE_BUSINESS_CONTEXT"
    UNAVAILABLE_WORKFLOW_CONTEXT = "UNAVAILABLE_WORKFLOW_CONTEXT"
    UNAVAILABLE_AGENT_CONTEXT = "UNAVAILABLE_AGENT_CONTEXT"
    UNAVAILABLE_TOOL_CONTEXT = "UNAVAILABLE_TOOL_CONTEXT"
    SUPPORT_DISCLOSURE_UNAVAILABLE = "SUPPORT_DISCLOSURE_UNAVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"
    UNKNOWN = "UNKNOWN"


class OutputPassportDisclosureKind(str, Enum):
    """Disclosure category for passport envelopes."""

    PROVENANCE = "provenance"
    ATTRIBUTION = "attribution"
    AUTHORITY = "authority"
    POLICY = "policy"
    RISK = "risk"
    MEMORY_INFLUENCE = "memory_influence"
    EVIDENCE_TRACE = "evidence_trace"
    UNCERTAINTY = "uncertainty"
    REFERENCE_ONLY = "reference_only"
    UNKNOWN = "unknown"


class OutputPassportActorKind(str, Enum):
    """Actor taxonomy for output attribution."""

    OPERATOR = "operator"
    ACTOR = "actor"
    SYSTEM = "system"
    COMPONENT = "component"
    UNKNOWN = "unknown"
    UNAVAILABLE = "unavailable"


class OutputPassportAttributionKind(str, Enum):
    """Attribution status taxonomy."""

    DECLARED = "declared"
    UNAVAILABLE = "unavailable"
    UNKNOWN = "unknown"
    NOT_APPLICABLE = "not_applicable"


class OutputPassportRiskTier(str, Enum):
    """Risk tier for disclosure (closed-world)."""

    R0 = "R0"
    R1 = "R1"
    R2 = "R2"
    R3 = "R3"
    R4 = "R4"
    R5 = "R5"
    R6 = "R6"
    UNKNOWN = "unknown"
    UNAVAILABLE = "unavailable"


class OutputPassportInfluenceStatus(str, Enum):
    """Memory influence disclosure status."""

    DECLARED = "declared"
    NONE_DECLARED = "none_declared"
    UNAVAILABLE = "unavailable"
    REDACTED = "redacted"
    UNKNOWN = "unknown"
    NOT_APPLICABLE = "not_applicable"


class OutputPassportReferenceKind(str, Enum):
    """Reference kind for evidence/trace binding."""

    EVIDENCE_REF = "evidence_ref"
    TRACE_REF = "trace_ref"
    BOTH = "both"
    NONE = "none"
    REFERENCE_ONLY = "reference_only"
    UNKNOWN = "unknown"


class OutputPassportReferenceStatus(str, Enum):
    """Reference attachment status."""

    REFERENCE_ATTACHED = "reference_attached"
    VERIFICATION_UNAVAILABLE = "verification_unavailable"
    NOT_VERIFIED = "not_verified"
    UNAVAILABLE = "unavailable"
    UNKNOWN = "unknown"


class OutputPassportAuthorizationStatus(str, Enum):
    """Authorization disclosure status (disclosure only, not grant)."""

    NOT_AUTHORIZED = "not_authorized"
    DISCLOSURE_ONLY = "disclosure_only"
    UNAVAILABLE = "unavailable"
    UNKNOWN = "unknown"


class OutputPassportUncertaintyLevel(str, Enum):
    """Uncertainty level taxonomy."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    UNKNOWN = "unknown"
    UNAVAILABLE = "unavailable"


class OutputPassportCheckpointStatus(str, Enum):
    """Pack checkpoint completion status."""

    DONE = "DONE"
    PARTIAL = "PARTIAL"
    NOT_DONE = "NOT_DONE"
    BLOCKED = "BLOCKED"
    UNAVAILABLE = "UNAVAILABLE"


OUTPUT_PASSPORT_UNAVAILABLE_REASON_DETAILS: dict[str, str] = {
    OutputPassportUnavailableReason.READ_MODEL_UNAVAILABLE.value: (
        "Output Passport read model is UNAVAILABLE in P1.9-A; owned by P1.9.8."
    ),
    OutputPassportUnavailableReason.VERIFICATION_UNAVAILABLE.value: (
        "Output Passport verification is UNAVAILABLE in P1.9-A; owned by P1.9.9."
    ),
    OutputPassportUnavailableReason.CLI_SHELL_TUI_UNAVAILABLE.value: (
        "CLI/Shell/TUI binding is UNAVAILABLE in P1.9-A; owned by P1.9.28."
    ),
    OutputPassportUnavailableReason.PROJECTION_UNAVAILABLE.value: (
        "Projection/API/event contract is UNAVAILABLE in P1.9-A; owned by P1.9.27."
    ),
    OutputPassportUnavailableReason.TRACE_VERIFICATION_UNAVAILABLE.value: (
        "TRACE_VERIFIED is UNAVAILABLE in P1.9-A; trace refs are reference-only."
    ),
    OutputPassportUnavailableReason.LEDGER_FINALITY_UNAVAILABLE.value: (
        "Ledger finality is UNAVAILABLE in P1.9-A; passport is not Ledger."
    ),
    OutputPassportUnavailableReason.EVIDENCE_FINALITY_UNAVAILABLE.value: (
        "Evidence finality is UNAVAILABLE in P1.9-A; evidence refs are reference-only."
    ),
    OutputPassportUnavailableReason.MEMORY_ACCESS_UNAVAILABLE.value: (
        "Memory read/write is UNAVAILABLE in P1.9-A; influence is disclosure-only."
    ),
    OutputPassportUnavailableReason.POLICY_CONTEXT_UNAVAILABLE.value: (
        "Policy context may be unavailable; disclosure does not enforce policy."
    ),
    OutputPassportUnavailableReason.AUTHORITY_CONTEXT_UNAVAILABLE.value: (
        "Authority context may be unavailable; disclosure does not grant authority."
    ),
    OutputPassportUnavailableReason.RUNTIME_GENERATION_UNAVAILABLE.value: (
        "Live runtime passport generation is UNAVAILABLE in P1.9-A."
    ),
    OutputPassportUnavailableReason.ATTRIBUTION_UNAVAILABLE.value: (
        "Attribution may be unavailable; unavailable must be explicit."
    ),
}

DEFAULT_OUTPUT_PASSPORT_UNAVAILABLE_REASONS = tuple(
    OutputPassportUnavailableReason(reason)
    for reason in OUTPUT_PASSPORT_UNAVAILABLE_REASON_DETAILS
)

FOUNDATION_INVARIANTS = (
    "Passport is structured disclosure, not proof.",
    "Provenance is represented without verification overclaim.",
    "Disclosure is represented without permission grant.",
    "Side-effect proof exists and all booleans are false by default.",
)


class _CanonicalMixin:
    def to_canonical_dict(self) -> dict[str, Any]:
        return _canonical_dataclass_dict(self)


@dataclass(frozen=True)
class OutputPassportSideEffectProof(_CanonicalMixin):
    """Proof that P1.9-A performs no authority/verification/mutation side effects."""

    ledger_written: bool = False
    global_trace_written: bool = False
    trace_verified: bool = False
    evidence_finalized: bool = False
    memory_read: bool = False
    memory_written: bool = False
    policy_enforced: bool = False
    custos_called: bool = False
    authority_granted: bool = False
    approval_created: bool = False
    tool_executed: bool = False
    workflow_mutated: bool = False
    runtime_mutated: bool = False
    passport_verified: bool = False
    live_passport_generated: bool = False
    disclosure_grants_permission: bool = False
    business_action_executed: bool = False
    workflow_executed: bool = False
    agent_executed: bool = False
    agent_authority_created: bool = False
    tool_permission_granted: bool = False


@dataclass(frozen=True)
class OutputPassportBoundary(_CanonicalMixin):
    """Explicit boundary invariants for output passport semantics."""

    passport_is_proof: bool = False
    passport_is_verification: bool = False
    attribution_is_trust: bool = False
    trace_ref_is_trace_verified: bool = False
    evidence_ref_is_finality: bool = False
    hash_is_truth: bool = False
    passport_is_ledger: bool = False
    disclosure_is_permission: bool = False


@dataclass(frozen=True)
class OutputPassportFoundation(_CanonicalMixin):
    """P1.9.0 foundation: provenance/disclosure semantics without verification."""

    schema_version: str
    checkpoint_id: str
    purpose: str
    provenance_meaning: str
    disclosure_meaning: str
    truth_label: OutputPassportTruthLabel
    verification_status: OutputPassportVerificationStatus
    boundary: OutputPassportBoundary
    source_label: OutputPassportSourceLabel
    unavailable_bindings: Mapping[str, str]
    invariants: tuple[str, ...]
    side_effects: OutputPassportSideEffectProof
    foundation_hash: str


@dataclass(frozen=True)
class OutputPassportVersion(_CanonicalMixin):
    """Version descriptor for output passport identity."""

    major: int
    minor: int
    patch: int
    schema_version: str
    version_label: str


@dataclass(frozen=True)
class OutputPassportSubjectRef(_CanonicalMixin):
    """Passive subject/output reference."""

    subject_ref_id: str
    output_ref: str
    subject_kind: str
    source_label: OutputPassportSourceLabel


@dataclass(frozen=True)
class OutputPassportIdentity(_CanonicalMixin):
    """P1.9.1 identity model for output passport."""

    schema_version: str
    checkpoint_id: str
    passport_id: str
    passport_version: OutputPassportVersion
    subject_ref: OutputPassportSubjectRef
    generation_context_ref: str
    truth_label: OutputPassportTruthLabel
    verification_status: OutputPassportVerificationStatus
    source_label: OutputPassportSourceLabel
    identity_hash: str


@dataclass(frozen=True)
class OutputActorAttribution(_CanonicalMixin):
    """Declared actor attribution."""

    attribution_kind: OutputPassportAttributionKind
    actor_kind: OutputPassportActorKind
    actor_ref: str
    display_name: str
    truth_label: OutputPassportTruthLabel
    source_label: OutputPassportSourceLabel


@dataclass(frozen=True)
class OutputAgentAttribution(_CanonicalMixin):
    """Declared agent attribution."""

    attribution_kind: OutputPassportAttributionKind
    agent_ref: str
    agent_id: str
    truth_label: OutputPassportTruthLabel
    source_label: OutputPassportSourceLabel


@dataclass(frozen=True)
class OutputModelAttribution(_CanonicalMixin):
    """Declared model attribution."""

    attribution_kind: OutputPassportAttributionKind
    model_ref: str
    model_id: str
    provider_ref: str
    truth_label: OutputPassportTruthLabel
    source_label: OutputPassportSourceLabel


@dataclass(frozen=True)
class OutputToolAttribution(_CanonicalMixin):
    """Declared tool attribution."""

    attribution_kind: OutputPassportAttributionKind
    tool_ref: str
    tool_id: str
    truth_label: OutputPassportTruthLabel
    source_label: OutputPassportSourceLabel


@dataclass(frozen=True)
class OutputPassportAttributionEnvelope(_CanonicalMixin):
    """P1.9.2 attribution envelope for actor/agent/model/tool contributors."""

    schema_version: str
    checkpoint_id: str
    actor_attribution: OutputActorAttribution
    agent_attribution: OutputAgentAttribution
    model_attribution: OutputModelAttribution
    tool_attribution: OutputToolAttribution
    unknown_attribution_declared: bool
    truth_label: OutputPassportTruthLabel
    source_label: OutputPassportSourceLabel
    invariants: tuple[str, ...]
    attribution_envelope_hash: str


@dataclass(frozen=True)
class AuthorityContextRef(_CanonicalMixin):
    """Passive authority context reference."""

    authority_context_ref_id: str
    authority_basis: str
    source_label: OutputPassportSourceLabel
    unavailable_reason: OutputPassportUnavailableReason | None = None


@dataclass(frozen=True)
class PolicyContextRef(_CanonicalMixin):
    """Passive policy context reference."""

    policy_context_ref_id: str
    policy_surface: str
    source_label: OutputPassportSourceLabel
    unavailable_reason: OutputPassportUnavailableReason | None = None


@dataclass(frozen=True)
class RiskDisclosure(_CanonicalMixin):
    """Risk disclosure fields."""

    risk_tier: OutputPassportRiskTier
    risk_notes: tuple[str, ...]
    truth_label: OutputPassportTruthLabel


@dataclass(frozen=True)
class OutputAuthorityPolicyRiskDisclosure(_CanonicalMixin):
    """P1.9.3 authority/policy/risk disclosure envelope."""

    schema_version: str
    checkpoint_id: str
    authority_context_ref: AuthorityContextRef
    policy_context_ref: PolicyContextRef
    risk_disclosure: RiskDisclosure
    authorization_status: OutputPassportAuthorizationStatus
    unavailable_reason: OutputPassportUnavailableReason | None
    truth_label: OutputPassportTruthLabel
    source_label: OutputPassportSourceLabel
    invariants: tuple[str, ...]
    authority_policy_risk_hash: str


@dataclass(frozen=True)
class MemoryInfluenceRef(_CanonicalMixin):
    """Passive memory influence reference."""

    memory_influence_ref_id: str
    memory_zone_ref: str
    influence_description: str
    source_label: OutputPassportSourceLabel


@dataclass(frozen=True)
class MemoryInfluenceDisclosure(_CanonicalMixin):
    """P1.9.4 memory influence disclosure without memory access."""

    schema_version: str
    checkpoint_id: str
    influence_status: OutputPassportInfluenceStatus
    influence_refs: tuple[MemoryInfluenceRef, ...]
    unavailable_reason: OutputPassportUnavailableReason | None
    truth_label: OutputPassportTruthLabel
    source_label: OutputPassportSourceLabel
    invariants: tuple[str, ...]
    memory_influence_hash: str


@dataclass(frozen=True)
class PassportEvidenceRef(_CanonicalMixin):
    """Passive evidence reference."""

    evidence_ref_id: str
    evidence_kind: str
    ref_status: OutputPassportReferenceStatus
    verification_status: OutputPassportVerificationStatus
    source_label: OutputPassportSourceLabel


@dataclass(frozen=True)
class PassportTraceRef(_CanonicalMixin):
    """Passive trace reference."""

    trace_ref_id: str
    trace_event_ref: str
    ref_status: OutputPassportReferenceStatus
    verification_status: OutputPassportVerificationStatus
    source_label: OutputPassportSourceLabel


@dataclass(frozen=True)
class EvidenceTraceBinding(_CanonicalMixin):
    """P1.9.5 evidence/trace reference-only binding."""

    schema_version: str
    checkpoint_id: str
    ref_kind: OutputPassportReferenceKind
    evidence_ref: PassportEvidenceRef | None
    trace_ref: PassportTraceRef | None
    ref_status: OutputPassportReferenceStatus
    verification_status: OutputPassportVerificationStatus
    unavailable_reason: OutputPassportUnavailableReason | None
    truth_label: OutputPassportTruthLabel
    source_label: OutputPassportSourceLabel
    invariants: tuple[str, ...]
    evidence_trace_binding_hash: str


@dataclass(frozen=True)
class PassportAssumption(_CanonicalMixin):
    """Declared assumption."""

    assumption_id: str
    statement: str
    source_label: OutputPassportSourceLabel


@dataclass(frozen=True)
class PassportLimitation(_CanonicalMixin):
    """Declared limitation."""

    limitation_id: str
    statement: str
    source_label: OutputPassportSourceLabel


@dataclass(frozen=True)
class PassportUncertainty(_CanonicalMixin):
    """Uncertainty descriptor."""

    uncertainty_level: OutputPassportUncertaintyLevel
    uncertainty_status: str
    confidence_notes: str
    confidence_unavailable_reason: OutputPassportUnavailableReason | None


@dataclass(frozen=True)
class AssumptionLimitationUncertaintyEnvelope(_CanonicalMixin):
    """P1.9.6 assumptions, limitations, and uncertainty fields."""

    schema_version: str
    checkpoint_id: str
    assumptions: tuple[PassportAssumption, ...]
    limitations: tuple[PassportLimitation, ...]
    unknowns: tuple[str, ...]
    uncertainty: PassportUncertainty
    truth_label: OutputPassportTruthLabel
    source_label: OutputPassportSourceLabel
    invariants: tuple[str, ...]
    uncertainty_envelope_hash: str


@dataclass(frozen=True)
class OutputPassportDeterminismProfile(_CanonicalMixin):
    """Documents hash input normalization rules."""

    hash_algorithm: str
    canonical_json: bool
    sort_keys: bool
    excluded_volatile_fields: tuple[str, ...]
    included_field_groups: tuple[str, ...]
    hash_is_verification: bool = False
    hash_is_truth: bool = False


@dataclass(frozen=True)
class OutputPassportHashContract(_CanonicalMixin):
    """P1.9.7 deterministic hash contract."""

    schema_version: str
    checkpoint_id: str
    determinism_profile: OutputPassportDeterminismProfile
    payload_hash: str
    hash_truth_label: OutputPassportTruthLabel
    hash_is_verification: bool
    source_label: OutputPassportSourceLabel
    invariants: tuple[str, ...]
    hash_contract_hash: str


@dataclass(frozen=True)
class OutputPassportPayload(_CanonicalMixin):
    """Aggregate dev-fixture output passport payload."""

    schema_version: str
    foundation: OutputPassportFoundation
    identity: OutputPassportIdentity
    attribution_envelope: OutputPassportAttributionEnvelope
    authority_policy_risk: OutputAuthorityPolicyRiskDisclosure
    memory_influence: MemoryInfluenceDisclosure
    evidence_trace_binding: EvidenceTraceBinding
    uncertainty_envelope: AssumptionLimitationUncertaintyEnvelope
    hash_contract: OutputPassportHashContract
    truth_label: OutputPassportTruthLabel
    source_label: OutputPassportSourceLabel
    side_effects: OutputPassportSideEffectProof
    payload_hash: str


@dataclass(frozen=True)
class OutputPassportCheckpointRead(_CanonicalMixin):
    """Checkpoint read entry for pack result."""

    checkpoint_id: str
    canonical_name: str
    status: OutputPassportCheckpointStatus
    truth_label: OutputPassportTruthLabel
    unavailable_reason: OutputPassportUnavailableReason | None
    limitations: tuple[str, ...]
    evidence_ref: str


@dataclass(frozen=True)
class P19APassportIdentityAttributionHashPackResult(_CanonicalMixin):
    """P1.9-A pack result envelope."""

    schema_version: str
    pack_id: str
    section_id: str
    covered_checkpoints: tuple[str, ...]
    checkpoint_reads: tuple[OutputPassportCheckpointRead, ...]
    checkpoint_statuses: Mapping[str, str]
    truth_labels: tuple[OutputPassportTruthLabel, ...]
    payload: OutputPassportPayload
    side_effect_proof: OutputPassportSideEffectProof
    unavailable_reasons: tuple[OutputPassportUnavailableReason, ...]
    unavailable_reason_details: Mapping[str, str]
    hash_contract_summary: str
    next_pack: str
    source_label: OutputPassportSourceLabel
    result_hash: str


E = TypeVar("E", bound=Enum)


def validate_known_fields(
    raw: Mapping[str, Any],
    known_fields: frozenset[str],
    *,
    label: str = "payload",
) -> None:
    unknown = set(raw.keys()) - known_fields
    if unknown:
        raise OutputPassportUnknownFieldError(
            f"{label}: unknown field(s): {', '.join(sorted(unknown))} — closed-world",
            code=OutputPassportErrorCode.UNKNOWN_FIELD,
            field=sorted(unknown)[0],
            details={"unknown_fields": sorted(unknown), "label": label},
        )


def _parse_enum(enum_type: type[E], value: E | str, field_name: str) -> E:
    if isinstance(value, enum_type):
        return value
    try:
        return enum_type(value)
    except ValueError as exc:
        raise OutputPassportValidationError(
            f"invalid {field_name}: {value!r}",
            code=OutputPassportErrorCode.INVALID_ENUM,
            field=field_name,
        ) from exc


def _parse_source_label(
    value: OutputPassportSourceLabel | str,
) -> OutputPassportSourceLabel:
    return _parse_enum(OutputPassportSourceLabel, value, "source_label")


def _parse_truth_label(
    value: OutputPassportTruthLabel | str,
    *,
    field_name: str = "truth_label",
    forbid_verified: bool = False,
) -> OutputPassportTruthLabel:
    label = _parse_enum(OutputPassportTruthLabel, value, field_name)
    if forbid_verified and label in FORBIDDEN_DEFAULT_TRUTH_LABELS:
        raise OutputPassportValidationError(
            f"forbidden {field_name}: {label.value}",
            code=OutputPassportErrorCode.FORBIDDEN_VERIFICATION_LABEL,
            field=field_name,
        )
    return label


def _parse_verification_status(
    value: OutputPassportVerificationStatus | str,
    *,
    field_name: str = "verification_status",
) -> OutputPassportVerificationStatus:
    status = _parse_enum(OutputPassportVerificationStatus, value, field_name)
    if status is OutputPassportVerificationStatus.VERIFIED:
        raise OutputPassportValidationError(
            "VERIFIED status is forbidden in P1.9-A without actual verification",
            code=OutputPassportErrorCode.FORBIDDEN_VERIFICATION_LABEL,
            field=field_name,
        )
    return status


def _canonical_value(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return _canonical_dataclass_dict(value)
    if isinstance(value, Mapping):
        return {
            str(_canonical_value(key)): _canonical_value(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    if isinstance(value, (list, tuple)):
        return [_canonical_value(item) for item in value]
    return value


def _canonical_dataclass_dict(value: Any) -> dict[str, Any]:
    return {
        field.name: _canonical_value(getattr(value, field.name))
        for field in fields(value)
    }


def to_canonical_dict(value: Any) -> dict[str, Any]:
    if is_dataclass(value):
        return _canonical_dataclass_dict(value)
    if isinstance(value, Mapping):
        return _canonical_value(value)
    raise OutputPassportValidationError(
        f"cannot canonicalize value of type {type(value)!r}",
        code=OutputPassportErrorCode.SERIALIZATION_ERROR,
    )


def to_canonical_json(value: Any) -> str:
    canonical = to_canonical_dict(value) if not isinstance(value, str) else value
    if isinstance(canonical, str):
        return canonical
    return json.dumps(canonical, sort_keys=True, separators=(",", ":"))


def stable_hash(value: Any) -> str:
    canonical = to_canonical_json(value)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _hash_payload(payload: Mapping[str, Any]) -> str:
    return stable_hash(dict(payload))


def _normalize_for_passport_hash(value: Any) -> Any:
    canonical = to_canonical_dict(value)
    return _strip_volatile_fields(canonical)


def _strip_volatile_fields(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _strip_volatile_fields(item)
            for key, item in sorted(value.items())
            if key not in OUTPUT_PASSPORT_HASH_VOLATILE_FIELDS
        }
    if isinstance(value, list):
        return [_strip_volatile_fields(item) for item in value]
    return value


def serialize_output_passport_payload(payload: OutputPassportPayload) -> str:
    return to_canonical_json(payload)


def compute_output_passport_hash(payload: OutputPassportPayload) -> str:
    normalized = _normalize_for_passport_hash(payload)
    return stable_hash(normalized)


def _all_false_side_effects() -> OutputPassportSideEffectProof:
    return OutputPassportSideEffectProof()


def _default_boundary() -> OutputPassportBoundary:
    return OutputPassportBoundary()


def _reason_details() -> dict[str, str]:
    return dict(OUTPUT_PASSPORT_UNAVAILABLE_REASON_DETAILS)


def build_output_passport_foundation(
    *,
    checkpoint_id: str = "P1.9.0",
    purpose: str = "Structured disclosure envelope for output provenance",
    provenance_meaning: str = "Declared origin context without verification claim",
    disclosure_meaning: str = "Explicit metadata exposure without permission grant",
    truth_label: OutputPassportTruthLabel | str = OutputPassportTruthLabel.CONTRACT_ONLY,
    verification_status: OutputPassportVerificationStatus | str = (
        OutputPassportVerificationStatus.NOT_VERIFIED
    ),
    source_label: OutputPassportSourceLabel | str = OutputPassportSourceLabel.CONTRACT_ONLY,
    unavailable_bindings: Mapping[str, str] | None = None,
    invariants: Sequence[str] = FOUNDATION_INVARIANTS,
) -> OutputPassportFoundation:
    truth_label_val = _parse_truth_label(truth_label, forbid_verified=True)
    verification_status_val = _parse_verification_status(verification_status)
    source_label_val = _parse_source_label(source_label)
    side_effects = _all_false_side_effects()
    bindings = (
        dict(unavailable_bindings)
        if unavailable_bindings is not None
        else dict(OUTPUT_PASSPORT_UNAVAILABLE_BINDINGS)
    )
    payload = {
        "schema_version": OUTPUT_PASSPORT_FOUNDATION_VERSION,
        "checkpoint_id": checkpoint_id,
        "purpose": purpose,
        "provenance_meaning": provenance_meaning,
        "disclosure_meaning": disclosure_meaning,
        "truth_label": truth_label_val,
        "verification_status": verification_status_val,
        "boundary": _default_boundary(),
        "source_label": source_label_val,
        "unavailable_bindings": bindings,
        "invariants": tuple(invariants),
        "side_effects": side_effects,
    }
    return OutputPassportFoundation(
        **payload,
        foundation_hash=_hash_payload(payload),
    )


def build_output_passport_version(
    *,
    major: int = 1,
    minor: int = 0,
    patch: int = 0,
    schema_version: str = OUTPUT_PASSPORT_IDENTITY_VERSION,
) -> OutputPassportVersion:
    return OutputPassportVersion(
        major=major,
        minor=minor,
        patch=patch,
        schema_version=schema_version,
        version_label=f"{major}.{minor}.{patch}",
    )


def build_output_passport_subject_ref(
    *,
    subject_ref_id: str = "dev-subject-ref-001",
    output_ref: str = "dev-output-ref-001",
    subject_kind: str = "generated_output",
    source_label: OutputPassportSourceLabel | str = OutputPassportSourceLabel.DEV_FIXTURE,
) -> OutputPassportSubjectRef:
    if not subject_ref_id.strip():
        raise OutputPassportValidationError(
            "subject_ref_id is required",
            code=OutputPassportErrorCode.VALIDATION_ERROR,
            field="subject_ref_id",
        )
    if not output_ref.strip():
        raise OutputPassportValidationError(
            "output_ref is required",
            code=OutputPassportErrorCode.VALIDATION_ERROR,
            field="output_ref",
        )
    return OutputPassportSubjectRef(
        subject_ref_id=subject_ref_id,
        output_ref=output_ref,
        subject_kind=subject_kind,
        source_label=_parse_source_label(source_label),
    )


def build_output_passport_identity(
    *,
    checkpoint_id: str = "P1.9.1",
    passport_id: str = "dev-passport-001",
    passport_version: OutputPassportVersion | None = None,
    subject_ref: OutputPassportSubjectRef | None = None,
    generation_context_ref: str = "dev-generation-context-ref-001",
    truth_label: OutputPassportTruthLabel | str = OutputPassportTruthLabel.CONTRACT_ONLY,
    verification_status: OutputPassportVerificationStatus | str = (
        OutputPassportVerificationStatus.NOT_VERIFIED
    ),
    source_label: OutputPassportSourceLabel | str = OutputPassportSourceLabel.DEV_FIXTURE,
) -> OutputPassportIdentity:
    if not passport_id.strip():
        raise OutputPassportValidationError(
            "passport_id is required",
            code=OutputPassportErrorCode.VALIDATION_ERROR,
            field="passport_id",
        )
    subject_ref_val = subject_ref or build_output_passport_subject_ref()
    passport_version_val = passport_version or build_output_passport_version()
    truth_label_val = _parse_truth_label(truth_label, forbid_verified=True)
    verification_status_val = _parse_verification_status(verification_status)
    source_label_val = _parse_source_label(source_label)
    payload = {
        "schema_version": OUTPUT_PASSPORT_IDENTITY_VERSION,
        "checkpoint_id": checkpoint_id,
        "passport_id": passport_id,
        "passport_version": passport_version_val,
        "subject_ref": subject_ref_val,
        "generation_context_ref": generation_context_ref,
        "truth_label": truth_label_val,
        "verification_status": verification_status_val,
        "source_label": source_label_val,
    }
    return OutputPassportIdentity(
        **payload,
        identity_hash=_hash_payload(payload),
    )


def build_output_passport_attribution_envelope(
    *,
    checkpoint_id: str = "P1.9.2",
    actor_attribution: OutputActorAttribution | None = None,
    agent_attribution: OutputAgentAttribution | None = None,
    model_attribution: OutputModelAttribution | None = None,
    tool_attribution: OutputToolAttribution | None = None,
    unknown_attribution_declared: bool = False,
    truth_label: OutputPassportTruthLabel | str = (
        OutputPassportTruthLabel.DECLARED_ATTRIBUTION
    ),
    source_label: OutputPassportSourceLabel | str = OutputPassportSourceLabel.DEV_FIXTURE,
) -> OutputPassportAttributionEnvelope:
    source_label_val = _parse_source_label(source_label)
    actor = actor_attribution or OutputActorAttribution(
        attribution_kind=OutputPassportAttributionKind.DECLARED,
        actor_kind=OutputPassportActorKind.OPERATOR,
        actor_ref="dev-operator-ref-001",
        display_name="DEV_FIXTURE Operator",
        truth_label=OutputPassportTruthLabel.DECLARED_ATTRIBUTION,
        source_label=source_label_val,
    )
    agent = agent_attribution or OutputAgentAttribution(
        attribution_kind=OutputPassportAttributionKind.DECLARED,
        agent_ref="dev-agent-ref-001",
        agent_id="dev-agent-001",
        truth_label=OutputPassportTruthLabel.DECLARED_ATTRIBUTION,
        source_label=source_label_val,
    )
    model = model_attribution or OutputModelAttribution(
        attribution_kind=OutputPassportAttributionKind.DECLARED,
        model_ref="dev-model-ref-001",
        model_id="dev-model-001",
        provider_ref="dev-provider-ref-001",
        truth_label=OutputPassportTruthLabel.DECLARED_ATTRIBUTION,
        source_label=source_label_val,
    )
    tool = tool_attribution or OutputToolAttribution(
        attribution_kind=OutputPassportAttributionKind.UNAVAILABLE,
        tool_ref="",
        tool_id="",
        truth_label=OutputPassportTruthLabel.UNAVAILABLE_ATTRIBUTION,
        source_label=source_label_val,
    )
    truth_label_val = _parse_truth_label(truth_label, forbid_verified=True)
    invariants = (
        "Attribution is declared, not trusted.",
        "Unknown/unavailable attribution must be explicit.",
        "Attribution does not imply proof or verification.",
    )
    payload = {
        "schema_version": OUTPUT_PASSPORT_ATTRIBUTION_VERSION,
        "checkpoint_id": checkpoint_id,
        "actor_attribution": actor,
        "agent_attribution": agent,
        "model_attribution": model,
        "tool_attribution": tool,
        "unknown_attribution_declared": unknown_attribution_declared,
        "truth_label": truth_label_val,
        "source_label": source_label_val,
        "invariants": invariants,
    }
    return OutputPassportAttributionEnvelope(
        **payload,
        attribution_envelope_hash=_hash_payload(payload),
    )


def build_authority_policy_risk_disclosure(
    *,
    checkpoint_id: str = "P1.9.3",
    authority_context_ref: AuthorityContextRef | None = None,
    policy_context_ref: PolicyContextRef | None = None,
    risk_disclosure: RiskDisclosure | None = None,
    authorization_status: OutputPassportAuthorizationStatus | str = (
        OutputPassportAuthorizationStatus.DISCLOSURE_ONLY
    ),
    unavailable_reason: OutputPassportUnavailableReason | str | None = None,
    truth_label: OutputPassportTruthLabel | str = OutputPassportTruthLabel.DISCLOSURE_ONLY,
    source_label: OutputPassportSourceLabel | str = OutputPassportSourceLabel.DEV_FIXTURE,
) -> OutputAuthorityPolicyRiskDisclosure:
    source_label_val = _parse_source_label(source_label)
    authority = authority_context_ref or AuthorityContextRef(
        authority_context_ref_id="dev-authority-context-ref-001",
        authority_basis="operator_declared_context",
        source_label=source_label_val,
    )
    policy = policy_context_ref or PolicyContextRef(
        policy_context_ref_id="dev-policy-context-ref-001",
        policy_surface="advisory_only",
        source_label=source_label_val,
        unavailable_reason=OutputPassportUnavailableReason.POLICY_CONTEXT_UNAVAILABLE,
    )
    risk = risk_disclosure or RiskDisclosure(
        risk_tier=OutputPassportRiskTier.R2,
        risk_notes=("DEV_FIXTURE risk disclosure only.",),
        truth_label=OutputPassportTruthLabel.DISCLOSURE_ONLY,
    )
    unavailable_reason_val = (
        _parse_enum(OutputPassportUnavailableReason, unavailable_reason, "unavailable_reason")
        if unavailable_reason is not None
        else None
    )
    truth_label_val = _parse_truth_label(truth_label, forbid_verified=True)
    invariants = (
        "Authority context ref exists ≠ authority granted.",
        "Policy context ref exists ≠ policy enforced.",
        "Risk disclosure exists ≠ permission or execution.",
    )
    payload = {
        "schema_version": OUTPUT_PASSPORT_AUTHORITY_POLICY_RISK_VERSION,
        "checkpoint_id": checkpoint_id,
        "authority_context_ref": authority,
        "policy_context_ref": policy,
        "risk_disclosure": risk,
        "authorization_status": _parse_enum(
            OutputPassportAuthorizationStatus,
            authorization_status,
            "authorization_status",
        ),
        "unavailable_reason": unavailable_reason_val,
        "truth_label": truth_label_val,
        "source_label": source_label_val,
        "invariants": invariants,
    }
    return OutputAuthorityPolicyRiskDisclosure(
        **payload,
        authority_policy_risk_hash=_hash_payload(payload),
    )


def build_memory_influence_disclosure(
    *,
    checkpoint_id: str = "P1.9.4",
    influence_status: OutputPassportInfluenceStatus | str = (
        OutputPassportInfluenceStatus.DECLARED
    ),
    influence_refs: Sequence[MemoryInfluenceRef] | None = None,
    unavailable_reason: OutputPassportUnavailableReason | str | None = None,
    truth_label: OutputPassportTruthLabel | str = (
        OutputPassportTruthLabel.MEMORY_INFLUENCE_DECLARED
    ),
    source_label: OutputPassportSourceLabel | str = OutputPassportSourceLabel.DEV_FIXTURE,
) -> MemoryInfluenceDisclosure:
    source_label_val = _parse_source_label(source_label)
    status_val = _parse_enum(OutputPassportInfluenceStatus, influence_status, "influence_status")
    refs = tuple(influence_refs) if influence_refs is not None else (
        MemoryInfluenceRef(
            memory_influence_ref_id="dev-memory-influence-ref-001",
            memory_zone_ref="dev-memory-zone-ref-001",
            influence_description="Declared memory influence reference only",
            source_label=source_label_val,
        ),
    )
    if status_val is OutputPassportInfluenceStatus.NONE_DECLARED:
        refs = ()
    unavailable_reason_val = (
        _parse_enum(OutputPassportUnavailableReason, unavailable_reason, "unavailable_reason")
        if unavailable_reason is not None
        else None
    )
    truth_label_val = _parse_truth_label(truth_label, forbid_verified=True)
    invariants = (
        "Memory influence disclosure is not memory read permission.",
        "No memory layer call occurs from this object.",
    )
    payload = {
        "schema_version": OUTPUT_PASSPORT_MEMORY_INFLUENCE_VERSION,
        "checkpoint_id": checkpoint_id,
        "influence_status": status_val,
        "influence_refs": refs,
        "unavailable_reason": unavailable_reason_val,
        "truth_label": truth_label_val,
        "source_label": source_label_val,
        "invariants": invariants,
    }
    return MemoryInfluenceDisclosure(
        **payload,
        memory_influence_hash=_hash_payload(payload),
    )


def build_evidence_trace_binding(
    *,
    checkpoint_id: str = "P1.9.5",
    ref_kind: OutputPassportReferenceKind | str = OutputPassportReferenceKind.BOTH,
    evidence_ref: PassportEvidenceRef | None = None,
    trace_ref: PassportTraceRef | None = None,
    ref_status: OutputPassportReferenceStatus | str = (
        OutputPassportReferenceStatus.REFERENCE_ATTACHED
    ),
    verification_status: OutputPassportVerificationStatus | str = (
        OutputPassportVerificationStatus.NOT_VERIFIED
    ),
    unavailable_reason: OutputPassportUnavailableReason | str | None = (
        OutputPassportUnavailableReason.TRACE_VERIFICATION_UNAVAILABLE
    ),
    truth_label: OutputPassportTruthLabel | str = OutputPassportTruthLabel.REFERENCE_ONLY,
    source_label: OutputPassportSourceLabel | str = OutputPassportSourceLabel.REFERENCE_ONLY,
) -> EvidenceTraceBinding:
    source_label_val = _parse_source_label(source_label)
    verification_status_val = _parse_verification_status(verification_status)
    truth_label_val = _parse_truth_label(truth_label, forbid_verified=True)
    if truth_label_val is OutputPassportTruthLabel.TRACE_VERIFIED:
        raise OutputPassportValidationError(
            "TRACE_VERIFIED truth label is forbidden in P1.9-A",
            code=OutputPassportErrorCode.FORBIDDEN_VERIFICATION_LABEL,
            field="truth_label",
        )
    evidence = evidence_ref or PassportEvidenceRef(
        evidence_ref_id="dev-evidence-ref-001",
        evidence_kind="artifact_ref",
        ref_status=OutputPassportReferenceStatus.REFERENCE_ATTACHED,
        verification_status=OutputPassportVerificationStatus.NOT_VERIFIED,
        source_label=source_label_val,
    )
    trace = trace_ref or PassportTraceRef(
        trace_ref_id="dev-trace-ref-001",
        trace_event_ref="dev-trace-event-ref-001",
        ref_status=OutputPassportReferenceStatus.NOT_VERIFIED,
        verification_status=OutputPassportVerificationStatus.NOT_VERIFIED,
        source_label=source_label_val,
    )
    unavailable_reason_val = (
        _parse_enum(OutputPassportUnavailableReason, unavailable_reason, "unavailable_reason")
        if unavailable_reason is not None
        else None
    )
    invariants = (
        "EvidenceRef is not evidence finality.",
        "TraceRef is not TRACE_VERIFIED.",
        "Binding is reference-only; no trace/Ledger write.",
    )
    payload = {
        "schema_version": OUTPUT_PASSPORT_EVIDENCE_TRACE_BINDING_VERSION,
        "checkpoint_id": checkpoint_id,
        "ref_kind": _parse_enum(OutputPassportReferenceKind, ref_kind, "ref_kind"),
        "evidence_ref": evidence,
        "trace_ref": trace,
        "ref_status": _parse_enum(OutputPassportReferenceStatus, ref_status, "ref_status"),
        "verification_status": verification_status_val,
        "unavailable_reason": unavailable_reason_val,
        "truth_label": truth_label_val,
        "source_label": source_label_val,
        "invariants": invariants,
    }
    return EvidenceTraceBinding(
        **payload,
        evidence_trace_binding_hash=_hash_payload(payload),
    )


def build_assumption_limitation_uncertainty_envelope(
    *,
    checkpoint_id: str = "P1.9.6",
    assumptions: Sequence[PassportAssumption] | None = None,
    limitations: Sequence[PassportLimitation] | None = None,
    unknowns: Sequence[str] | None = None,
    uncertainty: PassportUncertainty | None = None,
    truth_label: OutputPassportTruthLabel | str = OutputPassportTruthLabel.DISCLOSURE_ONLY,
    source_label: OutputPassportSourceLabel | str = OutputPassportSourceLabel.DEV_FIXTURE,
) -> AssumptionLimitationUncertaintyEnvelope:
    source_label_val = _parse_source_label(source_label)
    assumptions_val = tuple(assumptions) if assumptions is not None else (
        PassportAssumption(
            assumption_id="dev-assumption-001",
            statement="DEV_FIXTURE assumption for contract validation",
            source_label=source_label_val,
        ),
    )
    limitations_val = tuple(limitations) if limitations is not None else (
        PassportLimitation(
            limitation_id="dev-limitation-001",
            statement="Contract-only; no factual verification performed",
            source_label=source_label_val,
        ),
    )
    unknowns_val = tuple(unknowns) if unknowns is not None else ()
    uncertainty_val = uncertainty or PassportUncertainty(
        uncertainty_level=OutputPassportUncertaintyLevel.MEDIUM,
        uncertainty_status="declared",
        confidence_notes="Confidence scoring engine unavailable in P1.9-A",
        confidence_unavailable_reason=OutputPassportUnavailableReason.VERIFICATION_UNAVAILABLE,
    )
    _parse_enum(
        OutputPassportUncertaintyLevel,
        uncertainty_val.uncertainty_level,
        "uncertainty_level",
    )
    truth_label_val = _parse_truth_label(truth_label, forbid_verified=True)
    invariants = (
        "Assumptions and limitations are disclosure-only.",
        "Uncertainty fields do not imply factual verification.",
    )
    payload = {
        "schema_version": OUTPUT_PASSPORT_UNCERTAINTY_VERSION,
        "checkpoint_id": checkpoint_id,
        "assumptions": assumptions_val,
        "limitations": limitations_val,
        "unknowns": unknowns_val,
        "uncertainty": uncertainty_val,
        "truth_label": truth_label_val,
        "source_label": source_label_val,
        "invariants": invariants,
    }
    return AssumptionLimitationUncertaintyEnvelope(
        **payload,
        uncertainty_envelope_hash=_hash_payload(payload),
    )


def build_output_passport_hash_contract(
    payload: OutputPassportPayload,
    *,
    checkpoint_id: str = "P1.9.7",
    source_label: OutputPassportSourceLabel | str = OutputPassportSourceLabel.CONTRACT_ONLY,
) -> OutputPassportHashContract:
    source_label_val = _parse_source_label(source_label)
    profile = OutputPassportDeterminismProfile(
        hash_algorithm="sha256",
        canonical_json=True,
        sort_keys=True,
        excluded_volatile_fields=tuple(sorted(OUTPUT_PASSPORT_HASH_VOLATILE_FIELDS)),
        included_field_groups=(
            "foundation",
            "identity",
            "attribution_envelope",
            "authority_policy_risk",
            "memory_influence",
            "evidence_trace_binding",
            "uncertainty_envelope",
        ),
        hash_is_verification=False,
        hash_is_truth=False,
    )
    payload_hash = compute_output_passport_hash(payload)
    invariants = (
        "Hash is deterministic payload hash, not truth.",
        "Hash is not verification.",
        "Volatile fields excluded from hash input.",
    )
    contract_payload = {
        "schema_version": OUTPUT_PASSPORT_HASH_CONTRACT_VERSION,
        "checkpoint_id": checkpoint_id,
        "determinism_profile": profile,
        "payload_hash": payload_hash,
        "hash_truth_label": OutputPassportTruthLabel.DETERMINISTIC_PAYLOAD_HASH,
        "hash_is_verification": False,
        "source_label": source_label_val,
        "invariants": invariants,
    }
    return OutputPassportHashContract(
        **contract_payload,
        hash_contract_hash=_hash_payload(contract_payload),
    )


def build_dev_fixture_output_passport_payload(
    *,
    foundation: OutputPassportFoundation | None = None,
    identity: OutputPassportIdentity | None = None,
    attribution_envelope: OutputPassportAttributionEnvelope | None = None,
    authority_policy_risk: OutputAuthorityPolicyRiskDisclosure | None = None,
    memory_influence: MemoryInfluenceDisclosure | None = None,
    evidence_trace_binding: EvidenceTraceBinding | None = None,
    uncertainty_envelope: AssumptionLimitationUncertaintyEnvelope | None = None,
) -> OutputPassportPayload:
    foundation_val = foundation or build_output_passport_foundation(
        source_label=OutputPassportSourceLabel.DEV_FIXTURE,
    )
    identity_val = identity or build_output_passport_identity()
    attribution_val = attribution_envelope or build_output_passport_attribution_envelope()
    authority_val = authority_policy_risk or build_authority_policy_risk_disclosure()
    memory_val = memory_influence or build_memory_influence_disclosure()
    evidence_val = evidence_trace_binding or build_evidence_trace_binding()
    uncertainty_val = uncertainty_envelope or (
        build_assumption_limitation_uncertainty_envelope()
    )
    side_effects = _all_false_side_effects()
    partial_payload = OutputPassportPayload(
        schema_version=OUTPUT_PASSPORT_PAYLOAD_VERSION,
        foundation=foundation_val,
        identity=identity_val,
        attribution_envelope=attribution_val,
        authority_policy_risk=authority_val,
        memory_influence=memory_val,
        evidence_trace_binding=evidence_val,
        uncertainty_envelope=uncertainty_val,
        hash_contract=OutputPassportHashContract(
            schema_version=OUTPUT_PASSPORT_HASH_CONTRACT_VERSION,
            checkpoint_id="P1.9.7",
            determinism_profile=OutputPassportDeterminismProfile(
                hash_algorithm="sha256",
                canonical_json=True,
                sort_keys=True,
                excluded_volatile_fields=tuple(sorted(OUTPUT_PASSPORT_HASH_VOLATILE_FIELDS)),
                included_field_groups=("pending",),
                hash_is_verification=False,
                hash_is_truth=False,
            ),
            payload_hash="pending",
            hash_truth_label=OutputPassportTruthLabel.DETERMINISTIC_PAYLOAD_HASH,
            hash_is_verification=False,
            source_label=OutputPassportSourceLabel.DEV_FIXTURE,
            invariants=("pending",),
            hash_contract_hash="pending",
        ),
        truth_label=OutputPassportTruthLabel.DEV_FIXTURE,
        source_label=OutputPassportSourceLabel.DEV_FIXTURE,
        side_effects=side_effects,
        payload_hash="pending",
    )
    hash_contract = build_output_passport_hash_contract(partial_payload)
    payload_without_hash = {
        "schema_version": OUTPUT_PASSPORT_PAYLOAD_VERSION,
        "foundation": foundation_val,
        "identity": identity_val,
        "attribution_envelope": attribution_val,
        "authority_policy_risk": authority_val,
        "memory_influence": memory_val,
        "evidence_trace_binding": evidence_val,
        "uncertainty_envelope": uncertainty_val,
        "hash_contract": hash_contract,
        "truth_label": OutputPassportTruthLabel.DEV_FIXTURE,
        "source_label": OutputPassportSourceLabel.DEV_FIXTURE,
        "side_effects": side_effects,
    }
    return OutputPassportPayload(
        **payload_without_hash,
        payload_hash=compute_output_passport_hash(
            OutputPassportPayload(**payload_without_hash, payload_hash="pending")
        ),
    )


def _default_checkpoint_reads() -> tuple[OutputPassportCheckpointRead, ...]:
    definitions = (
        ("P1.9.0", "Provenance / Disclosure Foundation"),
        ("P1.9.1", "Output Passport Identity Model"),
        ("P1.9.2", "Actor / Agent / Model / Tool Attribution Envelope"),
        ("P1.9.3", "Authority / Policy / Risk Disclosure Envelope"),
        ("P1.9.4", "Memory Influence Disclosure"),
        ("P1.9.5", "EvidenceRef / TraceRef Binding"),
        ("P1.9.6", "Assumption / Limitation / Uncertainty Fields"),
        ("P1.9.7", "Output Passport Hash / Determinism Contract"),
    )
    reads: list[OutputPassportCheckpointRead] = []
    for checkpoint_id, canonical_name in definitions:
        reads.append(
            OutputPassportCheckpointRead(
                checkpoint_id=checkpoint_id,
                canonical_name=canonical_name,
                status=OutputPassportCheckpointStatus.DONE,
                truth_label=OutputPassportTruthLabel.CONTRACT_ONLY,
                unavailable_reason=None,
                limitations=(
                    "Contract-only foundation; read model/CLI/verification deferred.",
                ),
                evidence_ref=f"{checkpoint_id.lower().replace('.', '_')}_contract",
            )
        )
    return tuple(reads)


def build_p1_9_a_passport_pack_result() -> P19APassportIdentityAttributionHashPackResult:
    payload = build_dev_fixture_output_passport_payload()
    side_effects = _all_false_side_effects()
    checkpoint_reads = _default_checkpoint_reads()
    checkpoint_statuses = {
        read.checkpoint_id: read.status.value for read in checkpoint_reads
    }
    truth_labels = (
        OutputPassportTruthLabel.CONTRACT_ONLY,
        OutputPassportTruthLabel.DEV_FIXTURE,
        OutputPassportTruthLabel.REFERENCE_ONLY,
        OutputPassportTruthLabel.DISCLOSURE_ONLY,
        OutputPassportTruthLabel.DETERMINISTIC_PAYLOAD_HASH,
    )
    hash_contract_summary = (
        f"algorithm=sha256; payload_hash={payload.hash_contract.payload_hash}; "
        "hash_is_verification=false; hash_is_truth=false"
    )
    result_payload = {
        "schema_version": OUTPUT_PASSPORT_PACK_RESULT_VERSION,
        "pack_id": OUTPUT_PASSPORT_PACK_TASK_ID,
        "section_id": OUTPUT_PASSPORT_SECTION_ID,
        "covered_checkpoints": OUTPUT_PASSPORT_PACK_CHECKPOINT_IDS,
        "checkpoint_reads": checkpoint_reads,
        "checkpoint_statuses": checkpoint_statuses,
        "truth_labels": truth_labels,
        "payload": payload,
        "side_effect_proof": side_effects,
        "unavailable_reasons": DEFAULT_OUTPUT_PASSPORT_UNAVAILABLE_REASONS,
        "unavailable_reason_details": _reason_details(),
        "hash_contract_summary": hash_contract_summary,
        "next_pack": OUTPUT_PASSPORT_NEXT_PACK_ID,
        "source_label": OutputPassportSourceLabel.DEV_FIXTURE,
    }
    return P19APassportIdentityAttributionHashPackResult(
        **result_payload,
        result_hash=_hash_payload(result_payload),
    )


def hash_output_passport_payload(payload: OutputPassportPayload) -> str:
    return payload.payload_hash


def serialize_output_passport_pack_result(
    result: P19APassportIdentityAttributionHashPackResult,
) -> str:
    return to_canonical_json(result)
