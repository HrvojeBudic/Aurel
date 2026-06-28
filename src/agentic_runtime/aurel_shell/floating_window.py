"""AurelShell floating window shared contract (P2.0-C / P2.0.15).

Contract-only floating window descriptors. Floating windows are ephemeral
shell projection containers — not runtime sessions, source of truth, or live UI.

Architectural law:
  - Floating window is not runtime session.
  - Floating window is not source of truth.
  - Floating window does not execute actions.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .contracts import (
    AurelShellErrorCode,
    _CanonicalMixin,
    _hash_payload,
    _reject,
)
from .surface_registry import AurelSurfaceKind, SURFACE_KIND_IDS

AUREL_FLOATING_WINDOW_CONTRACT_VERSION = "aurel_floating_window_contract.v1"
AUREL_FLOATING_WINDOW_DESCRIPTOR_VERSION = "aurel_floating_window_descriptor.v1"

DEV_FIXTURE_WINDOW_ID = "dev_fixture_floating_window_001"


class FloatingWindowTruthLabel(str, Enum):
    CONTRACT_ONLY = "CONTRACT_ONLY"
    FLOATING_WINDOW_CONTRACT_ONLY = "FLOATING_WINDOW_CONTRACT_ONLY"
    DEV_FIXTURE = "DEV_FIXTURE"
    NOT_LIVE = "NOT_LIVE"
    UNAVAILABLE = "UNAVAILABLE"


class FloatingWindowKind(str, Enum):
    """Declared floating window category — contract only."""

    SHELL_PROJECTION_CONTAINER = "shell_projection_container"
    CONTEXT_VIEW = "context_view"
    INSPECT_PANEL = "inspect_panel"


class FloatingWindowScope(str, Enum):
    """Scope boundary for a floating window descriptor."""

    SURFACE_LOCAL = "surface_local"
    CROSS_SURFACE_VIEW = "cross_surface_view"
    DEV_FIXTURE = "dev_fixture"


class FloatingWindowAvailability(str, Enum):
    CONTRACT_ONLY = "CONTRACT_ONLY"
    UNAVAILABLE = "UNAVAILABLE"


_FLOATING_WINDOW_NON_GOALS: tuple[str, ...] = (
    "no_draggable_ui",
    "no_modal_ui",
    "no_window_manager",
    "no_live_shell_window",
    "no_runtime_session",
)


@dataclass(frozen=True)
class FloatingWindowSharedContract(_CanonicalMixin):
    """P2.0.15 — shared floating window contract foundation."""

    schema_version: str
    is_shell_container: bool
    owns_truth: bool
    mutates_runtime: bool
    executes_actions: bool
    is_live_ui: bool
    truth_label: FloatingWindowTruthLabel
    unavailable_reason: str
    non_goals: tuple[str, ...]
    contract_hash: str


@dataclass(frozen=True)
class FloatingWindowDescriptor(_CanonicalMixin):
    """Floating window descriptor — contract/read model only."""

    schema_version: str
    window_id: str
    window_kind: FloatingWindowKind
    owning_surface_id: str
    source_surface_id: str
    target_surface_id_optional: str | None
    scope: FloatingWindowScope
    title: str
    purpose: str
    payload_refs: tuple[str, ...]
    truth_label: FloatingWindowTruthLabel
    availability: FloatingWindowAvailability
    unavailable_reason: str
    is_shell_container: bool
    owns_truth: bool
    mutates_runtime: bool
    executes_actions: bool
    is_live_ui: bool
    is_dev_fixture: bool
    non_goals: tuple[str, ...]
    descriptor_hash: str


def build_floating_window_shared_contract() -> FloatingWindowSharedContract:
    payload = {
        "schema_version": AUREL_FLOATING_WINDOW_CONTRACT_VERSION,
        "is_shell_container": True,
        "owns_truth": False,
        "mutates_runtime": False,
        "executes_actions": False,
        "is_live_ui": False,
        "truth_label": FloatingWindowTruthLabel.FLOATING_WINDOW_CONTRACT_ONLY,
        "unavailable_reason": "floating_window_contract_only_no_ui_or_runtime",
        "non_goals": _FLOATING_WINDOW_NON_GOALS,
    }
    return FloatingWindowSharedContract(**payload, contract_hash=_hash_payload(payload))


def build_dev_fixture_floating_window_descriptor() -> FloatingWindowDescriptor:
    owning = SURFACE_KIND_IDS[AurelSurfaceKind.HQ]
    source = SURFACE_KIND_IDS[AurelSurfaceKind.AUREL_CRO]
    payload = {
        "schema_version": AUREL_FLOATING_WINDOW_DESCRIPTOR_VERSION,
        "window_id": DEV_FIXTURE_WINDOW_ID,
        "window_kind": FloatingWindowKind.CONTEXT_VIEW,
        "owning_surface_id": owning,
        "source_surface_id": source,
        "target_surface_id_optional": owning,
        "scope": FloatingWindowScope.DEV_FIXTURE,
        "title": "DEV_FIXTURE Operations Context View",
        "purpose": (
            "Contract-only floating window descriptor for cross-surface "
            "context inspection — not a live UI window"
        ),
        "payload_refs": ("dev_fixture:context_view_ref_001",),
        "truth_label": FloatingWindowTruthLabel.DEV_FIXTURE,
        "availability": FloatingWindowAvailability.CONTRACT_ONLY,
        "unavailable_reason": "dev_fixture_floating_window_descriptor_only",
        "is_shell_container": True,
        "owns_truth": False,
        "mutates_runtime": False,
        "executes_actions": False,
        "is_live_ui": False,
        "is_dev_fixture": True,
        "non_goals": _FLOATING_WINDOW_NON_GOALS,
    }
    return FloatingWindowDescriptor(**payload, descriptor_hash=_hash_payload(payload))


def assert_floating_window_does_not_own_truth(
    descriptor: FloatingWindowDescriptor,
) -> None:
    if descriptor.owns_truth:
        _reject(
            "floating window must not own truth",
            field="owns_truth",
            code=AurelShellErrorCode.SOURCE_OF_TRUTH_VIOLATION,
        )


def assert_floating_window_does_not_execute(
    descriptor: FloatingWindowDescriptor,
) -> None:
    if descriptor.executes_actions:
        _reject(
            "floating window must not execute actions",
            field="executes_actions",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_floating_window_does_not_mutate_runtime(
    descriptor: FloatingWindowDescriptor,
) -> None:
    if descriptor.mutates_runtime:
        _reject(
            "floating window must not mutate runtime",
            field="mutates_runtime",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_floating_window_is_not_live_ui(
    descriptor: FloatingWindowDescriptor,
) -> None:
    if descriptor.is_live_ui:
        _reject(
            "floating window must not be live UI",
            field="is_live_ui",
            code=AurelShellErrorCode.INVALID_TRUTH_LABEL,
        )
