# Chimera portfolio integration matrix

| Repository/application | Primary role | 128D integration | P2P integration |
|---|---|---|---|
| ChimeraIIOS | OS/kernel/platform | native system profile | trusted node fabric |
| BizX | application/game | world + player state | authenticated state sync |
| BizXtreme | extended game/WebGL/Unity | world/object/cognition state | authenticated state sync |
| CPU4096 | wide-register research | CPU/register multidimensional state | deterministic simulator sync |
| CPU4096Simulator | web/runtime simulator | CPU/kernel/brain state | simulator peer synchronization |
| NLP | ancient-language research | document/character/observer state | research record synchronization |
| PDFreaderPY | document ingestion | provenance/object state | provenance-preserving sync |
| eth-key-check | crypto research | deterministic research state | public/synthetic state only |

## Common rule

Repositories keep language-specific implementations separate but share the same semantic schema, conformance vectors and security boundaries. A repository may provide a native reference implementation and consume the canonical protocol from ChimeraIIOS.
