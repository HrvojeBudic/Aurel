"""M2 — trace ledger survives concurrent writers and detects full re-forge."""

from __future__ import annotations

import json
import threading

from agentic_runtime.core_types import PlanningFailureRecord
from agentic_runtime.trace import (
    GENESIS,
    PersistentTraceLedger,
    _entry_hash,
    _load_jsonl,
    canonical_json,
    sha,
)
from agentic_runtime.trace_anchor import FileAnchorSink


def _rec(tag: str) -> PlanningFailureRecord:
    return PlanningFailureRecord.make(tag, "card", "rejected", "reason")


def test_two_threads_one_ledger_keeps_chain_consistent(tmp_path):
    led = PersistentTraceLedger(base_dir=str(tmp_path), run_id="race", checkpoint_every=5)

    def worker(n: int) -> None:
        for i in range(50):
            led.append_planning_failure(_rec(f"{n}-{i}"))

    threads = [threading.Thread(target=worker, args=(n,)) for n in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    report = led.verify_persisted()
    assert report["ok"], report
    assert len(led) == 100


def test_anchor_catches_full_reforge(tmp_path):
    sink = FileAnchorSink(str(tmp_path / "anchors"))
    led = PersistentTraceLedger(
        base_dir=str(tmp_path / "run"), run_id="anc", checkpoint_every=2, anchor_sink=sink
    )
    for i in range(6):
        led.append_planning_failure(_rec(f"i{i}"))
    led.seal_run("completed")
    assert led.verify_persisted()["ok"]

    # FULL re-forge: rewrite events + checkpoints + receipt so the *internal*
    # chain re-verifies. Only the external anchor can catch it.
    evs = _load_jsonl(led.events_path)
    prev = GENESIS
    new_events = []
    for e in evs:
        e["payload"]["reason"] = "FORGED"
        e["prev_entry_hash"] = prev
        e.pop("entry_hash", None)
        e["entry_hash"] = _entry_hash(e)
        prev = e["entry_hash"]
        new_events.append(e)
    led.events_path.write_text(
        "\n".join(json.dumps(e, sort_keys=True) for e in new_events) + "\n"
    )
    cph = GENESIS
    new_cps = []
    for i, e in enumerate(new_events):
        seq = i + 1
        if seq % 2 == 0:
            cp = {"run_id": "anc", "sequence": seq,
                  "previous_checkpoint_hash": cph, "chain_head": e["entry_hash"]}
            cp["checkpoint_hash"] = sha(canonical_json(cp))
            cph = cp["checkpoint_hash"]
            new_cps.append(cp)
    led.checkpoints_path.write_text(
        "\n".join(json.dumps(c, sort_keys=True) for c in new_cps) + "\n"
    )
    receipt = json.loads(led.receipt_path.read_text())
    receipt["final_chain_hash"] = new_events[-1]["entry_hash"]
    led.receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True))

    # Internal-only verification (no anchor) is fooled by a complete re-forge...
    fooled = PersistentTraceLedger(
        base_dir=str(tmp_path / "run"), run_id="anc", checkpoint_every=2
    )
    fooled._anchor_sink = None
    # Point the default sink at an empty dir so no anchor is resolved.
    import os

    old = os.environ.get("AUREL_ANCHOR_ROOT")
    os.environ["AUREL_ANCHOR_ROOT"] = str(tmp_path / "empty")
    try:
        assert fooled.verify_persisted()["ok"] is True
    finally:
        if old is None:
            os.environ.pop("AUREL_ANCHOR_ROOT", None)
        else:
            os.environ["AUREL_ANCHOR_ROOT"] = old

    # ...but the anchored verifier fails closed.
    anchored = PersistentTraceLedger(
        base_dir=str(tmp_path / "run"), run_id="anc", checkpoint_every=2, anchor_sink=sink
    )
    rep = anchored.verify_persisted()
    assert rep["ok"] is False
    assert "anchor" in rep["reason"]


def test_clean_run_reports_anchored_true(tmp_path):
    sink = FileAnchorSink(str(tmp_path / "anchors"))
    led = PersistentTraceLedger(
        base_dir=str(tmp_path / "run"), run_id="clean", checkpoint_every=2, anchor_sink=sink
    )
    for i in range(4):
        led.append_planning_failure(_rec(f"i{i}"))
    led.seal_run("completed")
    rep = led.verify_persisted()
    assert rep["ok"] and rep["anchored"] is True


def test_anchor_detects_truncation_below_anchor(tmp_path):
    sink = FileAnchorSink(str(tmp_path / "anchors"))
    led = PersistentTraceLedger(
        base_dir=str(tmp_path / "run"), run_id="trunc", checkpoint_every=2, anchor_sink=sink
    )
    for i in range(6):
        led.append_planning_failure(_rec(f"i{i}"))
    led.seal_run("completed")
    # drop events below the anchored sequence
    lines = led.events_path.read_text().strip().split("\n")
    led.events_path.write_text("\n".join(lines[:3]) + "\n")
    anchored = PersistentTraceLedger(
        base_dir=str(tmp_path / "run"), run_id="trunc", checkpoint_every=2, anchor_sink=sink
    )
    assert anchored.verify_persisted()["ok"] is False
