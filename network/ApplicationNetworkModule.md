# Chimera II OS Application Network Module

All Chimera II OS applications can embed the Network Center alongside existing P2P services.

## Modes

- Client — connect to a configured Koronos/Spotnik service.
- Server — listen and host application rooms/services.
- Host — server + local client in the same process/session.
- P2P — direct peer links through the existing P2P layer.
- Hybrid — server control/state plus direct peer channels.

## UI

The application exposes **Network → Configure** with:

1. Nickname field.
2. Built-in avatar selector.
3. `Upload avatar` when no suitable built-in avatar exists.
4. Mode selector.
5. Bind/listen address and port for server/host.
6. Remote endpoint for client mode.
7. Room/service name.
8. P2P enable/disable and relay/discovery policy.
9. TLS/certificate/authentication settings.
10. Start/Stop and connection status.

Host mode creates a local client session against the local server so host actions use the same authorization and message routing path as remote users.

## Spotnik/Koronos integration

Spotnik remains the OS networking boundary; this module defines application-level sessions above it. Transport adapters may use QUIC/TLS, TCP/TLS, WebRTC, WebSocket/WebTransport, or libp2p according to platform capability.

## Profile and privacy

Only nickname and selected avatar metadata are exchanged as presentation profile data. Raw IP addresses are not persisted as profile attributes. Credentials, private keys, wallet secrets and unrelated OS secrets are excluded from network serialization.

## References

- IETF RFC 9000 — QUIC
- IETF RFC 6455 — WebSocket
- IETF RFC 8831 — WebRTC Data Channels
- libp2p modular transport, peer identity and NAT traversal architecture
