#!/usr/bin/env python3
"""Architectural guard checks (M7).

Two drift guards enforced in CI:

1. **Doc paths route through the registry.** No source or test may hard-code a
   ``"agent/…"`` documentation path — everything goes through
   ``doc_registry`` so the eventual physical relocation of docs is a one-constant
   change. (``doc_registry.py`` and the ratchet/guard scripts are exempt.)

2. **No permissive approver outside the governance resolver.** An
   ``AutoApprover(lambda r: True, … allow_r5=True)`` bypasses the whole approval
   envelope; it may only be built by ``governance/profile.py`` (which materializes
   a declared level) — never scattered through the app or harness.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "src"
TESTS = REPO / "tests"
BASELINE = REPO / "guard_baseline.json"

# Files allowed to reference literal agent/ doc paths (the seam + tooling).
_DOC_PATH_EXEMPT = {
    "doc_registry.py",
    "governance_guards.py",
    "lint_ratchet.py",
}
_DOC_PATH_RE = re.compile(r'["\']agent/[A-Za-z0-9_./-]+\.md["\']')

# Files allowed to build a fully-permissive approver.
_APPROVER_EXEMPT = {"profile.py"}
_PERMISSIVE_RE = re.compile(r"allow_r5\s*=\s*True")


def _iter_py():
    for base in (SRC, TESTS):
        for p in base.rglob("*.py"):
            if "__pycache__" in p.parts:
                continue
            yield p


def check_doc_paths() -> list[str]:
    hits = []
    for p in _iter_py():
        if p.name in _DOC_PATH_EXEMPT:
            continue
        for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            if _DOC_PATH_RE.search(line):
                hits.append(f"{p.relative_to(REPO)}:{i}: hard-coded doc path — use doc_registry")
    return hits


def check_permissive_approver() -> list[str]:
    hits = []
    for p in _iter_py():
        # tests may exercise permissive approvers directly; guard source only.
        if TESTS in p.parents or p.name in _APPROVER_EXEMPT:
            continue
        for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            if _PERMISSIVE_RE.search(line):
                hits.append(
                    f"{p.relative_to(REPO)}:{i}: permissive approver outside the "
                    "governance resolver — build it via governance.profile"
                )
    return hits


def _counts_by_file(violations: list[str]) -> dict[str, int]:
    """Aggregate violations to per-file counts (stable across line shifts)."""
    out: dict[str, int] = {}
    for v in violations:
        f = v.split(":", 1)[0]
        out[f] = out.get(f, 0) + 1
    return out


def collect() -> dict[str, int]:
    return _counts_by_file(check_doc_paths() + check_permissive_approver())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--update", action="store_true", help="freeze current violations")
    ap.add_argument("--check", action="store_true", help="fail only on NEW violations")
    args = ap.parse_args()

    current = collect()
    if args.update or not BASELINE.exists():
        BASELINE.write_text(json.dumps(current, indent=2, sort_keys=True) + "\n")
        print(f"guard baseline written: {sum(current.values())} known violations "
              f"across {len(current)} files")
        return 0

    baseline = json.loads(BASELINE.read_text())
    new = {f: (baseline.get(f, 0), n) for f, n in current.items() if n > baseline.get(f, 0)}
    if new:
        print("NEW governance guard violations (baseline may only shrink):")
        for f, (was, now) in sorted(new.items()):
            print(f"  {f}: {was} -> {now}")
        return 1
    fixed = {f: baseline[f] for f in baseline if f not in current or current[f] < baseline[f]}
    if fixed:
        print("Guard debt decreased — run --update to lock it in:")
        for f in sorted(fixed):
            print(f"  {f}")
    print("governance guards OK (no new violations)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
