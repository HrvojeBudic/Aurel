"""F8.5 — Succession drill: export → restore → verify → replay (read-only over a copy).

Proves operator succession readiness without touching the live trace tree:
copy the persisted trace to an isolated directory, verify forest integrity,
materialize sampled run heads via checkout, and replay transitions through
Chronos. Any discrepancy is reported honestly — never a silent PASS.
"""
from __future__ import annotations

import shutil
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional

from .chronos import ChronosReplay
from .chronos._util import state_transitions
from .sandbox import UnsafeLocalSandbox
from .worldline import CheckoutError, WorldLineForest

SandboxFactory = Callable[[str], Any]


def flag_enabled() -> bool:
    """True when succession drill is live (``AUREL_CHRONOS``)."""
    from .chronos import flag_enabled as chronos_enabled
    return chronos_enabled()


def _default_sandbox_factory(root: str) -> UnsafeLocalSandbox:
    return UnsafeLocalSandbox(root=root)


@dataclass
class SuccessionDrillReport:
    exported: bool
    restored: bool
    verified: bool
    replayed: int
    export_path: str
    sample_run_ids: list[str] = field(default_factory=list)
    discrepancies: list[dict[str, Any]] = field(default_factory=list)
    verify_detail: dict[str, Any] = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        return (
            self.exported
            and self.restored
            and self.verified
            and not self.discrepancies
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "exported": self.exported,
            "restored": self.restored,
            "verified": self.verified,
            "replayed": self.replayed,
            "passed": self.passed,
            "export_path": self.export_path,
            "sample_run_ids": list(self.sample_run_ids),
            "discrepancies": list(self.discrepancies),
            "verify_detail": dict(self.verify_detail),
        }


def run_succession_drill(
    trace_dir: str,
    *,
    out_dir: str,
    sample: int = 3,
    sandbox_factory: Optional[SandboxFactory] = None,
) -> SuccessionDrillReport:
    """Run the succession pipeline on an isolated copy of ``trace_dir``."""
    src = Path(trace_dir)
    dst = Path(out_dir)
    discrepancies: list[dict[str, Any]] = []

    if not src.is_dir():
        return SuccessionDrillReport(
            exported=False,
            restored=False,
            verified=False,
            replayed=0,
            export_path=str(dst),
            discrepancies=[{"stage": "export", "error": f"no trace dir at {src}"}],
        )

    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    exported = True

    factory = sandbox_factory or _default_sandbox_factory
    forest = WorldLineForest(str(dst))

    verify_detail = forest.verify()
    verified = bool(verify_detail.get("ok"))
    if not verified:
        discrepancies.append({"stage": "verify", **verify_detail})

    run_ids = forest._run_ids()
    sample_n = max(0, int(sample))
    sample_ids = run_ids[:sample_n] if sample_n else []

    restored = True
    for run_id in sample_ids:
        transitions = state_transitions(str(dst), run_id)
        if not transitions:
            continue
        entry_hash = str(transitions[-1].get("entry_hash", "") or "")
        if not entry_hash:
            restored = False
            discrepancies.append({
                "stage": "restore",
                "run_id": run_id,
                "error": "final transition missing entry_hash",
            })
            continue
        try:
            root = tempfile.mkdtemp(prefix="succession_restore_")
            forest.checkout(run_id, entry_hash, sandbox_factory=lambda _: factory(root))
        except CheckoutError as exc:
            restored = False
            discrepancies.append({
                "stage": "restore",
                "run_id": run_id,
                "error": str(exc),
            })

    replayed = 0
    for run_id in sample_ids:
        result = ChronosReplay.from_run(str(dst), run_id, sandbox_factory=factory)
        replayed += 1
        if not result.replayable:
            discrepancies.append({
                "stage": "replay",
                "run_id": run_id,
                "reason": result.reason,
                "mismatch_at": result.mismatch_at,
            })

    return SuccessionDrillReport(
        exported=exported,
        restored=restored,
        verified=verified,
        replayed=replayed,
        export_path=str(dst),
        sample_run_ids=sample_ids,
        discrepancies=discrepancies,
        verify_detail=verify_detail,
    )


__all__ = ["SuccessionDrillReport", "flag_enabled", "run_succession_drill"]
