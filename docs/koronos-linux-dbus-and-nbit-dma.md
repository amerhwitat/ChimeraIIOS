# Koronos Linux D-Bus and N-bit DMA compatibility

D-Bus is userspace IPC, not a kernel facility that a freestanding kernel can link directly. The `dbus_compat.h` frame is a versioned, bounded ABI contract only. Real interoperability requires a Linux-compatible userspace proxy linked with libdbus or sd-bus, authentication, policy enforcement, message parsing and routing. None of those are claimed implemented by the kernel validator.

DMA uses the device's real 32-bit or 64-bit bus address mask. The current bootstrap mapper is an identity physical-to-DMA mapping, limited to physical RAM below 4 GiB and platforms where bus addresses equal physical addresses. It fails closed for unaligned ranges, overflow, unavailable physical memory, or ranges outside the mask. It does not yet implement IOMMU/IOVA setup, bounce buffers, cache synchronization, or device-specific DMA negotiation.

Chimera N-bit values (128 through 8192 bits and beyond) are logical/runtime values, not wider physical addresses. A logical address must never be truncated into a DMA address. The helper reports min(logical width, hardware address width); a 32-bit DMA device remains limited by its 32-bit mask regardless of the process's N-bit mode.

Production work still required: PCI DMA-mask negotiation, reserved-memory support, IOMMU backends (Intel VT-d/AMD-Vi), bounce buffers, non-coherent cache maintenance, hardware tests, and a running userspace D-Bus bridge.
