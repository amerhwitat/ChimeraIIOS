# Chimera II OS Kotlin Mobile

Android Kotlin implementation for the Chimera II OS mobile application boundary. It is separate from the native C/C++/ASM computer edition and from the dedicated `Mobile Microkernel` source tree.

## Architecture
- Kotlin 2.4.20 + Android Gradle Plugin 9.4.0 + SDK 36 + JDK 17.
- Native Android entry point under `app/`.
- Cleartext traffic disabled by default.
- Designed to consume the Mobile Microkernel service boundary, Koronos scheduling/service contracts, 128D state representation, and authenticated opt-in P2P fabric.
- Future Kotlin Multiplatform work can share business/state logic with iOS while retaining platform-specific entry points.

This is an application layer, not a replacement for the bootloader, kernel, or native hardware-facing code.
