"""P1.4.5 — Identity Prompt Context hash tests (cases #44-50)."""

from __future__ import annotations

import dataclasses
from pathlib import Path

import pytest

from agentic_runtime.identity.kernel import load_identity_kernel
from agentic_runtime.identity.communication_modes import load_communication_mode_registry
from agentic_runtime.identity.operator_contract import load_operator_contract
from agentic_runtime.identity.persona import load_persona_manifest
from agentic_runtime.prompts.compiler_policy import load_identity_prompt_compiler_policy
from agentic_runtime.prompts.identity_context_compiler import compile_identity_prompt_context
from agentic_runtime.prompts.identity_context_hash import compute_identity_prompt_context_hash

REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(name="sources")
def fixture_sources():
    return {
        "kernel": load_identity_kernel(REPO_ROOT / "config" / "aurel" / "identity_kernel.yaml"),
        "persona": load_persona_manifest(REPO_ROOT / "config" / "aurel" / "persona_manifest.yaml"),
        "operator": load_operator_contract(REPO_ROOT / "config" / "aurel" / "operator_contract.yaml"),
        "modes": load_communication_mode_registry(
            REPO_ROOT / "config" / "aurel" / "communication_modes.yaml"
        ),
        "policy": load_identity_prompt_compiler_policy(
            REPO_ROOT / "config" / "aurel" / "identity_prompt_compiler.yaml"
        ),
    }


def _compile(sources, mode: str):
    return compile_identity_prompt_context(
        sources["kernel"],
        sources["persona"],
        sources["operator"],
        sources["modes"],
        mode,
        sources["policy"],
    )


def test_compiled_context_hash_deterministic(sources):
    r1 = _compile(sources, "FOCUS")
    r2 = _compile(sources, "FOCUS")
    assert r1.context_hash == r2.context_hash
    assert r1.context is not None
    h1 = compute_identity_prompt_context_hash(r1.context).value
    h2 = compute_identity_prompt_context_hash(r2.context).value
    assert h1 == h2 == r1.context_hash


def test_changing_selected_mode_changes_context_hash(sources):
    focus = _compile(sources, "FOCUS")
    deploy = _compile(sources, "DEPLOY")
    assert focus.context_hash != deploy.context_hash


def test_changing_identity_kernel_hash_changes_context_hash(sources):
    base = _compile(sources, "FOCUS")
    mutated = dataclasses.replace(
        base.context,
        source_bundle=dataclasses.replace(
            base.context.source_bundle,
            identity_kernel_hash="0" * 64,
        ),
    )
    assert compute_identity_prompt_context_hash(mutated).value != base.context_hash


def test_changing_persona_manifest_hash_changes_context_hash(sources):
    base = _compile(sources, "FOCUS")
    mutated = dataclasses.replace(
        base.context,
        source_bundle=dataclasses.replace(
            base.context.source_bundle,
            persona_manifest_hash="1" * 64,
        ),
    )
    assert compute_identity_prompt_context_hash(mutated).value != base.context_hash


def test_changing_operator_contract_hash_changes_context_hash(sources):
    base = _compile(sources, "FOCUS")
    mutated = dataclasses.replace(
        base.context,
        source_bundle=dataclasses.replace(
            base.context.source_bundle,
            operator_contract_hash="2" * 64,
        ),
    )
    assert compute_identity_prompt_context_hash(mutated).value != base.context_hash


def test_changing_communication_modes_hash_changes_context_hash(sources):
    base = _compile(sources, "FOCUS")
    mutated = dataclasses.replace(
        base.context,
        source_bundle=dataclasses.replace(
            base.context.source_bundle,
            communication_modes_hash="3" * 64,
        ),
    )
    assert compute_identity_prompt_context_hash(mutated).value != base.context_hash


def test_same_semantic_context_produces_same_hash(sources):
    r1 = _compile(sources, "SHADOW")
    r2 = _compile(sources, "SHADOW")
    assert r1.context is not None and r2.context is not None
    assert compute_identity_prompt_context_hash(r1.context).value == (
        compute_identity_prompt_context_hash(r2.context).value
    )
