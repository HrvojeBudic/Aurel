"""F5.0a seal — the "one door" HTTP server foundation.

  1. Structural one-door invariant: EXACTLY one route is a mutation (POST /proposals).
  2. Flag-off ⇒ the server is not constructed (byte-identical runtime).
  3. Flag-on ⇒ a real HTTP server: /health, /read/{model}, POST /proposals route
     to the dispatcher, unknown → 404, a malformed proposal → 400.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request

import pytest

from agentic_runtime.front_server import (
    ROUTES,
    FrontServerDisabled,
    create_front_server,
    match_route,
    mutation_routes,
)


def test_exactly_one_mutation_route():
    muts = mutation_routes()
    assert len(muts) == 1
    assert (muts[0].method, muts[0].path) == ("POST", "/proposals")
    assert all(not r.mutation for r in ROUTES if r is not muts[0])


def test_route_matching():
    assert match_route("POST", "/proposals").mutation is True
    assert match_route("GET", "/read/surfaces").handler == "handle_read"
    assert match_route("GET", "/read/hq/command?x=1").handler == "handle_read"
    assert match_route("GET", "/nope") is None
    assert match_route("POST", "/read/x") is None


def test_flag_off_server_not_constructed(monkeypatch):
    monkeypatch.delenv("AUREL_FRONT_SERVER", raising=False)
    with pytest.raises(FrontServerDisabled):
        create_front_server(object())


def _get(url):
    try:
        with urllib.request.urlopen(url, timeout=5) as r:  # nosec B310 - localhost test
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, None


def _post(url, payload):
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, method="POST",
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=5) as r:  # nosec B310 - localhost test
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


@pytest.fixture
def server(monkeypatch):
    monkeypatch.setenv("AUREL_FRONT_SERVER", "1")
    srv = create_front_server(object(), port=0)
    srv.serve_forever_background()
    try:
        yield f"http://{srv.host}:{srv.port}"
    finally:
        srv.shutdown()


def test_health(server):
    status, body = _get(server + "/health")
    assert status == 200 and body["status"] == "ok"


def test_read_placeholder(server):
    status, body = _get(server + "/read/surfaces")
    assert status == 200
    assert body["model"] == "surfaces" and body["live"] is False


def test_proposals_routes_to_dispatcher(server):
    status, body = _post(server + "/proposals", {"kind": "act"})
    assert status == 200
    assert body["accepted"] is True and body["kind"] == "act"


def test_malformed_proposal_400(server):
    status, body = _post(server + "/proposals", {"kind": "nonsense"})
    assert status == 400
    assert "error" in body


def test_unknown_route_404(server):
    status, _ = _get(server + "/does-not-exist")
    assert status == 404
