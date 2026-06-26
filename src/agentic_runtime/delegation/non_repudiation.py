"""Delegation evidence / non-repudiation reference binding (P1.8.5).

Deterministic, versioned, JSON-safe, side-effect-free evidence hook for
delegation accountability. Binds reference-only evidence, claim,
attestation, signature, and trace refs to DelegationRef / DelegationIdentity /
DelegationRoleBindingSet / DelegationConstraintSet /
DelegationAuthorityBindingSet without verifying evidence, proving claims,
verifying signatures, verifying trace, claiming legal finality, writing
Ledger, writing global trace, or creating Output Passport behavior.

Architectural law:
  - NonRepudiationRef exists ≠ non-repudiation is proven.
  - EvidenceRef exists ≠ evidence is verified.
  - ClaimRef exists ≠ claim is proven.
  - AttestationRef exists ≠ attestation is verified.
  - SignatureRef exists ≠ signature is verified.
  - TraceRef exists ≠ TRACE_VERIFIED.
  - EvidenceEnvelope exists ≠ legal finality.
  - CompletenessProfile exists ≠ trust score.
  - Evidence hash exists ≠ proof.
  - DelegationEvidenceRef describes an evidence reference; it does not verify
    evidence, prove truth, verify signature, verify trace, or write
    Ledger/global trace.
  - DelegationEvidenceEnvelope is a reference packet; it is not proof, not
    legal finality, not TRACE_VERIFIED, and does not verify evidence,
    signatures, traces, claims, or attestations.
  - DelegationEvidenceCompletenessProfile is not trust score, not
    verification, not proof, not legal finality.
  - DelegationNonRepudiationBinding binds evidence metadata; it is not proof,
    not verification, not legal finality, not trace verification.
  - DelegationNonRepudiationBindingSet describes evidence/non-repudiation
    hooks; it does not prove non-repudiation, does not verify evidence, does
    not verify signatures, does not verify trace, does not write
    Ledger/global trace.
  - evidence_envelope_hash exists ≠ legal finality.
  - non_repudiation_binding_set_hash exists ≠ proof of non-repudiation.
"""
from __future__ import annotations

from collections.abc import Mapping as MappingABC, Sequence
from dataclasses import dataclass, field, fields
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping

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

DELEGATION_NON_REPUDIATION_TASK_ID = "P1.8.5"
DELEGATION_EVIDENCE_REF_VERSION = "delegation_evidence_ref.v1"
DELEGATION_CLAIM_REF_VERSION = "delegation_claim_ref.v1"
DELEGATION_EVIDENCE_ENVELOPE_VERSION = "delegation_evidence_envelope.v1"
DELEGATION_EVIDENCE_COMPLETENESS_PROFILE_VERSION = (
    "delegation_evidence_completeness_profile.v1"
)
DELEGATION_NON_REPUDIATION_BINDING_VERSION = "delegation_non_repudiation_binding.v1"
DELEGATION_NON_REPUDIATION_BINDING_SET_VERSION = (
    "delegation_non_repudiation_binding_set.v1"
)
DELEGATION_NON_REPUDIATION_SIDE_EFFECTS_VERSION = (
    "delegation_non_repudiation_side_effects.v1"
)
DELEGATION_NON_REPUDIATION_STATUS_REPORT_VERSION = (
    "delegation_non_repudiation_status_report.v1"
)

DELEGATION_NON_REPUDIATION_UNAVAILABLE_BINDINGS: dict[str, str] = {
    "Projection/API/Event/Read Model": (
        "Projection/API/event/read model is not available in P1.8.5; "
        "evidence/non-repudiation schema only"
    ),
    "CLI/Shell/TUI Binding": (
        "CLI/Shell/TUI binding scheduled for later P1.8 tasks; not P1.8.5"
    ),
    "Ledger Write": (
        "Ledger write is not available in P1.8.5 "
        "evidence/non-repudiation reference binding"
    ),
    "Global Trace Write": (
        "Global trace spine write is not available in P1.8.5 "
        "evidence/non-repudiation reference binding"
    ),
    "Crypto Verifier": (
        "Cryptographic signature verification scheduled for later P1.8 tasks; "
        "not P1.8.5"
    ),
    "Signature Verifier": (
        "Signature verifier scheduled for later P1.8 tasks; not P1.8.5"
    ),
    "Trace Verifier": (
        "Trace verifier scheduled for later P1.8 tasks; not P1.8.5"
    ),
    "Evidence Truth Verifier": (
        "Evidence truth verifier scheduled for later P1.8 tasks; not P1.8.5"
    ),
    "Claim Verifier": (
        "Claim verifier scheduled for later P1.8 tasks; not P1.8.5"
    ),
    "Attestation Verifier": (
        "Attestation verifier scheduled for later P1.8 tasks; not P1.8.5"
    ),
    "Legal Non-Repudiation Engine": (
        "Legal non-repudiation engine scheduled for later P1.8 tasks; "
        "not P1.8.5"
    ),
    "Dispute Resolver": (
        "Dispute resolver scheduled for later P1.8 tasks; not P1.8.5"
    ),
    "Output Passport / P1.9": (
        "Output Passport is P1.9 scope; not P1.8.5"
    ),
    "Identity Mesh Binding / P1.8.6": (
        "Identity mesh binding is P1.8.6; not P1.8.5"
    ),
    "Runtime Delegation Execution": (
        "Runtime delegation execution is not available in P1.8.5"
    ),
    "Policy/Custos Decision": (
        "Policy/Custos decision scheduled for later P1.8 tasks; not P1.8.5"
    ),
}

EVIDENCE_REF_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "evidence_ref_id",
    "delegation_ref_id",
    "evidence_kind",
    "evidence_uri_ref",
    "evidence_hash_ref",
    "evidence_description",
    "proof_status",
    "source_label",
    "evidence_status",
    "evidence_ref_hash",
})

CLAIM_REF_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "claim_ref_id",
    "delegation_ref_id",
    "claim_subject_ref",
    "claim_statement",
    "claim_context_ref",
    "proof_status",
    "source_label",
    "claim_status",
    "claim_ref_hash",
})

EVIDENCE_ENVELOPE_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "evidence_envelope_id",
    "delegation_ref_id",
    "delegation_identity_hash",
    "role_binding_hash",
    "constraint_set_hash",
    "authority_binding_set_hash",
    "evidence_refs",
    "claim_refs",
    "attestation_refs",
    "signature_refs",
    "trace_refs",
    "proof_status",
    "source_label",
    "evidence_envelope_hash",
})

COMPLETENESS_PROFILE_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "profile_id",
    "delegation_ref_id",
    "evidence_envelope_hash",
    "has_delegation_identity",
    "has_role_binding",
    "has_constraints",
    "has_authority_refs",
    "has_evidence_refs",
    "has_claim_refs",
    "has_attestation_refs",
    "has_signature_refs",
    "has_trace_refs",
    "missing_components",
    "source_label",
    "profile_hash",
})

NON_REPUDIATION_BINDING_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "binding_id",
    "delegation_ref_id",
    "delegation_identity_hash",
    "role_binding_hash",
    "constraint_set_hash",
    "authority_binding_set_hash",
    "evidence_envelope_hash",
    "completeness_profile_hash",
    "source_label",
    "proof_status",
    "binding_hash",
})

NON_REPUDIATION_BINDING_SET_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "non_repudiation_binding_set_id",
    "delegation_ref_id",
    "delegation_identity_hash",
    "role_binding_hash",
    "constraint_set_hash",
    "authority_binding_set_hash",
    "bindings",
    "source_label",
    "non_repudiation_binding_set_hash",
    "side_effects",
})

NON_REPUDIATION_SIDE_EFFECTS_KNOWN_FIELDS: frozenset[str] = frozenset({
    "crypto_verified",
    "signature_verified",
    "trace_verified",
    "evidence_verified",
    "claim_verified",
    "attestation_verified",
    "ledger_written",
    "global_trace_written",
    "policy_called",
    "custos_called",
    "approval_created",
    "runtime_mutated",
    "non_repudiation_proven",
    "legal_finality_claimed",
})

NON_REPUDIATION_STATUS_REPORT_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "status_label",
    "available_contracts",
    "unavailable_bindings",
    "side_effects",
    "status_hash",
})


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class DelegationEvidenceKind(str, Enum):
    """Classifies the referenced evidence type.

    Evidence kind classifies the evidence reference type.
    It does not verify the evidence, signature, trace, attestation, or claim.
    """

    DOCUMENT_REF = "DOCUMENT_REF"
    ARTIFACT_REF = "ARTIFACT_REF"
    TRACE_REF = "TRACE_REF"
    SIGNATURE_REF = "SIGNATURE_REF"
    ATTESTATION_REF = "ATTESTATION_REF"
    OPERATOR_STATEMENT_REF = "OPERATOR_STATEMENT_REF"
    SYSTEM_EVENT_REF = "SYSTEM_EVENT_REF"
    EXTERNAL_REF = "EXTERNAL_REF"
    UNKNOWN = "UNKNOWN"


class DelegationEvidenceStatus(str, Enum):
    """Declared evidence reference availability.

    REFERENCE_ONLY means evidence context is reference-only.
    DECLARED means evidence context was declared as metadata.
    Neither means evidence is verified, claim is proven, signature is
    verified, trace is verified, or legal non-repudiation is final.
    """

    REFERENCE_ONLY = "REFERENCE_ONLY"
    DECLARED = "DECLARED"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"
    UNKNOWN = "UNKNOWN"


class DelegationProofReferenceStatus(str, Enum):
    """Proof / verification status ladder for evidence references.

    TRACE_REFERENCED is not TRACE_VERIFIED.
    SIGNATURE_REFERENCED is not signature verified.
    EVIDENCE_REFERENCED is not evidence proven true.
    CLAIM_REFERENCED is not claim proven.
    ATTESTATION_REFERENCED is not attestation verified.
    VERIFIER_UNAVAILABLE is honest unavailability, not failure or success.
    """

    REFERENCE_ONLY = "REFERENCE_ONLY"
    EVIDENCE_REFERENCED = "EVIDENCE_REFERENCED"
    CLAIM_REFERENCED = "CLAIM_REFERENCED"
    ATTESTATION_REFERENCED = "ATTESTATION_REFERENCED"
    SIGNATURE_REFERENCED = "SIGNATURE_REFERENCED"
    TRACE_REFERENCED = "TRACE_REFERENCED"
    VERIFIER_UNAVAILABLE = "VERIFIER_UNAVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"
    UNKNOWN = "UNKNOWN"


class DelegationDisputeReadinessStatus(str, Enum):
    """Dispute readiness classification.

    Dispute ref exists does not mean dispute is resolved.
    Dispute status exists does not mean legal process exists.
    """

    NOT_EVALUATED = "NOT_EVALUATED"
    DISPUTE_REF_AVAILABLE = "DISPUTE_REF_AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"
    UNKNOWN = "UNKNOWN"


# ---------------------------------------------------------------------------
# Enum parsers
# ---------------------------------------------------------------------------


def _parse_evidence_kind(
    value: DelegationEvidenceKind | str,
) -> DelegationEvidenceKind:
    if isinstance(value, DelegationEvidenceKind):
        return value
    if isinstance(value, str):
        try:
            return DelegationEvidenceKind(value)
        except ValueError as exc:
            raise DelegationError(
                f"invalid evidence_kind: {value!r}",
                code=DelegationErrorCode.INVALID_ENUM,
                field="evidence_kind",
            ) from exc
    raise DelegationError(
        "evidence_kind must be a string or DelegationEvidenceKind",
        code=DelegationErrorCode.INVALID_ENUM,
        field="evidence_kind",
    )


def _parse_evidence_status(
    value: DelegationEvidenceStatus | str,
) -> DelegationEvidenceStatus:
    if isinstance(value, DelegationEvidenceStatus):
        return value
    if isinstance(value, str):
        try:
            return DelegationEvidenceStatus(value)
        except ValueError as exc:
            raise DelegationError(
                f"invalid evidence_status: {value!r}",
                code=DelegationErrorCode.INVALID_ENUM,
                field="evidence_status",
            ) from exc
    raise DelegationError(
        "evidence_status must be a string or DelegationEvidenceStatus",
        code=DelegationErrorCode.INVALID_ENUM,
        field="evidence_status",
    )


def _parse_proof_reference_status(
    value: DelegationProofReferenceStatus | str,
) -> DelegationProofReferenceStatus:
    if isinstance(value, DelegationProofReferenceStatus):
        return value
    if isinstance(value, str):
        try:
            return DelegationProofReferenceStatus(value)
        except ValueError as exc:
            raise DelegationError(
                f"invalid proof_status: {value!r}",
                code=DelegationErrorCode.INVALID_ENUM,
                field="proof_status",
            ) from exc
    raise DelegationError(
        "proof_status must be a string or DelegationProofReferenceStatus",
        code=DelegationErrorCode.INVALID_ENUM,
        field="proof_status",
    )


def _parse_dispute_readiness_status(
    value: DelegationDisputeReadinessStatus | str,
) -> DelegationDisputeReadinessStatus:
    if isinstance(value, DelegationDisputeReadinessStatus):
        return value
    if isinstance(value, str):
        try:
            return DelegationDisputeReadinessStatus(value)
        except ValueError as exc:
            raise DelegationError(
                f"invalid dispute_readiness_status: {value!r}",
                code=DelegationErrorCode.INVALID_ENUM,
                field="dispute_readiness_status",
            ) from exc
    raise DelegationError(
        "dispute_readiness_status must be a string or "
        "DelegationDisputeReadinessStatus",
        code=DelegationErrorCode.INVALID_ENUM,
        field="dispute_readiness_status",
    )


# ---------------------------------------------------------------------------
# DelegationEvidenceRef
# ---------------------------------------------------------------------------


def compute_evidence_ref_hash(
    *,
    delegation_ref_id: str,
    evidence_kind: DelegationEvidenceKind,
    evidence_uri_ref: str | None,
    evidence_hash_ref: str | None,
    evidence_description: str,
    proof_status: DelegationProofReferenceStatus,
    source_label: DelegationSourceLabel,
    evidence_status: DelegationEvidenceStatus,
    schema_version: str = DELEGATION_EVIDENCE_REF_VERSION,
) -> str:
    """Deterministic hash of evidence reference content."""
    payload: dict[str, Any] = {
        "delegation_ref_id": delegation_ref_id,
        "evidence_description": evidence_description,
        "evidence_kind": evidence_kind.value,
        "evidence_status": evidence_status.value,
        "proof_status": proof_status.value,
        "schema_version": schema_version,
        "source_label": source_label.value,
    }
    if evidence_uri_ref is not None:
        payload["evidence_uri_ref"] = evidence_uri_ref
    if evidence_hash_ref is not None:
        payload["evidence_hash_ref"] = evidence_hash_ref
    return stable_hash(payload)


@dataclass(frozen=True)
class DelegationEvidenceRef:
    """One reference-only evidence object.

    DelegationEvidenceRef describes an evidence reference.
    It does not verify evidence.
    It does not prove truth.
    It does not verify signature.
    It does not verify trace.
    It does not write Ledger or global trace.
    """

    delegation_ref_id: str
    evidence_kind: DelegationEvidenceKind
    evidence_description: str
    evidence_uri_ref: str | None = None
    evidence_hash_ref: str | None = None
    proof_status: DelegationProofReferenceStatus = (
        DelegationProofReferenceStatus.REFERENCE_ONLY
    )
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE
    evidence_status: DelegationEvidenceStatus = (
        DelegationEvidenceStatus.REFERENCE_ONLY
    )
    schema_version: str = DELEGATION_EVIDENCE_REF_VERSION
    evidence_ref_id: str = ""
    evidence_ref_hash: str = ""

    def __post_init__(self) -> None:
        schema_version = _required_string(
            self.schema_version, field_name="schema_version"
        )
        delegation_ref_id = _required_string(
            self.delegation_ref_id, field_name="delegation_ref_id"
        )
        evidence_kind = _parse_evidence_kind(self.evidence_kind)
        evidence_description = _required_string(
            self.evidence_description, field_name="evidence_description"
        )
        evidence_uri_ref = _optional_string(self.evidence_uri_ref)
        evidence_hash_ref = _optional_string(self.evidence_hash_ref)
        proof_status = _parse_proof_reference_status(self.proof_status)
        source_label = _parse_source_label(self.source_label)
        evidence_status = _parse_evidence_status(self.evidence_status)

        evidence_ref_hash = compute_evidence_ref_hash(
            delegation_ref_id=delegation_ref_id,
            evidence_kind=evidence_kind,
            evidence_uri_ref=evidence_uri_ref,
            evidence_hash_ref=evidence_hash_ref,
            evidence_description=evidence_description,
            proof_status=proof_status,
            source_label=source_label,
            evidence_status=evidence_status,
            schema_version=schema_version,
        )
        evidence_ref_id = f"evref:{evidence_ref_hash[:16]}"

        if self.evidence_ref_hash not in ("", evidence_ref_hash):
            raise DelegationValidationError(
                "evidence_ref_hash does not match evidence ref content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="evidence_ref_hash",
            )
        if self.evidence_ref_id not in ("", evidence_ref_id):
            raise DelegationValidationError(
                "evidence_ref_id does not match evidence ref content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="evidence_ref_id",
            )

        object.__setattr__(self, "schema_version", schema_version)
        object.__setattr__(self, "delegation_ref_id", delegation_ref_id)
        object.__setattr__(self, "evidence_kind", evidence_kind)
        object.__setattr__(self, "evidence_description", evidence_description)
        object.__setattr__(self, "evidence_uri_ref", evidence_uri_ref)
        object.__setattr__(self, "evidence_hash_ref", evidence_hash_ref)
        object.__setattr__(self, "proof_status", proof_status)
        object.__setattr__(self, "source_label", source_label)
        object.__setattr__(self, "evidence_status", evidence_status)
        object.__setattr__(self, "evidence_ref_hash", evidence_ref_hash)
        object.__setattr__(self, "evidence_ref_id", evidence_ref_id)

    def to_canonical_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "delegation_ref_id": self.delegation_ref_id,
            "evidence_description": self.evidence_description,
            "evidence_kind": self.evidence_kind.value,
            "evidence_ref_hash": self.evidence_ref_hash,
            "evidence_ref_id": self.evidence_ref_id,
            "evidence_status": self.evidence_status.value,
            "proof_status": self.proof_status.value,
            "schema_version": self.schema_version,
            "source_label": self.source_label.value,
        }
        if self.evidence_uri_ref is not None:
            payload["evidence_uri_ref"] = self.evidence_uri_ref
        if self.evidence_hash_ref is not None:
            payload["evidence_hash_ref"] = self.evidence_hash_ref
        return payload

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> DelegationEvidenceRef:
        validate_known_fields(
            data, EVIDENCE_REF_KNOWN_FIELDS, label="delegation_evidence_ref"
        )
        return cls(
            delegation_ref_id=data["delegation_ref_id"],
            evidence_kind=data["evidence_kind"],
            evidence_description=data["evidence_description"],
            evidence_uri_ref=data.get("evidence_uri_ref"),
            evidence_hash_ref=data.get("evidence_hash_ref"),
            proof_status=data.get(
                "proof_status", DelegationProofReferenceStatus.REFERENCE_ONLY
            ),
            source_label=data.get(
                "source_label", DelegationSourceLabel.DEV_FIXTURE
            ),
            evidence_status=data.get(
                "evidence_status", DelegationEvidenceStatus.REFERENCE_ONLY
            ),
            schema_version=data.get(
                "schema_version", DELEGATION_EVIDENCE_REF_VERSION
            ),
            evidence_ref_id=data.get("evidence_ref_id", ""),
            evidence_ref_hash=data.get("evidence_ref_hash", ""),
        )


# ---------------------------------------------------------------------------
# DelegationNonRepudiationClaimRef
# ---------------------------------------------------------------------------


def compute_claim_ref_hash(
    *,
    delegation_ref_id: str,
    claim_subject_ref: str,
    claim_statement: str,
    claim_context_ref: str | None,
    proof_status: DelegationProofReferenceStatus,
    source_label: DelegationSourceLabel,
    claim_status: DelegationEvidenceStatus,
    schema_version: str = DELEGATION_CLAIM_REF_VERSION,
) -> str:
    """Deterministic hash of claim reference content."""
    payload: dict[str, Any] = {
        "claim_statement": claim_statement,
        "claim_status": claim_status.value,
        "claim_subject_ref": claim_subject_ref,
        "delegation_ref_id": delegation_ref_id,
        "proof_status": proof_status.value,
        "schema_version": schema_version,
        "source_label": source_label.value,
    }
    if claim_context_ref is not None:
        payload["claim_context_ref"] = claim_context_ref
    return stable_hash(payload)


@dataclass(frozen=True)
class DelegationNonRepudiationClaimRef:
    """One reference-only claim that evidence may support.

    ClaimRef describes a claim.
    It does not prove the claim.
    It does not verify non-repudiation.
    It does not create legal finality.
    """

    delegation_ref_id: str
    claim_subject_ref: str
    claim_statement: str
    claim_context_ref: str | None = None
    proof_status: DelegationProofReferenceStatus = (
        DelegationProofReferenceStatus.REFERENCE_ONLY
    )
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE
    claim_status: DelegationEvidenceStatus = (
        DelegationEvidenceStatus.REFERENCE_ONLY
    )
    schema_version: str = DELEGATION_CLAIM_REF_VERSION
    claim_ref_id: str = ""
    claim_ref_hash: str = ""

    def __post_init__(self) -> None:
        schema_version = _required_string(
            self.schema_version, field_name="schema_version"
        )
        delegation_ref_id = _required_string(
            self.delegation_ref_id, field_name="delegation_ref_id"
        )
        claim_subject_ref = _required_string(
            self.claim_subject_ref, field_name="claim_subject_ref"
        )
        claim_statement = _required_string(
            self.claim_statement, field_name="claim_statement"
        )
        claim_context_ref = _optional_string(self.claim_context_ref)
        proof_status = _parse_proof_reference_status(self.proof_status)
        source_label = _parse_source_label(self.source_label)
        claim_status = _parse_evidence_status(self.claim_status)

        claim_ref_hash = compute_claim_ref_hash(
            delegation_ref_id=delegation_ref_id,
            claim_subject_ref=claim_subject_ref,
            claim_statement=claim_statement,
            claim_context_ref=claim_context_ref,
            proof_status=proof_status,
            source_label=source_label,
            claim_status=claim_status,
            schema_version=schema_version,
        )
        claim_ref_id = f"clmref:{claim_ref_hash[:16]}"

        if self.claim_ref_hash not in ("", claim_ref_hash):
            raise DelegationValidationError(
                "claim_ref_hash does not match claim ref content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="claim_ref_hash",
            )
        if self.claim_ref_id not in ("", claim_ref_id):
            raise DelegationValidationError(
                "claim_ref_id does not match claim ref content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="claim_ref_id",
            )

        object.__setattr__(self, "schema_version", schema_version)
        object.__setattr__(self, "delegation_ref_id", delegation_ref_id)
        object.__setattr__(self, "claim_subject_ref", claim_subject_ref)
        object.__setattr__(self, "claim_statement", claim_statement)
        object.__setattr__(self, "claim_context_ref", claim_context_ref)
        object.__setattr__(self, "proof_status", proof_status)
        object.__setattr__(self, "source_label", source_label)
        object.__setattr__(self, "claim_status", claim_status)
        object.__setattr__(self, "claim_ref_hash", claim_ref_hash)
        object.__setattr__(self, "claim_ref_id", claim_ref_id)

    def to_canonical_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "claim_ref_hash": self.claim_ref_hash,
            "claim_ref_id": self.claim_ref_id,
            "claim_statement": self.claim_statement,
            "claim_status": self.claim_status.value,
            "claim_subject_ref": self.claim_subject_ref,
            "delegation_ref_id": self.delegation_ref_id,
            "proof_status": self.proof_status.value,
            "schema_version": self.schema_version,
            "source_label": self.source_label.value,
        }
        if self.claim_context_ref is not None:
            payload["claim_context_ref"] = self.claim_context_ref
        return payload

    @classmethod
    def from_dict(
        cls, data: Mapping[str, Any]
    ) -> DelegationNonRepudiationClaimRef:
        validate_known_fields(
            data, CLAIM_REF_KNOWN_FIELDS, label="delegation_claim_ref"
        )
        return cls(
            delegation_ref_id=data["delegation_ref_id"],
            claim_subject_ref=data["claim_subject_ref"],
            claim_statement=data["claim_statement"],
            claim_context_ref=data.get("claim_context_ref"),
            proof_status=data.get(
                "proof_status", DelegationProofReferenceStatus.REFERENCE_ONLY
            ),
            source_label=data.get(
                "source_label", DelegationSourceLabel.DEV_FIXTURE
            ),
            claim_status=data.get(
                "claim_status", DelegationEvidenceStatus.REFERENCE_ONLY
            ),
            schema_version=data.get(
                "schema_version", DELEGATION_CLAIM_REF_VERSION
            ),
            claim_ref_id=data.get("claim_ref_id", ""),
            claim_ref_hash=data.get("claim_ref_hash", ""),
        )


# ---------------------------------------------------------------------------
# DelegationEvidenceEnvelope
# ---------------------------------------------------------------------------


def _order_evidence_refs(
    refs: Sequence[DelegationEvidenceRef],
) -> tuple[DelegationEvidenceRef, ...]:
    """Deterministic ordering by evidence_ref_id."""
    return tuple(sorted(refs, key=lambda er: er.evidence_ref_id))


def _order_claim_refs(
    refs: Sequence[DelegationNonRepudiationClaimRef],
) -> tuple[DelegationNonRepudiationClaimRef, ...]:
    """Deterministic ordering by claim_ref_id."""
    return tuple(sorted(refs, key=lambda cr: cr.claim_ref_id))


def _order_string_list(
    items: Sequence[str],
) -> tuple[str, ...]:
    """Deterministic ordering for simple string lists."""
    return tuple(sorted(items))


def compute_evidence_envelope_hash(
    *,
    delegation_ref_id: str,
    delegation_identity_hash: str,
    role_binding_hash: str,
    constraint_set_hash: str,
    authority_binding_set_hash: str,
    evidence_refs: tuple[DelegationEvidenceRef, ...],
    claim_refs: tuple[DelegationNonRepudiationClaimRef, ...],
    attestation_refs: tuple[str, ...],
    signature_refs: tuple[str, ...],
    trace_refs: tuple[str, ...],
    proof_status: DelegationProofReferenceStatus,
    source_label: DelegationSourceLabel,
    schema_version: str = DELEGATION_EVIDENCE_ENVELOPE_VERSION,
) -> str:
    """Deterministic hash of the full evidence envelope."""
    payload: dict[str, Any] = {
        "attestation_refs": list(attestation_refs),
        "authority_binding_set_hash": authority_binding_set_hash,
        "claim_refs": [cr.to_canonical_dict() for cr in claim_refs],
        "constraint_set_hash": constraint_set_hash,
        "delegation_identity_hash": delegation_identity_hash,
        "delegation_ref_id": delegation_ref_id,
        "evidence_refs": [er.to_canonical_dict() for er in evidence_refs],
        "proof_status": proof_status.value,
        "role_binding_hash": role_binding_hash,
        "schema_version": schema_version,
        "signature_refs": list(signature_refs),
        "source_label": source_label.value,
        "trace_refs": list(trace_refs),
    }
    return stable_hash(payload)


@dataclass(frozen=True)
class DelegationEvidenceEnvelope:
    """Deterministic packet of evidence/claim/attestation/signature/trace refs
       for one delegation context.

    EvidenceEnvelope is a reference packet.
    It is not proof.
    It is not legal finality.
    It is not TRACE_VERIFIED.
    It does not verify evidence, signatures, traces, claims, or attestations.
    """

    delegation_ref_id: str
    delegation_identity_hash: str
    role_binding_hash: str
    constraint_set_hash: str
    authority_binding_set_hash: str
    evidence_refs: tuple[DelegationEvidenceRef, ...] = ()
    claim_refs: tuple[DelegationNonRepudiationClaimRef, ...] = ()
    attestation_refs: tuple[str, ...] = ()
    signature_refs: tuple[str, ...] = ()
    trace_refs: tuple[str, ...] = ()
    proof_status: DelegationProofReferenceStatus = (
        DelegationProofReferenceStatus.REFERENCE_ONLY
    )
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE
    schema_version: str = DELEGATION_EVIDENCE_ENVELOPE_VERSION
    evidence_envelope_id: str = ""
    evidence_envelope_hash: str = ""

    def __post_init__(self) -> None:
        schema_version = _required_string(
            self.schema_version, field_name="schema_version"
        )
        delegation_ref_id = _required_string(
            self.delegation_ref_id, field_name="delegation_ref_id"
        )
        delegation_identity_hash = _required_string(
            self.delegation_identity_hash,
            field_name="delegation_identity_hash",
        )
        role_binding_hash = _required_string(
            self.role_binding_hash, field_name="role_binding_hash"
        )
        constraint_set_hash = _required_string(
            self.constraint_set_hash, field_name="constraint_set_hash"
        )
        authority_binding_set_hash = _required_string(
            self.authority_binding_set_hash,
            field_name="authority_binding_set_hash",
        )
        proof_status = _parse_proof_reference_status(self.proof_status)
        source_label = _parse_source_label(self.source_label)

        evidence_refs = _order_evidence_refs(
            tuple(
                er if isinstance(er, DelegationEvidenceRef)
                else DelegationEvidenceRef.from_dict(er)
                for er in self.evidence_refs
            )
        )
        claim_refs = _order_claim_refs(
            tuple(
                cr if isinstance(cr, DelegationNonRepudiationClaimRef)
                else DelegationNonRepudiationClaimRef.from_dict(cr)
                for cr in self.claim_refs
            )
        )
        attestation_refs = _order_string_list(
            tuple(str(a) for a in self.attestation_refs)
        )
        signature_refs = _order_string_list(
            tuple(str(s) for s in self.signature_refs)
        )
        trace_refs = _order_string_list(
            tuple(str(t) for t in self.trace_refs)
        )

        evidence_envelope_hash = compute_evidence_envelope_hash(
            delegation_ref_id=delegation_ref_id,
            delegation_identity_hash=delegation_identity_hash,
            role_binding_hash=role_binding_hash,
            constraint_set_hash=constraint_set_hash,
            authority_binding_set_hash=authority_binding_set_hash,
            evidence_refs=evidence_refs,
            claim_refs=claim_refs,
            attestation_refs=attestation_refs,
            signature_refs=signature_refs,
            trace_refs=trace_refs,
            proof_status=proof_status,
            source_label=source_label,
            schema_version=schema_version,
        )
        evidence_envelope_id = f"evenv:{evidence_envelope_hash[:16]}"

        if self.evidence_envelope_hash not in ("", evidence_envelope_hash):
            raise DelegationValidationError(
                "evidence_envelope_hash does not match envelope content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="evidence_envelope_hash",
            )
        if self.evidence_envelope_id not in ("", evidence_envelope_id):
            raise DelegationValidationError(
                "evidence_envelope_id does not match envelope content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="evidence_envelope_id",
            )

        object.__setattr__(self, "schema_version", schema_version)
        object.__setattr__(self, "delegation_ref_id", delegation_ref_id)
        object.__setattr__(
            self, "delegation_identity_hash", delegation_identity_hash
        )
        object.__setattr__(self, "role_binding_hash", role_binding_hash)
        object.__setattr__(self, "constraint_set_hash", constraint_set_hash)
        object.__setattr__(
            self, "authority_binding_set_hash", authority_binding_set_hash
        )
        object.__setattr__(self, "evidence_refs", evidence_refs)
        object.__setattr__(self, "claim_refs", claim_refs)
        object.__setattr__(self, "attestation_refs", attestation_refs)
        object.__setattr__(self, "signature_refs", signature_refs)
        object.__setattr__(self, "trace_refs", trace_refs)
        object.__setattr__(self, "proof_status", proof_status)
        object.__setattr__(self, "source_label", source_label)
        object.__setattr__(
            self, "evidence_envelope_hash", evidence_envelope_hash
        )
        object.__setattr__(
            self, "evidence_envelope_id", evidence_envelope_id
        )

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "attestation_refs": list(self.attestation_refs),
            "authority_binding_set_hash": self.authority_binding_set_hash,
            "claim_refs": [cr.to_canonical_dict() for cr in self.claim_refs],
            "constraint_set_hash": self.constraint_set_hash,
            "delegation_identity_hash": self.delegation_identity_hash,
            "delegation_ref_id": self.delegation_ref_id,
            "evidence_envelope_hash": self.evidence_envelope_hash,
            "evidence_envelope_id": self.evidence_envelope_id,
            "evidence_refs": [
                er.to_canonical_dict() for er in self.evidence_refs
            ],
            "proof_status": self.proof_status.value,
            "role_binding_hash": self.role_binding_hash,
            "schema_version": self.schema_version,
            "signature_refs": list(self.signature_refs),
            "source_label": self.source_label.value,
            "trace_refs": list(self.trace_refs),
        }

    @classmethod
    def from_dict(
        cls, data: Mapping[str, Any]
    ) -> DelegationEvidenceEnvelope:
        validate_known_fields(
            data,
            EVIDENCE_ENVELOPE_KNOWN_FIELDS,
            label="delegation_evidence_envelope",
        )
        return cls(
            delegation_ref_id=data["delegation_ref_id"],
            delegation_identity_hash=data["delegation_identity_hash"],
            role_binding_hash=data["role_binding_hash"],
            constraint_set_hash=data["constraint_set_hash"],
            authority_binding_set_hash=data["authority_binding_set_hash"],
            evidence_refs=data.get("evidence_refs", ()),
            claim_refs=data.get("claim_refs", ()),
            attestation_refs=data.get("attestation_refs", ()),
            signature_refs=data.get("signature_refs", ()),
            trace_refs=data.get("trace_refs", ()),
            proof_status=data.get(
                "proof_status", DelegationProofReferenceStatus.REFERENCE_ONLY
            ),
            source_label=data.get(
                "source_label", DelegationSourceLabel.DEV_FIXTURE
            ),
            schema_version=data.get(
                "schema_version", DELEGATION_EVIDENCE_ENVELOPE_VERSION
            ),
            evidence_envelope_id=data.get("evidence_envelope_id", ""),
            evidence_envelope_hash=data.get("evidence_envelope_hash", ""),
        )


# ---------------------------------------------------------------------------
# DelegationEvidenceCompletenessProfile
# ---------------------------------------------------------------------------


def compute_completeness_profile_hash(
    *,
    delegation_ref_id: str,
    evidence_envelope_hash: str,
    has_delegation_identity: bool,
    has_role_binding: bool,
    has_constraints: bool,
    has_authority_refs: bool,
    has_evidence_refs: bool,
    has_claim_refs: bool,
    has_attestation_refs: bool,
    has_signature_refs: bool,
    has_trace_refs: bool,
    missing_components: tuple[str, ...],
    source_label: DelegationSourceLabel,
    schema_version: str = DELEGATION_EVIDENCE_COMPLETENESS_PROFILE_VERSION,
) -> str:
    """Deterministic hash of evidence completeness profile."""
    return stable_hash({
        "delegation_ref_id": delegation_ref_id,
        "evidence_envelope_hash": evidence_envelope_hash,
        "has_attestation_refs": has_attestation_refs,
        "has_authority_refs": has_authority_refs,
        "has_claim_refs": has_claim_refs,
        "has_constraints": has_constraints,
        "has_delegation_identity": has_delegation_identity,
        "has_evidence_refs": has_evidence_refs,
        "has_role_binding": has_role_binding,
        "has_signature_refs": has_signature_refs,
        "has_trace_refs": has_trace_refs,
        "missing_components": list(missing_components),
        "schema_version": schema_version,
        "source_label": source_label.value,
    })


@dataclass(frozen=True)
class DelegationEvidenceCompletenessProfile:
    """Present/missing evidence component profile, not trust score.

    CompletenessProfile is not trust score.
    CompletenessProfile is not verification.
    CompletenessProfile is not proof.
    CompletenessProfile is not legal finality.
    """

    delegation_ref_id: str
    evidence_envelope_hash: str
    has_delegation_identity: bool = False
    has_role_binding: bool = False
    has_constraints: bool = False
    has_authority_refs: bool = False
    has_evidence_refs: bool = False
    has_claim_refs: bool = False
    has_attestation_refs: bool = False
    has_signature_refs: bool = False
    has_trace_refs: bool = False
    missing_components: tuple[str, ...] = ()
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE
    schema_version: str = DELEGATION_EVIDENCE_COMPLETENESS_PROFILE_VERSION
    profile_id: str = ""
    profile_hash: str = ""

    def __post_init__(self) -> None:
        schema_version = _required_string(
            self.schema_version, field_name="schema_version"
        )
        delegation_ref_id = _required_string(
            self.delegation_ref_id, field_name="delegation_ref_id"
        )
        evidence_envelope_hash = _required_string(
            self.evidence_envelope_hash,
            field_name="evidence_envelope_hash",
        )
        source_label = _parse_source_label(self.source_label)

        for name in (
            "has_delegation_identity",
            "has_role_binding",
            "has_constraints",
            "has_authority_refs",
            "has_evidence_refs",
            "has_claim_refs",
            "has_attestation_refs",
            "has_signature_refs",
            "has_trace_refs",
        ):
            if not isinstance(getattr(self, name), bool):
                raise DelegationValidationError(
                    f"{name} must be boolean",
                    code=DelegationErrorCode.VALIDATION_ERROR,
                    field=name,
                )

        missing_components = _order_string_list(
            tuple(str(m) for m in self.missing_components)
        )

        profile_hash = compute_completeness_profile_hash(
            delegation_ref_id=delegation_ref_id,
            evidence_envelope_hash=evidence_envelope_hash,
            has_delegation_identity=self.has_delegation_identity,
            has_role_binding=self.has_role_binding,
            has_constraints=self.has_constraints,
            has_authority_refs=self.has_authority_refs,
            has_evidence_refs=self.has_evidence_refs,
            has_claim_refs=self.has_claim_refs,
            has_attestation_refs=self.has_attestation_refs,
            has_signature_refs=self.has_signature_refs,
            has_trace_refs=self.has_trace_refs,
            missing_components=missing_components,
            source_label=source_label,
            schema_version=schema_version,
        )
        profile_id = f"cmpprof:{profile_hash[:16]}"

        if self.profile_hash not in ("", profile_hash):
            raise DelegationValidationError(
                "profile_hash does not match profile content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="profile_hash",
            )
        if self.profile_id not in ("", profile_id):
            raise DelegationValidationError(
                "profile_id does not match profile content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="profile_id",
            )

        object.__setattr__(self, "schema_version", schema_version)
        object.__setattr__(self, "delegation_ref_id", delegation_ref_id)
        object.__setattr__(
            self, "evidence_envelope_hash", evidence_envelope_hash
        )
        object.__setattr__(self, "source_label", source_label)
        object.__setattr__(self, "missing_components", missing_components)
        object.__setattr__(self, "profile_hash", profile_hash)
        object.__setattr__(self, "profile_id", profile_id)

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "delegation_ref_id": self.delegation_ref_id,
            "evidence_envelope_hash": self.evidence_envelope_hash,
            "has_attestation_refs": self.has_attestation_refs,
            "has_authority_refs": self.has_authority_refs,
            "has_claim_refs": self.has_claim_refs,
            "has_constraints": self.has_constraints,
            "has_delegation_identity": self.has_delegation_identity,
            "has_evidence_refs": self.has_evidence_refs,
            "has_role_binding": self.has_role_binding,
            "has_signature_refs": self.has_signature_refs,
            "has_trace_refs": self.has_trace_refs,
            "missing_components": list(self.missing_components),
            "profile_hash": self.profile_hash,
            "profile_id": self.profile_id,
            "schema_version": self.schema_version,
            "source_label": self.source_label.value,
        }

    @classmethod
    def from_dict(
        cls, data: Mapping[str, Any]
    ) -> DelegationEvidenceCompletenessProfile:
        validate_known_fields(
            data,
            COMPLETENESS_PROFILE_KNOWN_FIELDS,
            label="delegation_evidence_completeness_profile",
        )
        return cls(
            delegation_ref_id=data["delegation_ref_id"],
            evidence_envelope_hash=data["evidence_envelope_hash"],
            has_delegation_identity=data.get("has_delegation_identity", False),
            has_role_binding=data.get("has_role_binding", False),
            has_constraints=data.get("has_constraints", False),
            has_authority_refs=data.get("has_authority_refs", False),
            has_evidence_refs=data.get("has_evidence_refs", False),
            has_claim_refs=data.get("has_claim_refs", False),
            has_attestation_refs=data.get("has_attestation_refs", False),
            has_signature_refs=data.get("has_signature_refs", False),
            has_trace_refs=data.get("has_trace_refs", False),
            missing_components=data.get("missing_components", ()),
            source_label=data.get(
                "source_label", DelegationSourceLabel.DEV_FIXTURE
            ),
            schema_version=data.get(
                "schema_version",
                DELEGATION_EVIDENCE_COMPLETENESS_PROFILE_VERSION,
            ),
            profile_id=data.get("profile_id", ""),
            profile_hash=data.get("profile_hash", ""),
        )


# ---------------------------------------------------------------------------
# DelegationNonRepudiationBinding
# ---------------------------------------------------------------------------


def compute_non_repudiation_binding_hash(
    *,
    delegation_ref_id: str,
    delegation_identity_hash: str,
    role_binding_hash: str,
    constraint_set_hash: str,
    authority_binding_set_hash: str,
    evidence_envelope_hash: str,
    completeness_profile_hash: str,
    source_label: DelegationSourceLabel,
    proof_status: DelegationProofReferenceStatus,
    schema_version: str = DELEGATION_NON_REPUDIATION_BINDING_VERSION,
) -> str:
    """Deterministic hash of non-repudiation binding."""
    return stable_hash({
        "authority_binding_set_hash": authority_binding_set_hash,
        "completeness_profile_hash": completeness_profile_hash,
        "constraint_set_hash": constraint_set_hash,
        "delegation_identity_hash": delegation_identity_hash,
        "delegation_ref_id": delegation_ref_id,
        "evidence_envelope_hash": evidence_envelope_hash,
        "proof_status": proof_status.value,
        "role_binding_hash": role_binding_hash,
        "schema_version": schema_version,
        "source_label": source_label.value,
    })


@dataclass(frozen=True)
class DelegationNonRepudiationBinding:
    """Binding between evidence envelope and delegation identity/role/constraint/
       authority context.

    NonRepudiationBinding binds evidence metadata.
    It is not proof.
    It is not verification.
    It is not legal finality.
    It is not trace verification.
    """

    delegation_ref_id: str
    delegation_identity_hash: str
    role_binding_hash: str
    constraint_set_hash: str
    authority_binding_set_hash: str
    evidence_envelope_hash: str
    completeness_profile_hash: str
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE
    proof_status: DelegationProofReferenceStatus = (
        DelegationProofReferenceStatus.REFERENCE_ONLY
    )
    schema_version: str = DELEGATION_NON_REPUDIATION_BINDING_VERSION
    binding_id: str = ""
    binding_hash: str = ""

    def __post_init__(self) -> None:
        schema_version = _required_string(
            self.schema_version, field_name="schema_version"
        )
        delegation_ref_id = _required_string(
            self.delegation_ref_id, field_name="delegation_ref_id"
        )
        delegation_identity_hash = _required_string(
            self.delegation_identity_hash,
            field_name="delegation_identity_hash",
        )
        role_binding_hash = _required_string(
            self.role_binding_hash, field_name="role_binding_hash"
        )
        constraint_set_hash = _required_string(
            self.constraint_set_hash, field_name="constraint_set_hash"
        )
        authority_binding_set_hash = _required_string(
            self.authority_binding_set_hash,
            field_name="authority_binding_set_hash",
        )
        evidence_envelope_hash = _required_string(
            self.evidence_envelope_hash,
            field_name="evidence_envelope_hash",
        )
        completeness_profile_hash = _required_string(
            self.completeness_profile_hash,
            field_name="completeness_profile_hash",
        )
        source_label = _parse_source_label(self.source_label)
        proof_status = _parse_proof_reference_status(self.proof_status)

        binding_hash = compute_non_repudiation_binding_hash(
            delegation_ref_id=delegation_ref_id,
            delegation_identity_hash=delegation_identity_hash,
            role_binding_hash=role_binding_hash,
            constraint_set_hash=constraint_set_hash,
            authority_binding_set_hash=authority_binding_set_hash,
            evidence_envelope_hash=evidence_envelope_hash,
            completeness_profile_hash=completeness_profile_hash,
            source_label=source_label,
            proof_status=proof_status,
            schema_version=schema_version,
        )
        binding_id = f"nrbind:{binding_hash[:16]}"

        if self.binding_hash not in ("", binding_hash):
            raise DelegationValidationError(
                "binding_hash does not match binding content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="binding_hash",
            )
        if self.binding_id not in ("", binding_id):
            raise DelegationValidationError(
                "binding_id does not match binding content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="binding_id",
            )

        object.__setattr__(self, "schema_version", schema_version)
        object.__setattr__(self, "delegation_ref_id", delegation_ref_id)
        object.__setattr__(
            self, "delegation_identity_hash", delegation_identity_hash
        )
        object.__setattr__(self, "role_binding_hash", role_binding_hash)
        object.__setattr__(self, "constraint_set_hash", constraint_set_hash)
        object.__setattr__(
            self, "authority_binding_set_hash", authority_binding_set_hash
        )
        object.__setattr__(
            self, "evidence_envelope_hash", evidence_envelope_hash
        )
        object.__setattr__(
            self, "completeness_profile_hash", completeness_profile_hash
        )
        object.__setattr__(self, "source_label", source_label)
        object.__setattr__(self, "proof_status", proof_status)
        object.__setattr__(self, "binding_hash", binding_hash)
        object.__setattr__(self, "binding_id", binding_id)

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "authority_binding_set_hash": self.authority_binding_set_hash,
            "binding_hash": self.binding_hash,
            "binding_id": self.binding_id,
            "completeness_profile_hash": self.completeness_profile_hash,
            "constraint_set_hash": self.constraint_set_hash,
            "delegation_identity_hash": self.delegation_identity_hash,
            "delegation_ref_id": self.delegation_ref_id,
            "evidence_envelope_hash": self.evidence_envelope_hash,
            "proof_status": self.proof_status.value,
            "role_binding_hash": self.role_binding_hash,
            "schema_version": self.schema_version,
            "source_label": self.source_label.value,
        }

    @classmethod
    def from_dict(
        cls, data: Mapping[str, Any]
    ) -> DelegationNonRepudiationBinding:
        validate_known_fields(
            data,
            NON_REPUDIATION_BINDING_KNOWN_FIELDS,
            label="delegation_non_repudiation_binding",
        )
        return cls(
            delegation_ref_id=data["delegation_ref_id"],
            delegation_identity_hash=data["delegation_identity_hash"],
            role_binding_hash=data["role_binding_hash"],
            constraint_set_hash=data["constraint_set_hash"],
            authority_binding_set_hash=data["authority_binding_set_hash"],
            evidence_envelope_hash=data["evidence_envelope_hash"],
            completeness_profile_hash=data["completeness_profile_hash"],
            source_label=data.get(
                "source_label", DelegationSourceLabel.DEV_FIXTURE
            ),
            proof_status=data.get(
                "proof_status", DelegationProofReferenceStatus.REFERENCE_ONLY
            ),
            schema_version=data.get(
                "schema_version", DELEGATION_NON_REPUDIATION_BINDING_VERSION
            ),
            binding_id=data.get("binding_id", ""),
            binding_hash=data.get("binding_hash", ""),
        )


# ---------------------------------------------------------------------------
# DelegationNonRepudiationBindingSet
# ---------------------------------------------------------------------------


def _order_non_repudiation_bindings(
    bindings: Sequence[DelegationNonRepudiationBinding],
) -> tuple[DelegationNonRepudiationBinding, ...]:
    """Deterministic ordering by binding_id."""
    return tuple(sorted(bindings, key=lambda b: b.binding_id))


def compute_non_repudiation_binding_set_hash(
    *,
    delegation_ref_id: str,
    delegation_identity_hash: str,
    role_binding_hash: str,
    constraint_set_hash: str,
    authority_binding_set_hash: str,
    bindings: tuple[DelegationNonRepudiationBinding, ...],
    source_label: DelegationSourceLabel,
    side_effects: DelegationNonRepudiationSideEffects,
    schema_version: str = DELEGATION_NON_REPUDIATION_BINDING_SET_VERSION,
) -> str:
    """Deterministic hash of the full non-repudiation binding set."""
    payload: dict[str, Any] = {
        "authority_binding_set_hash": authority_binding_set_hash,
        "bindings": [b.to_canonical_dict() for b in bindings],
        "constraint_set_hash": constraint_set_hash,
        "delegation_identity_hash": delegation_identity_hash,
        "delegation_ref_id": delegation_ref_id,
        "role_binding_hash": role_binding_hash,
        "schema_version": schema_version,
        "side_effects": side_effects.to_canonical_dict(),
        "source_label": source_label.value,
    }
    return stable_hash(payload)


@dataclass(frozen=True)
class DelegationNonRepudiationBindingSet:
    """Collection of non-repudiation bindings for one delegation.

    NonRepudiationBindingSet describes evidence/non-repudiation hooks.
    It does not prove non-repudiation.
    It does not verify evidence.
    It does not verify signatures.
    It does not verify trace.
    It does not write Ledger/global trace.
    """

    delegation_ref_id: str
    delegation_identity_hash: str
    role_binding_hash: str
    constraint_set_hash: str
    authority_binding_set_hash: str
    bindings: tuple[DelegationNonRepudiationBinding, ...] = ()
    side_effects: DelegationNonRepudiationSideEffects = field(
        default_factory=lambda: DelegationNonRepudiationSideEffects()
    )
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE
    schema_version: str = DELEGATION_NON_REPUDIATION_BINDING_SET_VERSION
    non_repudiation_binding_set_id: str = ""
    non_repudiation_binding_set_hash: str = ""

    def __post_init__(self) -> None:
        schema_version = _required_string(
            self.schema_version, field_name="schema_version"
        )
        delegation_ref_id = _required_string(
            self.delegation_ref_id, field_name="delegation_ref_id"
        )
        delegation_identity_hash = _required_string(
            self.delegation_identity_hash,
            field_name="delegation_identity_hash",
        )
        role_binding_hash = _required_string(
            self.role_binding_hash, field_name="role_binding_hash"
        )
        constraint_set_hash = _required_string(
            self.constraint_set_hash, field_name="constraint_set_hash"
        )
        authority_binding_set_hash = _required_string(
            self.authority_binding_set_hash,
            field_name="authority_binding_set_hash",
        )
        source_label = _parse_source_label(self.source_label)

        bindings = _order_non_repudiation_bindings(
            tuple(
                b if isinstance(b, DelegationNonRepudiationBinding)
                else DelegationNonRepudiationBinding.from_dict(b)
                for b in self.bindings
            )
        )
        side_effects = (
            self.side_effects
            if isinstance(self.side_effects, DelegationNonRepudiationSideEffects)
            else DelegationNonRepudiationSideEffects.from_dict(self.side_effects)
        )

        non_repudiation_binding_set_hash = (
            compute_non_repudiation_binding_set_hash(
                delegation_ref_id=delegation_ref_id,
                delegation_identity_hash=delegation_identity_hash,
                role_binding_hash=role_binding_hash,
                constraint_set_hash=constraint_set_hash,
                authority_binding_set_hash=authority_binding_set_hash,
                bindings=bindings,
                source_label=source_label,
                side_effects=side_effects,
                schema_version=schema_version,
            )
        )
        non_repudiation_binding_set_id = (
            f"nrbset:{non_repudiation_binding_set_hash[:16]}"
        )

        if self.non_repudiation_binding_set_hash not in (
            "",
            non_repudiation_binding_set_hash,
        ):
            raise DelegationValidationError(
                "non_repudiation_binding_set_hash does not match "
                "binding set content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="non_repudiation_binding_set_hash",
            )
        if self.non_repudiation_binding_set_id not in (
            "",
            non_repudiation_binding_set_id,
        ):
            raise DelegationValidationError(
                "non_repudiation_binding_set_id does not match "
                "binding set content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="non_repudiation_binding_set_id",
            )

        object.__setattr__(self, "schema_version", schema_version)
        object.__setattr__(self, "delegation_ref_id", delegation_ref_id)
        object.__setattr__(
            self, "delegation_identity_hash", delegation_identity_hash
        )
        object.__setattr__(self, "role_binding_hash", role_binding_hash)
        object.__setattr__(self, "constraint_set_hash", constraint_set_hash)
        object.__setattr__(
            self, "authority_binding_set_hash", authority_binding_set_hash
        )
        object.__setattr__(self, "bindings", bindings)
        object.__setattr__(self, "side_effects", side_effects)
        object.__setattr__(self, "source_label", source_label)
        object.__setattr__(
            self,
            "non_repudiation_binding_set_hash",
            non_repudiation_binding_set_hash,
        )
        object.__setattr__(
            self,
            "non_repudiation_binding_set_id",
            non_repudiation_binding_set_id,
        )

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "authority_binding_set_hash": self.authority_binding_set_hash,
            "bindings": [b.to_canonical_dict() for b in self.bindings],
            "constraint_set_hash": self.constraint_set_hash,
            "delegation_identity_hash": self.delegation_identity_hash,
            "delegation_ref_id": self.delegation_ref_id,
            "non_repudiation_binding_set_hash": (
                self.non_repudiation_binding_set_hash
            ),
            "non_repudiation_binding_set_id": (
                self.non_repudiation_binding_set_id
            ),
            "role_binding_hash": self.role_binding_hash,
            "schema_version": self.schema_version,
            "side_effects": self.side_effects.to_canonical_dict(),
            "source_label": self.source_label.value,
        }

    @classmethod
    def from_dict(
        cls, data: Mapping[str, Any]
    ) -> DelegationNonRepudiationBindingSet:
        validate_known_fields(
            data,
            NON_REPUDIATION_BINDING_SET_KNOWN_FIELDS,
            label="delegation_non_repudiation_binding_set",
        )
        return cls(
            delegation_ref_id=data["delegation_ref_id"],
            delegation_identity_hash=data["delegation_identity_hash"],
            role_binding_hash=data["role_binding_hash"],
            constraint_set_hash=data["constraint_set_hash"],
            authority_binding_set_hash=data["authority_binding_set_hash"],
            bindings=data.get("bindings", ()),
            side_effects=data.get(
                "side_effects", DelegationNonRepudiationSideEffects()
            ),
            source_label=data.get(
                "source_label", DelegationSourceLabel.DEV_FIXTURE
            ),
            schema_version=data.get(
                "schema_version",
                DELEGATION_NON_REPUDIATION_BINDING_SET_VERSION,
            ),
            non_repudiation_binding_set_id=data.get(
                "non_repudiation_binding_set_id", ""
            ),
            non_repudiation_binding_set_hash=data.get(
                "non_repudiation_binding_set_hash", ""
            ),
        )


# ---------------------------------------------------------------------------
# DelegationNonRepudiationSideEffects
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DelegationNonRepudiationSideEffects:
    """Hard proof that P1.8.5 is non-verifying, non-final, and non-mutating;
       all fields default to false."""

    crypto_verified: bool = False
    signature_verified: bool = False
    trace_verified: bool = False
    evidence_verified: bool = False
    claim_verified: bool = False
    attestation_verified: bool = False
    ledger_written: bool = False
    global_trace_written: bool = False
    policy_called: bool = False
    custos_called: bool = False
    approval_created: bool = False
    runtime_mutated: bool = False
    non_repudiation_proven: bool = False
    legal_finality_claimed: bool = False

    def __post_init__(self) -> None:
        for item in fields(self):
            value = getattr(self, item.name)
            if not isinstance(value, bool):
                raise DelegationValidationError(
                    f"{item.name} must be boolean",
                    code=DelegationErrorCode.VALIDATION_ERROR,
                    field=item.name,
                )

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "approval_created": self.approval_created,
            "attestation_verified": self.attestation_verified,
            "claim_verified": self.claim_verified,
            "crypto_verified": self.crypto_verified,
            "custos_called": self.custos_called,
            "evidence_verified": self.evidence_verified,
            "global_trace_written": self.global_trace_written,
            "ledger_written": self.ledger_written,
            "legal_finality_claimed": self.legal_finality_claimed,
            "non_repudiation_proven": self.non_repudiation_proven,
            "policy_called": self.policy_called,
            "runtime_mutated": self.runtime_mutated,
            "signature_verified": self.signature_verified,
            "trace_verified": self.trace_verified,
        }

    @classmethod
    def from_dict(
        cls, data: Mapping[str, Any]
    ) -> DelegationNonRepudiationSideEffects:
        validate_known_fields(
            data,
            NON_REPUDIATION_SIDE_EFFECTS_KNOWN_FIELDS,
            label="delegation_non_repudiation_side_effects",
        )
        return cls(
            **{
                name: data.get(name, False)
                for name in NON_REPUDIATION_SIDE_EFFECTS_KNOWN_FIELDS
            }
        )


# ---------------------------------------------------------------------------
# DelegationNonRepudiationStatusReport
# ---------------------------------------------------------------------------


def compute_non_repudiation_status_report_hash(
    *,
    schema_version: str,
    status_label: DelegationSourceLabel,
    available_contracts: Mapping[str, str],
    unavailable_bindings: Mapping[str, str],
    side_effects: DelegationNonRepudiationSideEffects,
) -> str:
    return stable_hash({
        "available_contracts": dict(
            sorted(available_contracts.items(), key=lambda item: item[0])
        ),
        "schema_version": schema_version,
        "side_effects": side_effects.to_canonical_dict(),
        "status_label": status_label.value,
        "unavailable_bindings": dict(
            sorted(unavailable_bindings.items(), key=lambda item: item[0])
        ),
    })


@dataclass(frozen=True)
class DelegationNonRepudiationStatusReport:
    """Reports evidence/non-repudiation model readiness and unavailable surfaces."""

    status_label: DelegationSourceLabel
    available_contracts: Mapping[str, str]
    unavailable_bindings: Mapping[str, str]
    side_effects: DelegationNonRepudiationSideEffects = field(
        default_factory=DelegationNonRepudiationSideEffects,
    )
    schema_version: str = DELEGATION_NON_REPUDIATION_STATUS_REPORT_VERSION
    status_hash: str = ""

    def __post_init__(self) -> None:
        status_label = _parse_source_label(self.status_label)
        schema_version = _required_string(
            self.schema_version, field_name="schema_version"
        )

        if not isinstance(self.available_contracts, MappingABC):
            raise DelegationValidationError(
                "available_contracts must be a mapping",
                code=DelegationErrorCode.VALIDATION_ERROR,
                field="available_contracts",
            )
        if not isinstance(self.unavailable_bindings, MappingABC):
            raise DelegationValidationError(
                "unavailable_bindings must be a mapping",
                code=DelegationErrorCode.VALIDATION_ERROR,
                field="unavailable_bindings",
            )

        side_effects = (
            self.side_effects
            if isinstance(
                self.side_effects, DelegationNonRepudiationSideEffects
            )
            else DelegationNonRepudiationSideEffects.from_dict(
                self.side_effects
            )
        )

        available_contracts = MappingProxyType(dict(self.available_contracts))
        unavailable_bindings = MappingProxyType(
            dict(self.unavailable_bindings)
        )

        status_hash = compute_non_repudiation_status_report_hash(
            schema_version=schema_version,
            status_label=status_label,
            available_contracts=available_contracts,
            unavailable_bindings=unavailable_bindings,
            side_effects=side_effects,
        )

        if self.status_hash not in ("", status_hash):
            raise DelegationValidationError(
                "status_hash does not match status content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="status_hash",
            )

        object.__setattr__(self, "status_label", status_label)
        object.__setattr__(self, "schema_version", schema_version)
        object.__setattr__(
            self, "available_contracts", available_contracts
        )
        object.__setattr__(
            self, "unavailable_bindings", unavailable_bindings
        )
        object.__setattr__(self, "side_effects", side_effects)
        object.__setattr__(self, "status_hash", status_hash)

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "available_contracts": dict(
                sorted(
                    self.available_contracts.items(),
                    key=lambda item: item[0],
                )
            ),
            "schema_version": self.schema_version,
            "side_effects": self.side_effects.to_canonical_dict(),
            "status_hash": self.status_hash,
            "status_label": self.status_label.value,
            "unavailable_bindings": dict(
                sorted(
                    self.unavailable_bindings.items(),
                    key=lambda item: item[0],
                )
            ),
        }

    @classmethod
    def from_dict(
        cls, data: Mapping[str, Any]
    ) -> DelegationNonRepudiationStatusReport:
        validate_known_fields(
            data,
            NON_REPUDIATION_STATUS_REPORT_KNOWN_FIELDS,
            label="delegation_non_repudiation_status_report",
        )
        return cls(
            status_label=data["status_label"],
            available_contracts=data["available_contracts"],
            unavailable_bindings=data["unavailable_bindings"],
            side_effects=data.get(
                "side_effects", DelegationNonRepudiationSideEffects()
            ),
            schema_version=data.get(
                "schema_version",
                DELEGATION_NON_REPUDIATION_STATUS_REPORT_VERSION,
            ),
            status_hash=data.get("status_hash", ""),
        )


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def build_delegation_evidence_ref(
    delegation_ref_id: str,
    evidence_kind: DelegationEvidenceKind | str,
    evidence_description: str,
    *,
    evidence_uri_ref: str | None = None,
    evidence_hash_ref: str | None = None,
    proof_status: DelegationProofReferenceStatus = (
        DelegationProofReferenceStatus.REFERENCE_ONLY
    ),
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE,
    evidence_status: DelegationEvidenceStatus = (
        DelegationEvidenceStatus.REFERENCE_ONLY
    ),
) -> DelegationEvidenceRef:
    """Build evidence reference without verifying evidence."""
    return DelegationEvidenceRef(
        delegation_ref_id=delegation_ref_id,
        evidence_kind=evidence_kind,
        evidence_description=evidence_description,
        evidence_uri_ref=evidence_uri_ref,
        evidence_hash_ref=evidence_hash_ref,
        proof_status=proof_status,
        source_label=source_label,
        evidence_status=evidence_status,
    )


def build_delegation_non_repudiation_claim_ref(
    delegation_ref_id: str,
    claim_subject_ref: str,
    claim_statement: str,
    *,
    claim_context_ref: str | None = None,
    proof_status: DelegationProofReferenceStatus = (
        DelegationProofReferenceStatus.REFERENCE_ONLY
    ),
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE,
    claim_status: DelegationEvidenceStatus = (
        DelegationEvidenceStatus.REFERENCE_ONLY
    ),
) -> DelegationNonRepudiationClaimRef:
    """Build claim reference without proving the claim."""
    return DelegationNonRepudiationClaimRef(
        delegation_ref_id=delegation_ref_id,
        claim_subject_ref=claim_subject_ref,
        claim_statement=claim_statement,
        claim_context_ref=claim_context_ref,
        proof_status=proof_status,
        source_label=source_label,
        claim_status=claim_status,
    )


def build_delegation_evidence_envelope(
    delegation_ref_id: str,
    delegation_identity_hash: str,
    role_binding_hash: str,
    constraint_set_hash: str,
    authority_binding_set_hash: str,
    *,
    evidence_refs: Sequence[
        DelegationEvidenceRef | Mapping[str, Any]
    ] = (),
    claim_refs: Sequence[
        DelegationNonRepudiationClaimRef | Mapping[str, Any]
    ] = (),
    attestation_refs: Sequence[str] = (),
    signature_refs: Sequence[str] = (),
    trace_refs: Sequence[str] = (),
    proof_status: DelegationProofReferenceStatus = (
        DelegationProofReferenceStatus.REFERENCE_ONLY
    ),
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE,
) -> DelegationEvidenceEnvelope:
    """Build evidence envelope without verifying evidence, claims, signatures,
       traces, or attestations."""
    return DelegationEvidenceEnvelope(
        delegation_ref_id=delegation_ref_id,
        delegation_identity_hash=delegation_identity_hash,
        role_binding_hash=role_binding_hash,
        constraint_set_hash=constraint_set_hash,
        authority_binding_set_hash=authority_binding_set_hash,
        evidence_refs=evidence_refs,
        claim_refs=claim_refs,
        attestation_refs=attestation_refs,
        signature_refs=signature_refs,
        trace_refs=trace_refs,
        proof_status=proof_status,
        source_label=source_label,
    )


def build_delegation_evidence_completeness_profile(
    delegation_ref_id: str,
    evidence_envelope_hash: str,
    *,
    has_delegation_identity: bool = False,
    has_role_binding: bool = False,
    has_constraints: bool = False,
    has_authority_refs: bool = False,
    has_evidence_refs: bool = False,
    has_claim_refs: bool = False,
    has_attestation_refs: bool = False,
    has_signature_refs: bool = False,
    has_trace_refs: bool = False,
    missing_components: Sequence[str] = (),
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE,
) -> DelegationEvidenceCompletenessProfile:
    """Build completeness profile without scoring trust, proof, confidence,
       validity, or legality."""
    return DelegationEvidenceCompletenessProfile(
        delegation_ref_id=delegation_ref_id,
        evidence_envelope_hash=evidence_envelope_hash,
        has_delegation_identity=has_delegation_identity,
        has_role_binding=has_role_binding,
        has_constraints=has_constraints,
        has_authority_refs=has_authority_refs,
        has_evidence_refs=has_evidence_refs,
        has_claim_refs=has_claim_refs,
        has_attestation_refs=has_attestation_refs,
        has_signature_refs=has_signature_refs,
        has_trace_refs=has_trace_refs,
        missing_components=missing_components,
        source_label=source_label,
    )


def build_delegation_non_repudiation_binding(
    delegation_ref_id: str,
    delegation_identity_hash: str,
    role_binding_hash: str,
    constraint_set_hash: str,
    authority_binding_set_hash: str,
    evidence_envelope_hash: str,
    completeness_profile_hash: str,
    *,
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE,
    proof_status: DelegationProofReferenceStatus = (
        DelegationProofReferenceStatus.REFERENCE_ONLY
    ),
) -> DelegationNonRepudiationBinding:
    """Build non-repudiation binding without proving, verifying, or writing
       trace/Ledger."""
    return DelegationNonRepudiationBinding(
        delegation_ref_id=delegation_ref_id,
        delegation_identity_hash=delegation_identity_hash,
        role_binding_hash=role_binding_hash,
        constraint_set_hash=constraint_set_hash,
        authority_binding_set_hash=authority_binding_set_hash,
        evidence_envelope_hash=evidence_envelope_hash,
        completeness_profile_hash=completeness_profile_hash,
        source_label=source_label,
        proof_status=proof_status,
    )


def build_delegation_non_repudiation_binding_set(
    delegation_ref_id: str,
    delegation_identity_hash: str,
    role_binding_hash: str,
    constraint_set_hash: str,
    authority_binding_set_hash: str,
    bindings: Sequence[
        DelegationNonRepudiationBinding | Mapping[str, Any]
    ],
    *,
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE,
) -> DelegationNonRepudiationBindingSet:
    """Build collection of non-repudiation bindings without proving
       non-repudiation, verifying evidence, verifying signatures, verifying
       trace, or writing trace/Ledger."""
    return DelegationNonRepudiationBindingSet(
        delegation_ref_id=delegation_ref_id,
        delegation_identity_hash=delegation_identity_hash,
        role_binding_hash=role_binding_hash,
        constraint_set_hash=constraint_set_hash,
        authority_binding_set_hash=authority_binding_set_hash,
        bindings=bindings,
        source_label=source_label,
    )


def _default_non_repudiation_available_contracts() -> dict[str, str]:
    return {
        "DelegationEvidenceCompletenessProfile": (
            DelegationSourceLabel.LIVE.value
        ),
        "DelegationEvidenceEnvelope": DelegationSourceLabel.LIVE.value,
        "DelegationEvidenceKind": DelegationSourceLabel.LIVE.value,
        "DelegationEvidenceRef": DelegationSourceLabel.LIVE.value,
        "DelegationEvidenceStatus": DelegationSourceLabel.LIVE.value,
        "DelegationNonRepudiationBinding": DelegationSourceLabel.LIVE.value,
        "DelegationNonRepudiationBindingSet": (
            DelegationSourceLabel.LIVE.value
        ),
        "DelegationNonRepudiationClaimRef": (
            DelegationSourceLabel.LIVE.value
        ),
        "DelegationNonRepudiationSideEffects": (
            DelegationSourceLabel.LIVE.value
        ),
        "DelegationNonRepudiationStatusReport": (
            DelegationSourceLabel.LIVE.value
        ),
        "DelegationProofReferenceStatus": DelegationSourceLabel.LIVE.value,
    }


def build_delegation_non_repudiation_status_report() -> (
    DelegationNonRepudiationStatusReport
):
    """Return honest P1.8.5 non-repudiation status report (non-verifying)."""
    return DelegationNonRepudiationStatusReport(
        status_label=DelegationSourceLabel.DEV_FIXTURE,
        available_contracts=_default_non_repudiation_available_contracts(),
        unavailable_bindings=DELEGATION_NON_REPUDIATION_UNAVAILABLE_BINDINGS,
        side_effects=DelegationNonRepudiationSideEffects(),
    )


def serialize_delegation_evidence_envelope(
    envelope: DelegationEvidenceEnvelope,
) -> str:
    """Serialize DelegationEvidenceEnvelope to deterministic canonical JSON."""
    return to_canonical_json(envelope)


def serialize_delegation_non_repudiation_binding_set(
    binding_set: DelegationNonRepudiationBindingSet,
) -> str:
    """Serialize DelegationNonRepudiationBindingSet to deterministic
       canonical JSON."""
    return to_canonical_json(binding_set)


def hash_delegation_evidence_ref(
    evidence_ref: DelegationEvidenceRef,
) -> str:
    """Return stable evidence_ref_hash for DelegationEvidenceRef content."""
    return evidence_ref.evidence_ref_hash


def hash_delegation_non_repudiation_claim_ref(
    claim_ref: DelegationNonRepudiationClaimRef,
) -> str:
    """Return stable claim_ref_hash for DelegationNonRepudiationClaimRef
       content."""
    return claim_ref.claim_ref_hash


def hash_delegation_evidence_envelope(
    envelope: DelegationEvidenceEnvelope,
) -> str:
    """Return stable evidence_envelope_hash for DelegationEvidenceEnvelope
       content."""
    return envelope.evidence_envelope_hash


def hash_delegation_evidence_completeness_profile(
    profile: DelegationEvidenceCompletenessProfile,
) -> str:
    """Return stable profile_hash for DelegationEvidenceCompletenessProfile
       content."""
    return profile.profile_hash


def hash_delegation_non_repudiation_binding_set(
    binding_set: DelegationNonRepudiationBindingSet,
) -> str:
    """Return stable non_repudiation_binding_set_hash for
       DelegationNonRepudiationBindingSet content."""
    return binding_set.non_repudiation_binding_set_hash
