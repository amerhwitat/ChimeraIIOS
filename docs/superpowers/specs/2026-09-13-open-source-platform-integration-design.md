# Open-Source Platform Integration Design

## Goal
Integrate open-source Linux, Windows and Apple/Darwin-adjacent services, desktop technologies and free/open-source application compatibility into Chimera II OS without copying proprietary binaries or collapsing upstream licensing boundaries.

## Scope

The integration covers three layers:

1. **Services compatibility** — service lifecycle, IPC, networking, audio/media, printing, device discovery, logging, scheduling, package/service metadata, shell/terminal and interoperability boundaries.
2. **Desktop/application compatibility** — Aurora adapters for Linux X11/GTK/Qt/Wayland, Windows Win32/WinUI/WPF/WinForms/terminal ecosystems, and macOS AppKit/SwiftUI/WebKit-era interfaces where technically and legally appropriate.
3. **Open-source application catalog** — manifests and compatibility launch boundaries for file managers, terminals, editors, office/document tools, image/PDF tools, media players, browsers/web engines, archives, calculators, system monitors, disk/network/developer/accessibility/backup tools.

The repository will not vendor entire Linux distributions, Windows source trees, proprietary Windows/macOS binaries, or arbitrarily scrape and execute third-party code. Large upstream projects are represented by versioned source manifests, SPDX/license metadata, acquisition/build recipes and clean-room Chimera adapters. Source may be vendored only when its upstream license and repository size make that appropriate.

## Architecture

`upstream source -> provenance/license manifest -> acquisition/build boundary -> Chimera adapter -> common capability ABI -> Aurora/Koronos service/application runtime`

The canonical registry is `opensource/sources.json`. Service definitions live under `services/`; application compatibility metadata lives under `applications/`; shared capability schemas live under `opensource/schema/`; language adapters live under the existing language directories and the new service/application subtrees.

The compatibility API is capability-oriented rather than OS-emulation-oriented. A Linux/systemd-like service and a Windows SCM service can both implement the same Chimera service lifecycle while retaining platform-specific backends.

## Supported language surfaces

C, C++, Rust, Python, Java, C#, Kotlin, Swift, TypeScript/JavaScript and Dart receive registry/schema bindings and representative service/application adapters. Upstream projects remain in their native implementation language; the language matrix does not require rewriting every upstream application in every language.

## Service families

Linux-inspired: systemd-style lifecycle, D-Bus IPC, NetworkManager-compatible networking, PipeWire/ALSA media, CUPS/IPP printing, udev-style device discovery, Samba-compatible sharing, timers/cron, structured logging and package/service metadata.

Windows-inspired: Service Control Manager lifecycle, Task Scheduler boundary, PowerShell/terminal integration, Win32/WinRT application-service boundary, Windows Terminal/console compatibility, WSL interoperability and notifications/background-task concepts.

Apple/Darwin-inspired: launchd/POSIX lifecycle concepts, CoreFoundation/AppKit boundary, WebKit integration boundary and Swift/SwiftUI adapter surface. Proprietary Apple frameworks remain external platform capabilities rather than redistributed code.

## Application families

The initial catalog defines compatibility records for: file manager, terminal, text/code editor, office/document suite, image viewer/editor, PDF viewer, media player, browser/web shell, archive manager, calculator, system monitor, disk/partition tools, network tools, developer tools, accessibility tools, screenshot/recording, backup/synchronization and package management.

Each record contains upstream project, source URL, license/SPDX expression, platform support, native language, build system, compatibility status, sandbox/security requirements and whether the source is vendored, fetched, wrapped or reference-only.

## Licensing and provenance

Every external source entry must preserve upstream attribution and license information. GPL/LGPL/BSD/MIT/Apache and other licenses are recorded exactly as provided by upstream. A compatible license does not automatically permit relicensing upstream code as GPL. SPDX identifiers, source revisions and modification notes are mandatory for vendored or patched sources.

## Security and execution policy

Acquisition, verification, staging and execution are separate operations. No downloaded service, driver, package or application is silently executed or installed. Checksums/signatures are verified when supplied by upstream; untrusted artifacts are quarantined. Secure Boot, driver-signature and platform security boundaries are not bypassed.

## Testing

CI validates JSON schemas/manifests, license/provenance completeness, registry parsing, platform capability selection, service lifecycle state transitions and application compatibility metadata. Language adapters receive syntax/compile/unit tests where toolchains are available. CI uses Linux GCC/Clang, Windows MSVC/clang-cl/MinGW, macOS Clang/Swift and the repository's existing Rust/Java/Python/C#/Kotlin/Node/Dart paths.

## Documentation

The implementation updates the root README and affected language READMEs and adds:

- `docs/OPEN_SOURCE_INTEGRATION.md`
- `docs/SERVICES_COMPATIBILITY.md`
- `docs/APPLICATION_COMPATIBILITY.md`
- `docs/SOURCE_PROVENANCE.md`
- `docs/superpowers/plans/2026-09-13-open-source-platform-integration.md`

## Source references

The design is informed by official upstream documentation and repositories, including Linux/freedesktop service projects, Microsoft's open-source Windows Terminal/Windows developer stack, and Apple's open-source project catalog/WebKit. WebKit explicitly publishes source in C++, Objective-C/Objective-C++, Swift and Python and uses BSD-style/LGPL licensing; Windows Terminal publishes its source under MIT; Microsoft documents current Windows App SDK/SDK development; Apple maintains a public open-source project catalog. These references are source/provenance inputs, not permission to redistribute proprietary platform components.
