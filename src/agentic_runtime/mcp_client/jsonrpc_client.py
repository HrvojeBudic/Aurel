"""
jsonrpc_client.py — client-side JSON-RPC 2.0 for the MCP client bridge (B0).

The mirror of the server-side ``mcp_gateway/jsonrpc.py``: here Aurel *issues*
requests and notifications and *correlates* responses. Deterministic (monotonic
request ids, no RNG) and fail-closed — a malformed response envelope raises
``JsonRpcClientError`` rather than being coerced into a fake result. Reuses the
shared protocol constants and the ``JsonRpcError`` value type from the gateway so
the two directions never drift.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from ..mcp_gateway.jsonrpc import JSONRPC_VERSION, JsonId, JsonRpcError


class JsonRpcClientError(RuntimeError):
    """A malformed / unexpected JSON-RPC response envelope. Fail-closed."""


@dataclass(frozen=True)
class Response:
    """A correlated JSON-RPC response: exactly one of result / error is set."""

    id: JsonId
    result: Any = None
    error: Optional[JsonRpcError] = None

    @property
    def is_error(self) -> bool:
        return self.error is not None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "result": self.result,
            "error": self.error.to_dict() if self.error else None,
        }


class JsonRpcClientCodec:
    """Builds requests / notifications and correlates responses for one session."""

    def __init__(self) -> None:
        self._next_id = 0

    def build_request(
        self, method: str, params: Optional[dict] = None
    ) -> tuple[int, dict]:
        """Return ``(id, message)`` for a correlatable request."""
        if not isinstance(method, str) or not method:
            raise JsonRpcClientError("method must be a non-empty string")
        self._next_id += 1
        rid = self._next_id
        msg: dict[str, Any] = {"jsonrpc": JSONRPC_VERSION, "id": rid, "method": method}
        if params is not None:
            msg["params"] = params
        return rid, msg

    def build_notification(
        self, method: str, params: Optional[dict] = None
    ) -> dict:
        """Return a notification message (no id — no response expected)."""
        if not isinstance(method, str) or not method:
            raise JsonRpcClientError("method must be a non-empty string")
        msg: dict[str, Any] = {"jsonrpc": JSONRPC_VERSION, "method": method}
        if params is not None:
            msg["params"] = params
        return msg

    def correlate(self, response: Any) -> Response:
        """Validate a decoded response envelope. Fail-closed on anything off-spec."""
        if not isinstance(response, dict):
            raise JsonRpcClientError("response must be a JSON object")
        if response.get("jsonrpc") != JSONRPC_VERSION:
            raise JsonRpcClientError("response jsonrpc must be '2.0'")
        has_result = "result" in response
        has_error = "error" in response
        if has_result == has_error:  # both present, or neither
            raise JsonRpcClientError(
                "response must carry exactly one of 'result' or 'error'"
            )
        rid = response.get("id")
        if has_error:
            err = response["error"]
            if (
                not isinstance(err, dict)
                or "code" not in err
                or "message" not in err
            ):
                raise JsonRpcClientError("malformed error object")
            return Response(
                id=rid,
                error=JsonRpcError(
                    code=int(err["code"]),
                    message=str(err["message"]),
                    data=err.get("data"),
                ),
            )
        return Response(id=rid, result=response["result"])

    def expect(self, response: Any, request_id: int) -> Response:
        """Correlate and assert the response answers ``request_id``."""
        parsed = self.correlate(response)
        if parsed.id != request_id:
            raise JsonRpcClientError(
                f"response id {parsed.id!r} does not match request id {request_id!r}"
            )
        return parsed
