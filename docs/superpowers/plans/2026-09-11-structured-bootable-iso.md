# Structured Bootable ISO Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a deterministic Chimera II hybrid BIOS/UEFI ISO layout containing the Spit Fire/Jasper boot chain, Koronos bootstrap artifacts, source/docs/manifests, checksums and validation metadata.

**Architecture:** Preserve the existing Multiboot2 bootstrap while adding a structured staging layer and optional UEFI El Torito image. Add low-level Spit Fire source, shared boot ABI headers and linker contracts, then make the ISO builder consume these artifacts and validate the resulting image.

**Tech Stack:** NASM, freestanding C/C++, GNU ld/gcc, optional gnu-efi, xorriso, GRUB2 fallback, Python validation, QEMU optional integration tests, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-09-11-structured-bootable-iso-design.md`

## Global Constraints

- Preserve the existing Multiboot2 bootstrap path.
- Prefer UEFI/GPT and retain BIOS/MBR compatibility.
- SF0 must remain exactly 512 bytes with `0xAA55`.
- UEFI loader is optional and must not make non-UEFI builds fail.
- Do not claim bare-metal completeness for research-only components.
- No downloaded Internet source is silently executed or redistributed.
- Validation must fail closed for malformed boot artifacts.

---

### Task 1: Add shared boot ABI and CPU profile headers

**Files:**
- Create: `boot/include/chimera/bootinfo.h`
- Create: `boot/include/chimera/cpu_profile.h`
- Create: `boot/include/chimera/boot_flags.h`
- Test: `tests/boot/test_boot_abi.py`

**Interfaces:**
- `chm_cpu_profile_t`
- `chm_bootinfo_t`
- `CHM_BOOTINFO_MAGIC`
- `CHM_BOOTINFO_VERSION`
- boot mode and feature flags

- [ ] Write a Python test that parses the headers and verifies the magic/version definitions and required field names.
- [ ] Implement packed-but-explicit C-compatible structures with static assertions in C++ consumers.
- [ ] Run the header test.
- [ ] Commit `feat: add Chimera boot ABI headers`.

### Task 2: Implement Spit Fire BIOS stages

**Files:**
- Create: `boot/spitfire/sf0_mbr.asm`
- Create: `boot/spitfire/sf1_longmode.asm`
- Create: `boot/spitfire/sf2_loader.cpp`
- Create: `boot/spitfire/sf2_loader.h`
- Create: `boot/spitfire/spitfire.ld`
- Test: `tests/boot/test_spitfire_layout.py`

**Interfaces:**
- SF0 loads SF1 at `0x7E00` using INT 13h extensions.
- SF1 exports a documented handoff to SF2.
- SF2 consumes `chm_bootinfo_t` and exposes `chm_sf2_entry(...)`.

- [ ] Write tests for source presence and linker symbols plus a conditional binary-size/signature test.
- [ ] Implement SF0 with preserved drive number, DAP, failure message and signature.
- [ ] Implement SF1 GDT/A20/long-mode transition contract and protected handoff stub.
- [ ] Implement freestanding SF2 loader contract without libc dependencies.
- [ ] Run static tests; assemble when NASM is available.
- [ ] Commit `feat: add Spit Fire staged boot sources`.

### Task 3: Add UEFI loader source and EFI build contract

**Files:**
- Create: `boot/spitfire/sfu_uefi.c`
- Create: `boot/spitfire/sfu_uefi.h`
- Create: `boot/spitfire/sfu_uefi.ld`
- Create: `boot/spitfire/efi/README.md`
- Test: `tests/boot/test_uefi_layout.py`

**Interfaces:**
- `efi_main(EFI_HANDLE, EFI_SYSTEM_TABLE*)`
- Standard `EFI/BOOT/BOOTX64.EFI` destination.

- [ ] Test that the standard EFI path and entry point exist.
- [ ] Implement an EFI application boundary that discovers the system table, records framebuffer/firmware information, locates the Chimera kernel payload, and reports missing optional services safely.
- [ ] Keep the source build-gated on an available EFI toolchain.
- [ ] Run static tests.
- [ ] Commit `feat: add Spit Fire UEFI loader contract`.

### Task 4: Add Koronos kernel handoff and linker contracts

**Files:**
- Create: `kernel/include/chimera/kernel_entry.h`
- Create: `kernel/include/chimera/memory_map.h`
- Create: `kernel/arch/x86_64/entry.asm`
- Create: `kernel/arch/x86_64/koronos.ld`
- Create: `kernel/core/boot_entry.cpp`
- Test: `tests/boot/test_koronos_contract.py`

- [ ] Test required symbols and ABI references.
- [ ] Implement a minimal C++20 freestanding entry that validates bootinfo and emits a deterministic ready token for QEMU-capable environments.
- [ ] Link the entry contract separately from future full kernel services.
- [ ] Run static tests.
- [ ] Commit `feat: add Koronos boot handoff contract`.

### Task 5: Replace ISO builder with structured staging and hybrid authoring

**Files:**
- Modify: `boot/iso/build-iso.sh`
- Create: `boot/iso/iso-layout.json`
- Create: `boot/iso/README.md`
- Create: `boot/iso/prepare-layout.sh`
- Create: `boot/iso/validate-iso.py`
- Test: `tests/iso/test_iso_layout.py`

- [ ] Write failing layout tests for required directories, boot files and manifest entries.
- [ ] Implement deterministic staging under `dist/iso`.
- [ ] Add `/boot/spitfire`, `/boot/jasper`, `/boot/koronos`, `/EFI/BOOT`, `/EFI/CHIMERA`, `/chimera/...`, `/src`, and `/checksums`.
- [ ] Author BIOS El Torito plus UEFI El Torito when xorriso and EFI artifacts exist; otherwise preserve a valid GRUB2/Multiboot2 fallback.
- [ ] Emit SHA-256 manifest and build metadata.
- [ ] Ensure `.iso` is ISO 9660 and clearly distinguish any raw `.img` output.
- [ ] Run layout validation.
- [ ] Commit `feat: build structured Chimera II ISO images`.

### Task 6: Add QEMU/CI verification

**Files:**
- Create: `tests/qemu_e2e/test_boot_image.py`
- Modify: `.github/workflows/verify.yml`
- Create: `docs/STRUCTURED_ISO_BUILD.md`

- [ ] Add environment-gated QEMU boot test using serial output and a timeout.
- [ ] Add CI checks for headers, assembly structure, ISO tree and checksums.
- [ ] Document exact Linux/Windows prerequisites and fallback behavior.
- [ ] Run all locally available tests.
- [ ] Commit `test: validate structured boot and ISO artifacts`.

### Task 7: Synchronize companion ISO-Tool repository

**Files:**
- Modify: `amerhwitat/nlp/ISO-Tool` corresponding ISO-layout/build integration files.

- [ ] Mirror the structured ISO manifest and validation contract.
- [ ] Add the new source discovery/build artifact categories to the existing recursive scanner.
- [ ] Update Python, Java, C#/.NET and C++ GUI action handlers to expose the structured ISO build/validate workflow.
- [ ] Update documentation and feature manifest without changing existing button semantics.
- [ ] Commit synchronized ISO-Tool integration.

### Task 8: Final verification and documentation reconciliation

**Files:**
- Modify: `README.md`
- Modify: `docs/INSTALLATION_AND_BOOT.md`
- Modify: `docs/CHIMERA_ECOSYSTEM_PORTFOLIO.md`

- [ ] Run Python/unit/static tests.
- [ ] Run available NASM/GCC/GRUB/xorriso checks.
- [ ] Run available CMake/C++ build checks.
- [ ] Run GitHub Actions and inspect job logs after the commit.
- [ ] Reconcile documentation claims with actual verification results.
- [ ] Commit final documentation update.
