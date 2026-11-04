macOS application cross-development

This integration supplies project scaffolding and host-toolchain discovery; it does not provide Xcode, Apple frameworks, a macOS runtime, or a redistributable Apple SDK.

Requirements: LLVM/Clang with Objective-C support, clangd, CMake, Ninja, an independently installed osxcross-compatible Darwin compiler, and a developer-supplied macOS SDK whose license permits its use.

Set MACOS_SDKROOT to the SDK root and run tools/build-macos-sdk.sh. Its report distinguishes an absent SDK from detected SDK files requiring license review. Neither blocked nor review-required is a successful application build.

Use sdk/macos/templates/DarwinCross.cmake with CMake. Configure clangd and CMake Tools in an installed editor/IDE for the selected osxcross compiler and compilation database. Xcode is macOS-only and is not included or claimed to run on these Linux editions. ISO policy: distribute only first-party templates, wrappers and reports; never package Apple SDK contents unless redistribution is expressly permitted.
