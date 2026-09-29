# Chimera II OS Implementation Progress — 2026-09-29

## Completed in this slice

### Koronos microkernel foundation

- Capability handles with explicit rights.
- Endpoint IPC with bounded queues.
- Microkernel syscall dispatch ABI.
- Microkernel object initialization/revocation.
- Integrated `kernel/core/microkernel.cpp` into the Koronos freestanding build.
- Added `kernel/include/chimera/microkernel.h`.
- Added dedicated CMake validation target.
- Repaired `kernel/build-koronos.sh`, which had become syntactically corrupted after earlier incremental edits.
- ELF64 and N-bit artifact generation remains enabled for 8 through 8192-bit execution metadata profiles.

### Mobile edition

- Added `mobile/build-mobile-edition.sh`.
- Mobile edition now has an explicit architecture/device-profile boundary.
- Desktop x86_64 Koronos is retained only as a reference/build artifact; it is not presented as an ARM phone boot image.
- Mobile sync contract now includes the shared microkernel IPC ABI and security policy.
- Android integration continues through device-specific ADB/fastboot/recovery adapters.
- Apple integration remains signed/hosted through the Apple toolchain.

### Mobile flash tool

- Device discovery: ADB and fastboot.
- Payload preparation.
- Exact-device manifest validation.
- Image SHA-256 verification.
- Architecture validation.
- Signed-image policy requirement.
- Rollback metadata policy.
- Dry-run support.
- Generic unspecified partition flashing is intentionally disabled.
- Authentication/unlock bypass functionality is not part of the Chimera flash contract.

### CI

Added `.github/workflows/microkernel-mobile-validation.yml` for shell, JSON, microkernel and mobile safety-contract validation.

## Current validation state

The repository has been updated and CI has been configured to compile/validate the new surfaces. A successful GitHub workflow run is the release gate for claiming that the new microkernel source actually links on the CI toolchain.

## Next integration gates

1. Successful Koronos freestanding build and ELF validation.
2. QEMU BIOS/UEFI boot of the resulting ISO.
3. Hyper-V Gen1/Gen2 boot validation.
4. VMware BIOS/EFI boot validation.
5. Live Aurora boot.
6. Installer Aurora boot.
7. Installed Aurora Desktop boot.
8. ARM64 cross-build for the mobile kernel/adapter boundary.
9. Device-specific mobile boot bundles and signed deployment adapters.
10. Physical-device validation per exact device manifest.

## Architectural rule

The common Koronos microkernel, scheduler, synchronization, timer, APC/DPC, hardware discovery and IPC layers are shared. Device-specific boot firmware, DTBs, vendor drivers, signing requirements and partition layouts remain adaptation inputs rather than being guessed or synthesized generically.
