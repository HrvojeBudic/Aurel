"""
registry.py — MCP server registry + connection manager (B5).

Declares which external MCP servers Aurel may call (config/live/mcp_servers.yaml)
and manages their lifecycle. **Every server is disabled by default** — nothing
connects until the operator flips ``enabled: true``. Secrets never live in the
config: a stdio server names env vars via ``env_passthrough`` (the transport
scrubs everything else). Fail-closed on an unknown / disabled server or a bad spec.

The connection manager takes an injectable transport factory, so seals drive it
against an in-process fake with no subprocess and no network.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional

from ..secrets import assert_no_raw_secrets_in_yaml
from ..yaml_minimal import YamlParseError, load_yaml
from .client import McpClient
from .transport import HttpTransport, StdioTransport, Transport

_VALID_TRANSPORTS = ("stdio", "http")


class McpConfigError(RuntimeError):
    """Invalid MCP server configuration. Fail-closed."""


@dataclass(frozen=True)
class McpServerSpec:
    name: str
    transport: str
    enabled: bool = False
    command: Optional[str] = None
    args: tuple[str, ...] = ()
    env_passthrough: tuple[str, ...] = ()
    url: Optional[str] = None
    allowed_tools: tuple[str, ...] = ()

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "transport": self.transport,
            "enabled": self.enabled,
            "command": self.command,
            "args": list(self.args),
            "env_passthrough": list(self.env_passthrough),
            "url": self.url,
            "allowed_tools": list(self.allowed_tools),
        }


def parse_server_spec(data: Any) -> McpServerSpec:
    """Validate one server entry. Fail-closed on anything off-spec."""
    if not isinstance(data, dict):
        raise McpConfigError("a server entry must be a mapping")
    name = data.get("name")
    if not isinstance(name, str) or not name:
        raise McpConfigError("server 'name' is required")
    transport = data.get("transport")
    if transport not in _VALID_TRANSPORTS:
        raise McpConfigError(f"server {name!r}: transport must be one of {_VALID_TRANSPORTS}")
    if transport == "stdio" and not data.get("command"):
        raise McpConfigError(f"server {name!r}: stdio transport requires 'command'")
    if transport == "http" and not data.get("url"):
        raise McpConfigError(f"server {name!r}: http transport requires 'url'")
    return McpServerSpec(
        name=name,
        transport=transport,
        enabled=bool(data.get("enabled", False)),
        command=data.get("command"),
        args=tuple(str(a) for a in (data.get("args") or [])),
        env_passthrough=tuple(str(e) for e in (data.get("env_passthrough") or [])),
        url=data.get("url"),
        allowed_tools=tuple(str(t) for t in (data.get("allowed_tools") or [])),
    )


@dataclass
class McpServerRegistry:
    servers: dict[str, McpServerSpec] = field(default_factory=dict)

    @staticmethod
    def load(path: str) -> "McpServerRegistry":
        p = Path(path)
        if not p.is_file():
            raise McpConfigError(f"missing MCP server config: {p}")
        try:
            data = load_yaml(p.read_text(encoding="utf-8"))
        except YamlParseError as e:
            raise McpConfigError(f"invalid YAML in {p}: {e}") from e
        assert_no_raw_secrets_in_yaml(data)
        entries = data.get("servers", []) if isinstance(data, dict) else []
        reg = McpServerRegistry()
        for entry in entries:
            spec = parse_server_spec(entry)
            if spec.name in reg.servers:
                raise McpConfigError(f"duplicate server name {spec.name!r}")
            reg.servers[spec.name] = spec
        return reg

    def get(self, name: str) -> Optional[McpServerSpec]:
        return self.servers.get(name)

    def names(self) -> set[str]:
        return set(self.servers)

    def enabled(self) -> list[McpServerSpec]:
        return [s for s in self.servers.values() if s.enabled]


def default_transport_factory(spec: McpServerSpec) -> Transport:
    """Build a real transport from a spec (used outside seals)."""
    if spec.transport == "stdio":
        assert spec.command is not None
        return StdioTransport(
            [spec.command, *spec.args], env_passthrough=list(spec.env_passthrough)
        )
    assert spec.url is not None
    return HttpTransport(spec.url)


class McpConnectionManager:
    """Connects to enabled MCP servers and manages their lifecycle."""

    def __init__(
        self,
        registry: McpServerRegistry,
        *,
        transport_factory: Callable[[McpServerSpec], Transport] = default_transport_factory,
        redactor: Any = None,
    ) -> None:
        self._registry = registry
        self._factory = transport_factory
        self._redactor = redactor
        self._clients: dict[str, McpClient] = {}

    def connect(self, name: str) -> McpClient:
        spec = self._registry.get(name)
        if spec is None:
            raise McpConfigError(f"unknown MCP server {name!r}")
        if not spec.enabled:
            raise McpConfigError(f"MCP server {name!r} is disabled")
        if name in self._clients:
            return self._clients[name]
        transport = self._factory(spec)
        client = McpClient(transport, spec.name, redactor=self._redactor)
        client.initialize()
        self._clients[name] = client
        return client

    def disconnect(self, name: str) -> None:
        client = self._clients.pop(name, None)
        if client is not None:
            client.close()

    def active(self) -> dict[str, McpClient]:
        return dict(self._clients)

    def health(self) -> dict[str, bool]:
        return {n: (n in self._clients) for n in self._registry.names()}
