# Chimera II Cognitive Node Network

## Goal

Each Chimera II installation may optionally become a **knowledge node**. Nodes exchange signed evidence records and summaries rather than unrestricted executable code or arbitrary model state.

This is intentionally a cooperative, allowlisted network—not an autonomous Internet scanner.

## Architecture

```text
                    ┌──────────────────────────┐
                    │ Internet / approved feeds │
                    └────────────┬─────────────┘
                                 │ HTTPS/TLS
                                 ▼
┌───────────────┐       ┌──────────────────────┐
│ Source parser │──────▶│ Evidence / KG store  │
└───────────────┘       └──────────┬───────────┘
                                   │
                         ┌─────────▼─────────┐
                         │ RNN / GRU / SSM   │
                         │ temporal state    │
                         └─────────┬─────────┘
                                   │
                         ┌─────────▼─────────┐
                         │ Reasoning / query │
                         └─────────┬─────────┘
                                   │
                           signed summaries
                                   │
                         ┌─────────▼─────────┐
                         │ Allowlisted nodes │
                         │ mTLS / HTTPS      │
                         └───────────────────┘
```

## Node identity and discovery

Preferred discovery order:

1. administrator-configured node URLs;
2. DNS-SD/mDNS inside a trusted LAN;
3. organization DNS registry;
4. optional public directory controlled by the user.

No automatic Internet-wide port scanning is permitted.

Each peer must have:

- stable node ID;
- public certificate/key identity;
- explicit trust policy;
- capabilities advertisement;
- protocol version;
- data-retention policy;
- maximum message size/rate;
- provenance requirements.

## Exchange protocol

`POST /v1/evidence`

```json
{
  "node_id": "example-node",
  "schema": "chimera-evidence-v1",
  "source": "https://example.org/document",
  "title": "Example",
  "summary": "Evidence-backed summary",
  "content_hash": "sha256:...",
  "retrieved_at": "2026-09-08T00:00:00Z",
  "signature": "..."
}
```

The receiving node stores provenance separately from neural state. A model prediction is never promoted to authoritative knowledge merely because another node sent it.

## Learning architecture

The cognition subsystem should evolve through stages:

1. deterministic evidence ingestion;
2. embedding/indexing;
3. recurrent temporal state (GRU/RNN);
4. state-space models for long contexts where efficient recurrence is preferable;
5. graph/neuro-symbolic reasoning for explicit relations;
6. retrieval-augmented generation with source citations;
7. federated/peer-assisted model improvement only after privacy, provenance and security controls are validated.

Recent research continues to investigate state-space models as efficient alternatives for long dynamical sequences, while neuro-symbolic knowledge-graph methods combine learned representations with explicit reasoning and provenance. Chimera should treat these as interchangeable research backends, not assume one architecture is universally superior.

## Security boundary

- mTLS for node-to-node transport.
- Signed evidence packets.
- Replay protection using timestamps/nonces.
- Per-peer quotas.
- Content-size limits.
- No executable payload exchange.
- No remote kernel-module loading.
- No remote privileged commands.
- Human/admin approval for new public peers.
- Local audit trail for all imported knowledge.

## Current prototype

`tools/cognition/chimera_rnn.py` contains a small deterministic recurrent-state engine and provenance-aware evidence store. It is deliberately dependency-free so the OS research environment can test the data model before an optional PyTorch/JAX/ONNX runtime is introduced.

Research references:

- State-space models for dynamical systems: https://arxiv.org/abs/2409.03231
- Neuro-symbolic reasoning over knowledge graphs: https://arxiv.org/abs/2412.10390
- Graph + language model integration: https://arxiv.org/abs/2310.05499

These references are research inputs, not claims that Chimera II is already a superintelligent system.
