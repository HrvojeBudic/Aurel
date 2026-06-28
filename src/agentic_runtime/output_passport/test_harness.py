"""Output Passport invariant test harness (P1.9-B / P1.9.10).

Focused invariant harness for output passport truth boundaries.
Harness pass is not output truth and is not verification.

Architectural law:
  - Test harness is not proof.
  - Test harness is not verification execution.
  - Harness pass does not claim output truth.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
from typing import Any

from .bindings import (
    AgentOutputPassportBinding,
    BusinessEnvironmentOutputPassportBinding,
    MemoryVsEvidenceSupportBoundary,
    ToolOutputPassportBinding,
    WorkflowOutputPassportBinding,
)
from .foundation import (
    FORBIDDEN_DEFAULT_TRUTH_LABELS,
    OutputPassportSideEffectProof,
    OutputPassportSourceLabel,
    OutputPassportTruthLabel,
    OutputPassportVerificationStatus,
    stable_hash,
    to_canonical_json,
)
from .read_model import OutputPassportReadModel, build_output_passport_read_model
from .verification_contract import (
    OutputPassportVerificationContract,
    build_output_passport_verification_contract,
)

OUTPUT_PASSPORT_TEST_HARNESS_TASK_ID = "P1.9.10"
OUTPUT_PASSPORT_TEST_HARNESS_VERSION = "output_passport_test_harness.v1"
OUTPUT_PASSPORT_HARNESS_CASE_VERSION = "output_passport_harness_case.v1"
OUTPUT_PASSPORT_HARNESS_RESULT_VERSION = "output_passport_harness_result.v1"
OUTPUT_PASSPORT_HARNESS_SUMMARY_VERSION = "output_passport_harness_summary.v1"


class OutputPassportInvariantId(str, Enum):
    """Closed-world invariant identifiers."""

    NO_FAKE_LIVE = "no_fake_live"
    NO_FAKE_TRACE_VERIFIED = "no_fake_trace_verified"
    NO_FAKE_EVIDENCE_FINAL = "no_fake_evidence_final"
    NO_FAKE_LEDGER_VERIFIED = "no_fake_ledger_verified"
    HASH_IS_NOT_TRUTH = "hash_is_not_truth"
    EVIDENCE_REF_NOT_FINALITY = "evidence_ref_not_finality"
    TRACE_REF_NOT_VERIFICATION = "trace_ref_not_verification"
    READ_MODEL_NOT_PROOF = "read_model_not_proof"
    VERIFICATION_CONTRACT_NOT_EXECUTION = "verification_contract_not_execution"
    BINDINGS_PASSIVE = "bindings_passive"
    OPERATOR_REVIEW_NOT_APPROVAL = "operator_review_not_approval"
    MEMORY_NOT_EVIDENCE = "memory_not_evidence"
    EVIDENCE_NOT_VERIFIED = "evidence_not_verified"


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
class OutputPassportInvariant(_CanonicalMixin):
    """Single invariant definition."""

    invariant_id: OutputPassportInvariantId
    description: str
    truth_label: OutputPassportTruthLabel


@dataclass(frozen=True)
class OutputPassportHarnessCase(_CanonicalMixin):
    """Harness case input."""

    schema_version: str
    case_id: str
    read_model: OutputPassportReadModel
    verification_contract: OutputPassportVerificationContract
    business_binding: BusinessEnvironmentOutputPassportBinding | None
    workflow_binding: WorkflowOutputPassportBinding | None
    agent_binding: AgentOutputPassportBinding | None
    tool_binding: ToolOutputPassportBinding | None
    support_boundary: MemoryVsEvidenceSupportBoundary | None
    source_label: OutputPassportSourceLabel
    harness_case_hash: str


@dataclass(frozen=True)
class OutputPassportHarnessResult(_CanonicalMixin):
    """Per-invariant check result."""

    schema_version: str
    case_id: str
    invariant_id: OutputPassportInvariantId
    passed: bool
    reason: str
    source_label: OutputPassportSourceLabel
    harness_result_hash: str


@dataclass(frozen=True)
class OutputPassportHarnessSummary(_CanonicalMixin):
    """Aggregate harness run result."""

    schema_version: str
    case_id: str
    results: tuple[OutputPassportHarnessResult, ...]
    all_passed: bool
    pass_count: int
    fail_count: int
    truth_label: OutputPassportTruthLabel
    source_label: OutputPassportSourceLabel
    side_effects: OutputPassportSideEffectProof
    harness_summary_hash: str


DEFAULT_INVARIANTS: tuple[OutputPassportInvariant, ...] = tuple(
    OutputPassportInvariant(
        invariant_id=invariant_id,
        description=description,
        truth_label=OutputPassportTruthLabel.TEST_HARNESS_ONLY,
    )
    for invariant_id, description in (
        (OutputPassportInvariantId.NO_FAKE_LIVE, "Read model must not claim LIVE"),
        (
            OutputPassportInvariantId.NO_FAKE_TRACE_VERIFIED,
            "Must not claim TRACE_VERIFIED by default",
        ),
        (
            OutputPassportInvariantId.NO_FAKE_EVIDENCE_FINAL,
            "Must not claim EVIDENCE_FINAL by default",
        ),
        (
            OutputPassportInvariantId.NO_FAKE_LEDGER_VERIFIED,
            "Must not claim LEDGER_VERIFIED by default",
        ),
        (
            OutputPassportInvariantId.HASH_IS_NOT_TRUTH,
            "Hash summary must not claim truth",
        ),
        (
            OutputPassportInvariantId.EVIDENCE_REF_NOT_FINALITY,
            "Evidence refs remain reference-only",
        ),
        (
            OutputPassportInvariantId.TRACE_REF_NOT_VERIFICATION,
            "Trace refs remain not verified",
        ),
        (
            OutputPassportInvariantId.READ_MODEL_NOT_PROOF,
            "Read model truth label is not proof",
        ),
        (
            OutputPassportInvariantId.VERIFICATION_CONTRACT_NOT_EXECUTION,
            "Verification boundary must not execute verifier",
        ),
        (
            OutputPassportInvariantId.BINDINGS_PASSIVE,
            "Bindings must not claim execution",
        ),
        (
            OutputPassportInvariantId.OPERATOR_REVIEW_NOT_APPROVAL,
            "Operator review must not grant permission",
        ),
        (
            OutputPassportInvariantId.MEMORY_NOT_EVIDENCE,
            "Memory support must not imply evidence support",
        ),
        (
            OutputPassportInvariantId.EVIDENCE_NOT_VERIFIED,
            "Evidence support must not imply verified",
        ),
    )
)


def build_output_passport_test_harness(
    invariants: Sequence[OutputPassportInvariant] = DEFAULT_INVARIANTS,
) -> tuple[OutputPassportInvariant, ...]:
    return tuple(invariants)


def build_default_harness_case(
    *,
    case_id: str = "dev-fixture-case",
    read_model: OutputPassportReadModel | None = None,
    verification_contract: OutputPassportVerificationContract | None = None,
    business_binding: BusinessEnvironmentOutputPassportBinding | None = None,
    workflow_binding: WorkflowOutputPassportBinding | None = None,
    agent_binding: AgentOutputPassportBinding | None = None,
    tool_binding: ToolOutputPassportBinding | None = None,
    support_boundary: MemoryVsEvidenceSupportBoundary | None = None,
    source_label: OutputPassportSourceLabel | str = OutputPassportSourceLabel.DEV_FIXTURE,
) -> OutputPassportHarnessCase:
    from .bindings import (
        bind_passport_to_agent,
        bind_passport_to_business_environment,
        bind_passport_to_tool,
        bind_passport_to_workflow,
        build_memory_supported_vs_evidence_supported_disclosure,
    )

    read_model_val = read_model or build_output_passport_read_model()
    verification_val = verification_contract or build_output_passport_verification_contract()
    business_val = business_binding or bind_passport_to_business_environment(
        passport_id=read_model_val.passport_id,
    )
    workflow_val = workflow_binding or bind_passport_to_workflow(
        passport_id=read_model_val.passport_id,
    )
    agent_val = agent_binding or bind_passport_to_agent(
        passport_id=read_model_val.passport_id,
    )
    tool_val = tool_binding or bind_passport_to_tool(
        passport_id=read_model_val.passport_id,
    )
    support_val = support_boundary or build_memory_supported_vs_evidence_supported_disclosure()
    if isinstance(source_label, str):
        source_label = OutputPassportSourceLabel(source_label)

    payload = {
        "schema_version": OUTPUT_PASSPORT_HARNESS_CASE_VERSION,
        "case_id": case_id,
        "read_model": read_model_val,
        "verification_contract": verification_val,
        "business_binding": business_val,
        "workflow_binding": workflow_val,
        "agent_binding": agent_val,
        "tool_binding": tool_val,
        "support_boundary": support_val,
        "source_label": source_label,
    }
    return OutputPassportHarnessCase(
        **payload,
        harness_case_hash=_hash_payload(payload),
    )


def build_harness_case_with_truth_label_override(
    *,
    truth_label: OutputPassportTruthLabel,
    case_id: str = "override-case",
) -> OutputPassportHarnessCase:
    """Test-only helper to inject forbidden truth labels for negative harness tests."""
    read_model = build_output_passport_read_model(
        truth_label=truth_label,
    )
    return build_default_harness_case(case_id=case_id, read_model=read_model)


def build_harness_case_with_binding_execution_flags(
    *,
    case_id: str = "binding-execution-case",
) -> OutputPassportHarnessCase:
    """Test-only helper: binding with execution flags set (should fail harness)."""
    from .bindings import bind_passport_to_business_environment

    read_model = build_output_passport_read_model()
    bad_binding = bind_passport_to_business_environment(
        passport_id=read_model.passport_id,
        business_action_executed=True,
    )
    return build_default_harness_case(
        case_id=case_id,
        read_model=read_model,
        business_binding=bad_binding,
    )


def _check_invariant(
    invariant: OutputPassportInvariant,
    case: OutputPassportHarnessCase,
) -> OutputPassportHarnessResult:
    passed = True
    reason = "ok"
    read_model = case.read_model
    verification = case.verification_contract

    if invariant.invariant_id is OutputPassportInvariantId.NO_FAKE_LIVE:
        if read_model.truth_label is OutputPassportTruthLabel.LIVE:
            passed = False
            reason = "read_model truth_label is LIVE"
        for section in read_model.display_sections:
            if section.truth_label is OutputPassportTruthLabel.LIVE:
                passed = False
                reason = f"section {section.section_id} claims LIVE"

    elif invariant.invariant_id is OutputPassportInvariantId.NO_FAKE_TRACE_VERIFIED:
        labels = {read_model.truth_label, *(
            s.truth_label for s in read_model.display_sections
        )}
        if OutputPassportTruthLabel.TRACE_VERIFIED in labels:
            passed = False
            reason = "TRACE_VERIFIED truth label detected"
        if verification.verification_status is OutputPassportVerificationStatus.VERIFIED:
            passed = False
            reason = "verification contract claims VERIFIED without harness proof"

    elif invariant.invariant_id is OutputPassportInvariantId.NO_FAKE_EVIDENCE_FINAL:
        labels = {read_model.truth_label, *(
            s.truth_label for s in read_model.display_sections
        )}
        if OutputPassportTruthLabel.EVIDENCE_FINAL in labels:
            passed = False
            reason = "EVIDENCE_FINAL truth label detected"

    elif invariant.invariant_id is OutputPassportInvariantId.NO_FAKE_LEDGER_VERIFIED:
        if read_model.truth_label is OutputPassportTruthLabel.LEDGER_VERIFIED:
            passed = False
            reason = "LEDGER_VERIFIED truth label detected"

    elif invariant.invariant_id is OutputPassportInvariantId.HASH_IS_NOT_TRUTH:
        if "hash_is_truth=true" in read_model.consumer_summary.hash_summary.lower():
            passed = False
            reason = "hash summary claims truth"

    elif invariant.invariant_id is OutputPassportInvariantId.EVIDENCE_REF_NOT_FINALITY:
        for section in read_model.display_sections:
            if section.section_id == "evidence_trace":
                if section.truth_label in FORBIDDEN_DEFAULT_TRUTH_LABELS:
                    passed = False
                    reason = "evidence_trace section overclaims finality"

    elif invariant.invariant_id is OutputPassportInvariantId.TRACE_REF_NOT_VERIFICATION:
        if read_model.verification_status is OutputPassportVerificationStatus.VERIFIED:
            passed = False
            reason = "read model verification_status is VERIFIED"

    elif invariant.invariant_id is OutputPassportInvariantId.READ_MODEL_NOT_PROOF:
        if read_model.truth_label not in (
            OutputPassportTruthLabel.READ_MODEL_ONLY,
            OutputPassportTruthLabel.CONTRACT_ONLY,
            OutputPassportTruthLabel.DEV_FIXTURE,
        ):
            if read_model.truth_label in FORBIDDEN_DEFAULT_TRUTH_LABELS:
                passed = False
                reason = "read model truth label is forbidden proof label"

    elif invariant.invariant_id is OutputPassportInvariantId.VERIFICATION_CONTRACT_NOT_EXECUTION:
        boundary = verification.boundary
        if boundary.verifier_executed or boundary.trace_verified:
            passed = False
            reason = "verification boundary claims execution"
        if verification.boundary.ledger_written or verification.boundary.global_trace_written:
            passed = False
            reason = "verification boundary claims ledger/trace write"

    elif invariant.invariant_id is OutputPassportInvariantId.BINDINGS_PASSIVE:
        for binding in (
            case.business_binding,
            case.workflow_binding,
            case.agent_binding,
            case.tool_binding,
        ):
            if binding is None:
                continue
            side = binding.side_effects
            if any(getattr(side, f.name) for f in fields(side)):
                passed = False
                reason = f"binding {binding.__class__.__name__} has side effects"

    elif invariant.invariant_id is OutputPassportInvariantId.OPERATOR_REVIEW_NOT_APPROVAL:
        review = read_model.operator_review_state
        if review.grants_permission or review.approves_execution:
            passed = False
            reason = "operator review grants permission or approves execution"

    elif invariant.invariant_id is OutputPassportInvariantId.MEMORY_NOT_EVIDENCE:
        if case.support_boundary is not None:
            if case.support_boundary.memory_implies_evidence:
                passed = False
                reason = "memory support implies evidence support"

    elif invariant.invariant_id is OutputPassportInvariantId.EVIDENCE_NOT_VERIFIED:
        if case.support_boundary is not None:
            if case.support_boundary.evidence_implies_verified:
                passed = False
                reason = "evidence support implies verified"
            if case.support_boundary.evidence_disclosure.implies_trace_verified:
                passed = False
                reason = "evidence support implies TRACE_VERIFIED"

    result_payload = {
        "schema_version": OUTPUT_PASSPORT_HARNESS_RESULT_VERSION,
        "case_id": case.case_id,
        "invariant_id": invariant.invariant_id,
        "passed": passed,
        "reason": reason,
        "source_label": case.source_label,
    }
    return OutputPassportHarnessResult(
        **result_payload,
        harness_result_hash=_hash_payload(result_payload),
    )


def run_output_passport_invariant_harness(
    *,
    case: OutputPassportHarnessCase | None = None,
    invariants: Sequence[OutputPassportInvariant] = DEFAULT_INVARIANTS,
) -> OutputPassportHarnessSummary:
    case_val = case or build_default_harness_case()
    results = tuple(_check_invariant(invariant, case_val) for invariant in invariants)
    pass_count = sum(1 for result in results if result.passed)
    fail_count = len(results) - pass_count
    side_effects = _all_false_side_effects()
    summary_payload = {
        "schema_version": OUTPUT_PASSPORT_HARNESS_SUMMARY_VERSION,
        "case_id": case_val.case_id,
        "results": results,
        "all_passed": fail_count == 0,
        "pass_count": pass_count,
        "fail_count": fail_count,
        "truth_label": OutputPassportTruthLabel.TEST_HARNESS_ONLY,
        "source_label": case_val.source_label,
        "side_effects": side_effects,
    }
    return OutputPassportHarnessSummary(
        **summary_payload,
        harness_summary_hash=_hash_payload(summary_payload),
    )


def serialize_output_passport_harness_summary(
    summary: OutputPassportHarnessSummary,
) -> str:
    return to_canonical_json(summary)
