"""P2.VSLICE-A command projection read model.

Operator-testable read-model path for listing, inspecting, and preflighting
governed global commands without CLI/TUI product behavior.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from agentic_runtime.governance_enforcement import GovernanceEnforcementConfig

from .command_availability import (
    CommandAvailabilityProjection,
    GlobalCommandContract,
    P2_VSLICE_A_PACK_ID,
    P2_VSLICE_A_REPORT_PATH,
    build_p2_vslice_a_command_registry,
    list_command_contracts,
    lookup_command_contract,
    project_command_availability,
)
from .command_preflight import (
    CommandIntent,
    CommandIntentSource,
    CommandPreflightDecision,
    P2VSliceAPreflightSideEffectProof,
    build_command_intent,
    build_p2_vslice_a_preflight_side_effect_proof,
    run_command_preflight,
)
from .contracts import _CanonicalMixin, _hash_payload


P2_VSLICE_A_READ_MODEL_VERSION = "p2_vslice_a_command_preflight_read_model.v1"


@dataclass(frozen=True)
class CommandInspectReadModel(_CanonicalMixin):
    command: GlobalCommandContract
    availability_entry_truth: str
    preflight_only: bool
    execution_claim: bool
    read_model_hash: str


@dataclass(frozen=True)
class CommandPreflightReadModel(_CanonicalMixin):
    schema_version: str
    pack_id: str
    registry_command_count: int
    projection: CommandAvailabilityProjection
    side_effect_proof: P2VSliceAPreflightSideEffectProof
    cli_tui_binding_available: bool
    cli_tui_unavailable_reason: str
    read_model_hash: str


@dataclass(frozen=True)
class P2VSliceAOperatorPathResult(_CanonicalMixin):
    listed_commands: tuple[GlobalCommandContract, ...]
    inspected_command: CommandInspectReadModel | None
    preflight_decision: CommandPreflightDecision | None
    read_model: CommandPreflightReadModel
    result_hash: str


def build_command_preflight_read_model() -> CommandPreflightReadModel:
    registry = build_p2_vslice_a_command_registry()
    projection = project_command_availability(registry)
    side_effects = build_p2_vslice_a_preflight_side_effect_proof()
    payload = {
        "schema_version": P2_VSLICE_A_READ_MODEL_VERSION,
        "pack_id": P2_VSLICE_A_PACK_ID,
        "registry_command_count": len(registry.commands),
        "projection": projection,
        "side_effect_proof": side_effects,
        "cli_tui_binding_available": False,
        "cli_tui_unavailable_reason": (
            "CLI/TUI command palette binding remains contract-only; "
            "pytest read-model harness is the operator-testable path for P2.VSLICE-A."
        ),
    }
    return CommandPreflightReadModel(**payload, read_model_hash=_hash_payload(payload))


def list_global_commands() -> tuple[GlobalCommandContract, ...]:
    return list_command_contracts()


def inspect_global_command(command_id: str) -> CommandInspectReadModel | None:
    command = lookup_command_contract(command_id)
    if command is None:
        return None
    projection = project_command_availability()
    availability_truth = command.truth_state.value
    for entry in projection.entries:
        if entry.command_id == command.command_id:
            availability_truth = entry.truth_label
            break
    payload = {
        "command": command,
        "availability_entry_truth": availability_truth,
        "preflight_only": command.allows_preflight,
        "execution_claim": command.allows_execution,
    }
    return CommandInspectReadModel(**payload, read_model_hash=_hash_payload(payload))


def preflight_global_command(
    command_id: str,
    *,
    arguments: Mapping[str, str] | None = None,
    source: CommandIntentSource = CommandIntentSource.OPERATOR,
    governance_config: GovernanceEnforcementConfig | None = None,
    policy_registry: Any | None = None,
    policy_context: Any | None = None,
    simulate_policy_deny: bool = False,
    simulate_identity_deny: bool = False,
    simulate_sandbox_deny: bool = False,
) -> CommandPreflightDecision:
    intent = build_command_intent(
        command_id,
        source=source,
        arguments=arguments,
    )
    return run_command_preflight(
        intent,
        governance_config=governance_config,
        policy_registry=policy_registry,
        policy_context=policy_context,
        simulate_policy_deny=simulate_policy_deny,
        simulate_identity_deny=simulate_identity_deny,
        simulate_sandbox_deny=simulate_sandbox_deny,
    )


def run_p2_vslice_a_operator_path(
    *,
    inspect_command_id: str = "shell.command.preflight",
    preflight_command_id: str = "shell.command.preflight",
) -> P2VSliceAOperatorPathResult:
    read_model = build_command_preflight_read_model()
    listed = list_global_commands()
    inspected = inspect_global_command(inspect_command_id)
    preflight = preflight_global_command(preflight_command_id)
    payload = {
        "listed_commands": listed,
        "inspected_command": inspected,
        "preflight_decision": preflight,
        "read_model": read_model,
    }
    return P2VSliceAOperatorPathResult(**payload, result_hash=_hash_payload(payload))


def render_command_list_summary(
    commands: tuple[GlobalCommandContract, ...] | None = None,
) -> str:
    if commands is None:
        commands = list_global_commands()
    lines = [f"P2.VSLICE-A global commands ({len(commands)})"]
    for command in commands:
        lines.append(
            f"  {command.slug} [{command.truth_state.value}] "
            f"mode={command.interaction_mode.value}"
        )
    return "\n".join(lines)


def render_preflight_decision_summary(decision: CommandPreflightDecision) -> str:
    command_slug = decision.command.slug if decision.command else "unknown"
    return "\n".join(
        (
            f"P2.VSLICE-A preflight: {command_slug}",
            f"outcome={decision.outcome.value}",
            f"truth_label={decision.truth_label}",
            f"preflight_allowed={str(decision.preflight_allowed).lower()}",
            f"executes_command={str(decision.executes_command).lower()}",
            f"policy={decision.policy_decision_summary.decision}",
            f"identity={decision.identity_invariant_summary.decision}",
            f"sandbox={decision.sandbox_backend_gate_summary.decision}",
            f"evidence_refs={len(decision.evidence_refs)}",
            f"report={P2_VSLICE_A_REPORT_PATH}",
        )
    )
