# Chimera KMDF Echo sample

Educational, bounded Windows KMDF integration sample. It demonstrates framework device creation, a sequential I/O queue, buffered IOCTL validation, and a user-mode test client.

This project is intentionally **not** part of the Chimera kernel build and does not implement privileged DMA, arbitrary physical memory access, or page pinning.

Build with a matching Windows Driver Kit and Visual Studio environment. Test only in a VM or dedicated development machine with appropriate driver-signing/debug configuration.
