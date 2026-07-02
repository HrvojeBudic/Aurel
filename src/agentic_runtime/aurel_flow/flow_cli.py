"""P3-FLOW-C read-only flow CLI backend (CLI_READ_ONLY).

Pure request/response handlers behind the `flow` CLI command family. Every
command reads projections built from the deterministic DEV_FIXTURE demo
substrate and renders deterministic text or canonical JSON. CLI inspect is
not dispatch: there are no execute / approve / resume / stop / retry /
recover / rollback commands, and the closed-world command-kind vocabulary
cannot express them. All side-effect booleans fail closed.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .demo import build_flow_demo_bundle, run_flow_foundation_demo
from .errors import AurelFlowErrorCode, AurelFlowValidationError
from .flow_projection import (
    build_flow_actual_code_inventory,
    build_flow_demo_scenario_read_model,
    build_flow_state_projection,
)
from .flow_protocol import build_flow_protocol_boundary
from .flow_seal import (
    build_flow_base_exit_seal_read_model,
    evaluate_flow_base_exit_seal,
)
from .flow_timeline import (
    build_runtime_behavior_timeline,
    build_runtime_event_relation_graph,
)
from .flow_wiring import build_flow_runtime_wiring_read_model
from .types import (
    FlowTruthLabel,
    _CanonicalMixin,
    stable_hash,
    to_canonical_json,
)

FLOW_CLI_CONTRACT_VERSION = "flow_cli.v1"


class FlowCliCommandKind(str, Enum):
    """Closed-world read-only flow CLI commands. No control verbs exist."""

    DEMO = "DEMO"
    INSPECT = "INSPECT"
    TIMELINE = "TIMELINE"
    WIRING = "WIRING"
    PROTOCOL = "PROTOCOL"
    SEAL = "SEAL"


FORBIDDEN_FLOW_CLI_COMMAND_KINDS: tuple[str, ...] = (
    "EXECUTE",
    "APPROVE",
    "RESUME",
    "STOP",
    "RETRY",
    "RECOVER",
    "ROLLBACK",
    "DISPATCH",
    "MUTATE",
    "SUBMIT",
)


class FlowCliOutputFormat(str, Enum):
    TEXT = "TEXT"
    JSON = "JSON"


@dataclass(frozen=True)
class FlowCliSideEffects(_CanonicalMixin):
    """CLI side-effect truth. Every boolean is permanently False."""

    mutates_runtime: bool = False
    executes_nodes: bool = False
    dispatches_work: bool = False
    approves_approvals: bool = False
    calls_tools: bool = False
    calls_llm: bool = False
    writes_trace: bool = False
    writes_ledger: bool = False
    writes_memory: bool = False
    mutates_policy: bool = False
    mutates_identity: bool = False

    def __post_init__(self) -> None:
        for effect_field in (
            "mutates_runtime",
            "executes_nodes",
            "dispatches_work",
            "approves_approvals",
            "calls_tools",
            "calls_llm",
            "writes_trace",
            "writes_ledger",
            "writes_memory",
            "mutates_policy",
            "mutates_identity",
        ):
            if getattr(self, effect_field):
                raise AurelFlowValidationError(
                    f"FlowCliSideEffects.{effect_field} must remain False",
                    code=AurelFlowErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                    field=effect_field,
                )


@dataclass(frozen=True)
class FlowCliRequest(_CanonicalMixin):
    """A read-only flow CLI request."""

    command_kind: FlowCliCommandKind
    output_format: FlowCliOutputFormat = FlowCliOutputFormat.TEXT
    contract_version: str = FLOW_CLI_CONTRACT_VERSION
    base_p3: bool = True


@dataclass(frozen=True)
class FlowCliResponse(_CanonicalMixin):
    """Deterministic response: rendered lines and/or canonical JSON."""

    request: FlowCliRequest
    exit_code: int
    rendered_lines: tuple[str, ...]
    json_payload: str
    side_effects: FlowCliSideEffects
    truth_label: FlowTruthLabel
    response_hash: str


def _lines_demo() -> tuple[tuple[str, ...], str]:
    foundation = run_flow_foundation_demo()
    bundle = build_flow_demo_bundle()
    scenario = build_flow_demo_scenario_read_model(bundle)
    lines = (
        "flow demo (DEV_FIXTURE — demo state is not execution)",
        f"graph: {foundation.graph.graph_id} "
        f"({foundation.graph.node_count} nodes, {foundation.graph.edge_count} edges)",
        f"run: {foundation.run_snapshot.run_id} @ step {foundation.run_snapshot.step} "
        f"lifecycle {foundation.run_snapshot.lifecycle_status.value}",
        f"ready: {', '.join(foundation.ready_node_ids) or '-'}",
        f"waiting approval: {', '.join(foundation.waiting_approval_node_ids) or '-'}",
        f"waiting dependency: {', '.join(foundation.waiting_dependency_node_ids) or '-'}",
        f"behavior demo run: {scenario.run_id}",
        f"completed (DEV_FIXTURE marks): {', '.join(scenario.completed_node_ids) or '-'}",
        f"failed (DEV_FIXTURE marks): {', '.join(scenario.failed_node_ids) or '-'}",
        f"rollback candidates (marked only): "
        f"{', '.join(scenario.rollback_candidate_node_ids) or '-'}",
        "truth: DEV_FIXTURE; live=False trace_verified=False execution_available=False",
    )
    return lines, to_canonical_json(scenario)


def _lines_inspect() -> tuple[tuple[str, ...], str]:
    bundle = build_flow_demo_bundle()
    projection = build_flow_state_projection(bundle.graph, bundle.run)
    inventory = build_flow_actual_code_inventory()
    node_lines = tuple(
        f"  {node_id}: {state}" for node_id, state in projection.node_states.items()
    )
    lines = (
        "flow inspect (READ_MODEL_ONLY — projection is not execution)",
        f"package: {inventory.package_name} "
        f"({inventory.module_count} modules, {inventory.test_count} flow tests)",
        f"graph: {projection.graph_id} run: {projection.run_id} step: {projection.step}",
        f"lifecycle: {projection.lifecycle_status}",
        "node states:",
        *node_lines,
        f"ready: {', '.join(projection.ready_node_ids) or '-'}",
        f"waiting approval: {', '.join(projection.waiting_approval_node_ids) or '-'}",
        f"waiting dependency: {', '.join(projection.waiting_dependency_node_ids) or '-'}",
        f"blocked: {', '.join(projection.blocked_node_ids) or '-'}",
        f"projection hash: {projection.projection_hash}",
        "truth: live=False trace_verified=False execution_available=False",
    )
    return lines, to_canonical_json(projection)


def _lines_timeline() -> tuple[tuple[str, ...], str]:
    bundle = build_flow_demo_bundle()
    timeline = build_runtime_behavior_timeline(bundle.event_stream)
    graph = build_runtime_event_relation_graph(bundle.event_stream)
    entry_lines = tuple(
        f"  [{entry.sequence}] {entry.event_kind} node={entry.node_id or '-'} "
        f"actor={entry.source_actor}"
        for entry in timeline.entries
    )
    lines = (
        "flow timeline (local behavior order — not AurelTrace, not hash-chain proof)",
        f"run: {timeline.run_id} stream: {timeline.stream_id}",
        f"entries: {timeline.entry_count}",
        *entry_lines,
        f"relation graph: {graph.node_count} nodes, {graph.edge_count} edges, "
        f"correlations: {', '.join(graph.correlation_ids) or '-'}",
        f"timeline hash: {timeline.timeline_hash}",
        "truth: trace_verified=False ledger_written=False",
    )
    payload = {
        "timeline": timeline.to_canonical_dict(),
        "relation_graph": graph.to_canonical_dict(),
    }
    return lines, to_canonical_json(payload)


def _lines_wiring() -> tuple[tuple[str, ...], str]:
    wiring = build_flow_runtime_wiring_read_model()
    entry_lines = tuple(
        f"  {entry.capability}: {entry.status.value} [{entry.temperature.value}]"
        for entry in wiring.matrix.entries
    )
    lines = (
        "flow wiring (hot/cold truth — a contract object is not active enforcement)",
        f"hot local: {wiring.matrix.hot_local_count} "
        f"cold: {wiring.matrix.cold_not_wired_count} "
        f"future: {wiring.matrix.future_count}",
        *entry_lines,
        "runtime_submit_wired=False trace_wired=False policy_wired=False "
        "persistence_wired=False rust_core_active=False",
    )
    return lines, to_canonical_json(wiring)


def _lines_protocol() -> tuple[tuple[str, ...], str]:
    boundary = build_flow_protocol_boundary()
    schema_lines = tuple(
        f"  {schema.schema_name}: {schema.contract_version}"
        for schema in boundary.schema_versions
    )
    lines = (
        "flow protocol (protocol-ready is not migration; Python is P3 truth)",
        f"serialization: {boundary.serialization_contract.serialization_format} "
        f"({boundary.serialization_contract.hash_algorithm})",
        "schemas:",
        *schema_lines,
        f"portable_to_rust_core={boundary.compatibility.portable_to_rust_core} "
        f"rust_core_active={boundary.compatibility.rust_core_active}",
        f"boundary hash: {boundary.boundary_hash}",
    )
    return lines, to_canonical_json(boundary)


def _lines_seal() -> tuple[tuple[str, ...], str]:
    result = evaluate_flow_base_exit_seal()
    read_model = build_flow_base_exit_seal_read_model(result)
    check_lines = tuple(
        f"  [{check.status.value}] {check.checkpoint_range} {check.title}"
        + (f" — {check.reason}" if check.reason else "")
        for check in result.seal.checks
    )
    lines = (
        "flow base-p3 seal (seal is local evidence, not TRACE_VERIFIED)",
        f"status: {result.seal.status.value}",
        f"checks: pass={result.pass_count} partial={result.partial_count} "
        f"blocked={result.blocked_count} fail={result.fail_count} "
        f"unavailable={result.unavailable_count}",
        *check_lines,
        "boundary: execution_available=False trace_verified=False "
        "ledger_written=False policy_enforced_by_flow=False "
        "runtime_submit_wired=False rust_core_active=False",
        f"seal id: {result.seal.seal_id}",
    )
    return lines, to_canonical_json(read_model)


_HANDLERS = {
    FlowCliCommandKind.DEMO: _lines_demo,
    FlowCliCommandKind.INSPECT: _lines_inspect,
    FlowCliCommandKind.TIMELINE: _lines_timeline,
    FlowCliCommandKind.WIRING: _lines_wiring,
    FlowCliCommandKind.PROTOCOL: _lines_protocol,
    FlowCliCommandKind.SEAL: _lines_seal,
}


def handle_flow_cli_request(request: FlowCliRequest) -> FlowCliResponse:
    """Handle a read-only flow CLI request. Pure: reads projections only."""

    handler = _HANDLERS.get(request.command_kind)
    if handler is None:
        raise AurelFlowValidationError(
            f"unsupported flow CLI command {request.command_kind!r}",
            code=AurelFlowErrorCode.UNSUPPORTED_CLI_COMMAND,
            field="command_kind",
        )
    lines, json_payload = handler()
    payload = {
        "contract_version": FLOW_CLI_CONTRACT_VERSION,
        "command_kind": request.command_kind.value,
        "output_format": request.output_format.value,
        "lines": lines,
    }
    return FlowCliResponse(
        request=request,
        exit_code=0,
        rendered_lines=lines,
        json_payload=json_payload,
        side_effects=FlowCliSideEffects(),
        truth_label=FlowTruthLabel.READ_MODEL_ONLY,
        response_hash=stable_hash(payload),
    )


def render_flow_cli_response(response: FlowCliResponse) -> str:
    """Render the response for stdout in its requested format."""

    if response.request.output_format is FlowCliOutputFormat.JSON:
        return response.json_payload
    return "\n".join(response.rendered_lines)
