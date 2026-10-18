#include "chimera/boot_target.h"

namespace {
static bool present(uint32_t kind) {
    const chimera_boot_module *m = chimera_multiboot_find(kind);
    return m && m->base != 0 && m->size != 0;
}
static bool any_live() {
    return present(CHIMERA_MODULE_LIVE_INITRAMFS) ||
           present(CHIMERA_MODULE_LIVE_MANIFEST);
}
static bool any_installer() {
    return present(CHIMERA_MODULE_INSTALL_IMAGE) ||
           present(CHIMERA_MODULE_INSTALL_MANIFEST) ||
           present(CHIMERA_MODULE_INSTALL_CONTRACT) ||
           present(CHIMERA_MODULE_INSTALL_PHASES) ||
           present(CHIMERA_MODULE_INSTALL_PROFILES);
}
static bool any_recovery() {
    return present(CHIMERA_MODULE_RECOVERY_INITRAMFS) ||
           present(CHIMERA_MODULE_RECOVERY_MANIFEST);
}
}

extern "C" int chimera_boot_target_validate(chimera_boot_target target) {
    const bool live = any_live();
    const bool installer = any_installer();
    const bool recovery = any_recovery();

    if (target != CHIMERA_BOOT_TARGET_LIVE &&
        target != CHIMERA_BOOT_TARGET_INSTALLER &&
        target != CHIMERA_BOOT_TARGET_RECOVERY)
        return CHIMERA_BOOT_TARGET_ERR_UNKNOWN;

    /* Never silently choose one target when the image contains several. */
    const unsigned selected = (live ? 1u : 0u) +
                              (installer ? 1u : 0u) +
                              (recovery ? 1u : 0u);
    if (selected > 1u)
        return CHIMERA_BOOT_TARGET_ERR_CONFLICTING_PAYLOADS;

    switch (target) {
        case CHIMERA_BOOT_TARGET_LIVE:
            if (!present(CHIMERA_MODULE_LIVE_INITRAMFS))
                return CHIMERA_BOOT_TARGET_ERR_MISSING_PAYLOAD;
            break;
        case CHIMERA_BOOT_TARGET_INSTALLER:
            /* The install image is the executable target's required payload. */
            if (!present(CHIMERA_MODULE_INSTALL_IMAGE))
                return CHIMERA_BOOT_TARGET_ERR_MISSING_PAYLOAD;
            break;
        case CHIMERA_BOOT_TARGET_RECOVERY:
            if (!present(CHIMERA_MODULE_RECOVERY_INITRAMFS))
                return CHIMERA_BOOT_TARGET_ERR_MISSING_PAYLOAD;
            break;
        default:
            return CHIMERA_BOOT_TARGET_ERR_UNKNOWN;
    }
    return CHIMERA_BOOT_TARGET_OK;
}
