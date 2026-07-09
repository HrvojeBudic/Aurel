"""F4B / B0 seal — client-side JSON-RPC 2.0 codec.

  1. Requests are correlatable (monotonic ids, correct shape, params optional).
  2. Notifications carry no id.
  3. correlate returns exactly one of result / error; fail-closed on off-spec.
  4. expect enforces id correlation.
  5. Flag default OFF.
"""
from __future__ import annotations

import pytest

from agentic_runtime.mcp_client import (
    JsonRpcClientCodec,
    JsonRpcClientError,
    flag_enabled,
)


def _ok(rid, result):
    return {"jsonrpc": "2.0", "id": rid, "result": result}


def _err(rid, code=-32601, msg="nope"):
    return {"jsonrpc": "2.0", "id": rid, "error": {"code": code, "message": msg}}


# --------------------------------------------------------------------------- #
# 1. Requests.
# --------------------------------------------------------------------------- #
def test_build_request_shape_and_monotonic_ids():
    c = JsonRpcClientCodec()
    id1, m1 = c.build_request("initialize", {"x": 1})
    id2, m2 = c.build_request("tools/list")
    assert (id1, id2) == (1, 2)
    assert m1 == {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"x": 1}}
    assert "params" not in m2                      # omitted when None
    assert m2["method"] == "tools/list"


def test_build_request_rejects_bad_method():
    c = JsonRpcClientCodec()
    with pytest.raises(JsonRpcClientError):
        c.build_request("")


# --------------------------------------------------------------------------- #
# 2. Notifications.
# --------------------------------------------------------------------------- #
def test_notification_has_no_id():
    c = JsonRpcClientCodec()
    n = c.build_notification("notifications/initialized")
    assert "id" not in n
    assert n == {"jsonrpc": "2.0", "method": "notifications/initialized"}


# --------------------------------------------------------------------------- #
# 3. Correlate.
# --------------------------------------------------------------------------- #
def test_correlate_success():
    r = JsonRpcClientCodec().correlate(_ok(1, {"tools": []}))
    assert r.is_error is False
    assert r.result == {"tools": []}
    assert r.id == 1


def test_correlate_error():
    r = JsonRpcClientCodec().correlate(_err(2, -32601, "method not found"))
    assert r.is_error is True
    assert r.error is not None
    assert r.error.code == -32601 and r.error.message == "method not found"


@pytest.mark.parametrize("bad", [
    "not a dict",
    {"id": 1, "result": {}},                       # missing jsonrpc
    {"jsonrpc": "1.0", "id": 1, "result": {}},     # wrong version
    {"jsonrpc": "2.0", "id": 1},                   # neither result nor error
    {"jsonrpc": "2.0", "id": 1, "result": {}, "error": {"code": 1, "message": "x"}},
    {"jsonrpc": "2.0", "id": 1, "error": {"code": 1}},  # malformed error object
])
def test_correlate_fail_closed(bad):
    with pytest.raises(JsonRpcClientError):
        JsonRpcClientCodec().correlate(bad)


# --------------------------------------------------------------------------- #
# 4. expect.
# --------------------------------------------------------------------------- #
def test_expect_matches_id():
    c = JsonRpcClientCodec()
    rid, _ = c.build_request("ping")
    assert c.expect(_ok(rid, {}), rid).id == rid


def test_expect_mismatch_raises():
    c = JsonRpcClientCodec()
    rid, _ = c.build_request("ping")
    with pytest.raises(JsonRpcClientError):
        c.expect(_ok(rid + 99, {}), rid)


# --------------------------------------------------------------------------- #
# 5. Flag.
# --------------------------------------------------------------------------- #
def test_flag_defaults_off(monkeypatch):
    monkeypatch.delenv("AUREL_MCP_CLIENT", raising=False)
    assert flag_enabled() is False
    monkeypatch.setenv("AUREL_MCP_CLIENT", "1")
    assert flag_enabled() is True
