"""P3-FLOW-D semantic evidence / proof expectation boundary.

AurelFlow can say what proof will be required later; it cannot produce proof.
Evidence requirement is not evidence. Proof expectation is not proof.
Semantic support expectation is not verification. Missing evidence and
unsupported output are runtime failure candidates, not just warnings.
Proof belongs to P5 AurelTrace.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

from .errors import AurelFlowErrorCode, AurelFlowValidationError
from .types import FlowTruthLabel, _CanonicalMixin, stable_hash

PROOF_EXPECTATION_ENVELOPE_VERSION = "proof_expectation_envelope.v1"
EVIDENCE_REQUIREMENT_VERSION = "evidence_requirement.v1"
SEMANTIC_SUPPORT_EXPECTATION_VERSION = "semantic_support_expectation.v1"
UNSUPPORTED_OUTPUT_RISK_VERSION = "unsupported_output_risk.v1"
SEMANTIC_SILENT_FAILURE_BOUNDARY_VERSION = "semantic_silent_failure_boundary.v1"
PROOF_EXPECTATION_READ_MODEL_VERSION = "proof_expectation_read_model.v1"

PROOF_UNAVAILABLE_REASON = (
    "no proof exists or can be produced by AurelFlow; a proof expectation "
    "envelope describes what P5 AurelTrace must verify later — proof "
    "expectation is not proof"
)
EVIDENCE_UNAVAILABLE_REASON = (
    "no evidence exists or can be produced by AurelFlow; an evidence "
    "requirement describes what a future verifier must supply — evidence "
    "requirement is not evidence"
)


def _forbid_true(obj: object, *boundary_fields: str) -> None:
    for boundary_field in boundary_fields:
        if getattr(obj, boundary_field):
            raise AurelFlowValidationError(
                f"{type(obj).__name__}.{boundary_field} must remain False",
                code=AurelFlowErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                field=boundary_field,
            )


def _forbid_false(obj: object, *boundary_fields: str) -> None:
    for boundary_field in boundary_fields:
        if not getattr(obj, boundary_field):
            raise AurelFlowValidationError(
                f"{type(obj).__name__}.{boundary_field} must remain True",
                code=AurelFlowErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                field=boundary_field,
            )


@dataclass(frozen=True)
class EvidenceRequirement(_CanonicalMixin):
    """What evidence a future verifier must supply. Requirement is not evidence."""

    requirement_id: str
    contract_version: str
    target_run_id: str
    target_node_id: str
    evidence_kind: str
    description: str
    truth_label: FlowTruthLabel
    unavailable_reason: str = EVIDENCE_UNAVAILABLE_REASON
    evidence_required: bool = True
    missing_evidence_is_failure_candidate: bool = True
    future_verifier_required: bool = True
    evidence_produced: bool = False
    proof_available: bool = False
    trace_verified: bool = False

    def __post_init__(self) -> None:
        _forbid_true(self, "evidence_produced", "proof_available", "trace_verified")
        _forbid_false(self, "evidence_required", "future_verifier_required")


def create_evidence_requirement(
    *,
    target_run_id: str,
    target_node_id: str,
    evidence_kind: str,
    description: str,
    missing_evidence_is_failure_candidate: bool = True,
) -> EvidenceRequirement:
    requirement_id = "flevr-" + stable_hash(
        {
            "contract_version": EVIDENCE_REQUIREMENT_VERSION,
            "target_run_id": target_run_id,
            "target_node_id": target_node_id,
            "evidence_kind": evidence_kind,
            "description": description,
        }
    )[:16]
    return EvidenceRequirement(
        requirement_id=requirement_id,
        contract_version=EVIDENCE_REQUIREMENT_VERSION,
        target_run_id=target_run_id,
        target_node_id=target_node_id,
        evidence_kind=evidence_kind,
        description=description,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
        missing_evidence_is_failure_candidate=missing_evidence_is_failure_candidate,
    )


@dataclass(frozen=True)
class SemanticSupportExpectation(_CanonicalMixin):
    """Output must be semantically supported later. Expectation is not verification."""

    expectation_id: str
    contract_version: str
    target_run_id: str
    target_node_id: str
    claim_ref: str
    truth_label: FlowTruthLabel
    semantic_support_required: bool = True
    contradiction_check_required: bool = True
    unsupported_output_is_failure_candidate: bool = True
    future_verifier_required: bool = True
    verification_performed: bool = False
    evidence_produced: bool = False
    proof_available: bool = False
    trace_verified: bool = False

    def __post_init__(self) -> None:
        _forbid_true(
            self,
            "verification_performed",
            "evidence_produced",
            "proof_available",
            "trace_verified",
        )
        _forbid_false(self, "semantic_support_required", "future_verifier_required")


def create_semantic_support_expectation(
    *,
    target_run_id: str,
    target_node_id: str,
    claim_ref: str,
    contradiction_check_required: bool = True,
) -> SemanticSupportExpectation:
    expectation_id = "flsse-" + stable_hash(
        {
            "contract_version": SEMANTIC_SUPPORT_EXPECTATION_VERSION,
            "target_run_id": target_run_id,
            "target_node_id": target_node_id,
            "claim_ref": claim_ref,
        }
    )[:16]
    return SemanticSupportExpectation(
        expectation_id=expectation_id,
        contract_version=SEMANTIC_SUPPORT_EXPECTATION_VERSION,
        target_run_id=target_run_id,
        target_node_id=target_node_id,
        claim_ref=claim_ref,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
        contradiction_check_required=contradiction_check_required,
    )


@dataclass(frozen=True)
class UnsupportedOutputRisk(_CanonicalMixin):
    """Unsupported output is a runtime failure candidate, not just a warning."""

    risk_id: str
    contract_version: str
    target_run_id: str
    target_node_id: str
    output_ref: str
    risk_reason: str
    truth_label: FlowTruthLabel
    is_failure_candidate: bool = True
    is_warning_only: bool = False
    proof_available: bool = False
    trace_verified: bool = False

    def __post_init__(self) -> None:
        _forbid_true(self, "is_warning_only", "proof_available", "trace_verified")
        _forbid_false(self, "is_failure_candidate")


def create_unsupported_output_risk(
    *,
    target_run_id: str,
    target_node_id: str,
    output_ref: str,
    risk_reason: str,
) -> UnsupportedOutputRisk:
    risk_id = "fluor-" + stable_hash(
        {
            "contract_version": UNSUPPORTED_OUTPUT_RISK_VERSION,
            "target_run_id": target_run_id,
            "target_node_id": target_node_id,
            "output_ref": output_ref,
            "risk_reason": risk_reason,
        }
    )[:16]
    return UnsupportedOutputRisk(
        risk_id=risk_id,
        contract_version=UNSUPPORTED_OUTPUT_RISK_VERSION,
        target_run_id=target_run_id,
        target_node_id=target_node_id,
        output_ref=output_ref,
        risk_reason=risk_reason,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
    )


@dataclass(frozen=True)
class SemanticSilentFailureBoundary(_CanonicalMixin):
    """No evidence is a runtime failure candidate; silent semantic success is forbidden."""

    boundary_version: str
    law: str
    truth_label: FlowTruthLabel
    boundary_hash: str
    missing_evidence_is_failure_candidate: bool = True
    unsupported_output_is_failure_candidate: bool = True
    silent_semantic_success_allowed: bool = False
    evidence_requirement_is_evidence: bool = False
    proof_expectation_is_proof: bool = False
    semantic_support_expectation_is_verification: bool = False

    def __post_init__(self) -> None:
        _forbid_true(
            self,
            "silent_semantic_success_allowed",
            "evidence_requirement_is_evidence",
            "proof_expectation_is_proof",
            "semantic_support_expectation_is_verification",
        )
        _forbid_false(
            self,
            "missing_evidence_is_failure_candidate",
            "unsupported_output_is_failure_candidate",
        )


def build_semantic_silent_failure_boundary() -> SemanticSilentFailureBoundary:
    law = (
        "no evidence is a runtime failure candidate, not just a warning; "
        "evidence requirement is not evidence, proof expectation is not proof, "
        "semantic support expectation is not verification"
    )
    payload = {
        "boundary_version": SEMANTIC_SILENT_FAILURE_BOUNDARY_VERSION,
        "law": law,
    }
    return SemanticSilentFailureBoundary(
        boundary_version=SEMANTIC_SILENT_FAILURE_BOUNDARY_VERSION,
        law=law,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
        boundary_hash=stable_hash(payload),
    )


@dataclass(frozen=True)
class ProofExpectationEnvelope(_CanonicalMixin):
    """What P5 must prove after a future execution. Expectation is not proof."""

    proof_expectation_id: str
    contract_version: str
    proposal_id: str
    execution_request_id: str
    target_run_id: str
    target_node_id: str
    required_verifier: str
    required_trace_expectation: str
    evidence_requirements: tuple[EvidenceRequirement, ...]
    truth_label: FlowTruthLabel
    unavailable_reason: str = PROOF_UNAVAILABLE_REASON
    metadata: Mapping[str, str] = field(default_factory=dict)
    evidence_required: bool = True
    semantic_support_required: bool = True
    contradiction_check_required: bool = True
    future_p5_required: bool = True
    proof_available: bool = False
    trace_verified: bool = False

    def __post_init__(self) -> None:
        _forbid_true(self, "proof_available", "trace_verified")
        _forbid_false(self, "evidence_required", "future_p5_required")


def create_proof_expectation_envelope(
    *,
    proposal_id: str,
    execution_request_id: str,
    target_run_id: str,
    target_node_id: str,
    required_verifier: str,
    required_trace_expectation: str,
    evidence_requirements: tuple[EvidenceRequirement, ...],
    semantic_support_required: bool = True,
    contradiction_check_required: bool = True,
    metadata: Mapping[str, str] | None = None,
) -> ProofExpectationEnvelope:
    proof_expectation_id = "flproof-" + stable_hash(
        {
            "contract_version": PROOF_EXPECTATION_ENVELOPE_VERSION,
            "proposal_id": proposal_id,
            "execution_request_id": execution_request_id,
            "target_run_id": target_run_id,
            "target_node_id": target_node_id,
            "required_verifier": required_verifier,
        }
    )[:16]
    return ProofExpectationEnvelope(
        proof_expectation_id=proof_expectation_id,
        contract_version=PROOF_EXPECTATION_ENVELOPE_VERSION,
        proposal_id=proposal_id,
        execution_request_id=execution_request_id,
        target_run_id=target_run_id,
        target_node_id=target_node_id,
        required_verifier=required_verifier,
        required_trace_expectation=required_trace_expectation,
        evidence_requirements=evidence_requirements,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
        metadata=dict(metadata or {}),
        semantic_support_required=semantic_support_required,
        contradiction_check_required=contradiction_check_required,
    )


@dataclass(frozen=True)
class ProofExpectationReadModel(_CanonicalMixin):
    """Deterministic view over proof expectations. Nothing here is proven."""

    read_model_version: str
    envelope_count: int
    evidence_requirement_count: int
    semantic_support_expectation_count: int
    unsupported_output_risk_count: int
    failure_candidate_count: int
    silent_failure_boundary: SemanticSilentFailureBoundary
    truth_label: FlowTruthLabel
    read_model_hash: str
    future_p5_required: bool = True
    proof_available: bool = False
    trace_verified: bool = False
    evidence_produced_any: bool = False
    verification_performed_any: bool = False

    def __post_init__(self) -> None:
        _forbid_true(
            self,
            "proof_available",
            "trace_verified",
            "evidence_produced_any",
            "verification_performed_any",
        )
        _forbid_false(self, "future_p5_required")


def build_proof_expectation_read_model(
    *,
    envelopes: tuple[ProofExpectationEnvelope, ...],
    semantic_support_expectations: tuple[SemanticSupportExpectation, ...] = (),
    unsupported_output_risks: tuple[UnsupportedOutputRisk, ...] = (),
) -> ProofExpectationReadModel:
    evidence_requirement_count = sum(
        len(envelope.evidence_requirements) for envelope in envelopes
    )
    failure_candidate_count = sum(
        1
        for envelope in envelopes
        for requirement in envelope.evidence_requirements
        if requirement.missing_evidence_is_failure_candidate
    ) + sum(
        1
        for expectation in semantic_support_expectations
        if expectation.unsupported_output_is_failure_candidate
    ) + sum(1 for risk in unsupported_output_risks if risk.is_failure_candidate)
    payload = {
        "read_model_version": PROOF_EXPECTATION_READ_MODEL_VERSION,
        "proof_expectation_ids": tuple(
            envelope.proof_expectation_id for envelope in envelopes
        ),
        "expectation_ids": tuple(
            expectation.expectation_id for expectation in semantic_support_expectations
        ),
        "risk_ids": tuple(risk.risk_id for risk in unsupported_output_risks),
    }
    return ProofExpectationReadModel(
        read_model_version=PROOF_EXPECTATION_READ_MODEL_VERSION,
        envelope_count=len(envelopes),
        evidence_requirement_count=evidence_requirement_count,
        semantic_support_expectation_count=len(semantic_support_expectations),
        unsupported_output_risk_count=len(unsupported_output_risks),
        failure_candidate_count=failure_candidate_count,
        silent_failure_boundary=build_semantic_silent_failure_boundary(),
        truth_label=FlowTruthLabel.READ_MODEL_ONLY,
        read_model_hash=stable_hash(payload),
    )
