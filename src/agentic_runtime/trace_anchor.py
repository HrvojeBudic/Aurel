"""External trace anchoring (M2).

The hash chain proves a ledger is *internally consistent*: mutate one event and
verification breaks. It does **not** prove *historical truth* — an attacker with
write access to the trace directory can rewrite every event, recompute the
chain, and pass verification. An anchor closes that gap by committing the run's
merkle root to a medium outside the agent's own write domain, so a full re-forge
is detectable across the trust boundary.

Two sinks:

* ``FileAnchorSink`` — append-only JSONL under a separate root (default
  ``~/.aurel/anchors``). Weaker: still filesystem, but a *different* directory
  that a run's sandboxed workspace does not have write authority over.
* ``GitAnchorSink`` — commits each anchor into a standalone git repository, so
  the anchor history is itself hash-chained and timestamped by git.

Both expose ``anchor(run_id, seq, merkle_root)`` and ``verify(run_id, root)``.
"""

from __future__ import annotations

import json
import os
import subprocess  # nosec B404 - git anchor uses fixed local git commands
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Protocol

from .core_types import now, sha


@dataclass(frozen=True)
class AnchorReceipt:
    run_id: str
    sequence: int
    merkle_root: str
    anchor_id: str
    sink: str
    created_at: float


class AnchorSink(Protocol):
    def reachable(self) -> bool: ...
    def anchor(self, run_id: str, sequence: int, merkle_root: str) -> AnchorReceipt: ...
    def verify(self, run_id: str, merkle_root: str) -> bool: ...
    def latest(self, run_id: str) -> Optional[AnchorReceipt]: ...


def _default_anchor_root() -> Path:
    override = os.environ.get("AUREL_ANCHOR_ROOT", "").strip()
    if override:
        return Path(override)
    return Path.home() / ".aurel" / "anchors"


class FileAnchorSink:
    """Append-only anchor log in a directory outside the run's write domain."""

    def __init__(self, root: Optional[str | Path] = None) -> None:
        self.root = Path(root) if root is not None else _default_anchor_root()
        self.log_path = self.root / "anchors.jsonl"

    def reachable(self) -> bool:
        try:
            self.root.mkdir(parents=True, exist_ok=True)
            self.log_path.touch(exist_ok=True)
            return os.access(self.root, os.W_OK)
        except OSError:
            return False

    def anchor(self, run_id: str, sequence: int, merkle_root: str) -> AnchorReceipt:
        self.root.mkdir(parents=True, exist_ok=True)
        anchor_id = sha(run_id, str(sequence), merkle_root)[:16]
        created_at = now()
        rec = {
            "run_id": run_id,
            "sequence": sequence,
            "merkle_root": merkle_root,
            "anchor_id": anchor_id,
            "sink": "file",
            "created_at": created_at,
        }
        with self.log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, sort_keys=True))
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        return AnchorReceipt(
            run_id=run_id, sequence=sequence, merkle_root=merkle_root,
            anchor_id=anchor_id, sink="file", created_at=created_at,
        )

    def _records(self, run_id: str) -> list[dict]:
        if not self.log_path.exists():
            return []
        out = []
        for line in self.log_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            if rec.get("run_id") == run_id:
                out.append(rec)
        return out

    def latest(self, run_id: str) -> Optional[AnchorReceipt]:
        recs = self._records(run_id)
        if not recs:
            return None
        rec = max(recs, key=lambda r: r.get("sequence", 0))
        return AnchorReceipt(
            run_id=str(rec["run_id"]), sequence=int(rec["sequence"]),
            merkle_root=str(rec["merkle_root"]), anchor_id=str(rec["anchor_id"]),
            sink=str(rec["sink"]), created_at=float(rec["created_at"]),
        )

    def verify(self, run_id: str, merkle_root: str) -> bool:
        """True iff the given root matches the most recent anchored root."""
        latest = self.latest(run_id)
        return latest is not None and latest.merkle_root == merkle_root


class GitAnchorSink:
    """Anchor into a standalone git repo — anchor history is itself chained."""

    def __init__(self, root: Optional[str | Path] = None) -> None:
        base = Path(root) if root is not None else (_default_anchor_root() / "git")
        self.root = base
        self._file_sink = FileAnchorSink(base)

    def reachable(self) -> bool:
        if not self._which_git():
            return False
        return self._file_sink.reachable() and self._ensure_repo()

    @staticmethod
    def _which_git() -> Optional[str]:
        from shutil import which

        return which("git")

    def _ensure_repo(self) -> bool:
        git = self._which_git()
        if git is None:
            return False
        self.root.mkdir(parents=True, exist_ok=True)
        if (self.root / ".git").is_dir():
            return True
        try:
            subprocess.run(  # nosec B603
                [git, "init", "-q"], cwd=self.root, check=True,
                capture_output=True, timeout=30)
            return True
        except (OSError, subprocess.SubprocessError):
            return False

    def anchor(self, run_id: str, sequence: int, merkle_root: str) -> AnchorReceipt:
        receipt = self._file_sink.anchor(run_id, sequence, merkle_root)
        git = self._which_git()
        if git is not None and self._ensure_repo():
            try:
                subprocess.run(  # nosec B603
                    [git, "add", "anchors.jsonl"], cwd=self.root, check=True,
                    capture_output=True, timeout=30)
                subprocess.run(  # nosec B603
                    [git, "-c", "user.email=anchor@aurel", "-c", "user.name=aurel-anchor",
                     "commit", "-q", "-m", f"anchor {run_id}@{sequence} {merkle_root[:12]}"],
                    cwd=self.root, check=True, capture_output=True, timeout=30)
            except (OSError, subprocess.SubprocessError):
                pass  # file anchor already durable; git is the strengthening layer
        return receipt

    def latest(self, run_id: str) -> Optional[AnchorReceipt]:
        return self._file_sink.latest(run_id)

    def verify(self, run_id: str, merkle_root: str) -> bool:
        return self._file_sink.verify(run_id, merkle_root)


def default_anchor_sink() -> AnchorSink:
    """File sink by default; opt into git via ``AUREL_ANCHOR_SINK=git``."""
    if os.environ.get("AUREL_ANCHOR_SINK", "").strip().lower() == "git":
        return GitAnchorSink()
    return FileAnchorSink()
