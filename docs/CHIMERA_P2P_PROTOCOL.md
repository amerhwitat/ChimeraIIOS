# Chimera authenticated P2P protocol

## Goals

Provide a common, language-neutral peer protocol for Chimera applications and OS nodes without requiring a central server.

## Peer lifecycle

1. Local configuration enables the peer service.
2. A node creates or loads a stable node identity.
3. A connection performs protocol/version negotiation.
4. Peers exchange capabilities and supported 128D profile extensions.
5. Authentication establishes trust according to the local trust policy.
6. Application synchronization begins only after authorization.

## Message envelope

```json
{
  "version": 1,
  "type": "request|response|publish|snapshot|delta|ack",
  "node_id": "...",
  "sequence": 1,
  "timestamp": "...",
  "capabilities": [],
  "object_id": "...",
  "payload_hash": "...",
  "payload": {},
  "signature": "..."
}
```

## Synchronization

Applications may use request/response, pub/sub, snapshot/delta or content-addressed object exchange. Sequence numbers provide deterministic ordering; payload hashes detect corruption; signatures and authenticated transports establish integrity and peer identity.

## Trust and safety

Peer discovery is configured/bootstrap-based or uses an explicitly approved discovery mechanism. The protocol does not authorize arbitrary Internet scanning. Credentials, private keys, seed phrases and secrets are never protocol payloads. Executable code is not transferred or automatically executed by synchronization.

## Transport mapping

Implementations may map the protocol onto TCP/TLS, QUIC, WebSocket/WebRTC, Unix-domain sockets, Bluetooth/nearby transports or OS-native IPC as appropriate. The logical envelope remains stable.

## Language mappings

- C/C++: low-level framing, kernel/service integration and high-performance peer transport.
- C#: managed service/application adapter.
- Java: JVM peer service.
- Node.js: asynchronous peer service and WebSocket/QUIC-capable adapters.
- Python: reference/research implementation.
- JavaScript/TypeScript: browser-compatible WebSocket/WebRTC adapter.
- Assembly: boot/kernel primitives only; networking policy remains in higher-level components.
