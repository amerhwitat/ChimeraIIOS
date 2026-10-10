# Koronos x86-32 bring-up: implementation boundary and acceptance plan

## Current increment

This increment introduces an isolated Multiboot v1 ELF32/i386 serial probe at `kernel/arch/x86_32/`. It is intentionally separate from the production Koronos entry path until the kernel's boot contract, memory map, allocator, ABI and interrupt model are ported. It prints `KORONOS32_BOOT_OK` through COM1 and halts. The QEMU smoke script builds an ISO containing this probe and requires the serial marker.

This is a **bring-up scaffold**, not a native 32-bit Koronos kernel. It does not initialize the production hardware/driver registry, GDT/IDT, paging, interrupts, scheduler, process model, userspace, recovery, installer or Aurora. It must not be advertised as a complete 32-bit OS.

## Reproducible checks

On a Linux host with GCC multilib, GRUB rescue tools, xorriso and QEMU:

```sh
python3 -m unittest tests/unit/test_koronos32_bringup.py
bash tools/runtime/check-koronos32-boot.sh
```

The workflow `.github/workflows/koronos32-bringup.yml` runs static contract tests and a real QEMU serial boot smoke test. A green probe job is evidence only for this isolated target; it does not establish that the production ISO boots.

## Remaining production work

1. Define a 32-bit Koronos ABI and boot contract: Multiboot/UEFI entry, stack, CPU feature baseline, memory-map handoff and panic/debug output.
2. Port kernel primitives without truncation: physical/virtual address types, page tables, allocator, ELF32 loader, process/context switch, syscall/trap ABI, timers and scheduler.
3. Implement 32-bit GDT/IDT/TSS, PIC/APIC routing, exception handling and privilege transitions; validate with dedicated fault and interrupt tests.
4. Port drivers one at a time behind explicit 32-bit interfaces; test device models in QEMU and physical hardware separately.
5. Build a dedicated 32-bit root filesystem, native compiler/binutils/runtime and Aurora dependency graph. Audit pointer width, structure layout, atomics, alignment, overflow and file formats.
6. Extend the canonical ISO pipeline without changing its established order: Spit Fire → Jasper/GRUB → Koronos ELF → hardware/driver initialization → scheduler/runtime loop → live/recovery/installer userspace → Aurora.
7. Add full ISO artifact checks and boot acceptance assertions for the actual production kernel and required payloads, then run QEMU tests for the final ISO.
8. For guest execution, require per-backend instruction conformance tests and documented supported opcode/exception/privilege coverage. For cross-bitness binaries, require an actual loader/ABI bridge or emulator plus positive and negative execution tests; metadata alone is not execution support.

## Acceptance gates

| Gate | Evidence required | Status after this increment |
|---|---|---|
| ELF32/i386 entry object | ELF header and Multiboot header inspection | CI check |
| Isolated x86-32 serial boot | QEMU serial marker | CI QEMU job |
| Production Koronos 32-bit kernel | Kernel boot, memory, trap, scheduler tests | Not implemented |
| Complete 32-bit ISO | Canonical ISO build and payload audit | Not verified |
| Native 32-bit drivers/toolchain/Aurora | Build and runtime tests on 32-bit environment | Not verified |
| Guest ISA backends | Conformance suite per ISA/backend | Not verified |
| Cross-bitness binary execution | Loader/emulator integration and ABI tests | Not verified |

Do not mark any gate complete solely because a source file, architecture identifier or build target exists.
