"""Path Governance Exit Seal + Live Integration Demo (P1.7.20).

Read-only evidence layer proving the P1.7 Integration-First vertical slice.
Does NOT add policy enforcement, write to the Ledger, activate approvals,
mutate runtime, or change sandbox behavior.

Seal pass is evidence, not runtime authority.
"""
from __future__ import annotations

import importlib
from collections.abc import Mapping as MappingABC, Sequence
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping

from .cli_binding import (
    PathGovernanceCliCommandKind,
    PathGovernanceCliOutputFormat,
    handle_path_governance_cli_request,
)
from .conflict_precedence import (
    CONFLICT_PRECEDENCE_TASK_ID,
    resolve_path_source_conflicts_shadow,
)
from .errors import (
    PathGovernanceErrorCode,
    PathGovernanceValidationError,
)
from .foundation import PATH_GOVERNANCE_TASK_ID, get_path_governance_foundation_status
from .labels import ProjectionSourceLabel, SourceTrustLabel
from .path_authority_scope import (
    PATH_AUTHORITY_SCOPE_TASK_ID,
    PathAuthorityBasis,
    PathAuthoritySubject,
    PathAuthoritySubjectKind,
    PathScopeAction,
    build_path_authority_scope,
)
from .path_identity import PATH_IDENTITY_TASK_ID, PathKind, build_path_identity
from .path_normalization import PATH_NORMALIZATION_TASK_ID
from .path_resolution_trace import (
    PATH_RESOLUTION_TRACE_TASK_ID,
    build_path_resolution_trace_payload,
)
from .path_resolver import (
    PATH_GOVERNANCE_RESOLVER_TASK_ID,
    PathGovernanceDecisionReason,
    PathGovernanceResolverResult,
    PathGovernanceShadowDecision,
)
from .path_violation_trace import (
    PATH_VIOLATION_TRACE_TASK_ID,
    build_path_violation_trace_payload,
)
from .policy_context_bridge import (
    PATH_POLICY_CONTEXT_BRIDGE_TASK_ID,
    bridge_path_governance_to_policy_context,
)
from .projection_contract import (
    PATH_GOVERNANCE_PROJECTION_TASK_ID,
    build_default_path_governance_capability_projection,
)
from .risk_classification import (
    PATH_SOURCE_RISK_TASK_ID,
    PathSourceRiskLevel,
    PathSourceRiskSignalKind,
    RiskClassificationBasis,
    build_path_source_risk_classification,
    build_path_source_risk_signal,
)
from .serialization import stable_hash
from .source_identity import SOURCE_IDENTITY_TASK_ID, SourceKind, SourceOrigin, build_source_identity
from .source_provenance import (
    SOURCE_PROVENANCE_TASK_ID,
    EvidenceBindingKind,
    EvidenceConfidence,
    SourceClaimKind,
    build_provenance_binding,
    build_source_claim_ref,
    build_source_evidence_ref,
)
from .source_trust_resolver import (
    SOURCE_TRUST_RESOLVER_TASK_ID,
    SourceTrustDecisionReason,
    SourceTrustResolverResult,
    SourceTrustShadowDecision,
)
from .source_trust_taxonomy import SOURCE_TRUST_TAXONOMY_TASK_ID
from .test_harness import (
    PATH_GOVERNANCE_TEST_HARNESS_TASK_ID,
    run_path_governance_harness_suite,
)
from .trusted_roots import TRUSTED_ROOT_REGISTRY_TASK_ID
from .untrusted_content_boundary import (
    UNTRUSTED_CONTENT_BOUNDARY_TASK_ID,
    ContentInfluenceSurface,
    UntrustedBoundaryPosture,
    UntrustedContentKind,
    build_untrusted_content_boundary,
)
from .validation import validate_known_fields

PATH_GOVERNANCE_EXIT_SEAL_TASK_ID = "P1.7.20"
PATH_GOVERNANCE_EXIT_SEAL_SCHEMA = "path_governance_exit_seal.v1"
PATH_GOVERNANCE_EXIT_SEAL_DOCS_TASK_ID = "P1.7.19"

_DEMO_FIXTURE_META: MappingProxyType[str, Any] = MappingProxyType({"fixture": "DEV_FIXTURE"})

P17_REPORT_INVENTORY: tuple[str, ...] = (
    "P1.7.0_PATH_GOVERNANCE_SOURCE_TRUST_FOUNDATION.md",
    "P1.7.1_PATH_IDENTITY_CANONICAL_PATH_SCHEMA.md",
    "P1.7.2_SOURCE_IDENTITY_SOURCE_REF_SCHEMA.md",
    "P1.7.3_SOURCE_TRUST_LABEL_TAXONOMY.md",
    "P1.7.4_TRUSTED_ROOT_SCOPE_REGISTRY_SEED.md",
    "P1.7.5_PATH_NORMALIZATION_ESCAPE_DETECTION_CONTRACT.md",
    "P1.7.6_PATH_AUTHORITY_SCOPE_MODEL.md",
    "P1.7.7_UNTRUSTED_CONTENT_BOUNDARY_MODEL.md",
    "P1.7.8_SOURCE_PROVENANCE_EVIDENCE_BINDING_SEED.md",
    "P1.7.9_PATH_SOURCE_RISK_CLASSIFICATION_MODEL.md",
    "P1.7.10_PATH_GOVERNANCE_RESOLVER_SHADOW_MODE.md",
    "P1.7.11_SOURCE_TRUST_RESOLVER_SHADOW_MODE.md",
    "P1.7.12_PATH_SOURCE_CONFLICT_PRECEDENCE_RULES.md",
    "P1.7.13_PATH_RESOLUTION_TRACE_HOOK.md",
    "P1.7.14_PATH_VIOLATION_DRIFT_TRACE_HOOK.md",
    "P1.7.15_PATH_GOVERNANCE_TEST_HARNESS.md",
    "P1.7.16_POLICY_CONTEXT_BRIDGE.md",
    "P1.7.17_PATH_GOVERNANCE_PROJECTION_API_EVENT_CONTRACT.md",
    "P1.7.18_PATH_GOVERNANCE_CLI_TUI_BINDING.md",
    "P1.7.19_DOCS_STATE_REPORTS_UPDATE.md",
)

P17_UNAVAILABLE_INTEGRATIONS: MappingProxyType[str, str] = MappingProxyType({
    "shell_ui": "UNAVAILABLE: Shell UI not implemented in P1.7",
    "http_api_server": "UNAVAILABLE: HTTP API server not implemented in P1.7",
    "policy_runtime": (
        "UNAVAILABLE: policy runtime/Custos enforcement not implemented in P1.7"
    ),
    "ledger_write": "UNAVAILABLE: Ledger write not implemented in P1.7",
    "global_trace_spine": (
        "UNAVAILABLE: global trace spine write not implemented in P1.7"
    ),
    "runtime_enforcement": (
        "UNAVAILABLE: runtime enforcement not implemented in P1.7"
    ),
    "source_trust_mutation": (
        "UNAVAILABLE: source trust mutation not implemented in P1.7"
    ),
    "approval_activation": (
        "UNAVAILABLE: approval activation not implemented in P1.7"
    ),
    "allow_deny_block": (
        "UNAVAILABLE: real allow/deny/block decisions not implemented in P1.7"
    ),
})

PATH_GOVERNANCE_EXIT_SEAL_SIDE_EFFECTS_KNOWN_FIELDS: frozenset[str] = frozenset({
    "policy_called",
    "approval_created",
    "ledger_written",
    "global_trace_written",
    "runtime_mutated",
    "enforcement_triggered",
    "source_mutated",
    "prompt_filtered",
    "memory_written",
    "tool_blocked",
    "side_effects_hash",
    "metadata",
})

PATH_GOVERNANCE_EXIT_SEAL_CHECK_RESULT_KNOWN_FIELDS: frozenset[str] = frozenset({
    "check_id",
    "check_kind",
    "status",
    "summary",
    "evidence_refs",
    "source_label",
    "unavailable_reason",
    "check_hash",
    "metadata",
})

PATH_GOVERNANCE_EXIT_SEAL_DEMO_INPUT_KNOWN_FIELDS: frozenset[str] = frozenset({
    "demo_id",
    "source_label",
    "include_harness_demo",
    "include_policy_context_demo",
    "include_projection_demo",
    "include_cli_demo",
    "include_trace_demo",
    "include_violation_demo",
    "include_unavailable_proof",
    "demo_hash",
    "metadata",
})

PATH_GOVERNANCE_EXIT_SEAL_RESULT_KNOWN_FIELDS: frozenset[str] = frozenset({
    "seal_id",
    "checks",
    "passed",
    "failed_count",
    "skipped_count",
    "unavailable_count",
    "error_count",
    "demo_summary",
    "side_effects",
    "source_label",
    "schema_version",
    "created_by_task",
    "seal_hash",
    "metadata",
})


class PathGovernanceExitSealCheckKind(str, Enum):
    """Exit seal check classification."""

    PACKAGE_IMPORTS = "PACKAGE_IMPORTS"
    REPORT_INVENTORY = "REPORT_INVENTORY"
    FOUNDATION_CAPABILITY = "FOUNDATION_CAPABILITY"
    PATH_IDENTITY_CAPABILITY = "PATH_IDENTITY_CAPABILITY"
    SOURCE_IDENTITY_CAPABILITY = "SOURCE_IDENTITY_CAPABILITY"
    SOURCE_TRUST_TAXONOMY_CAPABILITY = "SOURCE_TRUST_TAXONOMY_CAPABILITY"
    TRUSTED_ROOT_CAPABILITY = "TRUSTED_ROOT_CAPABILITY"
    PATH_NORMALIZATION_CAPABILITY = "PATH_NORMALIZATION_CAPABILITY"
    AUTHORITY_SCOPE_CAPABILITY = "AUTHORITY_SCOPE_CAPABILITY"
    UNTRUSTED_BOUNDARY_CAPABILITY = "UNTRUSTED_BOUNDARY_CAPABILITY"
    PROVENANCE_BINDING_CAPABILITY = "PROVENANCE_BINDING_CAPABILITY"
    RISK_CLASSIFICATION_CAPABILITY = "RISK_CLASSIFICATION_CAPABILITY"
    PATH_RESOLVER_SHADOW = "PATH_RESOLVER_SHADOW"
    SOURCE_TRUST_RESOLVER_SHADOW = "SOURCE_TRUST_RESOLVER_SHADOW"
    CONFLICT_PRECEDENCE_SHADOW = "CONFLICT_PRECEDENCE_SHADOW"
    PATH_RESOLUTION_TRACE_HOOK = "PATH_RESOLUTION_TRACE_HOOK"
    VIOLATION_DRIFT_TRACE_HOOK = "VIOLATION_DRIFT_TRACE_HOOK"
    TEST_HARNESS_DEMO = "TEST_HARNESS_DEMO"
    POLICY_CONTEXT_BRIDGE_DEMO = "POLICY_CONTEXT_BRIDGE_DEMO"
    PROJECTION_CONTRACT_DEMO = "PROJECTION_CONTRACT_DEMO"
    CLI_TUI_BINDING_DEMO = "CLI_TUI_BINDING_DEMO"
    UNAVAILABLE_STATES_PROOF = "UNAVAILABLE_STATES_PROOF"
    NO_ENFORCEMENT_PROOF = "NO_ENFORCEMENT_PROOF"
    DOCS_STATE_REPORTS_PROOF = "DOCS_STATE_REPORTS_PROOF"
    EXIT_SEAL_RESULT = "EXIT_SEAL_RESULT"
    UNKNOWN = "UNKNOWN"


class PathGovernanceExitSealStatus(str, Enum):
    """Exit seal check status; PASS is not runtime authority."""

    PASS = "PASS"
    FAIL = "FAIL"
    SKIPPED = "SKIPPED"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"
    UNKNOWN = "UNKNOWN"


def _freeze_metadata(metadata: Mapping[str, Any] | None) -> MappingProxyType[str, Any]:
    if not metadata:
        return MappingProxyType({})
    return MappingProxyType(dict(sorted(metadata.items(), key=lambda item: item[0])))


def _sorted_metadata_dict(metadata: Mapping[str, Any]) -> dict[str, Any]:
    return dict(sorted(dict(metadata).items(), key=lambda item: item[0]))


def _parse_source_label(value: ProjectionSourceLabel | str) -> ProjectionSourceLabel:
    if isinstance(value, ProjectionSourceLabel):
        return value
    return ProjectionSourceLabel(str(value))


def _parse_check_kind(value: PathGovernanceExitSealCheckKind | str) -> PathGovernanceExitSealCheckKind:
    if isinstance(value, PathGovernanceExitSealCheckKind):
        return value
    return PathGovernanceExitSealCheckKind(str(value))


def _parse_status(value: PathGovernanceExitSealStatus | str) -> PathGovernanceExitSealStatus:
    if isinstance(value, PathGovernanceExitSealStatus):
        return value
    return PathGovernanceExitSealStatus(str(value))


def compute_exit_seal_demo_id(
    *,
    source_label: ProjectionSourceLabel,
    include_harness_demo: bool,
    include_policy_context_demo: bool,
    include_projection_demo: bool,
    include_cli_demo: bool,
    include_trace_demo: bool,
    include_violation_demo: bool,
    include_unavailable_proof: bool,
    metadata: Mapping[str, Any],
) -> str:
    return stable_hash({
        "include_cli_demo": include_cli_demo,
        "include_harness_demo": include_harness_demo,
        "include_policy_context_demo": include_policy_context_demo,
        "include_projection_demo": include_projection_demo,
        "include_trace_demo": include_trace_demo,
        "include_unavailable_proof": include_unavailable_proof,
        "include_violation_demo": include_violation_demo,
        "metadata": _sorted_metadata_dict(metadata),
        "source_label": source_label.value,
    })


def compute_exit_seal_check_id(
    *,
    check_kind: PathGovernanceExitSealCheckKind,
    status: PathGovernanceExitSealStatus,
    evidence_refs: Sequence[str],
    unavailable_reason: str,
    source_label: ProjectionSourceLabel,
    metadata: Mapping[str, Any],
) -> str:
    return stable_hash({
        "check_kind": check_kind.value,
        "evidence_refs": list(evidence_refs),
        "metadata": _sorted_metadata_dict(metadata),
        "source_label": source_label.value,
        "status": status.value,
        "unavailable_reason": unavailable_reason,
    })


def compute_exit_seal_seal_id(
    *,
    check_ids: Sequence[str],
    schema_version: str,
    created_by_task: str,
) -> str:
    return stable_hash({
        "check_ids": sorted(check_ids),
        "created_by_task": created_by_task,
        "schema_version": schema_version,
    })


@dataclass(frozen=True)
class PathGovernanceExitSealSideEffects:
    """Side-effect truth booleans; all remain false in P1.7.20."""

    policy_called: bool = False
    approval_created: bool = False
    ledger_written: bool = False
    global_trace_written: bool = False
    runtime_mutated: bool = False
    enforcement_triggered: bool = False
    source_mutated: bool = False
    prompt_filtered: bool = False
    memory_written: bool = False
    tool_blocked: bool = False
    side_effects_hash: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for field_name, value in (
            ("policy_called", self.policy_called),
            ("approval_created", self.approval_created),
            ("ledger_written", self.ledger_written),
            ("global_trace_written", self.global_trace_written),
            ("runtime_mutated", self.runtime_mutated),
            ("enforcement_triggered", self.enforcement_triggered),
            ("source_mutated", self.source_mutated),
            ("prompt_filtered", self.prompt_filtered),
            ("memory_written", self.memory_written),
            ("tool_blocked", self.tool_blocked),
        ):
            if value is not False:
                raise PathGovernanceValidationError(
                    f"{field_name} must be false in P1.7.20",
                    code=PathGovernanceErrorCode.ENFORCEMENT_NOT_AVAILABLE,
                    field=field_name,
                )

    def to_canonical_dict(self, *, include_hash: bool = True) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "approval_created": self.approval_created,
            "enforcement_triggered": self.enforcement_triggered,
            "global_trace_written": self.global_trace_written,
            "ledger_written": self.ledger_written,
            "memory_written": self.memory_written,
            "metadata": _sorted_metadata_dict(self.metadata),
            "policy_called": self.policy_called,
            "prompt_filtered": self.prompt_filtered,
            "runtime_mutated": self.runtime_mutated,
            "source_mutated": self.source_mutated,
            "tool_blocked": self.tool_blocked,
        }
        if include_hash:
            payload["side_effects_hash"] = self.side_effects_hash
        return dict(sorted(payload.items(), key=lambda item: item[0]))

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> PathGovernanceExitSealSideEffects:
        validate_known_fields(
            data,
            PATH_GOVERNANCE_EXIT_SEAL_SIDE_EFFECTS_KNOWN_FIELDS,
            label="PathGovernanceExitSealSideEffects",
        )
        partial = cls(
            policy_called=bool(data.get("policy_called", False)),
            approval_created=bool(data.get("approval_created", False)),
            ledger_written=bool(data.get("ledger_written", False)),
            global_trace_written=bool(data.get("global_trace_written", False)),
            runtime_mutated=bool(data.get("runtime_mutated", False)),
            enforcement_triggered=bool(data.get("enforcement_triggered", False)),
            source_mutated=bool(data.get("source_mutated", False)),
            prompt_filtered=bool(data.get("prompt_filtered", False)),
            memory_written=bool(data.get("memory_written", False)),
            tool_blocked=bool(data.get("tool_blocked", False)),
            metadata=_freeze_metadata(data.get("metadata")),
        )
        side_effects_hash = stable_hash(partial.to_canonical_dict(include_hash=False))
        return cls(
            policy_called=partial.policy_called,
            approval_created=partial.approval_created,
            ledger_written=partial.ledger_written,
            global_trace_written=partial.global_trace_written,
            runtime_mutated=partial.runtime_mutated,
            enforcement_triggered=partial.enforcement_triggered,
            source_mutated=partial.source_mutated,
            prompt_filtered=partial.prompt_filtered,
            memory_written=partial.memory_written,
            tool_blocked=partial.tool_blocked,
            side_effects_hash=side_effects_hash,
            metadata=partial.metadata,
        )


def build_path_governance_exit_seal_side_effects(
    *,
    metadata: Mapping[str, Any] | None = None,
) -> PathGovernanceExitSealSideEffects:
    """Build side-effect truth record with all flags false."""
    frozen_metadata = _freeze_metadata(metadata)
    partial = PathGovernanceExitSealSideEffects(metadata=frozen_metadata)
    side_effects_hash = stable_hash(partial.to_canonical_dict(include_hash=False))
    return PathGovernanceExitSealSideEffects(
        side_effects_hash=side_effects_hash,
        metadata=frozen_metadata,
    )


@dataclass(frozen=True)
class PathGovernanceExitSealCheckResult:
    """Single exit seal check evidence; not policy decision."""

    check_id: str
    check_kind: PathGovernanceExitSealCheckKind
    status: PathGovernanceExitSealStatus
    summary: str
    evidence_refs: tuple[str, ...] = ()
    source_label: ProjectionSourceLabel = ProjectionSourceLabel.DEV_FIXTURE
    unavailable_reason: str = ""
    check_hash: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def to_canonical_dict(self, *, include_hash: bool = True) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "check_id": self.check_id,
            "check_kind": self.check_kind.value,
            "evidence_refs": list(self.evidence_refs),
            "metadata": _sorted_metadata_dict(self.metadata),
            "source_label": self.source_label.value,
            "status": self.status.value,
            "summary": self.summary,
            "unavailable_reason": self.unavailable_reason,
        }
        if include_hash:
            payload["check_hash"] = self.check_hash
        return dict(sorted(payload.items(), key=lambda item: item[0]))

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> PathGovernanceExitSealCheckResult:
        validate_known_fields(
            data,
            PATH_GOVERNANCE_EXIT_SEAL_CHECK_RESULT_KNOWN_FIELDS,
            label="PathGovernanceExitSealCheckResult",
        )
        parsed_kind = _parse_check_kind(data["check_kind"])
        parsed_status = _parse_status(data["status"])
        parsed_label = _parse_source_label(
            data.get("source_label", ProjectionSourceLabel.DEV_FIXTURE),
        )
        evidence_refs = tuple(str(item) for item in data.get("evidence_refs", ()))
        unavailable_reason = str(data.get("unavailable_reason", ""))
        metadata = _freeze_metadata(data.get("metadata"))
        if parsed_status is PathGovernanceExitSealStatus.UNAVAILABLE and not unavailable_reason:
            raise PathGovernanceValidationError(
                "unavailable_reason required when status is UNAVAILABLE",
                code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
                field="unavailable_reason",
            )
        check_id = str(data.get("check_id", "")) or compute_exit_seal_check_id(
            check_kind=parsed_kind,
            status=parsed_status,
            evidence_refs=evidence_refs,
            unavailable_reason=unavailable_reason,
            source_label=parsed_label,
            metadata=metadata,
        )
        partial = cls(
            check_id=check_id,
            check_kind=parsed_kind,
            status=parsed_status,
            summary=str(data["summary"]),
            evidence_refs=evidence_refs,
            source_label=parsed_label,
            unavailable_reason=unavailable_reason,
            metadata=metadata,
        )
        check_hash = stable_hash(partial.to_canonical_dict(include_hash=False))
        return cls(
            check_id=check_id,
            check_kind=partial.check_kind,
            status=partial.status,
            summary=partial.summary,
            evidence_refs=partial.evidence_refs,
            source_label=partial.source_label,
            unavailable_reason=partial.unavailable_reason,
            check_hash=check_hash,
            metadata=partial.metadata,
        )


def _build_check_result(
    *,
    check_kind: PathGovernanceExitSealCheckKind,
    status: PathGovernanceExitSealStatus,
    summary: str,
    source_label: ProjectionSourceLabel,
    evidence_refs: Sequence[str] = (),
    unavailable_reason: str = "",
    metadata: Mapping[str, Any] | None = None,
) -> PathGovernanceExitSealCheckResult:
    frozen_metadata = _freeze_metadata(metadata)
    if status is PathGovernanceExitSealStatus.UNAVAILABLE and not unavailable_reason:
        raise PathGovernanceValidationError(
            "unavailable_reason required when status is UNAVAILABLE",
            code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
            field="unavailable_reason",
        )
    check_id = compute_exit_seal_check_id(
        check_kind=check_kind,
        status=status,
        evidence_refs=evidence_refs,
        unavailable_reason=unavailable_reason,
        source_label=source_label,
        metadata=frozen_metadata,
    )
    partial = PathGovernanceExitSealCheckResult(
        check_id=check_id,
        check_kind=check_kind,
        status=status,
        summary=summary,
        evidence_refs=tuple(evidence_refs),
        source_label=source_label,
        unavailable_reason=unavailable_reason,
        metadata=frozen_metadata,
    )
    check_hash = stable_hash(partial.to_canonical_dict(include_hash=False))
    return PathGovernanceExitSealCheckResult(
        check_id=check_id,
        check_kind=check_kind,
        status=status,
        summary=summary,
        evidence_refs=tuple(evidence_refs),
        source_label=source_label,
        unavailable_reason=unavailable_reason,
        check_hash=check_hash,
        metadata=frozen_metadata,
    )


@dataclass(frozen=True)
class PathGovernanceExitSealDemoInput:
    """Exit seal demo configuration; DEV_FIXTURE by default."""

    demo_id: str
    source_label: ProjectionSourceLabel = ProjectionSourceLabel.DEV_FIXTURE
    include_harness_demo: bool = True
    include_policy_context_demo: bool = True
    include_projection_demo: bool = True
    include_cli_demo: bool = True
    include_trace_demo: bool = True
    include_violation_demo: bool = True
    include_unavailable_proof: bool = True
    demo_hash: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def to_canonical_dict(self, *, include_hash: bool = True) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "demo_id": self.demo_id,
            "include_cli_demo": self.include_cli_demo,
            "include_harness_demo": self.include_harness_demo,
            "include_policy_context_demo": self.include_policy_context_demo,
            "include_projection_demo": self.include_projection_demo,
            "include_trace_demo": self.include_trace_demo,
            "include_unavailable_proof": self.include_unavailable_proof,
            "include_violation_demo": self.include_violation_demo,
            "metadata": _sorted_metadata_dict(self.metadata),
            "source_label": self.source_label.value,
        }
        if include_hash:
            payload["demo_hash"] = self.demo_hash
        return dict(sorted(payload.items(), key=lambda item: item[0]))

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> PathGovernanceExitSealDemoInput:
        validate_known_fields(
            data,
            PATH_GOVERNANCE_EXIT_SEAL_DEMO_INPUT_KNOWN_FIELDS,
            label="PathGovernanceExitSealDemoInput",
        )
        parsed_label = _parse_source_label(
            data.get("source_label", ProjectionSourceLabel.DEV_FIXTURE),
        )
        metadata = _freeze_metadata(data.get("metadata"))
        demo_id = str(data.get("demo_id", "")) or compute_exit_seal_demo_id(
            source_label=parsed_label,
            include_harness_demo=bool(data.get("include_harness_demo", True)),
            include_policy_context_demo=bool(data.get("include_policy_context_demo", True)),
            include_projection_demo=bool(data.get("include_projection_demo", True)),
            include_cli_demo=bool(data.get("include_cli_demo", True)),
            include_trace_demo=bool(data.get("include_trace_demo", True)),
            include_violation_demo=bool(data.get("include_violation_demo", True)),
            include_unavailable_proof=bool(data.get("include_unavailable_proof", True)),
            metadata=metadata,
        )
        partial = cls(
            demo_id=demo_id,
            source_label=parsed_label,
            include_harness_demo=bool(data.get("include_harness_demo", True)),
            include_policy_context_demo=bool(data.get("include_policy_context_demo", True)),
            include_projection_demo=bool(data.get("include_projection_demo", True)),
            include_cli_demo=bool(data.get("include_cli_demo", True)),
            include_trace_demo=bool(data.get("include_trace_demo", True)),
            include_violation_demo=bool(data.get("include_violation_demo", True)),
            include_unavailable_proof=bool(data.get("include_unavailable_proof", True)),
            metadata=metadata,
        )
        demo_hash = stable_hash(partial.to_canonical_dict(include_hash=False))
        return cls(
            demo_id=demo_id,
            source_label=partial.source_label,
            include_harness_demo=partial.include_harness_demo,
            include_policy_context_demo=partial.include_policy_context_demo,
            include_projection_demo=partial.include_projection_demo,
            include_cli_demo=partial.include_cli_demo,
            include_trace_demo=partial.include_trace_demo,
            include_violation_demo=partial.include_violation_demo,
            include_unavailable_proof=partial.include_unavailable_proof,
            demo_hash=demo_hash,
            metadata=partial.metadata,
        )


@dataclass(frozen=True)
class PathGovernanceExitSealResult:
    """Exit seal aggregate evidence; not runtime permission."""

    seal_id: str
    checks: tuple[PathGovernanceExitSealCheckResult, ...]
    passed: bool
    failed_count: int
    skipped_count: int
    unavailable_count: int
    error_count: int
    demo_summary: str
    side_effects: PathGovernanceExitSealSideEffects
    source_label: ProjectionSourceLabel = ProjectionSourceLabel.DEV_FIXTURE
    schema_version: str = PATH_GOVERNANCE_EXIT_SEAL_SCHEMA
    created_by_task: str = PATH_GOVERNANCE_EXIT_SEAL_TASK_ID
    seal_hash: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def to_canonical_dict(self, *, include_hash: bool = True) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "checks": [
                check.to_canonical_dict(include_hash=True) for check in self.checks
            ],
            "created_by_task": self.created_by_task,
            "demo_summary": self.demo_summary,
            "error_count": self.error_count,
            "failed_count": self.failed_count,
            "metadata": _sorted_metadata_dict(self.metadata),
            "passed": self.passed,
            "schema_version": self.schema_version,
            "seal_id": self.seal_id,
            "side_effects": self.side_effects.to_canonical_dict(include_hash=True),
            "skipped_count": self.skipped_count,
            "source_label": self.source_label.value,
            "unavailable_count": self.unavailable_count,
        }
        if include_hash:
            payload["seal_hash"] = self.seal_hash
        return dict(sorted(payload.items(), key=lambda item: item[0]))

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> PathGovernanceExitSealResult:
        validate_known_fields(
            data,
            PATH_GOVERNANCE_EXIT_SEAL_RESULT_KNOWN_FIELDS,
            label="PathGovernanceExitSealResult",
        )
        checks = tuple(
            PathGovernanceExitSealCheckResult.from_dict(item)
            for item in data.get("checks", ())
        )
        side_effects = PathGovernanceExitSealSideEffects.from_dict(
            data.get("side_effects", {}),
        )
        parsed_label = _parse_source_label(
            data.get("source_label", ProjectionSourceLabel.DEV_FIXTURE),
        )
        metadata = _freeze_metadata(data.get("metadata"))
        schema_version = str(data.get("schema_version", PATH_GOVERNANCE_EXIT_SEAL_SCHEMA))
        created_by_task = str(data.get("created_by_task", PATH_GOVERNANCE_EXIT_SEAL_TASK_ID))
        seal_id = str(data.get("seal_id", "")) or compute_exit_seal_seal_id(
            check_ids=[check.check_id for check in checks],
            schema_version=schema_version,
            created_by_task=created_by_task,
        )
        partial = cls(
            seal_id=seal_id,
            checks=checks,
            passed=bool(data.get("passed", False)),
            failed_count=int(data.get("failed_count", 0)),
            skipped_count=int(data.get("skipped_count", 0)),
            unavailable_count=int(data.get("unavailable_count", 0)),
            error_count=int(data.get("error_count", 0)),
            demo_summary=str(data.get("demo_summary", "")),
            side_effects=side_effects,
            source_label=parsed_label,
            schema_version=schema_version,
            created_by_task=created_by_task,
            metadata=metadata,
        )
        seal_hash = stable_hash(partial.to_canonical_dict(include_hash=False))
        return cls(
            seal_id=seal_id,
            checks=partial.checks,
            passed=partial.passed,
            failed_count=partial.failed_count,
            skipped_count=partial.skipped_count,
            unavailable_count=partial.unavailable_count,
            error_count=partial.error_count,
            demo_summary=partial.demo_summary,
            side_effects=partial.side_effects,
            source_label=partial.source_label,
            schema_version=partial.schema_version,
            created_by_task=partial.created_by_task,
            seal_hash=seal_hash,
            metadata=partial.metadata,
        )


@dataclass(frozen=True)
class _ExitSealDemoEvidence:
    harness_run_id: str = ""
    bridge_id: str = ""
    envelope_hash: str = ""
    cli_response_ids: tuple[str, ...] = ()
    trace_payload_id: str = ""
    violation_payload_id: str = ""
    policy_called: bool = False


def build_path_governance_exit_seal_demo_input(
    *,
    source_label: ProjectionSourceLabel | str = ProjectionSourceLabel.DEV_FIXTURE,
    include_harness_demo: bool = True,
    include_policy_context_demo: bool = True,
    include_projection_demo: bool = True,
    include_cli_demo: bool = True,
    include_trace_demo: bool = True,
    include_violation_demo: bool = True,
    include_unavailable_proof: bool = True,
    metadata: Mapping[str, Any] | None = None,
) -> PathGovernanceExitSealDemoInput:
    """Build deterministic exit seal demo input; no side effects."""
    parsed_label = _parse_source_label(source_label)
    frozen_metadata = _freeze_metadata(metadata)
    demo_id = compute_exit_seal_demo_id(
        source_label=parsed_label,
        include_harness_demo=include_harness_demo,
        include_policy_context_demo=include_policy_context_demo,
        include_projection_demo=include_projection_demo,
        include_cli_demo=include_cli_demo,
        include_trace_demo=include_trace_demo,
        include_violation_demo=include_violation_demo,
        include_unavailable_proof=include_unavailable_proof,
        metadata=frozen_metadata,
    )
    partial = PathGovernanceExitSealDemoInput(
        demo_id=demo_id,
        source_label=parsed_label,
        include_harness_demo=include_harness_demo,
        include_policy_context_demo=include_policy_context_demo,
        include_projection_demo=include_projection_demo,
        include_cli_demo=include_cli_demo,
        include_trace_demo=include_trace_demo,
        include_violation_demo=include_violation_demo,
        include_unavailable_proof=include_unavailable_proof,
        metadata=frozen_metadata,
    )
    demo_hash = stable_hash(partial.to_canonical_dict(include_hash=False))
    return PathGovernanceExitSealDemoInput(
        demo_id=demo_id,
        source_label=parsed_label,
        include_harness_demo=include_harness_demo,
        include_policy_context_demo=include_policy_context_demo,
        include_projection_demo=include_projection_demo,
        include_cli_demo=include_cli_demo,
        include_trace_demo=include_trace_demo,
        include_violation_demo=include_violation_demo,
        include_unavailable_proof=include_unavailable_proof,
        demo_hash=demo_hash,
        metadata=frozen_metadata,
    )


def _demo_source_identity() -> object:
    return build_source_identity(
        source_kind=SourceKind.OPERATOR_INPUT,
        source_origin=SourceOrigin.OPERATOR,
        uri_or_path="DEV_FIXTURE:source/trusted",
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
        trust_label=SourceTrustLabel.TRUSTED,
        metadata=_DEMO_FIXTURE_META,
    )


def _demo_path_identity() -> object:
    return build_path_identity(
        "src/example.py",
        path_kind=PathKind.REPO_RELATIVE,
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
        metadata=_DEMO_FIXTURE_META,
    )


def _demo_path_result() -> PathGovernanceResolverResult:
    return PathGovernanceResolverResult(
        input_id="DEV_FIXTURE:path-input",
        shadow_decision=PathGovernanceShadowDecision.WOULD_ALLOW,
        decision_reasons=(PathGovernanceDecisionReason.SHADOW_MODE_ONLY,),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
        metadata=_DEMO_FIXTURE_META,
    )


def _demo_source_result() -> SourceTrustResolverResult:
    return SourceTrustResolverResult(
        input_id="DEV_FIXTURE:source-input",
        shadow_decision=SourceTrustShadowDecision.WOULD_REVIEW,
        decision_reasons=(SourceTrustDecisionReason.SHADOW_MODE_ONLY,),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
        metadata=_DEMO_FIXTURE_META,
    )


def _demo_conflict_result() -> object:
    return resolve_path_source_conflicts_shadow(
        path_resolver_result=_demo_path_result(),
        source_trust_resolver_result=_demo_source_result(),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )


def _demo_risk() -> object:
    return build_path_source_risk_classification(
        signals=(
            build_path_source_risk_signal(
                PathSourceRiskSignalKind.UNKNOWN_SOURCE,
                RiskClassificationBasis.SOURCE_TRUST,
                PathSourceRiskLevel.LOW,
                "DEV_FIXTURE risk",
                source_label=ProjectionSourceLabel.DEV_FIXTURE,
                metadata=_DEMO_FIXTURE_META,
            ),
        ),
        risk_level=PathSourceRiskLevel.LOW,
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
        metadata=_DEMO_FIXTURE_META,
    )


def _demo_provenance() -> object:
    source_identity = _demo_source_identity()
    return build_provenance_binding(
        source_identity=source_identity,
        evidence_refs=(
            build_source_evidence_ref(
                EvidenceBindingKind.SOURCE_TRUST_LABEL,
                source_identity,
                confidence=EvidenceConfidence.HIGH,
                source_label=ProjectionSourceLabel.DEV_FIXTURE,
                metadata=_DEMO_FIXTURE_META,
            ),
        ),
        claim_refs=(
            build_source_claim_ref(
                SourceClaimKind.FACTUAL_CLAIM,
                source_identity,
                "DEV_FIXTURE claim",
                confidence=EvidenceConfidence.HIGH,
                source_label=ProjectionSourceLabel.DEV_FIXTURE,
                metadata=_DEMO_FIXTURE_META,
            ),
        ),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
        metadata=_DEMO_FIXTURE_META,
    )


def _demo_authority_scope() -> object:
    return build_path_authority_scope(
        subject=PathAuthoritySubject(
            subject_kind=PathAuthoritySubjectKind.OPERATOR,
            display_name="DEV_FIXTURE",
            source_label=ProjectionSourceLabel.DEV_FIXTURE,
        ),
        actions=(PathScopeAction.READ,),
        basis=PathAuthorityBasis.TEST_FIXTURE,
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
        metadata=_DEMO_FIXTURE_META,
    )


def _demo_untrusted_boundary() -> object:
    return build_untrusted_content_boundary(
        content_kind=UntrustedContentKind.EXTERNAL_TEXT,
        source_identity=_demo_source_identity(),
        trust_label=SourceTrustLabel.UNTRUSTED,
        posture=UntrustedBoundaryPosture.REVIEW_REQUIRED,
        influence_surfaces=(ContentInfluenceSurface.PROMPT_INSTRUCTION,),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
        metadata=_DEMO_FIXTURE_META,
    )


def _run_exit_seal_demo_chain(
    demo_input: PathGovernanceExitSealDemoInput,
) -> _ExitSealDemoEvidence:
    """Run in-process DEV_FIXTURE demo chain; no side effects."""
    label = demo_input.source_label
    harness_run_id = ""
    bridge_id = ""
    envelope_hash = ""
    cli_response_ids: list[str] = []
    trace_payload_id = ""
    violation_payload_id = ""
    policy_called = False
    harness_result = None

    if demo_input.include_harness_demo:
        harness_result = run_path_governance_harness_suite(
            source_label=label,
            metadata=_DEMO_FIXTURE_META,
        )
        harness_run_id = harness_result.run_id

    path_result = _demo_path_result()
    source_result = _demo_source_result()
    conflict_result = _demo_conflict_result()
    risk = _demo_risk()
    provenance = _demo_provenance()
    authority = _demo_authority_scope()
    untrusted = _demo_untrusted_boundary()

    if demo_input.include_policy_context_demo and harness_result is not None:
        bridge = bridge_path_governance_to_policy_context(
            harness_result=harness_result,
            path_identity=_demo_path_identity(),
            source_identity=_demo_source_identity(),
            source_label=label,
            metadata=_DEMO_FIXTURE_META,
        )
        bridge_id = bridge.bridge_id
        policy_called = bridge.policy_called

    if demo_input.include_projection_demo:
        envelope = build_default_path_governance_capability_projection(
            source_label=label,
            metadata=_DEMO_FIXTURE_META,
            cli_binding_available=True,
        )
        envelope_hash = envelope.envelope_hash

    if demo_input.include_cli_demo:
        cli_ids: list[str] = []
        for command in (
            PathGovernanceCliCommandKind.STATUS,
            PathGovernanceCliCommandKind.READ_MODEL,
            PathGovernanceCliCommandKind.UNAVAILABLE_BINDINGS,
        ):
            response = handle_path_governance_cli_request(
                command_kind=command,
                output_format=PathGovernanceCliOutputFormat.TEXT,
                source_label=label,
                metadata=_DEMO_FIXTURE_META,
            )
            cli_ids.append(response.response_id)
        cli_response_ids = cli_ids

    if demo_input.include_trace_demo:
        trace_payload = build_path_resolution_trace_payload(
            path_resolver_result=path_result,
            source_trust_resolver_result=source_result,
            conflict_precedence_result=conflict_result,
            risk_classification=risk,
            provenance_binding=provenance,
            authority_scope=authority,
            untrusted_boundary=untrusted,
            source_label=label,
            metadata=_DEMO_FIXTURE_META,
        )
        trace_payload_id = trace_payload.payload_id

    if demo_input.include_violation_demo:
        trace_payload = build_path_resolution_trace_payload(
            path_resolver_result=path_result,
            source_trust_resolver_result=source_result,
            conflict_precedence_result=conflict_result,
            risk_classification=risk,
            provenance_binding=provenance,
            authority_scope=authority,
            untrusted_boundary=untrusted,
            source_label=label,
            metadata=_DEMO_FIXTURE_META,
        )
        violation_payload = build_path_violation_trace_payload(
            expected_path_resolver_result=path_result,
            current_path_resolver_result=path_result,
            expected_source_trust_result=source_result,
            current_source_trust_result=source_result,
            expected_conflict_precedence_result=conflict_result,
            current_conflict_precedence_result=conflict_result,
            expected_trace_payload=trace_payload,
            current_trace_payload=trace_payload,
            risk_classification=risk,
            provenance_binding=provenance,
            authority_scope=authority,
            untrusted_boundary=untrusted,
            source_label=label,
            metadata=_DEMO_FIXTURE_META,
        )
        violation_payload_id = violation_payload.payload_id

    return _ExitSealDemoEvidence(
        harness_run_id=harness_run_id,
        bridge_id=bridge_id,
        envelope_hash=envelope_hash,
        cli_response_ids=tuple(cli_response_ids),
        trace_payload_id=trace_payload_id,
        violation_payload_id=violation_payload_id,
        policy_called=policy_called,
    )


_PACKAGE_IMPORT_SYMBOLS: tuple[str, ...] = (
    "PathGovernanceExitSealCheckKind",
    "PathGovernanceExitSealStatus",
    "PathGovernanceExitSealSideEffects",
    "PathGovernanceExitSealCheckResult",
    "PathGovernanceExitSealDemoInput",
    "PathGovernanceExitSealResult",
    "build_path_governance_exit_seal_demo_input",
    "build_default_path_governance_exit_seal_checks",
    "run_path_governance_exit_seal",
    "render_path_governance_exit_seal_summary",
)

_CAPABILITY_PROOFS: tuple[tuple[PathGovernanceExitSealCheckKind, str, tuple[str, ...]], ...] = (
    (
        PathGovernanceExitSealCheckKind.FOUNDATION_CAPABILITY,
        PATH_GOVERNANCE_TASK_ID,
        ("get_path_governance_foundation_status",),
    ),
    (
        PathGovernanceExitSealCheckKind.PATH_IDENTITY_CAPABILITY,
        PATH_IDENTITY_TASK_ID,
        ("build_path_identity",),
    ),
    (
        PathGovernanceExitSealCheckKind.SOURCE_IDENTITY_CAPABILITY,
        SOURCE_IDENTITY_TASK_ID,
        ("build_source_identity",),
    ),
    (
        PathGovernanceExitSealCheckKind.SOURCE_TRUST_TAXONOMY_CAPABILITY,
        SOURCE_TRUST_TAXONOMY_TASK_ID,
        ("build_source_trust_taxonomy",),
    ),
    (
        PathGovernanceExitSealCheckKind.TRUSTED_ROOT_CAPABILITY,
        TRUSTED_ROOT_REGISTRY_TASK_ID,
        ("build_trusted_root_registry",),
    ),
    (
        PathGovernanceExitSealCheckKind.PATH_NORMALIZATION_CAPABILITY,
        PATH_NORMALIZATION_TASK_ID,
        ("normalize_path_for_governance", "normalize_path_string"),
    ),
    (
        PathGovernanceExitSealCheckKind.AUTHORITY_SCOPE_CAPABILITY,
        PATH_AUTHORITY_SCOPE_TASK_ID,
        ("build_path_authority_scope",),
    ),
    (
        PathGovernanceExitSealCheckKind.UNTRUSTED_BOUNDARY_CAPABILITY,
        UNTRUSTED_CONTENT_BOUNDARY_TASK_ID,
        ("build_untrusted_content_boundary",),
    ),
    (
        PathGovernanceExitSealCheckKind.PROVENANCE_BINDING_CAPABILITY,
        SOURCE_PROVENANCE_TASK_ID,
        ("build_provenance_binding",),
    ),
    (
        PathGovernanceExitSealCheckKind.RISK_CLASSIFICATION_CAPABILITY,
        PATH_SOURCE_RISK_TASK_ID,
        ("build_path_source_risk_classification",),
    ),
    (
        PathGovernanceExitSealCheckKind.PATH_RESOLVER_SHADOW,
        PATH_GOVERNANCE_RESOLVER_TASK_ID,
        ("resolve_path_governance_shadow",),
    ),
    (
        PathGovernanceExitSealCheckKind.SOURCE_TRUST_RESOLVER_SHADOW,
        SOURCE_TRUST_RESOLVER_TASK_ID,
        ("resolve_source_trust_shadow",),
    ),
    (
        PathGovernanceExitSealCheckKind.CONFLICT_PRECEDENCE_SHADOW,
        CONFLICT_PRECEDENCE_TASK_ID,
        ("resolve_path_source_conflicts_shadow",),
    ),
)


def build_default_path_governance_exit_seal_checks(
    demo_input: PathGovernanceExitSealDemoInput | None = None,
    *,
    demo_evidence: _ExitSealDemoEvidence | None = None,
    source_label: ProjectionSourceLabel | str = ProjectionSourceLabel.DEV_FIXTURE,
    metadata: Mapping[str, Any] | None = None,
) -> tuple[PathGovernanceExitSealCheckResult, ...]:
    """Build deterministic exit seal checks for P1.7.0–P1.7.20 coverage."""
    resolved_input = demo_input or build_path_governance_exit_seal_demo_input(
        source_label=source_label,
        metadata=metadata,
    )
    parsed_label = resolved_input.source_label
    frozen_metadata = _freeze_metadata(metadata)
    evidence = demo_evidence or _run_exit_seal_demo_chain(resolved_input)
    checks: list[PathGovernanceExitSealCheckResult] = []

    pg = importlib.import_module("agentic_runtime.path_governance")
    missing_symbols = [
        name for name in _PACKAGE_IMPORT_SYMBOLS if not hasattr(pg, name)
    ]
    checks.append(
        _build_check_result(
            check_kind=PathGovernanceExitSealCheckKind.PACKAGE_IMPORTS,
            status=(
                PathGovernanceExitSealStatus.PASS
                if not missing_symbols
                else PathGovernanceExitSealStatus.FAIL
            ),
            summary=(
                "path_governance package imports with exit seal symbols"
                if not missing_symbols
                else f"missing symbols: {', '.join(missing_symbols)}"
            ),
            source_label=parsed_label,
            evidence_refs=("agentic_runtime.path_governance",),
            metadata=frozen_metadata,
        ),
    )

    checks.append(
        _build_check_result(
            check_kind=PathGovernanceExitSealCheckKind.REPORT_INVENTORY,
            status=(
                PathGovernanceExitSealStatus.PASS
                if len(P17_REPORT_INVENTORY) == 20
                else PathGovernanceExitSealStatus.FAIL
            ),
            summary=f"P1.7 report inventory registry lists {len(P17_REPORT_INVENTORY)} reports",
            source_label=parsed_label,
            evidence_refs=P17_REPORT_INVENTORY,
            metadata=frozen_metadata,
        ),
    )

    for check_kind, task_id, symbols in _CAPABILITY_PROOFS:
        present = all(hasattr(pg, symbol) for symbol in symbols)
        checks.append(
            _build_check_result(
                check_kind=check_kind,
                status=(
                    PathGovernanceExitSealStatus.PASS
                    if present
                    else PathGovernanceExitSealStatus.FAIL
                ),
                summary=f"{task_id} capability symbols present",
                source_label=parsed_label,
                evidence_refs=(task_id, *symbols),
                metadata=frozen_metadata,
            ),
        )

    if resolved_input.include_harness_demo:
        checks.append(
            _build_check_result(
                check_kind=PathGovernanceExitSealCheckKind.TEST_HARNESS_DEMO,
                status=(
                    PathGovernanceExitSealStatus.PASS
                    if evidence.harness_run_id
                    else PathGovernanceExitSealStatus.SKIPPED
                ),
                summary="DEV_FIXTURE harness suite executed in-process",
                source_label=ProjectionSourceLabel.DEV_FIXTURE,
                evidence_refs=(evidence.harness_run_id,) if evidence.harness_run_id else (),
                metadata=frozen_metadata,
            ),
        )

    if resolved_input.include_policy_context_demo:
        checks.append(
            _build_check_result(
                check_kind=PathGovernanceExitSealCheckKind.POLICY_CONTEXT_BRIDGE_DEMO,
                status=(
                    PathGovernanceExitSealStatus.PASS
                    if evidence.bridge_id and evidence.policy_called is False
                    else PathGovernanceExitSealStatus.SKIPPED
                ),
                summary="policy context packet built; policy_called=false",
                source_label=ProjectionSourceLabel.DEV_FIXTURE,
                evidence_refs=(
                    evidence.bridge_id,
                    "policy_called=false",
                )
                if evidence.bridge_id
                else (),
                metadata=frozen_metadata,
            ),
        )

    if resolved_input.include_projection_demo:
        checks.append(
            _build_check_result(
                check_kind=PathGovernanceExitSealCheckKind.PROJECTION_CONTRACT_DEMO,
                status=(
                    PathGovernanceExitSealStatus.PASS
                    if evidence.envelope_hash
                    else PathGovernanceExitSealStatus.SKIPPED
                ),
                summary="API envelope object built; not HTTP server",
                source_label=ProjectionSourceLabel.DEV_FIXTURE,
                evidence_refs=(evidence.envelope_hash,) if evidence.envelope_hash else (),
                metadata=frozen_metadata,
            ),
        )

    if resolved_input.include_cli_demo:
        checks.append(
            _build_check_result(
                check_kind=PathGovernanceExitSealCheckKind.CLI_TUI_BINDING_DEMO,
                status=(
                    PathGovernanceExitSealStatus.PASS
                    if len(evidence.cli_response_ids) >= 3
                    else PathGovernanceExitSealStatus.SKIPPED
                ),
                summary="read-only CLI STATUS/READ_MODEL/UNAVAILABLE_BINDINGS rendered",
                source_label=ProjectionSourceLabel.DEV_FIXTURE,
                evidence_refs=evidence.cli_response_ids,
                metadata=frozen_metadata,
            ),
        )

    if resolved_input.include_trace_demo:
        checks.append(
            _build_check_result(
                check_kind=PathGovernanceExitSealCheckKind.PATH_RESOLUTION_TRACE_HOOK,
                status=(
                    PathGovernanceExitSealStatus.PASS
                    if evidence.trace_payload_id
                    else PathGovernanceExitSealStatus.SKIPPED
                ),
                summary=(
                    f"{PATH_RESOLUTION_TRACE_TASK_ID} trace payload built; "
                    "ledger_written=false; no TRACE_VERIFIED"
                ),
                source_label=ProjectionSourceLabel.DEV_FIXTURE,
                evidence_refs=(
                    PATH_RESOLUTION_TRACE_TASK_ID,
                    evidence.trace_payload_id,
                    "ledger_written=false",
                    "global_trace_written=false",
                )
                if evidence.trace_payload_id
                else (PATH_RESOLUTION_TRACE_TASK_ID,),
                metadata=frozen_metadata,
            ),
        )

    if resolved_input.include_violation_demo:
        checks.append(
            _build_check_result(
                check_kind=PathGovernanceExitSealCheckKind.VIOLATION_DRIFT_TRACE_HOOK,
                status=(
                    PathGovernanceExitSealStatus.PASS
                    if evidence.violation_payload_id
                    else PathGovernanceExitSealStatus.SKIPPED
                ),
                summary=(
                    f"{PATH_VIOLATION_TRACE_TASK_ID} violation/drift payload built; "
                    "runtime_mutated=false; enforcement_triggered=false"
                ),
                source_label=ProjectionSourceLabel.DEV_FIXTURE,
                evidence_refs=(
                    PATH_VIOLATION_TRACE_TASK_ID,
                    evidence.violation_payload_id,
                    "runtime_mutated=false",
                    "enforcement_triggered=false",
                )
                if evidence.violation_payload_id
                else (PATH_VIOLATION_TRACE_TASK_ID,),
                metadata=frozen_metadata,
            ),
        )

    if resolved_input.include_unavailable_proof:
        unavailable_refs = tuple(
            f"{key}:{reason}" for key, reason in P17_UNAVAILABLE_INTEGRATIONS.items()
        )
        checks.append(
            _build_check_result(
                check_kind=PathGovernanceExitSealCheckKind.UNAVAILABLE_STATES_PROOF,
                status=PathGovernanceExitSealStatus.PASS,
                summary="known unavailable integrations documented with reasons",
                source_label=ProjectionSourceLabel.UNAVAILABLE,
                evidence_refs=unavailable_refs,
                metadata=_freeze_metadata({"unavailable_count": len(unavailable_refs)}),
            ),
        )

    side_effects = build_path_governance_exit_seal_side_effects(metadata=frozen_metadata)
    checks.append(
        _build_check_result(
            check_kind=PathGovernanceExitSealCheckKind.NO_ENFORCEMENT_PROOF,
            status=PathGovernanceExitSealStatus.PASS,
            summary="all side-effect truth booleans remain false",
            source_label=parsed_label,
            evidence_refs=(side_effects.side_effects_hash,),
            metadata=_freeze_metadata({
                "policy_called": side_effects.policy_called,
                "approval_created": side_effects.approval_created,
                "ledger_written": side_effects.ledger_written,
                "global_trace_written": side_effects.global_trace_written,
                "runtime_mutated": side_effects.runtime_mutated,
                "enforcement_triggered": side_effects.enforcement_triggered,
                "source_mutated": side_effects.source_mutated,
                "prompt_filtered": side_effects.prompt_filtered,
                "memory_written": side_effects.memory_written,
                "tool_blocked": side_effects.tool_blocked,
            }),
        ),
    )

    foundation = get_path_governance_foundation_status()
    checks.append(
        _build_check_result(
            check_kind=PathGovernanceExitSealCheckKind.DOCS_STATE_REPORTS_PROOF,
            status=PathGovernanceExitSealStatus.PASS,
            summary=(
                f"P1.7.19 docs sync task {PATH_GOVERNANCE_EXIT_SEAL_DOCS_TASK_ID} "
                f"and report inventory registry present"
            ),
            source_label=parsed_label,
            evidence_refs=(
                PATH_GOVERNANCE_EXIT_SEAL_DOCS_TASK_ID,
                f"report_count={len(P17_REPORT_INVENTORY)}",
                foundation.task_id,
            ),
            metadata=frozen_metadata,
        ),
    )

    checks.append(
        _build_check_result(
            check_kind=PathGovernanceExitSealCheckKind.EXIT_SEAL_RESULT,
            status=PathGovernanceExitSealStatus.PASS,
            summary=f"exit seal schema {PATH_GOVERNANCE_EXIT_SEAL_SCHEMA} helpers present",
            source_label=parsed_label,
            evidence_refs=(PATH_GOVERNANCE_EXIT_SEAL_TASK_ID, PATH_GOVERNANCE_EXIT_SEAL_SCHEMA),
            metadata=frozen_metadata,
        ),
    )

    return tuple(sorted(checks, key=lambda item: (item.check_kind.value, item.check_id)))


def run_path_governance_exit_seal(
    demo_input: PathGovernanceExitSealDemoInput | None = None,
    *,
    source_label: ProjectionSourceLabel | str = ProjectionSourceLabel.DEV_FIXTURE,
    metadata: Mapping[str, Any] | None = None,
) -> PathGovernanceExitSealResult:
    """Run exit seal demo chain and build deterministic seal result."""
    resolved_input = demo_input or build_path_governance_exit_seal_demo_input(
        source_label=source_label,
        metadata=metadata,
    )
    parsed_label = resolved_input.source_label
    frozen_metadata = _freeze_metadata({
        **dict(resolved_input.metadata),
        **dict(metadata or {}),
    })
    demo_evidence = _run_exit_seal_demo_chain(resolved_input)
    checks = build_default_path_governance_exit_seal_checks(
        resolved_input,
        demo_evidence=demo_evidence,
        source_label=parsed_label,
        metadata=frozen_metadata,
    )

    failed_count = sum(
        1 for check in checks if check.status is PathGovernanceExitSealStatus.FAIL
    )
    skipped_count = sum(
        1 for check in checks if check.status is PathGovernanceExitSealStatus.SKIPPED
    )
    unavailable_count = sum(
        1 for check in checks if check.status is PathGovernanceExitSealStatus.UNAVAILABLE
    )
    error_count = sum(
        1 for check in checks if check.status is PathGovernanceExitSealStatus.ERROR
    )
    passed = failed_count == 0 and error_count == 0

    demo_parts = []
    if demo_evidence.harness_run_id:
        demo_parts.append(f"harness={demo_evidence.harness_run_id[:12]}")
    if demo_evidence.bridge_id:
        demo_parts.append(f"policy_context={demo_evidence.bridge_id[:12]}")
    if demo_evidence.envelope_hash:
        demo_parts.append(f"envelope={demo_evidence.envelope_hash[:12]}")
    if demo_evidence.cli_response_ids:
        demo_parts.append(f"cli_responses={len(demo_evidence.cli_response_ids)}")
    if demo_evidence.trace_payload_id:
        demo_parts.append(f"trace={demo_evidence.trace_payload_id[:12]}")
    if demo_evidence.violation_payload_id:
        demo_parts.append(f"violation={demo_evidence.violation_payload_id[:12]}")
    demo_summary = (
        "DEV_FIXTURE vertical slice: " + ", ".join(demo_parts)
        if demo_parts
        else "DEV_FIXTURE vertical slice: no demos enabled"
    )

    side_effects = build_path_governance_exit_seal_side_effects(metadata=frozen_metadata)
    seal_id = compute_exit_seal_seal_id(
        check_ids=[check.check_id for check in checks],
        schema_version=PATH_GOVERNANCE_EXIT_SEAL_SCHEMA,
        created_by_task=PATH_GOVERNANCE_EXIT_SEAL_TASK_ID,
    )
    partial = PathGovernanceExitSealResult(
        seal_id=seal_id,
        checks=checks,
        passed=passed,
        failed_count=failed_count,
        skipped_count=skipped_count,
        unavailable_count=unavailable_count,
        error_count=error_count,
        demo_summary=demo_summary,
        side_effects=side_effects,
        source_label=parsed_label,
        schema_version=PATH_GOVERNANCE_EXIT_SEAL_SCHEMA,
        created_by_task=PATH_GOVERNANCE_EXIT_SEAL_TASK_ID,
        metadata=frozen_metadata,
    )
    seal_hash = stable_hash(partial.to_canonical_dict(include_hash=False))
    return PathGovernanceExitSealResult(
        seal_id=seal_id,
        checks=checks,
        passed=passed,
        failed_count=failed_count,
        skipped_count=skipped_count,
        unavailable_count=unavailable_count,
        error_count=error_count,
        demo_summary=demo_summary,
        side_effects=side_effects,
        source_label=parsed_label,
        schema_version=PATH_GOVERNANCE_EXIT_SEAL_SCHEMA,
        created_by_task=PATH_GOVERNANCE_EXIT_SEAL_TASK_ID,
        seal_hash=seal_hash,
        metadata=frozen_metadata,
    )


def render_path_governance_exit_seal_summary(
    seal_result: PathGovernanceExitSealResult,
    *,
    include_checks: bool = True,
    include_unavailable: bool = True,
    include_side_effects: bool = True,
) -> str:
    """Render deterministic operator-readable exit seal summary."""
    lines = [
        f"Path Governance Exit Seal ({seal_result.schema_version})",
        f"Task: {seal_result.created_by_task}",
        f"Seal ID: {seal_result.seal_id}",
        f"Seal hash: {seal_result.seal_hash}",
        f"Source label: {seal_result.source_label.value}",
        f"Passed: {seal_result.passed}",
        (
            f"Counts: failed={seal_result.failed_count} skipped={seal_result.skipped_count} "
            f"unavailable={seal_result.unavailable_count} error={seal_result.error_count}"
        ),
        f"Demo: {seal_result.demo_summary}",
        "Seal pass is evidence, not runtime authority.",
    ]

    if include_checks:
        lines.append("Checks:")
        for check in sorted(seal_result.checks, key=lambda item: item.check_kind.value):
            lines.append(
                f"  [{check.check_kind.value}] {check.status.value}: {check.summary}"
            )

    if include_unavailable:
        lines.append("Known unavailable integrations:")
        for key, reason in sorted(P17_UNAVAILABLE_INTEGRATIONS.items()):
            lines.append(f"  {key}: {reason}")

    if include_side_effects:
        effects = seal_result.side_effects
        lines.append("Side-effect truth (all must be false):")
        for name in (
            "policy_called",
            "approval_created",
            "ledger_written",
            "global_trace_written",
            "runtime_mutated",
            "enforcement_triggered",
            "source_mutated",
            "prompt_filtered",
            "memory_written",
            "tool_blocked",
        ):
            lines.append(f"  {name}={getattr(effects, name)}")

    return "\n".join(lines)
