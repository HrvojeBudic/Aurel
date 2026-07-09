"""
jsonrpc.py — minimal stdlib JSON-RPC 2.0 for the MCP gateway (F3.3).

No third-party dependency: just the request/response/error value types and a
parser that validates the envelope and fails closed with the correct standard
error code. Deterministic and side-effect-free.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional, Union

JSONRPC_VERSION = "2.0"

# Standard JSON-RPC 2.0 error codes.
PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603
# Gateway-specific application error (governed denial / block).
GATEWAY_DENIED = -32001

JsonId = Union[str, int, None]


@dataclass(frozen=True)
class JsonRpcError:
    code: int
    message: str
    data: Optional[dict] = None

    def to_dict(self) -> dict:
        d: dict[str, Any] = {"code": self.code, "message": self.message}
        if self.data is not None:
            d["data"] = self.data
        return d


@dataclass(frozen=True)
class JsonRpcRequest:
    method: str
    id: JsonId = None
    params: dict = field(default_factory=dict)


def success(id: JsonId, result: Any) -> dict:
    return {"jsonrpc": JSONRPC_VERSION, "id": id, "result": result}


def error(id: JsonId, code: int, message: str, data: Optional[dict] = None) -> dict:
    return {
        "jsonrpc": JSONRPC_VERSION,
        "id": id,
        "error": JsonRpcError(code, message, data).to_dict(),
    }


def parse_request(raw: Any) -> Union[JsonRpcRequest, dict]:
    """Validate a decoded JSON-RPC request. Returns a request, or an error dict.

    Fails closed with the correct standard code: a non-object is INVALID_REQUEST,
    a wrong/missing ``jsonrpc`` is INVALID_REQUEST, a missing/non-str ``method``
    is INVALID_REQUEST, and non-object ``params`` is INVALID_PARAMS.
    """
    if not isinstance(raw, dict):
        return error(None, INVALID_REQUEST, "request must be a JSON object")
    rid = raw.get("id")
    if raw.get("jsonrpc") != JSONRPC_VERSION:
        return error(rid, INVALID_REQUEST, "jsonrpc must be '2.0'")
    method = raw.get("method")
    if not isinstance(method, str) or not method:
        return error(rid, INVALID_REQUEST, "method must be a non-empty string")
    params = raw.get("params", {})
    if not isinstance(params, dict):
        return error(rid, INVALID_PARAMS, "params must be an object")
    return JsonRpcRequest(method=method, id=rid, params=params)
