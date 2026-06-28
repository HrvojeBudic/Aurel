"""AurelShell fixture/mock/simulated disclosure contracts (P2.0-D / P2.0.21).

DEV_FIXTURE, MOCK, and SIMULATED states are provenance disclosures. They require
visible labels, source, and scope or expiry/boundary, and cannot be production
truth or LIVE.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TypeVar

from .contracts import (
    AurelShellErrorCode,
    _CanonicalMixin,
    _hash_payload,
    _reject,
)
from .surface_registry import AurelSurfaceKind, SURFACE_KIND_IDS
from .truth_labels import SurfaceTruthLabel

AUREL_FIXTURE_DISCIPLINE_CONTRACT_VERSION = "aurel_fixture_discipline_contract.v1"
AUREL_FIXTURE_DISCLOSURE_VERSION = "aurel_fixture_disclosure.v1"


class SurfaceFixtureKind(str, Enum):
    DEV_FIXTURE = "DEV_FIXTURE"
    MOCK = "MOCK"
    SIMULATED = "SIMULATED"


_FIXTURE_NON_GOALS: tuple[str, ...] = (
    "no_demo_ui",
    "no_production_data",
    "no_real_business_sample_data",
    "no_fake_product_state",
)


@dataclass(frozen=True)
class SurfaceFixtureDisciplineContract(_CanonicalMixin):
    """P2.0.21 contract: fixture-like states must be visibly disclosed."""

    schema_version: str
    dev_fixture_must_be_labeled: bool
    mock_must_be_labeled: bool
    simulated_must_be_labeled: bool
    fixture_not_live: bool
    mock_not_live: bool
    simulated_not_live: bool
    fixture_requires_source: bool
    fixture_requires_scope_or_expiry: bool
    truth_label: SurfaceTruthLabel
    non_goals: tuple[str, ...]
    contract_hash: str


@dataclass(frozen=True)
class SurfaceFixtureDisclosure(_CanonicalMixin):
    """Base disclosure for DEV_FIXTURE/MOCK/SIMULATED surface state."""

    schema_version: str
    surface_id: str
    surface_kind: AurelSurfaceKind
    fixture_kind: SurfaceFixtureKind
    source: str
    scope: str
    expires_or_boundary: str
    truth_label: SurfaceTruthLabel
    is_live: bool
    is_production_data: bool
    requires_visible_label: bool
    can_be_used_as_truth: bool
    non_goals: tuple[str, ...]
    disclosure_hash: str


@dataclass(frozen=True)
class SurfaceDevFixtureDisclosure(SurfaceFixtureDisclosure):
    """DEV_FIXTURE disclosure."""


@dataclass(frozen=True)
class SurfaceMockDisclosure(SurfaceFixtureDisclosure):
    """MOCK disclosure."""


@dataclass(frozen=True)
class SurfaceSimulatedDisclosure(SurfaceFixtureDisclosure):
    """SIMULATED disclosure."""


FixtureDisclosureT = TypeVar("FixtureDisclosureT", bound=SurfaceFixtureDisclosure)


def build_surface_fixture_discipline_contract() -> SurfaceFixtureDisciplineContract:
    payload = {
        "schema_version": AUREL_FIXTURE_DISCIPLINE_CONTRACT_VERSION,
        "dev_fixture_must_be_labeled": True,
        "mock_must_be_labeled": True,
        "simulated_must_be_labeled": True,
        "fixture_not_live": True,
        "mock_not_live": True,
        "simulated_not_live": True,
        "fixture_requires_source": True,
        "fixture_requires_scope_or_expiry": True,
        "truth_label": SurfaceTruthLabel.FIXTURE_DISCLOSURE_ONLY,
        "non_goals": _FIXTURE_NON_GOALS,
    }
    return SurfaceFixtureDisciplineContract(
        **payload,
        contract_hash=_hash_payload(payload),
    )


def _truth_label_for_fixture_kind(kind: SurfaceFixtureKind) -> SurfaceTruthLabel:
    if kind is SurfaceFixtureKind.DEV_FIXTURE:
        return SurfaceTruthLabel.DEV_FIXTURE
    if kind is SurfaceFixtureKind.MOCK:
        return SurfaceTruthLabel.MOCK
    return SurfaceTruthLabel.SIMULATED


def _build_fixture_disclosure(
    *,
    disclosure_type: type[FixtureDisclosureT],
    surface_kind: AurelSurfaceKind | str,
    fixture_kind: SurfaceFixtureKind,
    source: str,
    scope: str,
    expires_or_boundary: str,
) -> FixtureDisclosureT:
    if isinstance(surface_kind, str):
        surface_kind = AurelSurfaceKind(surface_kind)
    payload = {
        "schema_version": AUREL_FIXTURE_DISCLOSURE_VERSION,
        "surface_id": SURFACE_KIND_IDS[surface_kind],
        "surface_kind": surface_kind,
        "fixture_kind": fixture_kind,
        "source": source,
        "scope": scope,
        "expires_or_boundary": expires_or_boundary,
        "truth_label": _truth_label_for_fixture_kind(fixture_kind),
        "is_live": False,
        "is_production_data": False,
        "requires_visible_label": True,
        "can_be_used_as_truth": False,
        "non_goals": _FIXTURE_NON_GOALS,
    }
    disclosure = disclosure_type(**payload, disclosure_hash=_hash_payload(payload))
    assert_fixture_requires_source_scope_or_expiry(disclosure)
    assert_fixture_requires_visible_label(disclosure)
    assert_fixture_disclosure_not_live(disclosure)
    assert_fixture_disclosure_not_production_data(disclosure)
    return disclosure


def build_surface_dev_fixture_disclosure(
    *,
    surface_kind: AurelSurfaceKind | str = AurelSurfaceKind.AUREL_CRO,
    source: str = "p2_0_d_contract_test_disclosure",
    scope: str = "truth_permission_fixture_contract_tests",
    expires_or_boundary: str = "p2_0_d_contract_boundary_only",
) -> SurfaceDevFixtureDisclosure:
    return _build_fixture_disclosure(
        disclosure_type=SurfaceDevFixtureDisclosure,
        surface_kind=surface_kind,
        fixture_kind=SurfaceFixtureKind.DEV_FIXTURE,
        source=source,
        scope=scope,
        expires_or_boundary=expires_or_boundary,
    )


def build_surface_mock_disclosure(
    *,
    surface_kind: AurelSurfaceKind | str = AurelSurfaceKind.HUB,
    source: str = "p2_0_d_mock_contract_disclosure",
    scope: str = "truth_permission_fixture_contract_tests",
    expires_or_boundary: str = "p2_0_d_contract_boundary_only",
) -> SurfaceMockDisclosure:
    return _build_fixture_disclosure(
        disclosure_type=SurfaceMockDisclosure,
        surface_kind=surface_kind,
        fixture_kind=SurfaceFixtureKind.MOCK,
        source=source,
        scope=scope,
        expires_or_boundary=expires_or_boundary,
    )


def build_surface_simulated_disclosure(
    *,
    surface_kind: AurelSurfaceKind | str = AurelSurfaceKind.HQ,
    source: str = "p2_0_d_simulated_contract_disclosure",
    scope: str = "truth_permission_fixture_contract_tests",
    expires_or_boundary: str = "p2_0_d_contract_boundary_only",
) -> SurfaceSimulatedDisclosure:
    return _build_fixture_disclosure(
        disclosure_type=SurfaceSimulatedDisclosure,
        surface_kind=surface_kind,
        fixture_kind=SurfaceFixtureKind.SIMULATED,
        source=source,
        scope=scope,
        expires_or_boundary=expires_or_boundary,
    )


def assert_fixture_requires_source_scope_or_expiry(
    disclosure: SurfaceFixtureDisclosure,
) -> None:
    if not disclosure.source:
        _reject(
            "fixture/mock/simulated disclosure requires source",
            field="source",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if not disclosure.scope and not disclosure.expires_or_boundary:
        _reject(
            "fixture/mock/simulated disclosure requires scope or expiry/boundary",
            field="scope",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_fixture_requires_visible_label(
    disclosure: SurfaceFixtureDisclosure,
) -> None:
    if not disclosure.requires_visible_label:
        _reject(
            "fixture/mock/simulated disclosure requires visible label",
            field="requires_visible_label",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_fixture_disclosure_not_live(disclosure: SurfaceFixtureDisclosure) -> None:
    if disclosure.is_live or disclosure.truth_label is SurfaceTruthLabel.LIVE:
        _reject(
            "fixture/mock/simulated disclosure must not be LIVE",
            field="is_live",
            code=AurelShellErrorCode.INVALID_TRUTH_LABEL,
        )


def assert_fixture_disclosure_not_production_data(
    disclosure: SurfaceFixtureDisclosure,
) -> None:
    if disclosure.is_production_data or disclosure.can_be_used_as_truth:
        _reject(
            "fixture/mock/simulated disclosure must not be production truth",
            field="is_production_data",
            code=AurelShellErrorCode.INVALID_TRUTH_LABEL,
        )
