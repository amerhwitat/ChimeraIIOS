# Linux 7.x → Chimera II architecture crosswalk

Requested reference root: `https://elixir.bootlin.com/linux/v7.2.2/source`.

Automated access to Bootlin can be blocked by robots policy. Linux 7.2 itself is an upstream release; the Linux repository records the 7.2 release in August 2026. The upstream tree contains major top-level subsystems including `arch`, `kernel`, `mm`, `fs`, `net`, `drivers`, `ipc`, `security`, `virt`, `io_uring`, and related infrastructure.

| Linux concept | Chimera II target |
|---|---|
| `arch/` | `arch/` + ISA adapters |
| `kernel/` | `kernel/` scheduler, IRQ, syscall core |
| `mm/` | `kernel/mm/` / MemoryManager |
| `fs/` | `kernel/vfs/` + TensorFS |
| `net/` | `kernel/net/` + Spotnik |
| `ipc/` | `kernel/ipc/` + SPSC/zero-copy channels |
| `drivers/` | `drivers/` + device model |
| `security/` | `kernel/security/` + CEF capabilities |
| `virt/` | `hypervisor/` + C8192 virtual machine |
| `io_uring` | `kernel/io/` asynchronous I/O boundary |
| `init/` | `boot/` + kernel initialization |
| `lib/` | `lib/` architecture-neutral primitives |
| `tools/` | `tools/` build, tracing, ISA and crawler utilities |

## Ten-level crawl model

Depth is defined as link/reference expansion from the supplied Bootlin source root. Level 0 is the root; level 10 is the maximum traversal depth. The crawler is bounded and records failures rather than silently treating blocked pages as empty.

## Implementation gaps addressed in this refresh

1. Unified ISA frontend and per-family decoders.
2. Kernel scheduler/task model.
3. Virtual-memory/page allocator boundary.
4. IRQ/syscall abstraction.
5. VFS/file-handle boundary.
6. Network packet abstraction.
7. Architecture-independent kernel API.
8. Async-I/O extension point.
9. Browser architecture explorer.
10. Source/provenance tooling.

This is a crosswalk and architecture scaffold, not a copied Linux implementation.
