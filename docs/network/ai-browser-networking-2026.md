# Chimera AI, Neural and Browser Networking Architecture — 2026

## Research basis

Chimera tracks HTTP/3/QUIC, WebTransport, WASI HTTP, MCP, A2A and browser-agent interoperability as adapter boundaries rather than embedding vendor-specific implementations.

MCP 2026-07-28 is stateless at the transport layer and supports Streamable HTTP; the protocol also formalizes extensions and authorization hardening. Chimera therefore uses request-scoped capability metadata and does not depend on legacy MCP sessions.

WebTransport provides HTTP/3 transport with multiple streams, unidirectional streams and datagrams. It is selected for low-latency workloads where datagrams are useful, while HTTP/3 remains the general web transport.

WASI 0.3 adds native async to the WebAssembly Component Model. Chimera's Mobile, Edge and CVEL editions can use WASI HTTP/async adapters without coupling the kernel to a particular browser engine.

## Neural/runtime integration

The AI layer combines streaming inference, speculative decoding, mixture-of-experts routing, state-space-model adapters, retrieval-backed inference and federated/edge inference. Network selection is treated as part of inference scheduling: local inference avoids network cost; remote inference uses HTTP/3 or WebTransport based on latency and streaming requirements.

## Browser pipeline

`DNS -> TLS -> HTTP/3/QUIC -> origin policy -> cache -> structured extraction -> provenance -> capability gate -> telemetry`

Browser automation must remain capability constrained. Reading public content can be exposed as a non-mutating capability; arbitrary remote code execution, credential extraction, silent network configuration, unbounded crawling and transactions are not default capabilities.

## Editions

- Desktop: HTTP/3, WebTransport, MCP adapters, local model/runtime bridge.
- Server: HTTP/3, WebTransport, MCP/A2A gateway, OpenTelemetry integration.
- Mobile: HTTP/3, WASI HTTP, local-first inference and constrained WebTransport.
- Edge/IoT: WebTransport/WASI, streaming telemetry and federated inference adapters.
- CVEL: virtual DNS/TLS/HTTP/WASI networking for architecture and protocol testing.

## Integration rule

Protocol specifications and upstream projects are treated as external evidence. Chimera stores provenance, license and compatibility metadata and integrates through adapters. It does not automatically execute newly discovered Internet source code.
