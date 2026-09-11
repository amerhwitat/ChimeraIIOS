# ISO-Tool

Chimera II OS ISO/image build orchestrator with native Windows/MSVC, .NET and Python implementations.

## Source acquisition

The tool accepts GitHub/Git repository URLs, direct ZIP/TAR source archives, local archives, and local directories. Git sources are cloned with submodules. Archives are downloaded, SHA-256 recorded, safely extracted, and scanned. Absolute/traversal archive paths and symbolic/hard links are rejected.

The GUI provides a source textbox plus Browse Source and GitHub controls. It can scan the source before building and records source provenance in the build manifests.

## Build and application pipeline

`acquire → verify → scan → application discovery → dependency graph → deterministic build plan → registered build adapter → artifact staging → ISO/IMG mastering`

Registered adapters cover CMake, Make, Meson, Cargo, npm, Maven, Gradle, .NET and Autotools when available. AI/RNN/LLM planning remains advisory; deterministic build/dependency rules remain authoritative.

Application discovery reports required/recommended/optional entries from Python, Node.js, Rust, Java, .NET, Go, CMake and Make manifests. Available package managers include APT, DNF, Zypper, pacman, apk, XBPS, Portage, Homebrew, Flatpak, Snap, WinGet, Chocolatey and Scoop.

Package installation is never implicit. It requires explicit `--yes` authorization and registered commands; arbitrary downloaded scripts are not executed.

## Output controls

The Python GUI provides independent output fields for:

- build root
- final ISO file
- IMG file
- boot-image directory
- executables/libraries

The normal output hierarchy is:

```text
<output>/
├── sources/
├── knowledge/
├── build/
├── staging/
├── iso/
├── img/
├── boot-images/
├── binaries/{executables,libraries}/
├── manifests/
└── logs/
```

ISO mastering uses the existing xorriso/xorrisofs or Oscdimg backends. The selected IMG output is an ISO9660-compatible image copy; raw physical-disk operations are outside ISO-Tool.

## Chimera II integration

The staged ISO hierarchy preserves `/src`, `/bin`, `/lib`, `/applications/linux`, `/applications/windows`, `/boot`, `/efi`, `/tools`, `/docs`, and `/metadata` where applicable. Spit Fire and other Chimera II boot artifacts are staged according to the selected boot profile.

## Security and reproducibility

Downloaded archives are hashed. Build manifests record source, toolchain, build-system, artifact, and output information. Imported boot sectors are inert input and are never executed by ISO-Tool. Missing tools and failed build adapters are reported instead of being represented as successful builds.
