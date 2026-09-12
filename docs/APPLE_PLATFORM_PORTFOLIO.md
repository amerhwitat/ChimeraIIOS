# Apple Platform Portfolio

Chimera II OS and related applications now expose an Apple source/build boundary for iOS/iPadOS and macOS.

## Build model

- Native Apple UI: SwiftUI/Xcode.
- Shared portable logic: Kotlin Multiplatform/Kotlin-Native where Kotlin exists.
- Device target: `iosArm64`.
- Apple-Silicon simulator target: `iosSimulatorArm64`.
- macOS targets are native Swift/Xcode where a desktop application is appropriate.
- Authoritative build system: `xcodebuild`.
- Optional open-source automation: fastlane.
- Optional distribution boundary: Swift Package Manager/XCFramework.

## Artifacts

`build/ipa/` — exported IPA

`build/archive/` — XCArchive

`build/DerivedData/` — Xcode derived data

`build/xcframework/` — Kotlin/Native XCFrameworks

## Signing

Signing is operator-controlled. Never commit certificates, provisioning profiles, API keys, keychains, or private keys. An unsigned simulator/source validation build is the default CI path; signed archive/export requires configured macOS secrets.

## Windows/Linux

Windows PowerShell/CMD and Linux shells may prepare source, validate manifests, and dispatch a macOS runner. They cannot replace Xcode/macOS for a genuine iOS IPA build.

## Communications and permissions

BizX/BizXtreme Apple clients may share the existing authenticated conversation/P2P model. Camera, microphone and speaker access is explicit, permission-gated and user initiated. No silent recording, unsolicited scanning, arbitrary remote execution or credential exchange is part of the Apple boundary.

## References

Apple's `xcodebuild`/Xcode build system is the authoritative compiler/archive path. fastlane is MIT-licensed open-source automation and delegates iOS archiving/export to Xcode tooling.
