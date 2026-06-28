"""P2.0-E multi-client consistency contracts.

Future clients must project the same shell contracts. This module does not
create web, desktop, mobile, CLI, or TUI clients.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .contracts import AurelShellErrorCode, _CanonicalMixin, _hash_payload, _reject
from .surface_registry import (
    AurelSurfaceRegistry,
    build_default_surface_registry,
)

CLIENT_CONSISTENCY_CONTRACT_VERSION = "multi_client_consistency_contract.v1"
CLIENT_CONSISTENCY_EXPECTATION_VERSION = "client_consistency_expectation.v1"
CLIENT_PROJECTION_PARITY_RULE_VERSION = "client_projection_parity_rule.v1"


class ClientKind(str, Enum):
    WEB = "WEB"
    DESKTOP = "DESKTOP"
    MOBILE = "MOBILE"
    CLI = "CLI"
    TUI = "TUI"


_CLIENT_DISPLAY_NAMES: dict[ClientKind, str] = {
    ClientKind.WEB: "Web",
    ClientKind.DESKTOP: "Desktop",
    ClientKind.MOBILE: "Mobile",
    ClientKind.CLI: "CLI",
    ClientKind.TUI: "TUI",
}

_CLIENT_NON_GOALS: tuple[str, ...] = (
    "no_web_app_implementation",
    "no_tauri_desktop_implementation",
    "no_mobile_app_implementation",
    "no_cli_implementation",
    "no_tui_implementation",
    "no_client_runtime",
)


@dataclass(frozen=True)
class ClientProjectionParityRule(_CanonicalMixin):
    """Shared projection invariant for all future clients."""

    schema_version: str
    same_surface_registry: bool
    same_truth_labels: bool
    same_permission_meanings: bool
    same_unavailable_states: bool
    same_fixture_disclosures: bool
    same_snapshot_contract: bool
    rule_hash: str


@dataclass(frozen=True)
class ClientConsistencyExpectation(_CanonicalMixin):
    """Per-client projection expectation; not a client implementation."""

    schema_version: str
    client_kind: ClientKind
    client_display_name: str
    same_surface_registry: bool
    same_truth_labels: bool
    same_permission_meanings: bool
    same_unavailable_states: bool
    same_fixture_disclosures: bool
    same_snapshot_contract: bool
    creates_client: bool
    implements_ui: bool
    implements_cli: bool
    implements_runtime: bool
    truth_label: str
    non_goals: tuple[str, ...]
    expectation_hash: str


@dataclass(frozen=True)
class MultiClientConsistencyContract(_CanonicalMixin):
    """P2.0.23 contract for future client projection parity."""

    schema_version: str
    expectations: tuple[ClientConsistencyExpectation, ...]
    client_kinds: tuple[ClientKind, ...]
    projection_parity_rule: ClientProjectionParityRule
    canonical_surface_ids: tuple[str, ...]
    creates_clients: bool
    implements_ui: bool
    implements_cli: bool
    implements_runtime: bool
    truth_label: str
    non_goals: tuple[str, ...]
    contract_hash: str


def build_client_projection_parity_rule() -> ClientProjectionParityRule:
    payload = {
        "schema_version": CLIENT_PROJECTION_PARITY_RULE_VERSION,
        "same_surface_registry": True,
        "same_truth_labels": True,
        "same_permission_meanings": True,
        "same_unavailable_states": True,
        "same_fixture_disclosures": True,
        "same_snapshot_contract": True,
    }
    return ClientProjectionParityRule(**payload, rule_hash=_hash_payload(payload))


def _build_client_consistency_expectation(
    client_kind: ClientKind,
) -> ClientConsistencyExpectation:
    implements_cli = False
    payload = {
        "schema_version": CLIENT_CONSISTENCY_EXPECTATION_VERSION,
        "client_kind": client_kind,
        "client_display_name": _CLIENT_DISPLAY_NAMES[client_kind],
        "same_surface_registry": True,
        "same_truth_labels": True,
        "same_permission_meanings": True,
        "same_unavailable_states": True,
        "same_fixture_disclosures": True,
        "same_snapshot_contract": True,
        "creates_client": False,
        "implements_ui": False,
        "implements_cli": implements_cli,
        "implements_runtime": False,
        "truth_label": "CLIENT_CONSISTENCY_CONTRACT_ONLY",
        "non_goals": _CLIENT_NON_GOALS,
    }
    return ClientConsistencyExpectation(
        **payload,
        expectation_hash=_hash_payload(payload),
    )


def build_multi_client_consistency_contract(
    registry: AurelSurfaceRegistry | None = None,
) -> MultiClientConsistencyContract:
    if registry is None:
        registry = build_default_surface_registry()
    expectations = tuple(
        _build_client_consistency_expectation(client_kind)
        for client_kind in tuple(ClientKind)
    )
    payload = {
        "schema_version": CLIENT_CONSISTENCY_CONTRACT_VERSION,
        "expectations": expectations,
        "client_kinds": tuple(ClientKind),
        "projection_parity_rule": build_client_projection_parity_rule(),
        "canonical_surface_ids": registry.canonical_surface_ids,
        "creates_clients": False,
        "implements_ui": False,
        "implements_cli": False,
        "implements_runtime": False,
        "truth_label": "CLIENT_CONSISTENCY_CONTRACT_ONLY",
        "non_goals": _CLIENT_NON_GOALS,
    }
    contract = MultiClientConsistencyContract(
        **payload,
        contract_hash=_hash_payload(payload),
    )
    assert_client_consistency_does_not_create_clients(contract)
    assert_clients_share_same_registry_truth_permission_unavailable_fixture_contracts(
        contract
    )
    return contract


def assert_client_consistency_does_not_create_clients(
    contract: MultiClientConsistencyContract,
) -> None:
    if contract.creates_clients or contract.implements_ui or contract.implements_runtime:
        _reject(
            "multi-client consistency contract must not create clients or UI",
            field="creates_clients",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )
    if contract.implements_cli:
        _reject(
            "multi-client consistency contract must not implement CLI/TUI",
            field="implements_cli",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )
    for expectation in contract.expectations:
        if (
            expectation.creates_client
            or expectation.implements_ui
            or expectation.implements_cli
            or expectation.implements_runtime
        ):
            _reject(
                f"{expectation.client_kind.value} expectation must not implement client",
                field="expectations",
                code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
            )


def assert_clients_share_same_registry_truth_permission_unavailable_fixture_contracts(
    contract: MultiClientConsistencyContract,
) -> None:
    for expectation in contract.expectations:
        if not (
            expectation.same_surface_registry
            and expectation.same_truth_labels
            and expectation.same_permission_meanings
            and expectation.same_unavailable_states
            and expectation.same_fixture_disclosures
            and expectation.same_snapshot_contract
        ):
            _reject(
                f"{expectation.client_kind.value} parity expectation is incomplete",
                field="expectations",
                code=AurelShellErrorCode.VALIDATION_ERROR,
            )
