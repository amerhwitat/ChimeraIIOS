#ifndef CHIMERA_BOOT_FLAGS_H
#define CHIMERA_BOOT_FLAGS_H
#define CHM_BOOT_BIOS        (1u << 0)
#define CHM_BOOT_UEFI        (1u << 1)
#define CHM_BOOT_SECURE      (1u << 2)
#define CHM_BOOT_MEASURED    (1u << 3)
#define CHM_BOOT_MULTIBOOT2  (1u << 4)
#define CHM_BOOT_INITRD      (1u << 5)
#define CHM_BOOT_FRAMEBUFFER (1u << 6)
#define CHM_BOOT_ACPI        (1u << 7)
#define CHM_BOOT_EXPERIMENTAL (1u << 31)
#endif
