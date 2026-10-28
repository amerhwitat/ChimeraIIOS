# macOS SDK and application compatibility

## Supported profiles

| Profile | Purpose | Current guarantee |
|---|---|---|
| `apple-macos` | Build a macOS executable with Apple's SDK | Only on Apple-branded macOS hardware with a locally installed, licensed SDK |
| `portable-gnustep` | Build portable Objective-C/Foundation-style apps | Requires Clang and GNUstep Base; this is not a macOS SDK |
| `portable-posix` | Run a native ELF/portable app with compatibility environment variables | Only the app's existing POSIX/runtime dependencies are supported |
| `darwin-mach-o` | Run an existing macOS Mach-O executable | NOT IMPLEMENTED / NOT RELEASE-READY; the launcher rejects it unless an explicitly supplied runtime exists |

## Install or verify Apple's macOS SDK

The repository never vendors or downloads Apple SDK files. Use Apple's installer on a compatible Mac:

```sh
bash tools/macos-compat/install-sdk.sh install
bash tools/macos-compat/install-sdk.sh check
bash tools/macos-compat/check-sdk.sh apple-sdk
```

The `install` mode invokes `xcode-select --install` and then exits for the user to complete Apple's interactive installation and license prompts. It does not bypass the agreement or claim the SDK is ready until a later check finds both `xcrun` and a valid macOS SDK. If full Xcode is installed, select it using Xcode's Locations settings or `xcode-select --switch /Applications/Xcode.app/Contents/Developer` (adjust the path to the actual installation).

On Linux/Windows, the install command fails closed with an explanation. Install the portable GNUstep toolchain through the host package manager instead; GNUstep is not the Apple macOS SDK. ISO builds do not need Apple SDK contents.

Apple references: [Xcode and Apple SDKs Agreement](https://www.apple.com/legal/sla/docs/xcode.pdf), [installing Xcode Command Line Tools](https://developer.apple.com/documentation/xcode/installing-the-command-line-tools/).

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
