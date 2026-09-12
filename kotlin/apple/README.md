# Kotlin/Native Apple boundary

The Apple clients can consume shared Kotlin code through Kotlin/Native frameworks or XCFrameworks.

Recommended targets:

- `iosArm64` — physical iPhone/iPad devices.
- `iosSimulatorArm64` — Apple-Silicon simulator.

Use the repository's existing KMP Gradle project to produce the framework. `build-xcframework.sh` intentionally requires an explicit `KMP_XCFRAMEWORK_TASK` so it cannot guess the wrong Gradle module.

Swift/Xcode remains responsible for the final application target, signing, archive and IPA export.
