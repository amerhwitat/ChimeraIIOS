# Git Source, Archive, Application, and Output Pipeline Design

ISO-Tool accepts GitHub/Git URLs, direct ZIP/TAR archives, local archives, and local directories. Acquisition records source provenance and archive SHA-256. Archive extraction rejects traversal and links.

The scanner reads source, documentation, manifests, build descriptions, linker scripts, assembly, C/C++, Rust, Go, Java, Python, Node, C#, Fortran, Swift, Make, CMake, Meson, Autotools, Ninja, Cargo, npm, Maven/Gradle, and Visual Studio files while excluding ordinary VCS/cache/build/vendor trees unless requested.

Application discovery reports required/recommended/optional/unavailable components and available package managers. Installation is never performed during discovery and requires explicit `--yes` authorization plus a registered package-manager command.

The pipeline is: acquire -> verify -> extract -> scan -> application discovery -> dependency graph -> deterministic build plan -> registered build adapters -> artifact staging -> filesystem merge -> ISO/IMG mastering -> verification.

CMake and other native build systems remain authoritative; AI/RNN/LLM components can annotate plans but cannot bypass policy. Users can independently select ISO, IMG, boot-image, binary/library, and build-root destinations.
