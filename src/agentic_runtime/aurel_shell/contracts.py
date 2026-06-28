"""AurelShell contract foundation (P2.0-A / P2.0.0–P2.0.1).

Contract-only shell layer: AurelShell reveals governed state but does not own
truth, execute commands, grant permission, or mutate runtime.

Architectural law:
  - AurelShell reveals; AurelShell does not own truth.
  - Shell contract is not product UI.
  - Shell contract is not runtime authority.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
from typing import Any

AUREL_SHELL_PACK_TASK_ID = "P2.0-A"
AUREL_SHELL_SECTION_ID = "P2.0"
AUREL_SHELL_PACK_CHECKPOINT_IDS = (
    "P2.0.0",
    "P2.0.1",
    "P2.0.2",
    "P2.0.3",
    "P2.0.4",
    "P2.0.5",
    "P2.0.6",
    "P2.0.7",
    "P2.0.8",
)
AUREL_SHELL_NEXT_PACK_ID = "P2.0-B"

AUREL_SHELL_CONTRACT_VERSION = "aurel_shell_contract.v1"
AUREL_SHELL_BOUNDARY_VERSION = "aurel_shell_boundary.v1"

AUREL_SHELL_ID = "aurel_shell"
AUREL_SHELL_DISPLAY_NAME = "AurelShell"


class AurelShellErrorCode(str, Enum):
    VALIDATION_ERROR = "validation_error"
    INVALID_TRUTH_LABEL = "invalid_truth_label"
    SOURCE_OF_TRUTH_VIOLATION = "source_of_truth_violation"
    EXECUTION_AUTHORITY_VIOLATION = "execution_authority_violation"


class AurelShellValidationError(ValueError):
    def __init__(
        self,
        message: str,
        *,
        code: AurelShellErrorCode = AurelShellErrorCode.VALIDATION_ERROR,
        field: str | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.field = field


class AurelShellRole(str, Enum):
    """Shell role — operator command skin, not source of truth."""

    OPERATOR_COMMAND_SKIN = "operator_command_skin"


class AurelShellTruthLabel(str, Enum):
    """Truth labels for AurelShell contract data."""

    CONTRACT_ONLY = "CONTRACT_ONLY"
    READ_MODEL_ONLY = "READ_MODEL_ONLY"
    PROJECTION_ONLY = "PROJECTION_ONLY"
    DEV_FIXTURE = "DEV_FIXTURE"
    NOT_LIVE = "NOT_LIVE"
    UNAVAILABLE = "UNAVAILABLE"


FORBIDDEN_SHELL_TRUTH_LABELS: frozenset[AurelShellTruthLabel] = frozenset(
    {
        AurelShellTruthLabel.UNAVAILABLE,
    }
)

STRONG_FORBIDDEN_SHELL_TRUTH_LABELS: frozenset[str] = frozenset(
    {
        "LIVE",
        "RUNTIME_AUTHORITY",
        "SOURCE_OF_TRUTH",
        "UI_LIVE",
        "ROUTE_LIVE",
        "P2_0_B_DONE",
        "P2_READY_FOR_CODING",
    }
)


AUREL_SHELL_NON_GOALS: tuple[str, ...] = (
    "no_product_ui",
    "no_runtime_shell",
    "no_navigation",
    "no_routes",
    "no_command_palette",
    "no_cli_tui_binding",
    "no_permission_matrix",
    "no_runtime_mutation",
)

AUREL_SHELL_INVARIANTS: tuple[str, ...] = (
    "shell_reveals_state",
    "shell_does_not_own_truth",
    "shell_does_not_execute",
    "shell_does_not_grant_permission",
    "shell_does_not_mutate_runtime",
    "shell_is_not_ui",
)


class _CanonicalMixin:
    def to_canonical_dict(self) -> dict[str, Any]:
        return _canonical_dataclass_dict(self)


@dataclass(frozen=True)
class AurelShellSideEffectProof(_CanonicalMixin):
    """Proof that P2.0-A performs no UI/runtime/authority side effects."""

    ui_created: bool = False
    route_created: bool = False
    global_topbar_created: bool = False
    local_navigation_created: bool = False
    floating_window_created: bool = False
    command_palette_created: bool = False
    cli_binding_created: bool = False
    tui_binding_created: bool = False
    permission_matrix_created: bool = False
    runtime_mutated: bool = False
    workflow_executed: bool = False
    tool_executed: bool = False
    business_action_executed: bool = False
    system_authority_granted: bool = False
    agent_system_access_granted: bool = False
    memory_written: bool = False
    ledger_written: bool = False
    global_trace_written: bool = False
    p2_0_b_started: bool = False
    p2_1_started: bool = False


@dataclass(frozen=True)
class AurelShellBoundary(_CanonicalMixin):
    """P2.0.1 operator command skin boundary."""

    schema_version: str
    reveals_state: bool
    owns_truth: bool
    executes_commands: bool
    grants_permission: bool
    mutates_runtime: bool
    boundary_hash: str


@dataclass(frozen=True)
class AurelShellContract(_CanonicalMixin):
    """P2.0.0–P2.0.1 AurelShell contract foundation."""

    schema_version: str
    shell_id: str
    display_name: str
    role: AurelShellRole
    purpose: str
    operator_value: str
    truth_label: AurelShellTruthLabel
    boundary: AurelShellBoundary
    non_goals: tuple[str, ...]
    invariants: tuple[str, ...]
    side_effects: AurelShellSideEffectProof
    shell_contract_hash: str


def _canonical_value(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return _canonical_dataclass_dict(value)
    if isinstance(value, Mapping):
        return {
            str(_canonical_value(key)): _canonical_value(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    if isinstance(value, (list, tuple)):
        return [_canonical_value(item) for item in value]
    return value


def _canonical_dataclass_dict(value: Any) -> dict[str, Any]:
    return {
        field.name: _canonical_value(getattr(value, field.name))
        for field in fields(value)
    }


def to_canonical_json(value: Any) -> str:
    return json.dumps(_canonical_value(value), sort_keys=True, separators=(",", ":"))


def stable_hash(value: Any) -> str:
    payload = to_canonical_json(value)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _hash_payload(payload: Mapping[str, Any]) -> str:
    return stable_hash(dict(payload))


def _reject(message: str, *, field: str, code: AurelShellErrorCode) -> None:
    raise AurelShellValidationError(message, code=code, field=field)


def _all_false_side_effects() -> AurelShellSideEffectProof:
    return AurelShellSideEffectProof()


def build_aurel_shell_boundary() -> AurelShellBoundary:
    payload = {
        "schema_version": AUREL_SHELL_BOUNDARY_VERSION,
        "reveals_state": True,
        "owns_truth": False,
        "executes_commands": False,
        "grants_permission": False,
        "mutates_runtime": False,
    }
    return AurelShellBoundary(**payload, boundary_hash=_hash_payload(payload))


def build_aurel_shell_contract() -> AurelShellContract:
    boundary = build_aurel_shell_boundary()
    side_effects = _all_false_side_effects()
    payload = {
        "schema_version": AUREL_SHELL_CONTRACT_VERSION,
        "shell_id": AUREL_SHELL_ID,
        "display_name": AUREL_SHELL_DISPLAY_NAME,
        "role": AurelShellRole.OPERATOR_COMMAND_SKIN,
        "purpose": (
            "Operator command skin that reveals governed state without owning "
            "truth or executing runtime actions"
        ),
        "operator_value": (
            "Carries operator command intent contracts and surface projection "
            "readiness without granting authority"
        ),
        "truth_label": AurelShellTruthLabel.CONTRACT_ONLY,
        "boundary": boundary,
        "non_goals": AUREL_SHELL_NON_GOALS,
        "invariants": AUREL_SHELL_INVARIANTS,
        "side_effects": side_effects,
    }
    return AurelShellContract(**payload, shell_contract_hash=_hash_payload(payload))


def serialize_aurel_shell_contract(contract: AurelShellContract) -> str:
    return to_canonical_json(contract.to_canonical_dict())


def assert_shell_is_not_source_of_truth(contract: AurelShellContract) -> None:
    if contract.boundary.owns_truth:
        _reject(
            "AurelShell must not own truth",
            field="boundary.owns_truth",
            code=AurelShellErrorCode.SOURCE_OF_TRUTH_VIOLATION,
        )


def assert_shell_does_not_execute(contract: AurelShellContract) -> None:
    if contract.boundary.executes_commands:
        _reject(
            "AurelShell must not execute commands",
            field="boundary.executes_commands",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_shell_boundary_invariants(contract: AurelShellContract) -> None:
    assert_shell_is_not_source_of_truth(contract)
    assert_shell_does_not_execute(contract)
    boundary = contract.boundary
    if boundary.grants_permission:
        _reject(
            "AurelShell must not grant permission",
            field="boundary.grants_permission",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )
    if boundary.mutates_runtime:
        _reject(
            "AurelShell must not mutate runtime",
            field="boundary.mutates_runtime",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )
    if contract.truth_label.value in STRONG_FORBIDDEN_SHELL_TRUTH_LABELS:
        _reject(
            f"forbidden truth label: {contract.truth_label.value}",
            field="truth_label",
            code=AurelShellErrorCode.INVALID_TRUTH_LABEL,
        )
