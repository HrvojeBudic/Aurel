"""M5 — deterministic replay from a model cassette (no network)."""

from __future__ import annotations

from agentic_runtime import UnsafeLocalSandbox
from agentic_runtime.model_cassette import (
    ModelCassette,
    RecordingModelClient,
    ReplayModelClient,
    cassette_key,
)
from agentic_runtime.model_router import MockModelClient
from agentic_runtime.spine.harness import replay_spine_run


class _FakeHardSandbox(UnsafeLocalSandbox):
    def __init__(self, root=None):
        super().__init__(root)
        self.is_hard_isolated = True
        self.is_security_boundary = True


def test_cassette_records_and_replays(tmp_path):
    cas = ModelCassette(tmp_path / "c.jsonl")
    inner = MockModelClient()
    rec = RecordingModelClient(inner, cas, model_id="m")
    raw = rec.complete("sys", "user")
    assert len(cas) == 1
    # replay returns the identical recorded response, contacting no provider
    rep = ReplayModelClient(cas, model_id="m")
    assert rep.complete("sys", "user") == raw


def test_cassette_miss_is_fail_closed(tmp_path):
    cas = ModelCassette(tmp_path / "c.jsonl")
    rep = ReplayModelClient(cas, model_id="m")
    out = rep.complete("unseen-sys", "unseen-user")
    # a miss yields an honest refusal, never a fabricated completion
    assert "cassette miss" in out


def test_cassette_key_is_stable():
    a = cassette_key("m", "s", "u")
    b = cassette_key("m", "s", "u")
    assert a == b
    assert cassette_key("m", "s", "u2") != a


def test_replay_is_state_hash_deterministic(tmp_path):
    report = replay_spine_run(
        trace_dir=tmp_path / "traces",
        sandbox_factory=lambda: _FakeHardSandbox(),
    )
    assert report["replay_used_network"] is False
    assert report["cassette_size"] >= 1
    # the reconstructed run reaches the identical per-node world states
    assert report["deterministic"], report
    assert report["original_state_hashes"] == report["replay_state_hashes"]
