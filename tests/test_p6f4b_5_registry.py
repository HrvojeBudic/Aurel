"""F4B / B5 seal — MCP server registry + connection manager.

  1. Real config (config/live/mcp_servers.yaml) parses; all servers disabled.
  2. Spec validation is fail-closed (transport, stdio-command, http-url).
  3. Connection manager (fake transport factory): connect an enabled server →
     initialized client; disabled / unknown fail closed; disconnect; health.
"""
from __future__ import annotations

import pytest

from agentic_runtime.mcp_client import (
    McpConfigError,
    McpConnectionManager,
    McpServerRegistry,
    McpServerSpec,
    parse_server_spec,
)


# --------------------------------------------------------------------------- #
# 1. Real config.
# --------------------------------------------------------------------------- #
def test_real_config_parses_all_disabled():
    reg = McpServerRegistry.load("config/live/mcp_servers.yaml")
    assert {"filesystem", "example-http"} <= reg.names()
    assert reg.enabled() == []                      # nothing on by default


def test_load_from_tmp(tmp_path):
    (tmp_path / "s.yaml").write_text(
        "servers:\n"
        "  - name: fs\n    transport: stdio\n    command: echo\n    enabled: true\n"
        "  - name: web\n    transport: http\n    url: http://127.0.0.1:1/\n",
        encoding="utf-8",
    )
    reg = McpServerRegistry.load(str(tmp_path / "s.yaml"))
    assert reg.get("fs").enabled is True
    assert reg.get("web").enabled is False
    assert [s.name for s in reg.enabled()] == ["fs"]


# --------------------------------------------------------------------------- #
# 2. Spec validation.
# --------------------------------------------------------------------------- #
def test_spec_validation_fail_closed():
    with pytest.raises(McpConfigError):
        parse_server_spec({"transport": "stdio", "command": "x"})   # no name
    with pytest.raises(McpConfigError):
        parse_server_spec({"name": "a", "transport": "carrier-pigeon"})
    with pytest.raises(McpConfigError):
        parse_server_spec({"name": "a", "transport": "stdio"})       # no command
    with pytest.raises(McpConfigError):
        parse_server_spec({"name": "a", "transport": "http"})        # no url


def test_missing_config_fails_closed(tmp_path):
    with pytest.raises(McpConfigError):
        McpServerRegistry.load(str(tmp_path / "nope.yaml"))


# --------------------------------------------------------------------------- #
# 3. Connection manager (fake transport).
# --------------------------------------------------------------------------- #
class FakeTransport:
    def __init__(self):
        self._out = []

    def send(self, message):
        if "id" not in message:
            return
        self._out.append({"jsonrpc": "2.0", "id": message["id"], "result": {
            "protocolVersion": "2025-06-18", "capabilities": {"tools": {}},
            "serverInfo": {"name": "fake"}}})

    def receive(self, timeout_s=None):
        return self._out.pop(0)

    def close(self):
        pass


def _registry():
    reg = McpServerRegistry()
    reg.servers["on"] = McpServerSpec("on", "stdio", enabled=True, command="x")
    reg.servers["off"] = McpServerSpec("off", "stdio", enabled=False, command="x")
    return reg


def test_manager_connect_disabled_unknown():
    mgr = McpConnectionManager(_registry(), transport_factory=lambda spec: FakeTransport())
    client = mgr.connect("on")
    assert client.initialized is True
    assert "tools" in client.capabilities
    assert mgr.health() == {"on": True, "off": False}

    with pytest.raises(McpConfigError):
        mgr.connect("off")                          # disabled
    with pytest.raises(McpConfigError):
        mgr.connect("ghost")                        # unknown


def test_manager_connect_idempotent_and_disconnect():
    mgr = McpConnectionManager(_registry(), transport_factory=lambda spec: FakeTransport())
    c1 = mgr.connect("on")
    c2 = mgr.connect("on")
    assert c1 is c2                                 # reused, not reconnected
    mgr.disconnect("on")
    assert mgr.health()["on"] is False
