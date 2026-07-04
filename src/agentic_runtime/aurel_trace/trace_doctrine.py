"""P5-TRACE-A AurelTrace doctrine — machine-readable P5 boundary contract.

The doctrine encodes, structurally, what P5-TRACE-A is and is not. Its boolean
fields are locked at construction so the boundaries cannot be quietly flipped:

* P5 adds verification over the existing trace; it does not replace ``trace.py``.
* P5 does not execute, authorize, project UI, replay, or implement Rust/WASM.
* TRACE_BOUND is not TRACE_VERIFIED; hash integrity is not semantic correctness.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .trace_hash import (
    AUREL_TRACE_CONTRACT_VERSION,
    AurelTraceError,
    TraceTruthLabel,
    forbid_false,
    forbid_true,
)

AUREL_TRACE_DOCTRINE_ID = "aurel-trace-doctrine.p5-trace-a.v1"

_SOURCE_OF_TRUTH_STATEMENT = (
    "The existing trace.py ledger (InMemoryTraceLedger / PersistentTraceLedger) "
    "remains the current trace source of truth. P5-TRACE-A is an adapter and "
    "verification foundation over those records, not a replacement."
)
_EXISTING_LEDGER_STATEMENT = (
    "aurel_trace reads existing ledger records; it never appends, mutates, or "
    "creates a second ledger."
)
_TRACE_BOUND_LAW = (
    "A record that is present and referenced is TRACE_BOUND. TRACE_BOUND is not "
    "TRACE_VERIFIED."
)
_TRACE_VERIFIED_LAW = (
    "Broad semantic/business TRACE_VERIFIED is not claimed by P5-TRACE-A. Only "
    "TRACE_INTEGRITY_VERIFIED may be minted, and only when a supported hash "
    "chain actually verifies."
)
_PROJECTION_LAW = "Projections derive from trace; a projection is never the source of truth."


@dataclass(frozen=True)
class AurelTraceDoctrine:
    """Locked P5 boundary contract. Every boundary is structurally enforced."""

    doctrine_id: str = AUREL_TRACE_DOCTRINE_ID
    contract_version: str = AUREL_TRACE_CONTRACT_VERSION
    p5_scope: str = (
        "inventory, doctrine, canonical envelope adapter, stable refs, and "
        "structured hash-chain verification over existing trace records"
    )
    source_of_truth_statement: str = _SOURCE_OF_TRUTH_STATEMENT
    existing_ledger_statement: str = _EXISTING_LEDGER_STATEMENT
    trace_bound_law: str = _TRACE_BOUND_LAW
    trace_verified_law: str = _TRACE_VERIFIED_LAW
    projection_law: str = _PROJECTION_LAW
    execution_boundary: str = "P5 verifies history shape; P5 does not execute."
    authorization_boundary: str = "P5 is evidence, not authority; Custos authorizes."
    semantic_correctness_boundary: str = (
        "Hash-chain integrity is not semantic, policy, or business correctness."
    )
    replay_boundary: str = "P5-TRACE-A does not implement deterministic replay."
    rust_wasm_boundary: str = "P5-TRACE-A does not implement any Rust/WASM substrate."

    # Locked booleans — the machine-checkable boundary.
    duplicate_trace_spine_allowed: bool = False
    execution_available: bool = False
    authorization_available: bool = False
    semantic_correctness_claim_available: bool = False
    replay_available: bool = False
    rust_wasm_available: bool = False
    shell_ui_available: bool = False
    api_server_available: bool = False
    event_bus_available: bool = False
    p9_enforcement_available: bool = False
    trace_verified_requires_verification: bool = True
    trace_bound_is_trace_verified: bool = False

    truth_label: TraceTruthLabel = TraceTruthLabel.LIVE

    def __post_init__(self) -> None:
        forbid_true(
            self,
            "duplicate_trace_spine_allowed",
            "execution_available",
            "authorization_available",
            "semantic_correctness_claim_available",
            "replay_available",
            "rust_wasm_available",
            "shell_ui_available",
            "api_server_available",
            "event_bus_available",
            "p9_enforcement_available",
            "trace_bound_is_trace_verified",
        )
        forbid_false(self, "trace_verified_requires_verification")
        if self.truth_label is TraceTruthLabel.TRACE_INTEGRITY_VERIFIED:
            raise AurelTraceError("the doctrine is a LIVE contract, not a verified chain")

    def to_dict(self) -> dict[str, Any]:
        return {
            "doctrine_id": self.doctrine_id,
            "contract_version": self.contract_version,
            "p5_scope": self.p5_scope,
            "source_of_truth_statement": self.source_of_truth_statement,
            "existing_ledger_statement": self.existing_ledger_statement,
            "trace_bound_law": self.trace_bound_law,
            "trace_verified_law": self.trace_verified_law,
            "projection_law": self.projection_law,
            "execution_boundary": self.execution_boundary,
            "authorization_boundary": self.authorization_boundary,
            "semantic_correctness_boundary": self.semantic_correctness_boundary,
            "replay_boundary": self.replay_boundary,
            "rust_wasm_boundary": self.rust_wasm_boundary,
            "duplicate_trace_spine_allowed": self.duplicate_trace_spine_allowed,
            "execution_available": self.execution_available,
            "authorization_available": self.authorization_available,
            "semantic_correctness_claim_available": self.semantic_correctness_claim_available,
            "replay_available": self.replay_available,
            "rust_wasm_available": self.rust_wasm_available,
            "shell_ui_available": self.shell_ui_available,
            "api_server_available": self.api_server_available,
            "event_bus_available": self.event_bus_available,
            "p9_enforcement_available": self.p9_enforcement_available,
            "trace_verified_requires_verification": self.trace_verified_requires_verification,
            "trace_bound_is_trace_verified": self.trace_bound_is_trace_verified,
            "truth_label": self.truth_label.value,
        }


def build_aurel_trace_doctrine() -> AurelTraceDoctrine:
    return AurelTraceDoctrine()
