"""
worldline.py — read-only navigation over the world-line forest (M2: checkout).

A ``WorldLineForest`` sits over the persistent trace + the content-addressed
state store that share a ``base_dir``::

    base_dir/runs/<run_id>/events.jsonl   # governed transitions (edges)
    base_dir/states/<state_hash>/tree/…   # retained world-states (nodes)

M2 provides ``checkout`` only: reconstruct the exact world-state produced by any
persisted ``state_transition`` into a fresh throwaway sandbox and prove it
matches the recorded ``after_state_hash``. It is strictly read-only — it never
mutates any run, trace, or stored state; it only materializes a new sandbox.

Fork (M3) builds on this; no fork logic lives here.
"""
from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any, Callable, Optional

from .state_store import StateStore
from .trace import _load_jsonl

__all__ = ["WorldLineForest", "CheckoutError"]

# A factory turning a fresh root path into a sandbox backend to materialize into.
SandboxFactory = Callable[[str], Any]


class CheckoutError(RuntimeError):
    """A checkout could not be satisfied (unknown/invalid entry, or missing CAS node)."""


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
        self._store = StateStore(str(self.base_dir))

    def _events_path(self, run_id: str) -> Path:
        return self._runs_dir / run_id / "events.jsonl"

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
