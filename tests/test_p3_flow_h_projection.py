"""P3-FLOW-H governed autonomy projection behavior tests.

The projection is read-only: no UI autonomy toggle, override, or execution
authority, no frontend mutation, no API server, no frontend.
"""

from __future__ import annotations

import pytest

from agentic_runtime.aurel_flow import (
    AurelFlowValidationError,
    AutonomyDecisionClass,
    AutonomyGateInput,
    AutonomyModeSource,
    AutonomyScopeDimension,
    AutonomyViolationKind,
    FlowTruthLabel,
    GovernedAutonomyLevel,
    build_autonomy_scope_envelope,
    build_autonomy_violation_signal,
    build_governed_autonomy_projection,
    create_autonomy_scope_limit,
    evaluate_autonomy_gate,
    select_autonomy_mode,
)


def _projection_fixture():
    mode = select_autonomy_mode(
        run_id="run-1",
        level=GovernedAutonomyLevel.A2_PREPARE_CANDIDATES,
        mode_source=AutonomyModeSource.OPERATOR_SELECTED,
        selected_by="op-1",
    )
    scope = build_autonomy_scope_envelope(
        run_id="run-1",
        level=mode.level,
        limits=(
            create_autonomy_scope_limit(
                dimension=AutonomyScopeDimension.RUN_SCOPE,
                limit_description="this run only",
            ),
        ),
    )
    gate = evaluate_autonomy_gate(
        AutonomyGateInput(
            run_id="run-1",
            level=mode.level,
            decision_class=AutonomyDecisionClass.PREPARE_PLAN,
            budget_exhausted=True,
        )
    )
    violation = build_autonomy_violation_signal(
        run_id="run-1",
        kind=AutonomyViolationKind.SELF_UPGRADE_ATTEMPTED,
        detail="attempted self-upgrade",
    )
    projection = build_governed_autonomy_projection(
        mode, scope=scope, gate_results=(gate,), violations=(violation,)
    )
    return mode, scope, gate, violation, projection


def test_projection_summarizes_mode_scope_gates_and_violations() -> None:
    mode, scope, gate, _violation, projection = _projection_fixture()
    assert projection.level_value == mode.level.value
    assert projection.mode_source_value == "OPERATOR_SELECTED"
    assert projection.scope_dimension_count == len(scope.limits)
    assert projection.gate_decision_values == (gate.decision.value,)
    assert projection.violation_count == 1
    assert projection.attempted_self_upgrade_present is True
    assert projection.escalation_or_review_needed is True
    assert projection.truth_label is FlowTruthLabel.READ_MODEL_ONLY


def test_projection_resolver_summary_covers_every_decision_class() -> None:
    (*_rest, projection) = _projection_fixture()
    assert sum(projection.resolver_permission_state_counts.values()) == len(
        AutonomyDecisionClass
    )
    assert "FORBIDDEN_IN_P3" in projection.resolver_permission_state_counts


def test_projection_is_deterministic() -> None:
    first = _projection_fixture()[4]
    second = _projection_fixture()[4]
    assert first.projection_id == second.projection_id


def test_projection_preserves_ui_powerlessness() -> None:
    (*_rest, projection) = _projection_fixture()
    assert projection.react_projection_only is True
    assert projection.frontend_mutation_allowed is False
    assert projection.ui_autonomy_toggle_authority is False
    assert projection.ui_override_authority is False
    assert projection.ui_execution_allowed is False
    assert projection.api_server_implemented is False
    assert projection.frontend_implemented is False
    for forbidden_field in (
        "ui_autonomy_toggle_authority",
        "ui_override_authority",
        "ui_execution_allowed",
        "frontend_implemented",
    ):
        with pytest.raises(AurelFlowValidationError):
            type(projection)(
                **{
                    **{
                        field.name: getattr(projection, field.name)
                        for field in projection.__dataclass_fields__.values()
                    },
                    forbidden_field: True,
                }
            )


def test_projection_rejects_foreign_run_sources() -> None:
    mode, _scope, _gate, _violation, _projection = _projection_fixture()
    foreign_scope = build_autonomy_scope_envelope(
        run_id="other-run",
        level=mode.level,
        limits=(),
    )
    with pytest.raises(AurelFlowValidationError):
        build_governed_autonomy_projection(mode, scope=foreign_scope)
