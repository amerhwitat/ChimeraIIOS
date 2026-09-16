# Chimera II OS

Chimera II OS is a cross-language research operating-system and application platform centered on the Koronos microkernel, wide-register C8192/R8192 research ISA, multidimensional cognition, portable tooling, trusted peer networking and separate Mobile Microkernel/application stacks.

## Aurora Wayland Glass — world language desktop

Aurora now defines a Unicode/CLDR/BCP-47 language and writing-system boundary for the entire desktop. It supports dynamic language/locale discovery rather than a fixed hand-written list, with explicit language + script + region resolution, Unicode BiDi, LTR/RTL/mixed-direction layouts, script-aware shaping/font fallback, multilingual keyboards, IMEs, Wayland text-input/input-method integration, and localized dates, numbers, currencies, units, collation and plural rules. See `desktop/localization/world_language_support.json`, `desktop/localization/README.md` and `desktop/localization/update_cldr_languages.py`.

RTL support applies to Aurora panels, menus, dialogs, settings, notifications, terminal, file manager, package manager, games, Retro Center, developer tools, accessibility, login/lock screens and window decoration. Mixed Arabic/Latin text, numerals, paths, URLs, cursor movement, selection and clipboard are treated as BiDi text rather than manually reversed strings. Language switching is designed to occur without restarting applications. Translation, speech, handwriting and braille are provider boundaries; proprietary services/assets remain opt-in and license-aware.

Unicode distinguishes scripts from languages, so Aurora combines Unicode scripts with BCP-47 language identifiers and CLDR locale data. This allows multiple scripts per language and multiple languages per script, including Serbian Latin/Cyrillic and Japanese Han/Hiragana/Katakana combinations. The detailed CLDR inventory is refreshable during builds instead of becoming stale. Wayland text-input protocols provide the UTF-8 composition and input-method boundary.

## Complete source-code citation index

| Area | Source |
|---|---|
| Boot / Spit Fire | [boot and firmware trees](.) |
| Jasper boot manager | [boot-manager sources](.) |
| Koronos microkernel | [kernel sources](.) |
| Spotnik networking | [networking sources](.) |
| Application network module | [`network/ApplicationNetworkModule.md`](network/ApplicationNetworkModule.md) |
| Aurora desktop | [`desktop/`](desktop/) |
| Aurora world-language support | [`desktop/localization/`](desktop/localization/) |
| Open-source service compatibility | [`services/`](services/) |
| Open-source application catalog | [`applications/`](applications/) |
| Open-source provenance | [`opensource/`](opensource/) |
| RISC/CISC ISA catalog | [`isa/`](isa/) |
| Universal architecture registry | [`isa/world_architectures.json`](isa/world_architectures.json) |
| Universal execution API | [`execution/universal_execution_api.json`](execution/universal_execution_api.json) |
| Retro computer registry | [`emulation/retro_systems.json`](emulation/retro_systems.json) |
| Unix/Linux command registry | [`services/unix_command_registry.json`](services/unix_command_registry.json) |
| Linux package repositories | [`packages/repositories.json`](packages/repositories.json) |
| Aurora application registry | [`desktop/aurora_app_registry.json`](desktop/aurora_app_registry.json) |
| Nucleus / Hive / Kore / Aegis / CEF | [system service trees](.) |
| RegisterN / C8192 / R8192 | [ISA/register sources](.) |
| Quantum computing | [`quantum/`](quantum/) |
| Multidimensional / perspective mathematics | [`multidimensional/`](multidimensional/) |
| Neural reasoning | [`neural/`](neural/) |
| Voice / speech | [`voice/`](voice/) |
| Hardware / GPU / driver registry | [`drivers/`](drivers/) |
| Java hardware/driver + desktop layer | [`java/`](java/) |
| Rust implementation | [`rust/ChimeraIIOS/`](rust/ChimeraIIOS/) |
| Mobile Microkernel | [mobile sources](.) |
| P2P | [protocol sources](.) |
| Automation / ISO / tests | [tools, build and test trees](.) |
| Complete tracked repository | [full source tree](.) |

## Universal ISA, computer and OS registry

`isa/catalog.json` remains the canonical instruction catalog, while `isa/world_architectures.json` is the broader architecture/OS/emulator registry. The normalized instruction model separates architecture, mnemonic, operands, encoding, flags, memory effects, control flow and privilege. The registry is provenance-first: it indexes authoritative specifications and examples rather than copying proprietary manuals. It is designed to drive future assembler/disassembler, emulator, debugger and binary-analysis adapters.

## Universal execution API

`execution/universal_execution_api.json` defines the common execution boundary: decoder → operand resolver → semantic engine → machine state → memory bus → device bus → OS/ABI boundary. C/C++, Rust, Python, Java, C#, Kotlin, Swift, TypeScript, Dart and Go adapters can bind to the same model. Privileged execution is sandboxed by default and downloaded code is never executed automatically.

## Aurora Wayland Glass

`desktop/aurora_app_registry.json` makes Aurora the common presentation layer for Settings, Package Center, Terminal, ISA Explorer, CPU Emulator, Retro Center, BizX, BizXtreme, Network Center and Developer Center. Wayland is the native Linux compositor boundary; legacy personalities remain behavioral compatibility profiles rather than copied proprietary binaries.

## Retro Computer Center

`emulation/retro_systems.json` establishes a single Aurora registry for Amiga, Commodore, Atari, Apple, Sinclair, Acorn, Amstrad, PC/DOS, arcade and console families. Existing Amiga browser work under `nlp/Amiga` is the first integrated profile. The design uses adapter boundaries for SAE/UAE/vAmigaWeb, QEMU, MAME, libretro and other compatible projects. ROMs, BIOS images and commercial games remain user-supplied or properly licensed.

## Linux / Unix commands and package repositories

`services/unix_command_registry.json` catalogs filesystem, text, process, shell, network, archive, storage, system, development and package utilities. `packages/repositories.json` records package repository families including Debian, Ubuntu, Fedora, openSUSE, Arch, Alpine, Gentoo, FreeBSD, Homebrew and Flathub, plus upstream Linux/kernel, GNU, freedesktop, Wayland, Mesa, QEMU and libretro references. Package installation must enforce signatures, checksums, licenses, dependencies, architecture compatibility, permissions and rollback policy.

## BizX and BizXtreme integration

BizX and BizXtreme contain `CHIMERA_INTEGRATION.json` manifests. Aurora exposes them as applications while Koronos/Chimera APIs provide networking, execution, package, settings, retro and system-service boundaries. Existing language implementations remain language-specific adapters; licenses and provenance remain authoritative.

## Cross-repository Chimera integration

Relevant repositories expose `CHIMERA_INTEGRATION.json` contracts so the OS can discover capabilities without copying entire source trees into the kernel. This includes `BizX`, `BizXtreme`, `nlp`, `CPU4096`, `CPU4096Simulator`, `general`, `PDFreaderPY`, `eth-key-check`, `keygen`, `bruteforce`, `test`, `VanG`, and the project website.

## Unified build, dependency, packaging and installer automation

`tools/build/orchestrator.py` is the cross-platform automation entry point, with POSIX shell, Windows CMD and PowerShell wrappers under `scripts/`. Use `doctor`, `deps`, `configure`, `build`, `test`, `package`, `install`, `clean`, or `all`. The build manifest tracks C/C++/ASM, Rust, Python, Node.js/TypeScript, Java, .NET/C#, Kotlin, Swift and Dart toolchains.

## Application networking

`network/ApplicationNetworkModule.md` defines Client, Server, Host, P2P and Hybrid modes. Spotnik remains the OS networking boundary while application sessions can select QUIC/TLS, TCP/TLS, WebRTC, WebSocket/WebTransport and libp2p adapters.

## Open-source Linux / Windows / macOS services and applications

Chimera II has a provenance-first compatibility layer for open-source services, desktop technologies and free applications. Linux systemd/D-Bus/NetworkManager/PipeWire/CUPS/udev/Samba, Windows Service Control Manager/Task Scheduler/PowerShell/Windows Terminal/WSL/Windows App SDK, and macOS launchd/POSIX/CoreAudio/WebKit/printing boundaries are represented through platform adapters. Proprietary binaries are not redistributed and downloaded artifacts are not executed automatically.

## Neural multidimensional reasoning

The `neural/` layer combines weighted evidence, disagreement-aware confidence, observer/perspective transforms and multidimensional feature overlays. The 128D profile remains an experimental computational semantic representation, not a claim about the number of physical dimensions.

## Voice and speech

`voice/` provides a cross-platform TTS/STT boundary for Windows, Linux/Unix and Apple providers. The core does not silently upload text or audio and does not bundle proprietary speech engines.

## Quantum computing research layer

The `quantum/` tree provides a portable CPU-baseline state-vector simulator, QFT/gate primitives, C ABI, versioned `CHMQ-1` circuit IR and language adapters. External quantum services remain opt-in.

## Hardware, GPU and driver compatibility

The `drivers/` layer contains hardware capability and protocol registries. Chimera can discover, acquire, verify and stage Linux and Windows driver candidates through a security-first broker and never silently loads downloaded code or bypasses Secure Boot/signature enforcement.

## Licensing and provenance

Chimera II OS is distributed under GNU GPL v3 or later unless a subcomponent explicitly identifies a compatible third-party license. Third-party dependencies and assets retain their original licenses. Open-source compatibility, emulator and ISA layers record upstream provenance and license expressions rather than assuming all upstream projects can be relicensed as GPL.
