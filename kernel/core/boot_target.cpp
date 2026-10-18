#include "chimera/boot_target.h"

namespace {
static bool present(uint32_t kind) {
    const chimera_boot_module *m = chimera_multiboot_find(kind);
    return m && m->base != 0 && m->size != 0;
}
}

extern "C" int chimera_boot_target_validate(chimera_boot_target target) {
    /*
     * ISO images may deliberately contain more than one target's assets.
     * Admission validates only the explicitly requested target; it must not
     * infer a target from whichever module happens to be present first.
     */
    switch (target) {
        case CHIMERA_BOOT_TARGET_LIVE:
            return present(CHIMERA_MODULE_LIVE_INITRAMFS)
                ? CHIMERA_BOOT_TARGET_OK
                : CHIMERA_BOOT_TARGET_ERR_MISSING_PAYLOAD;
        case CHIMERA_BOOT_TARGET_INSTALLER:
            return present(CHIMERA_MODULE_INSTALL_IMAGE)
                ? CHIMERA_BOOT_TARGET_OK
                : CHIMERA_BOOT_TARGET_ERR_MISSING_PAYLOAD;
        case CHIMERA_BOOT_TARGET_RECOVERY:
            return present(CHIMERA_MODULE_RECOVERY_INITRAMFS)
                ? CHIMERA_BOOT_TARGET_OK
                : CHIMERA_BOOT_TARGET_ERR_MISSING_PAYLOAD;
        default:
            return CHIMERA_BOOT_TARGET_ERR_UNKNOWN;
    }
}
