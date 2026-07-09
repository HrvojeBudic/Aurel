"""
server.py — the Front HTTP (+ WebSocket) server: the one and only UI↔backend door.

Stdlib `ThreadingHTTPServer` + a declarative-route dispatcher (`routes.py`). The
server is **not constructed when the flag is OFF** (`create_front_server` raises),
so a flag-off runtime is byte-identical — no listener, no threads. Reads are pure
projections; the single `POST /proposals` route is the only mutation, reduced by
the `ProposalDispatcher`; `GET /ws` is a non-mutation WebSocket stream reduced
through the same dispatcher. No handler touches a subsystem directly.
"""
from __future__ import annotations

import json
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Optional

from .proposal_dispatcher import ProposalDispatcher, ProposalRejected
from .read_models import LiveReadModels
from .routes import match_route
from .websocket import WebSocketConnection, compute_accept_key

_FLAG = "AUREL_FRONT_SERVER"
_MAX_BODY_BYTES = 4 * 1024 * 1024


def flag_enabled() -> bool:
    """True iff the Front-server flag is explicitly enabled (default OFF)."""
    return os.environ.get(_FLAG, "").strip() in ("1", "true", "TRUE", "on")


class FrontServerDisabled(RuntimeError):
    """Raised when the server is requested while the flag is OFF. Fail-closed."""


class FrontApp:
    """The request handlers behind the routes. Read-only except the one door."""

    def __init__(self, runtime: Any, *, conversation_engine: Any = None) -> None:
        self._dispatcher = ProposalDispatcher(
            runtime, conversation_engine=conversation_engine)
        self._reads = LiveReadModels(runtime)

    def handle_health(self, method: str, path: str, body: Any) -> tuple[int, dict]:
        return 200, {"status": "ok", "server": "aurel_front.v1"}

    def handle_read(self, method: str, path: str, body: Any) -> tuple[int, dict]:
        # Pure live projections over the trace (F5.1) — no write, no subsystem call.
        return self._reads.read(path)

    def handle_proposals(self, method: str, path: str, body: Any) -> tuple[int, dict]:
        try:
            result = self._dispatcher.dispatch(body)
        except ProposalRejected as e:
            return 400, {"error": str(e)}
        return 200, result

    def ws_loop(self, ws: WebSocketConnection) -> None:
        """Serve one WebSocket session. Each inbound text frame is a JSON proposal
        reduced through the SAME dispatcher — the WS is a stream, not a new door."""
        while True:
            text = ws.recv_text()
            if text is None:
                break
            try:
                proposal = json.loads(text)
                reply = self._dispatcher.dispatch(proposal)
            except (ValueError, ProposalRejected) as e:
                reply = {"error": str(e)}
            ws.send_text(json.dumps(reply))


class FrontServer:
    """A running Front HTTP server bound to one runtime."""

    def __init__(self, runtime: Any, host: str = "127.0.0.1", port: int = 0,
                 *, conversation_engine: Any = None) -> None:
        self.app = FrontApp(runtime, conversation_engine=conversation_engine)
        self._httpd = ThreadingHTTPServer((host, port), _make_handler(self.app))
        self._thread: Optional[threading.Thread] = None

    @property
    def port(self) -> int:
        return self._httpd.server_address[1]

    @property
    def host(self) -> str:
        return self._httpd.server_address[0]

    def serve_forever_background(self) -> None:
        self._thread = threading.Thread(target=self._httpd.serve_forever, daemon=True)
        self._thread.start()

    def serve_forever(self) -> None:
        self._httpd.serve_forever()

    def shutdown(self) -> None:
        self._httpd.shutdown()
        self._httpd.server_close()


def _make_handler(app: FrontApp) -> type[BaseHTTPRequestHandler]:
    class _Handler(BaseHTTPRequestHandler):
        def log_message(self, *args: Any) -> None:  # silence stdout
            pass

        def _json(self, status: int, payload: dict) -> None:
            data = json.dumps(payload).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def _body(self) -> Any:
            length = int(self.headers.get("Content-Length", 0) or 0)
            if length <= 0 or length > _MAX_BODY_BYTES:
                return None
            raw = self.rfile.read(length)
            try:
                return json.loads(raw.decode("utf-8"))
            except (ValueError, UnicodeDecodeError):
                return None

        def _dispatch(self, method: str) -> None:
            route = match_route(method, self.path)
            if route is None:
                self._json(404, {"error": "not found"})
                return
            if route.handler == "handle_websocket_upgrade":
                self._websocket_upgrade()
                return
            body = self._body() if method == "POST" else None
            handler = getattr(app, route.handler)
            status, payload = handler(method, self.path, body)
            self._json(status, payload)

        def _websocket_upgrade(self) -> None:
            key = self.headers.get("Sec-WebSocket-Key")
            if not key:
                self._json(400, {"error": "missing Sec-WebSocket-Key"})
                return
            self.send_response(101, "Switching Protocols")
            self.send_header("Upgrade", "websocket")
            self.send_header("Connection", "Upgrade")
            self.send_header("Sec-WebSocket-Accept", compute_accept_key(key))
            self.end_headers()
            ws = WebSocketConnection(self.connection)
            try:
                app.ws_loop(ws)
            except OSError:
                pass
            finally:
                ws.close()

        def do_GET(self) -> None:
            self._dispatch("GET")

        def do_POST(self) -> None:
            self._dispatch("POST")

    return _Handler


def create_front_server(
    runtime: Any, *, host: str = "127.0.0.1", port: int = 0,
    conversation_engine: Any = None,
) -> FrontServer:
    """Build the Front server — but only when the flag is ON (else fail-closed)."""
    if not flag_enabled():
        raise FrontServerDisabled(
            "AUREL_FRONT_SERVER is OFF; the Front server is not constructed"
        )
    return FrontServer(runtime, host=host, port=port,
                       conversation_engine=conversation_engine)
