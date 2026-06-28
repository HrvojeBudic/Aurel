"""P2.0-E operator-testable surface demo state contracts.

The demo state is an inspectable read-model fixture. It is not product UI,
not a live shell, and not a runtime/demo harness.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .contracts import AurelShellErrorCode, _CanonicalMixin, _hash_payload, _reject
from .fixture_discipline import SurfaceFixtureKind
from .permission_matrix import (
    SurfacePermissionEntry,
    SurfacePermissionMatrixSnapshot,
    build_default_surface_permission_matrix,
)
from .surface_registry import (
    AurelSurfaceContract,
    AurelSurfaceKind,
    AurelSurfaceRegistry,
    build_default_surface_registry,
)
from .truth_labels import SurfaceTruthLabel
from .unavailable_state import (
    SurfaceUnavailableReason,
    SurfaceUnavailableState,
    SurfaceUnavailableStateContract,
    build_surface_unavailable_state,
    build_surface_unavailable_state_contract,
)

OPERATOR_DEMO_STATE_VERSION = "operator_demo_state.v1"
OPERATOR_DEMO_CARD_VERSION = "operator_demo_surface_card.v1"
OPERATOR_DEMO_TRUTH_BOUNDARY_VERSION = "operator_demo_truth_boundary.v1"
OPERATOR_DEMO_STATE_ID = "p2_0_e_operator_demo_state"


class OperatorDemoAvailabilityState(str, Enum):
    OPERATOR_TESTABLE = "OPERATOR_TESTABLE"
    CONTRACT_ONLY = "CONTRACT_ONLY"
    DEV_FIXTURE = "DEV_FIXTURE"
    NOT_LIVE = "NOT_LIVE"


_OPERATOR_DEMO_NON_GOALS: tuple[str, ...] = (
    "no_product_ui",
    "no_frontend_demo",
    "no_live_shell",
    "no_actual_operator_runtime",
    "no_demo_harness_runtime",
)


@dataclass(frozen=True)
class OperatorDemoTruthBoundary(_CanonicalMixin):
    """Truth guard for operator-testable demo state."""

    schema_version: str
    demo_is_operator_testable_contract: bool
    demo_is_dev_fixture: bool
    demo_is_live: bool
    truth_label: SurfaceTruthLabel
    fixture_kind: SurfaceFixtureKind
    source: str
    scope: str
    expires_or_boundary: str
    boundary_hash: str


@dataclass(frozen=True)
class OperatorDemoSurfaceCard(_CanonicalMixin):
    """Single operator-testable surface card."""

    schema_version: str
    demo_id: str
    surface_id: str
    surface_kind: AurelSurfaceKind
    display_name: str
    purpose: str
    operator_test_label: str
    availability_state: OperatorDemoAvailabilityState
    truth_label: SurfaceTruthLabel
    fixture_kind: SurfaceFixtureKind
    source: str
    scope: str
    expires_or_boundary: str
    permission_summary: str
    unavailable_state: SurfaceUnavailableState
    demo_is_operator_testable: bool
    demo_is_dev_fixture: bool
    demo_is_live: bool
    executes_action: bool
    mutates_runtime: bool
    writes_memory: bool
    writes_trace: bool
    creates_ui: bool
    non_goals: tuple[str, ...]
    card_hash: str


@dataclass(frozen=True)
class OperatorTestableSurfaceDemoState(_CanonicalMixin):
    """P2.0.22 demo/read-model state over all canonical surfaces."""

    schema_version: str
    demo_id: str
    cards: tuple[OperatorDemoSurfaceCard, ...]
    surface_count: int
    canonical_surface_ids: tuple[str, ...]
    truth_boundary: OperatorDemoTruthBoundary
    unavailable_state_contract: SurfaceUnavailableStateContract
    demo_state_exists: bool
    demo_state_covers_all_surfaces: bool
    demo_state_is_operator_testable: bool
    demo_state_is_dev_fixture: bool
    demo_state_is_not_live: bool
    demo_state_does_not_execute: bool
    demo_state_does_not_mutate_runtime: bool
    demo_state_does_not_write_memory: bool
    demo_state_does_not_write_trace: bool
    demo_state_does_not_create_ui: bool
    non_goals: tuple[str, ...]
    state_hash: str


def build_operator_demo_truth_boundary() -> OperatorDemoTruthBoundary:
    payload = {
        "schema_version": OPERATOR_DEMO_TRUTH_BOUNDARY_VERSION,
        "demo_is_operator_testable_contract": True,
        "demo_is_dev_fixture": True,
        "demo_is_live": False,
        "truth_label": SurfaceTruthLabel.DEV_FIXTURE,
        "fixture_kind": SurfaceFixtureKind.DEV_FIXTURE,
        "source": "p2_0_e_operator_demo_contract_fixture",
        "scope": "p2_0_e_operator_testable_contract_only",
        "expires_or_boundary": "not_live_no_product_ui_no_runtime",
    }
    return OperatorDemoTruthBoundary(
        **payload,
        boundary_hash=_hash_payload(payload),
    )


def _permission_summary_for(
    permission_matrix: SurfacePermissionMatrixSnapshot,
    surface: AurelSurfaceContract,
) -> str:
    entry: SurfacePermissionEntry | None = None
    for candidate in permission_matrix.entries:
        if candidate.surface_kind is surface.surface_kind:
            entry = candidate
            break
    if entry is None:
        _reject(
            f"missing permission entry for {surface.surface_id}",
            field="permission_matrix.entries",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    assert entry is not None
    return (
        f"{entry.operator_visible_label}; contract_only=true; "
        "authorizes_action=false; executes_action=false"
    )


def build_operator_demo_surface_card(
    surface: AurelSurfaceContract,
    *,
    permission_matrix: SurfacePermissionMatrixSnapshot | None = None,
) -> OperatorDemoSurfaceCard:
    if permission_matrix is None:
        permission_matrix = build_default_surface_permission_matrix()
    unavailable_state = build_surface_unavailable_state(
        surface_kind=surface.surface_kind,
        unavailable_reason=SurfaceUnavailableReason.MISSING_LIVE_PATH,
        operator_message=(
            f"{surface.display_name} is operator-testable as a P2.0-E "
            "contract fixture only."
        ),
        dependency="future_live_surface_or_client_runtime",
    )
    payload = {
        "schema_version": OPERATOR_DEMO_CARD_VERSION,
        "demo_id": f"{OPERATOR_DEMO_STATE_ID}:{surface.surface_id}",
        "surface_id": surface.surface_id,
        "surface_kind": surface.surface_kind,
        "display_name": surface.display_name,
        "purpose": surface.purpose,
        "operator_test_label": (
            f"{surface.display_name} operator-testable contract fixture"
        ),
        "availability_state": OperatorDemoAvailabilityState.OPERATOR_TESTABLE,
        "truth_label": SurfaceTruthLabel.DEV_FIXTURE,
        "fixture_kind": SurfaceFixtureKind.DEV_FIXTURE,
        "source": "p2_0_e_operator_demo_contract_fixture",
        "scope": "operator_demo_surface_card_contract_only",
        "expires_or_boundary": "not_live_no_ui_no_runtime_mutation",
        "permission_summary": _permission_summary_for(permission_matrix, surface),
        "unavailable_state": unavailable_state,
        "demo_is_operator_testable": True,
        "demo_is_dev_fixture": True,
        "demo_is_live": False,
        "executes_action": False,
        "mutates_runtime": False,
        "writes_memory": False,
        "writes_trace": False,
        "creates_ui": False,
        "non_goals": _OPERATOR_DEMO_NON_GOALS,
    }
    card = OperatorDemoSurfaceCard(**payload, card_hash=_hash_payload(payload))
    assert_operator_demo_is_not_live(card)
    assert_operator_demo_does_not_execute(card)
    assert_operator_demo_does_not_mutate_runtime(card)
    return card


def build_operator_testable_surface_demo_state(
    registry: AurelSurfaceRegistry | None = None,
) -> OperatorTestableSurfaceDemoState:
    if registry is None:
        registry = build_default_surface_registry()
    permission_matrix = build_default_surface_permission_matrix(registry)
    cards = tuple(
        build_operator_demo_surface_card(
            surface,
            permission_matrix=permission_matrix,
        )
        for surface in registry.surfaces
    )
    payload = {
        "schema_version": OPERATOR_DEMO_STATE_VERSION,
        "demo_id": OPERATOR_DEMO_STATE_ID,
        "cards": cards,
        "surface_count": len(cards),
        "canonical_surface_ids": registry.canonical_surface_ids,
        "truth_boundary": build_operator_demo_truth_boundary(),
        "unavailable_state_contract": build_surface_unavailable_state_contract(),
        "demo_state_exists": True,
        "demo_state_covers_all_surfaces": len(cards) == registry.surface_count == 7,
        "demo_state_is_operator_testable": True,
        "demo_state_is_dev_fixture": True,
        "demo_state_is_not_live": True,
        "demo_state_does_not_execute": True,
        "demo_state_does_not_mutate_runtime": True,
        "demo_state_does_not_write_memory": True,
        "demo_state_does_not_write_trace": True,
        "demo_state_does_not_create_ui": True,
        "non_goals": _OPERATOR_DEMO_NON_GOALS,
    }
    state = OperatorTestableSurfaceDemoState(
        **payload,
        state_hash=_hash_payload(payload),
    )
    assert_operator_demo_covers_all_surfaces(state)
    return state


def assert_operator_demo_is_not_live(
    demo: OperatorTestableSurfaceDemoState | OperatorDemoSurfaceCard,
) -> None:
    if isinstance(demo, OperatorTestableSurfaceDemoState):
        if not demo.demo_state_is_not_live:
            _reject(
                "operator demo state must be not live",
                field="demo_state_is_not_live",
                code=AurelShellErrorCode.INVALID_TRUTH_LABEL,
            )
        cards = demo.cards
    else:
        cards = (demo,)
    for card in cards:
        if card.demo_is_live or card.truth_label is SurfaceTruthLabel.LIVE:
            _reject(
                "operator demo card must not be LIVE",
                field="demo_is_live",
                code=AurelShellErrorCode.INVALID_TRUTH_LABEL,
            )


def assert_operator_demo_covers_all_surfaces(
    state: OperatorTestableSurfaceDemoState,
) -> None:
    if state.surface_count != 7 or not state.demo_state_covers_all_surfaces:
        _reject(
            "operator demo state must cover all seven canonical surfaces",
            field="surface_count",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_operator_demo_does_not_execute(
    demo: OperatorTestableSurfaceDemoState | OperatorDemoSurfaceCard,
) -> None:
    if isinstance(demo, OperatorTestableSurfaceDemoState):
        if not demo.demo_state_does_not_execute:
            _reject(
                "operator demo state must not execute",
                field="demo_state_does_not_execute",
                code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
            )
        cards = demo.cards
    else:
        cards = (demo,)
    for card in cards:
        if card.executes_action:
            _reject(
                "operator demo card must not execute",
                field="executes_action",
                code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
            )


def assert_operator_demo_does_not_mutate_runtime(
    demo: OperatorTestableSurfaceDemoState | OperatorDemoSurfaceCard,
) -> None:
    if isinstance(demo, OperatorTestableSurfaceDemoState):
        if not demo.demo_state_does_not_mutate_runtime:
            _reject(
                "operator demo state must not mutate runtime",
                field="demo_state_does_not_mutate_runtime",
                code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
            )
        cards = demo.cards
    else:
        cards = (demo,)
    for card in cards:
        if card.mutates_runtime or card.writes_memory or card.writes_trace:
            _reject(
                "operator demo card must not mutate runtime, memory, or trace",
                field="mutates_runtime",
                code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
            )
