# Apple Platform Expansion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans (recommended) to implement this plan task-by-task.

**Goal:** Add iOS/iPadOS and macOS source/build infrastructure across the Chimera portfolio, producing IPA/XCArchive/XCFramework artifacts on macOS while retaining Android and desktop implementations.

**Architecture:** Kotlin Multiplatform supplies shared portable logic where Kotlin already exists; native Swift/Xcode shells provide Apple UI and platform APIs. xcodebuild is authoritative; fastlane is optional automation. Windows/Linux scripts prepare or dispatch builds but never claim to compile Apple binaries without macOS/Xcode.

**Tech Stack:** Kotlin Multiplatform/Kotlin-Native, SwiftUI, Swift Package Manager, Xcode/xcodebuild, fastlane, Bash, PowerShell, CMD, GitHub Actions macOS runners.

**Spec:** Approved Apple architecture from the design discussion preceding this plan.

## Global Constraints
- iOS device target: `iosArm64`; Apple-Silicon simulator: `iosSimulatorArm64`.
- iOS compilation/IPA export requires macOS + Xcode.
- Signing certificates, provisioning profiles, Apple credentials and private keys never enter Git.
- Existing Android/desktop implementations remain intact.
- Camera/microphone require explicit runtime permission and user action.
- Existing authenticated P2P/128D boundaries remain; no unsolicited scanning, arbitrary remote execution, credential exchange or executable payload transfer.
- Third-party source/assets retain their licenses.

### Task 1 — Portfolio Apple tooling
Create `docs/APPLE_PLATFORM_PORTFOLIO.md`, `tools/apple/install-apple-toolchain.sh`, `tools/apple/build-apple-portfolio.sh`, `tools/apple/build-apple-portfolio.ps1`, `tools/apple/build-apple-portfolio.cmd`, and `tools/apple/README.md`. The shell installer checks macOS/Xcode/Swift/Ruby and optionally fastlane. The build script searches repositories for Apple projects/packages and archives/exports with xcodebuild. Windows wrappers clearly delegate to macOS/CI.

### Task 2 — Reusable Apple template
Create `apple/README.md`, `apple/Package.swift`, `apple/Shared/README.md`, `apple/iOS/README.md`, `apple/macOS/README.md`, `apple/scripts/{build-ios,archive-ios,export-ipa,build-macos,clean-apple}.sh`, and `apple/Config/ExportOptions.plist.example`. Standardize `build/ipa`, `build/archive`, and `build/DerivedData` outputs.

### Task 3 — Kotlin Apple boundary
Create `kotlin/apple/README.md`, `kotlin/apple/SharedKit.kt`, `kotlin/apple/BUILD_XCFRAMEWORK.md`, and `kotlin/apple/build-xcframework.sh`. Expose a stable Kotlin/Native framework/XCFramework boundary for Swift using `iosArm64` and `iosSimulatorArm64`.

### Task 4 — Portfolio propagation
Apply Apple scaffolding to BizX, BizXtreme, CPU4096, CPU4096Simulator, PDFreaderPY, nlp, eth-key-check, bruteforce, keygen, test, general, VanG, and amerhwitat.github.io. Each gets `apple/` build/docs files and a README update; Kotlin repos also get `kotlin/apple/README.md`. BizX/BizXtreme document real-time media/communications; CPU repos document wide-register/ISA boundaries; nlp/PDFreaderPY document native-safe service boundaries; crypto repos preserve safe research/owner-authorized boundaries.

### Task 5 — macOS CI
Create `.github/workflows/apple-build.yml` in applicable repositories. Use a macOS runner, validate source/packages, build simulator targets, and archive/export IPA only when signing configuration exists. Upload non-secret artifacts and never print credentials.

### Task 6 — Verification
Create `docs/APPLE_BUILD_VERIFICATION.md`. Validate shell syntax, plist XML, Package.swift on macOS, and existing Android/Kotlin builds. Record that IPA binaries are not claimed as built until a macOS/Xcode runner executes archive/export.

## Review checklist
- Every requirement in the approved Apple design maps to Tasks 1–6.
- No task relies on placeholders or hidden signing secrets.
- Artifact paths, target names, and platform boundaries are consistent.
