"""AurelShell navigation boundary contracts (P2.0-B / P2.0.9–P2.0.10).

Contract-only navigation semantics: no universal left nav, per-surface local
nav boundaries, Aurel Logo → CRO route binding. Navigation is not permission.

Architectural law:
  - Navigation is capability-neutral addressing.
  - Route binding is contract, not runtime.
  - No UI, route runtime, or topbar in this pack.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .contracts import (
    AurelShellErrorCode,
    AurelShellValidationError,
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

AUREL_NAV_BOUNDARY_VERSION = "aurel_nav_boundary.v1"
AUREL_LOGO_ROUTE_BINDING_VERSION = "aurel_logo_route_binding.v1"

AUREL_LOGO_SOURCE = "AUREL_LOGO"


class NavigationBoundaryTruthLabel(str, Enum):
    CONTRACT_ONLY = "CONTRACT_ONLY"
    BOUNDARY_CONTRACT_ONLY = "BOUNDARY_CONTRACT_ONLY"
    ROUTE_CONTRACT_ONLY = "ROUTE_CONTRACT_ONLY"
    ROUTE_HINT_ONLY = "ROUTE_HINT_ONLY"
    NOT_LIVE = "NOT_LIVE"
    UNAVAILABLE = "UNAVAILABLE"


class RouteBindingTruthLabel(str, Enum):
    ROUTE_CONTRACT_ONLY = "ROUTE_CONTRACT_ONLY"
    ROUTE_HINT_ONLY = "ROUTE_HINT_ONLY"
    NOT_LIVE = "NOT_LIVE"


FORBIDDEN_NAV_TRUTH_LABELS: frozenset[str] = frozenset(
    {
        "LIVE",
        "ROUTE_LIVE",
        "NAVIGATION_LIVE",
        "UI_LIVE",
        "RUNTIME_ROUTE_ACTIVE",
        "GLOBAL_LEFT_NAV_ACTIVE",
        "ROOT_ACCESS_GRANTED",
    }
)


@dataclass(frozen=True)
class NoUniversalLeftNavContract(_CanonicalMixin):
    """P2.0.9 — forbids universal left navigation model."""

    schema_version: str
    global_left_nav_allowed: bool
    per_surface_nav_required: bool
    surface_nav_is_local: bool
    surface_nav_does_not_grant_authority: bool
    surface_nav_does_not_own_truth: bool
    route_runtime_created: bool
    truth_label: NavigationBoundaryTruthLabel
    unavailable_reason: str
    non_goals: tuple[str, ...]
    contract_hash: str


@dataclass(frozen=True)
class SurfaceNavigationBoundary(_CanonicalMixin):
    """Per-surface local navigation boundary."""

    schema_version: str
    surface_id: str
    surface_kind: AurelSurfaceKind
    local_nav_required: bool
    local_nav_boundary: str
    global_left_nav_allowed: bool
    navigation_grants_permission: bool
    navigation_owns_truth: bool
    route_runtime_created: bool
    truth_label: NavigationBoundaryTruthLabel
    unavailable_reason: str
    non_goals: tuple[str, ...]
    boundary_hash: str


@dataclass(frozen=True)
class PerSurfaceNavigationBoundary(_CanonicalMixin):
    """P2.0.9 container — no universal left nav + per-surface boundaries."""

    schema_version: str
    no_universal_left_nav: NoUniversalLeftNavContract
    surface_boundaries: tuple[SurfaceNavigationBoundary, ...]
    surface_count: int
    pack_hash: str


@dataclass(frozen=True)
class LogoRouteTarget(_CanonicalMixin):
    """Logo route target descriptor."""

    surface_kind: AurelSurfaceKind
    surface_id: str
    display_name: str


@dataclass(frozen=True)
class AurelLogoRouteBinding(_CanonicalMixin):
    """P2.0.10 — Aurel Logo routes to Aurel CRO as contract/hint only."""

    schema_version: str
    source: str
    target: LogoRouteTarget
    target_is_system: bool
    target_is_settings: bool
    grants_root_access: bool
    route_runtime_created: bool
    truth_label: RouteBindingTruthLabel
    secondary_truth_labels: tuple[RouteBindingTruthLabel, ...]
    unavailable_reason: str
    non_goals: tuple[str, ...]
    binding_hash: str


_NAV_NON_GOALS: tuple[str, ...] = (
    "no_sidebar",
    "no_actual_local_nav",
    "no_topbar",
    "no_route_switching",
    "no_route_runtime",
)

_LOGO_NON_GOALS: tuple[str, ...] = (
    "no_actual_route_runtime",
    "no_frontend_route",
    "no_topbar_implementation",
    "no_click_behavior",
)


def build_no_universal_left_nav_contract() -> NoUniversalLeftNavContract:
    payload = {
        "schema_version": AUREL_NAV_BOUNDARY_VERSION,
        "global_left_nav_allowed": False,
        "per_surface_nav_required": True,
        "surface_nav_is_local": True,
        "surface_nav_does_not_grant_authority": True,
        "surface_nav_does_not_own_truth": True,
        "route_runtime_created": False,
        "truth_label": NavigationBoundaryTruthLabel.BOUNDARY_CONTRACT_ONLY,
        "unavailable_reason": "navigation_boundary_contract_only_no_ui_or_runtime",
        "non_goals": _NAV_NON_GOALS,
    }
    return NoUniversalLeftNavContract(**payload, contract_hash=_hash_payload(payload))


def _build_surface_navigation_boundary(
    kind: AurelSurfaceKind,
) -> SurfaceNavigationBoundary:
    payload = {
        "schema_version": AUREL_NAV_BOUNDARY_VERSION,
        "surface_id": SURFACE_KIND_IDS[kind],
        "surface_kind": kind,
        "local_nav_required": True,
        "local_nav_boundary": f"local_nav_boundary_{SURFACE_KIND_IDS[kind]}",
        "global_left_nav_allowed": False,
        "navigation_grants_permission": False,
        "navigation_owns_truth": False,
        "route_runtime_created": False,
        "truth_label": NavigationBoundaryTruthLabel.BOUNDARY_CONTRACT_ONLY,
        "unavailable_reason": "local_nav_boundary_contract_only",
        "non_goals": _NAV_NON_GOALS,
    }
    return SurfaceNavigationBoundary(**payload, boundary_hash=_hash_payload(payload))


def build_per_surface_navigation_boundaries(
    registry: AurelSurfaceRegistry | None = None,
) -> PerSurfaceNavigationBoundary:
    if registry is None:
        registry = build_default_surface_registry()
    no_universal = build_no_universal_left_nav_contract()
    surface_boundaries = tuple(
        _build_surface_navigation_boundary(surface.surface_kind)
        for surface in registry.surfaces
    )
    payload = {
        "schema_version": AUREL_NAV_BOUNDARY_VERSION,
        "no_universal_left_nav": no_universal,
        "surface_boundaries": surface_boundaries,
        "surface_count": len(surface_boundaries),
    }
    return PerSurfaceNavigationBoundary(**payload, pack_hash=_hash_payload(payload))


def build_aurel_logo_route_binding() -> AurelLogoRouteBinding:
    target = LogoRouteTarget(
        surface_kind=AurelSurfaceKind.AUREL_CRO,
        surface_id=SURFACE_KIND_IDS[AurelSurfaceKind.AUREL_CRO],
        display_name="Aurel CRO",
    )
    payload = {
        "schema_version": AUREL_LOGO_ROUTE_BINDING_VERSION,
        "source": AUREL_LOGO_SOURCE,
        "target": target,
        "target_is_system": False,
        "target_is_settings": False,
        "grants_root_access": False,
        "route_runtime_created": False,
        "truth_label": RouteBindingTruthLabel.ROUTE_CONTRACT_ONLY,
        "secondary_truth_labels": (RouteBindingTruthLabel.ROUTE_HINT_ONLY,),
        "unavailable_reason": "logo_route_binding_contract_only_no_runtime",
        "non_goals": _LOGO_NON_GOALS,
    }
    return AurelLogoRouteBinding(**payload, binding_hash=_hash_payload(payload))


def assert_no_universal_left_nav(contract: NoUniversalLeftNavContract) -> None:
    if contract.global_left_nav_allowed:
        _reject(
            "universal left nav is forbidden",
            field="global_left_nav_allowed",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if contract.route_runtime_created:
        _reject(
            "route runtime must not be created in P2.0-B",
            field="route_runtime_created",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )
    if contract.truth_label.value in FORBIDDEN_NAV_TRUTH_LABELS:
        _reject(
            f"forbidden navigation truth label: {contract.truth_label.value}",
            field="truth_label",
            code=AurelShellErrorCode.INVALID_TRUTH_LABEL,
        )


def assert_each_surface_has_local_nav_boundary(
    pack: PerSurfaceNavigationBoundary,
    *,
    expected_count: int = 7,
) -> None:
    if pack.surface_count != expected_count:
        _reject(
            f"expected {expected_count} surface nav boundaries, got {pack.surface_count}",
            field="surface_count",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    for boundary in pack.surface_boundaries:
        if not boundary.local_nav_required:
            _reject(
                f"surface {boundary.surface_id} must require local nav",
                field="local_nav_required",
                code=AurelShellErrorCode.VALIDATION_ERROR,
            )
        if boundary.global_left_nav_allowed:
            _reject(
                f"surface {boundary.surface_id} must forbid global left nav",
                field="global_left_nav_allowed",
                code=AurelShellErrorCode.VALIDATION_ERROR,
            )


def assert_navigation_does_not_grant_permission(
    boundary: SurfaceNavigationBoundary,
) -> None:
    if boundary.navigation_grants_permission:
        _reject(
            f"navigation for {boundary.surface_id} must not grant permission",
            field="navigation_grants_permission",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_surface_nav_does_not_own_truth(
    boundary: SurfaceNavigationBoundary,
) -> None:
    if boundary.navigation_owns_truth:
        _reject(
            f"navigation for {boundary.surface_id} must not own truth",
            field="navigation_owns_truth",
            code=AurelShellErrorCode.SOURCE_OF_TRUTH_VIOLATION,
        )


def assert_logo_routes_to_cro_only(binding: AurelLogoRouteBinding) -> None:
    if binding.target.surface_kind != AurelSurfaceKind.AUREL_CRO:
        _reject(
            "Aurel Logo must route to Aurel CRO",
            field="target.surface_kind",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_logo_does_not_route_to_system(binding: AurelLogoRouteBinding) -> None:
    if binding.target.surface_kind == AurelSurfaceKind.SYSTEM:
        _reject(
            "Aurel Logo must not route to SYSTEM",
            field="target.surface_kind",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if binding.target_is_system:
        _reject(
            "Aurel Logo target_is_system must be false",
            field="target_is_system",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_logo_does_not_grant_root(binding: AurelLogoRouteBinding) -> None:
    if binding.grants_root_access:
        _reject(
            "Aurel Logo must not grant root access",
            field="grants_root_access",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_no_navigation_runtime_created(
    contract: NoUniversalLeftNavContract,
) -> None:
    if contract.route_runtime_created:
        _reject(
            "navigation route runtime must not be created",
            field="route_runtime_created",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )
