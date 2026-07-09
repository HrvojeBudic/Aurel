"""F5.0b seal — manual RFC 6455 WebSocket (stdlib)."""
from __future__ import annotations

import json
import socket

import pytest

from agentic_runtime.front_server import (
    WebSocketError,
    build_frame,
    compute_accept_key,
    create_front_server,
    parse_frame,
)
from agentic_runtime.front_server import websocket as ws_mod
from agentic_runtime.front_server.websocket import OP_TEXT


def test_accept_key_rfc_vector():
    assert compute_accept_key("dGhlIHNhbXBsZSBub25jZQ==") == "s3pPLMBiTxaQ9kYGzzhZRbK+xOo="


def test_masked_frame_round_trip():
    payload = b"hello websocket"
    frame_bytes = build_frame(payload, OP_TEXT, masking_key=b"\x01\x02\x03\x04")
    frame, consumed = parse_frame(frame_bytes, require_masked=True)
    assert frame.payload == payload
    assert frame.masked is True
    assert consumed == len(frame_bytes)


def test_extended_length_round_trip():
    payload = b"x" * 70000
    frame, _ = parse_frame(build_frame(payload, masking_key=b"\xaa\xbb\xcc\xdd"),
                           require_masked=True)
    assert frame.payload == payload


def test_unmasked_client_frame_rejected():
    with pytest.raises(WebSocketError):
        parse_frame(build_frame(b"hi", OP_TEXT), require_masked=True)


def test_incomplete_buffer_raises_incomplete():
    full = build_frame(b"data", masking_key=b"\x01\x02\x03\x04")
    with pytest.raises(WebSocketError) as e:
        parse_frame(full[:3], require_masked=True)
    assert "incomplete" in str(e.value)


def test_transport_scope_guards_false():
    assert ws_mod.claims_remote_websocket is False
    assert ws_mod.claims_wss_tls is False


@pytest.fixture
def server(monkeypatch):
    monkeypatch.setenv("AUREL_FRONT_SERVER", "1")
    srv = create_front_server(object(), port=0)
    srv.serve_forever_background()
    try:
        yield srv
    finally:
        srv.shutdown()


def test_websocket_end_to_end(server):
    sock = socket.create_connection((server.host, server.port), timeout=5)
    try:
        req = (
            "GET /ws HTTP/1.1\r\n"
            f"Host: {server.host}:{server.port}\r\n"
            "Upgrade: websocket\r\nConnection: Upgrade\r\n"
            "Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==\r\n"
            "Sec-WebSocket-Version: 13\r\n\r\n"
        )
        sock.sendall(req.encode())
        resp = sock.recv(4096).decode()
        assert "101" in resp.split("\r\n", 1)[0]
        assert "s3pPLMBiTxaQ9kYGzzhZRbK+xOo=" in resp

        proposal = json.dumps({"kind": "act"}).encode()
        sock.sendall(build_frame(proposal, OP_TEXT, masking_key=b"\x11\x22\x33\x44"))
        frame, _ = parse_frame(sock.recv(65536))
        reply = json.loads(frame.payload)
        assert reply["accepted"] is True and reply["kind"] == "act"
    finally:
        sock.close()
