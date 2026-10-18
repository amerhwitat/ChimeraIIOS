#include "chimera/boot_target.h"
#include <assert.h>
#include <stdint.h>
#include <string.h>

/* Registry stubs make these admission tests host-runnable without booting. */
static chimera_boot_module modules[8];
static uint32_t count;
extern "C" const chimera_boot_module *chimera_multiboot_find(uint32_t kind) {
    for (uint32_t i = 0; i < count; ++i)
        if (modules[i].kind == kind) return &modules[i];
    return nullptr;
}
static void reset() { memset(modules, 0, sizeof(modules)); count = 0; }
static void add(uint32_t kind) {
    modules[count].kind = kind; modules[count].base = 0x100000 + count * 0x1000;
    modules[count].size = 0x1000; ++count;
}
int main() {
    reset();
    assert(chimera_boot_target_validate(CHIMERA_BOOT_TARGET_LIVE) ==
           CHIMERA_BOOT_TARGET_ERR_MISSING_PAYLOAD);
    add(CHIMERA_MODULE_LIVE_INITRAMFS);
    assert(chimera_boot_target_validate(CHIMERA_BOOT_TARGET_LIVE) == CHIMERA_BOOT_TARGET_OK);
    assert(chimera_boot_target_validate(CHIMERA_BOOT_TARGET_INSTALLER) ==
           CHIMERA_BOOT_TARGET_ERR_MISSING_PAYLOAD);

    /* Multiple target payload families may coexist on a multi-mode ISO. */
    add(CHIMERA_MODULE_INSTALL_IMAGE);
    add(CHIMERA_MODULE_RECOVERY_INITRAMFS);
    assert(chimera_boot_target_validate(CHIMERA_BOOT_TARGET_LIVE) == CHIMERA_BOOT_TARGET_OK);
    assert(chimera_boot_target_validate(CHIMERA_BOOT_TARGET_INSTALLER) == CHIMERA_BOOT_TARGET_OK);
    assert(chimera_boot_target_validate(CHIMERA_BOOT_TARGET_RECOVERY) == CHIMERA_BOOT_TARGET_OK);

    reset(); add(CHIMERA_MODULE_RECOVERY_MANIFEST);
    assert(chimera_boot_target_validate(CHIMERA_BOOT_TARGET_RECOVERY) ==
           CHIMERA_BOOT_TARGET_ERR_MISSING_PAYLOAD);
    reset(); add(CHIMERA_MODULE_INSTALL_IMAGE);
    assert(chimera_boot_target_validate(CHIMERA_BOOT_TARGET_INSTALLER) == CHIMERA_BOOT_TARGET_OK);
    assert(chimera_boot_target_validate(CHIMERA_BOOT_TARGET_INVALID) ==
           CHIMERA_BOOT_TARGET_ERR_UNKNOWN);
    return 0;
}
