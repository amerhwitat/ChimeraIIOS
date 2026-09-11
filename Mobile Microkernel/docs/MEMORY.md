# Mobile Memory Architecture

The mobile kernel uses a small privileged memory-management core and delegates policy-heavy allocation to userspace services.

The interface is designed for AArch64 and RISC-V64 address spaces, with hooks for ASIDs/VMIDs, IOMMU mappings, DMA-safe buffers, cache maintenance and memory pressure notification.

Large `RegisterN` and tensor state is not permanently pinned in kernel memory. Neural workloads remain userspace workloads and should use shared-memory or zero-copy IPC where safe.
