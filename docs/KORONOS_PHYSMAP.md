# Koronos physical mapping contract

Status: bootstrap identity-map verifier and checked physical-to-virtual API implemented; full address-space/process lifecycle remains incomplete.

## Verified bootstrap layout

The x86-64 Multiboot2 entry path builds:
- one PML4 with only entry 0 present;
- one PDPT with only entry 0 present;
- one four-page page directory containing 2,048 supervisor-only, writable 2-MiB large-page entries;
- an exact identity mapping of physical addresses [0, 4 GiB).

`koronos_physmap_init()` reads CR3 and validates this complete layout before setting the mapping-ready flag. It rejects unexpected higher-level entries, user-accessible identity leaves, missing large pages, and non-identity physical bases.

## API contract

- `koronos_physmap_validate_range(physical, length)` rejects zero-length, overflow, and out-of-range spans.
- `koronos_phys_to_virt(physical, length)` returns an identity alias only after the full bootstrap map has been verified.
- Callers must not use raw physical addresses as pointers.
- The current supported mapping ceiling is 4 GiB; this API does not yet provide arbitrary high-memory direct-map or temporary mapping support.

## Integration

Koronos verifies the page tables before initializing the frame allocator. The allocator is not enabled if the bootstrap map does not satisfy the contract. The host range test checks boundaries and confirms that translation is unavailable before initialization.

OctavianOS has the same source/header and uses this API for address-space page-table and frame aliases. Its address-space backend remains a bounded bootstrap implementation, not a scheduler-owned multi-process runtime. It still needs transactional rollback tests, active-CR3/TLB lifecycle, per-CPU transition state and process ownership.

## Remaining work

The next layer must make page-table frame ownership transactional, preserve kernel mappings intentionally, and guarantee rollback on every allocation or mapping failure. Then the ELF loader, user entry and scheduler-owned task lifecycle can be integrated. No readiness gate is changed by this work.

## Transactional ELF loader dependency

The adjacent `process_loader.cpp` now enforces a user virtual-address floor of 4 GiB and requires page-aligned stack sizes. It validates the complete PT_LOAD plan before creating an address space, rejects W+X and page-rounded overlaps, zeroes BSS and stack memory, and destroys the staged address space if any segment or stack mapping fails. Its output structure is published only after the complete image has been prepared.

Host regressions cover successful copy/BSS/stack setup, segment-map failure, stack-map failure, invalid stack alignment, W+X, page overlap and low-address rejection. The tests use a mock mapper: they validate loader transaction behavior, not real page-table teardown or hardware TLB behavior.
