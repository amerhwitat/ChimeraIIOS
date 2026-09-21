# Koronos Kernel & Chimera II OS Full-System Implementation Plan

> For agentic workers: use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax.

**Goal:** Convert the approved Koronos/Chimera II research specification into a reproducible, testable software platform with a bootable x86-64 research kernel, userspace service manager, package/command compatibility environment, storage/networking foundations, Aurora Wayland Glass, installer/image generation, and R8192/C8192 research tooling.

**Architecture:** Keep Koronos small and architecture-neutral; put policy-heavy services such as Kore, the package manager, shell, networking protocols, storage filesystems, and Aurora in userspace. Use explicit HAL/adapter boundaries for Linux, BSD, Windows, macOS, UEFI, BIOS, and R8192/C8192 instead of copying proprietary implementations.

**Tech Stack:** C++20/C17 for kernel/runtime components; C/assembly for boot paths; Python 3 for tooling; POSIX shell, Bash and PowerShell for automation; CMake + Ninja; Clang/GCC + LLD; QEMU for boot tests; Wayland/DRM-KMS/GBM/FreeType where available; JSON schemas; GitHub Actions; xorriso/GRUB-based ISO tooling selected by the existing build environment.

**Spec:** docs/superpowers/specs/2026-09-21-koronos-full-system-design.md

## Global Constraints

- Preserve the research boundary: R8192/C8192 and physical throughput are implementation targets, not existing silicon claims.
- Implement compatibility through documented APIs, file formats, protocols, command vocabularies and adapters; do not copy proprietary Microsoft/Apple binaries or source.
- Use the existing boot/boot_protocol.json CHMBOOT1 normalized handoff.
- Keep the repository package trust policy: official-first, HTTPS, signed remote binary repositories, explicit third-party opt-in, provenance recording, and never execute remote scripts automatically.
- Keep Aurora's existing policy: behavioral compatibility profiles, not proprietary binary cloning.
- Build for Linux-hosted CI first; cross-compile x86-64/ARM64/RISC-V as artifacts and use QEMU/emulators where available.
- Generated binaries belong in CI artifacts/releases, not source control.
- Maintain LF line endings for shell/Docker/YAML files.

## Review Focus

- Malformed/truncated ELF program headers are rejected without out-of-bounds reads — Task 3 tests.
- Scheduler wake/block/yield transitions cannot leave a task both queued and blocked — Task 2 tests.
- Capability and syscall pointer/length validation rejects overflow and unmapped ranges — Task 2 tests.
- Block/NVMe I/O completion and ownership are exactly-once — Task 5 tests.
- Aurora invalid protocol/object requests produce deterministic errors rather than compositor crashes — Task 8 tests.

---

## Task 1: Koronos public interfaces and deterministic test harness

Files: create include/chimera/koronos/types.hpp, result.hpp, capability.hpp, task.hpp, scheduler.hpp, memory.hpp, ipc.hpp, syscall.hpp, kernel.hpp; src/kernel/core.cpp; src/kernel/capability.cpp; tests/koronos/test_kernel_interfaces.cpp; cmake/koronos.cmake; modify CMakeLists.txt.

Produces: Task, TaskState, Scheduler, MemoryManager, CapabilityTable, Kernel, SyscallFrame and Result interfaces. Scheduler exposes enqueue, pick_next, block, wake and tick. MemoryManager exposes map, unmap and validate_range. CapabilityTable exposes grant, revoke and check. Kernel exposes init and run_once.

- [ ] Write failing construction/state/capability tests.
- [ ] Run the focused test target and confirm functional failures.
- [ ] Add minimal fixed-width interfaces, enums and deterministic errors.
- [ ] Run focused and complete host tests.
- [ ] Commit: feat(koronos): add kernel public interfaces and test harness.

## Task 2: Scheduler, virtual memory, IPC, capabilities and syscall validation

Files: modify src/kernel/kernel_arch.cpp, arch_context.cpp, chimera_kernel_main.cpp, microkernel_services.cpp; create src/kernel/scheduler.cpp; src/mm/page_allocator.cpp, page_table.cpp, vm_space.cpp, dma_map.cpp; src/ipc/channel.cpp, ring.cpp; src/sys/syscall_dispatch.cpp, process.cpp, handle_table.cpp; tests/koronos/test_scheduler.cpp, test_memory.cpp, test_ipc.cpp, test_syscall_validation.cpp.

- [ ] Write tests for duplicate enqueue, wake-after-block, priority ordering, page alignment, map/unmap, overflow, full/empty rings, stale capabilities and invalid syscall pointers.
- [ ] Implement scheduler state machine and priority selection.
- [ ] Implement buddy/page allocator with a deterministic host-backed backend for tests.
- [ ] Implement VM mappings, W^X, guard metadata and DMA validation.
- [ ] Implement IPC channels/rings and capability-checked shared memory.
- [ ] Implement syscall dispatch and pointer/length validation.
- [ ] Run AddressSanitizer/UBSan host tests.
- [ ] Commit: feat(koronos): implement scheduler memory ipc and syscall validation.

## Task 3: ELF loader, x86-64 kernel image and CHMBOOT1 handoff

Files: create include/chimera/koronos/elf_loader.hpp; src/boot/elf_loader.cpp; tests/boot/test_elf_loader.cpp; boot/x86/entry.S; boot/x86/long_mode.S; boot/uefi/ChimeraLoader.c; linker/koronos-x86_64.ld; tests/boot fixtures and tests; modify boot/x86 and boot/uefi existing loader sources and boot/boot_protocol.json as required.

- [ ] Add failing tests for bad magic, unsupported class, truncation, segment overflow, bad alignment and invalid permissions.
- [ ] Implement bounds-checked ELF32/ELF64 PT_LOAD validation.
- [ ] Add x86-64 bootstrap, GDT/IDT setup, page-table bootstrap and long-mode entry.
- [ ] Add UEFI PE32+ loader with memory-map/GOP/ACPI/SMBIOS discovery and CHMBOOT1 handoff before ExitBootServices.
- [ ] Add BIOS research path and normalized handoff.
- [ ] Build koronos-kernel.elf and chimera-loader.efi and inspect with readelf/objdump.
- [ ] Boot with QEMU and verify CHMBOOT1 -> Koronos -> scheduler output.
- [ ] Commit: feat(boot): add validated ELF loader and x86-64 boot handoff.

## Task 4: Kore system/service manager

Files: create system/kore/include/kore/unit.hpp, manager.hpp; system/kore/src/unit.cpp, manager.cpp, dependency_graph.cpp, watchdog.cpp, log.cpp; system/kore/tools/korectl.cpp; unit JSON files; tests/test_manager.cpp; CMakeLists.txt.

- [ ] Test circular dependencies, startup order, timeout and restart backoff.
- [ ] Implement unit parser and dependency graph.
- [ ] Implement process supervision and readiness protocol.
- [ ] Implement watchdog and structured logging.
- [ ] Implement korectl start/stop/restart/status/list/reload and systemctl-style vocabulary adapter.
- [ ] Add boot units for kernel runtime, network, Aurora and package services.
- [ ] Run manager end-to-end host supervision tests.
- [ ] Commit: feat(kore): add native service manager.

## Task 5: Storage, VFS, block devices and NVMe/HDD/SSD installation primitives

Files: create include/chimera/storage/block_device.hpp, nvme.hpp, vfs.hpp; src/storage/block_device.cpp, nvme.cpp, partition.cpp, vfs.cpp, filesystem_registry.cpp; filesystem adapter files; tests/storage/*; installer/storage-layout.json.

- [ ] Write fake-device tests for block I/O, partition parsing and NVMe queues.
- [ ] Implement exactly-once request ownership/completion.
- [ ] Implement GPT/MBR parsing with bounds checks.
- [ ] Implement NVMe controller/register/queue abstractions and a fake backend.
- [ ] Implement VFS adapter interfaces and FAT baseline; keep ext4, NTFS, XFS, ZFS and Btrfs explicitly adapter-scoped until implemented.
- [ ] Add installation layouts for SATA HDD, SATA SSD and NVMe.
- [ ] Run QEMU virtual-disk installation smoke tests.
- [ ] Commit: feat(storage): add block nvme partition and vfs foundations.

## Task 6: Dual-stack networking and zero-copy ownership

Files: modify src/net/inet.cpp, inet.h and spotnik.cpp; create include/chimera/net/packet.hpp, socket.hpp; src/net/packet_pool.cpp, routing.cpp, neighbor_cache.cpp, dhcp_policy.cpp, happy_eyeballs.cpp, socket_api.cpp, tcp_state.cpp; tests/net/*.

- [ ] Test ownership transitions, double release, route lookup, source selection, neighbor expiry and fallback policy.
- [ ] Implement packet pool and zero-copy descriptors.
- [ ] Implement unified IPv4/IPv6 longest-prefix routing.
- [ ] Implement neighbor cache and DHCP policy abstraction.
- [ ] Implement socket abstraction and Linux/POSIX host backend.
- [ ] Implement Happy Eyeballs/path scoring.
- [ ] Run ASan/UBSan and Linux network-namespace tests.
- [ ] Commit: feat(net): add dual-stack zero-copy network foundations.

## Task 7: Shell, PTY and Unix/Windows/macOS command compatibility

Files: create shell/core include and source, shell/pty include and source, shell/compat aliases and Bash/Zsh/Ksh/Fish profiles; tools/shell/validate_command_registry.py; tools/compat/linux_command_adapter.py, windows_command_adapter.py, macos_command_adapter.py; tests/shell/*; modify command source registry.

- [ ] Test command-registry schema and PTY lifecycle.
- [ ] Implement command registry validation/lookup.
- [ ] Implement PTY/session abstraction and job control.
- [ ] Implement POSIX shell execution with pipes/redirection.
- [ ] Connect Bash/Zsh/Ksh/Fish compatibility profiles to the common registry.
- [ ] Add Linux/BSD/Windows/macOS command adapters and explicit unsupported-operation reporting.
- [ ] Run the shell command matrix in CI.
- [ ] Commit: feat(shell): add terminal pty and command compatibility layer.

## Task 8: Aurora Wayland Glass compositor/session

Files: create desktop/aurora/compositor include/source files for compositor, Wayland, DRM, input, workspace, theme, clipboard, launcher and session; compositor tests; session.json; modify desktop event/UI contracts and aurora_app_registry.json.

- [ ] Test invalid event/object/protocol cases.
- [ ] Implement compositor object registry and deterministic event dispatch.
- [ ] Implement Wayland socket/event loop boundary.
- [ ] Implement DRM/KMS backend interface plus headless test backend.
- [ ] Implement input/focus/workspaces/clipboard/launcher.
- [ ] Implement Aurora Glass presentation using existing theme/wallpaper registries.
- [ ] Connect Settings, Terminal, Package Center, Network Center and Developer Center to stable service APIs.
- [ ] Run headless Wayland client tests and graphical smoke tests where available.
- [ ] Commit: feat(aurora): add Wayland glass desktop session architecture.

## Task 9: Compatibility package manager and application formats

Files: modify package-manager/chimera-pkg.py and repositories.json; create package schema, transaction, database, signatures, solver and adapters; create package-manager/tests/*.

- [ ] Test transactions, trust policy, signature rejection, dependency cycles and interrupted transactions.
- [ ] Implement package database and transaction journal.
- [ ] Implement repository metadata/signature verification.
- [ ] Implement deterministic dependency solving.
- [ ] Add adapters for APT/dpkg, DNF/RPM, pacman, Flatpak, AppImage, MSIX/MSI, plus existing Windows managers.
- [ ] Require explicit confirmation before execution and preserve provenance.
- [ ] Integrate Package Center with Aurora.
- [ ] Commit: feat(pkg): add trusted package transaction engine and adapters.

## Task 10: Installers, ISO/HDD/SSD/NVMe images, SDK, R8192/C8192 and release CI

Files: create installer/chimera-installer.py and layout/recovery manifests; tools/iso/build-iso.sh; tools/images/build-disk-image.sh and validate-image.py; tools/toolchain/chimera-elf-toolchain.cmake; src/isa/r8192_decoder.cpp, c8192_decoder.cpp, r8192_encoder.cpp, disassembler.cpp; tests/isa/test_roundtrip.cpp; docs/architecture/koronos/implementation-status.md; CI workflows for build/QEMU/release; modify README.md.

- [ ] Test dry-run BIOS/MBR, UEFI/GPT, NVMe/GPT and recovery layouts.
- [ ] Implement sparse-file image creation and partition validation.
- [ ] Assemble ISO around actual ELF/EFI/rootfs artifacts and validate El Torito metadata.
- [ ] Implement installer dry-run/apply separation with explicit destructive-operation confirmation.
- [ ] Implement R8192/C8192 encoder/decoder round trips for the current opcode catalog.
- [ ] Add x86-64/ARM64/RISC-V cross-build configuration and the Chimera research target.
- [ ] Add QEMU BIOS and UEFI boot workflows.
- [ ] Publish ELF/EFI/ISO/disk images with SHA-256, SBOM and provenance.
- [ ] Update implementation status to mark every feature native, adapter, emulated or research-only.
- [ ] Commit: release: add Chimera installation images and CI artifact pipeline.

## Integration Gate: full-system validation

Files: create tests/integration/test_boot_to_kore.sh, test_boot_to_aurora.sh, test_pkg_shell_network.sh, test_install_image.sh; modify .github/workflows/koronos-qemu.yml.

- [ ] Boot generated ISO in QEMU and verify Koronos scheduler/MM/IPC initialization.
- [ ] Verify Kore starts networking and shell.
- [ ] Verify shell can query services, network and package state.
- [ ] Verify Aurora starts through headless protocol tests.
- [ ] Verify package trust/transaction policy.
- [ ] Verify image metadata and SHA-256 checksums.
- [ ] Run the complete CI matrix and retain logs/artifacts.
- [ ] Commit: test: add full Chimera boot-to-userspace integration suite.

## Expected deliverables

1. Buildable Koronos host/emulator core with scheduler, MM, IPC, capabilities and syscall validation.
2. Real ELF64 kernel artifact plus x86-64 BIOS/UEFI research boot paths.
3. CHMBOOT1 handoff validation.
4. Kore service manager and korectl.
5. Block/VFS/NVMe/HDD/SSD installation primitives.
6. Dual-stack networking/zero-copy foundations.
7. PTY + POSIX shell with Bash/Zsh/Ksh/Fish profiles and command adapters.
8. Aurora Wayland Glass compositor/session architecture and headless tests.
9. Transactional package manager with trust/provenance and package-format adapters.
10. R8192/C8192 encoder/decoder tooling.
11. ISO/HDD/SSD/NVMe/QEMU image generation.
12. GitHub Actions build, QEMU validation and release pipeline.

## Explicit non-goals

- Claiming that R8192/C8192 is physical silicon.
- Claiming native execution of proprietary Windows/macOS binaries without a real compatibility/emulation layer.
- Copying proprietary Microsoft/Apple source, binaries or protected assets.
- Embedding all upstream Linux/Unix kernel source into Koronos.
- Writing arbitrary real host disks during CI.
