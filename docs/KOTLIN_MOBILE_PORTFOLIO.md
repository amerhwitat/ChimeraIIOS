# Kotlin Mobile Portfolio

The portfolio now includes isolated Kotlin Android mobile implementations under `kotlin/mobile/` in the related application repositories.

## Repositories

| Application | Kotlin mobile path | Mobile focus |
|---|---|---|
| BizX | `kotlin/mobile/` | Business application state and trusted P2P boundary |
| BizXtreme | `kotlin/mobile/` | Game/web/crypto application boundary |
| CPU4096 | `kotlin/mobile/` | Wide-register CPU research |
| CPU4096Simulator | `kotlin/mobile/` | ISA, memory/MMIO and simulator dashboard |
| PDFreaderPY | `kotlin/mobile/` | Document ingestion and provenance objects |
| nlp | `kotlin/mobile/` | Ancient-script NLP, Unicode and RTL research |
| eth-key-check | `kotlin/mobile/` | Owner-authorized crypto verification only |
| bruteforce | `kotlin/mobile/` | Synthetic/deterministic crypto research only |
| keygen | `kotlin/mobile/` | Authorized key generation and trusted-node research |
| test | `kotlin/mobile/` | Portfolio integration/conformance harness |
| ChimeraIIOS | `kotlin/mobile/` | Mobile application layer over the Mobile Microkernel boundary |

## Baseline

The Android implementations use Kotlin 2.4.20, Android Gradle Plugin 9.4.0, compile/target SDK 36, and JDK 17. Each application is isolated so the existing C/C++/ASM, Java, Node.js, Python, JavaScript, TypeScript, .NET, and desktop implementations remain independently buildable.

## Mobile architecture

The current delivered target is Android. The directory layout intentionally leaves a clean path to Kotlin Multiplatform: shared business/state logic can move into common source sets while Android and iOS keep dedicated entry points. Kotlin Multiplatform documents Android and iOS as stable targets, and Compose Multiplatform provides shared UI when desired.

The portfolio's 128D semantic-state model is treated as application state, not as a replacement for geometry, operating-system primitives, or platform APIs. Trusted-node communication remains opt-in, authenticated, replay-aware, and payload-integrity checked. No application performs unsolicited Internet scanning or remote command execution.

## Security baseline

The mobile applications default to no cleartext traffic. Any future network adapter must use TLS/secure transport and the existing authenticated P2P contract. Crypto research applications retain their existing authorization and synthetic-vector boundaries.

## Build

Open each `kotlin/mobile/` directory as an Android Studio Gradle project and build the `app` module. iOS builds require macOS/Xcode; an iOS target should be added as a Kotlin Multiplatform/Xcode integration rather than pretending an Android APK is an iOS application.

## Primary references

- Kotlin Multiplatform: https://kotlinlang.org/multiplatform/
- Kotlin Multiplatform quickstart: https://kotlinlang.org/docs/multiplatform/quickstart.html
- Kotlin Multiplatform project structure: https://kotlinlang.org/docs/multiplatform/multiplatform-project-recommended-structure.html
- Compose Multiplatform: https://kotlinlang.org/docs/multiplatform/compose-multiplatform-create-first-app.html
- Kotlin 2.4.20 release: https://kotlinlang.org/docs/whatsnew2420.html
- Android Gradle Plugin: https://developer.android.com/reference/tools/gradle-api
- Android network security: https://developer.android.com/privacy-and-security/security-config
