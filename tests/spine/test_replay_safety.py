"""AUREL-REPAIR-01 — replay/live paths must not silently use the unsafe sandbox.

These tests pin the truth contract for the Spine replay paths (harness helpers,
CLI, and Web UI): when no hard-isolated sandbox is functionally available, replay
fails closed with an honest UNAVAILABLE report — never a silent downgrade to
``UnsafeLocalSandbox`` dressed up as a live/verified/deterministic result.
"""

from __future__ import annotations

import json
import threading
import urllib.request
from http.server import ThreadingHTTPServer

import agentic_runtime.spine.harness as harness
from agentic_runtime.spine import webui


# --------------------------------------------------------------------------- #
#  resolve_replay_sandbox — the single honest chokepoint
# --------------------------------------------------------------------------- #
def test_resolve_no_hard_sandbox_is_fail_closed(monkeypatch):
    monkeypatch.setattr(harness, "_auto_hard_sandbox", lambda: None)
    factory, posture = harness.resolve_replay_sandbox(allow_unsafe=False)
    # No factory => the caller must fail closed. No unsafe sandbox is produced.
    assert factory is None
    assert posture["truth_label"] == "UNAVAILABLE"
    assert posture["hard_isolated"] is False
    assert posture["security_boundary"] is False
    assert posture["reason"]  # an operator-facing reason is present


def test_resolve_allow_unsafe_is_explicit_and_labelled(monkeypatch):
    monkeypatch.setattr(harness, "_auto_hard_sandbox", lambda: None)
    factory, posture = harness.resolve_replay_sandbox(allow_unsafe=True)
    # Dev-only opt-in: a backend IS produced, but it is clearly labelled UNSAFE
    # and never claims to be a security boundary.
    assert factory is not None
    sbx = factory()
    assert getattr(sbx, "is_security_boundary", True) is False
    assert posture["truth_label"] == "UNSAFE"
    assert posture["security_boundary"] is False
    assert "not a security boundary" in posture["reason"].lower()


def test_resolve_hard_sandbox_available_is_live(monkeypatch):
    class _Fake:
        mode = type("M", (), {"value": "bubblewrap"})()
        is_hard_isolated = True
        is_security_boundary = True

    monkeypatch.setattr(harness, "_auto_hard_sandbox", lambda: _Fake())
    factory, posture = harness.resolve_replay_sandbox(allow_unsafe=False)
    assert factory is not None
    assert posture["truth_label"] == "LIVE"
    assert posture["hard_isolated"] is True
    assert posture["security_boundary"] is True


# --------------------------------------------------------------------------- #
#  unavailable_replay_report — makes no false claim
# --------------------------------------------------------------------------- #
def test_unavailable_report_claims_nothing_false():
    _, posture = None, {
        "backend": "",
        "hard_isolated": False,
        "security_boundary": False,
        "truth_label": "UNAVAILABLE",
        "reason": "no hard sandbox",
    }
    report = harness.unavailable_replay_report(posture)
    assert report["available"] is False
    assert report["deterministic"] is False
    assert report["outcomes_match"] is False
    assert report["replay_used_network"] is False
    assert report["truth_label"] == "UNAVAILABLE"
    assert report["unavailable_reason"]
    # No fake trace verification / live claim smuggled into the report.
    assert "trace_verified" not in report
    assert report["truth_label"] not in {"LIVE", "TRACE_VERIFIED"}


# --------------------------------------------------------------------------- #
#  Web UI /api/replay — no silent unsafe fallback
# --------------------------------------------------------------------------- #
def _start_server(tmp_path):
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), webui._Handler)
    httpd.trace_dir = str(tmp_path)  # type: ignore[attr-defined]
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    return httpd, httpd.server_address[1]


def _post_replay(port, body=None):
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}/api/replay",
        data=json.dumps(body or {}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read().decode())


def test_webui_replay_fail_closed_without_hard_sandbox(monkeypatch, tmp_path):
    # Force the "no hard sandbox on this host" condition.
    monkeypatch.setattr(harness, "_auto_hard_sandbox", lambda: None)
    httpd, port = _start_server(tmp_path)
    try:
        payload = _post_replay(port)  # default: allow_unsafe not set
        assert payload["available"] is False
        assert payload["deterministic"] is False
        assert payload["truth_label"] == "UNAVAILABLE"
        assert payload["unavailable_reason"]
        # crucially: it did NOT silently run on the unsafe local backend
        assert payload["sandbox"]["security_boundary"] is False
        assert payload["sandbox"]["hard_isolated"] is False
    finally:
        httpd.shutdown()
