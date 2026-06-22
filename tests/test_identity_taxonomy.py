"""P1.4.7 — Identity taxonomy tests (cases #24-26, #58)."""

from __future__ import annotations

from agentic_runtime.identity.agent_identity_card_builder import build_agent_identity_card_from_paths
from agentic_runtime.identity.agent_identity_card_policy import load_agent_identity_card_config
from agentic_runtime.identity.identity_taxonomy import (
    TAXONOMY_NOT_IMPLEMENTED_NOTES,
    taxonomy_notes_for_null_fields,
)

FIXED_RUNTIME_ID = "aurel-runtime-00000000-0000-4000-8000-000000000001"


# 24
def test_taxonomy_agent_identity_equals_agent_id():
    config = load_agent_identity_card_config()
    assert config.identity_taxonomy.agent_identity == config.agent.agent_id


# 25
def test_taxonomy_human_principal_differs_from_agent():
    config = load_agent_identity_card_config()
    taxonomy = config.identity_taxonomy
    assert taxonomy.human_principal_identity
    assert taxonomy.human_principal_identity != taxonomy.agent_identity


# 26
def test_null_taxonomy_placeholders_surface_not_implemented_notes():
    config = load_agent_identity_card_config()
    taxonomy = config.identity_taxonomy
    notes = taxonomy_notes_for_null_fields(
        taxonomy.model_identity,
        taxonomy.workload_identity,
        taxonomy.delegated_identity,
    )
    assert len(notes) == 3
    for note in notes:
        assert "not implemented in P1.4.7" in note


def test_taxonomy_note_constants():
    assert "model_identity" in TAXONOMY_NOT_IMPLEMENTED_NOTES
    assert "workload_identity" in TAXONOMY_NOT_IMPLEMENTED_NOTES
    assert "delegated_identity" in TAXONOMY_NOT_IMPLEMENTED_NOTES


# 58
def test_built_card_preserves_identity_type_distinctions():
    card = build_agent_identity_card_from_paths(runtime_instance_id=FIXED_RUNTIME_ID)
    taxonomy = card.identity_taxonomy
    assert taxonomy.agent_identity == card.agent.agent_id
    assert taxonomy.human_principal_identity != taxonomy.agent_identity
    assert taxonomy.model_identity is None
    assert taxonomy.workload_identity is None
    assert taxonomy.delegated_identity is None
    assert card.agent.agent_type == "ai_agent"
