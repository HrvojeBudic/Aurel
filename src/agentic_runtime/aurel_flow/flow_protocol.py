"""P3-FLOW-C protocol-first / hybrid-ready boundary and P3 readiness matrix.

Prepares AurelFlow for future Python + Rust hybridization without migrating
anything now: schema/version metadata, the deterministic serialization
contract, and portability notes. Protocol-ready is not migration. Readiness
is not implementation. Python remains the P3 implementation truth.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from .errors import AurelFlowErrorCode, AurelFlowValidationError
from .read_model import FLOW_RUNTIME_READ_MODEL_VERSION
from .runtime_behavior_read_model import RUNTIME_BEHAVIOR_READ_MODEL_VERSION
from .runtime_events import (
    RUNTIME_EVENT_CONTRACT_VERSION,
    RUNTIME_EVENT_SNAPSHOT_VERSION,
    RUNTIME_EVENT_STREAM_VERSION,
)
from .scheduler import READY_QUEUE_VERSION, SCHEDULER_DECISION_VERSION
from .types import (
    MIGRATION_UNAVAILABLE_REASON,
    FlowTruthLabel,
    _CanonicalMixin,
    stable_hash,
    to_canonical_json,
)
from .workflow_graph import WORKFLOW_GRAPH_CONTRACT_VERSION
from .workflow_state import (
    WORKFLOW_RUN_CONTRACT_VERSION,
    WORKFLOW_STATE_SNAPSHOT_VERSION,
)

FLOW_PROTOCOL_BOUNDARY_VERSION = "flow_protocol_boundary.v1"
FLOW_PROTOCOL_ENVELOPE_VERSION = "flow_protocol_envelope.v1"
FLOW_SERIALIZATION_CONTRACT_VERSION = "flow_serialization_contract.v1"
FLOW_COMPATIBILITY_READ_MODEL_VERSION = "flow_compatibility_read_model.v1"
EXPANDED_P3_READINESS_MATRIX_VERSION = "expanded_p3_readiness_matrix.v1"


@dataclass(frozen=True)
class FlowSchemaVersion(_CanonicalMixin):
    """Versioned schema identity for one Flow contract."""

    schema_name: str
    schema_version: str
    contract_version: str
    owning_module: str


FLOW_SCHEMA_VERSIONS: tuple[FlowSchemaVersion, ...] = (
    FlowSchemaVersion(
        schema_name="workflow_graph",
        schema_version="v1",
        contract_version=WORKFLOW_GRAPH_CONTRACT_VERSION,
        owning_module="workflow_graph",
    ),
    FlowSchemaVersion(
        schema_name="workflow_run",
        schema_version="v1",
        contract_version=WORKFLOW_RUN_CONTRACT_VERSION,
        owning_module="workflow_state",
    ),
    FlowSchemaVersion(
        schema_name="workflow_state_snapshot",
        schema_version="v1",
        contract_version=WORKFLOW_STATE_SNAPSHOT_VERSION,
        owning_module="workflow_state",
    ),
    FlowSchemaVersion(
        schema_name="ready_queue",
        schema_version="v1",
        contract_version=READY_QUEUE_VERSION,
        owning_module="scheduler",
    ),
    FlowSchemaVersion(
        schema_name="scheduler_decision",
        schema_version="v1",
        contract_version=SCHEDULER_DECISION_VERSION,
        owning_module="scheduler",
    ),
    FlowSchemaVersion(
        schema_name="runtime_event",
        schema_version="v1",
        contract_version=RUNTIME_EVENT_CONTRACT_VERSION,
        owning_module="runtime_events",
    ),
    FlowSchemaVersion(
        schema_name="runtime_event_stream",
        schema_version="v1",
        contract_version=RUNTIME_EVENT_STREAM_VERSION,
        owning_module="runtime_events",
    ),
    FlowSchemaVersion(
        schema_name="runtime_event_stream_snapshot",
        schema_version="v1",
        contract_version=RUNTIME_EVENT_SNAPSHOT_VERSION,
        owning_module="runtime_events",
    ),
    FlowSchemaVersion(
        schema_name="flow_runtime_foundation_read_model",
        schema_version="v1",
        contract_version=FLOW_RUNTIME_READ_MODEL_VERSION,
        owning_module="read_model",
    ),
    FlowSchemaVersion(
        schema_name="runtime_behavior_read_model",
        schema_version="v1",
        contract_version=RUNTIME_BEHAVIOR_READ_MODEL_VERSION,
        owning_module="runtime_behavior_read_model",
    ),
)


@dataclass(frozen=True)
class FlowSerializationContract(_CanonicalMixin):
    """How every Flow contract serializes: deterministic and portable."""

    contract_version: str = FLOW_SERIALIZATION_CONTRACT_VERSION
    serialization_format: str = "canonical_json_sorted_keys"
    hash_algorithm: str = "sha256"
    stable_id_strategy: str = "sha256_of_canonical_json_payload"
    encoding: str = "utf-8"
    truth_label: FlowTruthLabel = FlowTruthLabel.CONTRACT_ONLY
    deterministic_serialization: bool = True


@dataclass(frozen=True)
class FlowCorePortabilityNotes(_CanonicalMixin):
    """Advisory notes on future Python/Rust hybrid portability."""

    notes: tuple[str, ...] = (
        "all contracts are frozen dataclasses with enum vocabularies — "
        "portable to Rust structs/enums",
        "all IDs and hashes derive from canonical JSON + sha256 — "
        "reproducible from any language",
        "no wall-clock time, randomness, threads, or IO in contract "
        "construction — deterministic across cores",
        "closed-world validation (allow-lists, fail-closed booleans) maps to "
        "exhaustive Rust match arms",
        "event streams are append-only ordered sequences — portable to a "
        "future log-backed store",
    )


@dataclass(frozen=True)
class FlowCompatibilityReadModel(_CanonicalMixin):
    """Hybrid-readiness truth. Rust-active and generated-code claims fail closed."""

    read_model_version: str
    portability_notes: FlowCorePortabilityNotes
    migration_unavailable_reason: str
    truth_label: FlowTruthLabel
    read_model_hash: str
    portable_to_rust_core: bool = True
    portable_to_proto_schema: bool = True
    python_is_implementation_truth: bool = True
    rust_core_active: bool = False
    go_core_active: bool = False
    protobuf_generated_code_present: bool = False
    capnproto_generated_code_present: bool = False

    def __post_init__(self) -> None:
        for boundary_field in (
            "rust_core_active",
            "go_core_active",
            "protobuf_generated_code_present",
            "capnproto_generated_code_present",
        ):
            if getattr(self, boundary_field):
                raise AurelFlowValidationError(
                    f"FlowCompatibilityReadModel.{boundary_field} must remain False",
                    code=AurelFlowErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                    field=boundary_field,
                )
        if not self.python_is_implementation_truth:
            raise AurelFlowValidationError(
                "FlowCompatibilityReadModel.python_is_implementation_truth must remain True",
                code=AurelFlowErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                field="python_is_implementation_truth",
            )


@dataclass(frozen=True)
class FlowProtocolEnvelope(_CanonicalMixin):
    """Versioned envelope binding a payload hash to its schema identity."""

    envelope_version: str
    schema: FlowSchemaVersion
    payload_kind: str
    payload_hash: str
    serialization_format: str
    truth_label: FlowTruthLabel


def build_flow_protocol_envelope(
    payload: Any, schema: FlowSchemaVersion, *, payload_kind: str
) -> FlowProtocolEnvelope:
    """Wrap any canonical-serializable value in a protocol envelope."""

    return FlowProtocolEnvelope(
        envelope_version=FLOW_PROTOCOL_ENVELOPE_VERSION,
        schema=schema,
        payload_kind=payload_kind,
        payload_hash=stable_hash(payload),
        serialization_format="canonical_json_sorted_keys",
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
    )


@dataclass(frozen=True)
class FlowProtocolBoundary(_CanonicalMixin):
    """The protocol-first boundary: ready for hybridization, migrating nothing."""

    boundary_version: str
    schema_versions: tuple[FlowSchemaVersion, ...]
    serialization_contract: FlowSerializationContract
    compatibility: FlowCompatibilityReadModel
    migration_unavailable_reason: str
    truth_label: FlowTruthLabel
    boundary_hash: str
    migration_active: bool = False
    rust_code_present: bool = False
    go_code_present: bool = False
    generated_schema_toolchain_present: bool = False

    def __post_init__(self) -> None:
        for boundary_field in (
            "migration_active",
            "rust_code_present",
            "go_code_present",
            "generated_schema_toolchain_present",
        ):
            if getattr(self, boundary_field):
                raise AurelFlowValidationError(
                    f"FlowProtocolBoundary.{boundary_field} must remain False",
                    code=AurelFlowErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                    field=boundary_field,
                )


def build_flow_compatibility_read_model() -> FlowCompatibilityReadModel:
    notes = FlowCorePortabilityNotes()
    payload = {
        "read_model_version": FLOW_COMPATIBILITY_READ_MODEL_VERSION,
        "notes": notes.notes,
    }
    return FlowCompatibilityReadModel(
        read_model_version=FLOW_COMPATIBILITY_READ_MODEL_VERSION,
        portability_notes=notes,
        migration_unavailable_reason=MIGRATION_UNAVAILABLE_REASON,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
        read_model_hash=stable_hash(payload),
    )


def build_flow_protocol_boundary() -> FlowProtocolBoundary:
    compatibility = build_flow_compatibility_read_model()
    contract = FlowSerializationContract()
    payload = {
        "boundary_version": FLOW_PROTOCOL_BOUNDARY_VERSION,
        "schemas": tuple(
            f"{schema.schema_name}:{schema.contract_version}"
            for schema in FLOW_SCHEMA_VERSIONS
        ),
        "compatibility_hash": compatibility.read_model_hash,
    }
    return FlowProtocolBoundary(
        boundary_version=FLOW_PROTOCOL_BOUNDARY_VERSION,
        schema_versions=FLOW_SCHEMA_VERSIONS,
        serialization_contract=contract,
        compatibility=compatibility,
        migration_unavailable_reason=MIGRATION_UNAVAILABLE_REASON,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
        boundary_hash=stable_hash(payload),
    )


def serialize_flow_protocol_boundary(boundary: FlowProtocolBoundary) -> str:
    """Deterministic JSON export of the protocol boundary."""

    return to_canonical_json(boundary)


class ExpandedP3ReadinessStatus(str, Enum):
    """Closed-world readiness statuses for expanded P3 checkpoints."""

    READY_FOR_PLAN = "READY_FOR_PLAN"
    PARTIAL_FOUNDATION = "PARTIAL_FOUNDATION"
    BLOCKED = "BLOCKED"
    UNAVAILABLE = "UNAVAILABLE"
    FUTURE_PACK = "FUTURE_PACK"


@dataclass(frozen=True)
class ExpandedP3ReadinessItem(_CanonicalMixin):
    """Readiness (not capability) for one expanded P3 checkpoint."""

    checkpoint: str
    title: str
    status: ExpandedP3ReadinessStatus
    foundation_evidence: str
    planned_pack: str
    implemented: bool = False

    def __post_init__(self) -> None:
        if self.implemented:
            raise AurelFlowValidationError(
                "ExpandedP3ReadinessItem.implemented must remain False — "
                "readiness is not implementation",
                code=AurelFlowErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                field="implemented",
            )


EXPANDED_P3_READINESS_ITEMS: tuple[ExpandedP3ReadinessItem, ...] = (
    ExpandedP3ReadinessItem(
        checkpoint="P3.10",
        title="authority boundary",
        status=ExpandedP3ReadinessStatus.PARTIAL_FOUNDATION,
        foundation_evidence=(
            "authority booleans already exist fail-closed on signals/frames/seal"
        ),
        planned_pack="P3-FLOW-D",
    ),
    ExpandedP3ReadinessItem(
        checkpoint="P3.11",
        title="operator review",
        status=ExpandedP3ReadinessStatus.PARTIAL_FOUNDATION,
        foundation_evidence=(
            "OperatorDecisionSignal with decision-quality flags and pause read models exist"
        ),
        planned_pack="P3-FLOW-D",
    ),
    ExpandedP3ReadinessItem(
        checkpoint="P3.12",
        title="reasoning/verifier/operator pause",
        status=ExpandedP3ReadinessStatus.PARTIAL_FOUNDATION,
        foundation_evidence="pause reasons include verifier/reasoning wait states",
        planned_pack="P3-FLOW-D",
    ),
    ExpandedP3ReadinessItem(
        checkpoint="P3.13",
        title="dynamic graph plasticity",
        status=ExpandedP3ReadinessStatus.READY_FOR_PLAN,
        foundation_evidence="graphs validate closed-world; no mutation-in-flight support yet",
        planned_pack="FUTURE_PACK",
    ),
    ExpandedP3ReadinessItem(
        checkpoint="P3.14",
        title="reversible checkpoint/fork/replay",
        status=ExpandedP3ReadinessStatus.PARTIAL_FOUNDATION,
        foundation_evidence=(
            "immutable transition history, sequences, and rollback candidates exist"
        ),
        planned_pack="FUTURE_PACK",
    ),
    ExpandedP3ReadinessItem(
        checkpoint="P3.15",
        title="self-healing control loop",
        status=ExpandedP3ReadinessStatus.PARTIAL_FOUNDATION,
        foundation_evidence="failure classification and recovery proposals exist candidate-only",
        planned_pack="FUTURE_PACK",
    ),
    ExpandedP3ReadinessItem(
        checkpoint="P3.16",
        title="autonomy levels enforcement",
        status=ExpandedP3ReadinessStatus.PARTIAL_FOUNDATION,
        foundation_evidence="autonomy profile visibility exists; no enforcement",
        planned_pack="FUTURE_PACK",
    ),
    ExpandedP3ReadinessItem(
        checkpoint="P3.17",
        title="real scheduling/resource allocation",
        status=ExpandedP3ReadinessStatus.READY_FOR_PLAN,
        foundation_evidence="ready queue exists; no resources, timers, or allocation",
        planned_pack="FUTURE_PACK",
    ),
    ExpandedP3ReadinessItem(
        checkpoint="P3.18",
        title="live service topology",
        status=ExpandedP3ReadinessStatus.READY_FOR_PLAN,
        foundation_evidence="no services exist; everything is in-process",
        planned_pack="FUTURE_PACK",
    ),
    ExpandedP3ReadinessItem(
        checkpoint="P3.19",
        title="harness evaluation system",
        status=ExpandedP3ReadinessStatus.READY_FOR_PLAN,
        foundation_evidence="deterministic demos and focused tests exist as seeds",
        planned_pack="FUTURE_PACK",
    ),
    ExpandedP3ReadinessItem(
        checkpoint="P3.20",
        title="P4 handoff",
        status=ExpandedP3ReadinessStatus.PARTIAL_FOUNDATION,
        foundation_evidence=(
            "every execution boundary is explicit and fail-closed; P4 AurelExec "
            "must supply executors behind Custos authority"
        ),
        planned_pack="P4",
    ),
)


@dataclass(frozen=True)
class ExpandedP3ReadinessMatrix(_CanonicalMixin):
    """Readiness matrix for P3.10–P3.20. Implements none of them."""

    matrix_version: str
    items: tuple[ExpandedP3ReadinessItem, ...]
    item_count: int
    truth_label: FlowTruthLabel
    matrix_hash: str
    implemented_count: int = 0

    def __post_init__(self) -> None:
        if self.implemented_count != 0:
            raise AurelFlowValidationError(
                "ExpandedP3ReadinessMatrix.implemented_count must remain 0",
                code=AurelFlowErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                field="implemented_count",
            )


def build_expanded_p3_readiness_matrix() -> ExpandedP3ReadinessMatrix:
    payload = {
        "matrix_version": EXPANDED_P3_READINESS_MATRIX_VERSION,
        "checkpoints": tuple(item.checkpoint for item in EXPANDED_P3_READINESS_ITEMS),
        "statuses": tuple(item.status.value for item in EXPANDED_P3_READINESS_ITEMS),
    }
    return ExpandedP3ReadinessMatrix(
        matrix_version=EXPANDED_P3_READINESS_MATRIX_VERSION,
        items=EXPANDED_P3_READINESS_ITEMS,
        item_count=len(EXPANDED_P3_READINESS_ITEMS),
        truth_label=FlowTruthLabel.READ_MODEL_ONLY,
        matrix_hash=stable_hash(payload),
    )
