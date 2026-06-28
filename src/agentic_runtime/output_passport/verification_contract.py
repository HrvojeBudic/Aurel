"""Output Passport verification contract boundary (P1.9-B / P1.9.9).

Defines how verification is represented and bounded without verifier execution,
trace verification, Ledger writes, or evidence finality.

Architectural law:
  - Verification contract is not verification execution.
  - Verification contract is not proof.
  - TRACE_VERIFIED requires actual trace verification.
  - EvidenceRef is not evidence finality.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
from typing import Any

from .foundation import (
    OutputPassportErrorCode,
    OutputPassportPayload,
    OutputPassportSideEffectProof,
    OutputPassportSourceLabel,
    OutputPassportTruthLabel,
    OutputPassportValidationError,
    OutputPassportVerificationStatus,
    build_dev_fixture_output_passport_payload,
    stable_hash,
    to_canonical_json,
)

OUTPUT_PASSPORT_VERIFICATION_CONTRACT_TASK_ID = "P1.9.9"
OUTPUT_PASSPORT_VERIFICATION_CONTRACT_VERSION = (
    "output_passport_verification_contract.v1"
)
OUTPUT_PASSPORT_VERIFICATION_BOUNDARY_VERSION = (
    "output_passport_verification_boundary.v1"
)
OUTPUT_PASSPORT_VERIFICATION_CLAIM_VERSION = "output_passport_verification_claim.v1"


class OutputPassportNonVerificationReason(str, Enum):
    """Closed-world why-not-verified reasons."""

    NO_VERIFIER_AVAILABLE = "no_verifier_available"
    VERIFICATION_RUNTIME_UNAVAILABLE = "verification_runtime_unavailable"
    TRACE_VERIFICATION_UNAVAILABLE = "trace_verification_unavailable"
    LEDGER_FINALITY_UNAVAILABLE = "ledger_finality_unavailable"
    EVIDENCE_FINALITY_UNAVAILABLE = "evidence_finality_unavailable"
    REFERENCE_ONLY = "reference_only"
    CONTRACT_ONLY = "contract_only"
    NO_PROOF_INPUT = "no_proof_input"
    UNAVAILABLE = "unavailable"
    ERROR = "error"


class _CanonicalMixin:
    def to_canonical_dict(self) -> dict[str, Any]:
        return _canonical_dataclass_dict(self)


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


def _hash_payload(payload: Mapping[str, Any]) -> str:
    return stable_hash(dict(payload))


def _all_false_side_effects() -> OutputPassportSideEffectProof:
    return OutputPassportSideEffectProof()


VERIFICATION_BOUNDARY_INVARIANTS: tuple[str, ...] = (
    "verification_contract_is_not_verification_execution",
    "verification_contract_is_not_proof",
    "trace_ref_is_not_trace_verified",
    "evidence_ref_is_not_evidence_finality",
    "hash_is_not_truth",
    "read_model_is_not_proof",
    "default_status_is_not_verified",
)


@dataclass(frozen=True)
class OutputPassportVerificationBoundary(_CanonicalMixin):
    """Boundary invariants — contract only, no execution."""

    schema_version: str
    checkpoint_id: str
    contract_is_verification: bool
    contract_is_proof: bool
    verifier_executed: bool
    trace_verified: bool
    evidence_finalized: bool
    ledger_written: bool
    global_trace_written: bool
    future_requirements: tuple[str, ...]
    invariants: tuple[str, ...]
    truth_label: OutputPassportTruthLabel
    source_label: OutputPassportSourceLabel
    side_effects: OutputPassportSideEffectProof
    verification_boundary_hash: str


@dataclass(frozen=True)
class OutputPassportVerificationClaim(_CanonicalMixin):
    """Declarative verification claim shape — no verifier input by default."""

    schema_version: str
    claim_id: str
    claim_kind: str
    verification_status: OutputPassportVerificationStatus
    non_verification_reason: OutputPassportNonVerificationReason
    proof_ref: str | None
    truth_label: OutputPassportTruthLabel
    source_label: OutputPassportSourceLabel
    verification_claim_hash: str


@dataclass(frozen=True)
class OutputPassportVerificationContract(_CanonicalMixin):
    """P1.9.9 verification representation without execution."""

    schema_version: str
    checkpoint_id: str
    passport_id: str
    verification_status: OutputPassportVerificationStatus
    non_verification_reason: OutputPassportNonVerificationReason
    boundary: OutputPassportVerificationBoundary
    claims: tuple[OutputPassportVerificationClaim, ...]
    future_verification_requirements: tuple[str, ...]
    truth_label: OutputPassportTruthLabel
    source_label: OutputPassportSourceLabel
    side_effects: OutputPassportSideEffectProof
    verification_contract_hash: str


def _reject_verified_without_proof(
    verification_status: OutputPassportVerificationStatus,
    *,
    proof_ref: str | None,
) -> None:
    if verification_status is OutputPassportVerificationStatus.VERIFIED:
        if not proof_ref:
            raise OutputPassportValidationError(
                "VERIFIED status requires explicit proof_ref input",
                code=OutputPassportErrorCode.FORBIDDEN_VERIFICATION_LABEL,
                field="verification_status",
            )


def build_output_passport_non_verification_boundary(
    *,
    checkpoint_id: str = "P1.9.9",
    future_requirements: Sequence[str] = (
        "trace_verifier_with_evidence_input",
        "ledger_integrity_check",
        "operator_verification_path",
    ),
    source_label: OutputPassportSourceLabel | str = OutputPassportSourceLabel.CONTRACT_ONLY,
) -> OutputPassportVerificationBoundary:
    if isinstance(source_label, str):
        source_label = OutputPassportSourceLabel(source_label)
    side_effects = _all_false_side_effects()
    payload = {
        "schema_version": OUTPUT_PASSPORT_VERIFICATION_BOUNDARY_VERSION,
        "checkpoint_id": checkpoint_id,
        "contract_is_verification": False,
        "contract_is_proof": False,
        "verifier_executed": False,
        "trace_verified": False,
        "evidence_finalized": False,
        "ledger_written": False,
        "global_trace_written": False,
        "future_requirements": tuple(future_requirements),
        "invariants": VERIFICATION_BOUNDARY_INVARIANTS,
        "truth_label": OutputPassportTruthLabel.VERIFICATION_CONTRACT_ONLY,
        "source_label": source_label,
        "side_effects": side_effects,
    }
    return OutputPassportVerificationBoundary(
        **payload,
        verification_boundary_hash=_hash_payload(payload),
    )


def build_output_passport_verification_contract(
    *,
    payload: OutputPassportPayload | None = None,
    checkpoint_id: str = "P1.9.9",
    verification_status: OutputPassportVerificationStatus | str = (
        OutputPassportVerificationStatus.NOT_VERIFIED
    ),
    non_verification_reason: OutputPassportNonVerificationReason | str = (
        OutputPassportNonVerificationReason.NO_VERIFIER_AVAILABLE
    ),
    proof_ref: str | None = None,
    boundary: OutputPassportVerificationBoundary | None = None,
    source_label: OutputPassportSourceLabel | str = OutputPassportSourceLabel.DEV_FIXTURE,
) -> OutputPassportVerificationContract:
    payload_val = payload or build_dev_fixture_output_passport_payload()
    boundary_val = boundary or build_output_passport_non_verification_boundary()
    if isinstance(verification_status, str):
        verification_status = OutputPassportVerificationStatus(verification_status)
    if isinstance(non_verification_reason, str):
        non_verification_reason = OutputPassportNonVerificationReason(
            non_verification_reason
        )
    if isinstance(source_label, str):
        source_label = OutputPassportSourceLabel(source_label)

    _reject_verified_without_proof(verification_status, proof_ref=proof_ref)

    claim_payload = {
        "schema_version": OUTPUT_PASSPORT_VERIFICATION_CLAIM_VERSION,
        "claim_id": "default-not-verified-claim",
        "claim_kind": "passport_integrity",
        "verification_status": verification_status,
        "non_verification_reason": non_verification_reason,
        "proof_ref": proof_ref,
        "truth_label": OutputPassportTruthLabel.VERIFICATION_CONTRACT_ONLY,
        "source_label": source_label,
    }
    default_claim = OutputPassportVerificationClaim(
        **claim_payload,
        verification_claim_hash=_hash_payload(claim_payload),
    )

    side_effects = _all_false_side_effects()
    contract_payload = {
        "schema_version": OUTPUT_PASSPORT_VERIFICATION_CONTRACT_VERSION,
        "checkpoint_id": checkpoint_id,
        "passport_id": payload_val.identity.passport_id,
        "verification_status": verification_status,
        "non_verification_reason": non_verification_reason,
        "boundary": boundary_val,
        "claims": (default_claim,),
        "future_verification_requirements": boundary_val.future_requirements,
        "truth_label": OutputPassportTruthLabel.VERIFICATION_CONTRACT_ONLY,
        "source_label": source_label,
        "side_effects": side_effects,
    }
    return OutputPassportVerificationContract(
        **contract_payload,
        verification_contract_hash=_hash_payload(contract_payload),
    )


def serialize_output_passport_verification_contract(
    contract: OutputPassportVerificationContract,
) -> str:
    return to_canonical_json(contract)
