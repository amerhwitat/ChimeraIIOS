#!/usr/bin/env python3
"""Chimera/Octavian knowledge database tool.

The native kernel ships an embedded knowledge base that the AI module and the
userspace tooling read at runtime. This tool builds, validates, queries and
appends to that database.

Design notes (what this is and is not):

* It is a *curated, structured knowledge base* — a retrieval corpus with stable
  ids, categories, tags and provenance for every entry.
* It is NOT a trained neural network. There is no gradient descent here, and the
  ISO does not carry model weights. The "learning" step is ingestion: every
  entry is validated, de-duplicated by id and appended to the JSON database,
  which is what the runtime module retrieves from.

Usage
-----
  python3 tools/ai/knowledge_db.py build   [--out config/ai/knowledge-db.json]
  python3 tools/ai/knowledge_db.py validate [--db config/ai/knowledge-db.json]
  python3 tools/ai/knowledge_db.py stats
  python3 tools/ai/knowledge_db.py query "riscv toolchain" [--limit 8]
  python3 tools/ai/knowledge_db.py append --json '{"topic": "...", ...}'
  python3 tools/ai/knowledge_db.py append --file new-entries.json
  python3 tools/ai/knowledge_db.py export-c --out kernel/generated/knowledge_db_index.h
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DEFAULT_DB = os.path.join(ROOT, "config", "ai", "knowledge-db.json")
SCHEMA_VERSION = 1

# --------------------------------------------------------------------------
# Seed corpus. Each tuple is (category, topic, summary, tags, source).
# Sources are cited so a reader can check the claim; "project" means the fact
# comes from this repository, "linux-7.3" from the Linux 7.3 tree/docs.
# --------------------------------------------------------------------------
SEED = [
    # ---------------- architectures ----------------
    ("arch", "x86_64 (AMD64)", "64-bit extension of x86: long mode, 16 general registers, 4-level (optionally 5-level) paging, CPL0-3 privilege rings, IST stacks in the TSS.", ["x86", "long-mode", "paging", "rings"], "linux-7.3: arch/x86"),
    ("arch", "x86 protected mode", "32-bit protected mode introduces segmentation, paging and the GDT/IDT; long mode requires PAE-like paging structures and EFER.LME.", ["x86", "segmentation", "gdt"], "linux-7.3: arch/x86/boot"),
    ("arch", "AArch64 (ARMv8-A)", "64-bit ARM: 31 GPRs plus SP, EL0-EL3 exception levels, TTBR0/TTBR1 translation regimes, 4/16/64 KiB granule support.", ["arm64", "aarch64", "el0"], "linux-7.3: arch/arm64"),
    ("arch", "RISC-V RV64GC", "Open ISA: RV64I base plus M/A/F/D/C extensions; M/S/U privilege modes, satp-based Sv39/Sv48 paging, CLINT/PLIC interrupt controllers.", ["riscv", "sv39", "plic"], "linux-7.3: arch/riscv"),
    ("arch", "RISC-V SBI", "Supervisor Binary Interface (SBI) is the firmware/kernel contract: console putchar, IPI send, timer set, hart start, system reset.", ["riscv", "sbi", "firmware"], "linux-7.3: arch/riscv/kernel/sbi.c"),
    ("arch", "IBM POWER (ppc64le)", "Little-endian POWER8+: 64-bit GPRs, segment tables plus hash/page-table MMU, OPAL firmware interface for runtime services.", ["ppc64le", "opal"], "linux-7.3: arch/powerpc"),
    ("arch", "s390x", "IBM Z 64-bit: 16 GPRs, dynamic address translation, channel I/O (subchannels/CCW) instead of MMIO, LPAR/z/VM virtualization.", ["s390", "channel-io"], "linux-7.3: arch/s390"),
    ("arch", "LoongArch", "64-bit RISC ISA with 32 GPRs, 3 privilege levels, page-walk through CRMD/DMW registers, LoongArch Linux ABI.", ["loongarch"], "linux-7.3: arch/loongarch"),
    ("arch", "MIPS", "Load/store RISC with delay slots, KSEG0/KSEG1 mapped segments, CP0 coprocessor for exceptions and TLB.", ["mips", "tlb"], "linux-7.3: arch/mips"),
    ("arch", "WebAssembly", "Stack machine with a linear memory; not a boot target for Koronos, but the desktop tooling emits wasm for in-browser demos.", ["wasm", "browser"], "project"),
    # ---------------- boot / firmware ----------------
    ("boot", "Multiboot2", "GRUB's Multiboot2 protocol: 32-bit entry with a magic value, information request tags, memory map, framebuffer and module tags; modules are named blobs the kernel classifies.", ["grub", "multiboot2", "modules"], "linux-7.3: Documentation/arch/x86/boot.rst (comparison)"),
    ("boot", "UEFI boot", "UEFI firmware loads PE/COFF images from the ESP; GRUB's efi.img provides the chain into Multiboot2 so one ISO boots BIOS and UEFI.", ["uefi", "esp", "grub"], "project: boot/iso/build-iso.sh"),
    ("boot", "El Torito", "ISO 9660 boot record that points the BIOS at a boot image; xorriso's -report_el_torito shows the catalog entries used for verification.", ["iso9660", "bios", "xorriso"], "project: ISO-BOOT-REPORT.txt"),
    ("boot", "initramfs (cpio)", "A gzip-compressed newc cpio archive the kernel unpacks into a ramfs and executes /init from; Koronos currently stages it as payload data.", ["cpio", "initramfs"], "linux-7.3: usr/initramfs_data.S"),
    ("boot", "Long-mode trampoline", "Transition from 32-bit protected mode to long mode: build PML4/PDPT/PD, set EFER.LME, enable CR0.PG then far-jump into a 64-bit code segment.", ["long-mode", "trampoline"], "project: boot/spitfire/sf1_longmode.asm"),
    ("boot", "Higher-half kernel", "Koronos links at 0xFFFF800000000000+ and keeps user images below 0x0000800000000000 so a single PML4 split separates user and kernel space.", ["higher-half", "pml4"], "project: kernel/arch/x86_64/koronos.ld"),
    # ---------------- kernel subsystems ----------------
    ("kernel", "4-level paging", "PML4 -> PDPT -> PD -> PT, 9 bits per level, 4 KiB pages, NX and U/S bits per entry; CR3 holds the physical address of the active PML4.", ["paging", "cr3", "nx"], "linux-7.3: arch/x86/mm"),
    ("kernel", "TSS and RSP0", "A 64-bit TSS descriptor supplies RSP0, the kernel stack used when an interrupt or syscall enters from CPL3; LTR loads the selector.", ["tss", "rsp0", "ltr"], "linux-7.3: arch/x86/kernel/cpu/common.c"),
    ("kernel", "GDT user descriptors", "Ring-3 code/data descriptors (DPL=3) are required before iretq can return to user mode; Koronos uses 0x1B data and 0x23 code selectors.", ["gdt", "dpl3", "iretq"], "project: kernel/arch/x86_64/user_entry.asm"),
    ("kernel", "SYSCALL/SYSRET", "MSR_STAR/LSTAR/SFMASK configure the fast system-call path; SYSCALL clobbers RCX (return RIP) and R11 (RFLAGS), so user stubs must preserve them.", ["syscall", "msr", "star"], "linux-7.3: arch/x86/entry/entry_64.S"),
    ("kernel", "INT 0x80 gate", "A DPL3 interrupt gate that saves CS, letting the kernel verify CS.RPL==3 as proof the call originated in user mode; Koronos uses it as the audit gate.", ["int80", "cpl3", "audit"], "project: kernel/core/target_launch.cpp"),
    ("kernel", "Physical frame allocator", "Bitmap/buddy allocator over the Multiboot2 memory map; Koronos rejects RAM above the 4 GiB bootstrap ceiling and reserves the framebuffer range.", ["frame-allocator", "memory-map"], "project: kernel/core/frame_allocator.cpp"),
    ("kernel", "ELF64 loading", "Validate e_ident/e_machine/e_type, iterate PT_LOAD, honour p_vaddr/p_filesz/p_memsz, zero BSS, honour PF_W/PF_X for W^X, reject overlap and overflow.", ["elf64", "w^x", "loader"], "project: kernel/core/process_loader.cpp"),
    ("kernel", "Interrupt descriptor table", "256 gates; each entry carries handler offset, segment selector, IST index and DPL. Koronos keeps ring-3 gates closed until TSS/stack/address space are ready.", ["idt", "ist"], "project: kernel/core/interrupt.cpp"),
    ("kernel", "APIC and PIT", "The 8254 PIT provides a calibration heartbeat; the local APIC timer drives per-CPU preemption. Koronos uses a PIT deadline to abort runaway ring-3 processes.", ["pit", "apic", "timer"], "project: kernel/core/timer.cpp"),
    ("kernel", "Scheduler", "Priority-ordered run queues with per-CPU snapshots; `make`-time config selects round-robin vs priority mode. Linux 7.x uses EEVDF, Koronos keeps a simpler deterministic policy.", ["scheduler", "eevdf"], "linux-7.3: kernel/sched/fair.c"),
    ("kernel", "Kbuild/Kconfig", "Linux-style build: per-directory Kbuild fragments (obj-y/obj-m), Kconfig symbols, savedefconfig, modules_install and DESTDIR install targets.", ["kbuild", "kconfig", "make"], "linux-7.3: Documentation/kbuild"),
    ("kernel", "printk-style tagging", "Koronos prefixes console lines ([KRN ], [RUN ], [SCH ], [MM  ], [AI  ]) so boot traces can be asserted mechanically, like dmesg tags on Linux.", ["logging", "trace"], "project"),
    # ---------------- drivers / hardware ----------------
    ("driver", "PCI enumeration", "Walk bus/device/function, read vendor/device/class from config space, size BARs, assign memory windows, then bind a driver by class/vendor id.", ["pci", "bar", "enumeration"], "linux-7.3: drivers/pci"),
    ("driver", "virtio", "Paravirtual device family (net, blk, console, gpu) with split virtqueues, descriptor rings and a status handshake; the transport is PCI or MMIO.", ["virtio", "virtqueue", "qemu"], "linux-7.3: drivers/virtio"),
    ("driver", "AHCI/SATA", "Host controller with per-port command lists and FIS packets; identify-device returns the model string used in storage inventories.", ["ahci", "sata", "storage"], "linux-7.3: drivers/ata"),
    ("driver", "NVMe", "Queue-pair based block protocol over PCIe: admin and I/O submission/completion queues, PRP/SGL data pointers, doorbell registers.", ["nvme", "pcie"], "linux-7.3: drivers/nvme"),
    ("driver", "xHCI USB", "Extensible host controller: device slots, transfer rings, endpoint contexts; keyboards and mass storage are the usual first targets.", ["usb", "xhci"], "linux-7.3: drivers/usb/host"),
    ("driver", "Framebuffer console", "Multiboot2 framebuffer tag gives address, pitch, width/height and bpp; a linear framebuffer blitter plus an 8x16 font draws the console.", ["framebuffer", "console", "font"], "project: kernel/drivers/builtin/pc-display.cpp"),
    ("driver", "ACPI tables", "RSDP -> RSDT/XSDT -> MADT (interrupt controllers), FADT (power), DSDT (device tree); required for APIC and power management.", ["acpi", "madt", "rsdp"], "linux-7.3: drivers/acpi"),
    ("driver", "Serial 16550 UART", "Port-mapped UART: divisor latch sets baud, line status bit 5 means transmit-hold-empty; COM1 is 0x3F8 and is the usual debug console.", ["uart", "serial", "com1"], "linux-7.3: drivers/tty/serial/8250"),
    ("driver", "isa-debugcon", "QEMU's port 0xE9 debug console: one `outb` per character, captured with -debugcon file:...; the acceptance traces use it.", ["qemu", "debugcon", "trace"], "project: tools/boot"),
    # ---------------- toolchains / languages ----------------
    ("toolchain", "GCC for freestanding code", "Flags that matter: -ffreestanding -fno-builtin -fno-stack-protector -fno-pic -fno-pie -mno-red-zone -mno-sse -mcmodel=kernel|large; link with -nostdlib.", ["gcc", "freestanding", "flags"], "linux-7.3: Makefile"),
    ("toolchain", "LLVM/Clang", "Clang can build Linux and freestanding kernels; lld links faster than GNU ld, and -fuse-ld=lld is the usual switch. Cross targets use --target=<triple>.", ["clang", "llvm", "lld"], "linux-7.3: Documentation/kbuild/llvm.rst"),
    ("toolchain", "GNU as / NASM", "GAS uses AT&T syntax by default (.intel_syntax available); NASM uses Intel syntax with `bits 64`, `global`, `section .text`. Koronos assembles with NASM.", ["nasm", "gas", "assembly"], "project: kernel/build-koronos.sh"),
    ("toolchain", "Linker scripts", "SECTIONS, ENTRY, PHDRS and OUTPUT_FORMAT control segment layout; a kernel script pins the load address and drops .eh_frame/.comment.", ["ld", "linker-script"], "project: kernel/arch/x86_64/koronos.ld"),
    ("toolchain", "objcopy/readelf/nm", "objcopy converts ELF<->binary and sets arch flags; readelf -lW proves PT_LOAD flags; nm checks exported symbols in the acceptance gates.", ["binutils", "elf", "readelf"], "project"),
    ("toolchain", "Cross compilation", "Use a triplet (aarch64-linux-gnu-, riscv64-linux-gnu-, powerpc64le-linux-gnu-) with --sysroot; Debian packages gcc-<triplet>.", ["cross", "triplet", "sysroot"], "linux-7.3: Documentation/kbuild"),
    ("language", "C (freestanding)", "No hosted libc: provide memset/memcpy/memmove, avoid TLS and constructors, and never assume a stack protector or red zone.", ["c", "freestanding"], "project"),
    ("language", "C++ in a kernel", "-fno-exceptions -fno-rtti -fno-threadsafe-statics; avoid new/delete or provide a pool; virtual dispatch is fine but adds vtables to .rodata.", ["c++", "rtti", "exceptions"], "project: kernel/build-koronos.sh"),
    ("language", "Rust for kernels", "no_std + core, panic handler, custom allocator; Linux 7.x supports Rust in drivers and core subsystems.", ["rust", "no_std"], "linux-7.3: rust/"),
    ("language", "Python tooling", "Build/verify scripts use stdlib only so CI images stay small; type hints + dataclasses keep schemas honest without dependencies.", ["python", "tooling"], "project"),
    # ---------------- desktop / userspace ----------------
    ("desktop", "Aurora shell", "Multi-profile HTML/JS desktop (Jasper/Windows-like, Gates/macOS-like, Aurora/Linux-like, Marine) rendered by WebKit in the Linux live session.", ["aurora", "webkit", "desktop"], "project: desktop/aurora-shell"),
    ("desktop", "WebKitGTK kiosk", "GTK3 window + WebKit2 WebView, undecorated fullscreen, hardware acceleration disabled for software rendering on VMs.", ["webkitgtk", "gtk3", "kiosk"], "project: live-image/lib/aurora-kiosk.py"),
    ("desktop", "X11 session", "startx from tty1 autologin, openbox as WM, feh for wallpapers; Ctrl+Alt+F2 reaches a text console, Ctrl+Q quits the kiosk.", ["x11", "openbox", "feh"], "project: live-image/build.sh"),
    ("desktop", "Wayland", "Compositor-owned input and buffers; clients speak xdg-shell. Aurora's Wayland profile is a visual skin, not a native compositor.", ["wayland", "xdg-shell"], "project"),
    ("userspace", "init contract", "One userspace init per boot, selected by the bootloader, running at CPL3 with its own CR3; it must emit its own readiness marker.", ["init", "pid1", "ring3"], "project: kernel/targets"),
    ("userspace", "syscall ABI", "Koronos native semantic IDs include EXIT=1, GETPID=2, YIELD=3, TIME_TICKS=4 and WRITE=9. The x86-64 SYSCALL entry translates a limited Linux ABI subset: WRITE=1, GETPID=39 and EXIT=60; unsupported calls return ENOSYS.", ["syscall", "abi"], "project: kernel/core/syscall.cpp + kernel/core/compat.cpp"),
    # ---------------- Linux 7.x reference ----------------
    ("linux", "Linux 7.3 release", "Linux 7.3 released 18 October 2026 (7.3.1 stable 30 October 2026); 7.2 is in stable maintenance, 6.18 and 6.12 are LTS lines.", ["linux", "release", "7.3"], "kernel.org / endoflife.date"),
    ("linux", "Linux boot protocol", "The x86 boot protocol hands the kernel a boot_params structure with memory map, initrd address and command line; bzImage is self-decompressing.", ["linux", "boot", "bzimage"], "linux-7.3: Documentation/arch/x86/boot.rst"),
    ("linux", "Linux init/main.c", "start_kernel() sets up traps, memory, scheduler, IRQs, then rest_init() spawns PID 1 which execs /sbin/init or /init from initramfs.", ["linux", "start_kernel", "init"], "linux-7.3: init/main.c"),
    ("linux", "Linux driver model", "bus/driver/device matching via IDs, probe()/remove(), devres-managed resources, and module_init/module_exit registration macros.", ["linux", "driver-model", "probe"], "linux-7.3: drivers/base"),
    ("linux", "Linux VFS", "super_block/dentry/inode/file abstractions with per-filesystem operations vectors; page cache and writeback sit below them.", ["linux", "vfs"], "linux-7.3: fs/"),
    ("linux", "Linux scheduler (EEVDF)", "Earliest Eligible Virtual Deadline First replaced CFS in 6.6+: per-task lag/virtual deadline, per-CPU runqueues, load balancing via sched domains.", ["linux", "eevdf", "sched"], "linux-7.3: kernel/sched/fair.c"),
    ("linux", "Linux Kbuild", "make defconfig/menuconfig, O= out-of-tree builds, per-directory Kbuild with obj-y/obj-m, and modules_install under /lib/modules/<release>.", ["linux", "kbuild"], "linux-7.3: Documentation/kbuild"),
]

CATEGORY_LABEL = {
    "arch": "CPU architecture",
    "boot": "boot and firmware",
    "kernel": "kernel subsystem",
    "driver": "hardware driver",
    "toolchain": "compiler, assembler, linker",
    "language": "programming language",
    "desktop": "desktop and session",
    "userspace": "userspace runtime",
    "linux": "Linux 7.x reference",
    "isa": "ISA instruction catalogue",
    "fs": "filesystem format",
}


def slug(value: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return s[:60]


def entry_id(category: str, topic: str) -> str:
    return f"{category}:{slug(topic)}"


def make_entry(category, topic, summary, tags, source) -> dict:
    return {
        "id": entry_id(category, topic),
        "category": category,
        "category_label": CATEGORY_LABEL.get(category, category),
        "topic": topic,
        "summary": summary,
        "tags": list(tags),
        "source": source,
        "confidence": "curated",
        "added": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
    }


def isa_entries() -> list[dict]:
    """Import the repository ISA catalogue (row-array format) as entries."""
    out = []
    path = os.path.join(ROOT, "isa", "isa_database.json")
    if not os.path.exists(path):
        return out
    try:
        data = json.load(open(path, encoding="utf-8"))
    except Exception:
        return out
    rows = data.get("instructions", [])
    for row in rows:
        if not isinstance(row, list) or len(row) < 5:
            continue
        arch, mnemonic, form, operands, syntax = row[0], row[1], row[2], row[3], row[4]
        bits = row[5] if len(row) > 5 else "?"
        out.append(make_entry(
            "isa",
            f"{arch} {mnemonic}",
            f"{syntax} — {form} form, operands: {', '.join(map(str, operands))}, {bits}-bit encoding.",
            [arch, mnemonic, form],
            "isa/isa_database.json (CHM-ISA-DB-4)",
        ))
    return out



# --------------------------------------------------------------------------
# Generated coverage: every architecture's toolchain/ABI boundary, every
# language's systems role, the driver families and the filesystem formats.
# These are templated from documented facts so coverage stays even; the source
# column points at where the claim comes from.
# --------------------------------------------------------------------------
ARCH = [
 ("x86_64","x86","GNU as (AT&T) or NASM (Intel)","x86_64-linux-gnu","`syscall` (MSR_LSTAR) / legacy `int 0x80`","4 KiB pages, 4- or 5-level paging","GRUB Multiboot2, UEFI PE/COFF, bzImage","RDX/RSI/RDI/R10/R8/R9 then stack; RCX and R11 clobbered by syscall"),
 ("i386","x86","GNU as or NASM","i386-linux-gnu","`int 0x80` / `sysenter`","4 KiB pages, PAE optional","Multiboot 1/2, bzImage","EAX number, EBX/ECX/EDX/ESI/EDI/EBP args"),
 ("aarch64","arm64","GNU as or LLVM MC","aarch64-linux-gnu","`svc #0`","4/16/64 KiB granules, TTBR0/TTBR1","UEFI stub + device tree, arm64 Image","X0-X5 args, X8 number, SVC immediate 0"),
 ("armv7","arm","GNU as","arm-linux-gnueabihf","`svc #0` (ARM and Thumb)","4 KiB, short-descriptor tables","U-Boot, device tree, zImage","R0-R6 args, R7 number"),
 ("riscv64","riscv","GNU as or LLVM MC","riscv64-linux-gnu","`ecall` (SBI or S-mode)","Sv39/Sv48/Sv57, 4 KiB base","OpenSBI + device tree, Image","A0-A5 args, A7 number"),
 ("riscv32","riscv","GNU as","riscv32-linux-gnu","`ecall`","Sv32 two-level paging","U-Boot/OpenSBI","A0-A5 args, A7 number"),
 ("ppc64le","powerpc","GNU as","powerpc64le-linux-gnu","`sc` (system call)","Hash MMU or radix tree, 64 KiB pages typical","OPAL/skiboot, PPC64 ELF v2","R3-R10 args, R0 number"),
 ("s390x","s390","GNU as (HLASM-compatible mnemonics)","s390x-linux-gnu","`svc 0`","DAT (dynamic address translation), 4 KiB","zipl + LPAR/z/VM","R2-R7 args, R1 number"),
 ("loongarch64","loongarch","GNU as","loongarch64-linux-gnu","`syscall 0`","16 KiB pages typical","UEFI + device tree","A0-A7 args, A7 number"),
 ("mips64le","mips","GNU as","mips64el-linux-gnuabi64","`syscall`","4/16/64 KiB, TLB-based","U-Boot ELF, device tree","A0-A3 args, V0 number"),
 ("sparc64","sparc","GNU as","sparc64-linux-gnu","`ta 0x6d` (trap always)","8 KiB pages, sun4v/sun4u MMU","OpenBoot/GRUB IEEE1275","O0-O5 args, G1 number"),
 ("wasm32","wasm","WAT or LLVM MC","wasm32-unknown-unknown","host sandbox call (no rings)","linear memory, 64 KiB pages","browser/WASI host","no register ABI; values on the operand stack"),
]
LANGS = [
 ("C","C11/C17 freestanding","kernel and userspace payloads in this tree","gcc -ffreestanding"),
 ("C++","C++17 freestanding","Koronos kernel core","g++ -fno-exceptions -fno-rtti"),
 ("Rust","no_std","Linux 7.x drivers and core subsystems; not used by Koronos yet","rustc --target <triple> -C panic=abort"),
 ("Zig","freestanding","can target bare metal via build.zig, no runtime","zig build-obj -target x86_64-freestanding"),
 ("Go","runtime-based","not suitable for ring-0 without a custom runtime; userspace tooling only","go build"),
 ("Ada/SPARK"," Ravenscar profile","formal-verification friendly embedded work","gnatmake"),
 ("Fortran","scientific","userspace numerics, not kernel","gfortran"),
 ("Python","CPython 3","image build, verification and knowledge tooling","python3"),
 ("JavaScript/TypeScript","WebKit/Node","Aurora desktop shell","node / WebKit2"),
 ("Java","JVM","CPU4096 simulator and hosted tools","javac"),
 ("x86 assembly","NASM/GAS","entry stubs, GDT/TSS setup, ring-3 trampoline","nasm -f elf64"),
 ("ARM assembly","GAS","AArch64 entry and vector tables","aarch64-linux-gnu-as"),
]
DRIVERS = [
 ("virtio-blk","Virtqueue-backed block device; sector reads via descriptor chains, used by QEMU images.","virtio"),
 ("virtio-net","Virtqueue RX/TX pairs with a MAC from the device config space.","virtio"),
 ("e1000","Intel 8254x PCI NIC; descriptor rings, EEPROM MAC, MMIO registers.","net"),
 ("rtl8139","Realtek 8139 PCI NIC; simple RX/TX buffer model, common in emulators.","net"),
 ("bochs-vga","QEMU default VGA; the Multiboot2 framebuffer tag supersedes programming it directly.","display"),
 ("PS/2 keyboard","i8042 controller, scan code set 1/2, IRQ1; the classic fallback input path.","input"),
 ("HPET","High Precision Event Timer, MMIO comparators; alternative to the PIT for calibration.","timer"),
 ("IOAPIC","Routes PCI/legacy interrupts to LAPIC vectors; programmed through the MADT.","interrupt"),
 ("SMP trampoline","APs start in real mode at a SIPI vector; a 16-bit trampoline switches them to long mode.","smp"),
 ("UEFI GOP","Graphics Output Protocol gives a linear framebuffer before ExitBootServices.","firmware"),
 ("SMBIOS","DMI tables describe the board, BIOS and memory modules.","firmware"),
 ("TPM 2.0","CRB/TIS interface, PCR extend and seal/unseal for measured boot.","security"),
 ("USB mass storage","BOT/SCSI over xHCI bulk endpoints.","usb"),
 ("AHCI port","Per-port command list, FIS-based DMA, hot-plug via port interrupt status.","storage"),
 ("NVMe admin queue","Identify Controller/Namespace, then create I/O queue pairs.","storage"),
 ("PCIe ECAM","MMCONFIG window maps 4 KiB per function; replaces legacy 0xCF8/0xCFC.","pci"),
 ("MSI/MSI-X","Message-signalled interrupts written to the LAPIC; MSI-X adds per-vector table entries.","interrupt"),
 ("IOMMU (VT-d)","DMA remapping tables let the kernel confine device access to owned frames.","security"),
 ("ACPI S5","FADT supplies the PM1a/PM1b control values that power the machine off.","power"),
 ("RTC (CMOS)","MC146818 registers 0x00-0x0D hold time and date; update-in-progress flag guards reads.","timer"),
]
FS = [
 ("ext4","journaled Linux filesystem; extent trees, 4 KiB blocks, journal replay.","fs"),
 ("FAT32","simple BPB-described filesystem used on EFI system partitions.","fs"),
 ("ISO9660 + Rock Ridge","optical layout used by the release images; El Torito adds the boot record.","fs"),
 ("squashfs","read-only compressed filesystem used by the Linux live image (xz + BCJ).","fs"),
 ("cpio newc","archive format of initramfs images (gzip-compressed).","fs"),
 ("tar","source snapshot archive stored on the ISO for provenance.","fs"),
]

def add(entries, cat, topic, summary, tags, source):
    e = kb.make_entry(cat, topic, summary, tags, source)
    entries.setdefault(e["id"], e)


def expand_seed(entries: dict) -> None:
    for row in SEED:
        e = make_entry(*row)
        entries.setdefault(e["id"], e)
    for e in isa_entries():
        entries.setdefault(e["id"], e)
    for (name, fam, asm, triple, syscall, paging, boot, abi) in ARCH:
        e = make_entry("arch", f"{name} toolchain",
                       f"{name}: assembler {asm}; GCC triplet {triple}; syscall entry {syscall}; paging {paging}; boot {boot}; ABI {abi}.",
                       [name, fam, "toolchain"], "linux-7.3 arch documentation / project")
        entries.setdefault(e["id"], e)
        e = make_entry("arch", f"{name} user/kernel boundary",
                       f"{name} crosses to CPL0 with {syscall} and keeps a per-process address space; the ABI is {abi}.",
                       [name, "syscall", "privilege"], "linux-7.3 arch documentation")
        entries.setdefault(e["id"], e)
    for (lang, mode, use, build_cmd) in LANGS:
        e = make_entry("language", f"{lang} in systems work",
                       f"{lang} ({mode}): {use}. Typical build: {build_cmd}.",
                       [lang.lower(), "language", mode], "project / linux-7.3")
        entries.setdefault(e["id"], e)
    for (name, summary, tag) in DRIVERS:
        e = make_entry("driver", name, summary, [tag, "driver"], "linux-7.3 drivers/ (reference model) / project")
        entries.setdefault(e["id"], e)
    for (name, summary, tag) in FS:
        e = make_entry("fs", name, summary, [tag, "filesystem"], "linux-7.3 fs/ (reference model)")
        entries.setdefault(e["id"], e)


def build(db_path: str) -> dict:
    entries = {}
    expand_seed(entries)
    db = {
        "schema_version": SCHEMA_VERSION,
        "name": "chimera-octavian-knowledge-db",
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "generator": "tools/ai/knowledge_db.py",
        "categories": CATEGORY_LABEL,
        "entry_count": len(entries),
        "notes": "Curated retrieval corpus for the embedded AI module. Appending a validated entry is the learning step; no model weights are stored.",
        "entries": sorted(entries.values(), key=lambda e: (e["category"], e["topic"])),
    }
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    with open(db_path, "w", encoding="utf-8") as fh:
        json.dump(db, fh, indent=1, ensure_ascii=False)
        fh.write("\n")
    return db


def load(db_path: str) -> dict:
    with open(db_path, encoding="utf-8") as fh:
        return json.load(fh)


def validate(db_path: str) -> int:
    db = load(db_path)
    problems = []
    if db.get("schema_version") != SCHEMA_VERSION:
        problems.append(f"schema_version != {SCHEMA_VERSION}")
    seen = set()
    for e in db.get("entries", []):
        for key in ("id", "category", "topic", "summary", "source"):
            if not e.get(key):
                problems.append(f"entry missing {key}: {e.get('id')}")
        if e["id"] in seen:
            problems.append(f"duplicate id {e['id']}")
        seen.add(e["id"])
    if db.get("entry_count") != len(seen):
        problems.append(f"entry_count {db.get('entry_count')} != actual {len(seen)}")
    if problems:
        print("INVALID:", *problems, sep="\n  ", file=sys.stderr)
        return 1
    cats = {}
    for e in db["entries"]:
        cats[e["category"]] = cats.get(e["category"], 0) + 1
    print(f"OK: {len(seen)} entries, schema {db['schema_version']}, {len(cats)} categories")
    for c, n in sorted(cats.items()):
        print(f"  {c:<12} {n}")
    return 0


def append(db_path: str, payload: dict) -> int:
    db = load(db_path)
    incoming = payload.get("entries") if "entries" in payload else [payload]
    added, skipped = [], []
    by_id = {e["id"]: e for e in db["entries"]}
    for item in incoming:
        category = item.get("category")
        topic = item.get("topic")
        if category not in CATEGORY_LABEL or not topic or not item.get("summary"):
            print(f"skip (incomplete): {item}", file=sys.stderr)
            continue
        e = {
            "id": item.get("id") or entry_id(category, topic),
            "category": category,
            "category_label": CATEGORY_LABEL[category],
            "topic": topic,
            "summary": item["summary"],
            "tags": item.get("tags", []),
            "source": item.get("source", "user-request"),
            "confidence": item.get("confidence", "user-supplied"),
            "added": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        }
        if e["id"] in by_id:
            skipped.append(e["id"])
            continue
        by_id[e["id"]] = e
        added.append(e["id"])
    db["entries"] = sorted(by_id.values(), key=lambda x: (x["category"], x["topic"]))
    db["entry_count"] = len(db["entries"])
    db["generated_utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with open(db_path, "w", encoding="utf-8") as fh:
        json.dump(db, fh, indent=1, ensure_ascii=False)
        fh.write("\n")
    print(f"appended {len(added)}, skipped {len(skipped)} (already present); total {db['entry_count']}")
    return 0


def query(db_path: str, text: str, limit: int) -> int:
    db = load(db_path)
    terms = [t for t in re.split(r"\W+", text.lower()) if t]
    scored = []
    for e in db["entries"]:
        hay = " ".join([e["topic"], e["summary"], " ".join(e["tags"]), e["category"]]).lower()
        score = sum(hay.count(t) for t in terms)
        if score:
            scored.append((score, e))
    scored.sort(key=lambda x: -x[0])
    for score, e in scored[:limit]:
        print(f"[{score}] {e['id']} — {e['topic']}\n     {e['summary'][:180]}\n     src: {e['source']}")
    if not scored:
        print("no matches")
    return 0


def export_c(db_path: str, out_path: str) -> int:
    """Emit a tiny C header so the kernel can report the corpus it carries."""
    db = load(db_path)
    digest = hashlib.sha256(json.dumps(db["entries"], sort_keys=True).encode()).hexdigest()
    counts = {}
    for e in db["entries"]:
        counts[e["category"]] = counts.get(e["category"], 0) + 1
    lines = [
        "/* generated by tools/ai/knowledge_db.py — do not edit */",
        "#ifndef CHIMERA_KNOWLEDGE_DB_INDEX_H",
        "#define CHIMERA_KNOWLEDGE_DB_INDEX_H",
        f'#define CHIMERA_KB_SCHEMA {db["schema_version"]}',
        f'#define CHIMERA_KB_ENTRIES {db["entry_count"]}',
        f'#define CHIMERA_KB_CATEGORIES {len(counts)}',
        f'#define CHIMERA_KB_DIGEST "{digest}"',
    ]
    for cat, n in sorted(counts.items()):
        lines.append(f'#define CHIMERA_KB_COUNT_{cat.upper().replace("-", "_")} {n}')
    lines += ["#endif", ""]
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    open(out_path, "w", encoding="utf-8").write("\n".join(lines))
    print(f"wrote {out_path} ({db['entry_count']} entries, digest {digest[:16]})")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=["build", "validate", "stats", "query", "append", "export-c"])
    ap.add_argument("argument", nargs="?")
    ap.add_argument("--db", default=DEFAULT_DB)
    ap.add_argument("--out", default=None)
    ap.add_argument("--json", default=None)
    ap.add_argument("--file", default=None)
    ap.add_argument("--limit", type=int, default=8)
    args = ap.parse_args()

    if args.command == "build":
        db = build(args.out or args.db)
        print(f"built {args.out or args.db}: {db['entry_count']} entries")
        return validate(args.out or args.db)
    if args.command == "validate":
        return validate(args.db)
    if args.command == "stats":
        return validate(args.db)
    if args.command == "query":
        return query(args.db, args.argument or "", args.limit)
    if args.command == "append":
        payload = json.loads(args.json) if args.json else json.load(open(args.file, encoding="utf-8"))
        return append(args.db, payload)
    if args.command == "export-c":
        return export_c(args.db, args.out or os.path.join(ROOT, "kernel", "generated", "knowledge_db_index.h"))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
