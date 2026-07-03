"""P3-FLOW-J no-invocation boundary tests.

Naming a model/tool/memory/verifier/sandbox/environment/data service never
invokes it: invocation booleans are unconstructible True across the whole
bridge output, and the J modules import no invocation-capable subsystem.
"""

from __future__ import annotations

import dataclasses
import re
from pathlib import Path

import pytest

import agentic_runtime.aurel_flow as aurel_flow
from agentic_runtime.aurel_flow import (
    AurelFlowValidationError,
    ServiceCapabilityKind,
    RuntimeServiceKind,
    WorkflowAtomicUnitKind,
    bridge_scheduling_requirements,
    build_execution_resource_requirement_read_model,
    create_data_access_requirement_frame,
    create_logical_service_ref,
    create_model_requirement_frame,
    create_sandbox_requirement_frame,
    create_service_capability_envelope,
    create_tool_requirement_frame,
    create_workflow_atomic_unit,
)

_FLOW_PACKAGE_DIR = Path(aurel_flow.__file__).resolve().parent
_J_MODULES = (
    "flow_compound_topology.py",
    "flow_service_topology.py",
    "flow_interop_topology.py",
    "flow_compound_topology_projection.py",
)

_FORBIDDEN_INVOCATION_PATTERNS = (
    r"from\s+agentic_runtime\.tools\b",
    r"from\s+agentic_runtime\.sandbox\b",
    r"from\s+agentic_runtime\.memory\b",
    r"from\s+agentic_runtime\.trace\b",
    r"from\s+agentic_runtime\.policy\b",
    r"from\s+agentic_runtime\.runtime\b",
    r"from\s+\.\.runtime\b",
    r"def\s+invoke_",
    r"\.invoke\(",
    r"def\s+call_model",
    r"def\s+call_tool",
    r"def\s+run_sandbox",
    r"def\s+read_memory",
    r"def\s+write_memory",
    r"def\s+access_data",
)


def test_j_sources_import_no_invocation_capable_subsystem() -> None:
    for filename in _J_MODULES:
        source = (_FLOW_PACKAGE_DIR / filename).read_text(encoding="utf-8")
        for pattern in _FORBIDDEN_INVOCATION_PATTERNS:
            assert not re.search(pattern, source), (
                f"{filename} matches forbidden pattern {pattern!r}"
            )


def _full_bridge():
    unit = create_workflow_atomic_unit(
        run_id="run-1",
        unit_kind=WorkflowAtomicUnitKind.SINGLE_NODE,
        node_ids=("n1",),
    )
    requirements = build_execution_resource_requirement_read_model(
        unit=unit,
        model_requirement=create_model_requirement_frame(
            unit=unit, model_required=True
        ),
        tool_requirement=create_tool_requirement_frame(
            unit=unit, tool_required=True, tool_names=("git",)
        ),
        sandbox_requirement=create_sandbox_requirement_frame(
            unit=unit, sandbox_required=True
        ),
        data_access_requirement=create_data_access_requirement_frame(
            unit=unit, data_access_required=True, memory_required=True
        ),
    )
    return bridge_scheduling_requirements(requirements=requirements)


def test_matching_a_requirement_invokes_nothing() -> None:
    bridge = _full_bridge()
    assert bridge.service_invoked is False
    for ref in bridge.matched_service_refs:
        assert ref.service_invoked is False
        assert ref.invocation_available is False
        with pytest.raises(AurelFlowValidationError):
            dataclasses.replace(ref, service_invoked=True)
    for candidate in bridge.routing_candidates:
        assert candidate.service_invoked is False
        with pytest.raises(AurelFlowValidationError):
            dataclasses.replace(candidate, service_invoked=True)


def test_capability_declaration_invokes_nothing() -> None:
    envelope = create_service_capability_envelope(
        service_ref=create_logical_service_ref(
            service_kind=RuntimeServiceKind.MEMORY_SERVICE,
            logical_name="praxis",
        ),
        capability_kinds=(
            ServiceCapabilityKind.CAN_RETRIEVE_MEMORY_CANDIDATE,
        ),
    )
    assert envelope.service_invoked is False
    assert envelope.permission_granted is False
    with pytest.raises(AurelFlowValidationError):
        dataclasses.replace(envelope, service_invoked=True)


def test_every_matched_ref_stays_future_bound_not_invocable() -> None:
    bridge = _full_bridge()
    for ref in bridge.matched_service_refs:
        assert ref.future_p4_required is True
        assert ref.future_p9_required is True
