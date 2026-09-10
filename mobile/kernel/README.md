# Koronos Mobile kernel integration

Koronos Mobile is designed around an AArch64 kernel boundary that can interoperate with Android GKI/KMI and vendor modules where the device requires them.

Android documentation describes GKI as a separation between hardware-agnostic generic kernel code and hardware-specific vendor modules. Chimera profiles therefore record GKI/KMI requirements and vendor-module locations instead of assuming that a generic kernel contains every phone driver.

Production images must use a compatible toolchain, exact KMI, device configuration, vendor modules and security metadata.
