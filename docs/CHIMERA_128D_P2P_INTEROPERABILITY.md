# Chimera 128D + P2P Interoperability

## Purpose

This document defines the common application interoperability contract for the Amer Hwitat repository ecosystem. It is intentionally language-neutral so C/C++, C#, Java, Node.js, Python, JavaScript and TypeScript implementations can exchange the same logical state.

## 128D state model

Applications may attach a `chimera_state` object to domain records. The base model distinguishes geometry from perspective and represents: position/shape, temporal state, observer/perspective, light/shadow/material response, events, objects, object properties, interaction rules, perception/representation, memory, inference and action. Implementations may use sparse vectors or extend beyond 128 dimensions without changing the envelope version.

## P2P envelope

Each peer message contains protocol version, message id, sender peer id, monotonic sequence, timestamp/expiry, capability set, message type, payload hash, optional parent/content hash, and an authenticated signature. Implementations must reject malformed messages, expired messages, duplicate sequence numbers and unauthorized capabilities.

## Discovery and trust

Peers are discovered from explicit configuration, local discovery, or trusted bootstrap services. Applications do not perform arbitrary Internet port scanning. A discovered peer is untrusted until identity and capability policy verification succeeds.

## Synchronization

State synchronization is content-addressed and deterministic. Peers exchange hashes/manifests first, then request missing records. Conflicts use application-specific version vectors or deterministic last-writer policies; security-sensitive records require explicit authorization rather than automatic conflict resolution.

## Transport mapping

Native applications may use TCP/UDP/QUIC. Browser applications may use WebSocket/WebRTC. The logical envelope is transport-independent. Transport selection must not change authorization semantics.

## Language mapping

- C/C++: POD/struct envelope and native transport adapters.
- C#: record/DTO envelope and async sockets/WebSocket adapters.
- Java: immutable record/POJO envelope and NIO/QUIC-capable adapters.
- Node.js: JSON/Buffer envelope and TCP/UDP/WebSocket adapters.
- Python: dataclass/JSON envelope and asyncio adapters.
- JavaScript/TypeScript: typed JSON envelope and WebSocket/WebRTC adapters.

## Security boundary

P2P synchronization never implies remote command execution. Applications expose capabilities explicitly and default to read-only synchronization. Secrets, private keys, credentials and host-level privileged operations are never transmitted as synchronization state.

## Repository contract

Repositories can keep their native architecture while consuming this contract through `chimera/p2p_protocol.json` or an equivalent language-native adapter. The canonical OS-level implementation remains in Chimera II OS; application repositories implement only the capabilities they need.

## License

This documentation and original implementation material are released under GNU GPLv3-or-later where the containing repository applies GPL licensing. Third-party material remains under its own license.
