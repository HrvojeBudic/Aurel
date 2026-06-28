"""AurelShell API contract (P2.0-F / P2.0.27).

The API contract describes the *shape* of a future read-only shell projection
API. It is a payload schema only.

Architectural law:
  - API contract is not an API server.
  - API contract does not create HTTP routes.
  - API contract does not handle network requests.
  - API contract does not mutate runtime or authorize actions.
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
    API_RUNTIME_UNAVAILABLE_REASON,
    P20FSideEffectProof,
    P20FTruthLabel,
    all_false_p2_0_f_side_effects,
)

SHELL_API_CONTRACT_VERSION = "aurel_shell_api_contract.v1"
SHELL_API_ENDPOINT_VERSION = "aurel_shell_api_endpoint_contract.v1"
SHELL_API_RESPONSE_VERSION = "aurel_shell_api_response_contract.v1"

SHELL_API_CONTRACT_ID = "p2_0_f_shell_api_contract"

_API_NON_GOALS: tuple[str, ...] = (
    "no_api_server",
    "no_http_routes",
    "no_network_request_handling",
    "no_runtime_mutation",
    "no_action_authorization",
)


class ShellAPIRuntimeStatus(str, Enum):
    """API runtime availability — contract only."""

    API_CONTRACT_ONLY = "API_CONTRACT_ONLY"
    UNAVAILABLE_API_RUNTIME = "UNAVAILABLE_API_RUNTIME"


@dataclass(frozen=True)
class ShellAPIResponseContract(_CanonicalMixin):
    """Response payload schema for a read-only projection endpoint."""

    schema_version: str
    response_name: str
    response_schema: Mapping[str, str]
    projection_ref: str
    truth_label: str
    response_hash: str


@dataclass(frozen=True)
class ShellAPIEndpointContract(_CanonicalMixin):
    """A single read-only endpoint *shape* — not a live route."""

    schema_version: str
    endpoint_name: str
    method_shape: str
    path_shape: str
    request_contract: Mapping[str, str]
    response_contract: ShellAPIResponseContract
    projection_ref: str
    truth_label: str
    is_api_server: bool
    creates_http_route: bool
    handles_network_request: bool
    mutates_runtime: bool
    authorizes_action: bool
    endpoint_hash: str


@dataclass(frozen=True)
class ShellAPIContract(_CanonicalMixin):
    """Shell projection API contract envelope (P2.0.27)."""

    schema_version: str
    api_contract_id: str
    contract_version: str
    endpoints: tuple[ShellAPIEndpointContract, ...]
    runtime_status: ShellAPIRuntimeStatus
    unavailable_reason: str
    projection_ref: str
    truth_label: str
    is_api_server: bool
    creates_http_route: bool
    handles_network_request: bool
    mutates_runtime: bool
    authorizes_action: bool
    non_goals: tuple[str, ...]
    side_effects: P20FSideEffectProof
    contract_hash: str


def build_shell_api_response_contract(
    *,
    response_name: str = "shell_projection_response",
    projection_ref: str = "",
) -> ShellAPIResponseContract:
    response_schema = {
        "projection_id": "string",
        "projection_version": "string",
        "source_snapshot_ref": "string",
        "surface_registry_summary": "object",
        "navigation_boundary_summary": "object",
        "continuity_summary": "object",
        "truth_label_summary": "object",
        "permission_matrix_summary": "object",
        "unavailable_state_summary": "object",
        "fixture_disclosure_summary": "object",
        "operator_demo_summary": "object",
        "client_consistency_summary": "object",
        "regression_harness_summary": "object",
        "readiness_summary": "object",
        "truth_label": "string",
        "is_read_model": "bool",
        "is_source_of_truth": "bool",
    }
    payload = {
        "schema_version": SHELL_API_RESPONSE_VERSION,
        "response_name": response_name,
        "response_schema": response_schema,
        "projection_ref": projection_ref,
        "truth_label": P20FTruthLabel.API_CONTRACT_ONLY.value,
    }
    return ShellAPIResponseContract(
        **payload,
        response_hash=_hash_payload(payload),
    )


def build_shell_api_endpoint_contract(
    *,
    endpoint_name: str = "get_shell_projection",
    method_shape: str = "GET",
    path_shape: str = "/aurel-shell/projection",
    projection_ref: str = "",
) -> ShellAPIEndpointContract:
    response_contract = build_shell_api_response_contract(projection_ref=projection_ref)
    request_contract = {
        "surface_id": "string?optional",
        "include_summaries": "bool?optional",
    }
    payload = {
        "schema_version": SHELL_API_ENDPOINT_VERSION,
        "endpoint_name": endpoint_name,
        "method_shape": method_shape,
        "path_shape": path_shape,
        "request_contract": request_contract,
        "response_contract": response_contract,
        "projection_ref": projection_ref,
        "truth_label": P20FTruthLabel.API_CONTRACT_ONLY.value,
        "is_api_server": False,
        "creates_http_route": False,
        "handles_network_request": False,
        "mutates_runtime": False,
        "authorizes_action": False,
    }
    return ShellAPIEndpointContract(
        **payload,
        endpoint_hash=_hash_payload(payload),
    )


def build_shell_api_contract(*, projection_ref: str = "") -> ShellAPIContract:
    endpoint = build_shell_api_endpoint_contract(projection_ref=projection_ref)
    side_effects = all_false_p2_0_f_side_effects()
    payload = {
        "schema_version": SHELL_API_CONTRACT_VERSION,
        "api_contract_id": SHELL_API_CONTRACT_ID,
        "contract_version": "v1",
        "endpoints": (endpoint,),
        "runtime_status": ShellAPIRuntimeStatus.UNAVAILABLE_API_RUNTIME,
        "unavailable_reason": API_RUNTIME_UNAVAILABLE_REASON,
        "projection_ref": projection_ref,
        "truth_label": P20FTruthLabel.API_CONTRACT_ONLY.value,
        "is_api_server": False,
        "creates_http_route": False,
        "handles_network_request": False,
        "mutates_runtime": False,
        "authorizes_action": False,
        "non_goals": _API_NON_GOALS,
        "side_effects": side_effects,
    }
    contract = ShellAPIContract(
        **payload,
        contract_hash=_hash_payload(payload),
    )
    assert_api_contract_is_not_server(contract)
    assert_no_http_routes_created(contract)
    return contract


def serialize_shell_api_contract(contract: ShellAPIContract) -> str:
    return to_canonical_json(contract.to_canonical_dict())


def assert_api_contract_is_not_server(contract: ShellAPIContract) -> None:
    # API_CONTRACT_ONLY / UNAVAILABLE_API_RUNTIME are the only allowed runtime
    # statuses; there is no live-server status. Reject any server-shaped claim.
    if contract.is_api_server or contract.handles_network_request:
        _reject(
            "shell API contract must not be an API server",
            field="is_api_server",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_no_http_routes_created(contract: ShellAPIContract) -> None:
    if contract.creates_http_route or any(
        endpoint.creates_http_route for endpoint in contract.endpoints
    ):
        _reject(
            "shell API contract must not create HTTP routes",
            field="creates_http_route",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )
