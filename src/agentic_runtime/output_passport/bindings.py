"""Output Passport passive bindings and support disclosure (P1.9-B / P1.9.12-P1.9.16).

Passive reference-only bindings to BusinessEnvironment, Workflow, Agent, and Tool
contexts plus memory-vs-evidence support boundary without execution or authority.

Architectural law:
  - Binding is not authority.
  - BusinessEnvironment binding is not business action.
  - Workflow binding is not workflow execution.
  - Agent binding is not agent authority.
  - Tool binding is not tool execution.
  - Memory-supported is not evidence-supported.
  - Evidence-supported is not verified.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any

from .foundation import (
    OutputPassportCheckpointRead,
    OutputPassportCheckpointStatus,
    OutputPassportPayload,
    OutputPassportSideEffectProof,
    OutputPassportSourceLabel,
    OutputPassportTruthLabel,
    OutputPassportUnavailableReason,
    OutputPassportVerificationStatus,
    build_dev_fixture_output_passport_payload,
    stable_hash,
    to_canonical_json,
)
from .read_model import OutputPassportReadModel, build_output_passport_read_model
from .verification_contract import (
    OutputPassportVerificationContract,
    build_output_passport_verification_contract,
)

if TYPE_CHECKING:
    from .test_harness import OutputPassportHarnessSummary


OUTPUT_PASSPORT_P1_9_B_PACK_TASK_ID = "P1.9-B"
OUTPUT_PASSPORT_P1_9_B_SECTION_ID = "P1.9"
OUTPUT_PASSPORT_P1_9_B_CHECKPOINT_IDS = (
    "P1.9.8",
    "P1.9.9",
    "P1.9.10",
    "P1.9.11",
    "P1.9.12",
    "P1.9.13",
    "P1.9.14",
    "P1.9.15",
    "P1.9.16",
)
OUTPUT_PASSPORT_P1_9_B_NEXT_PACK_ID = "P1.9-C"
OUTPUT_PASSPORT_P1_9_B_PACK_RESULT_VERSION = "output_passport_p1_9_b_pack_result.v1"
OUTPUT_PASSPORT_BINDING_VERSION = "output_passport_binding.v1"
OUTPUT_PASSPORT_SUPPORT_DISCLOSURE_VERSION = "output_passport_support_disclosure.v1"
OUTPUT_PASSPORT_SUPPORT_BOUNDARY_VERSION = "output_passport_support_boundary.v1"


class OutputPassportBindingKind(str, Enum):
    """Passive binding taxonomy."""

    BUSINESS_ENVIRONMENT = "business_environment"
    WORKFLOW = "workflow"
    AGENT = "agent"
    TOOL = "tool"
    UNKNOWN = "unknown"


class OutputPassportBindingStatus(str, Enum):
    """Binding status — reference only by default."""

    REFERENCE_ONLY = "reference_only"
    DECLARED = "declared"
    UNAVAILABLE = "unavailable"
    ERROR = "error"


class OutputPassportBindingUnavailableReason(str, Enum):
    """Why a binding context is unavailable."""

    UNAVAILABLE_BUSINESS_CONTEXT = "unavailable_business_context"
    UNAVAILABLE_WORKFLOW_CONTEXT = "unavailable_workflow_context"
    UNAVAILABLE_AGENT_CONTEXT = "unavailable_agent_context"
    UNAVAILABLE_TOOL_CONTEXT = "unavailable_tool_context"
    UNAVAILABLE = "unavailable"
    ERROR = "error"


class SupportDisclosureStatus(str, Enum):
    """Memory vs evidence support states."""

    MEMORY_SUPPORTED = "memory_supported"
    EVIDENCE_SUPPORTED = "evidence_supported"
    BOTH_MEMORY_AND_EVIDENCE_SUPPORTED = "both_memory_and_evidence_supported"
    UNSUPPORTED = "unsupported"
    UNKNOWN = "unknown"
    UNAVAILABLE = "unavailable"
    REDACTED = "redacted"


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


def _binding_side_effects(
    *,
    business_action_executed: bool = False,
    workflow_executed: bool = False,
    workflow_mutated: bool = False,
    agent_executed: bool = False,
    agent_authority_created: bool = False,
    tool_executed: bool = False,
    tool_permission_granted: bool = False,
) -> OutputPassportSideEffectProof:
    return OutputPassportSideEffectProof(
        business_action_executed=business_action_executed,
        workflow_executed=workflow_executed,
        workflow_mutated=workflow_mutated,
        agent_executed=agent_executed,
        agent_authority_created=agent_authority_created,
        tool_executed=tool_executed,
        tool_permission_granted=tool_permission_granted,
    )


@dataclass(frozen=True)
class BusinessEnvironmentOutputPassportBinding(_CanonicalMixin):
    """P1.9.12 passive BusinessEnvironment binding."""

    schema_version: str
    checkpoint_id: str
    binding_kind: OutputPassportBindingKind
    passport_id: str
    passport_ref: str
    business_environment_ref: str | None
    binding_status: OutputPassportBindingStatus
    binding_truth_label: OutputPassportTruthLabel
    unavailable_reason: OutputPassportBindingUnavailableReason | None
    side_effects: OutputPassportSideEffectProof
    source_label: OutputPassportSourceLabel
    binding_hash: str


@dataclass(frozen=True)
class WorkflowOutputPassportBinding(_CanonicalMixin):
    """P1.9.13 passive Workflow binding."""

    schema_version: str
    checkpoint_id: str
    binding_kind: OutputPassportBindingKind
    passport_id: str
    passport_ref: str
    workflow_ref: str | None
    workflow_step_ref: str | None
    binding_status: OutputPassportBindingStatus
    binding_truth_label: OutputPassportTruthLabel
    unavailable_reason: OutputPassportBindingUnavailableReason | None
    side_effects: OutputPassportSideEffectProof
    source_label: OutputPassportSourceLabel
    binding_hash: str


@dataclass(frozen=True)
class AgentOutputPassportBinding(_CanonicalMixin):
    """P1.9.14 passive Agent binding."""

    schema_version: str
    checkpoint_id: str
    binding_kind: OutputPassportBindingKind
    passport_id: str
    passport_ref: str
    agent_ref: str | None
    agent_role_ref: str | None
    binding_status: OutputPassportBindingStatus
    binding_truth_label: OutputPassportTruthLabel
    unavailable_reason: OutputPassportBindingUnavailableReason | None
    side_effects: OutputPassportSideEffectProof
    source_label: OutputPassportSourceLabel
    binding_hash: str


@dataclass(frozen=True)
class ToolOutputPassportBinding(_CanonicalMixin):
    """P1.9.15 passive Tool binding."""

    schema_version: str
    checkpoint_id: str
    binding_kind: OutputPassportBindingKind
    passport_id: str
    passport_ref: str
    tool_ref: str | None
    tool_manifest_ref: str | None
    tool_call_ref: str | None
    binding_status: OutputPassportBindingStatus
    binding_truth_label: OutputPassportTruthLabel
    unavailable_reason: OutputPassportBindingUnavailableReason | None
    side_effects: OutputPassportSideEffectProof
    source_label: OutputPassportSourceLabel
    binding_hash: str


@dataclass(frozen=True)
class MemorySupportedDisclosure(_CanonicalMixin):
    """Memory support disclosure without memory read."""

    schema_version: str
    support_status: SupportDisclosureStatus
    memory_refs: tuple[str, ...]
    disclosure_note: str
    truth_label: OutputPassportTruthLabel
    source_label: OutputPassportSourceLabel
    memory_supported_hash: str


@dataclass(frozen=True)
class EvidenceSupportedDisclosure(_CanonicalMixin):
    """Evidence support disclosure without verification."""

    schema_version: str
    support_status: SupportDisclosureStatus
    evidence_refs: tuple[str, ...]
    disclosure_note: str
    implies_verified: bool
    implies_trace_verified: bool
    truth_label: OutputPassportTruthLabel
    source_label: OutputPassportSourceLabel
    evidence_supported_hash: str


@dataclass(frozen=True)
class MemoryVsEvidenceSupportBoundary(_CanonicalMixin):
    """P1.9.16 memory vs evidence support boundary."""

    schema_version: str
    checkpoint_id: str
    support_status: SupportDisclosureStatus
    memory_disclosure: MemorySupportedDisclosure
    evidence_disclosure: EvidenceSupportedDisclosure
    memory_only: bool
    evidence_only: bool
    both_supported: bool
    memory_implies_evidence: bool
    evidence_implies_verified: bool
    truth_label: OutputPassportTruthLabel
    source_label: OutputPassportSourceLabel
    side_effects: OutputPassportSideEffectProof
    support_boundary_hash: str


@dataclass(frozen=True)
class P19BReadModelTestHarnessBindingPackResult(_CanonicalMixin):
    """P1.9-B pack result envelope."""

    schema_version: str
    pack_id: str
    section_id: str
    covered_checkpoints: tuple[str, ...]
    checkpoint_reads: tuple[OutputPassportCheckpointRead, ...]
    checkpoint_statuses: Mapping[str, str]
    truth_labels: tuple[OutputPassportTruthLabel, ...]
    payload: OutputPassportPayload
    read_model: OutputPassportReadModel
    verification_contract: OutputPassportVerificationContract
    harness_summary: OutputPassportHarnessSummary
    business_binding: BusinessEnvironmentOutputPassportBinding
    workflow_binding: WorkflowOutputPassportBinding
    agent_binding: AgentOutputPassportBinding
    tool_binding: ToolOutputPassportBinding
    support_boundary: MemoryVsEvidenceSupportBoundary
    side_effect_proof: OutputPassportSideEffectProof
    unavailable_reasons: tuple[OutputPassportUnavailableReason, ...]
    unavailable_reason_details: Mapping[str, str]
    verification_boundary_summary: str
    binding_boundary_summary: str
    support_disclosure_summary: str
    next_pack: str
    source_label: OutputPassportSourceLabel
    result_hash: str


def bind_passport_to_business_environment(
    *,
    passport_id: str = "dev-passport-001",
    passport_ref: str | None = None,
    business_environment_ref: str | None = "dev-business-env-ref-001",
    checkpoint_id: str = "P1.9.12",
    business_action_executed: bool = False,
    source_label: OutputPassportSourceLabel | str = OutputPassportSourceLabel.DEV_FIXTURE,
) -> BusinessEnvironmentOutputPassportBinding:
    if isinstance(source_label, str):
        source_label = OutputPassportSourceLabel(source_label)
    passport_ref_val = passport_ref or f"passport-ref:{passport_id}"
    if business_environment_ref is None:
        binding_status = OutputPassportBindingStatus.UNAVAILABLE
        unavailable = OutputPassportBindingUnavailableReason.UNAVAILABLE_BUSINESS_CONTEXT
    else:
        binding_status = OutputPassportBindingStatus.REFERENCE_ONLY
        unavailable = None
    side_effects = _binding_side_effects(
        business_action_executed=business_action_executed,
    )
    payload = {
        "schema_version": OUTPUT_PASSPORT_BINDING_VERSION,
        "checkpoint_id": checkpoint_id,
        "binding_kind": OutputPassportBindingKind.BUSINESS_ENVIRONMENT,
        "passport_id": passport_id,
        "passport_ref": passport_ref_val,
        "business_environment_ref": business_environment_ref,
        "binding_status": binding_status,
        "binding_truth_label": OutputPassportTruthLabel.REFERENCE_ONLY,
        "unavailable_reason": unavailable,
        "side_effects": side_effects,
        "source_label": source_label,
    }
    return BusinessEnvironmentOutputPassportBinding(
        **payload,
        binding_hash=_hash_payload(payload),
    )


def bind_passport_to_workflow(
    *,
    passport_id: str = "dev-passport-001",
    passport_ref: str | None = None,
    workflow_ref: str | None = "dev-workflow-ref-001",
    workflow_step_ref: str | None = "dev-workflow-step-ref-001",
    checkpoint_id: str = "P1.9.13",
    workflow_executed: bool = False,
    workflow_mutated: bool = False,
    source_label: OutputPassportSourceLabel | str = OutputPassportSourceLabel.DEV_FIXTURE,
) -> WorkflowOutputPassportBinding:
    if isinstance(source_label, str):
        source_label = OutputPassportSourceLabel(source_label)
    passport_ref_val = passport_ref or f"passport-ref:{passport_id}"
    if workflow_ref is None:
        binding_status = OutputPassportBindingStatus.UNAVAILABLE
        unavailable = OutputPassportBindingUnavailableReason.UNAVAILABLE_WORKFLOW_CONTEXT
    else:
        binding_status = OutputPassportBindingStatus.REFERENCE_ONLY
        unavailable = None
    side_effects = _binding_side_effects(
        workflow_executed=workflow_executed,
        workflow_mutated=workflow_mutated,
    )
    payload = {
        "schema_version": OUTPUT_PASSPORT_BINDING_VERSION,
        "checkpoint_id": checkpoint_id,
        "binding_kind": OutputPassportBindingKind.WORKFLOW,
        "passport_id": passport_id,
        "passport_ref": passport_ref_val,
        "workflow_ref": workflow_ref,
        "workflow_step_ref": workflow_step_ref,
        "binding_status": binding_status,
        "binding_truth_label": OutputPassportTruthLabel.REFERENCE_ONLY,
        "unavailable_reason": unavailable,
        "side_effects": side_effects,
        "source_label": source_label,
    }
    return WorkflowOutputPassportBinding(
        **payload,
        binding_hash=_hash_payload(payload),
    )


def bind_passport_to_agent(
    *,
    passport_id: str = "dev-passport-001",
    passport_ref: str | None = None,
    agent_ref: str | None = "dev-agent-ref-001",
    agent_role_ref: str | None = "dev-agent-role-ref-001",
    checkpoint_id: str = "P1.9.14",
    agent_executed: bool = False,
    agent_authority_created: bool = False,
    source_label: OutputPassportSourceLabel | str = OutputPassportSourceLabel.DEV_FIXTURE,
) -> AgentOutputPassportBinding:
    if isinstance(source_label, str):
        source_label = OutputPassportSourceLabel(source_label)
    passport_ref_val = passport_ref or f"passport-ref:{passport_id}"
    if agent_ref is None:
        binding_status = OutputPassportBindingStatus.UNAVAILABLE
        unavailable = OutputPassportBindingUnavailableReason.UNAVAILABLE_AGENT_CONTEXT
    else:
        binding_status = OutputPassportBindingStatus.REFERENCE_ONLY
        unavailable = None
    side_effects = _binding_side_effects(
        agent_executed=agent_executed,
        agent_authority_created=agent_authority_created,
    )
    payload = {
        "schema_version": OUTPUT_PASSPORT_BINDING_VERSION,
        "checkpoint_id": checkpoint_id,
        "binding_kind": OutputPassportBindingKind.AGENT,
        "passport_id": passport_id,
        "passport_ref": passport_ref_val,
        "agent_ref": agent_ref,
        "agent_role_ref": agent_role_ref,
        "binding_status": binding_status,
        "binding_truth_label": OutputPassportTruthLabel.REFERENCE_ONLY,
        "unavailable_reason": unavailable,
        "side_effects": side_effects,
        "source_label": source_label,
    }
    return AgentOutputPassportBinding(
        **payload,
        binding_hash=_hash_payload(payload),
    )


def bind_passport_to_tool(
    *,
    passport_id: str = "dev-passport-001",
    passport_ref: str | None = None,
    tool_ref: str | None = "dev-tool-ref-001",
    tool_manifest_ref: str | None = "dev-tool-manifest-ref-001",
    tool_call_ref: str | None = None,
    checkpoint_id: str = "P1.9.15",
    tool_executed: bool = False,
    tool_permission_granted: bool = False,
    source_label: OutputPassportSourceLabel | str = OutputPassportSourceLabel.DEV_FIXTURE,
) -> ToolOutputPassportBinding:
    if isinstance(source_label, str):
        source_label = OutputPassportSourceLabel(source_label)
    passport_ref_val = passport_ref or f"passport-ref:{passport_id}"
    if tool_ref is None:
        binding_status = OutputPassportBindingStatus.UNAVAILABLE
        unavailable = OutputPassportBindingUnavailableReason.UNAVAILABLE_TOOL_CONTEXT
    else:
        binding_status = OutputPassportBindingStatus.REFERENCE_ONLY
        unavailable = None
    side_effects = _binding_side_effects(
        tool_executed=tool_executed,
        tool_permission_granted=tool_permission_granted,
    )
    payload = {
        "schema_version": OUTPUT_PASSPORT_BINDING_VERSION,
        "checkpoint_id": checkpoint_id,
        "binding_kind": OutputPassportBindingKind.TOOL,
        "passport_id": passport_id,
        "passport_ref": passport_ref_val,
        "tool_ref": tool_ref,
        "tool_manifest_ref": tool_manifest_ref,
        "tool_call_ref": tool_call_ref,
        "binding_status": binding_status,
        "binding_truth_label": OutputPassportTruthLabel.REFERENCE_ONLY,
        "unavailable_reason": unavailable,
        "side_effects": side_effects,
        "source_label": source_label,
    }
    return ToolOutputPassportBinding(
        **payload,
        binding_hash=_hash_payload(payload),
    )


def build_memory_supported_vs_evidence_supported_disclosure(
    *,
    payload: OutputPassportPayload | None = None,
    checkpoint_id: str = "P1.9.16",
    support_status: SupportDisclosureStatus | str = (
        SupportDisclosureStatus.BOTH_MEMORY_AND_EVIDENCE_SUPPORTED
    ),
    source_label: OutputPassportSourceLabel | str = OutputPassportSourceLabel.DEV_FIXTURE,
) -> MemoryVsEvidenceSupportBoundary:
    payload_val = payload or build_dev_fixture_output_passport_payload()
    if isinstance(support_status, str):
        support_status = SupportDisclosureStatus(support_status)
    if isinstance(source_label, str):
        source_label = OutputPassportSourceLabel(source_label)

    memory_refs = tuple(
        ref.memory_influence_ref_id
        for ref in payload_val.memory_influence.influence_refs
    )
    evidence_refs = (
        (payload_val.evidence_trace_binding.evidence_ref.evidence_ref_id,)
        if payload_val.evidence_trace_binding.evidence_ref is not None
        else ()
    )

    memory_only = support_status is SupportDisclosureStatus.MEMORY_SUPPORTED
    evidence_only = support_status is SupportDisclosureStatus.EVIDENCE_SUPPORTED
    both_supported = (
        support_status is SupportDisclosureStatus.BOTH_MEMORY_AND_EVIDENCE_SUPPORTED
    )

    memory_payload = {
        "schema_version": OUTPUT_PASSPORT_SUPPORT_DISCLOSURE_VERSION,
        "support_status": support_status,
        "memory_refs": memory_refs,
        "disclosure_note": "Memory support declared without memory read",
        "truth_label": OutputPassportTruthLabel.DISCLOSURE_ONLY,
        "source_label": source_label,
    }
    memory_disclosure = MemorySupportedDisclosure(
        **memory_payload,
        memory_supported_hash=_hash_payload(memory_payload),
    )

    evidence_payload = {
        "schema_version": OUTPUT_PASSPORT_SUPPORT_DISCLOSURE_VERSION,
        "support_status": support_status,
        "evidence_refs": evidence_refs,
        "disclosure_note": "Evidence support declared without verification",
        "implies_verified": False,
        "implies_trace_verified": False,
        "truth_label": OutputPassportTruthLabel.DISCLOSURE_ONLY,
        "source_label": source_label,
    }
    evidence_disclosure = EvidenceSupportedDisclosure(
        **evidence_payload,
        evidence_supported_hash=_hash_payload(evidence_payload),
    )

    side_effects = _all_false_side_effects()
    boundary_payload = {
        "schema_version": OUTPUT_PASSPORT_SUPPORT_BOUNDARY_VERSION,
        "checkpoint_id": checkpoint_id,
        "support_status": support_status,
        "memory_disclosure": memory_disclosure,
        "evidence_disclosure": evidence_disclosure,
        "memory_only": memory_only,
        "evidence_only": evidence_only,
        "both_supported": both_supported,
        "memory_implies_evidence": False,
        "evidence_implies_verified": False,
        "truth_label": OutputPassportTruthLabel.DISCLOSURE_ONLY,
        "source_label": source_label,
        "side_effects": side_effects,
    }
    return MemoryVsEvidenceSupportBoundary(
        **boundary_payload,
        support_boundary_hash=_hash_payload(boundary_payload),
    )


def _default_p1_9_b_checkpoint_reads() -> tuple[OutputPassportCheckpointRead, ...]:
    definitions = (
        ("P1.9.8", "Output Passport Read Model", OutputPassportTruthLabel.READ_MODEL_ONLY),
        (
            "P1.9.9",
            "Output Passport Verification Contract",
            OutputPassportTruthLabel.VERIFICATION_CONTRACT_ONLY,
        ),
        (
            "P1.9.10",
            "Output Passport Test Harness",
            OutputPassportTruthLabel.TEST_HARNESS_ONLY,
        ),
        (
            "P1.9.11",
            "Operator Review State Field",
            OutputPassportTruthLabel.REVIEW_STATE_ONLY,
        ),
        (
            "P1.9.12",
            "BusinessEnvironment Output Passport Binding",
            OutputPassportTruthLabel.REFERENCE_ONLY,
        ),
        (
            "P1.9.13",
            "Workflow Output Passport Binding",
            OutputPassportTruthLabel.REFERENCE_ONLY,
        ),
        (
            "P1.9.14",
            "Agent Output Passport Binding",
            OutputPassportTruthLabel.REFERENCE_ONLY,
        ),
        (
            "P1.9.15",
            "Tool Output Passport Binding",
            OutputPassportTruthLabel.REFERENCE_ONLY,
        ),
        (
            "P1.9.16",
            "Memory-Supported vs Evidence-Supported Disclosure",
            OutputPassportTruthLabel.DISCLOSURE_ONLY,
        ),
    )
    reads: list[OutputPassportCheckpointRead] = []
    for checkpoint_id, canonical_name, truth_label in definitions:
        reads.append(
            OutputPassportCheckpointRead(
                checkpoint_id=checkpoint_id,
                canonical_name=canonical_name,
                status=OutputPassportCheckpointStatus.DONE,
                truth_label=truth_label,
                unavailable_reason=None,
                limitations=("Contract-only; no execution or verification.",),
                evidence_ref=f"{checkpoint_id.lower().replace('.', '_')}_contract",
            )
        )
    return tuple(reads)


P1_9_B_UNAVAILABLE_REASON_DETAILS: dict[str, str] = {
    OutputPassportUnavailableReason.CLI_SHELL_TUI_UNAVAILABLE.value: (
        "CLI/Shell/TUI binding scheduled for P1.9.28; not available in P1.9-B"
    ),
    OutputPassportUnavailableReason.PROJECTION_UNAVAILABLE.value: (
        "Projection/API/event contract scheduled for P1.9.27; not P1.9-B"
    ),
    OutputPassportUnavailableReason.TRACE_VERIFICATION_UNAVAILABLE.value: (
        "Trace verification is not available in P1.9-B; contract-only boundary"
    ),
}


def build_p1_9_b_read_model_test_harness_binding_pack_result() -> (
    P19BReadModelTestHarnessBindingPackResult
):
    from .test_harness import build_default_harness_case, run_output_passport_invariant_harness

    payload = build_dev_fixture_output_passport_payload()
    passport_id = payload.identity.passport_id
    business_binding = bind_passport_to_business_environment(passport_id=passport_id)
    workflow_binding = bind_passport_to_workflow(passport_id=passport_id)
    agent_binding = bind_passport_to_agent(passport_id=passport_id)
    tool_binding = bind_passport_to_tool(passport_id=passport_id)
    support_boundary = build_memory_supported_vs_evidence_supported_disclosure(
        payload=payload,
    )
    binding_summary = (
        f"business={business_binding.binding_status.value}; "
        f"workflow={workflow_binding.binding_status.value}; "
        f"agent={agent_binding.binding_status.value}; "
        f"tool={tool_binding.binding_status.value}"
    )
    read_model = build_output_passport_read_model(
        payload=payload,
        binding_summary=binding_summary,
    )
    verification_contract = build_output_passport_verification_contract(payload=payload)
    harness_case = build_default_harness_case(
        read_model=read_model,
        verification_contract=verification_contract,
        business_binding=business_binding,
        workflow_binding=workflow_binding,
        agent_binding=agent_binding,
        tool_binding=tool_binding,
        support_boundary=support_boundary,
    )
    harness_summary = run_output_passport_invariant_harness(case=harness_case)
    checkpoint_reads = _default_p1_9_b_checkpoint_reads()
    checkpoint_statuses = {
        read.checkpoint_id: read.status.value for read in checkpoint_reads
    }
    side_effects = _all_false_side_effects()
    truth_labels = (
        OutputPassportTruthLabel.READ_MODEL_ONLY,
        OutputPassportTruthLabel.VERIFICATION_CONTRACT_ONLY,
        OutputPassportTruthLabel.TEST_HARNESS_ONLY,
        OutputPassportTruthLabel.REVIEW_STATE_ONLY,
        OutputPassportTruthLabel.REFERENCE_ONLY,
        OutputPassportTruthLabel.DISCLOSURE_ONLY,
        OutputPassportTruthLabel.DEV_FIXTURE,
        OutputPassportTruthLabel.CONTRACT_ONLY,
    )
    verification_boundary_summary = (
        f"status={verification_contract.verification_status.value}; "
        f"reason={verification_contract.non_verification_reason.value}; "
        "verifier_executed=false"
    )
    binding_boundary_summary = (
        "all bindings REFERENCE_ONLY; no business/workflow/agent/tool execution"
    )
    support_disclosure_summary = (
        f"status={support_boundary.support_status.value}; "
        "memory_implies_evidence=false; evidence_implies_verified=false"
    )
    unavailable_reasons = (
        OutputPassportUnavailableReason.CLI_SHELL_TUI_UNAVAILABLE,
        OutputPassportUnavailableReason.PROJECTION_UNAVAILABLE,
        OutputPassportUnavailableReason.TRACE_VERIFICATION_UNAVAILABLE,
    )
    result_payload = {
        "schema_version": OUTPUT_PASSPORT_P1_9_B_PACK_RESULT_VERSION,
        "pack_id": OUTPUT_PASSPORT_P1_9_B_PACK_TASK_ID,
        "section_id": OUTPUT_PASSPORT_P1_9_B_SECTION_ID,
        "covered_checkpoints": OUTPUT_PASSPORT_P1_9_B_CHECKPOINT_IDS,
        "checkpoint_reads": checkpoint_reads,
        "checkpoint_statuses": checkpoint_statuses,
        "truth_labels": truth_labels,
        "payload": payload,
        "read_model": read_model,
        "verification_contract": verification_contract,
        "harness_summary": harness_summary,
        "business_binding": business_binding,
        "workflow_binding": workflow_binding,
        "agent_binding": agent_binding,
        "tool_binding": tool_binding,
        "support_boundary": support_boundary,
        "side_effect_proof": side_effects,
        "unavailable_reasons": unavailable_reasons,
        "unavailable_reason_details": P1_9_B_UNAVAILABLE_REASON_DETAILS,
        "verification_boundary_summary": verification_boundary_summary,
        "binding_boundary_summary": binding_boundary_summary,
        "support_disclosure_summary": support_disclosure_summary,
        "next_pack": OUTPUT_PASSPORT_P1_9_B_NEXT_PACK_ID,
        "source_label": OutputPassportSourceLabel.DEV_FIXTURE,
    }
    return P19BReadModelTestHarnessBindingPackResult(
        **result_payload,
        result_hash=_hash_payload(result_payload),
    )


def serialize_output_passport_binding_result(
    result: P19BReadModelTestHarnessBindingPackResult,
) -> str:
    return to_canonical_json(result)
