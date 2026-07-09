"""
websocket.py — manual RFC 6455 WebSocket in the standard library (F5.0b).

No third-party dependency: the handshake and framing are implemented directly on
stdlib `socket`/`hashlib`/`base64`. This is a *push/stream* channel, not a second
executor — an inbound text frame is a JSON `ProposalEnvelope` reduced through the
same `ProposalDispatcher`, never a direct subsystem call.

Scope (honest): localhost-only, no TLS/wss. `claims_remote_websocket` and
`claims_wss_tls` are False until a Tauri-Rust transport is introduced. Every
incoming client frame MUST be masked (RFC 6455 §5.1); an unmasked client frame is
rejected fail-closed.
"""
from __future__ import annotations

import base64
import hashlib
import struct
from dataclasses import dataclass
from typing import Optional

WS_GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"

OP_CONT = 0x0
OP_TEXT = 0x1
OP_BINARY = 0x2
OP_CLOSE = 0x8
OP_PING = 0x9
OP_PONG = 0xA

_MAX_PAYLOAD = 8 * 1024 * 1024

# Honest transport-scope guards.
claims_remote_websocket = False
claims_wss_tls = False


class WebSocketError(RuntimeError):
    """A protocol violation or short buffer. Fail-closed."""


def compute_accept_key(sec_websocket_key: str) -> str:
    """RFC 6455 §4.2.2: base64(SHA1(key + GUID))."""
    digest = hashlib.sha1((sec_websocket_key + WS_GUID).encode("ascii")).digest()  # nosec B324 - RFC 6455 mandates SHA1 here
    return base64.b64encode(digest).decode("ascii")


@dataclass(frozen=True)
class Frame:
    fin: bool
    opcode: int
    payload: bytes
    masked: bool


def build_frame(
    payload: bytes,
    opcode: int = OP_TEXT,
    *,
    fin: bool = True,
    masking_key: Optional[bytes] = None,
) -> bytes:
    """Build one frame. Server frames are unmasked (masking_key=None); a 4-byte
    masking_key produces a client-style masked frame (used by tests)."""
    b0 = (0x80 if fin else 0) | (opcode & 0x0F)
    out = bytearray([b0])
    length = len(payload)
    mask_bit = 0x80 if masking_key is not None else 0
    if length < 126:
        out.append(mask_bit | length)
    elif length < 65536:
        out.append(mask_bit | 126)
        out += struct.pack("!H", length)
    else:
        out.append(mask_bit | 127)
        out += struct.pack("!Q", length)
    if masking_key is not None:
        if len(masking_key) != 4:
            raise WebSocketError("masking key must be 4 bytes")
        out += masking_key
        out += bytes(b ^ masking_key[i % 4] for i, b in enumerate(payload))
    else:
        out += payload
    return bytes(out)


def parse_frame(buf: bytes, *, require_masked: bool = False) -> tuple[Frame, int]:
    """Parse one frame from ``buf``. Returns (frame, bytes_consumed).

    Raises ``WebSocketError('incomplete')`` if ``buf`` does not yet hold a full
    frame, or a protocol error (oversize / unmasked-when-required).
    """
    if len(buf) < 2:
        raise WebSocketError("incomplete")
    b0, b1 = buf[0], buf[1]
    fin = bool(b0 & 0x80)
    opcode = b0 & 0x0F
    masked = bool(b1 & 0x80)
    length = b1 & 0x7F
    offset = 2
    if length == 126:
        if len(buf) < offset + 2:
            raise WebSocketError("incomplete")
        length = struct.unpack("!H", buf[offset:offset + 2])[0]
        offset += 2
    elif length == 127:
        if len(buf) < offset + 8:
            raise WebSocketError("incomplete")
        length = struct.unpack("!Q", buf[offset:offset + 8])[0]
        offset += 8
    if length > _MAX_PAYLOAD:
        raise WebSocketError("payload exceeds max")
    if require_masked and not masked:
        raise WebSocketError("client frame must be masked (RFC 6455 §5.1)")
    mask_key = b""
    if masked:
        if len(buf) < offset + 4:
            raise WebSocketError("incomplete")
        mask_key = buf[offset:offset + 4]
        offset += 4
    if len(buf) < offset + length:
        raise WebSocketError("incomplete")
    raw = buf[offset:offset + length]
    if masked:
        raw = bytes(b ^ mask_key[i % 4] for i, b in enumerate(raw))
    return Frame(fin=fin, opcode=opcode, payload=raw, masked=masked), offset + length


class WebSocketConnection:
    """A server-side WebSocket over an accepted socket. Client frames must mask."""

    def __init__(self, sock: object) -> None:
        self._sock = sock
        self._buf = bytearray()
        self._closed = False

    def _recv_into_buffer(self) -> bool:
        chunk = self._sock.recv(65536)  # type: ignore[attr-defined]
        if not chunk:
            return False
        self._buf += chunk
        return True

    def recv_frame(self) -> Optional[Frame]:
        """Read one client frame (enforcing mask). None on close/EOF."""
        while not self._closed:
            try:
                frame, consumed = parse_frame(bytes(self._buf), require_masked=True)
            except WebSocketError as e:
                if str(e) == "incomplete":
                    if not self._recv_into_buffer():
                        return None
                    continue
                raise
            del self._buf[:consumed]
            if frame.opcode == OP_CLOSE:
                self.close()
                return None
            if frame.opcode == OP_PING:
                self._send(frame.payload, OP_PONG)
                continue
            if frame.opcode == OP_PONG:
                continue
            return frame
        return None

    def recv_text(self) -> Optional[str]:
        frame = self.recv_frame()
        if frame is None:
            return None
        return frame.payload.decode("utf-8", errors="replace")

    def _send(self, payload: bytes, opcode: int) -> None:
        if self._closed:
            return
        self._sock.sendall(build_frame(payload, opcode))  # type: ignore[attr-defined]

    def send_text(self, text: str) -> None:
        self._send(text.encode("utf-8"), OP_TEXT)

    def ping(self, payload: bytes = b"") -> None:
        self._send(payload, OP_PING)

    def close(self) -> None:
        if self._closed:
            return
        try:
            self._send(b"", OP_CLOSE)
        except OSError:  # pragma: no cover
            pass
        self._closed = True
