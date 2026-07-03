"""P3-FLOW-J no-network / no-execution boundary tests.

No J module can open a network, bind a transport, send a message, or
execute anything — structurally and by source scan.
"""

from __future__ import annotations

import re
from pathlib import Path

import agentic_runtime.aurel_flow as aurel_flow
from agentic_runtime.aurel_flow import (
    InteropLayerKind,
    RuntimeServiceKind,
    ServiceDependencyKind,
    ServiceRoutingReason,
    create_interoperability_layer_ref,
    create_logical_service_ref,
    create_service_dependency_edge,
    create_service_routing_candidate,
)

_FLOW_PACKAGE_DIR = Path(aurel_flow.__file__).resolve().parent
_J_MODULES = (
    "flow_compound_topology.py",
    "flow_service_topology.py",
    "flow_interop_topology.py",
    "flow_compound_topology_projection.py",
)

_FORBIDDEN_NETWORK_PATTERNS = (
    r"\bimport\s+socket\b",
    r"\bimport\s+requests\b",
    r"\bimport\s+urllib\b",
    r"\bimport\s+httpx\b",
    r"\bimport\s+aiohttp\b",
    r"\bimport\s+grpc\b",
    r"\bimport\s+nats\b",
    r"\bimport\s+websockets?\b",
    r"\bimport\s+http\b",
    r"\bfrom\s+http\b",
    r"\bimport\s+ssl\b",
    r"\bhttp://",
    r"https://(?!.*reports)",  # no live URLs; report paths are repo-relative
    r"\bbind\(",
    r"\bconnect\(",
    r"\blisten\(",
    r"\bsend\(",
    r"\brecv\(",
)


def test_j_sources_contain_no_network_machinery() -> None:
    for filename in _J_MODULES:
        source = (_FLOW_PACKAGE_DIR / filename).read_text(encoding="utf-8")
        for pattern in _FORBIDDEN_NETWORK_PATTERNS:
            assert not re.search(pattern, source), (
                f"{filename} matches forbidden pattern {pattern!r}"
            )


def test_no_object_in_the_j_vertical_slice_touches_the_network() -> None:
    tool = create_logical_service_ref(
        service_kind=RuntimeServiceKind.TOOL_SERVICE, logical_name="git"
    )
    model = create_logical_service_ref(
        service_kind=RuntimeServiceKind.MODEL_SERVICE, logical_name="frontier"
    )
    edge = create_service_dependency_edge(
        from_service_ref=tool,
        to_service_ref=model,
        dependency_kind=ServiceDependencyKind.REQUIRES_MODEL,
    )
    candidate = create_service_routing_candidate(
        run_id="run-1",
        atomic_unit_id="flwau-1",
        service_ref=tool,
        routing_reason=ServiceRoutingReason.TOOL_REQUIREMENT_MATCH,
    )
    routing_layer = create_interoperability_layer_ref(
        InteropLayerKind.ROUTING_LAYER_REF
    )
    assert tool.network_called is False
    assert edge.message_sent is False
    assert edge.transport_route is False
    assert candidate.network_called is False
    assert candidate.message_sent is False
    assert routing_layer.routing_performed is False
    assert routing_layer.transport_bound is False
    assert routing_layer.network_called is False


def test_execution_stays_unavailable_across_j_objects() -> None:
    ref = create_logical_service_ref(
        service_kind=RuntimeServiceKind.SANDBOX_SERVICE,
        logical_name="restricted",
    )
    candidate = create_service_routing_candidate(
        run_id="run-1",
        atomic_unit_id="flwau-1",
        service_ref=ref,
        routing_reason=ServiceRoutingReason.SANDBOX_REQUIREMENT_MATCH,
    )
    execution_layer = create_interoperability_layer_ref(
        InteropLayerKind.EXECUTION_LAYER_REF
    )
    assert candidate.execution_available is False
    assert candidate.dispatch_available is False
    assert execution_layer.execution_performed is False
