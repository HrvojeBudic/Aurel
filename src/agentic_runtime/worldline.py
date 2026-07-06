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
import shutil
import tempfile
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Optional

from .core_types import canonical_json, new_id, now, sha
from .sandbox import _tree_hash
from .state_store import StateStore
from .trace import GENESIS, PersistentTraceLedger, _append_jsonl, _load_jsonl

__all__ = [
    "WorldLineForest",
    "CheckoutError",
    "ForkError",
    "ForkRef",
    "ForkResult",
    "MergeError",
    "MergeConflict",
    "MergeRef",
    "MergeResult",
    "verify_fork",
    "verify_merge",
]


def _merkle(leaves: list[str]) -> str:
    """Binary merkle fold (odd node duplicated), matching the trace ledger's."""
    if not leaves:
        return GENESIS
    layer = list(leaves)
    while len(layer) > 1:
        nxt: list[str] = []
        for i in range(0, len(layer), 2):
            a = layer[i]
            b = layer[i + 1] if i + 1 < len(layer) else layer[i]
            nxt.append(sha(a, b))
        layer = nxt
    return layer[0]

# A factory turning a fresh root path into a sandbox backend to materialize into.
SandboxFactory = Callable[[str], Any]


class CheckoutError(RuntimeError):
    """A checkout could not be satisfied (unknown/invalid entry, or missing CAS node)."""


class ForkError(RuntimeError):
    """A fork could not be minted (bad parent chain, missing CAS state, or hash mismatch)."""


class MergeError(RuntimeError):
    """A merge could not be performed (unverified/unretained branch, or bad lineage)."""


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


# The identity fields of a merge edge, in canonical order. ``merge_hash`` is
# always recomputed from these — never stored-and-trusted (mirrors ForkRef).
_MERGE_FIELDS = (
    "merge_id",
    "parent_run_id",
    "child_run_ids",
    "base_state_hash",
    "merged_state_hash",
    "child_head_hashes",
    "strategy",
    "created_at",
)


@dataclass(frozen=True)
class MergeRef:
    """A tamper-evident edge welding sibling branches back into one world-state.

    The dual of :class:`ForkRef`: where a fork records a branch *out* of a
    parent state, a merge records sibling child runs rejoining *into* one merged
    state. ``merge_hash`` is derived from the identity fields and recomputed on
    every access, so a persisted edge always recomputes to the same value and a
    tampered stored hash cannot masquerade as authentic.
    """

    merge_id: str
    parent_run_id: str
    child_run_ids: tuple[str, ...]
    base_state_hash: str
    merged_state_hash: str
    child_head_hashes: tuple[str, ...]
    strategy: str
    created_at: float

    @property
    def merge_hash(self) -> str:
        return sha(canonical_json({
            "merge_id": self.merge_id,
            "parent_run_id": self.parent_run_id,
            "child_run_ids": list(self.child_run_ids),
            "base_state_hash": self.base_state_hash,
            "merged_state_hash": self.merged_state_hash,
            "child_head_hashes": list(self.child_head_hashes),
            "strategy": self.strategy,
            "created_at": self.created_at,
        }))

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "merge_id": self.merge_id,
            "parent_run_id": self.parent_run_id,
            "child_run_ids": list(self.child_run_ids),
            "base_state_hash": self.base_state_hash,
            "merged_state_hash": self.merged_state_hash,
            "child_head_hashes": list(self.child_head_hashes),
            "strategy": self.strategy,
            "created_at": self.created_at,
        }
        d["merge_hash"] = self.merge_hash
        return d

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "MergeRef":
        return cls(
            merge_id=d["merge_id"],
            parent_run_id=d["parent_run_id"],
            child_run_ids=tuple(d["child_run_ids"]),
            base_state_hash=d["base_state_hash"],
            merged_state_hash=d["merged_state_hash"],
            child_head_hashes=tuple(d["child_head_hashes"]),
            strategy=d["strategy"],
            created_at=d["created_at"],
        )


@dataclass(frozen=True)
class MergeConflict:
    """A path written by more than one branch with divergent content."""

    path: str
    child_run_ids: tuple[str, ...]


@dataclass(frozen=True)
class MergeResult:
    """Outcome of a merge attempt: CLEAN with a merged state, or CONFLICT.

    On CLEAN the ``merge_ref`` is persisted and ``merged_state_hash`` names the
    unified world-state in the CAS. On CONFLICT nothing is persisted, an operator
    must resolve, and ``conflicts`` lists the contended paths — the flow layer
    turns this into a PAUSED join.
    """

    status: str  # "CLEAN" | "CONFLICT"
    parent_run_id: str
    child_run_ids: tuple[str, ...]
    base_state_hash: str
    merged_state_hash: Optional[str]
    merge_ref: Optional[MergeRef]
    conflicts: tuple[MergeConflict, ...]

    @property
    def clean(self) -> bool:
        return self.status == "CLEAN"

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "parent_run_id": self.parent_run_id,
            "child_run_ids": list(self.child_run_ids),
            "base_state_hash": self.base_state_hash,
            "merged_state_hash": self.merged_state_hash,
            "merge_ref": self.merge_ref.to_dict() if self.merge_ref else None,
            "conflicts": [
                {"path": c.path, "child_run_ids": list(c.child_run_ids)}
                for c in self.conflicts
            ],
        }


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
        self._merges_path = self.base_dir / "merges.jsonl"
        self._branches_path = self.base_dir / "branches.jsonl"
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

    # ----------------------------------------------------------------------- #
    #  Merge (M4) — weld sibling branches back into one world-state.
    # ----------------------------------------------------------------------- #
    def merges(self) -> list[dict[str, Any]]:
        """All persisted merge edges (raw dicts), oldest first."""
        return _load_jsonl(self._merges_path)

    def _fork_index(self) -> dict[str, dict[str, Any]]:
        return {e["child_run_id"]: e for e in self.forks()}

    def _child_base_state(self, child_run_id: str, fork_index: dict[str, dict]) -> str:
        edge = fork_index.get(child_run_id)
        if edge is None:
            raise MergeError(
                f"run {child_run_id!r} is not a forked child (no lineage edge); "
                "only sibling forks of a common base can be merged"
            )
        return edge["parent_state_hash"]

    def merge(
        self,
        parent_run_id: str,
        child_run_ids: "list[str] | tuple[str, ...]",
        *,
        strategy: str = "disjoint_paths",
    ) -> MergeResult:
        """Merge sibling forked children back into one world-state.

        Preconditions (fail-closed): at least one child; every child verifies as
        a persisted chain; every child forked from the *same* base state; every
        child's head world-state is retained in the CAS. The ``disjoint_paths``
        strategy unions the branches' writes: paths touched by only one branch
        merge automatically; a path written divergently by two branches is a
        :class:`MergeConflict` and the merge returns CONFLICT without persisting.

        On CLEAN the merged tree is stored in the CAS and a :class:`MergeRef` is
        appended to ``merges.jsonl`` (the dual of ``forks.jsonl``); the sealed
        parent and child ledgers are never mutated.
        """
        if strategy != "disjoint_paths":
            raise MergeError(f"unsupported merge strategy {strategy!r}")
        children = tuple(sorted(child_run_ids))
        if not children:
            raise MergeError("merge needs at least one child run")

        with self._lock:
            fork_index = self._fork_index()

            # 1. Common base: every child must fork from the same base state.
            bases = {self._child_base_state(c, fork_index) for c in children}
            if len(bases) != 1:
                raise MergeError(
                    "children do not share a common fork base state; "
                    f"found {len(bases)} distinct bases"
                )
            base_state_hash = bases.pop()
            if not self._store.has(base_state_hash):
                raise MergeError(
                    f"base state {base_state_hash!r} is not retained in the CAS"
                )

            # 2. Every child must verify and expose a retained head state.
            child_heads: dict[str, str] = {}
            child_head_hashes: list[str] = []
            for c in children:
                rep = PersistentTraceLedger(
                    base_dir=str(self.base_dir), run_id=c
                ).verify_persisted()
                if not rep["ok"]:
                    raise MergeError(f"child {c!r} does not verify: {rep['reason']!r}")
                head_state = self._run_head_state(c) or base_state_hash
                if not self._store.has(head_state):
                    raise MergeError(
                        f"child {c!r} head state {head_state!r} not retained in the "
                        "CAS — run the child with retain_states=True"
                    )
                child_heads[c] = head_state
                child_head_hashes.append(self._run_head(c))

            # 3. Diff each child against the base; detect path-level conflicts.
            base_files = _read_tree(self._store, base_state_hash)
            per_child_changes: dict[str, dict[str, bytes]] = {}
            for c in children:
                child_files = _read_tree(self._store, child_heads[c])
                per_child_changes[c] = _tree_delta(base_files, child_files)

            writers: dict[str, list[str]] = {}
            for c, changes in per_child_changes.items():
                for path in changes:
                    writers.setdefault(path, []).append(c)
            conflicts: list[MergeConflict] = []
            for path, cs in writers.items():
                if len(cs) > 1:
                    contents = {per_child_changes[c].get(path) for c in cs}
                    if len(contents) > 1:  # divergent writes to the same path
                        conflicts.append(MergeConflict(path=path, child_run_ids=tuple(sorted(cs))))
            if conflicts:
                return MergeResult(
                    status="CONFLICT",
                    parent_run_id=parent_run_id,
                    child_run_ids=children,
                    base_state_hash=base_state_hash,
                    merged_state_hash=None,
                    merge_ref=None,
                    conflicts=tuple(sorted(conflicts, key=lambda x: x.path)),
                )

            # 4. Build the merged tree = base + every branch's writes; store it.
            merged_state_hash = _materialize_merged(
                self._store, base_state_hash, per_child_changes
            )

            # 5. Persist the merge edge (dual of a fork edge).
            merge_ref = MergeRef(
                merge_id=new_id("merge"),
                parent_run_id=parent_run_id,
                child_run_ids=children,
                base_state_hash=base_state_hash,
                merged_state_hash=merged_state_hash,
                child_head_hashes=tuple(child_head_hashes),
                strategy=strategy,
                created_at=now(),
            )
            _append_jsonl(self._merges_path, merge_ref.to_dict())
            return MergeResult(
                status="CLEAN",
                parent_run_id=parent_run_id,
                child_run_ids=children,
                base_state_hash=base_state_hash,
                merged_state_hash=merged_state_hash,
                merge_ref=merge_ref,
                conflicts=(),
            )

    def branch_and_merge(
        self,
        parent_run_id: str,
        parent_entry_hash: str,
        branch_drivers: "list[Callable[[ForkResult], Any]] | tuple[Callable[[ForkResult], Any], ...]",
        *,
        strategy: str = "disjoint_paths",
        sandbox_factory: Optional[SandboxFactory] = None,
    ) -> MergeResult:
        """Fork one child per branch, drive each, then merge at the join.

        This is the integrated fork→branch→merge lifecycle: each ``driver`` gets
        a :class:`ForkResult` and is expected to drive that child run through the
        normal runtime (``build_runtime(sandbox=res.sandbox,
        trace_run_id=res.child_run_id, retain_states=True, …)``) and seal it. The
        join is a :meth:`merge`. Branches run sequentially in v1; because each
        child has its own ledger and sandbox clone, swapping in threads or
        processes changes nothing about correctness — there is no shared writer.
        """
        child_ids: list[str] = []
        for drive in branch_drivers:
            res = self.fork(parent_run_id, parent_entry_hash, sandbox_factory=sandbox_factory)
            drive(res)
            child_ids.append(res.child_run_id)
        return self.merge(parent_run_id, child_ids, strategy=strategy)

    # ----------------------------------------------------------------------- #
    #  Forest integrity, GC, and named branches (M4).
    # ----------------------------------------------------------------------- #
    def _run_ids(self) -> list[str]:
        """Every persisted run id (a run dir carrying a metadata.json)."""
        if not self._runs_dir.is_dir():
            return []
        return sorted(
            p.name for p in self._runs_dir.iterdir()
            if (p / "metadata.json").exists()
        )

    def _run_head(self, run_id: str) -> str:
        """The head chain hash of a run (last event, or its genesis if empty)."""
        events = _load_jsonl(self._events_path(run_id))
        if events:
            return events[-1]["entry_hash"]
        md = self._run_metadata(run_id)
        return md.get("genesis_hash", GENESIS)

    def _run_head_state(self, run_id: str) -> Optional[str]:
        """The head *world-state* of a run: the after_state_hash of its last
        state_transition (None if the run made no transitions)."""
        last: Optional[str] = None
        for ev in _load_jsonl(self._events_path(run_id)):
            if ev.get("event_type") == "state_transition":
                after = ev.get("payload", {}).get("after_state_hash")
                if after:
                    last = after
        return last

    def branches(self) -> dict[str, dict[str, Any]]:
        """Current named branches (last write wins per name)."""
        out: dict[str, dict[str, Any]] = {}
        for rec in _load_jsonl(self._branches_path):
            out[rec["name"]] = rec
        return out

    def name_branch(self, name: str, run_id: str, entry_hash: str) -> dict[str, Any]:
        """Name a branch head pointing at ``run_id`` @ ``entry_hash``.

        Resolves the world-state the entry produced (a transition's
        ``after_state_hash``, or the run's ``initial_state_hash`` for a
        genesis pointer) and records it so GC keeps that state reachable.
        """
        md = self._run_metadata(run_id)
        state_hash = self._parent_state_for_entry(run_id, entry_hash, md)
        rec = {
            "name": name,
            "run_id": run_id,
            "entry_hash": entry_hash,
            "state_hash": state_hash,
            "created_at": now(),
        }
        _append_jsonl(self._branches_path, rec)
        return rec

    def forest_root(self) -> str:
        """Merkle root over the sorted union of run heads and fork hashes.

        A single digest that changes if any run's head moves or any lineage
        edge is added or altered — the forest's tamper-evident summary.
        """
        run_heads = [self._run_head(r) for r in self._run_ids()]
        fork_hashes = [ForkRef.from_dict(e).fork_hash for e in self.forks()]
        merge_hashes = [MergeRef.from_dict(e).merge_hash for e in self.merges()]
        leaves = sorted(set(run_heads) | set(fork_hashes) | set(merge_hashes))
        return _merkle(leaves)

    def live_states(self, pins: Any = ()) -> set[str]:
        """The reachable world-state set: branch heads, run heads, every fork's
        ``parent_state_hash`` (so no fork is ever orphaned), plus ``pins``."""
        live: set[str] = set(pins)
        for br in self.branches().values():
            if br.get("state_hash"):
                live.add(br["state_hash"])
        for run_id in self._run_ids():
            head_state = self._run_head_state(run_id)
            if head_state:
                live.add(head_state)
        for edge in self.forks():
            psh = edge.get("parent_state_hash")
            if psh:
                live.add(psh)
        # Merge edges keep their base and merged states reachable so a merged
        # world-line can always be reconstructed and re-verified.
        for edge in self.merges():
            for key in ("base_state_hash", "merged_state_hash"):
                sh = edge.get(key)
                if sh:
                    live.add(sh)
        return live

    def gc(self, pins: Any = ()) -> list[str]:
        """Mark-sweep the CAS to the reachable set (see :meth:`live_states`).

        Returns the state hashes removed. Fork parent-states are always live, so
        collecting never breaks a lineage that was actually retained.
        """
        return self._store.gc(self.live_states(pins))

    def verify(self) -> dict[str, Any]:
        """Verify the whole forest: every run's linear chain, then every fork
        edge's C1–C7 (topologically, ancestors first, cycle-guarded), and
        return the ``forest_root`` when whole.
        """
        forks = self.forks()
        index = {e["child_run_id"]: e for e in forks}
        for run_id in self._run_ids():
            rep = PersistentTraceLedger(
                base_dir=str(self.base_dir), run_id=run_id
            ).verify_persisted()
            if not rep["ok"]:
                return {
                    "ok": False,
                    "stage": "run",
                    "run_id": run_id,
                    "reason": rep["reason"],
                }
        for edge in forks:
            res = verify_fork(edge, str(self.base_dir), self._store, forks_index=index)
            if not res["ok"]:
                return {
                    "ok": False,
                    "stage": "fork",
                    "fork_id": edge.get("fork_id"),
                    "failed_check": res.get("failed_check"),
                    "reason": res.get("reason"),
                }
        merges = self.merges()
        for edge in merges:
            res = verify_merge(edge, str(self.base_dir), self._store, forks_index=index)
            if not res["ok"]:
                return {
                    "ok": False,
                    "stage": "merge",
                    "merge_id": edge.get("merge_id"),
                    "failed_check": res.get("failed_check"),
                    "reason": res.get("reason"),
                }
        return {
            "ok": True,
            "reason": "",
            "run_count": len(self._run_ids()),
            "fork_count": len(forks),
            "merge_count": len(merges),
            "forest_root": self.forest_root(),
        }


def _read_tree(store: StateStore, state_hash: str) -> dict[str, bytes]:
    """Materialize a CAS state and return {relative_path: content_bytes}."""
    tmp = tempfile.mkdtemp(prefix="ar_merge_read_")
    try:
        store.materialize(state_hash, tmp)
        out: dict[str, bytes] = {}
        root = Path(tmp)
        for p in sorted(root.rglob("*")):
            if p.is_file():
                out[str(p.relative_to(root))] = p.read_bytes()
        return out
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _tree_delta(base: dict[str, bytes], child: dict[str, bytes]) -> dict[str, bytes]:
    """Files the child added or changed relative to base. Deletions are ignored
    in v1 (disjoint_paths merges additive/edit writes, not removals)."""
    delta: dict[str, bytes] = {}
    for path, content in child.items():
        if base.get(path) != content:
            delta[path] = content
    return delta


def _materialize_merged(
    store: StateStore,
    base_state_hash: str,
    per_child_changes: dict[str, dict[str, bytes]],
) -> str:
    """Apply every branch's writes onto the base tree and store the result."""
    tmp = tempfile.mkdtemp(prefix="ar_merge_build_")
    try:
        store.materialize(base_state_hash, tmp)
        root = Path(tmp)
        for changes in per_child_changes.values():
            for rel, content in changes.items():
                dest = root / rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(content)
        return store.put(tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def verify_merge(
    merge_dict: dict[str, Any],
    base_dir: str,
    store: StateStore,
    *,
    forks_index: Optional[dict[str, dict[str, Any]]] = None,
) -> dict[str, Any]:
    """Verify a single merge edge against checks M1–M5.

    M1 recompute ``merge_hash`` from the stored fields; M2 each child is a forked
    run whose base state equals the recorded ``base_state_hash``; M3 the merged
    state is retained and materializes back to its hash; M4 every child chain
    verifies; M5 recomputing the disjoint-path merge from base + child heads
    reproduces exactly ``merged_state_hash`` (no hidden edits smuggled in).
    """
    base = Path(base_dir)
    if forks_index is None:
        forks_index = {e["child_run_id"]: e for e in _load_jsonl(base / "forks.jsonl")}
    ref = MergeRef.from_dict(merge_dict)
    mid = merge_dict.get("merge_id")

    def fail(check: str, reason: str) -> dict[str, Any]:
        return {"ok": False, "failed_check": check, "reason": reason, "merge_id": mid}

    # M1
    if ref.merge_hash != merge_dict.get("merge_hash"):
        return fail("M1", "merge_hash does not recompute from stored fields")

    # M2 — common base lineage.
    for c in ref.child_run_ids:
        edge = forks_index.get(c)
        if edge is None:
            return fail("M2", f"merged child {c!r} has no fork lineage")
        if edge.get("parent_state_hash") != ref.base_state_hash:
            return fail("M2", f"child {c!r} base != recorded merge base_state_hash")

    # M3 — merged state retained and exact.
    if not store.has(ref.merged_state_hash):
        return fail("M3", f"merged state {ref.merged_state_hash!r} not retained")
    tmp = tempfile.mkdtemp(prefix="ar_verify_merge_")
    try:
        store.materialize(ref.merged_state_hash, tmp)
        if _tree_hash(tmp) != ref.merged_state_hash:
            return fail("M3", "materialized merged state does not hash to merged_state_hash")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    # M4 — every child chain verifies.
    for c in ref.child_run_ids:
        rep = PersistentTraceLedger(base_dir=base_dir, run_id=c).verify_persisted()
        if not rep["ok"]:
            return fail("M4", f"child {c!r} does not verify: {rep['reason']!r}")

    # M5 — recompute the merge deterministically and require an exact match.
    if not store.has(ref.base_state_hash):
        return fail("M5", "base state not retained; cannot recompute merge")
    base_files = _read_tree(store, ref.base_state_hash)
    per_child: dict[str, dict[str, bytes]] = {}
    for c in ref.child_run_ids:
        head = _run_head_state_of(base_dir, c) or ref.base_state_hash
        if not store.has(head):
            return fail("M5", f"child {c!r} head state not retained")
        per_child[c] = _tree_delta(base_files, _read_tree(store, head))
    recomputed = _materialize_merged(store, ref.base_state_hash, per_child)
    if recomputed != ref.merged_state_hash:
        return fail("M5", "recomputed merge != recorded merged_state_hash")

    return {"ok": True, "failed_check": None, "reason": "", "merge_id": mid}


def _run_head_state_of(base_dir: str, run_id: str) -> Optional[str]:
    """Standalone head-state lookup for a run (used by verify_merge)."""
    last: Optional[str] = None
    for ev in _load_jsonl(Path(base_dir) / "runs" / run_id / "events.jsonl"):
        if ev.get("event_type") == "state_transition":
            after = ev.get("payload", {}).get("after_state_hash")
            if after:
                last = after
    return last


def verify_fork(
    fork_dict: dict[str, Any],
    base_dir: str,
    store: StateStore,
    *,
    forks_index: Optional[dict[str, dict[str, Any]]] = None,
    _stack: frozenset = frozenset(),
) -> dict[str, Any]:
    """Verify a single lineage edge against checks C1–C7.

    C1 recompute ``fork_hash`` from the stored six fields; C2 recompute
    ``child_genesis_hash`` and match both the stored value and the child run's
    metadata genesis; C3 the parent CAS state exists and materializes back to
    its hash; C4 the parent entry is a ``state_transition`` whose
    ``after_state_hash`` equals ``parent_state_hash`` (or, for a genesis pointer,
    equals the parent run's ``initial_state_hash``); C5 the parent run verifies
    as a linear chain; C6 the child chain verifies from its forked genesis; C7 if
    the parent is itself a child in ``forks.jsonl`` that ancestor edge passes
    C1–C6 first (recursion is ancestor-first and cycle-guarded).

    Returns ``{"ok": bool, "failed_check": str|None, "reason": str, "fork_id": ...}``.
    """
    base = Path(base_dir)
    if forks_index is None:
        forks_index = {e["child_run_id"]: e for e in _load_jsonl(base / "forks.jsonl")}

    ref = ForkRef.from_dict(fork_dict)
    fid = fork_dict.get("fork_id")

    def fail(check: str, reason: str) -> dict[str, Any]:
        return {"ok": False, "failed_check": check, "reason": reason, "fork_id": fid}

    # cycle guard (C7): a lineage that loops back onto a run already on the path
    if ref.child_run_id in _stack:
        return fail("C7", f"cycle in fork lineage at child {ref.child_run_id!r}")
    stack = _stack | {ref.child_run_id}

    # C1 — fork_hash recomputes from the stored identity fields.
    if ref.fork_hash != fork_dict.get("fork_hash"):
        return fail("C1", "fork_hash does not recompute from stored fields")

    # C2 — child_genesis recomputes and matches stored + child metadata.
    if ref.child_genesis_hash != fork_dict.get("child_genesis_hash"):
        return fail("C2", "child_genesis_hash does not recompute from stored fields")
    child_md_path = base / "runs" / ref.child_run_id / "metadata.json"
    if not child_md_path.exists():
        return fail("C2", f"child run {ref.child_run_id!r} has no metadata")
    child_md = json.loads(child_md_path.read_text(encoding="utf-8"))
    if child_md.get("genesis_hash") != ref.child_genesis_hash:
        return fail("C2", "child metadata genesis_hash != recomputed child_genesis")

    # C3 — the parent world-state is retained and materializes back to its hash.
    if not store.has(ref.parent_state_hash):
        return fail(
            "C3",
            f"parent state {ref.parent_state_hash!r} not retained in the CAS "
            "(never retained or garbage-collected) — lineage UNVERIFIABLE",
        )
    tmp = tempfile.mkdtemp(prefix="ar_verify_fork_")
    try:
        store.materialize(ref.parent_state_hash, tmp)
        if _tree_hash(tmp) != ref.parent_state_hash:
            return fail("C3", "materialized parent state does not hash to parent_state_hash")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    # C4 — the parent entry anchors the claimed parent state.
    parent_md_path = base / "runs" / ref.parent_run_id / "metadata.json"
    if not parent_md_path.exists():
        return fail("C4", f"parent run {ref.parent_run_id!r} has no metadata")
    parent_md = json.loads(parent_md_path.read_text(encoding="utf-8"))
    parent_genesis = parent_md.get("genesis_hash", GENESIS)
    if ref.parent_entry_hash == parent_genesis:
        if parent_md.get("initial_state_hash") != ref.parent_state_hash:
            return fail("C4", "fork-from-genesis parent_state_hash != parent initial_state_hash")
    else:
        events = _load_jsonl(base / "runs" / ref.parent_run_id / "events.jsonl")
        ev = next((e for e in events if e.get("entry_hash") == ref.parent_entry_hash), None)
        if ev is None:
            return fail("C4", f"parent entry {ref.parent_entry_hash!r} not found in parent run")
        if ev.get("event_type") != "state_transition":
            return fail("C4", "parent entry is not a state_transition")
        if ev.get("payload", {}).get("after_state_hash") != ref.parent_state_hash:
            return fail("C4", "parent transition after_state_hash != parent_state_hash")

    # C7 — if the parent is itself a child edge, it must pass C1–C6 first.
    parent_edge = forks_index.get(ref.parent_run_id)
    if parent_edge is not None:
        sub = verify_fork(parent_edge, base_dir, store, forks_index=forks_index, _stack=stack)
        if not sub["ok"]:
            return fail(
                "C7",
                f"ancestor fork {parent_edge.get('fork_id')!r} failed "
                f"{sub.get('failed_check')}: {sub.get('reason')}",
            )

    # C5 — the parent run verifies as an independent linear chain.
    parent_report = PersistentTraceLedger(
        base_dir=base_dir, run_id=ref.parent_run_id
    ).verify_persisted()
    if not parent_report["ok"]:
        return fail("C5", f"parent run {ref.parent_run_id!r} does not verify: {parent_report['reason']!r}")

    # C6 — the child run verifies from its forked genesis.
    child_report = PersistentTraceLedger(
        base_dir=base_dir, run_id=ref.child_run_id
    ).verify_persisted()
    if not child_report["ok"]:
        return fail("C6", f"child run {ref.child_run_id!r} does not verify: {child_report['reason']!r}")

    return {"ok": True, "failed_check": None, "reason": "", "fork_id": fid}
