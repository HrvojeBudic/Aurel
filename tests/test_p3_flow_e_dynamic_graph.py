"""P3-FLOW-E template vs realized runtime graph tests (P3.13.0-P3.13.4)."""

from __future__ import annotations

import pytest

from agentic_runtime.aurel_flow import (
    AurelFlowValidationError,
    FlowTruthLabel,
    GraphDeterminationTime,
    GraphDeterminationTimeKind,
    GraphRealizationReason,
    RealizedRuntimeGraph,
    RealizedRuntimeGraphRef,
    RuntimeGraphInstance,
    WorkflowTemplate,
    WorkflowTemplateRef,
    build_flow_demo_bundle,
    build_runtime_graph_instance,
    create_workflow_template,
    realize_runtime_graph,
    realized_runtime_graph_ref,
    workflow_template_ref,
)


def _bundle():
    return build_flow_demo_bundle()


def test_workflow_template_created_from_graph() -> None:
    bundle = _bundle()
    template = create_workflow_template(bundle.graph)
    assert isinstance(template, WorkflowTemplate)
    assert template.source_workflow_graph_id == bundle.graph.graph_id
    assert template.node_count == len(bundle.graph.nodes)
    assert template.edge_count == len(bundle.graph.edges)
    assert template.truth_label is FlowTruthLabel.CONTRACT_ONLY


def test_template_ref_matches_template() -> None:
    bundle = _bundle()
    template = create_workflow_template(bundle.graph)
    ref = workflow_template_ref(template)
    assert isinstance(ref, WorkflowTemplateRef)
    assert ref.template_id == template.template_id
    assert ref.template_version == template.version


def test_template_construction_is_deterministic() -> None:
    bundle = _bundle()
    template_a = create_workflow_template(bundle.graph)
    template_b = create_workflow_template(bundle.graph)
    assert template_a.template_id == template_b.template_id
    assert template_a.template_hash == template_b.template_hash


def test_realized_graph_is_distinct_from_template() -> None:
    bundle = _bundle()
    template = create_workflow_template(bundle.graph)
    realized = realize_runtime_graph(
        template=template, run=bundle.run, realization_reason=GraphRealizationReason.RUN_CREATED
    )
    assert isinstance(realized, RealizedRuntimeGraph)
    assert not isinstance(realized, WorkflowTemplate)
    assert realized.realized_graph_id != template.template_id
    assert realized.template_id == template.template_id
    assert realized.run_id == bundle.run.run_id


def test_realization_does_not_mutate_template() -> None:
    bundle = _bundle()
    template = create_workflow_template(bundle.graph)
    template_dict_before = template.to_canonical_dict()
    realize_runtime_graph(
        template=template, run=bundle.run, realization_reason=GraphRealizationReason.RUN_CREATED
    )
    assert template.to_canonical_dict() == template_dict_before


def test_realization_does_not_execute() -> None:
    bundle = _bundle()
    template = create_workflow_template(bundle.graph)
    realized = realize_runtime_graph(
        template=template, run=bundle.run, realization_reason=GraphRealizationReason.RUN_CREATED
    )
    assert realized.execution_available is False
    assert realized.dispatch_available is False
    assert realized.trace_verified is False


def test_realization_rejects_mismatched_run() -> None:
    bundle = _bundle()
    template = create_workflow_template(bundle.graph)
    other_bundle = build_flow_demo_bundle()
    # other_bundle uses the same demo graph_id, so force a mismatch by
    # constructing a template pointed at a different graph id.
    fake_template = WorkflowTemplate(
        template_id="fltpl-fake",
        contract_version=template.contract_version,
        source_workflow_graph_id="not-the-real-graph",
        source_graph_hash="not-the-real-hash",
        name="fake",
        version="1",
        node_count=0,
        edge_count=0,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
        template_hash="fake-hash",
    )
    with pytest.raises(AurelFlowValidationError):
        realize_runtime_graph(
            template=fake_template,
            run=other_bundle.run,
            realization_reason=GraphRealizationReason.RUN_CREATED,
        )


def test_realized_graph_construction_is_deterministic() -> None:
    bundle = _bundle()
    template = create_workflow_template(bundle.graph)
    determination = GraphDeterminationTime(
        determination_kind=GraphDeterminationTimeKind.RUN_STEP, run_step=bundle.run.state.step
    )
    realized_a = realize_runtime_graph(
        template=template,
        run=bundle.run,
        realization_reason=GraphRealizationReason.RUN_CREATED,
        determination_time=determination,
    )
    realized_b = realize_runtime_graph(
        template=template,
        run=bundle.run,
        realization_reason=GraphRealizationReason.RUN_CREATED,
        determination_time=determination,
    )
    assert realized_a.realized_graph_id == realized_b.realized_graph_id
    assert realized_a.realized_graph_hash == realized_b.realized_graph_hash


def test_realized_graph_ref_matches_realized_graph() -> None:
    bundle = _bundle()
    template = create_workflow_template(bundle.graph)
    realized = realize_runtime_graph(
        template=template, run=bundle.run, realization_reason=GraphRealizationReason.RUN_CREATED
    )
    ref = realized_runtime_graph_ref(realized)
    assert isinstance(ref, RealizedRuntimeGraphRef)
    assert ref.realized_graph_id == realized.realized_graph_id
    assert ref.run_id == realized.run_id


def test_runtime_graph_instance_does_not_execute() -> None:
    bundle = _bundle()
    template = create_workflow_template(bundle.graph)
    realized = realize_runtime_graph(
        template=template, run=bundle.run, realization_reason=GraphRealizationReason.RUN_CREATED
    )
    instance = build_runtime_graph_instance(realized)
    assert isinstance(instance, RuntimeGraphInstance)
    assert instance.realized_graph_id == realized.realized_graph_id
    assert instance.execution_available is False


def test_realized_graph_boolean_fails_closed_on_true_construction() -> None:
    bundle = _bundle()
    template = create_workflow_template(bundle.graph)
    determination = GraphDeterminationTime(
        determination_kind=GraphDeterminationTimeKind.RUN_STEP, run_step=0
    )
    with pytest.raises(AurelFlowValidationError):
        RealizedRuntimeGraph(
            realized_graph_id="flrrg-fake",
            contract_version="realized_runtime_graph.v1",
            template_id=template.template_id,
            source_workflow_graph_id=template.source_workflow_graph_id,
            run_id=bundle.run.run_id,
            graph_version=1,
            determination_time=determination,
            realization_reason=GraphRealizationReason.RUN_CREATED,
            node_count=1,
            edge_count=0,
            truth_label=FlowTruthLabel.CONTRACT_ONLY,
            realized_graph_hash="fake",
            execution_available=True,
        )


def test_dynamic_graph_construction_does_not_mutate_demo_run() -> None:
    bundle = _bundle()
    step_before = bundle.run.state.step
    lifecycle_before = bundle.run.state.lifecycle_status
    history_before = len(bundle.run.history)

    template = create_workflow_template(bundle.graph)
    realized = realize_runtime_graph(
        template=template, run=bundle.run, realization_reason=GraphRealizationReason.RUN_CREATED
    )
    build_runtime_graph_instance(realized)

    assert bundle.run.state.step == step_before
    assert bundle.run.state.lifecycle_status is lifecycle_before
    assert len(bundle.run.history) == history_before
