"""P3-FLOW-J no-service-mesh boundary tests.

No service registry runtime, discovery runtime, transport adapter, message
bus, broker, load balancer, health probe runner, or telemetry exporter is
introduced — the topology layer stays a map.
"""

from __future__ import annotations

import re
from pathlib import Path

import agentic_runtime.aurel_flow as aurel_flow
from agentic_runtime.aurel_flow import (
    ABSENT_RUNTIME_SYSTEMS,
    InteropLayerKind,
    RuntimeServiceKind,
    assess_topology_health,
    build_compound_runtime_topology,
    create_interoperability_layer_ref,
    create_logical_service_ref,
    create_runtime_service_node,
)

_FLOW_PACKAGE_DIR = Path(aurel_flow.__file__).resolve().parent
_J_MODULES = (
    "flow_compound_topology.py",
    "flow_service_topology.py",
    "flow_interop_topology.py",
    "flow_compound_topology_projection.py",
)

_FORBIDDEN_MESH_PATTERNS = (
    r"class\s+\w*Registry\b",
    r"class\s+\w*Broker\b",
    r"class\s+\w*Bus\b",
    r"class\s+\w*Balancer\b",
    r"class\s+\w*Prober?\b",
    r"class\s+\w*Exporter\b",
    r"class\s+\w*Transport\b",
    r"class\s+\w*Client\b",
    r"class\s+\w*Server\b",
    r"def\s+discover",
    r"def\s+register_endpoint",
    r"def\s+register_service",
    r"def\s+route_message",
    r"def\s+probe",
    r"def\s+heartbeat",
    r"def\s+publish",
    r"def\s+subscribe",
    r"\bpub[_/]?sub\b",
    r"\bqueue\.Queue\b",
    r"class\s+\w*CircuitBreaker\b",
    r"class\s+\w*LoadBalancer\b",
    r"def\s+load_balance",
    r"\bistio\b|\blinkerd\b|\benvoy\b|\bconsul\b",
)


def test_j_sources_contain_no_service_mesh_machinery() -> None:
    for filename in _J_MODULES:
        source = (_FLOW_PACKAGE_DIR / filename).read_text(encoding="utf-8")
        for pattern in _FORBIDDEN_MESH_PATTERNS:
            assert not re.search(pattern, source, re.IGNORECASE), (
                f"{filename} matches forbidden pattern {pattern!r}"
            )


def test_discovery_layer_ref_performs_no_discovery() -> None:
    discovery = create_interoperability_layer_ref(
        InteropLayerKind.DISCOVERY_LAYER_REF
    )
    assert discovery.discovery_performed is False
    assert discovery.future_owner == "P4 AurelExec"


def test_topology_health_is_not_a_health_probe_runner() -> None:
    topology = build_compound_runtime_topology(
        run_id="run-1",
        service_nodes=(
            create_runtime_service_node(
                service_ref=create_logical_service_ref(
                    service_kind=RuntimeServiceKind.MODEL_SERVICE,
                    logical_name="frontier",
                )
            ),
        ),
    )
    health = assess_topology_health(topology=topology)
    assert health.service_health_checked is False
    assert health.telemetry_active is False
    assert health.diagnostic_only is True


def test_absent_system_list_names_the_whole_mesh_surface() -> None:
    for absent in (
        "service_runtime",
        "service_discovery",
        "endpoint_registry",
        "network_transport",
        "message_bus",
        "service_mesh",
        "protocol_client_server",
        "worker_pool",
        "load_balancer",
        "health_probe_runner",
        "telemetry_exporter",
        "persistence",
    ):
        assert absent in ABSENT_RUNTIME_SYSTEMS
