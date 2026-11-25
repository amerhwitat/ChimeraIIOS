#include "chimera/service.h"
#include <assert.h>

int main() {
    assert(chimera_service_set_state("test.storage", CHM_SVC_DECLARED) == 0);
    assert(chimera_service_get_state("test.storage") == CHM_SVC_DECLARED);

    /* Services cannot appear already started or skip the STARTING phase. */
    assert(chimera_service_set_state("test.network", CHM_SVC_RUNNING) == -4);
    assert(chimera_service_set_state("test.storage", 99u) == -1);
    assert(chimera_service_set_state("test.storage", CHM_SVC_RUNNING) == -3);

    assert(chimera_service_set_state("test.storage", CHM_SVC_STARTING) == 0);
    assert(chimera_service_set_state("test.storage", CHM_SVC_RUNNING) == 0);
    assert(chimera_service_set_state("test.storage", CHM_SVC_STARTING) == -3);
    assert(chimera_service_set_state("test.storage", CHM_SVC_STOPPING) == 0);
    assert(chimera_service_set_state("test.storage", CHM_SVC_STOPPED) == 0);
    assert(chimera_service_set_state("test.storage", CHM_SVC_STARTING) == 0);
    assert(chimera_service_set_state("test.storage", CHM_SVC_FAILED) == 0);
    assert(chimera_service_set_state("test.storage", CHM_SVC_RUNNING) == -3);
    assert(chimera_service_set_state("test.storage", CHM_SVC_RECOVERING) == 0);
    assert(chimera_service_set_state("test.storage", CHM_SVC_STARTING) == 0);
    assert(chimera_service_get_state("test.storage") == CHM_SVC_STARTING);
    return 0;
}
