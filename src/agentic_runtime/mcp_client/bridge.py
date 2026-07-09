"""
bridge.py — bridge external MCP tools into Aurel governance (B4).

A discovered MCP tool becomes a first-class Aurel tool only by being *explicitly*
bridged (allowlist, empty by default). Bridging registers two things that make it
governable exactly like a native tool:

  - a ``ToolContract`` (contract registry) derived from the server's JSON-Schema
    ``inputSchema``, with an **unconditional HIGH external floor** (external API +
    network side effects) — a malicious server annotation cannot lower it;
  - a ``ToolSpec`` (tool runtime) under a namespaced name ``mcp__<server>__<tool>``
    whose handler calls ``client.call_tool`` and returns **leak-safe evidence**
    (``ToolCallResult.to_dict`` — hashes/provenance, never raw external text);
    the raw content flows to context only through the ContextLoom sink (B6).

Because both registrations are required, an un-bridged tool simply does not exist
for ``runtime.submit`` — no bypass of the P1.3 manifest seal. The descriptor hash
is pinned at bridge time so a later rug-pull can be detected (``verify_pin``).
"""
from __future__ import annotations

from typing import Any, Callable, Optional

from ..core_types import ObservationEnvelope
from ..tool_contracts import (
    ArgSpec,
    OutputContract,
    SideEffect,
    ToolContract,
    ToolContractRegistry,
)
from ..tools import (
    ToolRiskLevel,
    ToolSandboxRequirement,
    ToolSpec,
    ToolVerifierRequirement,
)
from .client import McpCallError, McpToolDescriptor

# MCP tools are external API calls over the network ⇒ HIGH risk floor, always.
_MCP_SIDE_EFFECTS = frozenset({SideEffect.EXTERNAL_API_CALL, SideEffect.NETWORK_REQUEST})

# JSON-Schema type → Aurel ArgSpec / ToolSpec token.
_JSON_TO_TOKEN: dict[str, str] = {
    "string": "str",
    "integer": "int",
    "number": "number",
    "boolean": "bool",
    "array": "list",
    "object": "dict",
}


def bridged_name(server_name: str, tool_name: str) -> str:
    return f"mcp__{server_name}__{tool_name}"


def _schema_parts(schema: Any) -> tuple[dict, set[str]]:
    props = schema.get("properties", {}) if isinstance(schema, dict) else {}
    required = schema.get("required", []) if isinstance(schema, dict) else []
    props = props if isinstance(props, dict) else {}
    req = set(required) if isinstance(required, list) else set()
    return props, req


def json_schema_to_argspecs(schema: Any) -> dict[str, ArgSpec]:
    props, required = _schema_parts(schema)
    out: dict[str, ArgSpec] = {}
    for name, spec in props.items():
        token = _JSON_TO_TOKEN.get((spec or {}).get("type"), "str")
        out[str(name)] = ArgSpec(type=token, required=name in required)
    return out


def json_schema_to_spec_tokens(schema: Any) -> dict[str, str]:
    props, required = _schema_parts(schema)
    out: dict[str, str] = {}
    for name, spec in props.items():
        token = _JSON_TO_TOKEN.get((spec or {}).get("type"), "str")
        out[str(name)] = token if name in required else token + "?"
    return out


def json_schema_to_contract(name: str, description: str, schema: Any) -> ToolContract:
    """Contract with an unconditional HIGH external floor (escalation-only)."""
    return ToolContract(
        name=name,
        description=description[:200],
        input_schema=json_schema_to_argspecs(schema),
        side_effect_profile=_MCP_SIDE_EFFECTS,
        output_schema=OutputContract(),
    )


class McpBridge:
    """Bridges MCP tools from one client into a contract registry + tool runtime."""

    def __init__(
        self,
        client: Any,
        runtime: Any,
        *,
        sink: Optional[Callable[[Any, str], None]] = None,
    ) -> None:
        self._client = client
        inner = getattr(runtime, "runtime", runtime)
        self._contracts: ToolContractRegistry = inner.contracts
        self._tools = inner.tools
        self._policy = inner.policy
        self._sink = sink
        self._bridged: dict[str, str] = {}    # bridged_name -> original tool name
        self._pins: dict[str, str] = {}       # bridged_name -> descriptor_hash

    def bridge_tool(self, descriptor: McpToolDescriptor) -> str:
        bname = bridged_name(self._client.server_name, descriptor.name)
        contract = json_schema_to_contract(
            bname, descriptor.description.content, descriptor.input_schema
        )
        self._contracts.register(contract)
        self._tools.register(ToolSpec(
            name=bname,
            description=descriptor.description.content[:200],
            input_schema=json_schema_to_spec_tokens(descriptor.input_schema),
            handler=self._make_handler(descriptor.name),
            risk_level=ToolRiskLevel.HIGH,
            required_capabilities=["network"],
            sandbox_requirement=ToolSandboxRequirement.WORKSPACE,
            verifier_requirement=ToolVerifierRequirement.NONE,
        ))
        # The policy engine holds its own registered-tools set (snapshot at build);
        # keep it in sync so the capability gate recognizes the bridged tool.
        try:
            self._policy.registered_tools.add(bname)
        except AttributeError:  # pragma: no cover - policy without a mutable set
            pass
        self._bridged[bname] = descriptor.name
        self._pins[bname] = descriptor.descriptor_hash
        return bname

    def _make_handler(
        self, original: str
    ) -> Callable[[Any, dict], ObservationEnvelope]:
        def handler(_sandbox: Any, args: dict) -> ObservationEnvelope:
            try:
                result = self._client.call_tool(original, args)
            except McpCallError as e:
                return ObservationEnvelope.make(
                    "", success=False, stderr=str(e)[:200],
                    artifacts={"mcp_error": True},
                )
            if self._sink is not None:
                self._sink(result, self._client.server_name)
            # Leak-safe: to_dict carries hashes/provenance, never raw external text.
            return ObservationEnvelope.make(
                "", success=not result.is_error, artifacts=result.to_dict(),
            )
        return handler

    def bridged_tools(self) -> dict[str, str]:
        return dict(self._bridged)

    def verify_pin(self, descriptor: McpToolDescriptor) -> bool:
        """True iff a re-discovered descriptor still matches the pinned hash (T7)."""
        bname = bridged_name(self._client.server_name, descriptor.name)
        pinned = self._pins.get(bname)
        return pinned is not None and pinned == descriptor.descriptor_hash
