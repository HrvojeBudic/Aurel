"""
state_store.py — Content-addressed state store (CAS) for the world-line DAG (M0).

A ``StateStore`` retains governed world-states keyed by their content hash. The
address is byte-identical to ``SandboxBackend.state_hash()`` because both use the
same ``_tree_hash`` function — a state committed here can be looked up by the
exact ``before_state_hash`` / ``after_state_hash`` already recorded in the trace.

This is **additive and retained**. It does not touch the sandbox's ephemeral
``snapshot`` / ``rollback`` path; that linear rollback machinery is unchanged.
M0 provides only storage primitives (``put`` / ``has`` / ``materialize`` / ``gc``);
checkout, fork, and replay build on top of these in later milestones.

On-disk layout::

    base_dir/states/<state_hash>/tree/…      # one dedup'd copy per unique state
    base_dir/states/.tmp-<uuid>/             # in-flight write, promoted atomically

Crash-safety: a state is written to a ``.tmp-*`` directory, fsynced, then
atomically ``os.replace``d onto its final ``<state_hash>`` name. ``has()`` only
reports a state present once ``<state_hash>/tree`` exists, so a half-written
state (still under ``.tmp-*``, or interrupted before the rename) is never visible
as present.
"""
from __future__ import annotations

import os
import shutil
from pathlib import Path
from uuid import uuid4

from .sandbox import _tree_hash

__all__ = ["StateStore"]

_TMP_PREFIX = ".tmp-"


def _fsync_dir(path: str) -> None:
    """Best-effort fsync of a directory entry so a rename is durable."""
    try:
        fd = os.open(path, os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
    except OSError:
        pass


def _fsync_tree(root: str) -> None:
    """Best-effort fsync of every file and directory under ``root``."""
    for dirpath, _dirnames, filenames in os.walk(root):
        for fn in filenames:
            try:
                fd = os.open(os.path.join(dirpath, fn), os.O_RDONLY)
                try:
                    os.fsync(fd)
                finally:
                    os.close(fd)
            except OSError:
                pass
        _fsync_dir(dirpath)


class StateStore:
    """Content-addressed store of governed world-states.

    The store is created lazily: no directory is written until the first
    ``put``. All addresses are ``_tree_hash`` digests, identical to
    ``SandboxBackend.state_hash()``.
    """

    def __init__(self, base_dir: str) -> None:
        self.base_dir = Path(base_dir)
        self._states_dir = self.base_dir / "states"

    def _state_dir(self, state_hash: str) -> Path:
        return self._states_dir / state_hash

    def _reject_nested(self, root: str) -> None:
        """Raise when this store sits inside the tree being stored."""
        try:
            tree = Path(root).resolve()
            store = self.base_dir.resolve()
        except OSError:
            return
        if store == tree or store.is_relative_to(tree):
            raise ValueError(
                f"state store base_dir {store} is inside the workspace {tree}; "
                "each retained state would copy every previous state into the "
                "next one. Point the trace/state directory outside the "
                "workspace (e.g. AUREL_TRACE_DIR=~/.aurel/traces)."
            )

    def has(self, state_hash: str) -> bool:
        """True only for a fully materialized state (its ``tree/`` exists)."""
        return (self._state_dir(state_hash) / "tree").is_dir()

    def put(self, root: str) -> str:
        """Store the tree at ``root`` keyed by its content hash; return the hash.

        Dedup: if the state is already present this is a no-op (no copy, no new
        directory). The copy is written to a temp directory, fsynced, then
        atomically renamed onto its final name so a crash can never leave a
        partial state visible via ``has()``.
        """
        # Fail closed when the store lives inside the tree it is asked to store.
        # Every put would then copy the accumulated states into the next state:
        # the tree grows without bound and eventually dies deep in copytree with
        # a bare "File name too long". The address is `_tree_hash`, which walks
        # everything by design (it must match the sandbox's recorded
        # before/after hashes), so this cannot be fixed by ignoring paths during
        # the copy — that would store a tree whose content no longer matches its
        # own address. The fix is a base_dir outside the workspace.
        self._reject_nested(root)

        state_hash = _tree_hash(root)
        if self.has(state_hash):
            return state_hash

        self._states_dir.mkdir(parents=True, exist_ok=True)
        tmp = self._states_dir / f"{_TMP_PREFIX}{uuid4().hex}"
        try:
            shutil.copytree(root, tmp / "tree")
            _fsync_tree(str(tmp))
            try:
                os.replace(tmp, self._state_dir(state_hash))
            except OSError:
                # Lost a dedup race (another writer promoted the same hash), or
                # the final name already exists — treat an existing state as
                # present; otherwise re-raise the real failure.
                if self.has(state_hash):
                    return state_hash
                raise
            _fsync_dir(str(self._states_dir))
        finally:
            if tmp.exists():
                shutil.rmtree(tmp, ignore_errors=True)
        return state_hash

    def materialize(self, state_hash: str, dest_root: str) -> None:
        """Reconstruct a stored state into ``dest_root``.

        ``dest_root`` should be empty/fresh for the reconstructed tree to hash
        back to ``state_hash``. Raises ``KeyError`` if the state is absent.
        """
        src = self._state_dir(state_hash) / "tree"
        if not src.is_dir():
            raise KeyError(f"unknown state {state_hash}")
        os.makedirs(dest_root, exist_ok=True)
        shutil.copytree(src, dest_root, dirs_exist_ok=True)

    def gc(self, live: set[str]) -> list[str]:
        """Mark-sweep: remove every stored state whose hash is not in ``live``.

        In-flight/crash-leftover ``.tmp-*`` directories are always removed (they
        are never live). Returns the list of state hashes actually removed.
        """
        removed: list[str] = []
        if not self._states_dir.is_dir():
            return removed
        for entry in self._states_dir.iterdir():
            name = entry.name
            if name.startswith(_TMP_PREFIX):
                shutil.rmtree(entry, ignore_errors=True)
                continue
            if name not in live:
                shutil.rmtree(entry, ignore_errors=True)
                removed.append(name)
        return removed
