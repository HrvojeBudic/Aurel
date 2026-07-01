"""P2.VSLICE-A governed command palette preflight vertical slice pack result."""

from __future__ import annotations

from dataclasses import dataclass

from .aurel_shell.command_availability import (
    P2_VSLICE_A_PACK_ID,
    P2_VSLICE_A_REPORT_PATH,
    build_p2_vslice_a_command_registry,
    project_command_availability,
)
from .aurel_shell.command_preflight import (
    P2VSliceAPreflightSideEffectProof,
    build_p2_vslice_a_preflight_side_effect_proof,
)
from .aurel_shell.command_projection import (
    build_command_preflight_read_model,
    run_p2_vslice_a_operator_path,
)
from .governance_enforcement import P1ENFASideEffectProof


P2_VSLICE_A_RESULT_VERSION = "p2_vslice_a_result.v1"
P2_9_B_STATUS = "NOT_DONE"


@dataclass(frozen=True)
class P2VSliceAResult:
    pack_id: str
    schema_version: str
    report_path: str
    registry_command_count: int
    projection_entry_count: int
    operator_path_available: bool
    preflight_only: bool
    command_execution_implemented: bool
    shell_live_claimed: bool
    p2_9_b_status: str
    side_effect_proof: P2VSliceAPreflightSideEffectProof
    p1_enf_side_effect_proof: P1ENFASideEffectProof

    def to_canonical_dict(self) -> dict[str, object]:
        return {
            "command_execution_implemented": self.command_execution_implemented,
            "operator_path_available": self.operator_path_available,
            "p1_enf_side_effect_proof": self.p1_enf_side_effect_proof.to_canonical_dict(),
            "p2_9_b_status": self.p2_9_b_status,
            "pack_id": self.pack_id,
            "preflight_only": self.preflight_only,
            "projection_entry_count": self.projection_entry_count,
            "registry_command_count": self.registry_command_count,
            "report_path": self.report_path,
            "schema_version": self.schema_version,
            "shell_live_claimed": self.shell_live_claimed,
            "side_effect_proof": self.side_effect_proof.to_canonical_dict(),
        }


def build_p2_vslice_a_result() -> P2VSliceAResult:
    registry = build_p2_vslice_a_command_registry()
    projection = project_command_availability(registry)
    operator_path = run_p2_vslice_a_operator_path()
    read_model = build_command_preflight_read_model()
    side_effects = build_p2_vslice_a_preflight_side_effect_proof()
    enf_proof = P1ENFASideEffectProof()
    assert operator_path.preflight_decision is not None
    assert operator_path.preflight_decision.executes_command is False
    assert read_model.cli_tui_binding_available is False
    assert side_effects.p2_9_b_implemented is False
    assert enf_proof.p2_9_b_implemented is False
    return P2VSliceAResult(
        pack_id=P2_VSLICE_A_PACK_ID,
        schema_version=P2_VSLICE_A_RESULT_VERSION,
        report_path=P2_VSLICE_A_REPORT_PATH,
        registry_command_count=len(registry.commands),
        projection_entry_count=len(projection.entries),
        operator_path_available=True,
        preflight_only=True,
        command_execution_implemented=False,
        shell_live_claimed=False,
        p2_9_b_status=P2_9_B_STATUS,
        side_effect_proof=side_effects,
        p1_enf_side_effect_proof=enf_proof,
    )
