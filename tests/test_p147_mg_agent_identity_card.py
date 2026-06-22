"""P1.4.7-MG — Agent Identity Card merge-gate hardening tests."""

from __future__ import annotations

import argparse
import dataclasses
from pathlib import Path

import pytest

from agentic_runtime.cli_modules.common import config_dir
from agentic_runtime.identity.agent_identity_card_builder import (
    build_agent_identity_card,
    build_agent_identity_card_from_bundle,
    build_agent_identity_card_from_paths,
)
from agentic_runtime.identity.agent_identity_card_policy import (
    AgentIdentityCardError,
    load_agent_identity_card_config,
)
from agentic_runtime.identity.capability_inventory import (
    CAPABILITY_INVENTORY,
    IMPLEMENTED_CAPABILITY_IDS,
    PLANNED_CAPABILITY_IDS,
)
from agentic_runtime.identity.communication_modes import load_communication_mode_registry
from agentic_runtime.identity.kernel import load_identity_kernel
from agentic_runtime.identity.operator_contract import load_operator_contract
from agentic_runtime.identity.persona import load_persona_manifest
from agentic_runtime.identity.self_model_builder import build_aurel_self_model_from_paths
from agentic_runtime.identity.self_model_policy import SelfModelError, load_self_model_policy
from agentic_runtime.identity.source_bundle import load_identity_source_bundle
from agentic_runtime.model_config import default_config_dir
from agentic_runtime.prompts.compiler_policy import load_identity_prompt_compiler_policy

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXED_RUNTIME_ID = "aurel-runtime-00000000-0000-4000-8000-000000000001"
CANONICAL_POLICY = REPO_ROOT / "config/aurel/self_model_policy.yaml"
CANONICAL_CARD = REPO_ROOT / "config/aurel/agent_identity_card.yaml"


def _card_sources():
    return {
        "kernel": load_identity_kernel(REPO_ROOT / "config/aurel/identity_kernel.yaml"),
        "persona": load_persona_manifest(REPO_ROOT / "config/aurel/persona_manifest.yaml"),
        "operator": load_operator_contract(REPO_ROOT / "config/aurel/operator_contract.yaml"),
        "modes": load_communication_mode_registry(
            REPO_ROOT / "config/aurel/communication_modes.yaml"
        ),
        "compiler": load_identity_prompt_compiler_policy(
            REPO_ROOT / "config/aurel/identity_prompt_compiler.yaml"
        ),
        "card_config": load_agent_identity_card_config(CANONICAL_CARD),
        "self_model": build_aurel_self_model_from_paths(include_prompt_context=True),
        "policy": load_self_model_policy(CANONICAL_POLICY),
    }


def test_agent_identity_card_respects_custom_self_model_policy_path(tmp_path, monkeypatch):
    import agentic_runtime.identity.source_bundle as source_bundle_module

    policy_calls: list[Path | None] = []
    real_load = source_bundle_module.load_self_model_policy

    def tracking_load(path=None):
        policy_calls.append(Path(path) if path is not None else None)
        return real_load(path)

    monkeypatch.setattr(source_bundle_module, "load_self_model_policy", tracking_load)

    custom = tmp_path / "self_model_policy.yaml"
    custom.write_text(CANONICAL_POLICY.read_text(encoding="utf-8"), encoding="utf-8")

    build_agent_identity_card_from_paths(
        self_model_policy_path=custom,
        runtime_instance_id=FIXED_RUNTIME_ID,
    )

    assert None not in policy_calls
    assert custom.resolve() in {p.resolve() for p in policy_calls if p is not None}


def test_custom_self_model_policy_changes_final_card_validation():
    sources = _card_sources()
    valid_policy = sources["policy"]
    invalid_policy = dataclasses.replace(valid_policy, applies_to_agent="NotAurel")

    build_agent_identity_card(
        sources["kernel"],
        sources["persona"],
        sources["operator"],
        sources["modes"],
        sources["compiler"],
        sources["self_model"],
        valid_policy,
        sources["card_config"],
        runtime_instance_id=FIXED_RUNTIME_ID,
    )

    with pytest.raises(AgentIdentityCardError):
        build_agent_identity_card(
            sources["kernel"],
            sources["persona"],
            sources["operator"],
            sources["modes"],
            sources["compiler"],
            sources["self_model"],
            invalid_policy,
            sources["card_config"],
            runtime_instance_id=FIXED_RUNTIME_ID,
        )


def test_invalid_custom_policy_path_fails_card_build(tmp_path):
    custom = tmp_path / "self_model_policy.yaml"
    text = CANONICAL_POLICY.read_text(encoding="utf-8").replace(
        'applies_to_agent: "Aurel"', 'applies_to_agent: "Evil"', 1
    )
    custom.write_text(text, encoding="utf-8")

    with pytest.raises((AgentIdentityCardError, SelfModelError)):
        build_agent_identity_card_from_paths(
            self_model_policy_path=custom,
            runtime_instance_id=FIXED_RUNTIME_ID,
        )


def test_self_model_inventory_marks_agent_identity_card_implemented():
    model = build_aurel_self_model_from_paths(include_prompt_context=False)
    cap = next(c for c in model.capability_inventory if c.id == "agent_identity_card")
    assert cap.status == "implemented"
    assert cap.roadmap_phase == "P1.4.7"


def test_capability_inventory_matches_implemented_patch_registry():
    implemented = {entry.id for entry in CAPABILITY_INVENTORY if entry.status == "implemented"}
    assert "agent_identity_card" in implemented
    assert implemented == IMPLEMENTED_CAPABILITY_IDS
    assert "agent_identity_card" not in PLANNED_CAPABILITY_IDS


def test_build_from_bundle_matches_from_paths():
    card_paths = build_agent_identity_card_from_paths(runtime_instance_id=FIXED_RUNTIME_ID)
    bundle = load_identity_source_bundle()
    card_bundle = build_agent_identity_card_from_bundle(
        bundle,
        runtime_instance_id=FIXED_RUNTIME_ID,
    )
    assert (
        card_paths.stable_agent_identity_hash
        == card_bundle.stable_agent_identity_hash
    )
    assert (
        card_paths.runtime_agent_identity_card_hash
        == card_bundle.runtime_agent_identity_card_hash
    )


def test_cli_default_config_dir_matches_library():
    args = argparse.Namespace(config_dir="")
    assert config_dir(args) == default_config_dir()
