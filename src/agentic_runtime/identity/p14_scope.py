"""P1.4 scope constants (P1.4.0) — static names and patch IDs only.

Architectural law (see docs/P1.4_IDENTITY_AUTONOMY_SCOPE_CONTRACT.md):
  - Identity is not policy.
  - Persona is not authority.
  - Communication mode is not permission.
  - Tool access is not tool authority.
  - Operator is the final authority.
  - Aurel cannot self-escalate autonomy.
"""
from __future__ import annotations

P14_PATCHES: tuple[str, ...] = tuple(f"P1.4.{i}" for i in range(21))

P14_SCOPE_IN: frozenset[str] = frozenset(
    {
        "identity_kernel",
        "persona_manifest",
        "operator_relationship_contract",
        "communication_modes",
        "identity_prompt_context_compiler",
        "self_model",
        "agent_identity_card",
        "autonomy_scale_engine",
        "measured_autonomy_score",
        "governance_heretic_profiles",
        "constitutional_floor",
        "code_inspection_autonomy_score",
        "agentic_profile",
        "identity_integrity_guard",
        "principal_delegate_model",
        "heretic_sandbox",
        "continuity_capsule",
        "metacognitive_drift_signals",
        "regulatory_standards_registry",
        "p14_seal",
    }
)

P14_SCOPE_OUT: frozenset[str] = frozenset(
    {
        "full_memory_graph",
        "full_policy_card_engine",
        "full_path_governance_engine",
        "full_delegation_mesh",
        "full_provenance_disclosure_engine",
        "neural_world_model",
        "autonomous_self_improvement",
        "lora_fine_tuning_pipeline",
        "full_shell_ui",
    }
)

P14_FORWARD_HOOKS: frozenset[str] = frozenset(
    {
        "P1.5",
        "P1.6",
        "P1.7",
        "P1.8",
        "P1.9",
        "P3",
        "P10",
        "P11",
        "P14",
        "P21",
    }
)
