# Chimera II OS — Deep Boot-to-Aurora Runtime Gap Audit

## Critical gaps

1. Protected user processes: ELF validation exists, but PT_LOAD mappings, private address spaces, user stacks, ring-3 context switching, fault delivery, capability-space installation, and teardown are incomplete.
2. IPC isolation: endpoint IPC is currently an in-kernel bootstrap queue and must evolve to isolated service endpoints with blocking/wakeup semantics and per-process capability spaces.
3. Memory management: BuddyAllocator is a reservation stub; complete physical-page allocation, page tables/VMAR-like regions, guard pages, reclamation and COW are still required.
4. Aurora runtime: the session starts external Wayland components; native graphics/input service ownership is still incomplete.
5. Mobile: device-profile safety is present, but mobile init is a bootstrap wrapper and requires service supervision plus real ARM64 process/VM and device-driver support.
6. Service supervision: Kore/Nucleus/Hive/Aegis/Spotnik need explicit process IDs, IPC endpoints, capability manifests, restart policy and fault boundaries.

## Implemented now

- Protected-process admission/load-plan API validates ELF PT_LOAD ranges, entry/stack bounds and rejects W+X segments.
- Kernel build and CI gate the process layer.
- Endpoint send no longer executes a service callback inline in the sender's kernel path.
- Aurora launcher crosses an actual exec boundary.
- Boot-to-Aurora and Microkernel Mobile Edition contracts record ownership and remaining dependencies.

## Reference architecture

seL4: endpoint IPC, capabilities, capDL/loader and isolated address spaces.
Microkit: protection domains, memory regions and channels.
Zircon: process/thread objects, handles/rights, VMAR/VMO and userboot.
Redox: userspace schemes as message-passing service boundaries.

These are architectural references, not copied source.
