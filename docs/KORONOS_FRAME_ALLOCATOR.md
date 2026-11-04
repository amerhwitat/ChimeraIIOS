# Koronos frame allocator: first implementation slice

Status: implemented as a bounded x86-64 bootstrap allocator; CI and QEMU validation are pending.

## Scope

This change adds a bitmap physical-frame allocator to ChimeraIIOS main and wires it into the canonical Koronos build and boot initialization. It is intentionally limited to the existing low-4-GiB bootstrap physical mapping contract.

## Ownership rules

- Usable frames come only from Multiboot2 memory-map entries whose type is usable RAM.
- Low 1 MiB, the kernel image, the Multiboot2 information block, boot modules and framebuffer memory are reserved before allocation is enabled.
- Allocation marks every frame allocated under a spinlock. Free validates the complete requested run before changing any bit, so partial frees cannot occur.
- Double-free, unaligned, low-memory and out-of-range frees are rejected. Reserved kernel pages are reported as not allocator-owned and cannot be returned to the free pool.
- Overlapping usable memory-map entries cannot inflate the free-page count because already-free/allocated bits are checked.
- Framebuffer reservations are applied after memory-map discovery, so Multiboot2 tag ordering does not accidentally make the framebuffer allocatable.
- Malformed tags, malformed entry sizes, arithmetic overflow, missing memory map/end tags and unsupported RAM above the 4-GiB limit fail initialization.

## Explicit limitation

This is not yet a general physical-memory manager. It does not support memory above 4 GiB, NUMA zones, hotplug, DMA-specific pools, or physical-to-virtual conversion. The boot path logs an explicit allocator-unavailable diagnostic when the map violates the current contract. It does not silently truncate high RAM.

The allocator returns physical addresses. Callers must not dereference them unless the active bootstrap mapping proves that the physical address is directly mapped. The address-space backend is deliberately not introduced by this slice.

## Tests added

- Synthetic Multiboot2 map parsing.
- Frame allocation and free accounting.
- Double-free rejection.
- Alignment and low-memory reservation checks.
- Framebuffer reservation despite an overlapping usable-RAM entry.
- Explicit rejection of usable RAM above 4 GiB.

The host tests are registered with CTest as `chimera_frame_allocator` and `chimera_frame_allocator_rejects_above_4g`.

## Still blocked

This slice does not implement safe page-table ownership, transactional ELF loading, per-CPU TSS/syscall entry, process-owned kernel stacks, saved task contexts, scheduling, wait/exit, or SMP TLB shootdowns. It must not be used to enable ring-3 target launch or production userspace readiness. QEMU BIOS/UEFI and fault-injection tests remain required.
