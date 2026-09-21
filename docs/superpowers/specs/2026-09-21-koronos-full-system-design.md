# Koronos Kernel & Chimera II OS Full-System Implementation Design

Date: 2026-09-21
Repository: amerhwitat/ChimeraIIOS
Status: Proposed architectural implementation

## 1. Purpose

Turn the existing Chimera II research scaffolding into a staged, reproducible software platform centered on the Koronos microkernel, with boot/ELF, memory, scheduler, IPC, device/HAL, networking, Kore service management, package management, shells/utilities, Aurora Wayland Glass, installers, storage targets, compatibility layers, and CI-built binary artifacts.

The supplied specifications describe Chimera II as a research/software-defined ecosystem rather than an existing production operating system. The implementation will therefore mark each feature as native, compatibility, emulated, or research-only and will not claim unsupported hardware capability.

## 2. Source-derived constraints

The supplied CHM-8192 material defines a bootloader + microkernel + memory manager + networking + ISA execution engine + virtualization + userspace architecture, with paging, zero-copy I/O, dual-stack networking, and R8192/C8192. It describes R8192 as a 64-bit fixed instruction-word model with 1024 8192-bit GPRs, 512 predicate/mask registers, 256 wide vector/floating registers and 64 tensor registers.

The low-level specification explicitly says these are design targets rather than existing silicon and that physical performance requires FPGA/silicon measurement. The ecosystem blueprint supplies conceptual kernel/network/bootloader snippets that must be converted into testable implementations.

## 3. Koronos kernel

### 3.1 Architecture layer
Implement architecture-independent kernel APIs with backends for:
- x86_64
- ARM64
- RISC-V 64
- Chimera R8192 emulator/research target
- Cortex-M research/firmware profile

Responsibilities:
CPU context, exceptions/interrupts, timers, atomics/barriers, MMU/page tables, boot handoff, CPU discovery and architecture capability reporting.

### 3.2 Kernel core
Implement:
- boot/init sequence
- kernel objects and IDs
- ref-counting
- capability handles
- logging/panic/assert
- deterministic tracing
- configuration/state reporting

### 3.3 Scheduler
Replace placeholder behavior with:
- per-CPU run queues
- priority-aware scheduling
- MLFQ/fixed-priority policy modules
- wait queues
- completion queues
- timer wheel
- CPU affinity
- optional work stealing
- context-switch interface
- deterministic scheduler traces

### 3.4 Memory management
Implement:
- physical page-frame allocator
- buddy allocator
- slab/size-class caches
- page tables
- virtual memory areas
- copy-on-write
- guard pages
- W^X
- page fault path
- MMIO protection
- DMA/IOMMU mapping interface
- shared-memory mappings

### 3.5 IPC/syscalls
Implement:
- synchronous and asynchronous IPC
- channels/ports
- shared-memory grants
- event objects
- SPSC/MPSC ring primitives
- service discovery
- syscall dispatcher
- ABI versioning
- pointer/length validation
- process/thread lifecycle
- handles/fds
- time/signals/events
- filesystem/socket/device syscall boundaries

### 3.6 Security
Implement capability checks, isolation boundaries, measured/signed image hooks, protected MMIO, audit events, explicit DMA ownership, and constant-time cryptography interfaces where required.

## 4. Boot and ELF

### BIOS/MBR
Stage-1 bootstrap -> protected mode -> GDT/IDT -> page-table bootstrap -> long mode -> ELF64 loader -> CHMBOOT1 handoff.

### UEFI/GPT
PE32+ EFI loader -> memory-map/GOP/ACPI/SMBIOS discovery -> ELF load -> ExitBootServices -> CHMBOOT1.

### Other protocols
Normalize Multiboot1/2, Limine and chainloaded contexts into CHMBOOT1 through explicit adapters.

### ELF
Implement:
- ELF32/ELF64 validation
- PT_LOAD loading
- alignment/overflow checks
- W^X permission mapping
- kernel/user address-space boundaries
- relocation policy
- symbol/debug metadata handling
- malformed ELF tests

CI must produce a real koronos-kernel.elf and inspect it with standard ELF tooling.

## 5. Device manager and storage

Create a device/HAL boundary for:
- PCI/PCIe
- USB
- block devices
- NVMe
- input
- network
- display/GPU
- ACPI
- Device Tree
- firmware discovery

Storage targets:
- SATA HDD
- SATA SSD
- NVMe
- USB/removable
- QEMU virtual disks

Installer modes:
guided, manual partitioning, recovery, dual-boot, image deployment, unattended.

Prefer GPT + ESP on modern systems and retain MBR legacy support. NVMe begins with a controller/queue abstraction and requires QEMU/emulator tests before real-hardware support is claimed.

## 6. Networking

Build from the existing src/net and zero-copy design:

Ethernet -> ARP/ND -> IPv4/IPv6 -> ICMP -> UDP/TCP -> routing/neighbor cache -> sockets -> zero-copy allocator -> NIC DMA rings.

Required implementation areas:
RX/TX ownership states, scatter-gather, DMA descriptors, checksums/offloads, PMTU, retransmission, congestion control, SACK, backpressure, routing metrics, SLAAC, DHCPv6/DHCPv4 policy, address selection and Happy Eyeballs v2.

The existing research design already targets these interfaces; production status requires tests and implementation.

## 7. Kore system manager

Create Kore as the native service supervisor in userspace, controlled through korectl.

Unit types:
service, socket, target, timer, mount, device, path, scope.

Capabilities:
dependency graph, ordered boot/shutdown, restart policies, environment files, user/system services, readiness, watchdogs, resource limits, sandbox/capability policy, structured logging and status/query API.

Provide a systemctl-style compatibility vocabulary without copying systemd source.

## 8. Package manager

Evolve chimera-pkg from its current adapter into a transaction engine with:
- package metadata
- repository trust
- signatures
- dependency solving
- install/upgrade/remove transactions
- rollback/checkpoints
- local package database
- file ownership
- explicit hooks
- sandboxed build mode

Adapters:
APT/dpkg, DNF/RPM, pacman, zypper, apk, xbps, Portage, Homebrew, Flatpak, Snap, winget/MSIX/MSI, Chocolatey and Scoop.

AppImage/Flatpak/MSIX are compatibility formats; they do not make Chimera natively become their host OS.

## 9. Shells, terminals and utilities

Native terminal stack:
- PTY/TTY service
- POSIX-oriented shell contract
- Bash profile
- Zsh profile
- Korn-shell compatibility
- optional Fish profile
- job control
- pipes/redirection
- environment
- signals
- terminal capability database
- UTF-8 and RTL support

Implement the POSIX utility baseline first and add compatibility aliases for common Linux/BSD, Windows and macOS command vocabularies. A compatibility command must state or expose its backend/profile where semantics differ.

## 10. Aurora Wayland Glass

Aurora remains a native compositor/session architecture and not a proprietary desktop clone.

Components:
- display/session daemon
- Wayland compositor
- window/workspace manager
- seat/input manager
- clipboard/data device
- theme/wallpaper manager
- launcher
- notifications
- settings
- accessibility
- terminal integration
- personality profiles

Rendering:
application -> toolkit -> Wayland protocol -> Aurora compositor -> DRM/KMS -> GPU driver.

Existing event/UI/profile JSON contracts remain stable interfaces. Linux, Windows and macOS personalities are behavioral profiles only.

## 11. Cross-platform compatibility

Linux:
POSIX/ELF and Linux-oriented command and API adapters.

Windows:
Win32 vocabulary, Winsock boundary, PE/COFF boundary, MSIX/MSI/winget metadata adapters and optional WSL-style interoperability.

macOS:
Mach-O boundary, POSIX command vocabulary, launchd-style service vocabulary and AppKit/SwiftUI behavioral profiles.

No proprietary source, vendor binaries, trademarks or protected assets will be copied into the repository without a compatible license.

## 12. Compiler, linker and SDK

Toolchain:
Clang/GCC -> LLVM IR -> target/assembler -> LLD -> ELF/EFI/PE-compatible artifacts.

SDK outputs:
headers, libraries, compiler/assembler/linker wrappers, debugger/profiler tools, system headers, tensor/crypto APIs.

R8192/C8192 assembler/disassembler and emulator integration remain research-stage until validated.

## 13. Binary and ISO pipeline

CI will generate:
- koronos-kernel.elf
- Chimera EFI loader
- userspace binaries
- Kore
- Aurora
- shell/utilities
- initramfs
- ISO
- HDD image
- SSD image
- NVMe/QEMU image

Generated binaries should be attached to GitHub Releases with checksums, SBOM/provenance and build metadata rather than committed as source blobs.

## 14. Validation

CI stages:
1. formatting/schema validation
2. host build
3. kernel unit tests
4. emulator tests
5. ELF/EFI validation
6. QEMU x86_64 boot smoke test
7. package transaction tests
8. shell/utility tests
9. Wayland/Aurora protocol tests
10. installer dry-run tests
11. ISO/image creation
12. release packaging

A feature is considered implemented only when source, documented interface, tests, CI build, inspectable artifact and limitations are present.

## 15. Implementation stages

A. Koronos foundation:
headers, scheduler, memory, IPC, capabilities, syscall boundary.

B. Boot:
x86_64 BIOS path, UEFI loader, ELF loader, CHMBOOT1, boot tests.

C. Userspace:
Kore, PTY/shell, core utilities, service APIs.

D. Storage/network:
block/NVMe/VFS, filesystem interfaces, DMA ownership, TCP/IP hardening.

E. Aurora:
Wayland compositor/session, input/render pipeline, glass shell, settings, package center and terminal.

F. Compatibility:
POSIX/Linux/BSD, Windows and macOS profiles, package/command adapters.

G. Installer/releases:
ISO/HDD/SSD/NVMe image tooling, recovery path, signed and reproducible artifacts.

H. R8192/C8192:
decoder/interpreter, assembler/disassembler, ABI integration, emulator tests.

## 16. Repository changes

New or expanded areas:
include/chimera/koronos
src/kernel
src/mm
src/ipc
src/sys
src/device
system/kore
shell
tools/compat
desktop/aurora/compositor
boot/x86
boot/uefi
installer
docs/architecture/koronos
tests/koronos

Existing package-manager, boot, desktop, networking, memory and shell registries remain integrated rather than duplicated.

## 17. Required source references

The implementation will cite:
- supplied CHM-8192 technical specification
- supplied Chimera II low/high-level specification
- supplied ecosystem/robotics blueprint
- Linux kernel ABI/documentation
- UEFI Specification
- POSIX Shell and Utilities specification
- Wayland protocol/architecture documentation
- LLVM/LLD documentation
- FreeBSD/OpenBSD package/service documentation
- Microsoft WSL interoperability documentation
- AppImage/Flatpak documentation

External documentation defines interfaces and concepts only; it does not replace the repository's own implementation status.

## 18. Explicit limitations

“Full implementation of all Linux/Unix/Windows/macOS commands and utilities” cannot literally mean embedding every upstream OS command, proprietary API or vendor binary. The implementation will provide a native compatible core, documented adapters, emulation boundaries and an extensible registry so additional tools can be added without redesigning Koronos.

The supplied documentation itself states that Chimera II is a research concept and that physical throughput, energy and brain-emulation claims require implementation and measurement.