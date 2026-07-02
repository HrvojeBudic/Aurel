"""P3-FLOW-A AurelFlow foundation errors.

Structured, fail-closed error surface for the AurelFlow runtime foundation.
Raising these errors is contract validation only — it does not execute, retry,
roll back, or dispatch anything.
"""

from __future__ import annotations

from enum import Enum


class AurelFlowErrorCode(str, Enum):
    # graph shape
    EMPTY_GRAPH_ID = "EMPTY_GRAPH_ID"
    EMPTY_GRAPH_NAME = "EMPTY_GRAPH_NAME"
    EMPTY_NODE_SET = "EMPTY_NODE_SET"
    EMPTY_NODE_ID = "EMPTY_NODE_ID"
    EMPTY_EDGE_ID = "EMPTY_EDGE_ID"
    DUPLICATE_NODE_ID = "DUPLICATE_NODE_ID"
    DUPLICATE_EDGE_ID = "DUPLICATE_EDGE_ID"
    UNKNOWN_NODE_REF = "UNKNOWN_NODE_REF"
    UNSUPPORTED_NODE_TYPE = "UNSUPPORTED_NODE_TYPE"
    UNSUPPORTED_EDGE_TYPE = "UNSUPPORTED_EDGE_TYPE"
    MISSING_ENTRY_NODE = "MISSING_ENTRY_NODE"
    MISSING_EXIT_NODE = "MISSING_EXIT_NODE"
    UNKNOWN_ENTRY_NODE = "UNKNOWN_ENTRY_NODE"
    UNKNOWN_EXIT_NODE = "UNKNOWN_EXIT_NODE"
    GRAPH_CYCLE_DETECTED = "GRAPH_CYCLE_DETECTED"
    UNREACHABLE_NODE = "UNREACHABLE_NODE"
    APPROVAL_FLAG_MISMATCH = "APPROVAL_FLAG_MISMATCH"
    INVALID_GRAPH = "INVALID_GRAPH"
    # run / lifecycle
    GRAPH_RUN_MISMATCH = "GRAPH_RUN_MISMATCH"
    EMPTY_RUN_KEY = "EMPTY_RUN_KEY"
    UNKNOWN_TRANSITION_TARGET = "UNKNOWN_TRANSITION_TARGET"
    STALE_TRANSITION_SOURCE = "STALE_TRANSITION_SOURCE"
    INVALID_LIFECYCLE_TRANSITION = "INVALID_LIFECYCLE_TRANSITION"
    INVALID_NODE_TRANSITION = "INVALID_NODE_TRANSITION"
    TERMINAL_LIFECYCLE_STATE = "TERMINAL_LIFECYCLE_STATE"
    TERMINAL_NODE_STATE = "TERMINAL_NODE_STATE"
    # runtime behavior (P3-FLOW-B)
    UNKNOWN_EVENT_REF = "UNKNOWN_EVENT_REF"
    RUN_MISMATCH = "RUN_MISMATCH"
    FORBIDDEN_TRUTH_LABEL = "FORBIDDEN_TRUTH_LABEL"
    FORBIDDEN_BOUNDARY_CLAIM = "FORBIDDEN_BOUNDARY_CLAIM"
    DIRECT_STATE_MUTATION_FORBIDDEN = "DIRECT_STATE_MUTATION_FORBIDDEN"
    INVALID_COMMITMENT_STATUS = "INVALID_COMMITMENT_STATUS"
    SIGNAL_KIND_MISMATCH = "SIGNAL_KIND_MISMATCH"
    NOT_RESUMABLE = "NOT_RESUMABLE"
    EMPTY_ACTOR_ID = "EMPTY_ACTOR_ID"
    # projection / CLI / seal (P3-FLOW-C)
    UNSUPPORTED_CLI_COMMAND = "UNSUPPORTED_CLI_COMMAND"
    UNSUPPORTED_OUTPUT_FORMAT = "UNSUPPORTED_OUTPUT_FORMAT"
    INVALID_SEAL_CHECK = "INVALID_SEAL_CHECK"
    ERROR = "ERROR"


class AurelFlowError(Exception):
    """Base error for the AurelFlow foundation."""


class AurelFlowValidationError(AurelFlowError):
    """Fail-closed validation error carrying a structured code and field."""

    def __init__(self, message: str, *, code: AurelFlowErrorCode, field: str) -> None:
        super().__init__(message)
        self.code = code
        self.field = field


def reject(message: str, *, code: AurelFlowErrorCode, field: str) -> None:
    raise AurelFlowValidationError(message, code=code, field=field)
