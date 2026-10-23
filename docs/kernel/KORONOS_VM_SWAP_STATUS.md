# Koronos virtual memory and swap implementation status

Date: 2026-10-23  
Branch: `audit/koronos-cross-os-syscall-roadmap-20261023`

## Implemented in this change

- Added a versioned `chimera/swap.h` C ABI with backend callbacks for exact 4 KiB reads and writes.
- Added a bounded swap-slot manager with allocation/release, per-page CRC-32 integrity verification, I/O error accounting, capacity bounds, and a status snapshot.
- Swap starts disabled and is enabled only when a caller provides a valid backend. This deliberately avoids treating RAM or an unconfigured device as persistent swap.
- Added host regression coverage for invalid initialization, allocation/store/load/release, I/O failure rollback, and corruption detection.
- Integrated the implementation, test, and required-symbol checks into `kernel/build-koronos.sh`.

## Important limitation

This is the **swap storage backend foundation**, not a claim that full virtual-memory paging or a Windows `Page.sys` equivalent is finished. The current address-space implementation still uses a fixed address-space table, fixed mapping records, contiguous physical allocations, and a 512 MiB per-space limit. It does not yet implement a complete page-fault-driven demand-paging/eviction policy, swap-in/out PTE transitions, dirty/reference tracking, page replacement, TLB shootdown, or storage-driver-backed boot-time swap discovery. Those features must be implemented before this can be called a complete VM/swap system. The production DAPS verifier has also been strengthened to require a `vm_swap` evidence section proving page-fault handling, successful swap round-trip, I/O failure rollback, and corruption rejection with raw trace markers; the current backend-only implementation cannot satisfy that gate yet.

## Required next milestones

1. Extend the address-space contract with map/unmap/protect/query operations that update page tables and reclaim intermediate page-table frames safely.
2. Add per-page metadata (resident/swapped, permissions, dirty/reference bits, owner address-space generation) and pinning so syscall copy-in/out cannot race eviction.
3. Implement page-fault resolution and a bounded page-replacement policy. A page may transition to swapped only after successful full-page backend write; failed write must leave the resident mapping intact.
4. Implement swap-in as read → checksum verify → allocate resident frame → populate frame → install PTE → invalidate TLB → release swap slot, with rollback on every failure.
5. Add SMP-safe TLB shootdown and page-table locking before enabling eviction on multiple CPUs.
6. Discover and validate a real swap backend through the storage stack; never assume a disk, partition, or pagefile exists.
7. Test exhaustion, fragmentation, repeated swap cycles, corrupt pages, I/O failures, concurrent faults, teardown, and no leaked frames/slots.
8. Run BIOS/UEFI boot acceptance and the unchanged DAPS production evidence gate.

## Check → Plan → Do → Act

- **Check:** audited current frame allocator and address-space limits; no complete swap implementation was present.
- **Plan:** isolate storage I/O behind a small ABI and test it independently before connecting page-fault eviction.
- **Do:** add the bounded, checksummed swap backend and regression tests; wire them into the kernel build.
- **Act:** CI must compile and run the new tests. Demand paging and full production VM acceptance remain blocked until the milestones above pass.
