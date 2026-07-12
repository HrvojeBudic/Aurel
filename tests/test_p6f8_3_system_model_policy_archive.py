"""F8.3 seal — System model-routing, policy browser, archive status."""
from __future__ import annotations

import pytest

from agentic_runtime import build_runtime
from agentic_runtime.front_server import LiveReadModels, SystemReadModel
from agentic_runtime.policy_cards import PolicyCardRegistry, create_default_sandbox_policy_card


@pytest.fixture(autouse=True)
def _system_off(monkeypatch):
    monkeypatch.delenv("AUREL_SYSTEM", raising=False)


def test_model_routing_profiles_and_promotion_gates(monkeypatch):
    monkeypatch.setenv("AUREL_SYSTEM", "1")
    kernel = build_runtime()
    model = SystemReadModel.from_runtime(kernel, router=kernel.router)
    body = model.model_routing()
    assert body["available"] is True
    assert body["profiles"]
    assert body["promotion_gates"]["grants_authority"] is False
    assert "promote_skill" in body["promotion_gates"]["blocked_auto_actions"]


def test_policy_browser_lists_cards_with_canonical_hash(monkeypatch):
    monkeypatch.setenv("AUREL_SYSTEM", "1")
    registry = PolicyCardRegistry.from_cards([create_default_sandbox_policy_card()])
    kernel = build_runtime(policy_card_registry=registry)
    body = SystemReadModel.from_runtime(kernel).policy_browser()
    assert body["available"] is True
    assert body["registry_bound"] is True
    assert len(body["cards"]) == 1
    assert body["cards"][0]["canonical_hash"]
    assert body["registry_canonical_hash"]
    assert body["grants_authority"] is False


def test_policy_browser_masks_secret_fields(monkeypatch):
    monkeypatch.setenv("AUREL_SYSTEM", "1")
    card = create_default_sandbox_policy_card()
    kernel = build_runtime(policy_card_registry=PolicyCardRegistry.from_cards([card]))
    masked = SystemReadModel.from_runtime(kernel).policy_browser()
    blob = str(masked)
    assert "sk-" not in blob or "<masked:" in blob


def test_archive_status_in_memory_honest(monkeypatch):
    monkeypatch.setenv("AUREL_SYSTEM", "1")
    kernel = build_runtime()
    body = SystemReadModel.from_runtime(kernel).archive_status()
    assert body["available"] is True
    assert body["integrity"]["status"] == "UNAVAILABLE" or "reason" in body["integrity"]


def test_archive_status_persistent_trace(monkeypatch, tmp_path):
    monkeypatch.setenv("AUREL_SYSTEM", "1")
    trace_dir = str(tmp_path / "traces")
    kernel = build_runtime(trace_backend="persistent", trace_dir=trace_dir)
    body = SystemReadModel.from_runtime(kernel).archive_status()
    assert body["available"] is True
    assert "persistence" in body
    assert "integrity" in body
    assert "receipt_backlog" in body


def test_system_reads_live_and_unavailable(monkeypatch):
    kernel = build_runtime(policy_card_registry=PolicyCardRegistry.from_cards(
        [create_default_sandbox_policy_card()]))
    reads = LiveReadModels(kernel)
    _status_off, off = reads.read("/read/system/model_routing")
    assert off["available"] is False

    monkeypatch.setenv("AUREL_SYSTEM", "1")
    for path in ("/read/system/model_routing", "/read/system/policies", "/read/system/archive"):
        status, body = reads.read(path)
        assert status == 200
        assert body["available"] is True
        assert body["operator_only"] is True


def test_zero_write_on_system_reads(monkeypatch):
    monkeypatch.setenv("AUREL_SYSTEM", "1")
    kernel = build_runtime(policy_card_registry=PolicyCardRegistry.from_cards(
        [create_default_sandbox_policy_card()]))
    reads = LiveReadModels(kernel)
    before = len(list(kernel.runtime.trace.replay()))
    for path in ("/read/system/model_routing", "/read/system/policies", "/read/system/archive"):
        reads.read(path)
    after = len(list(kernel.runtime.trace.replay()))
    assert after == before
