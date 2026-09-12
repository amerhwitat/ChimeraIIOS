# Chimera II Neural Reasoning Layer

The Neural Reasoning Layer is a deterministic, explainable user-space engine that combines evidence scoring, confidence, perspective transforms, multidimensional feature vectors, and optional RNN/LLM adapters.

## Design

1. **Evidence** is represented as weighted features rather than opaque truth.
2. **Perspective** transforms observation coordinates without changing the underlying geometry.
3. **Multidimensional reasoning** keeps feature axes explicit; 128D is an experimental semantic profile, not a physical claim.
4. **Confidence** is bounded to `[0,1]` and is never presented as certainty.
5. **Adapters** can connect an external neural model, but the base engine remains dependency-free.

The core intentionally does not ship model weights or scrape the Internet automatically. Network/model providers are explicit adapters with policy and provenance boundaries.
