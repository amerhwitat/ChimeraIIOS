# Chimera II Mobile

Chimera II Mobile is the Android-class target of Koronos. It provides device-profiled microkernel images and integration scaffolding for AArch64 devices.

The target is designed for development boards and individually validated devices first, then expanded by model. It does not claim that a single image can boot every Samsung or Chinese-manufacturer handset.

Primary interfaces:
- AArch64
- fastboot/fastbootd or documented vendor boot protocol
- A/B and dynamic partitions where the device provides them
- Android GKI/KMI and vendor modules
- Android Verified Boot (AVB)
- recovery and rollback-safe update paths
