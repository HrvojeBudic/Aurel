"""P5.0 — Existing Trace Inventory / Compatibility Lock."""

from __future__ import annotations

import json

from agentic_runtime.aurel_trace import (
    ExistingTraceInventory,
    TraceTruthLabel,
    build_existing_trace_inventory,
)


def test_inventory_includes_current_ledger_record_types():
    inventory = build_existing_trace_inventory()
    for record_type in (
        "StateTransitionRecord",
        "PlanningFailureRecord",
        "RuntimeStatusTransitionRecord",
        "BudgetDecisionRecord",
        "MemoryGovernanceRecord",
        "ToolContractViolationRecord",
        "ApprovalReceiptRecord",
        "PraxisEventRecord",
        "SandboxViolationRecord",
    ):
        assert record_type in inventory.record_types
        assert record_type in inventory.supported_record_types


def test_inventory_includes_current_ledger_types():
    inventory = build_existing_trace_inventory()
    assert "InMemoryTraceLedger" in inventory.ledger_types
    assert "PersistentTraceLedger" in inventory.ledger_types
    assert "agentic_runtime.trace" in inventory.trace_modules


def test_inventory_records_known_hash_and_id_fields():
    inventory = build_existing_trace_inventory()
    assert "entry_hash" in inventory.known_hash_fields
    assert "prev_entry_hash" in inventory.known_previous_hash_fields
    assert "id" in inventory.known_record_id_fields
    assert inventory.known_payload_fields  # payload_hash() method noted


def test_inventory_does_not_claim_the_canonical_event_form_supported():
    inventory = build_existing_trace_inventory()
    # contracts.trace.AurelTraceLog is a separate canonical scheme; it must be
    # reported as unsupported (deferred), never silently claimed supported.
    joined = " ".join(inventory.unsupported_record_types)
    assert "AurelTraceLog" in joined
    for unsupported in inventory.unsupported_record_types:
        assert unsupported not in inventory.supported_record_types


def test_inventory_is_deterministic():
    a = build_existing_trace_inventory()
    b = build_existing_trace_inventory()
    assert a == b
    assert a.to_dict() == b.to_dict()


def test_inventory_is_serializable():
    inventory = build_existing_trace_inventory()
    payload = json.dumps(inventory.to_dict(), sort_keys=True)
    round_trip = json.loads(payload)
    assert round_trip["inventory_id"] == inventory.inventory_id
    assert round_trip["truth_label"] == TraceTruthLabel.LIVE.value


def test_inventory_truth_label_is_live_not_verified():
    inventory = build_existing_trace_inventory()
    assert inventory.truth_label is TraceTruthLabel.LIVE
    assert isinstance(inventory, ExistingTraceInventory)
