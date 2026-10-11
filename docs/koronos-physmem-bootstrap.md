# Koronos physical memory bootstrap allocator

The x86-64 Multiboot2 entry currently installs identity mappings for physical addresses below 4 GiB using 2-MiB PDEs. This allocator is intentionally limited to that range and is a prerequisite primitive, not a complete virtual-memory subsystem.

- Parses Multiboot2 memory-map tag type 6 with bounds and entry-size checks.
- Starts with no free pages; admits only full 4-KiB pages from type-1 usable RAM ranges.
- Reserves the first MiB, the kernel image/BSS range, the Multiboot2 information block, and module payload ranges.
- Tracks allocated pages separately to reject invalid frees and double-free.
- Fails closed if the memory map is absent or malformed.

It does **not** create user page tables, split the existing 2-MiB identity mappings, enforce NX/W^X, provide a higher-half kernel/direct map, or perform TLB invalidation. The generic ELF loader is not wired to this allocator until a page-table backend can safely provide writable kernel aliases and user mappings. AP startup, per-CPU TSS/interrupt stacks, ring-3 entry, and assembly context switching remain separate production blockers.
