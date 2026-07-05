"""M0 — content-addressed state store (CAS) done-conditions.

Proves the CAS address is byte-identical to ``sandbox.state_hash()``, that
storage dedups, that materialize/checkout round-trip exactly, that gc is a
precise mark-sweep, and that a partially-written state is never visible.
"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

from agentic_runtime.sandbox import UnsafeLocalSandbox
from agentic_runtime.state_store import StateStore


def _sbx(files: dict[str, str]) -> UnsafeLocalSandbox:
    sbx = UnsafeLocalSandbox(root=tempfile.mkdtemp())
    for path, content in files.items():
        sbx.write_file(path, content)
    return sbx


def _store() -> StateStore:
    return StateStore(tempfile.mkdtemp())


def test_commit_is_keyed_by_state_hash_and_dedups():
    sbx = _sbx({"a.txt": "hello", "sub/b.txt": "world"})
    store = _store()

    h = sbx.commit_state(store)
    assert h == sbx.state_hash()  # CAS address == sandbox state hash (same _tree_hash)
    assert store.has(h)

    states_dir = store.base_dir / "states"
    before = sorted(os.listdir(states_dir))

    h2 = sbx.commit_state(store)  # identical tree -> dedup, no new dir
    assert h2 == h
    assert sorted(os.listdir(states_dir)) == before
    assert before.count(h) == 1


def test_materialize_reproduces_state_hash():
    sbx = _sbx({"a.txt": "hello", "sub/b.txt": "world"})
    store = _store()
    h = sbx.commit_state(store)

    dest = tempfile.mkdtemp()
    store.materialize(h, dest)

    assert UnsafeLocalSandbox(root=dest).state_hash() == h


def test_materialize_unknown_state_raises():
    store = _store()
    try:
        store.materialize("deadbeef", tempfile.mkdtemp())
    except KeyError:
        return
    raise AssertionError("expected KeyError for unknown state")


def test_commit_then_checkout_roundtrip():
    sbx = _sbx({"x.py": "print(1)\n", "d/y.txt": "z"})
    store = _store()
    h = sbx.commit_state(store)

    restored = sbx.checkout(store, h)

    assert isinstance(restored, UnsafeLocalSandbox)
    assert restored.root != sbx.root          # a genuinely fresh workspace
    assert restored.state_hash() == h          # byte-identical reconstruction


def test_gc_removes_unreferenced_and_keeps_live():
    store = _store()
    ha = _sbx({"a": "1"}).commit_state(store)
    hb = _sbx({"b": "2"}).commit_state(store)
    hc = _sbx({"c": "3"}).commit_state(store)
    assert len({ha, hb, hc}) == 3              # distinct content -> distinct nodes

    removed = store.gc({ha, hc})

    assert set(removed) == {hb}
    assert store.has(ha) and store.has(hc)
    assert not store.has(hb)


def test_gc_sweeps_tmp_leftovers():
    store = _store()
    h = _sbx({"a": "1"}).commit_state(store)
    states_dir = store.base_dir / "states"
    leftover = states_dir / ".tmp-orphan"
    (leftover / "tree").mkdir(parents=True)

    removed = store.gc({h})

    assert removed == []                        # tmp dirs are not reported as states
    assert not leftover.exists()                # but they are swept
    assert store.has(h)


def test_partial_write_is_never_visible_as_present():
    sbx = _sbx({"a.txt": "hello"})
    store = _store()
    h = sbx.state_hash()

    # Simulate a crash during the atomic commit: the rename fails after the copy.
    with patch("agentic_runtime.state_store.os.replace", side_effect=OSError("crash")):
        try:
            sbx.commit_state(store)
        except OSError:
            pass

    assert not store.has(h)                      # final name never showed a partial
    assert not (store.base_dir / "states" / h).exists()


def test_bare_state_dir_without_tree_is_not_present():
    store = _store()
    states_dir = store.base_dir / "states"
    (states_dir / "deadbeef").mkdir(parents=True)  # dir exists, but no tree/

    assert not store.has("deadbeef")
