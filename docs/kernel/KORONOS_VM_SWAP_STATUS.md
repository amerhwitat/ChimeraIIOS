# Koronos virtual memory and swap implementation status

Date: 2026-10-23  
Branch: `audit/koronos-cross-os-syscall-roadmap-20261023`

## Implemented in this change

- Added a versioned `chimera/swap.h` C ABI with backend callbacks for exact 4 KiB reads and writes.
- Added a bounded swap-slot manager with allocation/release, per-page CRC-32 integrity verification, I/O error accounting, capacity bounds, and a status snapshot. Backend reads/writes now run outside the metadata spinlock; per-slot in-flight states prevent release/reinitialization races, and a regression callback queries the snapshot during I/O to catch lock-held I/O deadlocks.
- Swap starts disabled and is enabled only when a caller provides a valid backend. This deliberately avoids treating RAM or an unconfigured device as persistent swap.
- Added host regression coverage for invalid initialization, allocation/store/load/release, I/O failure rollback, and corruption detection.
- Integrated the implementation, test, and required-symbol checks into `kernel/build-koronos.sh`.

## Important limitation

This is **not** a complete virtual-memory manager or Windows `Page.sys` equivalent. Address-space map/unmap/protect/query entry points now exist, but unmap/protect fail closed until a real synchronous all-CPU TLB-shootdown callback is registered. The implementation still uses a fixed address-space table, fixed mapping records, contiguous physical allocations, and a 512 MiB per-space limit; mapping metadata is not yet generation-safe, and empty intermediate page-table frames are not reclaimed on unmap. Per-page metadata now records resident/swapped/loading/evicting state, pin count, dirty/reference flags, and swap slot; pin/unpin is integrated around native file read/write and console/path user-memory accesses, and unmap rejects pinned pages. However, no page-fault-driven state transitions, eviction policy, swap-in/out PTE transitions, or storage-driver-backed boot-time swap discovery are implemented. The strengthened DAPS gate now requires trace evidence for those operations and failure paths; the current implementation cannot satisfy it, so production closeout remains blocked.

## Required next milestones

1. Complete address-space control: add host/kernel tests for map/unmap/protect/query, reclaim empty intermediate page-table frames, bind mapping descriptors to per-space generations, and implement/register the real synchronous SMP TLB-shootdown callback. The boot self-test now checks query, overlap rejection without frame loss, and pin/unpin balance. The current callback is only an explicit contract; no production callback is registered.
2. Finish per-page metadata integration by adding owner address-space generations and page-replacement reference/dirty consumption; current pinning protects native syscall copy-in/out, but eviction is not implemented and no code transitions metadata into SWAPPED/EVICTING/LOADING.
3. Implement page-fault resolution and a bounded page-replacement policy. A page may transition to swapped only after successful full-page backend write; failed write must leave the resident mapping intact.
4. Implement swap-in as read → checksum verify → allocate resident frame → populate frame → install PTE → invalidate TLB → release swap slot, with rollback on every failure.
5. Add SMP-safe TLB shootdown and page-table locking before enabling eviction on multiple CPUs.
6. Discover and validate a real swap backend through the storage stack; never assume a disk, partition, or pagefile exists.
7. Test exhaustion, fragmentation, repeated swap cycles, corrupt pages, I/O failures, concurrent faults, teardown, and no leaked frames/slots.
8. Run BIOS/UEFI boot acceptance and the unchanged DAPS production evidence gate.

## Check → Plan → Do → Act

- **Check:** audited current frame allocator and address-space limits; no complete swap implementation was present.
- **Plan:** isolate storage I/O behind a small ABI and test it independently before connecting page-fault eviction.
- **Do:** add the bounded, checksummed swap backend, avoid blocking storage I/O under its spinlock, make ELF mapping transactional, add compact per-page metadata and syscall pinning, expose guarded address-space control operations, and wire swap/control symbols into the canonical build.
- **Act:** exact-head CI must compile/link the new APIs and run the swap regression. Demand paging, per-page pinning, page-fault swap-in/out, storage discovery, SMP TLB shootdown, and full production VM acceptance remain blocked until the milestones above pass.
