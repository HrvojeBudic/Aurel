"""AurelShell unavailable-state contracts (P2.0-D / P2.0.20).

Unavailable states are explicit operator information. They must state reason,
dependency, and next action, and they must not hide errors or claim LIVE.
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
from .truth_labels import SurfaceTruthLabel

AUREL_UNAVAILABLE_STATE_CONTRACT_VERSION = "aurel_unavailable_state_contract.v1"
AUREL_UNAVAILABLE_STATE_VERSION = "aurel_unavailable_state.v1"


class SurfaceUnavailableReason(str, Enum):
    MISSING_BACKEND_CAPABILITY = "MISSING_BACKEND_CAPABILITY"
    MISSING_RUNTIME_BINDING = "MISSING_RUNTIME_BINDING"
    MISSING_PERMISSION = "MISSING_PERMISSION"
    MISSING_OPERATOR_APPROVAL = "MISSING_OPERATOR_APPROVAL"
    MISSING_TRACE_PROOF = "MISSING_TRACE_PROOF"
    MISSING_LIVE_PATH = "MISSING_LIVE_PATH"
    NOT_IMPLEMENTED_YET = "NOT_IMPLEMENTED_YET"
    DISABLED_BY_POLICY = "DISABLED_BY_POLICY"
    DEPENDENCY_BLOCKED = "DEPENDENCY_BLOCKED"


class SurfaceUnavailableNextAction(str, Enum):
    KEEP_CONTRACT_ONLY = "KEEP_CONTRACT_ONLY"
    WAIT_FOR_BACKEND_CAPABILITY = "WAIT_FOR_BACKEND_CAPABILITY"
    REQUEST_OPERATOR_APPROVAL = "REQUEST_OPERATOR_APPROVAL"
    REQUEST_PERMISSION_REVIEW = "REQUEST_PERMISSION_REVIEW"
    REQUEST_TRACE_PROOF = "REQUEST_TRACE_PROOF"
    IMPLEMENT_LATER_PACK = "IMPLEMENT_LATER_PACK"
    CHECK_POLICY = "CHECK_POLICY"
    UNBLOCK_DEPENDENCY = "UNBLOCK_DEPENDENCY"


_UNAVAILABLE_NON_GOALS: tuple[str, ...] = (
    "no_automatic_repair",
    "no_backend_runtime_probe",
    "no_ui_error_rendering",
    "no_availability_monitor",
)


@dataclass(frozen=True)
class SurfaceUnavailableStateContract(_CanonicalMixin):
    """P2.0.20 contract: unavailable state must be visible and reasoned."""

    schema_version: str
    unavailable_state_has_reason: bool
    unavailable_state_has_next_action: bool
    unavailable_not_reported_as_live: bool
    unavailable_is_not_error_hiding: bool
    unavailable_is_operator_visible: bool
    truth_label: SurfaceTruthLabel
    non_goals: tuple[str, ...]
    contract_hash: str


@dataclass(frozen=True)
class SurfaceUnavailableState(_CanonicalMixin):
    """Explicit unavailable state for a surface."""

    schema_version: str
    surface_id: str
    surface_kind: AurelSurfaceKind
    unavailable_reason: SurfaceUnavailableReason
    operator_message: str
    next_action: SurfaceUnavailableNextAction
    is_live: bool
    is_error_hiding: bool
    is_operator_visible: bool
    dependency: str
    truth_label: SurfaceTruthLabel
    non_goals: tuple[str, ...]
    state_hash: str


def build_surface_unavailable_state_contract() -> SurfaceUnavailableStateContract:
    payload = {
        "schema_version": AUREL_UNAVAILABLE_STATE_CONTRACT_VERSION,
        "unavailable_state_has_reason": True,
        "unavailable_state_has_next_action": True,
        "unavailable_not_reported_as_live": True,
        "unavailable_is_not_error_hiding": True,
        "unavailable_is_operator_visible": True,
        "truth_label": SurfaceTruthLabel.UNAVAILABLE_STATE_CONTRACT_ONLY,
        "non_goals": _UNAVAILABLE_NON_GOALS,
    }
    return SurfaceUnavailableStateContract(
        **payload,
        contract_hash=_hash_payload(payload),
    )


def build_surface_unavailable_state(
    *,
    surface_kind: AurelSurfaceKind | str = AurelSurfaceKind.AUREL_CRO,
    unavailable_reason: SurfaceUnavailableReason | str | None = (
        SurfaceUnavailableReason.NOT_IMPLEMENTED_YET
    ),
    operator_message: str = "Surface state is unavailable in this contract layer.",
    next_action: SurfaceUnavailableNextAction | str | None = (
        SurfaceUnavailableNextAction.KEEP_CONTRACT_ONLY
    ),
    dependency: str = "live_surface_runtime",
) -> SurfaceUnavailableState:
    if isinstance(surface_kind, str):
        surface_kind = AurelSurfaceKind(surface_kind)
    if unavailable_reason is None:
        _reject(
            "UNAVAILABLE state requires a reason",
            field="unavailable_reason",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if isinstance(unavailable_reason, str):
        unavailable_reason = SurfaceUnavailableReason(unavailable_reason)
    if next_action is None:
        _reject(
            "UNAVAILABLE state requires a next action",
            field="next_action",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if isinstance(next_action, str):
        next_action = SurfaceUnavailableNextAction(next_action)
    payload = {
        "schema_version": AUREL_UNAVAILABLE_STATE_VERSION,
        "surface_id": SURFACE_KIND_IDS[surface_kind],
        "surface_kind": surface_kind,
        "unavailable_reason": unavailable_reason,
        "operator_message": operator_message,
        "next_action": next_action,
        "is_live": False,
        "is_error_hiding": False,
        "is_operator_visible": True,
        "dependency": dependency,
        "truth_label": SurfaceTruthLabel.UNAVAILABLE,
        "non_goals": _UNAVAILABLE_NON_GOALS,
    }
    state = SurfaceUnavailableState(**payload, state_hash=_hash_payload(payload))
    assert_unavailable_has_reason_and_next_action(state)
    assert_unavailable_is_not_live(state)
    assert_unavailable_is_not_error_hiding(state)
    assert_unavailable_is_operator_visible(state)
    return state


def assert_unavailable_has_reason_and_next_action(
    state: SurfaceUnavailableState,
) -> None:
    if not state.unavailable_reason:
        _reject(
            "UNAVAILABLE state requires a reason",
            field="unavailable_reason",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if not state.next_action:
        _reject(
            "UNAVAILABLE state requires a next action",
            field="next_action",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_unavailable_is_not_live(state: SurfaceUnavailableState) -> None:
    if state.is_live or state.truth_label is SurfaceTruthLabel.LIVE:
        _reject(
            "UNAVAILABLE state must not be LIVE",
            field="is_live",
            code=AurelShellErrorCode.INVALID_TRUTH_LABEL,
        )


def assert_unavailable_is_not_error_hiding(
    state: SurfaceUnavailableState,
) -> None:
    if state.is_error_hiding:
        _reject(
            "UNAVAILABLE state must not hide ERROR",
            field="is_error_hiding",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_unavailable_is_operator_visible(
    state: SurfaceUnavailableState,
) -> None:
    if not state.is_operator_visible:
        _reject(
            "UNAVAILABLE state must be operator-visible",
            field="is_operator_visible",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
