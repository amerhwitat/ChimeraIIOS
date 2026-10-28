# macOS SDK and application compatibility

## Supported profiles

| Profile | Purpose | Current guarantee |
|---|---|---|
| `apple-macos` | Build a macOS executable with Apple's SDK | Only on Apple-branded macOS hardware with a locally installed, licensed SDK |
| `portable-gnustep` | Build portable Objective-C/Foundation-style apps | Requires Clang and GNUstep Base; this is not a macOS SDK |
| `portable-posix` | Run a native ELF/portable app with compatibility environment variables | Only the app's existing POSIX/runtime dependencies are supported |
| `darwin-mach-o` | Run an existing macOS Mach-O executable | NOT IMPLEMENTED / NOT RELEASE-READY; the launcher rejects it unless an explicitly supplied runtime exists |

## Why the SDK is not vendored

Apple's Xcode/SDK terms restrict use of Apple software and SDKs. Do not copy proprietary SDK headers, frameworks, binaries, or SDK archives into either repository, ISO, CI artifact, or public app catalog. On a licensed Apple Mac, install Xcode/Command Line Tools and let `xcrun --sdk macosx --show-sdk-path` locate the SDK locally. The scripts deliberately refuse Apple SDK builds on non-macOS hosts.

References: [Apple Xcode and SDK agreement](https://www.apple.com/legal/sla/docs/xcode.pdf), [Apple Developer Program License Agreement](https://developer.apple.com/support/terms/apple-developer-program-license-agreement/).

## Build

Check the host and available toolchain:

```sh
bash tools/macos-compat/check-sdk.sh auto
```

Build on licensed macOS hardware:

```sh
bash tools/macos-compat/build-app.sh apple-macos src/main.m build/macos/my-app
```

Build a portable Foundation-style Objective-C app on a GNUstep-enabled host:

```sh
bash tools/macos-compat/build-app.sh portable-gnustep src/main.m build/portable/my-app
```

Run a compatible native/portable application:

```sh
bash tools/macos-compat/run-app.sh build/portable/my-app [arguments...]
```

A successful compile is not proof that the app runs on ChimeraIIOS or OctavianOS. The kernel/runtime must provide the needed executable format, syscalls, libraries, GUI APIs, graphics/input integration, and security semantics. The current wrapper does not implement Darwin syscalls, Mach-O loading, Cocoa/AppKit, Metal, CoreGraphics, launch services, code signing, or macOS sandbox semantics. It refuses Mach-O binaries instead of falsely reporting compatibility.

## Implementation roadmap / missing links

1. Keep proprietary SDK use local to licensed Apple hardware; never redistribute it.
2. Add open-source portable Objective-C support through GNUstep where available.
3. Add a compatibility manifest per app: source availability, target ABI, binary format, framework dependencies, GUI dependencies, license, build result, runtime result.
4. Implement and independently test Mach-O parsing/loader, Darwin syscall/ABI mapping, dynamic linking, Foundation/AppKit alternatives, graphics/input adapters, process/sandbox semantics, and app signing policy before claiming native macOS app compatibility.
5. Validate each application separately on both OSes; mark unsupported apps blocked instead of silently falling back.

## Release-gate status

This layer is scaffolding and honest routing, not a full macOS compatibility subsystem. Do not promote an app or publish an OS release based only on a successful toolchain check.
