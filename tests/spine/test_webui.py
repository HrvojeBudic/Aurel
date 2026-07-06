"""SPINE-LIVE UI tests — the local web console serves and runs the slice."""

from __future__ import annotations

import json
import threading
import urllib.request
from http.server import ThreadingHTTPServer

from agentic_runtime.spine import webui


def _start_server(tmp_path):
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), webui._Handler)
    httpd.trace_dir = str(tmp_path)  # type: ignore[attr-defined]
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    return httpd, httpd.server_address[1]


def test_index_page_served(tmp_path):
    httpd, port = _start_server(tmp_path)
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/") as r:
            body = r.read().decode()
        assert r.status == 200
        assert "SPINE-LIVE console" in body
        assert "/api/run" in body
    finally:
        httpd.shutdown()


def test_api_run_offline_mock(tmp_path):
    httpd, port = _start_server(tmp_path)
    try:
        req = urllib.request.Request(
            f"http://127.0.0.1:{port}/api/run",
            data=json.dumps({"goal": "fix calc", "live": False, "plan_driven": False}).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req) as r:
            payload = json.loads(r.read().decode())
        # offline (mock model, no hard sandbox in CI) → honest, well-formed result
        assert payload["scenario"] == "spine_buggy_calculator"
        assert "spine_live" in payload
        assert "model_evidence" in payload
        assert isinstance(payload["spine_live"], bool)
    finally:
        httpd.shutdown()


def test_unknown_path_404(tmp_path):
    httpd, port = _start_server(tmp_path)
    try:
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{port}/nope")
            assert False, "expected 404"
        except urllib.error.HTTPError as e:
            assert e.code == 404
    finally:
        httpd.shutdown()
