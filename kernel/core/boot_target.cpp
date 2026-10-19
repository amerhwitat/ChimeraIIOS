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

extern "C" int chimera_boot_target_parse(const char *line, chimera_boot_target *out) {
    if (!out) return CHIMERA_BOOT_TARGET_ERR_UNKNOWN;
    *out = CHIMERA_BOOT_TARGET_INVALID;
    if (!line) return CHIMERA_BOOT_TARGET_ERR_NOT_SELECTED;
    const char key[] = "chimera.target=";
    uint32_t matches = 0;
    for (const char *p = line; *p;) {
        while (*p == ' ' || *p == '\\t' || *p == '\\r' || *p == '\\n') ++p;
        if (!*p) break;
        const char *start = p;
        while (*p && *p != ' ' && *p != '\\t' && *p != '\\r' && *p != '\\n') ++p;
        const uint32_t len = static_cast<uint32_t>(p - start);
        if (len >= sizeof(key) - 1u) {
            bool same = true;
            for (uint32_t i = 0; i < sizeof(key) - 1u; ++i)
                if (start[i] != key[i]) { same = false; break; }
            if (same) {
                ++matches;
                const char *v = start + sizeof(key) - 1u;
                const uint32_t vlen = len - (sizeof(key) - 1u);
                if (vlen == 4 && v[0]=='l' && v[1]=='i' && v[2]=='v' && v[3]=='e')
                    *out = CHIMERA_BOOT_TARGET_LIVE;
                else if (vlen == 9 && v[0]=='i' && v[1]=='n' && v[2]=='s' && v[3]=='t' && v[4]=='a' && v[5]=='l' && v[6]=='l' && v[7]=='e' && v[8]=='r')
                    *out = CHIMERA_BOOT_TARGET_INSTALLER;
                else if (vlen == 8 && v[0]=='r' && v[1]=='e' && v[2]=='c' && v[3]=='o' && v[4]=='v' && v[5]=='e' && v[6]=='r' && v[7]=='y')
                    *out = CHIMERA_BOOT_TARGET_RECOVERY;
                else
                    return CHIMERA_BOOT_TARGET_ERR_UNKNOWN;
            }
        }
    }
    if (matches == 0) return CHIMERA_BOOT_TARGET_ERR_NOT_SELECTED;
    if (matches != 1) { *out = CHIMERA_BOOT_TARGET_INVALID; return CHIMERA_BOOT_TARGET_ERR_DUPLICATE; }
    return CHIMERA_BOOT_TARGET_OK;
}
