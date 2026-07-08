"""nc_bindings.py — loader + CI firewall for the NC-law ⇄ merge-gate mapping.

Loads ``nc_merge_bindings.json`` and lets the merge gate resolve, for any check
it emits, the exact DSD no-collapse law it protects. ``validate_coverage`` is the
canon firewall: it asserts every gate the ``MergeGate`` can emit has a binding,
so a new check can never ship uncovered by canon.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from importlib import resources
from pathlib import Path

_RESOURCE = "nc_merge_bindings.json"


def _read_bindings_text() -> str:
    """Read the packaged bindings JSON, robustly.

    Prefer ``importlib.resources`` (works for wheel + editable installs), but
    fall back to a path next to this module. The resource finder can be
    transiently disrupted by unrelated test-suite state (meta-path / import
    cache churn); the file always sits beside nc_bindings.py, so a __file__
    read is a correct, disruption-proof fallback rather than a hard failure.
    """
    try:
        return resources.files(__package__).joinpath(_RESOURCE).read_text("utf-8")
    except (FileNotFoundError, ModuleNotFoundError, TypeError):
        return (Path(__file__).resolve().parent / _RESOURCE).read_text("utf-8")


@dataclass(frozen=True)
class NCBinding:
    gate_id: str
    check: str
    nc_law: str
    statement: str
    canon_source: str
    severity: str
    verdict_on_fail: str
    test_hook: str


@lru_cache(maxsize=1)
def load_bindings() -> dict[str, NCBinding]:
    """Return ``{gate_id: NCBinding}`` from the packaged JSON."""
    raw = _read_bindings_text()
    doc = json.loads(raw)
    out: dict[str, NCBinding] = {}
    for entry in doc["bindings"]:
        b = NCBinding(**entry)
        if b.gate_id in out:
            raise ValueError(f"duplicate NC binding gate_id: {b.gate_id!r}")
        out[b.gate_id] = b
    return out


def binding_for(gate_id: str) -> NCBinding:
    """Resolve the NC binding for a gate, or raise if the gate is uncovered."""
    bindings = load_bindings()
    try:
        return bindings[gate_id]
    except KeyError as e:
        raise KeyError(
            f"merge-gate check {gate_id!r} has no NC binding — canon firewall breach"
        ) from e


def validate_coverage(gate_ids: "set[str] | frozenset[str]") -> None:
    """Assert every emitted gate has a binding (and flag orphan bindings).

    Raises ``AssertionError`` on any uncovered gate — wired into CI so the merge
    gate can never drift from canon.
    """
    bindings = load_bindings()
    covered = set(bindings)
    missing = set(gate_ids) - covered
    if missing:
        raise AssertionError(f"merge-gate checks without NC binding: {sorted(missing)}")
    orphan = covered - set(gate_ids)
    if orphan:
        raise AssertionError(f"NC bindings with no emitting gate: {sorted(orphan)}")
