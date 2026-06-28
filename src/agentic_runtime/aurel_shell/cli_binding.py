"""AurelShell CLI / TUI inspect binding contracts (P2.0-F / P2.0.28).

Defines read-only inspect binding semantics for the shell projection. The CLI
binding is a contract for read-only inspection. The TUI binding is explicitly
UNAVAILABLE — there is no TUI convention in this repo.

Architectural law:
  - CLI inspect is read-only.
  - CLI inspect does not execute, mutate runtime, grant permission, or start
    a workflow.
  - TUI binding is UNAVAILABLE; an unavailable contract is better than a fake
    TUI product.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from typing import Any

from .contracts import (
    AurelShellErrorCode,
    _CanonicalMixin,
    _hash_payload,
    _reject,
    to_canonical_json,
)
from .projection import (
    P20FSideEffectProof,
    P20FTruthLabel,
    all_false_p2_0_f_side_effects,
    build_shell_projection_payload,
)

SHELL_INSPECT_COMMAND_VERSION = "aurel_shell_inspect_command_contract.v1"
SHELL_CLI_BINDING_VERSION = "aurel_shell_cli_binding_contract.v1"
SHELL_TUI_BINDING_VERSION = "aurel_shell_tui_binding_contract.v1"
SHELL_BINDING_TRUTH_BOUNDARY_VERSION = "aurel_shell_binding_truth_boundary.v1"

SHELL_CLI_BINDING_ID = "p2_0_f_shell_cli_inspect_binding"
SHELL_TUI_BINDING_ID = "p2_0_f_shell_tui_binding"

TUI_UNAVAILABLE_REASON = (
    "UNAVAILABLE_TUI: AurelShell has no TUI runtime or convention in P2.0-F; "
    "an explicit unavailable binding is declared instead of a fake TUI product"
)
TUI_NEXT_ACTION = (
    "Define a TUI inspect convention in a later pack before binding a TUI; "
    "P2.0-F only declares the read-only inspect contract"
)

_CLI_NON_GOALS: tuple[str, ...] = (
    "no_command_execution",
    "no_shell_mutation",
    "no_live_cli_product",
    "no_live_tui",
    "no_permission_grant",
    "no_workflow_start",
)


class ShellBindingKind(str, Enum):
    """Inspect binding taxonomy."""

    CLI_INSPECT = "cli_inspect"
    TUI = "tui"


class ShellBindingStatus(str, Enum):
    """Binding status — read-only contract or unavailable."""

    READ_ONLY_CONTRACT = "read_only_contract"
    UNAVAILABLE = "unavailable"


class ShellBindingUnavailableReason(str, Enum):
    """Why a binding is unavailable."""

    TUI_UNAVAILABLE = "tui_unavailable"
    UNAVAILABLE = "unavailable"


@dataclass(frozen=True)
class ShellBindingTruthBoundary(_CanonicalMixin):
    """Truth boundary shared by inspect bindings."""

    schema_version: str
    is_read_only: bool
    executes_action: bool
    mutates_runtime: bool
    grants_permission: bool
    starts_workflow: bool
    writes_memory: bool
    writes_trace: bool
    truth_label: str
    boundary_hash: str


@dataclass(frozen=True)
class ShellInspectCommandContract(_CanonicalMixin):
    """Read-only inspect command shape."""

    schema_version: str
    command_shape: str
    inspect_target: str
    projection_ref: str
    output_shape: Mapping[str, str]
    is_read_only: bool
    executes_action: bool
    mutates_runtime: bool
    truth_label: str
    command_hash: str


@dataclass(frozen=True)
class ShellCLIBindingContract(_CanonicalMixin):
    """Read-only shell CLI inspect binding contract (P2.0.28)."""

    schema_version: str
    binding_id: str
    binding_kind: ShellBindingKind
    binding_status: ShellBindingStatus
    command_shape: str
    inspect_target: str
    projection_ref: str
    inspect_command: ShellInspectCommandContract
    truth_boundary: ShellBindingTruthBoundary
    unavailable_reason: str
    truth_label: str
    is_read_only: bool
    executes_action: bool
    mutates_runtime: bool
    grants_permission: bool
    starts_workflow: bool
    writes_memory: bool
    writes_trace: bool
    non_goals: tuple[str, ...]
    side_effects: P20FSideEffectProof
    binding_hash: str


@dataclass(frozen=True)
class ShellTUIBindingContract(_CanonicalMixin):
    """Shell TUI binding contract — explicitly UNAVAILABLE (P2.0.28)."""

    schema_version: str
    binding_id: str
    binding_kind: ShellBindingKind
    binding_status: ShellBindingStatus
    command_shape: str
    inspect_target: str
    projection_ref: str
    truth_boundary: ShellBindingTruthBoundary
    unavailable_reason: str
    next_action: str
    truth_label: str
    is_read_only: bool
    executes_action: bool
    mutates_runtime: bool
    grants_permission: bool
    starts_workflow: bool
    writes_memory: bool
    writes_trace: bool
    non_goals: tuple[str, ...]
    side_effects: P20FSideEffectProof
    binding_hash: str


def _read_only_truth_boundary(truth_label: str) -> ShellBindingTruthBoundary:
    payload = {
        "schema_version": SHELL_BINDING_TRUTH_BOUNDARY_VERSION,
        "is_read_only": True,
        "executes_action": False,
        "mutates_runtime": False,
        "grants_permission": False,
        "starts_workflow": False,
        "writes_memory": False,
        "writes_trace": False,
        "truth_label": truth_label,
    }
    return ShellBindingTruthBoundary(
        **payload,
        boundary_hash=_hash_payload(payload),
    )


def build_shell_inspect_command_contract(
    *,
    projection_ref: str = "",
) -> ShellInspectCommandContract:
    output_shape = {
        "projection_id": "string",
        "source_snapshot_ref": "string",
        "truth_label": "string",
        "read_only": "bool",
        "authority_granted": "bool",
    }
    payload = {
        "schema_version": SHELL_INSPECT_COMMAND_VERSION,
        "command_shape": "aurel-shell inspect projection",
        "inspect_target": "shell_projection_read_model",
        "projection_ref": projection_ref,
        "output_shape": output_shape,
        "is_read_only": True,
        "executes_action": False,
        "mutates_runtime": False,
        "truth_label": P20FTruthLabel.CLI_INSPECT_CONTRACT_ONLY.value,
    }
    return ShellInspectCommandContract(
        **payload,
        command_hash=_hash_payload(payload),
    )


def build_shell_cli_binding_contract(
    *,
    projection_ref: str = "",
) -> ShellCLIBindingContract:
    inspect_command = build_shell_inspect_command_contract(projection_ref=projection_ref)
    truth_boundary = _read_only_truth_boundary(
        P20FTruthLabel.CLI_INSPECT_CONTRACT_ONLY.value,
    )
    side_effects = all_false_p2_0_f_side_effects()
    payload = {
        "schema_version": SHELL_CLI_BINDING_VERSION,
        "binding_id": SHELL_CLI_BINDING_ID,
        "binding_kind": ShellBindingKind.CLI_INSPECT,
        "binding_status": ShellBindingStatus.READ_ONLY_CONTRACT,
        "command_shape": inspect_command.command_shape,
        "inspect_target": inspect_command.inspect_target,
        "projection_ref": projection_ref,
        "inspect_command": inspect_command,
        "truth_boundary": truth_boundary,
        "unavailable_reason": "",
        "truth_label": P20FTruthLabel.CLI_INSPECT_CONTRACT_ONLY.value,
        "is_read_only": True,
        "executes_action": False,
        "mutates_runtime": False,
        "grants_permission": False,
        "starts_workflow": False,
        "writes_memory": False,
        "writes_trace": False,
        "non_goals": _CLI_NON_GOALS,
        "side_effects": side_effects,
    }
    contract = ShellCLIBindingContract(
        **payload,
        binding_hash=_hash_payload(payload),
    )
    assert_cli_inspect_is_read_only(contract)
    assert_cli_does_not_execute(contract)
    return contract


def build_shell_tui_binding_contract(
    *,
    projection_ref: str = "",
) -> ShellTUIBindingContract:
    truth_boundary = _read_only_truth_boundary(P20FTruthLabel.TUI_UNAVAILABLE.value)
    side_effects = all_false_p2_0_f_side_effects()
    payload = {
        "schema_version": SHELL_TUI_BINDING_VERSION,
        "binding_id": SHELL_TUI_BINDING_ID,
        "binding_kind": ShellBindingKind.TUI,
        "binding_status": ShellBindingStatus.UNAVAILABLE,
        "command_shape": "",
        "inspect_target": "shell_projection_read_model",
        "projection_ref": projection_ref,
        "truth_boundary": truth_boundary,
        "unavailable_reason": TUI_UNAVAILABLE_REASON,
        "next_action": TUI_NEXT_ACTION,
        "truth_label": P20FTruthLabel.TUI_UNAVAILABLE.value,
        "is_read_only": True,
        "executes_action": False,
        "mutates_runtime": False,
        "grants_permission": False,
        "starts_workflow": False,
        "writes_memory": False,
        "writes_trace": False,
        "non_goals": _CLI_NON_GOALS,
        "side_effects": side_effects,
    }
    contract = ShellTUIBindingContract(
        **payload,
        binding_hash=_hash_payload(payload),
    )
    assert_tui_status_explicit(contract)
    return contract


def handle_shell_cli_inspect(
    *,
    projection_ref: str = "",
) -> dict[str, Any]:
    """Run the read-only inspect path in-process. Returns a read-only view.

    This grants no authority, executes nothing, and mutates nothing. It is the
    operator-testable read-only path exercised by the P2.0 live integration
    demo.
    """
    projection = build_shell_projection_payload()
    return {
        "projection_id": projection.projection_id,
        "projection_payload_hash": projection.projection_payload_hash,
        "source_snapshot_ref": projection.source_snapshot_ref,
        "truth_label": projection.truth_label,
        "read_only": True,
        "executed": False,
        "authority_granted": False,
        "mutated_runtime": False,
        "started_workflow": False,
    }


def serialize_shell_cli_binding_contract(
    contract: ShellCLIBindingContract | ShellTUIBindingContract,
) -> str:
    return to_canonical_json(contract.to_canonical_dict())


def assert_cli_inspect_is_read_only(contract: ShellCLIBindingContract) -> None:
    if not contract.is_read_only or not contract.truth_boundary.is_read_only:
        _reject(
            "shell CLI inspect binding must be read-only",
            field="is_read_only",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_cli_does_not_execute(contract: ShellCLIBindingContract) -> None:
    if (
        contract.executes_action
        or contract.mutates_runtime
        or contract.grants_permission
        or contract.starts_workflow
        or contract.writes_memory
        or contract.writes_trace
    ):
        _reject(
            "shell CLI inspect binding must not execute, mutate, grant, or start work",
            field="executes_action",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_tui_status_explicit(contract: ShellTUIBindingContract) -> None:
    if contract.binding_status is ShellBindingStatus.UNAVAILABLE and (
        not contract.unavailable_reason or not contract.next_action
    ):
        _reject(
            "unavailable TUI binding must carry an unavailable reason and next action",
            field="unavailable_reason",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
