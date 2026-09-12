# Repository Portfolio — 2026-09

This document summarizes the current role and build entry point for the Amer Hwitat repository family after the cross-language build-orchestration work.

| Repository | Primary role | Main implementation tracks | Start/build |
|---|---|---|---|
| `ChimeraIIOS` | Operating-system, microkernel, ISA, desktop/mobile, database and trusted-node research | C/C++, ASM, Python, .NET, Java, Node/web | `cpp/build-msvc.bat`, `cpp/build-gcc.sh`, root CMake |
| `nlp` | Ancient-script OCR, transliteration, translation, RNN/LLM and database platform | Python, C++, Rust, TypeScript, .NET/web | `build-tools/build.bat` |
| `BizX` | Business/game application with language-separated desktop and runtime implementations | C++, C#, Node, Java, Python, JS/TS | `build-tools/build.bat` |
| `BizXtreme` | Extended game/WebGL/Unity/Chimera integration | C++, C#, Node, Java, Python, JS/TS, WebGL | `build-tools/build.bat` |
| `PDFreaderPY` | PDF/document ingestion and evidence extraction | Python | PyInstaller/build-tools |
| `CPU4096` | Wide-register CPU research and deterministic workload vectors | C++, Java, Node, Python | `cmake -S cpp -B cpp/build` |
| `CPU4096Simulator` | Browser/Node Chimera CPU and system simulator | Node.js, JavaScript | `npm ci && npm test` |
| `test` | Host-side Chimera integration/conformance platform | Python, Node integration | `python3 start_chimera.py` |
| `keygen` | Java/Koronos 128D and interoperability track | Java, C++, Node, Python vectors | `mvn test` |
| `eth-key-check` | Safe owner-authorized Ethereum/crypto verification | C++, Java, Node, Python | repository build orchestrator |
| `bruteforce` | Safe cryptographic research/vector interoperability | C++, Java, Node, Python | repository build orchestrator |
| `general` | Shared/general experiments and integration material | capability-dependent | repository build orchestrator |
| `VanG` | Project-family repository with capability-detected build surface | capability-dependent | repository build orchestrator |
| `amerhwitat.github.io` | Public web/documentation and research index | HTML/JS/Node where applicable | web build/deploy workflow |

## Chimera II OS accomplishments

- Separate **Computer Edition / Koronos** and **Mobile Microkernel** architecture.
- Universal ISA and `RegisterN`/C8192/R8192 research layers.
- Architecture-neutral memory bus and CPU/toolchain registries.
- Neural/trusted-node and Nucleus database architecture.
- ISO-Tool with language-specific implementations and Visual C++ tooling.
- Dedicated mobile `Flash-Tool` for image inspection, verification and safe dry-run fastboot command generation.
- Native C/C++ build layer isolated under `cpp/`.
- Visual Studio 2022 solution/projects for the native computer targets.
- Code::Blocks GCC projects/workspace.
- GNU CMake build path retained as the cross-platform source of truth.
- Windows batch, PowerShell and POSIX shell automation.
- CI workflows for multi-OS verification.

## Build philosophy

The build layer detects capabilities rather than assuming every repository contains every programming language. A target is reported as `PASS`, `FAIL` or `SKIPPED` with dependency, compilation, linking, testing and artifact information.

PyInstaller packaging is target-OS native; an executable intended for Windows is packaged on Windows, Linux on Linux and macOS on macOS. GitHub Actions provides Windows, Linux and macOS runners and matrix execution for repeatable verification.

## Verification status

A repository configuration or project file is not treated as proof that its executable successfully builds. Native compilation is only marked successful after a corresponding local or GitHub Actions build has completed successfully. This distinction is preserved in CI reports.
