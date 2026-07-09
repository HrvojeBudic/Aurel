"""
tool_registry.py — the gateway's allowlist of externally-exposed tools (F3.3).

Aurel-as-MCP-server exposes **only** tools that are explicitly exposed here AND
carry a real ``ToolContract``. No contract / not exposed ⇒ not listed ⇒ never
executed (the P1.3 manifest seal is untouched — the gateway adds a second,
tighter gate on top of it, never a bypass).

Each exposed tool gets an **external risk floor** that is *escalation-only*: it is
raised to at least the platform external minimum (MEDIUM — external origin is
never trusted) and at least the tool's intrinsic contract risk floor. A caller-
or annotation-supplied floor can only push it higher, never lower. This is how an
untrusted external client is kept away from a tool that is intrinsically cheap
(e.g. a read) but still external.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from ..core_types import RiskLevel
from ..tool_contracts import ToolContract

# External origin is never trusted below MEDIUM, whatever the tool intrinsically is.
DEFAULT_EXTERNAL_FLOOR = RiskLevel.MEDIUM

_RISK_ORDER: dict[RiskLevel, int] = {
    RiskLevel.TRIVIAL: 0,
    RiskLevel.LOW: 1,
    RiskLevel.MEDIUM: 2,
    RiskLevel.HIGH: 3,
    RiskLevel.CRITICAL: 4,
}

# ArgSpec type token → JSON Schema type.
_JSON_TYPE: dict[str, str] = {
    "str": "string",
    "int": "integer",
    "float": "number",
    "number": "number",
    "bool": "boolean",
    "list": "array",
    "list[str]": "array",
    "dict": "object",
}


def _max_risk(*risks: RiskLevel) -> RiskLevel:
    return max(risks, key=lambda r: _RISK_ORDER[r])


def _input_schema_for(contract: ToolContract) -> dict:
    """Derive a JSON-Schema object from a contract's typed input spec."""
    properties: dict[str, dict] = {}
    required: list[str] = []
    for name, spec in sorted(contract.input_schema.items()):
        prop: dict = {"type": _JSON_TYPE.get(spec.type, "string")}
        if spec.enum is not None:
            prop["enum"] = list(spec.enum)
        properties[name] = prop
        if spec.required:
            required.append(name)
    return {"type": "object", "properties": properties, "required": required}


@dataclass(frozen=True)
class ExposedTool:
    """One tool the gateway offers to external MCP clients."""

    name: str
    description: str
    external_risk_floor: RiskLevel
    input_schema: dict = field(default_factory=dict)

    def to_mcp_tool(self) -> dict:
        """The MCP ``tools/list`` descriptor for this tool."""
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.input_schema,
            "x_external_risk_floor": self.external_risk_floor.value,
        }


class GatewayToolRegistry:
    """The exposed-tool allowlist. Empty by default — nothing is exposed until
    explicitly ``expose``-d."""

    def __init__(self) -> None:
        self._exposed: dict[str, ExposedTool] = {}

    def expose(
        self, contract: ToolContract, external_risk_floor: Optional[RiskLevel] = None
    ) -> ExposedTool:
        """Expose a contracted tool. The floor can only be escalated, never lowered."""
        floor = _max_risk(
            DEFAULT_EXTERNAL_FLOOR,
            contract.risk_floor(),
            external_risk_floor or DEFAULT_EXTERNAL_FLOOR,
        )
        tool = ExposedTool(
            name=contract.name,
            description=contract.description,
            external_risk_floor=floor,
            input_schema=_input_schema_for(contract),
        )
        self._exposed[contract.name] = tool
        return tool

    def get(self, name: str) -> Optional[ExposedTool]:
        return self._exposed.get(name)

    def is_exposed(self, name: str) -> bool:
        return name in self._exposed

    def names(self) -> set[str]:
        return set(self._exposed)

    def list_tools(self) -> list[dict]:
        """Deterministic MCP ``tools/list`` payload (sorted by name)."""
        return [self._exposed[n].to_mcp_tool() for n in sorted(self._exposed)]
