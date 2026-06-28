"""Output Passport operator test path and readiness audit (P1.9-C).

P1.9.22 operator-testable path, P1.9.26 readiness audit, and P1.9-C pack result.

Architectural law:
  - Operator-testable path is not CLI/live demo.
  - Readiness audit is not exit seal.
  - TEST_PATH_ONLY is not product readiness.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
from typing import Any

from .disclosure_states import (
    build_heretic_quarantined_output_disclosure,
    build_lora_adapter_influence_disclosure,
    build_mock_dev_fixture_simulated_disclosure,
)
from .foundation import (
    FORBIDDEN_DEFAULT_TRUTH_LABELS,
    OutputPassportCheckpointRead,
    OutputPassportCheckpointStatus,
    OutputPassportErrorCode,
    OutputPassportPayload,
    OutputPassportSideEffectProof,
    OutputPassportSourceLabel,
    OutputPassportTruthLabel,
    OutputPassportUnavailableReason,
    OutputPassportValidationError,
    build_dev_fixture_output_passport_payload,
    build_p1_9_a_passport_pack_result,
    stable_hash,
    to_canonical_json,
)
from .read_model import build_output_passport_read_model
from .revision_replay_failure import (
    build_output_passport_failure_unavailable_handling,
    build_output_passport_replay_seed,
    build_output_passport_revision_history,
)
from .surface_read_model import build_all_surface_passport_read_models
from .test_harness import run_output_passport_invariant_harness
from .truth_boundary import build_trace_payload_vs_verification_boundary

OUTPUT_PASSPORT_P1_9_C_PACK_TASK_ID = "P1.9-C"
OUTPUT_PASSPORT_P1_9_C_SECTION_ID = "P1.9"
OUTPUT_PASSPORT_P1_9_C_CHECKPOINT_IDS = (
    "P1.9.17",
    "P1.9.18",
    "P1.9.19",
    "P1.9.20",
    "P1.9.21",
    "P1.9.22",
    "P1.9.23",
    "P1.9.24",
    "P1.9.25",
    "P1.9.26",
)
OUTPUT_PASSPORT_P1_9_C_NEXT_PACK_ID = "P1.9-D"
OUTPUT_PASSPORT_P1_9_C_PACK_RESULT_VERSION = (
    "output_passport_p1_9_c_pack_result.v1"
)
OUTPUT_PASSPORT_OPERATOR_TEST_PATH_VERSION = (
    "output_passport_operator_test_path.v1"
)
OUTPUT_PASSPORT_TEST_PATH_STEP_VERSION = "output_passport_test_path_step.v1"
OUTPUT_PASSPORT_TEST_PATH_RESULT_VERSION = (
    "output_passport_test_path_result.v1"
)
OUTPUT_PASSPORT_READINESS_AUDIT_VERSION = (
    "output_passport_readiness_audit.v1"
)
OUTPUT_PASSPORT_READINESS_AUDIT_RESULT_VERSION = (
    "output_passport_readiness_audit_result.v1"
)
OUTPUT_PASSPORT_READINESS_CHECKLIST_VERSION = (
    "output_passport_readiness_checklist.v1"
)


class OutputPassportReadinessAuditStatus(str, Enum):
    """Readiness audit outcome — not exit seal."""

    READY = "ready"
    NOT_READY = "not_ready"
    BLOCKED = "blocked"
    CONDITIONAL = "conditional"


class OutputPassportTestPathStepId(str, Enum):
    """Closed-world operator test path steps."""

    FIXTURE_INPUT = "fixture_input"
    READ_MODEL_CREATION = "read_model_creation"
    TRUTH_BOUNDARY_VALIDATION = "truth_boundary_validation"
    FAILURE_UNAVAILABLE_VALIDATION = "failure_unavailable_validation"
    READINESS_AUDIT_EXECUTION = "readiness_audit_execution"
    RESULT_SUMMARY = "result_summary"


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
class OutputPassportTestPathStep(_CanonicalMixin):
    """Single operator test path step."""

    schema_version: str
    step_id: OutputPassportTestPathStepId
    step_label: str
    passed: bool
    truth_label: OutputPassportTruthLabel
    source_label: OutputPassportSourceLabel
    notes: str
    step_hash: str


@dataclass(frozen=True)
class OutputPassportTestPathResult(_CanonicalMixin):
    """Result of operator test path execution."""

    schema_version: str
    all_steps_passed: bool
    fake_live_detected: bool
    fake_trace_verified_detected: bool
    fake_seal_detected: bool
    steps: tuple[OutputPassportTestPathStep, ...]
    truth_label: OutputPassportTruthLabel
    source_label: OutputPassportSourceLabel
    side_effects: OutputPassportSideEffectProof
    test_path_result_hash: str


@dataclass(frozen=True)
class OutputPassportOperatorTestPath(_CanonicalMixin):
    """P1.9.22 local operator-testable path — not CLI."""

    schema_version: str
    checkpoint_id: str
    path_label: str
    steps: tuple[OutputPassportTestPathStep, ...]
    result: OutputPassportTestPathResult
    truth_label: OutputPassportTruthLabel
    source_label: OutputPassportSourceLabel
    side_effects: OutputPassportSideEffectProof
    operator_test_path_hash: str


@dataclass(frozen=True)
class OutputPassportReadinessChecklist(_CanonicalMixin):
    """Checklist items for P1.9 readiness audit."""

    schema_version: str
    p1_9_a_foundation_present: bool
    p1_9_b_read_harness_present: bool
    p1_9_c_truth_boundary_present: bool
    no_fake_live: bool
    no_fake_trace_verified: bool
    no_fake_seal: bool
    unavailable_reasons_present: bool
    p1_9_d_tasks_identified: bool
    checklist_hash: str


@dataclass(frozen=True)
class OutputPassportReadinessAuditResult(_CanonicalMixin):
    """P1.9.26 audit result — not exit seal."""

    schema_version: str
    checkpoint_id: str
    audit_status: OutputPassportReadinessAuditStatus
    checklist: OutputPassportReadinessChecklist
    gaps: tuple[str, ...]
    next_pack: str
    next_pack_tasks: tuple[str, ...]
    truth_label: OutputPassportTruthLabel
    source_label: OutputPassportSourceLabel
    side_effects: OutputPassportSideEffectProof
    readiness_audit_result_hash: str


@dataclass(frozen=True)
class OutputPassportReadinessAudit(_CanonicalMixin):
    """P1.9.26 readiness audit envelope."""

    schema_version: str
    checkpoint_id: str
    audit_result: OutputPassportReadinessAuditResult
    invariants: tuple[str, ...]
    truth_label: OutputPassportTruthLabel
    source_label: OutputPassportSourceLabel
    side_effects: OutputPassportSideEffectProof
    readiness_audit_hash: str


@dataclass(frozen=True)
class P19CTruthBoundaryFailureReadinessPackResult(_CanonicalMixin):
    """P1.9-C pack result envelope."""

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
    trace_truth_boundary_summary: str
    fixture_simulation_disclosure_summary: str
    heretic_quarantine_disclosure_summary: str
    lora_adapter_influence_summary: str
    surface_read_model_summary: str
    operator_testable_path_summary: str
    revision_replay_failure_summary: str
    readiness_audit_summary: str
    next_pack: str
    source_label: OutputPassportSourceLabel
    result_hash: str


READINESS_AUDIT_INVARIANTS: tuple[str, ...] = (
    "readiness_audit_only_not_seal",
    "audit_does_not_claim_exit_sealed",
    "conditional_ready_for_integration_tail",
)

P1_9_D_REMAINING_TASKS: tuple[str, ...] = (
    "P1.9.27 Output Passport Projection/API/Event Contract",
    "P1.9.28 Output Passport Shell/CLI/TUI Binding",
    "P1.9.29 Output Passport Docs/State/Reports Update",
    "P1.9.30 P1.9 Exit Seal + Live Integration Demo",
)

P1_9_C_UNAVAILABLE_REASON_DETAILS: dict[str, str] = {
    OutputPassportUnavailableReason.CLI_SHELL_TUI_UNAVAILABLE.value: (
        "CLI/Shell/TUI binding scheduled for P1.9.28; not available in P1.9-C"
    ),
    OutputPassportUnavailableReason.PROJECTION_UNAVAILABLE.value: (
        "Projection/API/event contract scheduled for P1.9.27; not P1.9-C"
    ),
    OutputPassportUnavailableReason.TRACE_VERIFICATION_UNAVAILABLE.value: (
        "Trace verification is not available in P1.9-C; payload/reference only"
    ),
    OutputPassportUnavailableReason.RUNTIME_GENERATION_UNAVAILABLE.value: (
        "Live runtime passport generation is not available in P1.9-C"
    ),
}


def _build_test_path_step(
    step_id: OutputPassportTestPathStepId,
    *,
    step_label: str,
    passed: bool,
    notes: str,
    source_label: OutputPassportSourceLabel,
) -> OutputPassportTestPathStep:
    step_payload = {
        "schema_version": OUTPUT_PASSPORT_TEST_PATH_STEP_VERSION,
        "step_id": step_id,
        "step_label": step_label,
        "passed": passed,
        "truth_label": OutputPassportTruthLabel.TEST_PATH_ONLY,
        "source_label": source_label,
        "notes": notes,
    }
    return OutputPassportTestPathStep(
        **step_payload,
        step_hash=_hash_payload(step_payload),
    )


def _detect_forbidden_labels(
    truth_labels: Sequence[OutputPassportTruthLabel],
) -> tuple[bool, bool, bool]:
    fake_live = OutputPassportTruthLabel.LIVE in truth_labels
    fake_trace = OutputPassportTruthLabel.TRACE_VERIFIED in truth_labels
    fake_seal = (
        OutputPassportTruthLabel.SEALED in truth_labels
        or OutputPassportTruthLabel.EXIT_SEALED in truth_labels
    )
    return fake_live, fake_trace, fake_seal


def build_output_passport_operator_testable_path(
    *,
    checkpoint_id: str = "P1.9.22",
    source_label: OutputPassportSourceLabel | str = OutputPassportSourceLabel.DEV_FIXTURE,
    truth_labels_to_check: Sequence[OutputPassportTruthLabel] | None = None,
) -> OutputPassportOperatorTestPath:
    if isinstance(source_label, str):
        source_label = OutputPassportSourceLabel(source_label)

    side_effects = _all_false_side_effects()
    payload = build_dev_fixture_output_passport_payload()
    read_model = build_output_passport_read_model(payload=payload)
    trace_payload, trace_boundary = build_trace_payload_vs_verification_boundary()
    failure, unavailable = build_output_passport_failure_unavailable_handling()
    audit = build_output_passport_readiness_audit()

    labels = list(truth_labels_to_check or ())
    labels.extend([
        payload.truth_label,
        read_model.truth_label,
        trace_boundary.truth_label,
        audit.truth_label,
    ])
    fake_live, fake_trace, fake_seal = _detect_forbidden_labels(labels)

    steps = (
        _build_test_path_step(
            OutputPassportTestPathStepId.FIXTURE_INPUT,
            step_label="Load dev fixture passport payload",
            passed=payload.source_label is OutputPassportSourceLabel.DEV_FIXTURE,
            notes="fixture_input=dev-passport-001",
            source_label=source_label,
        ),
        _build_test_path_step(
            OutputPassportTestPathStepId.READ_MODEL_CREATION,
            step_label="Build read model from fixture",
            passed=read_model.truth_label is OutputPassportTruthLabel.READ_MODEL_ONLY,
            notes="read_model_only_not_proof",
            source_label=source_label,
        ),
        _build_test_path_step(
            OutputPassportTestPathStepId.TRUTH_BOUNDARY_VALIDATION,
            step_label="Validate trace payload vs verification boundary",
            passed=(
                trace_payload.trace_payload_present
                and not trace_boundary.trace_verified
            ),
            notes=f"trace_payload_status={trace_payload.trace_payload_status.value}",
            source_label=source_label,
        ),
        _build_test_path_step(
            OutputPassportTestPathStepId.FAILURE_UNAVAILABLE_VALIDATION,
            step_label="Validate failure/unavailable handling",
            passed=bool(unavailable.unavailable_reason),
            notes=f"unavailable_reason={unavailable.unavailable_reason}",
            source_label=source_label,
        ),
        _build_test_path_step(
            OutputPassportTestPathStepId.READINESS_AUDIT_EXECUTION,
            step_label="Execute readiness audit",
            passed=audit.audit_result.audit_status
            in (
                OutputPassportReadinessAuditStatus.READY,
                OutputPassportReadinessAuditStatus.CONDITIONAL,
            ),
            notes=f"audit_status={audit.audit_result.audit_status.value}",
            source_label=source_label,
        ),
        _build_test_path_step(
            OutputPassportTestPathStepId.RESULT_SUMMARY,
            step_label="Summarize test path result",
            passed=not fake_live and not fake_trace and not fake_seal,
            notes="no_fake_live_trace_seal",
            source_label=source_label,
        ),
    )
    all_passed = all(step.passed for step in steps)
    result_payload = {
        "schema_version": OUTPUT_PASSPORT_TEST_PATH_RESULT_VERSION,
        "all_steps_passed": all_passed,
        "fake_live_detected": fake_live,
        "fake_trace_verified_detected": fake_trace,
        "fake_seal_detected": fake_seal,
        "steps": steps,
        "truth_label": OutputPassportTruthLabel.TEST_PATH_ONLY,
        "source_label": source_label,
        "side_effects": side_effects,
    }
    result = OutputPassportTestPathResult(
        **result_payload,
        test_path_result_hash=_hash_payload(result_payload),
    )

    path_payload = {
        "schema_version": OUTPUT_PASSPORT_OPERATOR_TEST_PATH_VERSION,
        "checkpoint_id": checkpoint_id,
        "path_label": "p1_9_c_dev_fixture_truth_boundary_path",
        "steps": steps,
        "result": result,
        "truth_label": OutputPassportTruthLabel.TEST_PATH_ONLY,
        "source_label": source_label,
        "side_effects": side_effects,
    }
    return OutputPassportOperatorTestPath(
        **path_payload,
        operator_test_path_hash=_hash_payload(path_payload),
    )


def build_output_passport_readiness_checklist(
    *,
    truth_labels: Sequence[OutputPassportTruthLabel] | None = None,
    unavailable_reasons_present: bool = True,
) -> OutputPassportReadinessChecklist:
    labels = list(truth_labels or ())
    fake_live, fake_trace, fake_seal = _detect_forbidden_labels(labels)
    checklist_payload = {
        "schema_version": OUTPUT_PASSPORT_READINESS_CHECKLIST_VERSION,
        "p1_9_a_foundation_present": True,
        "p1_9_b_read_harness_present": True,
        "p1_9_c_truth_boundary_present": True,
        "no_fake_live": not fake_live,
        "no_fake_trace_verified": not fake_trace,
        "no_fake_seal": not fake_seal,
        "unavailable_reasons_present": unavailable_reasons_present,
        "p1_9_d_tasks_identified": True,
    }
    return OutputPassportReadinessChecklist(
        **checklist_payload,
        checklist_hash=_hash_payload(checklist_payload),
    )


def run_output_passport_readiness_audit(
    *,
    truth_labels: Sequence[OutputPassportTruthLabel] | None = None,
    unavailable_reasons_present: bool = True,
) -> OutputPassportReadinessAuditResult:
    checklist = build_output_passport_readiness_checklist(
        truth_labels=truth_labels,
        unavailable_reasons_present=unavailable_reasons_present,
    )
    all_ok = all([
        checklist.p1_9_a_foundation_present,
        checklist.p1_9_b_read_harness_present,
        checklist.p1_9_c_truth_boundary_present,
        checklist.no_fake_live,
        checklist.no_fake_trace_verified,
        checklist.no_fake_seal,
        checklist.unavailable_reasons_present,
        checklist.p1_9_d_tasks_identified,
    ])
    gaps: tuple[str, ...] = ()
    if not all_ok:
        gap_list: list[str] = []
        if not checklist.no_fake_live:
            gap_list.append("fake_live_label_detected")
        if not checklist.no_fake_trace_verified:
            gap_list.append("fake_trace_verified_label_detected")
        if not checklist.no_fake_seal:
            gap_list.append("fake_seal_label_detected")
        if not checklist.unavailable_reasons_present:
            gap_list.append("missing_unavailable_reasons")
        gaps = tuple(gap_list)

    if gaps:
        audit_status = OutputPassportReadinessAuditStatus.BLOCKED
    elif all_ok:
        audit_status = OutputPassportReadinessAuditStatus.CONDITIONAL
    else:
        audit_status = OutputPassportReadinessAuditStatus.NOT_READY

    side_effects = _all_false_side_effects()
    result_payload = {
        "schema_version": OUTPUT_PASSPORT_READINESS_AUDIT_RESULT_VERSION,
        "checkpoint_id": "P1.9.26",
        "audit_status": audit_status,
        "checklist": checklist,
        "gaps": gaps,
        "next_pack": OUTPUT_PASSPORT_P1_9_C_NEXT_PACK_ID,
        "next_pack_tasks": P1_9_D_REMAINING_TASKS,
        "truth_label": OutputPassportTruthLabel.READINESS_AUDIT_ONLY,
        "source_label": OutputPassportSourceLabel.DEV_FIXTURE,
        "side_effects": side_effects,
    }
    return OutputPassportReadinessAuditResult(
        **result_payload,
        readiness_audit_result_hash=_hash_payload(result_payload),
    )


def build_output_passport_readiness_audit(
    *,
    checkpoint_id: str = "P1.9.26",
    truth_labels: Sequence[OutputPassportTruthLabel] | None = None,
    source_label: OutputPassportSourceLabel | str = OutputPassportSourceLabel.DEV_FIXTURE,
) -> OutputPassportReadinessAudit:
    if isinstance(source_label, str):
        source_label = OutputPassportSourceLabel(source_label)

    audit_result = run_output_passport_readiness_audit(truth_labels=truth_labels)
    side_effects = _all_false_side_effects()
    audit_payload = {
        "schema_version": OUTPUT_PASSPORT_READINESS_AUDIT_VERSION,
        "checkpoint_id": checkpoint_id,
        "audit_result": audit_result,
        "invariants": READINESS_AUDIT_INVARIANTS,
        "truth_label": OutputPassportTruthLabel.READINESS_AUDIT_ONLY,
        "source_label": source_label,
        "side_effects": side_effects,
    }
    return OutputPassportReadinessAudit(
        **audit_payload,
        readiness_audit_hash=_hash_payload(audit_payload),
    )


def _default_p1_9_c_checkpoint_reads() -> tuple[OutputPassportCheckpointRead, ...]:
    definitions = (
        ("P1.9.17", "Trace Payload vs Trace Verification Truth Boundary"),
        ("P1.9.18", "MOCK / DEV_FIXTURE / SIMULATED Disclosure Contract"),
        ("P1.9.19", "Heretic / Quarantined Output Disclosure"),
        ("P1.9.20", "LoRA / Adapter Influence Disclosure"),
        ("P1.9.21", "Aurel CRO / HQ / CORP / HUB / IDE Surface Passport Read Model"),
        ("P1.9.22", "Output Passport Operator-Testable Path"),
        ("P1.9.23", "Output Passport Rejection / Revision History"),
        ("P1.9.24", "Output Passport Replay Seed"),
        ("P1.9.25", "Output Passport Failure / UNAVAILABLE Handling"),
        ("P1.9.26", "P1.9 Passport Readiness Audit"),
    )
    truth_map = {
        "P1.9.17": OutputPassportTruthLabel.PAYLOAD_ONLY,
        "P1.9.18": OutputPassportTruthLabel.DEV_FIXTURE,
        "P1.9.19": OutputPassportTruthLabel.DISCLOSURE_ONLY,
        "P1.9.20": OutputPassportTruthLabel.DISCLOSURE_ONLY,
        "P1.9.21": OutputPassportTruthLabel.READ_MODEL_ONLY,
        "P1.9.22": OutputPassportTruthLabel.TEST_PATH_ONLY,
        "P1.9.23": OutputPassportTruthLabel.REVISION_HISTORY_ONLY,
        "P1.9.24": OutputPassportTruthLabel.REPLAY_SEED_ONLY,
        "P1.9.25": OutputPassportTruthLabel.FAILURE_DISCLOSURE,
        "P1.9.26": OutputPassportTruthLabel.READINESS_AUDIT_ONLY,
    }
    reads: list[OutputPassportCheckpointRead] = []
    for checkpoint_id, canonical_name in definitions:
        reads.append(
            OutputPassportCheckpointRead(
                checkpoint_id=checkpoint_id,
                canonical_name=canonical_name,
                status=OutputPassportCheckpointStatus.DONE,
                truth_label=truth_map[checkpoint_id],
                unavailable_reason=None,
                limitations=("Contract-only; no verification or runtime execution.",),
                evidence_ref=f"{checkpoint_id.lower().replace('.', '_')}_contract",
            )
        )
    return tuple(reads)


def build_p1_9_c_truth_boundary_failure_readiness_pack_result() -> (
    P19CTruthBoundaryFailureReadinessPackResult
):
    from .bindings import build_p1_9_b_read_model_test_harness_binding_pack_result

    payload = build_dev_fixture_output_passport_payload()
    trace_payload, trace_boundary = build_trace_payload_vs_verification_boundary()
    fixture, mock_boundary = build_mock_dev_fixture_simulated_disclosure()
    heretic, quarantine = build_heretic_quarantined_output_disclosure()
    lora, adapter = build_lora_adapter_influence_disclosure()
    surfaces = build_all_surface_passport_read_models()
    test_path = build_output_passport_operator_testable_path()
    revision_history = build_output_passport_revision_history()
    replay_seed = build_output_passport_replay_seed()
    failure, unavailable = build_output_passport_failure_unavailable_handling()
    readiness_audit = build_output_passport_readiness_audit()
    harness_summary = run_output_passport_invariant_harness()
    p1_9_a_result = build_p1_9_a_passport_pack_result()
    p1_9_b_result = build_p1_9_b_read_model_test_harness_binding_pack_result()

    checkpoint_reads = _default_p1_9_c_checkpoint_reads()
    checkpoint_statuses = {
        read.checkpoint_id: read.status.value for read in checkpoint_reads
    }
    side_effects = _all_false_side_effects()
    truth_labels = (
        OutputPassportTruthLabel.CONTRACT_ONLY,
        OutputPassportTruthLabel.DEV_FIXTURE,
        OutputPassportTruthLabel.PAYLOAD_ONLY,
        OutputPassportTruthLabel.REFERENCE_ONLY,
        OutputPassportTruthLabel.DISCLOSURE_ONLY,
        OutputPassportTruthLabel.READ_MODEL_ONLY,
        OutputPassportTruthLabel.TEST_PATH_ONLY,
        OutputPassportTruthLabel.REVISION_HISTORY_ONLY,
        OutputPassportTruthLabel.REPLAY_SEED_ONLY,
        OutputPassportTruthLabel.FAILURE_DISCLOSURE,
        OutputPassportTruthLabel.READINESS_AUDIT_ONLY,
        OutputPassportTruthLabel.NOT_SEAL,
    )
    unavailable_reasons = (
        OutputPassportUnavailableReason.CLI_SHELL_TUI_UNAVAILABLE,
        OutputPassportUnavailableReason.PROJECTION_UNAVAILABLE,
        OutputPassportUnavailableReason.TRACE_VERIFICATION_UNAVAILABLE,
        OutputPassportUnavailableReason.RUNTIME_GENERATION_UNAVAILABLE,
    )
    trace_summary = (
        f"payload_status={trace_payload.trace_payload_status.value}; "
        f"verification={trace_boundary.trace_verification_status.value}; "
        "trace_verified=false"
    )
    fixture_summary = (
        f"reality={fixture.reality_label.value}; "
        f"mock_is_live={mock_boundary.mock_is_live}"
    )
    heretic_summary = (
        f"heretic_trust={heretic.trust_status.value}; "
        f"quarantine={quarantine.quarantine_status.value}"
    )
    lora_summary = (
        f"lora_approval={lora.approval_status.value}; "
        f"adapter_promotion={adapter.promotion_status.value}"
    )
    surface_summary = (
        f"surfaces={len(surfaces)}; "
        f"consumers={[s.consumer_kind.value for s in surfaces]}"
    )
    test_path_summary = (
        f"all_passed={test_path.result.all_steps_passed}; "
        f"steps={len(test_path.steps)}"
    )
    revision_summary = (
        f"entries={len(revision_history.entries)}; "
        f"append_only={revision_history.append_only_contract}; "
        f"replay_executed={replay_seed.determinism_boundary.replay_executed}"
    )
    readiness_summary = (
        f"audit_status={readiness_audit.audit_result.audit_status.value}; "
        f"next_pack={readiness_audit.audit_result.next_pack}; "
        f"harness_passed={harness_summary.all_passed}; "
        f"p1_9_a={p1_9_a_result.pack_id}; p1_9_b={p1_9_b_result.pack_id}"
    )

    result_payload = {
        "schema_version": OUTPUT_PASSPORT_P1_9_C_PACK_RESULT_VERSION,
        "pack_id": OUTPUT_PASSPORT_P1_9_C_PACK_TASK_ID,
        "section_id": OUTPUT_PASSPORT_P1_9_C_SECTION_ID,
        "covered_checkpoints": OUTPUT_PASSPORT_P1_9_C_CHECKPOINT_IDS,
        "checkpoint_reads": checkpoint_reads,
        "checkpoint_statuses": checkpoint_statuses,
        "truth_labels": truth_labels,
        "payload": payload,
        "side_effect_proof": side_effects,
        "unavailable_reasons": unavailable_reasons,
        "unavailable_reason_details": P1_9_C_UNAVAILABLE_REASON_DETAILS,
        "trace_truth_boundary_summary": trace_summary,
        "fixture_simulation_disclosure_summary": fixture_summary,
        "heretic_quarantine_disclosure_summary": heretic_summary,
        "lora_adapter_influence_summary": lora_summary,
        "surface_read_model_summary": surface_summary,
        "operator_testable_path_summary": test_path_summary,
        "revision_replay_failure_summary": revision_summary,
        "readiness_audit_summary": readiness_summary,
        "next_pack": OUTPUT_PASSPORT_P1_9_C_NEXT_PACK_ID,
        "source_label": OutputPassportSourceLabel.DEV_FIXTURE,
    }
    return P19CTruthBoundaryFailureReadinessPackResult(
        **result_payload,
        result_hash=_hash_payload(result_payload),
    )


def serialize_output_passport_truth_readiness_payload(
    result: P19CTruthBoundaryFailureReadinessPackResult,
) -> str:
    return to_canonical_json(result)
