"""P2.VSLICE-A governed command palette vertical slice tests."""

from __future__ import annotations

from agentic_runtime.aurel_shell.command_availability import (
    P2_VSLICE_A_PACK_ID,
    CommandAvailabilityTruth,
    GlobalCommandInteractionMode,
    build_p2_vslice_a_command_registry,
    list_command_contracts,
    lookup_command_contract,
    project_command_availability,
)
from agentic_runtime.aurel_shell.command_projection import (
    build_command_preflight_read_model,
    inspect_global_command,
    list_global_commands,
    preflight_global_command,
    render_command_list_summary,
    run_p2_vslice_a_operator_path,
)
from agentic_runtime.p2_command_palette_vslice import (
    P2_9_B_STATUS,
    build_p2_vslice_a_result,
)


def test_global_command_registry_lists_seed_commands() -> None:
    registry = build_p2_vslice_a_command_registry()
    slugs = {command.slug for command in registry.commands}
    assert "shell.commands.list" in slugs
    assert "shell.command.inspect" in slugs
    assert "shell.command.preflight" in slugs
    assert "surface.registry.list" in slugs
    assert "system.status.read" in slugs
    assert "evidence.latest.read" in slugs
    assert "shell.command.execute" in slugs
    assert registry.executes_commands is False


def test_global_command_contract_has_version_and_truth_state() -> None:
    command = lookup_command_contract("shell.command.preflight")
    assert command is not None
    assert command.schema_version.startswith("p2_vslice_a_")
    assert command.truth_state is CommandAvailabilityTruth.AVAILABLE_PREFLIGHT_ONLY
    assert command.allows_execution is False
    assert command.claims_live is False
    assert command.claims_trace_verified is False


def test_command_availability_projection_marks_preflight_only() -> None:
    projection = project_command_availability()
    preflight_entries = [
        entry
        for entry in projection.entries
        if entry.command_id == "global_command:shell.command.preflight"
    ]
    assert len(preflight_entries) == 1
    entry = preflight_entries[0]
    assert entry.available_for_preflight is True
    assert entry.available_for_execution is False
    assert entry.truth_state is CommandAvailabilityTruth.AVAILABLE_PREFLIGHT_ONLY
    assert projection.uses_live is False
    assert projection.uses_trace_verified is False


def test_dev_fixture_command_does_not_claim_live() -> None:
    command = lookup_command_contract("system.status.read")
    assert command is not None
    assert command.truth_state is CommandAvailabilityTruth.AVAILABLE_DEV_FIXTURE
    assert command.claims_live is False


def test_p2_vslice_a_produces_evidence_refs() -> None:
    result = build_p2_vslice_a_result()
    operator = run_p2_vslice_a_operator_path()
    assert result.operator_path_available is True
    assert operator.preflight_decision is not None
    assert len(operator.preflight_decision.evidence_refs) >= 1
    assert result.report_path.endswith(
        "P2_VSLICE_A_GOVERNED_COMMAND_PALETTE_PREFLIGHT.md"
    )


def test_p2_vslice_a_keeps_p29b_not_done() -> None:
    result = build_p2_vslice_a_result()
    assert result.p2_9_b_status == P2_9_B_STATUS == "NOT_DONE"
    assert result.side_effect_proof.p2_9_b_implemented is False
    assert result.p1_enf_side_effect_proof.p2_9_b_implemented is False


def test_operator_path_list_inspect_preflight() -> None:
    commands = list_global_commands()
    assert len(commands) >= 6
    inspected = inspect_global_command("shell.commands.list")
    assert inspected is not None
    assert inspected.execution_claim is False
    decision = preflight_global_command("shell.commands.list")
    assert decision.preflight_allowed is True
    assert decision.executes_command is False
    summary = render_command_list_summary()
    assert "shell.commands.list" in summary


def test_read_model_marks_cli_tui_gap() -> None:
    read_model = build_command_preflight_read_model()
    assert read_model.cli_tui_binding_available is False
    assert "pytest read-model harness" in read_model.cli_tui_unavailable_reason


def test_risky_execute_command_is_unavailable() -> None:
    command = lookup_command_contract("shell.command.execute")
    assert command is not None
    assert command.interaction_mode is GlobalCommandInteractionMode.UNAVAILABLE
    assert command.truth_state is CommandAvailabilityTruth.UNAVAILABLE_BACKEND_MISSING
    decision = preflight_global_command("shell.command.execute")
    assert decision.execution_allowed is False
    assert decision.executes_command is False


def test_pack_id_constant() -> None:
    assert P2_VSLICE_A_PACK_ID == "P2.VSLICE-A"
    assert list_command_contracts() == list_global_commands()
