# BizX / BizXtreme Runtime Integration

BizX and BizXtreme provide language-separated Node.js, Java, and Python implementations under their respective `nodejs/`, `java/`, and `python/` trees. Chimera II OS integration consumes these implementations through stable user-space API boundaries rather than coupling the kernel or native components to a particular managed runtime.

## Implementation boundaries

| Runtime | Role | Build/test entry point |
|---|---|---|
| Node.js 20+ | Server, web/API and integration services | `npm test` |
| Java 17+ | JVM application/services and enterprise integration | `mvn test` |
| Python 3.10+ | Automation, tooling, service integration and research workflows | `python -m unittest discover -s tests` |

## BizX

BizX exposes core business services, wallet/provider abstractions, catalog and payment lifecycle models, API boundaries, and CLI entry points in each supported language.

## BizXtreme

BizXtreme extends the same boundaries with crypto/chain registries, WebGL and Three.js adapters, game state services, Aurora-facing integration, and Chimera-facing application services.

## Chimera II OS integration

- The managed-language implementations belong in user-space services and web/API layers.
- Koronos and other performance-critical native components remain implemented in their appropriate native language.
- Wallet providers communicate through explicit request boundaries; private keys and signing material must remain in the secure wallet/runtime boundary.
- WebGL and Three.js implementations are runtime adapters; Java/Python do not pretend to replace the browser graphics runtime.
- Packaged APK/WebGL/Unity artifacts remain separate from these language-specific source trees.

## Repository layout rule

Application source is organized language-first. Subsystems may be mirrored between implementations, but source files from different programming languages are not mixed inside a Java or Python implementation directory.
