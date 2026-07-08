#!/usr/bin/env python3
"""Lint/type debt ratchet (M7).

The repo carries a large suppressed lint/type debt (ruff E501, and mypy under
six disabled error codes). Cleaning it in one pass is infeasible; letting it
grow silently is how the debt got here. This ratchet freezes the current
per-code counts in ``quality_baseline.json`` and fails CI only when a count
*increases* — so the debt can shrink but never grow.

Usage:
    python scripts/lint_ratchet.py --update    # write/refresh the baseline
    python scripts/lint_ratchet.py --check      # fail if any count grew
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess  # nosec B404 - fixed local linters
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
BASELINE = REPO / "quality_baseline.json"

# The six error codes disabled in pyproject's [tool.mypy]; the ratchet tracks
# them re-enabled so their count can only fall.
MYPY_CODES = ["arg-type", "return-value", "assignment", "union-attr", "call-arg", "var-annotated"]
RUFF_TRACKED = ["E501"]  # line-too-long: bounded, cosmetic; ratchet, don't fix en masse


def _ruff_argv() -> list[str] | None:
    """Prefer ``python -m ruff`` (CI installs it via pip); fall back to a ruff
    binary on PATH (e.g. a snap/standalone install). Returns None if ruff is
    unreachable — the caller MUST treat that as "unknown", never as zero, so a
    missing linter can't silently ratchet the baseline down to 0."""
    probe = subprocess.run([sys.executable, "-m", "ruff", "--version"],  # nosec B603
                           cwd=REPO, capture_output=True, text=True)
    if probe.returncode == 0:
        return [sys.executable, "-m", "ruff"]
    binary = shutil.which("ruff")
    return [binary] if binary else None


def _ruff_counts() -> dict[str, int]:
    argv = _ruff_argv()
    if argv is None:
        raise RuntimeError(
            "ruff is not reachable (neither 'python -m ruff' nor a 'ruff' binary "
            "on PATH); refusing to compute E501 as 0 and corrupt the baseline")
    out = subprocess.run(  # nosec B603
        argv + ["check", "src", "tests",
                "--select", ",".join(RUFF_TRACKED), "--output-format", "json"],
        cwd=REPO, capture_output=True, text=True,
    )
    counts: dict[str, int] = {c: 0 for c in RUFF_TRACKED}
    try:
        for item in json.loads(out.stdout or "[]"):
            code = item.get("code")
            if code in counts:
                counts[code] += 1
    except json.JSONDecodeError:
        pass
    return counts


def _mypy_count() -> int:
    args = [sys.executable, "-m", "mypy", "src/agentic_runtime"]
    for code in MYPY_CODES:
        args += ["--enable-error-code", code]
    out = subprocess.run(args, cwd=REPO, capture_output=True, text=True)  # nosec B603
    n = 0
    for line in out.stdout.splitlines():
        if ": error:" in line:
            n += 1
    return n


def collect() -> dict[str, int]:
    counts = _ruff_counts()
    counts["mypy_total"] = _mypy_count()
    return counts


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--update", action="store_true", help="write the baseline")
    ap.add_argument("--check", action="store_true", help="fail if any count grew")
    args = ap.parse_args()

    current = collect()
    if args.update or not BASELINE.exists():
        BASELINE.write_text(json.dumps(current, indent=2, sort_keys=True) + "\n")
        print(f"baseline written: {current}")
        return 0

    baseline = json.loads(BASELINE.read_text())
    grew = {k: (baseline.get(k, 0), v) for k, v in current.items()
            if v > baseline.get(k, 0)}
    print(f"current: {current}")
    print(f"baseline: {baseline}")
    if grew:
        print("\nDEBT INCREASED (ratchet violation):")
        for k, (was, now) in grew.items():
            print(f"  {k}: {was} -> {now}")
        return 1
    shrank = {k: (baseline.get(k, 0), v) for k, v in current.items()
              if v < baseline.get(k, 0)}
    if shrank:
        print("\nDebt decreased — run --update to lock in the improvement:")
        for k, (was, now) in shrank.items():
            print(f"  {k}: {was} -> {now}")
    print("\nratchet OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
