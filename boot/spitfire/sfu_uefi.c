#include "sfu_uefi.h"

EFI_STATUS EFIAPI efi_main(EFI_HANDLE image, EFI_SYSTEM_TABLE *st) {
    InitializeLib(image, st);
    Print(L"Chimera II Spit Fire UEFI\r\n");
    Print(L"Kernel payload: %s\r\n", CHM_EFI_KERNEL_PATH);
    if (!st || !st->BootServices) return EFI_INVALID_PARAMETER;
    /* The production loader boundary is intentionally kept small: filesystem,
       signature and ExitBootServices policy are supplied by the selected EFI build. */
    return EFI_SUCCESS;
}
