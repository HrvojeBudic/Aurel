"""AurelShell cross-surface handoff contract (P2.0-C / P2.0.16).

Contract-only surface-to-surface handoff intents. Handoff is intent routing,
not execution, permission grant, or workflow start.

Architectural law:
  - Handoff is not execution.
  - Handoff is not permission.
  - Handoff is not SYSTEM access.
  - Handoff is not tool call.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .boundaries import build_system_no_agent_access_boundary
from .contracts import (
    AurelShellErrorCode,
    _CanonicalMixin,
    _hash_payload,
    _reject,
)
from .surface_registry import (
    AurelSurfaceKind,
    AurelSurfaceRegistry,
    SURFACE_KIND_IDS,
    build_default_surface_registry,
)

AUREL_HANDOFF_CONTRACT_VERSION = "aurel_handoff_contract.v1"
AUREL_HANDOFF_INTENT_VERSION = "aurel_handoff_intent.v1"

DEV_FIXTURE_HANDOFF_IDS: tuple[str, ...] = (
    "dev_fixture_handoff_cro_to_hq",
    "dev_fixture_handoff_hq_to_corp",
    "dev_fixture_handoff_hub_to_ide",
)


class HandoffTruthLabel(str, Enum):
    CONTRACT_ONLY = "CONTRACT_ONLY"
    HANDOFF_CONTRACT_ONLY = "HANDOFF_CONTRACT_ONLY"
    DEV_FIXTURE = "DEV_FIXTURE"
    NOT_LIVE = "NOT_LIVE"
    NOT_EXECUTED = "NOT_EXECUTED"
    UNAVAILABLE = "UNAVAILABLE"


class HandoffIntentKind(str, Enum):
    """Declared handoff intent category — contract only."""

    INSPECT_CONTEXT = "inspect_context"
    OPEN_VIEW = "open_view"
    INSPECT_CONTRACT = "inspect_contract"


class HandoffAvailability(str, Enum):
    CONTRACT_ONLY = "CONTRACT_ONLY"
    UNAVAILABLE = "UNAVAILABLE"


_HANDOFF_NON_GOALS: tuple[str, ...] = (
    "no_command_execution",
    "no_runtime_transition_engine",
    "no_automatic_workflow_start",
    "no_tool_execution",
    "no_permission_grant",
)


@dataclass(frozen=True)
class SurfaceHandoffBoundary(_CanonicalMixin):
    """Boundary constraints for a handoff intent."""

    executes_action: bool
    grants_permission: bool
    bypasses_system_boundary: bool
    starts_workflow: bool
    executes_tool: bool
    requires_operator_review: bool


@dataclass(frozen=True)
class SurfaceHandoffIntent(_CanonicalMixin):
    """Single cross-surface handoff intent descriptor."""

    schema_version: str
    handoff_id: str
    source_surface_id: str
    target_surface_id: str
    source_surface_kind: AurelSurfaceKind
    target_surface_kind: AurelSurfaceKind
    intent_kind: HandoffIntentKind
    intent_summary: str
    payload_refs: tuple[str, ...]
    operator_intent: str
    truth_label: HandoffTruthLabel
    availability: HandoffAvailability
    boundary: SurfaceHandoffBoundary
    is_dev_fixture: bool
    non_goals: tuple[str, ...]
    intent_hash: str


@dataclass(frozen=True)
class SurfaceHandoffResult(_CanonicalMixin):
    """Handoff result envelope — contract-only, not executed."""

    handoff_id: str
    executed: bool
    truth_label: HandoffTruthLabel


@dataclass(frozen=True)
class CrossSurfaceHandoffContract(_CanonicalMixin):
    """P2.0.16 — cross-surface handoff contract container."""

    schema_version: str
    handoff_intents: tuple[SurfaceHandoffIntent, ...]
    dev_fixture_handoffs: tuple[SurfaceHandoffIntent, ...]
    truth_label: HandoffTruthLabel
    unavailable_reason: str
    non_goals: tuple[str, ...]
    contract_hash: str


def _default_handoff_boundary() -> SurfaceHandoffBoundary:
    return SurfaceHandoffBoundary(
        executes_action=False,
        grants_permission=False,
        bypasses_system_boundary=False,
        starts_workflow=False,
        executes_tool=False,
        requires_operator_review=True,
    )


def _build_handoff_intent(
    *,
    handoff_id: str,
    source_kind: AurelSurfaceKind,
    target_kind: AurelSurfaceKind,
    intent_kind: HandoffIntentKind,
    intent_summary: str,
    operator_intent: str,
    payload_refs: tuple[str, ...],
    is_dev_fixture: bool,
) -> SurfaceHandoffIntent:
    truth = (
        HandoffTruthLabel.DEV_FIXTURE
        if is_dev_fixture
        else HandoffTruthLabel.HANDOFF_CONTRACT_ONLY
    )
    payload = {
        "schema_version": AUREL_HANDOFF_INTENT_VERSION,
        "handoff_id": handoff_id,
        "source_surface_id": SURFACE_KIND_IDS[source_kind],
        "target_surface_id": SURFACE_KIND_IDS[target_kind],
        "source_surface_kind": source_kind,
        "target_surface_kind": target_kind,
        "intent_kind": intent_kind,
        "intent_summary": intent_summary,
        "payload_refs": payload_refs,
        "operator_intent": operator_intent,
        "truth_label": truth,
        "availability": HandoffAvailability.CONTRACT_ONLY,
        "boundary": _default_handoff_boundary(),
        "is_dev_fixture": is_dev_fixture,
        "non_goals": _HANDOFF_NON_GOALS,
    }
    return SurfaceHandoffIntent(**payload, intent_hash=_hash_payload(payload))


def build_surface_handoff_intent(
    *,
    handoff_id: str,
    source_kind: AurelSurfaceKind,
    target_kind: AurelSurfaceKind,
    intent_kind: HandoffIntentKind,
    intent_summary: str,
    operator_intent: str,
    payload_refs: tuple[str, ...] = (),
    is_dev_fixture: bool = False,
) -> SurfaceHandoffIntent:
    return _build_handoff_intent(
        handoff_id=handoff_id,
        source_kind=source_kind,
        target_kind=target_kind,
        intent_kind=intent_kind,
        intent_summary=intent_summary,
        operator_intent=operator_intent,
        payload_refs=payload_refs,
        is_dev_fixture=is_dev_fixture,
    )


def _build_dev_fixture_handoffs() -> tuple[SurfaceHandoffIntent, ...]:
    return (
        _build_handoff_intent(
            handoff_id=DEV_FIXTURE_HANDOFF_IDS[0],
            source_kind=AurelSurfaceKind.AUREL_CRO,
            target_kind=AurelSurfaceKind.HQ,
            intent_kind=HandoffIntentKind.INSPECT_CONTEXT,
            intent_summary="Inspect operations context",
            operator_intent="operator_inspect_hq_operations_context",
            payload_refs=("dev_fixture:operations_context_ref",),
            is_dev_fixture=True,
        ),
        _build_handoff_intent(
            handoff_id=DEV_FIXTURE_HANDOFF_IDS[1],
            source_kind=AurelSurfaceKind.HQ,
            target_kind=AurelSurfaceKind.CORP,
            intent_kind=HandoffIntentKind.OPEN_VIEW,
            intent_summary="Open BusinessEnvironment view",
            operator_intent="operator_open_business_environment_view",
            payload_refs=("dev_fixture:business_environment_view_ref",),
            is_dev_fixture=True,
        ),
        _build_handoff_intent(
            handoff_id=DEV_FIXTURE_HANDOFF_IDS[2],
            source_kind=AurelSurfaceKind.HUB,
            target_kind=AurelSurfaceKind.IDE,
            intent_kind=HandoffIntentKind.INSPECT_CONTRACT,
            intent_summary="Inspect tool/code contract",
            operator_intent="operator_inspect_tool_code_contract",
            payload_refs=("dev_fixture:tool_code_contract_ref",),
            is_dev_fixture=True,
        ),
    )


def build_cross_surface_handoff_contract(
    registry: AurelSurfaceRegistry | None = None,
) -> CrossSurfaceHandoffContract:
    if registry is None:
        registry = build_default_surface_registry()
    dev_fixtures = _build_dev_fixture_handoffs()
    for intent in dev_fixtures:
        assert_handoff_validates_surface_registry(intent, registry)
    payload = {
        "schema_version": AUREL_HANDOFF_CONTRACT_VERSION,
        "handoff_intents": dev_fixtures,
        "dev_fixture_handoffs": dev_fixtures,
        "truth_label": HandoffTruthLabel.HANDOFF_CONTRACT_ONLY,
        "unavailable_reason": "handoff_contract_only_no_runtime_engine",
        "non_goals": _HANDOFF_NON_GOALS,
    }
    return CrossSurfaceHandoffContract(**payload, contract_hash=_hash_payload(payload))


def assert_handoff_validates_surface_registry(
    intent: SurfaceHandoffIntent,
    registry: AurelSurfaceRegistry,
) -> None:
    valid_ids = {surface.surface_id for surface in registry.surfaces}
    if intent.source_surface_id not in valid_ids:
        _reject(
            f"invalid source surface: {intent.source_surface_id!r}",
            field="source_surface_id",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if intent.target_surface_id not in valid_ids:
        _reject(
            f"invalid target surface: {intent.target_surface_id!r}",
            field="target_surface_id",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_handoff_does_not_execute(intent: SurfaceHandoffIntent) -> None:
    if intent.boundary.executes_action:
        _reject(
            "handoff must not execute actions",
            field="boundary.executes_action",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_handoff_does_not_grant_permission(intent: SurfaceHandoffIntent) -> None:
    if intent.boundary.grants_permission:
        _reject(
            "handoff must not grant permission",
            field="boundary.grants_permission",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_handoff_respects_system_boundary(intent: SurfaceHandoffIntent) -> None:
    system_boundary = build_system_no_agent_access_boundary()
    if intent.target_surface_kind == AurelSurfaceKind.SYSTEM:
        if intent.boundary.bypasses_system_boundary:
            _reject(
                "handoff must not bypass SYSTEM boundary",
                field="boundary.bypasses_system_boundary",
                code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
            )
    if intent.boundary.bypasses_system_boundary:
        _reject(
            "handoff must not bypass SYSTEM boundary",
            field="boundary.bypasses_system_boundary",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )
    if not system_boundary.access_rule.operator_only:
        _reject(
            "SYSTEM boundary must remain operator-only",
            field="system_boundary",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
