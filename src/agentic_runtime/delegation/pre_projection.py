"""Delegation pre-projection readiness / surface contract seed model (P1.8.16).

Deterministic, versioned, JSON-safe, side-effect-free reference-only
pre-projection readiness / surface contract seed metadata layer over
P1.8.15 accountability packet context.

Produces pre-projection readiness refs, surface contract seed refs,
read model seed refs, API contract seed refs, event contract seed refs,
surface eligibility entries/profile, projection gap matrix entries/matrix,
pre-projection seed envelopes, bindings, binding sets, side effects, and
status report without creating projection/API/event contract, read model,
API contract, event contract, surface contract, CLI/Shell/TUI binding,
UI surface, field exposure, redaction enforcement, policy/Custos decision,
runtime execution, trace write, Ledger write, Output Passport behavior,
P1.8.17 behavior, P1.8.18 behavior, P1.8.19 behavior, P1.8.20 behavior,
P1.9 behavior, TRACE_VERIFIED claim, or runtime mutation.

Architectural law:
  - PreProjectionReadinessRef exists does not mean projection ready.
  - SurfaceContractSeedRef exists does not mean surface contract.
  - ReadModelSeedRef exists does not mean read model.
  - APIContractSeedRef exists does not mean API contract.
  - EventContractSeedRef exists does not mean event contract.
  - SurfaceEligibilityProfile exists does not mean surface approval.
  - Operator-visible candidate is not projected field.
  - Redacted candidate is not policy enforcement.
  - ProjectionGapMatrix exists does not mean projection validation.
  - Gap present does not mean runtime failure.
  - Context present does not mean contract readiness.
  - PreProjectionSeedEnvelope exists does not mean Projection/API/Event Contract.
  - SeedHash is not TRACE_VERIFIED.
  - Golden Thread is continuity evidence only and is not trace verification.
"""
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum
from typing import Any

from .foundation import (
    DelegationError,
    DelegationErrorCode,
    DelegationSourceLabel,
    DelegationUnknownFieldError,
    DelegationValidationError,
    _optional_string,
    _parse_source_label,
    _required_string,
    stable_hash,
    to_canonical_json,
    validate_known_fields,
)

# ---------------------------------------------------------------------------
# Version constants
# ---------------------------------------------------------------------------

DELEGATION_PRE_PROJECTION_SEED_TASK_ID = "P1.8.16"
DELEGATION_PRE_PROJECTION_READINESS_REF_VERSION = "delegation_pre_projection_readiness_ref.v1"
DELEGATION_SURFACE_CONTRACT_SEED_REF_VERSION = "delegation_surface_contract_seed_ref.v1"
DELEGATION_READ_MODEL_SEED_REF_VERSION = "delegation_read_model_seed_ref.v1"
DELEGATION_API_CONTRACT_SEED_REF_VERSION = "delegation_api_contract_seed_ref.v1"
DELEGATION_EVENT_CONTRACT_SEED_REF_VERSION = "delegation_event_contract_seed_ref.v1"
DELEGATION_SURFACE_ELIGIBILITY_ENTRY_VERSION = "delegation_surface_eligibility_entry.v1"
DELEGATION_SURFACE_ELIGIBILITY_PROFILE_VERSION = "delegation_surface_eligibility_profile.v1"
DELEGATION_PROJECTION_GAP_MATRIX_ENTRY_VERSION = "delegation_projection_gap_matrix_entry.v1"
DELEGATION_PROJECTION_GAP_MATRIX_VERSION = "delegation_projection_gap_matrix.v1"
DELEGATION_PRE_PROJECTION_SEED_ENVELOPE_VERSION = "delegation_pre_projection_seed_envelope.v1"
DELEGATION_PRE_PROJECTION_SEED_BINDING_VERSION = "delegation_pre_projection_seed_binding.v1"
DELEGATION_PRE_PROJECTION_SEED_BINDING_SET_VERSION = "delegation_pre_projection_seed_binding_set.v1"
DELEGATION_PRE_PROJECTION_SEED_SIDE_EFFECTS_VERSION = "delegation_pre_projection_seed_side_effects.v1"
DELEGATION_PRE_PROJECTION_SEED_STATUS_REPORT_VERSION = "delegation_pre_projection_seed_status_report.v1"

# ---------------------------------------------------------------------------
# Unavailable bindings
# ---------------------------------------------------------------------------

DELEGATION_PRE_PROJECTION_SEED_UNAVAILABLE_BINDINGS: dict[str, str] = {
    "Projection/API/Event/Read Model": (
        "Projection/API/event/read model is not available in P1.8.16; "
        "pre-projection seed is reference-only metadata, not projection contract"
    ),
    "Projection Contract": (
        "Projection contract is not available in P1.8.16; "
        "PreProjectionSeedEnvelope is not Projection contract"
    ),
    "Read Model": (
        "Read model is not available in P1.8.16; "
        "ReadModelSeedRef is not read model; reserved for P1.8.17"
    ),
    "API Contract": (
        "API contract is not available in P1.8.16; "
        "APIContractSeedRef is not API contract; reserved for P1.8.17"
    ),
    "Event Contract": (
        "Event contract is not available in P1.8.16; "
        "EventContractSeedRef is not event contract; reserved for P1.8.17"
    ),
    "Surface Contract": (
        "Surface contract is not available in P1.8.16; "
        "SurfaceContractSeedRef is not surface contract; reserved for P1.8.17"
    ),
    "CLI/Shell/TUI Binding": (
        "CLI/Shell/TUI binding is not available in P1.8.16; "
        "pre-projection seed is reference-only metadata; reserved for P1.8.18"
    ),
    "UI Surface": (
        "UI surface is not available in P1.8.16; "
        "surface eligibility profile is not surface approval"
    ),
    "Field Exposure": (
        "Field exposure is not available in P1.8.16; "
        "Operator-visible candidate is not projected field"
    ),
    "Redaction Enforcement": (
        "Redaction enforcement is not available in P1.8.16; "
        "redacted candidate is not policy enforcement"
    ),
    "Policy/Custos Decision": (
        "Policy/Custos decision is not available in P1.8.16; "
        "pre-projection seed does not make policy decisions"
    ),
    "Runtime Execution": (
        "Runtime execution is not available in P1.8.16; "
        "pre-projection seed does not execute runtime"
    ),
    "Trace Writer": (
        "Trace writer is not available in P1.8.16; "
        "pre-projection seed does not write trace"
    ),
    "Ledger Writer": (
        "Ledger writer is not available in P1.8.16; "
        "pre-projection seed does not write Ledger"
    ),
    "Ledger Finality": (
        "Ledger finality is not available in P1.8.16; "
        "pre-projection seed does not finalize Ledger"
    ),
    "Trace Verification": (
        "Trace verification is not available in P1.8.16; "
        "seed hashes are not TRACE_VERIFIED"
    ),
    "Output Passport / P1.9": (
        "Output Passport / P1.9 is not implemented in P1.8.16"
    ),
    "P1.8.17 Projection/API/Event Contract": (
        "P1.8.17 projection/API/event contract is not implemented in P1.8.16"
    ),
    "P1.8.18 CLI/Shell/TUI Binding": (
        "P1.8.18 CLI/Shell/TUI binding is not implemented in P1.8.16"
    ),
    "P1.8.19 Docs/State/Report Seal Update": (
        "P1.8.19 docs/state/report seal update is not implemented in P1.8.16"
    ),
    "P1.8.20 Exit Seal Demo": (
        "P1.8.20 exit seal demo is not implemented in P1.8.16"
    ),
    "TRACE_VERIFIED Claim": (
        "TRACE_VERIFIED claim is not available in P1.8.16; "
        "pre-projection seed is reference-only metadata"
    ),
    "Golden Thread Trace Verification": (
        "Golden Thread is continuity evidence only and is not trace verification"
    ),
    "Global Trace Write": (
        "Global trace write is not available in P1.8.16; "
        "pre-projection seed does not write global trace"
    ),
    "Runtime Mutation": (
        "Runtime mutation is not available in P1.8.16; "
        "pre-projection seed does not mutate runtime"
    ),
}

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class DelegationPreProjectionSeedKind(Enum):
    """Classification of pre-projection seed metadata records.

    Boundary: Pre-projection seed kind classifies future projection
    preparation metadata. It does not create projection, read model,
    API/event contracts, Shell/CLI/UI, or Output Passport.
    """
    PRE_PROJECTION_READINESS = "pre_projection_readiness"
    SURFACE_CONTRACT_SEED = "surface_contract_seed"
    READ_MODEL_SEED = "read_model_seed"
    API_CONTRACT_SEED = "api_contract_seed"
    EVENT_CONTRACT_SEED = "event_contract_seed"
    SURFACE_ELIGIBILITY = "surface_eligibility"
    PROJECTION_GAP_MATRIX = "projection_gap_matrix"
    PRE_PROJECTION_SEED = "pre_projection_seed"
    REFERENCE_ONLY = "reference_only"
    UNKNOWN = "unknown"


class DelegationPreProjectionSeedReferenceStatus(Enum):
    """Reference status ladder for pre-projection seed contexts.

    Boundary:
      PRE_PROJECTION_READINESS_REFERENCED is not projection ready.
      SURFACE_CONTRACT_SEED_REFERENCED is not surface contract.
      READ_MODEL_SEED_REFERENCED is not read model.
      API_CONTRACT_SEED_REFERENCED is not API contract.
      EVENT_CONTRACT_SEED_REFERENCED is not event contract.
      SURFACE_ELIGIBILITY_REFERENCED is not surface approval.
      PROJECTION_GAP_MATRIX_REFERENCED is not projection validation.
      UNAVAILABLE labels are honest unavailability.
    """
    REFERENCE_ONLY = "reference_only"
    PRE_PROJECTION_READINESS_REFERENCED = "pre_projection_readiness_referenced"
    SURFACE_CONTRACT_SEED_REFERENCED = "surface_contract_seed_referenced"
    READ_MODEL_SEED_REFERENCED = "read_model_seed_referenced"
    API_CONTRACT_SEED_REFERENCED = "api_contract_seed_referenced"
    EVENT_CONTRACT_SEED_REFERENCED = "event_contract_seed_referenced"
    SURFACE_ELIGIBILITY_REFERENCED = "surface_eligibility_referenced"
    PROJECTION_GAP_MATRIX_REFERENCED = "projection_gap_matrix_referenced"
    PROJECTION_UNAVAILABLE = "projection_unavailable"
    API_EVENT_CONTRACT_UNAVAILABLE = "api_event_contract_unavailable"
    READ_MODEL_UNAVAILABLE = "read_model_unavailable"
    CLI_SHELL_TUI_UNAVAILABLE = "cli_shell_tui_unavailable"
    UI_SURFACE_UNAVAILABLE = "ui_surface_unavailable"
    TRACE_VERIFICATION_UNAVAILABLE = "trace_verification_unavailable"
    LEDGER_FINALITY_UNAVAILABLE = "ledger_finality_unavailable"
    OUTPUT_PASSPORT_UNAVAILABLE = "output_passport_unavailable"
    UNAVAILABLE = "unavailable"
    ERROR = "error"
    UNKNOWN = "unknown"


class DelegationPreProjectionSeedStatus(Enum):
    """Seed declaration status.

    Boundary: REFERENCE_ONLY means pre-projection seed is reference-only.
    DECLARED means seed context was declared as metadata.
    Neither means projection-ready, API-ready, event-ready, CLI-bound,
    Shell-bound, field-exposed, or UI-ready.
    """
    REFERENCE_ONLY = "reference_only"
    DECLARED = "declared"
    UNAVAILABLE = "unavailable"
    ERROR = "error"
    UNKNOWN = "unknown"


class DelegationSurfaceExposureClass(Enum):
    """Candidate exposure classification for future surface fields/components.

    Boundary:
      OPERATOR_VISIBLE_CANDIDATE is not projected field.
      INTERNAL_ONLY is not enforcement.
      GOVERNANCE_ONLY is not policy decision.
      TRACE_CONTEXT_ONLY is not trace write.
      POLICY_CONTEXT_ONLY is not policy evaluation.
      RUNTIME_CONTEXT_ONLY is not runtime execution.
      REDACTED_CANDIDATE is not redaction enforcement.
      UNAVAILABLE is honest unavailability.
    """
    OPERATOR_VISIBLE_CANDIDATE = "operator_visible_candidate"
    INTERNAL_ONLY = "internal_only"
    GOVERNANCE_ONLY = "governance_only"
    TRACE_CONTEXT_ONLY = "trace_context_only"
    POLICY_CONTEXT_ONLY = "policy_context_only"
    RUNTIME_CONTEXT_ONLY = "runtime_context_only"
    REDACTED_CANDIDATE = "redacted_candidate"
    UNAVAILABLE = "unavailable"
    UNKNOWN = "unknown"


class DelegationProjectionSeedFamily(Enum):
    """Family taxonomy for pre-projection seed ingredients.

    Boundary: Projection seed family classifies pre-projection ingredients.
    It does not represent projection validation, contract readiness,
    or API/event/read model availability.
    """
    ACCOUNTABILITY_PACKET_CONTEXT = "accountability_packet_context"
    INTEGRATION_SUMMARY_CONTEXT = "integration_summary_context"
    COMPONENT_COVERAGE_CONTEXT = "component_coverage_context"
    SURFACE_ELIGIBILITY_CONTEXT = "surface_eligibility_context"
    READ_MODEL_SEED_CONTEXT = "read_model_seed_context"
    API_CONTRACT_SEED_CONTEXT = "api_contract_seed_context"
    EVENT_CONTRACT_SEED_CONTEXT = "event_contract_seed_context"
    SURFACE_CONTRACT_SEED_CONTEXT = "surface_contract_seed_context"
    TRUTH_LABEL_CONTEXT = "truth_label_context"
    UNAVAILABLE_SURFACE_CONTEXT = "unavailable_surface_context"
    GOLDEN_THREAD_CONTEXT = "golden_thread_context"
    UNKNOWN = "unknown"


# ---------------------------------------------------------------------------
# Known fields (closed-world validation)
# ---------------------------------------------------------------------------

PRE_PROJECTION_READINESS_REF_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "pre_projection_readiness_ref_id",
    "delegation_ref_id",
    "pre_projection_readiness_ref",
    "pre_projection_readiness_description",
    "reference_status",
    "source_label",
    "seed_status",
    "pre_projection_readiness_hash",
})

SURFACE_CONTRACT_SEED_REF_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "surface_contract_seed_ref_id",
    "delegation_ref_id",
    "surface_contract_seed_ref",
    "surface_contract_seed_description",
    "reference_status",
    "source_label",
    "seed_status",
    "surface_contract_seed_hash",
})

READ_MODEL_SEED_REF_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "read_model_seed_ref_id",
    "delegation_ref_id",
    "read_model_seed_ref",
    "read_model_seed_description",
    "reference_status",
    "source_label",
    "seed_status",
    "read_model_seed_hash",
})

API_CONTRACT_SEED_REF_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "api_contract_seed_ref_id",
    "delegation_ref_id",
    "api_contract_seed_ref",
    "api_contract_seed_description",
    "reference_status",
    "source_label",
    "seed_status",
    "api_contract_seed_hash",
})

EVENT_CONTRACT_SEED_REF_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "event_contract_seed_ref_id",
    "delegation_ref_id",
    "event_contract_seed_ref",
    "event_contract_seed_description",
    "reference_status",
    "source_label",
    "seed_status",
    "event_contract_seed_hash",
})

SURFACE_ELIGIBILITY_ENTRY_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "eligibility_entry_id",
    "delegation_ref_id",
    "field_ref",
    "field_description",
    "exposure_class",
    "exposure_reason",
    "source_label",
    "entry_hash",
})

SURFACE_ELIGIBILITY_PROFILE_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "surface_eligibility_profile_id",
    "delegation_ref_id",
    "entries",
    "operator_visible_candidate_count",
    "internal_only_count",
    "governance_only_count",
    "trace_context_only_count",
    "policy_context_only_count",
    "runtime_context_only_count",
    "redacted_candidate_count",
    "unavailable_count",
    "source_label",
    "surface_eligibility_profile_hash",
})

PROJECTION_GAP_MATRIX_ENTRY_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "entry_id",
    "delegation_ref_id",
    "family",
    "present",
    "hash_present",
    "source_label_present",
    "finding_count",
    "unavailable_reason",
    "source_label",
    "entry_hash",
})

PROJECTION_GAP_MATRIX_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "projection_gap_matrix_id",
    "delegation_ref_id",
    "entries",
    "source_label",
    "projection_gap_matrix_hash",
})

PRE_PROJECTION_SEED_ENVELOPE_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "pre_projection_seed_envelope_id",
    "delegation_ref_id",
    "accountability_packet_binding_set_hash",
    "integration_summary_envelope_hash",
    "accountability_packet_envelope_hash",
    "surface_eligibility_profile_hash",
    "projection_gap_matrix_hash",
    "read_model_seed_refs",
    "api_contract_seed_refs",
    "event_contract_seed_refs",
    "surface_contract_seed_refs",
    "golden_thread_ref",
    "next_handoff_ref",
    "source_label",
    "pre_projection_seed_envelope_hash",
})

PRE_PROJECTION_SEED_BINDING_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "binding_id",
    "delegation_ref_id",
    "accountability_packet_binding_set_hash",
    "integration_summary_envelope_hash",
    "accountability_packet_envelope_hash",
    "surface_eligibility_profile_hash",
    "projection_gap_matrix_hash",
    "pre_projection_seed_envelope_hash",
    "source_label",
    "seed_status",
    "binding_hash",
})

PRE_PROJECTION_SEED_BINDING_SET_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "pre_projection_seed_binding_set_id",
    "delegation_ref_id",
    "accountability_packet_binding_set_hash",
    "integration_summary_envelope_hash",
    "accountability_packet_envelope_hash",
    "bindings",
    "side_effects",
    "source_label",
    "pre_projection_seed_binding_set_hash",
})

PRE_PROJECTION_SEED_SIDE_EFFECTS_KNOWN_FIELDS: frozenset[str] = frozenset({
    "projection_created",
    "read_model_created",
    "api_contract_created",
    "event_contract_created",
    "surface_contract_created",
    "cli_shell_tui_bound",
    "ui_surface_created",
    "field_exposed",
    "redaction_enforced",
    "policy_decision_emitted",
    "custos_decision_emitted",
    "runtime_executed",
    "trace_written",
    "ledger_written",
    "output_passport_created",
    "global_trace_written",
    "runtime_mutated",
})

PRE_PROJECTION_SEED_STATUS_REPORT_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "status_label",
    "available_contracts",
    "unavailable_bindings",
    "side_effects",
    "status_hash",
})

# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class DelegationPreProjectionReadinessRef:
    """Reference-only pre-projection readiness metadata.

    Boundary: Describes future projection preparation metadata.
    Does not create projection, validate projection, or create
    API/event/read model contracts.
    """
    schema_version: str
    pre_projection_readiness_ref_id: str
    delegation_ref_id: str
    pre_projection_readiness_ref: str | None
    pre_projection_readiness_description: str
    reference_status: DelegationPreProjectionSeedReferenceStatus
    source_label: DelegationSourceLabel
    seed_status: DelegationPreProjectionSeedStatus
    pre_projection_readiness_hash: str


@dataclass(frozen=True)
class DelegationSurfaceContractSeedRef:
    """Reference-only future surface contract seed metadata.

    Boundary: Describes future surface contract seed metadata.
    Is not surface contract. Does not create Shell, CLI, TUI, UI,
    or projection binding.
    """
    schema_version: str
    surface_contract_seed_ref_id: str
    delegation_ref_id: str
    surface_contract_seed_ref: str | None
    surface_contract_seed_description: str
    reference_status: DelegationPreProjectionSeedReferenceStatus
    source_label: DelegationSourceLabel
    seed_status: DelegationPreProjectionSeedStatus
    surface_contract_seed_hash: str


@dataclass(frozen=True)
class DelegationReadModelSeedRef:
    """Reference-only future read model seed metadata.

    Boundary: Describes future read model seed metadata.
    Is not read model. Does not define read model schema.
    Does not create projection state.
    """
    schema_version: str
    read_model_seed_ref_id: str
    delegation_ref_id: str
    read_model_seed_ref: str | None
    read_model_seed_description: str
    reference_status: DelegationPreProjectionSeedReferenceStatus
    source_label: DelegationSourceLabel
    seed_status: DelegationPreProjectionSeedStatus
    read_model_seed_hash: str


@dataclass(frozen=True)
class DelegationAPIContractSeedRef:
    """Reference-only future API contract seed metadata.

    Boundary: Describes future API contract seed metadata.
    Is not API contract. Does not define endpoint schema.
    Does not expose fields.
    """
    schema_version: str
    api_contract_seed_ref_id: str
    delegation_ref_id: str
    api_contract_seed_ref: str | None
    api_contract_seed_description: str
    reference_status: DelegationPreProjectionSeedReferenceStatus
    source_label: DelegationSourceLabel
    seed_status: DelegationPreProjectionSeedStatus
    api_contract_seed_hash: str


@dataclass(frozen=True)
class DelegationEventContractSeedRef:
    """Reference-only future event contract seed metadata.

    Boundary: Describes future event contract seed metadata.
    Is not event contract. Does not define event payload schema.
    Does not emit events.
    """
    schema_version: str
    event_contract_seed_ref_id: str
    delegation_ref_id: str
    event_contract_seed_ref: str | None
    event_contract_seed_description: str
    reference_status: DelegationPreProjectionSeedReferenceStatus
    source_label: DelegationSourceLabel
    seed_status: DelegationPreProjectionSeedStatus
    event_contract_seed_hash: str


@dataclass(frozen=True)
class DelegationSurfaceEligibilityEntry:
    """One candidate exposure classification row for a future surface field.

    Boundary: Is not field exposure, surface approval, redaction
    enforcement, or policy decision.
    """
    schema_version: str
    eligibility_entry_id: str
    delegation_ref_id: str
    field_ref: str
    field_description: str
    exposure_class: DelegationSurfaceExposureClass
    exposure_reason: str
    source_label: DelegationSourceLabel
    entry_hash: str


@dataclass(frozen=True)
class DelegationSurfaceEligibilityProfile:
    """Deterministic profile of candidate exposure classes for future projection work.

    Boundary: Is not surface approval. Operator-visible candidate is not
    projected field. Internal-only candidate is not enforcement. Redacted
    candidate is not redaction enforcement. Is not projection contract.
    """
    schema_version: str
    surface_eligibility_profile_id: str
    delegation_ref_id: str
    entries: tuple[DelegationSurfaceEligibilityEntry, ...]
    operator_visible_candidate_count: int
    internal_only_count: int
    governance_only_count: int
    trace_context_only_count: int
    policy_context_only_count: int
    runtime_context_only_count: int
    redacted_candidate_count: int
    unavailable_count: int
    source_label: DelegationSourceLabel
    surface_eligibility_profile_hash: str


@dataclass(frozen=True)
class DelegationProjectionGapMatrixEntry:
    """One present/missing row for pre-projection ingredients.

    Boundary: Is not projection validation. Gap present is not runtime
    failure. Context present is not contract readiness. Finding count
    is not risk score.
    """
    schema_version: str
    entry_id: str
    delegation_ref_id: str
    family: DelegationProjectionSeedFamily
    present: bool
    hash_present: bool
    source_label_present: bool
    finding_count: int
    unavailable_reason: str
    source_label: DelegationSourceLabel
    entry_hash: str


@dataclass(frozen=True)
class DelegationProjectionGapMatrix:
    """Lightweight reference-only matrix of pre-projection ingredients.

    Boundary: Is not projection validation, projection/API/event contract,
    read model, or product surface readiness.
    """
    schema_version: str
    projection_gap_matrix_id: str
    delegation_ref_id: str
    entries: tuple[DelegationProjectionGapMatrixEntry, ...]
    source_label: DelegationSourceLabel
    projection_gap_matrix_hash: str


@dataclass(frozen=True)
class DelegationPreProjectionSeedEnvelope:
    """Deterministic packet around P1.8.15 accountability packet hashes.

    Boundary: Is a backend seed packet. Is not projection contract,
    read model, API contract, event contract, CLI/Shell/TUI binding,
    Output Passport, or TRACE_VERIFIED.
    """
    schema_version: str
    pre_projection_seed_envelope_id: str
    delegation_ref_id: str
    accountability_packet_binding_set_hash: str
    integration_summary_envelope_hash: str
    accountability_packet_envelope_hash: str
    surface_eligibility_profile_hash: str
    projection_gap_matrix_hash: str
    read_model_seed_refs: str | None
    api_contract_seed_refs: str | None
    event_contract_seed_refs: str | None
    surface_contract_seed_refs: str | None
    golden_thread_ref: str
    next_handoff_ref: str
    source_label: DelegationSourceLabel
    pre_projection_seed_envelope_hash: str


@dataclass(frozen=True)
class DelegationPreProjectionSeedBinding:
    """Binding between pre-projection seed envelope and accountability packet context.

    Boundary: Binds seed metadata. Is not projection validation,
    projection/API/event contract, surface approval, or TRACE_VERIFIED.
    """
    schema_version: str
    binding_id: str
    delegation_ref_id: str
    accountability_packet_binding_set_hash: str
    integration_summary_envelope_hash: str
    accountability_packet_envelope_hash: str
    surface_eligibility_profile_hash: str
    projection_gap_matrix_hash: str
    pre_projection_seed_envelope_hash: str
    source_label: DelegationSourceLabel
    seed_status: DelegationPreProjectionSeedStatus
    binding_hash: str


@dataclass(frozen=True)
class DelegationPreProjectionSeedBindingSet:
    """Collection of pre-projection seed bindings for one delegation.

    Boundary: Describes seed hooks. Does not create projection, read model,
    API contract, event contract, surface contract, CLI/Shell/TUI binding,
    UI, trace, Ledger, Output Passport, or runtime mutation.
    """
    schema_version: str
    pre_projection_seed_binding_set_id: str
    delegation_ref_id: str
    accountability_packet_binding_set_hash: str
    integration_summary_envelope_hash: str
    accountability_packet_envelope_hash: str
    bindings: tuple[DelegationPreProjectionSeedBinding, ...]
    side_effects: DelegationPreProjectionSeedSideEffects
    source_label: DelegationSourceLabel
    pre_projection_seed_binding_set_hash: str


@dataclass(frozen=True)
class DelegationPreProjectionSeedSideEffects:
    """Hard proof that P1.8.16 is non-projecting, non-exposing, non-redacting,
    non-binding, non-writing, non-passporting, and non-mutating.

    All fields must default to False.
    """
    projection_created: bool
    read_model_created: bool
    api_contract_created: bool
    event_contract_created: bool
    surface_contract_created: bool
    cli_shell_tui_bound: bool
    ui_surface_created: bool
    field_exposed: bool
    redaction_enforced: bool
    policy_decision_emitted: bool
    custos_decision_emitted: bool
    runtime_executed: bool
    trace_written: bool
    ledger_written: bool
    output_passport_created: bool
    global_trace_written: bool
    runtime_mutated: bool


@dataclass(frozen=True)
class DelegationPreProjectionSeedStatusReport:
    """Reports pre-projection seed model capability and unavailable surfaces."""
    schema_version: str
    status_label: str
    available_contracts: tuple[str, ...]
    unavailable_bindings: dict[str, str]
    side_effects: DelegationPreProjectionSeedSideEffects
    status_hash: str


# ---------------------------------------------------------------------------
# Parse helpers
# ---------------------------------------------------------------------------

def _parse_pre_projection_seed_kind(
    value: DelegationPreProjectionSeedKind | str,
) -> DelegationPreProjectionSeedKind:
    if isinstance(value, DelegationPreProjectionSeedKind):
        return value
    try:
        return DelegationPreProjectionSeedKind(value)
    except ValueError:
        raise DelegationValidationError(
            f"Unknown DelegationPreProjectionSeedKind: {value!r}",
            error_code=DelegationErrorCode.VALIDATION_ERROR,
        )


def _parse_pre_projection_seed_reference_status(
    value: DelegationPreProjectionSeedReferenceStatus | str,
) -> DelegationPreProjectionSeedReferenceStatus:
    if isinstance(value, DelegationPreProjectionSeedReferenceStatus):
        return value
    try:
        return DelegationPreProjectionSeedReferenceStatus(value)
    except ValueError:
        raise DelegationValidationError(
            f"Unknown DelegationPreProjectionSeedReferenceStatus: {value!r}",
            error_code=DelegationErrorCode.VALIDATION_ERROR,
        )


def _parse_pre_projection_seed_status(
    value: DelegationPreProjectionSeedStatus | str,
) -> DelegationPreProjectionSeedStatus:
    if isinstance(value, DelegationPreProjectionSeedStatus):
        return value
    try:
        return DelegationPreProjectionSeedStatus(value)
    except ValueError:
        raise DelegationValidationError(
            f"Unknown DelegationPreProjectionSeedStatus: {value!r}",
            error_code=DelegationErrorCode.VALIDATION_ERROR,
        )


def _parse_surface_exposure_class(
    value: DelegationSurfaceExposureClass | str,
) -> DelegationSurfaceExposureClass:
    if isinstance(value, DelegationSurfaceExposureClass):
        return value
    try:
        return DelegationSurfaceExposureClass(value)
    except ValueError:
        raise DelegationValidationError(
            f"Unknown DelegationSurfaceExposureClass: {value!r}",
            error_code=DelegationErrorCode.VALIDATION_ERROR,
        )


def _parse_projection_seed_family(
    value: DelegationProjectionSeedFamily | str,
) -> DelegationProjectionSeedFamily:
    if isinstance(value, DelegationProjectionSeedFamily):
        return value
    try:
        return DelegationProjectionSeedFamily(value)
    except ValueError:
        raise DelegationValidationError(
            f"Unknown DelegationProjectionSeedFamily: {value!r}",
            error_code=DelegationErrorCode.VALIDATION_ERROR,
        )


# ---------------------------------------------------------------------------
# Compute hash functions
# ---------------------------------------------------------------------------

def _compute_pre_projection_readiness_hash(
    *,
    pre_projection_readiness_ref: str | None,
    pre_projection_readiness_description: str,
    reference_status: DelegationPreProjectionSeedReferenceStatus,
    source_label: DelegationSourceLabel,
    seed_status: DelegationPreProjectionSeedStatus,
) -> str:
    return stable_hash({
        "pre_projection_readiness_ref": pre_projection_readiness_ref,
        "pre_projection_readiness_description": pre_projection_readiness_description,
        "reference_status": reference_status.value,
        "source_label": source_label.value,
        "seed_status": seed_status.value,
    })


def _compute_surface_contract_seed_hash(
    *,
    surface_contract_seed_ref: str | None,
    surface_contract_seed_description: str,
    reference_status: DelegationPreProjectionSeedReferenceStatus,
    source_label: DelegationSourceLabel,
    seed_status: DelegationPreProjectionSeedStatus,
) -> str:
    return stable_hash({
        "surface_contract_seed_ref": surface_contract_seed_ref,
        "surface_contract_seed_description": surface_contract_seed_description,
        "reference_status": reference_status.value,
        "source_label": source_label.value,
        "seed_status": seed_status.value,
    })


def _compute_read_model_seed_hash(
    *,
    read_model_seed_ref: str | None,
    read_model_seed_description: str,
    reference_status: DelegationPreProjectionSeedReferenceStatus,
    source_label: DelegationSourceLabel,
    seed_status: DelegationPreProjectionSeedStatus,
) -> str:
    return stable_hash({
        "read_model_seed_ref": read_model_seed_ref,
        "read_model_seed_description": read_model_seed_description,
        "reference_status": reference_status.value,
        "source_label": source_label.value,
        "seed_status": seed_status.value,
    })


def _compute_api_contract_seed_hash(
    *,
    api_contract_seed_ref: str | None,
    api_contract_seed_description: str,
    reference_status: DelegationPreProjectionSeedReferenceStatus,
    source_label: DelegationSourceLabel,
    seed_status: DelegationPreProjectionSeedStatus,
) -> str:
    return stable_hash({
        "api_contract_seed_ref": api_contract_seed_ref,
        "api_contract_seed_description": api_contract_seed_description,
        "reference_status": reference_status.value,
        "source_label": source_label.value,
        "seed_status": seed_status.value,
    })


def _compute_event_contract_seed_hash(
    *,
    event_contract_seed_ref: str | None,
    event_contract_seed_description: str,
    reference_status: DelegationPreProjectionSeedReferenceStatus,
    source_label: DelegationSourceLabel,
    seed_status: DelegationPreProjectionSeedStatus,
) -> str:
    return stable_hash({
        "event_contract_seed_ref": event_contract_seed_ref,
        "event_contract_seed_description": event_contract_seed_description,
        "reference_status": reference_status.value,
        "source_label": source_label.value,
        "seed_status": seed_status.value,
    })


def _compute_surface_eligibility_entry_hash(
    *,
    field_ref: str,
    field_description: str,
    exposure_class: DelegationSurfaceExposureClass,
    exposure_reason: str,
    source_label: DelegationSourceLabel,
) -> str:
    return stable_hash({
        "field_ref": field_ref,
        "field_description": field_description,
        "exposure_class": exposure_class.value,
        "exposure_reason": exposure_reason,
        "source_label": source_label.value,
    })


def _compute_surface_eligibility_profile_hash(
    *,
    entry_hashes: tuple[str, ...],
    operator_visible_candidate_count: int,
    internal_only_count: int,
    governance_only_count: int,
    trace_context_only_count: int,
    policy_context_only_count: int,
    runtime_context_only_count: int,
    redacted_candidate_count: int,
    unavailable_count: int,
    source_label: DelegationSourceLabel,
) -> str:
    return stable_hash({
        "entry_hashes": list(entry_hashes),
        "operator_visible_candidate_count": operator_visible_candidate_count,
        "internal_only_count": internal_only_count,
        "governance_only_count": governance_only_count,
        "trace_context_only_count": trace_context_only_count,
        "policy_context_only_count": policy_context_only_count,
        "runtime_context_only_count": runtime_context_only_count,
        "redacted_candidate_count": redacted_candidate_count,
        "unavailable_count": unavailable_count,
        "source_label": source_label.value,
    })


def _compute_projection_gap_matrix_entry_hash(
    *,
    family: DelegationProjectionSeedFamily,
    present: bool,
    hash_present: bool,
    source_label_present: bool,
    finding_count: int,
    unavailable_reason: str,
    source_label: DelegationSourceLabel,
) -> str:
    return stable_hash({
        "family": family.value,
        "present": present,
        "hash_present": hash_present,
        "source_label_present": source_label_present,
        "finding_count": finding_count,
        "unavailable_reason": unavailable_reason,
        "source_label": source_label.value,
    })


def _compute_projection_gap_matrix_hash(
    *,
    entry_hashes: tuple[str, ...],
    source_label: DelegationSourceLabel,
) -> str:
    return stable_hash({
        "entry_hashes": list(entry_hashes),
        "source_label": source_label.value,
    })


def _compute_pre_projection_seed_envelope_hash(
    *,
    accountability_packet_binding_set_hash: str,
    integration_summary_envelope_hash: str,
    accountability_packet_envelope_hash: str,
    surface_eligibility_profile_hash: str,
    projection_gap_matrix_hash: str,
    read_model_seed_refs: str | None,
    api_contract_seed_refs: str | None,
    event_contract_seed_refs: str | None,
    surface_contract_seed_refs: str | None,
    golden_thread_ref: str,
    next_handoff_ref: str,
    source_label: DelegationSourceLabel,
) -> str:
    return stable_hash({
        "accountability_packet_binding_set_hash": accountability_packet_binding_set_hash,
        "integration_summary_envelope_hash": integration_summary_envelope_hash,
        "accountability_packet_envelope_hash": accountability_packet_envelope_hash,
        "surface_eligibility_profile_hash": surface_eligibility_profile_hash,
        "projection_gap_matrix_hash": projection_gap_matrix_hash,
        "read_model_seed_refs": read_model_seed_refs,
        "api_contract_seed_refs": api_contract_seed_refs,
        "event_contract_seed_refs": event_contract_seed_refs,
        "surface_contract_seed_refs": surface_contract_seed_refs,
        "golden_thread_ref": golden_thread_ref,
        "next_handoff_ref": next_handoff_ref,
        "source_label": source_label.value,
    })


def _compute_pre_projection_seed_binding_hash(
    *,
    accountability_packet_binding_set_hash: str,
    integration_summary_envelope_hash: str,
    accountability_packet_envelope_hash: str,
    surface_eligibility_profile_hash: str,
    projection_gap_matrix_hash: str,
    pre_projection_seed_envelope_hash: str,
    source_label: DelegationSourceLabel,
    seed_status: DelegationPreProjectionSeedStatus,
) -> str:
    return stable_hash({
        "accountability_packet_binding_set_hash": accountability_packet_binding_set_hash,
        "integration_summary_envelope_hash": integration_summary_envelope_hash,
        "accountability_packet_envelope_hash": accountability_packet_envelope_hash,
        "surface_eligibility_profile_hash": surface_eligibility_profile_hash,
        "projection_gap_matrix_hash": projection_gap_matrix_hash,
        "pre_projection_seed_envelope_hash": pre_projection_seed_envelope_hash,
        "source_label": source_label.value,
        "seed_status": seed_status.value,
    })


def _compute_pre_projection_seed_binding_set_hash(
    *,
    accountability_packet_binding_set_hash: str,
    integration_summary_envelope_hash: str,
    accountability_packet_envelope_hash: str,
    binding_hashes: tuple[str, ...],
    source_label: DelegationSourceLabel,
) -> str:
    return stable_hash({
        "accountability_packet_binding_set_hash": accountability_packet_binding_set_hash,
        "integration_summary_envelope_hash": integration_summary_envelope_hash,
        "accountability_packet_envelope_hash": accountability_packet_envelope_hash,
        "binding_hashes": list(binding_hashes),
        "source_label": source_label.value,
    })


def _compute_pre_projection_seed_status_report_hash(
    *,
    status_label: str,
    available_contracts: tuple[str, ...],
    unavailable_bindings: dict[str, str],
) -> str:
    return stable_hash({
        "status_label": status_label,
        "available_contracts": list(available_contracts),
        "unavailable_bindings": dict(unavailable_bindings),
    })


# ---------------------------------------------------------------------------
# Builder functions
# ---------------------------------------------------------------------------

def build_delegation_pre_projection_readiness_ref(
    *,
    pre_projection_readiness_ref_id: str,
    delegation_ref_id: str,
    pre_projection_readiness_ref: str | None = None,
    pre_projection_readiness_description: str = "",
    reference_status: DelegationPreProjectionSeedReferenceStatus | str = DelegationPreProjectionSeedReferenceStatus.REFERENCE_ONLY,
    source_label: DelegationSourceLabel | str = DelegationSourceLabel.DEV_FIXTURE,
    seed_status: DelegationPreProjectionSeedStatus | str = DelegationPreProjectionSeedStatus.REFERENCE_ONLY,
) -> DelegationPreProjectionReadinessRef:
    reference_status_val = _parse_pre_projection_seed_reference_status(reference_status)
    source_label_val = _parse_source_label(source_label)
    seed_status_val = _parse_pre_projection_seed_status(seed_status)
    readiness_hash_val = _compute_pre_projection_readiness_hash(
        pre_projection_readiness_ref=pre_projection_readiness_ref,
        pre_projection_readiness_description=pre_projection_readiness_description,
        reference_status=reference_status_val,
        source_label=source_label_val,
        seed_status=seed_status_val,
    )
    return DelegationPreProjectionReadinessRef(
        schema_version=DELEGATION_PRE_PROJECTION_READINESS_REF_VERSION,
        pre_projection_readiness_ref_id=pre_projection_readiness_ref_id,
        delegation_ref_id=delegation_ref_id,
        pre_projection_readiness_ref=pre_projection_readiness_ref,
        pre_projection_readiness_description=pre_projection_readiness_description,
        reference_status=reference_status_val,
        source_label=source_label_val,
        seed_status=seed_status_val,
        pre_projection_readiness_hash=readiness_hash_val,
    )


def build_delegation_surface_contract_seed_ref(
    *,
    surface_contract_seed_ref_id: str,
    delegation_ref_id: str,
    surface_contract_seed_ref: str | None = None,
    surface_contract_seed_description: str = "",
    reference_status: DelegationPreProjectionSeedReferenceStatus | str = DelegationPreProjectionSeedReferenceStatus.SURFACE_CONTRACT_SEED_REFERENCED,
    source_label: DelegationSourceLabel | str = DelegationSourceLabel.DEV_FIXTURE,
    seed_status: DelegationPreProjectionSeedStatus | str = DelegationPreProjectionSeedStatus.REFERENCE_ONLY,
) -> DelegationSurfaceContractSeedRef:
    reference_status_val = _parse_pre_projection_seed_reference_status(reference_status)
    source_label_val = _parse_source_label(source_label)
    seed_status_val = _parse_pre_projection_seed_status(seed_status)
    seed_hash_val = _compute_surface_contract_seed_hash(
        surface_contract_seed_ref=surface_contract_seed_ref,
        surface_contract_seed_description=surface_contract_seed_description,
        reference_status=reference_status_val,
        source_label=source_label_val,
        seed_status=seed_status_val,
    )
    return DelegationSurfaceContractSeedRef(
        schema_version=DELEGATION_SURFACE_CONTRACT_SEED_REF_VERSION,
        surface_contract_seed_ref_id=surface_contract_seed_ref_id,
        delegation_ref_id=delegation_ref_id,
        surface_contract_seed_ref=surface_contract_seed_ref,
        surface_contract_seed_description=surface_contract_seed_description,
        reference_status=reference_status_val,
        source_label=source_label_val,
        seed_status=seed_status_val,
        surface_contract_seed_hash=seed_hash_val,
    )


def build_delegation_read_model_seed_ref(
    *,
    read_model_seed_ref_id: str,
    delegation_ref_id: str,
    read_model_seed_ref: str | None = None,
    read_model_seed_description: str = "",
    reference_status: DelegationPreProjectionSeedReferenceStatus | str = DelegationPreProjectionSeedReferenceStatus.READ_MODEL_SEED_REFERENCED,
    source_label: DelegationSourceLabel | str = DelegationSourceLabel.DEV_FIXTURE,
    seed_status: DelegationPreProjectionSeedStatus | str = DelegationPreProjectionSeedStatus.REFERENCE_ONLY,
) -> DelegationReadModelSeedRef:
    reference_status_val = _parse_pre_projection_seed_reference_status(reference_status)
    source_label_val = _parse_source_label(source_label)
    seed_status_val = _parse_pre_projection_seed_status(seed_status)
    seed_hash_val = _compute_read_model_seed_hash(
        read_model_seed_ref=read_model_seed_ref,
        read_model_seed_description=read_model_seed_description,
        reference_status=reference_status_val,
        source_label=source_label_val,
        seed_status=seed_status_val,
    )
    return DelegationReadModelSeedRef(
        schema_version=DELEGATION_READ_MODEL_SEED_REF_VERSION,
        read_model_seed_ref_id=read_model_seed_ref_id,
        delegation_ref_id=delegation_ref_id,
        read_model_seed_ref=read_model_seed_ref,
        read_model_seed_description=read_model_seed_description,
        reference_status=reference_status_val,
        source_label=source_label_val,
        seed_status=seed_status_val,
        read_model_seed_hash=seed_hash_val,
    )


def build_delegation_api_contract_seed_ref(
    *,
    api_contract_seed_ref_id: str,
    delegation_ref_id: str,
    api_contract_seed_ref: str | None = None,
    api_contract_seed_description: str = "",
    reference_status: DelegationPreProjectionSeedReferenceStatus | str = DelegationPreProjectionSeedReferenceStatus.API_CONTRACT_SEED_REFERENCED,
    source_label: DelegationSourceLabel | str = DelegationSourceLabel.DEV_FIXTURE,
    seed_status: DelegationPreProjectionSeedStatus | str = DelegationPreProjectionSeedStatus.REFERENCE_ONLY,
) -> DelegationAPIContractSeedRef:
    reference_status_val = _parse_pre_projection_seed_reference_status(reference_status)
    source_label_val = _parse_source_label(source_label)
    seed_status_val = _parse_pre_projection_seed_status(seed_status)
    seed_hash_val = _compute_api_contract_seed_hash(
        api_contract_seed_ref=api_contract_seed_ref,
        api_contract_seed_description=api_contract_seed_description,
        reference_status=reference_status_val,
        source_label=source_label_val,
        seed_status=seed_status_val,
    )
    return DelegationAPIContractSeedRef(
        schema_version=DELEGATION_API_CONTRACT_SEED_REF_VERSION,
        api_contract_seed_ref_id=api_contract_seed_ref_id,
        delegation_ref_id=delegation_ref_id,
        api_contract_seed_ref=api_contract_seed_ref,
        api_contract_seed_description=api_contract_seed_description,
        reference_status=reference_status_val,
        source_label=source_label_val,
        seed_status=seed_status_val,
        api_contract_seed_hash=seed_hash_val,
    )


def build_delegation_event_contract_seed_ref(
    *,
    event_contract_seed_ref_id: str,
    delegation_ref_id: str,
    event_contract_seed_ref: str | None = None,
    event_contract_seed_description: str = "",
    reference_status: DelegationPreProjectionSeedReferenceStatus | str = DelegationPreProjectionSeedReferenceStatus.EVENT_CONTRACT_SEED_REFERENCED,
    source_label: DelegationSourceLabel | str = DelegationSourceLabel.DEV_FIXTURE,
    seed_status: DelegationPreProjectionSeedStatus | str = DelegationPreProjectionSeedStatus.REFERENCE_ONLY,
) -> DelegationEventContractSeedRef:
    reference_status_val = _parse_pre_projection_seed_reference_status(reference_status)
    source_label_val = _parse_source_label(source_label)
    seed_status_val = _parse_pre_projection_seed_status(seed_status)
    seed_hash_val = _compute_event_contract_seed_hash(
        event_contract_seed_ref=event_contract_seed_ref,
        event_contract_seed_description=event_contract_seed_description,
        reference_status=reference_status_val,
        source_label=source_label_val,
        seed_status=seed_status_val,
    )
    return DelegationEventContractSeedRef(
        schema_version=DELEGATION_EVENT_CONTRACT_SEED_REF_VERSION,
        event_contract_seed_ref_id=event_contract_seed_ref_id,
        delegation_ref_id=delegation_ref_id,
        event_contract_seed_ref=event_contract_seed_ref,
        event_contract_seed_description=event_contract_seed_description,
        reference_status=reference_status_val,
        source_label=source_label_val,
        seed_status=seed_status_val,
        event_contract_seed_hash=seed_hash_val,
    )


def build_delegation_surface_eligibility_entry(
    *,
    eligibility_entry_id: str,
    delegation_ref_id: str,
    field_ref: str = "",
    field_description: str = "",
    exposure_class: DelegationSurfaceExposureClass | str = DelegationSurfaceExposureClass.OPERATOR_VISIBLE_CANDIDATE,
    exposure_reason: str = "",
    source_label: DelegationSourceLabel | str = DelegationSourceLabel.DEV_FIXTURE,
) -> DelegationSurfaceEligibilityEntry:
    exposure_class_val = _parse_surface_exposure_class(exposure_class)
    source_label_val = _parse_source_label(source_label)
    entry_hash_val = _compute_surface_eligibility_entry_hash(
        field_ref=field_ref,
        field_description=field_description,
        exposure_class=exposure_class_val,
        exposure_reason=exposure_reason,
        source_label=source_label_val,
    )
    return DelegationSurfaceEligibilityEntry(
        schema_version=DELEGATION_SURFACE_ELIGIBILITY_ENTRY_VERSION,
        eligibility_entry_id=eligibility_entry_id,
        delegation_ref_id=delegation_ref_id,
        field_ref=field_ref,
        field_description=field_description,
        exposure_class=exposure_class_val,
        exposure_reason=exposure_reason,
        source_label=source_label_val,
        entry_hash=entry_hash_val,
    )


def build_delegation_surface_eligibility_profile(
    *,
    surface_eligibility_profile_id: str,
    delegation_ref_id: str,
    entries: Sequence[DelegationSurfaceEligibilityEntry] = (),
    source_label: DelegationSourceLabel | str = DelegationSourceLabel.DEV_FIXTURE,
) -> DelegationSurfaceEligibilityProfile:
    source_label_val = _parse_source_label(source_label)
    entries_tuple = tuple(entries)
    entry_hashes = tuple(e.entry_hash for e in entries_tuple)
    # Compute counts deterministically
    operator_visible = sum(1 for e in entries_tuple if e.exposure_class == DelegationSurfaceExposureClass.OPERATOR_VISIBLE_CANDIDATE)
    internal_only = sum(1 for e in entries_tuple if e.exposure_class == DelegationSurfaceExposureClass.INTERNAL_ONLY)
    governance_only = sum(1 for e in entries_tuple if e.exposure_class == DelegationSurfaceExposureClass.GOVERNANCE_ONLY)
    trace_only = sum(1 for e in entries_tuple if e.exposure_class == DelegationSurfaceExposureClass.TRACE_CONTEXT_ONLY)
    policy_only = sum(1 for e in entries_tuple if e.exposure_class == DelegationSurfaceExposureClass.POLICY_CONTEXT_ONLY)
    runtime_only = sum(1 for e in entries_tuple if e.exposure_class == DelegationSurfaceExposureClass.RUNTIME_CONTEXT_ONLY)
    redacted = sum(1 for e in entries_tuple if e.exposure_class == DelegationSurfaceExposureClass.REDACTED_CANDIDATE)
    unavailable = sum(1 for e in entries_tuple if e.exposure_class == DelegationSurfaceExposureClass.UNAVAILABLE)
    profile_hash_val = _compute_surface_eligibility_profile_hash(
        entry_hashes=entry_hashes,
        operator_visible_candidate_count=operator_visible,
        internal_only_count=internal_only,
        governance_only_count=governance_only,
        trace_context_only_count=trace_only,
        policy_context_only_count=policy_only,
        runtime_context_only_count=runtime_only,
        redacted_candidate_count=redacted,
        unavailable_count=unavailable,
        source_label=source_label_val,
    )
    return DelegationSurfaceEligibilityProfile(
        schema_version=DELEGATION_SURFACE_ELIGIBILITY_PROFILE_VERSION,
        surface_eligibility_profile_id=surface_eligibility_profile_id,
        delegation_ref_id=delegation_ref_id,
        entries=entries_tuple,
        operator_visible_candidate_count=operator_visible,
        internal_only_count=internal_only,
        governance_only_count=governance_only,
        trace_context_only_count=trace_only,
        policy_context_only_count=policy_only,
        runtime_context_only_count=runtime_only,
        redacted_candidate_count=redacted,
        unavailable_count=unavailable,
        source_label=source_label_val,
        surface_eligibility_profile_hash=profile_hash_val,
    )


def build_delegation_projection_gap_matrix_entry(
    *,
    entry_id: str,
    delegation_ref_id: str,
    family: DelegationProjectionSeedFamily | str = DelegationProjectionSeedFamily.UNKNOWN,
    present: bool = False,
    hash_present: bool = False,
    source_label_present: bool = False,
    finding_count: int = 0,
    unavailable_reason: str = "",
    source_label: DelegationSourceLabel | str = DelegationSourceLabel.DEV_FIXTURE,
) -> DelegationProjectionGapMatrixEntry:
    family_val = _parse_projection_seed_family(family)
    source_label_val = _parse_source_label(source_label)
    entry_hash_val = _compute_projection_gap_matrix_entry_hash(
        family=family_val,
        present=present,
        hash_present=hash_present,
        source_label_present=source_label_present,
        finding_count=finding_count,
        unavailable_reason=unavailable_reason,
        source_label=source_label_val,
    )
    return DelegationProjectionGapMatrixEntry(
        schema_version=DELEGATION_PROJECTION_GAP_MATRIX_ENTRY_VERSION,
        entry_id=entry_id,
        delegation_ref_id=delegation_ref_id,
        family=family_val,
        present=present,
        hash_present=hash_present,
        source_label_present=source_label_present,
        finding_count=finding_count,
        unavailable_reason=unavailable_reason,
        source_label=source_label_val,
        entry_hash=entry_hash_val,
    )


def build_delegation_projection_gap_matrix(
    *,
    projection_gap_matrix_id: str,
    delegation_ref_id: str,
    entries: Sequence[DelegationProjectionGapMatrixEntry] = (),
    source_label: DelegationSourceLabel | str = DelegationSourceLabel.DEV_FIXTURE,
) -> DelegationProjectionGapMatrix:
    source_label_val = _parse_source_label(source_label)
    entries_tuple = tuple(entries)
    entry_hashes = tuple(e.entry_hash for e in entries_tuple)
    matrix_hash_val = _compute_projection_gap_matrix_hash(
        entry_hashes=entry_hashes,
        source_label=source_label_val,
    )
    return DelegationProjectionGapMatrix(
        schema_version=DELEGATION_PROJECTION_GAP_MATRIX_VERSION,
        projection_gap_matrix_id=projection_gap_matrix_id,
        delegation_ref_id=delegation_ref_id,
        entries=entries_tuple,
        source_label=source_label_val,
        projection_gap_matrix_hash=matrix_hash_val,
    )


def build_delegation_pre_projection_seed_envelope(
    *,
    pre_projection_seed_envelope_id: str,
    delegation_ref_id: str,
    accountability_packet_binding_set_hash: str = "",
    integration_summary_envelope_hash: str = "",
    accountability_packet_envelope_hash: str = "",
    surface_eligibility_profile_hash: str = "",
    projection_gap_matrix_hash: str = "",
    read_model_seed_refs: str | None = None,
    api_contract_seed_refs: str | None = None,
    event_contract_seed_refs: str | None = None,
    surface_contract_seed_refs: str | None = None,
    golden_thread_ref: str = "",
    next_handoff_ref: str = "",
    source_label: DelegationSourceLabel | str = DelegationSourceLabel.DEV_FIXTURE,
) -> DelegationPreProjectionSeedEnvelope:
    source_label_val = _parse_source_label(source_label)
    _ = _required_string(pre_projection_seed_envelope_id, field_name="pre_projection_seed_envelope_id")
    envelope_hash_val = _compute_pre_projection_seed_envelope_hash(
        accountability_packet_binding_set_hash=accountability_packet_binding_set_hash,
        integration_summary_envelope_hash=integration_summary_envelope_hash,
        accountability_packet_envelope_hash=accountability_packet_envelope_hash,
        surface_eligibility_profile_hash=surface_eligibility_profile_hash,
        projection_gap_matrix_hash=projection_gap_matrix_hash,
        read_model_seed_refs=read_model_seed_refs,
        api_contract_seed_refs=api_contract_seed_refs,
        event_contract_seed_refs=event_contract_seed_refs,
        surface_contract_seed_refs=surface_contract_seed_refs,
        golden_thread_ref=golden_thread_ref,
        next_handoff_ref=next_handoff_ref,
        source_label=source_label_val,
    )
    return DelegationPreProjectionSeedEnvelope(
        schema_version=DELEGATION_PRE_PROJECTION_SEED_ENVELOPE_VERSION,
        pre_projection_seed_envelope_id=pre_projection_seed_envelope_id,
        delegation_ref_id=delegation_ref_id,
        accountability_packet_binding_set_hash=accountability_packet_binding_set_hash,
        integration_summary_envelope_hash=integration_summary_envelope_hash,
        accountability_packet_envelope_hash=accountability_packet_envelope_hash,
        surface_eligibility_profile_hash=surface_eligibility_profile_hash,
        projection_gap_matrix_hash=projection_gap_matrix_hash,
        read_model_seed_refs=read_model_seed_refs,
        api_contract_seed_refs=api_contract_seed_refs,
        event_contract_seed_refs=event_contract_seed_refs,
        surface_contract_seed_refs=surface_contract_seed_refs,
        golden_thread_ref=golden_thread_ref,
        next_handoff_ref=next_handoff_ref,
        source_label=source_label_val,
        pre_projection_seed_envelope_hash=envelope_hash_val,
    )


def build_delegation_pre_projection_seed_binding(
    *,
    binding_id: str,
    delegation_ref_id: str,
    accountability_packet_binding_set_hash: str = "",
    integration_summary_envelope_hash: str = "",
    accountability_packet_envelope_hash: str = "",
    surface_eligibility_profile_hash: str = "",
    projection_gap_matrix_hash: str = "",
    pre_projection_seed_envelope_hash: str = "",
    source_label: DelegationSourceLabel | str = DelegationSourceLabel.DEV_FIXTURE,
    seed_status: DelegationPreProjectionSeedStatus | str = DelegationPreProjectionSeedStatus.REFERENCE_ONLY,
) -> DelegationPreProjectionSeedBinding:
    source_label_val = _parse_source_label(source_label)
    seed_status_val = _parse_pre_projection_seed_status(seed_status)
    binding_hash_val = _compute_pre_projection_seed_binding_hash(
        accountability_packet_binding_set_hash=accountability_packet_binding_set_hash,
        integration_summary_envelope_hash=integration_summary_envelope_hash,
        accountability_packet_envelope_hash=accountability_packet_envelope_hash,
        surface_eligibility_profile_hash=surface_eligibility_profile_hash,
        projection_gap_matrix_hash=projection_gap_matrix_hash,
        pre_projection_seed_envelope_hash=pre_projection_seed_envelope_hash,
        source_label=source_label_val,
        seed_status=seed_status_val,
    )
    return DelegationPreProjectionSeedBinding(
        schema_version=DELEGATION_PRE_PROJECTION_SEED_BINDING_VERSION,
        binding_id=binding_id,
        delegation_ref_id=delegation_ref_id,
        accountability_packet_binding_set_hash=accountability_packet_binding_set_hash,
        integration_summary_envelope_hash=integration_summary_envelope_hash,
        accountability_packet_envelope_hash=accountability_packet_envelope_hash,
        surface_eligibility_profile_hash=surface_eligibility_profile_hash,
        projection_gap_matrix_hash=projection_gap_matrix_hash,
        pre_projection_seed_envelope_hash=pre_projection_seed_envelope_hash,
        source_label=source_label_val,
        seed_status=seed_status_val,
        binding_hash=binding_hash_val,
    )


def build_delegation_pre_projection_seed_binding_set(
    *,
    pre_projection_seed_binding_set_id: str,
    delegation_ref_id: str,
    accountability_packet_binding_set_hash: str = "",
    integration_summary_envelope_hash: str = "",
    accountability_packet_envelope_hash: str = "",
    bindings: Sequence[DelegationPreProjectionSeedBinding] = (),
    source_label: DelegationSourceLabel | str = DelegationSourceLabel.DEV_FIXTURE,
) -> DelegationPreProjectionSeedBindingSet:
    source_label_val = _parse_source_label(source_label)
    bindings_tuple = tuple(bindings)
    binding_hashes = tuple(b.binding_hash for b in bindings_tuple)
    side_effects_val = DelegationPreProjectionSeedSideEffects(
        projection_created=False,
        read_model_created=False,
        api_contract_created=False,
        event_contract_created=False,
        surface_contract_created=False,
        cli_shell_tui_bound=False,
        ui_surface_created=False,
        field_exposed=False,
        redaction_enforced=False,
        policy_decision_emitted=False,
        custos_decision_emitted=False,
        runtime_executed=False,
        trace_written=False,
        ledger_written=False,
        output_passport_created=False,
        global_trace_written=False,
        runtime_mutated=False,
    )
    binding_set_hash_val = _compute_pre_projection_seed_binding_set_hash(
        accountability_packet_binding_set_hash=accountability_packet_binding_set_hash,
        integration_summary_envelope_hash=integration_summary_envelope_hash,
        accountability_packet_envelope_hash=accountability_packet_envelope_hash,
        binding_hashes=binding_hashes,
        source_label=source_label_val,
    )
    return DelegationPreProjectionSeedBindingSet(
        schema_version=DELEGATION_PRE_PROJECTION_SEED_BINDING_SET_VERSION,
        pre_projection_seed_binding_set_id=pre_projection_seed_binding_set_id,
        delegation_ref_id=delegation_ref_id,
        accountability_packet_binding_set_hash=accountability_packet_binding_set_hash,
        integration_summary_envelope_hash=integration_summary_envelope_hash,
        accountability_packet_envelope_hash=accountability_packet_envelope_hash,
        bindings=bindings_tuple,
        side_effects=side_effects_val,
        source_label=source_label_val,
        pre_projection_seed_binding_set_hash=binding_set_hash_val,
    )


def build_delegation_pre_projection_seed_status_report(
    *,
    status_label: str = "P1.8.16: reference-only pre-projection seed metadata layer",
    available_contracts: Sequence[str] = (),
    unavailable_bindings: dict[str, str] | None = None,
) -> DelegationPreProjectionSeedStatusReport:
    available_contracts_tuple = tuple(available_contracts)
    unavailable = (
        dict(unavailable_bindings)
        if unavailable_bindings is not None
        else dict(DELEGATION_PRE_PROJECTION_SEED_UNAVAILABLE_BINDINGS)
    )
    side_effects_val = DelegationPreProjectionSeedSideEffects(
        projection_created=False,
        read_model_created=False,
        api_contract_created=False,
        event_contract_created=False,
        surface_contract_created=False,
        cli_shell_tui_bound=False,
        ui_surface_created=False,
        field_exposed=False,
        redaction_enforced=False,
        policy_decision_emitted=False,
        custos_decision_emitted=False,
        runtime_executed=False,
        trace_written=False,
        ledger_written=False,
        output_passport_created=False,
        global_trace_written=False,
        runtime_mutated=False,
    )
    status_hash_val = _compute_pre_projection_seed_status_report_hash(
        status_label=status_label,
        available_contracts=available_contracts_tuple,
        unavailable_bindings=unavailable,
    )
    return DelegationPreProjectionSeedStatusReport(
        schema_version=DELEGATION_PRE_PROJECTION_SEED_STATUS_REPORT_VERSION,
        status_label=status_label,
        available_contracts=available_contracts_tuple,
        unavailable_bindings=unavailable,
        side_effects=side_effects_val,
        status_hash=status_hash_val,
    )


# ---------------------------------------------------------------------------
# Hash functions (public)
# ---------------------------------------------------------------------------

def hash_delegation_pre_projection_readiness_ref(
    ref: DelegationPreProjectionReadinessRef,
) -> str:
    return ref.pre_projection_readiness_hash


def hash_delegation_surface_contract_seed_ref(
    ref: DelegationSurfaceContractSeedRef,
) -> str:
    return ref.surface_contract_seed_hash


def hash_delegation_read_model_seed_ref(
    ref: DelegationReadModelSeedRef,
) -> str:
    return ref.read_model_seed_hash


def hash_delegation_api_contract_seed_ref(
    ref: DelegationAPIContractSeedRef,
) -> str:
    return ref.api_contract_seed_hash


def hash_delegation_event_contract_seed_ref(
    ref: DelegationEventContractSeedRef,
) -> str:
    return ref.event_contract_seed_hash


def hash_delegation_surface_eligibility_entry(
    entry: DelegationSurfaceEligibilityEntry,
) -> str:
    return entry.entry_hash


def hash_delegation_surface_eligibility_profile(
    profile: DelegationSurfaceEligibilityProfile,
) -> str:
    return profile.surface_eligibility_profile_hash


def hash_delegation_projection_gap_matrix_entry(
    entry: DelegationProjectionGapMatrixEntry,
) -> str:
    return entry.entry_hash


def hash_delegation_projection_gap_matrix(
    matrix: DelegationProjectionGapMatrix,
) -> str:
    return matrix.projection_gap_matrix_hash


def hash_delegation_pre_projection_seed_envelope(
    envelope: DelegationPreProjectionSeedEnvelope,
) -> str:
    return envelope.pre_projection_seed_envelope_hash


def hash_delegation_pre_projection_seed_binding(
    binding: DelegationPreProjectionSeedBinding,
) -> str:
    return binding.binding_hash


def hash_delegation_pre_projection_seed_binding_set(
    binding_set: DelegationPreProjectionSeedBindingSet,
) -> str:
    return binding_set.pre_projection_seed_binding_set_hash


def hash_delegation_pre_projection_seed_status_report(
    report: DelegationPreProjectionSeedStatusReport,
) -> str:
    return report.status_hash


# ---------------------------------------------------------------------------
# Serialize functions
# ---------------------------------------------------------------------------

def serialize_delegation_pre_projection_seed_envelope(
    envelope: DelegationPreProjectionSeedEnvelope,
) -> str:
    """Produce deterministic canonical JSON of a pre-projection seed envelope."""
    validate_known_fields(
        {f.name: getattr(envelope, f.name) for f in envelope.__dataclass_fields__.values()},
        PRE_PROJECTION_SEED_ENVELOPE_KNOWN_FIELDS,
        label="DelegationPreProjectionSeedEnvelope",
    )
    payload: dict[str, Any] = {
        "schema_version": envelope.schema_version,
        "pre_projection_seed_envelope_id": envelope.pre_projection_seed_envelope_id,
        "delegation_ref_id": envelope.delegation_ref_id,
        "accountability_packet_binding_set_hash": envelope.accountability_packet_binding_set_hash,
        "integration_summary_envelope_hash": envelope.integration_summary_envelope_hash,
        "accountability_packet_envelope_hash": envelope.accountability_packet_envelope_hash,
        "surface_eligibility_profile_hash": envelope.surface_eligibility_profile_hash,
        "projection_gap_matrix_hash": envelope.projection_gap_matrix_hash,
        "read_model_seed_refs": envelope.read_model_seed_refs,
        "api_contract_seed_refs": envelope.api_contract_seed_refs,
        "event_contract_seed_refs": envelope.event_contract_seed_refs,
        "surface_contract_seed_refs": envelope.surface_contract_seed_refs,
        "golden_thread_ref": envelope.golden_thread_ref,
        "next_handoff_ref": envelope.next_handoff_ref,
        "source_label": envelope.source_label.value,
        "pre_projection_seed_envelope_hash": envelope.pre_projection_seed_envelope_hash,
    }
    return to_canonical_json(payload)


def serialize_delegation_pre_projection_seed_binding_set(
    binding_set: DelegationPreProjectionSeedBindingSet,
) -> str:
    """Produce deterministic canonical JSON of a pre-projection seed binding set."""
    validate_known_fields(
        {f.name: getattr(binding_set, f.name) for f in binding_set.__dataclass_fields__.values()},
        PRE_PROJECTION_SEED_BINDING_SET_KNOWN_FIELDS,
        label="DelegationPreProjectionSeedBindingSet",
    )
    payload: dict[str, Any] = {
        "schema_version": binding_set.schema_version,
        "pre_projection_seed_binding_set_id": binding_set.pre_projection_seed_binding_set_id,
        "delegation_ref_id": binding_set.delegation_ref_id,
        "accountability_packet_binding_set_hash": binding_set.accountability_packet_binding_set_hash,
        "integration_summary_envelope_hash": binding_set.integration_summary_envelope_hash,
        "accountability_packet_envelope_hash": binding_set.accountability_packet_envelope_hash,
        "bindings": [
            {
                "binding_id": b.binding_id,
                "delegation_ref_id": b.delegation_ref_id,
                "accountability_packet_binding_set_hash": b.accountability_packet_binding_set_hash,
                "integration_summary_envelope_hash": b.integration_summary_envelope_hash,
                "accountability_packet_envelope_hash": b.accountability_packet_envelope_hash,
                "surface_eligibility_profile_hash": b.surface_eligibility_profile_hash,
                "projection_gap_matrix_hash": b.projection_gap_matrix_hash,
                "pre_projection_seed_envelope_hash": b.pre_projection_seed_envelope_hash,
                "source_label": b.source_label.value,
                "seed_status": b.seed_status.value,
                "binding_hash": b.binding_hash,
            }
            for b in binding_set.bindings
        ],
        "side_effects": {
            "projection_created": binding_set.side_effects.projection_created,
            "read_model_created": binding_set.side_effects.read_model_created,
            "api_contract_created": binding_set.side_effects.api_contract_created,
            "event_contract_created": binding_set.side_effects.event_contract_created,
            "surface_contract_created": binding_set.side_effects.surface_contract_created,
            "cli_shell_tui_bound": binding_set.side_effects.cli_shell_tui_bound,
            "ui_surface_created": binding_set.side_effects.ui_surface_created,
            "field_exposed": binding_set.side_effects.field_exposed,
            "redaction_enforced": binding_set.side_effects.redaction_enforced,
            "policy_decision_emitted": binding_set.side_effects.policy_decision_emitted,
            "custos_decision_emitted": binding_set.side_effects.custos_decision_emitted,
            "runtime_executed": binding_set.side_effects.runtime_executed,
            "trace_written": binding_set.side_effects.trace_written,
            "ledger_written": binding_set.side_effects.ledger_written,
            "output_passport_created": binding_set.side_effects.output_passport_created,
            "global_trace_written": binding_set.side_effects.global_trace_written,
            "runtime_mutated": binding_set.side_effects.runtime_mutated,
        },
        "source_label": binding_set.source_label.value,
        "pre_projection_seed_binding_set_hash": binding_set.pre_projection_seed_binding_set_hash,
    }
    return to_canonical_json(payload)
