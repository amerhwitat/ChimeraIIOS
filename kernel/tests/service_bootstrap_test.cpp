#include "chimera/service.h"
#include <stdio.h>

int main() {
    chimera_kore_bootstrap();
    const char *services[] = {
        "chimera.device",
        "chimera.storage",
        "chimera.security",
        "chimera.logging",
        "chimera.kore"
    };
    for (const char *id : services) {
        const uint32_t state = chimera_service_get_state(id);
        if (state != CHM_SVC_DECLARED) {
            fprintf(stderr, "FAIL: bootstrap fabricated readiness for %s (state=%u)\n",
                    id, static_cast<unsigned>(state));
            return 1;
        }
    }
    puts("PASS: Kore bootstrap declares core services without fabricating RUNNING state");
    return 0;
}
