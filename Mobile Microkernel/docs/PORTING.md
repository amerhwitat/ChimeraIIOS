# Mobile Porting Guide

A new mobile SoC port should implement, in order:

1. boot handoff and memory-map discovery;
2. exception/vector entry and context switching;
3. timer and interrupt-controller backend;
4. MMU/address-space backend;
5. CPU topology and power-state discovery;
6. scheduler CPU-capacity/thermal inputs;
7. IOMMU/DMA interface;
8. display/input/storage/network and sensor drivers;
9. verified-boot and secure-storage integration;
10. suspend/resume validation.

Vendor-specific functionality belongs below the generic interfaces. The portable kernel must continue to build without a vendor SDK or proprietary binary.
