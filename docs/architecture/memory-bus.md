# Chimera II Virtual Memory Bus

Koronos models memory as a virtual interconnect. A CPU register width is not assumed to equal a physical motherboard bus width.

Pipeline: descriptor -> safe probe -> BusSnapshot -> architecture profile -> virtual bus -> RAM/MMIO/DMA route.

The probe consumes firmware, device-tree, ACPI, hypervisor or virtual-platform descriptors. Host builds do not dereference arbitrary physical addresses for discovery.

Profiles describe address width, transaction data width, endianness, ordering, cache-line size, coherency, DMA/IOMMU capability, CPU/NUMA topology and firmware/hypervisor flags.

RAM, MMIO, DMA windows and reserved ranges are distinct. MMIO requires a handler; executable MMIO access is rejected. DMA is rejected when the selected profile does not advertise DMA.

RegisterN<4096> and RegisterN<8192> are logical execution state. Wide values can be transferred through multiple physical transactions or vector lanes, so transaction width remains independent from RegisterN width.

Architecture profiles cover principal Chimera targets plus major legacy/emulated targets. Platform-defined behavior is represented as such and requires runtime inspection rather than an invented universal topology.

External evidence includes QEMU's documented multi-architecture system/user emulation and LLVM's target-independent MC instruction representation. Chimera uses these as compatibility boundaries and does not copy their source into the kernel.
