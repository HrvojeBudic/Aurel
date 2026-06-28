"""Output Passport read model contracts (P1.9-B / P1.9.8, P1.9.11).

Consumer-readable projection of P1.9-A passport data without verification,
proof claims, runtime generation, or operator approval activation.

Architectural law:
  - Read model is not proof.
  - Read model is not verification.
  - Operator review state is not approval.
  - Operator review state is not execution.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
from typing import Any

from .foundation import (
    OutputPassportPayload,
    OutputPassportSideEffectProof,
    OutputPassportSourceLabel,
    OutputPassportTruthLabel,
    OutputPassportVerificationStatus,
    build_dev_fixture_output_passport_payload,
    stable_hash,
    to_canonical_json,
)

OUTPUT_PASSPORT_READ_MODEL_TASK_ID = "P1.9.8"
OUTPUT_PASSPORT_OPERATOR_REVIEW_TASK_ID = "P1.9.11"
OUTPUT_PASSPORT_READ_MODEL_VERSION = "output_passport_read_model.v1"
OUTPUT_PASSPORT_OPERATOR_REVIEW_VERSION = "output_passport_operator_review.v1"
OUTPUT_PASSPORT_CONSUMER_SUMMARY_VERSION = "output_passport_consumer_summary.v1"
OUTPUT_PASSPORT_DISPLAY_SECTION_VERSION = "output_passport_display_section.v1"


class OutputPassportReadModelStatus(str, Enum):
    """Read-model readiness status."""

    READY = "ready"
    PARTIAL = "partial"
    UNAVAILABLE = "unavailable"
    ERROR = "error"


class OutputPassportOperatorReviewStatus(str, Enum):
    """Operator review state labels — not approval."""

    NOT_REQUIRED = "not_required"
    PENDING = "pending"
    REVIEWED = "reviewed"
    REJECTED = "rejected"
    REVISION_REQUESTED = "revision_requested"
    UNAVAILABLE = "unavailable"


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


@dataclass(frozen=True)
class OutputPassportReviewRequirement(_CanonicalMixin):
    """Why operator review is or is not required."""

    review_required: bool
    requirement_reason: str
    truth_label: OutputPassportTruthLabel
    source_label: OutputPassportSourceLabel


@dataclass(frozen=True)
class OutputPassportOperatorReviewState(_CanonicalMixin):
    """P1.9.11 operator review field — explicit state, not approval."""

    schema_version: str
    checkpoint_id: str
    review_status: OutputPassportOperatorReviewStatus
    review_requirement: OutputPassportReviewRequirement
    operator_ref: str | None
    review_note: str | None
    unavailable_reason: str | None
    grants_permission: bool
    approves_execution: bool
    truth_label: OutputPassportTruthLabel
    source_label: OutputPassportSourceLabel
    side_effects: OutputPassportSideEffectProof
    operator_review_hash: str


@dataclass(frozen=True)
class OutputPassportDisplaySection(_CanonicalMixin):
    """Named read-model section for consumer display."""

    schema_version: str
    section_id: str
    section_name: str
    summary: str
    truth_label: OutputPassportTruthLabel
    verification_status: OutputPassportVerificationStatus
    source_label: OutputPassportSourceLabel
    section_hash: str


@dataclass(frozen=True)
class OutputPassportConsumerSummary(_CanonicalMixin):
    """High-level consumer-facing rollup."""

    schema_version: str
    passport_id: str
    headline: str
    verification_summary: str
    hash_summary: str
    truth_label: OutputPassportTruthLabel
    source_label: OutputPassportSourceLabel
    consumer_summary_hash: str


@dataclass(frozen=True)
class OutputPassportReadModel(_CanonicalMixin):
    """P1.9.8 consumer-readable passport projection."""

    schema_version: str
    checkpoint_id: str
    passport_id: str
    read_model_status: OutputPassportReadModelStatus
    consumer_summary: OutputPassportConsumerSummary
    display_sections: tuple[OutputPassportDisplaySection, ...]
    operator_review_state: OutputPassportOperatorReviewState
    verification_status: OutputPassportVerificationStatus
    binding_summary: str | None
    truth_label: OutputPassportTruthLabel
    source_label: OutputPassportSourceLabel
    side_effects: OutputPassportSideEffectProof
    read_model_hash: str


def build_operator_review_state_field(
    *,
    checkpoint_id: str = "P1.9.11",
    review_status: OutputPassportOperatorReviewStatus | str = (
        OutputPassportOperatorReviewStatus.NOT_REQUIRED
    ),
    review_required: bool = False,
    requirement_reason: str = "No operator review required for DEV_FIXTURE passport",
    operator_ref: str | None = None,
    review_note: str | None = None,
    unavailable_reason: str | None = None,
    truth_label: OutputPassportTruthLabel | str = OutputPassportTruthLabel.REVIEW_STATE_ONLY,
    source_label: OutputPassportSourceLabel | str = OutputPassportSourceLabel.DEV_FIXTURE,
) -> OutputPassportOperatorReviewState:
    if isinstance(review_status, str):
        review_status = OutputPassportOperatorReviewStatus(review_status)
    if isinstance(truth_label, str):
        truth_label = OutputPassportTruthLabel(truth_label)
    if isinstance(source_label, str):
        source_label = OutputPassportSourceLabel(source_label)
    side_effects = _all_false_side_effects()
    review_requirement = OutputPassportReviewRequirement(
        review_required=review_required,
        requirement_reason=requirement_reason,
        truth_label=OutputPassportTruthLabel.REVIEW_STATE_ONLY,
        source_label=source_label,
    )
    payload = {
        "schema_version": OUTPUT_PASSPORT_OPERATOR_REVIEW_VERSION,
        "checkpoint_id": checkpoint_id,
        "review_status": review_status,
        "review_requirement": review_requirement,
        "operator_ref": operator_ref,
        "review_note": review_note,
        "unavailable_reason": unavailable_reason,
        "grants_permission": False,
        "approves_execution": False,
        "truth_label": truth_label,
        "source_label": source_label,
        "side_effects": side_effects,
    }
    return OutputPassportOperatorReviewState(
        **payload,
        operator_review_hash=_hash_payload(payload),
    )


def _build_display_section(
    *,
    section_id: str,
    section_name: str,
    summary: str,
    truth_label: OutputPassportTruthLabel,
    verification_status: OutputPassportVerificationStatus = (
        OutputPassportVerificationStatus.NOT_VERIFIED
    ),
    source_label: OutputPassportSourceLabel = OutputPassportSourceLabel.DEV_FIXTURE,
) -> OutputPassportDisplaySection:
    payload = {
        "schema_version": OUTPUT_PASSPORT_DISPLAY_SECTION_VERSION,
        "section_id": section_id,
        "section_name": section_name,
        "summary": summary,
        "truth_label": truth_label,
        "verification_status": verification_status,
        "source_label": source_label,
    }
    return OutputPassportDisplaySection(
        **payload,
        section_hash=_hash_payload(payload),
    )


def build_output_passport_read_model(
    *,
    payload: OutputPassportPayload | None = None,
    checkpoint_id: str = "P1.9.8",
    operator_review_state: OutputPassportOperatorReviewState | None = None,
    binding_summary: str | None = None,
    read_model_status: OutputPassportReadModelStatus | str = (
        OutputPassportReadModelStatus.READY
    ),
    truth_label: OutputPassportTruthLabel | str = OutputPassportTruthLabel.READ_MODEL_ONLY,
    source_label: OutputPassportSourceLabel | str = OutputPassportSourceLabel.DEV_FIXTURE,
) -> OutputPassportReadModel:
    payload_val = payload or build_dev_fixture_output_passport_payload()
    review_state = operator_review_state or build_operator_review_state_field()
    if isinstance(read_model_status, str):
        read_model_status = OutputPassportReadModelStatus(read_model_status)
    if isinstance(truth_label, str):
        truth_label = OutputPassportTruthLabel(truth_label)
    if isinstance(source_label, str):
        source_label = OutputPassportSourceLabel(source_label)

    identity = payload_val.identity
    attribution = payload_val.attribution_envelope
    authority = payload_val.authority_policy_risk
    memory = payload_val.memory_influence
    evidence_trace = payload_val.evidence_trace_binding
    uncertainty = payload_val.uncertainty_envelope
    hash_contract = payload_val.hash_contract

    consumer_payload = {
        "schema_version": OUTPUT_PASSPORT_CONSUMER_SUMMARY_VERSION,
        "passport_id": identity.passport_id,
        "headline": (
            f"Output passport {identity.passport_id} — read model projection only"
        ),
        "verification_summary": (
            "NOT_VERIFIED — read model does not claim verification"
        ),
        "hash_summary": (
            f"payload_hash={hash_contract.payload_hash}; hash_is_truth=false"
        ),
        "truth_label": OutputPassportTruthLabel.READ_MODEL_ONLY,
        "source_label": source_label,
    }
    consumer_summary = OutputPassportConsumerSummary(
        **consumer_payload,
        consumer_summary_hash=_hash_payload(consumer_payload),
    )

    sections: list[OutputPassportDisplaySection] = [
        _build_display_section(
            section_id="identity",
            section_name="Passport Identity",
            summary=(
                f"passport_id={identity.passport_id}; "
                f"subject={identity.subject_ref.subject_ref_id}"
            ),
            truth_label=OutputPassportTruthLabel.CONTRACT_ONLY,
        ),
        _build_display_section(
            section_id="attribution",
            section_name="Attribution Summary",
            summary=(
                f"actor={attribution.actor_attribution.actor_ref}; "
                f"agent={attribution.agent_attribution.agent_ref}"
            ),
            truth_label=OutputPassportTruthLabel.DECLARED_ATTRIBUTION,
        ),
        _build_display_section(
            section_id="authority_policy_risk",
            section_name="Authority / Policy / Risk Disclosure",
            summary=(
                f"authorization={authority.authorization_status.value}; "
                f"risk_tier={authority.risk_disclosure.risk_tier.value}"
            ),
            truth_label=OutputPassportTruthLabel.DISCLOSURE_ONLY,
        ),
        _build_display_section(
            section_id="memory_influence",
            section_name="Memory Influence Disclosure",
            summary=(
                f"influence_status={memory.influence_status.value}; "
                f"refs={len(memory.influence_refs)}"
            ),
            truth_label=OutputPassportTruthLabel.MEMORY_INFLUENCE_DECLARED,
        ),
        _build_display_section(
            section_id="evidence_trace",
            section_name="EvidenceRef / TraceRef Summary",
            summary=(
                f"evidence_ref="
                f"{evidence_trace.evidence_ref.evidence_ref_id if evidence_trace.evidence_ref else 'none'}; "
                f"trace_ref="
                f"{evidence_trace.trace_ref.trace_ref_id if evidence_trace.trace_ref else 'none'}; "
                "reference_only=true"
            ),
            truth_label=OutputPassportTruthLabel.REFERENCE_ONLY,
            verification_status=OutputPassportVerificationStatus.REFERENCE_ONLY,
        ),
        _build_display_section(
            section_id="uncertainty",
            section_name="Assumptions / Limitations / Uncertainty",
            summary=(
                f"assumptions={len(uncertainty.assumptions)}; "
                f"limitations={len(uncertainty.limitations)}; "
                f"unknowns={len(uncertainty.unknowns)}"
            ),
            truth_label=OutputPassportTruthLabel.DISCLOSURE_ONLY,
        ),
        _build_display_section(
            section_id="hash",
            section_name="Hash / Determinism Summary",
            summary=(
                f"algorithm={hash_contract.determinism_profile.hash_algorithm}; "
                f"hash_is_verification=false; hash_is_truth=false"
            ),
            truth_label=OutputPassportTruthLabel.DETERMINISTIC_PAYLOAD_HASH,
        ),
        _build_display_section(
            section_id="verification_state",
            section_name="Verification State",
            summary="NOT_VERIFIED — verification contract is not execution",
            truth_label=OutputPassportTruthLabel.VERIFICATION_CONTRACT_ONLY,
            verification_status=OutputPassportVerificationStatus.NOT_VERIFIED,
        ),
    ]

    side_effects = _all_false_side_effects()
    read_model_payload = {
        "schema_version": OUTPUT_PASSPORT_READ_MODEL_VERSION,
        "checkpoint_id": checkpoint_id,
        "passport_id": identity.passport_id,
        "read_model_status": read_model_status,
        "consumer_summary": consumer_summary,
        "display_sections": tuple(sections),
        "operator_review_state": review_state,
        "verification_status": OutputPassportVerificationStatus.NOT_VERIFIED,
        "binding_summary": binding_summary,
        "truth_label": truth_label,
        "source_label": source_label,
        "side_effects": side_effects,
    }
    return OutputPassportReadModel(
        **read_model_payload,
        read_model_hash=_hash_payload(read_model_payload),
    )


def serialize_output_passport_read_model(read_model: OutputPassportReadModel) -> str:
    return to_canonical_json(read_model)
