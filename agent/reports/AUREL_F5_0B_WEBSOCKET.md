# AUREL F5.0b — WebSocket Transport (RFC 6455, stdlib)

_branch `feat/f5-front-v1`. A bidirectional stream that is not a second door._

## What shipped
`front_server/websocket.py` — a hand-rolled RFC 6455 implementation on stdlib only
(handshake `Sec-WebSocket-Accept = base64(SHA1(key + GUID))`, frame encode/decode + client-mask
unmasking, ping/pong, close). `GET /ws` upgrades in the server; an inbound frame is the same
`ProposalEnvelope` reduced through the same dispatcher — the WS never calls a subsystem directly.

## Evidence
Seal `tests/test_p6f5_0b_websocket.py` — correct accept-key from the RFC vector; masked frame
round-trip; an unmasked client frame is rejected (protocol fail-closed).

## Boundary
localhost-only, **no wss/TLS** (`claims_remote_websocket` / `claims_wss_tls` False) until a
Tauri-Rust transport lands.
