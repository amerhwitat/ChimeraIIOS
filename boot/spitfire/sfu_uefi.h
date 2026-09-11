#ifndef CHIMERA_SFU_UEFI_H
#define CHIMERA_SFU_UEFI_H
#include <efi.h>
#include <efilib.h>
#define CHM_EFI_KERNEL_PATH L"\\EFI\\CHIMERA\\koronos.elf"
EFI_STATUS EFIAPI efi_main(EFI_HANDLE image, EFI_SYSTEM_TABLE *system_table);
#endif
