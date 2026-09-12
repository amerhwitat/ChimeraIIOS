# iOS/iPadOS integration

Use a native SwiftUI/Xcode application target for the Apple UI and platform APIs. Existing Kotlin logic can be exposed as a Kotlin/Native framework or XCFramework.

Device architecture: `arm64` / KMP target `iosArm64`.
Apple-Silicon simulator: `arm64` / KMP target `iosSimulatorArm64`.

Permissions for camera/microphone are requested only when the user activates the relevant feature. Network communications reuse the authenticated application protocol and do not enable arbitrary remote execution.
