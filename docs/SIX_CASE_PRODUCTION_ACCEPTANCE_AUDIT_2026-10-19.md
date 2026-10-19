# Six-case production acceptance audit — 2026-10-19

## Evidence reviewed

- OctavianOS native Koronos run: https://github.com/amerhwitat/OctavianOS/actions/runs/39226439884
- Candidate source commit tested by that run: `e4c614c1e9a86a9aa01f57cf0f517b95d61994b9`
- Candidate ISO artifact: `octavianos-native-iso-candidate` (review candidate, not a release)
- ISO SHA-256, recomputed from the downloaded artifact: `2f5c1d8d0168a1c8e824cc370203fd0d5fcdcad491fb2771e323add76f8c5ca6`
- Koronos ELF SHA-256, recomputed from the matching build artifact: `6c33b09a314afad25fefad446acc1b1415b403208c1bf8923447ec182c432cca`
- QEMU trace artifact: `octavianos-full-iso-qemu-trace`, artifact digest `sha256:3b408a53a7e43c51a1597776ab96c432ed5be4b625c16aebd44a1ee0208dc2b4`
- Verifier job: `Verify real Live, Installer, and Recovery userspace`, job ID `117974930456`, failed on all three supplied logs.

These hashes identify the candidate artifacts examined; they do not convert any acceptance case to PASS.

## What the serial/debug traces prove

1. **Production init does not execute.** All traces say `Protected-process admission layer ready (load-plan mode)` and `USERSPACE READY is withheld: ELF load-plan admission is not a process execution context`. None contains the required CPL3-originated init syscall acknowledgement or matching nonzero PID READY event.
2. **The full-ISO trace is an Installer route, not a Live boot.** It contains installation image/manifest/contract modules and reports `Installer target detected; live service idle`. The Recovery initramfs is absent in that trace. It then says the graphical installer userspace is not running and waits for the Koronos userspace installer loader.
3. **Installer completion is not demonstrated.** The installer trace says `USERSPACE HANDOFF NOT VERIFIED`, `installer execution is not verified`, and `Waiting for the Koronos userspace installer loader`. There is no completed installation, reboot, or boot of an installed system.
4. **Recovery operation is not demonstrated.** The recovery trace accepts a recovery initramfs module but says `USERSPACE HANDOFF NOT VERIFIED: repair shell has not been entered`. Acceptance of a module is not a recovery operation.
5. **SMP is not demonstrated.** Traces report one detected/online CPU and `AP startup not implemented`. There is no AP-startup evidence or concurrent per-CPU progress.
6. **Firmware coverage is incomplete.** The inspected traces report `Firmware: BIOS` and `UEFI system table: absent`. They do not provide UEFI evidence or a six-combination matrix.

## Required work before acceptance

- Implement a real production init execution path (or supported interpreter/runtime) with user-mode entry, syscall provenance, real PID lifecycle, and matching target/PID readiness acknowledgement.
- Stage and route the correct target-specific initramfs/init payload for Live, Installer, and Recovery; the current trace demonstrates an Installer payload was selected for the full-ISO boot.
- Add actual Live Aurora desktop-ready evidence, installer completion/reboot/installed-boot evidence, and a real recovery-operation result.
- Implement AP startup and test simultaneous per-CPU progress independently of the six boot cases.
- Run separate BIOS and UEFI boots for each target, attach raw logs and artifact hashes, and run the unchanged production verifier against those exact artifacts.

## Architecture references

- UEFI boot-services and loader ownership boundary: https://uefi.org/specs/UEFI/2.10/07_Services_Boot_Services.html
- Linux kernel documentation: https://docs.kernel.org/
- Windows user/kernel isolation: https://learn.microsoft.com/en-us/windows-hardware/drivers/gettingstarted/user-mode-and-kernel-mode
- Apple XNU architecture source: https://github.com/apple-oss-distributions/xnu

The sources inform architecture and evidence requirements; they do not substitute for runtime proof. All six production cases remain `NOT_RUN`. Do not merge as production-ready or publish a release based on this audit.
