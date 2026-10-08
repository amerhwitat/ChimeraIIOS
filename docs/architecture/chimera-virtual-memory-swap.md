# Chimera II virtual memory and swap/pagefile roadmap

The OS must distinguish logical register width, virtual-address width, physical-address width, and bus transaction width. A configurable N-bit ISA does not create infinite RAM. Every address space needs explicit valid ranges, physical mappings, page sizes, permissions and quotas.

## Page lifecycle
1. Reserve a virtual region with permissions and backing object.
2. Resolve faults only after validating region and access rights.
3. Allocate a zeroed frame, load file-backed bytes, zero-fill BSS, or restore a checked swap slot.
4. Update page tables and perform architecture-required TLB invalidation.
5. On eviction, reject pinned/kernel/MMIO pages; write dirty anonymous pages to an allocated swap slot before revoking mappings.
6. Validate page checksums on page-in; I/O errors become controlled process faults, never uninitialized memory.
7. On process exit/swapoff, drain I/O, release slots/frames and scrub data per policy.

The reference utility tools/memory/chimera_swap.py uses fixed 4096-byte slots and CRC32 corruption detection. It is not a live pager: no page tables, page-fault handler, eviction policy, asynchronous I/O, encryption, crash recovery, slot bitmap or resume protocol.

Production requirements include demand paging, per-process address spaces, copy-on-write, dirty-page writeback, swap allocation and exhaustion handling, crash-safe metadata, optional authenticated encryption, I/O error handling, TLB shootdown, swapoff/drain and secure zeroing. Swap is not RAM and may be disabled. Chimera should define its own semantics instead of pretending to implement Linux swap or Windows pagefile internals.
