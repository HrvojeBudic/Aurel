"""
worldline.py — navigation over the world-line forest (M2 checkout, M3 fork).

A ``WorldLineForest`` sits over the persistent trace + the content-addressed
state store that share a ``base_dir``::

    base_dir/runs/<run_id>/events.jsonl   # governed transitions (edges)
    base_dir/states/<state_hash>/tree/…   # retained world-states (nodes)
    base_dir/forks.jsonl                  # hash-linked lineage edges (M3)

M2 provides ``checkout``: reconstruct the exact world-state produced by any
persisted ``state_transition`` into a fresh throwaway sandbox and prove it
matches the recorded ``after_state_hash``. It is strictly read-only.

M3 adds ``fork``: bind a **new** child run to a chosen parent transition (or the
parent's genesis) by a cryptographic ``ForkRef`` edge. The child run's event
ledger chains from a forked genesis ``sha(GENESIS, fork_hash)`` so parent and
child each verify as independent linear chains while the ``ForkRef`` (persisted
to ``forks.jsonl``) is the tamper-evident glue that makes lineage checkable. The
main line — snapshot/rollback and any non-forked run — is byte-for-byte
unchanged.
"""
from __future__ import annotations

import json
import tempfile
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Optional

from .core_types import canonical_json, new_id, now, sha
from .state_store import StateStore
from .trace import GENESIS, PersistentTraceLedger, _append_jsonl, _load_jsonl

__all__ = ["WorldLineForest", "CheckoutError", "ForkError", "ForkRef", "ForkResult"]

# A factory turning a fresh root path into a sandbox backend to materialize into.
SandboxFactory = Callable[[str], Any]


class CheckoutError(RuntimeError):
    """A checkout could not be satisfied (unknown/invalid entry, or missing CAS node)."""


class ForkError(RuntimeError):
    """A fork could not be minted (bad parent chain, missing CAS state, or hash mismatch)."""


# The six identity fields of a fork edge, in canonical order. ``fork_hash`` and
# ``child_genesis_hash`` are always recomputed from these — never stored-and-trusted.
_FORK_FIELDS = (
    "fork_id",
    "parent_run_id",
    "parent_entry_hash",
    "parent_state_hash",
    "child_run_id",
    "created_at",
)


@dataclass(frozen=True)
class ForkRef:
    """A tamper-evident lineage edge binding a child run to a parent transition.

    The six declared fields are the edge's identity; ``fork_hash`` and
    ``child_genesis_hash`` are *derived* and recomputed on every access from the
    stored values (never from a fresh ``now()``), so a persisted edge always
    recomputes to the same pair. ``child_genesis_hash`` is the genesis the child
    run's event chain hangs from — that is what welds the child to this edge.
    """

    fork_id: str
    parent_run_id: str
    parent_entry_hash: str
    parent_state_hash: str
    child_run_id: str
    created_at: float

    @property
    def fork_hash(self) -> str:
        return sha(canonical_json({f: getattr(self, f) for f in _FORK_FIELDS}))

    @property
    def child_genesis_hash(self) -> str:
        return sha(GENESIS, self.fork_hash)

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {f: getattr(self, f) for f in _FORK_FIELDS}
        d["fork_hash"] = self.fork_hash
        d["child_genesis_hash"] = self.child_genesis_hash
        return d

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "ForkRef":
        # Only the six identity fields are honored; derived hashes are recomputed,
        # so a tampered ``fork_hash``/``child_genesis_hash`` in the record cannot
        # masquerade as authentic — it will simply fail to match on re-derivation.
        return cls(**{f: d[f] for f in _FORK_FIELDS})


@dataclass
class ForkResult:
    """What ``WorldLineForest.fork`` returns: the edge, the child run id, the
    materialized child workspace, and an (empty) child ledger already chained
    from the forked genesis. Drive the child through the normal runtime by
    ``build_runtime(sandbox=result.sandbox, trace_run_id=result.child_run_id, …)``.
    """

    fork_ref: ForkRef
    child_run_id: str
    sandbox: Any
    child_ledger: PersistentTraceLedger


def _default_checkout_sandbox(root: str) -> Any:
    """Prefer a hard-isolated backend; fall back to a plain workspace.

    Checkout is a read-only *reconstruction* (no tool ever executes here), so an
    unsafe local workspace is an acceptable materialization target when no hard
    sandbox is available. The mutating paths (M3 fork execution) remain gated on
    real isolation elsewhere.
    """
    from .sandbox import BubblewrapSandbox, DockerSandbox, UnsafeLocalSandbox

    try:
        if BubblewrapSandbox.is_available():
            return BubblewrapSandbox(root=root)
    except Exception:
        pass
    try:
        if DockerSandbox.is_available():
            return DockerSandbox(root=root)
    except Exception:
        pass
    return UnsafeLocalSandbox(root=root)


class WorldLineForest:
    """Read-only view over runs + retained states under one ``base_dir``."""

    def __init__(self, base_dir: str) -> None:
        self.base_dir = Path(base_dir)
        self._runs_dir = self.base_dir / "runs"
        self._forks_path = self.base_dir / "forks.jsonl"
        self._store = StateStore(str(self.base_dir))
        # Serializes fork minting: read parent chain -> append edge -> build child
        # ledger as one atomic step so concurrent forks can't interleave ids/edges.
        self._lock = threading.RLock()

    def _events_path(self, run_id: str) -> Path:
        return self._runs_dir / run_id / "events.jsonl"

    def _metadata_path(self, run_id: str) -> Path:
        return self._runs_dir / run_id / "metadata.json"

    @property
    def store(self) -> StateStore:
        return self._store

    def forks(self) -> list[dict[str, Any]]:
        """All persisted lineage edges (raw dicts), oldest first."""
        return _load_jsonl(self._forks_path)

    def _find_transition(self, run_id: str, entry_hash: str) -> dict[str, Any]:
        events_path = self._events_path(run_id)
        if not events_path.exists():
            raise CheckoutError(f"unknown run {run_id!r} (no events at {events_path})")
        for event in _load_jsonl(events_path):
            if event.get("entry_hash") == entry_hash:
                if event.get("event_type") != "state_transition":
                    raise CheckoutError(
                        f"entry {entry_hash!r} is a {event.get('event_type')!r}, "
                        "not a state_transition; only state transitions carry a "
                        "checkout-able after_state_hash"
                    )
                return event
        raise CheckoutError(
            f"unknown transition {entry_hash!r} in run {run_id!r}"
        )

    def checkout(
        self,
        run_id: str,
        entry_hash: str,
        *,
        sandbox_factory: Optional[SandboxFactory] = None,
    ) -> Any:
        """Reconstruct a transition's post-state into a fresh sandbox.

        Locates the persisted ``state_transition`` with ``entry_hash``, reads its
        ``after_state_hash``, materializes that CAS node into a new throwaway
        sandbox root, and asserts the reconstructed ``state_hash()`` matches the
        recorded hash. Raises ``CheckoutError`` if the entry is missing, is not a
        state transition, or its state was never retained in the CAS.

        Read-only: nothing under ``base_dir`` is modified.
        """
        event = self._find_transition(run_id, entry_hash)
        after_state_hash = event.get("payload", {}).get("after_state_hash", "")
        if not after_state_hash:
            raise CheckoutError(
                f"transition {entry_hash!r} has no after_state_hash"
            )
        if not self._store.has(after_state_hash):
            raise CheckoutError(
                f"state {after_state_hash!r} for transition {entry_hash!r} is not "
                "retained in the CAS — re-run the source with retain_states=True"
            )

        factory = sandbox_factory or _default_checkout_sandbox
        new_root = tempfile.mkdtemp(prefix="ar_worldline_")
        sandbox = factory(new_root)
        self._store.materialize(after_state_hash, sandbox.root)

        reconstructed = sandbox.state_hash()
        if reconstructed != after_state_hash:
            raise CheckoutError(
                f"reconstructed state {reconstructed!r} does not match recorded "
                f"after_state_hash {after_state_hash!r} for transition {entry_hash!r}"
            )
        return sandbox

    # ----------------------------------------------------------------------- #
    #  Fork (M3) — mint a lineage-bound child run from a parent transition.
    # ----------------------------------------------------------------------- #
    def _run_metadata(self, run_id: str) -> dict[str, Any]:
        md_path = self._metadata_path(run_id)
        if not md_path.exists():
            raise ForkError(f"unknown parent run {run_id!r} (no metadata at {md_path})")
        return json.loads(md_path.read_text(encoding="utf-8"))

    def _parent_state_for_entry(
        self, run_id: str, entry_hash: str, md: dict[str, Any]
    ) -> str:
        """Resolve the parent world-state a fork at ``entry_hash`` branches from.

        Two cases: forking at the parent's genesis (``entry_hash`` equals the
        run's ``genesis_hash``) branches from the recorded ``initial_state_hash``;
        forking at a transition branches from that transition's ``after_state_hash``.
        """
        parent_genesis = md.get("genesis_hash", GENESIS)
        if entry_hash == parent_genesis:
            initial = md.get("initial_state_hash")
            if not initial:
                raise ForkError(
                    f"fork-from-genesis of run {run_id!r} needs a retained initial "
                    "state — re-run the parent with retain_states=True"
                )
            return initial
        try:
            event = self._find_transition(run_id, entry_hash)
        except CheckoutError as exc:  # normalize to the fork error surface
            raise ForkError(str(exc)) from exc
        after_state_hash = event.get("payload", {}).get("after_state_hash", "")
        if not after_state_hash:
            raise ForkError(f"transition {entry_hash!r} has no after_state_hash")
        return after_state_hash

    def fork(
        self,
        run_id: str,
        entry_hash: str,
        *,
        sandbox_factory: Optional[SandboxFactory] = None,
    ) -> ForkResult:
        """Mint a new child run bound to parent ``run_id`` at ``entry_hash``.

        Under the forest lock: verify the parent chain, resolve and assert the
        parent world-state exists in the CAS and reconstructs to its hash, mint a
        fresh child ``run_id`` / ``fork_id`` / ``created_at``, persist the
        ``ForkRef`` edge to ``forks.jsonl`` (append + fsync) **before** building
        the child ledger, then create the child ledger chained from the forked
        genesis. Returns a :class:`ForkResult`.

        ``entry_hash`` may be a ``state_transition`` entry hash or the parent
        run's genesis hash (fork-from-genesis, via the M1 ``initial_state_hash``).
        Read-only with respect to the parent; the only writes are the new child
        run and the appended fork edge.
        """
        with self._lock:
            # 1. Parent must exist and verify as an independent linear chain.
            md = self._run_metadata(run_id)
            parent_report = PersistentTraceLedger(
                base_dir=str(self.base_dir), run_id=run_id
            ).verify_persisted()
            if not parent_report["ok"]:
                raise ForkError(
                    f"parent run {run_id!r} does not verify: {parent_report['reason']!r}"
                )

            # 2. Resolve the parent world-state and assert it is retained + exact.
            parent_state_hash = self._parent_state_for_entry(run_id, entry_hash, md)
            if not self._store.has(parent_state_hash):
                raise ForkError(
                    f"parent state {parent_state_hash!r} for entry {entry_hash!r} is "
                    "not retained in the CAS — re-run the parent with retain_states=True"
                )

            # 3. Materialize the child workspace and prove it hashes to the parent.
            factory = sandbox_factory or _default_checkout_sandbox
            new_root = tempfile.mkdtemp(prefix="ar_fork_")
            sandbox = factory(new_root)
            self._store.materialize(parent_state_hash, sandbox.root)
            reconstructed = sandbox.state_hash()
            if reconstructed != parent_state_hash:
                raise ForkError(
                    f"materialized child state {reconstructed!r} does not match parent "
                    f"state {parent_state_hash!r}"
                )

            # 4. Mint identity and bind the edge. Persist it BEFORE the child
            #    ledger so a crash can never leave a child run with no lineage.
            child_run_id = new_id("run")
            fork_ref = ForkRef(
                fork_id=new_id("fork"),
                parent_run_id=run_id,
                parent_entry_hash=entry_hash,
                parent_state_hash=parent_state_hash,
                child_run_id=child_run_id,
                created_at=now(),
            )
            _append_jsonl(self._forks_path, fork_ref.to_dict())

            # 5. Build the child ledger chained from the forked genesis.
            child_ledger = PersistentTraceLedger(
                base_dir=str(self.base_dir),
                run_id=child_run_id,
                parent_ref=fork_ref,
            )
            return ForkResult(
                fork_ref=fork_ref,
                child_run_id=child_run_id,
                sandbox=sandbox,
                child_ledger=child_ledger,
            )
