"""P5.1 — AurelTrace Doctrine / Boundary Lock."""

from __future__ import annotations

import dataclasses
import json

import pytest

from agentic_runtime.aurel_trace import (
    AurelTraceError,
    TraceTruthLabel,
    build_aurel_trace_doctrine,
)


def test_doctrine_forbids_duplicate_trace_truth():
    doctrine = build_aurel_trace_doctrine()
    assert doctrine.duplicate_trace_spine_allowed is False
    with pytest.raises(AurelTraceError):
        dataclasses.replace(doctrine, duplicate_trace_spine_allowed=True)


def test_doctrine_forbids_execution_auth_replay_ui_rust_wasm():
    doctrine = build_aurel_trace_doctrine()
    assert doctrine.execution_available is False
    assert doctrine.authorization_available is False
    assert doctrine.semantic_correctness_claim_available is False
    assert doctrine.replay_available is False
    assert doctrine.rust_wasm_available is False
    assert doctrine.shell_ui_available is False
    assert doctrine.api_server_available is False
    assert doctrine.event_bus_available is False
    assert doctrine.p9_enforcement_available is False
    for locked in (
        "execution_available",
        "authorization_available",
        "semantic_correctness_claim_available",
        "replay_available",
        "rust_wasm_available",
        "shell_ui_available",
        "api_server_available",
        "event_bus_available",
        "p9_enforcement_available",
    ):
        with pytest.raises(AurelTraceError):
            dataclasses.replace(doctrine, **{locked: True})


def test_doctrine_separates_trace_bound_from_trace_verified():
    doctrine = build_aurel_trace_doctrine()
    assert doctrine.trace_bound_is_trace_verified is False
    assert doctrine.trace_verified_requires_verification is True
    with pytest.raises(AurelTraceError):
        dataclasses.replace(doctrine, trace_bound_is_trace_verified=True)
    with pytest.raises(AurelTraceError):
        dataclasses.replace(doctrine, trace_verified_requires_verification=False)


def test_doctrine_states_existing_ledger_is_source_of_truth():
    doctrine = build_aurel_trace_doctrine()
    assert "trace.py" in doctrine.source_of_truth_statement
    assert "not a replacement" in doctrine.source_of_truth_statement
    assert "never appends" in doctrine.existing_ledger_statement


def test_doctrine_is_live_and_serializable():
    doctrine = build_aurel_trace_doctrine()
    assert doctrine.truth_label is TraceTruthLabel.LIVE
    payload = json.dumps(doctrine.to_dict(), sort_keys=True)
    assert json.loads(payload)["duplicate_trace_spine_allowed"] is False


def test_doctrine_cannot_claim_integrity_verified_label():
    with pytest.raises(AurelTraceError):
        dataclasses.replace(
            build_aurel_trace_doctrine(),
            truth_label=TraceTruthLabel.TRACE_INTEGRITY_VERIFIED,
        )
