"""P3-FLOW-G failure taxonomy / root-cause diagnosis layer (P3.15.5-P3.15.14).

A failure signal names a detected runtime failure; classifying it is
deterministic bookkeeping, not proof. A root-cause diagnosis is advisory:
confidence is not verification, and an evidence reference never retrieves
evidence. Semantic silent failures (missing evidence, unsupported output)
are runtime failure candidates, not harmless warnings. Nothing in this
module executes recovery, runs a verifier, or writes Trace/Ledger —
verified diagnosis belongs to P5 AurelTrace.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping

from .errors import AurelFlowErrorCode, AurelFlowValidationError
from .types import FlowTruthLabel, _CanonicalMixin, stable_hash
from .workflow_state import WorkflowRun

RUNTIME_FAILURE_SIGNAL_VERSION = "runtime_failure_signal.v1"
FAILURE_CLASSIFICATION_FRAME_VERSION = "failure_classification_frame.v1"
FAILURE_CLASSIFICATION_READ_MODEL_VERSION = "failure_classification_read_model.v1"
ROOT_CAUSE_DIAGNOSIS_VERSION = "root_cause_diagnosis.v1"
DIAGNOSIS_EVIDENCE_REF_VERSION = "diagnosis_evidence_ref.v1"
DIAGNOSIS_UNCERTAINTY_FRAME_VERSION = "diagnosis_uncertainty_frame.v1"
DIAGNOSIS_READ_MODEL_VERSION = "diagnosis_read_model.v1"
SEMANTIC_SILENT_FAILURE_SIGNAL_VERSION = "semantic_silent_failure_signal.v1"
UNSUPPORTED_OUTPUT_SIGNAL_VERSION = "unsupported_output_signal.v1"
EVIDENCE_MISSING_SIGNAL_VERSION = "evidence_missing_signal.v1"
EVIDENCE_SUPPORT_REQUIREMENT_VERSION = "evidence_support_requirement.v1"
CONTRADICTION_CHECK_REQUIREMENT_VERSION = "contradiction_check_requirement.v1"
SEMANTIC_FAILURE_READ_MODEL_VERSION = "semantic_failure_read_model.v1"

DIAGNOSIS_PROOF_UNAVAILABLE_REASON = (
    "a diagnosis is an advisory hypothesis over locally recorded state; it is "
    "never proof and never verification — the evidence spine belongs to P5 "
    "AurelTrace"
)
EVIDENCE_RETRIEVAL_UNAVAILABLE_REASON = (
    "an evidence reference names already-recorded local state by id only; no "
    "retrieval, source cross-check, or verifier execution exists in P3-FLOW-G"
)
VERIFIER_EXECUTION_UNAVAILABLE_REASON = (
    "no verifier executes in P3-FLOW-G; a contradiction check requirement "
    "requires a future check, it does not run one — execution belongs to P4 "
    "AurelExec and proof to P5 AurelTrace"
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


class RuntimeFailureKind(str, Enum):
    """Closed-world runtime failure taxonomy. Naming a failure fixes nothing."""

    TOOL_TIMEOUT = "TOOL_TIMEOUT"
    TOOL_RATE_LIMITED = "TOOL_RATE_LIMITED"
    TOOL_UNAVAILABLE = "TOOL_UNAVAILABLE"
    SCHEMA_MISMATCH = "SCHEMA_MISMATCH"
    MALFORMED_JSON = "MALFORMED_JSON"
    MISSING_FIELD = "MISSING_FIELD"
    TYPE_ERROR = "TYPE_ERROR"
    CONTEXT_DECAY = "CONTEXT_DECAY"
    STALE_RETRIEVAL = "STALE_RETRIEVAL"
    CONTRADICTORY_EVIDENCE = "CONTRADICTORY_EVIDENCE"
    CONTROL_LOOP_COLLAPSE = "CONTROL_LOOP_COLLAPSE"
    RETRY_STORM = "RETRY_STORM"
    NO_PROGRESS = "NO_PROGRESS"
    SEMANTIC_SILENT_FAILURE = "SEMANTIC_SILENT_FAILURE"
    UNSUPPORTED_OUTPUT = "UNSUPPORTED_OUTPUT"
    EVIDENCE_MISSING = "EVIDENCE_MISSING"
    TOPOLOGY_AMPLIFICATION_RISK = "TOPOLOGY_AMPLIFICATION_RISK"
    DIVERSITY_CORRELATION_RISK = "DIVERSITY_CORRELATION_RISK"
    CHECKPOINT_REQUIRED_MISSING = "CHECKPOINT_REQUIRED_MISSING"
    UNKNOWN = "UNKNOWN"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"


class FailureSeverity(str, Enum):
    """Failure severity. Severity is bookkeeping, not urgency-driven execution."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
    UNKNOWN = "UNKNOWN"


class FailureRootCauseCategory(str, Enum):
    """Where a failure likely originates. A category is a hypothesis bucket."""

    TOOL_INFRASTRUCTURE = "TOOL_INFRASTRUCTURE"
    SCHEMA_CONTRACT = "SCHEMA_CONTRACT"
    CONTEXT_EVIDENCE = "CONTEXT_EVIDENCE"
    CONTROL_LOOP = "CONTROL_LOOP"
    SEMANTIC_OUTPUT = "SEMANTIC_OUTPUT"
    TOPOLOGY_STRUCTURE = "TOPOLOGY_STRUCTURE"
    CHECKPOINT_DISCIPLINE = "CHECKPOINT_DISCIPLINE"
    UNKNOWN = "UNKNOWN"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"


class DiagnosisConfidence(str, Enum):
    """Advisory diagnosis confidence.

    Deliberately closed-world: there is no CERTAIN, PROVEN, or VERIFIED
    member, so a diagnosis structurally cannot claim proof-grade confidence.
    """

    VERY_LOW = "VERY_LOW"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    UNKNOWN = "UNKNOWN"


LOW_CONFIDENCE_DIAGNOSIS_LEVELS: tuple[DiagnosisConfidence, ...] = (
    DiagnosisConfidence.VERY_LOW,
    DiagnosisConfidence.LOW,
    DiagnosisConfidence.UNKNOWN,
)


@dataclass(frozen=True)
class RuntimeFailureSignal(_CanonicalMixin):
    """A detected runtime failure. Detection is not a fix and not proof."""

    failure_signal_id: str
    contract_version: str
    run_id: str
    failure_kind: RuntimeFailureKind
    detail: str
    detected_at_logical_sequence: int
    truth_label: FlowTruthLabel
    node_id: str = ""
    source_event_id: str = ""
    unavailable_reason: str = DIAGNOSIS_PROOF_UNAVAILABLE_REASON
    proof_available: bool = False
    trace_verified: bool = False
    recovery_executed: bool = False

    def __post_init__(self) -> None:
        _forbid_true(self, "proof_available", "trace_verified", "recovery_executed")


def create_runtime_failure_signal(
    run: WorkflowRun,
    *,
    failure_kind: RuntimeFailureKind,
    detail: str,
    node_id: str = "",
    source_event_id: str = "",
) -> RuntimeFailureSignal:
    """Name a detected failure over an existing run. Pure derivation: the
    logical sequence anchor is the run's own step counter, never a wall clock."""

    payload = {
        "contract_version": RUNTIME_FAILURE_SIGNAL_VERSION,
        "run_id": run.run_id,
        "failure_kind": failure_kind.value,
        "detail": detail,
        "detected_at_logical_sequence": run.state.step,
        "node_id": node_id,
        "source_event_id": source_event_id,
    }
    return RuntimeFailureSignal(
        failure_signal_id="flfsg-" + stable_hash(payload)[:16],
        contract_version=RUNTIME_FAILURE_SIGNAL_VERSION,
        run_id=run.run_id,
        failure_kind=failure_kind,
        detail=detail,
        detected_at_logical_sequence=run.state.step,
        truth_label=FlowTruthLabel.LOCAL_RUNTIME_SUBSTRATE,
        node_id=node_id,
        source_event_id=source_event_id,
    )


_FAILURE_CLASSIFICATION_TABLE: Mapping[
    RuntimeFailureKind, tuple[FailureRootCauseCategory, FailureSeverity]
] = {
    RuntimeFailureKind.TOOL_TIMEOUT: (
        FailureRootCauseCategory.TOOL_INFRASTRUCTURE,
        FailureSeverity.MEDIUM,
    ),
    RuntimeFailureKind.TOOL_RATE_LIMITED: (
        FailureRootCauseCategory.TOOL_INFRASTRUCTURE,
        FailureSeverity.MEDIUM,
    ),
    RuntimeFailureKind.TOOL_UNAVAILABLE: (
        FailureRootCauseCategory.TOOL_INFRASTRUCTURE,
        FailureSeverity.HIGH,
    ),
    RuntimeFailureKind.SCHEMA_MISMATCH: (
        FailureRootCauseCategory.SCHEMA_CONTRACT,
        FailureSeverity.MEDIUM,
    ),
    RuntimeFailureKind.MALFORMED_JSON: (
        FailureRootCauseCategory.SCHEMA_CONTRACT,
        FailureSeverity.MEDIUM,
    ),
    RuntimeFailureKind.MISSING_FIELD: (
        FailureRootCauseCategory.SCHEMA_CONTRACT,
        FailureSeverity.LOW,
    ),
    RuntimeFailureKind.TYPE_ERROR: (
        FailureRootCauseCategory.SCHEMA_CONTRACT,
        FailureSeverity.MEDIUM,
    ),
    RuntimeFailureKind.CONTEXT_DECAY: (
        FailureRootCauseCategory.CONTEXT_EVIDENCE,
        FailureSeverity.MEDIUM,
    ),
    RuntimeFailureKind.STALE_RETRIEVAL: (
        FailureRootCauseCategory.CONTEXT_EVIDENCE,
        FailureSeverity.MEDIUM,
    ),
    RuntimeFailureKind.CONTRADICTORY_EVIDENCE: (
        FailureRootCauseCategory.CONTEXT_EVIDENCE,
        FailureSeverity.HIGH,
    ),
    RuntimeFailureKind.CONTROL_LOOP_COLLAPSE: (
        FailureRootCauseCategory.CONTROL_LOOP,
        FailureSeverity.CRITICAL,
    ),
    RuntimeFailureKind.RETRY_STORM: (
        FailureRootCauseCategory.CONTROL_LOOP,
        FailureSeverity.HIGH,
    ),
    RuntimeFailureKind.NO_PROGRESS: (
        FailureRootCauseCategory.CONTROL_LOOP,
        FailureSeverity.HIGH,
    ),
    RuntimeFailureKind.SEMANTIC_SILENT_FAILURE: (
        FailureRootCauseCategory.SEMANTIC_OUTPUT,
        FailureSeverity.HIGH,
    ),
    RuntimeFailureKind.UNSUPPORTED_OUTPUT: (
        FailureRootCauseCategory.SEMANTIC_OUTPUT,
        FailureSeverity.HIGH,
    ),
    RuntimeFailureKind.EVIDENCE_MISSING: (
        FailureRootCauseCategory.SEMANTIC_OUTPUT,
        FailureSeverity.HIGH,
    ),
    RuntimeFailureKind.TOPOLOGY_AMPLIFICATION_RISK: (
        FailureRootCauseCategory.TOPOLOGY_STRUCTURE,
        FailureSeverity.HIGH,
    ),
    RuntimeFailureKind.DIVERSITY_CORRELATION_RISK: (
        FailureRootCauseCategory.TOPOLOGY_STRUCTURE,
        FailureSeverity.HIGH,
    ),
    RuntimeFailureKind.CHECKPOINT_REQUIRED_MISSING: (
        FailureRootCauseCategory.CHECKPOINT_DISCIPLINE,
        FailureSeverity.HIGH,
    ),
    RuntimeFailureKind.UNKNOWN: (
        FailureRootCauseCategory.UNKNOWN,
        FailureSeverity.UNKNOWN,
    ),
    RuntimeFailureKind.UNAVAILABLE: (
        FailureRootCauseCategory.UNAVAILABLE,
        FailureSeverity.UNKNOWN,
    ),
    RuntimeFailureKind.ERROR: (
        FailureRootCauseCategory.ERROR,
        FailureSeverity.UNKNOWN,
    ),
}


def failure_classification_table() -> Mapping[
    RuntimeFailureKind, tuple[FailureRootCauseCategory, FailureSeverity]
]:
    """The total deterministic kind -> (category, severity) table."""

    return dict(_FAILURE_CLASSIFICATION_TABLE)


@dataclass(frozen=True)
class FailureClassificationFrame(_CanonicalMixin):
    """Deterministic classification of one failure signal. Not proof."""

    classification_id: str
    contract_version: str
    failure_signal_id: str
    run_id: str
    failure_kind: RuntimeFailureKind
    severity: FailureSeverity
    root_cause_category: FailureRootCauseCategory
    truth_label: FlowTruthLabel
    unavailable_reason: str = DIAGNOSIS_PROOF_UNAVAILABLE_REASON
    classification_is_not_proof: bool = True
    proof_available: bool = False
    trace_verified: bool = False
    recovery_executed: bool = False

    def __post_init__(self) -> None:
        _forbid_false(self, "classification_is_not_proof")
        _forbid_true(self, "proof_available", "trace_verified", "recovery_executed")


def classify_runtime_failure(
    failure_signal: RuntimeFailureSignal,
) -> FailureClassificationFrame:
    """Deterministically classify a failure signal from the closed-world table."""

    category, severity = _FAILURE_CLASSIFICATION_TABLE[failure_signal.failure_kind]
    payload = {
        "contract_version": FAILURE_CLASSIFICATION_FRAME_VERSION,
        "failure_signal_id": failure_signal.failure_signal_id,
        "failure_kind": failure_signal.failure_kind.value,
        "severity": severity.value,
        "root_cause_category": category.value,
    }
    return FailureClassificationFrame(
        classification_id="flfcf-" + stable_hash(payload)[:16],
        contract_version=FAILURE_CLASSIFICATION_FRAME_VERSION,
        failure_signal_id=failure_signal.failure_signal_id,
        run_id=failure_signal.run_id,
        failure_kind=failure_signal.failure_kind,
        severity=severity,
        root_cause_category=category,
        truth_label=FlowTruthLabel.LOCAL_RUNTIME_SUBSTRATE,
    )


@dataclass(frozen=True)
class FailureClassificationReadModel(_CanonicalMixin):
    """Deterministic aggregate over classification frames."""

    read_model_version: str
    run_id: str
    classification_count: int
    severity_counts: Mapping[str, int]
    category_counts: Mapping[str, int]
    critical_present: bool
    truth_label: FlowTruthLabel
    read_model_hash: str
    classification_is_not_proof: bool = True
    proof_available: bool = False

    def __post_init__(self) -> None:
        _forbid_false(self, "classification_is_not_proof")
        _forbid_true(self, "proof_available")


def build_failure_classification_read_model(
    run_id: str, frames: tuple[FailureClassificationFrame, ...]
) -> FailureClassificationReadModel:
    for frame in frames:
        if frame.run_id != run_id:
            raise AurelFlowValidationError(
                f"classification frame run {frame.run_id!r} does not match "
                f"read model run {run_id!r}",
                code=AurelFlowErrorCode.RUN_MISMATCH,
                field="frames",
            )
    severity_counts: dict[str, int] = {}
    category_counts: dict[str, int] = {}
    for frame in frames:
        severity_counts[frame.severity.value] = (
            severity_counts.get(frame.severity.value, 0) + 1
        )
        category_counts[frame.root_cause_category.value] = (
            category_counts.get(frame.root_cause_category.value, 0) + 1
        )
    payload = {
        "read_model_version": FAILURE_CLASSIFICATION_READ_MODEL_VERSION,
        "run_id": run_id,
        "classification_ids": tuple(frame.classification_id for frame in frames),
    }
    return FailureClassificationReadModel(
        read_model_version=FAILURE_CLASSIFICATION_READ_MODEL_VERSION,
        run_id=run_id,
        classification_count=len(frames),
        severity_counts=severity_counts,
        category_counts=category_counts,
        critical_present=any(
            frame.severity is FailureSeverity.CRITICAL for frame in frames
        ),
        truth_label=FlowTruthLabel.READ_MODEL_ONLY,
        read_model_hash=stable_hash(payload),
    )


class DiagnosisEvidenceKind(str, Enum):
    """What kind of already-recorded local state an evidence ref names."""

    RUNTIME_EVENT = "RUNTIME_EVENT"
    STATE_COMMITMENT = "STATE_COMMITMENT"
    CHECKPOINT_SNAPSHOT = "CHECKPOINT_SNAPSHOT"
    TOPOLOGY_SNAPSHOT = "TOPOLOGY_SNAPSHOT"
    RUNTIME_DIFF = "RUNTIME_DIFF"
    FAILURE_SIGNAL = "FAILURE_SIGNAL"
    OPERATOR_NOTE = "OPERATOR_NOTE"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"


@dataclass(frozen=True)
class DiagnosisEvidenceRef(_CanonicalMixin):
    """Reference to already-recorded local state. A ref never retrieves."""

    evidence_ref_id: str
    ref_version: str
    evidence_kind: DiagnosisEvidenceKind
    target_id: str
    truth_label: FlowTruthLabel
    unavailable_reason: str = EVIDENCE_RETRIEVAL_UNAVAILABLE_REASON
    evidence_retrieved: bool = False
    retrieval_available: bool = False
    proof_available: bool = False

    def __post_init__(self) -> None:
        _forbid_true(
            self, "evidence_retrieved", "retrieval_available", "proof_available"
        )


def create_diagnosis_evidence_ref(
    *, evidence_kind: DiagnosisEvidenceKind, target_id: str
) -> DiagnosisEvidenceRef:
    payload = {
        "ref_version": DIAGNOSIS_EVIDENCE_REF_VERSION,
        "evidence_kind": evidence_kind.value,
        "target_id": target_id,
    }
    return DiagnosisEvidenceRef(
        evidence_ref_id="fldev-" + stable_hash(payload)[:16],
        ref_version=DIAGNOSIS_EVIDENCE_REF_VERSION,
        evidence_kind=evidence_kind,
        target_id=target_id,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
    )


@dataclass(frozen=True)
class RootCauseDiagnosis(_CanonicalMixin):
    """Advisory root-cause hypothesis for one failure signal. Not proof.

    Low confidence fail-closes into mandatory human review: a diagnosis with
    VERY_LOW, LOW, or UNKNOWN confidence cannot be constructed without
    ``requires_human_review`` set True.
    """

    diagnosis_id: str
    contract_version: str
    failure_signal_id: str
    run_id: str
    candidate_root_cause: FailureRootCauseCategory
    confidence: DiagnosisConfidence
    diagnostic_evidence_refs: tuple[DiagnosisEvidenceRef, ...]
    uncertainty_reason: str
    truth_label: FlowTruthLabel
    requires_human_review: bool
    requires_verifier: bool = True
    requires_checkpoint: bool = True
    requires_topology_review: bool = False
    unavailable_reason: str = DIAGNOSIS_PROOF_UNAVAILABLE_REASON
    diagnosis_is_not_proof: bool = True
    proof_available: bool = False
    trace_verified: bool = False
    recovery_executed: bool = False

    def __post_init__(self) -> None:
        _forbid_false(self, "diagnosis_is_not_proof")
        _forbid_true(self, "proof_available", "trace_verified", "recovery_executed")
        if (
            self.confidence in LOW_CONFIDENCE_DIAGNOSIS_LEVELS
            and not self.requires_human_review
        ):
            raise AurelFlowValidationError(
                f"diagnosis with {self.confidence.value} confidence must "
                "require human review",
                code=AurelFlowErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                field="requires_human_review",
            )


def create_root_cause_diagnosis(
    failure_signal: RuntimeFailureSignal,
    *,
    candidate_root_cause: FailureRootCauseCategory,
    confidence: DiagnosisConfidence,
    diagnostic_evidence_refs: tuple[DiagnosisEvidenceRef, ...] = (),
    uncertainty_reason: str = "",
    requires_human_review: bool = False,
    requires_topology_review: bool = False,
) -> RootCauseDiagnosis:
    """Derive an advisory diagnosis. Low confidence forces human review."""

    forced_review = (
        requires_human_review or confidence in LOW_CONFIDENCE_DIAGNOSIS_LEVELS
    )
    payload = {
        "contract_version": ROOT_CAUSE_DIAGNOSIS_VERSION,
        "failure_signal_id": failure_signal.failure_signal_id,
        "candidate_root_cause": candidate_root_cause.value,
        "confidence": confidence.value,
        "evidence_ref_ids": tuple(
            ref.evidence_ref_id for ref in diagnostic_evidence_refs
        ),
        "uncertainty_reason": uncertainty_reason,
    }
    return RootCauseDiagnosis(
        diagnosis_id="fldia-" + stable_hash(payload)[:16],
        contract_version=ROOT_CAUSE_DIAGNOSIS_VERSION,
        failure_signal_id=failure_signal.failure_signal_id,
        run_id=failure_signal.run_id,
        candidate_root_cause=candidate_root_cause,
        confidence=confidence,
        diagnostic_evidence_refs=diagnostic_evidence_refs,
        uncertainty_reason=uncertainty_reason,
        truth_label=FlowTruthLabel.LOCAL_RUNTIME_SUBSTRATE,
        requires_human_review=forced_review,
        requires_topology_review=requires_topology_review,
    )


@dataclass(frozen=True)
class DiagnosisUncertaintyFrame(_CanonicalMixin):
    """Explicit uncertainty record for a diagnosis. Doubt is first-class."""

    uncertainty_frame_id: str
    contract_version: str
    diagnosis_id: str
    run_id: str
    uncertainty_reason: str
    alternative_root_causes: tuple[FailureRootCauseCategory, ...]
    truth_label: FlowTruthLabel
    requires_human_review: bool = True
    unavailable_reason: str = DIAGNOSIS_PROOF_UNAVAILABLE_REASON
    proof_available: bool = False

    def __post_init__(self) -> None:
        _forbid_false(self, "requires_human_review")
        _forbid_true(self, "proof_available")


def build_diagnosis_uncertainty_frame(
    diagnosis: RootCauseDiagnosis,
    *,
    uncertainty_reason: str,
    alternative_root_causes: tuple[FailureRootCauseCategory, ...] = (),
) -> DiagnosisUncertaintyFrame:
    payload = {
        "contract_version": DIAGNOSIS_UNCERTAINTY_FRAME_VERSION,
        "diagnosis_id": diagnosis.diagnosis_id,
        "uncertainty_reason": uncertainty_reason,
        "alternative_root_causes": tuple(
            category.value for category in alternative_root_causes
        ),
    }
    return DiagnosisUncertaintyFrame(
        uncertainty_frame_id="flduf-" + stable_hash(payload)[:16],
        contract_version=DIAGNOSIS_UNCERTAINTY_FRAME_VERSION,
        diagnosis_id=diagnosis.diagnosis_id,
        run_id=diagnosis.run_id,
        uncertainty_reason=uncertainty_reason,
        alternative_root_causes=alternative_root_causes,
        truth_label=FlowTruthLabel.LOCAL_RUNTIME_SUBSTRATE,
    )


@dataclass(frozen=True)
class DiagnosisReadModel(_CanonicalMixin):
    """Deterministic aggregate over diagnoses. Aggregation is not proof."""

    read_model_version: str
    run_id: str
    diagnosis_count: int
    low_confidence_count: int
    requires_human_review_count: int
    any_requires_human_review: bool
    truth_label: FlowTruthLabel
    read_model_hash: str
    diagnosis_is_not_proof: bool = True
    proof_available: bool = False
    trace_verified: bool = False

    def __post_init__(self) -> None:
        _forbid_false(self, "diagnosis_is_not_proof")
        _forbid_true(self, "proof_available", "trace_verified")


def build_diagnosis_read_model(
    run_id: str, diagnoses: tuple[RootCauseDiagnosis, ...]
) -> DiagnosisReadModel:
    for diagnosis in diagnoses:
        if diagnosis.run_id != run_id:
            raise AurelFlowValidationError(
                f"diagnosis run {diagnosis.run_id!r} does not match read "
                f"model run {run_id!r}",
                code=AurelFlowErrorCode.RUN_MISMATCH,
                field="diagnoses",
            )
    low_confidence_count = sum(
        1
        for diagnosis in diagnoses
        if diagnosis.confidence in LOW_CONFIDENCE_DIAGNOSIS_LEVELS
    )
    review_count = sum(
        1 for diagnosis in diagnoses if diagnosis.requires_human_review
    )
    payload = {
        "read_model_version": DIAGNOSIS_READ_MODEL_VERSION,
        "run_id": run_id,
        "diagnosis_ids": tuple(diagnosis.diagnosis_id for diagnosis in diagnoses),
    }
    return DiagnosisReadModel(
        read_model_version=DIAGNOSIS_READ_MODEL_VERSION,
        run_id=run_id,
        diagnosis_count=len(diagnoses),
        low_confidence_count=low_confidence_count,
        requires_human_review_count=review_count,
        any_requires_human_review=review_count > 0,
        truth_label=FlowTruthLabel.READ_MODEL_ONLY,
        read_model_hash=stable_hash(payload),
    )


@dataclass(frozen=True)
class SemanticSilentFailureSignal(_CanonicalMixin):
    """Output that looks fine but is semantically unsupported.

    A semantic silent failure is a runtime failure candidate, never a
    harmless warning.
    """

    semantic_failure_signal_id: str
    contract_version: str
    run_id: str
    detail: str
    detected_at_logical_sequence: int
    truth_label: FlowTruthLabel
    node_id: str = ""
    as_runtime_failure_kind: RuntimeFailureKind = (
        RuntimeFailureKind.SEMANTIC_SILENT_FAILURE
    )
    unavailable_reason: str = VERIFIER_EXECUTION_UNAVAILABLE_REASON
    treated_as_runtime_failure_candidate: bool = True
    is_harmless_warning: bool = False
    proof_available: bool = False
    trace_verified: bool = False

    def __post_init__(self) -> None:
        _forbid_false(self, "treated_as_runtime_failure_candidate")
        _forbid_true(self, "is_harmless_warning", "proof_available", "trace_verified")


def create_semantic_silent_failure_signal(
    run: WorkflowRun, *, detail: str, node_id: str = ""
) -> SemanticSilentFailureSignal:
    payload = {
        "contract_version": SEMANTIC_SILENT_FAILURE_SIGNAL_VERSION,
        "run_id": run.run_id,
        "detail": detail,
        "detected_at_logical_sequence": run.state.step,
        "node_id": node_id,
    }
    return SemanticSilentFailureSignal(
        semantic_failure_signal_id="flssf-" + stable_hash(payload)[:16],
        contract_version=SEMANTIC_SILENT_FAILURE_SIGNAL_VERSION,
        run_id=run.run_id,
        detail=detail,
        detected_at_logical_sequence=run.state.step,
        truth_label=FlowTruthLabel.LOCAL_RUNTIME_SUBSTRATE,
        node_id=node_id,
    )


@dataclass(frozen=True)
class UnsupportedOutputSignal(_CanonicalMixin):
    """Output not supported by recorded evidence. A failure candidate."""

    signal_id: str
    contract_version: str
    run_id: str
    detail: str
    detected_at_logical_sequence: int
    truth_label: FlowTruthLabel
    node_id: str = ""
    unsupported_output_detected: bool = True
    as_runtime_failure_kind: RuntimeFailureKind = RuntimeFailureKind.UNSUPPORTED_OUTPUT
    unavailable_reason: str = VERIFIER_EXECUTION_UNAVAILABLE_REASON
    treated_as_runtime_failure_candidate: bool = True
    is_harmless_warning: bool = False
    proof_available: bool = False

    def __post_init__(self) -> None:
        _forbid_false(
            self, "unsupported_output_detected", "treated_as_runtime_failure_candidate"
        )
        _forbid_true(self, "is_harmless_warning", "proof_available")


def create_unsupported_output_signal(
    run: WorkflowRun, *, detail: str, node_id: str = ""
) -> UnsupportedOutputSignal:
    payload = {
        "contract_version": UNSUPPORTED_OUTPUT_SIGNAL_VERSION,
        "run_id": run.run_id,
        "detail": detail,
        "detected_at_logical_sequence": run.state.step,
        "node_id": node_id,
    }
    return UnsupportedOutputSignal(
        signal_id="fluos-" + stable_hash(payload)[:16],
        contract_version=UNSUPPORTED_OUTPUT_SIGNAL_VERSION,
        run_id=run.run_id,
        detail=detail,
        detected_at_logical_sequence=run.state.step,
        truth_label=FlowTruthLabel.LOCAL_RUNTIME_SUBSTRATE,
        node_id=node_id,
    )


@dataclass(frozen=True)
class EvidenceMissingSignal(_CanonicalMixin):
    """Required evidence is absent. Absence is a failure candidate."""

    signal_id: str
    contract_version: str
    run_id: str
    detail: str
    detected_at_logical_sequence: int
    truth_label: FlowTruthLabel
    node_id: str = ""
    evidence_missing: bool = True
    as_runtime_failure_kind: RuntimeFailureKind = RuntimeFailureKind.EVIDENCE_MISSING
    unavailable_reason: str = EVIDENCE_RETRIEVAL_UNAVAILABLE_REASON
    treated_as_runtime_failure_candidate: bool = True
    is_harmless_warning: bool = False
    proof_available: bool = False

    def __post_init__(self) -> None:
        _forbid_false(
            self, "evidence_missing", "treated_as_runtime_failure_candidate"
        )
        _forbid_true(self, "is_harmless_warning", "proof_available")


def create_evidence_missing_signal(
    run: WorkflowRun, *, detail: str, node_id: str = ""
) -> EvidenceMissingSignal:
    payload = {
        "contract_version": EVIDENCE_MISSING_SIGNAL_VERSION,
        "run_id": run.run_id,
        "detail": detail,
        "detected_at_logical_sequence": run.state.step,
        "node_id": node_id,
    }
    return EvidenceMissingSignal(
        signal_id="flems-" + stable_hash(payload)[:16],
        contract_version=EVIDENCE_MISSING_SIGNAL_VERSION,
        run_id=run.run_id,
        detail=detail,
        detected_at_logical_sequence=run.state.step,
        truth_label=FlowTruthLabel.LOCAL_RUNTIME_SUBSTRATE,
        node_id=node_id,
    )


@dataclass(frozen=True)
class EvidenceSupportRequirement(_CanonicalMixin):
    """Future outputs must be evidence-supported. Requiring is not retrieving."""

    requirement_id: str
    contract_version: str
    run_id: str
    truth_label: FlowTruthLabel
    node_id: str = ""
    failure_signal_id: str = ""
    unavailable_reason: str = EVIDENCE_RETRIEVAL_UNAVAILABLE_REASON
    semantic_support_required: bool = True
    requires_evidence_verification_candidate: bool = True
    evidence_retrieved: bool = False
    retrieval_available: bool = False
    proof_available: bool = False

    def __post_init__(self) -> None:
        _forbid_false(
            self,
            "semantic_support_required",
            "requires_evidence_verification_candidate",
        )
        _forbid_true(
            self, "evidence_retrieved", "retrieval_available", "proof_available"
        )


def create_evidence_support_requirement(
    *, run_id: str, node_id: str = "", failure_signal_id: str = ""
) -> EvidenceSupportRequirement:
    payload = {
        "contract_version": EVIDENCE_SUPPORT_REQUIREMENT_VERSION,
        "run_id": run_id,
        "node_id": node_id,
        "failure_signal_id": failure_signal_id,
    }
    return EvidenceSupportRequirement(
        requirement_id="flesr-" + stable_hash(payload)[:16],
        contract_version=EVIDENCE_SUPPORT_REQUIREMENT_VERSION,
        run_id=run_id,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
        node_id=node_id,
        failure_signal_id=failure_signal_id,
    )


@dataclass(frozen=True)
class ContradictionCheckRequirement(_CanonicalMixin):
    """Contradictory evidence must be checked later. Requiring runs no verifier."""

    requirement_id: str
    contract_version: str
    run_id: str
    truth_label: FlowTruthLabel
    failure_signal_id: str = ""
    unavailable_reason: str = VERIFIER_EXECUTION_UNAVAILABLE_REASON
    contradiction_check_required: bool = True
    requires_verifier: bool = True
    verifier_executed: bool = False
    proof_available: bool = False
    trace_verified: bool = False

    def __post_init__(self) -> None:
        _forbid_false(self, "contradiction_check_required", "requires_verifier")
        _forbid_true(self, "verifier_executed", "proof_available", "trace_verified")


def create_contradiction_check_requirement(
    *, run_id: str, failure_signal_id: str = ""
) -> ContradictionCheckRequirement:
    payload = {
        "contract_version": CONTRADICTION_CHECK_REQUIREMENT_VERSION,
        "run_id": run_id,
        "failure_signal_id": failure_signal_id,
    }
    return ContradictionCheckRequirement(
        requirement_id="flccr-" + stable_hash(payload)[:16],
        contract_version=CONTRADICTION_CHECK_REQUIREMENT_VERSION,
        run_id=run_id,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
        failure_signal_id=failure_signal_id,
    )


@dataclass(frozen=True)
class SemanticFailureReadModel(_CanonicalMixin):
    """Deterministic aggregate over semantic failure signals and requirements."""

    read_model_version: str
    run_id: str
    semantic_silent_failure_count: int
    unsupported_output_count: int
    evidence_missing_count: int
    evidence_support_requirement_count: int
    contradiction_check_requirement_count: int
    any_semantic_failure_candidate: bool
    truth_label: FlowTruthLabel
    read_model_hash: str
    semantic_failures_are_failure_candidates: bool = True
    verifier_executed: bool = False
    proof_available: bool = False

    def __post_init__(self) -> None:
        _forbid_false(self, "semantic_failures_are_failure_candidates")
        _forbid_true(self, "verifier_executed", "proof_available")


def build_semantic_failure_read_model(
    run_id: str,
    *,
    semantic_silent_failures: tuple[SemanticSilentFailureSignal, ...] = (),
    unsupported_outputs: tuple[UnsupportedOutputSignal, ...] = (),
    evidence_missing_signals: tuple[EvidenceMissingSignal, ...] = (),
    evidence_support_requirements: tuple[EvidenceSupportRequirement, ...] = (),
    contradiction_check_requirements: tuple[ContradictionCheckRequirement, ...] = (),
) -> SemanticFailureReadModel:
    signal_run_ids = (
        tuple(signal.run_id for signal in semantic_silent_failures)
        + tuple(signal.run_id for signal in unsupported_outputs)
        + tuple(signal.run_id for signal in evidence_missing_signals)
        + tuple(requirement.run_id for requirement in evidence_support_requirements)
        + tuple(
            requirement.run_id for requirement in contradiction_check_requirements
        )
    )
    for signal_run_id in signal_run_ids:
        if signal_run_id != run_id:
            raise AurelFlowValidationError(
                f"semantic signal run {signal_run_id!r} does not match read "
                f"model run {run_id!r}",
                code=AurelFlowErrorCode.RUN_MISMATCH,
                field="signals",
            )
    payload = {
        "read_model_version": SEMANTIC_FAILURE_READ_MODEL_VERSION,
        "run_id": run_id,
        "semantic_ids": tuple(
            signal.semantic_failure_signal_id for signal in semantic_silent_failures
        ),
        "unsupported_ids": tuple(
            signal.signal_id for signal in unsupported_outputs
        ),
        "missing_ids": tuple(
            signal.signal_id for signal in evidence_missing_signals
        ),
    }
    any_candidate = bool(
        semantic_silent_failures or unsupported_outputs or evidence_missing_signals
    )
    return SemanticFailureReadModel(
        read_model_version=SEMANTIC_FAILURE_READ_MODEL_VERSION,
        run_id=run_id,
        semantic_silent_failure_count=len(semantic_silent_failures),
        unsupported_output_count=len(unsupported_outputs),
        evidence_missing_count=len(evidence_missing_signals),
        evidence_support_requirement_count=len(evidence_support_requirements),
        contradiction_check_requirement_count=len(contradiction_check_requirements),
        any_semantic_failure_candidate=any_candidate,
        truth_label=FlowTruthLabel.READ_MODEL_ONLY,
        read_model_hash=stable_hash(payload),
    )
