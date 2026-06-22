"""P1.4.6 — Self-Model builder and validation tests (cases #23-50, #61-64)."""

from __future__ import annotations

import dataclasses
from pathlib import Path

import pytest

from agentic_runtime.identity.self_model import SelfModelCapability
from agentic_runtime.identity.self_model_builder import (
    build_aurel_self_model,
    build_aurel_self_model_from_paths,
)
from agentic_runtime.identity.self_model_policy import SelfModelError, load_self_model_policy
from agentic_runtime.identity.self_model_validation import validate_aurel_self_model
from agentic_runtime.identity.kernel import load_identity_kernel
from agentic_runtime.identity.persona import load_persona_manifest
from agentic_runtime.identity.operator_contract import load_operator_contract
from agentic_runtime.identity.communication_modes import load_communication_mode_registry
from agentic_runtime.prompts.compiler_policy import load_identity_prompt_compiler_policy

REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(name="sources")
def fixture_sources():
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
        "policy": load_self_model_policy(REPO_ROOT / "config/aurel/self_model_policy.yaml"),
    }


def _build(sources, context=None):
    return build_aurel_self_model(
        sources["kernel"],
        sources["persona"],
        sources["operator"],
        sources["modes"],
        sources["compiler"],
        context,
        sources["policy"],
    )


# 23
def test_build_self_model_with_valid_sources_succeeds():
    model = build_aurel_self_model_from_paths()
    assert model.agent_name == "Aurel"
    assert len(model.capability_inventory) >= 15


@pytest.mark.parametrize(
    ("missing_kwarg",),
    [
        ("kernel_path",),
        ("persona_path",),
        ("operator_path",),
        ("modes_path",),
        ("compiler_path",),
        ("self_model_policy_path",),
    ],
)
def test_missing_source_fails_build(missing_kwarg):
    kwargs = {
        "kernel_path": REPO_ROOT / "config/aurel/identity_kernel.yaml",
        "persona_path": REPO_ROOT / "config/aurel/persona_manifest.yaml",
        "operator_path": REPO_ROOT / "config/aurel/operator_contract.yaml",
        "modes_path": REPO_ROOT / "config/aurel/communication_modes.yaml",
        "compiler_path": REPO_ROOT / "config/aurel/identity_prompt_compiler.yaml",
        "self_model_policy_path": REPO_ROOT / "config/aurel/self_model_policy.yaml",
        "include_prompt_context": False,
    }
    kwargs[missing_kwarg] = REPO_ROOT / "nonexistent/missing.yaml"
    with pytest.raises(SelfModelError):
        build_aurel_self_model_from_paths(**kwargs)


def test_invalid_identity_kernel_fails_build(sources):
    bad_kernel = dataclasses.replace(
        sources["kernel"],
        immutables=dataclasses.replace(
            sources["kernel"].immutables,
            self_escalation_allowed=True,
        ),
    )
    with pytest.raises(SelfModelError):
        build_aurel_self_model(
            bad_kernel,
            sources["persona"],
            sources["operator"],
            sources["modes"],
            sources["compiler"],
            None,
            sources["policy"],
        )


def test_invalid_persona_manifest_fails_build(sources):
    bad_persona = dataclasses.replace(sources["persona"], can_grant_permissions=True)
    with pytest.raises(SelfModelError):
        build_aurel_self_model(
            sources["kernel"],
            bad_persona,
            sources["operator"],
            sources["modes"],
            sources["compiler"],
            None,
            sources["policy"],
        )


def test_invalid_operator_contract_fails_build(sources):
    bad_operator = dataclasses.replace(
        sources["operator"],
        authority=dataclasses.replace(
            sources["operator"].authority,
            aurel_final_authority=True,
        ),
    )
    with pytest.raises(SelfModelError):
        build_aurel_self_model(
            sources["kernel"],
            sources["persona"],
            bad_operator,
            sources["modes"],
            sources["compiler"],
            None,
            sources["policy"],
        )


def test_invalid_communication_modes_fails_build(sources):
    bad_gb = dataclasses.replace(
        sources["modes"].global_boundaries,
        modes_can_execute_actions=True,
    )
    bad_modes = dataclasses.replace(sources["modes"], global_boundaries=bad_gb)
    with pytest.raises(SelfModelError):
        build_aurel_self_model(
            sources["kernel"],
            sources["persona"],
            sources["operator"],
            bad_modes,
            sources["compiler"],
            None,
            sources["policy"],
        )


def test_invalid_compiler_policy_fails_build(sources):
    bad_compiler = dataclasses.replace(
        sources["compiler"],
        safety=dataclasses.replace(
            sources["compiler"].safety,
            raw_yaml_in_prompt_forbidden=False,
        ),
    )
    with pytest.raises(SelfModelError):
        build_aurel_self_model(
            sources["kernel"],
            sources["persona"],
            sources["operator"],
            sources["modes"],
            bad_compiler,
            None,
            sources["policy"],
        )


def test_self_model_includes_source_hashes():
    model = build_aurel_self_model_from_paths(include_prompt_context=False)
    bundle = model.source_bundle
    assert len(bundle.identity_kernel_hash) == 64
    assert len(bundle.persona_manifest_hash) == 64
    assert len(bundle.operator_contract_hash) == 64
    assert len(bundle.communication_modes_hash) == 64
    assert len(bundle.identity_prompt_compiler_policy_hash) == 64


def test_self_model_includes_identity_summary():
    model = build_aurel_self_model_from_paths(include_prompt_context=False)
    text = "\n".join(model.identity_summary).lower()
    assert "aurel" in text
    assert "operator" in text


def test_self_model_includes_authority_boundaries():
    model = build_aurel_self_model_from_paths(include_prompt_context=False)
    text = "\n".join(model.authority_boundaries).lower()
    assert "self-escalat" in text
    assert "tool rights" in text


def test_self_model_includes_capability_inventory():
    model = build_aurel_self_model_from_paths(include_prompt_context=False)
    ids = {cap.id for cap in model.capability_inventory}
    assert "identity_kernel" in ids
    assert "self_model" in ids


def test_capability_inventory_marks_p15_as_planned():
    model = build_aurel_self_model_from_paths(include_prompt_context=False)
    cap = next(c for c in model.capability_inventory if c.id == "evaluation_mirror")
    assert cap.status == "planned"
    assert cap.roadmap_phase == "P1.5"


@pytest.mark.parametrize(
    "cap_id",
    ["evaluation_mirror", "policy_cards"],
)
def test_capability_inventory_marks_future_as_planned(cap_id):
    model = build_aurel_self_model_from_paths(include_prompt_context=False)
    cap = next(c for c in model.capability_inventory if c.id == cap_id)
    assert cap.status == "planned"


def test_self_model_inventory_marks_agent_identity_card_implemented():
    model = build_aurel_self_model_from_paths(include_prompt_context=False)
    cap = next(c for c in model.capability_inventory if c.id == "agent_identity_card")
    assert cap.status == "implemented"
    assert cap.roadmap_phase == "P1.4.7"


def test_self_model_does_not_mark_planned_modules_as_implemented():
    model = build_aurel_self_model_from_paths(include_prompt_context=False)
    planned_ids = {
        "evaluation_mirror",
        "mneme_memory_graph",
    }
    for cap in model.capability_inventory:
        if cap.id in planned_ids:
            assert cap.status == "planned"


def test_self_model_does_not_mark_implemented_as_verified_without_evidence():
    model = build_aurel_self_model_from_paths(include_prompt_context=False)
    for cap in model.capability_inventory:
        if cap.status == "implemented":
            assert cap.evidence_ref is None


def test_self_model_fails_validation_if_verified_without_evidence_ref(sources):
    model = build_aurel_self_model_from_paths(include_prompt_context=False)
    bad_caps = tuple(
        dataclasses.replace(cap, status="verified", evidence_ref=None)
        if cap.id == "identity_kernel"
        else cap
        for cap in model.capability_inventory
    )
    bad_model = dataclasses.replace(model, capability_inventory=bad_caps)
    result = validate_aurel_self_model(bad_model, sources["policy"])
    assert result.valid is False


def test_self_model_includes_known_limitations():
    model = build_aurel_self_model_from_paths(include_prompt_context=False)
    assert len(model.known_limitations) >= 10
    descriptions = "\n".join(item.description for item in model.known_limitations)
    assert "Evaluation Mirror" in descriptions


def test_self_model_includes_evidence_posture():
    model = build_aurel_self_model_from_paths(include_prompt_context=False)
    assert model.evidence_posture.evidence_system_phase == "P1.5 planned"


def test_evidence_posture_says_p15_planned():
    model = build_aurel_self_model_from_paths(include_prompt_context=False)
    assert "P1.5" in model.evidence_posture.evidence_system_phase


def test_evidence_posture_does_not_claim_evaluation_mirror_available():
    model = build_aurel_self_model_from_paths(include_prompt_context=False)
    assert model.evidence_posture.evaluation_mirror_available is False


def test_self_model_includes_non_goals():
    model = build_aurel_self_model_from_paths(include_prompt_context=False)
    text = "\n".join(model.non_goals).lower()
    assert "does not authorize tool execution" in text
    assert "does not imply consciousness" in text


def test_self_model_includes_next_unimplemented_modules():
    model = build_aurel_self_model_from_paths(include_prompt_context=False)
    assert any("P1.4.8" in item for item in model.next_unimplemented_modules)
    assert any("P1.5" in item for item in model.next_unimplemented_modules)


def test_displayed_output_does_not_claim_unavailable_roadmap_capabilities():
    model = build_aurel_self_model_from_paths(include_prompt_context=False)
    summary = "\n".join(model.identity_summary + model.authority_boundaries).lower()
    assert "evaluation mirror is active" not in summary
    assert "autonomy scale engine is active" not in summary


def test_displayed_output_does_not_imply_consciousness():
    model = build_aurel_self_model_from_paths(include_prompt_context=False)
    positive = "\n".join(model.identity_summary).lower()
    assert "i am conscious" not in positive
    assert "sentient" not in positive


def test_displayed_output_does_not_grant_authority():
    model = build_aurel_self_model_from_paths(include_prompt_context=False)
    positive = "\n".join(model.identity_summary + model.authority_boundaries).lower()
    assert "can grant authority" not in positive
    assert "grants authority" not in positive


def test_displayed_output_does_not_claim_verified_capability_without_evidence():
    model = build_aurel_self_model_from_paths(include_prompt_context=False)
    for cap in model.capability_inventory:
        if cap.status != "verified":
            continue
        assert cap.evidence_ref is not None
