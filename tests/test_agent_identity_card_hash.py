"""P1.4.7 — Agent Identity Card hash tests (cases #47-54)."""

from __future__ import annotations

import dataclasses
from pathlib import Path

from agentic_runtime.identity.agent_identity_card_builder import build_agent_identity_card
from agentic_runtime.identity.agent_identity_card_hash import (
    compute_runtime_agent_identity_card_hash,
    compute_stable_agent_identity_hash,
    runtime_card_to_canonical_dict,
    stable_identity_to_canonical_dict,
)
from agentic_runtime.identity.agent_identity_card_policy import (
    AgentSourceBindings,
    load_agent_identity_card_config,
)
from agentic_runtime.identity.communication_modes import load_communication_mode_registry
from agentic_runtime.identity.kernel import load_identity_kernel
from agentic_runtime.identity.operator_contract import load_operator_contract
from agentic_runtime.identity.persona import load_persona_manifest
from agentic_runtime.identity.self_model_builder import build_aurel_self_model_from_paths
from agentic_runtime.identity.self_model_policy import load_self_model_policy
from agentic_runtime.prompts.compiler_policy import load_identity_prompt_compiler_policy

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXED_RUNTIME_ID = "aurel-runtime-00000000-0000-4000-8000-000000000001"
ALT_RUNTIME_ID = "aurel-runtime-00000000-0000-4000-8000-000000000002"


def _build(runtime_instance_id: str = FIXED_RUNTIME_ID):
    return build_agent_identity_card(
        load_identity_kernel(REPO_ROOT / "config/aurel/identity_kernel.yaml"),
        load_persona_manifest(REPO_ROOT / "config/aurel/persona_manifest.yaml"),
        load_operator_contract(REPO_ROOT / "config/aurel/operator_contract.yaml"),
        load_communication_mode_registry(REPO_ROOT / "config/aurel/communication_modes.yaml"),
        load_identity_prompt_compiler_policy(
            REPO_ROOT / "config/aurel/identity_prompt_compiler.yaml"
        ),
        build_aurel_self_model_from_paths(include_prompt_context=True),
        load_self_model_policy(REPO_ROOT / "config/aurel/self_model_policy.yaml"),
        load_agent_identity_card_config(REPO_ROOT / "config/aurel/agent_identity_card.yaml"),
        runtime_instance_id=runtime_instance_id,
    )


# 47
def test_stable_hash_is_deterministic():
    card_a = _build()
    card_b = _build()
    assert compute_stable_agent_identity_hash(card_a) == compute_stable_agent_identity_hash(card_b)


# 48
def test_runtime_hash_is_deterministic_for_same_runtime_id():
    card_a = _build(FIXED_RUNTIME_ID)
    card_b = _build(FIXED_RUNTIME_ID)
    assert compute_runtime_agent_identity_card_hash(card_a) == compute_runtime_agent_identity_card_hash(
        card_b
    )


# 49
def test_runtime_hash_changes_when_runtime_instance_id_changes():
    stable_a = compute_stable_agent_identity_hash(_build(FIXED_RUNTIME_ID))
    stable_b = compute_stable_agent_identity_hash(_build(ALT_RUNTIME_ID))
    runtime_a = compute_runtime_agent_identity_card_hash(_build(FIXED_RUNTIME_ID))
    runtime_b = compute_runtime_agent_identity_card_hash(_build(ALT_RUNTIME_ID))
    assert stable_a == stable_b
    assert runtime_a != runtime_b


# 50
def test_stable_hash_excludes_runtime_instance_id():
    card = _build(FIXED_RUNTIME_ID)
    stable_dict = stable_identity_to_canonical_dict(card)
    assert "runtime" not in stable_dict
    runtime_dict = runtime_card_to_canonical_dict(card)
    assert runtime_dict["runtime"]["runtime_instance_id"] == FIXED_RUNTIME_ID


# 51
def test_stable_hash_changes_when_source_hash_changes():
    card = _build()
    altered = dataclasses.replace(
        card,
        source_bindings=AgentSourceBindings(
            identity_kernel_hash="0" * 64,
            persona_manifest_hash=card.source_bindings.persona_manifest_hash,
            operator_contract_hash=card.source_bindings.operator_contract_hash,
            communication_modes_hash=card.source_bindings.communication_modes_hash,
            identity_prompt_compiler_policy_hash=(
                card.source_bindings.identity_prompt_compiler_policy_hash
            ),
            self_model_hash=card.source_bindings.self_model_hash,
        ),
        stable_agent_identity_hash=None,
        runtime_agent_identity_card_hash=None,
    )
    assert compute_stable_agent_identity_hash(card) != compute_stable_agent_identity_hash(altered)


# 52
def test_runtime_hash_changes_when_source_hash_changes():
    card = _build()
    altered = dataclasses.replace(
        card,
        source_bindings=AgentSourceBindings(
            identity_kernel_hash=card.source_bindings.identity_kernel_hash,
            persona_manifest_hash=card.source_bindings.persona_manifest_hash,
            operator_contract_hash=card.source_bindings.operator_contract_hash,
            communication_modes_hash=card.source_bindings.communication_modes_hash,
            identity_prompt_compiler_policy_hash=(
                card.source_bindings.identity_prompt_compiler_policy_hash
            ),
            self_model_hash="f" * 64,
        ),
        stable_agent_identity_hash=None,
        runtime_agent_identity_card_hash=None,
    )
    assert compute_runtime_agent_identity_card_hash(card) != compute_runtime_agent_identity_card_hash(
        altered
    )


# 53
def test_runtime_started_at_not_in_canonical_dicts():
    card = _build()
    runtime_dict = runtime_card_to_canonical_dict(card)
    assert "runtime_started_at" not in runtime_dict["runtime"]


# 54
def test_hash_values_are_64_hex():
    card = _build()
    stable = compute_stable_agent_identity_hash(card)
    runtime = compute_runtime_agent_identity_card_hash(card)
    assert len(stable) == 64
    assert len(runtime) == 64
    assert stable.islower()
    assert runtime.islower()
