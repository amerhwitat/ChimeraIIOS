# Chimera Mobile Communications and APK Automation

## Scope
All Kotlin mobile applications use a common communication boundary for synchronized text chat, voice sessions and camera/video capability detection. BizX and BizXtreme are the first-class application integrations; the same contract is available to CPU simulators, NLP/document applications, crypto research applications and integration tools.

## Media
Android microphone/camera permissions are declared but should be requested at the point of user action. WebRTC is used as the real-time media transport boundary. Current Maven coordinate: `io.github.webrtc-sdk:android:150.7871.01`.

## Conversation synchronization
Events contain conversation ID, sender ID, sequence number and SHA-256 payload integrity. Duplicate/out-of-order events are rejected locally. Network authentication remains the responsibility of the existing authenticated P2P/session layer.

## Build automation
`tools/mobile/install-android-sdk.ps1` provisions the Android CLI/SDK when absent. `build-portfolio-mobile.ps1`, `.cmd`, and `.sh` clone/update the related repositories, discover Kotlin Android projects, and invoke debug/release Gradle builds.

The scripts never embed credentials and never execute arbitrary remote payloads.
