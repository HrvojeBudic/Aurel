"""P1.4.7 — Agent Identity Card config, builder, validation tests (cases #1-46, #61-64)."""

from __future__ import annotations

import dataclasses
from pathlib import Path

import pytest

from agentic_runtime.identity.agent_identity_card_builder import (
    build_agent_identity_card,
    build_agent_identity_card_from_paths,
)
from agentic_runtime.identity.agent_identity_card_policy import (
    AgentIdentityCardError,
    default_agent_identity_card_path,
    load_agent_identity_card_config,
    parse_agent_identity_card_document,
)
from agentic_runtime.identity.agent_identity_card_validation import (
    validate_agent_identity_card,
    validate_agent_identity_card_config,
)
from agentic_runtime.identity.communication_modes import load_communication_mode_registry
from agentic_runtime.identity.kernel import load_identity_kernel
from agentic_runtime.identity.operator_contract import load_operator_contract
from agentic_runtime.identity.persona import load_persona_manifest
from agentic_runtime.identity.runtime_instance import (
    RUNTIME_INSTANCE_PREFIX,
    generate_runtime_instance_id,
)
from agentic_runtime.identity.self_model_builder import build_aurel_self_model_from_paths
from agentic_runtime.identity.self_model_policy import load_self_model_policy
from agentic_runtime.prompts.compiler_policy import load_identity_prompt_compiler_policy
from agentic_runtime.yaml_minimal import load_yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
CANONICAL = REPO_ROOT / "config" / "aurel" / "agent_identity_card.yaml"
FIXED_RUNTIME_ID = "aurel-runtime-00000000-0000-4000-8000-000000000001"


def _load_doc() -> dict:
    return load_yaml(CANONICAL.read_text(encoding="utf-8"))


def _copy_to(tmp_path: Path) -> Path:
    target = tmp_path / "agent_identity_card.yaml"
    target.write_text(CANONICAL.read_text(encoding="utf-8"), encoding="utf-8")
    return target


def _validate_with_field(tmp_path: Path, old: str, new: str):
    path = _copy_to(tmp_path)
    text = path.read_text(encoding="utf-8").replace(old, new, 1)
    path.write_text(text, encoding="utf-8")
    return validate_agent_identity_card_config(load_agent_identity_card_config(path))


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
        "card_config": load_agent_identity_card_config(CANONICAL),
        "self_model": build_aurel_self_model_from_paths(include_prompt_context=True),
        "policy": load_self_model_policy(REPO_ROOT / "config/aurel/self_model_policy.yaml"),
    }


def _build_card(sources, runtime_instance_id: str | None = FIXED_RUNTIME_ID):
    return build_agent_identity_card(
        sources["kernel"],
        sources["persona"],
        sources["operator"],
        sources["modes"],
        sources["compiler"],
        sources["self_model"],
        sources["policy"],
        sources["card_config"],
        runtime_instance_id=runtime_instance_id,
    )


# 1, 2
def test_valid_config_loads_and_validates():
    config = load_agent_identity_card_config(CANONICAL)
    result = validate_agent_identity_card_config(config)
    assert result.valid is True
    assert config.card_class == "machine_readable_agent_identity"
    assert config.applies_to_agent == "Aurel"
    assert len(config.invariants) == 6


def test_default_path_points_to_canonical():
    assert default_agent_identity_card_path() == CANONICAL


# 3
def test_missing_agent_identity_card_section_fails():
    with pytest.raises(AgentIdentityCardError, match="agent_identity_card"):
        parse_agent_identity_card_document({"something_else": {}})


# 4
def test_card_class_not_machine_readable_fails(tmp_path):
    result = _validate_with_field(
        tmp_path,
        'card_class: "machine_readable_agent_identity"',
        'card_class: "marketing_card"',
    )
    assert result.valid is False


# 5
def test_applies_to_agent_not_aurel_fails(tmp_path):
    result = _validate_with_field(
        tmp_path, 'applies_to_agent: "Aurel"', 'applies_to_agent: "OtherAgent"'
    )
    assert result.valid is False


def test_agent_type_not_ai_agent_fails_at_parse(tmp_path):
    path = _copy_to(tmp_path)
    text = path.read_text(encoding="utf-8").replace('agent_type: "ai_agent"', 'agent_type: "human"', 1)
    path.write_text(text, encoding="utf-8")
    with pytest.raises(AgentIdentityCardError, match="agent_type"):
        load_agent_identity_card_config(path)


@pytest.mark.parametrize(
    ("field", "old", "new"),
    [
        ("agent_id", 'agent_id: "aurel.local.operator.primary"', 'agent_id: "other.agent"'),
        ("agent_name", 'agent_name: "Aurel"', 'agent_name: "NotAurel"'),
        ("agent_class", 'agent_class: "sovereign_personal_agent"', 'agent_class: "generic"'),
        ("identity_version", 'identity_version: "1.4"', 'identity_version: "9.9"'),
        (
            "deployment_scope",
            'deployment_scope: "single_operator_local_first"',
            'deployment_scope: "cloud_multi_tenant"',
        ),
        ("machine_scope", 'machine_scope: "local"', 'machine_scope: "remote"'),
    ],
)
def test_agent_field_mismatch_fails(tmp_path, field, old, new):
    result = _validate_with_field(tmp_path, old, new)
    assert result.valid is False, field


@pytest.mark.parametrize(
    ("old", "new"),
    [
        ('authority_source: "operator"', 'authority_source: "aurel"'),
        ('final_authority: "operator"', 'final_authority: "aurel"'),
        ("self_escalation_allowed: false", "self_escalation_allowed: true"),
        ("delegated_authority_required_for_actions: true", "delegated_authority_required_for_actions: false"),
        ("tool_access_implies_authority: false", "tool_access_implies_authority: true"),
    ],
)
def test_authority_field_mismatch_fails(tmp_path, old, new):
    result = _validate_with_field(tmp_path, old, new)
    assert result.valid is False


@pytest.mark.parametrize(
    ("old", "new"),
    [
        (
            'runtime_instance_id_strategy: "local_generated_uuid"',
            'runtime_instance_id_strategy: "external_oauth"',
        ),
        ('runtime_machine_scope: "local"', 'runtime_machine_scope: "cloud"'),
        ("local_first: true", "local_first: false"),
    ],
)
def test_runtime_field_mismatch_fails(tmp_path, old, new):
    result = _validate_with_field(tmp_path, old, new)
    assert result.valid is False


def test_taxonomy_agent_identity_must_match_agent_id(tmp_path):
    result = _validate_with_field(
        tmp_path,
        'agent_identity: "aurel.local.operator.primary"',
        'agent_identity: "mismatch.agent"',
    )
    assert result.valid is False


def test_taxonomy_human_must_differ_from_agent(tmp_path):
    result = _validate_with_field(
        tmp_path,
        'human_principal_identity: "operator.primary"',
        'human_principal_identity: "aurel.local.operator.primary"',
    )
    assert result.valid is False


@pytest.mark.parametrize(
    "boundary_field",
    [
        "card_can_grant_authority",
        "card_can_change_identity_kernel",
        "card_can_change_autonomy",
        "card_can_create_delegation",
        "card_can_authorize_tools",
        "card_can_replace_operator",
        "card_can_override_policy",
    ],
)
def test_boundary_must_be_false(tmp_path, boundary_field):
    path = _copy_to(tmp_path)
    text = path.read_text(encoding="utf-8").replace(f"{boundary_field}: false", f"{boundary_field}: true", 1)
    path.write_text(text, encoding="utf-8")
    result = validate_agent_identity_card_config(load_agent_identity_card_config(path))
    assert result.valid is False


@pytest.mark.parametrize(
    ("invariant_id", "key"),
    [
        ("AIC-001", "card_can_grant_authority"),
        ("AIC-002", "self_escalation_allowed"),
        ("AIC-003", "tool_access_implies_authority"),
        ("AIC-004", "card_can_create_delegation"),
        ("AIC-005", "card_can_replace_operator"),
        ("AIC-006", "agent_type"),
    ],
)
def test_invariants_present(invariant_id, key):
    config = load_agent_identity_card_config(CANONICAL)
    inv = next(item for item in config.invariants if item.id == invariant_id)
    assert inv.key == key
    assert inv.severity == "critical"
    assert inv.violation_action == "fail_build"


def test_aic006_expected_value_is_string():
    config = load_agent_identity_card_config(CANONICAL)
    inv = next(item for item in config.invariants if item.id == "AIC-006")
    assert inv.expected_value == "ai_agent"


def test_unknown_invariant_key_fails(tmp_path):
    path = _copy_to(tmp_path)
    text = path.read_text(encoding="utf-8").replace(
        'key: "card_can_grant_authority"', 'key: "unknown_invariant_key"', 1
    )
    path.write_text(text, encoding="utf-8")
    result = validate_agent_identity_card_config(load_agent_identity_card_config(path))
    assert result.valid is False


def test_build_agent_identity_card_succeeds():
    card = build_agent_identity_card_from_paths(runtime_instance_id=FIXED_RUNTIME_ID)
    assert card.agent.agent_name == "Aurel"
    assert card.runtime.runtime_instance_id == FIXED_RUNTIME_ID


def test_build_populates_all_source_hashes(sources):
    card = _build_card(sources)
    bindings = card.source_bindings
    for value in (
        bindings.identity_kernel_hash,
        bindings.persona_manifest_hash,
        bindings.operator_contract_hash,
        bindings.communication_modes_hash,
        bindings.identity_prompt_compiler_policy_hash,
        bindings.self_model_hash,
    ):
        assert value is not None
        assert len(value) == 64


def test_runtime_instance_id_generated_when_not_supplied():
    card = build_agent_identity_card_from_paths(runtime_instance_id=None)
    runtime_id = card.runtime.runtime_instance_id
    assert runtime_id is not None
    assert runtime_id.startswith(RUNTIME_INSTANCE_PREFIX)


def test_runtime_instance_id_is_not_secret_like():
    generated = generate_runtime_instance_id().value
    assert "secret" not in generated.lower()
    assert "token" not in generated.lower()
    assert "credential" not in generated.lower()


def test_invalid_kernel_fails_build(sources):
    bad_kernel = dataclasses.replace(
        sources["kernel"],
        immutables=dataclasses.replace(
            sources["kernel"].immutables,
            self_escalation_allowed=True,
        ),
    )
    with pytest.raises(AgentIdentityCardError):
        build_agent_identity_card(
            bad_kernel,
            sources["persona"],
            sources["operator"],
            sources["modes"],
            sources["compiler"],
            sources["self_model"],
            sources["policy"],
            sources["card_config"],
            runtime_instance_id=FIXED_RUNTIME_ID,
        )


def test_invalid_persona_fails_build(sources):
    bad_persona = dataclasses.replace(sources["persona"], can_grant_permissions=True)
    with pytest.raises(AgentIdentityCardError):
        build_agent_identity_card(
            sources["kernel"],
            bad_persona,
            sources["operator"],
            sources["modes"],
            sources["compiler"],
            sources["self_model"],
            sources["policy"],
            sources["card_config"],
            runtime_instance_id=FIXED_RUNTIME_ID,
        )


def test_invalid_operator_fails_build(sources):
    bad_operator = dataclasses.replace(
        sources["operator"],
        authority=dataclasses.replace(
            sources["operator"].authority,
            aurel_final_authority=True,
        ),
    )
    with pytest.raises(AgentIdentityCardError):
        build_agent_identity_card(
            sources["kernel"],
            sources["persona"],
            bad_operator,
            sources["modes"],
            sources["compiler"],
            sources["self_model"],
            sources["policy"],
            sources["card_config"],
            runtime_instance_id=FIXED_RUNTIME_ID,
        )


def test_invalid_modes_fails_build(sources):
    bad_modes = dataclasses.replace(
        sources["modes"],
        global_boundaries=dataclasses.replace(
            sources["modes"].global_boundaries,
            modes_can_execute_actions=True,
        ),
    )
    with pytest.raises(AgentIdentityCardError):
        build_agent_identity_card(
            sources["kernel"],
            sources["persona"],
            sources["operator"],
            bad_modes,
            sources["compiler"],
            sources["self_model"],
            sources["policy"],
            sources["card_config"],
            runtime_instance_id=FIXED_RUNTIME_ID,
        )


def test_invalid_compiler_fails_build(sources):
    bad_compiler = dataclasses.replace(
        sources["compiler"],
        safety=dataclasses.replace(
            sources["compiler"].safety,
            raw_yaml_in_prompt_forbidden=False,
        ),
    )
    with pytest.raises(AgentIdentityCardError):
        build_agent_identity_card(
            sources["kernel"],
            sources["persona"],
            sources["operator"],
            sources["modes"],
            bad_compiler,
            sources["self_model"],
            sources["policy"],
            sources["card_config"],
            runtime_instance_id=FIXED_RUNTIME_ID,
        )


def test_invalid_card_config_fails_build(sources, tmp_path):
    path = _copy_to(tmp_path)
    text = path.read_text(encoding="utf-8").replace("card_can_grant_authority: false", "card_can_grant_authority: true", 1)
    path.write_text(text, encoding="utf-8")
    bad_config = load_agent_identity_card_config(path)
    with pytest.raises(AgentIdentityCardError):
        build_agent_identity_card(
            sources["kernel"],
            sources["persona"],
            sources["operator"],
            sources["modes"],
            sources["compiler"],
            sources["self_model"],
            sources["policy"],
            bad_config,
            runtime_instance_id=FIXED_RUNTIME_ID,
        )


def test_built_card_passes_final_validation(sources):
    card = _build_card(sources)
    result = validate_agent_identity_card(card)
    assert result.valid is True


def test_card_does_not_grant_authority(sources):
    card = _build_card(sources)
    assert card.boundaries.card_can_grant_authority is False
    assert card.authority.final_authority == "operator"


def test_card_does_not_create_delegation(sources):
    card = _build_card(sources)
    assert card.boundaries.card_can_create_delegation is False


def test_card_does_not_authorize_tools(sources):
    card = _build_card(sources)
    assert card.boundaries.card_can_authorize_tools is False
    assert card.authority.tool_access_implies_authority is False


def test_config_source_bindings_null_before_build():
    config = load_agent_identity_card_config(CANONICAL)
    assert config.source_bindings.identity_kernel_hash is None
    assert config.source_bindings.self_model_hash is None


def test_runtime_started_at_excluded_from_card(sources):
    card = _build_card(sources)
    assert card.runtime.runtime_started_at is None


# 61-64 regression guards
def test_import_public_api():
    from agentic_runtime.identity import (
        build_agent_identity_card_from_paths,
        compute_stable_agent_identity_hash,
        load_agent_identity_card_config,
        validate_agent_identity_card,
    )

    config = load_agent_identity_card_config()
    assert validate_agent_identity_card_config(config).valid
    card = build_agent_identity_card_from_paths(runtime_instance_id=FIXED_RUNTIME_ID)
    assert compute_stable_agent_identity_hash(card)
    assert validate_agent_identity_card(card).valid


def test_canonical_stable_hash_snapshot():
    card = build_agent_identity_card_from_paths(runtime_instance_id=FIXED_RUNTIME_ID)
    assert card.stable_agent_identity_hash == (
        "706d7e47dc0e9941dc8e2894628fec0f94e34d4cf9c1747cd494e22a1950441c"
    )


def test_canonical_runtime_hash_snapshot():
    card = build_agent_identity_card_from_paths(runtime_instance_id=FIXED_RUNTIME_ID)
    assert card.runtime_agent_identity_card_hash == (
        "16173d97701bfc45f132ea035c8fc95cc34e48bca857724e7699131f7d5eb925"
    )


def test_future_placeholders_remain_null_in_config():
    config = load_agent_identity_card_config(CANONICAL)
    placeholders = config.future_placeholders
    assert placeholders.delegation_grant_ref is None
    assert placeholders.non_repudiation_key_ref is None
