# Boot-to-destination production acceptance contract

**Release gate: BLOCKED until real production boots are verified.** This defines the required build and boot order. A compiled object, menu entry, kernel banner, candidate ring-3 probe, or scheduler heartbeat is not proof of a usable OS.

## Required order

1. **Build environment:** pin source revision/toolchain, validate dependencies and storage, start from a known build state, and fail fast on missing inputs.
2. **Firmware media:** build and inspect BIOS and UEFI boot paths independently, including BIOS El Torito, GRUB2 configuration, and `EFI/BOOT/BOOTX64.EFI` for x86-64 UEFI.
3. **GRUB2/Jasper:** verify Live, Installer, and Recovery entries route to exactly one matching target and its actual payload. No silent fallback to Live. Record firmware, target, and payload hashes.
4. **HAL/platform:** initialize CPU and firmware tables, memory map/allocator, interrupt controller/timer, PCI/device discovery, display, storage, input, and supported networking. Record actual device probe results and explicit errors; linking a driver is not a successful probe.
5. **Kernel:** verify address-space isolation, ELF PT_LOAD/BSS/entry bounds, NX/W^X, user stack, process-owned CR3, ring-3 transition, real syscall origin, kernel-owned PID, exit/cleanup, timer interrupts, scheduler and SMP. Exercise failure cleanup.
6. **Payload handoff:** launch the selected target's real init from its declared module/archive. Bound archive traversal and decompression. Do not interpret an installer disk image as CPIO; stage a separately typed installer init ELF or implement a real image/mount/install backend.
7. **Services:** target init starts services in dependency order, waits for real health/readiness, handles failure/timeouts, and records process status. A service catalog or “orchestration online” log is not proof of a running service.
8. **Destination behavior:**
   - **Live CD:** start required services, session manager/compositor and Aurora; verify interactive input and visible rendering at the highest supported display mode, with tested 1024×768 and 640×480 fallbacks.
   - **Installer:** use a disposable test disk; verify partition/filesystem/bootloader writes, installation result, reboot, and boot from the installed disk rather than the ISO.
   - **Recovery:** execute and verify a real diagnostic or repair operation.
   - **Installed OS:** mount required filesystems, start configured services, launch the desktop/session, and verify usable display/input after a disk boot.
9. **Release:** preserve separate traces and artifacts; any missing case or failed verifier blocks publication.

## Independent acceptance matrix

| Destination | BIOS | UEFI |
|---|---|---|
| Live → services → Aurora | NOT VERIFIED until interactive desktop test passes | NOT VERIFIED until interactive desktop test passes |
| Installer → install → reboot → installed OS | NOT VERIFIED until disk workflow passes | NOT VERIFIED until disk workflow passes |
| Recovery → real recovery action | NOT VERIFIED until operation passes | NOT VERIFIED until operation passes |

Additionally verify all required services' actual process/health state, highest supported display mode and both fallbacks, real user-originated syscall plus matching nonzero PID/readiness from init, and AP startup with concurrent per-CPU execution before claiming SMP. Include negative tests for missing/wrong/ambiguous payloads, malformed ELF, driver/service failure, timeout, and premature init exit.

## Known blockers from the current audit

- Candidate ring-3 smoke is not production payload acceptance.
- The inspected target launcher has CPIO ELF extraction for Live/Recovery but explicitly rejects an installer disk image when a separately typed native installer init ELF is absent. The final ISO's actual module staging must be verified.
- PID/syscall/process-exit semantics and full service/desktop startup need real production traces.
- The runtime heartbeat and “bootstrap hook returned” do not prove userspace is running.

## Evidence required per revision

Record commit SHA; toolchain/dependency results; BIOS/UEFI GRUB artifact checks; HAL probes; kernel build/tests; target module identity and hashes; six independent production QEMU outcomes; service health; display mode/fallbacks; Aurora launch; installer/reboot/installed boot; recovery operation; SMP evidence; artifact URLs; release decision.

**This contract is a documentation update, not an implementation claim. Do not fabricate readiness markers or weaken the existing verifier.**


## Latest verified CI evidence — 2026-10-20

Cross-repository OctavianOS workflow run [#39413346831](https://github.com/amerhwitat/OctavianOS/actions/runs/39413346831), commit `a564ccc568a9a55b9e77233873cfe18d7929ef62`, is a **failed production candidate**, not a release.

- PASS: freestanding Koronos build, ELF/Multiboot2 entry validation, Live/Recovery module classification tests, kernel readiness smoke, payload staging, ISO candidate creation, and artwork verification.
- FAIL: QEMU Recovery target-routing/readiness smoke.
- SKIPPED: Installer routing smoke, complete-ISO boot gate, production Live/Installer/Recovery verification, and prerelease publication.
- Runtime trace: the ring-3 probe reports `init_pid=1`, but init then says required native filesystem/process/device/graphics services are unavailable, exits before the target-specific `USERSPACE READY` handshake, and the scheduler monitor reports `Runnable: 0`.
- The workflow emitted `Recovery readiness failure was not reported`; this is a verifier/reporting-path defect to investigate alongside the missing service implementations. Do not weaken the acceptance check to turn this failure green.

Candidate ISO artifact (review only): [octavianos-native-iso-candidate](https://github.com/amerhwitat/OctavianOS/actions/runs/39413346831/artifacts/12260134142). QEMU trace artifact: [octavianos-full-iso-qemu-trace](https://github.com/amerhwitat/OctavianOS/actions/runs/39413346831/artifacts/12260288932). These artifacts do not imply production acceptance.

**Status remains NOT VERIFIED:** all six destination/firmware combinations, Aurora interactive desktop, installer disk-write/reboot/installed-disk boot, a real recovery operation, and AP-backed concurrent SMP remain unproven. Do not publish or promote this candidate.
