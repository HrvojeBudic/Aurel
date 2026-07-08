#!/usr/bin/env python3
"""Reverse-dependency audit for agentic_runtime (F0.3).

For every module under src/agentic_runtime, list who imports it (src + tests).
Modules with zero importers and no CLI wiring are attic candidates — moving
them is a human decision; this script only reports.

Usage:
    python3 scripts/reverse_deps.py            # summary: zero-importer modules
    python3 scripts/reverse_deps.py --all      # full importer map
    python3 scripts/reverse_deps.py --json     # machine-readable full map
"""
from __future__ import annotations

import argparse
import ast
import json
import sys
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_ROOT = REPO_ROOT / "src" / "agentic_runtime"
TESTS_ROOT = REPO_ROOT / "tests"
PACKAGE = "agentic_runtime"


def _module_name(path: Path) -> str:
    rel = path.relative_to(SRC_ROOT.parent)
    parts = list(rel.with_suffix("").parts)
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def _iter_py(root: Path):
    for path in sorted(root.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        yield path


def _imported_modules(path: Path, current_module: str, is_package: bool) -> set[str]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError:
        return set()
    # Relative imports resolve against the containing package: the module
    # itself for __init__.py, its parent package otherwise.
    package = current_module if is_package else ".".join(current_module.split(".")[:-1])
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith(PACKAGE):
                    found.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                base_parts = package.split(".") if package else []
                if node.level - 1 >= len(base_parts):
                    continue
                base = ".".join(base_parts[: len(base_parts) - (node.level - 1)])
                module = f"{base}.{node.module}" if node.module else base
            else:
                module = node.module or ""
            if module.startswith(PACKAGE):
                found.add(module)
                # `from pkg import name` may target a submodule, not an attr.
                for alias in node.names:
                    found.add(f"{module}.{alias.name}")
    return found


def build_map() -> dict[str, list[str]]:
    modules = {_module_name(p): p for p in _iter_py(SRC_ROOT)}
    importers: dict[str, set[str]] = defaultdict(set)

    for source_root, label in ((SRC_ROOT, "src"), (TESTS_ROOT, "tests")):
        for path in _iter_py(source_root):
            if source_root is SRC_ROOT:
                current = _module_name(path)
                origin = current
                is_package = path.name == "__init__.py"
            else:
                current = PACKAGE  # tests import absolutely
                origin = f"tests/{path.relative_to(TESTS_ROOT)}"
                is_package = True
            for target in _imported_modules(path, current, is_package):
                # Credit the module itself and every ancestor package.
                parts = target.split(".")
                for i in range(1, len(parts) + 1):
                    candidate = ".".join(parts[:i])
                    if candidate in modules and candidate != origin:
                        importers[candidate].add(f"{label}:{origin}")

    return {mod: sorted(importers.get(mod, set())) for mod in sorted(modules)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true", help="print full importer map")
    ap.add_argument("--json", action="store_true", help="full map as JSON")
    args = ap.parse_args()

    dep_map = build_map()
    if args.json:
        print(json.dumps(dep_map, indent=2))
        return 0
    if args.all:
        for mod, importers in dep_map.items():
            print(f"{mod}  ({len(importers)})")
            for imp in importers:
                print(f"    <- {imp}")
        return 0

    orphans = [m for m, imps in dep_map.items()
               if not imps and m != PACKAGE and not m.endswith("cli")]
    print(f"modules: {len(dep_map)}   zero-importer candidates: {len(orphans)}")
    for mod in orphans:
        print(f"  {mod}")
    print("\nNote: CLI-wired and entry-point modules can be false positives; "
          "verify before atticizing.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
