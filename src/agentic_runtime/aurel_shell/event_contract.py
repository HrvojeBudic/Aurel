"""AurelShell event contract (P2.0-F / P2.0.27).

The event contract describes the *shape* of a future shell projection event.
It is a payload shape only.

Architectural law:
  - Event contract is not an emitted runtime event.
  - Event contract does not create an event bus.
  - Event contract does not mutate runtime or write trace.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum

from .contracts import (
    AurelShellErrorCode,
    _CanonicalMixin,
    _hash_payload,
    _reject,
    to_canonical_json,
)
from .projection import (
    EVENT_RUNTIME_UNAVAILABLE_REASON,
    P20FSideEffectProof,
    P20FTruthLabel,
    all_false_p2_0_f_side_effects,
)

SHELL_EVENT_CONTRACT_VERSION = "aurel_shell_event_contract.v1"
SHELL_EVENT_PAYLOAD_VERSION = "aurel_shell_event_payload_contract.v1"

SHELL_EVENT_CONTRACT_ID = "p2_0_f_shell_event_contract"

_EVENT_NON_GOALS: tuple[str, ...] = (
    "no_runtime_event_emission",
    "no_event_bus",
    "no_runtime_mutation",
    "no_trace_write",
)


class ShellEventRuntimeStatus(str, Enum):
    """Event runtime availability — contract only."""

    EVENT_CONTRACT_ONLY = "EVENT_CONTRACT_ONLY"
    UNAVAILABLE_EVENT_RUNTIME = "UNAVAILABLE_EVENT_RUNTIME"


@dataclass(frozen=True)
class ShellEventPayloadContract(_CanonicalMixin):
    """Event payload shape — not an emitted event."""

    schema_version: str
    event_name: str
    event_payload_shape: Mapping[str, str]
    projection_ref: str
    summary: str
    truth_label: str
    is_runtime_event: bool
    event_emitted: bool
    event_payload_hash: str


@dataclass(frozen=True)
class ShellEventContract(_CanonicalMixin):
    """Shell projection event contract envelope (P2.0.27)."""

    schema_version: str
    event_contract_id: str
    contract_version: str
    event_name: str
    event_payload_contract: ShellEventPayloadContract
    runtime_status: ShellEventRuntimeStatus
    unavailable_reason: str
    projection_ref: str
    truth_label: str
    is_runtime_event: bool
    event_emitted: bool
    event_bus_created: bool
    mutates_runtime: bool
    writes_trace: bool
    non_goals: tuple[str, ...]
    side_effects: P20FSideEffectProof
    contract_hash: str


def build_shell_event_payload_contract(
    *,
    event_name: str = "aurel_shell_projection_updated",
    projection_ref: str = "",
) -> ShellEventPayloadContract:
    event_payload_shape = {
        "event_name": "string",
        "projection_ref": "string",
        "source_snapshot_ref": "string",
        "surface_count": "string",
        "truth_label": "string",
        "is_runtime_event": "bool",
        "event_emitted": "bool",
    }
    payload = {
        "schema_version": SHELL_EVENT_PAYLOAD_VERSION,
        "event_name": event_name,
        "event_payload_shape": event_payload_shape,
        "projection_ref": projection_ref,
        "summary": "Contract-only projection event shape; no event is emitted",
        "truth_label": P20FTruthLabel.EVENT_CONTRACT_ONLY.value,
        "is_runtime_event": False,
        "event_emitted": False,
    }
    return ShellEventPayloadContract(
        **payload,
        event_payload_hash=_hash_payload(payload),
    )


def build_shell_event_contract(*, projection_ref: str = "") -> ShellEventContract:
    event_payload_contract = build_shell_event_payload_contract(
        projection_ref=projection_ref,
    )
    side_effects = all_false_p2_0_f_side_effects()
    payload = {
        "schema_version": SHELL_EVENT_CONTRACT_VERSION,
        "event_contract_id": SHELL_EVENT_CONTRACT_ID,
        "contract_version": "v1",
        "event_name": event_payload_contract.event_name,
        "event_payload_contract": event_payload_contract,
        "runtime_status": ShellEventRuntimeStatus.UNAVAILABLE_EVENT_RUNTIME,
        "unavailable_reason": EVENT_RUNTIME_UNAVAILABLE_REASON,
        "projection_ref": projection_ref,
        "truth_label": P20FTruthLabel.EVENT_CONTRACT_ONLY.value,
        "is_runtime_event": False,
        "event_emitted": False,
        "event_bus_created": False,
        "mutates_runtime": False,
        "writes_trace": False,
        "non_goals": _EVENT_NON_GOALS,
        "side_effects": side_effects,
    }
    contract = ShellEventContract(
        **payload,
        contract_hash=_hash_payload(payload),
    )
    assert_event_contract_is_not_emitted_runtime_event(contract)
    assert_no_event_bus_created(contract)
    return contract


def serialize_shell_event_contract(contract: ShellEventContract) -> str:
    return to_canonical_json(contract.to_canonical_dict())


def assert_event_contract_is_not_emitted_runtime_event(
    contract: ShellEventContract,
) -> None:
    if (
        contract.is_runtime_event
        or contract.event_emitted
        or contract.event_payload_contract.event_emitted
        or contract.event_payload_contract.is_runtime_event
    ):
        _reject(
            "shell event contract must not be an emitted runtime event",
            field="event_emitted",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_no_event_bus_created(contract: ShellEventContract) -> None:
    if contract.event_bus_created or contract.mutates_runtime or contract.writes_trace:
        _reject(
            "shell event contract must not create an event bus or mutate runtime",
            field="event_bus_created",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )
