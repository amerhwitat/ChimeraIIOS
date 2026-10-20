#include <cstdio>
#include "chimera/service.h"

int main() {
    chimera_kore_bootstrap();
    const char *ids[] = {
        "chimera.device", "chimera.storage", "chimera.security",
        "chimera.logging", "chimera.kore"
    };
    for (const char *id : ids) {
        const uint32_t state = chimera_service_get_state(id);
        if (state == CHM_SVC_RUNNING) {
            std::fprintf(stderr, "FAIL: unbacked service %s reported RUNNING\n", id);
            return 1;
        }
        if (state != CHM_SVC_BLOCKED) {
            std::fprintf(stderr, "FAIL: service %s expected BLOCKED, got %u\n", id, state);
            return 1;
        }
    }
    std::puts("Service bootstrap honesty regression tests: PASS");
    return 0;
}
