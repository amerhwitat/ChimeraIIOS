# ISO-Tool language parity and synchronization

The Chimera II OS copy of ISO-Tool follows the same cross-language contract as `amerhwitat/nlp/ISO-Tool`.

Python is the reference orchestration layer. C++ and .NET provide native Windows desktop integration and expose the same toolchain, dependency, build, artifact, boot and verification concepts.

## Shared pipeline

`toolchain detection → dependency checks → recursive source analysis → build/link planning → parallel compilation → artifact collection → Spit Fire boot artifact → ISO/IMG staging → verification`

## Shared repositories

ChimeraIIOS, BizX and BizXtreme are the standard combined workspace sources. Source trees and provenance are retained; generated executables, libraries and boot artifacts are staged separately.

## Synchronization rule

`amerhwitat/nlp/ISO-Tool` is the reference implementation for shared orchestration behavior. `ChimeraIIOS/ISO-Tool` mirrors the integration contract so either repository can participate in the same build workflow without silently changing artifact semantics.
