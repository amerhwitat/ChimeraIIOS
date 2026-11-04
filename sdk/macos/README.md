# macOS application cross-development

Chimera ships first-party templates, build integration and an honest toolchain report. It does not ship Xcode, Apple frameworks, a macOS runtime or a redistributable Apple SDK.

## Dependencies included in the live ISO
- LLVM/Clang, clangd, CMake, Ninja, LLD and pkg-config.
- GNU Objective-C compiler/runtime development support and GNUstep Base for host-side Objective-C development.
- The CMake Darwin cross toolchain template and Objective-C Foundation app example.

## External Darwin requirements
- An independently installed osxcross-compatible Darwin compiler (for example, `o64-clang` and `o64-clang++`).
- A developer-supplied macOS SDK whose license permits the intended use. Set `MACOS_SDKROOT` to its root.
- Swift compilation is reported when `swiftc` exists, but a Swift compiler alone does not supply Apple SDK frameworks or a Darwin linker.

Run `tools/build-macos-sdk.sh` to create `macos-sdk-report.json`. Missing SDK/toolchains remain blocked/skipped. If an SDK is present, inspect its exact license yourself. Only after that review, explicitly set `MACOS_SDK_LICENSE_REVIEWED=1` and run the helper to attempt the Objective-C CMake sample. The helper records `built` or `failed`; discovery alone is never a successful build.

Use `sdk/macos/templates/DarwinCross.cmake` with CMake. Configure clangd and CMake Tools in a bundled editor/IDE for the selected osxcross compiler and compilation database. Xcode is macOS-only and is not included or claimed to run on Chimera.

## ISO redistribution policy
The ISO includes the report, first-party templates, example source and helper only. It never copies Apple SDK frameworks, headers, runtimes or Xcode binaries. Do not relax this policy unless the exact SDK license explicitly permits redistribution and that decision is reviewed and documented.
