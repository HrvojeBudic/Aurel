"""P3-FLOW-C runtime wiring / hot-cold matrix, persistence and autonomy truth.

A contract object must never pretend to be active runtime enforcement. This
module states exactly what is local, read-only, contract-only, unavailable,
or future (P3-FLOW-D / P4 / P5 / P9). Persistence readiness is not
persistence. Autonomy visibility is not autonomy grant.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .errors import AurelFlowErrorCode, AurelFlowValidationError
from .types import (
    AUTHORITY_UNAVAILABLE_REASON,
    EXECUTION_UNAVAILABLE_REASON,
    PERSISTENCE_UNAVAILABLE_REASON,
    POLICY_ENFORCEMENT_UNAVAILABLE_REASON,
    TOP_LEVEL_EXPORT_UNAVAILABLE_REASON,
    TRACE_VERIFICATION_UNAVAILABLE_REASON,
    FlowTruthLabel,
    _CanonicalMixin,
    stable_hash,
)

FLOW_WIRING_READ_MODEL_VERSION = "flow_runtime_wiring_read_model.v1"
FLOW_HOT_COLD_MATRIX_VERSION = "flow_hot_cold_path_matrix.v1"
FLOW_PERSISTENCE_STATUS_VERSION = "flow_persistence_status_projection.v1"
FLOW_AUTONOMY_PROFILE_VERSION = "flow_autonomy_profile_read_model.v1"
FLOW_GOVERNANCE_PROFILE_VERSION = "flow_governance_profile_read_model.v1"

PERSISTENCE_LABEL = "UNAVAILABLE_PERSISTENCE"


class FlowCapabilityWiringStatus(str, Enum):
    """Closed-world wiring statuses for Flow capabilities."""

    AUREL_FLOW_LOCAL_ONLY = "AUREL_FLOW_LOCAL_ONLY"
    PACKAGE_INTERNAL = "PACKAGE_INTERNAL"
    READ_MODEL_ONLY = "READ_MODEL_ONLY"
    CONTRACT_ONLY = "CONTRACT_ONLY"
    INTERNAL_ONLY = "INTERNAL_ONLY"
    DEV_FIXTURE_ONLY = "DEV_FIXTURE_ONLY"
    CLI_READ_ONLY = "CLI_READ_ONLY"
    CLI_NOT_WIRED = "CLI_NOT_WIRED"
    RUNTIME_SUBMIT_NOT_WIRED = "RUNTIME_SUBMIT_NOT_WIRED"
    AGENTIC_ENTITY_NOT_WIRED = "AGENTIC_ENTITY_NOT_WIRED"
    REPO_AGENT_NOT_WIRED = "REPO_AGENT_NOT_WIRED"
    BUILD_RUNTIME_NOT_WIRED = "BUILD_RUNTIME_NOT_WIRED"
    TRACE_NOT_WIRED = "TRACE_NOT_WIRED"
    POLICY_NOT_WIRED = "POLICY_NOT_WIRED"
    PERSISTENCE_UNAVAILABLE = "PERSISTENCE_UNAVAILABLE"
    TOP_LEVEL_EXPORT_UNAVAILABLE = "TOP_LEVEL_EXPORT_UNAVAILABLE"
    PYTHON_ONLY_HYBRID_READY = "PYTHON_ONLY_HYBRID_READY"
    FUTURE_P3D = "FUTURE_P3D"
    FUTURE_P4 = "FUTURE_P4"
    FUTURE_P5 = "FUTURE_P5"
    FUTURE_P9 = "FUTURE_P9"


class FlowPathTemperature(str, Enum):
    """Whether a capability is a live local path, cold, or future."""

    HOT_LOCAL = "HOT_LOCAL"
    COLD_NOT_WIRED = "COLD_NOT_WIRED"
    FUTURE = "FUTURE"


@dataclass(frozen=True)
class FlowRuntimeWiringEntry(_CanonicalMixin):
    """One capability's honest wiring classification."""

    capability: str
    status: FlowCapabilityWiringStatus
    temperature: FlowPathTemperature
    truth_label: FlowTruthLabel
    reason: str
    owning_phase: str = "P3"


FLOW_WIRING_ENTRIES: tuple[FlowRuntimeWiringEntry, ...] = (
    FlowRuntimeWiringEntry(
        capability="WorkflowGraph",
        status=FlowCapabilityWiringStatus.AUREL_FLOW_LOCAL_ONLY,
        temperature=FlowPathTemperature.HOT_LOCAL,
        truth_label=FlowTruthLabel.LOCAL_RUNTIME_SUBSTRATE,
        reason="closed-world validated graph contract, local and in-memory",
    ),
    FlowRuntimeWiringEntry(
        capability="WorkflowRun",
        status=FlowCapabilityWiringStatus.AUREL_FLOW_LOCAL_ONLY,
        temperature=FlowPathTemperature.HOT_LOCAL,
        truth_label=FlowTruthLabel.LOCAL_RUNTIME_SUBSTRATE,
        reason="immutable run state with explicit transition history, in-memory only",
    ),
    FlowRuntimeWiringEntry(
        capability="SchedulerDecision",
        status=FlowCapabilityWiringStatus.READ_MODEL_ONLY,
        temperature=FlowPathTemperature.HOT_LOCAL,
        truth_label=FlowTruthLabel.READ_MODEL_ONLY,
        reason="readiness explanation only; a decision is not an execution capability",
    ),
    FlowRuntimeWiringEntry(
        capability="RuntimeEvent",
        status=FlowCapabilityWiringStatus.AUREL_FLOW_LOCAL_ONLY,
        temperature=FlowPathTemperature.HOT_LOCAL,
        truth_label=FlowTruthLabel.LOCAL_RUNTIME_BEHAVIOR,
        reason="local behavior record; structurally not TraceEvent, never Ledger",
    ),
    FlowRuntimeWiringEntry(
        capability="RuntimeBehaviorReadModel",
        status=FlowCapabilityWiringStatus.READ_MODEL_ONLY,
        temperature=FlowPathTemperature.HOT_LOCAL,
        truth_label=FlowTruthLabel.READ_MODEL_ONLY,
        reason="aggregated behavior truth for inspection only",
    ),
    FlowRuntimeWiringEntry(
        capability="PauseResumeSignals",
        status=FlowCapabilityWiringStatus.INTERNAL_ONLY,
        temperature=FlowPathTemperature.HOT_LOCAL,
        truth_label=FlowTruthLabel.INTERNAL_ONLY,
        reason="internal lifecycle state signals; no authority, no execution",
    ),
    FlowRuntimeWiringEntry(
        capability="RetryRecoveryRollbackCandidates",
        status=FlowCapabilityWiringStatus.CONTRACT_ONLY,
        temperature=FlowPathTemperature.HOT_LOCAL,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
        reason="candidate/proposal objects only; execution belongs to P4 AurelExec",
    ),
    FlowRuntimeWiringEntry(
        capability="FlowDemo",
        status=FlowCapabilityWiringStatus.DEV_FIXTURE_ONLY,
        temperature=FlowPathTemperature.HOT_LOCAL,
        truth_label=FlowTruthLabel.DEV_FIXTURE,
        reason="deterministic fixture scenario; demo completion is not execution",
    ),
    FlowRuntimeWiringEntry(
        capability="FlowCliBinding",
        status=FlowCapabilityWiringStatus.CLI_READ_ONLY,
        temperature=FlowPathTemperature.HOT_LOCAL,
        truth_label=FlowTruthLabel.READ_MODEL_ONLY,
        reason="read-only flow inspect/timeline/wiring/protocol/seal views; no control commands",
    ),
    FlowRuntimeWiringEntry(
        capability="RuntimeSubmitBridge",
        status=FlowCapabilityWiringStatus.RUNTIME_SUBMIT_NOT_WIRED,
        temperature=FlowPathTemperature.FUTURE,
        truth_label=FlowTruthLabel.UNAVAILABLE,
        reason="no Runtime.submit bridge exists; proposal/permission boundary belongs to P3-FLOW-D",
        owning_phase="P3-FLOW-D",
    ),
    FlowRuntimeWiringEntry(
        capability="AgenticEntityBridge",
        status=FlowCapabilityWiringStatus.AGENTIC_ENTITY_NOT_WIRED,
        temperature=FlowPathTemperature.COLD_NOT_WIRED,
        truth_label=FlowTruthLabel.UNAVAILABLE,
        reason="AgenticEntity.run does not know about aurel_flow",
    ),
    FlowRuntimeWiringEntry(
        capability="RepoAgentBridge",
        status=FlowCapabilityWiringStatus.REPO_AGENT_NOT_WIRED,
        temperature=FlowPathTemperature.COLD_NOT_WIRED,
        truth_label=FlowTruthLabel.UNAVAILABLE,
        reason="repo_agent does not know about aurel_flow",
    ),
    FlowRuntimeWiringEntry(
        capability="BuildRuntimeBridge",
        status=FlowCapabilityWiringStatus.BUILD_RUNTIME_NOT_WIRED,
        temperature=FlowPathTemperature.COLD_NOT_WIRED,
        truth_label=FlowTruthLabel.UNAVAILABLE,
        reason="build_runtime does not construct or wire aurel_flow",
    ),
    FlowRuntimeWiringEntry(
        capability="TraceBridge",
        status=FlowCapabilityWiringStatus.TRACE_NOT_WIRED,
        temperature=FlowPathTemperature.FUTURE,
        truth_label=FlowTruthLabel.UNAVAILABLE,
        reason=TRACE_VERIFICATION_UNAVAILABLE_REASON,
        owning_phase="P5",
    ),
    FlowRuntimeWiringEntry(
        capability="PolicyCustosBridge",
        status=FlowCapabilityWiringStatus.POLICY_NOT_WIRED,
        temperature=FlowPathTemperature.FUTURE,
        truth_label=FlowTruthLabel.UNAVAILABLE,
        reason=POLICY_ENFORCEMENT_UNAVAILABLE_REASON,
        owning_phase="P9",
    ),
    FlowRuntimeWiringEntry(
        capability="Persistence",
        status=FlowCapabilityWiringStatus.PERSISTENCE_UNAVAILABLE,
        temperature=FlowPathTemperature.COLD_NOT_WIRED,
        truth_label=FlowTruthLabel.UNAVAILABLE,
        reason=PERSISTENCE_UNAVAILABLE_REASON,
    ),
    FlowRuntimeWiringEntry(
        capability="TopLevelExport",
        status=FlowCapabilityWiringStatus.TOP_LEVEL_EXPORT_UNAVAILABLE,
        temperature=FlowPathTemperature.COLD_NOT_WIRED,
        truth_label=FlowTruthLabel.UNAVAILABLE,
        reason=TOP_LEVEL_EXPORT_UNAVAILABLE_REASON,
    ),
    FlowRuntimeWiringEntry(
        capability="PythonRustHybridCore",
        status=FlowCapabilityWiringStatus.PYTHON_ONLY_HYBRID_READY,
        temperature=FlowPathTemperature.HOT_LOCAL,
        truth_label=FlowTruthLabel.LOCAL_RUNTIME_SUBSTRATE,
        reason="Python is the P3 implementation truth; contracts are protocol-ready, Rust core inactive",
    ),
    FlowRuntimeWiringEntry(
        capability="Execution",
        status=FlowCapabilityWiringStatus.FUTURE_P4,
        temperature=FlowPathTemperature.FUTURE,
        truth_label=FlowTruthLabel.UNAVAILABLE,
        reason=EXECUTION_UNAVAILABLE_REASON,
        owning_phase="P4",
    ),
)


@dataclass(frozen=True)
class FlowHotColdPathMatrix(_CanonicalMixin):
    """Hot/cold/future classification over all Flow capabilities."""

    matrix_version: str
    entries: tuple[FlowRuntimeWiringEntry, ...]
    hot_local_count: int
    cold_not_wired_count: int
    future_count: int
    truth_label: FlowTruthLabel
    matrix_hash: str


@dataclass(frozen=True)
class FlowRuntimeWiringReadModel(_CanonicalMixin):
    """Wiring truth read model. Integration booleans fail closed."""

    read_model_version: str
    matrix: FlowHotColdPathMatrix
    truth_label: FlowTruthLabel
    read_model_hash: str
    cli_read_only_wired: bool = True
    runtime_submit_wired: bool = False
    agentic_entity_wired: bool = False
    repo_agent_wired: bool = False
    build_runtime_wired: bool = False
    trace_wired: bool = False
    policy_wired: bool = False
    persistence_wired: bool = False
    rust_core_active: bool = False

    def __post_init__(self) -> None:
        for boundary_field in (
            "runtime_submit_wired",
            "agentic_entity_wired",
            "repo_agent_wired",
            "build_runtime_wired",
            "trace_wired",
            "policy_wired",
            "persistence_wired",
            "rust_core_active",
        ):
            if getattr(self, boundary_field):
                raise AurelFlowValidationError(
                    f"FlowRuntimeWiringReadModel.{boundary_field} must remain False",
                    code=AurelFlowErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                    field=boundary_field,
                )


def build_flow_hot_cold_matrix() -> FlowHotColdPathMatrix:
    entries = FLOW_WIRING_ENTRIES
    payload = {
        "matrix_version": FLOW_HOT_COLD_MATRIX_VERSION,
        "capabilities": tuple(entry.capability for entry in entries),
        "statuses": tuple(entry.status.value for entry in entries),
    }
    return FlowHotColdPathMatrix(
        matrix_version=FLOW_HOT_COLD_MATRIX_VERSION,
        entries=entries,
        hot_local_count=sum(
            1 for entry in entries if entry.temperature is FlowPathTemperature.HOT_LOCAL
        ),
        cold_not_wired_count=sum(
            1
            for entry in entries
            if entry.temperature is FlowPathTemperature.COLD_NOT_WIRED
        ),
        future_count=sum(
            1 for entry in entries if entry.temperature is FlowPathTemperature.FUTURE
        ),
        truth_label=FlowTruthLabel.READ_MODEL_ONLY,
        matrix_hash=stable_hash(payload),
    )


def build_flow_runtime_wiring_read_model(
    *, cli_read_only_wired: bool = True
) -> FlowRuntimeWiringReadModel:
    matrix = build_flow_hot_cold_matrix()
    payload = {
        "read_model_version": FLOW_WIRING_READ_MODEL_VERSION,
        "matrix_hash": matrix.matrix_hash,
        "cli_read_only_wired": cli_read_only_wired,
    }
    return FlowRuntimeWiringReadModel(
        read_model_version=FLOW_WIRING_READ_MODEL_VERSION,
        matrix=matrix,
        truth_label=FlowTruthLabel.READ_MODEL_ONLY,
        read_model_hash=stable_hash(payload),
        cli_read_only_wired=cli_read_only_wired,
    )


@dataclass(frozen=True)
class FlowEventStoreBoundary(_CanonicalMixin):
    """No external event store exists. Fail-closed."""

    store_kind: str = "NONE"
    future_boundary: str = "external event store belongs to a future storage pack"
    external_event_store_connected: bool = False

    def __post_init__(self) -> None:
        if self.external_event_store_connected:
            raise AurelFlowValidationError(
                "FlowEventStoreBoundary.external_event_store_connected must remain False",
                code=AurelFlowErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                field="external_event_store_connected",
            )


@dataclass(frozen=True)
class FlowProjectionStoreBoundary(_CanonicalMixin):
    """No projection store exists. Fail-closed."""

    store_kind: str = "NONE"
    future_boundary: str = "projection store belongs to a future storage pack"
    projection_store_connected: bool = False

    def __post_init__(self) -> None:
        if self.projection_store_connected:
            raise AurelFlowValidationError(
                "FlowProjectionStoreBoundary.projection_store_connected must remain False",
                code=AurelFlowErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                field="projection_store_connected",
            )


@dataclass(frozen=True)
class FlowAppendOnlyLogReadiness(_CanonicalMixin):
    """Advisory: the event stream is append-only shaped, but not persisted."""

    append_only_shape_present: bool = True
    persisted: bool = False

    def __post_init__(self) -> None:
        if self.persisted:
            raise AurelFlowValidationError(
                "FlowAppendOnlyLogReadiness.persisted must remain False",
                code=AurelFlowErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                field="persisted",
            )


@dataclass(frozen=True)
class FlowReplayCursorReadiness(_CanonicalMixin):
    """Advisory: sequences give a replay-cursor shape, but replay is future."""

    sequence_ordering_present: bool = True
    replay_available: bool = False

    def __post_init__(self) -> None:
        if self.replay_available:
            raise AurelFlowValidationError(
                "FlowReplayCursorReadiness.replay_available must remain False",
                code=AurelFlowErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                field="replay_available",
            )


@dataclass(frozen=True)
class FlowPersistenceStatusProjection(_CanonicalMixin):
    """Persistence truth: readiness is not persistence."""

    projection_version: str
    persistence_label: str
    reason: str
    event_store_boundary: FlowEventStoreBoundary
    projection_store_boundary: FlowProjectionStoreBoundary
    append_only_readiness: FlowAppendOnlyLogReadiness
    replay_cursor_readiness: FlowReplayCursorReadiness
    truth_label: FlowTruthLabel
    projection_hash: str
    future_storage_boundary: bool = True
    persisted: bool = False
    external_event_store: bool = False
    projection_store: bool = False

    def __post_init__(self) -> None:
        for boundary_field in ("persisted", "external_event_store", "projection_store"):
            if getattr(self, boundary_field):
                raise AurelFlowValidationError(
                    f"FlowPersistenceStatusProjection.{boundary_field} must remain False",
                    code=AurelFlowErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                    field=boundary_field,
                )


def build_flow_persistence_status_projection() -> FlowPersistenceStatusProjection:
    payload = {
        "projection_version": FLOW_PERSISTENCE_STATUS_VERSION,
        "persistence_label": PERSISTENCE_LABEL,
    }
    return FlowPersistenceStatusProjection(
        projection_version=FLOW_PERSISTENCE_STATUS_VERSION,
        persistence_label=PERSISTENCE_LABEL,
        reason=PERSISTENCE_UNAVAILABLE_REASON,
        event_store_boundary=FlowEventStoreBoundary(),
        projection_store_boundary=FlowProjectionStoreBoundary(),
        append_only_readiness=FlowAppendOnlyLogReadiness(),
        replay_cursor_readiness=FlowReplayCursorReadiness(),
        truth_label=FlowTruthLabel.UNAVAILABLE,
        projection_hash=stable_hash(payload),
    )


class FlowAutonomyLevel(str, Enum):
    """Visible autonomy scale. A6+ are future-only in P3."""

    A0_OBSERVE_ONLY = "A0_OBSERVE_ONLY"
    A1_SUGGEST_ONLY = "A1_SUGGEST_ONLY"
    A2_INTERNAL_ORGANIZE = "A2_INTERNAL_ORGANIZE"
    A3_INTERNAL_PAUSE_RESUME = "A3_INTERNAL_PAUSE_RESUME"
    A4_SELF_HEAL_CANDIDATE = "A4_SELF_HEAL_CANDIDATE"
    A5_EXECUTION_PROPOSAL_READY = "A5_EXECUTION_PROPOSAL_READY"
    A6_BOUNDED_AUTO_EXECUTION = "A6_BOUNDED_AUTO_EXECUTION"
    A7_ADAPTIVE_AUTONOMY = "A7_ADAPTIVE_AUTONOMY"


@dataclass(frozen=True)
class FlowAutonomyLevelProjection(_CanonicalMixin):
    """One autonomy level's honest availability."""

    level: FlowAutonomyLevel
    description: str
    available_in_p3: bool
    future_marker: str = ""


FLOW_AUTONOMY_LEVEL_PROJECTIONS: tuple[FlowAutonomyLevelProjection, ...] = (
    FlowAutonomyLevelProjection(
        level=FlowAutonomyLevel.A0_OBSERVE_ONLY,
        description="observe local flow state",
        available_in_p3=True,
    ),
    FlowAutonomyLevelProjection(
        level=FlowAutonomyLevel.A1_SUGGEST_ONLY,
        description="suggest via read models and proposals",
        available_in_p3=True,
    ),
    FlowAutonomyLevelProjection(
        level=FlowAutonomyLevel.A2_INTERNAL_ORGANIZE,
        description="organize internal graph/run/queue state",
        available_in_p3=True,
    ),
    FlowAutonomyLevelProjection(
        level=FlowAutonomyLevel.A3_INTERNAL_PAUSE_RESUME,
        description="pause/resume internal lifecycle state on operator signal",
        available_in_p3=True,
    ),
    FlowAutonomyLevelProjection(
        level=FlowAutonomyLevel.A4_SELF_HEAL_CANDIDATE,
        description="mark failure/retry/recovery candidates (never executed)",
        available_in_p3=True,
    ),
    FlowAutonomyLevelProjection(
        level=FlowAutonomyLevel.A5_EXECUTION_PROPOSAL_READY,
        description="produce declarative recovery proposals for future executors",
        available_in_p3=True,
    ),
    FlowAutonomyLevelProjection(
        level=FlowAutonomyLevel.A6_BOUNDED_AUTO_EXECUTION,
        description="bounded auto execution",
        available_in_p3=False,
        future_marker="FUTURE_P4",
    ),
    FlowAutonomyLevelProjection(
        level=FlowAutonomyLevel.A7_ADAPTIVE_AUTONOMY,
        description="adaptive autonomy",
        available_in_p3=False,
        future_marker="FUTURE_LATER",
    ),
)


@dataclass(frozen=True)
class FlowAutonomyProfileReadModel(_CanonicalMixin):
    """Autonomy visibility. Visibility is not grant: execution stays False."""

    read_model_version: str
    current_autonomy_level: FlowAutonomyLevel
    max_allowed_autonomy_level: FlowAutonomyLevel
    approval_mode: str
    risk_auto_approval_boundary: str
    scope_envelope_summary: str
    sandbox_profile: str
    unsafe_local_warning: str
    level_projections: tuple[FlowAutonomyLevelProjection, ...]
    truth_label: FlowTruthLabel
    read_model_hash: str
    hard_isolated: bool = False
    reflex_available: bool = False
    measured_autonomy_signal_available: bool = False
    execution_available: bool = False
    autonomy_granted_by_this_read_model: bool = False

    def __post_init__(self) -> None:
        for boundary_field in (
            "execution_available",
            "autonomy_granted_by_this_read_model",
        ):
            if getattr(self, boundary_field):
                raise AurelFlowValidationError(
                    f"FlowAutonomyProfileReadModel.{boundary_field} must remain False",
                    code=AurelFlowErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                    field=boundary_field,
                )


def build_flow_autonomy_profile_read_model() -> FlowAutonomyProfileReadModel:
    payload = {
        "read_model_version": FLOW_AUTONOMY_PROFILE_VERSION,
        "current": FlowAutonomyLevel.A3_INTERNAL_PAUSE_RESUME.value,
        "max_allowed": FlowAutonomyLevel.A5_EXECUTION_PROPOSAL_READY.value,
    }
    return FlowAutonomyProfileReadModel(
        read_model_version=FLOW_AUTONOMY_PROFILE_VERSION,
        current_autonomy_level=FlowAutonomyLevel.A3_INTERNAL_PAUSE_RESUME,
        max_allowed_autonomy_level=FlowAutonomyLevel.A5_EXECUTION_PROPOSAL_READY,
        approval_mode="OPERATOR_DECIDES",
        risk_auto_approval_boundary="NONE_AUTO_APPROVED",
        scope_envelope_summary=(
            "internal AurelFlow state only: graph, run, events, pauses, candidates"
        ),
        sandbox_profile="NONE_REQUIRED_NO_EXECUTION",
        unsafe_local_warning=(
            "AurelFlow is a local in-process library; it executes nothing, so no "
            "sandbox isolation applies — execution isolation belongs to P4 AurelExec"
        ),
        level_projections=FLOW_AUTONOMY_LEVEL_PROJECTIONS,
        truth_label=FlowTruthLabel.READ_MODEL_ONLY,
        read_model_hash=stable_hash(payload),
    )


@dataclass(frozen=True)
class FlowGovernanceProfileReadModel(_CanonicalMixin):
    """Core-law visibility: who proposes, disposes, authorizes, proves."""

    read_model_version: str
    entity_proposes: bool
    runtime_disposes: bool
    operator_decides: bool
    custos_authorizes_marker: str
    trace_proves_marker: str
    authority_unavailable_reason: str
    truth_label: FlowTruthLabel
    read_model_hash: str
    execution_available: bool = False
    policy_enforced_by_flow: bool = False

    def __post_init__(self) -> None:
        for boundary_field in ("execution_available", "policy_enforced_by_flow"):
            if getattr(self, boundary_field):
                raise AurelFlowValidationError(
                    f"FlowGovernanceProfileReadModel.{boundary_field} must remain False",
                    code=AurelFlowErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                    field=boundary_field,
                )


def build_flow_governance_profile_read_model() -> FlowGovernanceProfileReadModel:
    payload = {"read_model_version": FLOW_GOVERNANCE_PROFILE_VERSION}
    return FlowGovernanceProfileReadModel(
        read_model_version=FLOW_GOVERNANCE_PROFILE_VERSION,
        entity_proposes=True,
        runtime_disposes=True,
        operator_decides=True,
        custos_authorizes_marker="FUTURE_P9",
        trace_proves_marker="FUTURE_P5",
        authority_unavailable_reason=AUTHORITY_UNAVAILABLE_REASON,
        truth_label=FlowTruthLabel.READ_MODEL_ONLY,
        read_model_hash=stable_hash(payload),
    )
