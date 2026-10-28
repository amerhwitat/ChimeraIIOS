# macOS integration and Apple SDK location

macOS applications use native SwiftUI/AppKit/Xcode targets where a desktop shell is required. Shared Swift Package and Kotlin/Native boundaries keep portable protocol/state logic separate from Apple UI.

## Where the macOS SDK lives

The Apple **MacOSX SDK is supplied by Xcode or the Xcode Command Line Tools; it is not vendored in this repository**. On a macOS build host, ask the active developer toolchain for the authoritative path:

```sh
xcode-select -p
xcrun --sdk macosx --show-sdk-path
```

Common locations (the exact versioned directory can vary):

- Full Xcode: `/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX.sdk`
- Command Line Tools: `/Library/Developer/CommandLineTools/SDKs/MacOSX.sdk`

Use the path returned by `xcrun` rather than hard-coding a versioned SDK path. If the command fails, install Xcode or the Command Line Tools on a supported macOS host and select the intended developer directory with `sudo xcode-select --switch /Applications/Xcode.app/Contents/Developer`.

## Repository paths

- Chimera II OS native macOS integration: `apple/macOS/`
- macOS build wrapper: `apple/scripts/build-macos.sh`
- Chimera's portable cross-platform SDK (not Apple's MacOSX SDK): `sdk/`

For OctavianOS, these Chimera paths are mirrored under `vendor/chimera-ii-os/source/`.

## Build a macOS target

Run on macOS with Xcode installed, providing an existing Xcode project or workspace and scheme:

```sh
PROJECT=path/to/App.xcodeproj SCHEME=App apple/scripts/build-macos.sh
# or
WORKSPACE=path/to/App.xcworkspace SCHEME=App apple/scripts/build-macos.sh
```

The script builds into `build/DerivedData`. The Linux SDK CI performs cross-target Objective-C syntax/object checks, but that is **not** equivalent to building and running a native Xcode application with the Apple SDK. A native macOS build must be validated on a macOS runner or host.
