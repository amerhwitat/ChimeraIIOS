# Unified Installer Experience — Production Implementation Contract

Status: implementation specification and safe staging contract; not a claim that disk installation is already production-ready.

## Experience goals

Deliver a guided, full-screen setup experience comparable in task coverage to Windows Setup and mainstream Linux installers, using the Aurora Wayland Glass visual language and the unified OctavianOS/Chimera emblem. Preserve a text-mode rescue path when graphics are unavailable.

## Screen sequence

1. Welcome / Install, Try Live, Repair, Firmware and Hardware Diagnostics.
2. Language, region, keyboard layout, screen reader, high contrast, scaling and keyboard navigation.
3. Network: wired/wireless discovery, DHCP/static IPv4/IPv6, proxy, offline install and mirror reachability.
4. Installation source and integrity: ISO/repository selection, signed manifest, hashes, version and architecture compatibility.
5. Destination selection: enumerate disks by stable ID/model/size; show removable/read-only/active-system warnings; never choose a disk implicitly.
6. Partitioning: guided erase, install alongside where supported, manual GPT/MBR; EFI System Partition, root, optional home, recovery and swap policy; show an exact destructive-operation preview.
7. Filesystem and security: supported filesystem matrix, encryption, key escrow/recovery warning, Secure Boot state and bootloader target.
8. Edition / software: Live base, Aurora desktop, Marine desktop, accessibility, development tools, compatibility runtimes, optional application groups.
9. Accounts and first boot: administrator/user creation, password policy, timezone, hostname, network and privacy choices.
10. Hardware / driver review: PCI/USB/ACPI discovery, native-first matching, signature/hash verification, unsupported-device warnings; never execute untrusted driver code.
11. Final review: exact disk identifiers, partitions, packages, boot entries, encryption and data-loss statement; require explicit confirmation.
12. Installation progress: phase-based progress with timestamped verbose logs, cancel semantics, retryable phases and bounded error details.
13. Verification: filesystem and manifest verification, installed kernel/init/service presence, bootloader entries, recovery entry and checksums.
14. Completion: show logs, recovery key instructions, reboot/eject media, and a first-boot verification plan.

## Transaction and safety requirements

- Separate discovery/plan from mutation. The default is dry-run.
- Require explicit user confirmation bound to the selected disk's stable identifier and a digest of the displayed plan. Re-confirm if the plan changes.
- Use a journal with PREPARED, APPLYING, VERIFYING, COMMITTED, ROLLBACK_REQUIRED and ROLLED_BACK states. Persist before each destructive phase.
- Do not shell-concatenate untrusted device names, mount paths, URLs, or user input. Use argument-vector process APIs and strict allowlists.
- Never claim rollback if the partition table/filesystem cannot be restored. Preserve logs and report partial irreversible changes.
- Verify signatures/hashes before staging packages. No proprietary drivers, firmware, ROMs, fonts, codecs or branded assets without redistribution rights.
- The installer CLI and graphical frontend must call the same tested transaction engine.
- Keep the recovery/diagnostics path usable when graphics or network is unavailable.

## Current repository reality / acceptance gates

The existing C++ installer core currently prints a broad plan and copies a source tree to a target root. Its GUI executable is presently a console stub. It does not yet implement safe partitioning, filesystem creation, encryption, a real bootloader installation backend, a transactional rollback journal, or first-boot acceptance. Those features must be implemented and tested before advertising this as a full installer.

Acceptance requires unit tests for plan validation and journal recovery, disposable-disk QEMU tests, interruption/power-loss tests, signed manifest verification, BIOS and UEFI install/reboot tests, and a test proving a mismatched or changed target disk is rejected before any destructive operation.
