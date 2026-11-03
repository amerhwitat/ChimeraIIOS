# Third-party SDK and toolchain policy

This directory stores provenance, version locks, build recipes and license metadata.
It is not a dump of proprietary vendor SDKs.

- Open-source toolchains may be fetched by a pinned version and verified checksum.
- Apple macOS/iOS SDK frameworks and headers are proprietary/licensed Apple materials.
  Do not commit or redistribute them. A developer may point the build to an
  independently licensed local SDK with `APPLE_SDKROOT`; otherwise the target is
  reported as unavailable and Apple-specific code is not compiled.
- Windows SDK/WDK and Android NDK are likewise staged only when their licenses
  permit local use and their paths are explicitly configured.
- Cross-compilers are build-host tools; target binaries must be architecture-tagged.

See `sdk/third-party-sdk-manifest.json` for the supported external toolchain contract.
