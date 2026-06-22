"""P1.4.6 — Self-Model hash tests (cases #51-54)."""

from __future__ import annotations

import dataclasses
from pathlib import Path

from agentic_runtime.identity.self_model_builder import build_aurel_self_model_from_paths
from agentic_runtime.identity.self_model_hash import compute_self_model_hash

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_self_model_hash_deterministic():
    m1 = build_aurel_self_model_from_paths(include_prompt_context=False)
    m2 = build_aurel_self_model_from_paths(include_prompt_context=False)
    h1 = compute_self_model_hash(m1).value
    h2 = compute_self_model_hash(m2).value
    assert h1 == h2


def test_changing_source_hash_changes_self_model_hash():
    base = build_aurel_self_model_from_paths(include_prompt_context=False)
    mutated = dataclasses.replace(
        base,
        source_bundle=dataclasses.replace(
            base.source_bundle,
            identity_kernel_hash="0" * 64,
        ),
    )
    assert compute_self_model_hash(mutated).value != compute_self_model_hash(base).value


def test_changing_capability_status_changes_self_model_hash():
    base = build_aurel_self_model_from_paths(include_prompt_context=False)
    bad_caps = tuple(
        dataclasses.replace(cap, status="planned") if cap.id == "self_model" else cap
        for cap in base.capability_inventory
    )
    mutated = dataclasses.replace(base, capability_inventory=bad_caps)
    assert compute_self_model_hash(mutated).value != compute_self_model_hash(base).value


def test_changing_known_limitation_changes_self_model_hash():
    base = build_aurel_self_model_from_paths(include_prompt_context=False)
    if not base.known_limitations:
        return
    first = base.known_limitations[0]
    mutated_limit = dataclasses.replace(first, description=first.description + " (updated)")
    mutated = dataclasses.replace(
        base,
        known_limitations=(mutated_limit,) + base.known_limitations[1:],
    )
    assert compute_self_model_hash(mutated).value != compute_self_model_hash(base).value
